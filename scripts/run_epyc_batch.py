#!/usr/bin/env python3
"""Batch EPYC Cube-and-Conquer runner for scaling evidence."""
import json
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "evidence/epyc-cube-001"
INSTANCES = list((ROOT / "evidence/policy-train-v02/instances").glob("*.cnf"))

DEPTHS = [4, 5, 6]
WORKERS = 64
SECONDS_PER_CUBE = 30.0
MAX_NODES_PER_CUBE = 200000

EVIDENCE.mkdir(parents=True, exist_ok=True)


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
    manifest_path = EVIDENCE / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest.setdefault("schema_version", 1)
    manifest.setdefault("study", "epyc_cube_and_conquer_scale_up")
    manifest.setdefault("runs", [])

    tasks = []
    for inst in INSTANCES:
        for depth in DEPTHS:
            out_name = f"{inst.stem}_d{depth}_w{WORKERS}.json"
            out_path = EVIDENCE / out_name
            if out_path.exists():
                continue
            tasks.append((inst, depth, out_path))

    print(f"Queued {len(tasks)} runs across {len(INSTANCES)} instances x {len(DEPTHS)} depths")

    with ProcessPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(run_epyc, inst, depth, WORKERS, SECONDS_PER_CUBE, MAX_NODES_PER_CUBE, out): (inst, depth)
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
