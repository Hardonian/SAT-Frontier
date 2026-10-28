# SAT-Frontier

A CPU-first experimental lab for finding faster **correct** SAT and exact model-counting algorithms. Version 0.1 establishes the measurement and correctness infrastructure; it does not claim a new asymptotic algorithm.

Start with Python 3.10 or newer. Runtime and tests use only the standard library; installation is optional.

```bash
python3 -m unittest discover -s tests -v
python3 -m sat_frontier doctor
python3 -m sat_frontier solve examples/two-components.cnf
python3 verify_evidence.py evidence/smoke-train
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

Each campaign creates a fresh output directory, raw DIMACS formulas, JSONL and CSV records, frozen configuration, source hashes, environment details, and an integrity manifest. Outputs cannot overwrite an earlier run. Campaign workers have a hard wall limit of the solver allowance plus two seconds; direct `solve` uses cooperative checks. Cache entry counts are capped, but byte-level RAM limits are not implemented. Use trusted, reasonably sized inputs. This is a research harness, not a hardened public service.

Read [the ETH analysis](docs/ETH_ANALYSIS.md), [research protocol](docs/RESEARCH_PROTOCOL.md), [milestones](docs/MILESTONES.md), and [resume checkpoint](RESUME.md). The next execution commission is [HERMES_COMMISSION.md](HERMES_COMMISSION.md).

Prepared locally on 2026-10-28. Source verification is attributed in `docs/SOURCES.md`; no Lean build or source-level proof audit has been performed here. No remote repository or production deployment is implied. Third-party baseline integration and larger held-out studies are explicit next milestones.
