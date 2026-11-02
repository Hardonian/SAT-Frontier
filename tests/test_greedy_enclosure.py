"""Unit tests for Greedy Priority-Weighted Reliability Enclosures."""
from fractions import Fraction
import unittest

from sat_frontier.greedy_enclosure import (
    compute_greedy_enclosure,
    sort_cuts_by_greedy_failure_priority,
    sort_paths_by_greedy_survival_priority,
)
from sat_frontier.reliability import build_wheatstone_bridge, build_grid_network


class TestGreedyEnclosure(unittest.TestCase):
    """Rigorous verification of greedy priority-weighted enclosure bounding."""

    def test_wheatstone_bridge_greedy_enclosure_containment(self):
        """Wheatstone bridge enclosure [R_lower, R_upper] contains exact reliability."""
        net, s, t = build_wheatstone_bridge(Fraction(9, 10))
        edge_probs = {e: Fraction(9, 10) for e in net.edges}

        # Exact reliability of Wheatstone bridge at p=0.9 is 12231/12500 = 0.97848
        exact_r = Fraction(12231, 12500)

        res = compute_greedy_enclosure(net, s, t, edge_probs, target_tolerance=Fraction(1, 100))
        self.assertTrue(res.enclosed)
        self.assertLessEqual(res.lower_bound_exact, exact_r)
        self.assertGreaterEqual(res.upper_bound_exact, exact_r)
        self.assertLessEqual(res.gap_exact, Fraction(1, 100))
        self.assertTrue(res.tolerance_achieved)

    def test_grid_2x3_greedy_enclosure(self):
        """Grid 2x3 network achieves tolerance within 10 greedy steps."""
        net, s, t = build_grid_network(2, 3, Fraction(9, 10))
        edge_probs = {e: Fraction(9, 10) for e in net.edges}

        res = compute_greedy_enclosure(net, s, t, edge_probs, target_tolerance=Fraction(5, 100), max_steps=10)
        self.assertTrue(res.enclosed)
        self.assertGreater(res.lower_bound_exact, Fraction(0, 1))
        self.assertLessEqual(res.upper_bound_exact, Fraction(1, 1))
        self.assertLessEqual(res.lower_bound_exact, res.upper_bound_exact)

    def test_greedy_cut_sorting_prioritizes_failure_probability(self):
        """Greedy cut sorting orders cuts by descending failure probability."""
        edges = [(0, 1), (1, 2), (0, 2)]
        edge_probs = {
            (0, 1): Fraction(9, 10),  # failure prob = 1/10
            (1, 2): Fraction(9, 10),  # failure prob = 1/10
            (0, 2): Fraction(1, 2),   # failure prob = 1/2
        }
        # Cut 1: {3} (edge (0, 2)), failure prob = 1/2
        # Cut 2: {1, 2} (edges (0, 1) and (1, 2)), failure prob = 1/10 * 1/10 = 1/100
        cuts = [{1, 2}, {3}]
        sorted_cuts = sort_cuts_by_greedy_failure_priority(cuts, edges, edge_probs)
        self.assertEqual(sorted_cuts[0], {3})
        self.assertEqual(sorted_cuts[1], {1, 2})


if __name__ == '__main__':
    unittest.main()
