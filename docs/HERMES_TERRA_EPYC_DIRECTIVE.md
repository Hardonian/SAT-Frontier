# Hermes Commission & Execution Directive: SAT-Frontier on High-Core AMD EPYC

**Agent Target**: Hermes Agent powered by **OpenAI GPT-6.1 Terra**  
**Host Architecture**: 64-Core AMD EPYC Server (128 Execution Contexts, 168 GB DDR4 RAM, Multi-NUMA)  
**Remote Repository**: [`https://github.com/Hardonian/SAT-Frontier.git`](https://github.com/Hardonian/SAT-Frontier.git)  
**Target Branch**: `main`  
**Baseline Milestone**: **Release v0.2.6** (Commit `c55cd02` / `9fe49db`)  
**Verified Evidence Baseline**: **16 Empirical Suites | 2,702 Verified Runs | 118 Passing Unit Tests**

---

## 1. Executive Mission & Role Definition

You are **Hermes**, operating with **OpenAI GPT-6.1 Terra** as your reasoning and code-execution engine. You are deployed on the 64-core AMD EPYC server to execute, scale, and formally verify the next frontier of exact #SAT and Weighted Model Counting (WMC) network reliability algorithms for `SAT-Frontier`.

### Primary Objectives:
1. **Synchronize & Verify Live State**: Pull the authoritative repository state directly from the GitHub remote (`origin/main`), assert complete cryptographic integrity across all 16 existing evidence suites (2,702 runs) and 118 unit tests.
2. **Execute Frontier High-Core EPYC Cut Scaling Campaign (`epyc-cut-001`)**: Run high-concurrency Cube-and-Conquer lookahead across up to 64 workers on the 10 pre-compiled cut-compiled frontier topologies (`grid_3x8..3x11`, `grid_4x5..4x7`, `grid_5x5`, `barbell_6_3_6`, `chvatal`).
3. **Assert Cross-Depth Mathematical Invariance**: Verify 100% exact rational weight equality (`Fraction`) across depths $d \in \{4, 6, 8\}$, proving that lookahead partitioning preserves mathematical truth while unlocking super-linear parallel pruning.
4. **Advance Milestone M1 Upstream Lean 4 Audit**: Execute the bounded-concurrency formal kernel verification on the 168 GB RAM host to isolate the transitive dependency memory ceiling.

---

## 2. Theoretical Review & Frontier Context

The `SAT-Frontier` laboratory has established a rigorous foundation across 14 preregistered hypotheses. Hermes must understand the theoretical breakthroughs achieved prior to launching EPYC compute:

### A. The Duality Revolution: Cut Compilation vs. Path Enumeration
In network infrastructure reliability, classical formulations enumerate simple paths (DNF), requiring $O(2^{|V|})$ auxiliary routing indicators and exponential flow-conservation clauses in CNF. This creates a severe **topological hardness cliff**:
- In `evidence/epyc-cube-002/`, path-based CNFs stalled completely at `grid_2x11`, `grid_3x7`, and `grid_4x4` (exhausting 194 million search nodes across 64 workers).
- **Hypothesis H9 (Dual Cut-Based Monotone CNF Duality)** proved that network connectivity is logically equivalent to the simultaneous survival of all inclusion-minimal $s-t$ cuts:
  $$\Phi_{\text{cut}}(G, s, t) = \bigwedge_{C \in \mathcal{C}_{\text{min}}(s, t)} \left( \bigvee_{e \in C} x_e \right)$$
  This formulation uses **strictly $|E|$ variables, zero auxiliary variables, and zero MTZ subtour elimination bloat**.
- In `evidence/cut-wmc-001/`, Dual Cut compilation shattered the hardness cliff: `grid_3x7` solved in **2.13 seconds** (from >600s timeout) and `grid_2x11` solved in **0.12 seconds** with 0 rational weight mismatches.

### B. Generalization Across Topologies & Failure Modes (H10 – H14)
1. **Multi-Terminal / All-Terminal Reliability (H10)**: Generalized Menger cut duality in `sat_frontier/k_cut_compiler.py` to $K \ge 2$ terminal subsets without Steiner tree enumeration. Solved multi-terminal `grid_4x4` in 0.39s (17/17 oracle matches).
2. **Algebraic Model Counting over $\mathbb{Z}[x]$ (H11)**: Evaluates complete closed-form reliability polynomials $P(x) = \sum c_k x^k$ and finite-size percolation phase transitions $p_c$ in a single DPLL search pass in `sat_frontier/poly_wmc.py`. Solved `grid_4x5` (degree 31, 1,353 clauses) in 2.05s (17/17 oracle matches).
3. **Directed Dicut Duality (H12)**: Solves directed two-terminal reachability ($s \leadsto t$) in cyclic networks in `sat_frontier/dicut_compiler.py` over minimal dicuts with strictly $|A|$ variables (18/18 oracle matches).
4. **Mixed Node-and-Edge Reliability (H13)**: Unifies simultaneous, independent vertex failures ($q_v$) and edge failures ($p_e$) in `sat_frontier/mixed_cut_compiler.py`. Internal node-splitting $v \mapsto (v_{\text{in}}, v_{\text{out}})$ maps physical mixed cuts into directed cuts in split graph $G^*$ with strictly $|V_{\text{internal}}| + |E|$ variables (16/16 oracle matches).
5. **Shared-Risk Resource Groups (SRRG / Fate-Sharing) (H14)**: Solves correlated multi-link failures in `sat_frontier/srrg_compiler.py` where physical edges share conduits, sheaths, or availability zone circuits. Formulates minimal SRRG hitting-set cuts over risk variables $|\mathcal{R}|$ alone (22/22 oracle matches, sub-0.15ms latency).
6. **All-Pairs SLA Matrix & Centrality Engine**: Evaluates all $\binom{|V|}{2}$ pairs simultaneously in `sat_frontier/enterprise/all_pairs.py`, computing Network Diameter Reliability ($R_{\text{min}}$) and failure-aware node centrality $C_R(v)$.

---

## 3. Remote Synchronization & Environment Setup

On the AMD EPYC server, initialize a clean workspace tracking the official GitHub remote:

```bash
# 1. Clone or pull latest main branch from GitHub remote
git clone https://github.com/Hardonian/SAT-Frontier.git
cd SAT-Frontier
git fetch origin main
git checkout main
git pull origin main

# Assert HEAD commit matches v0.2.6 baseline
git log -n 1 --oneline
# Expected: c55cd02 (or latest main commit)

# 2. Inspect CPU, Core Topology, and RAM
lscpu | grep -E "Model name|CPU\(s\):|Thread\(s\) per core:|NUMA node\(s\):"
free -h

# 3. Verify Python 3.10+ Environment & Dependencies
python3 --version
python3 -m unittest discover -s tests -v

# 4. Run Unified Master Evidence Verifier
# MUST pass 16/16 suites (2,702 runs) before modifying or launching experiments!
python3 verify_all_evidence.py
```

---

## 4. Execution Plan: Track 1 (High-Core EPYC Cut Campaign)

### Benchmark Suite Overview (`instances/epyc-cut-frontier/`)
The 10 frontier benchmark formulas have been pre-compiled and cryptographically hashed:
- `grid_3x8.cnf` (37 vars, 1,973 clauses)
- `grid_3x9.cnf` (42 vars, 4,082 clauses)
- `grid_3x10.cnf` (47 vars, 8,351 clauses)
- `grid_3x11.cnf` (52 vars, 16,954 clauses)
- `grid_4x5.cnf` (31 vars, 1,353 clauses)
- `grid_4x6.cnf` (38 vars, 5,024 clauses)
- `grid_4x7.cnf` (45 vars, 18,187 clauses)
- `grid_5x5.cnf` (40 vars, 8,742 clauses)
- `barbell_6_3_6.cnf` (31 vars, 33 clauses)
- `chvatal.cnf` (23 vars, 539 clauses)

### Execution Protocol

#### A. Automated Turnkey Launcher (Recommended)
```bash
chmod +x scripts/run_epyc_cut_campaign.sh
./scripts/run_epyc_cut_campaign.sh
```

#### B. Direct Python Execution with 64 Workers and Multi-NUMA Binding
On Linux AMD EPYC with multiple NUMA nodes, always execute with `numactl --interleave=all` to eliminate memory bus starvation:

```bash
numactl --interleave=all python3 scripts/run_epyc_cut_campaign.py \
    --workers 64 \
    --depths 4 6 8 \
    --seconds-per-cube 30.0 \
    --max-nodes-per-cube 200000 \
    --evidence-dir evidence/epyc-cut-001
```

### Safety & Fault Tolerance Features
1. **Durable Per-Cube Checkpointing**:
   - Intermediate results are saved under `evidence/epyc-cut-001/checkpoints/<instance>_d<depth>/`.
   - If preempted or interrupted, re-running the script resumes exactly from the last completed cube.
2. **Cross-Depth Exact Rational Invariant Assertion**:
   - For every instance completed at multiple depths (e.g., $d=4, 6, 8$), the runner enforces `wf_d4 == wf_d6 == wf_d8` with exact rational equality (`Fraction`). Any discrepancy triggers an immediate fatal assertion error.
3. **Cryptographic Ledger**:
   - Generates `evidence/epyc-cut-001/runs.csv`, `runs.jsonl`, `summary.json`, `manifest.json`, and `SHA256SUMS`.
4. **Verification**:
   ```bash
   python3 verify_evidence.py evidence/epyc-cut-001
   ```

---

## 5. Execution Plan: Track 2 (Upstream ETH Lean 4 Formal Audit)

Milestone M1 established that `openai/math` commit `7ef5c0c` contains 3,091 transitive Lean modules that exhaust typical memory ceilings (pinned in `evidence/eth-audit/continuation/lean_audit_blocker_2026-10-28.json`). On the 168 GB RAM EPYC server, Hermes can resolve this blocker using bounded concurrency:

```bash
# Execute Lean 4 build with capped parallel workers (e.g. 4 workers)
bash scripts/run_lean4_audit.sh 4

# If the comparator endpoint builds successfully, extract the axiom list:
lake env lean scripts/extract_axioms.lean
```

---

## 6. Strict Research Rules for Hermes (AGENTS.md)

1. **Zero Relabeling of Unknowns**: Never label a timed-out, node-limited, or incomplete run as UNSAT or zero probability. Incomplete runs must remain recorded as `status: "unknown"` with exact incomplete cube counts.
2. **Strict Evidence Isolation**: All outputs from new campaigns must be written into a fresh, dedicated directory (e.g. `evidence/epyc-cut-001/`). Never overwrite existing evidence directories.
3. **Hardware Evidence Segregation**: Keep CPU and GPU evidence strictly distinct. Never mix CUDA tensor metrics into CPU verification manifests.
4. **Preserve Historical Source Hashes**: Do not alter line endings, trailing spaces, or imports in historical files (`pyproject.toml`, `sat_frontier/core.py`, `sat_frontier/reliability.py`, `sat_frontier/wmc.py`, `sat_frontier/cut_compiler.py`, etc.).
5. **No External Paid Services**: All compute must be performed locally on the host server; no cloud GPU rental or unauthorized external publication.
6. **Update Checkpoints**: Update `TASK_STATE.json` and `RESUME.md` upon completion of the campaign.
