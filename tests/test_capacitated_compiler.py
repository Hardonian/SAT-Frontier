"""Unit tests for Capacitated Network Flow Reliability Compiler."""
import unittest
from fractions import Fraction

from sat_frontier.capacitated_compiler import (
    CapacitatedNetwork,
    brute_force_capacitated_oracle,
    find_minimal_capacity_breaking_sets,
    solve_capacitated_reliability,
    to_capacitated_cut_cnf,
)


class TestCapacitatedCompiler(unittest.TestCase):
    def test_unit_capacity_demand_1(self):
        """When demand D=1 and all capacities are 1, matches standard cut reliability."""
        net = CapacitatedNetwork()
        net.add_edge(0, 1, capacity=1, prob=Fraction(9, 10))
        net.add_edge(1, 2, capacity=1, prob=Fraction(9, 10))
        net.add_edge(0, 2, capacity=1, prob=Fraction(8, 10))

        rel, _, _ = solve_capacitated_reliability(net, 0, 2, demand=1)
        oracle_rel = brute_force_capacitated_oracle(net, 0, 2, demand=1)
        self.assertEqual(rel, oracle_rel)
        # Expected: 1 - (1 - 0.8) * (1 - 0.9*0.9) = 1 - 0.2 * 0.19 = 1 - 0.038 = 0.962 = 481/500
        self.assertEqual(rel, Fraction(481, 500))

    def test_parallel_edges_demand_2(self):
        """Two parallel paths with unit capacity: demand 2 requires both to survive."""
        net = CapacitatedNetwork()
        net.add_edge(0, 1, capacity=1, prob=Fraction(9, 10))
        net.add_edge(1, 3, capacity=1, prob=Fraction(9, 10))
        net.add_edge(0, 2, capacity=1, prob=Fraction(8, 10))
        net.add_edge(2, 3, capacity=1, prob=Fraction(8, 10))

        rel, _, _ = solve_capacitated_reliability(net, 0, 3, demand=2)
        oracle_rel = brute_force_capacitated_oracle(net, 0, 3, demand=2)
        self.assertEqual(rel, oracle_rel)
        # Both path 1 (0.81) and path 2 (0.64) must survive: 0.81 * 0.64 = 0.5184 = 324/625
        self.assertEqual(rel, Fraction(81, 100) * Fraction(64, 100))

    def test_heterogeneous_capacity_single_cut(self):
        """Single cut with capacities c1=2, c2=1, c3=1 under demand D=3."""
        net = CapacitatedNetwork()
        # Direct parallel edges between 0 and 1
        net.add_edge(0, 1, capacity=2, prob=Fraction(9, 10))   # eid 1
        net.add_edge(0, 1, capacity=1, prob=Fraction(85, 100)) # eid 2
        net.add_edge(0, 1, capacity=1, prob=Fraction(85, 100)) # eid 3

        rel, _, _ = solve_capacitated_reliability(net, 0, 1, demand=3)
        oracle_rel = brute_force_capacitated_oracle(net, 0, 1, demand=3)
        self.assertEqual(rel, oracle_rel)
        # Demand 3 requires eid 1 (cap 2) AND at least one of eid 2 or 3 (cap 1)
        # p(eid 1) * (1 - (1 - p2)(1 - p3))
        # 0.9 * (1 - 0.15 * 0.15) = 0.9 * (1 - 0.0225) = 0.9 * 0.9775 = 0.87975
        expected = Fraction(9, 10) * (Fraction(1, 1) - Fraction(15, 100) * Fraction(15, 100))
        self.assertEqual(rel, expected)

    def test_insufficient_total_capacity(self):
        """When total cut capacity is less than demand, reliability is exactly 0."""
        net = CapacitatedNetwork()
        net.add_edge(0, 1, capacity=1, prob=Fraction(9, 10))
        net.add_edge(1, 2, capacity=1, prob=Fraction(9, 10))

        rel, _, _ = solve_capacitated_reliability(net, 0, 2, demand=2)
        oracle_rel = brute_force_capacitated_oracle(net, 0, 2, demand=2)
        self.assertEqual(rel, Fraction(0, 1))
        self.assertEqual(rel, oracle_rel)

    def test_wheatstone_bridge_demand_2(self):
        """Wheatstone bridge with unit capacities evaluated at demand D=2."""
        net = CapacitatedNetwork()
        # 0:s, 1:top, 2:bottom, 3:t
        net.add_edge(0, 1, capacity=1, prob=Fraction(9, 10))
        net.add_edge(1, 3, capacity=1, prob=Fraction(9, 10))
        net.add_edge(0, 2, capacity=1, prob=Fraction(9, 10))
        net.add_edge(2, 3, capacity=1, prob=Fraction(9, 10))
        net.add_edge(1, 2, capacity=1, prob=Fraction(8, 10))

        rel_d1, _, _ = solve_capacitated_reliability(net, 0, 3, demand=1)
        oracle_d1 = brute_force_capacitated_oracle(net, 0, 3, demand=1)
        self.assertEqual(rel_d1, oracle_d1)

        rel_d2, _, _ = solve_capacitated_reliability(net, 0, 3, demand=2)
        oracle_d2 = brute_force_capacitated_oracle(net, 0, 3, demand=2)
        self.assertEqual(rel_d2, oracle_d2)
        # For D=2, both top and bottom disjoint paths must operate (bridge cannot carry 2 units)
        # R(D=2) = 0.9^4 = 0.6561 = 6561/10000
        self.assertEqual(rel_d2, Fraction(6561, 10000))

    def test_multi_hop_mesh_with_capacities(self):
        """5-node mesh with multi-unit edge capacities matching Dinic max flow oracle."""
        net = CapacitatedNetwork()
        net.add_edge(0, 1, capacity=2, prob=Fraction(92, 100))
        net.add_edge(0, 2, capacity=3, prob=Fraction(88, 100))
        net.add_edge(1, 2, capacity=1, prob=Fraction(95, 100))
        net.add_edge(1, 3, capacity=2, prob=Fraction(90, 100))
        net.add_edge(2, 3, capacity=3, prob=Fraction(85, 100))
        net.add_edge(1, 4, capacity=2, prob=Fraction(94, 100))
        net.add_edge(3, 4, capacity=4, prob=Fraction(91, 100))

        for demand in [1, 2, 3, 4]:
            rel, _, _ = solve_capacitated_reliability(net, 0, 4, demand=demand)
            oracle_rel = brute_force_capacitated_oracle(net, 0, 4, demand=demand)
            self.assertEqual(rel, oracle_rel, f"Mismatch at demand {demand}")

    def test_multichannel_trunking_cardinality(self):
        """4 parallel optical channels under demand D=3 (3-out-of-4 survivability)."""
        net = CapacitatedNetwork()
        for i in range(4):
            net.add_edge(0, 1, capacity=1, prob=Fraction(9, 10))

        # Demand 3: requires at least 3 out of 4 channels to operate
        rel, _, _ = solve_capacitated_reliability(net, 0, 1, demand=3)
        oracle_rel = brute_force_capacitated_oracle(net, 0, 1, demand=3)
        self.assertEqual(rel, oracle_rel)
        # Analytic: binom(4, 3)*0.9^3*0.1 + binom(4, 4)*0.9^4
        # 4 * 0.729 * 0.1 + 0.6561 = 0.2916 + 0.6561 = 0.9477 = 9477 / 10000
        self.assertEqual(rel, Fraction(9477, 10000))



if __name__ == "__main__":
    unittest.main()
