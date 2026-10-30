"""Unit tests for All-Pairs SLA Matrix and Topological Centrality (sat_frontier/enterprise/all_pairs.py)."""
from fractions import Fraction
import json
import unittest

from sat_frontier.enterprise import (
    EnterpriseTopology,
    compute_all_pairs_sla,
    generate_all_pairs_markdown_report,
    render_terminal_heatmap,
)


class TestAllPairsSLA(unittest.TestCase):
    def test_triangle_all_pairs(self):
        topo = EnterpriseTopology("TriangleMesh")
        topo.add_link("A", "B", availability=0.9)
        topo.add_link("B", "C", availability=0.9)
        topo.add_link("A", "C", availability=0.9)

        res = compute_all_pairs_sla(topo)
        self.assertEqual(len(res.nodes), 3)
        self.assertEqual(res.total_pairs_evaluated, 3)

        # In triangle with p=0.9: R(A, B) = p + p^2 - p^3 = 0.9 + 0.81 - 0.729 = 0.981
        self.assertEqual(res.matrix[("A", "B")], Fraction(981, 1000))
        self.assertEqual(res.matrix[("B", "C")], Fraction(981, 1000))
        self.assertEqual(res.matrix[("A", "C")], Fraction(981, 1000))

        # Self-availability is 1.0
        self.assertEqual(res.matrix[("A", "A")], Fraction(1, 1))

        # Node centrality is identical for symmetric triangle
        for n in ["A", "B", "C"]:
            self.assertAlmostEqual(res.node_centrality[n], 0.981, places=3)

    def test_line_bottleneck_all_pairs(self):
        topo = EnterpriseTopology("LineNetwork")
        # A - B - C - D with p=0.9 for each link
        topo.add_link("A", "B", availability=0.9)
        topo.add_link("B", "C", availability=0.9)
        topo.add_link("C", "D", availability=0.9)

        res = compute_all_pairs_sla(topo)
        self.assertEqual(res.total_pairs_evaluated, 6)

        # R(A, D) = 0.9^3 = 0.729
        self.assertEqual(res.matrix[("A", "D")], Fraction(729, 1000))
        self.assertEqual(res.diameter_reliability, Fraction(729, 1000))
        self.assertIn("A", res.diameter_pair)
        self.assertIn("D", res.diameter_pair)

        # Interior nodes B and C should have higher centrality than boundary nodes A and D
        self.assertGreater(res.node_centrality["B"], res.node_centrality["A"])
        self.assertGreater(res.node_centrality["C"], res.node_centrality["D"])

    def test_terminal_heatmap_and_reports(self):
        topo = EnterpriseTopology("DemoCloud")
        topo.add_link("Web", "App", availability=0.999)
        topo.add_link("App", "DB", availability=0.999)

        res = compute_all_pairs_sla(topo)
        heatmap = render_terminal_heatmap(res)
        self.assertIn("All-Pairs SLA Availability Matrix", heatmap)
        self.assertIn("Web", heatmap)
        self.assertIn("App", heatmap)
        self.assertIn("DB", heatmap)

        md_report = generate_all_pairs_markdown_report(res)
        self.assertIn("# All-Pairs SLA Availability Matrix", md_report)
        self.assertIn("Node Resilience Centrality Ranking", md_report)

        data = res.to_dict()
        json_str = json.dumps(data)
        self.assertIn("diameter_reliability", json_str)


if __name__ == "__main__":
    unittest.main()

