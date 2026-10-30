"""Calibrated scaling benchmark across variable sizes (n=12 to 24) beyond small oracle limits."""
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
OUT = ROOT / 'evidence/scaling-benchmark-001'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run_worker(conn, f, algo, seconds, max_nodes):
    try:
        if algo == 'separator':
            res = solve_separator(f, seconds=seconds, max_nodes=max_nodes)
        else:
            res = solve(f, algo, seconds=seconds, max_nodes=max_nodes)
        conn.send(res)
    except Exception as exc:
        conn.send({'status': 'error', 'count': None, 'error': type(exc).__name__})
    finally:
        conn.close()


def isolated_run(f, algo, seconds=5.0, max_nodes=100000):
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

    sizes = [12, 14, 16, 18, 20]
    families = ['random', 'planted', 'disconnected', 'barbell']
    algorithms = ['baseline', 'memo', 'components', 'combined', 'separator']
    seeds = [701, 702, 703]  # 3 seeds per (size, family)
    seconds = 3.0
    max_nodes = 50000

    cfg = {
        'schema_version': 1,
        'sizes': sizes,
        'families': families,
        'algorithms': algorithms,
        'seeds': seeds,
        'seconds': seconds,
        'max_nodes': max_nodes,
    }
    (OUT / 'config.json').write_text(json.dumps(cfg, indent=2) + '\n')

    source = [ROOT / 'sat_frontier/core.py', ROOT / 'sat_frontier/separator.py', Path(__file__)]
    source_hashes = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in source}

    git_path = shutil.which('git')
    git_rev = subprocess.run([git_path, 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip() if git_path else None

    meta = {
        'status': 'running',
        'study': 'calibrated_scaling_benchmark',
        'source_sha256': source_hashes,
        'git_revision': git_rev,
        'platform': platform.platform(),
        'python': sys.version,
    }
    (OUT / 'manifest.json').write_text(json.dumps(meta, indent=2) + '\n')

    # Generate all test instances
    instances = {}
    for n in sizes:
        for family in families:
            for seed in seeds:
                if family == 'barbell':
                    # n_cluster = (n - 1) // 2
                    n_cluster = max(2, (n - 1) // 2)
                    bridge_len = n - 2 * n_cluster
                    f = generate_barbell(n_cluster, bridge_len, seed=seed)
                elif family == 'disconnected':
                    f = generate('disconnected', n, 3.5, seed=seed)
                elif family == 'planted':
                    f = generate('planted', n, 3.5, seed=seed)
                elif family == 'random':
                    f = generate('random', n, 3.5, seed=seed)

                data = f.dimacs().encode()
                digest = sha(data)
                (OUT / 'instances' / (digest + '.cnf')).write_bytes(data)
                # Compute oracle count if n <= 18
                oracle_count = oracle(f) if n <= 18 else None
                instances[(n, family, seed)] = (f, digest, oracle_count)

    rows = []
    with (OUT / 'runs.jsonl').open('x') as log:
        for n in sizes:
            for family in families:
                for seed in seeds:
                    f, digest, expected = instances[(n, family, seed)]
                    for algo in algorithms:
                        r = isolated_run(f, algo, seconds=seconds, max_nodes=max_nodes)
                        row = {
                            **r,
                            'n': n,
                            'family': family,
                            'seed': seed,
                            'instance_sha256': digest,
                            'algorithm': algo,
                            'solver_algorithm': r.get('algorithm'),
                            'oracle_count': expected,
                        }
                        if r['status'] == 'exact' and expected is not None:
                            if r['count'] != expected:
                                raise RuntimeError(f"Oracle mismatch on n={n}: {expected} vs {r['count']}")
                            row['validation'] = 'oracle_pass'
                        elif r['status'] == 'exact':
                            row['validation'] = 'exact_unverified_by_oracle'
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

    # Compute per-size and per-algorithm summary
    summary = {}
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r['n'], r['algorithm'])].append(r)

    for n in sizes:
        summary[str(n)] = {}
        for algo in algorithms:
            items = grouped[(n, algo)]
            exacts = [r for r in items if r['status'] == 'exact']
            summary[str(n)][algo] = {
                'total_runs': len(items),
                'exact_runs': len(exacts),
                'exact_fraction': len(exacts) / len(items),
                'median_nodes': statistics.median(r['nodes'] for r in exacts) if exacts else None,
                'mean_nodes': statistics.mean(r['nodes'] for r in exacts) if exacts else None,
                'median_cache_hits': statistics.median(r.get('cache_hits', 0) for r in exacts) if exacts else None,
                'median_component_splits': statistics.median(r.get('component_splits', 0) for r in exacts) if exacts else None,
                'median_solver_ms': statistics.median(r['elapsed_seconds'] * 1000 for r in exacts) if exacts else None,
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
        unknown=sum(r['status'] == 'unknown' for r in rows),
        artifact_sha256=artifact_hashes,
    )
    (OUT / 'manifest.json').write_text(json.dumps(meta, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'complete', 'runs': len(rows), 'exact': meta['exact'], 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
