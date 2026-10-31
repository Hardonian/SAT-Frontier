"""Prepare and pre-compile cut-based CNF instances for High-Core EPYC campaign.

Generates the frontier benchmark formulas:
- grid_3x8, grid_3x9, grid_3x10, grid_3x11
- grid_4x5, grid_4x6, grid_4x7
- grid_5x5
- barbell_6_bridge_6 (two 6-cliques and one bridge)
- chvatal

Outputs .cnf files with exact 'c p weight' declarations to instances/epyc-cut-frontier/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sat_frontier.cut_compiler import to_cut_cnf
from sat_frontier.reliability import (
    NetworkGraph,
    build_barbell_network,
    build_grid_network,
)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build_chvatal_graph(p: Fraction = Fraction(9, 10)) -> tuple[NetworkGraph, int, int]:
    """Chvátal graph: 12 vertices, 24 edges, 4-regular, triangle-free."""
    # Canonical edge set from NetworkX's authoritative generator source:
    # https://networkx.org/documentation/stable/_modules/networkx/generators/small.html#chvatal_graph
    adjacency = {0: [1, 4, 6, 9], 1: [2, 5, 7], 2: [3, 6, 8],
                 3: [4, 7, 9], 4: [5, 8], 5: [10, 11], 6: [10, 11],
                 7: [8, 11], 8: [10], 9: [10, 11]}
    edges = [(u, v) for u, neighbors in adjacency.items() for v in neighbors]
    net = NetworkGraph()
    for u, v in edges:
        net.add_edge(u, v, p)
    return net, 0, 7


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path,
                        default=ROOT / 'instances' / 'epyc-cut-frontier')
    parser.add_argument('--only', nargs='+', help='Generate only these instance names')
    args = parser.parse_args(argv)
    out_dir = args.output_dir.absolute()

    instances = [
        ("grid_3x8", lambda: build_grid_network(3, 8, Fraction(9, 10))),
        ("grid_3x9", lambda: build_grid_network(3, 9, Fraction(9, 10))),
        ("grid_3x10", lambda: build_grid_network(3, 10, Fraction(9, 10))),
        ("grid_3x11", lambda: build_grid_network(3, 11, Fraction(9, 10))),
        ("grid_4x5", lambda: build_grid_network(4, 5, Fraction(9, 10))),
        ("grid_4x6", lambda: build_grid_network(4, 6, Fraction(9, 10))),
        ("grid_4x7", lambda: build_grid_network(4, 7, Fraction(9, 10))),
        ("grid_5x5", lambda: build_grid_network(5, 5, Fraction(9, 10))),
        ("barbell_6_bridge_6", lambda: build_barbell_network(
            cluster_size=6, p_cluster=Fraction(9, 10), p_bridge=Fraction(9, 10))),
        ("chvatal", lambda: build_chvatal_graph(Fraction(9, 10))),
    ]

    if args.only:
        unknown = set(args.only) - {name for name, _ in instances}
        if unknown:
            parser.error('Unknown instances: ' + ', '.join(sorted(unknown)))
        instances = [(name, gen) for name, gen in instances if name in args.only]
    # Atomic reservation: never regenerate over historical benchmark inputs.
    out_dir.mkdir(parents=True, exist_ok=False)
    manifest = {}
    print("=" * 70)
    print("Pre-compiling Frontier Cut CNFs for EPYC Campaign")
    print(f"Output directory: {out_dir}")
    print("=" * 70)

    for name, gen_fn in instances:
        t0 = time.perf_counter()
        net, s, t = gen_fn()
        if any(not 0 <= p <= 1 for p in net.edge_probs.values()):
            raise ValueError('Invalid network probability for ' + name)
        wf = to_cut_cnf(net, s, t)
        dimacs_text = wf.dimacs()
        dimacs_bytes = dimacs_text.encode("utf-8")
        h = sha256_bytes(dimacs_bytes)

        cnf_path = out_dir / f"{name}.cnf"
        cnf_path.write_bytes(dimacs_bytes)
        elapsed = time.perf_counter() - t0

        manifest[name] = {
            "file": f"{name}.cnf",
            "vars": wf.n_vars,
            "clauses": len(wf.clauses),
            "sha256": h,
            "size_bytes": len(dimacs_bytes),
            "compilation_sec": round(elapsed, 4),
            "vertices": len(net.adj), "edges": len(net.edges),
            "source": s, "target": t,
            "interpretation": "network reliability probability",
            "edge_probabilities": {str(k): str(v) for k, v in net.edge_probs.items()},
        }

        print(f"[COMPILED] {name:16s} | Vars={wf.n_vars:3d} | Clauses={len(wf.clauses):6d} | Time={elapsed:6.2f}s | SHA256={h[:16]}...")

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print("\n" + "=" * 70)
    print(f"Successfully compiled {len(instances)} frontier instances.")
    print(f"Manifest written to: {manifest_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()

