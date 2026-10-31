# Empirical Results: Repairable Systems Network Reliability (Hypothesis H20)

- **Total Runs**: 24
- **All Oracle Verified**: True (100% exact rational match vs. exhaustive state-space oracle)
- **Mean Latency**: 13.21 ms per instance
- **Total Elapsed**: 0.32 s

## Verification Summary Table

| Topology | Family | Nodes | Edges | Availability | Nines | MTBF (hrs) | MTTR (hrs) | Oracle Match | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `parallel_corridors_p1` | parallel_paths | 3 | 2 | 0.99204775 | 2.0995 | 1000.0 | 8.016 | **EXACT** | **EXACT** |
| `parallel_corridors_p2` | parallel_paths | 4 | 4 | 0.99993676 | 4.199 | 63375.25 | 4.008 | **EXACT** | **EXACT** |
| `parallel_corridors_p3` | parallel_paths | 5 | 6 | 0.9999995 | 6.2985 | 5313312.83 | 2.672 | **EXACT** | **EXACT** |
| `parallel_corridors_p4` | parallel_paths | 6 | 8 | 1.0 | 8.398 | 501114055.05 | 2.004 | **EXACT** | **EXACT** |
| `ladder_2x2` | ladder_2xn | 4 | 4 | 0.99986808 | 3.8797 | 27780.94 | 3.6654 | **EXACT** | **EXACT** |
| `ladder_2x3` | ladder_2xn | 6 | 7 | 0.9999018 | 4.0079 | 35981.94 | 3.5339 | **EXACT** | **EXACT** |
| `ladder_2x4` | ladder_2xn | 8 | 10 | 0.99990376 | 4.0166 | 37382.7 | 3.5981 | **EXACT** | **EXACT** |
| `ladder_2x5` | ladder_2xn | 10 | 13 | 0.99989775 | 3.9903 | 36716.58 | 3.7548 | **EXACT** | **EXACT** |
| `wheatstone_mttr_2h` | wheatstone_bridge | 4 | 5 | 0.99999202 | 5.0978 | 125127.36 | 0.999 | **EXACT** | **EXACT** |
| `wheatstone_mttr_4h` | wheatstone_bridge | 4 | 5 | 0.99996813 | 4.4966 | 62629.67 | 1.9961 | **EXACT** | **EXACT** |
| `wheatstone_mttr_8h` | wheatstone_bridge | 4 | 5 | 0.99987304 | 3.8963 | 31384.19 | 3.9849 | **EXACT** | **EXACT** |
| `wheatstone_mttr_12h` | wheatstone_bridge | 4 | 5 | 0.99971555 | 3.546 | 20971.9 | 5.9671 | **EXACT** | **EXACT** |
| `wheatstone_mttr_24h` | wheatstone_bridge | 4 | 5 | 0.99887711 | 2.9497 | 10567.57 | 11.8795 | **EXACT** | **EXACT** |
| `diamond_mesh_cross` | diamond_mesh | 4 | 5 | 0.99991171 | 4.0541 | 56449.05 | 4.9841 | **EXACT** | **EXACT** |
| `diamond_mesh_simple` | diamond_mesh | 4 | 4 | 0.99982573 | 3.7588 | 28781.56 | 5.0167 | **EXACT** | **EXACT** |
| `barbell_k2` | barbell | 4 | 3 | 0.96484703 | 1.454 | 333.33 | 12.1446 | **EXACT** | **EXACT** |
| `barbell_k3` | barbell | 6 | 7 | 0.98758991 | 1.9062 | 914.97 | 11.4976 | **EXACT** | **EXACT** |
| `triangular_ladder_t2` | triangular_ladder | 6 | 7 | 0.99595283 | 2.3928 | 1938.64 | 7.8779 | **EXACT** | **EXACT** |
| `triangular_ladder_t3` | triangular_ladder | 8 | 10 | 0.99592127 | 2.3895 | 1909.35 | 7.8196 | **EXACT** | **EXACT** |
| `triangular_ladder_t4` | triangular_ladder | 10 | 13 | 0.99588972 | 2.3861 | 1880.93 | 7.7631 | **EXACT** | **EXACT** |
| `telecom_ring_n4` | telecom_ring | 4 | 4 | 0.99999745 | 5.5928 | 783437.62 | 2.0008 | **EXACT** | **EXACT** |
| `telecom_ring_n5` | telecom_ring | 5 | 5 | 0.99999617 | 5.4169 | 522604.38 | 2.0012 | **EXACT** | **EXACT** |
| `telecom_ring_n6` | telecom_ring | 6 | 6 | 0.99999426 | 5.241 | 348611.26 | 2.0016 | **EXACT** | **EXACT** |
| `telecom_ring_n7` | telecom_ring | 7 | 7 | 0.99999235 | 5.1162 | 261614.77 | 2.002 | **EXACT** | **EXACT** |

All 24 instances matched independent exhaustive state-space renewal oracles with 100% exact rational precision.
