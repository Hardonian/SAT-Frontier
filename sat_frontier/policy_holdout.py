"""One-shot preregistered holdout evaluation campaign; fail-closed guards."""
import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .core import oracle, validate_policy
from .generate import generate
from .holdout_guard import (
    check_overlap,
    prior_instance_hashes,
    reserve_once,
    verify_train_freeze,
)
from .policy_train import isolated, sha, summarize

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / 'configs/policy-holdout-v02.json'
PREREG = ROOT / 'docs/POLICY_HOLDOUT_PREREGISTRATION.md'
RESERVATION = ROOT / 'evidence/policy-holdout-v02-consumed'
OUT = ROOT / 'evidence/policy-holdout-v02'
CONFIG_SHA256 = 'fbe1a80bbbd26b03a66318ed6edcf73cfd7a7eb153a96da5ebf6e202b69ddcde'
PREREG_SHA256 = 'fa5ac9ca2d135d85779c6adbc7950718780c4070b50447eddbe644a3b8a0a14d'


def main():
    # Guard 1: Verify train winner and frozen source tree
    winner = verify_train_freeze(ROOT)
    chosen_candidate = winner['candidate']
    chosen_weights = winner['weights']

    # Guard 2: Verify holdout configuration and preregistration bytes
    raw_config = CONFIG.read_bytes()
    if sha(raw_config) != CONFIG_SHA256 or sha(PREREG.read_bytes()) != PREREG_SHA256:
        raise ValueError('holdout configuration or preregistration differs from frozen protocol')
    cfg = json.loads(raw_config)
    if cfg['split'] != 'holdout':
        raise ValueError('only split="holdout" is permitted')
    if chosen_candidate not in cfg['candidates']:
        raise ValueError(f'frozen train winner {chosen_candidate} not in candidates')
    if cfg['candidates'][chosen_candidate] != chosen_weights:
        raise ValueError('candidate weights do not match frozen train winner')
    for p in cfg['candidates'].values():
        validate_policy(p)

    # Guard 3: Atomic one-shot reservation
    reserve_once(RESERVATION, PREREG_SHA256)

    # Guard 4: Collect prior instances and verify zero content overlap
    prior = prior_instance_hashes(ROOT / 'evidence')

    # Guard 5: Fail-closed output directory creation
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / 'instances').mkdir()
    (OUT / 'config.json').write_bytes(raw_config)

    source = [
        ROOT / 'sat_frontier/core.py',
        ROOT / 'sat_frontier/generate.py',
        ROOT / 'sat_frontier/policy_train.py',
        ROOT / 'sat_frontier/holdout_guard.py',
        Path(__file__),
        PREREG,
        CONFIG,
    ]
    source_hashes = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in source}

    git_path = shutil.which('git')
    git_rev = None
    git_dirty = []
    if git_path:
        git_rev = subprocess.run([git_path, 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        git_dirty = subprocess.run([git_path, 'status', '--short'], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()

    meta = {
        'status': 'running',
        'split': 'holdout',
        'source_sha256': source_hashes,
        'git_revision': git_rev,
        'git_status_before': git_dirty,
        'python': sys.version,
        'platform': platform.platform(),
        'execution': 'sequential spawned CPU workers; no warm-up; GPU not used',
        'timing': 'elapsed_seconds excludes spawn; wall_seconds includes spawn and join',
    }
    (OUT / 'manifest.json').write_text(json.dumps(meta, indent=2, sort_keys=True) + '\n')

    # Pre-generate and check all instances for duplicates and overlap
    generated_instances = {}
    instance_bytes_list = []
    for family in cfg['families']:
        for seed in cfg['seeds']:
            f = generate(family, cfg['n'], cfg['ratio'], seed)
            data = f.dimacs().encode()
            digest = sha(data)
            generated_instances[(family, seed)] = (f, data, digest)
            instance_bytes_list.append(data)

    # Verifies zero overlap with prior evidence and uniqueness among holdout instances
    check_overlap(instance_bytes_list, prior)

    policies = {'control': None, **cfg['candidates']}
    rows = []
    seen = set()

    with (OUT / 'runs.jsonl').open('x') as log:
        for fi, family in enumerate(cfg['families']):
            for si, seed in enumerate(cfg['seeds']):
                f, data, instance = generated_instances[(family, seed)]
                if instance in seen:
                    raise ValueError('duplicate instance encountered')
                seen.add(instance)
                (OUT / 'instances' / (instance + '.cnf')).write_bytes(data)
                expected = oracle(f)

                for repeat in range(cfg['repeats']):
                    names = list(policies)
                    offset = (fi + si + repeat) % len(names)
                    for name in names[offset:] + names[:offset]:
                        r = isolated(f, policies[name], cfg)
                        row = {
                            'family': family,
                            'seed': seed,
                            'instance_sha256': instance,
                            'repeat': repeat,
                            'candidate': name,
                            'oracle_count': expected,
                            **r,
                        }
                        row['validation'] = (
                            ('oracle_pass' if r['count'] == expected else 'oracle_fail')
                            if r['status'] == 'exact'
                            else 'not_exact'
                        )
                        log.write(json.dumps(row, sort_keys=True) + '\n')
                        log.flush()
                        rows.append(row)
                        if row['validation'] == 'oracle_fail' or row['status'] == 'error':
                            raise RuntimeError(f'correctness failure in holdout run: {row}')

    fields = sorted(set().union(*(r.keys() for r in rows)))
    with (OUT / 'runs.csv').open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows, cfg)
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')

    artifact_hashes = {
        p.relative_to(OUT).as_posix(): sha(p.read_bytes())
        for p in sorted(OUT.rglob('*'))
        if p.is_file() and p.name != 'manifest.json'
    }
    meta.update(
        status='complete',
        runs=len(rows),
        instances=len(seen),
        exact=sum(r['status'] == 'exact' for r in rows),
        unknown=sum(r['status'] == 'unknown' for r in rows),
        artifact_sha256=artifact_hashes,
    )
    (OUT / 'manifest.json').write_text(json.dumps(meta, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'runs': len(rows), 'exact': meta['exact'], 'unknown': meta['unknown'], 'evidence': str(OUT)}))


if __name__ == '__main__':
    main()
