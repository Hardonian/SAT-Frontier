# High-Concurrency Cube-and-Conquer on Dual Cut Topologies (`evidence/cut-cube-001/`)

**Execution Date**: 2026-10-28  
**Hardware Environment**: 24 Logical CPU Cores, 31.6 GB RAM, Windows 11  
**Study Scope**: 12 hardness-boundary topologies across depths $d \in \{2, 4, 6\}$ (36 total runs, 20 worker concurrency).  
**Verification**: 100% cryptographic SHA-256 match in `verify_evidence.py`; 19/19 cross-depth invariance checks show 0 rational weight mismatches.

---

## 1. Scientific Significance

This study verifies the multiplicative combination of **Dual Cut Compilation** (Hypothesis H9) with **Parallel Cube-and-Conquer Lookahead** (Hypothesis H8).

In the earlier EPYC campaign, path-based formulas hit an impassable structural cliff at $3\times 7$ and $2\times 11$. While single-threaded Dual Cut compilation unlocked $3\times 7$ (2.13s), larger instances like $3\times 8$, $3\times 9$, and $4\times 6$ remained beyond the single-threaded node budget (100,000 nodes).

Here, we demonstrated that **deeper lookahead partitioning directly converts intractable instances into fully solved exact instances**:

- **`grid_3x8`**: At depth 2 (4 cubes), the cubes exceeded the node budget (`unknown`). Increasing lookahead to depth 4 (16 cubes) unlocked exact solution in **3.68 seconds** (322,629 nodes), and depth 6 (64 cubes) completed in **3.25 seconds** (408,021 nodes).
- **`grid_3x9`**: Intractable at depths 2 and 4 (`unknown`). At depth 6 (64 cubes), all cubes solved within budget in **11.52 seconds**, evaluating **1,406,923 search nodes** with zero incomplete cubes!
- **`grid_4x6`**: Intractable at depths 2 and 4 (`unknown`). At depth 6 (64 cubes), solved completely in **11.06 seconds**, evaluating **1,336,764 search nodes** with zero incomplete cubes!

---

## 2. Quantitative Summary

| Topology | Vars | Clauses | Depth 2 (4 cubes) | Depth 4 (16 cubes) | Depth 6 (64 cubes) | Total Evaluated Nodes (d=6) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `grid_2x10` | 28 | 100 | **exact** (0.88s) | **exact** (0.83s) | **exact** (0.85s, 75.5 c/s) | 5,610 |
| `grid_2x11` | 31 | 121 | **exact** (0.89s) | **exact** (0.85s) | **exact** (0.90s, 70.9 c/s) | 8,319 |
| `grid_2x12` | 34 | 144 | **exact** (0.99s) | **exact** (0.95s) | **exact** (1.02s, 62.5 c/s) | 11,856 |
| `grid_3x6` | 27 | 435 | **exact** (1.22s) | **exact** (1.12s) | **exact** (0.98s, 65.2 c/s) | 29,352 |
| `grid_3x7` | 32 | 938 | **exact** (1.85s) | **exact** (1.62s) | **exact** (1.39s, 46.2 c/s) | 99,661 |
| `grid_3x8` | 37 | 1,973 | unknown | **exact** (3.68s) | **exact** (3.26s, 19.7 c/s) | 408,021 |
| `grid_3x9` | 42 | 4,082 | unknown | unknown | **exact** (11.52s, 5.6 c/s) | **1,406,923** |
| `grid_4x4` | 24 | 348 | **exact** (0.99s) | **exact** (1.00s) | **exact** (1.05s, 60.7 c/s) | 21,555 |
| `grid_4x5` | 31 | 1,353 | **exact** (2.66s) | **exact** (1.93s) | **exact** (1.92s, 33.4 c/s) | 224,479 |
| `grid_4x6` | 38 | 5,024 | unknown | unknown | **exact** (11.06s, 5.8 c/s) | **1,336,764** |
| `barbell_k6`| 31 | 33 | **exact** (0.79s) | **exact** (0.87s) | **exact** (0.87s, 73.8 c/s) | 12,676 |
| `barbell_k7`| 43 | 65 | **exact** (0.90s) | **exact** (0.90s) | **exact** (1.12s, 57.4 c/s) | 68,338 |

---

## 3. Mathematical Verification & Exact Invariance

Across all 19 paired cross-depth comparisons where instances were solved at multiple depths, the computed rational probabilities matched identically down to the exact fraction:
- `grid_3x8` at $d=4$ and $d=6$: `483613138738686463066367339798409/500000000000000000000000000000000` (identical)
- `grid_3x7` at $d=2, 4, 6$: `96860501287470574774715548659159/100000000000000000000000000000000` (identical)
- Zero mismatches across all runs.
