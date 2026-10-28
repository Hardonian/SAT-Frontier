"""Empirical evaluation of Graph Separator Branching (Hypothesis H4)."""
import csv
import hashlib
import json
import multiprocessing as mp
import platform
import shutil
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from time import perf_counter

from .core import oracle, solve
from .generate import generate
from .separator import generate_barbell, solve_separator

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/separator-study-001'
PREREG = ROOT / 'docs/SEPARATOR_PREREGISTRATION.md'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run_worker(conn, f, algo, seconds, max_nodes):
    try:
        if algo == 'control':
            res = solve(f, 'combined', seconds=seconds, max_nodes=max_nodes)
        elif algo == 'separator':
            res = solve_separator(f, seconds=seconds, max_nodes=max_nodes)
        else:
            raise ValueError(f'unknown algorithm {algo}')
        conn.send(res)
    except Exception as exc:
        conn.send({'status': 'error', 'count': None, 'error': type(exc).__name__})
    finally:
        conn.close()


def isolated_run(f, algo, seconds=2.0, max_nodes=50000):
    ctx = mp.get_context('spawn')
    recv, send = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=run_worker, args=(send, f, algo, seconds, max_nodes))
    start = perf_counter()
    proc.start()
    send.close()
    try:
        if recv.poll(seconds + 2.0):
            try:
                res = recv.recv()
            except EOFError:
                res = {'status': 'error', 'count': None, 'error': 'worker exited'}
        else:
            res = {'status': 'unknown', 'count': None, 'reason': 'hard_wall_limit'}
    finally:
        proc.join(0.1)
        if proc.is_alive():
            proc.terminate()
            proc.join()
        recv.close()
    res['wall_seconds'] = perf_counter() - start
    return res


def main():
    if OUT.exists():
        raise FileExistsError(f'{OUT} already exists')
    OUT.mkdir(parents=True)
    (OUT / 'instances').mkdir()

    families = ['barbell', 'disconnected', 'planted', 'random']
    seeds = list(range(501, 511))  # 10 seeds per family = 40 instances
    repeats = 2
    seconds = 2.0
    max_nodes = 50000

    cfg = {
        'schema_version': 1,
        'families': families,
        'seeds': seeds,
        'repeats': repeats,
        'seconds': seconds,
        'max_nodes': max_nodes,
        'algorithms': ['control', 'separator'],
    }
    (OUT / 'config.json').write_text(json.dumps(cfg, indent=2) + '\n')

    source = [
        ROOT / 'sat_frontier/core.py',
        ROOT / 'sat_frontier/separator.py',
        Path(__file__),
        PREREG,
    ]
    source_hashes = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in source}

    git_path = shutil.which('git')
    git_rev = subprocess.run([git_path, 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip() if git_path else None

    meta = {
        'status': 'running',
        'study': 'separator_hypothesis_h4',
        'source_sha256': source_hashes,
        'git_revision': git_rev,
        'platform': platform.platform(),
        'python': sys.version,
    }
    (OUT / 'manifest.json').write_text(json.dumps(meta, indent=2) + '\n')

    instances = {}
    for family in families:
        for seed in seeds:
            if family == 'barbell':
                # n_cluster=5, bridge_len=1 -> 11 variables
                f = generate_barbell(5, 1, seed=seed)
            elif family == 'disconnected':
                f = generate('disconnected', 12, 4, seed=seed)
            elif family == 'planted':
                f = generate('planted', 12, 4, seed=seed)
            elif family == 'random':
                f = generate('random', 12, 4, seed=seed)
            data = f.dimacs().encode()
            digest = sha(data)
            (OUT / 'instances' / (digest + '.cnf')).write_bytes(data)
            instances[(family, seed)] = (f, digest, oracle(f))

    rows = []
    with (OUT / 'runs.jsonl').open('x') as log:
        for family in families:
            for seed in seeds:
                f, digest, expected_count = instances[(family, seed)]
                for repeat in range(repeats):
                    algos = ['control', 'separator']
                    if (seed + repeat) % 2 == 1:
                        algos = ['separator', 'control']
                    for algo in algos:
                        r = isolated_run(f, algo, seconds=seconds, max_nodes=max_nodes)
                        row = {
                            **r,
                            'family': family,
                            'seed': seed,
                            'instance_sha256': digest,
                            'repeat': repeat,
                            'algorithm': algo,
                            'solver_algorithm': r.get('algorithm'),
                            'oracle_count': expected_count,
                        }
                        if r['status'] == 'exact':
                            if r['count'] != expected_count:
                                raise RuntimeError(f"Oracle count mismatch: expected {expected_count}, got {r['count']}")
                            row['validation'] = 'oracle_pass'
                        else:
                            row['validation'] = 'not_exact'

                        log.write(json.dumps(row, sort_keys=True) + '\n')
                        log.flush()
                        rows.append(row)

    fields = sorted(set().union(*(r.keys() for r in rows)))
    with (OUT / 'runs.csv').open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    # Compute summary comparisons
    summary = {}
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r['family'], r['algorithm'])].append(r)

    for family in families:
        summary[family] = {}
        for algo in ['control', 'separator']:
            items = grouped[(family, algo)]
            exacts = [r for r in items if r['status'] == 'exact']
            summary[family][algo] = {
                'total_runs': len(items),
                'exact_runs': len(exacts),
                'exact_fraction': len(exacts) / len(items),
                'median_nodes': statistics.median(r['nodes'] for r in exacts) if exacts else None,
                'mean_nodes': statistics.mean(r['nodes'] for r in exacts) if exacts else None,
                'median_component_splits': statistics.median(r['component_splits'] for r in exacts) if exacts else None,
                'median_solver_seconds': statistics.median(r['elapsed_seconds'] for r in exacts) if exacts else None,
            }

        # Paired comparisons
        sep_runs = grouped[(family, 'separator')]
        ctrl_runs = grouped[(family, 'control')]
        node_diffs = [
            s_r['nodes'] - c_r['nodes']
            for s_r, c_r in zip(sep_runs, ctrl_runs)
            if s_r['status'] == 'exact' and c_r['status'] == 'exact'
        ]
        time_ratios = [
            s_r['elapsed_seconds'] / c_r['elapsed_seconds']
            for s_r, c_r in zip(sep_runs, ctrl_runs)
            if s_r['status'] == 'exact' and c_r['status'] == 'exact' and c_r['elapsed_seconds'] > 0
        ]
        summary[family]['paired'] = {
            'mean_node_reduction': -statistics.mean(node_diffs) if node_diffs else 0.0,
            'median_time_overhead_ratio': statistics.median(time_ratios) if time_ratios else 1.0,
            'node_reduced_pairs': sum(d < 0 for d in node_diffs),
            'node_equal_pairs': sum(d == 0 for d in node_diffs),
            'node_increased_pairs': sum(d > 0 for d in node_diffs),
        }

    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')

    artifact_hashes = {
        p.relative_to(OUT).as_posix(): sha(p.read_bytes())
        for p in sorted(OUT.rglob('*'))
        if p.is_file() and p.name != 'manifest.json'
    }
    meta.update(
        status='complete',
        runs=len(rows),
        instances=len(instances),
        exact=sum(r['status'] == 'exact' for r in rows),
        artifact_sha256=artifact_hashes,
    )
    (OUT / 'manifest.json').write_text(json.dumps(meta, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'complete', 'runs': len(rows), 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()

