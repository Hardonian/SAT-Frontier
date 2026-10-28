import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from sat_frontier.core import Formula, oracle, solve
from sat_frontier.crosscheck import transformations
from sat_frontier.experiment import isolated
from sat_frontier.independent import count, minimize
from verify_evidence import verify

ROOT = Path(__file__).resolve().parents[1]


class MetamorphicTests(unittest.TestCase):
    def test_transformations_against_truth_table_and_solver(self):
        for f in (Formula(4, ((1, -2), (2, 3), (-3, 4))),
                  Formula(3, ((1,), (-1,))), Formula(3, ())):
            original = oracle(f)
            for name, (variant, factor) in transformations(f).items():
                with self.subTest(name=name, f=f):
                    self.assertEqual(oracle(variant), original*factor)
                    self.assertEqual(solve(variant)["count"], original*factor)

    def test_minimization_is_deterministic(self):
        f = Formula(4, ((1, 2), (3, 4), (-1, 3)))
        predicate = lambda g: any(1 in c for c in g.clauses)
        self.assertEqual(minimize(f, predicate), Formula(4, ((1,),)))
        self.assertEqual(minimize(f, predicate), minimize(f, predicate))
        with self.assertRaises(ValueError):
            minimize(f, lambda g: False)


class CounterProcessTests(unittest.TestCase):
    def make_binary(self, directory, body):
        p = Path(directory)/"fixture"
        p.write_text("#!" + sys.executable + "\n" + body + "\n")
        p.chmod(0o755)
        return p

    def test_process_failures_and_timeout(self):
        f = Formula(2, ((1, 2),))
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(count(Path(d)/"missing", f)["reason"], "missing_binary")
            p = self.make_binary(d, "print('not a count')")
            self.assertEqual(count(p, f)["reason"], "malformed_output")
            p = self.make_binary(d, "import os, signal; os.kill(os.getpid(), signal.SIGKILL)")
            crash = count(p, f)
            self.assertEqual(crash["reason"], "process_exit")
            self.assertLess(crash["returncode"], 0)
            p = self.make_binary(d, "import time; time.sleep(10)")
            timeout = count(p, f, seconds=0.1)
            self.assertEqual(timeout["status"], "unknown")
            self.assertIsNone(timeout["count"])
            self.assertLess(timeout["wall_seconds"], 2)
            p = self.make_binary(d, "print('# solutions\\n3\\n# END')")
            self.assertEqual(count(p, f)["count"], 3)

    @unittest.skipUnless(sys.platform.startswith("linux"), "RLIMIT_AS and wait4 are Linux-specific")
    def test_resource_limits_real_process(self):
        f = Formula(2, ((1, 2),))
        with tempfile.TemporaryDirectory() as d:
            p = self.make_binary(d, "data = bytearray(200 * 1024 * 1024); print('# solutions\\n3\\n# END')")
            r = count(p, f, memory_bytes=64*1024*1024)
            self.assertEqual(r["reason"], "process_exit")
            self.assertEqual(r["memory_limit"], "rlimit_as")
            self.assertGreater(r["peak_rss_kib"], 0)
        r = isolated(f, "combined", 2, 1000, 100, 256*1024*1024)
        self.assertEqual(r["count"], 3)
        self.assertEqual(r["memory_limit"], "rlimit_as")
        self.assertGreater(r["peak_rss_kib"], 0)

    def test_unsupported_memory_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.make_binary(d, "print('hello')")
            with patch("sat_frontier.independent.sys.platform", "unsupported"):
                self.assertEqual(count(p, Formula(1, ()), memory_bytes=100)["reason"], "memory_limit_unsupported")

    def test_real_counter_when_explicitly_provided(self):
        binary = os.environ.get("SAT_FRONTIER_SHARPSAT")
        if not binary:
            self.skipTest("SAT_FRONTIER_SHARPSAT not configured; independent executable integration not run")
        for f in (Formula(5, ((1, 2), (3, 4))), Formula(3, ((1,), (-1,))),
                  Formula(5, ((1, 2), (2, -3), (-1, 4)))):
            r = count(binary, f, memory_bytes=536870912)
            self.assertEqual(r["status"], "exact", r)
            self.assertEqual(r["count"], oracle(f))


class LegacyEvidenceTests(unittest.TestCase):
    def test_explicit_historical_root_preserves_checks(self):
        run = ROOT/"evidence/smoke-train"
        with tempfile.TemporaryDirectory() as d:
            with zipfile.ZipFile(ROOT/"artifacts/bootstrap/sat-frontier-v0.1.0.zip") as z:
                for name in z.namelist():
                    if name.startswith("sat-frontier/sat_frontier/") and name.endswith(".py"):
                        (Path(d)/Path(name).relative_to("sat-frontier")).parent.mkdir(parents=True, exist_ok=True)
                        (Path(d)/Path(name).relative_to("sat-frontier")).write_bytes(z.read(name))
            self.assertEqual(verify(run, d)["runs"], 160)
            with self.assertRaisesRegex(ValueError, "source hash mismatch"):
                verify(run)
            (Path(d)/"sat_frontier/core.py").write_text("tampered")
            with self.assertRaisesRegex(ValueError, "source hash mismatch"):
                verify(run, d)
