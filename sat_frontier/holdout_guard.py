"""Fail-closed building blocks for the unrun v0.2 policy holdout.

These guards do not constitute a holdout runner.  The reservation directory is
per checkout; deletion, a different clone, or malicious modification is not
prevented.  No holdout results may be generated until an integrated runner and
its evidence handling are reviewed and frozen in a separate preregistration.
"""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / 'evidence/policy-train-v02'
RESERVATION = ROOT / 'evidence/policy-holdout-v02-consumed'
WINNER_SHA256 = '06a06a61f261bc5bbce7ec24b58e4f1293c68bdeb18ae1f0cb24d21ddd9d4a60'
TRAIN_MANIFEST_SHA256 = '5215eaa1a743ace564d695c4554d508b843b29e8b061f87efc4ae693e47e54f2'
EXPECTED_SOURCE = {
    'configs/policy-train-v02.json': '73874f4dbb96e3b177169ae075f4484dabb05c5f947c12dbe7059482cabd6eed',
    'docs/POLICY_PREREGISTRATION.md': '90c53104bd660e3f43b158bb5a7dff3a6109e2d07ecc655a13cf47a87e0a8b62',
    'sat_frontier/core.py': 'b2c325f7482d2ad7754bbe1ea1347a32dfcbed69bf65fa29bce7e84e367e4587',
    'sat_frontier/generate.py': '7b0fdb60e0237ffb5200f055bed2741e387b7be2070d28d421949995ae5ebd52',
    'sat_frontier/policy_train.py': '111fb3910fe559ee960c6299e2d89084197ba0d9f89e30cac30db4d2124409b2',
}
# The verifier and package initializer are not included in the train winner's
# source map, but are executed by verification and must also be pinned.
VERIFIER_SOURCE = {
    'verify_policy_evidence.py': 'd30744e4009aec4f32dcf0cc76f9d0b1b871100ac8b6ffade276eae24a0282a7',
    'sat_frontier/__init__.py': '83fa8605d5cc1c4ecf35b7e52ef1859edef58b57887d884ac349de79cdc1bade',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_train_freeze(root=ROOT):
    """Verify pinned winner bytes, its full source map, and train evidence."""
    root = Path(root)
    train = root / 'evidence/policy-train-v02'
    raw = (train / 'winner.json').read_bytes()
    if digest(raw) != WINNER_SHA256:
        raise ValueError('frozen winner mismatch')
    if digest((train / 'manifest.json').read_bytes()) != TRAIN_MANIFEST_SHA256:
        raise ValueError('frozen train manifest mismatch')
    winner = json.loads(raw)
    if (winner.get('candidate') != 'component' or not winner.get('train_only')
            or winner.get('holdout_consumed') is not False
            or winner.get('source_sha256') != EXPECTED_SOURCE):
        raise ValueError('frozen winner content mismatch')
    for name, expected in {**EXPECTED_SOURCE, **VERIFIER_SOURCE}.items():
        if digest((root / name).read_bytes()) != expected:
            raise ValueError('frozen source mismatch: ' + name)
    # Import lazily so this module remains usable in isolation by guard tests.
    if root.resolve() != ROOT.resolve():
        raise ValueError('historical evidence verification requires the actual source root')
    from verify_policy_evidence import verify
    result = verify(train)
    if result != {'status': 'verified', 'runs': 384, 'instances': 32,
                  'exact_oracle_pass': 360, 'winner': 'component'}:
        raise ValueError('unexpected train evidence verification')
    return winner


def check_overlap(instance_bytes, excluded_hashes):
    """Reject any byte-identical prior instance and duplicates within the split."""
    seen = set()
    excluded = set(excluded_hashes)
    for data in instance_bytes:
        key = digest(data)
        if key in excluded:
            raise ValueError('holdout instance overlaps prior evidence: ' + key)
        if key in seen:
            raise ValueError('duplicate holdout instance: ' + key)
        seen.add(key)
    if not seen:
        raise ValueError('empty holdout instance set')
    return seen


def prior_instance_hashes(evidence_root):
    """Hash actual stored CNFs, not names, including development evidence."""
    root = Path(evidence_root)
    hashes = {digest(p.read_bytes()) for p in root.rglob('*.cnf') if p.is_file()}
    if not hashes:
        raise ValueError('no prior CNFs found; refusing overlap check')
    return hashes


def _fsync_dir(path):
    if not hasattr(os, 'O_DIRECTORY'):
        return
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def reserve_once(path, preregistration_sha256):
    """Durably consume a local split before reading/generating/evaluating it.

    Directory creation is the atomic one-shot decision. An empty or incomplete
    reservation after a crash is consumed too and must never be removed/reused.
    Caller must separately verify a prior immutable preregistration and source.
    """
    path = Path(path)
    if len(preregistration_sha256) != 64 or any(c not in '0123456789abcdef' for c in preregistration_sha256):
        raise ValueError('invalid preregistration hash')
    path.mkdir(mode=0o700, exist_ok=False)
    _fsync_dir(path.parent)
    with (path / 'reservation.json').open('x', encoding='utf-8') as handle:
        json.dump({'status': 'consumed', 'preregistration_sha256': preregistration_sha256}, handle, sort_keys=True)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    _fsync_dir(path)
