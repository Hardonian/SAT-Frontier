"""Dual Mixed-Cut Monotone CNF Compilation for Mixed Node-and-Edge Reliability.

Compiles network connectivity under simultaneous, independent node and edge failures
into compact monotone CNF over physical node and edge variables alone:
    Connected(s, t) <=> \\bigwedge_{(V_C, E_C) in MinMixedCuts(s, t)} (\\bigvee_{v in V_C} y_v \\lor \\bigvee_{e in E_C} x_e)
Eliminates all auxiliary path variables and flow constraints via node-splitting dicut projection.
"""
from collections import deque
from fractions import Fraction
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from .dicut_compiler import DirectedNetworkGraph, find_all_minimal_dicuts
from .wmc import WeightedFormula


class MixedNetworkGraph:
    """Network topology with independent vertex and edge operational probabilities."""

    def __init__(self, is_directed: bool = False):
        self.is_directed: bool = is_directed
        self.nodes: Set[Any] = set()
        self.edges: List[Tuple[Any, Any]] = []  # 1-indexed (u, v)
        self.node_probs: Dict[Any, Fraction] = {}
        self.edge_probs: Dict[int, Fraction] = {}
        self.adj: Dict[Any, List[Tuple[Any, int]]] = {}

    def add_node(self, node: Any, prob: Fraction = Fraction(1, 1)) -> None:
        """Add a node with operational probability prob."""
        if node not in self.nodes:
            self.nodes.add(node)
            self.adj[node] = []
        self.node_probs[node] = Fraction(prob)

    def add_edge(self, u: Any, v: Any, prob: Fraction = Fraction(9, 10)) -> int:
        """Add an edge between u and v with operational probability prob."""
        if u not in self.nodes:
            self.add_node(u)
        if v not in self.nodes:
            self.add_node(v)
        eid = len(self.edges) + 1
        self.edges.append((u, v))
        self.edge_probs[eid] = Fraction(prob)
        self.adj[u].append((v, eid))
        if not self.is_directed:
            self.adj[v].append((u, eid))
        return eid


def to_split_graph(
    net: MixedNetworkGraph, s: Any, t: Any
) -> Tuple[DirectedNetworkGraph, Dict[int, int], Dict[int, Fraction], List[Any]]:
    """Transform a MixedNetworkGraph into an augmented DirectedNetworkGraph via node-splitting.

    Returns:
        (dnet, arc_to_var, var_weights, internal_nodes)
    """
    dnet = DirectedNetworkGraph()
    arc_to_var: Dict[int, int] = {}
    var_weights: Dict[int, Fraction] = {}

    internal_nodes = sorted([v for v in net.nodes if v != s and v != t], key=str)
    m_nodes = len(internal_nodes)
    m_edges = len(net.edges)

    # 1. Internal node variables: 1 .. m_nodes
    node_to_var: Dict[Any, int] = {}
    for i, v in enumerate(internal_nodes, 1):
        node_to_var[v] = i
        p_node = net.node_probs.get(v, Fraction(1, 1))
        var_weights[i] = p_node
        arc_id = dnet.add_edge(f"{v}_in", f"{v}_out", p_node)
        arc_to_var[arc_id] = i

    # 2. Edge variables: m_nodes + 1 .. m_nodes + m_edges
    for j, (u, v) in enumerate(net.edges, 1):
        var_id = m_nodes + j
        p_edge = net.edge_probs.get(j, Fraction(9, 10))
        var_weights[var_id] = p_edge

        u_out = f"{u}_out" if u in node_to_var else u
        u_in = f"{u}_in" if u in node_to_var else u
        v_out = f"{v}_out" if v in node_to_var else v
        v_in = f"{v}_in" if v in node_to_var else v

        # Forward arc
        a_fwd = dnet.add_edge(u_out, v_in, p_edge)
        arc_to_var[a_fwd] = var_id

        # Backward arc if undirected
        if not net.is_directed:
            a_bwd = dnet.add_edge(v_out, u_in, p_edge)
            arc_to_var[a_bwd] = var_id

    return dnet, arc_to_var, var_weights, internal_nodes


def find_all_minimal_mixed_cuts(
    net: MixedNetworkGraph, s: Any, t: Any
) -> List[Tuple[int, ...]]:
    """Enumerate all inclusion-minimal mixed (vertex and edge) cuts separating s and t.

    Uses node-splitting dicut projection and eliminates subsumed physical cuts.
    """
    if s == t:
        return []

    if s not in net.nodes or t not in net.nodes:
        return [()]

    dnet, arc_to_var, _, _ = to_split_graph(net, s, t)
    raw_dicuts = find_all_minimal_dicuts(dnet, s, t)

    if not raw_dicuts:
        return []
    if () in raw_dicuts or [] in raw_dicuts:
        return [()]

    # Map directed arcs in each dicut back to physical variable IDs
    physical_cuts = set()
    for cut in raw_dicuts:
        phys = tuple(sorted(set(arc_to_var[arc_id] for arc_id in cut)))
        if phys:
            physical_cuts.add(phys)

    # Filter strictly inclusion-minimal physical cuts
    min_physical_cuts = []
    for c in physical_cuts:
        if not any(set(other) < set(c) for other in physical_cuts if other != c):
            min_physical_cuts.append(c)

    return sorted(min_physical_cuts)


def to_mixed_cut_cnf(
    net: MixedNetworkGraph, s: Any, t: Any
) -> WeightedFormula:
    """Compile mixed network reliability into a dual mixed-cut WeightedFormula."""
    if s == t:
        return WeightedFormula([], n_vars=0, weights={})

    if s not in net.nodes or t not in net.nodes:
        return WeightedFormula([[1], [-1]], n_vars=1)

    min_cuts = find_all_minimal_mixed_cuts(net, s, t)
    if not min_cuts or () in min_cuts or [] in min_cuts:
        return WeightedFormula([[1], [-1]], n_vars=1)

    dnet, arc_to_var, var_weights, internal_nodes = to_split_graph(net, s, t)
    n_vars = len(var_weights)

    weights: Dict[int, Fraction] = {}
    for var_id, p in var_weights.items():
        weights[var_id] = p
        weights[-var_id] = Fraction(1) - p

    clauses = [list(c) for c in min_cuts]

    # If source or target themselves have failure probability < 1, add unit clauses
    q_s = net.node_probs.get(s, Fraction(1, 1))
    q_t = net.node_probs.get(t, Fraction(1, 1))

    # Note: If terminal failure is modeled directly, terminal variables can be included.
    # By convention in network reliability, s and t operational probability factorizes:
    # R_total = q_s * q_t * R(s-t | s,t operational).
    return WeightedFormula(clauses, n_vars=n_vars, weights=weights)


def brute_force_mixed_oracle(
    net: MixedNetworkGraph, s: Any, t: Any
) -> Fraction:
    """Independent exhaustive state-space enumeration oracle for mixed node-and-edge reliability.

    Iterates over all 2^(|V_internal| + |E|) operational states and sums the exact rational probability
    of all states where an operational s-t path exists.
    """
    if s == t:
        return Fraction(1)
    if s not in net.nodes or t not in net.nodes:
        return Fraction(0)

    internal_nodes = sorted([v for v in net.nodes if v != s and v != t], key=str)
    edges = list(net.edges)

    m_nodes = len(internal_nodes)
    m_edges = len(edges)
    total_bits = m_nodes + m_edges

    node_p = [net.node_probs.get(v, Fraction(1, 1)) for v in internal_nodes]
    edge_p = [net.edge_probs.get(i + 1, Fraction(9, 10)) for i in range(m_edges)]

    total_prob = Fraction(0)

    for mask in range(1 << total_bits):
        active_nodes = {s, t}
        state_prob = Fraction(1)

        # Node operational states
        for i, v in enumerate(internal_nodes):
            if mask & (1 << i):
                active_nodes.add(v)
                state_prob *= node_p[i]
            else:
                state_prob *= (Fraction(1) - node_p[i])

        # Edge operational states
        active_edges = []
        for j, (u, v) in enumerate(edges):
            if mask & (1 << (m_nodes + j)):
                active_edges.append((u, v))
                state_prob *= edge_p[j]
            else:
                state_prob *= (Fraction(1) - edge_p[j])

        # Check connectivity in active subgraph
        adj = {u: [] for u in active_nodes}
        for u, v in active_edges:
            if u in active_nodes and v in active_nodes:
                adj[u].append(v)
                if not net.is_directed:
                    adj[v].append(u)

        vis = {s}
        q = deque([s])
        while q:
            curr = q.popleft()
            for nbr in adj.get(curr, []):
                if nbr not in vis:
                    vis.add(nbr)
                    q.append(nbr)

        if t in vis:
            total_prob += state_prob

    # Account for terminal operational probabilities
    q_s = net.node_probs.get(s, Fraction(1, 1))
    q_t = net.node_probs.get(t, Fraction(1, 1))
    return q_s * q_t * total_prob

