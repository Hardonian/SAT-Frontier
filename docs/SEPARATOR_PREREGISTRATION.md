# Preregistration: Graph Separator Decomposition (Hypothesis H4, v0.2.1)

## 1. Background and Motivation

The M3 held-out campaign demonstrated that local, point-wise branching heuristics (such as literal occurrences, polarity balance, and short-clause counts) do not yield structural search reduction and suffer from net runtime regression due to feature calculation overhead.

In exact counting (#SAT), component decomposition provides super-linear speedup when the incidence graph separates into disjoint connected components. When a formula's residual graph is connected, standard DPLL solvers branch on high-occurrence variables without considering whether removing that variable disconnects the graph.

Hypothesis H4 posits that **identifying articulation points (cut vertices) or balanced vertex separators** on the formula's primal/incidence graph and prioritizing branching on separator variables will induce earlier connected-component decomposition, thereby strictly reducing the recursive search tree size (search nodes) on formulas with latent bridge or bottleneck structure.

## 2. Theoretical Invariants

1. **Count preservation**: Branching on variable $v$ partitions satisfying assignments into $v=1$ and $v=0$. Unit propagation fixes forced literals. Eliminating isolated variables multiplies counts by $2^k$. Component counts multiply. The exact count identity $\#SAT(F) = \#SAT(F|_{v=1}) + \#SAT(F|_{v=0})$ holds unconditionally.
2. **Determinism**: Given identical CNF inputs, separator variable selection must be strictly deterministic.
3. **No unsound reductions**: No pure-literal elimination is used.
4. **Adversarial case**: On dense random expander formulas (where no small vertex separator exists), separator analysis will inspect candidate vertices without finding cut vertices, adding $O(V \cdot (V + E))$ graph traversal overhead per node. On such instances, separator-guided branching is expected to exhibit search node parity but higher wall-clock elapsed time.

## 3. Algorithm Specification

Let $G = (V, E)$ be the primal graph of active variables in the residual formula, where $(u, w) \in E$ iff $u$ and $w$ appear together in at least one active clause.
For each candidate variable $v \in V$:
1. Compute the connected components of $G \setminus \{v\}$ using breadth-first search.
2. If the number of components $k(v) \ge 2$, $v$ is an articulation point.
3. Quality of cut: $M(v) = \max_{C \in \text{comps}} |C|$. A smaller maximum component size represents a more balanced partition.
4. Score tuple:
   - `is_cut`: $1$ if $k(v) \ge 2$, else $0$.
   - `balance`: $-M(v)$ if $is\_cut == 1$, else $0$.
   - `components`: $k(v)$ if $is\_cut == 1$, else $1$.
   - `occurrence`: Total occurrences of $v$ in active clauses.
   - `tie_breaker`: $-v$ (lexicographically lowest variable index).
5. Choose $v^* = \arg\max_{v \in V} \text{score}(v)$.

## 4. Evaluation Protocol

- Algorithms:
  - `control`: `combined` (memoization on, component decomposition on, maximum occurrence branching).
  - `separator`: `solve_separator` (memoization on, component decomposition on, separator-guided branching).
- Benchmark Distributions:
  - `barbell`: Barbell graph formulas with two dense clusters connected by a bridge path.
  - `disconnected`: Multi-component formulas with weak interconnects.
  - `planted`: Structured planted-solution formulas.
  - `random`: Uniform random 3-SAT (negative control for graph separation).
- Evaluation Metrics:
  - Recursive search nodes.
  - Number of component splits triggered during search.
  - Solver elapsed time.
  - Exact count verification: 100% agreement between control and separator on every instance.
- Acceptance criteria for H4:
  - Separator branching strictly reduces recursive nodes on structured/bridge formulas.
  - Search node reduction must be accompanied by an increase in component split operations.

