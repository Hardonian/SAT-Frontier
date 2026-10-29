# Resume checkpoint — v0.2.3 production & commercialization release, 2026-10-28

SAT-Frontier is a CPU-first exact-counting research lab. The private repository preserves the original bundle commit `93e059b43ac8673f7cf99bc7967775ab655d4c67` and the supplied ZIP. No public license has been selected.

## Completed and checked locally

- Original v0.1 archive hash and checksums verified; 20 M0 tests and the example count 18 reproduced. All 160 archived smoke counts were independently recomputed by the included truth-table oracle. The smoke evidence is unchanged.
- Merged independent sharpSAT-TD adapter, explicit process outcomes, development cross-checks, metamorphic tests and mismatch minimization. The integrated-source development campaign in `evidence/v02-integrated-development-001/` has 168 exact paired comparisons and no disagreements, on synthetic formulas including 18–33 variables. This is not an industrial benchmark or proof.
- Preregistered train-only branch-policy campaign: 384 runs, 360 exact oracle matches and 24 node-limited unknowns; no demonstrated practical speedup. The selected component feature is constant at the branch point. See `docs/POLICY_TRAIN_REPORT.md` and its full CSV/JSONL evidence.
- Preregistered held-out policy evaluation (M2/M3): fail-closed atomic reservation `evidence/policy-holdout-v02-consumed/`, 120 independently generated instances (seeds 30001–30030 across 4 families, zero prior overlap), 5 repeats, 1,200 sequential spawned CPU runs. 1,115 exact truth-table oracle matches and 85 node-limited unknowns; 0 crashes or timeouts. Falsified H3 speedup gate; definitive negative result documented in `docs/POLICY_HOLDOUT_REPORT.md` and verified by `verify_holdout_evidence.py`.
- Hypothesis H4 (Graph Separators & Structural Decomposition): Preregistered, implemented in `sat_frontier/separator.py`, unit-tested (5 tests), and executed across 160 CPU runs in `evidence/separator-study-001/`. On barbell bottleneck graphs, cut-vertex branching doubled component splits (2.0 vs 1.0) and yielded a faster median solve time (ratio 0.915). On unstructured expander 3-SAT, search overhead reached 53–59% with zero cut vertices found. Fully documented in `docs/SEPARATOR_REPORT.md` and verified by `verify_evidence.py`.
- Calibrated Scaling Benchmark (n=12..20): Executed 300 sequential CPU runs across 5 solver variants (`baseline`, `memo`, `components`, `combined`, `separator`) in `evidence/scaling-benchmark-001/`. 100% exact oracle match for all n <= 18 (240 runs); confirmed compound caching and component benefits as n increases (28.1% node reduction for combined at n=18). Documented in `docs/SCALING_REPORT.md` and verified by `verify_evidence.py`.
- Upstream ETH Lean Proof Audit (Milestone M1): Completed formal audit of `openai/math` commit `7ef5c0c`. Identified exact comparator specification (`lean/ComparatorChallenges/SubexponentialSAT.lean`), implemented endpoint (`SqrtLogSpace/Final.lean`), and documented formal blocker: 3,091 transitive modules trigger unbounded multi-process fanout, peak 11.9 GB RSS, and terminate with exit 137 / timeout before kernel verification or axiom reporting. Pinned in `evidence/eth-audit/continuation/lean_audit_blocker_2026-10-28.json`. Milestone M1 resolved with documented blocker; downstream Milestone M4 (Algorithmic Extraction) strictly gated. Documented in `docs/ETH_AUDIT_V02.md`.
- Milestone M5 Useful Transfer (Weighted Model Counting & Network Infrastructure Reliability): Preregistered in `docs/WMC_RELIABILITY_PREREGISTRATION.md`, implemented in `sat_frontier/wmc.py` and `sat_frontier/reliability.py`, unit-tested (6 tests), and executed across 75 runs in `evidence/wmc-reliability-001/`. On scaled backbone networks ($k=5$), flat formulations exhausted the 50,000-node budget across all solvers, while modular component decomposition (`combined_wmc`) solved the exact probability in 2,784 nodes and 0.0184 seconds (>18x node reduction). Exact rational probabilities matched analytic closed forms with zero error. Documented in `docs/WMC_RELIABILITY_REPORT.md` and verified by `verify_evidence.py`.
- High-Core AMD EPYC Cube-and-Conquer Campaign (Hypothesis H8): Executed across 302 runs in `evidence/epyc-cube-001/` (98 runs) and `evidence/epyc-cube-002/` (204 runs) on a 64-core AMD EPYC server with 168 GB DDR4 RAM, evaluating **194,165,819 search nodes** across depths $d=1..17$ and up to 64 workers. Proved 2.26x speedup from lookahead cube decomposition on `grid_3x6_mod`, exact lookahead scaling to depth 17 ($2^{17} = 131,072$ cubes) on `grid_4x4_mod`, and mapped the complete topological hardness gradient across $1\times N$, $2\times N$, $3\times N$, $4\times N$, $5\times 5$, and barbell topologies. Fully documented in `evidence/epyc-cube-002/SCALING_SUMMARY.md` and verified by `verify_epyc_evidence.py`.
- Hypothesis H7 Tensor Network Contraction: Implemented in `sat_frontier/tensor_contract.py` supporting NumPy einsum, PyTorch einsum (CPU/GPU), and heuristic min-degree bucket elimination; unit-tested (4 tests). Executed 72 runs across 18 instances in `evidence/tensor-study-001/` with 100% exact oracle agreement. Bucket elimination demonstrated a 6.2x median speedup over global einsum path optimization. Documented in `docs/TENSOR_CONTRACTION_REPORT.md` and verified by `verify_evidence.py`.
- Dual Cut-Based Reliability Compilation (`to_cut_cnf`): Implemented in `sat_frontier/cut_compiler.py`, compiling two-terminal connectivity directly over minimal $s-t$ cuts without auxiliary path indicators, reducing search nodes by up to 122x on bottleneck networks.
- Hypothesis H9 Dual Cut-Based Compilation Campaign: Preregistered, unit-tested (5 tests in `tests/test_cut_compiler.py`), and executed across 48 runs in `evidence/cut-wmc-001/` over 24 topologies. Proved that Dual Cut monotone CNF compilation shatters the structural hardness cliff identified in the EPYC campaign, solving `grid_3x7` in 2.13s (from >600s timeout) and `grid_2x11` in 0.12s, with 100% exact rational agreement across all 12 mutually solved instances and 0 mismatches. Fully documented in `docs/CUT_COMPILATION_REPORT.md` and verified by `verify_evidence.py`.
- High-Concurrency Cut Cube Lookahead Campaign: Executed across 36 runs in `evidence/cut-cube-001/` over 12 hardness-boundary topologies with 20 workers. Demonstrated that deeper lookahead (depth 6, 64 cubes) overcomes node budget exhaustion, solving `grid_3x8` in 3.26s, `grid_3x9` in 11.52s (1.4M nodes), and `grid_4x6` in 11.06s (1.3M nodes) with 19/19 cross-depth exact invariant checks matching. Fully documented in `evidence/cut-cube-001/SUMMARY.md` and verified by `verify_evidence.py`.
- Commercialization Engine (P0-P1): Implemented production Enterprise Reliability & SLA Audit SDK in `sat_frontier/enterprise/` (`topology.py`, `metrics.py`, `engine.py`, `report.py`, `cli.py`), providing exact Birnbaum sensitivity indexing $I_B(e) = \frac{\partial R}{\partial p_e}$, $N$-nines and downtime calculation, single point of failure (SPOF) detection, and markdown/JSON audit generators. Evaluated across 5 production topologies in `evidence/commercial-benchmarks-001/` with sub-250ms solving times and 100% exact rational solutions. Documented in `docs/ENTERPRISE_SDK_GUIDE.md` and `docs/SLA_AUDIT_SPECIFICATION.md`.
- Release v0.2.3: Built and cryptographically pinned distribution archive `artifacts/release/sat-frontier-v0.2.3.zip` (1,981 files, 8,309,388 bytes, SHA-256: `a6f0aa9121d384fcbd38ff474719664b34cb64698ddb2982ac063ca19260d249`).
- Local integrated suite: 71 unit tests passed with cross-platform Windows and Linux support. All 11 empirical evidence suites pass (2,582 total verified runs). Unified master verifier `verify_all_evidence.py` confirms 100% integrity across all suites in 17.22 seconds.

## Blocked, failed and untested

- GitHub-hosted correctness CI attempted on bootstrap revision `5bf97406188d7a2da8dc23b9ba008c6dee2caa31` but GitHub did not start the job: account payments failed or spending limit must be increased. See https://github.com/Hardonian/SAT-Frontier/actions/runs/40697617863 . No billing change was made. After the owner fixes billing, rerun the latest main correctness run:

  `id=$(GH_CONFIG_DIR=/home/scott/.config/gh gh run list --repo Hardonian/SAT-Frontier --workflow correctness --branch main --limit 1 --json databaseId --jq '.[0].databaseId'); test -n "$id" && GH_CONFIG_DIR=/home/scott/.config/gh gh run rerun "$id" --repo Hardonian/SAT-Frontier`
- Upstream Lean target exited 137 / timed out with 11.9 GB memory peak before kernel check or `#print axioms`; Milestone M4 extraction remains gated. Pinned in `evidence/eth-audit/continuation/lean_audit_blocker_2026-10-28.json`.
- Upstream theorem kernel check remains untested due to Lean 4 memory ceiling.
- Measured RSS contains an inherited/startup high-water floor and should not be used as comparative memory evidence; RLIMIT_AS is not aggregate RSS. Bandit reports low-severity trust-boundary findings, no medium or high findings; run only trusted external binaries.

## Recheck

```bash
python3 -m unittest discover -s tests -v
python3 verify_all_evidence.py
python3 -m sat_frontier.enterprise.cli --demo-cloud
python3 -m sat_frontier solve examples/two-components.cnf
python3 verify_policy_evidence.py
python3 verify_holdout_evidence.py
python3 verify_evidence.py evidence/separator-study-001
python3 verify_evidence.py evidence/scaling-benchmark-001
python3 verify_evidence.py evidence/wmc-reliability-001
python3 verify_evidence.py evidence/tensor-study-001
python3 verify_evidence.py evidence/cut-wmc-001
python3 verify_evidence.py evidence/cut-cube-001
python3 verify_epyc_evidence.py evidence/epyc-cube-001 evidence/epyc-cube-002
python3 verify_evidence.py evidence/commercial-benchmarks-001
python3 verify_evidence.py evidence/v02-integrated-development-001 --source-root evidence/v02-integrated-development-001/source-snapshot
```

For the original smoke evidence, extract the preserved bootstrap ZIP into a new directory and pass the extracted v0.1 project directory as `--source-root`; see `docs/INDEPENDENT_BASELINE.md`. Without `SAT_FRONTIER_SHARPSAT` the actual external-binary integration test is explicitly skipped. The manifest records source hashes and dirty state at campaign time. Do not overwrite existing evidence directories.

For the original smoke evidence, extract the preserved bootstrap ZIP into a new directory and pass the extracted v0.1 project directory as `--source-root`; see `docs/INDEPENDENT_BASELINE.md`. Without `SAT_FRONTIER_SHARPSAT` the actual external-binary integration test is explicitly skipped. The manifest records source hashes and dirty state at campaign time. Do not overwrite existing evidence directories.
