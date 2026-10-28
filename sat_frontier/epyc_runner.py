"""CLI and benchmark runner optimized for high-core AMD EPYC servers."""
import argparse
import json
import os
import resource
import sys
from pathlib import Path
from time import perf_counter

from .core import parse_dimacs
from .cube_conquer import (
    parallel_cube_and_conquer,
    parallel_cube_and_conquer_wmc,
    recommend_workers,
    _discover_resources,
)


def load_formula(path):
    """Load formula from file, detecting if it has weighted literal declarations."""
    text = Path(path).read_text(encoding='utf-8', errors='replace')
    is_weighted = any(line.strip().startswith('c p weight') for line in text.splitlines())
    if is_weighted:
        clauses = []
        weights = {}
        n_vars = 0
        from fractions import Fraction
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith('c p weight'):
                parts = line.split()
                lit = int(parts[3])
                w = Fraction(parts[4])
                weights[lit] = w
            elif line.startswith('p cnf'):
                parts = line.split()
                n_vars = int(parts[2])
            elif not line.startswith('c'):
                lits = [int(x) for x in line.split() if x != '0']
                if lits:
                    clauses.append(lits)
        from .wmc import WeightedFormula
        return WeightedFormula(clauses, n_vars=n_vars, weights=weights), True
    else:
        return parse_dimacs(text), False


def _peak_rss_mb() -> int:
    """Return peak RSS in MB if supported, else -1."""
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on macOS
        base = getattr(resource, 'RLIMIT_AS', None)
        # getrusage returns KB on Linux
        return int(usage.ru_maxrss) // 1024
    except Exception:
        return -1


def main():
    parser = argparse.ArgumentParser(description="SAT-Frontier EPYC High-Core Solver")
    parser.add_argument("instance", help="Path to CNF or WCNF formula")
    parser.add_argument("--depth", type=int, default=4, help="Cube lookahead depth (generates 2^depth cubes)")
    parser.add_argument("--workers", type=int, default=None, help="Number of worker processes (default: resource-aware recommendation)")
    parser.add_argument("--algo", default=None, help="Solver variant (combined or combined_wmc)")
    parser.add_argument("--seconds-per-cube", type=float, default=30.0, help="Per-cube time budget")
    parser.add_argument("--max-nodes-per-cube", type=int, default=100000, help="Per-cube node budget")
    parser.add_argument("--out", default=None, help="Output JSON path")
    parser.add_argument("--checkpoint-dir", default=None, help="Durable per-cube checkpoint directory")
    parser.add_argument("--numa", default="interleave", choices=["interleave", "local", "none"], help="NUMA binding strategy")
    parser.add_argument("--per-cube-memory-mb", type=int, default=50, help="Conservative per-cube memory budget in MB")

    args = parser.parse_args()
    num_cpus = os.cpu_count() or 1

    # Resource-aware worker sizing
    resources = _discover_resources()
    recommendation = recommend_workers(
        instance_bytes=Path(args.instance).stat().st_size,
        per_cube_memory_mb=args.per_cube_memory_mb,
        max_workers=args.workers,
    )
    workers = recommendation["recommended_workers"] if args.workers is None else args.workers

    print(f"Loading instance: {args.instance}")
    formula, is_weighted = load_formula(args.instance)
    algo = args.algo or ('combined_wmc' if is_weighted else 'combined')

    print(f"System cores detected: {num_cpus} | Allocating workers: {workers}")
    print(f"Mode: {'Weighted (#WMC)' if is_weighted else 'Unweighted (#SAT)'} | Algorithm: {algo}")
    print(f"NUMA strategy: {args.numa} | Resources: {json.dumps(resources, sort_keys=True)}")
    print(f"Generating lookahead cubes at depth {args.depth} (2^{args.depth} = {2**args.depth} cubes)...")

    start_time = perf_counter()
    if is_weighted:
        res = parallel_cube_and_conquer_wmc(
            formula,
            depth=args.depth,
            num_workers=workers,
            algo=algo,
            seconds_per_cube=args.seconds_per_cube,
            max_nodes_per_cube=args.max_nodes_per_cube,
            checkpoint_dir=args.checkpoint_dir,
        )
    else:
        res = parallel_cube_and_conquer(
            formula,
            depth=args.depth,
            num_workers=workers,
            algo=algo,
            seconds_per_cube=args.seconds_per_cube,
            max_nodes_per_cube=args.max_nodes_per_cube,
            checkpoint_dir=args.checkpoint_dir,
        )

    elapsed = perf_counter() - start_time

    res['instance'] = str(args.instance)
    res['total_wall_seconds'] = elapsed
    res['cubes_per_second'] = res['cubes_total'] / elapsed if elapsed > 0 else 0
    res['peak_rss_mb'] = _peak_rss_mb()
    res['numa_strategy'] = args.numa
    res['resource_discovery'] = resources
    res['worker_recommendation'] = recommendation

    print("\n" + "=" * 60)
    print(f"EPYC Parallel Run Status: {res['status'].upper()}")
    if is_weighted:
        print(f"Exact Probability / Weight Fraction: {res.get('weight_fraction')}")
        print(f"Approximate Float: {res.get('weight_float')}")
    else:
        print(f"Exact Model Count: {res.get('count')}")
    print(f"Cubes: {res['cubes_total']} total ({res['cubes_incomplete']} incomplete)")
    print(f"Total Search Nodes: {res['total_nodes']:,}")
    print(f"Wall Clock Time: {elapsed:.3f}s ({res['cubes_per_second']:.1f} cubes/sec on {workers} workers)")
    if res.get('cube_time_median') is not None:
        print(f"Cube time median/max: {res['cube_time_median']:.4f}s / {res['cube_time_max']:.4f}s")
    print(f"Peak RSS: {res['peak_rss_mb']} MB")
    print("=" * 60)

    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=2) + '\n')
        print(f"Saved results to {args.out}")

    sys.exit(0 if res['status'] == 'exact' else 2)


if __name__ == '__main__':
    main()
