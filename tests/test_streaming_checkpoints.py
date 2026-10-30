"""Interrupted real worker pools must leave reusable per-cube checkpoints."""
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from sat_frontier.core import Formula, oracle
from sat_frontier.wmc import WeightedFormula, wmc_oracle
from sat_frontier.cube_conquer import parallel_cube_and_conquer, parallel_cube_and_conquer_wmc


CHILD = '''
import sys, time
from fractions import Fraction
from pathlib import Path
from sat_frontier.core import Formula
from sat_frontier.wmc import WeightedFormula
import sat_frontier.cube_conquer as cc

if __name__ == '__main__':
    original = cc._save_checkpoint
    def save(*args):
        original(*args)
        Path(sys.argv[2]).write_text('saved')
        time.sleep(60)  # keep other results pending while parent is interrupted
    cc._save_checkpoint = save
    if sys.argv[3] == 'weighted':
        formula = WeightedFormula([[1, 2], [3, 4]], n_vars=4,
                                  weights={1: Fraction(1, 3), -1: Fraction(2, 3)})
        runner = cc.parallel_cube_and_conquer_wmc
    else:
        formula = Formula(4, [[1, 2], [3, 4]])
        runner = cc.parallel_cube_and_conquer
    runner(formula, depth=2, num_workers=2, checkpoint_dir=sys.argv[1])
'''


class OutOfOrderTests(unittest.TestCase):
    def test_reverse_completion_preserves_cube_signatures(self):
        class ReversePool:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def imap_unordered(self, fn, tasks, chunksize):
                self_chunksize = chunksize
                if self_chunksize != 1:
                    raise AssertionError('results must not be batched')
                return iter([fn(task) for task in reversed(tasks)])
        class Context:
            def Pool(self, processes):
                return ReversePool()
        f = Formula(4, [[1, 2], [3, 4]])
        with tempfile.TemporaryDirectory() as directory:
            with patch('sat_frontier.cube_conquer.get_context', return_value=Context()):
                result = parallel_cube_and_conquer(f, depth=2, num_workers=2, checkpoint_dir=directory)
            self.assertEqual(result['count'], oracle(f))
            with patch('sat_frontier.cube_conquer.get_context') as context:
                resumed = parallel_cube_and_conquer(f, depth=2, num_workers=2, checkpoint_dir=directory)
            context.return_value.Pool.assert_not_called()
            self.assertEqual(resumed['count'], oracle(f))
            self.assertEqual(len(resumed['results']), 4)


@unittest.skipUnless(os.name == 'posix', 'process-group termination requires POSIX')
class InterruptedCheckpointTests(unittest.TestCase):
    def test_interrupted_resume_weighted_and_unweighted(self):
        for weighted in (False, True):
            with self.subTest(weighted=weighted), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                child = root / 'child.py'
                child.write_text(CHILD)
                ck = root / 'checkpoints'
                marker = root / 'saved'
                env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
                proc = subprocess.Popen([sys.executable, str(child), str(ck), str(marker),
                                         'weighted' if weighted else 'plain'],
                                        env=env, start_new_session=True)
                try:
                    deadline = time.monotonic() + 15
                    while not marker.exists() and proc.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.02)
                    self.assertTrue(marker.exists(), 'first checkpoint was not published before timeout')
                finally:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=5)
                paths = list(ck.glob('*.json'))
                self.assertEqual(len(paths), 1)
                saved = json.loads(paths[0].read_text())
                self.assertEqual(saved['status'], 'exact')
                if weighted:
                    formula = WeightedFormula([[1, 2], [3, 4]], n_vars=4,
                                              weights={1: Fraction(1, 3), -1: Fraction(2, 3)})
                    runner, expected, key = parallel_cube_and_conquer_wmc, wmc_oracle(formula), 'weight_fraction'
                else:
                    formula = Formula(4, [[1, 2], [3, 4]])
                    runner, expected, key = parallel_cube_and_conquer, oracle(formula), 'count'
                # Existing exact checkpoint is not rewritten, and every cube is counted once.
                with patch('sat_frontier.cube_conquer._save_checkpoint', wraps=__import__(
                        'sat_frontier.cube_conquer', fromlist=['_save_checkpoint'])._save_checkpoint) as save:
                    result = runner(formula, depth=2, num_workers=2, checkpoint_dir=ck)
                self.assertEqual(save.call_count, 3)
                self.assertEqual(result['status'], 'exact')
                self.assertEqual(Fraction(result[key]), expected)
                self.assertEqual(len({tuple(r['cube']) for r in result['results']}), 4)
                self.assertEqual(len(list(ck.glob('*.json'))), 4)
                self.assertEqual(json.loads(paths[0].read_text()), saved)
