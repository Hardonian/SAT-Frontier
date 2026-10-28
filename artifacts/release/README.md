# SAT-Frontier Release Artifacts

This directory contains the distribution release archives and provenance records for `SAT-Frontier`.

---

## 1. Release v0.2.2 (Current Research Checkpoint)

### Archive Integrity
```
7af321ae10f969d8c69c5bb903edece3badbbef4423e9deed7e120787898d1e6  sat-frontier-v0.2.2.zip
```

- **File Name**: `sat-frontier-v0.2.2.zip`
- **File Size**: 8,155,290 bytes
- **File Count**: 1,950 files
- **Root Directory**: `sat-frontier-v0.2.2/`
- **Date**: 2026-10-28
- **Scope & Contents**:
  1. **Source Code**: Python package `sat_frontier` including exact counting solver (`core.py`), independent truth-table oracle, component caching, dynamic decomposition, graph separator heuristics (`separator.py`), Weighted Model Counting engine (`wmc.py`), Network Infrastructure Reliability / Fault Tree compiler (`reliability.py`), Dual Cut-based monotone CNF compilation engine (`cut_compiler.py`), Parallel Cube-and-Conquer engine (`cube_conquer.py`), and Tensor Network Contraction solver (`tensor_contract.py`).
  2. **Deployment & Tooling Scripts**: High-core EPYC batch scaling runner (`scripts/run_epyc_batch.py`), automated lookahead runner (`scripts/run_epyc_cube_conquer.sh`), Lean 4 bounded auditor (`scripts/run_lean4_audit.sh`), axiom extractor (`scripts/extract_axioms.lean`), real-time side-by-side demo (`scripts/demo_cut_vs_path.py`), cut WMC study runner (`scripts/run_cut_wmc_study.py`), cut lookahead study runner (`scripts/run_cut_cube_study.py`), and external run ingestion validator (`scripts/ingest_epyc_runs.py`).
  3. **Test Suite**: 67 unit and metamorphic tests across `tests/` with 100% pass rate.
  4. **Master Verification Suite**: Unified master verifier (`verify_all_evidence.py`), plus suite-specific verifiers (`verify_evidence.py`, `verify_policy_evidence.py`, `verify_holdout_evidence.py`, `verify_epyc_evidence.py`).
  5. **Empirical Evidence**: **2,577 verified empirical runs** across 10 complete suites (`policy-train-v02`, `policy-holdout-v02`, `separator-study-001`, `scaling-benchmark-001`, `wmc-reliability-001`, `tensor-study-001`, `cut-wmc-001`, `cut-cube-001`, `epyc-cube-001`, `epyc-cube-002`).
  6. **Research Documentation**: Theoretical foundations, preregistrations, milestone ledgers, and empirical reports across `docs/`.

---

## 2. Release v0.2.1

### Archive Integrity
```
a593b828409dbe89931e1d2dd71c17e1e3dda22c0673771ee1deb3ec782e730d  sat-frontier-v0.2.1.zip
```

- **File Name**: `sat-frontier-v0.2.1.zip`
- **File Size**: 7,781,303 bytes
- **File Count**: 1,870 files
- **Root Directory**: `sat-frontier-v0.2.1/`

### Built Python Wheel
```
88846e268d8151364d1bbf6c2568bcb2625aac2ff10e386691b4246d6b9b3ba4  dist/sat_frontier-0.2.1-py3-none-any.whl
```
- **Validation**: Installed into an isolated virtual environment and executed via CLI against `examples/two-components.cnf`, returning exact model count 18 with 0 errors. Provenance recorded in `evidence/packaging-v021.txt`.
