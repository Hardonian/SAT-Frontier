"""Prepare and pre-compile cut-based CNF instances for High-Core EPYC campaign.

Generates the frontier benchmark formulas:
- grid_3x8, grid_3x9, grid_3x10, grid_3x11
- grid_4x5, grid_4x6, grid_4x7
- grid_5x5
- barbell_6_3_6
- chvatal

Outputs .cnf files with exact 'c p weight' declarations to instances/epyc-cut-frontier/.
"""
from __future__ import annotations

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


def build_chvatal_graph(p: Fraction = Fraction(9, 10)) -> Tuple[NetworkGraph, int, int]:
    """Chvátal graph: 12 vertices, 24 edges, 4-regular, triangle-free."""
    # Vertices 0..11
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 0),  # outer 5-cycle
        (5, 6), (6, 7), (7, 8), (8, 9), (9, 5),  # inner 5-cycle
        (0, 5), (1, 7), (2, 9), (3, 6), (4, 8),  # cross edges
        (10, 0), (10, 2), (10, 6), (10, 8),      # hub 10
        (11, 1), (11, 3), (11, 5), (11, 7),      # hub 11
    ]
    net = NetworkGraph()
    for u, v in edges:
        net.add_edge(u, v, p)
    return net, 0, 7


def main():
    out_dir = ROOT / "instances" / "epyc-cut-frontier"
    out_dir.mkdir(parents=True, exist_ok=True)

    instances = [
        ("grid_3x8", lambda: build_grid_network(3, 8, Fraction(9, 10))),
        ("grid_3x9", lambda: build_grid_network(3, 9, Fraction(9, 10))),
        ("grid_3x10", lambda: build_grid_network(3, 10, Fraction(9, 10))),
        ("grid_3x11", lambda: build_grid_network(3, 11, Fraction(9, 10))),
        ("grid_4x5", lambda: build_grid_network(4, 5, Fraction(9, 10))),
        ("grid_4x6", lambda: build_grid_network(4, 6, Fraction(9, 10))),
        ("grid_4x7", lambda: build_grid_network(4, 7, Fraction(9, 10))),
        ("grid_5x5", lambda: build_grid_network(5, 5, Fraction(9, 10))),
        ("barbell_6_3_6", lambda: build_barbell_network(6, 3, Fraction(9, 10))),
        ("chvatal", lambda: build_chvatal_graph(Fraction(9, 10))),
    ]

    manifest = {}
    print("=" * 70)
    print("Pre-compiling Frontier Cut CNFs for EPYC Campaign")
    print(f"Output directory: {out_dir}")
    print("=" * 70)

    for name, gen_fn in instances:
        t0 = time.perf_counter()
        net, s, t = gen_fn()
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

