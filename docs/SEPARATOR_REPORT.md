# Graph Separator Decomposition Report (Hypothesis H4, v0.2.1)

**Summary Outcome**: Evaluated graph separator and articulation-point branching (`solve_separator`) against the occurrence-based `combined` control across 160 sequential CPU worker runs on four distributions (`barbell`, `disconnected`, `planted`, `random`).

All 160 runs produced exact counts matching the independent truth-table oracle (100% oracle pass).

---

## 1. Quantitative Results

| Family | Control median nodes / mean nodes | Separator median nodes / mean nodes | Component splits (control / sep) | Median solver ms (control / sep) | Paired time overhead ratio (sep / ctrl) |
|---|---:|---:|---:|---:|---:|
| **barbell** | 18.0 / 18.1 | 19.0 / 18.4 | 1.0 / 2.0 | 0.807 / 0.748 | **0.915** (separator is faster) |
| **disconnected** | 17.0 / 16.0 | 17.0 / 16.2 | 1.0 / 1.0 | 0.626 / 0.779 | 1.251 (+25% overhead) |
| **planted** | 17.0 / 20.8 | 17.0 / 20.8 | 0.0 / 0.0 | 1.512 / 2.062 | 1.532 (+53% overhead) |
| **random** | 17.0 / 17.2 | 17.0 / 17.2 | 0.0 / 0.0 | 1.244 / 2.048 | 1.594 (+59% overhead) |

---

## 2. Findings on Hypothesis H4

1. **Structured Bottlenecks (Barbell)**: On barbell formulas with a dedicated path bridge between two dense subcomponents, articulation-point detection successfully isolates the cut vertex and doubles median component splits (2.0 vs 1.0), yielding a net runtime speedup (time ratio 0.915).
2. **Dense Expander Formulas (Random & Planted)**: On uniform random 3-SAT at critical ratio 4, the primal graph is a dense expander with high vertex connectivity ($\kappa(G) \ge 2$). No single-vertex separator exists. Consequently, the separator heuristic branches on occurrence tie-breakers, producing **identical node trees** (20/20 pairs identical in random, 20/20 in planted).
3. **Overhead Penalty**: Computing reachability and connected components for $V \setminus \{v\}$ across all active variables incurs $53\%$ to $59\%$ computational overhead when no articulation point exists.
4. **Falsification Verdict**: In accordance with the preregistered falsifier ("Separator search overhead removes gains"), Hypothesis H4 fails as a general-purpose heuristic for uniform random SAT, while providing targeted structural advantage on graph topologies with low-order cutsets.

Evidence directory: `evidence/separator-study-001/`

