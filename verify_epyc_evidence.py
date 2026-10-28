"""Verify mathematical partition integrity, cube summation, and cross-depth invariance for EPYC Cube-and-Conquer evidence."""
import argparse
from fractions import Fraction
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_epyc_run_directory(dir_path: Path):
    dir_path = Path(dir_path).resolve()
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    manifest_file = dir_path / "manifest.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest missing: {manifest_file}")

    manifest = json.loads(manifest_file.read_text())
    if manifest.get("schema_version") != 1:
        raise ValueError(f"Invalid schema_version in {manifest_file}")

    json_files = sorted(dir_path.glob("*.json"))
    runs_checked = 0
    exact_runs = 0
    unknown_runs = 0
    total_nodes_evaluated = 0

    instance_exact_values = defaultdict(list)

    for jf in json_files:
        if jf.name == "manifest.json":
            continue

        data = json.loads(jf.read_text())
        status = data.get("status")
        results = data.get("results", [])
        total_nodes = data.get("total_nodes", 0)
        total_nodes_evaluated += total_nodes

        if results:
            # 1. Node sum invariant: sum(cube_nodes) == total_nodes
            sum_nodes = sum(r.get("nodes", 0) for r in results)
            if sum_nodes != total_nodes:
                raise ValueError(f"Node sum mismatch in {jf.name}: {sum_nodes} != {total_nodes}")

            # 2. Incomplete cubes invariant: count(incomplete) == cubes_incomplete
            incomplete = sum(1 for r in results if r.get("status") != "exact")
            if incomplete != data.get("cubes_incomplete", 0):
                raise ValueError(f"Incomplete cube count mismatch in {jf.name}: {incomplete} != {data.get('cubes_incomplete')}")

            # 3. Summation invariant for exact results
            if status == "exact":
                exact_runs += 1
                if "weight_fraction" in data and data["weight_fraction"] is not None:
                    # Rational WMC summation
                    frac_sum = sum(
                        Fraction(r["weight_fraction"])
                        for r in results
                        if "weight_fraction" in r and r["weight_fraction"] is not None
                    )
                    expected_frac = Fraction(data["weight_fraction"])
                    if frac_sum != expected_frac:
                        raise ValueError(f"Rational weight fraction sum mismatch in {jf.name}: {frac_sum} != {expected_frac}")
                elif "count" in data and data["count"] is not None:
                    count_sum = sum(r.get("count", 0) for r in results)
                    if count_sum != data["count"]:
                        raise ValueError(f"Count sum mismatch in {jf.name}: {count_sum} != {data['count']}")
            elif status in ("unknown", "budget_exceeded", "timeout"):
                unknown_runs += 1
            else:
                raise ValueError(f"Unexpected status '{status}' in {jf.name}")

        runs_checked += 1

        # Track for cross-depth invariance
        parts = jf.stem.split("_d")
        if len(parts) >= 2 and status == "exact":
            inst_base = parts[0]
            val = data.get("weight_fraction") or data.get("count")
            if val is not None:
                instance_exact_values[inst_base].append((jf.name, str(val)))

    # 4. Cross-depth invariance check
    multi_depth_verified = 0
    for inst_name, observations in instance_exact_values.items():
        if len(observations) > 1:
            distinct_values = set(val for _, val in observations)
            if len(distinct_values) != 1:
                raise ValueError(f"Cross-depth inconsistency on {inst_name}: {observations}")
            multi_depth_verified += 1

    return {
        "status": "verified",
        "directory": str(dir_path.relative_to(ROOT) if dir_path.is_relative_to(ROOT) else dir_path),
        "json_runs": runs_checked,
        "exact_runs": exact_runs,
        "unknown_runs": unknown_runs,
        "total_nodes_evaluated": total_nodes_evaluated,
        "multi_depth_instances_invariant": multi_depth_verified,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="*", default=["evidence/epyc-cube-001", "evidence/epyc-cube-002"])
    args = parser.parse_args()

    all_passed = True
    summaries = []
    for d in args.directories:
        try:
            res = verify_epyc_run_directory(ROOT / d)
            summaries.append(res)
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(f"FAILED {d}: {e}", file=sys.stderr)
            all_passed = False

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
