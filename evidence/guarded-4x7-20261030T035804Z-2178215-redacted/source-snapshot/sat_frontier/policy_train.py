"""One-shot preregistered train-only campaign; never evaluates holdout."""
import csv
import hashlib
import json
import multiprocessing as mp
import os
import platform
import random
import shutil
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter

from .core import oracle, solve, validate_policy
from .generate import generate

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / 'configs/policy-train-v02.json'
PREREG = ROOT / 'docs/POLICY_PREREGISTRATION.md'
OUT = ROOT / 'evidence/policy-train-v02'
CONFIG_SHA256 = '73874f4dbb96e3b177169ae075f4484dabb05c5f947c12dbe7059482cabd6eed'
PREREG_SHA256 = '90c53104bd660e3f43b158bb5a7dff3a6109e2d07ecc655a13cf47a87e0a8b62'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def worker(conn, f, policy, cfg):
    try:
        result = solve(f, 'combined', cfg['seconds'], cfg['max_nodes'], cfg['cache_limit'], branch_policy=policy)
        if sys.platform.startswith('linux'):
            import resource
            result['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        else:
            result['peak_rss_kib'] = None
        conn.send(result)
    except Exception as exc:
        conn.send({'status': 'error', 'count': None, 'error': type(exc).__name__})
    finally:
        conn.close()


def isolated(f, policy, cfg):
    ctx = mp.get_context('spawn')
    recv, send = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=worker, args=(send, f, policy, cfg))
    start = perf_counter()
    proc.start()
    send.close()
    try:
        if recv.poll(cfg['seconds'] + 2):
            try:
                result = recv.recv()
            except EOFError:
                result = {'status': 'error', 'count': None, 'error': 'worker exited'}
        else:
            result = {'status': 'unknown', 'count': None, 'reason': 'hard_wall_limit'}
    finally:
        proc.join(0.1)
        if proc.is_alive():
            proc.terminate()
            proc.join()
        recv.close()
    result['wall_seconds'] = perf_counter() - start
    return result


def bootstrap(values, seed, samples, statistic):
    if not values:
        return None
    rng = random.Random(seed)
    distribution = sorted(statistic([rng.choice(values) for _ in values]) for _ in range(samples))
    return [distribution[int(.025 * (samples - 1))], distribution[int(.975 * (samples - 1))]]


def summarize(rows, cfg):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row['family'], row['seed'], row['candidate'])].append(row)
    result = {}
    for family in cfg['families']:
        result[family] = {}
        for candidate in ['control'] + list(cfg['candidates']):
            pairs = [(grouped[(family, seed, candidate)], grouped[(family, seed, 'control')])
                     for seed in cfg['seeds']]
            own = [r for a, _ in pairs for r in a]
            differences = [sum(r['status'] == 'exact' for r in a) / len(a)
                           - sum(r['status'] == 'exact' for r in b) / len(b) for a, b in pairs]
            ratios = [statistics.mean(r['elapsed_seconds'] for r in b) /
                      statistics.mean(r['elapsed_seconds'] for r in a)
                      for a, b in pairs if all(r['status'] == 'exact' for r in a + b)]
            exact_times = [r['elapsed_seconds'] for r in own if r['status'] == 'exact']
            walls = [r['wall_seconds'] for r in own]
            rss = [r['peak_rss_kib'] for r in own if r.get('peak_rss_kib') is not None]
            result[family][candidate] = {
                'instances': len(pairs), 'runs': len(own),
                'exact_fraction': sum(r['status'] == 'exact' for r in own) / len(own),
                'unknown_fraction': sum(r['status'] == 'unknown' for r in own) / len(own),
                'error_fraction': sum(r['status'] == 'error' for r in own) / len(own),
                'reasons': dict(Counter(r.get('reason') for r in own if r.get('reason'))),
                'paired_solved_difference': statistics.mean(differences),
                'paired_solved_difference_bootstrap_95': bootstrap(differences, cfg['bootstrap_seed'], cfg['bootstrap_samples'], statistics.mean),
                'solved_regression_instances': sum(d < 0 for d in differences),
                'solved_improvement_instances': sum(d > 0 for d in differences),
                'conditional_exact_pair_instances': len(ratios),
                'conditional_median_speed_ratio_control_over_candidate': statistics.median(ratios) if ratios else None,
                'conditional_median_solver_time_ratio_candidate_over_control': statistics.median([1 / x for x in ratios]) if ratios else None,
                'conditional_timing_regression_instances': sum(x < 1 for x in ratios),
                'conditional_speed_ratio_bootstrap_95': bootstrap(ratios, cfg['bootstrap_seed'], cfg['bootstrap_samples'], statistics.median),
                'median_solver_seconds_exact_only': statistics.median(exact_times) if exact_times else None,
                'median_wall_seconds_all': statistics.median(walls),
                'median_nodes_all': statistics.median(r['nodes'] for r in own if 'nodes' in r),
                'peak_worker_rss_kib_max': max(rss) if rss else None,
            }
    return result


def main():
    raw_config = CONFIG.read_bytes()
    if sha(raw_config) != CONFIG_SHA256 or sha(PREREG.read_bytes()) != PREREG_SHA256:
        raise ValueError('configuration or preregistration differs from the frozen train protocol')
    cfg = json.loads(raw_config)
    if cfg['split'] != 'train' or len(cfg['candidates']) > 12:
        raise ValueError('only the finite train split is allowed')
    for p in cfg['candidates'].values():
        validate_policy(p)
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / 'instances').mkdir()
    (OUT / 'config.json').write_bytes(raw_config)
    source = [ROOT / 'sat_frontier/core.py', ROOT / 'sat_frontier/generate.py', Path(__file__), PREREG, CONFIG]
    source_hashes = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in source}
    git_path = shutil.which('git')
    if git_path is None:
        raise RuntimeError('git required to capture source revision')
    git = subprocess.run([git_path, 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run([git_path, 'status', '--short'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    meta = {'status': 'running', 'split': 'train', 'source_sha256': source_hashes,
            'git_revision': git, 'git_status_before': dirty, 'python': sys.version,
            'platform': platform.platform(), 'load_at_start': list(os.getloadavg()) if hasattr(os, 'getloadavg') else None,
            'cpu_affinity': sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else None,
            'execution': 'sequential spawned CPU workers; no warm-up; GPU not used',
            'rss': 'Linux ru_maxrss KiB per worker; null if unavailable',
            'timing': 'elapsed_seconds excludes spawn; wall_seconds includes spawn and join'}
    (OUT / 'manifest.json').write_text(json.dumps(meta, indent=2, sort_keys=True) + '\n')
    policies = {'control': None, **cfg['candidates']}
    rows = []
    seen = set()
    with (OUT / 'runs.jsonl').open('x') as log:
        for fi, family in enumerate(cfg['families']):
            for si, seed in enumerate(cfg['seeds']):
                f = generate(family, cfg['n'], cfg['ratio'], seed)
                data = f.dimacs().encode()
                instance = sha(data)
                if instance in seen:
                    raise ValueError('duplicate instance; preserved partial evidence')
                seen.add(instance)
                (OUT / 'instances' / (instance + '.cnf')).write_bytes(data)
                expected = oracle(f)
                for repeat in range(cfg['repeats']):
                    names = list(policies)
                    offset = (fi + si + repeat) % len(names)
                    for name in names[offset:] + names[:offset]:
                        r = isolated(f, policies[name], cfg)
                        row = {'family': family, 'seed': seed, 'instance_sha256': instance,
                               'repeat': repeat, 'candidate': name, 'oracle_count': expected, **r}
                        row['validation'] = ('oracle_pass' if r['count'] == expected else 'oracle_fail') if r['status'] == 'exact' else 'not_exact'
                        log.write(json.dumps(row, sort_keys=True) + '\n')
                        log.flush()
                        rows.append(row)
                        if row['validation'] == 'oracle_fail' or row['status'] == 'error':
                            raise RuntimeError('correctness or worker failure; raw evidence preserved')
    fields = sorted(set().union(*(r.keys() for r in rows)))
    with (OUT / 'runs.csv').open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    ranking = sorted(cfg['candidates'], key=lambda name: (
        -sum(r['status'] == 'exact' for r in rows if r['candidate'] == name),
        sum(r.get('nodes', cfg['max_nodes']) for r in rows if r['candidate'] == name), name))
    chosen = ranking[0]
    frozen = {'candidate': chosen, 'weights': cfg['candidates'][chosen], 'ranking': ranking,
              'selection_rule': 'most exact runs, then least total nodes including unknown, then ID',
              'source_sha256': source_hashes, 'train_only': True, 'holdout_consumed': False}
    (OUT / 'winner.json').write_text(json.dumps(frozen, indent=2, sort_keys=True) + '\n')
    (OUT / 'summary.json').write_text(json.dumps(summarize(rows, cfg), indent=2, sort_keys=True) + '\n')
    meta.update(status='complete', runs=len(rows), instances=len(seen), winner=chosen,
                exact=sum(r['status'] == 'exact' for r in rows),
                artifact_sha256={str(p.relative_to(OUT)): sha(p.read_bytes()) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'manifest.json'})
    (OUT / 'manifest.json').write_text(json.dumps(meta, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'runs': len(rows), 'exact': meta['exact'], 'winner': chosen, 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
