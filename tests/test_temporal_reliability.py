"""Unit tests for continuous temporal network reliability and closed-form MTTF."""
import math
import unittest
from fractions import Fraction

from sat_frontier.poly_wmc import ReliabilityPolynomial
from sat_frontier.reliability import (
    NetworkGraph,
    build_barbell_network,
    build_grid_network,
    build_wheatstone_bridge,
)
from sat_frontier.temporal_reliability import (
    compute_exact_mttf,
    compute_quantile_life,
    evaluate_temporal_reliability,
    numerical_quadrature_mttf_oracle,
    polynomial_to_monomial_basis,
)


class TestTemporalReliability(unittest.TestCase):
    def test_single_edge_mttf(self):
        """Single link with hazard rate lambda: MTTF = 1/lambda, Var = 1/lambda^2."""
        net = NetworkGraph()
        net.add_edge(0, 1, Fraction(9, 10))
        lam = 0.01  # 1/100 hours
        res = evaluate_temporal_reliability(net, 0, 1, hazard_rate_per_hour=lam)

        self.assertEqual(res.mttf_exact, Fraction(100, 1))
        self.assertAlmostEqual(res.mttf_hours, 100.0)
        self.assertAlmostEqual(res.variance_hours2, 10000.0)
        self.assertAlmostEqual(res.std_dev_hours, 100.0)

        # B10 life: e^(-lam * t) = 0.90 => t = -ln(0.9) / 0.01 = 10.536 hours
        expected_b10 = -math.log(0.90) / lam
        self.assertAlmostEqual(res.b10_life_hours, expected_b10, places=4)

    def test_two_parallel_edges_mttf(self):
        """Two parallel links: MTTF = 1.5 / lambda."""
        net = NetworkGraph()
        # 0 to 1 with two parallel paths through 2 and 3
        net.add_edge(0, 2, Fraction(1, 1))
        net.add_edge(2, 1, Fraction(1, 1))
        net.add_edge(0, 3, Fraction(1, 1))
        net.add_edge(3, 1, Fraction(1, 1))
        # Or more simply, multi-edge representation in NetworkGraph
        # Let's test with a direct 3-node diamond
        # Paths: 0-2-1 and 0-3-1
        # When each of the 4 edges has hazard rate lambda:
        # Path 1 operates with e^(-2 lambda t), Path 2 with e^(-2 lambda t)
        # R(t) = 2 e^(-2 lambda t) - e^(-4 lambda t)
        # MTTF = 2 / (2 lambda) - 1 / (4 lambda) = 1/lambda - 0.25/lambda = 0.75 / lambda
        lam = 0.01
        res = evaluate_temporal_reliability(net, 0, 1, hazard_rate_per_hour=lam)
        self.assertEqual(res.mttf_exact, Fraction(75, 1))  # 0.75 / 0.01 = 75 hours
        self.assertAlmostEqual(res.mttf_hours, 75.0)

    def test_wheatstone_bridge_exact_mttf(self):
        """Wheatstone bridge exact analytic MTTF = 49 / (60 * lambda)."""
        net, s, t = build_wheatstone_bridge(p=Fraction(9, 10))
        lam = 0.001  # 1 failure per 1000 hours
        res = evaluate_temporal_reliability(net, s, t, hazard_rate_per_hour=lam)

        # Exact formula: 49 / (60 * 0.001) = 49 / 0.06 = 4900 / 6 = 2450 / 3
        expected_exact = Fraction(49, 60) / Fraction(1, 1000)
        self.assertEqual(res.mttf_exact, expected_exact)
        self.assertAlmostEqual(res.mttf_hours, float(expected_exact), places=5)

    def test_simpson_quadrature_oracle_agreement(self):
        """Verify algebraic MTTF matches Simpson's rule quadrature on grid_2x3 and grid_2x4."""
        for cols in [3, 4]:
            net, s, t = build_grid_network(rows=2, cols=cols, p=Fraction(9, 10))
            lam = 0.0005
            res = evaluate_temporal_reliability(net, s, t, hazard_rate_per_hour=lam)
            quad_mttf = numerical_quadrature_mttf_oracle(res.polynomial, hazard_rate_per_hour=lam)

            rel_err = abs(res.mttf_hours - quad_mttf) / res.mttf_hours
            self.assertLess(rel_err, 1e-4, f"Quadrature mismatch on grid_2x{cols}: {res.mttf_hours} vs {quad_mttf}")

    def test_quantile_lifetime_inversion(self):
        """Verify B10 and B1 life evaluations invert R(t) accurately."""
        net, s, t = build_grid_network(rows=2, cols=3, p=Fraction(9, 10))
        lam = 0.0001
        res = evaluate_temporal_reliability(net, s, t, hazard_rate_per_hour=lam)

        # Check R(t_B10) == 0.90
        x_b10 = math.exp(-lam * res.b10_life_hours)
        r_b10 = res.polynomial.evaluate(x_b10)
        self.assertAlmostEqual(r_b10, 0.90, places=4)

        # Check R(t_B1) == 0.99
        x_b1 = math.exp(-lam * res.b1_life_hours)
        r_b1 = res.polynomial.evaluate(x_b1)
        self.assertAlmostEqual(r_b1, 0.99, places=4)

    def test_barbell_temporal_reliability(self):
        """Barbell network (k=3, bridge=1) matching Simpson's quadrature oracle."""
        net, s, t = build_barbell_network(cluster_size=3)
        lam = 0.0002
        res = evaluate_temporal_reliability(net, s, t, hazard_rate_per_hour=lam)
        quad_mttf = numerical_quadrature_mttf_oracle(res.polynomial, hazard_rate_per_hour=lam)
        rel_err = abs(res.mttf_hours - quad_mttf) / res.mttf_hours
        self.assertLess(rel_err, 1e-4)

    def test_grid_3x3_temporal_reliability(self):
        """Grid 3x3 (12 edges) matching Simpson's quadrature oracle."""
        net, s, t = build_grid_network(rows=3, cols=3, p=Fraction(9, 10))
        lam = 0.0001
        res = evaluate_temporal_reliability(net, s, t, hazard_rate_per_hour=lam)
        quad_mttf = numerical_quadrature_mttf_oracle(res.polynomial, hazard_rate_per_hour=lam)
        rel_err = abs(res.mttf_hours - quad_mttf) / res.mttf_hours
        self.assertLess(rel_err, 1e-4)



if __name__ == "__main__":
    unittest.main()
