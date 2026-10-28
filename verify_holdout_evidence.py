"""Check the committed policy holdout campaign's integrity and independent oracle counts."""
import json
import sys
from pathlib import Path
from sat_frontier.core import oracle, parse_dimacs
from sat_frontier.generate import generate
from sat_frontier.policy_train import ROOT, sha, summarize


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(run):
    run = Path(run).resolve()
    manifest = json.loads((run / 'manifest.json').read_text())
    cfg = json.loads((run / 'config.json').read_text())

    require(manifest['status'] == 'complete' and manifest['split'] == 'holdout', 'not a completed holdout run')

    for name, digest in manifest['source_sha256'].items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT) and sha(path.read_bytes()) == digest, 'source mismatch: ' + name)

    actual_paths = {p.relative_to(run).as_posix() for p in run.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    require(actual_paths == set(manifest['artifact_sha256']), 'artifact inventory mismatch')

    for name, digest in manifest['artifact_sha256'].items():
        path = (run / name).resolve()
        require(path.is_relative_to(run) and sha(path.read_bytes()) == digest, 'artifact mismatch: ' + name)

    rows = [json.loads(line) for line in (run / 'runs.jsonl').read_text().splitlines()]
    expected_keys = {
        (f, seed, repeat, name)
        for f in cfg['families']
        for seed in cfg['seeds']
        for repeat in range(cfg['repeats'])
        for name in ['control'] + list(cfg['candidates'])
    }
    keys = [(r['family'], r['seed'], r['repeat'], r['candidate']) for r in rows]
    require(len(keys) == len(set(keys)) and set(keys) == expected_keys and len(rows) == manifest['runs'], 'row grid mismatch')
    require(len(rows) == 1200, f'expected 1200 rows, got {len(rows)}')

    instances = {}
    for family in cfg['families']:
        for seed in cfg['seeds']:
            formula = generate(family, cfg['n'], cfg['ratio'], seed)
            data = formula.dimacs().encode()
            digest = sha(data)
            saved = (run / 'instances' / (digest + '.cnf')).read_bytes()
            require(saved == data and parse_dimacs(saved.decode()) == formula, 'formula mismatch')
            instances[(family, seed)] = (digest, oracle(formula))

    require(len(set(v[0] for v in instances.values())) == manifest['instances'], 'instance count mismatch')
    require(len(instances) == 120, f'expected 120 instances, got {len(instances)}')

    for r in rows:
        digest, count = instances[(r['family'], r['seed'])]
        require(r['instance_sha256'] == digest and r['oracle_count'] == count, 'instance or oracle mismatch')
        if r['status'] == 'exact':
            require(r['count'] == count and r['validation'] == 'oracle_pass', 'count mismatch')
        else:
            require(r['status'] == 'unknown' and r['count'] is None and r['validation'] == 'not_exact', 'invalid incomplete result')

    expected_summary = summarize(rows, cfg)
    actual_summary = json.loads((run / 'summary.json').read_text())
    require(actual_summary == expected_summary, 'summary mismatch')

    return {
        'status': 'verified',
        'runs': len(rows),
        'instances': len(instances),
        'exact_oracle_pass': sum(r['status'] == 'exact' for r in rows),
        'unknown_runs': sum(r['status'] == 'unknown' for r in rows),
    }


if __name__ == '__main__':
    run_dir = sys.argv[1] if len(sys.argv) > 1 else ROOT / 'evidence/policy-holdout-v02'
    print(json.dumps(verify(run_dir), indent=2))

