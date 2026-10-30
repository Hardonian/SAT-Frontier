"""Unit tests for Dual Mixed-Cut Compilation (sat_frontier/mixed_cut_compiler.py)."""
from fractions import Fraction
import random
import unittest

from sat_frontier.mixed_cut_compiler import (
    MixedNetworkGraph,
    brute_force_mixed_oracle,
    find_all_minimal_mixed_cuts,
    to_mixed_cut_cnf,
)
from sat_frontier.wmc import wmc_solve


class TestMixedCutCompiler(unittest.TestCase):
    def test_single_edge_mixed(self):
        net = MixedNetworkGraph()
        net.add_node("s", Fraction(1, 1))
        net.add_node("t", Fraction(1, 1))
        net.add_edge("s", "t", Fraction(4, 5))

        cuts = find_all_minimal_mixed_cuts(net, "s", "t")
        self.assertEqual(cuts, [(1,)])

        wf = to_mixed_cut_cnf(net, "s", "t")
        res = wmc_solve(wf)
        self.assertEqual(res["status"], "exact")
        self.assertEqual(Fraction(res["weight_fraction"]), Fraction(4, 5))
        self.assertEqual(
            Fraction(res["weight_fraction"]),
            brute_force_mixed_oracle(net, "s", "t"),
        )

    def test_diamond_mixed_cuts(self):
        net = MixedNetworkGraph()
        net.add_node("s", Fraction(1, 1))
        net.add_node("t", Fraction(1, 1))
        net.add_node(1, Fraction(85, 100))
        net.add_node(2, Fraction(90, 100))

        net.add_edge("s", 1, Fraction(9, 10))
        net.add_edge("s", 2, Fraction(9, 10))
        net.add_edge(1, 2, Fraction(9, 10))
        net.add_edge(1, "t", Fraction(9, 10))
        net.add_edge(2, "t", Fraction(9, 10))

        cuts = find_all_minimal_mixed_cuts(net, "s", "t")
        self.assertEqual(len(cuts), 9)

        wf = to_mixed_cut_cnf(net, "s", "t")
        res = wmc_solve(wf)
        self.assertEqual(res["status"], "exact")

        orc_val = brute_force_mixed_oracle(net, "s", "t")
        self.assertEqual(Fraction(res["weight_fraction"]), orc_val)
        self.assertEqual(Fraction(res["weight_fraction"]), Fraction(2316843, 2500000))

    def test_directed_mixed_graph(self):
        net = MixedNetworkGraph(is_directed=True)
        net.add_node("s", Fraction(1, 1))
        net.add_node("t", Fraction(1, 1))
        net.add_node("a", Fraction(88, 100))
        net.add_node("b", Fraction(92, 100))

        net.add_edge("s", "a", Fraction(9, 10))
        net.add_edge("s", "b", Fraction(9, 10))
        net.add_edge("a", "b", Fraction(85, 100))
        net.add_edge("a", "t", Fraction(95, 100))
        net.add_edge("b", "t", Fraction(95, 100))

        wf = to_mixed_cut_cnf(net, "s", "t")
        res = wmc_solve(wf)
        self.assertEqual(res["status"], "exact")

        orc_val = brute_force_mixed_oracle(net, "s", "t")
        self.assertEqual(Fraction(res["weight_fraction"]), orc_val)

    def test_tautology_and_disconnected(self):
        net = MixedNetworkGraph()
        net.add_node("s")
        net.add_node("t")

        # Tautology
        wf_same = to_mixed_cut_cnf(net, "s", "s")
        res_same = wmc_solve(wf_same)
        self.assertEqual(Fraction(res_same["weight_fraction"]), Fraction(1, 1))

        # Disconnected
        wf_disc = to_mixed_cut_cnf(net, "s", "t")
        res_disc = wmc_solve(wf_disc)
        self.assertEqual(Fraction(res_disc["weight_fraction"]), Fraction(0, 1))
        self.assertEqual(brute_force_mixed_oracle(net, "s", "t"), Fraction(0, 1))

    def test_random_mixed_graphs_oracle(self):
        random.seed(42)
        for trial in range(10):
            n = random.randint(4, 6)
            is_dir = bool(trial % 2 == 1)
            net = MixedNetworkGraph(is_directed=is_dir)
            s, t = 1, n
            for v in range(1, n + 1):
                p_v = Fraction(random.randint(8, 10), 10) if (v != s and v != t) else Fraction(1, 1)
                net.add_node(v, p_v)

            possible_edges = (
                [(u, v) for u in range(1, n + 1) for v in range(1, n + 1) if u != v]
                if is_dir
                else [(u, v) for i, u in enumerate(range(1, n + 1)) for v in range(u + 1, n + 1)]
            )
            sampled_edges = random.sample(possible_edges, random.randint(n - 1, min(len(possible_edges), 10)))
            for u, v in sampled_edges:
                p_e = Fraction(random.randint(7, 9), 10)
                net.add_edge(u, v, p_e)

            wf = to_mixed_cut_cnf(net, s, t)
            res = wmc_solve(wf)
            self.assertEqual(res["status"], "exact")

            orc_val = brute_force_mixed_oracle(net, s, t)
            self.assertEqual(
                Fraction(res["weight_fraction"]),
                orc_val,
                f"Mismatch on trial {trial} ({'directed' if is_dir else 'undirected'}): {res['weight_fraction']} vs {orc_val}",
            )

    def test_mixed_polynomial_evaluation(self):
        from sat_frontier.poly_wmc import ReliabilityPolynomial, solve_poly_wmc
        net = MixedNetworkGraph()
        net.add_node("s")
        net.add_node("t")
        net.add_node("a")
        net.add_node("b")
        net.add_edge("s", "a")
        net.add_edge("s", "b")
        net.add_edge("a", "t")
        net.add_edge("b", "t")

        wf = to_mixed_cut_cnf(net, "s", "t")
        active_vars = set(range(1, wf.n_vars + 1))
        coeffs, status, _ = solve_poly_wmc(wf.clauses, active_vars)
        self.assertEqual(status, "exact")
        self.assertEqual(coeffs, [0, 0, 0, 2, 6, 6, 1])
        poly = ReliabilityPolynomial(coeffs)
        self.assertAlmostEqual(poly.evaluate(0.9), 0.926559, places=6)

    def test_bottleneck_cut_vertex_mixed(self):
        # Barbell: s - a - Gateway - b - t. Gateway is a critical cut-vertex.
        net = MixedNetworkGraph()
        net.add_node("s")
        net.add_node("a", Fraction(9, 10))
        net.add_node("Gateway", Fraction(95, 100))
        net.add_node("b", Fraction(9, 10))
        net.add_node("t")

        net.add_edge("s", "a", Fraction(99, 100))
        net.add_edge("a", "Gateway", Fraction(99, 100))
        net.add_edge("Gateway", "b", Fraction(99, 100))
        net.add_edge("b", "t", Fraction(99, 100))

        cuts = find_all_minimal_mixed_cuts(net, "s", "t")
        # Gateway is internal node 2 (alphabetical: 'Gateway', 'a', 'b')
        # Gateway alone should form a unit cut clause [Gateway_var]
        unit_cuts = [c for c in cuts if len(c) == 1]
        self.assertGreaterEqual(len(unit_cuts), 1)


if __name__ == "__main__":
    unittest.main()
