"""Append-only run evidence and subprocess-enforced wall limits."""
import csv
import hashlib
import json
import math
import multiprocessing as mp
import platform
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from .core import ALGORITHMS, oracle, solve
from .generate import FAMILIES, generate


def digest(data):
    return hashlib.sha256(data).hexdigest()


def doctor():
    return {"python": sys.version, "platform": platform.platform(),
            "machine": platform.machine(), "backend": "CPU Python integers",
            "gpu_used": False, "lean_verified_locally": False}


def _worker(conn, formula, algorithm, seconds, nodes, cache, memory_bytes):
    try:
        if memory_bytes is not None:
            if not sys.platform.startswith("linux"):
                conn.send({"status": "error", "count": None, "error": "memory_limit_unsupported",
                           "memory_limit": "unsupported", "peak_rss_kib": None})
                return
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        result = solve(formula, algorithm, seconds, nodes, cache)
        if sys.platform.startswith("linux"):
            import resource
            result["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        else:
            result["peak_rss_kib"] = None
        result["memory_limit"] = "rlimit_as" if memory_bytes is not None else "not_requested"
        conn.send(result)
    except Exception as e:
        conn.send({"status": "error", "count": None, "error": type(e).__name__})
    finally:
        conn.close()


def isolated(formula, algorithm, seconds, nodes, cache, memory_bytes=None):
    if memory_bytes is not None and (type(memory_bytes) is not int or memory_bytes <= 0):
        raise ValueError("invalid memory limit")
    ctx = mp.get_context("spawn")
    receive, send = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_worker, args=(send, formula, algorithm, seconds, nodes, cache, memory_bytes))
    start = perf_counter()
    proc.start()
    send.close()
    try:
        if receive.poll(seconds+2):
            try:
                result = receive.recv()
            except EOFError:
                result = {"status": "error", "count": None, "error": "worker exited"}
        else:
            result = {"status": "unknown", "count": None, "reason": "hard_wall_limit"}
    finally:
        proc.join(0.1)
        if proc.is_alive():
            proc.terminate()
            proc.join()
        receive.close()
    result.setdefault("peak_rss_kib", None)
    result.setdefault("memory_limit", "requested_unverified" if memory_bytes is not None else "not_requested")
    result["wall_seconds"] = perf_counter()-start
    return result


def validate_config(c):
    required = {"sizes", "ratios", "families", "seeds", "algorithms", "repeats",
                "seconds", "max_nodes", "cache_limit", "oracle_max_n"}
    if not required <= set(c) or set(c) - required - {"memory_bytes"} or set(c["seeds"]) != {"train", "holdout"}:
        raise ValueError("config keys must match the documented schema")
    if "memory_bytes" in c and (type(c["memory_bytes"]) is not int or c["memory_bytes"] <= 0):
        raise ValueError("invalid memory_bytes")
    def ints(xs, low, high):
        return (isinstance(xs, list) and bool(xs) and len(set(xs)) == len(xs)
                and all(type(x) is int and low <= x <= high for x in xs))
    if not ints(c["sizes"], 3, 256):
        raise ValueError("sizes must be distinct integers in [3,256]")
    if not isinstance(c["ratios"], list) or not c["ratios"] or not all(
        type(x) in (int, float) and math.isfinite(x) and 0 < x <= 20 for x in c["ratios"]):
        raise ValueError("invalid ratios")
    for split in ("train", "holdout"):
        if not ints(c["seeds"][split], 0, 2**32-1):
            raise ValueError("invalid seeds")
    if set(c["seeds"]["train"]) & set(c["seeds"]["holdout"]):
        raise ValueError("seed splits overlap")
    for key, allowed in (("families", FAMILIES), ("algorithms", ALGORITHMS)):
        if not isinstance(c[key], list) or not c[key] or len(set(c[key])) != len(c[key]) or any(
            x not in allowed for x in c[key]):
            raise ValueError(f"invalid {key}")
    for key, low, high in (("repeats", 1, 10), ("max_nodes", 1, 10_000_000),
                           ("cache_limit", 0, 1_000_000), ("oracle_max_n", 0, 16)):
        if type(c[key]) is not int or not low <= c[key] <= high:
            raise ValueError(f"invalid {key}")
    if type(c["seconds"]) not in (int, float) or not math.isfinite(c["seconds"]) or not 0 < c["seconds"] <= 60:
        raise ValueError("seconds must be in (0,60]")
    runs = math.prod(len(c[k]) for k in ("sizes", "ratios", "families", "algorithms"))*c["repeats"]
    if runs * max(map(len, c["seeds"].values())) > 5000:
        raise ValueError("campaign exceeds 5000-run safety cap")


def campaign(config_path, out, split):
    c = json.loads(config_path.read_text())
    validate_config(c)
    if split not in ("train", "holdout"):
        raise ValueError("invalid split")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    instances = out / "instances"
    instances.mkdir()
    config_bytes = json.dumps(c, sort_keys=True, indent=2).encode()
    (out / "config.json").write_bytes(config_bytes)
    root = Path(__file__).resolve().parent.parent
    paths = sorted(list((root / "sat_frontier").glob("*.py")) + list((root / "tests").glob("*.py")) + [root / "pyproject.toml", root / "verify_evidence.py"])
    source_hashes = {str(p.relative_to(root)): digest(p.read_bytes()) for p in paths}
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
    git_status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, capture_output=True, text=True)
    meta = {"schema_version": 1, "split": split, "environment": doctor(),
            "config_sha256": digest(config_bytes), "source_sha256": source_hashes,
            "git_dirty": bool(git_status.stdout) if git_status.returncode == 0 else None,
            "git_status_porcelain": git_status.stdout if git_status.returncode == 0 else None,
            "git_revision": git.stdout.strip() if git.returncode == 0 else None,
            "status": "running", "measurement": "solver elapsed excludes process startup; wall includes it"}
    (out / "manifest.json").write_text(json.dumps(meta, indent=2, sort_keys=True)+"\n")
    rows = []
    with (out / "runs.jsonl").open("x") as log:
        for family in c["families"]:
            for n in c["sizes"]:
                for ratio in c["ratios"]:
                    for seed in c["seeds"][split]:
                        f = generate(family, n, ratio, seed)
                        data = f.dimacs().encode()
                        sha = digest(data)
                        (instances / f"{sha}.cnf").write_bytes(data)
                        expected = oracle(f) if n <= c["oracle_max_n"] else None
                        for repeat in range(c["repeats"]):
                            # Rotate order to reduce systematic warm-up/order bias.
                            algs = c["algorithms"]
                            offset = (seed+repeat) % len(algs)
                            for algorithm in algs[offset:] + algs[:offset]:
                                result = isolated(f, algorithm, c["seconds"], c["max_nodes"], c["cache_limit"], c.get("memory_bytes"))
                                if result["status"] == "exact":
                                    validation = ("oracle_pass" if expected == result["count"] else "oracle_fail") if expected is not None else "unchecked"
                                else:
                                    validation = "not_exact"
                                row = dict(family=family, n=n, ratio=ratio, seed=seed,
                                           split=split, repeat=repeat, algorithm=algorithm,
                                           instance_sha256=sha, oracle_count=expected,
                                           validation=validation, **{k:v for k,v in result.items() if k != "algorithm"})
                                log.write(json.dumps(row, sort_keys=True)+"\n")
                                log.flush()
                                rows.append(row)
                                if validation == "oracle_fail" or result["status"] == "error":
                                    raise ValueError(f"correctness/worker failure; preserved evidence at {out}")
    # Agreement on larger instances is evidence, not an independent proof.
    counts = defaultdict(set)
    for row in rows:
        if row["status"] == "exact":
            counts[row["instance_sha256"]].add(row["count"])
    if any(len(v) > 1 for v in counts.values()):
        raise ValueError("solver disagreement; inspect preserved evidence")
    fields = sorted(set().union(*(r.keys() for r in rows)))
    with (out / "runs.csv").open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    meta.update(status="complete", runs=len(rows), exact=sum(r["status"] == "exact" for r in rows),
                oracle_pass=sum(r["validation"] == "oracle_pass" for r in rows))
    meta["artifact_sha256"] = {p.name: digest(p.read_bytes()) for p in
                               (out / "runs.jsonl", out / "runs.csv", out / "config.json")}
    (out / "manifest.json").write_text(json.dumps(meta, indent=2, sort_keys=True)+"\n")
    return {"status": "complete", "runs": len(rows), "exact": meta["exact"],
            "oracle_pass": meta["oracle_pass"], "out": str(out)}
