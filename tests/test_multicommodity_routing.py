"""Unit tests for Exact Concurrent Multi-Commodity Routing and Leighton-Rao Gap Engine."""
from fractions import Fraction
import unittest

from sat_frontier.multi_commodity_compiler import MultiCommodityNetwork
from sat_frontier.multicommodity_routing_compiler import (
    audit_concurrent_multi_commodity_flow,
    brute_force_exact_routing_oracle,
)


class TestMultiCommodityRouting(unittest.TestCase):
    """Rigorous verification of concurrent routing reliability and Leighton-Rao gap."""

    def test_single_commodity_matches_cut_condition(self):
        """Single commodity: Max-Flow = Min-Cut implies routing reliability equals cut condition."""
        net = MultiCommodityNetwork()
        net.add_edge(0, 1, capacity=1, prob=Fraction(9, 10))
        net.add_edge(1, 2, capacity=1, prob=Fraction(9, 10))
        net.add_edge(0, 2, capacity=1, prob=Fraction(9, 10))
        net.add_commodity(0, 2, demand=1)

        rep = audit_concurrent_multi_commodity_flow(net)
        self.assertEqual(rep.routing_reliability_exact, rep.cut_condition_reliability_exact)
        self.assertEqual(rep.leighton_rao_gap_exact, Fraction(0, 1))
        self.assertFalse(rep.gap_detected)
        self.assertTrue(rep.is_provably_routable)

    def test_triangle_two_noncrossing_commodities_match(self):
        """Triangle with 2 non-crossing commodities satisfies Seymour-Okamura exactness."""
        net = MultiCommodityNetwork()
        net.add_edge(0, 1, capacity=1, prob=Fraction(9, 10))
        net.add_edge(1, 2, capacity=1, prob=Fraction(9, 10))
        net.add_edge(0, 2, capacity=1, prob=Fraction(9, 10))
        net.add_commodity(0, 1, demand=1)
        net.add_commodity(1, 2, demand=1)

        rep = audit_concurrent_multi_commodity_flow(net)
        self.assertEqual(rep.routing_reliability_exact, rep.cut_condition_reliability_exact)
        self.assertEqual(rep.routing_reliability_exact, Fraction(81, 100))
        self.assertEqual(rep.leighton_rao_gap_exact, Fraction(0, 1))
        self.assertFalse(rep.gap_detected)

    def test_c4_crossing_demands_leighton_rao_gap(self):
        """C_4 with opposite crossing demands: cut condition is 0.6561 but true routing is 0.0."""
        net = MultiCommodityNetwork()
        net.add_edge(0, 1, capacity=1, prob=Fraction(9, 10))
        net.add_edge(1, 2, capacity=1, prob=Fraction(9, 10))
        net.add_edge(2, 3, capacity=1, prob=Fraction(9, 10))
        net.add_edge(3, 0, capacity=1, prob=Fraction(9, 10))
        # Opposite crossing demands: (0, 2) and (1, 3)
        net.add_commodity(0, 2, demand=1)
        net.add_commodity(1, 3, demand=1)

        rep = audit_concurrent_multi_commodity_flow(net)
        # Cut condition over-estimates at (9/10)^4 = 6561/10000
        self.assertEqual(rep.cut_condition_reliability_exact, Fraction(6561, 10000))
        # True routing reliability is strictly 0
        self.assertEqual(rep.routing_reliability_exact, Fraction(0, 1))
        # Leighton-Rao gap is exactly 6561/10000
        self.assertEqual(rep.leighton_rao_gap_exact, Fraction(6561, 10000))
        self.assertTrue(rep.gap_detected)
        self.assertFalse(rep.is_provably_routable)

    def test_k23_bipartite_three_demands_leighton_rao_gap(self):
        """K_{2,3} with 3 pairwise demands: cut condition is 0.531441 but true routing is 0.0."""
        net = MultiCommodityNetwork()
        # Partitions: A={0, 1}, B={2, 3, 4}
        for a in (0, 1):
            for b in (2, 3, 4):
                net.add_edge(a, b, capacity=1, prob=Fraction(9, 10))

        # 3 pairwise demands across independent set B
        net.add_commodity(2, 3, demand=1)
        net.add_commodity(3, 4, demand=1)
        net.add_commodity(2, 4, demand=1)

        rep = audit_concurrent_multi_commodity_flow(net)
        # Cut condition reports 531441/1000000
        self.assertEqual(rep.cut_condition_reliability_exact, Fraction(531441, 1000000))
        # True routing reliability is strictly 0
        self.assertEqual(rep.routing_reliability_exact, Fraction(0, 1))
        # Leighton-Rao gap detected
        self.assertEqual(rep.leighton_rao_gap_exact, Fraction(531441, 1000000))
        self.assertTrue(rep.gap_detected)
        self.assertFalse(rep.is_provably_routable)

    def test_ladder_two_independent_commodities(self):
        """2x2 ladder network routing 2 independent horizontal flows."""
        net = MultiCommodityNetwork()
        # Top line: 0-1
        net.add_edge(0, 1, capacity=1, prob=Fraction(9, 10))
        # Bottom line: 2-3
        net.add_edge(2, 3, capacity=1, prob=Fraction(9, 10))
        # Rungs: 0-2 and 1-3
        net.add_edge(0, 2, capacity=1, prob=Fraction(9, 10))
        net.add_edge(1, 3, capacity=1, prob=Fraction(9, 10))

        # Commodities: 0->1 and 2->3
        net.add_commodity(0, 1, demand=1)
        net.add_commodity(2, 3, demand=1)

        rep = audit_concurrent_multi_commodity_flow(net)
        self.assertTrue(rep.is_provably_routable)
        self.assertGreater(rep.routing_reliability_exact, Fraction(0, 1))
        self.assertLessEqual(rep.routing_reliability_exact, rep.cut_condition_reliability_exact)


if __name__ == '__main__':
    unittest.main()

