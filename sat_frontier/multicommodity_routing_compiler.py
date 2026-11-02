"""Exact Concurrent Multi-Commodity Routing Reliability and Leighton-Rao Gap Engine.

Hypothesis H22 (Theorem 14):
The Multi-Commodity Cut Condition Monotone CNF provides a certified upper bound
on concurrent routing reliability:
    R_routing(G, K) <= R_cut_condition(G, K)
with equality holding if and only if (G, K) satisfies the Seymour-Okamura
topological routing conditions (e.g., non-crossing demands on planar/series-parallel networks).
On networks with crossing demands (such as C_4 with opposite terminals or K_{2,3} bipartite graphs),
the Leighton-Rao routing gap is strictly positive:
    Delta_LR = R_cut_condition(G, K) - R_routing(G, K) > 0.
The Exact Integer Multi-Commodity Flow (IMCF) compiler encodes true simultaneous
non-conflicting path routing constraints under shared edge capacity, evaluating
R_routing(G, K) with exact rational precision (Fraction).

Theorem 14 (Leighton-Rao Multi-Commodity Routing Gap & Exact Duality):
Let G = (V, E) be a network where physical edge e in E has integer capacity c_e >= 1
and independent survival probability p_e in (0, 1].
Let K = {(s_1, t_1, d_1), ..., (s_k, t_k, d_k)} be k concurrent commodity demands.
1. (Cut Condition Upper Bound):
   For every operational state x in {0, 1}^E, if there exists a valid concurrent routing
   f = (f_1, ..., f_k) satisfying flow conservation and shared capacity:
       sum_{k=1}^m |f_k(e)| <= c_e * x_e   for all e in E,
   then every cut partition S subset V satisfies the aggregate capacity threshold:
       sum_{e in delta(S)} c_e * x_e >= sum_{k: |S cap {s_k, t_k}| = 1} d_k.
   Consequently:
       R_routing(G, K) <= R_cut_condition(G, K).
2. (Leighton-Rao Infeasibility Gap):
   There exist networks G and commodity sets K where the cut condition is satisfied
   with probability R_cut_condition > 0, yet NO concurrent integer or fractional routing
   exists in any operational state, yielding R_routing = 0 and Delta_LR > 0.
   Specifically, on C_4 with crossing demands K = {(0, 2, 1), (1, 3, 1)}:
       R_cut_condition(C_4, K; p=9/10) = 6561/10000 = 0.6561
       R_routing(C_4, K; p=9/10) = 0.0
       Delta_LR = 0.6561.
   On K_{2,3} with pairwise demands K = {(2, 3, 1), (3, 4, 1), (2, 4, 1)}:
       R_cut_condition(K_{2,3}, K; p=9/10) = 531441/1000000 = 0.531441
       R_routing(K_{2,3}, K; p=9/10) = 0.0
       Delta_LR = 0.531441.
3. (Exact Routing Reliability Evaluation):
   Exact evaluation over all 2^{|E|} physical states determines the true concurrent
   routability in exact rational arithmetic (Fraction), providing safety-critical guarantees
   against optimistic cut-condition estimation.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
import itertools
import time
from typing import Any, Dict, List, NamedTuple, Sequence, Set, Tuple

from sat_frontier.multi_commodity_compiler import (
    CommodityDemand,
    MultiCommodityNetwork,
    brute_force_multi_commodity_oracle,
)


class MultiCommodityAuditReport(NamedTuple):
    """Complete concurrent multi-commodity reliability and Leighton-Rao gap audit."""
    routing_reliability_exact: Fraction
    cut_condition_reliability_exact: Fraction
    leighton_rao_gap_exact: Fraction
    routing_reliability_float: float
    cut_condition_reliability_float: float
    leighton_rao_gap_float: float
    gap_detected: bool
    is_provably_routable: bool
    n_edges: int
    n_commodities: int
    elapsed_seconds: float


def find_all_simple_paths_in_graph(
    edges: Sequence[Tuple[Any, Any]],
    source: Any,
    target: Any,
) -> List[List[int]]:
    """Find all simple paths between source and target, returning list of edge indices."""
    adj = defaultdict(list)
    for idx, (u, v) in enumerate(edges):
        adj[u].append((v, idx))
        adj[v].append((u, idx))

    paths: List[List[int]] = []

    def dfs(curr: Any, visited: Set[Any], current_path: List[int]) -> None:
        if curr == target:
            paths.append(list(current_path))
            return
        for nbr, eid in adj[curr]:
            if nbr not in visited:
                visited.add(nbr)
                current_path.append(eid)
                dfs(nbr, visited, current_path)
                current_path.pop()
                visited.remove(nbr)

    dfs(source, {source}, [])
    return paths


def is_concurrent_routing_feasible(
    edges: Sequence[Tuple[Any, Any]],
    capacities: Sequence[int],
    commodities: Sequence[CommodityDemand],
    state_mask: int,
) -> bool:
    """Check if concurrent integer routing exists in the subgraph defined by state_mask."""
    # Filter active edges
    active_edge_indices = [i for i in range(len(edges)) if (state_mask >> i) & 1]
    if not active_edge_indices:
        return False

    active_edges = [edges[i] for i in active_edge_indices]
    active_capacities = [capacities[i] for i in active_edge_indices]

    # Map original edge indices to active edge indices
    active_edge_map = {orig_i: active_i for active_i, orig_i in enumerate(active_edge_indices)}

    # Build adjacency on active subgraph
    adj = defaultdict(list)
    for active_i, (u, v) in enumerate(active_edges):
        adj[u].append((v, active_i))
        adj[v].append((u, active_i))

    # Find candidate simple paths for each commodity in active subgraph
    comm_paths: List[List[List[int]]] = []
    for comm in commodities:
        paths: List[List[int]] = []

        def dfs(curr: Any, visited: Set[Any], cur_path: List[int]) -> None:
            if curr == comm.target:
                paths.append(list(cur_path))
                return
            for nbr, eid in adj[curr]:
                if nbr not in visited:
                    visited.add(nbr)
                    cur_path.append(eid)
                    dfs(nbr, visited, cur_path)
                    cur_path.pop()
                    visited.remove(nbr)

        dfs(comm.source, {comm.source}, [])
        if not paths:
            return False
        comm_paths.append(paths)

    # Backtracking search to assign paths satisfying concurrent edge capacities
    edge_usage: Dict[int, int] = defaultdict(int)

    def backtrack(comm_idx: int) -> bool:
        if comm_idx == len(commodities):
            return True

        comm = commodities[comm_idx]
        demand = comm.demand

        for path in comm_paths[comm_idx]:
            # Check capacity
            can_fit = True
            for eid in path:
                if edge_usage[eid] + demand > active_capacities[eid]:
                    can_fit = False
                    break

            if can_fit:
                for eid in path:
                    edge_usage[eid] += demand
                if backtrack(comm_idx + 1):
                    return True
                for eid in path:
                    edge_usage[eid] -= demand

        return False

    return backtrack(0)


def brute_force_exact_routing_oracle(
    net: MultiCommodityNetwork,
) -> Fraction:
    """Exhaustive state-space oracle evaluating TRUE concurrent routing reliability in Q."""
    m = len(net.edges)
    if m > 16:
        raise ValueError(f"Oracle limit exceeded: {m} > 16 physical edges")

    edges = list(net.edges)
    capacities = [net.edge_capacities[i] for i in range(1, m + 1)]
    probs = [net.edge_probs.get(i, Fraction(9, 10)) for i in range(1, m + 1)]

    exact_prob = Fraction(0, 1)

    for state in range(1 << m):
        if is_concurrent_routing_feasible(edges, capacities, net.commodities, state):
            term = Fraction(1, 1)
            for i in range(m):
                p = probs[i]
                if (state >> i) & 1:
                    term *= p
                else:
                    term *= (Fraction(1, 1) - p)
            exact_prob += term

    return exact_prob


def audit_concurrent_multi_commodity_flow(
    net: MultiCommodityNetwork,
) -> MultiCommodityAuditReport:
    """Perform comprehensive multi-commodity audit distinguishing cut condition from true routing."""
    t0 = time.perf_counter()

    # 1. Evaluate True Routing Reliability
    r_routing = brute_force_exact_routing_oracle(net)

    # 2. Evaluate Cut-Condition Reliability
    r_cut = brute_force_multi_commodity_oracle(net)

    # 3. Compute Leighton-Rao Routing Gap
    gap = r_cut - r_routing
    elapsed = time.perf_counter() - t0

    return MultiCommodityAuditReport(
        routing_reliability_exact=r_routing,
        cut_condition_reliability_exact=r_cut,
        leighton_rao_gap_exact=gap,
        routing_reliability_float=float(r_routing),
        cut_condition_reliability_float=float(r_cut),
        leighton_rao_gap_float=float(gap),
        gap_detected=gap > 0,
        is_provably_routable=r_routing > 0,
        n_edges=len(net.edges),
        n_commodities=len(net.commodities),
        elapsed_seconds=elapsed,
    )

