"""Unit and metamorphic tests for Algebraic Model Counting over Z[x] (Hypothesis H11)."""
import unittest
from fractions import Fraction

from sat_frontier.cut_compiler import to_cut_cnf
from sat_frontier.poly_wmc import (
    ReliabilityPolynomial,
    brute_force_poly_oracle,
    compute_reliability_polynomial,
    poly_add,
    poly_mul,
)
from sat_frontier.reliability import NetworkGraph, wheatstone_analytic
from sat_frontier.wmc import wmc_solve


class PolyWMCTests(unittest.TestCase):

    def test_poly_arithmetic(self):
        """Verify polynomial addition and discrete convolution in Z[x]."""
        # (1 + 2x) * (3 + 4x) = 3 + 10x + 8x^2
        p1 = [1, 2]
        p2 = [3, 4]
        self.assertEqual(poly_mul(p1, p2), [3, 10, 8])

        # (1 + 2x) + (3 + 4x + 5x^2) = 4 + 6x + 5x^2
        p3 = [3, 4, 5]
        self.assertEqual(poly_add(p1, p3), [4, 6, 5])

        # Zero multiplication
        self.assertEqual(poly_mul(p1, [0]), [0])

    def test_wheatstone_bridge_polynomial_analytic(self):
        """Verify exact polynomial on Wheatstone bridge matches closed-form analytic formula."""
        net = NetworkGraph()
        # 1-2, 1-3, 2-3, 2-4, 3-4
        net.add_edge(1, 2, prob=Fraction(9, 10))
        net.add_edge(1, 3, prob=Fraction(9, 10))
        net.add_edge(2, 3, prob=Fraction(9, 10))
        net.add_edge(2, 4, prob=Fraction(9, 10))
        net.add_edge(3, 4, prob=Fraction(9, 10))

        poly, status, nodes, dt = compute_reliability_polynomial(net, 1, 4)
        self.assertEqual(status, "exact")

        # Closed form: 2x^2 + 8x^3 + 5x^4 + x^5
        expected_coeffs = [0, 0, 2, 8, 5, 1]
        self.assertEqual(poly.coefficients, expected_coeffs)
        self.assertEqual(poly.total_connected_subgraphs, 16)

        # Evaluate at p=0.9
        p = Fraction(9, 10)
        r_poly = poly.evaluate(p)
        r_analytic = wheatstone_analytic(p)
        self.assertEqual(r_poly, r_analytic)

    def test_triangle_poly_matches_brute_force(self):
        """Verify triangle graph polynomial matches independent brute-force oracle."""
        net = NetworkGraph()
        net.add_edge(1, 2, prob=Fraction(9, 10))
        net.add_edge(2, 3, prob=Fraction(9, 10))
        net.add_edge(1, 3, prob=Fraction(9, 10))

        poly, status, _, _ = compute_reliability_polynomial(net, 1, 3)
        self.assertEqual(status, "exact")

        bf_coeffs = brute_force_poly_oracle(net, 1, 3)
        self.assertEqual(poly.coefficients, bf_coeffs)
        # Paths of length 1: edge (1,3). Paths of length 2: (1,2)+(2,3).
        # c_1 = 1, c_2 = 3, c_3 = 1
        self.assertEqual(poly.coefficients, [0, 1, 3, 1])

    def test_c4_cycle_poly_matches_brute_force(self):
        """Verify 4-cycle graph polynomial matches independent brute-force oracle."""
        net = NetworkGraph()
        for u, v in [(1, 2), (2, 3), (3, 4), (4, 1)]:
            net.add_edge(u, v, prob=Fraction(9, 10))

        poly, status, _, _ = compute_reliability_polynomial(net, 1, 3)
        self.assertEqual(status, "exact")

        bf_coeffs = brute_force_poly_oracle(net, 1, 3)
        self.assertEqual(poly.coefficients, bf_coeffs)

    def test_k4_complete_poly_matches_brute_force(self):
        """Verify K4 complete graph polynomial matches independent brute-force oracle."""
        net = NetworkGraph()
        edges = [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]
        for u, v in edges:
            net.add_edge(u, v, prob=Fraction(9, 10))

        poly, status, _, _ = compute_reliability_polynomial(net, 1, 4)
        self.assertEqual(status, "exact")

        bf_coeffs = brute_force_poly_oracle(net, 1, 4)
        self.assertEqual(poly.coefficients, bf_coeffs)

    def test_grid_2x3_poly_matches_brute_force(self):
        """Verify 2x3 grid polynomial matches independent brute-force oracle."""
        net = NetworkGraph()
        edges = [(1, 2), (2, 3), (4, 5), (5, 6), (1, 4), (2, 5), (3, 6)]
        for u, v in edges:
            net.add_edge(u, v, prob=Fraction(9, 10))

        poly, status, _, _ = compute_reliability_polynomial(net, 1, 6)
        self.assertEqual(status, "exact")

        bf_coeffs = brute_force_poly_oracle(net, 1, 6)
        self.assertEqual(poly.coefficients, bf_coeffs)

    def test_susceptibility_matches_finite_difference(self):
        """Verify exact derivative dR/dp matches numerical finite difference."""
        # Polynomial: 2x^2 + 8x^3 + 5x^4 + x^5
        poly = ReliabilityPolynomial([0, 0, 2, 8, 5, 1])

        h = 1e-6
        for p in [0.2, 0.4, 0.6, 0.8]:
            deriv_exact = poly.susceptibility(p)
            deriv_num = (poly.evaluate(p + h) - poly.evaluate(p - h)) / (2 * h)
            self.assertAlmostEqual(deriv_exact, deriv_num, places=5)

    def test_point_evaluation_matches_cut_wmc_fraction(self):
        """Verify polynomial evaluated at p=0.95 matches exact fraction from WMC solver."""
        net = NetworkGraph()
        # 2x4 grid: 8 nodes, 10 edges
        cols = 4
        node_id = lambda r, c: r * cols + c + 1
        p_val = Fraction(95, 100)
        for r in range(2):
            for c in range(4):
                u = node_id(r, c)
                if c + 1 < 4:
                    net.add_edge(u, node_id(r, c + 1), prob=p_val)
                if r + 1 < 2:
                    net.add_edge(u, node_id(r + 1, c), prob=p_val)

        # Solve via polynomial
        poly, status, _, _ = compute_reliability_polynomial(net, 1, 8)
        self.assertEqual(status, "exact")
        r_from_poly = poly.evaluate(p_val)

        # Solve via standard cut WMC
        wf = to_cut_cnf(net, 1, 8)
        res_wmc = wmc_solve(wf)

        self.assertEqual(str(r_from_poly), res_wmc["weight_fraction"])

    def test_disconnected_terminals_yields_zero_poly(self):
        """Verify disconnected terminal pair yields all zero coefficients."""
        net = NetworkGraph()
        net.add_edge(1, 2, prob=Fraction(9, 10))
        net.add_edge(3, 4, prob=Fraction(9, 10))

        poly, status, _, _ = compute_reliability_polynomial(net, 1, 4)
        self.assertEqual(poly.total_connected_subgraphs, 0)
        self.assertTrue(all(c == 0 for c in poly.coefficients))


if __name__ == "__main__":
    unittest.main()

