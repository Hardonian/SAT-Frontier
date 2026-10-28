"""Tests for Weighted Model Counting (WMC) and Network Reliability analysis."""
import unittest
from fractions import Fraction
from sat_frontier.wmc import WeightedFormula, wmc_oracle, wmc_solve
from sat_frontier.reliability import (
    build_wheatstone_bridge,
    wheatstone_analytic,
    build_barbell_network,
    build_grid_network,
)


class WMCTests(unittest.TestCase):

    def test_wmc_oracle_exact_agreement(self):
        """Verify wmc_solve matches wmc_oracle on small weighted formulas."""
        clauses = [[1, 2], [-1, 3], [-2, -3]]
        weights = {
            1: Fraction(3, 10), -1: Fraction(7, 10),
            2: Fraction(6, 10), -2: Fraction(4, 10),
            3: Fraction(8, 10), -3: Fraction(2, 10),
        }
        wf = WeightedFormula(clauses, n_vars=3, weights=weights)
        oracle_w = wmc_oracle(wf)

        for algo in ['baseline_wmc', 'memo_wmc', 'components_wmc', 'combined_wmc', 'separator_wmc']:
            res = wmc_solve(wf, algorithm=algo)
            self.assertEqual(res['status'], 'exact')
            self.assertEqual(Fraction(res['weight_fraction']), oracle_w)

    def test_free_variables_scaling(self):
        """Free variables contribute (w(v) + w(-v)) to the weighted sum."""
        clauses = [[1]]
        weights = {
            1: Fraction(1, 2), -1: Fraction(1, 2),
            2: Fraction(3, 1), -2: Fraction(2, 1),  # Sum = 5
        }
        wf = WeightedFormula(clauses, n_vars=2, weights=weights)
        oracle_w = wmc_oracle(wf)
        self.assertEqual(oracle_w, Fraction(5, 2))

        res = wmc_solve(wf, algorithm='combined_wmc')
        self.assertEqual(Fraction(res['weight_fraction']), Fraction(5, 2))

    def test_wheatstone_bridge_analytic_verification(self):
        """Verify Wheatstone bridge network matches exact closed-form reliability."""
        for p_val in [Fraction(1, 10), Fraction(1, 2), Fraction(7, 10), Fraction(9, 10), Fraction(99, 100)]:
            net, s, t = build_wheatstone_bridge(p=p_val)
            wf = net.to_weighted_cnf(s, t)

            expected_analytic = wheatstone_analytic(p_val)
            oracle_w = wmc_oracle(wf)
            self.assertEqual(oracle_w, expected_analytic)

            res = wmc_solve(wf, algorithm='combined_wmc')
            self.assertEqual(res['status'], 'exact')
            self.assertEqual(Fraction(res['weight_fraction']), expected_analytic)

    def test_barbell_network_decomposition(self):
        """Verify barbell network exact count and component split on bridge edge."""
        net, s, t = build_barbell_network(cluster_size=3, p_cluster=Fraction(9, 10), p_bridge=Fraction(8, 10))
        wf = net.to_weighted_cnf(s, t)

        oracle_w = wmc_oracle(wf)
        res_baseline = wmc_solve(wf, algorithm='baseline_wmc')
        res_combined = wmc_solve(wf, algorithm='combined_wmc')
        res_sep = wmc_solve(wf, algorithm='separator_wmc')

        self.assertEqual(Fraction(res_baseline['weight_fraction']), oracle_w)
        self.assertEqual(Fraction(res_combined['weight_fraction']), oracle_w)
        self.assertEqual(Fraction(res_sep['weight_fraction']), oracle_w)

        # Component decomposition should record component splits
        self.assertGreater(res_combined['component_splits'], 0)

    def test_grid_network_exact_consistency(self):
        """Verify grid mesh network reliability is consistent across all solver variants."""
        net, s, t = build_grid_network(rows=2, cols=3, p=Fraction(85, 100))
        wf = net.to_weighted_cnf(s, t)

        results = {}
        for algo in ['baseline_wmc', 'memo_wmc', 'components_wmc', 'combined_wmc']:
            res = wmc_solve(wf, algorithm=algo)
            self.assertEqual(res['status'], 'exact')
            results[algo] = res['weight_fraction']

        # All variants must agree on the exact rational probability
        unique_fractions = set(results.values())
        self.assertEqual(len(unique_fractions), 1)


if __name__ == '__main__':
    unittest.main()

