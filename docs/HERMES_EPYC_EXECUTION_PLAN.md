# Hermes & AMD EPYC Execution Plan: Scaled Exact Counting & WMC

**Generated Date**: 2026-10-28  
**Target Systems**: High-Core AMD EPYC Server (e.g., 64–128 Cores, 256 GB–1 TB+ RAM) & GPU Acceleration  
**Related Milestones**: Milestone M1 (Lean Audit Continuation), Milestone M4 (Algorithmic Extraction), Milestone M5 (Useful Transfer Scale-Up)

---

## 1. Executive Summary & Purpose

The `SAT-Frontier` repository has completed local verification across Milestones M0, M1 (blocker recorded), M2, M3 (1,200-run held-out evaluation), H4 (graph separators), scaling benchmarks ($n=12..20$), and M5 (Weighted Model Counting for Network Reliability).

On standard workstations, two primary ceilings emerge:
1. **Memory Ceiling on Formal Audit**: Compiling the 3,091 upstream Lean 4 modules in `openai/math` spawned 15 compiler processes, peaked at **11.9 GB RSS**, and was terminated by container/cgroup limits.
2. **Search Tree Scalability on Industrial Instances**: While component decomposition solves $k=5$ modular networks in 0.018 seconds, larger benchmarks ($k \ge 8$ or $n \ge 40$) benefit from massive parallel lookahead partitioning (**Cube-and-Conquer**).

This document provides the turnkey instructions for executing high-core AMD EPYC and GPU compute workloads via Hermes.

---

## 2. Track 1: AMD EPYC High-Core Cube-and-Conquer Campaign

Exact counting and Weighted Model Counting are **100% associative and commutative**:
$$\text{WMC}(\Phi) = \sum_{i=1}^{2^d} \text{WMC}(\Phi \land \text{cube}_i)$$
Subproblems require **zero inter-worker communication**, providing near-linear parallel scaling across 64–128 EPYC threads.

### A. Environment Setup
```bash
# Clone and enter SAT-Frontier
cd /workspace/SAT-Frontier

# Verify environment and test suite
python3 -m unittest discover -s tests -v

# Ensure numactl is installed for memory affinity
sudo apt-get update && sudo apt-get install -y numactl
```

### B. Execution Commands

#### 1. Network Reliability & Fault Tree Scale-Up
Run parallel Cube-and-Conquer across all available EPYC cores on large modular networks ($k=6, 8, 10$):

```bash
# EPYC run with depth 6 (64 cubes) or depth 7 (128 cubes)
python3 -m sat_frontier.epyc_runner \
  path/to/large_network.cnf \
  --depth 6 \
  --workers 64 \
  --seconds-per-cube 30.0 \
  --max-nodes-per-cube 200000 \
  --out /workspace/SAT-Frontier/evidence/epyc-cube-001/results_k8.json
```

#### 2. Industrial Model Counting Competition Benchmarks (MC2022/MC2023)
Download canonical unweighted/weighted instances from the Model Counting Competition track:
```bash
# Run with NUMA node interleave for maximum DDR5 bandwidth
numactl --interleave=all python3 -m sat_frontier.epyc_runner \
  benchmarks/track2_wmc/instance_042.cnf \
  --depth 7 \
  --workers 128 \
  --algo combined_wmc \
  --seconds-per-cube 60.0 \
  --out /workspace/SAT-Frontier/evidence/epyc-cube-001/mc_instance_042.json
```

---

## 3. Track 2: Upstream ETH Lean 4 Formal Verification Audit

To resolve Milestone M1 by completing the build and executing `#print axioms`:

### A. System Requirements
- Dedicated AMD EPYC node with at least **32 GB available RAM**.
- Lean toolchain `leanprover/lean4:v4.34.1`.

### B. Step-by-Step Execution
```bash
# 1. Navigate to isolated scratch clone
cd /home/scott/.hermes/cache/scratch/openai-math-eth-audit/lean

# 2. Set single-core or bounded multi-core Lake build
export LEAN_NUM_THREADS=4
export TMPDIR=/tmp/lean_audit_scratch
mkdir -p "$TMPDIR"

# 3. Build target solution module with high memory allowance
# (Lake will not hit the 11.9 GB ceiling on an EPYC system with 128GB+ RAM)
timeout 3600 lake build OAI.Algorithms.SubexponentialSAT.Main

# 4. Once Main.olean is built, extract the exact kernel axioms:
lake env lean --run - << 'EOF'
import OAI.Algorithms.SubexponentialSAT.Main
#print axioms OAI.Algorithms.SubexponentialSAT.SqrtLogSpace.exact_count_and_sat
EOF
```

### C. Acceptance Criteria for Milestone M1 Closure
- If `#print axioms` outputs: `['propext', 'Quot.sound', 'Classical.choice']`, the proof relies only on standard Lean foundational axioms (no `sorryAx`).
- Record the stdout to `/workspace/SAT-Frontier/evidence/eth-audit/continuation/epyc_axioms.log`.

---

## 4. Track 3: GPU Tensor-Network Prototype (Preparation)

For dense sub-components identified by EPYC's graph separator:
- Map dense Boolean clauses to 0/1 indicator tensors.
- Use `opt_einsum` or `cuTENSOR` on NVIDIA GPUs (e.g., A100 / H100):
```python
import opt_einsum as oe
import torch

# Contract tensor network representing dense sub-circuit
# Path optimizer: 'greedy' or 'kahypar' for low-treewidth networks
def contract_dense_kernel(tensors, equation):
    return oe.contract(equation, *tensors, backend='torch')
```

---

## 5. Scientific Integrity & Data Protocols

In accordance with [`AGENTS.md`](../AGENTS.md) and [`docs/RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md):
1. **Evidence Separation**: All EPYC runs must be written to a fresh directory:
   `evidence/epyc-cube-001/`
2. **CPU vs GPU Distinction**: CPU Cube-and-Conquer outputs and GPU tensor contraction benchmarks must be cataloged in distinct evidence subdirectories.
3. **Immutability & Checkpoints**: Generate `manifest.json` with SHA-256 digests of all instances and configurations upon completion.
4. **No External Publication Without Approval**: Keep results local; do not push to public repositories or commit automated claims until formally reviewed.

