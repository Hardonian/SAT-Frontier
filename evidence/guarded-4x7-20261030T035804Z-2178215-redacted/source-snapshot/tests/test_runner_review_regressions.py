import importlib.util
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from sat_frontier.cube_conquer import _cube_signature
from sat_frontier.epyc_runner import load_formula
from sat_frontier.wmc import wmc_oracle

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('review_campaign', ROOT / 'scripts/run_epyc_cut_campaign.py')
campaign = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign)


class RunnerReviewRegressions(unittest.TestCase):
    def test_weight_comments_with_tabs_and_multiple_spaces_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'x.cnf'
            path.write_text('c\tp  weight 1 1/3 0\nc p weight -1 2/3 0\np cnf 1 1\n1 0\n')
            formula, weighted = load_formula(path)
            self.assertTrue(weighted)
            self.assertEqual(wmc_oracle(formula), Fraction(1, 3))

    def test_partition_rejects_duplicate_or_missing_tasks(self):
        data = {'status': 'exact', 'results': [
            {'cube': [1], 'status': 'exact', 'nodes': 1, 'count': 1},
            {'cube': [1], 'status': 'exact', 'nodes': 1, 'count': 1}],
            'cubes_total': 2, 'cubes_incomplete': 0, 'total_nodes': 2, 'count': 2}
        with self.assertRaisesRegex(ValueError, 'partition'):
            campaign.validate_result(data, 0, [(1,), (-1,)])
        data['results'][1]['cube'] = [-1]
        self.assertEqual(campaign.validate_result(data, 0, [(1,), (-1,)]), ('unweighted', 2))

    def test_checkpoint_signature_changes_with_source(self):
        args = ('p cnf 1 0\n', (1,), 'combined', 10.0, 500)
        self.assertNotEqual(_cube_signature(*args, 'old'), _cube_signature(*args, 'new'))


if __name__ == '__main__':
    unittest.main()
