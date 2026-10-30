import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/verify_historical_copy.py'
spec = importlib.util.spec_from_file_location('historical_copy', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HistoricalCopyTests(unittest.TestCase):
    def test_exact_reconstruction_and_reject_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'artifact'
            path.write_bytes(b'first\nsecond\n')
            expected = hashlib.sha256(b'first\r\nsecond\r\n').hexdigest()
            change = module.reconstruct(path, expected)
            self.assertEqual(path.read_bytes(), b'first\r\nsecond\r\n')
            self.assertEqual(change['reconstructed_sha256'], expected)
            self.assertIsNone(module.reconstruct(path, expected))
            path.write_bytes(b'tampered\n')
            with self.assertRaises(ValueError):
                module.reconstruct(path, expected)
            self.assertEqual(path.read_bytes(), b'tampered\n')

    def test_mixed_newlines_and_unsafe_path_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            path = root / 'artifact'
            path.write_bytes(b'a\r\nb\n')
            with self.assertRaises(ValueError):
                module.reconstruct(path, '0' * 64)
            with self.assertRaises(ValueError):
                module.checked_path(root, '../outside')
            os.symlink(root.parent, root / 'link')
            with self.assertRaises(ValueError):
                module.checked_path(root, 'link/outside')

    def test_existing_destination_and_repository_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d) / 'marker'
            marker.write_text('unchanged')
            for dest in (Path(d), ROOT / 'not-created-verification-copy'):
                p = subprocess.run([sys.executable, str(SCRIPT), str(dest)], capture_output=True)
                self.assertNotEqual(p.returncode, 0)
            self.assertEqual(marker.read_text(), 'unchanged')
            self.assertFalse((ROOT / 'not-created-verification-copy').exists())


if __name__ == '__main__':
    unittest.main()
