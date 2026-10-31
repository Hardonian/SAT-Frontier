import importlib.util
import json
from pathlib import Path
from fractions import Fraction
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'operations'))
from graph_transfer_oracle import transfer, brute

spec = importlib.util.spec_from_file_location('prepare', ROOT / 'scripts/prepare_epyc_cut_campaign.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class FixtureRegressionTests(unittest.TestCase):
    def test_chvatal_is_24_edge_four_regular_triangle_free(self):
        graph, _, _ = prepare.build_chvatal_graph()
        self.assertEqual((len(graph.adj), len(graph.edges)), (12, 24))
        neighbors = {u: {v for v, _ in ns} for u, ns in graph.adj.items()}
        self.assertEqual({len(ns) for ns in neighbors.values()}, {4})
        self.assertFalse(any(neighbors[u] & neighbors[v] for u, v in graph.edges))

    def test_barbell_generated_with_valid_probability_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'fresh'
            prepare.main(['--output-dir', str(output), '--only', 'barbell_6_bridge_6'])
            manifest = json.loads((output / 'manifest.json').read_text())
            self.assertEqual(set(manifest), {'barbell_6_bridge_6'})
            row = manifest['barbell_6_bridge_6']
            self.assertEqual((row['vertices'], row['edges']), (12, 31))
            self.assertEqual(set(row['edge_probabilities'].values()), {'9/10'})

    def test_generator_refuses_existing_directory_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            sentinel = output / 'sentinel'
            sentinel.write_text('preserve')
            with self.assertRaises(FileExistsError):
                prepare.main(['--output-dir', str(output), '--only', 'chvatal'])
            self.assertEqual(sentinel.read_text(), 'preserve')
            self.assertEqual({p.name for p in output.iterdir()}, {'sentinel'})

    def test_invalid_name_does_not_reserve_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'fresh'
            with self.assertRaises(SystemExit):
                prepare.main(['--output-dir', str(output), '--only', 'not-a-fixture'])
            self.assertFalse(output.exists())

    def test_independent_transfer_matches_brute_on_small_graphs(self):
        cases = [([(0, 1)], 0, 1),
                 ([(0, 1), (1, 2), (0, 2)], 0, 2),
                 ([(0, 1), (0, 2), (1, 3), (2, 3)], 0, 3),
                 ([(u, v) for u in range(4) for v in range(u + 1, 4)], 0, 3)]
        for edges, source, target in cases:
            for probabilities in ([Fraction(9, 10)] * len(edges),
                                  [Fraction((i % 3) + 1, 5) for i in range(len(edges))]):
                self.assertEqual(transfer(edges, source, target, probabilities)[0],
                                 brute(edges, source, target, probabilities))

    def test_signed_weights_are_weighted_sums_not_probabilities(self):
        edges = [(0, 1), (1, 2), (0, 2)]
        probabilities = [Fraction(3), Fraction(3), Fraction(9, 10)]
        self.assertEqual(transfer(edges, 0, 2, probabilities)[0],
                         brute(edges, 0, 2, probabilities))

    def test_original_fixture_hashes_unchanged(self):
        import hashlib
        folder = ROOT / 'instances/epyc-cut-frontier'
        for row in json.loads((folder / 'manifest.json').read_text()).values():
            self.assertEqual(hashlib.sha256((folder / row['file']).read_bytes()).hexdigest(), row['sha256'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
