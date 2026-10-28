"""Network Reliability and Fault Tree compiler to Weighted CNF."""
from fractions import Fraction
from .wmc import WeightedFormula


class NetworkGraph:
    """Network topology where edges have independent operational probabilities."""

    def __init__(self):
        self.adj = {}
        self.edges = []
        self.edge_probs = {}

    def add_edge(self, u, v, prob):
        """Add undirected edge with operational probability prob in [0, 1]."""
        u, v = min(u, v), max(u, v)
        edge_id = len(self.edges) + 1  # 1-based edge index
        self.edges.append((u, v))
        self.edge_probs[edge_id] = Fraction(prob) if not isinstance(prob, Fraction) else prob

        if u not in self.adj:
            self.adj[u] = []
        if v not in self.adj:
            self.adj[v] = []
        self.adj[u].append((v, edge_id))
        self.adj[v].append((u, edge_id))

    def find_all_simple_paths(self, source, target):
        """Find all elementary simple paths (as lists of edge IDs) from source to target."""
        all_paths = []

        def dfs(curr, visited_nodes, curr_path_edges):
            if curr == target:
                all_paths.append(list(curr_path_edges))
                return
            for nxt, edge_id in self.adj.get(curr, []):
                if nxt not in visited_nodes:
                    visited_nodes.add(nxt)
                    curr_path_edges.append(edge_id)
                    dfs(nxt, visited_nodes, curr_path_edges)
                    curr_path_edges.pop()
                    visited_nodes.remove(nxt)

        dfs(source, {source}, [])
        return all_paths

    def to_weighted_cnf(self, source, target, modular=True):
        """Compile two-terminal connectivity into an exact probability-preserving WeightedFormula."""
        paths = self.find_all_simple_paths(source, target)
        if not paths:
            # No path exists: 0 probability (unsatisfiable formula)
            return WeightedFormula([[1], [-1]], n_vars=1)

        num_edges = len(self.edges)
        clauses = []
        weights = {}

        # 1. Edge variables: 1 .. num_edges
        for e_id in range(1, num_edges + 1):
            p = self.edge_probs[e_id]
            weights[e_id] = p
            weights[-e_id] = Fraction(1) - p

        next_var = num_edges + 1

        # Check for articulation bridge edges common to all s->t paths
        bridge_edges = set.intersection(*(set(p) for p in paths)) if modular else set()

        if modular and bridge_edges:
            # Select the first bridge edge to partition paths into left and right subpaths
            bridge_edge = sorted(bridge_edges)[0]
            left_paths = []
            right_paths = []
            for p in paths:
                idx = p.index(bridge_edge)
                left_paths.append(tuple(p[:idx]))
                right_paths.append(tuple(p[idx + 1:]))

            left_unique = sorted(set(left_paths))
            right_unique = sorted(set(right_paths))

            left_indicators = []
            for p in left_unique:
                y_i = next_var
                next_var += 1
                left_indicators.append(y_i)
                weights[y_i] = Fraction(1)
                weights[-y_i] = Fraction(1)
                for e_id in p:
                    clauses.append([-y_i, e_id])
                clauses.append([-e_id for e_id in p] + [y_i])

            right_indicators = []
            for p in right_unique:
                y_j = next_var
                next_var += 1
                right_indicators.append(y_j)
                weights[y_j] = Fraction(1)
                weights[-y_j] = Fraction(1)
                for e_id in p:
                    clauses.append([-y_j, e_id])
                clauses.append([-e_id for e_id in p] + [y_j])

            # Top-level operational conditions
            if left_indicators:
                clauses.append(left_indicators)
            clauses.append([bridge_edge])
            if right_indicators:
                clauses.append(right_indicators)

            return WeightedFormula(clauses, n_vars=next_var - 1, weights=weights)

        # Standard flat path encoding when no bridge or modular=False
        path_indicators = []
        for p_idx, path in enumerate(paths):
            y_i = next_var
            next_var += 1
            path_indicators.append(y_i)

            weights[y_i] = Fraction(1)
            weights[-y_i] = Fraction(1)

            for e_id in path:
                clauses.append([-y_i, e_id])
            clauses.append([-e_id for e_id in path] + [y_i])

        clauses.append(path_indicators)
        return WeightedFormula(clauses, n_vars=next_var - 1, weights=weights)

    def find_all_minimal_cuts(self, source, target):
        """Find all minimal (inclusion-minimal) s-t edge cuts."""
        from itertools import combinations
        all_nodes = list(self.adj.keys())
        intermediate_nodes = [n for n in all_nodes if n != source and n != target]
        raw_cuts = set()

        for r in range(len(intermediate_nodes) + 1):
            for subset in combinations(intermediate_nodes, r):
                s_set = set(subset) | {source}
                t_set = set(all_nodes) - s_set
                cut_edges = []
                for u, v in self.edges:
                    if (u in s_set and v in t_set) or (v in s_set and u in t_set):
                        for neighbor, eid in self.adj[u]:
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

    def to_cut_cnf(self, source, target):
        """Compile two-terminal reliability into a dual cut-based monotone WeightedFormula.

        By Max-Flow Min-Cut / Menger's theorem, s is connected to t iff at least
        one edge in every minimal s-t cut is operational:
            Connected(s, t) <=> \\bigwedge_{C in Cuts} (\\bigvee_{e in C} e)
        Eliminates all auxiliary path indicators, operating strictly on the edge variables.
        """
        min_cuts = self.find_all_minimal_cuts(source, target)
        if not min_cuts:
            return WeightedFormula([[1], [-1]], n_vars=1)

        num_edges = len(self.edges)
        weights = {}
        for e in range(1, num_edges + 1):
            p = self.edge_probs[e]
            weights[e] = p
            weights[-e] = Fraction(1) - p

        clauses = [list(c) for c in min_cuts]
        return WeightedFormula(clauses, n_vars=num_edges, weights=weights)


def build_wheatstone_bridge(p=Fraction(9, 10)):
    """Classic 5-edge Wheatstone bridge benchmark between nodes 1 and 4."""
    net = NetworkGraph()
    # Edges:
    # 1: (1, 2)
    # 2: (1, 3)
    # 3: (2, 3) - bridge
    # 4: (2, 4)
    # 5: (3, 4)
    net.add_edge(1, 2, p)
    net.add_edge(1, 3, p)
    net.add_edge(2, 3, p)
    net.add_edge(2, 4, p)
    net.add_edge(3, 4, p)
    return net, 1, 4


def wheatstone_analytic(p):
    """Analytic closed form for identical edge probability on Wheatstone bridge."""
    p = Fraction(p)
    return 2 * (p ** 2) + 2 * (p ** 3) - 5 * (p ** 4) + 2 * (p ** 5)


def build_barbell_network(cluster_size=4, p_cluster=Fraction(95, 100), p_bridge=Fraction(80, 100)):
    """Two dense cluster networks connected by a single critical backbone link."""
    net = NetworkGraph()
    source = 1
    target = 2 * cluster_size

    # Left cluster: 1 .. cluster_size
    for i in range(1, cluster_size + 1):
        for j in range(i + 1, cluster_size + 1):
            net.add_edge(i, j, p_cluster)

    # Right cluster: (cluster_size + 1) .. (2 * cluster_size)
    for i in range(cluster_size + 1, 2 * cluster_size + 1):
        for j in range(i + 1, 2 * cluster_size + 1):
            net.add_edge(i, j, p_cluster)

    # Critical backbone bridge between node cluster_size and node cluster_size + 1
    net.add_edge(cluster_size, cluster_size + 1, p_bridge)

    return net, source, target


def build_grid_network(rows=2, cols=3, p=Fraction(9, 10)):
    """Grid mesh network between top-left (1) and bottom-right (rows * cols)."""
    net = NetworkGraph()
    def node_id(r, c):
        return r * cols + c + 1

    for r in range(rows):
        for c in range(cols):
            u = node_id(r, c)
            if c + 1 < cols:
                net.add_edge(u, node_id(r, c + 1), p)
            if r + 1 < rows:
                net.add_edge(u, node_id(r + 1, c), p)

    return net, node_id(0, 0), node_id(rows - 1, cols - 1)
