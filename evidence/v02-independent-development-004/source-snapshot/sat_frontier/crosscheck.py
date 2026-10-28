"""Run a small development-only differential and metamorphic #SAT campaign."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from .core import Formula
from .experiment import isolated, doctor
from .generate import generate
from .independent import count, minimize


def sha(data):
    return hashlib.sha256(data).hexdigest()


def library_hashes(binary):
    """Record resolved shared-object bytes for this trusted executable on Linux."""
    if not sys.platform.startswith("linux"):
        return {"status": "unsupported", "sha256": {}}
    result = subprocess.run(["ldd", str(binary)], capture_output=True, text=True, check=False)
    if result.returncode:
        return {"status": "unavailable", "sha256": {}, "detail": result.stderr}
    paths = set()
    for line in result.stdout.splitlines():
        for token in line.split():
            if token.startswith("/") and Path(token).is_file():
                paths.add(Path(token).resolve())
    return {"status": "recorded", "sha256": {str(p): sha(p.read_bytes()) for p in sorted(paths)}}


def transformations(f):
    """Each pair is (formula, multiplicative factor)."""
    perm = {i: f.n + 1 - i for i in range(1, f.n+1)}
    rename = tuple(tuple((1 if x > 0 else -1)*perm[abs(x)] for x in c) for c in f.clauses)
    return {
        "original": (f, 1),
        "rename": (Formula(f.n, rename), 1),
        "order": (Formula(f.n, tuple(tuple(reversed(c)) for c in reversed(f.clauses))), 1),
        "duplicate": (Formula(f.n, f.clauses + f.clauses[:1]), 1),
        "tautology": (Formula(f.n, f.clauses + ((1, -1),)), 1),
        "forced": (Formula(f.n+1, f.clauses + ((f.n+1,),)), 1),
        "unused": (Formula(f.n+1, f.clauses), 2),
    }


def campaign(binary, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out/"instances").mkdir()
    binary = Path(binary).resolve()
    root = Path(__file__).resolve().parent.parent
    config = {"families": ["random", "planted", "disconnected", "contradictory"],
              "sizes": [18, 24, 32], "ratio": 3, "seeds": [311, 719],
              "seconds": 10, "memory_bytes": 536870912, "algorithm": "combined",
              "split": "development_not_holdout"}
    config_bytes = (json.dumps(config, indent=2, sort_keys=True)+"\n").encode()
    (out/"config.json").write_bytes(config_bytes)
    paths = sorted(list((root/"sat_frontier").glob("*.py")) + list((root/"tests").glob("*.py")) + [root/"pyproject.toml", root/"verify_evidence.py"])
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, capture_output=True, text=True, check=True).stdout
    rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    meta = {"status": "running", "schema_version": 1, "split": config["split"],
            "source_sha256": {str(p.relative_to(root)): sha(p.read_bytes()) for p in paths},
            "git_revision": rev, "git_dirty": bool(status), "git_status_porcelain": status,
            "config_sha256": sha(config_bytes), "environment": doctor(),
            "dependency": {"name": "sharpSAT-TD", "expected_source_revision": "0c234c11b77115bad89484e80e1d2fc95dd42317", "binary_sha256": sha(binary.read_bytes()), "binary_path": str(binary), "matches_tested_binary": sha(binary.read_bytes()) == "85b94b45c3967df384f5ced2e4670fe270f3fc77ee67ca943b6b390ac75f92b5", "shared_libraries": library_hashes(binary)},
            "measurement": "Linux direct-child wait4/getrusage peak RSS KiB (may include inherited fork/startup high-water); RLIMIT_AS bytes; solver elapsed excludes startup"}
    (out/"manifest.json").write_text(json.dumps(meta, indent=2, sort_keys=True)+"\n")
    rows = []
    with (out/"runs.jsonl").open("x") as log:
        for family in config["families"]:
            for n in config["sizes"]:
                for seed in config["seeds"]:
                    formula = generate(family, n, config["ratio"], seed)
                    base = None
                    for name, (f, factor) in transformations(formula).items():
                        data = f.dimacs().encode(); instance = sha(data)
                        (out/"instances"/(instance+".cnf")).write_bytes(data)
                        ours = isolated(f, config["algorithm"], config["seconds"], 1000000, 100000, config["memory_bytes"])
                        theirs = count(binary, f, config["seconds"], config["memory_bytes"])
                        row = {"family": family, "n": f.n, "seed": seed, "transform": name,
                               "instance_sha256": instance, "ours": ours, "independent": theirs,
                               "status": ours["status"], "count": ours["count"]}
                        rows.append(row); log.write(json.dumps(row, sort_keys=True)+"\n"); log.flush()
                        if ours["status"] != "exact" or theirs["status"] != "exact":
                            raise RuntimeError(f"inconclusive counter; evidence preserved at {out}")
                        if base is None:
                            base = ours["count"]
                        mismatch = ours["count"] != theirs["count"] or ours["count"] != base*factor
                        if mismatch:
                            (out/"disagreement.cnf").write_bytes(data)
                            (out/"disagreement.json").write_text(json.dumps(row, indent=2, sort_keys=True)+"\n")
                            if ours["count"] != theirs["count"]:
                                def disagrees(candidate):
                                    a = isolated(candidate, config["algorithm"], config["seconds"], 1000000, 100000, config["memory_bytes"])
                                    b = count(binary, candidate, config["seconds"], config["memory_bytes"])
                                    if a["status"] != "exact" or b["status"] != "exact":
                                        raise RuntimeError("minimization inconclusive; original retained")
                                    return a["count"] != b["count"]
                                minimal = minimize(f, disagrees)
                                (out/"minimized.cnf").write_text(minimal.dimacs())
                            else:
                                def disagrees(candidate):
                                    transformed, multiple = transformations(candidate)[name]
                                    a = isolated(candidate, config["algorithm"], config["seconds"], 1000000, 100000, config["memory_bytes"])
                                    b = isolated(transformed, config["algorithm"], config["seconds"], 1000000, 100000, config["memory_bytes"])
                                    if a["status"] != "exact" or b["status"] != "exact":
                                        raise RuntimeError("minimization inconclusive; original retained")
                                    return b["count"] != a["count"] * multiple
                                minimal = minimize(formula, disagrees)
                                (out/"minimized-base.cnf").write_text(minimal.dimacs())
                                (out/"minimized.cnf").write_text(transformations(minimal)[name][0].dimacs())
                            raise RuntimeError(f"count disagreement; evidence preserved at {out}")
    meta.update(status="complete", runs=len(rows), exact=len(rows),
                artifact_sha256={p.name: sha(p.read_bytes()) for p in (out/"config.json", out/"runs.jsonl")})
    (out/"manifest.json").write_text(json.dumps(meta, indent=2, sort_keys=True)+"\n")
    return {"status": "complete", "runs": len(rows), "out": str(out)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--binary", required=True); p.add_argument("--out", required=True)
    a = p.parse_args()
    print(json.dumps(campaign(a.binary, a.out), indent=2))


if __name__ == "__main__":
    main()
