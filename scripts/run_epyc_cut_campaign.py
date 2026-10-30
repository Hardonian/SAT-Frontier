"""Run a cut-CNF campaign in a fresh, immutable evidence directory.

A failed or interrupted campaign retains its raw logs and partial records, but has
no complete manifest. A new invocation always requires a new evidence directory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_result(data, returncode, expected_cubes=None):
    """Reject process failures and inconsistent solver outputs, never invent metrics."""
    status = data.get('status')
    if (status, returncode) not in (('exact', 0), ('unknown', 2)):
        raise ValueError(f'runner status/exit mismatch: {status!r}/{returncode}')
    results = data['results']
    total = data['cubes_total']
    incomplete = data['cubes_incomplete']
    nodes = data['total_nodes']
    if not isinstance(results, list) or len(results) != total or not results:
        raise ValueError('cube results do not match cubes_total')
    if expected_cubes is not None:
        actual = [tuple(r['cube']) for r in results]
        if len(actual) != len(set(actual)) or set(actual) != set(expected_cubes):
            raise ValueError('cube partition does not match requested tasks')
    if sum(r['nodes'] for r in results) != nodes:
        raise ValueError('cube node sum mismatch')
    if sum(r['status'] != 'exact' for r in results) != incomplete:
        raise ValueError('incomplete cube count mismatch')
    if status == 'exact':
        if incomplete:
            raise ValueError('exact result contains incomplete cubes')
        if data.get('weight_fraction') is not None:
            value = Fraction(data['weight_fraction'])
            if sum((Fraction(r['weight_fraction']) for r in results), Fraction()) != value:
                raise ValueError('cube weight sum mismatch')
            return ('weighted', value)
        if data.get('count') is not None:
            value = data['count']
            if sum(r['count'] for r in results) != value:
                raise ValueError('cube count sum mismatch')
            return ('unweighted', value)
        raise ValueError('exact result missing count or weight')
    if data.get('weight_fraction') is not None or data.get('count') is not None:
        raise ValueError('unknown result contains a count')
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=None)
    parser.add_argument('--depths', nargs='+', type=int, default=[4, 6, 8])
    parser.add_argument('--instances-dir', default=str(ROOT / 'instances' / 'epyc-cut-frontier'))
    parser.add_argument('--evidence-dir', default=str(ROOT / 'evidence' / 'epyc-cut-001'))
    parser.add_argument('--seconds-per-cube', type=float, default=30.0)
    parser.add_argument('--max-nodes-per-cube', type=int, default=200000)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    workers = args.workers if args.workers is not None else min(64, os.cpu_count() or 1)
    if workers < 1 or any(d < 0 for d in args.depths) or len(set(args.depths)) != len(args.depths):
        parser.error('workers must be positive and depths must be distinct nonnegative integers')
    if not math.isfinite(args.seconds_per_cube) or args.seconds_per_cube <= 0 or args.max_nodes_per_cube <= 0:
        parser.error('budgets must be positive and finite')
    cnfs = sorted(Path(args.instances_dir).glob('*.cnf'))
    if not cnfs:
        parser.error('no CNF instances found')
    evidence = Path(args.evidence_dir).absolute()
    print(f'Instances: {len(cnfs)}; depths: {args.depths}; workers: {workers}; evidence: {evidence}', flush=True)
    if args.dry_run:
        return
    # Atomic reservation, including refusal of existing empty dirs and symlinks.
    evidence.mkdir(parents=True, exist_ok=False)
    (evidence / 'instances').mkdir()
    (evidence / 'checkpoints').mkdir()
    (evidence / 'logs').mkdir()
    (evidence / 'results').mkdir()
    config = {'study': evidence.name, 'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'workers': workers, 'depths': args.depths, 'seconds_per_cube': args.seconds_per_cube,
              'max_nodes_per_cube': args.max_nodes_per_cube,
              'hardware': {'system': platform.system(), 'machine': platform.machine(),
                           'cpu': platform.processor(), 'logical_cpus': os.cpu_count(), 'python': platform.python_version()}}
    (evidence / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
    sources = [ROOT / 'pyproject.toml', Path(__file__).resolve()]
    sources.extend(sorted((ROOT / 'sat_frontier').rglob('*.py')))
    sources.extend(sorted((ROOT / 'tests').rglob('*.py')))
    source_hashes = {str(p.relative_to(ROOT)): sha256_file(p) for p in sources}
    (evidence / 'source-hashes.json').write_text(json.dumps(source_hashes, indent=2) + '\n')
    # Freeze exactly the bytes passed to the solver, with digest-addressed filenames.
    instances = []
    for cnf in cnfs:
        content = cnf.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        pinned = evidence / 'instances' / (digest + '.cnf')
        if not pinned.exists():
            pinned.write_bytes(content)
        instances.append((cnf.stem, digest, pinned))
    headers = ['instance', 'instance_sha256', 'depth', 'workers', 'cubes_total', 'cubes_incomplete',
               'status', 'search_nodes', 'solver_wall_seconds', 'process_wall_seconds',
               'cubes_per_second', 'count', 'weight_fraction', 'returncode', 'result_path']
    invariant = {}
    comparisons = exact = unknown = runs = 0
    with (evidence / 'runs.csv').open('x', newline='', encoding='utf-8') as csvfile, \
         (evidence / 'runs.jsonl').open('x', encoding='utf-8') as jsonfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        csvfile.flush()
        for name, digest, pinned in instances:
            for depth in args.depths:
                run_id = f'{name}_d{depth}_w{workers}'
                result = evidence / 'results' / (run_id + '.json')
                checkpoint = evidence / 'checkpoints' / run_id
                checkpoint.mkdir()
                cmd = [sys.executable, '-m', 'sat_frontier.epyc_runner', str(pinned), '--depth', str(depth),
                       '--workers', str(workers), '--seconds-per-cube', str(args.seconds_per_cube),
                       '--max-nodes-per-cube', str(args.max_nodes_per_cube), '--out', str(result),
                       '--checkpoint-dir', str(checkpoint)]
                start = time.perf_counter()
                proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
                elapsed = time.perf_counter() - start
                (evidence / 'logs' / (run_id + '.json')).write_text(json.dumps(
                    {'command': cmd, 'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr,
                     'process_wall_seconds': elapsed}, indent=2) + '\n')
                try:
                    data = json.loads(result.read_text())
                    sys.path.insert(0, str(ROOT))
                    from sat_frontier.epyc_runner import load_formula
                    from sat_frontier.cube_conquer import generate_cubes
                    formula, weighted = load_formula(pinned)
                    n_vars = formula.n_vars if weighted else formula.n
                    expected_cubes = generate_cubes(formula.clauses, n_vars, depth=depth)
                    value = validate_result(data, proc.returncode, expected_cubes)
                    if value is not None:
                        if digest in invariant:
                            if invariant[digest] != value:
                                raise ValueError(f'cross-depth mismatch for {name}: {invariant[digest]} != {value}')
                            comparisons += 1
                        else:
                            invariant[digest] = value
                        exact += 1
                    else:
                        unknown += 1
                    row = {'instance': name, 'instance_sha256': digest, 'depth': depth, 'workers': workers,
                           'cubes_total': data['cubes_total'], 'cubes_incomplete': data['cubes_incomplete'],
                           'status': data['status'], 'search_nodes': data['total_nodes'],
                           'solver_wall_seconds': data['total_wall_seconds'], 'process_wall_seconds': elapsed,
                           'cubes_per_second': data['cubes_per_second'], 'count': data.get('count'),
                           'weight_fraction': data.get('weight_fraction'), 'returncode': proc.returncode,
                           'result_path': str(result.relative_to(evidence))}
                except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
                    print(f'FAILED {run_id}: {exc}; retained logs and partial evidence in {evidence}', file=sys.stderr)
                    return 1
                writer.writerow(row)
                jsonfile.write(json.dumps(row) + '\n')
                csvfile.flush()
                jsonfile.flush()
                runs += 1
                print(f'{run_id}: {data["status"]}, nodes={data["total_nodes"]}, process_seconds={elapsed:.3f}', flush=True)
    if any(not p.is_file() or sha256_file(p) != source_hashes[str(p.relative_to(ROOT))] for p in sources):
        print(f'FAILED: source changed during campaign; partial evidence retained in {evidence}', file=sys.stderr)
        return 1
    summary = {'study': evidence.name, 'total_runs': runs, 'exact_runs': exact, 'unknown_runs': unknown,
               'cross_depth_comparisons': comparisons}
    (evidence / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    # Include checkpoints, raw results and logs in the ledger, not just summaries.
    artifacts = {str(p.relative_to(evidence)): sha256_file(p) for p in sorted(evidence.rglob('*')) if p.is_file()}
    manifest = {'study': evidence.name, 'schema_version': 1, 'status': 'complete', 'runs': runs,
                'instances': len({digest for _, digest, _ in instances}), 'exact': exact, 'unknown': unknown,
                'config_sha256': artifacts['config.json'], 'artifact_sha256': artifacts, 'source_sha256': source_hashes}
    manifest_path = evidence / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    checksums = {**artifacts, 'manifest.json': sha256_file(manifest_path)}
    (evidence / 'SHA256SUMS').write_text(''.join(f'{v}  {k}\n' for k, v in sorted(checksums.items())))
    print(f'Complete: {exact}/{runs} exact, {unknown} unknown, {comparisons} cross-depth comparisons')
    return 0


if __name__ == '__main__':
    sys.exit(main())
