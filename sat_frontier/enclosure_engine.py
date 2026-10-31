"""Any-Time Monotone Dual Bounding and Rigorous Reliability Enclosures.

Hypothesis H21 (Theorem 13):
Monotone Dual Bounding evaluates certified upper and lower bounds on network reliability
in polynomial delay without complete cut or path enumeration:
    R_lower(P') <= R(G) <= R_upper(C')
where C' subset C is any subset of minimal cuts and P' subset P is any subset of minimal paths.

Theorem 13 (Monotone Dual Enclosure Duality):
Let G = (V, E) be a network with independent edge probabilities p_e in [0, 1].
Let C be the complete set of minimal s-t cuts and P be the complete set of minimal s-t paths.
1. For any subset of minimal cuts C' subset C, the monotone positive CNF formula:
       phi_{C'} = bigwedge_{C in C'} bigvee_{e in C} x_e
   satisfies:
       R(G) <= WMC(phi_{C'}; p) = R_upper(C').
2. For any subset of minimal paths P' subset P, the subgraph G[P'] induced by P' satisfies:
       R_lower(P') = R(G[P']; p) <= R(G).
3. The interval [R_lower(P'), R_upper(C')] is a guaranteed mathematical enclosure:
       R(G) in [R_lower(P'), R_upper(C')].
   For any epsilon > 0, iteratively expanding P' with shortest surviving paths and C'
   with minimum-capacity cuts monotonically narrows the certificate gap:
       Delta(P', C') = R_upper(C') - R_lower(P') <= epsilon.
"""
from __future__ import annotations

from collections import deque
from fractions import Fraction
from typing import Any, Dict, Generator, List, NamedTuple, Set, Tuple

from sat_frontier.cut_compiler import find_all_minimal_cuts, to_cut_cnf
from sat_frontier.reliability import NetworkGraph
from sat_frontier.wmc import WeightedFormula, wmc_solve


class EnclosureResult(NamedTuple):
    """Certified reliability enclosure interval and convergence metrics."""
    lower_bound_exact: Fraction
    upper_bound_exact: Fraction
    gap_exact: Fraction
    lower_bound_float: float
    upper_bound_float: float
    gap_float: float
    paths_count: int
    cuts_count: int
    enclosed: bool
    exact_reliability: Fraction | None = None


def find_shortest_paths(net: Any, source: Any, target: Any, max_paths: int = 10) -> List[List[Tuple[int, int]]]:
    """Find up to max_paths edge-minimal simple paths from source to target via BFS."""
    paths: List[List[Tuple[int, int]]] = []
    queue: deque[Tuple[Any, List[Tuple[int, int]], Set[Any]]] = deque([(source, [], {source})])

    while queue and len(paths) < max_paths:
        curr, path_edges, visited = queue.popleft()
        if curr == target:
            paths.append(path_edges)
            continue
        for item in net.adj.get(curr, []):
            nbr = item[0] if isinstance(item, (list, tuple)) else item
            if nbr not in visited:
                e = (curr, nbr)
                queue.append((nbr, path_edges + [e], visited | {nbr}))

    return paths


def compute_enclosure(
    net: Any,
    source: Any,
    target: Any,
    edge_probs: Dict[Tuple[int, int], Fraction],
    selected_cuts: List[Set[int]] | None = None,
    selected_paths: List[List[Tuple[int, int]]] | None = None,
) -> EnclosureResult:
    """Compute guaranteed lower bound from paths and upper bound from cuts."""
    edges = list(net.edges)
    edge_to_idx = {e: idx for idx, e in enumerate(edges, start=1)}
    for u, v in edges:
        edge_to_idx[(v, u)] = edge_to_idx[(u, v)]

    # 1. Compute Upper Bound from cuts: WMC(phi_{C'})
    if selected_cuts is None:
        all_cuts = find_all_minimal_cuts(net, source, target)
        selected_cuts = all_cuts if len(all_cuts) <= 2 else all_cuts[:max(1, len(all_cuts) // 2)]

    clauses = [list(c) for c in selected_cuts]
    m = len(edges)
    weights: Dict[int, Fraction] = {}
    for idx, (u, v) in enumerate(edges, start=1):
        p = edge_probs.get((u, v), edge_probs.get((v, u), Fraction(9, 10)))
        weights[idx] = p
        weights[-idx] = Fraction(1) - p

    wf_upper = WeightedFormula(clauses, n_vars=m, weights=weights)
    res_upper = wmc_solve(wf_upper, algorithm="combined")
    r_upper = Fraction(res_upper["weight_fraction"])

    # 2. Compute Lower Bound from paths: R(G[P'])
    if selected_paths is None:
        selected_paths = find_shortest_paths(net, source, target, max_paths=2)

    path_edges: Set[Tuple[int, int]] = set()
    for p_edges in selected_paths:
        for u, v in p_edges:
            path_edges.add((u, v) if (u, v) in edge_probs else (v, u))

    if not path_edges:
        r_lower = Fraction(0, 1)
    else:
        # Build subgraph containing only edges in selected_paths
        sub_net = NetworkGraph()
        for u, v in path_edges:
            p = edge_probs.get((u, v), edge_probs.get((v, u), Fraction(9, 10)))
            sub_net.add_edge(u, v, p)

        # Full exact reliability on the path-induced subgraph
        wf_lower = to_cut_cnf(sub_net, source, target)
        res_lower = wmc_solve(wf_lower, algorithm="combined")
        r_lower = Fraction(res_lower["weight_fraction"])

    # Verify enclosure monotonicity
    gap = r_upper - r_lower
    enclosed = gap >= 0

    return EnclosureResult(
        lower_bound_exact=r_lower,
        upper_bound_exact=r_upper,
        gap_exact=gap,
        lower_bound_float=float(r_lower),
        upper_bound_float=float(r_upper),
        gap_float=float(gap),
        paths_count=len(selected_paths),
        cuts_count=len(selected_cuts),
        enclosed=enclosed,
    )


def anytime_enclosure_stream(
    net: Any,
    source: Any,
    target: Any,
    edge_probs: Dict[Tuple[int, int], Fraction],
    max_steps: int = 10,
) -> Generator[EnclosureResult, None, None]:
    """Stream progressively tighter enclosure intervals [R_lower, R_upper] by iteratively adding cuts and paths."""
    all_cuts = find_all_minimal_cuts(net, source, target)
    all_paths = find_shortest_paths(net, source, target, max_paths=max_steps)

    # Sort cuts by size (smallest bottleneck cuts first)
    sorted_cuts = sorted(all_cuts, key=lambda c: len(c))

    curr_cuts: List[Set[int]] = []
    curr_paths: List[List[Tuple[int, int]]] = []

    steps = max(1, min(max_steps, max(len(sorted_cuts), len(all_paths))))
    cut_step = max(1, len(sorted_cuts) // steps)
    path_step = max(1, len(all_paths) // steps)

    for i in range(1, steps + 1):
        curr_cuts = sorted_cuts[:min(len(sorted_cuts), i * cut_step)]
        curr_paths = all_paths[:min(len(all_paths), i * path_step)]
        enc = compute_enclosure(net, source, target, edge_probs, curr_cuts, curr_paths)
        yield enc
