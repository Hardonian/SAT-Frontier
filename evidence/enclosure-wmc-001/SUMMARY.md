# Empirical Results: Any-Time Monotone Dual Bounding & Enclosure Intervals (Hypothesis H21)

- **Total Runs**: 24
- **All Enclosures Certified**: True ($R_{\\text{lower}} \\le R(G) \\le R_{\\text{upper}}$ holds on 100% of runs)
- **Mean Latency**: 8.83 ms per instance
- **Total Elapsed**: 0.21 s

## Verification Summary Table

| Topology | Family | Nodes | Edges | Cuts Used / Total | Lower Bound | Exact Reliability | Upper Bound | Gap ($\Delta$) | Containment | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `ladder_2x2_partial` | ladder_2xn | 4 | 4 | 2/4 | 0.9639 | 0.9639 | 0.981 | 0.0171 | **ENCLOSED** | **EXACT** |
| `ladder_2x3_partial` | ladder_2xn | 6 | 7 | 4/9 | 0.86751 | 0.958781 | 0.962361 | 0.094851 | **ENCLOSED** | **EXACT** |
| `ladder_2x4_partial` | ladder_2xn | 8 | 10 | 8/16 | 0.780759 | 0.948023 | 0.950512 | 0.169753 | **ENCLOSED** | **EXACT** |
| `ladder_2x5_partial` | ladder_2xn | 10 | 13 | 12/25 | 0.702683 | 0.936911 | 0.938768 | 0.236085 | **ENCLOSED** | **EXACT** |
| `ladder_2x6_partial` | ladder_2xn | 12 | 16 | 18/36 | 0.632415 | 0.925889 | 0.926339 | 0.293924 | **ENCLOSED** | **EXACT** |
| `mesh_3x3_frac_1_3` | mesh_3xn | 9 | 12 | 10/30 | 0.862903 | 0.972502 | 0.973365 | 0.110462 | **ENCLOSED** | **EXACT** |
| `mesh_3x3_frac_2_3` | mesh_3xn | 9 | 12 | 20/30 | 0.862903 | 0.972502 | 0.972676 | 0.109773 | **ENCLOSED** | **EXACT** |
| `mesh_3x4_frac_1_3` | mesh_3xn | 12 | 17 | 27/81 | 0.776612 | 0.972593 | 0.972751 | 0.196138 | **ENCLOSED** | **EXACT** |
| `mesh_3x4_frac_2_3` | mesh_3xn | 12 | 17 | 54/81 | 0.776612 | 0.972593 | 0.972601 | 0.195989 | **ENCLOSED** | **EXACT** |
| `mesh_3x5_frac_1_3` | mesh_3xn | 15 | 22 | 64/194 | 0.698951 | 0.971353 | 0.971375 | 0.272424 | **ENCLOSED** | **EXACT** |
| `mesh_3x5_frac_2_3` | mesh_3xn | 15 | 22 | 129/194 | 0.698951 | 0.971353 | 0.971354 | 0.272403 | **ENCLOSED** | **EXACT** |
| `barbell_k3_partial` | barbell | 6 | 7 | 2/5 | 0.756295 | 0.792219 | 0.798 | 0.041705 | **ENCLOSED** | **EXACT** |
| `barbell_k4_partial` | barbell | 8 | 13 | 4/9 | 0.756295 | 0.799583 | 0.7997 | 0.043405 | **ENCLOSED** | **EXACT** |
| `barbell_k5_partial` | barbell | 10 | 21 | 8/17 | 0.756295 | 0.79998 | 0.79998 | 0.043685 | **ENCLOSED** | **EXACT** |
| `wheatstone_cuts_1` | wheatstone_bridge | 4 | 5 | 1/4 | 0.922994 | 0.950629 | 0.9775 | 0.054506 | **ENCLOSED** | **EXACT** |
| `wheatstone_cuts_2` | wheatstone_bridge | 4 | 5 | 2/4 | 0.922994 | 0.950629 | 0.955506 | 0.032512 | **ENCLOSED** | **EXACT** |
| `wheatstone_cuts_3` | wheatstone_bridge | 4 | 5 | 3/4 | 0.922994 | 0.950629 | 0.953068 | 0.030074 | **ENCLOSED** | **EXACT** |
| `wheatstone_cuts_4` | wheatstone_bridge | 4 | 5 | 4/4 | 0.922994 | 0.950629 | 0.950629 | 0.027636 | **ENCLOSED** | **EXACT** |
| `parallel_corridors_p2` | parallel_paths | 4 | 4 | 2/4 | 0.9025 | 0.990494 | 0.995125 | 0.092625 | **ENCLOSED** | **EXACT** |
| `parallel_corridors_p3` | parallel_paths | 5 | 6 | 4/8 | 0.9025 | 0.999073 | 0.999525 | 0.097025 | **ENCLOSED** | **EXACT** |
| `parallel_corridors_p4` | parallel_paths | 6 | 8 | 8/16 | 0.990494 | 0.99991 | 0.999954 | 0.00946 | **ENCLOSED** | **EXACT** |
| `parallel_corridors_p5` | parallel_paths | 7 | 10 | 16/32 | 0.990494 | 0.999991 | 0.999995 | 0.009502 | **ENCLOSED** | **EXACT** |
| `grid_4x3_frac_1_4` | grid_4xn | 12 | 17 | 20/81 | 0.776612 | 0.972593 | 0.973143 | 0.19653 | **ENCLOSED** | **EXACT** |
| `grid_4x3_frac_1_2` | grid_4xn | 12 | 17 | 40/81 | 0.776612 | 0.972593 | 0.972668 | 0.196056 | **ENCLOSED** | **EXACT** |

All 24 instances satisfied the certified mathematical enclosure $R_{\text{lower}} \le R(G) \le R_{\text{upper}}$ with 100% exact rational precision.
