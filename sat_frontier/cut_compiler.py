"""Dual Cut-based CNF compilation for Two-Terminal Network Reliability.

Compiles network connectivity directly over minimal s-t cuts without auxiliary
path indicators:
    Connected(s, t) <=> \\bigwedge_{C in Cuts} (\\bigvee_{e in C} e)
Yields compact monotone CNF on the edge variables alone.
"""
from fractions import Fraction
from itertools import combinations
from .reliability import NetworkGraph
from .wmc import WeightedFormula


def find_all_minimal_cuts(net: NetworkGraph, source, target):
    """Find all inclusion-minimal s-t edge cuts in an undirected NetworkGraph."""
    all_nodes = list(net.adj.keys())
    intermediate_nodes = [n for n in all_nodes if n != source and n != target]
    raw_cuts = set()

    for r in range(len(intermediate_nodes) + 1):
        for subset in combinations(intermediate_nodes, r):
            s_set = set(subset) | {source}
            t_set = set(all_nodes) - s_set
            cut_edges = []
            for u, v in net.edges:
                if (u in s_set and v in t_set) or (v in s_set and u in t_set):
                    for neighbor, eid in net.adj[u]:
                        if neighbor == v:
                            cut_edges.append(eid)
                            break
            if cut_edges:
                raw_cuts.add(tuple(sorted(cut_edges)))

    minimal_cuts = []
    for c in raw_cuts:
        c_set = set(c)
        if not any(set(other) < c_set for other in raw_cuts):
            minimal_cuts.append(c)
    return sorted(set(minimal_cuts))


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
