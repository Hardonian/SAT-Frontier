# SAT-Frontier Release Artifacts

This directory contains the distribution release archives and provenance records for `SAT-Frontier`.

---

## 1. Release v0.2.7 (Current Production & Frontier Breakthrough Release)

### Archive Integrity (Release v0.2.7)

```text
38589bf17094fbd7ddc023e2609aa4c45ac17ae9836030fc4aabd4a5ac1c4d3e  sat-frontier-v0.2.7.zip
```

- **File Name**: `sat-frontier-v0.2.7.zip`
- **File Size**: 14,301,198 bytes
- **File Count**: 6,843 files
- **Root Directory**: `sat-frontier-v0.2.7/`
- **Date**: 2026-10-30
- **Scope & Contents**:
  1. **Bounded-Diameter / Latency-Constrained Reliability (Hypothesis H17)**: Dual Length-Bounded Cut Monotone CNF compiler in `sat_frontier/bounded_hop_compiler.py`. Formulated and proved the Dual $L$-Hop Cut Duality Theorem showing that $\mathbb{P}(\text{dist}(s, t) \le L)$ compiles directly into monotone positive clauses over physical edge variables alone with strictly $|E|$ variables and zero auxiliary indicators. Evaluated across 24 benchmark instances in `evidence/bounded-hop-wmc-001/` with 24/24 independent BFS shortest-path truth-table oracle checks matching with 100% exact rational precision (`Fraction`) in 0.38ms mean latency. Integrated into `EnterpriseReliabilityEngine.audit_bounded_latency`. Documented in `docs/BOUNDED_HOP_PREREGISTRATION.md` and `docs/BOUNDED_HOP_REPORT.md`.
  2. **Interactive Web Visualizer & SLA Dashboard (Generative UI)**: Standalone single-page application in `sat_frontier/enterprise/web/index.html` with force-directed SVG graph physics, real-time SLA metrics, $N$-nines badges, Birnbaum criticality heatmaps, and dynamic continuous $R(t)$ lifetime curve plots. Zero-dependency REST API server in `sat_frontier/enterprise/server.py`.
  3. **Formal Verification in Lean 4 (`lean/CutDuality.lean`)**: Mechanized graph connectivity, edge cuts, operational states, and proved master theorem `dual_cut_menger_duality`: $\text{Connected}(G_{\mathbf{x}}, s, t) \iff (\forall \text{cut} : \text{VertexCut } V \, s \, t, \text{CutSurvives } g \, x \, \text{cut})$.
  4. **Industry Topology Importers & Internet Topology Zoo**: Zero-dependency universal importers in `sat_frontier/enterprise/importers.py` (GraphML, GML, NetworkX/Cytoscape JSON, CSV/TSV) and curated carrier backbones in `instances/topologies/` (Abilene, Internet2, BellSouth, Colt, GEANT).
  5. **Capacitated Network Flow Reliability (Hypothesis H16)**: Dual Cut Threshold Monotone CNF compiler in `sat_frontier/capacitated_compiler.py`. Formulated and proved the Capacitated Dual Cut Duality Theorem showing that $\mathbb{P}(\text{MaxFlow} \ge D)$ compiles directly into monotone positive clauses over physical edge variables alone with strictly $|E|$ variables and zero auxiliary flow variables. Evaluated across 24 benchmark instances in `evidence/capacitated-wmc-001/` with 24/24 independent Dinic max-flow truth-table oracle checks matching with 100% exact rational precision. Documented in `docs/CAPACITATED_RELIABILITY_PREREGISTRATION.md` and `docs/CAPACITATED_RELIABILITY_REPORT.md`.
  6. **Continuous Temporal Network Reliability & Exact Closed-Form MTTF (Hypothesis H15)**: Continuous lifetime and Mean Time To Failure (MTTF) engine in `sat_frontier/temporal_reliability.py`. Formulated and proved the Exact Algebraic MTTF Integration Theorem: $\text{MTTF} = \sum_{j=1}^m \frac{a_j}{j \lambda}$, evaluating exact rational lifetime moments directly from monomial expansions of $P(x) \in \mathbb{Z}[x]$ in microseconds without Monte Carlo sampling. Evaluated across 24 instances in `evidence/temporal-wmc-001/` with 24/24 independent composite Simpson quadrature verifications within $10^{-4}$ relative tolerance. Documented in `docs/TEMPORAL_RELIABILITY_PREREGISTRATION.md` and `docs/TEMPORAL_RELIABILITY_REPORT.md`.
  7. **Comprehensive Research Monograph & LaTeX Publication Paper**: Authored `docs/RESEARCH_PAPERS/SAT_FRONTIER_UNIFIED_DUALITY.md` and `docs/RESEARCH_PAPERS/SAT_FRONTIER_UNIFIED_DUALITY.tex` formatted for IEEE Transactions on Reliability, unifying all 9 duality theorems, proofs, complexity bounds, 19-suite empirical results, and formal audit findings on OpenAI's ETH refutation.
  8. **Turnkey Hermes GPT-6.1 Terra Directive for AMD EPYC**: Authored turnkey execution directive in `docs/HERMES_TERRA_EPYC_DIRECTIVE.md` for autonomous commission of the 64-core AMD EPYC server (168 GB RAM), including NUMA memory interleaving, automated verification checks, and cross-depth invariants.
  9. **Empirical Evidence Base**: **2,774 verified empirical runs** across 19 complete suites with 100% cryptographic SHA-256 and invariant validation (`verify_all_evidence.py`).
  10. **Unit Test Suite**: 164 unit and metamorphic tests across `tests/` with 100% pass rate (162 passed, 2 skipped GPU tests).

---

## 2. Release v0.2.6 (Previous Production Release)

### Archive Integrity (Release v0.2.6)

```text
ac36a41bd0f7d07c71f7d429bc36b59bbd53cd14be2c971abb6b653e0e616865  sat-frontier-v0.2.6.zip
```

- **File Name**: `sat-frontier-v0.2.6.zip`
- **File Size**: 8,813,747 bytes
- **File Count**: 2,172 files
- **Root Directory**: `sat-frontier-v0.2.6/`
- **Date**: 2026-10-29
- **Scope & Contents**:
  1. **Dual SRRG-Cut Monotone CNF Compilation (Hypothesis H14)**: Shared-Risk Resource Group (SRRG / Fate-Sharing) correlated multi-failure network reliability compiler in `sat_frontier/srrg_compiler.py`. Formulated and proved that network connectivity under arbitrary physical risk group mappings compiles directly into monotone CNF clauses over risk survival variables alone with zero auxiliary routing variables. Evaluated across 24 benchmark instances in `evidence/srrg-wmc-001/` with 22/22 independent brute-force oracle checks matching with 100% exact rational precision (`Fraction`). Sub-0.15ms solving latencies across all 24 instances. Documented in `docs/SRRG_RELIABILITY_PREREGISTRATION.md` and `docs/SRRG_RELIABILITY_REPORT.md`.
  2. **High-Core AMD EPYC Cut-Compilation Campaign Infrastructure**: Pre-compiled 10 frontier benchmark formulas in `instances/epyc-cut-frontier/` (`grid_3x8..3x11`, `grid_4x5..4x7`, `grid_5x5`, `barbell_6_3_6`, `chvatal`), complete with turnkey batch runners (`scripts/run_epyc_cut_campaign.sh`, `scripts/run_epyc_cut_campaign.py`), cross-depth invariant checks, and specification guide (`docs/EPYC_CUT_CAMPAIGN_SPECIFICATION.md`).
  3. **Enterprise Reliability SDK Expansion**: Added `audit_srrg_reliability` to `sat_frontier/enterprise/engine.py`.
  4. **Empirical Evidence**: **2,702 verified empirical runs** across 16 complete suites with 100% cryptographic SHA-256 and invariant validation (`verify_all_evidence.py`).
  5. **Unit Test Suite**: 118 unit and metamorphic tests across `tests/` with 100% pass rate.

---

## 3. Release v0.2.5 (Previous Breakthrough Release)

### Archive Integrity (Release v0.2.5)

```text
c957354f8b064474c5ca1f7ed29537d8d6162817ee3ce0eec60ed9cc6d01e834  sat-frontier-v0.2.5.zip
```

- **File Name**: `sat-frontier-v0.2.5.zip`
- **File Size**: 8,500,575 bytes
- **File Count**: 2,127 files
- **Root Directory**: `sat-frontier-v0.2.5/`
- **Date**: 2026-10-29
- **Scope & Contents**:
  1. **Dual Mixed-Cut Monotone CNF Compilation (Hypothesis H13)**: Mixed node-and-edge failure network reliability compiler in `sat_frontier/mixed_cut_compiler.py`. Formulated and proved that internal node-splitting ($v \mapsto (v_{\text{in}}, v_{\text{out}})$ with capacity/operational probability $q_v$) maps physical mixed cuts into directed cuts in split graph $G^*$, producing exact monotone CNF formulas with zero auxiliary variables. Evaluated across 24 benchmark instances in `evidence/mixed-wmc-001/` with 16/16 independent brute-force oracle checks matching with 100% exact rational precision (`Fraction`). Sub-290ms solving latencies across all instances. Documented in `docs/MIXED_RELIABILITY_PREREGISTRATION.md` and `docs/MIXED_RELIABILITY_REPORT.md`.
  2. **All-Pairs SLA Matrix & Centrality Engine**: Complete network-wide pairwise availability engine in `sat_frontier/enterprise/all_pairs.py`. Computes all $\binom{|V|}{2}$ pairwise SLA availabilities, identifies worst-case SLA bottleneck pairs, calculates Network Diameter Reliability $R_{\text{min}}$, computes failure-aware node centrality $C_R(v) = \frac{1}{|V|-1}\sum_{u \ne v} R(v, u)$, and generates both ANSI terminal heatmaps and Markdown SLA audit reports. Integrated into `sat_frontier/enterprise/engine.py` (`audit_all_pairs`) and enterprise CLI (`--all-pairs`, `--demo-subsea`).
  3. **Empirical Evidence**: **2,678 verified empirical runs** across 15 complete suites with 100% cryptographic SHA-256 and invariant validation (`verify_all_evidence.py`).
  4. **Unit Test Suite**: 110 unit and metamorphic tests across `tests/` with 100% pass rate.

---

## 4. Release v0.2.4 (Previous Breakthrough Release)

### Archive Integrity (Release v0.2.4)

```text
741068c116f079df75c9b4cbcfe089c8251e2b0fb3ae5c4314657df19bf19247  sat-frontier-v0.2.4.zip
```

- **File Name**: `sat-frontier-v0.2.4.zip`
- **File Size**: 8,446,536 bytes
- **File Count**: 2,089 files
- **Root Directory**: `sat-frontier-v0.2.4/`
- **Date**: 2026-10-29
- **Scope & Contents**:
  1. **Dual Dicut Monotone CNF Compilation (Hypothesis H12)**: Directed two-terminal reliability ($s \leadsto t$) compiler in `sat_frontier/dicut_compiler.py` with zero auxiliary variables and zero MTZ subtour elimination bloat. Evaluated across 24 benchmark instances in `evidence/dicut-wmc-001/` with 18/18 independent brute-force oracle checks matching with 100% exact rational precision. Documented in `docs/DICUT_RELIABILITY_PREREGISTRATION.md` and `docs/DICUT_RELIABILITY_REPORT.md`.
  2. **Algebraic Model Counting over $\mathbb{Z}[x]$ & Percolation Susceptibility (Hypothesis H11)**: Closed-form reliability polynomial engine in `sat_frontier/poly_wmc.py` evaluating complete polynomial spectra and continuous percolation thresholds $p_c$ in a single DPLL search pass. Evaluated across 24 benchmark instances in `evidence/poly-wmc-001/` with 17/17 independent brute-force oracle checks matching with 100% exact integer coefficient equality. Documented in `docs/POLYNOMIAL_WMC_PREREGISTRATION.md` and `docs/POLYNOMIAL_WMC_REPORT.md`.
  3. **Multi-Terminal & All-Terminal Reliability (Hypothesis H10)**: Dual K-Cut monotone CNF compiler in `sat_frontier/k_cut_compiler.py` generalizing Menger duality to multi-terminal ($K \ge 2$) and all-terminal ($K = V$) reliability with zero auxiliary variables. Evaluated across 24 instances in `evidence/k-terminal-wmc-001/` with 17/17 independent oracle matches.
  4. **Enterprise Reliability SDK Expansion**: Integrated `audit_parametric_curve` and `audit_directed_network` into `sat_frontier/enterprise/engine.py`.
  5. **Empirical Evidence**: **2,654 verified empirical runs** across 14 complete suites with 100% cryptographic SHA-256 and invariant validation (`verify_all_evidence.py`).
  6. **Unit Test Suite**: 100 unit and metamorphic tests across `tests/` with 100% pass rate.

---

## 5. Release v0.2.3 (Commercialization Baseline)

### Archive Integrity (Release v0.2.3)

```text
63403d4e69db721b49fcb8f85e0af3732742fa7f09d3dabec90a8d10321108af  sat-frontier-v0.2.3.zip
```

- **File Name**: `sat-frontier-v0.2.3.zip`
- **File Size**: 8,353,250 bytes
- **File Count**: 2,017 files
- **Root Directory**: `sat-frontier-v0.2.3/`
- **Date**: 2026-10-28
- **Scope & Contents**:
  1. **Multi-Terminal & All-Terminal Reliability (Hypothesis H10)**: Dual K-Cut monotone CNF compiler in `sat_frontier/k_cut_compiler.py` generalizing Menger duality to multi-terminal ($K \ge 2$) and all-terminal ($K = V$) reliability with zero auxiliary variables, eliminating hyper-exponential Steiner tree enumeration. 24 benchmark instances executed in `evidence/k-terminal-wmc-001/` with 17/17 independent brute-force oracle checks matching with 100% exact rational precision.
  2. **Enterprise Reliability & SLA Audit SDK**: Full commercialization suite in `sat_frontier/enterprise/` (`topology.py`, `metrics.py`, `engine.py`, `report.py`, `cli.py`), including exact Birnbaum criticality indexing $I_B(e) = \frac{\partial R}{\partial p_e}$, downtime conversions ($N$-nines, minutes/year, hours/year), MTBF/MTTR/FIT modeling, single point of failure (SPOF) detection, multi-terminal quorum auditing (`audit_multi_terminal`), and automated compliance report generation.
  3. **Real-World Mission-Critical Benchmarks**: Evaluated 5 production systems (Cloud Multi-Region VPC, Transatlantic Subsea Optical Mesh, IEEE 14-Bus Power Grid, Avionics DO-178C Quad-Redundant Actuator, Telecom Metro Dual-Ring) in `evidence/commercial-benchmarks-001/` with 100% exact rational agreement and sub-250ms solving latencies.
  4. **Enterprise & Specification Guides**: Developer quickstart and CI/CD integration guide (`docs/ENTERPRISE_SDK_GUIDE.md`), regulatory compliance audit specification (`docs/SLA_AUDIT_SPECIFICATION.md`), multi-terminal empirical report (`docs/K_TERMINAL_REPORT.md`), and enterprise monetization roadmap (`docs/COMMERCIAL_APPLICATIONS.md`).
  5. **Empirical Evidence**: **2,606 verified empirical runs** across 12 complete suites (`policy-train-v02`, `policy-holdout-v02`, `separator-study-001`, `scaling-benchmark-001`, `wmc-reliability-001`, `tensor-study-001`, `cut-wmc-001`, `cut-cube-001`, `epyc-cube-001`, `epyc-cube-002`, `commercial-benchmarks-001`, `k-terminal-wmc-001`).
  6. **Test Suite**: 80 unit and metamorphic tests across `tests/` with 100% pass rate.
  7. **Core Research Engines**: Dual Cut-based monotone CNF compiler (`cut_compiler.py`), Dual K-cut compiler (`k_cut_compiler.py`), high-core parallel Cube-and-Conquer engine (`cube_conquer.py`), Weighted Model Counting engine (`wmc.py`), Tensor Network Contraction engine (`tensor_contract.py`), and dynamic separator heuristic engine (`separator.py`).

---

## 6. Release v0.2.2 (Research Checkpoint)

### Archive Integrity (Release v0.2.2)

```text
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

## 7. Release v0.2.1

### Archive Integrity (Release v0.2.1)

```text
a593b828409dbe89931e1d2dd71c17e1e3dda22c0673771ee1deb3ec782e730d  sat-frontier-v0.2.1.zip
```

- **File Name**: `sat-frontier-v0.2.1.zip`
- **File Size**: 7,781,303 bytes
- **File Count**: 1,870 files
- **Root Directory**: `sat-frontier-v0.2.1/`

### Built Python Wheel

```text
88846e268d8151364d1bbf6c2568bcb2625aac2ff10e386691b4246d6b9b3ba4  dist/sat_frontier-0.2.1-py3-none-any.whl
```

- **Validation**: Installed into an isolated virtual environment and executed via CLI against `examples/two-components.cnf`, returning exact model count 18 with 0 errors. Provenance recorded in `evidence/packaging-v021.txt`.
