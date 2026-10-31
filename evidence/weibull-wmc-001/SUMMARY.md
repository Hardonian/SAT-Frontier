# Empirical Results: Weibull Aging Network Reliability (Hypothesis H19)

- **Total Runs**: 24
- **All Oracle Verified**: True (tolerance $< 10^{-4}$ vs. Simpson's composite rule)
- **Mean Latency**: 62.21 ms per instance
- **Total Elapsed**: 1.49 s

## Verification Summary Table

| Topology | Family | Nodes | Edges | Beta | MTTF (hrs) | B10 Life (hrs) | Simpson Oracle | Rel Err | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `ladder_2x3_beta2` | ladder_2xn | 6 | 7 | 2.0 | 7231.8004 | 4131.6275 | 7231.8004 | 3.02e-15 | **EXACT** |
| `ladder_2x4_beta2` | ladder_2xn | 8 | 10 | 2.0 | 6609.9057 | 3870.933 | 6609.9057 | 1.00e-14 | **EXACT** |
| `ladder_2x5_beta2` | ladder_2xn | 10 | 13 | 2.0 | 6168.2411 | 3671.1112 | 6168.2411 | 4.13e-15 | **EXACT** |
| `ladder_2x6_beta2` | ladder_2xn | 12 | 16 | 2.0 | 5839.7528 | 3515.3653 | 5839.7528 | 5.76e-15 | **EXACT** |
| `ladder_2x7_beta2` | ladder_2xn | 14 | 19 | 2.0 | 5583.655 | 3389.0358 | 5583.655 | 1.89e-14 | **EXACT** |
| `ladder_2x8_beta2` | ladder_2xn | 16 | 22 | 2.0 | 5376.1855 | 3283.3309 | 5376.1855 | 3.50e-14 | **EXACT** |
| `mesh_3x3_beta1.5` | mesh_3xn | 9 | 12 | 1.5 | 6490.9209 | 3366.7991 | 6490.9209 | 2.58e-14 | **EXACT** |
| `mesh_3x3_beta2.0` | mesh_3xn | 9 | 12 | 2.0 | 7121.789 | 4419.9047 | 7121.789 | 1.92e-15 | **EXACT** |
| `mesh_3x4_beta1.5` | mesh_3xn | 12 | 17 | 1.5 | 6159.0129 | 3336.7751 | 6159.0129 | 1.96e-14 | **EXACT** |
| `mesh_3x4_beta2.0` | mesh_3xn | 12 | 17 | 2.0 | 6858.5216 | 4390.3102 | 6858.5216 | 5.17e-15 | **EXACT** |
| `mesh_3x5_beta1.5` | mesh_3xn | 15 | 22 | 1.5 | 5856.7093 | 3263.6727 | 5856.7093 | 1.58e-13 | **EXACT** |
| `mesh_3x5_beta2.0` | mesh_3xn | 15 | 22 | 2.0 | 6611.605 | 4317.9733 | 6611.605 | 1.24e-13 | **EXACT** |
| `barbell_k3_beta2` | barbell | 6 | 7 | 2.0 | 3064.5929 | 1428.4079 | 3064.5929 | 6.38e-15 | **EXACT** |
| `barbell_k4_beta2` | barbell | 8 | 13 | 2.0 | 3384.1598 | 1592.9076 | 3384.1598 | 1.72e-14 | **EXACT** |
| `barbell_k5_beta2` | barbell | 10 | 21 | 2.0 | 3594.9365 | 1619.8464 | 3594.9365 | 6.10e-13 | **EXACT** |
| `barbell_k3_beta1.5` | barbell | 6 | 7 | 1.5 | 2708.3452 | 940.7618 | 2708.3452 | 4.06e-10 | **EXACT** |
| `wheatstone_bridge_beta1.0` | wheatstone_bridge | 4 | 5 | 1.0 | 8166.6667 | 2386.5767 | 8166.6667 | 1.68e-14 | **EXACT** |
| `wheatstone_bridge_beta1.5` | wheatstone_bridge | 4 | 5 | 1.5 | 8315.727 | 3847.544 | 8315.727 | 1.42e-14 | **EXACT** |
| `wheatstone_bridge_beta2.0` | wheatstone_bridge | 4 | 5 | 2.0 | 8537.3899 | 4885.2601 | 8537.3899 | 1.00e-14 | **EXACT** |
| `wheatstone_bridge_beta2.5` | wheatstone_bridge | 4 | 5 | 2.5 | 8725.0847 | 5637.8064 | 8725.0847 | 8.34e-16 | **EXACT** |
| `wheatstone_bridge_beta3.0` | wheatstone_bridge | 4 | 5 | 3.0 | 8875.574 | 6202.8574 | 8875.574 | 1.21e-14 | **EXACT** |
| `grid_4x3_beta1.5` | grid_4xn | 12 | 17 | 1.5 | 6159.0129 | 3336.7751 | 6159.0129 | 1.96e-14 | **EXACT** |
| `grid_4x3_beta2.0` | grid_4xn | 12 | 17 | 2.0 | 6858.5216 | 4390.3102 | 6858.5216 | 5.17e-15 | **EXACT** |
| `grid_4x4_beta1.5` | grid_4xn | 16 | 24 | 1.5 | 6087.5634 | 3434.8774 | 6087.5634 | 1.74e-13 | **EXACT** |

All 24 instances matched independent composite numerical quadrature oracles within $10^{-4}$ relative tolerance.
