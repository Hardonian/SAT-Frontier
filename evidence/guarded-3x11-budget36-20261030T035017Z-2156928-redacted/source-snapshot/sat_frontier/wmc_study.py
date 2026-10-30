"""Empirical study runner for Weighted Model Counting and Network Reliability (Milestone M5)."""
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
from fractions import Fraction
from pathlib import Path
from time import perf_counter

from .reliability import (
    build_barbell_network,
    build_grid_network,
    build_wheatstone_bridge,
    wheatstone_analytic,
)
from .wmc import WeightedFormula, wmc_oracle, wmc_solve

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/wmc-reliability-001'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run_worker(conn, wf, algo, seconds, max_nodes):
    try:
        res = wmc_solve(wf, algorithm=algo, seconds=seconds, max_nodes=max_nodes)
        conn.send(res)
    except Exception as exc:
        conn.send({'status': 'error', 'weight_fraction': None, 'error': type(exc).__name__})
    finally:
        conn.close()


def isolated_run(wf, algo, seconds=10.0, max_nodes=100000):
    ctx = mp.get_context('spawn')
    recv, send = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=run_worker, args=(send, wf, algo, seconds, max_nodes))
    start = perf_counter()
    proc.start()
    send.close()
    try:
        if recv.poll(seconds + 2.0):
            try:
                res = recv.recv()
            except EOFError:
                res = {'status': 'error', 'weight_fraction': None, 'error': 'worker_exited'}
        else:
            res = {'status': 'unknown', 'weight_fraction': None, 'reason': 'hard_wall_limit'}
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
        raise FileExistsError(f"{OUT} already exists")
    OUT.mkdir(parents=True)
    (OUT / 'instances').mkdir()

    seconds = 5.0
    max_nodes = 50000

    cfg = {
        'schema_version': 1,
        'study': 'wmc_network_reliability_m5',
        'seconds': seconds,
        'max_nodes': max_nodes,
        'algorithms': ['baseline_wmc', 'memo_wmc', 'components_wmc', 'combined_wmc', 'separator_wmc'],
    }
    (OUT / 'config.json').write_text(json.dumps(cfg, indent=2) + '\n')

    source = [
        ROOT / 'sat_frontier/wmc.py',
        ROOT / 'sat_frontier/reliability.py',
        Path(__file__),
    ]
    source_hashes = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in source}

    git_path = shutil.which('git')
    git_rev = subprocess.run([git_path, 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip() if git_path else None

    meta = {
        'status': 'running',
        'study': 'wmc_network_reliability_m5',
        'source_sha256': source_hashes,
        'git_revision': git_rev,
        'platform': platform.platform(),
        'python': sys.version,
    }
    (OUT / 'manifest.json').write_text(json.dumps(meta, indent=2) + '\n')

    # Benchmark Instances
    instance_specs = []

    # 1. Wheatstone bridges
    for p in [Fraction(1, 2), Fraction(7, 10), Fraction(9, 10)]:
        net, s, t = build_wheatstone_bridge(p=p)
        wf = net.to_weighted_cnf(s, t)
        instance_specs.append(('wheatstone', f"wheatstone_p{p}", wf, wheatstone_analytic(p)))

    # 2. Barbell networks (modular and flat)
    for k in [3, 4, 5]:
        net, s, t = build_barbell_network(cluster_size=k, p_cluster=Fraction(9, 10), p_bridge=Fraction(8, 10))
        wf_mod = net.to_weighted_cnf(s, t, modular=True)
        wf_flat = net.to_weighted_cnf(s, t, modular=False)

        oracle_val = wmc_oracle(wf_mod) if wf_mod.n_vars <= 16 else None
        instance_specs.append(('barbell_modular', f"barbell_k{k}_mod", wf_mod, oracle_val))
        instance_specs.append(('barbell_flat', f"barbell_k{k}_flat", wf_flat, oracle_val))

    # 3. Grid networks
    for rows, cols in [(2, 3), (2, 4), (3, 3)]:
        for p in [Fraction(8, 10), Fraction(9, 10)]:
            net, s, t = build_grid_network(rows=rows, cols=cols, p=p)
            wf = net.to_weighted_cnf(s, t)
            oracle_val = wmc_oracle(wf) if wf.n_vars <= 16 else None
            instance_specs.append(('grid', f"grid_{rows}x{cols}_p{p}", wf, oracle_val))

    instances = {}
    for family, label, wf, expected in instance_specs:
        dimacs_data = wf.dimacs().encode()
        digest = sha(dimacs_data)
        (OUT / 'instances' / f"{digest}.cnf").write_bytes(dimacs_data)
        instances[label] = (wf, digest, family, expected)

    rows = []
    algorithms = cfg['algorithms']

    with (OUT / 'runs.jsonl').open('x') as log:
        for label, (wf, digest, family, expected) in instances.items():
            for algo in algorithms:
                r = isolated_run(wf, algo, seconds=seconds, max_nodes=max_nodes)
                row = {
                    **r,
                    'instance_label': label,
                    'family': family,
                    'instance_sha256': digest,
                    'n_vars': wf.n_vars,
                    'n_clauses': len(wf.clauses),
                    'algorithm': algo,
                    'expected_fraction': str(expected) if expected is not None else None,
                }
                if r['status'] == 'exact' and expected is not None:
                    if Fraction(r['weight_fraction']) != expected:
                        raise RuntimeError(f"Oracle mismatch on {label}: {expected} vs {r['weight_fraction']}")
                    row['validation'] = 'oracle_pass'
                elif r['status'] == 'exact':
                    row['validation'] = 'exact_unverified'
                else:
                    row['validation'] = 'incomplete'

                log.write(json.dumps(row, sort_keys=True) + '\n')
                log.flush()
                rows.append(row)

    fields = sorted(set().union(*(r.keys() for r in rows)))
    with (OUT / 'runs.csv').open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    # Compute Summary
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r['family'], r['algorithm'])].append(r)

    families = sorted(set(r['family'] for r in rows))
    summary = {}
    for fam in families:
        summary[fam] = {}
        for algo in algorithms:
            items = grouped[(fam, algo)]
            exacts = [r for r in items if r['status'] == 'exact']
            summary[fam][algo] = {
                'total_runs': len(items),
                'exact_runs': len(exacts),
                'median_nodes': statistics.median(r['nodes'] for r in exacts) if exacts else None,
                'mean_nodes': statistics.mean(r['nodes'] for r in exacts) if exacts else None,
                'median_splits': statistics.median(r.get('component_splits', 0) for r in exacts) if exacts else None,
                'median_cache_hits': statistics.median(r.get('cache_hits', 0) for r in exacts) if exacts else None,
                'median_ms': statistics.median(r['elapsed_seconds'] * 1000 for r in exacts) if exacts else None,
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
    print(json.dumps({'status': 'complete', 'runs': len(rows), 'exact': meta['exact'], 'instances': len(instances)}))


if __name__ == '__main__':
    main()
