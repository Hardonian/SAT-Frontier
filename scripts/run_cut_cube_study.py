"""Empirical study: Parallel Cube-and-Conquer lookahead on Dual Cut-compiled network reliability.

Evaluates high-concurrency lookahead scaling on the newly unlocked cut CNF topologies
(grid_2x11..12, grid_3x6..9, grid_4x4..6, barbell_k6..7).

Strictly adheres to AGENTS.md:
- Fresh output directory: evidence/cut-cube-001/
- No relabeling unknown as UNSAT or zero
- Verified exact fraction equality across depths
- Immutable SHA256SUMS and manifest.json
"""
import csv
import hashlib
import json
import os
import platform
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sat_frontier.cut_compiler import to_cut_cnf
from sat_frontier.reliability import build_barbell_network, build_grid_network
from sat_frontier.cube_conquer import parallel_cube_and_conquer_wmc


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_hard_cut_benchmarks():
    benchmarks = []

    # 1. Ladders at hardness boundary
    for n in [10, 11, 12]:
        net, s, t = build_grid_network(rows=2, cols=n, p=Fraction(9, 10))
        benchmarks.append((f"grid_2x{n}", "ladder", net, s, t))

    # 2. 3xN Meshes across hardness boundary and beyond
    for n in [6, 7, 8, 9]:
        net, s, t = build_grid_network(rows=3, cols=n, p=Fraction(9, 10))
        benchmarks.append((f"grid_3x{n}", "mesh_3xn", net, s, t))

    # 3. 4xN Grids across hardness boundary and beyond
    for n in [4, 5, 6]:
        net, s, t = build_grid_network(rows=4, cols=n, p=Fraction(9, 10))
        benchmarks.append((f"grid_4x{n}", "mesh_4xn", net, s, t))

    # 4. Dense Barbells
    for k in [6, 7]:
        net, s, t = build_barbell_network(
            cluster_size=k,
            p_cluster=Fraction(95, 100),
            p_bridge=Fraction(85, 100),
        )
        benchmarks.append((f"barbell_k{k}", "barbell", net, s, t))

    return benchmarks


def main():
    evidence_dir = ROOT / "evidence" / "cut-cube-001"
    instances_dir = evidence_dir / "instances"
    instances_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "study_name": "cut-cube-001",
        "description": "Parallel Cube-and-Conquer lookahead on Dual Cut-compiled network reliability",
        "depths": [2, 4, 6],
        "workers": 20,
        "seconds_per_cube": 15.0,
        "max_nodes_per_cube": 100000,
        "algo": "combined_wmc",
    }
    config_bytes = json.dumps(config, indent=2, sort_keys=True).encode("utf-8")
    (evidence_dir / "config.json").write_bytes(config_bytes)
    config_sha256 = sha256_bytes(config_bytes)

    benchmarks = generate_hard_cut_benchmarks()
    print(f"Generated {len(benchmarks)} hard benchmark topologies.")

    runs = []
    csv_rows = []
    instance_digests = {}
    exact_count = 0
    unknown_count = 0
    invariance_verified = 0

    print(f"\n{'Instance':<14} | {'Depth':<5} | {'Cubes':<6} | {'Status':<7} | {'Nodes':<9} | {'Time (s)':<8} | Rate (c/s) | Weight")
    print("-" * 88)

    for label, family, net, s, t in benchmarks:
        # Compile cut CNF once per topology
        t_c0 = time.perf_counter()
        wf = to_cut_cnf(net, s, t)
        t_comp = time.perf_counter() - t_c0

        dimacs = wf.dimacs().encode("utf-8")
        inst_sha = sha256_bytes(dimacs)
        cnf_path = instances_dir / f"{inst_sha}.cnf"
        if not cnf_path.exists():
            cnf_path.write_bytes(dimacs)
        instance_digests[f"instances/{inst_sha}.cnf"] = inst_sha

        previous_weight = None

        for depth in config["depths"]:
            t0 = time.perf_counter()
            res = parallel_cube_and_conquer_wmc(
                wf,
                depth=depth,
                num_workers=config["workers"],
                algo=config["algo"],
                seconds_per_cube=config["seconds_per_cube"],
                max_nodes_per_cube=config["max_nodes_per_cube"],
            )
            wall_time = time.perf_counter() - t0

            c_tot = res["cubes_total"]
            c_inc = res["cubes_incomplete"]
            st = res["status"]
            nodes = res["total_nodes"]
            rate = c_tot / max(0.0001, wall_time)
            wf_str = res.get("weight_fraction")

            # Check mathematical invariance across depths
            if st == "exact":
                exact_count += 1
                if previous_weight is not None:
                    assert Fraction(wf_str) == Fraction(previous_weight), f"Weight mismatch on {label} depth {depth}"
                    invariance_verified += 1
                previous_weight = wf_str
            else:
                unknown_count += 1

            disp_wf = (wf_str[:20] + "...") if wf_str and len(wf_str) > 20 else str(wf_str)
            print(f"{label:<14} | {depth:<5} | {c_tot:<6} | {st:<7} | {nodes:<9} | {wall_time:<8.3f} | {rate:<10.1f} | {disp_wf}")

            # Record Run
            run_rec = {
                "algorithm": "cube_conquer_wmc",
                "compiler": "cut_cnf",
                "family": family,
                "instance_label": label,
                "instance_sha256": inst_sha,
                "depth": depth,
                "workers": config["workers"],
                "cubes_total": c_tot,
                "cubes_incomplete": c_inc,
                "n_vars": wf.n_vars,
                "n_clauses": len(wf.clauses),
                "status": st,
                "nodes": nodes,
                "elapsed_seconds": res.get("elapsed_seconds", wall_time),
                "wall_seconds": wall_time,
                "cubes_per_second": rate,
            }
            if st == "exact":
                run_rec["weight_fraction"] = wf_str
                run_rec["weight_float"] = res["weight_float"]
            runs.append(run_rec)

            csv_rows.append({
                "instance_label": label,
                "family": family,
                "depth": depth,
                "workers": config["workers"],
                "cubes_total": c_tot,
                "cubes_incomplete": c_inc,
                "status": st,
                "nodes": nodes,
                "wall_seconds": f"{wall_time:.4f}",
                "cubes_per_sec": f"{rate:.1f}",
                "weight_fraction": wf_str if wf_str else "",
            })

    # Write runs.jsonl
    runs_jsonl_path = evidence_dir / "runs.jsonl"
    with open(runs_jsonl_path, "w", encoding="utf-8") as f:
        for r in runs:
            f.write(json.dumps(r, sort_keys=True) + "\n")

    # Write runs.csv
    runs_csv_path = evidence_dir / "runs.csv"
    with open(runs_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "instance_label", "family", "depth", "workers",
            "cubes_total", "cubes_incomplete", "status", "nodes",
            "wall_seconds", "cubes_per_sec", "weight_fraction",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    # Write summary.json
    summary = {
        "study": "cut-cube-001",
        "total_instances": len(benchmarks),
        "total_runs": len(runs),
        "exact_runs": exact_count,
        "unknown_runs": unknown_count,
        "cross_depth_invariance_checks": invariance_verified,
        "workers": config["workers"],
    }
    summary_bytes = json.dumps(summary, indent=2, sort_keys=True).encode("utf-8")
    (evidence_dir / "summary.json").write_bytes(summary_bytes)

    # Artifact SHA256 mapping
    artifact_sha256 = {
        "config.json": config_sha256,
        "runs.jsonl": sha256_file(runs_jsonl_path),
        "runs.csv": sha256_file(runs_csv_path),
        "summary.json": sha256_bytes(summary_bytes),
    }
    artifact_sha256.update(instance_digests)

    # Source SHA256 mapping
    source_files = [
        "pyproject.toml",
        "sat_frontier/__init__.py",
        "sat_frontier/core.py",
        "sat_frontier/reliability.py",
        "sat_frontier/cut_compiler.py",
        "sat_frontier/cube_conquer.py",
        "sat_frontier/wmc.py",
    ]
    source_sha256 = {f: sha256_file(ROOT / f) for f in source_files}

    manifest = {
        "schema_version": 1,
        "status": "complete",
        "instances": len(benchmarks),
        "runs": len(runs),
        "exact": exact_count,
        "unknown": unknown_count,
        "hardware": {
            "system": platform.system(),
            "cpu": platform.processor(),
            "python": sys.version,
            "logical_cores": os.cpu_count(),
        },
        "config_sha256": config_sha256,
        "source_sha256": source_sha256,
        "artifact_sha256": artifact_sha256,
    }
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    (evidence_dir / "manifest.json").write_bytes(manifest_bytes)

    # Write SHA256SUMS
    sha256sums_lines = []
    for rel_path in sorted(artifact_sha256.keys()):
        sha256sums_lines.append(f"{artifact_sha256[rel_path]}  {rel_path}")
    (evidence_dir / "SHA256SUMS").write_text("\n".join(sha256sums_lines) + "\n", encoding="utf-8")

    print("\nStudy execution complete.")
    print(f"Total runs: {len(runs)} | Exact: {exact_count} | Unknown: {unknown_count} | Cross-depth invariant checks: {invariance_verified}")


if __name__ == "__main__":
    main()
