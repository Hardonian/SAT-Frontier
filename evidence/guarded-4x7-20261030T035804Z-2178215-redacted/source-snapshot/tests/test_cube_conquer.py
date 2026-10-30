"""Tests for parallel Cube-and-Conquer lookahead solver."""
import unittest
import json
import tempfile
from fractions import Fraction
from pathlib import Path

from sat_frontier.core import Formula, oracle, solve
from sat_frontier.cube_conquer import generate_cubes, parallel_cube_and_conquer, parallel_cube_and_conquer_wmc
from sat_frontier.generate import generate
from sat_frontier.reliability import build_wheatstone_bridge, wheatstone_analytic
from sat_frontier.epyc_runner import load_formula
from sat_frontier.wmc import WeightedFormula, parse_weighted_dimacs, wmc_oracle


class CubeConquerTests(unittest.TestCase):

    def test_checkpoint_current_partition_only(self):
        f = Formula(6, ((1, 2), (3, 4)))
        self.assertEqual(oracle(f), 36)
        # The repository example has 18 models; changing budget formerly doubled it to 36.
        from sat_frontier.core import parse_dimacs
        f = parse_dimacs(Path('examples/two-components.cnf').read_text())
        self.assertEqual(oracle(f), 18)
        with tempfile.TemporaryDirectory() as directory:
            for depth, budget in [(2, 50000), (2, 50001), (2, 50001), (1, 50001), (3, 50001)]:
                result = parallel_cube_and_conquer(f, depth=depth, num_workers=2,
                                                    max_nodes_per_cube=budget, checkpoint_dir=directory)
                self.assertEqual(result['count'], 18)
                self.assertEqual(result['status'], 'exact')
                self.assertEqual(len(result['results']), result['cubes_total'])
            # A previously incomplete cube must be retried, not treated as permanent.
            for path in Path(directory).glob('*.json'):
                record = json.loads(path.read_text())
                record['status'] = 'unknown'
                record['count'] = None
                path.write_text(json.dumps(record))
            result = parallel_cube_and_conquer(f, depth=2, num_workers=2,
                                                max_nodes_per_cube=50001, checkpoint_dir=directory)
            self.assertEqual(result['count'], 18)

    def test_weighted_parser_and_resume(self):
        text = 'p cnf 2 3\nc p weight 1 1/3\nc p weight -1 2/3\n1\n2 0 0 -1 0\n'
        wf = parse_weighted_dimacs(text)
        self.assertEqual(wf.clauses, [[1, 2], [], [-1]])
        self.assertEqual(wmc_oracle(wf), 0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.cnf'
            path.write_text(text)
            loaded, weighted = load_formula(path)
            self.assertTrue(weighted)
            self.assertEqual(loaded.clauses, wf.clauses)
            for budget in (50000, 50001, 50001):
                result = parallel_cube_and_conquer_wmc(loaded, depth=2, num_workers=2,
                                                        max_nodes_per_cube=budget,
                                                        checkpoint_dir=Path(directory) / 'ck')
                self.assertEqual(result['status'], 'exact')
                self.assertEqual(result['weight_fraction'], '0')
                self.assertEqual(len(result['results']), result['cubes_total'])
            positive = WeightedFormula([[1, 2]], n_vars=2,
                                       weights={1: Fraction(1, 3), -1: Fraction(2, 3)})
            for depth, budget in [(1, 50000), (1, 50001), (2, 50001)]:
                result = parallel_cube_and_conquer_wmc(positive, depth=depth, num_workers=2,
                                                        max_nodes_per_cube=budget,
                                                        checkpoint_dir=Path(directory) / 'ck')
                self.assertEqual(Fraction(result['weight_fraction']), wmc_oracle(positive))

    def test_duplicate_priority_variables_do_not_duplicate_cubes(self):
        cubes = generate_cubes([[1, 2]], 2, depth=2, priority_vars=[1, 1, 2])
        self.assertEqual(set(cubes), {(1, 2), (1, -2), (-1, 2), (-1, -2)})

    def test_cube_generation_properties(self):
        """Verify cube generation creates 2^d disjoint cubes."""
        clauses = [[1, 2], [-1, 3], [2, -3], [4, -5]]
        cubes = generate_cubes(clauses, n_vars=5, depth=3)
        self.assertEqual(len(cubes), 8)
        # All cubes must be unique
        self.assertEqual(len(set(cubes)), 8)
        for c in cubes:
            self.assertEqual(len(c), 3)

    def test_unweighted_cube_and_conquer_matches_oracle(self):
        """Verify parallel Cube-and-Conquer exact count matches oracle on random 3-SAT."""
        f = generate('random', n=10, ratio=3.0, seed=42)
        expected_oracle = oracle(f)
        res_sequential = solve(f, algorithm='combined')

        self.assertEqual(res_sequential['count'], expected_oracle)

        # Test with 2 workers and depth 2 (4 cubes)
        res_parallel = parallel_cube_and_conquer(f, depth=2, num_workers=2)
        self.assertEqual(res_parallel['status'], 'exact')
        self.assertEqual(res_parallel['count'], expected_oracle)
        self.assertEqual(res_parallel['cubes_total'], 4)
        self.assertEqual(res_parallel['cubes_incomplete'], 0)

    def test_weighted_cube_and_conquer_matches_analytic(self):
        """Verify weighted parallel Cube-and-Conquer matches analytic Wheatstone reliability."""
        p_val = Fraction(9, 10)
        net, s, t = build_wheatstone_bridge(p=p_val)
        wf = net.to_weighted_cnf(s, t)
        expected = wheatstone_analytic(p_val)

        res_parallel = parallel_cube_and_conquer_wmc(wf, depth=2, num_workers=2)
        self.assertEqual(res_parallel['status'], 'exact')
        self.assertEqual(Fraction(res_parallel['weight_fraction']), expected)
        self.assertEqual(res_parallel['cubes_total'], 4)
        self.assertEqual(res_parallel['cubes_incomplete'], 0)


if __name__ == '__main__':
    unittest.main()
