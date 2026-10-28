#!/usr/bin/env python3
"""Interactive demonstration: Dual Cut Compilation vs Path Enumeration in real time.

Demonstrates how Menger's Theorem dual cut formulation eliminates auxiliary variables,
bounds clause lengths, and resolves the structural hardness cliff on planar mesh networks.
"""
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sat_frontier.cut_compiler import to_cut_cnf
from sat_frontier.reliability import build_grid_network, build_wheatstone_bridge
from sat_frontier.wmc import wmc_solve


def run_comparison(name: str, net, s, t, max_nodes: int = 100000, seconds: float = 10.0):
    print(f"\n=======================================================")
    print(f" Benchmark: {name}")
    print(f"=======================================================")

    # 1. Compile Path CNF
    t0 = time.perf_counter()
    wf_path = net.to_weighted_cnf(s, t)
    t_comp_path = time.perf_counter() - t0

    # 2. Compile Cut CNF
    t0 = time.perf_counter()
    wf_cut = to_cut_cnf(net, s, t)
    t_comp_cut = time.perf_counter() - t0

    print(f"Formula Compilation:")
    print(f"  * Path CNF : {wf_path.n_vars:>4} vars, {len(wf_path.clauses):>6} clauses (compiled in {t_comp_path:.4f}s)")
    print(f"  * Cut  CNF : {wf_cut.n_vars:>4} vars, {len(wf_cut.clauses):>6} clauses (compiled in {t_comp_cut:.4f}s)")

    # 3. Solve Path CNF
    t0 = time.perf_counter()
    res_path = wmc_solve(wf_path, algorithm="combined_wmc", seconds=seconds, max_nodes=max_nodes)
    t_solve_path = time.perf_counter() - t0

    # 4. Solve Cut CNF
    t0 = time.perf_counter()
    res_cut = wmc_solve(wf_cut, algorithm="combined_wmc", seconds=seconds, max_nodes=max_nodes)
    t_solve_cut = time.perf_counter() - t0

    print(f"\nWMC Exact Solver Results:")
    print(f"  * Path CNF : status={res_path['status']:<7} | nodes={res_path['nodes']:>7} | time={t_solve_path:.4f}s | prob={res_path.get('weight_fraction', 'N/A')}")
    print(f"  * Cut  CNF : status={res_cut['status']:<7} | nodes={res_cut['nodes']:>7} | time={t_solve_cut:.4f}s | prob={res_cut.get('weight_fraction', 'N/A')}")

    if res_path["status"] == "exact" and res_cut["status"] == "exact":
        speedup = res_path["nodes"] / max(1, res_cut["nodes"])
        match = Fraction(res_path["weight_fraction"]) == Fraction(res_cut["weight_fraction"])
        print(f"\n-> Search Node Reduction: {speedup:.2f}x | Exact Rational Agreement: {match}")
    elif res_cut["status"] == "exact" and res_path["status"] != "exact":
        print(f"\n-> BREAKTHROUGH: Cut compilation solves exact reliability where Path formulation timed out!")


def main():
    print("SAT-Frontier: Dual Cut Compilation vs Path Enumeration Demo")

    # 1. Classic Wheatstone Bridge
    net_wb, s_wb, t_wb = build_wheatstone_bridge(p=Fraction(9, 10))
    run_comparison("Wheatstone Bridge (p=0.9)", net_wb, s_wb, t_wb)

    # 2. Planar Ladder 2x5
    net_2x5, s_2x5, t_2x5 = build_grid_network(rows=2, cols=5, p=Fraction(9, 10))
    run_comparison("Grid 2x5 Ladder", net_2x5, s_2x5, t_2x5)

    # 3. Planar Mesh 3x4
    net_3x4, s_3x4, t_3x4 = build_grid_network(rows=3, cols=4, p=Fraction(9, 10))
    run_comparison("Grid 3x4 Mesh", net_3x4, s_3x4, t_3x4)

    # 4. Planar Mesh 3x7 (The Structural Hardness Cliff)
    net_3x7, s_3x7, t_3x7 = build_grid_network(rows=3, cols=7, p=Fraction(9, 10))
    run_comparison("Grid 3x7 Mesh (Hardness Boundary)", net_3x7, s_3x7, t_3x7, seconds=5.0)


if __name__ == "__main__":
    main()

