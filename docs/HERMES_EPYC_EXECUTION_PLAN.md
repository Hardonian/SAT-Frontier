# Hermes & AMD EPYC Execution Plan: Scaled Exact Counting & WMC

**Generated Date**: 2026-10-28  
**Target Systems**: High-Core AMD EPYC Server (64 Cores / 128 Threads, 168 GB DDR4 RAM, 3x GPUs: V100-SXM2, Tesla P40, RTX 3060)  
**Related Milestones**: Milestone M1 (Lean Audit Continuation), Milestone M4 (Algorithmic Extraction), Milestone M5 (Useful Transfer Scale-Up)  
**Execution Status**: **Track 1 Completed & Verified** (302 EPYC runs, 194M search nodes); **Track 2 Blocker Pinned** (`evidence/eth-audit/continuation/lean_audit_blocker_2026-10-28.json`); **Track 3 CPU Verified** (`evidence/tensor-study-001/`).

---

## 1. Executive Summary & Accomplishments

The high-core compute workloads on the 64-core AMD EPYC server (168 GB RAM) via Hermes have completed with full mathematical verification:

1. **Track 1: High-Core Cube-and-Conquer Campaign**:
   - **Runs Evaluated**: 302 total runs (98 in `evidence/epyc-cube-001/`, 204 in `evidence/epyc-cube-002/`).
   - **Search Nodes Explored**: **194,165,819 nodes**.
   - **Throughput & Scaling**: On `grid_3x6_mod`, increasing cube lookahead depth from $d=4$ to $d=8$ with 64 workers accelerated wall-clock time from 59.36s to 26.23s (**2.26x speedup**), maintaining 100% exact rational weight invariance (`484992228090957506024017833/500000000000000000000000000`).
   - On `grid_4x4_mod`, Cube-and-Conquer successfully completed up to **depth 17** ($2^{17} = 131,072$ cubes) at 478 cubes/second, exploring 29,555,959 nodes before encountering the timeout ceiling at depth 18.
   - **Topological Hardness Gradient Mapped**: Full scaling map across $1\times N$, $2\times N$, $3\times N$, $4\times N$, $5\times 5$, and barbell networks documented in [`evidence/epyc-cube-002/SCALING_SUMMARY.md`](../evidence/epyc-cube-002/SCALING_SUMMARY.md).
   - **Cryptographic & Invariant Verification**: All runs verified by [`verify_epyc_evidence.py`](../verify_epyc_evidence.py).

2. **Track 2: Upstream ETH Lean 4 Formal Audit Continuation**:
   - Exact failure signature pinned in [`evidence/eth-audit/continuation/lean_audit_blocker_2026-10-28.json`](../evidence/eth-audit/continuation/lean_audit_blocker_2026-10-28.json): 3,091 transitive modules in `openai/math` spawn 15 concurrent compiler processes, peak at 11.9 GB RSS, and terminate with exit 137 / timeout before kernel verification or `#print axioms`. Milestone M1 closed with formal blocker; downstream M4 extraction gated.
   - Turnkey bounded concurrency script provided: [`scripts/run_lean4_audit.sh`](../scripts/run_lean4_audit.sh) with [`scripts/extract_axioms.lean`](../scripts/extract_axioms.lean).

3. **Track 3: Tensor Network Contraction & Dual Cut Compilation**:
   - Evaluated 72 runs across 18 instances in `evidence/tensor-study-001/` with 100% exact oracle agreement. Heuristic min-degree bucket elimination demonstrated a 6.2x median speedup over global einsum optimization.
   - Implemented Dual Cut-Based CNF compilation (`to_cut_cnf`) in [`sat_frontier/reliability.py`](../sat_frontier/reliability.py), replacing path enumeration ($O(2^{|V|})$ auxiliary variables) with minimal cut constraints on edge variables alone, reducing search nodes by **>6.4x**.

---

## 2. Hardness Gradient Map & Structural Findings

The empirical findings from `evidence/epyc-cube-002/SCALING_SUMMARY.md`:

| Topology | Instances | Tracked Depths | Status & Hardness Boundary | Structural Root Cause |
| :--- | :--- | :--- | :--- | :--- |
| **$1 \times N$ Paths** | $1\times 5 .. 1\times 20$ | $d=10$ | **EXACT (trivial)**, <0.2s | Treewidth 1; no cycle interference |
| **$2 \times N$ Ladders** | $2\times 5 .. 2\times 10$ | $d=5 .. 13$ | **EXACT**, tractable up to $2\times 10$ ($d=13$, 13.2M nodes) | Treewidth 2; tractable lookahead |
| | $2\times 11, 2\times 12$ | $d=1 .. 8$ | **UNKNOWN (structural cliff)** | Dense hypergraph path enumeration (>16k clauses) |
| **$3 \times N$ Meshes** | $3\times 3 .. 3\times 6$ | $d=4 .. 8$ | **EXACT** with 600s budget ($d=8$, 5.2M nodes, 26s) | Solvable via high-core lookahead decomposition |
| | $3\times 7, 3\times 8$ | $d=1 .. 4$ | **UNKNOWN (structural cliff)** | Exponential path blowup (1,401 vars, 20,430 clauses) |
| **$4 \times N$ Grids** | $4\times 3, 4\times 4$ | $d=5 .. 17$ | **EXACT** up to $d=17$ (29.6M nodes, 274s, 478 cubes/s) | Depth lookahead scales linearly until $d=18$ timeout |
| | $4\times 5$ | $d=4$ | **UNKNOWN (hard)** | 14,109 clauses |
| **$5 \times 5$ Mesh** | $5\times 5$ | $d=2$ | **UNKNOWN (intractable)** | 8,552 variables, 156,945 clauses |
| **Barbell** | $k=6$ | $d=5 .. 8$ | **EXACT** (<0.2s) | Cut-edge bridge partitions components instantly |
| | $k=8, k=10$ | $d=4 .. 5$ | **UNKNOWN / gen timeout** | Intra-cluster path cross-products |

---

## 3. Recommended Next Compute Runs for Hermes & EPYC

1. **High-Core Cube Scaling on Dual Cut Hardness Boundary Instances**:
   - The Dual Cut compiler (`sat_frontier/cut_compiler.py`) has been verified in `evidence/cut-wmc-001/`, eliminating auxiliary path variables and reducing search nodes by up to 122x (solving `grid_3x7` in 2.13s and `grid_2x11` in 0.12s).
   - Deploy high-core Cube-and-Conquer lookahead on the cut CNFs across the 64-core AMD EPYC server:
     ```bash
     python scripts/run_epyc_batch.py \
       --evidence-dir evidence/epyc-cube-003 \
       --instances-dir evidence/cut-wmc-001/instances \
       --workers 64 \
       --depths 4 6 8
     ```
   - This tests whether high-core parallel lookahead combines multiplicatively with monotone cut pruning on large topologies ($3\times 8$, $4\times 5$, $5\times 5$).

2. **Upstream Lean 4 Kernel Audit with Bounded Concurrency (Track 2)**:
   - On the 168 GB DDR4 EPYC host, execute the bounded concurrency audit to resolve the multi-process memory ceiling blocker:
     ```bash
     bash scripts/run_lean4_audit.sh 4
     ```
   - If build succeeds, run the axiom extractor:
     ```bash
     lake env lean scripts/extract_axioms.lean
     ```

3. **GPU Tensor Network Acceleration on NVIDIA V100 / RTX 3060 (Track 3)**:
   - The host contains an NVIDIA V100-SXM2 (16 GB) and RTX 3060 (12 GB).
   - Run PyTorch GPU tensor contraction on the cut-compiled formulas:
     ```bash
     python -c "
     import sat_frontier.tensor_contract as tc
     from sat_frontier.core import parse_dimacs
     from pathlib import Path

     for cnf in Path('evidence/cut-wmc-001/instances').glob('*.cnf'):
         f, _ = parse_dimacs(cnf.read_text())
         res = tc.tensor_solve(f, backend='torch', device='cuda', mode='bucket_elimination')
         print(f'{cnf.stem}: {res}')
     "
     ```
   - Save all GPU outputs to a fresh, distinct directory `evidence/gpu-tensor-001/` strictly adhering to `AGENTS.md`.

4. **Automated Verification**:
   - Re-verify all empirical evidence anytime using:
     ```bash
     python verify_epyc_evidence.py evidence/epyc-cube-001 evidence/epyc-cube-002
     python verify_evidence.py evidence/cut-wmc-001
     ```
     ```bash
     python verify_epyc_evidence.py
     ```
