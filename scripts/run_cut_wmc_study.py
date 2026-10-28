"""Hypothesis H9 Empirical Runner: Dual Cut-based CNF compilation vs Path-based compilation.

Evaluates the Dual Cut compilation technique (to_cut_cnf) against standard Path
enumeration (to_weighted_cnf) for Two-Terminal Network Reliability across planar grids
and bottleneck topologies.

Strictly adheres to AGENTS.md:
- Fresh output directory: evidence/cut-wmc-001/
- No relabeling unknown as UNSAT or zero
- Verified exact fraction equality when both finish
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

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sat_frontier.cut_compiler import to_cut_cnf
from sat_frontier.reliability import (
    build_barbell_network,
    build_grid_network,
    build_wheatstone_bridge,
)
from sat_frontier.wmc import WeightedFormula, wmc_solve


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_benchmark_networks():
    """Generate benchmark instances across grid and barbell topologies."""
    networks = []

    # 1. 2xN grids (ladders)
    for n in range(3, 13):
        net, s, t = build_grid_network(rows=2, cols=n, p=Fraction(9, 10))
        networks.append((f"grid_2x{n}", "grid_2xn", net, s, t))

    # 2. 3xN grids
    for n in range(3, 9):
        net, s, t = build_grid_network(rows=3, cols=n, p=Fraction(9, 10))
        networks.append((f"grid_3x{n}", "grid_3xn", net, s, t))

    # 3. 4xN grids
    for n in range(3, 6):
        net, s, t = build_grid_network(rows=4, cols=n, p=Fraction(9, 10))
        networks.append((f"grid_4x{n}", "grid_4xn", net, s, t))

    # 4. Barbell networks
    for k in range(3, 8):
        net, s, t = build_barbell_network(
            cluster_size=k,
            p_cluster=Fraction(95, 100),
            p_bridge=Fraction(85, 100),
        )
        networks.append((f"barbell_k{k}", "barbell", net, s, t))

    return networks


def main():
    repo_root = Path(__file__).resolve().parent.parent
    evidence_dir = repo_root / "evidence" / "cut-wmc-001"
    instances_dir = evidence_dir / "instances"
    instances_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "study_name": "cut-wmc-001",
        "hypothesis": "H9",
        "description": "Dual Cut-based CNF compilation versus Path enumeration on two-terminal network reliability",
        "max_nodes": 100000,
        "seconds_budget": 15.0,
        "solver_algorithm": "combined_wmc",
        "compiler_variants": ["path_cnf", "cut_cnf"],
    }
    config_bytes = json.dumps(config, indent=2, sort_keys=True).encode("utf-8")
    (evidence_dir / "config.json").write_bytes(config_bytes)
    config_sha256 = sha256_bytes(config_bytes)

    networks = generate_benchmark_networks()
    print(f"Generated {len(networks)} benchmark network topologies.")

    runs = []
    csv_rows = []
    instance_digests = {}
    verified_matches = 0
    mismatches = 0
    exact_count = 0
    unknown_count = 0

    print(f"{'Instance':<16} | {'Compiler':<10} | {'Vars':<6} | {'Clauses':<8} | {'Status':<8} | {'Nodes':<8} | {'Time (s)':<8} | Notes")
    print("-" * 85)

    for label, family, net, s, t in networks:
        # 1. Compile both formulations
        # Path formulation
        wf_path = net.to_weighted_cnf(s, t)
        path_dimacs = wf_path.dimacs().encode("utf-8")
        path_sha = sha256_bytes(path_dimacs)
        path_cnf_file = instances_dir / f"{path_sha}.cnf"
        path_cnf_file.write_bytes(path_dimacs)
        instance_digests[f"instances/{path_sha}.cnf"] = path_sha

        # Cut formulation
        wf_cut = to_cut_cnf(net, s, t)
        cut_dimacs = wf_cut.dimacs().encode("utf-8")
        cut_sha = sha256_bytes(cut_dimacs)
        cut_cnf_file = instances_dir / f"{cut_sha}.cnf"
        cut_cnf_file.write_bytes(cut_dimacs)
        instance_digests[f"instances/{cut_sha}.cnf"] = cut_sha

        # 2. Solve Path formulation
        t0 = time.perf_counter()
        res_path = wmc_solve(
            wf_path,
            algorithm=config["solver_algorithm"],
            seconds=config["seconds_budget"],
            max_nodes=config["max_nodes"],
        )
        t_path = time.perf_counter() - t0

        # 3. Solve Cut formulation
        t0 = time.perf_counter()
        res_cut = wmc_solve(
            wf_cut,
            algorithm=config["solver_algorithm"],
            seconds=config["seconds_budget"],
            max_nodes=config["max_nodes"],
        )
        t_cut = time.perf_counter() - t0

        # 4. Check consistency if both solved
        both_exact = (res_path["status"] == "exact" and res_cut["status"] == "exact")
        match_note = ""
        if both_exact:
            if Fraction(res_path["weight_fraction"]) == Fraction(res_cut["weight_fraction"]):
                verified_matches += 1
                match_note = "Exact rational match"
            else:
                mismatches += 1
                match_note = f"MISMATCH: path={res_path['weight_fraction']} cut={res_cut['weight_fraction']}"
                print(f"FATAL MISMATCH on {label}!")
        elif res_cut["status"] == "exact" and res_path["status"] != "exact":
            match_note = "Cut solved, path budget-exhausted"
        elif res_path["status"] == "exact" and res_cut["status"] != "exact":
            match_note = "Path solved, cut budget-exhausted"
        else:
            match_note = "Both budget-exhausted"

        print(f"{label:<16} | {'path_cnf':<10} | {wf_path.n_vars:<6} | {len(wf_path.clauses):<8} | {res_path['status']:<8} | {res_path['nodes']:<8} | {t_path:<8.4f} |")
        print(f"{label:<16} | {'cut_cnf':<10} | {wf_cut.n_vars:<6} | {len(wf_cut.clauses):<8} | {res_cut['status']:<8} | {res_cut['nodes']:<8} | {t_cut:<8.4f} | {match_note}")

        # Record Path Run
        path_record = {
            "algorithm": config["solver_algorithm"],
            "compiler": "path_cnf",
            "family": family,
            "instance_label": label,
            "instance_sha256": path_sha,
            "n_vars": wf_path.n_vars,
            "n_clauses": len(wf_path.clauses),
            "status": res_path["status"],
            "nodes": res_path["nodes"],
            "cache_entries": res_path.get("cache_entries", 0),
            "cache_hits": res_path.get("cache_hits", 0),
            "component_splits": res_path.get("component_splits", 0),
            "unit_assignments": res_path.get("unit_assignments", 0),
            "elapsed_seconds": res_path.get("elapsed_seconds", t_path),
            "wall_seconds": t_path,
        }
        if res_path["status"] == "exact":
            path_record["weight_fraction"] = res_path["weight_fraction"]
            path_record["weight_float"] = res_path["weight_float"]
            exact_count += 1
        else:
            unknown_count += 1
        runs.append(path_record)

        # Record Cut Run
        cut_record = {
            "algorithm": config["solver_algorithm"],
            "compiler": "cut_cnf",
            "family": family,
            "instance_label": label,
            "instance_sha256": cut_sha,
            "n_vars": wf_cut.n_vars,
            "n_clauses": len(wf_cut.clauses),
            "status": res_cut["status"],
            "nodes": res_cut["nodes"],
            "cache_entries": res_cut.get("cache_entries", 0),
            "cache_hits": res_cut.get("cache_hits", 0),
            "component_splits": res_cut.get("component_splits", 0),
            "unit_assignments": res_cut.get("unit_assignments", 0),
            "elapsed_seconds": res_cut.get("elapsed_seconds", t_cut),
            "wall_seconds": t_cut,
        }
        if res_cut["status"] == "exact":
            cut_record["weight_fraction"] = res_cut["weight_fraction"]
            cut_record["weight_float"] = res_cut["weight_float"]
            exact_count += 1
        else:
            unknown_count += 1
        runs.append(cut_record)

        # CSV row
        csv_rows.append({
            "instance_label": label,
            "family": family,
            "path_vars": wf_path.n_vars,
            "path_clauses": len(wf_path.clauses),
            "path_status": res_path["status"],
            "path_nodes": res_path["nodes"],
            "path_time": f"{t_path:.4f}",
            "cut_vars": wf_cut.n_vars,
            "cut_clauses": len(wf_cut.clauses),
            "cut_status": res_cut["status"],
            "cut_nodes": res_cut["nodes"],
            "cut_time": f"{t_cut:.4f}",
            "speedup_nodes": f"{res_path['nodes'] / max(1, res_cut['nodes']):.2f}" if res_cut["nodes"] > 0 else "N/A",
            "notes": match_note,
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
            "instance_label", "family",
            "path_vars", "path_clauses", "path_status", "path_nodes", "path_time",
            "cut_vars", "cut_clauses", "cut_status", "cut_nodes", "cut_time",
            "speedup_nodes", "notes",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    # Write summary.json
    summary = {
        "study": "cut-wmc-001",
        "total_instances": len(networks),
        "total_runs": len(runs),
        "exact_runs": exact_count,
        "unknown_runs": unknown_count,
        "verified_matches": verified_matches,
        "mismatches": mismatches,
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
        "sat_frontier/wmc.py",
    ]
    source_sha256 = {f: sha256_file(repo_root / f) for f in source_files}

    manifest = {
        "schema_version": 1,
        "status": "complete",
        "instances": len(networks),
        "runs": len(runs),
        "exact": exact_count,
        "unknown": unknown_count,
        "hardware": {
            "system": platform.system(),
            "cpu": platform.processor(),
            "python": sys.version,
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
    print(f"Total runs: {len(runs)} | Exact: {exact_count} | Unknown: {unknown_count} | Matches verified: {verified_matches} | Mismatches: {mismatches}")


if __name__ == "__main__":
    main()
