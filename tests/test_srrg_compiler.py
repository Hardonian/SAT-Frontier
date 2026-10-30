"""Unit tests for SRRG correlated failure reliability compiler (sat_frontier/srrg_compiler.py)."""
import unittest
from fractions import Fraction

from sat_frontier.srrg_compiler import (
    SRRGNetwork,
    brute_force_srrg_oracle,
    find_all_simple_paths,
    find_minimal_srrg_cuts,
    solve_srrg_reliability,
    to_srrg_cut_cnf,
)


class TestSRRGCompiler(unittest.TestCase):
    def test_independent_parallel_edges(self):
        """Two parallel edges with distinct risk groups."""
        # s=0, t=2 with intermediate nodes 1 and 3
        # Path 1: 0-1-2 with group g1
        # Path 2: 0-3-2 with group g2
        net = SRRGNetwork(
            num_nodes=4,
            edges=[(0, 1), (1, 2), (0, 3), (3, 2)],
            edge_to_groups={
                (0, 1): ["g1"],
                (1, 2): ["g1"],
                (0, 3): ["g2"],
                (3, 2): ["g2"],
            },
            group_probs={"g1": Fraction(9, 10), "g2": Fraction(8, 10)},
            is_directed=False,
        )
        cuts = find_minimal_srrg_cuts(net, 0, 2)
        self.assertEqual(len(cuts), 1)
        self.assertEqual(cuts[0], frozenset({"g1", "g2"}))

        rel, _, _ = solve_srrg_reliability(net, 0, 2)
        oracle_rel = brute_force_srrg_oracle(net, 0, 2)
        # 1 - (1 - 0.9)*(1 - 0.8) = 1 - 0.1*0.2 = 1 - 0.02 = 0.98 = 98/100 = 49/50
        self.assertEqual(rel, Fraction(49, 50))
        self.assertEqual(rel, oracle_rel)

    def test_shared_fate_parallel_edges(self):
        """Two disjoint topological paths sharing the SAME physical conduit."""
        # Path 1: 0-1-2 in conduit g_shared
        # Path 2: 0-3-2 in conduit g_shared
        net = SRRGNetwork(
            num_nodes=4,
            edges=[(0, 1), (1, 2), (0, 3), (3, 2)],
            edge_to_groups={
                (0, 1): ["g_shared"],
                (1, 2): ["g_shared"],
                (0, 3): ["g_shared"],
                (3, 2): ["g_shared"],
            },
            group_probs={"g_shared": Fraction(95, 100)},
            is_directed=False,
        )
        cuts = find_minimal_srrg_cuts(net, 0, 2)
        self.assertEqual(len(cuts), 1)
        self.assertEqual(cuts[0], frozenset({"g_shared"}))

        rel, _, _ = solve_srrg_reliability(net, 0, 2)
        oracle_rel = brute_force_srrg_oracle(net, 0, 2)
        # Because both paths share g_shared, reliability is simply p(g_shared) = 95/100
        self.assertEqual(rel, Fraction(19, 20))
        self.assertEqual(rel, oracle_rel)

    def test_bridge_network_correlated_sheaths(self):
        """Wheatstone bridge network with correlated fiber sheaths."""
        # 0:s, 1:top, 2:bottom, 3:t
        # e(0,1): gA, e(1,3): gA
        # e(0,2): gB, e(2,3): gB
        # e(1,2): gC (bridge)
        net = SRRGNetwork(
            num_nodes=4,
            edges=[(0, 1), (1, 3), (0, 2), (2, 3), (1, 2)],
            edge_to_groups={
                (0, 1): ["gA"],
                (1, 3): ["gA"],
                (0, 2): ["gB"],
                (2, 3): ["gB"],
                (1, 2): ["gC"],
            },
            group_probs={
                "gA": Fraction(9, 10),
                "gB": Fraction(9, 10),
                "gC": Fraction(8, 10),
            },
            is_directed=False,
        )
        cuts = find_minimal_srrg_cuts(net, 0, 3)
        # Any cut must hit path {gA} and {gB}. Thus {gA, gB} is minimal.
        self.assertEqual(len(cuts), 1)
        self.assertEqual(cuts[0], frozenset({"gA", "gB"}))

        rel, _, _ = solve_srrg_reliability(net, 0, 3)
        oracle_rel = brute_force_srrg_oracle(net, 0, 3)
        # 1 - (1 - 0.9)^2 = 1 - 0.01 = 0.99 = 99/100
        self.assertEqual(rel, Fraction(99, 100))
        self.assertEqual(rel, oracle_rel)

    def test_multi_group_per_edge(self):
        """Edges subject to both a conduit risk and a regional power risk."""
        # 0 -> 1 -> 2
        # e(0,1): conduit c1 AND power p_east
        # e(1,2): conduit c2 AND power p_east
        net = SRRGNetwork(
            num_nodes=3,
            edges=[(0, 1), (1, 2)],
            edge_to_groups={
                (0, 1): ["c1", "p_east"],
                (1, 2): ["c2", "p_east"],
            },
            group_probs={
                "c1": Fraction(9, 10),
                "c2": Fraction(9, 10),
                "p_east": Fraction(95, 100),
            },
            is_directed=True,
        )
        cuts = find_minimal_srrg_cuts(net, 0, 2)
        # The path has groups {c1, c2, p_east}.
        # Minimal hitting sets are singletons: {c1}, {c2}, {p_east}.
        self.assertEqual(len(cuts), 3)
        cut_sets = set(cuts)
        self.assertIn(frozenset({"c1"}), cut_sets)
        self.assertIn(frozenset({"c2"}), cut_sets)
        self.assertIn(frozenset({"p_east"}), cut_sets)

        rel, _, _ = solve_srrg_reliability(net, 0, 2)
        oracle_rel = brute_force_srrg_oracle(net, 0, 2)
        # Path operates iff all 3 groups operate: 0.9 * 0.9 * 0.95 = 0.7695 = 1539/2000
        self.assertEqual(rel, Fraction(1539, 2000))
        self.assertEqual(rel, oracle_rel)

    def test_disconnected_network(self):
        """Graph with no path between terminals."""
        net = SRRGNetwork(
            num_nodes=3,
            edges=[(0, 1)],
            edge_to_groups={(0, 1): ["g1"]},
            group_probs={"g1": Fraction(9, 10)},
            is_directed=False,
        )
        rel, _, _ = solve_srrg_reliability(net, 0, 2)
        self.assertEqual(rel, Fraction(0, 1))

    def test_cloud_vpc_availability_zones(self):
        """Cloud VPC architecture: redundant services routed across AZs."""
        # Client (0) connects to App Servers (1, 2) in az_a, az_b,
        # which connect to Database (3) in az_db.
        # e(0,1): az_a, e(1,3): az_a, az_db
        # e(0,2): az_b, e(2,3): az_b, az_db
        net = SRRGNetwork(
            num_nodes=4,
            edges=[(0, 1), (1, 3), (0, 2), (2, 3)],
            edge_to_groups={
                (0, 1): ["az_a"],
                (1, 3): ["az_a", "az_db"],
                (0, 2): ["az_b"],
                (2, 3): ["az_b", "az_db"],
            },
            group_probs={
                "az_a": Fraction(98, 100),
                "az_b": Fraction(98, 100),
                "az_db": Fraction(999, 1000),
            },
            is_directed=True,
        )
        rel, _, _ = solve_srrg_reliability(net, 0, 3)
        oracle_rel = brute_force_srrg_oracle(net, 0, 3)
        self.assertEqual(rel, oracle_rel)
        # Expected: az_db must survive AND (az_a or az_b must survive)
        # p(az_db) * (1 - (1 - p(az_a))*(1 - p(az_b)))
        # 0.999 * (1 - 0.02*0.02) = 0.999 * (1 - 0.0004) = 0.999 * 0.9996 = 0.9986004
        self.assertEqual(rel, Fraction(999, 1000) * Fraction(2499, 2500))

    def test_complex_mesh_oracle_agreement(self):
        """5-node mesh with 6 overlapping risk groups matching oracle exactly."""
        # 0:s, 4:t, intermediate 1, 2, 3
        edges = [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3), (1, 4), (3, 4)]
        edge_to_groups = {
            (0, 1): ["g1", "g2"],
            (0, 2): ["g2", "g3"],
            (1, 2): ["g4"],
            (1, 3): ["g1", "g5"],
            (2, 3): ["g3", "g5"],
            (1, 4): ["g2", "g6"],
            (3, 4): ["g4", "g6"],
        }
        group_probs = {
            "g1": Fraction(9, 10),
            "g2": Fraction(92, 100),
            "g3": Fraction(88, 100),
            "g4": Fraction(95, 100),
            "g5": Fraction(91, 100),
            "g6": Fraction(97, 100),
        }
        net = SRRGNetwork(
            num_nodes=5,
            edges=edges,
            edge_to_groups=edge_to_groups,
            group_probs=group_probs,
            is_directed=False,
        )
        rel, nodes, elapsed = solve_srrg_reliability(net, 0, 4)
        oracle_rel = brute_force_srrg_oracle(net, 0, 4)
        self.assertEqual(rel, oracle_rel)

    def test_unbreakable_bypass_path(self):
        """Network where an unshared high-reliability fiber line has zero risk groups."""
        # 0 -> 1 with no risk groups (dedicated private dark fiber)
        net = SRRGNetwork(
            num_nodes=2,
            edges=[(0, 1)],
            edge_to_groups={(0, 1): []},
            group_probs={},
            is_directed=True,
        )
        rel, _, _ = solve_srrg_reliability(net, 0, 1)
        self.assertEqual(rel, Fraction(1, 1))


if __name__ == "__main__":
    unittest.main()
