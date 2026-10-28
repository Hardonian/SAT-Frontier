import argparse
import json
import sys
from pathlib import Path
from .core import ALGORITHMS, parse_dimacs, solve
from .experiment import campaign, doctor


def main():
    p = argparse.ArgumentParser(description="SAT-Frontier: exact counting research")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    s = sub.add_parser("solve")
    s.add_argument("input", type=Path)
    s.add_argument("--algorithm", choices=ALGORITHMS, default="combined")
    s.add_argument("--seconds", type=float, default=5)
    s.add_argument("--max-nodes", type=int, default=1_000_000)
    c = sub.add_parser("campaign")
    c.add_argument("--config", type=Path, required=True)
    c.add_argument("--out", type=Path, required=True)
    c.add_argument("--split", choices=("train", "holdout"), default="train")
    args = p.parse_args()
    try:
        if args.command == "doctor":
            result = doctor()
        elif args.command == "solve":
            result = solve(parse_dimacs(args.input.read_text()), args.algorithm,
                           args.seconds, args.max_nodes)
        else:
            result = campaign(args.config, args.out, args.split)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if result.get("status") == "unknown" else 0
    except (ValueError, OSError, KeyError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
