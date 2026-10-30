import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('campaign_harness', ROOT / 'scripts/run_epyc_cut_campaign.py')
campaign = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign)


class CampaignSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.inputs = self.base / 'input'
        self.inputs.mkdir()
        (self.inputs / 'tiny.cnf').write_text('p cnf 2 1\n1 2 0\n')
        self.output = self.base / 'evidence'
        self.args = ['campaign', '--instances-dir', str(self.inputs), '--evidence-dir', str(self.output),
                     '--workers', '1', '--depths', '0', '1']

    def run_campaign(self, *extra):
        with patch.object(sys, 'argv', self.args + list(extra)), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return campaign.main()

    def test_dry_run_does_not_create_directory(self):
        self.run_campaign('--dry-run')
        self.assertFalse(self.output.exists())

    def test_existing_evidence_is_never_overwritten(self):
        self.output.mkdir()
        sentinel = self.output / 'manifest.json'
        sentinel.write_text('untouched')
        with self.assertRaises(FileExistsError):
            self.run_campaign()
        self.assertEqual(sentinel.read_text(), 'untouched')

    def test_real_small_campaign_and_generic_verifier(self):
        self.assertEqual(self.run_campaign(), 0)
        rows = [json.loads(line) for line in (self.output / 'runs.jsonl').read_text().splitlines()]
        self.assertEqual([r['count'] for r in rows], [3, 3])
        self.assertTrue(all(r['search_nodes'] >= 0 and r['cubes_per_second'] > 0 for r in rows))
        summary = json.loads((self.output / 'summary.json').read_text())
        self.assertEqual(summary['cross_depth_comparisons'], 1)
        check = subprocess.run([sys.executable, str(ROOT / 'verify_evidence.py'), str(self.output)], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        result = self.output / rows[0]['result_path']
        result.write_text('tampered')
        check = subprocess.run([sys.executable, str(ROOT / 'verify_evidence.py'), str(self.output)], capture_output=True, text=True)
        self.assertNotEqual(check.returncode, 0)

    def test_runner_crash_is_not_unknown_and_logs_survive(self):
        failure = subprocess.CompletedProcess([], 9, stdout='partial', stderr='crashed')
        with patch.object(campaign.subprocess, 'run', return_value=failure):
            self.assertEqual(self.run_campaign(), 1)
        self.assertFalse((self.output / 'manifest.json').exists())
        log = json.loads(next((self.output / 'logs').glob('*.json')).read_text())
        self.assertEqual((log['returncode'], log['stderr']), (9, 'crashed'))

    def test_result_status_and_cube_invariants_fail_closed(self):
        result = {'status': 'exact', 'results': [{'status': 'exact', 'nodes': 2, 'count': 3}],
                  'cubes_total': 1, 'cubes_incomplete': 0, 'total_nodes': 2, 'count': 3}
        self.assertEqual(campaign.validate_result(result, 0), ('unweighted', 3))
        with self.assertRaises(ValueError):
            campaign.validate_result(result, 2)
        result['total_nodes'] = 0
        with self.assertRaises(ValueError):
            campaign.validate_result(result, 0)


if __name__ == '__main__':
    unittest.main()
