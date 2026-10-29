"""Dual K-Cut CNF compilation for Multi-Terminal and All-Terminal Network Reliability.

Compiles generalized K-terminal network connectivity directly over minimal K-cuts
without Steiner tree enumeration or auxiliary variables:
    Connected(K) <=> \\bigwedge_{C in K-Cuts} (\\bigvee_{e in C} e)
Yields compact monotone CNF on the physical edge variables alone.
"""
from collections import deque
from fractions import Fraction
from typing import Any, Iterable, List, Set, Tuple

from .reliability import NetworkGraph
from .wmc import WeightedFormula


def find_all_minimal_k_cuts(net: NetworkGraph, terminals: Iterable[Any]) -> List[Tuple[int, ...]]:
    """Find all inclusion-minimal K-cuts in an undirected NetworkGraph.

    A cut delta(S) is an inclusion-minimal K-cut if and only if:
    1. G[S] is connected;
    2. G[V \\ S] is connected;
    3. S contains at least one terminal in K; and
    4. (V \\ S) contains at least one terminal in K.

    By fixing an arbitrary reference terminal k0 in K and requiring k0 in S,
    every inclusion-minimal K-cut is enumerated exactly once with zero duplicates.
    """
    K: Set[Any] = set(terminals)
    all_nodes: Set[Any] = set(net.adj.keys())

    # If fewer than 2 terminals, the terminal set is vacuously connected
    if len(K) < 2:
        return []

    # If any terminal is not present in the graph, terminals are disconnected
    if not K.issubset(all_nodes):
        return [()]  # Empty clause represents UNSAT (reliability 0)

    adj = {u: [nbr for nbr, _ in net.adj[u]] for u in all_nodes}

    edge_map = {}
    for eid, (u, v) in enumerate(net.edges, 1):
        edge_map[(min(u, v), max(u, v))] = eid

    k0 = min(K)

    # Check if all terminals are reachable from k0 in the full graph G
    q_check = deque([k0])
    visited_check = {k0}
    while q_check:
        curr = q_check.popleft()
        for nbr in adj[curr]:
            if nbr not in visited_check:
                visited_check.add(nbr)
                q_check.append(nbr)
    if not K.issubset(visited_check):
        return [()]  # Terminals disconnected in G itself: UNSAT

    cuts = set()

    def is_connected(sub_nodes: Set[Any]) -> bool:
        if not sub_nodes:
            return False
        start = next(iter(sub_nodes))
        visited = {start}
        q = deque([start])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v in sub_nodes and v not in visited:
                    visited.add(v)
                    q.append(v)
        return len(visited) == len(sub_nodes)

    def search(S: Set[Any], frontier: Set[Any], forbidden: Set[Any]):
        T = all_nodes - S
        # Pruning condition: if T has no terminals from K, no further S-expansion will yield terminals in T
        if not (T & K):
            return

        if is_connected(T):
            cut_edges = []
            for u in S:
                for v in adj[u]:
                    if v in T:
                        cut_edges.append(edge_map[(min(u, v), max(u, v))])
            cuts.add(tuple(sorted(cut_edges)))

        cur_forbidden = set(forbidden)
        for u in sorted(frontier):
            cur_forbidden.add(u)
            new_frontier = (frontier - {u} - cur_forbidden) | (
                set(adj[u]) - S - cur_forbidden
            )
            search(S | {u}, new_frontier, cur_forbidden)

    initial_frontier = set(adj[k0])
    search({k0}, initial_frontier, set())
    return sorted(cuts)


def to_k_cut_cnf(net: NetworkGraph, terminals: Iterable[Any]) -> WeightedFormula:
    """Compile multi-terminal reliability into a dual K-cut based monotone WeightedFormula."""
    min_cuts = find_all_minimal_k_cuts(net, terminals)
    if not min_cuts:
        # If no cuts exist (e.g. |K| < 2), formula is tautology
        return WeightedFormula([], n_vars=len(net.edges))

    if () in min_cuts or [] in min_cuts:
        # Empty cut clause indicates terminals are disconnected (UNSAT)
        return WeightedFormula([[1], [-1]], n_vars=1)

    num_edges = len(net.edges)
    weights = {}
    for e in range(1, num_edges + 1):
        p = net.edge_probs[e]
        weights[e] = p
        weights[-e] = Fraction(1) - p

    clauses = [list(c) for c in min_cuts]
    return WeightedFormula(clauses, n_vars=num_edges, weights=weights)


def brute_force_k_terminal_oracle(net: NetworkGraph, terminals: Iterable[Any]) -> Fraction:
    """Independent exhaustive oracle for K-terminal reliability.

    Iterates over all 2^|E| subgraphs and sums the exact rational probability
    of all operational states where all vertices in K remain mutually connected.
    """
    K = set(terminals)
    all_nodes = set(net.adj.keys())
    if len(K) < 2:
        return Fraction(1)
    if not K.issubset(all_nodes):
        return Fraction(0)

    edges = list(net.edges)
    m = len(edges)
    probs = [net.edge_probs[i + 1] for i in range(m)]

    total_prob = Fraction(0)
    k0 = min(K)

    for mask in range(1 << m):
        active_edges = [edges[i] for i in range(m) if (mask & (1 << i))]
        state_prob = Fraction(1)
        for i in range(m):
            if mask & (1 << i):
                state_prob *= probs[i]
            else:
                state_prob *= (Fraction(1) - probs[i])

        adj_sub = {u: [] for u in all_nodes}
        for u, v in active_edges:
            adj_sub[u].append(v)
            adj_sub[v].append(u)

        visited = {k0}
        q = deque([k0])
        while q:
            u = q.popleft()
            for v in adj_sub[u]:
                if v not in visited:
                    visited.add(v)
                    q.append(v)

        if K.issubset(visited):
            total_prob += state_prob

    return total_prob

