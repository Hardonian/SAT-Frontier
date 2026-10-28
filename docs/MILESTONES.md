# Milestones

| Gate | Scope | Acceptance | Status |
| --- | --- | --- | --- |
| M0 | Runnable exact-count lab | Independent oracle, five ablations, strict parser, budget semantics, evidence, tests | Implemented and locally verified |
| M1 | Trust and baselines | Pin source release; build/audit formal target or record blocker; integrate mature exact counter; measure RSS | Partial: independent development checks and resource fields completed; upstream Lean build and theorem comparison not completed |
| M2 | Policy discovery | Restricted deterministic policy schema, bounded search, counterexample retention/minimization, metamorphic tests | Completed: train slice, metamorphic tests, fail-closed holdout guards and atomic reservation |
| M3 | Held-out evaluation | Freeze winner; paired data and confidence intervals; 30+ cases per family and 5+ repeats; publish negative results | Completed: 1,200-run preregistered holdout evaluated and verified; negative result report published |
| M4 | Algorithmic extraction | Audited lemma, implementation, invariant proof, explicit bit-cost recurrence, independent review | Research-dependent |
| M5 | Useful transfer | One task-matched application/reduction, encoding overhead, end-to-end benefit and regression budget | Research-dependent |

M0 is a preparation release. The v0.2 research checkpoint extends it but does not complete M1, prove the upstream theorem, or establish a performance gain. M4/M5 success cannot be promised. A publishable negative result or falsified candidate is a legitimate research outcome if supported by preserved evidence.
