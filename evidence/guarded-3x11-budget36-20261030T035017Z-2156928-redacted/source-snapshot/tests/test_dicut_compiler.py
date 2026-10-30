"""Unit tests for Dual Dicut CNF Compilation (sat_frontier/dicut_compiler.py)."""
from fractions import Fraction
import unittest

from sat_frontier.dicut_compiler import (
    DirectedNetworkGraph,
    brute_force_directed_oracle,
    find_all_minimal_dicuts,
    prune_directed_graph,
    to_dicut_cnf,
)
from sat_frontier.wmc import wmc_solve


class TestDicutCompiler(unittest.TestCase):
    def test_single_arc(self):
        dnet = DirectedNetworkGraph()
        dnet.add_edge("s", "t", Fraction(3, 4))
        cuts = find_all_minimal_dicuts(dnet, "s", "t")
        self.assertEqual(cuts, [(1,)])

        wf = to_dicut_cnf(dnet, "s", "t")
        res = wmc_solve(wf)
        self.assertEqual(res["status"], "exact")
        self.assertEqual(Fraction(res["weight_fraction"]), Fraction(3, 4))
        self.assertEqual(
            Fraction(res["weight_fraction"]),
            brute_force_directed_oracle(dnet, "s", "t"),
        )

    def test_diamond_cross_edge(self):
        dnet = DirectedNetworkGraph()
        # 1 -> 2, 1 -> 3, 2 -> 4, 3 -> 4, 2 -> 3
        dnet.add_edge(1, 2, Fraction(9, 10))
        dnet.add_edge(1, 3, Fraction(9, 10))
        dnet.add_edge(2, 4, Fraction(9, 10))
        dnet.add_edge(3, 4, Fraction(9, 10))
        dnet.add_edge(2, 3, Fraction(9, 10))

        cuts = find_all_minimal_dicuts(dnet, 1, 4)
        self.assertEqual(len(cuts), 4)

        wf = to_dicut_cnf(dnet, 1, 4)
        res = wmc_solve(wf)
        self.assertEqual(res["status"], "exact")
        oracle_val = brute_force_directed_oracle(dnet, 1, 4)
        self.assertEqual(Fraction(res["weight_fraction"]), oracle_val)
        self.assertEqual(Fraction(res["weight_fraction"]), Fraction(97119, 100000))

    def test_directed_cycle_feedback(self):
        dnet = DirectedNetworkGraph()
        # 1 -> 2, 2 -> 3, 3 -> 2 (cycle!), 3 -> 4, 1 -> 4
        dnet.add_edge(1, 2, Fraction(8, 10))
        dnet.add_edge(2, 3, Fraction(8, 10))
        dnet.add_edge(3, 2, Fraction(8, 10))
        dnet.add_edge(3, 4, Fraction(8, 10))
        dnet.add_edge(1, 4, Fraction(8, 10))

        wf = to_dicut_cnf(dnet, 1, 4)
        res = wmc_solve(wf)
        self.assertEqual(res["status"], "exact")
        oracle_val = brute_force_directed_oracle(dnet, 1, 4)
        self.assertEqual(Fraction(res["weight_fraction"]), oracle_val)

    def test_asymmetric_reversal_disconnect(self):
        dnet = DirectedNetworkGraph()
        # 1 -> 2 -> 3
        dnet.add_edge(1, 2, Fraction(9, 10))
        dnet.add_edge(2, 3, Fraction(9, 10))

        # Forward reachability 1 -> 3
        wf_fwd = to_dicut_cnf(dnet, 1, 3)
        res_fwd = wmc_solve(wf_fwd)
        self.assertEqual(Fraction(res_fwd["weight_fraction"]), Fraction(81, 100))

        # Reverse reachability 3 -> 1 is impossible
        wf_rev = to_dicut_cnf(dnet, 3, 1)
        res_rev = wmc_solve(wf_rev)
        self.assertEqual(Fraction(res_rev["weight_fraction"]), Fraction(0))
        self.assertEqual(brute_force_directed_oracle(dnet, 3, 1), Fraction(0))

    def test_pruning_irrelevant_nodes(self):
        dnet = DirectedNetworkGraph()
        # Path 1 -> 2 -> 3, plus dead-end node 99 from 2, and unreachable node 100
        dnet.add_edge(1, 2, Fraction(9, 10))
        dnet.add_edge(2, 3, Fraction(9, 10))
        dnet.add_edge(2, 99, Fraction(9, 10))
        dnet.add_edge(100, 1, Fraction(9, 10))

        pruned, ok = prune_directed_graph(dnet, 1, 3)
        self.assertTrue(ok)
        self.assertEqual(pruned.nodes, {1, 2, 3})
        self.assertEqual(len(pruned.edges), 2)

    def test_tautology_same_node(self):
        dnet = DirectedNetworkGraph()
        dnet.add_edge(1, 2, Fraction(9, 10))
        wf = to_dicut_cnf(dnet, 1, 1)
        res = wmc_solve(wf)
        self.assertEqual(Fraction(res["weight_fraction"]), Fraction(1))
        self.assertEqual(brute_force_directed_oracle(dnet, 1, 1), Fraction(1))

    def test_layered_dag_oracle_matches(self):
        dnet = DirectedNetworkGraph()
        # Layer 1: s
        # Layer 2: a, b
        # Layer 3: c, d
        # Layer 4: t
        dnet.add_edge("s", "a", Fraction(85, 100))
        dnet.add_edge("s", "b", Fraction(85, 100))
        dnet.add_edge("a", "c", Fraction(90, 100))
        dnet.add_edge("a", "d", Fraction(90, 100))
        dnet.add_edge("b", "c", Fraction(90, 100))
        dnet.add_edge("b", "d", Fraction(90, 100))
        dnet.add_edge("c", "t", Fraction(95, 100))
        dnet.add_edge("d", "t", Fraction(95, 100))

        wf = to_dicut_cnf(dnet, "s", "t")
        res = wmc_solve(wf)
        self.assertEqual(res["status"], "exact")
        oracle_val = brute_force_directed_oracle(dnet, "s", "t")
        self.assertEqual(Fraction(res["weight_fraction"]), oracle_val)

    def test_random_directed_graphs_oracle(self):
        import random
        random.seed(42)
        for trial in range(10):
            n = random.randint(4, 6)
            dnet = DirectedNetworkGraph()
            possible_edges = [(u, v) for u in range(1, n + 1) for v in range(1, n + 1) if u != v]
            sampled_edges = random.sample(possible_edges, random.randint(n, min(len(possible_edges), 11)))
            for u, v in sampled_edges:
                p = Fraction(random.randint(6, 9), 10)
                dnet.add_edge(u, v, p)

            wf = to_dicut_cnf(dnet, 1, n)
            res = wmc_solve(wf)
            self.assertEqual(res["status"], "exact")
            oracle_val = brute_force_directed_oracle(dnet, 1, n)
            self.assertEqual(Fraction(res["weight_fraction"]), oracle_val)

    def test_directed_polynomial_evaluation(self):
        from sat_frontier.poly_wmc import ReliabilityPolynomial, solve_poly_wmc
        dnet = DirectedNetworkGraph()
        dnet.add_edge(1, 2)
        dnet.add_edge(1, 3)
        dnet.add_edge(2, 4)
        dnet.add_edge(3, 4)
        dnet.add_edge(2, 3)

        wf = to_dicut_cnf(dnet, 1, 4)
        coeffs, status, nodes = solve_poly_wmc(wf.clauses, set(range(1, wf.n_vars + 1)))
        self.assertEqual(status, "exact")
        self.assertEqual(coeffs, [0, 0, 2, 7, 5, 1])
        poly = ReliabilityPolynomial(coeffs)
        self.assertAlmostEqual(poly.evaluate(0.9), 0.97119)


if __name__ == "__main__":
    unittest.main()
