"""Tests for Tensor Network exact counting and WMC."""
import unittest
from fractions import Fraction

from sat_frontier.core import oracle, parse_dimacs
from sat_frontier.generate import generate
from sat_frontier.reliability import build_wheatstone_bridge, wheatstone_analytic
from sat_frontier.tensor_contract import HAS_NUMPY, HAS_TORCH, tensor_solve
from sat_frontier.wmc import WeightedFormula, wmc_oracle


class TensorContractTests(unittest.TestCase):

    def setUp(self):
        if not HAS_NUMPY and not HAS_TORCH:
            self.skipTest("NumPy or PyTorch required for tensor contraction tests.")

    def test_unweighted_tensor_contract_matches_oracle(self):
        """Verify tensor network contraction matches oracle count on random 3-SAT."""
        f = generate('random', n=8, ratio=3.0, seed=123)
        expected = oracle(f)

        # NumPy einsum mode
        res_numpy = tensor_solve(f, backend='numpy', mode='einsum')
        self.assertEqual(res_numpy['status'], 'exact')
        self.assertEqual(res_numpy['count'], expected)

        # NumPy bucket elimination mode
        res_bucket = tensor_solve(f, backend='numpy', mode='bucket_elimination')
        self.assertEqual(res_bucket['status'], 'exact')
        self.assertEqual(res_bucket['count'], expected)

        # PyTorch CPU mode
        if HAS_TORCH:
            res_torch = tensor_solve(f, backend='torch', device='cpu', mode='einsum')
            self.assertEqual(res_torch['status'], 'exact')
            self.assertEqual(res_torch['count'], expected)

    def test_weighted_tensor_contract_matches_wmc_oracle(self):
        """Verify weighted tensor contraction matches wmc_oracle."""
        clauses = [[1, 2], [-1, 3], [-2, -3]]
        weights = {
            1: Fraction(3, 10), -1: Fraction(7, 10),
            2: Fraction(6, 10), -2: Fraction(4, 10),
            3: Fraction(8, 10), -3: Fraction(2, 10),
        }
        wf = WeightedFormula(clauses, n_vars=3, weights=weights)
        expected = float(wmc_oracle(wf))

        res = tensor_solve(wf, weights=wf.weights, backend='numpy', mode='einsum')
        self.assertEqual(res['status'], 'exact')
        self.assertAlmostEqual(res['weight_float'], expected, places=7)

        res_b = tensor_solve(wf, weights=wf.weights, backend='numpy', mode='bucket_elimination')
        self.assertEqual(res_b['status'], 'exact')
        self.assertAlmostEqual(res_b['weight_float'], expected, places=7)

    def test_wheatstone_bridge_tensor_analytic(self):
        """Verify tensor network matches exact analytic reliability of Wheatstone bridge."""
        p_val = Fraction(9, 10)
        net, s, t = build_wheatstone_bridge(p=p_val)
        wf = net.to_weighted_cnf(s, t)
        expected = float(wheatstone_analytic(p_val))

        res = tensor_solve(wf, weights=wf.weights, backend='numpy', mode='einsum')
        self.assertEqual(res['status'], 'exact')
        self.assertAlmostEqual(res['weight_float'], expected, places=7)

    def test_free_variable_scaling(self):
        """Verify free variables scale count correctly in tensor network."""
        f = parse_dimacs("p cnf 3 1\n1 2 0\n")  # Variable 3 is free
        expected = oracle(f)  # (3 models for vars 1,2) * 2 = 6

        res_e = tensor_solve(f, backend='numpy', mode='einsum')
        self.assertEqual(res_e['count'], expected)

        res_b = tensor_solve(f, backend='numpy', mode='bucket_elimination')
        self.assertEqual(res_b['count'], expected)


if __name__ == '__main__':
    unittest.main()
