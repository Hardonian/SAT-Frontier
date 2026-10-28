# SAT-Frontier v0.2.1 Release Artifact

This directory contains the distribution release archive for `SAT-Frontier` checkpoint release v0.2.1.

## Release Archive Integrity

```
1887de473437cedca8a8475dec49a25746ba275322988e0ebc65aacaea5d713f  sat-frontier-v0.2.1.zip
```

- **File Name**: `sat-frontier-v0.2.1.zip`
- **File Size**: 1,580,095 bytes
- **File Count**: 1,499 files
- **Root Directory**: `sat-frontier-v0.2.1/`

## Built Python Wheel

```
9fdaff0155a0139e31a720d5034e344663cd33a14600643efe6bc52e6a5ce4a5  sat_frontier-0.2.1-py3-none-any.whl
```

- **Package**: `sat_frontier-0.2.1-py3-none-any.whl`
- **Validation**: Installed into an isolated virtual environment and executed via CLI against `examples/two-components.cnf`, returning exact model count 18 with 0 errors. Provenance recorded in `evidence/packaging-v021.txt`.

## Scope & Contents

The v0.2.1 release archive packages:
1. **Source Code**: Python package `sat_frontier` including exact counting solver (`core.py`), independent truth-table oracle, component caching, dynamic decomposition, graph separator heuristics (`separator.py`), Weighted Model Counting engine (`wmc.py`), and Network Infrastructure Reliability / Fault Tree compiler (`reliability.py`).
2. **Test Suite**: 54 unit and metamorphic tests across `tests/`.
3. **Verification Suites**: Independent hash and manifest verifiers (`verify_evidence.py`, `verify_policy_evidence.py`, `verify_holdout_evidence.py`).
4. **Empirical Evidence**: All immutable run manifests, per-instance CNF files, JSONL event streams, and summary statistics across all research milestones (M0 baseline, M1 upstream audit, M2 policy train, M3 1,200-run preregistered holdout, H4 graph separator study, calibrated scaling benchmark n=12..20, and M5 WMC network reliability study).
5. **Research Documentation**: Protocol, preregistrations, milestone tracking, and empirical reports (`docs/`).
