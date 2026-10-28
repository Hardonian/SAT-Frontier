# What the result changes

ETH posits a positive exponential rate for worst-case 3-SAT as the variable count grows, up to polynomial input overhead. Its rejection would permit subexponential algorithms without implying a polynomial-time algorithm or resolving P versus NP.

The OpenAI announcement dated October 26, 2026 reports a refutation and Lean formalization, with an expert collaboration examining it. The published scope document states a deterministic exact counter for fixed k-CNF, with polynomial space and time

`(L+1)^(O_k(1)) · 2^(O_k(n (log log n)^2 / sqrt(log n)))`.

It separately attributes sharper manuscript bounds of

`(n+m)^(O_k(1)) · 2^(O_k(n log log n / sqrt(log n)))`,

and, for `m <= Dn` with fixed D,

`(n+m)^(O_{k,D}(1)) · 2^(O_{k,D}(n / sqrt(log n)))`.

L is encoding length, m clause count, n variable count, and k clause-width bound. These are source-reported results, not independently reproduced here. References: S1–S3 in `SOURCES.md`.

## Interpretation

For fixed k, `(log log n)^2/sqrt(log n)` tends to zero. Thus that exponent is o(n), while it can still grow much faster than log(n). This explains how a subexponential bound can coexist with superpolynomial running time. Hidden constants and polynomial overhead can dominate practical inputs. k-dependent constants prohibit reading this as a uniform guarantee when k grows with n.

An exact model count also answers decision SAT by checking whether the count is positive. Conversely, a decision solver alone does not automatically provide an efficient exact counter. Comparisons must match the task.

An ETH-conditional lower-bound theorem retains its logical implication. If its premise is false, that implication no longer supplies the intended hardness evidence. It does not automatically produce a fast algorithm for the target problem. A transfer requires an explicit reduction with variable, clause, encoding-size, parameter, and solution-multiplicity accounting. Counting reductions in particular must track whether they preserve counts.

The useful experimental objective is a narrower one: find transformations or search policies that preserve semantics and improve measured cost on specified instance distributions. Neither a regression fit nor a finite benchmark proves a worst-case asymptotic bound. Successful engineering and a new complexity theorem are separate outputs.

## Formalization audit before extraction

1. Pin an upstream commit and hash the manuscript and formal sources; mutable main URLs are discovery references only.
2. Read the upstream build instructions; reproduce their exact toolchain and dependency locks in an isolated checkout.
3. Locate the implemented proof, the comparator declaration, the connecting theorem, and its full dependency chain. A comparator statement alone is not a proof.
4. Compare input encoding, deterministic machine model, uniformity, fixed-k quantifiers, arithmetic costs, space and time definitions with the manuscript.
5. Inspect axiom reports, trust extensions, placeholders and admitted statements. Text search alone cannot establish the absence of hidden assumptions.
6. Build the precise target and retain logs, commands, exit codes and artifact hashes. Review manuscript-only improvements separately from the weaker formal bound.
7. Extract one algorithmic lemma only after its computational content and cost model are understood. Test an executable version against independent oracles and write a correctness argument for the implementation.

This release has completed source discovery, not those audit steps. The manuscript PDF's content was not extracted in this environment; no claim about its internal mechanism is made.
