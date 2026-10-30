"""Bounded-Diameter / Latency-Constrained Network Reliability Compiler.

Hypothesis H17:
Dual Length-Bounded Cut Monotone CNF Compilation encodes exact bounded-hop / latency-constrained
reliability P(dist_{G_x}(s, t) <= L) with strictly |E| variables and zero auxiliary variables.

Theorem (Dual L-Hop Cut Duality):
Let G = (V, E) be a network where each edge e in E has operational probability p_e in (0, 1].
Let L >= 1 be the maximum allowable hop count (latency deadline).
An operational path of length <= L connects s and t in G_x if and only if every
inclusion-minimal L-hop cut C in C_min(s, t, L) contains at least one operational edge:
    dist_{G_x}(s, t) <= L  <=>  bigwedge_{C in C_min(s, t, L)} (bigvee_{e in C} x_e) = 1.
Phi_L contains strictly |E| Boolean variables and zero auxiliary variables.
"""
from __future__ import annotations

import collections
import itertools
import time
from fractions import Fraction
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from sat_frontier.reliability import NetworkGraph
from sat_frontier.wmc import WeightedFormula, wmc_solve


def find_all_bounded_paths(
    net: NetworkGraph,
    source: Any,
    target: Any,
    max_hops: int,
) -> List[List[int]]:
    """Enumerate all simple s-t paths of length <= max_hops.
    
    Returns a list of paths, where each path is a list of 1-indexed edge IDs.
    """
    if source == target:
        return [[]]
    if max_hops <= 0:
        return []

    # Map (min(u, v), max(u, v)) -> list of edge IDs (to handle parallel edges)
    edge_map: Dict[Tuple[Any, Any], List[int]] = collections.defaultdict(list)
    for eid, (u, v) in enumerate(net.edges, 1):
        pair = (min(u, v), max(u, v))
        edge_map[pair].append(eid)

    all_paths: List[List[int]] = []

    def dfs(curr: Any, visited_nodes: Set[Any], current_path_edges: List[int], hops_left: int):
        if curr == target:
            all_paths.append(list(current_path_edges))
            return
        if hops_left <= 0:
            return

        for nbr, _ in net.adj.get(curr, []):
            if nbr not in visited_nodes:
                visited_nodes.add(nbr)
                pair = (min(curr, nbr), max(curr, nbr))
                for eid in edge_map[pair]:
                    current_path_edges.append(eid)
                    dfs(nbr, visited_nodes, current_path_edges, hops_left - 1)
                    current_path_edges.pop()
                visited_nodes.remove(nbr)

    dfs(source, {source}, [], max_hops)
    return all_paths


def find_minimal_bounded_cuts(
    net: NetworkGraph,
    source: Any,
    target: Any,
    max_hops: int,
) -> Set[Tuple[int, ...]]:
    """Find all inclusion-minimal L-hop edge cuts separating source from target within max_hops.
    
    An L-hop cut intersects every simple path of length <= max_hops.
    Minimal L-cuts correspond to the minimal transversals (hitting sets) of the path hypergraph.
    """
    paths = find_all_bounded_paths(net, source, target, max_hops)
    if not paths:
        # No path of length <= max_hops exists in G even if all edges are operational!
        # The empty cut severs all paths of length <= L.
        return {()}

    # Convert paths to frozensets of edge IDs
    path_sets = [frozenset(p) for p in paths]

    # Minimal hitting set search
    # We order edges by frequency in paths for effective pruning
    edge_counts: Dict[int, int] = collections.defaultdict(int)
    for p in path_sets:
        for e in p:
            edge_counts[e] += 1

    sorted_edges = sorted(edge_counts.keys(), key=lambda e: edge_counts[e], reverse=True)

    minimal_cuts: Set[Tuple[int, ...]] = set()

    def search_transversals(
        uncovered_paths: List[FrozenSet[int]],
        current_cut: Set[int],
        edge_idx: int,
    ):
        if not uncovered_paths:
            # All paths covered. Check inclusion-minimality against already found cuts
            # and verify no subset of current_cut also covers all paths.
            cut_tuple = tuple(sorted(current_cut))
            # Test minimality: for every edge e in current_cut, current_cut \ {e} must leave at least one path uncovered
            is_minimal = True
            for e in current_cut:
                reduced = current_cut - {e}
                # If reduced hits every path in path_sets, then current_cut is not minimal!
                if all(bool(p & reduced) for p in path_sets):
                    is_minimal = False
                    break
            if is_minimal:
                minimal_cuts.add(cut_tuple)
            return

        if edge_idx >= len(sorted_edges):
            return

        # Pick the most constrained uncovered path (minimum size)
        target_path = min(uncovered_paths, key=len)

        for e in target_path:
            current_cut.add(e)
            next_uncovered = [p for p in uncovered_paths if e not in p]
            search_transversals(next_uncovered, current_cut, edge_idx + 1)
            current_cut.remove(e)

    search_transversals(path_sets, set(), 0)
    return minimal_cuts


def to_bounded_hop_cnf(
    net: NetworkGraph,
    source: Any,
    target: Any,
    max_hops: int,
) -> Tuple[WeightedFormula, List[List[int]]]:
    """Compile bounded-hop reachability dist(s, t) <= max_hops into a monotone CNF."""
    min_cuts = find_minimal_bounded_cuts(net, source, target, max_hops)

    if () in min_cuts or not min_cuts:
        # Either no operational path of length <= max_hops is topologically possible,
        # or the target is completely unreachable. Return UNSAT formula.
        clauses = [[1], [-1]]
        wf = WeightedFormula(clauses, n_vars=1, weights={1: Fraction(1, 2), -1: Fraction(1, 2)})
        return wf, clauses

    clauses: List[List[int]] = []
    seen: Set[Tuple[int, ...]] = set()

    for cut in sorted(min_cuts):
        if not cut:
            continue
        clause = sorted(cut)
        tup = tuple(clause)
        if tup not in seen:
            seen.add(tup)
            clauses.append(clause)

    weights: Dict[int, Fraction] = {}
    for eid in range(1, len(net.edges) + 1):
        p = net.edge_probs.get(eid, Fraction(9, 10))
        weights[eid] = p
        weights[-eid] = Fraction(1, 1) - p

    wf = WeightedFormula(clauses, n_vars=len(net.edges), weights=weights)
    return wf, clauses


def solve_bounded_hop_reliability(
    net: NetworkGraph,
    source: Any,
    target: Any,
    max_hops: int,
    timeout_seconds: float = 30.0,
    max_nodes: int = 100000,
) -> Tuple[Fraction, int, float]:
    """Compute exact rational probability P(dist(s, t) <= max_hops).
    
    Returns:
        (exact_probability, search_nodes, solve_time_seconds)
    """
    t0 = time.perf_counter()
    wf, clauses = to_bounded_hop_cnf(net, source, target, max_hops)
    res = wmc_solve(wf, algorithm="combined_wmc", seconds=timeout_seconds, max_nodes=max_nodes)
    if res["status"] == "exact":
        return Fraction(res["weight_fraction"]), res["nodes"], time.perf_counter() - t0
    else:
        return Fraction(0), res["nodes"], time.perf_counter() - t0


def brute_force_bounded_hop_oracle(
    net: NetworkGraph,
    source: Any,
    target: Any,
    max_hops: int,
) -> Fraction:
    """Independent oracle for P(dist_{G_x}(s, t) <= max_hops) via BFS over all 2^{|E|} subgraphs."""
    m = len(net.edges)
    edge_probs = [net.edge_probs.get(i, Fraction(9, 10)) for i in range(1, m + 1)]

    # Map 1-indexed edge -> (u, v)
    edges = net.edges
    total_prob = Fraction(0)

    for state in itertools.product([0, 1], repeat=m):
        # Calculate state probability
        state_weight = Fraction(1)
        for i, val in enumerate(state):
            state_weight *= edge_probs[i] if val == 1 else (Fraction(1) - edge_probs[i])

        if state_weight == 0:
            continue

        # Build active subgraph adjacency
        adj = collections.defaultdict(list)
        for i, val in enumerate(state):
            if val == 1:
                u, v = edges[i]
                adj[u].append(v)
                adj[v].append(u)

        # BFS shortest path from source to target
        dist = {source: 0}
        q = collections.deque([source])
        connected = False

        while q:
            curr = q.popleft()
            d = dist[curr]
            if curr == target:
                if d <= max_hops:
                    connected = True
                break
            if d >= max_hops:
                continue
            for nbr in adj[curr]:
                if nbr not in dist:
                    dist[nbr] = d + 1
                    q.append(nbr)

        if connected:
            total_prob += state_weight

    return total_prob

