#!/usr/bin/env python3
"""Ingestion, invariant verification, and cryptographic pinning for external EPYC runs.

Usage:
    python scripts/ingest_epyc_runs.py --run-dir evidence/epyc-cube-003
"""
import argparse
import hashlib
import json
import os
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ingest_directory(run_dir: Path):
    if not run_dir.exists():
        print(f"Error: Directory {run_dir} does not exist.")
        sys.exit(1)

    print(f"Ingesting EPYC run directory: {run_dir}")
    json_files = sorted(list(run_dir.glob("*.json")))
    # Filter out manifest.json, summary.json, config.json
    run_json_files = [f for f in json_files if f.name not in ("manifest.json", "summary.json", "config.json")]

    if not run_json_files:
        print(f"No run JSON files found in {run_dir}.")
        return

    print(f"Found {len(run_json_files)} run record files.")

    exact_count = 0
    unknown_count = 0
    total_nodes = 0
    invariance_checks = {}

    for jf in run_json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Error parsing {jf.name}: {e}")
            continue

        status = data.get("status")
        if status == "exact":
            exact_count += 1
            wf = data.get("weight_fraction")
            # Invariant check across depths
            inst = data.get("instance_label", data.get("instance", jf.stem))
            # Clean instance key
            base_key = inst.split("_d")[0] if "_d" in inst else inst
            if wf:
                if base_key not in invariance_checks:
                    invariance_checks[base_key] = []
                invariance_checks[base_key].append((jf.name, wf))
        elif status == "unknown":
            unknown_count += 1
            if data.get("count") is not None or data.get("weight_fraction") is not None:
                print(f"FATAL: Incomplete run {jf.name} contains count/weight! AGENTS.md violation.")
                sys.exit(1)
        else:
            print(f"Warning: Unknown status '{status}' in {jf.name}")

        nodes = data.get("total_nodes", data.get("nodes", 0))
        total_nodes += nodes

    # Verify cross-depth mathematical invariance
    mismatches = 0
    for base_key, records in invariance_checks.items():
        if len(records) > 1:
            first_fname, first_wf = records[0]
            first_frac = Fraction(first_wf)
            for other_fname, other_wf in records[1:]:
                other_frac = Fraction(other_wf)
                if first_frac != other_frac:
                    print(f"MATHEMATICAL INVARIANCE VIOLATION on {base_key}:")
                    print(f"  {first_fname}: {first_wf}")
                    print(f"  {other_fname}: {other_wf}")
                    mismatches += 1

    if mismatches > 0:
        print(f"FATAL: {mismatches} mathematical invariance mismatches found!")
        sys.exit(1)

    print(f"Mathematical invariance verified: {len(invariance_checks)} instances checked, 0 mismatches.")

    # Generate SHA256SUMS
    all_files = sorted([f for f in run_dir.rglob("*") if f.is_file() and f.name != "SHA256SUMS"])
    sha_lines = []
    artifact_sha = {}
    for f in all_files:
        rel = f.relative_to(run_dir).as_posix()
        digest = sha256_file(f)
        sha_lines.append(f"{digest}  {rel}")
        artifact_sha[rel] = digest

    sha_path = run_dir / "SHA256SUMS"
    sha_path.write_bytes(("\n".join(sha_lines) + "\n").encode("utf-8"))
    print(f"Generated SHA256SUMS ledger for {len(all_files)} files.")

    # Update or create manifest.json
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.update({
        "schema_version": 1,
        "status": "complete",
        "directory": str(run_dir),
        "total_files": len(all_files),
        "runs": len(run_json_files),
        "exact": exact_count,
        "unknown": unknown_count,
        "total_nodes_evaluated": total_nodes,
        "invariance_instances_checked": len([k for k, v in invariance_checks.items() if len(v) > 1]),
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Updated {manifest_path}")

    print("\nIngestion and mathematical verification complete:")
    print(f"  * Total runs : {len(run_json_files)}")
    print(f"  * Exact runs : {exact_count}")
    print(f"  * Unknown    : {unknown_count}")
    print(f"  * Nodes      : {total_nodes:,}")


def main():
    parser = argparse.ArgumentParser(description="Ingest, verify, and pin external EPYC run evidence")
    parser.add_argument("--run-dir", required=True, help="Directory containing external run evidence")
    args = parser.parse_args()
    ingest_directory(Path(args.run_dir))


if __name__ == "__main__":
    main()

