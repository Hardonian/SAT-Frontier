# Milestones

| Gate | Scope | Acceptance | Status |
| --- | --- | --- | --- |
| M0 | Runnable exact-count lab | Independent oracle, five ablations, strict parser, budget semantics, evidence, tests | Implemented and locally verified |
| M1 | Trust and baselines | Pin source release; build/audit formal target or record blocker; integrate mature exact counter; measure RSS | Closed with blocker: independent development cross-checks passed; upstream Lean build resource ceiling (11.9 GB peak, exit 137/timeout) recorded; downstream M4 gated |
| M2 | Policy discovery | Restricted deterministic policy schema, bounded search, counterexample retention/minimization, metamorphic tests | Completed: train slice, metamorphic tests, fail-closed holdout guards and atomic reservation |
| M3 | Held-out evaluation | Freeze winner; paired data and confidence intervals; 30+ cases per family and 5+ repeats; publish negative results | Completed: 1,200-run preregistered holdout evaluated and verified; negative result report published |
| M4 | Algorithmic extraction | Audited lemma, implementation, invariant proof, explicit bit-cost recurrence, independent review | Gated: awaiting independent proof certificate / kernel verification of upstream candidate |
| M5 | Useful transfer | One task-matched application/reduction, encoding overhead, end-to-end benefit and regression budget | Completed: Two-Terminal Network Infrastructure Reliability via Weighted Model Counting (WMC); >18x node reduction and exact rational probability computed on instances where non-decomposed solvers exhaust budget |

M0 is a preparation release. The v0.2.1 research checkpoint extends it: M1 is resolved with a formal blocker, M2 and M3 are completed with verified negative results, Hypothesis H4 (graph separators) and the Calibrated Scaling Benchmark (n=12..20) are fully executed and documented, and Milestone M5 (Useful Transfer) is completed with an exact Weighted Model Counting engine for network reliability and risk analysis. Neither a performance gain on random CNF nor the upstream complexity theorem is established. Preserved evidence grounds all findings.
