"""Tests for parallel Cube-and-Conquer lookahead solver."""
import unittest
from fractions import Fraction

from sat_frontier.core import Formula, oracle, solve
from sat_frontier.cube_conquer import generate_cubes, parallel_cube_and_conquer, parallel_cube_and_conquer_wmc
from sat_frontier.generate import generate
from sat_frontier.reliability import build_wheatstone_bridge, wheatstone_analytic


class CubeConquerTests(unittest.TestCase):

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
