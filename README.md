# SAT-Frontier

A CPU-first experimental lab for finding faster **correct** SAT and exact model-counting algorithms. Version 0.2.2 adds an independent exact-counter adapter, resource-aware cross-checks, a bounded policy study, graph separator decomposition, Weighted Model Counting (WMC) for network reliability, Tensor Network Contraction, and high-core parallel Cube-and-Conquer scaling on AMD EPYC. It does not claim a new asymptotic algorithm or P=NP proof.

Start with Python 3.10 or newer. Core runtime and tests use only the standard library; NumPy and PyTorch are optional for tensor contractions.

```bash
python3 -m unittest discover -s tests -v
python3 -m sat_frontier doctor
python3 -m sat_frontier solve examples/two-components.cnf
python3 verify_policy_evidence.py
python3 verify_epyc_evidence.py evidence/epyc-cube-001 evidence/epyc-cube-002
```

The example has 18 satisfying assignments, including its unused variable. `solve` returns exact integer counts, or `unknown` with no count after a resource limit. Exit codes: 0 completed, 1 invalid input/error, 2 unknown. Campaign completion means the protocol finished; inspect its exact/unknown counts before interpreting results.

| Variant | Cache | Components | Branch choice | Scope |
| --- | --- | --- | --- | --- |
| baseline | off | off | most occurrences | Unweighted exact count (#SAT) |
| memo | on | off | most occurrences | Formula cache memoization |
| components | off | on | most occurrences | Connected incidence components |
| combined | on | on | most occurrences | Memoization + component split |
| balanced | on | on | positive × negative occurrences | Variable polarity balance |
| separator | on | on | cut-vertex separator | Articulation point decomposition |
| combined_wmc | on | on | most occurrences | Weighted Model Counting (rational) |
| cube_conquer | on | on | lookahead cube pool | High-core parallel lookahead (EPYC) |
| tensor_contract | N/A | N/A | min-degree bucket / einsum | Multi-linear tensor contraction |

These are established techniques implemented as transparent controls. They are not presented as discoveries or implementations of the released ETH-refuting construction. All variants use unit propagation; none use pure-literal elimination without proof.

Each campaign creates a fresh output directory, raw DIMACS formulas, JSONL and CSV records, frozen configuration, source/test hashes, Git state and an integrity manifest. Outputs cannot overwrite an earlier run.

Read [the research protocol](docs/RESEARCH_PROTOCOL.md), [milestones](docs/MILESTONES.md), [resume checkpoint](RESUME.md), and [Hermes & EPYC Execution Plan](docs/HERMES_EPYC_EXECUTION_PLAN.md).

See [independent counter baseline](docs/INDEPENDENT_BASELINE.md), [policy preregistration](docs/POLICY_PREREGISTRATION.md), [held-out results](docs/POLICY_HOLDOUT_REPORT.md), [upstream ETH audit](docs/ETH_AUDIT_V02.md), [WMC reliability report](docs/WMC_RELIABILITY_REPORT.md), [tensor contraction report](docs/TENSOR_CONTRACTION_REPORT.md), and [EPYC scaling summary](evidence/epyc-cube-002/SCALING_SUMMARY.md).
