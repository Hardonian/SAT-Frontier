# Tensor Network Contraction Empirical Study Preregistration (Hypothesis H7)

## Hypothesis H7
**Statement**: Tensor network contraction achieves polynomial/low-exponential intermediate state sizes and out-scales combinatorial DPLL branching on bounded-treewidth CNF formulas (e.g. 2D grid and ladder topologies), but suffers exponential intermediate state blowup on random 3-SAT expanders where combinatorial CDCL/DPLL component branching is required.

## Empirical Design
1. **Target Topologies**:
   - **Planar Grid Formulations** ($L \times L$ grid networks compiled to CNF, treewidth $O(L)$): $L \in \{3, 4, 5\}$.
   - **Ladder Reliability Circuits** (treewidth $O(1)$): length $k \in \{4, 8, 12, 16\}$.
   - **Expander Random 3-SAT** (treewidth $O(n)$): $n \in \{8, 12, 16\}$, clause ratio $\alpha = 3.0, 4.2$.
2. **Solvers Evaluated**:
   - `tensor_einsum`: Single global einsum contraction via NumPy with greedy contraction path.
   - `tensor_bucket`: Min-degree bucket elimination variable contraction.
   - `combined_dpll`: Combinatorial DPLL counting with connected component decomposition and formula memoization.
   - `baseline_dpll`: Flat DPLL backtracking without component decomposition or caching.
3. **Correctness Gates**:
   - Exhaustive oracle verification for $n \le 16$.
   - Zero disagreement tolerated across all solvers.
4. **Hardware and Environment**:
   - CPU-only execution (strictly separated from GPU runs as mandated by `AGENTS.md`).
   - Single-threaded deterministic execution per run.
   - Output directory: `evidence/tensor-study-001/`.
5. **Primary Metrics**:
   - Elapsed CPU wall-clock time (seconds).
   - Exact count match.
   - Peak intermediate tensor rank / dimension.
