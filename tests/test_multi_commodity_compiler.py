"""Unit tests for Multi-Commodity Capacitated Flow Reliability Compiler (Hypothesis H18)."""
import unittest
from fractions import Fraction

from sat_frontier.multi_commodity_compiler import (
    CommodityDemand,
    MultiCommodityNetwork,
    audit_multi_commodity,
    brute_force_multi_commodity_oracle,
    compile_multi_commodity_clauses,
)
from sat_frontier.wmc import WeightedFormula, wmc_solve


class TestMultiCommodityCompiler(unittest.TestCase):
    """Test suite for multi-commodity dual cut compilation."""

    def test_single_commodity_single_edge(self):
        """Single commodity over a single edge."""
        net = MultiCommodityNetwork()
        net.add_edge("s", "t", capacity=2, prob=Fraction(3, 4))
        net.add_commodity("s", "t", demand=2)

        oracle = brute_force_multi_commodity_oracle(net)
        self.assertEqual(oracle, Fraction(3, 4))

        clauses, weights, n_vars = compile_multi_commodity_clauses(net)
        wf = WeightedFormula(clauses, n_vars=n_vars, weights=weights)
        res = wmc_solve(wf)
        self.assertEqual(res["status"], "exact")
        self.assertEqual(Fraction(res["weight_fraction"]), Fraction(3, 4))

    def test_single_commodity_insufficient_capacity(self):
        """Demand exceeds capacity: formula must be UNSAT."""
        net = MultiCommodityNetwork()
        net.add_edge("s", "t", capacity=1, prob=Fraction(9, 10))
        net.add_commodity("s", "t", demand=2)

        oracle = brute_force_multi_commodity_oracle(net)
        self.assertEqual(oracle, Fraction(0))

        clauses, weights, n_vars = compile_multi_commodity_clauses(net)
        wf = WeightedFormula(clauses, n_vars=n_vars, weights=weights)
        res = wmc_solve(wf)
        self.assertEqual(res["status"], "exact")
        self.assertEqual(Fraction(res["weight_fraction"]), Fraction(0))

    def test_two_commodities_sharing_bottleneck(self):
        """Two commodities sharing a central bottleneck bridge."""
        # s1 - a - c - b - t1
        # s2 - a - c - b - t2
        # Bridge is (a, c) with capacity 2.
        # Demands: (s1, t1, 1), (s2, t2, 1). Aggregate demand across bridge is 2.
        net = MultiCommodityNetwork()
        net.add_edge("s1", "a", capacity=2, prob=Fraction(9, 10))
        net.add_edge("s2", "a", capacity=2, prob=Fraction(9, 10))
        net.add_edge("a", "b", capacity=2, prob=Fraction(4, 5))  # bottleneck
        net.add_edge("b", "t1", capacity=2, prob=Fraction(9, 10))
        net.add_edge("b", "t2", capacity=2, prob=Fraction(9, 10))
        net.add_commodity("s1", "t1", demand=1)
        net.add_commodity("s2", "t2", demand=1)

        oracle = brute_force_multi_commodity_oracle(net)
        clauses, weights, n_vars = compile_multi_commodity_clauses(net)
        wf = WeightedFormula(clauses, n_vars=n_vars, weights=weights)
        res = wmc_solve(wf)

        self.assertEqual(res["status"], "exact")
        self.assertEqual(Fraction(res["weight_fraction"]), oracle)

    def test_parallel_independent_commodities(self):
        """Two commodities routed on disjoint parallel paths."""
        net = MultiCommodityNetwork()
        net.add_edge("s1", "t1", capacity=1, prob=Fraction(4, 5))
        net.add_edge("s2", "t2", capacity=1, prob=Fraction(3, 4))
        net.add_commodity("s1", "t1", demand=1)
        net.add_commodity("s2", "t2", demand=1)

        oracle = brute_force_multi_commodity_oracle(net)
        # Independent survival: (4/5) * (3/4) = 3/5
        self.assertEqual(oracle, Fraction(3, 5))

        audit = audit_multi_commodity(net)
        self.assertEqual(audit["status"], "exact")
        self.assertEqual(Fraction(audit["reliability_fraction"]), Fraction(3, 5))

    def test_diamond_multi_commodity(self):
        """Diamond topology with two crossing commodities."""
        # s1 -> u -> t1, s2 -> v -> t2
        # cross links (u, v)
        net = MultiCommodityNetwork()
        net.add_edge("s1", "u", capacity=1, prob=Fraction(9, 10))
        net.add_edge("u", "t1", capacity=1, prob=Fraction(9, 10))
        net.add_edge("s2", "v", capacity=1, prob=Fraction(4, 5))
        net.add_edge("v", "t2", capacity=1, prob=Fraction(4, 5))
        net.add_edge("u", "v", capacity=1, prob=Fraction(1, 2))
        net.add_commodity("s1", "t1", demand=1)
        net.add_commodity("s2", "t2", demand=1)

        oracle = brute_force_multi_commodity_oracle(net)
        audit = audit_multi_commodity(net)
        self.assertEqual(audit["status"], "exact")
        self.assertEqual(Fraction(audit["reliability_fraction"]), oracle)


if __name__ == "__main__":
    unittest.main()

