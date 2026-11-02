# SAT-Frontier: The Thirteen Unified Dual Cut Theorems & Exact Infrastructure Reliability Lab

**Production Release**: `v0.2.9`  
**Date**: October 2026  
**Empirical Evidence Base**: 23 Complete Research Suites, 2,870 Verified Execution Runs  
**Unit Test Suite**: 187 Unit and Metamorphic Tests (184 Passed, 3 Skipped POSIX/GPU)  
**Verification**: 100% SHA-256 Cryptographic Hash Integrity across Evidence Ledgers  
**Primary Repository**: [`https://github.com/Hardonian/SAT-Frontier.git`](https://github.com/Hardonian/SAT-Frontier.git)

---

## 1. Overview & Core Mission

**SAT-Frontier** is a CPU-first exact model counting (#SAT / #WMC), theoretical computer science, and network resilience engineering laboratory. The laboratory is dedicated to:

1. **Foundational Theoretical Exact Counting**: Establishing mathematically proven, zero-auxiliary-variable reductions from #P-complete network infrastructure problems to Conjunctive Normal Form (CNF) Weighted Model Counting (#WMC).
2. **Shattering Path-Enumeration Pathologies**: Replacing classical $O(2^{|V|})$ path-indicator encodings with inclusion-minimal cut transversals, resolving the planar grid hardness cliff (e.g., reducing `grid_3x7` from >600s timeout to 2.13s).
3. **Continuous Lifetime & Stochastic Renewal Analysis**: Integrating exact closed-form continuous Mean Time To Failure (MTTF), Weibull fatigue/aging moments, and repairable asymptotic failure frequency via exact rational arithmetic ($\mathbb{Q}$) and the Birnbaum criticality derivative.
4. **Any-Time Rigorous Monotone Enclosures**: Evaluating certified lower and upper reliability intervals $[R_{\text{lower}}, R_{\text{upper}}]$ that contract with polynomial delay without requiring complete exponential enumeration.
5. **Formal Verification in Lean 4**: Mechanizing graph cut duality, algebraic MTTF integration, multi-commodity flow duality, Weibull wear-out aging, repairable renewal balance, and monotone enclosure relaxations in pure Lean 4.
6. **Rigorous Empirical Ledgering & Upstream Audit**: Maintaining 100% cryptographic SHA-256 ledgers across 23 research campaigns (2,870 runs), publishing definitive negative results in accordance with pre-registered protocols, and conducting an independent formal audit of OpenAI's claimed subexponential SAT refutation of the Exponential Time Hypothesis (`openai/math`).

---

## 2. The Thirteen Unified Dual Cut Theorems

SAT-Frontier unifies physical and logical network resilience analysis into thirteen foundational duality theorems that compile directly into purely positive monotone CNF formulas with **strictly zero auxiliary routing or flow variables**:

| Theorem | Domain & Scope | Mathematical Formulation | Variable Complexity |
| :--- | :--- | :--- | :---: |
| **Theorem 1** | **Two-Terminal Cut Duality** | $s \longleftrightarrow t \iff \bigwedge_{C \in \mathcal{C}_{\min}(s, t)} \bigvee_{e \in C} x_e$ | Strictly $\vert E \vert$ |
| **Theorem 2** | **Multi-Terminal ($K$-Terminal) & All-Terminal** | $K \text{ connected} \iff \bigwedge_{C \in \mathcal{C}_{\min}(K)} \bigvee_{e \in C} x_e$ | Strictly $\vert E \vert$ |
| **Theorem 3** | **Directed Dicut Reachability ($s \leadsto t$)** | $s \leadsto t \iff \bigwedge_{D \in \mathcal{D}_{\min}(s, t)} \bigvee_{a \in D} x_a$ | Strictly $\vert A \vert$ |
| **Theorem 4** | **Mixed Node-and-Edge Failure (Split Graph $G^*$)** | $s \longleftrightarrow t \text{ in } G \iff s \leadsto t \text{ in } G^*$ via $(v_{\text{in}}, v_{\text{out}})$ | Strictly $\vert E \vert + \vert V \setminus \{s,t\} \vert$ |
| **Theorem 5** | **Shared-Risk Resource Groups (SRRG / Fate-Sharing)** | $s \longleftrightarrow t \iff \bigwedge_{C} \bigwedge_{H \in \mathcal{H}_{\min}(C)} \bigvee_{r \in H} y_r$ | Strictly $\vert \mathcal{R} \vert$ |
| **Theorem 6** | **Algebraic Model Counting over $\mathbb{Z}[x]$** | $P(x) = \sum_{k=0}^m c_k x^k (1-x)^{m-k} = \sum_{j=1}^m a_j x^j \in \mathbb{Z}[x]$ | Single DPLL pass |
| **Theorem 7** | **Exact Closed-Form Algebraic MTTF Integration** | $\text{MTTF} = \sum_{j=1}^m \frac{a_j}{j \lambda}, \quad \mathbb{E}[T^2] = 2 \sum_{j=1}^m \frac{a_j}{(j \lambda)^2}$ | Microsecond evaluation |
| **Theorem 8** | **Capacitated Flow Reliability $\mathbb{P}(\text{MaxFlow} \ge D)$** | $\text{MaxFlow} \ge D \iff \bigwedge_{C} \bigwedge_{F \in \mathcal{F}_{\min}(C, D)} \bigvee_{e \in F} x_e$ | Strictly $\vert E \vert$ |
| **Theorem 9** | **Bounded-Diameter / Latency SLA $\mathbb{P}(\text{dist} \le L)$** | $\text{dist}(s, t) \le L \iff \bigwedge_{C \in \mathcal{C}_{\min}(s, t, L)} \bigvee_{e \in C} x_e$ | Strictly $\vert E \vert$ |
| **Theorem 10** | **Concurrent Multi-Commodity Capacitated Flow** | $\text{Flow} \ge \mathbf{d} \iff \bigwedge_{S: D(S)>0} \bigwedge_{F \in \mathcal{F}_{\min}(\Delta(S), D(S))} \bigvee_{e \in F} x_e$ | Strictly $\vert E \vert$ |
| **Theorem 11** | **Generalized Weibull Aging & Wear-Out MTTF** | $\text{MTTF} = \frac{\Gamma(1+1/\beta)}{\lambda} \sum \frac{c_k}{k^{1/\beta}}, \quad \mathbb{E}[T^r] = \frac{\Gamma(1+r/\beta)}{\lambda^r} \sum \frac{a_j}{j^{r/\beta}}$ | Closed-form $\mathbb{Z}[x]$ |
| **Theorem 12** | **Repairable System Markov Renewal Duality** | $\omega_{\text{sys}} = \sum I_B(e) \lambda_e A_e, \quad \text{MTBF} = \frac{A_{\text{sys}}}{\omega_{\text{sys}}}, \quad \text{MTTR} = \frac{U_{\text{sys}}}{\omega_{\text{sys}}}$ | Exact rational $\mathbb{Q}$ |
| **Theorem 13** | **Monotone Dual Enclosure & Certified Bounds** | $R_{\text{lower}}(\mathcal{P}') \le R(G) \le R_{\text{upper}}(\mathcal{C}'), \quad \Delta \to 0$ | Polynomial delay |

---

## 3. High-Performance Enterprise Architecture & SDK

SAT-Frontier includes an enterprise-grade reliability and SLA compliance engineering toolkit located in `sat_frontier/enterprise/`:

- **Universal Topology Importers** (`sat_frontier/enterprise/importers.py`): Zero-dependency importers supporting GraphML, GML, NetworkX/Cytoscape JSON, and CSV/TSV link inventories.
- **Enterprise Reliability Engine** (`sat_frontier/enterprise/engine.py`):
  - Two-Terminal SLA & N-Nines availability auditing (`audit_terminal_pair`).
  - Multi-Terminal $K$-Cut quorum auditing (`audit_multi_terminal`).
  - Network-wide pairwise SLA matrix, diameter reliability, and centrality (`audit_all_pairs`).
  - Closed-form reliability polynomial & percolation threshold ($p_c$) extraction (`audit_parametric_curve`).
  - Directed dicut reachability (`audit_directed_network`).
  - Shared-Risk Resource Group (SRRG) correlated failure auditing (`audit_srrg_reliability`).
  - Continuous exponential lifetime MTTF and $B_{10}$ warranty life (`audit_temporal_reliability`).
  - Continuous Weibull fatigue/wear-out aging MTTF & raw moments (`audit_weibull_reliability`).
  - Repairable system asymptotic failure frequency, MTBF, and MTTR (`audit_repairable_network`).
  - Certified any-time monotone lower and upper bounds (`audit_enclosure_bounds`).
  - Capacitated multi-unit flow reliability (`audit_capacitated_reliability`).
  - Bounded-hop / latency-constrained SLA reliability (`audit_bounded_latency`).
  - Concurrent multi-commodity demand satisfaction (`audit_multi_commodity_flow`).
- **Production CLI** (`python -m sat_frontier.enterprise.cli`): Command-line tool for automated CI/CD SLA compliance audits with markdown and JSON export.
- **Interactive Web Visualizer & REST Server** (`sat_frontier/enterprise/server.py`, `sat_frontier/enterprise/web/index.html`): Zero-dependency browser dashboard with SVG graph physics, real-time SLA metrics, Birnbaum criticality heatmaps, and dynamic continuous $R(t)$ lifetime curve plots.
- **Desktop Application Launcher** (`sat_frontier/enterprise/desktop.py`, `scripts/launch_dashboard.py`): Standalone cross-platform desktop runner with automatic dynamic port binding and browser integration.

---

## 4. Empirical Evidence Ledger (23 Suites, 2,870 Verified Runs)

All empirical runs are cryptographically sealed with SHA-256 instance digests, execution parameters, and independent verification checks:

| Suite Name | Hypothesis | Instances | Total Runs | Primary Evaluation Metric | Independent Verification |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `policy-train-v02` | H1–H3 | 48 | 384 | Search Nodes | Exhaustive Truth-Table |
| `policy-holdout-v02` | H3 | 120 | 1,200 | Speedup Ratio Gate | Held-out Truth-Table |
| `separator-study-001` | H4 | 16 | 160 | Component Splits | Exact Counter |
| `scaling-benchmark-001` | H1, H2 | 20 | 300 | Caching Ratio | Truth-Table ($n \le 18$) |
| `wmc-reliability-001` | H6 | 15 | 75 | Search Nodes | Closed-Form Analytic |
| `tensor-study-001` | H7 | 18 | 72 | Tensor Contraction | DPLL Exact WMC |
| `cut-wmc-001` | H9 | 24 | 48 | Hardness Cliff Resolution | Path-Based WMC |
| `cut-cube-001` | H8, H9 | 12 | 36 | Lookahead Depth ($d=2,4,6$) | Invariant Cross-Checks |
| `epyc-cube-001` | H8 | 14 | 98 | 1..32 Cores Scaling | Cross-Depth Invariants |
| `epyc-cube-002` | H8 | 26 | 204 | 1..64 Cores Scaling (194M nodes) | Hardness Mapping |
| `commercial-benchmarks-001` | P0–P1 | 5 | 5 | Sub-second Production SLA | Closed-Form Analytic |
| `k-terminal-wmc-001` | H10 | 24 | 24 | Multi-Terminal WMC | Brute Force $K$-Oracle |
| `poly-wmc-001` | H11 | 24 | 24 | $\mathbb{Z}[x]$ Polynomial Coefficients | Brute Force Expansion |
| `dicut-wmc-001` | H12 | 24 | 24 | Directed Reachability ($s \leadsto t$) | Brute Force Di-Oracle |
| `mixed-wmc-001` | H13 | 24 | 24 | Node + Edge Failure WMC | Brute Force Mixed Oracle |
| `srrg-wmc-001` | H14 | 24 | 24 | Fate-Sharing Correlated Failure | Brute Force SRRG Oracle |
| `temporal-wmc-001` | H15 | 24 | 24 | Continuous Algebraic MTTF | Simpson Quadrature Rule |
| `capacitated-wmc-001` | H16 | 24 | 24 | Flow Demand $\mathbb{P}(\text{MaxFlow} \ge D)$ | Dinic Max-Flow Oracle |
| `bounded-hop-wmc-001` | H17 | 24 | 24 | Hop-Bounded $\mathbb{P}(\text{dist} \le L)$ | BFS Shortest-Path Oracle |
| `multi-commodity-wmc-001` | H18 | 24 | 24 | Concurrent Multi-Commodity Flow | Brute Force Multi-Oracle |
| `weibull-wmc-001` | H19 | 24 | 24 | Weibull Wear-Out MTTF Integration | Simpson Quadrature Rule |
| `repairable-wmc-001` | H20 | 24 | 24 | Failure Frequency $\omega_{\text{sys}}$, MTBF, MTTR | Markov Renewal Oracle |
| `enclosure-wmc-001` | H21 | 24 | 24 | Certified Interval Containment | Independent Exact Oracle |
| **TOTAL** | **23 Suites** | **617** | **2,870** | **Comprehensive Empirical Base** | **100% Cryptographic Match** |

---

## 5. Formal Lean 4 Verification

Core mathematical theorems are mechanized in pure Lean 4:

- [`lean/CutDuality.lean`](lean/CutDuality.lean): Formal verification of Menger cut duality (`dual_cut_menger_duality`).
- [`lean/AlgebraicReliability.lean`](lean/AlgebraicReliability.lean): Formal verification of Exact Algebraic MTTF Integration ($\int_0^\infty P(e^{-\lambda t}) dt = \sum_{k=1}^m \frac{c_k}{k \lambda}$).
- [`lean/MultiCommodityDuality.lean`](lean/MultiCommodityDuality.lean): Formal verification of Concurrent Multi-Commodity Cut Duality.
- [`lean/WeibullReliability.lean`](lean/WeibullReliability.lean): Formal verification of Polynomial Weibull Wear-Out Linearity and raw moments.
- [`lean/RepairableDuality.lean`](lean/RepairableDuality.lean): Formal verification of Repairable Renewal Availability Conservation ($A + U = 1$) and failure frequency positivity.
- [`lean/EnclosureDuality.lean`](lean/EnclosureDuality.lean): Formal verification of Monotone Clause Relaxation and Certified Enclosure Interval Non-Negativity.

---

## 6. Formal Audit of OpenAI's Claimed ETH Refutation

Milestone M1 mandated an independent formal audit of OpenAI's claimed subexponential SAT refutation (`openai/math`, commit `7ef5c0c`). Our audit identified:

1. **Target Specification**: The comparator challenge was located in `lean/ComparatorChallenges/SubexponentialSAT.lean`, targeting endpoint `SqrtLogSpace/Final.lean`.
2. **Resource Ceiling Blocker**: Elaborating `SqrtLogSpace/Final.lean` imports 3,091 transitive Lean modules. During compilation, the Lean 4 elaborator spawns unbounded worker processes, exhausting host memory and terminating with **Exit 137 (OOM / SIGKILL)** at **11.9 GB peak RSS**.
3. **Gating Algorithmic Extraction**: Because the upstream proof fails to complete kernel verification or emit `#print axioms`, Milestone M4 remains strictly gated. Documented in [`docs/ETH_AUDIT_V02.md`](docs/ETH_AUDIT_V02.md) and pinned in `evidence/eth-audit/continuation/lean_audit_blocker_2026-10-28.json`.

---

## 7. Quickstart & Verification Guide

### Prerequisites

Python 3.10+ (core runtime and test suite use Python standard library alone; NumPy/PyTorch are optional for tensor contractions).

### Running Unit Tests

```bash
python -m unittest discover -s tests -v
```

All 187 unit and metamorphic tests execute in ~14 seconds with 0 failures.

### Running Enterprise CLI Audits

```bash
# Two-terminal Cloud VPC audit with Birnbaum sensitivity indexing
python -m sat_frontier.enterprise.cli --demo-cloud

# Continuous Weibull wear-out aging MTTF & B10 useful life audit
python -m sat_frontier.enterprise.cli --demo-cloud --weibull --weibull-beta 2.0

# Repairable system Markov renewal failure frequency, MTBF, and MTTR audit
python -m sat_frontier.enterprise.cli --demo-cloud --repairable

# Any-time certified monotone dual enclosure bounding
python -m sat_frontier.enterprise.cli --demo-cloud --enclosure

# All-pairs transatlantic subsea optical mesh SLA matrix and ANSI heatmap
python -m sat_frontier.enterprise.cli --demo-subsea --all-pairs

# Export compliance Markdown and machine-readable JSON reports
python -m sat_frontier.enterprise.cli --demo-cloud --out-report audit.md --out-json audit.json
```

### Launching Interactive Web Dashboard

```bash
# Launch background server and open default browser automatically
python scripts/launch_dashboard.py

# Or launch directly via enterprise CLI flag
python -m sat_frontier.enterprise.cli --dashboard
```

### Cryptographic Evidence Verification

```bash
# Verify active 23-suite empirical evidence ledgers
python verify_all_evidence.py

# Verify individual research campaigns
python verify_evidence.py evidence/weibull-wmc-001
python verify_evidence.py evidence/repairable-wmc-001
python verify_evidence.py evidence/enclosure-wmc-001
python verify_evidence.py evidence/multi-commodity-wmc-001
python verify_evidence.py evidence/bounded-hop-wmc-001
python verify_evidence.py evidence/capacitated-wmc-001
```

---

## 8. Repository Documentation Index

- **Academic Monograph & Publication Manuscript**:
  - [`docs/RESEARCH_PAPERS/SAT_FRONTIER_UNIFIED_DUALITY.md`](docs/RESEARCH_PAPERS/SAT_FRONTIER_UNIFIED_DUALITY.md): Comprehensive research paper unifying the Thirteen Dual Cut Theorems.
  - [`docs/RESEARCH_PAPERS/SAT_FRONTIER_UNIFIED_DUALITY.tex`](docs/RESEARCH_PAPERS/SAT_FRONTIER_UNIFIED_DUALITY.tex): Publication-grade IEEEtran manuscript.
- **Master Reports & Project Status**:
  - [`docs/RESULTS.md`](docs/RESULTS.md): Master empirical results report across 23 suites and 21 hypotheses.
  - [`docs/MILESTONES.md`](docs/MILESTONES.md): Milestone progression ledger (M0 through M5 and releases v0.1 through v0.2.9).
  - [`RESUME.md`](RESUME.md): Standalone operational checkpoint and replication directive.
  - [`TASK_STATE.json`](TASK_STATE.json): Machine-readable project state schema.
  - [`artifacts/release/README.md`](artifacts/release/README.md): Official release archive ledger and SHA-256 provenance.
- **Enterprise & Technical Guides**:
  - [`docs/ENTERPRISE_SDK_GUIDE.md`](docs/ENTERPRISE_SDK_GUIDE.md): Developer quickstart and CI/CD integration guide.
  - [`docs/SLA_AUDIT_SPECIFICATION.md`](docs/SLA_AUDIT_SPECIFICATION.md): Mathematical audit specification and regulatory compliance standards.
  - [`docs/COMMERCIAL_APPLICATIONS.md`](docs/COMMERCIAL_APPLICATIONS.md): Commercial monetization and industry deployments.
- **Research Campaign Reports & Preregistrations**:
  - [`docs/WEIBULL_RELIABILITY_REPORT.md`](docs/WEIBULL_RELIABILITY_REPORT.md) & [`docs/WEIBULL_RELIABILITY_PREREGISTRATION.md`](docs/WEIBULL_RELIABILITY_PREREGISTRATION.md) (H19)
  - [`docs/REPAIRABLE_RELIABILITY_REPORT.md`](docs/REPAIRABLE_RELIABILITY_REPORT.md) & [`docs/REPAIRABLE_RELIABILITY_PREREGISTRATION.md`](docs/REPAIRABLE_RELIABILITY_PREREGISTRATION.md) (H20)
  - [`docs/ENCLOSURE_BOUNDING_REPORT.md`](docs/ENCLOSURE_BOUNDING_REPORT.md) & [`docs/ENCLOSURE_BOUNDING_PREREGISTRATION.md`](docs/ENCLOSURE_BOUNDING_PREREGISTRATION.md) (H21)
  - [`docs/MULTI_COMMODITY_REPORT.md`](docs/MULTI_COMMODITY_REPORT.md) & [`docs/MULTI_COMMODITY_PREREGISTRATION.md`](docs/MULTI_COMMODITY_PREREGISTRATION.md) (H18)
  - [`docs/BOUNDED_HOP_REPORT.md`](docs/BOUNDED_HOP_REPORT.md) & [`docs/BOUNDED_HOP_PREREGISTRATION.md`](docs/BOUNDED_HOP_PREREGISTRATION.md) (H17)
  - [`docs/CAPACITATED_RELIABILITY_REPORT.md`](docs/CAPACITATED_RELIABILITY_REPORT.md) & [`docs/CAPACITATED_RELIABILITY_PREREGISTRATION.md`](docs/CAPACITATED_RELIABILITY_PREREGISTRATION.md) (H16)
  - [`docs/TEMPORAL_RELIABILITY_REPORT.md`](docs/TEMPORAL_RELIABILITY_REPORT.md) & [`docs/TEMPORAL_RELIABILITY_PREREGISTRATION.md`](docs/TEMPORAL_RELIABILITY_PREREGISTRATION.md) (H15)
  - [`docs/SRRG_RELIABILITY_REPORT.md`](docs/SRRG_RELIABILITY_REPORT.md) & [`docs/SRRG_RELIABILITY_PREREGISTRATION.md`](docs/SRRG_RELIABILITY_PREREGISTRATION.md) (H14)
  - [`docs/MIXED_RELIABILITY_REPORT.md`](docs/MIXED_RELIABILITY_REPORT.md) & [`docs/MIXED_RELIABILITY_PREREGISTRATION.md`](docs/MIXED_RELIABILITY_PREREGISTRATION.md) (H13)
  - [`docs/DICUT_RELIABILITY_REPORT.md`](docs/DICUT_RELIABILITY_REPORT.md) & [`docs/DICUT_RELIABILITY_PREREGISTRATION.md`](docs/DICUT_RELIABILITY_PREREGISTRATION.md) (H12)
  - [`docs/POLYNOMIAL_WMC_REPORT.md`](docs/POLYNOMIAL_WMC_REPORT.md) & [`docs/POLYNOMIAL_WMC_PREREGISTRATION.md`](docs/POLYNOMIAL_WMC_PREREGISTRATION.md) (H11)
  - [`docs/K_TERMINAL_REPORT.md`](docs/K_TERMINAL_REPORT.md) & [`docs/K_TERMINAL_PREREGISTRATION.md`](docs/K_TERMINAL_PREREGISTRATION.md) (H10)
  - [`docs/CUT_COMPILATION_REPORT.md`](docs/CUT_COMPILATION_REPORT.md) (H9)
  - [`docs/EPYC_SCALING_REPORT.md`](docs/EPYC_SCALING_REPORT.md) (H8)
  - [`docs/TENSOR_CONTRACTION_REPORT.md`](docs/TENSOR_CONTRACTION_REPORT.md) & [`docs/TENSOR_CONTRACTION_PREREGISTRATION.md`](docs/TENSOR_CONTRACTION_PREREGISTRATION.md) (H7)
  - [`docs/WMC_RELIABILITY_REPORT.md`](docs/WMC_RELIABILITY_REPORT.md) & [`docs/WMC_RELIABILITY_PREREGISTRATION.md`](docs/WMC_RELIABILITY_PREREGISTRATION.md) (H6)
  - [`docs/SEPARATOR_REPORT.md`](docs/SEPARATOR_REPORT.md) (H4)
  - [`docs/POLICY_HOLDOUT_REPORT.md`](docs/POLICY_HOLDOUT_REPORT.md) (H3)
  - [`docs/POLICY_TRAIN_REPORT.md`](docs/POLICY_TRAIN_REPORT.md) (H1–H3)
  - [`docs/SCALING_REPORT.md`](docs/SCALING_REPORT.md) (H1, H2)
  - [`docs/COMMERCIAL_BENCHMARKS_REPORT.md`](docs/COMMERCIAL_BENCHMARKS_REPORT.md) (P0–P1)
  - [`docs/ETH_AUDIT_V02.md`](docs/ETH_AUDIT_V02.md) (M1 Audit)
