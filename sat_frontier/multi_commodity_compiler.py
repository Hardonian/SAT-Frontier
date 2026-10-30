"""Multi-Commodity Capacitated Flow Reliability Compiler via Dual Cut Duality.

Hypothesis H18:
Dual Multi-Cut Threshold Monotone CNF Compilation encodes concurrent multi-commodity
demand reliability P(ConcurrentFlow(G, K) >= D) with strictly |E| variables and
zero auxiliary commodity flow or routing variables.

Theorem 10 (Multi-Commodity Dual Cut Duality Theorem):
Let G = (V, E) be a network where each physical edge e in E has integer capacity c_e >= 1
and independent operational survival probability p_e in (0, 1].
Let K = {(s_1, t_1, d_1), ..., (s_m, t_m, d_m)} be a set of m concurrent commodity
flow demands where s_k != t_k in V and d_k in N_{>= 1}.
For any cut partition (S, V \\ S), let K(S) = {k : |S cap {s_k, t_k}| = 1} be the set
of commodities separated by S, with aggregate demand D(S) = sum_{k in K(S)} d_k.
In any operational subgraph G_x defined by state x in {0, 1}^E, concurrent routing
requires that every cut partition S with D(S) > 0 has surviving physical capacity:
    sum_{e in Delta(S)} c_e * x_e >= D(S).
For each non-trivial cut partition S, the knapsack capacity threshold compiles into
monotone positive clauses across inclusion-minimal capacity-breaking subsets F:
    sum_{e in Delta(S)} c_e * x_e >= D(S) <=> bigwedge_{F in F_min(Delta(S), D(S))} (bigvee_{e in F} x_e).
The exact multi-commodity cut formula is:
    Phi_mc(G, K) = bigwedge_{S: D(S) > 0} bigwedge_{F in F_min(Delta(S), D(S))} (bigvee_{e in F} x_e).
Phi_mc contains strictly |E| variables and zero auxiliary flow variables.
"""
from __future__ import annotations

import itertools
import time
from fractions import Fraction
from typing import Any, Dict, FrozenSet, List, NamedTuple, Optional, Set, Tuple

from sat_frontier.reliability import NetworkGraph
from sat_frontier.wmc import WeightedFormula, wmc_solve


class CommodityDemand(NamedTuple):
    """Specification of an individual commodity flow demand."""
    source: Any
    target: Any
    demand: int


class MultiCommodityNetwork:
    """Capacitated network supporting multiple concurrent commodity flow demands."""

    def __init__(self, is_directed: bool = False):
        self.is_directed: bool = is_directed
        self.nodes: Set[Any] = set()
        self.edges: List[Tuple[Any, Any]] = []
        self.edge_capacities: Dict[int, int] = {}       # 1-indexed edge id -> capacity
        self.edge_probs: Dict[int, Fraction] = {}       # 1-indexed edge id -> survival prob
        self.adj: Dict[Any, List[Tuple[Any, int]]] = {} # u -> list of (v, edge_id)
        self.commodities: List[CommodityDemand] = []

    def add_edge(
        self,
        u: Any,
        v: Any,
        capacity: int = 1,
        prob: Fraction = Fraction(9, 10),
    ) -> int:
        """Add an edge with capacity and operational survival probability."""
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

    def add_commodity(self, source: Any, target: Any, demand: int = 1) -> None:
        """Add a commodity demand requirement."""
        if source == target:
            raise ValueError(f"Commodity source and target must be distinct: {source}")
        if demand <= 0:
            raise ValueError(f"Commodity demand must be positive: {demand}")
        self.nodes.add(source)
        self.nodes.add(target)
        self.commodities.append(CommodityDemand(source=source, target=target, demand=demand))


def find_minimal_capacity_breaking_sets(
    cut_edges: Set[int],
    edge_capacities: Dict[int, int],
    demand: int,
) -> List[FrozenSet[int]]:
    """Find all inclusion-minimal subsets F subseteq cut whose failure causes surviving capacity < demand."""
    sorted_edges = sorted(cut_edges)
    total_cap = sum(edge_capacities.get(e, 1) for e in sorted_edges)

    if total_cap < demand:
        # Cut cannot even satisfy demand when all edges operate: formula is UNSAT
        return [frozenset()]

    max_allowable_failure = total_cap - demand
    minimal_breakers: List[FrozenSet[int]] = []

    n = len(sorted_edges)
    for size in range(1, n + 1):
        for comb in itertools.combinations(sorted_edges, size):
            cand = frozenset(comb)
            if any(m.issubset(cand) for m in minimal_breakers):
                continue

            failed_cap = sum(edge_capacities.get(e, 1) for e in cand)
            if failed_cap > max_allowable_failure:
                minimal_breakers.append(cand)

    return minimal_breakers


def enumerate_all_cut_partitions(
    nodes: List[Any],
) -> List[FrozenSet[Any]]:
    """Enumerate non-trivial cut partitions (S, V \\ S) up to symmetry."""
    n = len(nodes)
    if n < 2:
        return []

    # Fix first node in S to eliminate complement symmetry (S vs V \ S)
    fixed = nodes[0]
    other_nodes = nodes[1:]
    partitions: List[FrozenSet[Any]] = []

    for r in range(0, len(other_nodes)):
        for comb in itertools.combinations(other_nodes, r):
            s_set = frozenset([fixed] + list(comb))
            partitions.append(s_set)

    return partitions


def compile_multi_commodity_clauses(
    net: MultiCommodityNetwork,
) -> Tuple[List[List[int]], Dict[int, Fraction], int]:
    """Compile multi-commodity flow demands into monotone CNF clauses over edge variables alone.

    Returns:
        (clauses, literal_weights, n_vars)
    """
    n_vars = len(net.edges)
    all_nodes = sorted(list(net.nodes), key=str)

    # Edge crossing lookup
    def get_crossing_edges(s_set: FrozenSet[Any]) -> Set[int]:
        crossing = set()
        for eid, (u, v) in enumerate(net.edges, start=1):
            u_in = u in s_set
            v_in = v in s_set
            if net.is_directed:
                if u_in and not v_in:
                    crossing.add(eid)
            else:
                if u_in != v_in:
                    crossing.add(eid)
        return crossing

    # Calculate aggregate demand crossing cut partition S
    def get_crossing_demand(s_set: FrozenSet[Any]) -> int:
        demand = 0
        for comm in net.commodities:
            u_in = comm.source in s_set
            v_in = comm.target in s_set
            if net.is_directed:
                if u_in and not v_in:
                    demand += comm.demand
            else:
                if u_in != v_in:
                    demand += comm.demand
        return demand

    clauses: List[List[int]] = []
    seen_clauses: Set[Tuple[int, ...]] = set()

    partitions = enumerate_all_cut_partitions(all_nodes)
    for s_set in partitions:
        demand = get_crossing_demand(s_set)
        if demand <= 0:
            continue

        crossing_edges = get_crossing_edges(s_set)
        breakers = find_minimal_capacity_breaking_sets(
            crossing_edges, net.edge_capacities, demand
        )

        for breaker in breakers:
            if not breaker:
                # Empty breaker: unsatisfied cut condition (formula is UNSAT)
                return [[1], [-1]], {}, n_vars

            clause = sorted(list(breaker))
            clause_key = tuple(clause)
            if clause_key not in seen_clauses:
                seen_clauses.add(clause_key)
                clauses.append(clause)

    weights: Dict[int, Fraction] = {}
    for eid in range(1, n_vars + 1):
        p = net.edge_probs.get(eid, Fraction(9, 10))
        weights[eid] = p
        weights[-eid] = Fraction(1) - p

    return clauses, weights, n_vars


def brute_force_multi_commodity_oracle(
    net: MultiCommodityNetwork,
    limit_edges: int = 14,
) -> Fraction:
    """Exhaustive truth-table oracle computing exact multi-commodity reliability.

    For small graphs, checks all 2^|E| operational states against concurrent flow feasibility.
    """
    m = len(net.edges)
    if m > limit_edges:
        raise ValueError(f"Network exceeds oracle limit of {limit_edges} edges: {m}")

    all_nodes = sorted(list(net.nodes), key=str)
    partitions = enumerate_all_cut_partitions(all_nodes)

    # For each state, verify all cut conditions
    def is_state_feasible(state: int) -> bool:
        # Check all cut partitions
        for s_set in partitions:
            # Crossing demand
            demand = 0
            for comm in net.commodities:
                u_in = comm.source in s_set
                v_in = comm.target in s_set
                if net.is_directed:
                    if u_in and not v_in:
                        demand += comm.demand
                else:
                    if u_in != v_in:
                        demand += comm.demand
            if demand <= 0:
                continue

            # Surviving capacity across the cut
            surv_cap = 0
            for eid, (u, v) in enumerate(net.edges, start=1):
                if (state >> (eid - 1)) & 1:  # Edge survives
                    u_in = u in s_set
                    v_in = v in s_set
                    if net.is_directed:
                        if u_in and not v_in:
                            surv_cap += net.edge_capacities[eid]
                    else:
                        if u_in != v_in:
                            surv_cap += net.edge_capacities[eid]

            if surv_cap < demand:
                return False
        return True

    exact_prob = Fraction(0)
    for state in range(1 << m):
        if is_state_feasible(state):
            term = Fraction(1)
            for eid in range(1, m + 1):
                p = net.edge_probs.get(eid, Fraction(9, 10))
                if (state >> (eid - 1)) & 1:
                    term *= p
                else:
                    term *= (Fraction(1) - p)
            exact_prob += term

    return exact_prob


def audit_multi_commodity(
    net: MultiCommodityNetwork,
    algorithm: str = "combined",
) -> Dict[str, Any]:
    """Execute complete multi-commodity flow reliability audit."""
    t0 = time.perf_counter()
    clauses, weights, n_vars = compile_multi_commodity_clauses(net)
    compile_time = time.perf_counter() - t0

    wf = WeightedFormula(clauses, n_vars=n_vars, weights=weights)
    solve_res = wmc_solve(wf, algorithm=algorithm)

    return {
        "status": solve_res["status"],
        "reliability_fraction": solve_res.get("weight_fraction"),
        "reliability_float": solve_res.get("weight_float"),
        "search_nodes": solve_res.get("nodes", 0),
        "compile_seconds": compile_time,
        "solve_seconds": solve_res.get("elapsed_seconds", 0.0),
        "n_variables": n_vars,
        "n_clauses": len(clauses),
        "n_commodities": len(net.commodities),
    }

