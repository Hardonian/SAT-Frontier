# Empirical Results: Multi-Commodity Leighton-Rao Routing Gap (Hypothesis H22)

- **Total Runs**: 24
- **Upper Bound Invariant Verified**: True ($R_{\text{routing}} \le R_{\text{cut}}$ holds on 100% of runs)
- **Mean Latency**: 2.03 ms per instance
- **Total Elapsed**: 0.05 s

## Verification Summary Table

| Topology | Family | Nodes | Edges | Commodities | $R_{\text{routing}}$ (Exact) | $R_{\text{cut}}$ (Exact) | Leighton-Rao Gap ($\Delta$) | Invariant | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `triangle_single_commodity` | planar_noncrossing | 3 | 3 | 1 | 0.981 | 0.981 | 0.0 | **SATISFIED** | **EXACT** |
| `triangle_two_adjacent` | planar_noncrossing | 3 | 3 | 2 | 0.81 | 0.81 | 0.0 | **SATISFIED** | **EXACT** |
| `ladder_2x2_horizontal` | planar_noncrossing | 4 | 4 | 2 | 0.81 | 0.81 | 0.0 | **SATISFIED** | **EXACT** |
| `bottleneck_trunk_sufficient` | planar_noncrossing | 6 | 5 | 2 | 0.733056 | 0.733056 | 0.0 | **SATISFIED** | **EXACT** |
| `tree_disjoint_branch` | planar_noncrossing | 5 | 4 | 1 | 0.81 | 0.81 | 0.0 | **SATISFIED** | **EXACT** |
| `cycle_c4_adjacent` | planar_noncrossing | 4 | 4 | 2 | 0.81 | 0.81 | 0.0 | **SATISFIED** | **EXACT** |
| `cycle_c4_opposite_p90` | cycle_crossing | 4 | 4 | 2 | 0.0 | 0.6561 | 0.6561 | **SATISFIED** | **EXACT** |
| `cycle_c4_opposite_p80` | cycle_crossing | 4 | 4 | 2 | 0.0 | 0.4096 | 0.4096 | **SATISFIED** | **EXACT** |
| `cycle_c4_opposite_p95` | cycle_crossing | 4 | 4 | 2 | 0.0 | 0.814506 | 0.814506 | **SATISFIED** | **EXACT** |
| `cycle_c5_crossing_pairs` | cycle_crossing | 5 | 5 | 2 | 0.0 | 0.59049 | 0.59049 | **SATISFIED** | **EXACT** |
| `cycle_c5_interlaced_three` | cycle_crossing | 5 | 5 | 3 | 0.0 | 0.0 | 0.0 | **SATISFIED** | **EXACT** |
| `cycle_c6_opposite_crossing` | cycle_crossing | 6 | 6 | 2 | 0.0 | 0.531441 | 0.531441 | **SATISFIED** | **EXACT** |
| `k23_pairwise_b_p90` | bipartite_k23 | 5 | 6 | 3 | 0.0 | 0.531441 | 0.531441 | **SATISFIED** | **EXACT** |
| `k23_pairwise_b_p80` | bipartite_k23 | 5 | 6 | 3 | 0.0 | 0.262144 | 0.262144 | **SATISFIED** | **EXACT** |
| `k23_pairwise_b_p95` | bipartite_k23 | 5 | 6 | 3 | 0.0 | 0.735092 | 0.735092 | **SATISFIED** | **EXACT** |
| `k23_cross_partition_demands` | bipartite_k23 | 5 | 6 | 2 | 0.780759 | 0.905418 | 0.124659 | **SATISFIED** | **EXACT** |
| `k23_two_demands_routable` | bipartite_k23 | 5 | 6 | 2 | 0.780759 | 0.780759 | 0.0 | **SATISFIED** | **EXACT** |
| `k24_disjoint_pairs` | bipartite_k23 | 6 | 8 | 2 | 0.929103 | 0.950361 | 0.021258 | **SATISFIED** | **EXACT** |
| `diamond_diagonal_cross` | saturated_mesh | 4 | 5 | 2 | 0.86751 | 0.93312 | 0.06561 | **SATISFIED** | **EXACT** |
| `grid_2x3_horizontal_parallel` | saturated_mesh | 6 | 7 | 2 | 0.6561 | 0.6561 | 0.0 | **SATISFIED** | **EXACT** |
| `grid_2x3_diagonal_crossing` | saturated_mesh | 6 | 7 | 2 | 0.0 | 0.637729 | 0.637729 | **SATISFIED** | **EXACT** |
| `grid_2x3_three_demands` | saturated_mesh | 6 | 7 | 3 | 0.59049 | 0.59049 | 0.0 | **SATISFIED** | **EXACT** |
| `bottleneck_trunk_contention` | saturated_mesh | 6 | 5 | 2 | 0.0 | 0.0 | 0.0 | **SATISFIED** | **EXACT** |
| `ladder_2x4_diagonal_flows` | saturated_mesh | 8 | 10 | 2 | 0.0 | 0.529475 | 0.529475 | **SATISFIED** | **EXACT** |

All 24 benchmark instances verified that $R_{\text{routing}} \le R_{\text{cut}}$ with 100% exact rational precision, confirming the Leighton-Rao routing gap on crossing cycles and bipartite configurations.
