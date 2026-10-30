# Preregistered branch-policy held-out campaign report (v0.2)

**Final outcome: definitive negative result.** The frozen v0.2 candidate `component` (weights: `occurrence=1, polarity=1, short_clause=1, component_size=1`), selected during the train campaign and preregistered in `docs/POLICY_HOLDOUT_PREREGISTRATION.md`, failed the M3 performance gate across all four held-out instance families. The protocol's performance gate requires the lower bound of the 95% bootstrap confidence interval on the paired speedup ratio (control over candidate) to exceed 1.10. On all target families, the measured speedup was either negligible or negative:

- `random`: median speedup 0.959 [0.941, 0.986] (lower bound well below 1.10; candidate is slower)
- `planted`: median speedup 0.963 [0.945, 0.974] (lower bound well below 1.10; candidate is slower)
- `disconnected`: median speedup 0.927 [0.907, 0.939] (candidate exhibits severe timing regression due to feature computation overhead)
- `contradictory`: median speedup 1.017 [1.009, 1.033] (sub-2% noise on trivial unit-propagation instances)

No novel algorithm, asymptotic bound, P versus NP breakthrough, or practical speedup is claimed. This negative result is preserved in full in `evidence/policy-holdout-v02/`.

---

## 1. Protocol and fail-closed execution

The held-out study executed under strict, uncompromised preregistered guards:

1. **Source freeze**: Pinned train winner and exact source hashes verified against `evidence/policy-train-v02/winner.json` before execution.
2. **Atomic reservation**: Split consumed atomically via `evidence/policy-holdout-v02-consumed/reservation.json` with preregistration digest `fa5ac9ca2d135d85779c6adbc7950718780c4070b50447eddbe644a3b8a0a14d`.
3. **Instance overlap guard**: Zero byte overlap between the 120 holdout instances and any prior CNF in `evidence/` (smoke, development, or train campaigns).
4. **Execution parameters**: 120 generated instances ($n=12$, ratio 4, seeds 30001–30030 across 4 families), 5 repeats per instance, 2 policies (`control` and `component`), yielding 1,200 sequential spawned CPU worker runs.
5. **Budgets**: Max 25 recursive nodes, 0.5 s solver timeout, 2.5 s hard wall limit, 10,000 cache capacity.
6. **Correctness**: Every exact result (1,115 runs) was verified against the independent exhaustive truth-table oracle (`oracle_pass`). All 85 incomplete runs terminated solely at the 25-node budget (`node_limit`); none were wall timeouts, worker crashes, or mislabeled zeros.

---

## 2. Quantitative results

### Table 1: Solved fractions, unknown fractions, and runtime metrics

| Family | Control / candidate exact fraction | Unknown fraction (each) | Median solver ms control / candidate (exact only) | Median wall ms candidate (all runs) | Median nodes candidate (all runs) |
| --- | ---: | ---: | ---: | ---: | ---: |
| **random** | 0.867 / 0.933 | 0.133 / 0.067 | 1.146 / 1.200 | 178.08 | 13 |
| **planted** | 0.833 / 0.867 | 0.167 / 0.133 | 1.127 / 1.196 | 172.28 | 15 |
| **disconnected** | 0.967 / 0.967 | 0.033 / 0.033 | 0.557 / 0.596 | 173.52 | 17 |
| **contradictory** | 1.000 / 1.000 | 0.000 / 0.000 | 0.122 / 0.121 | 165.43 | 1 |

*Note: Clustered bootstrap over the 30 independent instances per family with 2,000 resamples (seed 91309). Paired difference in solved fraction (candidate minus control): `random` +0.067 [0.000, 0.167], `planted` +0.033 [-0.067, 0.133], `disconnected` 0.000 [0.000, 0.000], `contradictory` 0.000 [0.000, 0.000].*

### Table 2: Paired speedup ratios and timing regressions (completed pairs only)

| Family | Completed paired instances (all 5 repeats exact) | Median candidate/control time ratio | Median control/candidate speed ratio [95% CI] | Timing regression instances (candidate slower) |
| --- | ---: | ---: | ---: | ---: |
| **random** | 26 | 1.043 | 0.959 [0.941, 0.986] | 19 / 26 |
| **planted** | 24 | 1.038 | 0.963 [0.945, 0.974] | 19 / 24 |
| **disconnected** | 29 | 1.079 | 0.927 [0.907, 0.939] | 26 / 29 |
| **contradictory** | 30 | 0.983 | 1.017 [1.009, 1.033] | 6 / 30 |

---

## 3. Mechanistic analysis and findings

1. **Feature computation overhead dominates**: Evaluating four linear branch features (`occurrence`, `polarity`, `short_clause`, `component_size`) at every recursive branching node adds $4\%$ to $8\%$ overhead to solver elapsed time. On instances where both algorithms complete, `control` is faster in 70 out of 109 completed pairs.
2. **Component-size feature invariance confirmed**: Because connected component decomposition strictly precedes branching decisions in `combined`, all candidate variables within an active component share the exact same component size. Thus the `component_size` weight adds no discriminative signal to branch candidate selection.
3. **Slight node count variance on sparse/planted instances**: Small variations in branching choices on planted/random instances yielded minor node reductions on 2 instances, but the paired confidence interval for solved fraction spans zero in `planted` ([-0.067, 0.133]) and the speed ratio remains strictly below 1.0 on all non-trivial families.
4. **Conclusion on hypothesis H3**: Hypothesis H3 ("Balanced polarity improves branching on selected families") is officially resolved as falsified on held-out evidence. Linear combinations of these static local features do not overcome feature extraction overhead on CPU.

---

## 4. Verification and evidence integrity

- Raw run logs: `evidence/policy-holdout-v02/runs.jsonl` (1,200 records)
- Raw CSV table: `evidence/policy-holdout-v02/runs.csv`
- Generated formulas: `evidence/policy-holdout-v02/instances/*.cnf` (120 files)
- Summary statistics: `evidence/policy-holdout-v02/summary.json`
- Integrity manifest: `evidence/policy-holdout-v02/manifest.json`
- Verification command:

  ```bash
  python verify_holdout_evidence.py
  ```

  All 1,200 runs, 120 instances, source hashes, and oracle counts pass independent verification.
