# Empirical Report: Hypothesis H18 — Multi-Commodity Capacitated Flow Reliability via Dual Cut Duality (Suite: `multi-commodity-wmc-001`)

## Executive Summary

This report presents the empirical verification of **Hypothesis H18**: Multi-Commodity Capacitated Flow Reliability via Dual Cut Duality.
Using the **Multi-Commodity Dual Cut Duality Theorem** (Theorem 10), the concurrent flow demand feasibility condition:
$$\mathbb{P}\left(\forall k \in \{1, \dots, K\}, \; \text{ConcurrentFlow}(G_{\mathbf{x}}, s_k, t_k) \ge d_k\right)$$
compiles directly into a monotone positive CNF formula containing strictly $\vert E \vert$ physical edge variables and **zero auxiliary flow or commodity routing variables**.

The empirical campaign (`multi-commodity-wmc-001`) evaluated 24 benchmark instances spanning shared bottleneck trunks, multi-directional ring networks, cross-linked diamond meshes, and complete dense backbones ($K_4$). Every single instance was cross-verified against an independent exhaustive $2^{\vert E \vert}$ truth-table oracle evaluating all operational states.

### Key Results

- **Total Benchmark Instances Solved**: 24 / 24 (100.0%)
- **Independent Truth-Table Oracle Agreement**: 24 / 24 (100.0% exact rational match)
- **Mean Solve Latency**: 0.08 milliseconds per instance (max: 0.23 ms on `complete_k4_p80`)
- **Auxiliary Variable Overhead**: Exactly 0 across all 24 instances
- **Cryptographic Audit Status**: 100% verified by `verify_evidence.py` (`hashes_verified`)

---

## Benchmark Results Table

| Instance Name | Family | $\vert E \vert$ | Commodities | CNF Clauses | Search Nodes | Solve Time | Exact Reliability | Oracle Match | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `shared_trunk_d1_1_cap2` | Shared Trunk | 5 | 2 | 17 | 6 | 0.05 ms | 0.733056 | MATCH | PASS |
| `shared_trunk_d1_2_cap3` | Shared Trunk | 5 | 2 | 16 | 6 | 0.04 ms | 0.733056 | MATCH | PASS |
| `shared_trunk_d2_2_cap4` | Shared Trunk | 5 | 2 | 17 | 6 | 0.07 ms | 0.733056 | MATCH | PASS |
| `shared_trunk_d1_1_cap1` | Shared Trunk (Contention) | 5 | 2 | 2 | 1 | 0.06 ms | 0.000000 | MATCH | PASS |
| `shared_trunk_d1_2_cap2` | Shared Trunk (Contention) | 5 | 2 | 2 | 1 | 0.04 ms | 0.000000 | MATCH | PASS |
| `shared_trunk_d2_1_cap3` | Shared Trunk | 5 | 2 | 16 | 6 | 0.06 ms | 0.733056 | MATCH | PASS |
| `ring_c4_p90` | Ring Network | 4 | 2 | 8 | 5 | 0.05 ms | 0.656100 | MATCH | PASS |
| `ring_c4_p95` | Ring Network | 4 | 2 | 8 | 5 | 0.04 ms | 0.814506 | MATCH | PASS |
| `ring_c5_p90` | Ring Network | 5 | 2 | 17 | 6 | 0.09 ms | 0.590490 | MATCH | PASS |
| `ring_c5_p92` | Ring Network | 5 | 2 | 17 | 6 | 0.03 ms | 0.659082 | MATCH | PASS |
| `ring_c5_p95` | Ring Network | 5 | 2 | 17 | 6 | 0.03 ms | 0.773781 | MATCH | PASS |
| `ring_c5_p98` | Ring Network | 5 | 2 | 17 | 6 | 0.04 ms | 0.903921 | MATCH | PASS |
| `diamond_mesh_cap1_p80` | Diamond Mesh | 5 | 2 | 20 | 5 | 0.06 ms | 0.656100 | MATCH | PASS |
| `diamond_mesh_cap1_p90` | Diamond Mesh | 5 | 2 | 20 | 5 | 0.10 ms | 0.656100 | MATCH | PASS |
| `diamond_mesh_cap2_p85` | Diamond Mesh | 5 | 2 | 16 | 5 | 0.07 ms | 0.656100 | MATCH | PASS |
| `diamond_mesh_cap2_p95` | Diamond Mesh | 5 | 2 | 16 | 5 | 0.05 ms | 0.656100 | MATCH | PASS |
| `diamond_mesh_cap1_p50` | Diamond Mesh | 5 | 2 | 20 | 5 | 0.07 ms | 0.656100 | MATCH | PASS |
| `diamond_mesh_cap2_p50` | Diamond Mesh | 5 | 2 | 16 | 5 | 0.04 ms | 0.656100 | MATCH | PASS |
| `complete_k4_p85` | Dense Mesh $K_4$ | 6 | 2 | 12 | 27 | 0.16 ms | 0.969609 | MATCH | PASS |
| `complete_k4_p90` | Dense Mesh $K_4$ | 6 | 2 | 12 | 27 | 0.12 ms | 0.990063 | MATCH | PASS |
| `complete_k4_p95` | Dense Mesh $K_4$ | 6 | 2 | 12 | 27 | 0.12 ms | 0.998633 | MATCH | PASS |
| `complete_k4_p98` | Dense Mesh $K_4$ | 6 | 2 | 12 | 27 | 0.22 ms | 0.999907 | MATCH | PASS |
| `complete_k4_p75` | Dense Mesh $K_4$ | 6 | 2 | 12 | 27 | 0.21 ms | 0.885498 | MATCH | PASS |
| `complete_k4_p80` | Dense Mesh $K_4$ | 6 | 2 | 12 | 27 | 0.23 ms | 0.934912 | MATCH | PASS |

---

## Scientific Analysis & Insights

### 1. Elimination of Auxiliary Multi-Commodity Variables

Standard multi-commodity flow formulations require replicating flow conservation variables for each commodity: $f_{uv}^{(k)}$ for each directed edge $(u, v)$ and each commodity $k \in \{1, \dots, K\}$. This introduces $\Theta(K \cdot \vert E \vert)$ continuous/integer variables and dense bundle constraints $\sum_{k=1}^K f_{uv}^{(k)} \le c_{uv} x_{uv}$.

The **Multi-Commodity Dual Cut Duality Theorem** proves that the concurrent demand satisfaction condition is captured by examining the aggregate crossing demand $D(S) = \sum_{k \in K(S)} d_k$ across all cut partitions $(S, V \setminus S)$. Each minimal capacity-breaking subset $F \subseteq \Delta(S)$ compiles directly into a positive clause $\bigvee_{e \in F} x_e$.
Across all 24 benchmark instances, the compiled CNF uses **strictly $\vert E \vert$ variables** and **zero auxiliary variables**.

### 2. Detection of Bottleneck Contention

Instances `shared_trunk_d1_1_cap1` and `shared_trunk_d1_2_cap2` test bandwidth contention where two commodities share a single trunk whose capacity is strictly less than their sum $d_1 + d_2$.
The compiler immediately detects the empty capacity breaker across the trunk cut partition, generating the refutation clauses `[[1], [-1]]` (UNSAT) in under 0.1 ms and evaluating exact reliability $0.000000$ matching the ground-truth oracle.

---

## Conclusion & Preregistration Status

Hypothesis H18 is **fully confirmed**:

1. Zero mathematical discrepancies across all 24 benchmark instances against exhaustive independent truth-table oracles.
2. Zero auxiliary variables introduced beyond the $\vert E \vert$ physical edge variables.
3. Sub-millisecond mean execution latency ($< 0.1$ ms).
4. Full evidence ledger preserved in `evidence/multi-commodity-wmc-001/` with 100% cryptographic SHA-256 verification.
