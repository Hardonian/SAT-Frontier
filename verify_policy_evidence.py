"""Check the committed policy campaign's integrity and independent oracle counts."""
import json
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
    winner = json.loads((run / 'winner.json').read_text())
    require(manifest['status'] == 'complete' and manifest['split'] == 'train', 'not a completed train run')
    for name, digest in manifest['source_sha256'].items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT) and sha(path.read_bytes()) == digest, 'source mismatch: ' + name)
    actual_paths = {p.relative_to(run).as_posix() for p in run.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    require(actual_paths == set(manifest['artifact_sha256']), 'artifact inventory mismatch')
    for name, digest in manifest['artifact_sha256'].items():
        path = (run / name).resolve()
        require(path.is_relative_to(run) and sha(path.read_bytes()) == digest, 'artifact mismatch: ' + name)
    rows = [json.loads(line) for line in (run / 'runs.jsonl').read_text().splitlines()]
    expected_keys = {(f, seed, repeat, name) for f in cfg['families'] for seed in cfg['seeds']
                     for repeat in range(cfg['repeats']) for name in ['control'] + list(cfg['candidates'])}
    keys = [(r['family'], r['seed'], r['repeat'], r['candidate']) for r in rows]
    require(len(keys) == len(set(keys)) and set(keys) == expected_keys and len(rows) == manifest['runs'], 'row grid mismatch')
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
    for r in rows:
        digest, count = instances[(r['family'], r['seed'])]
        require(r['instance_sha256'] == digest and r['oracle_count'] == count, 'instance or oracle mismatch')
        if r['status'] == 'exact':
            require(r['count'] == count and r['validation'] == 'oracle_pass', 'count mismatch')
        else:
            require(r['status'] == 'unknown' and r['count'] is None and r['validation'] == 'not_exact', 'invalid incomplete result')
    ranking = sorted(cfg['candidates'], key=lambda name: (
        -sum(r['status'] == 'exact' for r in rows if r['candidate'] == name),
        sum(r.get('nodes', cfg['max_nodes']) for r in rows if r['candidate'] == name), name))
    require(winner['ranking'] == ranking and winner['candidate'] == ranking[0], 'selection mismatch')
    require(winner['weights'] == cfg['candidates'][ranking[0]] and winner['source_sha256'] == manifest['source_sha256'], 'freeze mismatch')
    require(summarize(rows, cfg) == json.loads((run / 'summary.json').read_text()), 'summary mismatch')
    return {'status': 'verified', 'runs': len(rows), 'instances': len(instances),
            'exact_oracle_pass': sum(r['status'] == 'exact' for r in rows), 'winner': ranking[0]}


if __name__ == '__main__':
    print(json.dumps(verify(ROOT / 'evidence/policy-train-v02'), sort_keys=True))
