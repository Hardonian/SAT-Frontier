# Preregistration: Weighted Model Counting (WMC) & Network Infrastructure Reliability (Milestone M5)

## 1. Motivation and Real-World Objective

In computational logic and risk analysis, decision SAT answers whether a system state exists, whereas **Weighted Model Counting (WMC)** computes the exact probability of an event over an uncertain system state space.

Milestone M5 of SAT-Frontier requires a **useful transfer**: a task-matched real-world application, an explicit reduction, encoding overhead tracking, and verified end-to-end benefit over non-decomposed baselines.

The target domain is **Two-Terminal Network Infrastructure Reliability (2TR)** and **Fault Tree Analysis (FTA)**:

- **Two-Terminal Reliability**: Given a network $G = (V, E)$, source $s$, target $t$, where each edge $e$ fails independently with probability $1 - p_e$ (or functions with probability $p_e \in [0, 1] \cap \mathbb{Q}$), compute the exact probability $R(G, s, t)$ that a functional path connects $s$ and $t$.
- Computing $R(G, s, t)$ is classically $\sharp\text{P}$-complete (Valiant, 1979).

## 2. Theoretical Reduction to Weighted CNF

Let $P_1, P_2, \dots, P_k$ be the elementary simple paths connecting $s$ to $t$ in $G$.
The network is operational if and only if:
$$\Phi_{\text{rel}} = \bigvee_{i=1}^k \left( \bigwedge_{e \in P_i} x_e \right)$$
where Boolean variable $x_e$ represents edge $e$ being operational.

### Encoding & Weight Preservation

1. **Edge Variables**: For each edge $e \in E$, variable $x_e$ has literal weights:
   $$w(x_e) = p_e, \quad w(\neg x_e) = 1 - p_e$$
   Normalized: $w(x_e) + w(\neg x_e) = 1$.
2. **Tseitin Path Variables**: For each path $P_i$, introduce auxiliary indicator $y_i \iff \bigwedge_{e \in P_i} x_e$.
   In CNF clauses:
   - For each $e \in P_i$: $(\neg y_i \lor x_e)$
   - $(\bigvee_{e \in P_i} \neg x_e \lor y_i)$
3. **Top-Level Goal**: Clause $(\bigvee_{i=1}^k y_i)$.
4. **Weight Preservation Invariant**:
   For each auxiliary variable $y_i$, assign neutral weights:
   $$w(y_i) = 1, \quad w(\neg y_i) = 1$$
   *Proof of Count Preservation*:
   For any assignment $\sigma$ to the edge variables $x_E$, each path condition $\bigwedge_{e \in P_i} \sigma(x_e)$ evaluates deterministically to True or False. The Tseitin equivalence forces exactly one truth value for each $y_i$. Thus, there is a unique extension to the $y$ variables. The product of auxiliary weights is $\prod_{i} 1 = 1$. Therefore:
   $$\text{WMC}(\text{CNF}) = \sum_{\sigma \in \text{SAT}(\Phi_{\text{rel}})} \prod_{e \in E} w(\sigma(x_e)) = R(G, s, t)$$
   The reduction preserves exact probabilities without extraneous solution multiplicity.

## 3. Algorithms & Ablations

We evaluate five solver configurations using exact rational arithmetic (`fractions.Fraction`):

1. `baseline_wmc`: Pure DPLL branch-and-bound with unit propagation, no component splitting, no memoization.
2. `memo_wmc`: Weighted DPLL with residual component formula caching.
3. `components_wmc`: Weighted DPLL with dynamic incidence graph connected-component splitting, no caching.
4. `combined_wmc`: Component decomposition + component memoization.
5. `separator_wmc`: Articulation-point cut-vertex branching prioritized before DLCS on the weighted residual formula.

## 4. Test Distributions & Benchmarks

1. **Classic Wheatstone Bridge**: Benchmark 5-edge topology with exact closed-form algebraic reliability $R(p) = 2p^2 + 2p^3 - 5p^4 + 2p^5$.
2. **Backbone / Barbell Networks**: Two dense sub-networks joined by a single critical link (simulating regional datacenters joined by a transoceanic cable).
3. **Grid Mesh Networks**: $2 \times k$ and $3 \times 3$ communication grids with redundant routing.
4. **Ring with Chords**: Circular topology with cross-diameter bypass channels.

## 5. Formal Hypotheses

- **Hypothesis H6a (Correctness)**: On all benchmark network topologies, `wmc_solve` with exact `Fraction` arithmetic matches exhaustive truth-table evaluation and analytic closed forms with zero error.
- **Hypothesis H6b (Component Pruning)**: On modular/backbone topologies, dynamic component decomposition (`components_wmc` and `combined_wmc`) achieves exponential search node reduction relative to `baseline_wmc`.
- **Hypothesis H6c (Separator Advantage)**: Articulation-point branching will detect the backbone link in modular networks at root depth, forcing immediate two-component factorization.
