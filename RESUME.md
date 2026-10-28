# Resume checkpoint — v0.2 research draft, 2026-10-28

SAT-Frontier is a CPU-first exact-counting research lab. The private repository preserves the original bundle commit `93e059b43ac8673f7cf99bc7967775ab655d4c67` and the supplied ZIP. No public license has been selected.

## Completed and checked locally

- Original v0.1 archive hash and checksums verified; 20 M0 tests and the example count 18 reproduced. All 160 archived smoke counts were independently recomputed by the included truth-table oracle. The smoke evidence is unchanged.
- Merged independent sharpSAT-TD adapter, explicit process outcomes, development cross-checks, metamorphic tests and mismatch minimization. The integrated-source development campaign in `evidence/v02-integrated-development-001/` has 168 exact paired comparisons and no disagreements, on synthetic formulas including 18–33 variables. This is not an industrial benchmark or proof.
- Preregistered train-only branch-policy campaign: 384 runs, 360 exact oracle matches and 24 node-limited unknowns; no demonstrated practical speedup. The selected component feature is constant at the branch point. See `docs/POLICY_TRAIN_REPORT.md` and its full CSV/JSONL evidence. Holdout has not been consumed.
- Local integrated suite: 35 tests passed with the selected external binary installed locally, including its real executable test. Run the suite again when evaluating a new revision. `verify_policy_evidence.py` validates the frozen historical policy run; `verify_evidence.py` checks recorded hashes against the original matching source snapshots.

## Blocked, failed and untested

- Hosted correctness CI attempted on bootstrap revision `5bf97406188d7a2da8dc23b9ba008c6dee2caa31` but GitHub did not start the job: account payments failed or spending limit must be increased. See https://github.com/Hardonian/SAT-Frontier/actions/runs/40697617863 . No billing change was made. After the owner fixes billing, rerun the latest main correctness run:

  `id=$(GH_CONFIG_DIR=/home/scott/.config/gh gh run list --repo Hardonian/SAT-Frontier --workflow correctness --branch main --limit 1 --json databaseId --jq '.[0].databaseId'); test -n "$id" && GH_CONFIG_DIR=/home/scott/.config/gh gh run rerun "$id" --repo Hardonian/SAT-Frontier`
- The upstream ETH formalization build timed out and comparator tooling was unavailable; no kernel-checked theorem, statement correspondence or actual theorem axiom report was obtained. Exact next commands and pinned provenance are in `docs/ETH_AUDIT_V02.md`. M1 is not complete.
- Holdout is unrun. Before any use, implement the preregistered source-hash and train-overlap guards, freeze integrated source and configuration, and use a fresh preregistered holdout. No speedup, P=NP, GPU result or asymptotic bound is claimed.
- Measured RSS contains an inherited/startup high-water floor and should not be used as comparative memory evidence; RLIMIT_AS is not aggregate RSS. Bandit reports low-severity trust-boundary findings, no medium or high findings; run only trusted external binaries.

## Recheck

```bash
python3 -m unittest discover -s tests -v
python3 -m sat_frontier solve examples/two-components.cnf
python3 verify_policy_evidence.py
python3 verify_evidence.py evidence/v02-integrated-development-001 --source-root evidence/v02-integrated-development-001/source-snapshot
```

For the original smoke evidence, extract the preserved bootstrap ZIP into a new directory and pass the extracted v0.1 project directory as `--source-root`; see `docs/INDEPENDENT_BASELINE.md`. Without `SAT_FRONTIER_SHARPSAT` the actual external-binary integration test is explicitly skipped. The manifest records source hashes and dirty state at campaign time. Do not overwrite existing evidence directories.
