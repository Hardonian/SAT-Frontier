# SAT-Frontier v0.2.1 Release Artifact

This directory contains the distribution release archive for `SAT-Frontier` checkpoint release v0.2.1.

## Release Archive Integrity

```
a593b828409dbe89931e1d2dd71c17e1e3dda22c0673771ee1deb3ec782e730d  sat-frontier-v0.2.1.zip
```

- **File Name**: `sat-frontier-v0.2.1.zip`
- **File Size**: 7,781,303 bytes
- **File Count**: 1,870 files
- **Root Directory**: `sat-frontier-v0.2.1/`

## Built Python Wheel

```
88846e268d8151364d1bbf6c2568bcb2625aac2ff10e386691b4246d6b9b3ba4  dist/sat_frontier-0.2.1-py3-none-any.whl
```

- **Package**: `sat_frontier-0.2.1-py3-none-any.whl`
- **Validation**: Installed into an isolated virtual environment and executed via CLI against `examples/two-components.cnf`, returning exact model count 18 with 0 errors. Provenance recorded in `evidence/packaging-v021.txt`.

## Scope & Contents

The release archive packages:
1. **Source Code**: Python package `sat_frontier` including exact counting solver (`core.py`), independent truth-table oracle, component caching, dynamic decomposition, graph separator heuristics (`separator.py`), Weighted Model Counting engine (`wmc.py`), Network Infrastructure Reliability / Fault Tree compiler with dual cut compilation (`reliability.py`), Parallel Cube-and-Conquer engine (`cube_conquer.py`), and Tensor Network Contraction solver (`tensor_contract.py`).
2. **Deployment Scripts**: Automated high-core EPYC Cube-and-Conquer runner (`scripts/run_epyc_cube_conquer.sh`), batch scaling runner (`scripts/run_epyc_batch.py`), Lean 4 formal axiom auditor (`scripts/run_lean4_audit.sh`), and axiom extractor (`scripts/extract_axioms.lean`).
3. **Test Suite**: 62 unit and metamorphic tests across `tests/`.
4. **Verification Suites**: Independent hash and manifest verifiers (`verify_evidence.py`, `verify_policy_evidence.py`, `verify_holdout_evidence.py`, `verify_epyc_evidence.py`).
5. **Empirical Evidence**: 2,493 verified empirical runs with immutable manifests, per-instance CNF files, JSONL event streams, SHA256SUMS ledgers, and summary statistics across all research milestones (M0 baseline, M1 upstream audit, M2 policy train, M3 1,200-run preregistered holdout, H4 graph separator study, calibrated scaling benchmark n=12..20, M5 WMC network reliability study, H7 tensor contraction study, and EPYC high-core scaling campaign).
6. **Research Documentation**: Protocol, preregistrations, milestone tracking, and empirical reports (`docs/`).
