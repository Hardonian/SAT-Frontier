import unittest
from sat_frontier.core import Formula, oracle, solve
from sat_frontier.generate import generate
from sat_frontier.separator import (
    find_separator_variable,
    generate_barbell,
    solve_separator,
)


class SeparatorTests(unittest.TestCase):
    def test_cut_vertex_detection(self):
        # Bridge graph: (1 or 2) and (2 or 3) -> variable 2 is the cut vertex
        cnf = ((1, 2), (2, 3))
        v = find_separator_variable(cnf, {1, 2, 3})
        self.assertEqual(v, 2)

        # Barbell graph: {1,2,3} connected to {5,6,7} via bridge 4
        cnf_barbell = ((1, 2), (2, 3), (3, 1), (3, 4), (4, 5), (5, 6), (6, 7), (7, 5))
        v_barbell = find_separator_variable(cnf_barbell, set(range(1, 8)))
        self.assertEqual(v_barbell, 4)

    def test_exact_count_preservation_against_oracle(self):
        # Test on varied small formulas against independent exhaustive oracle
        test_formulas = [
            Formula(4, ((1, -2), (2, 3), (-3, 4))),
            Formula(3, ((1,), (-1,))),
            Formula(4, ()),
            Formula(5, ((1, 2), (2, 3), (3, 4), (4, 5))),
            generate_barbell(3, 1, seed=101),
            generate_barbell(3, 2, seed=102),
            generate('random', 8, 3, seed=201),
            generate('planted', 8, 3, seed=202),
            generate('disconnected', 8, 3, seed=203),
            generate('contradictory', 8, 3, seed=204),
        ]
        for f in test_formulas:
            with self.subTest(n=f.n, clauses=len(f.clauses)):
                expected = oracle(f)
                r_sep = solve_separator(f)
                r_comb = solve(f, 'combined')
                self.assertEqual(r_sep['status'], 'exact')
                self.assertEqual(r_sep['count'], expected)
                self.assertEqual(r_comb['count'], expected)

    def test_barbell_search_advantage(self):
        # On a barbell graph with 2 clusters of 5 vars and a 1-var bridge (11 vars total)
        f = generate_barbell(5, 1, seed=999)
        r_comb = solve(f, 'combined')
        r_sep = solve_separator(f)

        self.assertEqual(r_comb['count'], r_sep['count'])
        # Separator branching specifically targets the bottleneck bridge, inducing more component splits
        self.assertGreaterEqual(r_sep['component_splits'], r_comb['component_splits'])

    def test_invalid_budgets(self):
        f = Formula(2, ((1, 2),))
        with self.assertRaises(ValueError):
            solve_separator(f, seconds=-1)
        with self.assertRaises(ValueError):
            solve_separator(f, max_nodes=0)
        with self.assertRaises(ValueError):
            solve_separator(f, cache_limit=-1)

    def test_node_limit_unknown(self):
        f = generate('random', 12, 4, seed=555)
        r = solve_separator(f, max_nodes=2)
        self.assertEqual(r['status'], 'unknown')
        self.assertEqual(r['reason'], 'node_limit')
        self.assertIsNone(r['count'])


if __name__ == '__main__':
    unittest.main()

