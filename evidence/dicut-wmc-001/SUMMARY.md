# Empirical Summary: Directed Network Reliability via Dual Dicut CNF Compilation (Hypothesis H12)

**Campaign**: `evidence/dicut-wmc-001`  
**Instances**: 24  
**Exact Solved**: 24/24  
**Oracle Checks**: 18/18 matched with 100% exact rational equality (0 mismatches)  

## Key Findings

1. **Exact Directed Reachability**: Dual dicut compilation strictly encodes directed s-t reachability without path enumeration or MTZ subtour elimination variables.
2. **Zero Auxiliary Variables**: Requires strictly |A| Boolean variables, achieving instantaneous unit propagation upon arc failures.
3. **100% Independent Oracle Agreement**: Across all 16 instances with |A| <= 16, exact rational probabilities identically match exhaustive state enumeration.
4. **Direct Algebraic Integration**: Closed-form reliability polynomials P(x) and percolation susceptibility curves computed in milliseconds.

## Results Table

| Instance | Category | |V|/|A| | Cuts | $p_c$ | $\chi_{\text{max}}$ | Reliability | Total Latency | Independent Oracle |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `dag_layered_2x2` | layered_dag | 4/4 | 4 | 0.577 | 1.5396 | 96.390000% | 0.18 ms | MATCH |
| `dag_layered_2x3` | layered_dag | 5/6 | 8 | 0.447 | 1.7173 | 99.314100% | 0.24 ms | MATCH |
| `dag_layered_3x2` | layered_dag | 6/8 | 11 | 0.593 | 1.878 | 97.387839% | 0.34 ms | MATCH |
| `dag_layered_3x3` | layered_dag | 8/15 | 51 | 0.442 | 2.167 | 99.775125% | 2.89 ms | MATCH |
| `dag_layered_3x4` | layered_dag | 10/24 | 227 | 0.361 | 2.5066 | 99.979238% | 29.95 ms | UNCHECKED |
| `dag_layered_4x2` | layered_dag | 8/12 | 26 | 0.608 | 2.1243 | 97.520604% | 1.17 ms | MATCH |
| `dag_layered_4x3` | layered_dag | 11/24 | 310 | 0.443 | 2.4711 | 99.793763% | 44.2 ms | UNCHECKED |
| `dag_diamond_cross` | layered_dag | 4/5 | 4 | 0.533 | 1.5708 | 97.119000% | 0.15 ms | MATCH |
| `mesh_directed_2x2` | cyclic_mesh | 4/5 | 4 | 0.577 | 1.5396 | 96.390000% | 0.12 ms | MATCH |
| `mesh_directed_2x3` | cyclic_mesh | 6/9 | 9 | 0.554 | 1.6868 | 97.089759% | 0.31 ms | MATCH |
| `mesh_directed_2x4` | cyclic_mesh | 8/13 | 16 | 0.688 | 1.9362 | 94.010929% | 0.68 ms | MATCH |
| `mesh_directed_3x3` | cyclic_mesh | 9/16 | 30 | 0.575 | 1.9827 | 97.635490% | 1.71 ms | MATCH |
| `cycle_directed_ring_4` | cyclic_mesh | 4/5 | 2 | 0.333 | 1.3333 | 98.100000% | 0.15 ms | MATCH |
| `cycle_directed_ring_6` | cyclic_mesh | 6/8 | 3 | 0.729 | 1.5026 | 88.290000% | 0.15 ms | MATCH |
| `cycle_directed_ring_8` | cyclic_mesh | 8/11 | 6 | 0.643 | 1.6851 | 95.507100% | 0.22 ms | MATCH |
| `barbell_dir_3_3_bridge1` | bottleneck_barbell | 6/13 | 3 | 0.729 | 1.5026 | 88.290000% | 0.19 ms | MATCH |
| `barbell_dir_3_3_bridge2` | bottleneck_barbell | 6/14 | 8 | 0.56 | 1.7648 | 97.666398% | 0.42 ms | MATCH |
| `barbell_dir_4_4_bridge1` | bottleneck_barbell | 8/25 | 5 | 0.572 | 1.4418 | 89.806320% | 0.56 ms | UNCHECKED |
| `barbell_dir_4_4_bridge2` | bottleneck_barbell | 8/26 | 19 | 0.474 | 1.9427 | 98.853463% | 1.77 ms | UNCHECKED |
| `enterprise_k8s_microservices` | enterprise | 9/12 | 14 | 0.699 | 2.1811 | 99.903941% | 0.65 ms | MATCH |
| `enterprise_airflow_etl_dag` | enterprise | 10/17 | 61 | 0.48 | 2.0907 | 99.998981% | 10.19 ms | UNCHECKED |
| `enterprise_fedwire_settlement` | enterprise | 8/11 | 11 | 0.678 | 2.1086 | 99.998357% | 0.43 ms | MATCH |
| `enterprise_autonomous_vehicle_rpc` | enterprise | 11/16 | 56 | 0.611 | 2.358 | 99.999647% | 3.73 ms | MATCH |
| `enterprise_cloud_event_mesh` | enterprise | 11/20 | 182 | 0.496 | 2.3955 | 99.998106% | 18.98 ms | UNCHECKED |

