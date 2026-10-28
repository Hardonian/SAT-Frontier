# Policy holdout preregistration (v0.2, before execution)

This preregistration commits the exact protocol, candidate, splits, seeds, budgets, fail-closed guards, and analysis rules for evaluating the frozen v0.2 policy winner on held-out data.

## 1. Frozen candidate and hypothesis

- Winner selected by train protocol: `component` with integer weights `{"occurrence": 1, "polarity": 1, "short_clause": 1, "component_size": 1}`.
- Hypothesis: Evaluate whether the train-selected candidate demonstrates any statistically significant improvement over the `combined` control on unseen instances.
- Negative control expectation: Component decomposition strictly precedes variable branching; therefore component size is invariant across active literals within each component. As observed on train data, `component` is behaviorally identical to `mixed` at the branch point. Any measured runtime difference on exact instances is expected to be feature computation overhead rather than structural search acceleration.
- Correctness requirement: Exact counts must match the independent exhaustive oracle on all 12 variables; unknown results must never be relabeled as UNSAT or count zero.

## 2. Configuration and budgets

Frozen in `configs/policy-holdout-v02.json`:
- Split: `holdout`
- Four target families: `random`, `planted`, `disconnected`, `contradictory`
- Problem size: $n = 12$, clause/variable ratio $= 4$
- Seeds: 30 distinct fresh seeds per family ($30001$ to $30030$), yielding 120 independently generated instances.
- Repeats: 5 repeats per instance for both control and candidate, yielding $120 \times 2 \times 5 = 1,200$ total worker runs.
- Solver limits: max recursive nodes 25, solver timeout 0.5 s, hard worker process limit 2.5 s, cache capacity 10,000 entries.
- Execution model: sequential spawned CPU worker processes, no GPU, no remote compute, no warm-up.
- Order rotation: candidate order is rotated systematically across repeats and instances to mitigate execution order bias.

## 3. Fail-closed guards

Before generating or evaluating any holdout instance, the runner must execute:
1. **Source and train freeze verification**: Check SHA-256 hashes of all implementation and verification source files against `evidence/policy-train-v02/winner.json` via `holdout_guard.verify_train_freeze()`.
2. **Preregistration and configuration verification**: Verify SHA-256 digests of `configs/policy-holdout-v02.json` and this document before launch.
3. **Atomic reservation**: Durably create `evidence/policy-holdout-v02-consumed` containing `reservation.json` with the preregistration hash using `holdout_guard.reserve_once()`. Any existing reservation halts execution immediately.
4. **Prior evidence overlap check**: Collect SHA-256 digests of all prior CNF instances in `evidence/`. Verify that zero holdout instances match any prior instance, and that all 120 holdout instances are distinct.
5. **Atomic evidence generation**: Save raw output to a fresh directory `evidence/policy-holdout-v02`, streaming records to `runs.jsonl` and writing all 120 DIMACS files before completion.

## 4. Analysis plan

- Statistical units: Clustered bootstrap over the 120 independently generated instances (never individual timing repeats), 2,000 resamples, PRNG seed 91309.
- Metrics:
  - Paired difference in solved fraction (candidate minus control) with 95% bootstrap confidence interval per family.
  - Number of solved-regression and solved-improvement instances.
  - Conditional speed ratio (control elapsed / candidate elapsed) restricted to instances where both methods solved all 5 repeats, with 95% bootstrap confidence interval.
  - Median solver ms (exact only), median wall ms (all runs), median nodes, and peak worker RSS.
  - Complete accounting of reasons for unknown results (node limit vs timeout).
- Acceptance criterion: M3 performance gate in `docs/RESEARCH_PROTOCOL.md` requires median speedup lower 95% bound > 1.10. If this bound is not met, the result is formally classified as a negative result and published in full.
