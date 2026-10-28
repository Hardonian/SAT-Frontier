#!/usr/bin/env python3
"""Batch EPYC Cube-and-Conquer runner for scaling evidence."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent.parent


def run_epyc(instance: Path, depth: int, workers: int, seconds: float, max_nodes: int, out: Path):
    cmd = [
        sys.executable, "-m", "sat_frontier.epyc_runner",
        str(instance),
        "--depth", str(depth),
        "--workers", str(workers),
        "--seconds-per-cube", str(seconds),
        "--max-nodes-per-cube", str(max_nodes),
        "--out", str(out),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, timeout=600)
        return {
            "instance": str(instance),
            "depth": depth,
            "workers": workers,
            "exit_code": proc.returncode,
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-1000:],
            "out": str(out),
        }
    except subprocess.TimeoutExpired:
        return {
            "instance": str(instance),
            "depth": depth,
            "workers": workers,
            "exit_code": -1,
            "stdout_tail": "",
            "stderr_tail": "timeout",
            "out": str(out),
        }


def main():
    parser = argparse.ArgumentParser(description="Batch EPYC Cube-and-Conquer scaling runner")
    parser.add_argument("--evidence-dir", default=str(ROOT / "evidence/epyc-cube-003"), help="Output evidence directory")
    parser.add_argument("--instances-dir", default=str(ROOT / "evidence/cut-wmc-001/instances"), help="Directory of CNF/WCNF instances")
    parser.add_argument("--depths", nargs="+", type=int, default=[4, 6, 8], help="Cube lookahead depths")
    parser.add_argument("--workers", type=int, default=64, help="Worker count per run")
    parser.add_argument("--seconds-per-cube", type=float, default=30.0, help="Per-cube time budget in seconds")
    parser.add_argument("--max-nodes-per-cube", type=int, default=200000, help="Per-cube search node budget")
    parser.add_argument("--concurrency", type=int, default=1, help="Concurrent EPYC runs (default 1 to avoid oversubscribing cores)")
    args = parser.parse_args()

    evidence_dir = Path(args.evidence_dir)
    instances_dir = Path(args.instances_dir)
    instances = sorted(list(instances_dir.glob("*.cnf")))

    if not instances:
        print(f"No .cnf instances found in {instances_dir}")
        sys.exit(1)

    evidence_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = evidence_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest.setdefault("schema_version", 1)
    manifest.setdefault("study", "epyc_cube_and_conquer_batch")
    manifest.setdefault("runs", [])

    tasks = []
    for inst in instances:
        for depth in args.depths:
            out_name = f"{inst.stem}_d{depth}_w{args.workers}.json"
            out_path = evidence_dir / out_name
            if out_path.exists():
                continue
            tasks.append((inst, depth, out_path))

    print(f"Queued {len(tasks)} runs across {len(instances)} instances x {len(args.depths)} depths")
    print(f"Output directory: {evidence_dir}")

    with ProcessPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {
            pool.submit(run_epyc, inst, depth, args.workers, args.seconds_per_cube, args.max_nodes_per_cube, out): (inst, depth)
            for inst, depth, out in tasks
        }
        for fut in as_completed(futures):
            inst, depth = futures[fut]
            try:
                res = fut.result()
                manifest["runs"].append({
                    "instance": res["instance"],
                    "depth": depth,
                    "workers": res["workers"],
                    "exit_code": res["exit_code"],
                    "out": res["out"],
                })
                status = "OK" if res["exit_code"] == 0 else f"FAIL({res['exit_code']})"
                print(f"[{status}] {inst.name} depth={depth}")
                if res["exit_code"] != 0:
                    print("  STDERR:", res["stderr_tail"][-300:])
            except Exception as exc:
                print(f"[ERROR] {inst.name} depth={depth}: {exc}")

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Manifest updated: {manifest_path}")


if __name__ == "__main__":
    main()
