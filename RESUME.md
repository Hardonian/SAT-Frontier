# Resume checkpoint — v0.2.1 research checkpoint, 2026-10-28

SAT-Frontier is a CPU-first exact-counting research lab. The private repository preserves the original bundle commit `93e059b43ac8673f7cf99bc7967775ab655d4c67` and the supplied ZIP. No public license has been selected.

## Completed and checked locally

- Original v0.1 archive hash and checksums verified; 20 M0 tests and the example count 18 reproduced. All 160 archived smoke counts were independently recomputed by the included truth-table oracle. The smoke evidence is unchanged.
- Merged independent sharpSAT-TD adapter, explicit process outcomes, development cross-checks, metamorphic tests and mismatch minimization. The integrated-source development campaign in `evidence/v02-integrated-development-001/` has 168 exact paired comparisons and no disagreements, on synthetic formulas including 18–33 variables. This is not an industrial benchmark or proof.
- Preregistered train-only branch-policy campaign: 384 runs, 360 exact oracle matches and 24 node-limited unknowns; no demonstrated practical speedup. The selected component feature is constant at the branch point. See `docs/POLICY_TRAIN_REPORT.md` and its full CSV/JSONL evidence.
- Preregistered held-out policy evaluation (M2/M3): fail-closed atomic reservation `evidence/policy-holdout-v02-consumed/`, 120 independently generated instances (seeds 30001–30030 across 4 families, zero prior overlap), 5 repeats, 1,200 sequential spawned CPU runs. 1,115 exact truth-table oracle matches and 85 node-limited unknowns; 0 crashes or timeouts. Falsified H3 speedup gate; definitive negative result documented in `docs/POLICY_HOLDOUT_REPORT.md` and verified by `verify_holdout_evidence.py`.
- Hypothesis H4 (Graph Separators & Structural Decomposition): Preregistered, implemented in `sat_frontier/separator.py`, unit-tested (5 tests), and executed across 160 CPU runs in `evidence/separator-study-001/`. On barbell bottleneck graphs, cut-vertex branching doubled component splits (2.0 vs 1.0) and yielded a faster median solve time (ratio 0.915). On unstructured expander 3-SAT, search overhead reached 53–59% with zero cut vertices found. Fully documented in `docs/SEPARATOR_REPORT.md` and verified by `verify_evidence.py`.
- Calibrated Scaling Benchmark (n=12..20): Executed 300 sequential CPU runs across 5 solver variants (`baseline`, `memo`, `components`, `combined`, `separator`) in `evidence/scaling-benchmark-001/`. 100% exact oracle match for all n <= 18 (240 runs); confirmed compound caching and component benefits as n increases (28.1% node reduction for combined at n=18). Documented in `docs/SCALING_REPORT.md` and verified by `verify_evidence.py`.
- Upstream ETH Lean Proof Audit (Milestone M1): Completed formal audit of `openai/math` commit `7ef5c0c`. Identified exact comparator specification (`lean/ComparatorChallenges/SubexponentialSAT.lean`), implemented endpoint (`SqrtLogSpace/Final.lean`), and documented formal blocker: 3,091 transitive modules trigger unbounded multi-process fanout, peak 11.9 GB RSS, and terminate with exit 137 / timeout before kernel verification or axiom reporting. Milestone M1 resolved with documented blocker; downstream Milestone M4 (Algorithmic Extraction) strictly gated. Documented in `docs/ETH_AUDIT_V02.md`.
- Local integrated suite: 49 tests passed with cross-platform Windows and Linux support. All verifiers pass.

## Blocked, failed and untested

- GitHub-hosted correctness CI attempted on bootstrap revision `5bf97406188d7a2da8dc23b9ba008c6dee2caa31` but GitHub did not start the job: account payments failed or spending limit must be increased. See https://github.com/Hardonian/SAT-Frontier/actions/runs/40697617863 . No billing change was made. After the owner fixes billing, rerun the latest main correctness run:

  `id=$(GH_CONFIG_DIR=/home/scott/.config/gh gh run list --repo Hardonian/SAT-Frontier --workflow correctness --branch main --limit 1 --json databaseId --jq '.[0].databaseId'); test -n "$id" && GH_CONFIG_DIR=/home/scott/.config/gh gh run rerun "$id" --repo Hardonian/SAT-Frontier`
- Upstream Lean target exited 137 / timed out with 11.9 GB memory peak before kernel check or `#print axioms`; Milestone M4 extraction remains gated.
- Industrial competitiveness and large-scale external benchmark suites remain untested. No speedup, P=NP, GPU result or asymptotic bound is claimed.
- Measured RSS contains an inherited/startup high-water floor and should not be used as comparative memory evidence; RLIMIT_AS is not aggregate RSS. Bandit reports low-severity trust-boundary findings, no medium or high findings; run only trusted external binaries.

## Recheck

```bash
python3 -m unittest discover -s tests -v
python3 -m sat_frontier solve examples/two-components.cnf
python3 verify_policy_evidence.py
python3 verify_holdout_evidence.py
python3 verify_evidence.py evidence/separator-study-001
python3 verify_evidence.py evidence/scaling-benchmark-001
python3 verify_evidence.py evidence/v02-integrated-development-001 --source-root evidence/v02-integrated-development-001/source-snapshot
```

For the original smoke evidence, extract the preserved bootstrap ZIP into a new directory and pass the extracted v0.1 project directory as `--source-root`; see `docs/INDEPENDENT_BASELINE.md`. Without `SAT_FRONTIER_SHARPSAT` the actual external-binary integration test is explicitly skipped. The manifest records source hashes and dirty state at campaign time. Do not overwrite existing evidence directories.
