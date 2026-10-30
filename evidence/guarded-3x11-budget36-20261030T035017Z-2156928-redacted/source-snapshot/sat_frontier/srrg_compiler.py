"""Shared-Risk Resource Group (SRRG) Correlated Failure Reliability Compiler.

Hypothesis H14:
Dual SRRG-Cut Monotone CNF Compilation for Correlated Multi-Failure
Network Reliability.

In real-world mission-critical networks (optical DWDM rings, subsea fiber bundles,
cloud multi-region transit fabrics, power grids), physical edges often share
underlying risk infrastructure (conduits, fiber sheaths, optical amplifiers,
availability zone power circuits). A single physical failure event disables all
dependent transmission links simultaneously (fate-sharing).

Theorem (Dual SRRG-Cut Monotone CNF Duality):
Let G = (V, E) be a network where each edge e in E is mapped to a set of
Shared-Risk Resource Groups R(e) subseteq R. Each risk group g in R fails
independently with probability q_g = 1 - p_g.
Let P(s, t) be the set of simple s-t paths in G, with path risk set
R(P) = union_{e in P} R(e).
An SRRG s-t cut is a subset of risk groups K subseteq R whose simultaneous
failure interrupts all s-t paths:
    forall P in P(s, t),  K cap R(P) != empty.
Let K_min^SRRG(s, t) denote the family of inclusion-minimal SRRG cuts.
Then s and t are connected if and only if in every minimal SRRG cut K,
at least one risk group g in K remains operational:
    Phi_SRRG(G, s, t) = bigwedge_{K in K_min^SRRG(s, t)} (bigvee_{g in K} y_g)
where each boolean variable y_g indicates that risk group g is operational,
having weight p_g for positive literal y_g and 1 - p_g for negative literal ~y_g.
Phi_SRRG contains strictly |R| variables and zero auxiliary variables.
"""
from __future__ import annotations

import itertools
from collections import deque
from fractions import Fraction
from typing import Dict, FrozenSet, List, NamedTuple, Optional, Set, Tuple

from sat_frontier.wmc import WeightedFormula, wmc_solve


class SRRGNetwork(NamedTuple):
    """Network with Shared-Risk Resource Group (SRRG) mappings."""
    num_nodes: int
    edges: List[Tuple[int, int]]  # (u, v)
    edge_to_groups: Dict[Tuple[int, int], List[str]]
    group_probs: Dict[str, Fraction]
    is_directed: bool = False


def find_all_simple_paths(
    net: SRRGNetwork,
    s: int,
    t: int,
) -> List[List[Tuple[int, int]]]:
    """Find all simple s-t paths in net."""
    adj: Dict[int, List[Tuple[int, Tuple[int, int]]]] = {i: [] for i in range(net.num_nodes)}
    for u, v in net.edges:
        adj[u].append((v, (u, v)))
        if not net.is_directed:
            adj[v].append((u, (u, v)))

    paths: List[List[Tuple[int, int]]] = []

    def dfs(curr: int, target: int, visited: Set[int], current_path: List[Tuple[int, int]]):
        if curr == target:
            paths.append(list(current_path))
            return
        for nbr, edge in adj[curr]:
            if nbr not in visited:
                visited.add(nbr)
                current_path.append(edge)
                dfs(nbr, target, visited, current_path)
                current_path.pop()
                visited.remove(nbr)

    dfs(s, t, {s}, [])
    return paths


def find_minimal_srrg_cuts(
    net: SRRGNetwork,
    s: int,
    t: int,
) -> List[FrozenSet[str]]:
    """Compute all inclusion-minimal SRRG cuts K subseteq R.

    An SRRG cut is a hitting set of the risk sets R(P) for all simple s-t paths.
    An inclusion-minimal cut has no proper subset that is also an SRRG cut.
    """
    paths = find_all_simple_paths(net, s, t)
    if not paths:
        return []

    # Map each path to its set of risk groups
    path_groups: List[FrozenSet[str]] = []
    all_groups: Set[str] = set()
    for p in paths:
        pg: Set[str] = set()
        for e in p:
            # Look up edge groups (undirected may be stored either way)
            groups = net.edge_to_groups.get(e)
            if groups is None and not net.is_directed:
                groups = net.edge_to_groups.get((e[1], e[0]), [])
            if groups:
                pg.update(groups)
        f_pg = frozenset(pg)
        path_groups.append(f_pg)
        all_groups.update(f_pg)

    if not path_groups or any(len(pg) == 0 for pg in path_groups):
        # A path with no risk groups is unbreakable!
        # If any path has no groups, no set of risk groups can disconnect it.
        return []

    # Find minimal hitting sets of path_groups using breadth-first candidate generation
    # Sort groups by frequency in path_groups descending
    group_freq = {g: sum(1 for pg in path_groups if g in pg) for g in all_groups}
    sorted_groups = sorted(all_groups, key=lambda g: (-group_freq[g], g))

    minimal_cuts: List[FrozenSet[str]] = []

    # BFS by cardinality to guarantee minimal sets found first
    # Candidate search
    def is_hitting_set(cand: FrozenSet[str]) -> bool:
        return all(bool(cand & pg) for pg in path_groups)

    # Branch-and-bound / enumeration by increasing size
    max_k = len(sorted_groups)
    for size in range(1, max_k + 1):
        # Generate candidates of this size
        for comb in itertools.combinations(sorted_groups, size):
            cand = frozenset(comb)
            # Check if any already-found minimal cut is a subset
            if any(m.issubset(cand) for m in minimal_cuts):
                continue
            if is_hitting_set(cand):
                minimal_cuts.append(cand)

    return minimal_cuts


def to_srrg_cut_cnf(
    net: SRRGNetwork,
    s: int,
    t: int,
) -> Tuple[str, Dict[int, Fraction], Dict[str, int]]:
    """Compile SRRG network reliability into a monotone CNF over risk group variables.

    Returns:
        (dimacs_cnf_str, var_weights, group_to_var)
    """
    cuts = find_minimal_srrg_cuts(net, s, t)
    all_groups = sorted({g for cut in cuts for g in cut})
    group_to_var: Dict[str, int] = {g: i + 1 for i, g in enumerate(all_groups)}

    var_weights: Dict[int, Fraction] = {}
    for g, var in group_to_var.items():
        var_weights[var] = net.group_probs.get(g, Fraction(9, 10))

    if not cuts:
        # Check if connected or disconnected
        paths = find_all_simple_paths(net, s, t)
        if not paths:
            # Completely disconnected: formula is UNSAT (x1 and ~x1)
            cnf_str = "p cnf 1 2\n1 0\n-1 0\n"
            var_weights = {1: Fraction(1, 2)}
            return cnf_str, var_weights, {}
        else:
            # Always connected (unbreakable path exists): empty CNF (tautology, 0 clauses)
            cnf_str = "p cnf 0 0\n"
            return cnf_str, {}, {}

    clauses: List[List[int]] = []
    for cut in cuts:
        clause = [group_to_var[g] for g in sorted(cut)]
        clauses.append(clause)

    num_vars = len(group_to_var)
    num_clauses = len(clauses)
    lines = [f"p cnf {num_vars} {num_clauses}"]
    for cl in clauses:
        lines.append(" ".join(str(lit) for lit in cl) + " 0")
    cnf_str = "\n".join(lines) + "\n"

    return cnf_str, var_weights, group_to_var


def solve_srrg_reliability(
    net: SRRGNetwork,
    s: int,
    t: int,
) -> Tuple[Fraction, int, float]:
    """Solve exact two-terminal SRRG reliability via monotone cut CNF compilation.

    Returns:
        (exact_reliability, search_nodes, solve_time_sec)
    """
    cuts = find_minimal_srrg_cuts(net, s, t)
    paths = find_all_simple_paths(net, s, t)

    if not paths:
        return Fraction(0, 1), 0, 0.0

    if not cuts:
        # An unbreakable path exists
        return Fraction(1, 1), 0, 0.0

    cuts = find_minimal_srrg_cuts(net, s, t)
    paths = find_all_simple_paths(net, s, t)

    if not paths:
        return Fraction(0, 1), 0, 0.0

    if not cuts:
        # An unbreakable path exists
        return Fraction(1, 1), 0, 0.0

    all_groups = sorted({g for cut in cuts for g in cut})
    group_to_var: Dict[str, int] = {g: i + 1 for i, g in enumerate(all_groups)}

    literal_weights: Dict[int, Fraction] = {}
    for g, var in group_to_var.items():
        p = net.group_probs.get(g, Fraction(9, 10))
        literal_weights[var] = p
        literal_weights[-var] = Fraction(1, 1) - p

    clauses: List[List[int]] = []
    for cut in cuts:
        clauses.append([group_to_var[g] for g in sorted(cut)])

    wf = WeightedFormula(clauses, n_vars=len(group_to_var), weights=literal_weights)
    res = wmc_solve(wf, algorithm='combined_wmc', seconds=15.0, max_nodes=100000)
    if res['status'] == 'exact':
        return Fraction(res['weight_fraction']), res['nodes'], res['elapsed_seconds']
    else:
        raise RuntimeError(f"WMC solver failed: {res.get('reason')}")


def brute_force_srrg_oracle(
    net: SRRGNetwork,
    s: int,
    t: int,
) -> Fraction:
    """Independent 2^|R| state enumeration oracle for exact SRRG reliability verification."""
    all_groups = sorted(net.group_probs.keys())
    n_groups = len(all_groups)
    group_idx = {g: i for i, g in enumerate(all_groups)}

    total_prob = Fraction(0, 1)

    for state in itertools.product([0, 1], repeat=n_groups):
        state_dict = {all_groups[i]: state[i] for i in range(n_groups)}

        # Weight of this risk state
        prob = Fraction(1, 1)
        for g in all_groups:
            p_g = net.group_probs[g]
            prob *= p_g if state_dict[g] == 1 else (Fraction(1, 1) - p_g)

        # Determine which edges are operational
        # An edge operates iff ALL of its assigned risk groups operate (state == 1)
        adj: Dict[int, List[int]] = {i: [] for i in range(net.num_nodes)}
        for u, v in net.edges:
            groups = net.edge_to_groups.get((u, v))
            if groups is None and not net.is_directed:
                groups = net.edge_to_groups.get((v, u), [])

            edge_up = True
            if groups:
                edge_up = all(state_dict[g] == 1 for g in groups)

            if edge_up:
                adj[u].append(v)
                if not net.is_directed:
                    adj[v].append(u)

        # Check reachability from s to t
        vis = {s}
        q = deque([s])
        while q:
            curr = q.popleft()
            for nbr in adj.get(curr, []):
                if nbr not in vis:
                    vis.add(nbr)
                    q.append(nbr)

        if t in vis:
            total_prob += prob

    return total_prob
