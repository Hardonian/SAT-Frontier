import json
import random
import tempfile
import unittest
from pathlib import Path
from sat_frontier.core import Formula, ALGORITHMS, oracle, solve, parse_dimacs
from sat_frontier.generate import generate, FAMILIES
from sat_frontier.experiment import campaign, validate_config, isolated


class CountingTests(unittest.TestCase):
    def check_all(self, f, expected=None):
        if expected is None:
            expected = oracle(f)
        for name in ALGORITHMS:
            result = solve(f, name)
            self.assertEqual(result["status"], "exact", (f, name, result))
            self.assertEqual(result["count"], expected, (f, name, result))

    def test_empty(self):
        self.check_all(Formula(0, ()), 1)
        self.check_all(Formula(8, ()), 256)

    def test_empty_clause(self):
        self.check_all(Formula(3, ((),)), 0)

    def test_free_variables_and_units(self):
        self.check_all(Formula(5, ((1,), (2, 3))), 12)

    def test_tautology_and_duplicates(self):
        self.check_all(Formula(3, ((1, -1), (2, 2), (2,))), 4)

    def test_contradictory_units(self):
        self.check_all(Formula(4, ((1,), (-1,))), 0)

    def test_components(self):
        f = Formula(5, ((1, 2), (3, 4)))
        self.check_all(f, 18)
        self.assertGreater(solve(f)["component_splits"], 0)

    def test_no_pure_literal_model_loss(self):
        self.check_all(Formula(2, ((1, 2),)), 3)

    def test_exhaustive_two_variable_formulas(self):
        clauses = [(), (1,), (-1,), (2,), (-2,), (1, 2), (1, -2), (-1, 2), (-1, -2)]
        for mask in range(1 << len(clauses)):
            self.check_all(Formula(2, tuple(c for i, c in enumerate(clauses) if mask >> i & 1)))

    def test_random_mixed_width(self):
        rng = random.Random(7741)
        for _ in range(180):
            n = rng.randrange(1, 9)
            cs = tuple(tuple(rng.choice((-1, 1))*rng.randint(1, n)
                             for _ in range(rng.randrange(5)))
                       for _ in range(rng.randrange(15)))
            self.check_all(Formula(n, cs))

    def test_generators(self):
        for family in FAMILIES:
            for seed in range(10):
                f = generate(family, 8, 4, seed)
                self.assertEqual(f, generate(family, 8, 4, seed))
                self.check_all(f)
                if family == "planted":
                    self.assertGreater(oracle(f), 0)
                if family == "contradictory":
                    self.assertEqual(oracle(f), 0)

    def test_budget_unknown(self):
        r = solve(Formula(3, ((1, 2, 3),)), max_nodes=1)
        self.assertEqual(r["status"], "unknown")
        self.assertIsNone(r["count"])

    def test_invalid_budgets(self):
        for seconds in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                solve(Formula(0, ()), seconds=seconds)

    def test_cache_capacity_does_not_change_count(self):
        f = generate("disconnected", 12, 2, 8)
        for cap in (0, 1, 10):
            self.assertEqual(solve(f, cache_limit=cap)["count"], oracle(f))

    def test_oracle_limit(self):
        with self.assertRaises(ValueError):
            oracle(Formula(21, ()))

    def test_dimacs_roundtrip(self):
        f = Formula(3, ((1, -2), (), (3,)))
        self.assertEqual(parse_dimacs(f.dimacs()), f)
        self.assertEqual(parse_dimacs("c hi\np cnf 3 2\n1\n-2 0 3 0\n"),
                         Formula(3, ((1, -2), (3,))))

    def test_reject_malformed(self):
        for text in ("", "1 0", "p cnf 2 1\n3 0", "p cnf 2 1\n1",
                     "p cnf 2 2\n1 0", "p cnf -1 0", "p cnf 1 0\np cnf 1 0"):
            with self.assertRaises(ValueError, msg=text):
                parse_dimacs(text)


class RunnerTests(unittest.TestCase):
    def config(self):
        return json.loads((Path(__file__).resolve().parents[1]/"configs/smoke.json").read_text())

    def test_split_overlap_rejected(self):
        c = self.config()
        c["seeds"]["holdout"] = c["seeds"]["train"]
        with self.assertRaises(ValueError):
            validate_config(c)

    def test_run_cap(self):
        c = self.config()
        c["repeats"] = 10
        c["seeds"]["train"] = list(range(100))
        with self.assertRaises(ValueError):
            validate_config(c)

    def test_subprocess_result(self):
        r = isolated(Formula(2, ((1, 2),)), "combined", 1, 1000, 100)
        self.assertEqual(r["count"], 3)

    def test_campaign_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            c = self.config()
            c.update(sizes=[4], ratios=[2], families=["random"], algorithms=["baseline", "combined"])
            c["seeds"] = {"train": [11], "holdout": [1009]}
            path = root / "config.json"
            path.write_text(json.dumps(c))
            out = root / "run"
            r = campaign(path, out, "train")
            self.assertEqual(r["oracle_pass"], 2)
            manifest = json.loads((out/"manifest.json").read_text())
            self.assertEqual(manifest["status"], "complete")
            self.assertTrue(manifest["artifact_sha256"])
            with self.assertRaises(FileExistsError):
                campaign(path, out, "train")


if __name__ == "__main__":
    unittest.main()
