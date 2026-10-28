"""Verify stored hashes, not scientific validity. Uses no third-party packages."""
import hashlib
import json
import sys
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(run):
    run = Path(run).resolve()
    root = Path(__file__).resolve().parent
    m = json.loads((run/"manifest.json").read_text())
    if m["status"] != "complete":
        raise ValueError("run is incomplete")
    for name, expected in m["source_sha256"].items():
        path = (root/name).resolve()
        if not path.is_relative_to(root) or sha(path) != expected:
            raise ValueError(f"source hash mismatch: {name}")
    for name, expected in m["artifact_sha256"].items():
        path = (run/name).resolve()
        if not path.is_relative_to(run) or sha(path) != expected:
            raise ValueError(f"artifact hash mismatch: {name}")
    if sha(run/"config.json") != m["config_sha256"]:
        raise ValueError("configuration mismatch")
    rows = [json.loads(line) for line in (run/"runs.jsonl").read_text().splitlines()]
    if len(rows) != m["runs"]:
        raise ValueError("run count mismatch")
    ids = set()
    for row in rows:
        instance = row["instance_sha256"]
        if len(instance) != 64 or any(c not in "0123456789abcdef" for c in instance):
            raise ValueError("invalid instance digest")
        ids.add(instance)
        if row["status"] != "exact" and row["count"] is not None:
            raise ValueError("incomplete result contains a count")
    for instance in ids:
        if sha(run/"instances"/(instance+".cnf")) != instance:
            raise ValueError("instance hash mismatch")
    return {"status": "hashes_verified", "runs": len(rows), "instances": len(ids),
            "note": "Integrity only; does not establish a proof or independent correctness."}


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("usage: python3 verify_evidence.py RUN_DIRECTORY")
        print(json.dumps(verify(sys.argv[1]), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
