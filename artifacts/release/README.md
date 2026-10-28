# SAT-Frontier v0.2.1 Release Artifact

This directory contains the distribution release archive for `SAT-Frontier` checkpoint release v0.2.1.

## Release Archive Integrity

```
b3d224835007f8324869bac03c16b7a8406069d95babf647af9d21e85d736c65  sat-frontier-v0.2.1.zip
```

- **File Name**: `sat-frontier-v0.2.1.zip`
- **File Size**: 1,719,077 bytes
- **File Count**: 1,536 files
- **Root Directory**: `sat-frontier-v0.2.1/`

## Built Python Wheel

```
a7d3395f22258ebfe93c24b20d608652a058b350b84312848dd2497413f8b8ae  dist/sat_frontier-0.2.1-py3-none-any.whl
```

- **Package**: `sat_frontier-0.2.1-py3-none-any.whl`
- **Validation**: Installed into an isolated virtual environment and executed via CLI against `examples/two-components.cnf`, returning exact model count 18 with 0 errors. Provenance recorded in `evidence/packaging-v021.txt`.

## Scope & Contents

The v0.2.1 release archive packages:
1. **Source Code**: Python package `sat_frontier` including exact counting solver (`core.py`), independent truth-table oracle, component caching, dynamic decomposition, graph separator heuristics (`separator.py`), Weighted Model Counting engine (`wmc.py`), Network Infrastructure Reliability / Fault Tree compiler (`reliability.py`), Parallel Cube-and-Conquer engine (`cube_conquer.py`), and Tensor Network Contraction solver (`tensor_contract.py`).
2. **Deployment Scripts**: Automated high-core EPYC Cube-and-Conquer runner (`scripts/run_epyc_cube_conquer.sh`) and Lean 4 formal axiom auditor (`scripts/run_lean4_audit.sh`).
3. **Test Suite**: 61 unit and metamorphic tests across `tests/`.
4. **Verification Suites**: Independent hash and manifest verifiers (`verify_evidence.py`, `verify_policy_evidence.py`, `verify_holdout_evidence.py`).
5. **Empirical Evidence**: 2,191 verified empirical runs with immutable manifests, per-instance CNF files, JSONL event streams, and summary statistics across all research milestones (M0 baseline, M1 upstream audit, M2 policy train, M3 1,200-run preregistered holdout, H4 graph separator study, calibrated scaling benchmark n=12..20, M5 WMC network reliability study, and H7 tensor contraction study).
6. **Research Documentation**: Protocol, preregistrations, milestone tracking, and empirical reports (`docs/`).
