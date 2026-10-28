"""Unit and metamorphic tests for Dual Cut-Based CNF compilation."""
import unittest
from fractions import Fraction
from itertools import combinations

from sat_frontier.cut_compiler import find_all_minimal_cuts, to_cut_cnf
from sat_frontier.reliability import (
    NetworkGraph,
    build_barbell_network,
    build_grid_network,
    build_wheatstone_bridge,
    wheatstone_analytic,
)
from sat_frontier.wmc import wmc_oracle, wmc_solve


def independent_ground_truth_cuts(net: NetworkGraph, source, target):
    """Exhaustive brute-force baseline finding all inclusion-minimal s-t edge cuts.

    Checks all subsets of edges up to full size to guarantee independent correctness.
    """
    all_nodes = list(net.adj.keys())
    num_edges = len(net.edges)
    edge_map = {}
    for eid, (u, v) in enumerate(net.edges, 1):
        edge_map[eid] = (u, v)

    def is_st_cut(cut_eids):
        removed = set(cut_eids)
        # Check if s and t are connected in G \ cut
        visited = {source}
        queue = [source]
        while queue:
            curr = queue.pop(0)
            if curr == target:
                return False
            for neighbor, eid in net.adj[curr]:
                if eid not in removed and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return True

    all_cuts = []
    # Test all edge subsets in increasing size
    for r in range(1, num_edges + 1):
        for subset in combinations(range(1, num_edges + 1), r):
            if is_st_cut(subset):
                # Check inclusion-minimality against already found smaller cuts
                subset_set = set(subset)
                if not any(set(prior) < subset_set for prior in all_cuts):
                    all_cuts.append(subset)

    return sorted(tuple(sorted(c)) for c in all_cuts)


class CutCompilerTests(unittest.TestCase):

    def test_minimal_cuts_against_brute_force_oracle(self):
        """Verify find_all_minimal_cuts identically matches exhaustive edge-subset oracle."""
        # 1. Wheatstone bridge (5 edges, 4 nodes)
        net_wb, s_wb, t_wb = build_wheatstone_bridge()
        cuts_wb = find_all_minimal_cuts(net_wb, s_wb, t_wb)
        oracle_wb = independent_ground_truth_cuts(net_wb, s_wb, t_wb)
        self.assertEqual(cuts_wb, oracle_wb)
        self.assertEqual(len(cuts_wb), 4)

        # 2. Grid 2x3 (7 edges, 6 nodes)
        net_g, sg, tg = build_grid_network(2, 3)
        cuts_g = find_all_minimal_cuts(net_g, sg, tg)
        oracle_g = independent_ground_truth_cuts(net_g, sg, tg)
        self.assertEqual(cuts_g, oracle_g)
        self.assertEqual(len(cuts_g), 9)

    def test_cut_cnf_matches_wmc_oracle(self):
        """Verify exact probability from to_cut_cnf matches wmc_oracle on small formulas."""
        for p_val in [Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(9, 10)]:
            net, s, t = build_wheatstone_bridge(p=p_val)
            wf_cut = to_cut_cnf(net, s, t)
            oracle_val = wmc_oracle(wf_cut, limit=16)
            analytic_val = wheatstone_analytic(p_val)
            self.assertEqual(oracle_val, analytic_val)

            res = wmc_solve(wf_cut, algorithm="combined_wmc")
            self.assertEqual(res["status"], "exact")
            self.assertEqual(Fraction(res["weight_fraction"]), analytic_val)

    def test_disconnected_terminals_yields_unsat(self):
        """When source and target are in disconnected components, cut CNF has empty cut (UNSAT)."""
        net = NetworkGraph()
        # Component 1: nodes 1-2
        net.add_edge(1, 2, Fraction(9, 10))
        # Component 2: nodes 3-4 (disconnected from 1-2)
        net.add_edge(3, 4, Fraction(9, 10))

        wf_cut = to_cut_cnf(net, 1, 4)
        res = wmc_solve(wf_cut, algorithm="combined_wmc")
        self.assertEqual(res["status"], "exact")
        self.assertEqual(Fraction(res["weight_fraction"]), Fraction(0))

    def test_direct_single_edge_terminal(self):
        """Single edge connecting s to t yields single unit clause."""
        net = NetworkGraph()
        net.add_edge(1, 2, Fraction(8, 10))
        wf_cut = to_cut_cnf(net, 1, 2)
        self.assertEqual(wf_cut.n_vars, 1)
        self.assertEqual(wf_cut.clauses, [[1]])
        res = wmc_solve(wf_cut, algorithm="combined_wmc")
        self.assertEqual(res["status"], "exact")
        self.assertEqual(Fraction(res["weight_fraction"]), Fraction(8, 10))

    def test_metamorphic_node_label_invariance(self):
        """Relabeling nodes does not change minimal cut sizes or reliability fraction."""
        net1, s1, t1 = build_wheatstone_bridge(p=Fraction(7, 10))
        wf1 = to_cut_cnf(net1, s1, t1)
        res1 = wmc_solve(wf1, algorithm="combined_wmc")

        # Create isomorphic network with permuted node IDs
        # Node mapping: 1->10, 2->20, 3->30, 4->40
        perm = {1: 10, 2: 20, 3: 30, 4: 40}
        net2 = NetworkGraph()
        for u, v in net1.edges:
            net2.add_edge(perm[u], perm[v], Fraction(7, 10))

        wf2 = to_cut_cnf(net2, perm[s1], perm[t1])
        res2 = wmc_solve(wf2, algorithm="combined_wmc")

        self.assertEqual(len(wf1.clauses), len(wf2.clauses))
        self.assertEqual(res1["weight_fraction"], res2["weight_fraction"])


if __name__ == "__main__":
    unittest.main()
