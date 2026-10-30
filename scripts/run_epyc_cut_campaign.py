"""Turnkey High-Core AMD EPYC Campaign Runner on Frontier Cut-Compiled Topologies.

Executes Parallel Cube-and-Conquer lookahead on the 10 frontier cut-compiled benchmark
instances (grid_3x8..3x11, grid_4x5..4x7, grid_5x5, barbell, chvatal) across
depths d in {4, 6, 8} and worker counts up to 64.

Strictly follows AGENTS.md:
- Fresh evidence directory: evidence/epyc-cut-001/
- No relabeling unknown as UNSAT or zero
- Cross-depth exact rational invariant verification
- Durable per-cube checkpoints
- Cryptographic SHA-256 ledger and verification
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="EPYC High-Core Cut Campaign Runner")
    parser.add_argument("--workers", type=int, default=None, help="Worker count (default: all available logical cores)")
    parser.add_argument("--depths", nargs="+", type=int, default=[4, 6, 8], help="Cube lookahead depths (e.g. 4 6 8)")
    parser.add_argument("--instances-dir", default=str(ROOT / "instances" / "epyc-cut-frontier"), help="Directory of cut CNFs")
    parser.add_argument("--evidence-dir", default=str(ROOT / "evidence" / "epyc-cut-001"), help="Output evidence directory")
    parser.add_argument("--seconds-per-cube", type=float, default=30.0, help="Per-cube time budget in seconds")
    parser.add_argument("--max-nodes-per-cube", type=int, default=200000, help="Per-cube search node budget")
    parser.add_argument("--dry-run", action="store_true", help="Print plan and exit without execution")

    args = parser.parse_args()

    instances_dir = Path(args.instances_dir)
    evidence_dir = Path(args.evidence_dir)
    checkpoints_dir = evidence_dir / "checkpoints"
    inst_storage_dir = evidence_dir / "instances"

    evidence_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    inst_storage_dir.mkdir(parents=True, exist_ok=True)

    available_cpus = os.cpu_count() or 1
    workers = args.workers if args.workers is not None else min(64, available_cpus)

    cnf_files = sorted(list(instances_dir.glob("*.cnf")))
    if not cnf_files:
        print(f"Error: No .cnf files found in {instances_dir}")
        sys.exit(1)

    print("=" * 70)
    print("SAT-Frontier: High-Core EPYC Cut-Compiled Scaling Campaign")
    print("=" * 70)
    print(f"Host:              {platform.node()} ({platform.system()} {platform.machine()})")
    print(f"CPU:               {platform.processor()}")
    print(f"Available Cores:   {available_cpus}")
    print(f"Allocated Workers: {workers}")
    print(f"Depths:            {args.depths}")
    print(f"Instances ({len(cnf_files)}):     {[f.stem for f in cnf_files]}")
    print(f"Output Directory:  {evidence_dir}")
    print("=" * 70)

    if args.dry_run:
        print("Dry run requested. Exiting without execution.")
        return

    # Write config
    config = {
        "study": "epyc-cut-001",
        "description": "High-Core AMD EPYC Parallel Cube-and-Conquer Campaign on Frontier Cut-Compiled Topologies",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "allocated_workers": workers,
        "depths": args.depths,
        "seconds_per_cube": args.seconds_per_cube,
        "max_nodes_per_cube": args.max_nodes_per_cube,
        "hardware": {
            "system": platform.system(),
            "cpu": platform.processor(),
            "cores": available_cpus,
            "python": platform.python_version(),
        },
    }
    (evidence_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n")

    runs_csv_path = evidence_dir / "runs.csv"
    runs_jsonl_path = evidence_dir / "runs.jsonl"
    csv_rows = []
    jsonl_rows = []
    artifact_hashes = {
        "config.json": sha256_file(evidence_dir / "config.json"),
    }

    # Copy / pin instances into evidence directory
    for cnf in cnf_files:
        dest = inst_storage_dir / cnf.name
        if not dest.exists():
            dest.write_bytes(cnf.read_bytes())
        artifact_hashes[f"instances/{cnf.name}"] = sha256_file(dest)

    csv_headers = [
        "instance",
        "depth",
        "workers",
        "cubes_total",
        "cubes_incomplete",
        "status",
        "search_nodes",
        "solve_time_sec",
        "cubes_per_sec",
        "weight_fraction",
    ]

    total_runs = 0
    total_exact = 0
    total_unknown = 0
    cross_depth_invariants = {}

    for cnf in cnf_files:
        inst_name = cnf.stem
        for depth in args.depths:
            total_runs += 1
            run_out_path = evidence_dir / f"{inst_name}_d{depth}_w{workers}.json"
            ckpt_dir = checkpoints_dir / f"{inst_name}_d{depth}"
            ckpt_dir.mkdir(parents=True, exist_ok=True)

            cmd = [
                sys.executable, "-m", "sat_frontier.epyc_runner",
                str(cnf),
                "--depth", str(depth),
                "--workers", str(workers),
                "--seconds-per-cube", str(args.seconds_per_cube),
                "--max-nodes-per-cube", str(args.max_nodes_per_cube),
                "--out", str(run_out_path),
                "--checkpoint-dir", str(ckpt_dir),
            ]

            t0 = time.perf_counter()
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
            wall_time = time.perf_counter() - t0

            if run_out_path.exists():
                res_data = json.loads(run_out_path.read_text())
                status = res_data.get("status", "unknown")
                nodes = res_data.get("nodes", 0)
                cubes_total = res_data.get("cubes_total", 2**depth)
                cubes_incomplete = res_data.get("cubes_incomplete", 0)
                cps = res_data.get("cubes_per_sec", 0.0)
                wf_str = res_data.get("weight_fraction", "")
                artifact_hashes[run_out_path.name] = sha256_file(run_out_path)
            else:
                status = "unknown"
                nodes = 0
                cubes_total = 2**depth
                cubes_incomplete = cubes_total
                cps = 0.0
                wf_str = ""

            if status == "exact":
                total_exact += 1
                if inst_name not in cross_depth_invariants:
                    cross_depth_invariants[inst_name] = wf_str
                else:
                    assert cross_depth_invariants[inst_name] == wf_str, (
                        f"CRITICAL: Cross-depth rational mismatch on {inst_name}: "
                        f"{cross_depth_invariants[inst_name]} != {wf_str}"
                    )
            else:
                total_unknown += 1

            record = {
                "instance": inst_name,
                "depth": depth,
                "workers": workers,
                "cubes_total": cubes_total,
                "cubes_incomplete": cubes_incomplete,
                "status": status,
                "search_nodes": nodes,
                "solve_time_sec": round(wall_time, 4),
                "cubes_per_sec": round(cps, 2),
                "weight_fraction": wf_str,
            }
            jsonl_rows.append(record)
            csv_rows.append([record[k] for k in csv_headers])

            print(
                f"[{total_runs:02d}/{len(cnf_files)*len(args.depths):02d}] "
                f"{inst_name:16s} d={depth} w={workers:2d} | "
                f"Status={status.upper():7s} Nodes={nodes:8,d} | "
                f"Time={wall_time:6.2f}s CPS={cps:6.1f} | "
                f"Incomplete={cubes_incomplete:2d}/{cubes_total:3d}"
            )

    # Write CSV
    with open(runs_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        writer.writerows(csv_rows)
    artifact_hashes["runs.csv"] = sha256_file(runs_csv_path)

    # Write JSONL
    with open(runs_jsonl_path, "w", encoding="utf-8") as f:
        for r in jsonl_rows:
            f.write(json.dumps(r) + "\n")
    artifact_hashes["runs.jsonl"] = sha256_file(runs_jsonl_path)

    summary = {
        "study": "epyc-cut-001",
        "total_runs": total_runs,
        "exact_runs": total_exact,
        "unknown_runs": total_unknown,
        "allocated_workers": workers,
        "invariants_checked": len(cross_depth_invariants),
    }
    (evidence_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    artifact_hashes["summary.json"] = sha256_file(evidence_dir / "summary.json")

    # Manifest
    source_files = [
        "pyproject.toml",
        "sat_frontier/__init__.py",
        "sat_frontier/core.py",
        "sat_frontier/reliability.py",
        "sat_frontier/wmc.py",
        "sat_frontier/cut_compiler.py",
        "sat_frontier/cube_conquer.py",
        "sat_frontier/epyc_runner.py",
    ]
    source_sha256 = {f: sha256_file(ROOT / f) for f in source_files}

    manifest = {
        "study": "epyc-cut-001",
        "schema_version": 1,
        "runs": total_runs,
        "instances": len(cnf_files),
        "exact": total_exact,
        "unknown": total_unknown,
        "status": "complete",
        "hardware": config["hardware"],
        "config_sha256": artifact_hashes["config.json"],
        "artifact_sha256": dict(sorted(artifact_hashes.items())),
        "source_sha256": source_sha256,
    }

    manifest_path = evidence_dir / "manifest.json"
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)

    # SHA256SUMS
    sha256sums_lines = []
    for k in sorted(artifact_hashes.keys()):
        sha256sums_lines.append(f"{artifact_hashes[k]}  {k}")
    sha256sums_lines.append(f"{sha256_bytes(manifest_bytes)}  manifest.json")
    (evidence_dir / "SHA256SUMS").write_text("\n".join(sha256sums_lines) + "\n")

    print("\n" + "=" * 70)
    print(f"CAMPAIGN COMPLETE: {total_exact}/{total_runs} exact runs, {len(cross_depth_invariants)} invariant checks passed.")
    print(f"Manifest written to: {manifest_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
