# Research protocol v0.1

## First campaign

Run the frozen smoke configuration on the train split only. Its 32 generated cases × five algorithms produce 160 solver runs. Ratios 2 and 4, sizes 8 and 12, and four families exercise different behaviors. These tiny cases validate the apparatus; they cannot establish competitiveness. Random and planted instances must never be pooled into a claim about uniform random SAT. Disconnected formulas deliberately favor decomposition; they are a positive control. Contradictory units are a negative correctness control, not a performance achievement.

Holdout seeds are declared in advance but have not been used for the supplied campaign. They provide an honest procedural split, not secret data. Do not tune policies against them. Freeze source and a candidate ID before a held-out run. Once used, mark that split consumed and create a new preregistered split for subsequent development. Tests use additional fixed seeds and are development evidence.

## Claims and acceptance

`hypotheses.csv` records falsifiable questions. Every candidate needs a precise transformation or policy, expected advantage, adversarial counterexamples, invariants, and a bounded evaluation budget before coding. Separate candidate generation from evaluation. Do not execute arbitrary generated code in the host; first use a restricted policy representation, static validation and isolated workers.

Correctness gates: exhaustive small instances, randomized differential tests, metamorphic tests, and an independent mature exact counter on larger inputs. The current oracle is exhaustive through at most 16 variables in campaigns; standalone oracle allows 20. Five related implementations agreeing above that cutoff is not independent verification. Large results remain `unchecked`. A wrong count stops the campaign and preserves evidence. Retain and minimize every counterexample before further tuning.

Performance gates for a future candidate: independent exact-counter baseline installed and pinned; at least five repeats on at least 30 paired held-out instances per target family; paired bootstrap confidence intervals across instances, not repeated timings of a single instance; median speedup lower 95% confidence bound above 1.10; no correctness failures; solved fraction reported with all timeouts. Report per-family regressions and memory peaks. A claim may be explicitly scoped to one family. Include multiple-comparison corrections when searching many policies and confirm winners on fresh data. v0.1 does not implement this inferential analysis or satisfy this gate.

Use identical per-instance resource budgets and hardware placement, record load and warm-up policy, rotate algorithm order, and distinguish solver time from process startup. Do not report success-only speedups while omitting timeouts. Cache capacity is an entry limit, not a memory measurement. Measure RSS in the next milestone. Never fit a finite timing curve and label it an asymptotic proof.

## Correctness argument for the current code

An empty clause has zero models; no remaining clauses admits all assignments to remaining variables. Removing duplicate clauses/literals and tautologies preserves the Boolean function. A unit literal fixes one variable in every satisfying assignment. A variable absent from the residual formula contributes a factor of two. After removing these variables, branching on an active variable partitions assignments into two disjoint sets whose counts add. Incidence components use disjoint variable sets, so their counts multiply. Cached counts are keyed by the canonical residual formula after free variables have been factored out; this makes them independent of eliminated free variables. Recursion strictly reduces active variables or separates components. Resource exhaustion discards incomplete counts.

This is an informal inductive argument plus tests, not a machine-checked proof. The worst case remains exponential; caching can consume exponential space until the configured cap. It is not the polynomial-space subexponential construction reported upstream.

## Expansion order

First obtain trusted baselines and calibrated larger data. Next search deterministic branching/separator policies. Then evaluate bounded-width dynamic programming and component signatures, documenting parameter dependence and canonicalization costs. Only after the upstream proof audit should a track attempt executable extraction. Add graph problems through explicit reductions in a separate namespace. No edits or dependencies on UNIFORM, GRAPH-Lab, or XLAxiom are required.
