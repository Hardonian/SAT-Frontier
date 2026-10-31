"""Unit and Metamorphic Tests for Weibull Aging and Wear-Out Reliability Engine."""
import math
import unittest
from fractions import Fraction

from sat_frontier.poly_wmc import ReliabilityPolynomial
from sat_frontier.weibull_reliability import (
    audit_weibull_reliability,
    compute_weibull_b_life,
    compute_weibull_mttf,
    weibull_quadrature_oracle,
)


class TestWeibullReliability(unittest.TestCase):
    """Test suite for Theorem 11 (Generalized Weibull MTTF Integration)."""

    def test_single_edge_weibull(self):
        """Single link: R(x) = x. Analytic MTTF = Gamma(1 + 1/beta) / lambda."""
        # P(x) = x with 1 edge: c = [0, 1]
        poly = ReliabilityPolynomial([0, 1])
        lam = 1e-4

        # beta = 1.0 (Exponential): MTTF = 1 / lambda = 10,000 hrs
        mttf_1, var_1 = compute_weibull_mttf(poly, beta=1.0, lambda_per_hour=lam)
        self.assertAlmostEqual(mttf_1, 10_000.0, places=4)
        self.assertAlmostEqual(math.sqrt(var_1), 10_000.0, places=4)

        # beta = 2.0 (Rayleigh wearout): MTTF = sqrt(pi) / (2 * lambda) = 8,862.269 hrs
        mttf_2, var_2 = compute_weibull_mttf(poly, beta=2.0, lambda_per_hour=lam)
        expected_2 = (math.sqrt(math.pi) / 2.0) / lam
        self.assertAlmostEqual(mttf_2, expected_2, places=3)

        # Independent Simpson quadrature check
        quad_2 = weibull_quadrature_oracle(poly, beta=2.0, lambda_per_hour=lam)
        rel_err = abs(mttf_2 - quad_2) / mttf_2
        self.assertLess(rel_err, 1e-4)

    def test_two_parallel_edges_weibull(self):
        """Two parallel links: P(x) = 2x - x^2.

        At beta=1: MTTF = (2 - 1/2) / lambda = 1.5 / lambda.
        At beta=2: MTTF = (sqrt(pi)/2 / lambda) * (2 - 1/sqrt(2)).
        """
        # Two edges: c0=0, c1=0, c2=1 => in Bernstein basis: 2x(1-x) + x^2 = 2x - x^2
        # c = [0, 0, 1] (state with 2 surviving edges is operational)
        # Actually in Bernstein: c0=0, c1=2 (two states with 1 edge work), c2=1 (both work)
        poly = ReliabilityPolynomial([0, 2, 1])
        lam = 1e-4

        # Exponential beta = 1: 15,000 hrs
        mttf_1, _ = compute_weibull_mttf(poly, beta=1.0, lambda_per_hour=lam)
        self.assertAlmostEqual(mttf_1, 15_000.0, places=4)

        # Rayleigh beta = 2
        mttf_2, _ = compute_weibull_mttf(poly, beta=2.0, lambda_per_hour=lam)
        expected_2 = (math.sqrt(math.pi) / 2.0 / lam) * (2.0 - 1.0 / math.sqrt(2.0))
        self.assertAlmostEqual(mttf_2, expected_2, places=3)

        # Quadrature verification
        quad_2 = weibull_quadrature_oracle(poly, beta=2.0, lambda_per_hour=lam)
        rel_err = abs(mttf_2 - quad_2) / mttf_2
        self.assertLess(rel_err, 1e-4)

    def test_wheatstone_bridge_weibull(self):
        """Wheatstone bridge network under various aging shapes beta in {1.0, 1.5, 2.0, 3.0}."""
        # Bridge has 5 edges. Standard coefficients c_k:
        # k=0:0, k=1:0, k=2:0, k=3:4, k=4:5, k=5:1
        poly = ReliabilityPolynomial([0, 0, 0, 4, 5, 1])
        lam = 2e-4

        for beta in [1.0, 1.5, 2.0, 2.5, 3.0]:
            mttf, var = compute_weibull_mttf(poly, beta=beta, lambda_per_hour=lam)
            self.assertGreater(mttf, 0.0)
            self.assertGreater(var, 0.0)

            # Independent quadrature oracle
            quad = weibull_quadrature_oracle(poly, beta=beta, lambda_per_hour=lam)
            rel_err = abs(mttf - quad) / mttf
            self.assertLess(rel_err, 1e-3, f"Failed at beta={beta}: mttf={mttf}, quad={quad}")

    def test_quantile_weibull_b_life(self):
        """Verify B10 and B1 life evaluations accurately invert continuous R(t)."""
        poly = ReliabilityPolynomial([0, 2, 1])
        lam = 1e-4
        beta = 2.0

        b10 = compute_weibull_b_life(poly, beta=beta, lambda_per_hour=lam, target_unreliability=0.10)
        b1 = compute_weibull_b_life(poly, beta=beta, lambda_per_hour=lam, target_unreliability=0.01)

        self.assertGreater(b10, b1)  # B10 lifetime is longer than B1

        # Check R(b10) == 0.90
        x_10 = math.exp(-((lam * b10) ** beta))
        r_10 = poly.evaluate(x_10)
        self.assertAlmostEqual(r_10, 0.90, places=4)

        # Check R(b1) == 0.99
        x_1 = math.exp(-((lam * b1) ** beta))
        r_1 = poly.evaluate(x_1)
        self.assertAlmostEqual(r_1, 0.99, places=4)

    def test_invalid_parameters(self):
        """Reject non-positive beta or lambda."""
        poly = ReliabilityPolynomial([0, 1])
        with self.assertRaises(ValueError):
            compute_weibull_mttf(poly, beta=0.0, lambda_per_hour=1e-4)
        with self.assertRaises(ValueError):
            compute_weibull_mttf(poly, beta=-1.5, lambda_per_hour=1e-4)
        with self.assertRaises(ValueError):
            compute_weibull_mttf(poly, beta=2.0, lambda_per_hour=0.0)


if __name__ == "__main__":
    unittest.main()
