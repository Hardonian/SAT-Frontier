# SAT-Frontier

A CPU-first experimental lab for finding faster **correct** SAT and exact model-counting algorithms. Version 0.2 adds an independent exact-counter adapter, resource-aware cross-checks and a bounded policy study. It does not claim a new asymptotic algorithm or demonstrated practical speedup.

Start with Python 3.10 or newer. Runtime and tests use only the standard library; installation is optional.

```bash
python3 -m unittest discover -s tests -v
python3 -m sat_frontier doctor
python3 -m sat_frontier solve examples/two-components.cnf
python3 verify_policy_evidence.py
python3 -m sat_frontier campaign --config configs/smoke.json --out experiments/train-001 --split train
```

The example has 18 satisfying assignments, including its unused variable. `solve` returns exact integer counts, or `unknown` with no count after a resource limit. Exit codes: 0 completed, 1 invalid input/error, 2 unknown. Campaign completion means the protocol finished; inspect its exact/unknown counts before interpreting results.

| Variant | Cache | Components | Branch choice |
| --- | --- | --- | --- |
| baseline | off | off | most occurrences |
| memo | on | off | most occurrences |
| components | off | on | most occurrences |
| combined | on | on | most occurrences |
| balanced | on | on | positive × negative occurrences |

These are established techniques implemented as transparent controls. They are not presented as discoveries or implementations of the released ETH-refuting construction. All variants use unit propagation; none use pure-literal elimination, which is not generally count-preserving.

Each campaign creates a fresh output directory, raw DIMACS formulas, JSONL and CSV records, frozen configuration, source/test hashes, Git state and an integrity manifest. Outputs cannot overwrite an earlier run. Campaign workers have a hard wall limit of the solver allowance plus two seconds; direct `solve` uses cooperative checks. Optional Linux `memory_bytes` enforces RLIMIT_AS per worker, not an aggregate RSS limit; unsupported platforms explicitly report the limitation. Peak RSS is reported with the measurement caveats in [the baseline notes](docs/INDEPENDENT_BASELINE.md). Use trusted, reasonably sized inputs and trusted external executables; this is a research harness, not a hardened public service.

Read [the ETH analysis](docs/ETH_ANALYSIS.md), [research protocol](docs/RESEARCH_PROTOCOL.md), [milestones](docs/MILESTONES.md), and [resume checkpoint](RESUME.md). The next execution commission is [HERMES_COMMISSION.md](HERMES_COMMISSION.md).

See [independent counter build and run](docs/INDEPENDENT_BASELINE.md), [policy preregistration](docs/POLICY_PREREGISTRATION.md), [train results](docs/POLICY_TRAIN_REPORT.md), and [upstream ETH audit](docs/ETH_AUDIT_V02.md). The historic smoke verifier requires the v0.1 source root because it checks the exact source hashes used by that run; see the baseline notes for a portable extraction command. Held-out policy evaluation and the upstream Lean proof check remain incomplete. No license for public redistribution has been selected.
