"""Dual Directed Cut (Dicut) CNF Compilation for Directed Network Reliability (s ~> t).

Compiles directed two-terminal reachability directly over minimal directed cuts (dicuts)
without path enumeration, MTZ subtour elimination variables, or auxiliary indicators:
    Reach(s, t) <=> \\bigwedge_{C in MinDicuts(s, t)} (\\bigvee_{e in C} x_e)
Yields compact monotone CNF on the physical directed arc variables alone.
"""
from collections import deque
from fractions import Fraction
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from .wmc import WeightedFormula


class DirectedNetworkGraph:
    """Directed network topology with independent arc operational probabilities."""

    def __init__(self):
        self.nodes: Set[Any] = set()
        self.edges: List[Tuple[Any, Any]] = []  # 1-indexed list of (u, v) arcs
        self.edge_probs: Dict[int, Fraction] = {}
        self.adj: Dict[Any, List[Tuple[Any, int]]] = {}  # u -> list of (v, eid)
        self.rev_adj: Dict[Any, List[Tuple[Any, int]]] = {}  # v -> list of (u, eid)

    def add_node(self, node: Any) -> None:
        if node not in self.nodes:
            self.nodes.add(node)
            self.adj[node] = []
            self.rev_adj[node] = []

    def add_edge(self, u: Any, v: Any, prob: Fraction = Fraction(9, 10)) -> int:
        """Add a directed arc from u to v with operational probability prob."""
        self.add_node(u)
        self.add_node(v)
        eid = len(self.edges) + 1
        self.edges.append((u, v))
        self.edge_probs[eid] = Fraction(prob)
        self.adj[u].append((v, eid))
        self.rev_adj[v].append((u, eid))
        return eid


def prune_directed_graph(
    net: DirectedNetworkGraph, s: Any, t: Any
) -> Tuple[DirectedNetworkGraph, bool]:
    """Prune nodes and arcs that cannot lie on any directed path from s to t.

    Returns:
        (pruned_net, is_connected)
    """
    if s not in net.nodes or t not in net.nodes:
        return net, False

    # 1. Forward reachability from s
    q_fwd = deque([s])
    vis_fwd = {s}
    while q_fwd:
        curr = q_fwd.popleft()
        for nbr, _ in net.adj.get(curr, []):
            if nbr not in vis_fwd:
                vis_fwd.add(nbr)
                q_fwd.append(nbr)

    if t not in vis_fwd:
        return net, False

    # 2. Backward reachability from t
    q_bwd = deque([t])
    vis_bwd = {t}
    while q_bwd:
        curr = q_bwd.popleft()
        for nbr, _ in net.rev_adj.get(curr, []):
            if nbr not in vis_bwd:
                vis_bwd.add(nbr)
                q_bwd.append(nbr)

    relevant_nodes = vis_fwd & vis_bwd
    pruned = DirectedNetworkGraph()
    for n in relevant_nodes:
        pruned.add_node(n)

    # Re-insert only arcs connecting relevant nodes
    for eid, (u, v) in enumerate(net.edges, 1):
        if u in relevant_nodes and v in relevant_nodes:
            p = net.edge_probs[eid]
            pruned.add_edge(u, v, p)

    return pruned, True


def find_all_minimal_dicuts(
    net: DirectedNetworkGraph, s: Any, t: Any
) -> List[Tuple[int, ...]]:
    """Find all inclusion-minimal directed s-t cuts (dicuts) in net.

    An arc cut delta+(S) with s in S and t not in S is an inclusion-minimal dicut iff:
    1. Every vertex u in S is reachable from s in the induced subgraph D[S]; and
    2. For every arc (u, v) in delta+(S), the target node v can reach t in D[V \\ S].

    Uses a branch-and-bound search over valid reachability sets S.
    """
    if s == t:
        return []

    if s not in net.nodes or t not in net.nodes:
        return [()]  # Empty clause: UNSAT (disconnected)

    # Quick reachability check
    q = deque([s])
    visited = {s}
    while q:
        curr = q.popleft()
        for nbr, _ in net.adj.get(curr, []):
            if nbr not in visited:
                visited.add(nbr)
                q.append(nbr)
    if t not in visited:
        return [()]  # Disconnected in full graph: UNSAT

    all_nodes = set(net.nodes)
    adj_out = {u: [v for v, _ in net.adj.get(u, [])] for u in all_nodes}

    edge_map = {}
    for eid, (u, v) in enumerate(net.edges, 1):
        edge_map[(u, v)] = eid

    cuts = set()

    def search(S: Set[Any], frontier: Set[Any], forbidden: Set[Any]):
        T = all_nodes - S
        if t in S:
            return

        # 1. Compute forward cut edges delta+(S) and target nodes in T
        cut_edge_ids = []
        target_nodes = set()
        for u in S:
            for v in adj_out[u]:
                if v in T:
                    cut_edge_ids.append(edge_map[(u, v)])
                    target_nodes.add(v)

        if not cut_edge_ids:
            return

        # 2. Check if all target_nodes can reach t in D[T]
        adj_T_rev = {v: [] for v in T}
        for u, v in net.edges:
            if u in T and v in T:
                adj_T_rev[v].append(u)

        vis_t = {t}
        q_t = deque([t])
        while q_t:
            curr = q_t.popleft()
            for nbr in adj_T_rev[curr]:
                if nbr not in vis_t:
                    vis_t.add(nbr)
                    q_t.append(nbr)

        if all(v in vis_t for v in target_nodes):
            cuts.add(tuple(sorted(cut_edge_ids)))

        # 3. Branch: expand S by adding nodes from frontier (excluding t)
        cur_forbidden = set(forbidden)
        for u in sorted(frontier - {t}):
            cur_forbidden.add(u)
            new_S = S | {u}
            new_frontier = (frontier - {u} - cur_forbidden) | (
                set(adj_out[u]) - new_S - cur_forbidden
            )
            search(new_S, new_frontier, cur_forbidden)

    initial_frontier = set(adj_out[s])
    search({s}, initial_frontier, set())
    return sorted(cuts)


def to_dicut_cnf(
    net: DirectedNetworkGraph, s: Any, t: Any
) -> WeightedFormula:
    """Compile directed two-terminal reachability into a dual dicut-based WeightedFormula."""
    if s == t:
        # Vacuously connected: return tautology with weight 1
        return WeightedFormula([], n_vars=0, weights={})

    min_cuts = find_all_minimal_dicuts(net, s, t)
    num_edges = len(net.edges)

    if not min_cuts or () in min_cuts or [] in min_cuts:
        # Empty cut clause or no path: UNSAT (reliability 0)
        return WeightedFormula([[1], [-1]], n_vars=1)

    weights = {}
    for e in range(1, num_edges + 1):
        p = net.edge_probs[e]
        weights[e] = p
        weights[-e] = Fraction(1) - p

    clauses = [list(c) for c in min_cuts]
    return WeightedFormula(clauses, n_vars=num_edges, weights=weights)


def brute_force_directed_oracle(
    net: DirectedNetworkGraph, s: Any, t: Any
) -> Fraction:
    """Independent exhaustive oracle for directed two-terminal reachability.

    Iterates over all 2^|A| operational subgraphs and sums the exact rational probability
    of all states where a directed path from s to t exists.
    """
    if s == t:
        return Fraction(1)
    if s not in net.nodes or t not in net.nodes:
        return Fraction(0)

    edges = list(net.edges)
    m = len(edges)
    probs = [net.edge_probs[i + 1] for i in range(m)]

    total_prob = Fraction(0)

    for mask in range(1 << m):
        active_edges = [edges[i] for i in range(m) if (mask & (1 << i))]
        state_prob = Fraction(1)
        for i in range(m):
            if mask & (1 << i):
                state_prob *= probs[i]
            else:
                state_prob *= (Fraction(1) - probs[i])

        adj_sub = {u: [] for u in net.nodes}
        for u, v in active_edges:
            adj_sub[u].append(v)

        visited = {s}
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj_sub[u]:
                if v not in visited:
                    visited.add(v)
                    q.append(v)

        if t in visited:
            total_prob += state_prob

    return total_prob
