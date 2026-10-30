"""Empirical study runner for Tensor Network Contraction vs Combinatorial DPLL (Hypothesis H7)."""
import csv
from fractions import Fraction
import hashlib
import json
import multiprocessing as mp
import platform
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from time import perf_counter

from .core import Formula, oracle, solve
from .generate import generate
from .reliability import (
    NetworkGraph,
    build_grid_network,
    build_wheatstone_bridge,
    wheatstone_analytic,
)
from .tensor_contract import HAS_NUMPY, HAS_TORCH, tensor_solve
from .wmc import WeightedFormula, wmc_oracle, wmc_solve

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/tensor-study-001'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build_ladder_network(k, p=Fraction(9, 10)):
    """Build a k-step ladder reliability network (treewidth O(1))."""
    net = NetworkGraph()
    for i in range(k):
        net.add_edge(i, i + 1, p)              # top rail
        net.add_edge(k + 1 + i, k + 2 + i, p)  # bottom rail
        net.add_edge(i, k + 1 + i, p)          # rung
    net.add_edge(k, 2 * k + 1, p)              # final rung
    return net, 0, 2 * k + 1


def run_worker(conn, target_fn, args):
    try:
        res = target_fn(*args)
        conn.send(res)
    except Exception as exc:
        conn.send({'status': 'error', 'count': None, 'error': type(exc).__name__})
    finally:
        conn.close()


def isolated_call(target_fn, args, timeout=15.0):
    ctx = mp.get_context('spawn')
    recv, send = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=run_worker, args=(send, target_fn, args))
    proc.start()
    send.close()
    try:
        if recv.poll(timeout):
            try:
                res = recv.recv()
            except EOFError:
                res = {'status': 'error', 'count': None, 'error': 'worker_exited'}
        else:
            res = {'status': 'unknown', 'count': None, 'reason': 'hard_wall_limit'}
    finally:
        proc.join(0.1)
        if proc.is_alive():
            proc.terminate()
            proc.join(0.5)
    return res


def solve_wrapper(f, algo, weights=None, seconds=10.0, max_nodes=50000):
    if algo == 'tensor_einsum':
        return tensor_solve(f, weights=weights, backend='numpy', mode='einsum')
    elif algo == 'tensor_bucket':
        return tensor_solve(f, weights=weights, backend='numpy', mode='bucket_elimination')
    elif algo in ('combined', 'baseline'):
        if weights is not None or isinstance(f, WeightedFormula):
            wf = f if isinstance(f, WeightedFormula) else WeightedFormula(f.clauses, getattr(f, 'n_vars', f.n), weights)
            return wmc_solve(wf, algorithm=algo, seconds=seconds, max_nodes=max_nodes)
        else:
            return solve(f, algorithm=algo, seconds=seconds, max_nodes=max_nodes)
    else:
        raise ValueError(f"Unknown algorithm: {algo}")


def main():
    if not HAS_NUMPY:
        print("NumPy is required for tensor contraction study.")
        sys.exit(1)

    if OUT.exists():
        import shutil
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'instances').mkdir(parents=True, exist_ok=True)

    config = {
        'study': 'tensor-study-001',
        'hypothesis': 'H7',
        'device': 'cpu',
        'algorithms': ['tensor_einsum', 'tensor_bucket', 'combined', 'baseline'],
        'seconds_per_run': 10.0,
        'max_nodes': 50000,
        'preregistration': 'docs/TENSOR_CONTRACTION_PREREGISTRATION.md',
    }
    (OUT / 'config.json').write_text(json.dumps(config, indent=2, sort_keys=True) + '\n')

    # Hash sources
    source_files = [
        'sat_frontier/__init__.py',
        'sat_frontier/core.py',
        'sat_frontier/generate.py',
        'sat_frontier/reliability.py',
        'sat_frontier/tensor_contract.py',
        'sat_frontier/tensor_study.py',
        'sat_frontier/wmc.py',
        'pyproject.toml',
    ]
    source_hashes = {}
    for sf in source_files:
        p = ROOT / sf
        if p.exists():
            source_hashes[sf] = sha(p.read_bytes())

    meta = {
        'status': 'started',
        'schema_version': 1,
        'hardware': {
            'cpu': platform.processor() or 'unknown',
            'system': platform.system(),
            'python': sys.version,
        },
        'source_sha256': source_hashes,
        'config_sha256': sha((OUT / 'config.json').read_bytes()),
    }
    (OUT / 'manifest.json').write_text(json.dumps(meta, indent=2, sort_keys=True) + '\n')

    # Generate benchmark instances across 4 families
    instances = []

    # 1. Ladder networks (treewidth O(1))
    for k in [2, 3, 4]:
        net, s, t = build_ladder_network(k)
        wf = net.to_weighted_cnf(s, t)
        instances.append(('ladder', f'ladder_k{k}', wf, wf.weights, None))

    # 2. Grid networks (treewidth O(L))
    for rows, cols in [(2, 2), (2, 3)]:
        net, s, t = build_grid_network(rows, cols, p=Fraction(9, 10))
        wf = net.to_weighted_cnf(s, t)
        instances.append(('grid', f'grid_{rows}x{cols}', wf, wf.weights, None))

    # 3. Wheatstone bridge (analytic baseline)
    p_wheat = Fraction(9, 10)
    net_w, sw, tw = build_wheatstone_bridge(p=p_wheat)
    wf_w = net_w.to_weighted_cnf(sw, tw)
    expected_wheat = float(wheatstone_analytic(p_wheat))
    instances.append(('wheatstone', 'wheatstone_bridge', wf_w, wf_w.weights, expected_wheat))

    # 4. Random 3-SAT expanders (linear treewidth)
    for n in [8, 12, 14]:
        for ratio in [3.0, 4.2]:
            for seed in [101, 102]:
                f = generate('random', n=n, ratio=ratio, seed=seed)
                exp_count = oracle(f)
                instances.append(('random_expander', f'rand_n{n}_r{ratio}_s{seed}', f, None, exp_count))

    # Persist all instances to disk and index them
    for family, label, formula, weights, expected in instances:
        dimacs_data = formula.dimacs().encode('utf-8')
        inst_digest = sha(dimacs_data)
        inst_file = OUT / 'instances' / f'{inst_digest}.cnf'
        if not inst_file.exists():
            inst_file.write_bytes(dimacs_data)

    algorithms = config['algorithms']
    rows = []

    with (OUT / 'runs.jsonl').open('w') as log:
        for family, label, formula, weights, expected in instances:
            n_vars = getattr(formula, 'n_vars', getattr(formula, 'n', 0))
            n_clauses = len(formula.clauses)
            dimacs_data = formula.dimacs().encode('utf-8')
            inst_digest = sha(dimacs_data)

            for algo in algorithms:
                r = isolated_call(solve_wrapper, (formula, algo, weights, config['seconds_per_run'], config['max_nodes']))

                val = r.get('count')
                if val is None and 'weight_float' in r:
                    val = r['weight_float']
                elif val is None and 'weight_fraction' in r and r['weight_fraction'] is not None:
                    val = float(Fraction(r['weight_fraction']))

                is_exact = (r.get('status') == 'exact')

                row = {
                    'family': family,
                    'instance': label,
                    'instance_sha256': inst_digest,
                    'n_vars': n_vars,
                    'n_clauses': n_clauses,
                    'algorithm': algo,
                    'status': r.get('status', 'unknown'),
                    'count': r.get('count') if is_exact else None,
                    'weight_float': r.get('weight_float') if is_exact else None,
                    'elapsed_seconds': r.get('elapsed_seconds', 0.0),
                    'nodes': r.get('nodes', 0),
                    'expected': expected,
                }

                # Validation against oracle / analytic
                if is_exact and expected is not None:
                    if isinstance(expected, int):
                        if r.get('count') != expected:
                            raise RuntimeError(f"Oracle mismatch on {label} ({algo}): {expected} vs {r.get('count')}")
                        row['validation'] = 'oracle_pass'
                    elif isinstance(expected, float):
                        if abs(val - expected) > 1e-6:
                            raise RuntimeError(f"Analytic mismatch on {label} ({algo}): {expected} vs {val}")
                        row['validation'] = 'oracle_pass'
                elif is_exact:
                    row['validation'] = 'exact_unverified'
                else:
                    row['validation'] = 'incomplete'

                log.write(json.dumps(row, sort_keys=True) + '\n')
                log.flush()
                rows.append(row)

    # Write CSV
    fields = sorted(set().union(*(r.keys() for r in rows)))
    with (OUT / 'runs.csv').open('w', newline='') as handle:
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
                'median_ms': statistics.median(r['elapsed_seconds'] * 1000 for r in exacts) if exacts else None,
                'mean_ms': statistics.mean(r['elapsed_seconds'] * 1000 for r in exacts) if exacts else None,
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
