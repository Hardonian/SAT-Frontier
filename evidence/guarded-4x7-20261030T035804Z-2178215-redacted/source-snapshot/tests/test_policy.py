import unittest
from sat_frontier.core import Formula, canonical, oracle, policy_scores, solve, validate_policy
from sat_frontier.generate import generate
from sat_frontier.policy_train import isolated, summarize, bootstrap


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.p = dict(occurrence=1, polarity=1, short_clause=1, component_size=1)

    def test_validation_closed_integer_schema(self):
        for p in ({}, dict(self.p, evil=1), dict(self.p, polarity=True),
                  dict(self.p, polarity=1.0), dict(self.p, occurrence=11),
                  dict(self.p, occurrence='__import__("os")'),
                  dict.fromkeys(self.p, 0)):
            with self.assertRaises(ValueError):
                validate_policy(p)
        with self.assertRaises(ValueError):
            solve(Formula(0, ()), 'baseline', branch_policy=self.p)

    def test_exact_feature_scores(self):
        cnf = canonical(((1, 2), (-1, 2, 3), (4, 5)))
        # Variable 1: 2 occurrences, 1 balanced, 1 short, component size 3.
        self.assertEqual(policy_scores(cnf, self.p), {1: 7, 2: 6, 3: 4, 4: 4, 5: 4})

    def test_oracle_and_repeatability(self):
        policies = [self.p, dict(self.p, short_clause=-3),
                    dict(occurrence=1, polarity=0, short_clause=0, component_size=0)]
        for seed in range(15):
            f = generate('random', 8, 3, seed + 70)
            expected = oracle(f)
            for policy in policies:
                a = solve(f, branch_policy=policy)
                b = solve(f, branch_policy=policy)
                self.assertEqual(a['count'], expected)
                self.assertEqual((a['count'], a['nodes']), (b['count'], b['nodes']))

    def test_component_term_is_constant_after_split(self):
        f = generate('random', 10, 3, 312)
        a = solve(f, branch_policy=dict(self.p, component_size=0))
        b = solve(f, branch_policy=self.p)
        self.assertEqual((a['count'], a['nodes']), (b['count'], b['nodes']))

    def test_node_budget_reason(self):
        r = solve(Formula(3, ((1, 2, 3),)), max_nodes=1, branch_policy=self.p)
        self.assertEqual((r['status'], r['count'], r['reason']), ('unknown', None, 'node_limit'))

    def test_isolated_policy(self):
        cfg = dict(seconds=1, max_nodes=100, cache_limit=20)
        r = isolated(Formula(3, ((1, 2),)), self.p, cfg)
        self.assertEqual((r['status'], r['count']), ('exact', 6))
        self.assertGreaterEqual(r['wall_seconds'], r['elapsed_seconds'])

    def test_paired_bootstrap_clusters_repeats(self):
        cfg = dict(families=['random'], candidates={'p': self.p}, seeds=[1, 2],
                   bootstrap_seed=1, bootstrap_samples=200)
        rows = []
        for seed in cfg['seeds']:
            for name in ('control', 'p'):
                for repeat in range(2):
                    status = 'unknown' if seed == 1 and name == 'p' else 'exact'
                    rows.append(dict(family='random', seed=seed, candidate=name,
                                     status=status, elapsed_seconds=1, wall_seconds=2,
                                     nodes=2, peak_rss_kib=3))
        summary = summarize(rows, cfg)['random']['p']
        self.assertEqual(summary['paired_solved_difference'], -0.5)
        self.assertEqual(summary['solved_regression_instances'], 1)
        self.assertEqual(summary['conditional_exact_pair_instances'], 1)
        self.assertEqual(bootstrap([3], 1, 10, sum), [3, 3])


if __name__ == '__main__':
    unittest.main()
