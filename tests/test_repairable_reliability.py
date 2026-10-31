"""Unit and Metamorphic Tests for Repairable Network Reliability Engine."""
import unittest
from fractions import Fraction

from sat_frontier.reliability import NetworkGraph, build_wheatstone_bridge
from sat_frontier.repairable_reliability import (
    audit_repairable_network,
    brute_force_repairable_oracle,
)


class TestRepairableReliability(unittest.TestCase):
    """Test suite for Theorem 12 (Repairable System Renewal Duality)."""

    def test_single_link_repairable(self):
        """Single link: lambda = 1/1000, mu = 1/10.

        Exact A = 100/101, MTBF = 1000 hrs, MTTR = 10 hrs.
        """
        net = NetworkGraph()
        net.add_edge(1, 2, Fraction(1))
        f_rates = {(1, 2): Fraction(1, 1000)}
        r_rates = {(1, 2): Fraction(1, 10)}

        res = audit_repairable_network(net, 1, 2, f_rates, r_rates)
        self.assertEqual(res.availability_exact, Fraction(100, 101))
        self.assertEqual(res.unavailability_exact, Fraction(1, 101))
        self.assertEqual(res.failure_frequency_exact, Fraction(1, 1010))
        self.assertEqual(res.mtbf_hours_exact, Fraction(1000, 1))
        self.assertEqual(res.mttr_hours_exact, Fraction(10, 1))

        # Check against brute force oracle
        a_o, w_o, mtbf_o, mttr_o = brute_force_repairable_oracle(net, 1, 2, f_rates, r_rates)
        self.assertEqual(res.availability_exact, a_o)
        self.assertEqual(res.failure_frequency_exact, w_o)
        self.assertEqual(res.mtbf_hours_exact, mtbf_o)
        self.assertEqual(res.mttr_hours_exact, mttr_o)

    def test_two_parallel_links_repairable(self):
        """Two parallel links: redundant parallel availability and MTBF multiplication."""
        # 3 nodes: 1 -> 3 -> 2 and 1 -> 4 -> 2, or direct parallel
        net = NetworkGraph()
        net.add_edge(1, 3, Fraction(1))
        net.add_edge(3, 2, Fraction(1))
        net.add_edge(1, 4, Fraction(1))
        net.add_edge(4, 2, Fraction(1))

        f_rates = {e: Fraction(1, 1000) for e in net.edges}
        r_rates = {e: Fraction(1, 10) for e in net.edges}

        res = audit_repairable_network(net, 1, 2, f_rates, r_rates)
        self.assertGreater(res.availability_exact, Fraction(99, 100))
        self.assertGreater(res.mtbf_hours_exact, Fraction(1000, 1))

        # Check against independent oracle
        a_o, w_o, mtbf_o, mttr_o = brute_force_repairable_oracle(net, 1, 2, f_rates, r_rates)
        self.assertEqual(res.availability_exact, a_o)
        self.assertEqual(res.failure_frequency_exact, w_o)
        self.assertEqual(res.mtbf_hours_exact, mtbf_o)
        self.assertEqual(res.mttr_hours_exact, mttr_o)

    def test_wheatstone_bridge_repairable(self):
        """Wheatstone bridge network with heterogeneous component parameters."""
        net, s, t = build_wheatstone_bridge(p=Fraction(9, 10))
        edges = list(net.edges)

        # Diverse failure rates (1/500 to 1/2000) and repair rates (1/4 to 1/20)
        f_rates = {
            edges[0]: Fraction(1, 500),
            edges[1]: Fraction(1, 800),
            edges[2]: Fraction(1, 1200),
            edges[3]: Fraction(1, 1500),
            edges[4]: Fraction(1, 2000),
        }
        r_rates = {
            edges[0]: Fraction(1, 8),
            edges[1]: Fraction(1, 12),
            edges[2]: Fraction(1, 6),
            edges[3]: Fraction(1, 10),
            edges[4]: Fraction(1, 15),
        }

        res = audit_repairable_network(net, s, t, f_rates, r_rates)
        a_o, w_o, mtbf_o, mttr_o = brute_force_repairable_oracle(net, s, t, f_rates, r_rates)

        self.assertEqual(res.availability_exact, a_o)
        self.assertEqual(res.failure_frequency_exact, w_o)
        self.assertEqual(res.mtbf_hours_exact, mtbf_o)
        self.assertEqual(res.mttr_hours_exact, mttr_o)

    def test_series_bottleneck_repairable(self):
        """Series bottleneck: A_sys = A1 * A2, failure frequency is additive."""
        net = NetworkGraph()
        net.add_edge(1, 2, Fraction(1))
        net.add_edge(2, 3, Fraction(1))

        f_rates = {(1, 2): Fraction(1, 1000), (2, 3): Fraction(1, 2000)}
        r_rates = {(1, 2): Fraction(1, 10), (2, 3): Fraction(1, 10)}

        res = audit_repairable_network(net, 1, 3, f_rates, r_rates)
        a_o, w_o, mtbf_o, mttr_o = brute_force_repairable_oracle(net, 1, 3, f_rates, r_rates)

        self.assertEqual(res.availability_exact, a_o)
        self.assertEqual(res.failure_frequency_exact, w_o)
        self.assertEqual(res.mtbf_hours_exact, mtbf_o)
        self.assertEqual(res.mttr_hours_exact, mttr_o)


if __name__ == "__main__":
    unittest.main()
