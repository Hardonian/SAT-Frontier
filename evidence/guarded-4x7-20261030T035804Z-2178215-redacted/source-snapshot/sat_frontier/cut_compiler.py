"""Dual Cut-based CNF compilation for Two-Terminal Network Reliability.

Compiles network connectivity directly over minimal s-t cuts without auxiliary
path indicators:
    Connected(s, t) <=> \\bigwedge_{C in Cuts} (\\bigvee_{e in C} e)
Yields compact monotone CNF on the edge variables alone.
"""
from collections import deque
from fractions import Fraction
from .reliability import NetworkGraph
from .wmc import WeightedFormula


def find_all_minimal_cuts(net: NetworkGraph, source, target):
    """Find all inclusion-minimal s-t edge cuts in an undirected NetworkGraph.

    By Menger's theorem / graph connectivity, an edge cut delta(S) separating source
    from target is inclusion-minimal if and only if both G[S] and G[V \\ S] are
    connected subgraphs. Enumerates connected subsets S containing source and excluding
    target via canonical frontier expansion without generating disconnected partitions.
    """
    all_nodes = set(net.adj.keys())
    adj = {u: [nbr for nbr, _ in net.adj[u]] for u in all_nodes}

    edge_map = {}
    for eid, (u, v) in enumerate(net.edges, 1):
        edge_map[(min(u, v), max(u, v))] = eid

    def is_connected_target(t_set):
        if target not in t_set:
            return False
        visited = {target}
        q = deque([target])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v in t_set and v not in visited:
                    visited.add(v)
                    q.append(v)
        return len(visited) == len(t_set)

    cuts = set()

    def search(S, frontier, forbidden):
        t_set = all_nodes - S
        if is_connected_target(t_set):
            cut_edges = []
            for u in S:
                for v in adj[u]:
                    if v in t_set:
                        cut_edges.append(edge_map[(min(u, v), max(u, v))])
            cuts.add(tuple(sorted(cut_edges)))

        cur_forbidden = set(forbidden)
        for u in sorted(frontier):
            cur_forbidden.add(u)
            new_frontier = (frontier - {u} - cur_forbidden) | (
                set(adj[u]) - S - cur_forbidden - {target}
            )
            search(S | {u}, new_frontier, cur_forbidden)

    initial_frontier = set(adj[source]) - {target}
    search({source}, initial_frontier, set())
    return sorted(cuts)


def to_cut_cnf(net: NetworkGraph, source, target):
    """Compile two-terminal reliability into a dual cut-based monotone WeightedFormula."""
    min_cuts = find_all_minimal_cuts(net, source, target)
    if not min_cuts:
        return WeightedFormula([[1], [-1]], n_vars=1)

    num_edges = len(net.edges)
    weights = {}
    for e in range(1, num_edges + 1):
        p = net.edge_probs[e]
        weights[e] = p
        weights[-e] = Fraction(1) - p

    clauses = [list(c) for c in min_cuts]
    return WeightedFormula(clauses, n_vars=num_edges, weights=weights)

