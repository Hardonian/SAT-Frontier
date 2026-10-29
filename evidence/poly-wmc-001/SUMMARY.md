# Empirical Summary: Exact Reliability Polynomials & Percolation Phase Transitions (Hypothesis H11)

**Campaign**: `evidence/poly-wmc-001`  
**Instances**: 24  
**Exact Solved**: 24/24  
**Oracle Checks**: 17/17 matched with 100% exact integer coefficient equality (0 mismatches)  

## Key Findings

1. **Exact Closed-Form Polynomials**: Algebraic model counting over $\mathbb{Z}[x]$ evaluates the entire reliability polynomial $P(x) = \sum c_k x^k$ in a single exact search pass, eliminating the need to re-run DPLL for different edge operational probabilities.
2. **100% Exact Oracle Agreement**: Across all 17 instances where $|E| \le 16$, every integer coefficient $c_k$ ($k=0..|E|$) identically matches the independent brute-force state enumeration oracle with zero discrepancy.
3. **Percolation Phase Transitions**: Accurately computes the exact finite-size susceptibility peak $\chi_{\text{max}} = \max_p \frac{dR}{dp}$ and the effective percolation threshold $p_c$ across planar grids, mapping the transition from disconnected to connected regimes.

## Results Table

| Instance | Category | |V|/|E| | Cuts | Degree | $p_c$ (Threshold) | $\chi_{\text{max}}$ | $R(0.9)$ | Latency (ms) | Independent Oracle |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `grid_2x3` | planar_grid | 6/7 | 9 | 7 | 0.6460 | 1.8775 | 95.878080% | 0.17 ms | MATCH (100% exact) |
| `grid_2x4` | planar_grid | 8/10 | 16 | 10 | 0.6930 | 2.1660 | 94.802251% | 0.32 ms | MATCH (100% exact) |
| `grid_2x5` | planar_grid | 10/13 | 25 | 13 | 0.7240 | 2.4249 | 93.691069% | 0.82 ms | MATCH (100% exact) |
| `grid_2x6` | planar_grid | 12/16 | 36 | 16 | 0.7460 | 2.6564 | 92.588884% | 1.96 ms | MATCH (100% exact) |
| `grid_2x7` | planar_grid | 14/19 | 49 | 19 | 0.7630 | 2.8649 | 91.499321% | 5.23 ms | UNCHECKED (|E|=19 > 16) |
| `grid_3x3` | planar_grid | 9/12 | 30 | 12 | 0.6310 | 2.1792 | 97.250217% | 0.87 ms | MATCH (100% exact) |
| `grid_3x4` | planar_grid | 12/17 | 81 | 17 | 0.6440 | 2.4154 | 97.259325% | 6.17 ms | UNCHECKED (|E|=17 > 16) |
| `grid_3x5` | planar_grid | 15/22 | 194 | 22 | 0.6590 | 2.6272 | 97.135308% | 39.88 ms | UNCHECKED (|E|=22 > 16) |
| `grid_3x6` | planar_grid | 18/27 | 435 | 27 | 0.6730 | 2.8215 | 96.998446% | 257.75 ms | UNCHECKED (|E|=27 > 16) |
| `grid_4x4` | planar_grid | 16/24 | 348 | 24 | 0.6350 | 2.6101 | 97.504635% | 125.26 ms | UNCHECKED (|E|=24 > 16) |
| `grid_4x5` | planar_grid | 20/31 | 1353 | 31 | 0.6380 | 2.7841 | 97.515497% | 2050.03 ms | UNCHECKED (|E|=31 > 16) |
| `complete_k3` | complete_graph | 3/3 | 2 | 3 | 0.3330 | 1.3333 | 98.100000% | 0.06 ms | MATCH (100% exact) |
| `complete_k4` | complete_graph | 4/6 | 4 | 6 | 0.2860 | 1.7002 | 99.784800% | 0.11 ms | MATCH (100% exact) |
| `complete_k5` | complete_graph | 5/10 | 8 | 10 | 0.2500 | 2.0958 | 99.979480% | 0.35 ms | MATCH (100% exact) |
| `cycle_c4` | cycle_graph | 4/4 | 4 | 4 | 0.5770 | 1.5396 | 96.390000% | 0.06 ms | MATCH (100% exact) |
| `cycle_c6` | cycle_graph | 6/6 | 9 | 6 | 0.7370 | 1.9544 | 92.655900% | 0.10 ms | MATCH (100% exact) |
| `cycle_c8` | cycle_graph | 8/8 | 16 | 8 | 0.8090 | 2.4214 | 88.173279% | 0.27 ms | MATCH (100% exact) |
| `barbell_3_3_bridge1` | bottleneck_barbell | 7/8 | 6 | 8 | 0.8860 | 2.3249 | 77.951241% | 0.08 ms | MATCH (100% exact) |
| `barbell_4_4_bridge1` | bottleneck_barbell | 9/14 | 10 | 14 | 0.9990 | 1.9980 | 80.651751% | 0.22 ms | MATCH (100% exact) |
| `barbell_3_3_bridge3` | bottleneck_barbell | 9/10 | 8 | 10 | 0.9990 | 3.9960 | 63.140505% | 0.11 ms | MATCH (100% exact) |
| `enterprise_cloud_vpc` | enterprise | 7/8 | 12 | 8 | 0.7060 | 2.0607 | 94.170762% | 0.21 ms | MATCH (100% exact) |
| `enterprise_subsea_optical` | enterprise | 7/9 | 12 | 9 | 0.6420 | 1.9315 | 95.964612% | 0.25 ms | MATCH (100% exact) |
| `enterprise_ieee14_power_grid` | enterprise | 14/20 | 64 | 20 | 0.6300 | 2.2715 | 97.321044% | 4.99 ms | UNCHECKED (|E|=20 > 16) |
| `enterprise_avionics_qmr` | enterprise | 10/12 | 36 | 12 | 0.6960 | 2.2131 | 95.193338% | 0.84 ms | MATCH (100% exact) |
