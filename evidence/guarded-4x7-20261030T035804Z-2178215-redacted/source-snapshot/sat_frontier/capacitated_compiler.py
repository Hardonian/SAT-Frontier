"""Capacitated Network Flow Reliability Compiler via Dual Cut Threshold Compilation.

Hypothesis H16:
Dual Cut Threshold Monotone CNF Compilation encodes exact multi-unit demand
connectivity P(MaxFlow(s, t) >= D) with strictly |E| variables and zero auxiliary
flow or routing variables.

Theorem (Capacitated Dual Cut Duality):
Let G = (V, E) be a network where each edge e in E has integer capacity c_e >= 1
and operational probability p_e in (0, 1].
Let D >= 1 be the target flow demand between source s and target t.
By the Max-Flow Min-Cut Theorem, the maximum s-t flow is at least D if and only if
every s-t cut has surviving capacity at least D:
    MaxFlow(G, s, t) >= D  <=>  forall C in C_min(s, t),  sum_{e in C} c_e * x_e >= D.
For any minimal cut C, a subset of edges F subseteq C is an inclusion-minimal
capacity-breaking subset if:
    sum_{e in C \\ F} c_e < D  and  forall e in F, sum_{e' in C \\ (F \\ {e})} c_e' >= D.
Then surviving capacity across C is at least D if and only if in every minimal
capacity-breaking subset F, at least one edge in F survives:
    sum_{e in C} c_e * x_e >= D  <=>  bigwedge_{F in F_min(C, D)} (bigvee_{e in F} x_e).
The exact capacitated reliability formula is the conjunction across all minimal cuts:
    Phi_cap(G, s, t, D) = bigwedge_{C in C_min(s, t)} bigwedge_{F in F_min(C, D)} (bigvee_{e in F} x_e).
Phi_cap contains strictly |E| variables and zero auxiliary flow variables.
"""
from __future__ import annotations

import itertools
import time
from collections import deque
from fractions import Fraction
from typing import Any, Dict, FrozenSet, List, NamedTuple, Optional, Set, Tuple

from sat_frontier.cut_compiler import find_all_minimal_cuts
from sat_frontier.reliability import NetworkGraph
from sat_frontier.wmc import WeightedFormula, wmc_solve


class CapacitatedNetwork:
    """Network graph with discrete integer edge capacities and operational probabilities."""

    def __init__(self, is_directed: bool = False):
        self.is_directed: bool = is_directed
        self.nodes: Set[Any] = set()
        self.edges: List[Tuple[Any, Any]] = []
        self.edge_capacities: Dict[int, int] = {}      # 1-indexed edge id -> integer capacity
        self.edge_probs: Dict[int, Fraction] = {}      # 1-indexed edge id -> Fraction prob
        self.adj: Dict[Any, List[Tuple[Any, int]]] = {}

    def add_edge(
        self,
        u: Any,
        v: Any,
        capacity: int = 1,
        prob: Fraction = Fraction(9, 10),
    ) -> int:
        """Add an edge with capacity and operational probability."""
        self.nodes.add(u)
        self.nodes.add(v)
        eid = len(self.edges) + 1
        self.edges.append((u, v))
        self.edge_capacities[eid] = capacity
        self.edge_probs[eid] = prob

        self.adj.setdefault(u, []).append((v, eid))
        self.adj.setdefault(v, [])
        if not self.is_directed:
            self.adj[v].append((u, eid))
        return eid


def find_minimal_capacity_breaking_sets(
    cut: Set[int],
    edge_capacities: Dict[int, int],
    demand: int,
) -> List[FrozenSet[int]]:
    """Find all inclusion-minimal subsets F subseteq cut whose failure causes surviving capacity < demand."""
    cut_edges = sorted(cut)
    total_cap = sum(edge_capacities.get(e, 1) for e in cut_edges)

    if total_cap < demand:
        # Cut cannot even satisfy demand when all edges operate!
        # An empty failure set breaks demand: formula is UNSAT
        return [frozenset()]

    max_allowable_failure = total_cap - demand
    # A subset F breaks demand iff sum_{e in F} c_e > max_allowable_failure
    breaking_threshold = max_allowable_failure + 1

    minimal_breakers: List[FrozenSet[int]] = []

    # Search subsets by increasing cardinality
    n = len(cut_edges)
    for size in range(1, n + 1):
        for comb in itertools.combinations(cut_edges, size):
            cand = frozenset(comb)
            # Check if any smaller minimal breaker is already a subset
            if any(m.issubset(cand) for m in minimal_breakers):
                continue

            failed_cap = sum(edge_capacities.get(e, 1) for e in cand)
            if failed_cap >= breaking_threshold:
                minimal_breakers.append(cand)

    return minimal_breakers


def find_all_capacitated_cuts(net: CapacitatedNetwork, source: Any, target: Any) -> List[Set[int]]:
    """Find all inclusion-minimal s-t edge cuts in net, correctly handling multigraph parallel edges."""
    nodes = list(net.nodes)
    adj: Dict[Any, Set[Any]] = {u: set() for u in nodes}
    for u, v in net.edges:
        adj[u].add(v)
        if not net.is_directed:
            adj[v].add(u)

    def is_connected_subgraph(sub_nodes: Set[Any], seed: Any) -> bool:
        if seed not in sub_nodes:
            return False
        vis = {seed}
        q = deque([seed])
        while q:
            curr = q.popleft()
            for nbr in adj.get(curr, set()):
                if nbr in sub_nodes and nbr not in vis:
                    vis.add(nbr)
                    q.append(nbr)
        return len(vis) == len(sub_nodes)

    all_nodes_set = set(nodes)
    minimal_cuts: List[Set[int]] = []
    seen_S: Set[FrozenSet[Any]] = set()

    def explore(S: Set[Any], frontier: Set[Any]):
        T = all_nodes_set - S
        if target in T and is_connected_subgraph(T, target):
            # Compute all edges crossing between S and T
            cut = set()
            for eid, (u, v) in enumerate(net.edges, 1):
                if (u in S and v in T) or (not net.is_directed and v in S and u in T):
                    cut.add(eid)
            if cut:
                minimal_cuts.append(cut)

        for nbr in sorted(frontier, key=str):
            if nbr == target:
                continue
            new_S = S | {nbr}
            f_new_S = frozenset(new_S)
            if f_new_S not in seen_S:
                seen_S.add(f_new_S)
                new_frontier = (frontier - {nbr}) | {x for x in adj[nbr] if x not in new_S}
                explore(new_S, new_frontier)

    seen_S.add(frozenset({source}))
    init_frontier = {x for x in adj.get(source, set()) if x != source}
    explore({source}, init_frontier)
    return minimal_cuts


def to_capacitated_cut_cnf(
    net: CapacitatedNetwork,
    source: Any,
    target: Any,
    demand: int = 1,
) -> Tuple[WeightedFormula, List[List[int]]]:
    """Compile capacitated network demand connectivity into a monotone CNF over edge variables."""
    min_cuts = find_all_capacitated_cuts(net, source, target)
    if not min_cuts:
        # Disconnected
        clauses = [[1], [-1]]
        wf = WeightedFormula(clauses, n_vars=1, weights={1: Fraction(1, 2), -1: Fraction(1, 2)})
        return wf, clauses

    clauses: List[List[int]] = []
    seen_clauses: Set[Tuple[int, ...]] = set()

    for cut in min_cuts:
        breaking_sets = find_minimal_capacity_breaking_sets(cut, net.edge_capacities, demand)
        for b_set in breaking_sets:
            if len(b_set) == 0:
                # Capacity of cut is strictly less than demand! Always broken.
                clauses = [[1], [-1]]
                wf = WeightedFormula(clauses, n_vars=1, weights={1: Fraction(1, 2), -1: Fraction(1, 2)})
                return wf, clauses

            clause = sorted(b_set)
            tup = tuple(clause)
            if tup not in seen_clauses:
                seen_clauses.add(tup)
                clauses.append(clause)

    weights: Dict[int, Fraction] = {}
    for eid in range(1, len(net.edges) + 1):
        p = net.edge_probs.get(eid, Fraction(9, 10))
        weights[eid] = p
        weights[-eid] = Fraction(1, 1) - p

    wf = WeightedFormula(clauses, n_vars=len(net.edges), weights=weights)
    return wf, clauses


def solve_capacitated_reliability(
    net: CapacitatedNetwork,
    source: Any,
    target: Any,
    demand: int = 1,
    timeout_seconds: float = 30.0,
    max_nodes: int = 100000,
) -> Tuple[Fraction, int, float]:
    """Compute exact rational probability P(MaxFlow >= demand).

    Returns:
        (exact_probability, search_nodes, solve_time_seconds)
    """
    t0 = time.perf_counter()
    wf, clauses = to_capacitated_cut_cnf(net, source, target, demand)
    res = wmc_solve(wf, algorithm="combined_wmc", seconds=timeout_seconds, max_nodes=max_nodes)
    if res["status"] == "exact":
        return Fraction(res["weight_fraction"]), res["nodes"], time.perf_counter() - t0
    else:
        raise RuntimeError(f"Capacitated solver failed: {res.get('reason')}")


def compute_max_flow_dinic(
    nodes: Set[Any],
    edges: List[Tuple[Any, Any]],
    capacities: Dict[int, int],
    active_edge_ids: Set[int],
    source: Any,
    target: Any,
) -> int:
    """Compute exact maximum s-t flow via Dinic's blocking flow algorithm."""
    # Build residual graph
    res_cap: Dict[Tuple[Any, Any], int] = {}
    adj: Dict[Any, List[Any]] = {u: [] for u in nodes}

    for eid in active_edge_ids:
        u, v = edges[eid - 1]
        c = capacities.get(eid, 1)
        res_cap[(u, v)] = res_cap.get((u, v), 0) + c
        res_cap[(v, u)] = res_cap.get((v, u), 0) + c  # undirected
        if v not in adj[u]:
            adj[u].append(v)
        if u not in adj[v]:
            adj[v].append(u)

    total_flow = 0

    while True:
        # BFS to build level graph
        level = {source: 0}
        q = deque([source])
        while q:
            curr = q.popleft()
            for nbr in adj.get(curr, []):
                if nbr not in level and res_cap.get((curr, nbr), 0) > 0:
                    level[nbr] = level[curr] + 1
                    q.append(nbr)

        if target not in level:
            break

        # DFS along shortest augmenting paths
        ptr = {u: 0 for u in nodes}

        def dfs(curr: Any, pushed: int) -> int:
            if curr == target or pushed == 0:
                return pushed
            for i in range(ptr[curr], len(adj.get(curr, []))):
                ptr[curr] = i
                nbr = adj[curr][i]
                cap = res_cap.get((curr, nbr), 0)
                if level.get(nbr) == level[curr] + 1 and cap > 0:
                    tr = dfs(nbr, min(pushed, cap))
                    if tr > 0:
                        res_cap[(curr, nbr)] -= tr
                        res_cap[(nbr, curr)] += tr
                        return tr
            return 0

        while True:
            pushed = dfs(source, 10**9)
            if pushed == 0:
                break
            total_flow += pushed

    return total_flow


def brute_force_capacitated_oracle(
    net: CapacitatedNetwork,
    source: Any,
    target: Any,
    demand: int = 1,
) -> Fraction:
    """Independent 2^|E| state enumeration oracle computing exact rational P(MaxFlow >= demand)."""
    m = len(net.edges)
    total_prob = Fraction(0, 1)

    for mask in range(1 << m):
        active_eids = set()
        state_prob = Fraction(1, 1)

        for i in range(m):
            eid = i + 1
            p = net.edge_probs.get(eid, Fraction(9, 10))
            if mask & (1 << i):
                active_eids.add(eid)
                state_prob *= p
            else:
                state_prob *= (Fraction(1, 1) - p)

        flow = compute_max_flow_dinic(
            net.nodes, net.edges, net.edge_capacities, active_eids, source, target
        )
        if flow >= demand:
            total_prob += state_prob

    return total_prob
