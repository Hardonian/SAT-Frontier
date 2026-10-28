# Preregistered branch-policy train campaign

**Outcome: no demonstrated performance win.** The rule in `POLICY_PREREGISTRATION.md` selected `component`, weights `{occurrence: 1, polarity: 1, short_clause: 1, component_size: 1}`. It tied `mixed` on exact completions and total nodes; the preregistered lexical tie-break selected `component`. The component-size term is constant within each branchable incidence component because decomposition precedes branching: it cannot influence this solver's branch ranking. The selected policy is therefore behaviorally identical to `mixed`, not evidence that component size helped. Both are train-selected and are not holdout results.

Data: 32 generated 12-variable instances (8 per family), 2 repeats, 6 policies including the combined control: 384 sequential spawned CPU worker runs, 25-node/0.5-second solver limits and 2.5-second external deadline. All 360 exact outputs matched the independent exhaustive truth-table oracle; 24 results were unknown at the node limit, never counts; there were no wall timeouts, errors, or mismatches. All six policies finished 60 of 64 runs. Aggregate nodes were control/occurrence 814, polarity 798, short 786, mixed/component 782. These totals include capped unknown runs. This small, synthetic train-only study is not a general performance result.

## Paired family results: selected candidate vs combined control

Each fraction has 16 runs on 8 independent instances; both repeats of an instance are clustered for bootstrap. The 95% intervals are percentile bootstrap over instances with 2,000 resamples and are exploratory, uncorrected for five-candidate search. The paired solved difference and CI were 0.000 [0.000, 0.000] for every family; all error and wall-timeout fractions were 0. The only unknowns were four node-limited planted runs for each method. Solved-regression and solved-improvement instance counts were both zero in every family.

| Family | Control / candidate exact fraction | Unknown fraction each | Median solver ms control / candidate, exact only | Median wall ms candidate, all | Median nodes candidate, all | Max worker RSS KiB candidate |
|---|---:|---:|---:|---:|---:|---:|
| random | 1.00 / 1.00 | 0.00 | 4.253 / 4.147 | 46.375 | 13 | 20,420 |
| planted | 0.75 / 0.75 | 0.25 | 4.925 / 5.033 | 58.246 | 15 | 20,388 |
| disconnected | 1.00 / 1.00 | 0.00 | 4.174 / 4.385 | 51.492 | 18 | 20,412 |
| contradictory | 1.00 / 1.00 | 0.00 | 3.128 / 3.389 | 46.197 | 1 | 20,444 |

| Family | Complete paired instances | Median candidate/control solver-time ratio | Median control/candidate speed ratio [95% CI] | Timing-regression instances |
|---|---:|---:|---:|---:|
| random | 8 | 1.011 | 0.990 [0.968, 1.140] | 5 |
| planted | 6 | 1.020 | 0.980 [0.925, 1.123] | 4 |
| disconnected | 8 | 1.061 | 0.943 [0.869, 1.000] | 7 |
| contradictory | 8 | 1.074 | 0.933 [0.855, 1.065] | 5 |

Timing ratios use the mean of each instance's two solver times; time-ratio and speed-ratio medians are taken separately, so they are not necessarily exact reciprocals. These ratios **condition on both methods solving both repeats** and omit the planted node-limited pairs; the solved/unknown fractions above include them. Candidate/control time ratio is an overall measured overhead comparison, not an isolated profiling measurement of feature computation. Timing-regression means the paired candidate mean exceeded the control mean, not statistical significance. The contradictory-unit control typically branches zero times, so apparent differences there are measurement noise, not feature cost. All solver times exclude worker startup; wall includes startup and teardown. Worker peak RSS is Linux `ru_maxrss` in KiB and includes Python runtime; no hard memory limit was applied. Execution was sequential on a shared WSL CPU host, not isolated from other workloads.

Full per-candidate results, raw runs, every CNF, source/config hashes, environment and frozen winner are in `evidence/policy-train-v02/`. The tested implementation was committed as `82a34dfb0e8c177e58ca526f4352ab034af1f2d4` before the run. The manifest's working-tree status includes the newly created evidence directory because the runner creates it before collecting status; source hashes point to the tested source. `python verify_policy_evidence.py` rechecks artifacts, every instance's independent oracle count, row grid, selection and summaries. Hash integrity does not prove general correctness.

## Gates and limitations

- No holdout was run or consumed. The preregistration specifies 30 fresh seeds per family and five repeats, including source-hash and instance-overlap guards that **must still be implemented** by any future holdout runner. Do not treat the train-only runner as a holdout runner.
- No pinned mature external exact counter is used here. The future performance gate requires that baseline and fresh held-out analysis; repeated timings are not independent instances. Sample size is small and intervals are exploratory; no multiplicity correction or industrial benchmark is claimed.
- `python -m unittest discover -s tests -v`: 27 tests passed. CLI example returned exact count 18. `python verify_policy_evidence.py`: 384 records, 32 instances, 360 oracle-checked exact results, verified. The tests at the tested revision have SHA-256: `tests/test_core.py` = `6971205c6a974a725612d56d7355f85ca733947d1fe9b545483b6a56c69b839d`; `tests/test_policy.py` = `8ed3b9c6dce8edd49fb5b30cafc1ac10e8ae1b12209b08cfa8f816bee264f5e6`. These hashes supplement the campaign manifest, which omits test-file hashes.
- Existing `python verify_evidence.py evidence/smoke-train` reports `source hash mismatch: sat_frontier/core.py` against the intentionally modified working tree. The historical core at base revision `5bf9740` matches its recorded hash `3cff957d7c560ab61e2d1b5fba7e20dab403a7c0f937dd161ec402ff86ba04c3`; smoke artifact and instance hashes were independently checked and match. The original evidence was not modified.
- Bandit on all changed Python: 0 medium/high and 4 low findings, exit 1, no suppressions. B311 is the intentionally seeded statistical bootstrap PRNG, not security randomness. B404 and two B603 findings cover fixed-argument, no-shell Git metadata subprocesses with a resolved executable; they are not user-supplied shell commands. These remain visible rather than being suppressed.
