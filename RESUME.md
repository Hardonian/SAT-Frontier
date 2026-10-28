# Resume checkpoint — 2026-10-28

Goal: find faster correct SAT/#SAT algorithms through reproducible experiments, motivated by the reported ETH refutation. Current preparation release: M0, version 0.1.0.

Delivered: exact-count DPLL baseline, memo/component ablations, balanced-branch candidate, independent truth-table oracle, strict DIMACS parsing, deterministic synthetic families, isolated campaign workers, config limits, raw formulas/CSV/JSONL, hash manifests, CI definition, source review and next Hermes commission.

Verified locally with Python 3.12.14 on CPU: 20 unittest tests passed. Included exhaustive enumeration of 512 subsets of the two-variable non-tautological clause set, 180 random mixed-width formulas and 40 generated family cases, all compared across five variants. These are bounded checks plus an informal correctness argument, not formal verification. The example returns 18. Smoke train campaign: 32 cases, 160 exact runs, 160 independent oracle matches, zero unknowns/errors. Holdout campaign not run. GitHub CI has not run.

Sources located/read as documented in docs/SOURCES.md. The manuscript PDF was not extracted, Lean was not built, theorem dependencies were not audited, and the announced construction was not implemented. No mature solver, GPU, remote host, external repository, public release, industrial benchmark or asymptotic improvement is claimed.

Next: follow HERMES_COMMISSION.md to pin sources, audit/build the upstream proof if possible, integrate an independent exact counter, add RSS/cross-checks and search a bounded policy space. Read docs/RESEARCH_PROTOCOL.md before using holdout seeds. Preserve evidence/smoke-train without edits.

```bash
python3 -m unittest discover -s tests -v
python3 -m sat_frontier solve examples/two-components.cnf
python3 -m sat_frontier campaign --config configs/smoke.json --out experiments/train-002 --split train
```

Run manifests are authoritative for source hashes. The initial smoke run predates Git initialization; its git_revision is null by design. Verify current state rather than treating this note as a substitute for Git inspection.
