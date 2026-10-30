"""Unit tests for Hypothesis H17: Bounded-Diameter / Latency-Constrained Network Reliability."""
import unittest
from fractions import Fraction

from sat_frontier.bounded_hop_compiler import (
    brute_force_bounded_hop_oracle,
    find_all_bounded_paths,
    find_minimal_bounded_cuts,
    solve_bounded_hop_reliability,
    to_bounded_hop_cnf,
)
from sat_frontier.reliability import NetworkGraph


class BoundedHopCompilerTests(unittest.TestCase):

    def test_line_graph_hop_bounds(self):
        """Line of 3 edges (4 nodes: 0-1-2-3). Shortest distance is 3."""
        net = NetworkGraph()
        p = Fraction(9, 10)
        net.add_edge(0, 1, prob=p)
        net.add_edge(1, 2, prob=p)
        net.add_edge(2, 3, prob=p)

        # L = 2: topologically impossible to reach node 3 in 2 hops
        rel_2, _, _ = solve_bounded_hop_reliability(net, 0, 3, max_hops=2)
        oracle_2 = brute_force_bounded_hop_oracle(net, 0, 3, max_hops=2)
        self.assertEqual(rel_2, Fraction(0))
        self.assertEqual(oracle_2, Fraction(0))

        # L = 3: exactly requires all 3 edges: (9/10)^3 = 729/1000
        rel_3, _, _ = solve_bounded_hop_reliability(net, 0, 3, max_hops=3)
        oracle_3 = brute_force_bounded_hop_oracle(net, 0, 3, max_hops=3)
        self.assertEqual(rel_3, Fraction(729, 1000))
        self.assertEqual(rel_3, oracle_3)

    def test_parallel_paths_different_lengths(self):
        """Graph with 1-hop direct link and 2-hop alternate path."""
        net = NetworkGraph()
        # Direct link 0-1 (1 hop, p = 0.8)
        net.add_edge(0, 1, prob=Fraction(8, 10))
        # Alternate path 0-2-1 (2 hops, each prob 0.9)
        net.add_edge(0, 2, prob=Fraction(9, 10))
        net.add_edge(2, 1, prob=Fraction(9, 10))

        # Max hops L = 1: only direct link is eligible
        rel_1, _, _ = solve_bounded_hop_reliability(net, 0, 1, max_hops=1)
        oracle_1 = brute_force_bounded_hop_oracle(net, 0, 1, max_hops=1)
        self.assertEqual(rel_1, Fraction(8, 10))
        self.assertEqual(rel_1, oracle_1)

        # Max hops L = 2: both direct link and 2-hop path eligible
        # P(reach <= 2) = 1 - P(fail direct)*P(fail alternate)
        # = 1 - (1 - 0.8)*(1 - 0.81) = 1 - 0.2 * 0.19 = 1 - 0.038 = 0.962 = 481/500
        rel_2, _, _ = solve_bounded_hop_reliability(net, 0, 1, max_hops=2)
        oracle_2 = brute_force_bounded_hop_oracle(net, 0, 1, max_hops=2)
        self.assertEqual(rel_2, Fraction(481, 500))
        self.assertEqual(rel_2, oracle_2)

    def test_wheatstone_bridge_hop_bounds(self):
        """Wheatstone bridge: evaluate L=2 vs L=3."""
        net = NetworkGraph()
        p = Fraction(9, 10)
        net.add_edge(0, 1, prob=p)  # e1
        net.add_edge(0, 2, prob=p)  # e2
        net.add_edge(1, 3, prob=p)  # e3
        net.add_edge(2, 3, prob=p)  # e4
        net.add_edge(1, 2, prob=p)  # e5 (bridge)

        # L = 2: paths are {e1, e3} and {e2, e4}. Bridge edge e5 cannot be used!
        # P(dist <= 2) = 1 - (1 - p^2)^2 = 1 - (1 - 81/100)^2 = 1 - (19/100)^2 = 1 - 361/10000 = 9639/10000
        rel_2, _, _ = solve_bounded_hop_reliability(net, 0, 3, max_hops=2)
        oracle_2 = brute_force_bounded_hop_oracle(net, 0, 3, max_hops=2)
        self.assertEqual(rel_2, Fraction(9639, 10000))
        self.assertEqual(rel_2, oracle_2)

        # L = 3: all paths valid, recovering standard two-terminal reliability
        rel_3, _, _ = solve_bounded_hop_reliability(net, 0, 3, max_hops=3)
        oracle_3 = brute_force_bounded_hop_oracle(net, 0, 3, max_hops=3)
        self.assertEqual(rel_3, oracle_3)
        # For p=0.9, standard Wheatstone R = 2*p^2 + 2*p^3 - 5*p^4 + 2*p^5 = 0.97848 = 12231/12500
        self.assertEqual(rel_3, Fraction(12231, 12500))
        self.assertGreater(rel_3, rel_2)

    def test_ladder_topology_oracle_match(self):
        """2x3 ladder with 7 edges, tested across L=2, L=3, L=4."""
        net = NetworkGraph()
        p = Fraction(85, 100)
        net.add_edge(0, 1, prob=p)
        net.add_edge(1, 2, prob=p)
        net.add_edge(3, 4, prob=p)
        net.add_edge(4, 5, prob=p)
        net.add_edge(0, 3, prob=p)
        net.add_edge(1, 4, prob=p)
        net.add_edge(2, 5, prob=p)

        for L in [2, 3, 4]:
            rel, _, _ = solve_bounded_hop_reliability(net, 0, 2, max_hops=L)
            oracle = brute_force_bounded_hop_oracle(net, 0, 2, max_hops=L)
            self.assertEqual(rel, oracle, f"Mismatch on ladder at L={L}")


if __name__ == "__main__":
    unittest.main()
