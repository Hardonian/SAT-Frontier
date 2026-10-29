# SAT-Frontier Release Artifacts

This directory contains the distribution release archives and provenance records for `SAT-Frontier`.

---

## 1. Release v0.2.3 (Current Production & Commercialization Release)

### Archive Integrity
```
100a9309e45985cfe46dba0359501804ea45ec86dca5ffb8cd5cbeafe4a4ee6c  sat-frontier-v0.2.3.zip
```

- **File Name**: `sat-frontier-v0.2.3.zip`
- **File Size**: 8,311,031 bytes
- **File Count**: 1,981 files
- **Root Directory**: `sat-frontier-v0.2.3/`
- **Date**: 2026-10-28
- **Scope & Contents**:
  1. **Enterprise Reliability & SLA Audit SDK**: Full commercialization suite in `sat_frontier/enterprise/` (`topology.py`, `metrics.py`, `engine.py`, `report.py`, `cli.py`), including exact Birnbaum criticality indexing $I_B(e) = \frac{\partial R}{\partial p_e}$, downtime conversions ($N$-nines, minutes/year, hours/year), MTBF/MTTR/FIT modeling, single point of failure (SPOF) identification, and automated compliance report generation.
  2. **Real-World Mission-Critical Benchmarks**: Evaluated 5 production systems (Cloud Multi-Region VPC, Transatlantic Subsea Optical Mesh, IEEE 14-Bus Power Grid, Avionics DO-178C Quad-Redundant Actuator, Telecom Metro Dual-Ring) in `evidence/commercial-benchmarks-001/` with 100% exact rational agreement and sub-250ms solving latencies.
  3. **Enterprise & Specification Guides**: Developer quickstart and CI/CD integration guide (`docs/ENTERPRISE_SDK_GUIDE.md`), regulatory compliance audit specification (`docs/SLA_AUDIT_SPECIFICATION.md`), and enterprise monetization roadmap (`docs/COMMERCIAL_APPLICATIONS.md`).
  4. **Empirical Evidence**: **2,582 verified empirical runs** across 11 complete suites (`policy-train-v02`, `policy-holdout-v02`, `separator-study-001`, `scaling-benchmark-001`, `wmc-reliability-001`, `tensor-study-001`, `cut-wmc-001`, `cut-cube-001`, `epyc-cube-001`, `epyc-cube-002`, `commercial-benchmarks-001`).
  5. **Test Suite**: 71 unit and metamorphic tests across `tests/` with 100% pass rate.
  6. **Core Research Engines**: Dual Cut-based monotone CNF compiler (`cut_compiler.py`), high-core parallel Cube-and-Conquer engine (`cube_conquer.py`), Weighted Model Counting engine (`wmc.py`), Tensor Network Contraction engine (`tensor_contract.py`), and dynamic separator heuristic engine (`separator.py`).

---

## 2. Release v0.2.2 (Research Checkpoint)

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
