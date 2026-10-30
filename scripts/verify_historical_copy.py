#!/usr/bin/env python3
"""Verify the 16 historical suites in a fresh, external Git archive copy.

Never change the checkout, Git objects, or historical ledgers. A reconstructed
file is accepted only when its exact SHA-256 matches its existing ledger.
"""
import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUITES = ('policy-train-v02', 'policy-holdout-v02', 'separator-study-001',
          'scaling-benchmark-001', 'wmc-reliability-001', 'tensor-study-001',
          'cut-wmc-001', 'cut-cube-001', 'epyc-cube-001', 'epyc-cube-002',
          'commercial-benchmarks-001', 'k-terminal-wmc-001', 'poly-wmc-001',
          'dicut-wmc-001', 'mixed-wmc-001', 'srrg-wmc-001')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_path(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError(f'unsafe ledger path: {name}')
    return path


def reconstruct(path, expected):
    if not re.fullmatch(r'[0-9a-f]{64}', expected):
        raise ValueError(f'invalid SHA-256 for {path}')
    before = path.read_bytes()
    old = sha(before)
    if old == expected:
        return None
    # No mixed CR/LF, binary, or speculative transformations.
    if b'\r' in before or b'\0' in before or b'\n' not in before:
        raise ValueError(f'hash mismatch not eligible for LF-to-CRLF: {path}')
    after = before.replace(b'\n', b'\r\n')
    if sha(after) != expected:
        raise ValueError(f'neither original nor reconstructed bytes match ledger: {path}')
    path.write_bytes(after)
    if sha(path.read_bytes()) != expected:
        raise ValueError(f'write verification failed: {path}')
    return {'path': str(path), 'git_bytes_sha256': old, 'reconstructed_sha256': expected}


def prepare(copy):
    changes = []
    seen = {}
    for name in SUITES:
        run = (copy / 'evidence' / name).resolve()
        manifest = json.loads((run / 'manifest.json').read_bytes())
        refs = [(run, p, h) for p, h in manifest.get('artifact_sha256', {}).items()]
        sums = run / 'SHA256SUMS'
        if sums.exists():
            for line in sums.read_text(encoding='utf-8').splitlines():
                if line.strip() and not line.lstrip().startswith('#'):
                    h, p = line.split(maxsplit=1)
                    refs.append((run, p.lstrip('*'), h))
        for base, rel, expected in refs:
            path = checked_path(base, rel)
            if path in seen and seen[path] != expected:
                raise ValueError(f'conflicting ledger hashes: {path}')
            seen[path] = expected
            change = reconstruct(path, expected)
            if change:
                change['path'] = str(path.relative_to(copy))
                changes.append(change)
    return len(seen), changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path, help='new directory outside the repository')
    parser.add_argument('--revision', default='HEAD', help='Git commit (default HEAD)')
    args = parser.parse_args()
    dest = args.destination.resolve()
    if dest.is_relative_to(REPO) or REPO.is_relative_to(dest):
        parser.error('destination must be outside and not an ancestor of the repository')
    commit = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', '--verify', args.revision + '^{commit}'], text=True).strip()
    dest.mkdir(parents=False, exist_ok=False)
    try:
        archive = subprocess.check_output(['git', '-C', str(REPO), 'archive', '--format=tar', commit])
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            # Git archive is trusted local history, but reject links and special files.
            for member in tar:
                if not (member.isfile() or member.isdir()):
                    raise ValueError(f'unsupported archive member: {member.name}')
                checked_path(dest, member.name)
                tar.extract(member, dest, filter='data')
        checked, changes = prepare(dest)
        results = []
        for name in SUITES:
            if name == 'policy-train-v02':
                cmd = ['verify_policy_evidence.py']
            elif name == 'policy-holdout-v02':
                cmd = ['verify_holdout_evidence.py']
            elif name.startswith('epyc-cube-'):
                cmd = ['verify_epyc_evidence.py', 'evidence/' + name]
            else:
                cmd = ['verify_evidence.py', 'evidence/' + name]
            result = subprocess.run([sys.executable, *cmd], cwd=dest, text=True, capture_output=True)
            results.append({'suite': name, 'command': cmd, 'exit_code': result.returncode,
                            'stdout': result.stdout, 'stderr': result.stderr})
        exit_code = int(any(r['exit_code'] != 0 for r in results))
        report = {'revision': commit, 'ledger_references_checked': checked,
                  'reconstructed_files': changes, 'suite_results': results, 'exit_code': exit_code,
                  'note': 'Reconstruction is a hash-validated derived copy, not original Git bytes; verifier success is not proof of scientific validity. Checks and coverage differ by suite.'}
        (dest / 'historical_reconstruction_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'destination': str(dest), 'revision': commit, 'ledger_references_checked': checked,
                          'reconstructed_files': len(changes), 'suites_passed': sum(r['exit_code'] == 0 for r in results),
                          'suites_total': len(results), 'exit_code': exit_code}, indent=2))
        return exit_code
    except Exception as exc:
        print(f'FAILED (partial copy retained at {dest}): {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
