import multiprocessing as mp
import os
from pathlib import Path
import shutil
import signal
import tempfile
import unittest
from unittest.mock import patch

from sat_frontier import holdout_guard as guard


def _reserve_then_wait(path, ready):
    guard.reserve_once(path, 'a' * 64)
    ready.send(True)
    ready.close()
    if hasattr(signal, 'pause'):
        signal.pause()
    else:
        import time
        while True:
            time.sleep(1)


class HoldoutGuardTests(unittest.TestCase):
    def test_train_evidence_and_winner(self):
        winner = guard.verify_train_freeze()
        self.assertEqual(winner['candidate'], 'component')
        self.assertEqual(winner['weights'], dict(component_size=1, occurrence=1,
                                                polarity=1, short_clause=1))

    def _copy_freeze(self, root):
        source = guard.ROOT
        files = ['evidence/policy-train-v02/winner.json', 'evidence/policy-train-v02/manifest.json',
                 *guard.EXPECTED_SOURCE, *guard.VERIFIER_SOURCE]
        for relative in files:
            dst = root / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, dst)

    def test_winner_source_and_config_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_freeze(root)
            for relative in ['evidence/policy-train-v02/winner.json', 'evidence/policy-train-v02/manifest.json',
                             *guard.EXPECTED_SOURCE, *guard.VERIFIER_SOURCE]:
                path = root / relative
                before = path.read_bytes()
                path.write_bytes(before + b' ')
                with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, 'mismatch'):
                    guard.verify_train_freeze(root)
                path.write_bytes(before)

    def test_exact_content_overlap_and_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'renamed.cnf').write_bytes(b'p cnf 1 1\n1 0\n')
            prior = guard.prior_instance_hashes(root)
            with self.assertRaisesRegex(ValueError, 'overlaps'):
                guard.check_overlap([b'p cnf 1 1\n1 0\n'], prior)
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                guard.check_overlap([b'other', b'other'], prior)
            self.assertEqual(guard.check_overlap([b'new'], prior), {guard.digest(b'new')})
            with self.assertRaisesRegex(ValueError, 'empty'):
                guard.check_overlap([], prior)

    def test_reservation_is_exclusive_and_incomplete_is_consumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'claim'
            with patch.object(guard, '_fsync_dir', side_effect=OSError('injected interruption')):
                with self.assertRaises(OSError):
                    guard.reserve_once(path, 'a' * 64)
            self.assertTrue(path.is_dir())
            with self.assertRaises(FileExistsError):
                guard.reserve_once(path, 'a' * 64)

    def test_sigkill_after_reservation_cannot_reconsume(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'claim'
            ctx = mp.get_context('spawn')
            receiver, sender = ctx.Pipe(duplex=False)
            proc = ctx.Process(target=_reserve_then_wait, args=(path, sender))
            proc.start()
            sender.close()
            try:
                self.assertTrue(receiver.poll(10), 'child failed to reserve')
                self.assertTrue(receiver.recv())
                self.assertIsNotNone(proc.pid)
                if proc.pid is None:
                    self.fail('child process has no PID')
                if hasattr(signal, 'SIGKILL'):
                    os.kill(proc.pid, signal.SIGKILL)
                    proc.join(10)
                    self.assertEqual(proc.exitcode, -signal.SIGKILL)
                else:
                    proc.kill()
                    proc.join(10)
                    self.assertNotEqual(proc.exitcode, 0)
                with self.assertRaises(FileExistsError):
                    guard.reserve_once(path, 'a' * 64)
            finally:
                if proc.is_alive():
                    proc.kill()
                    proc.join()
                receiver.close()

    def test_bad_preregistration_does_not_consume(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'claim'
            with self.assertRaises(ValueError):
                guard.reserve_once(path, 'bad')
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
