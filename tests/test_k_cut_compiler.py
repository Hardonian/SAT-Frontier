"""Unit tests for Multi-Terminal and All-Terminal Dual K-Cut compilation (Hypothesis H10)."""
import unittest
from fractions import Fraction

from sat_frontier.cut_compiler import find_all_minimal_cuts, to_cut_cnf
from sat_frontier.k_cut_compiler import (
    brute_force_k_terminal_oracle,
    find_all_minimal_k_cuts,
    to_k_cut_cnf,
)
from sat_frontier.reliability import NetworkGraph
from sat_frontier.wmc import wmc_solve


class KCutCompilerTests(unittest.TestCase):
    def test_two_terminal_reduction_matches_to_cut_cnf(self):
        """Verify K-cut compilation on K={s, t} identically matches 2-terminal cut compiler."""
        net = NetworkGraph()
        # Wheatstone bridge topology
        edges = [(1, 2), (1, 3), (2, 3), (2, 4), (3, 4)]
        probs = [
            Fraction(9, 10),
            Fraction(8, 10),
            Fraction(5, 10),
            Fraction(95, 100),
            Fraction(85, 100),
        ]
        for (u, v), p in zip(edges, probs):
            net.add_edge(u, v, prob=p)

        cuts_2term = find_all_minimal_cuts(net, 1, 4)
        cuts_kterm = find_all_minimal_k_cuts(net, [1, 4])
        self.assertEqual(cuts_2term, cuts_kterm)

        wf_2term = to_cut_cnf(net, 1, 4)
        wf_kterm = to_k_cut_cnf(net, [1, 4])
        res_2term = wmc_solve(wf_2term)
        res_kterm = wmc_solve(wf_kterm)
        self.assertEqual(res_2term["weight_fraction"], res_kterm["weight_fraction"])

    def test_triangle_all_terminal_against_oracle(self):
        """Verify all-terminal reliability on triangle graph matches brute-force oracle."""
        net = NetworkGraph()
        for u, v in [(1, 2), (2, 3), (1, 3)]:
            net.add_edge(u, v, prob=Fraction(9, 10))

        bf_prob = brute_force_k_terminal_oracle(net, [1, 2, 3])
        wf = to_k_cut_cnf(net, [1, 2, 3])
        res = wmc_solve(wf)

        self.assertEqual(res["status"], "exact")
        self.assertEqual(str(bf_prob), res["weight_fraction"])
        # Analytic: 3*(0.9)^2 - 2*(0.9)^3 = 2.43 - 1.458 = 0.972 = 243/250
        self.assertEqual(bf_prob, Fraction(243, 250))

    def test_c4_three_terminal_against_oracle(self):
        """Verify 3-terminal reliability on C4 ring matches brute-force oracle."""
        net = NetworkGraph()
        edges = [(1, 2), (2, 3), (3, 4), (4, 1)]
        probs = [Fraction(8, 10), Fraction(9, 10), Fraction(95, 100), Fraction(7, 10)]
        for (u, v), p in zip(edges, probs):
            net.add_edge(u, v, prob=p)

        terminals = [1, 2, 3]
        bf_prob = brute_force_k_terminal_oracle(net, terminals)
        wf = to_k_cut_cnf(net, terminals)
        res = wmc_solve(wf)

        self.assertEqual(res["status"], "exact")
        self.assertEqual(str(bf_prob), res["weight_fraction"])

    def test_k4_all_and_three_terminal_against_oracle(self):
        """Verify K4 complete graph all-terminal and 3-terminal match brute-force oracle."""
        net = NetworkGraph()
        edges = [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]
        probs = [
            Fraction(9, 10),
            Fraction(85, 100),
            Fraction(95, 100),
            Fraction(8, 10),
            Fraction(9, 10),
            Fraction(75, 100),
        ]
        for (u, v), p in zip(edges, probs):
            net.add_edge(u, v, prob=p)

        # All-terminal
        bf_all = brute_force_k_terminal_oracle(net, [1, 2, 3, 4])
        wf_all = to_k_cut_cnf(net, [1, 2, 3, 4])
        res_all = wmc_solve(wf_all)
        self.assertEqual(str(bf_all), res_all["weight_fraction"])

        # 3-terminal
        bf_3 = brute_force_k_terminal_oracle(net, [1, 2, 3])
        wf_3 = to_k_cut_cnf(net, [1, 2, 3])
        res_3 = wmc_solve(wf_3)
        self.assertEqual(str(bf_3), res_3["weight_fraction"])

    def test_grid_2x3_four_corners_against_oracle(self):
        """Verify 4-corner multi-terminal reliability on 2x3 grid matches brute force oracle."""
        net = NetworkGraph()
        edges = [(1, 2), (2, 3), (4, 5), (5, 6), (1, 4), (2, 5), (3, 6)]
        for u, v in edges:
            net.add_edge(u, v, prob=Fraction(9, 10))

        corners = [1, 3, 4, 6]
        bf_prob = brute_force_k_terminal_oracle(net, corners)
        wf = to_k_cut_cnf(net, corners)
        res = wmc_solve(wf)

        self.assertEqual(res["status"], "exact")
        self.assertEqual(str(bf_prob), res["weight_fraction"])

    def test_disconnected_terminals_yields_unsat(self):
        """Verify disconnected terminal components yield empty cut clause (UNSAT)."""
        net = NetworkGraph()
        net.add_edge(1, 2, prob=Fraction(9, 10))
        net.add_edge(3, 4, prob=Fraction(9, 10))

        # Terminals 1 and 4 are in disconnected components
        wf = to_k_cut_cnf(net, [1, 4])
        res = wmc_solve(wf)
        self.assertEqual(res["weight_fraction"], "0")

    def test_bridge_cut_edge_yields_unit_clause(self):
        """Verify that a bridge edge separating terminals produces a unit clause."""
        net = NetworkGraph()
        # Bell 1: 1-2-3 triangle
        net.add_edge(1, 2, prob=Fraction(9, 10))
        net.add_edge(2, 3, prob=Fraction(9, 10))
        net.add_edge(1, 3, prob=Fraction(9, 10))
        # Bridge: 3-4
        net.add_edge(3, 4, prob=Fraction(8, 10))
        # Bell 2: 4-5-6 triangle
        net.add_edge(4, 5, prob=Fraction(9, 10))
        net.add_edge(5, 6, prob=Fraction(9, 10))
        net.add_edge(4, 6, prob=Fraction(9, 10))

        # Terminals in both bells
        terminals = [1, 2, 5, 6]
        cuts = find_all_minimal_k_cuts(net, terminals)
        # Bridge edge is edge 4 (3, 4)
        bridge_eid = 4
        # There must be a cut of size 1 containing exactly bridge_eid
        self.assertIn((bridge_eid,), cuts)

    def test_metamorphic_node_permutation_invariance(self):
        """Permuting vertex labels preserves minimal cut sizes and exact probability."""
        net1 = NetworkGraph()
        edges1 = [(1, 2), (2, 3), (3, 4), (4, 1)]
        for u, v in edges1:
            net1.add_edge(u, v, prob=Fraction(9, 10))

        # Permutation: 1->3, 2->4, 3->1, 4->2
        mapping = {1: 3, 2: 4, 3: 1, 4: 2}
        net2 = NetworkGraph()
        for u, v in edges1:
            net2.add_edge(mapping[u], mapping[v], prob=Fraction(9, 10))

        terminals1 = [1, 2, 3]
        terminals2 = [mapping[t] for t in terminals1]

        cuts1 = find_all_minimal_k_cuts(net1, terminals1)
        cuts2 = find_all_minimal_k_cuts(net2, terminals2)
        self.assertEqual(len(cuts1), len(cuts2))

        wf1 = to_k_cut_cnf(net1, terminals1)
        wf2 = to_k_cut_cnf(net2, terminals2)
        res1 = wmc_solve(wf1)
        res2 = wmc_solve(wf2)
        self.assertEqual(res1["weight_fraction"], res2["weight_fraction"])


if __name__ == "__main__":
    unittest.main()
