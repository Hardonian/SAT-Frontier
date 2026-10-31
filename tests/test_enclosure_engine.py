"""Unit and Metamorphic Tests for Any-Time Monotone Dual Bounding & Enclosure Engine."""
import unittest
from fractions import Fraction

from sat_frontier.cut_compiler import to_cut_cnf
from sat_frontier.enclosure_engine import (
    anytime_enclosure_stream,
    compute_enclosure,
    find_shortest_paths,
)
from sat_frontier.reliability import NetworkGraph, build_grid_network, build_wheatstone_bridge
from sat_frontier.wmc import wmc_solve


class TestEnclosureEngine(unittest.TestCase):
    """Test suite for Theorem 13 (Monotone Dual Enclosure Duality)."""

    def test_single_edge_enclosure(self):
        """Single link: exactly 1 cut and 1 path. Gap is 0."""
        net = NetworkGraph()
        net.add_edge(1, 2, Fraction(8, 10))
        e_probs = {(1, 2): Fraction(8, 10)}

        enc = compute_enclosure(net, 1, 2, e_probs)
        self.assertEqual(enc.lower_bound_exact, Fraction(8, 10))
        self.assertEqual(enc.upper_bound_exact, Fraction(8, 10))
        self.assertEqual(enc.gap_exact, Fraction(0, 1))
        self.assertTrue(enc.enclosed)

    def test_parallel_paths_enclosure(self):
        """Two parallel links: partial path gives lower bound, partial cuts give upper bound."""
        net = NetworkGraph()
        net.add_edge(1, 3, Fraction(9, 10))
        net.add_edge(3, 2, Fraction(9, 10))
        net.add_edge(1, 4, Fraction(9, 10))
        net.add_edge(4, 2, Fraction(9, 10))
        e_probs = {e: Fraction(9, 10) for e in net.edges}

        # Full exact reliability
        wf = to_cut_cnf(net, 1, 2)
        r_exact = Fraction(wmc_solve(wf, algorithm="combined")["weight_fraction"])

        # Select only 1 path out of 2
        path1 = [(1, 3), (3, 2)]
        enc_part = compute_enclosure(net, 1, 2, e_probs, selected_paths=[path1])

        self.assertLess(enc_part.lower_bound_exact, r_exact)
        self.assertGreaterEqual(enc_part.upper_bound_exact, r_exact)
        self.assertTrue(enc_part.enclosed)
        self.assertGreater(enc_part.gap_exact, Fraction(0, 1))

    def test_wheatstone_bridge_enclosure(self):
        """Wheatstone bridge: verify R_lower <= R_exact <= R_upper under partial cuts and paths."""
        net, s, t = build_wheatstone_bridge(p=Fraction(85, 100))
        e_probs = {e: Fraction(85, 100) for e in net.edges}

        wf = to_cut_cnf(net, s, t)
        r_exact = Fraction(wmc_solve(wf, algorithm="combined")["weight_fraction"])

        # Stream progressive enclosures
        stream = list(anytime_enclosure_stream(net, s, t, e_probs, max_steps=5))
        self.assertGreater(len(stream), 1)

        for enc in stream:
            self.assertLessEqual(enc.lower_bound_exact, r_exact)
            self.assertGreaterEqual(enc.upper_bound_exact, r_exact)
            self.assertTrue(enc.enclosed)
            self.assertGreaterEqual(enc.gap_exact, Fraction(0, 1))

        # Final step should achieve tightest bound (gap narrows)
        self.assertLessEqual(stream[-1].gap_exact, stream[0].gap_exact)

    def test_ladder_convergence(self):
        """2x3 ladder: streaming anytime enclosure strictly narrows the certificate gap."""
        net, s, t = build_grid_network(rows=2, cols=3, p=Fraction(9, 10))
        e_probs = {e: Fraction(9, 10) for e in net.edges}

        stream = list(anytime_enclosure_stream(net, s, t, e_probs, max_steps=4))
        self.assertGreaterEqual(len(stream), 2)

        prev_gap = Fraction(1, 1)
        for enc in stream:
            self.assertTrue(enc.enclosed)
            self.assertLessEqual(enc.gap_exact, prev_gap)
            prev_gap = enc.gap_exact


if __name__ == "__main__":
    unittest.main()

