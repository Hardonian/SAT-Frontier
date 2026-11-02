"""Greedy Priority-Weighted Reliability Enclosures and Accelerated Dual Contraction.

Hypothesis H23 (Theorem 15):
Greedy Priority-Weighted Enclosure Bounding contracts the certification interval:
    Delta(P', C') = R_upper(C') - R_lower(P') <= epsilon
exponentially faster than cardinality-based cut/path selection by prioritizing
minimal cuts by maximum failure probability prod_{e in C} (1 - p_e) and minimal
paths by maximum survival probability prod_{e in P} p_e:
    C_1, C_2, ... sorted by prod_{e in C_i} (1 - p_e) desc
    P_1, P_2, ... sorted by prod_{e in P_j} p_e desc.

Theorem 15 (Greedy Priority Enclosure Duality):
Let G = (V, E) be a network with independent edge probabilities p_e in [0, 1].
Let C be the set of minimal s-t cuts and P be the set of minimal s-t paths.
1. (Monotone Contraction Invariant):
   For any nested sequences C_1 subseteq C_2 subseteq ... subseteq C and
   P_1 subseteq P_2 subseteq ... subseteq P:
       R_lower(P_1) <= R_lower(P_2) <= ... <= R(G) <= ... <= R_upper(C_2) <= R_upper(C_1).
2. (Greedy Probability-Weighted Convergence):
   Selecting cut C* = argmax_{C in C \\ C'} prod_{e in C} (1 - p_e) maximizes the single-clause
   tightening of the Boolean upper bound:
       Delta_upper = WMC(phi_{C'}; p) - WMC(phi_{C' cup {C*}}; p).
   Selecting path P* = argmax_{P in P \\ P'} prod_{e in P} p_e maximizes the initial
   lower-bound probability increment of the path-induced subgraph G[P' cup {P*}].
3. (Any-Time Certified Termination):
   For any target certificate tolerance epsilon > 0, greedy priority streaming terminates
   with the minimal number of evaluated cuts and paths satisfying R_upper - R_lower <= epsilon.
"""
from __future__ import annotations

from collections import defaultdict, deque
from fractions import Fraction
import time
from typing import Any, Dict, Generator, List, NamedTuple, Sequence, Set, Tuple

from sat_frontier.cut_compiler import find_all_minimal_cuts, to_cut_cnf
from sat_frontier.reliability import NetworkGraph
from sat_frontier.wmc import WeightedFormula, wmc_solve


class GreedyEnclosureResult(NamedTuple):
    """Certified greedy reliability enclosure metrics."""
    lower_bound_exact: Fraction
    upper_bound_exact: Fraction
    gap_exact: Fraction
    lower_bound_float: float
    upper_bound_float: float
    gap_float: float
    paths_count: int
    cuts_count: int
    enclosed: bool
    tolerance_achieved: bool
    elapsed_seconds: float


def find_all_simple_paths(
    net: Any,
    source: Any,
    target: Any,
    max_paths: int = 50,
) -> List[List[Tuple[int, int]]]:
    """Find simple paths from source to target via bounded depth-first search."""
    paths: List[List[Tuple[int, int]]] = []
    edges = list(net.edges)

    adj: Dict[Any, List[Any]] = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    def dfs(curr: Any, visited: Set[Any], current_path: List[Tuple[int, int]]) -> None:
        if len(paths) >= max_paths:
            return
        if curr == target:
            paths.append(list(current_path))
            return
        for nbr in adj.get(curr, []):
            if nbr not in visited:
                dfs(nbr, visited | {nbr}, current_path + [(curr, nbr)])

    dfs(source, {source}, [])
    return paths


def sort_cuts_by_greedy_failure_priority(
    cuts: Sequence[Set[int]],
    edges: Sequence[Tuple[int, int]],
    edge_probs: Dict[Tuple[int, int], Fraction],
) -> List[Set[int]]:
    """Sort minimal cuts in descending order of failure probability: prod_{e in C} (1 - p_e)."""
    def cut_failure_weight(cut: Set[int]) -> Fraction:
        weight = Fraction(1, 1)
        for eid in cut:
            # eid is 1-indexed into edges
            u, v = edges[eid - 1]
            p = edge_probs.get((u, v), edge_probs.get((v, u), Fraction(9, 10)))
            weight *= (Fraction(1, 1) - p)
        return weight

    return sorted(cuts, key=cut_failure_weight, reverse=True)


def sort_paths_by_greedy_survival_priority(
    paths: Sequence[List[Tuple[int, int]]],
    edge_probs: Dict[Tuple[int, int], Fraction],
) -> List[List[Tuple[int, int]]]:
    """Sort minimal paths in descending order of survival probability: prod_{e in P} p_e."""
    def path_survival_weight(path: List[Tuple[int, int]]) -> Fraction:
        weight = Fraction(1, 1)
        for u, v in path:
            p = edge_probs.get((u, v), edge_probs.get((v, u), Fraction(9, 10)))
            weight *= p
        return weight

    return sorted(paths, key=path_survival_weight, reverse=True)


def compute_greedy_enclosure(
    net: Any,
    source: Any,
    target: Any,
    edge_probs: Dict[Tuple[int, int], Fraction],
    target_tolerance: Fraction = Fraction(1, 100),  # default epsilon = 0.01 (1% gap)
    max_steps: int = 15,
) -> GreedyEnclosureResult:
    """Compute greedy priority-contracted enclosure until target tolerance or max steps."""
    t0 = time.perf_counter()
    edges = list(net.edges)
    m = len(edges)

    # Base variable weights for CNF
    weights: Dict[int, Fraction] = {}
    for idx, (u, v) in enumerate(edges, start=1):
        p = edge_probs.get((u, v), edge_probs.get((v, u), Fraction(9, 10)))
        weights[idx] = p
        weights[-idx] = Fraction(1, 1) - p

    # Enumerate all minimal cuts and simple paths
    all_cuts = find_all_minimal_cuts(net, source, target)
    all_paths = find_all_simple_paths(net, source, target, max_paths=max_steps * 2)

    # Sort cuts and paths with greedy priority
    sorted_cuts = sort_cuts_by_greedy_failure_priority(all_cuts, edges, edge_probs)
    sorted_paths = sort_paths_by_greedy_survival_priority(all_paths, edge_probs)

    best_r_upper = Fraction(1, 1)
    best_r_lower = Fraction(0, 1)
    best_gap = Fraction(1, 1)

    steps = min(max_steps, max(len(sorted_cuts), len(sorted_paths)))
    chosen_cuts_count = 0
    chosen_paths_count = 0

    for step in range(1, steps + 1):
        # 1. Update Upper Bound with top step cuts
        k_cuts = min(step, len(sorted_cuts))
        curr_cuts = sorted_cuts[:k_cuts]
        clauses = [list(c) for c in curr_cuts]
        wf_upper = WeightedFormula(clauses, n_vars=m, weights=weights)
        res_upper = wmc_solve(wf_upper, algorithm="combined")
        r_upper = Fraction(res_upper["weight_fraction"])

        # 2. Update Lower Bound with top step paths
        k_paths = min(step, len(sorted_paths))
        curr_paths = sorted_paths[:k_paths]
        path_edges: Set[Tuple[int, int]] = set()
        for p in curr_paths:
            for u, v in p:
                path_edges.add((u, v) if (u, v) in edge_probs else (v, u))

        sub_net = NetworkGraph()
        for u, v in path_edges:
            p = edge_probs.get((u, v), edge_probs.get((v, u), Fraction(9, 10)))
            sub_net.add_edge(u, v, p)

        wf_lower = to_cut_cnf(sub_net, source, target)
        res_lower = wmc_solve(wf_lower, algorithm="combined")
        r_lower = Fraction(res_lower["weight_fraction"])

        gap = r_upper - r_lower
        best_r_upper = r_upper
        best_r_lower = r_lower
        best_gap = gap
        chosen_cuts_count = k_cuts
        chosen_paths_count = k_paths

        if gap <= target_tolerance:
            break

    elapsed = time.perf_counter() - t0

    return GreedyEnclosureResult(
        lower_bound_exact=best_r_lower,
        upper_bound_exact=best_r_upper,
        gap_exact=best_gap,
        lower_bound_float=float(best_r_lower),
        upper_bound_float=float(best_r_upper),
        gap_float=float(best_gap),
        paths_count=chosen_paths_count,
        cuts_count=chosen_cuts_count,
        enclosed=best_gap >= 0,
        tolerance_achieved=best_gap <= target_tolerance,
        elapsed_seconds=elapsed,
    )
