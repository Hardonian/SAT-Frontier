# Preregistration: Exact Reliability Polynomials and Percolation Phase Transitions via Algebraic Model Counting (Hypothesis H11)

**Date**: 2026-10-29  
**Hypothesis ID**: H11  
**Target Domain**: Algebraic Model Counting over $\mathbb{Z}[x]$, Exact Network Reliability Polynomials, and Finite-Size Percolation Phase Transitions  
**Primary Metric**: Exact integer coefficient agreement ($c_k$) with independent brute-force oracle and susceptibility peak calculation  
**Falsification Condition**: Any coefficient mismatch between algebraic model counting and the exhaustive subgraph oracle, or failure of polynomial operations on planar grids.

---

## 1. Problem Formulation & Algebraic Semiring Duality

In traditional Weighted Model Counting (#WMC), edge operational probabilities $p_e$ are fixed numerical constants, producing a single numerical output $R \in \mathbb{Q}$. When operational parameters vary (e.g. temperature degradation, hardware aging, SLA sensitivity analysis, or phase transition analysis in statistical physics), the entire DPLL search tree must be re-executed for each parameter point.

To evaluate network connectivity continuously across all operational states simultaneously, we reformulate #WMC over the **polynomial semiring** $(\mathbb{Z}[x], +, \times, 0, 1)$.

### 1.1 Polynomial Literal Weights

Let $\Phi$ be the monotone Dual Cut CNF formula representing network connectivity over edge variables $\{x_1, \dots, x_m\}$ ($m = |E|$). We assign polynomial literal weights:
$$w(x_e) = x \quad (\text{edge operates, adding 1 to operational edge count})$$
$$w(\neg x_e) = 1 \quad (\text{edge fails})$$

### 1.2 Model Count in the Polynomial Semiring

The algebraic model count evaluates:
$$P(x) = \sum_{\tau \models \Phi} \prod_{e: \tau(x_e)=\top} x = \sum_{k=0}^m c_k x^k$$
where $c_k \in \mathbb{N}$ is the **exact number of operational subgraphs of cardinality $k$ that connect the target terminals**.

### 1.3 Exact Closed-Form Reliability & Susceptibility

Once the polynomial vector $\mathbf{c} = (c_0, c_1, \dots, c_m)$ is computed:

1. **Instantaneous Point Evaluation**: For any edge probability $p \in [0, 1]$:
   $$R(p) = \sum_{k=0}^m c_k p^k (1 - p)^{m - k}$$
   Evaluated in $O(m)$ arithmetic operations with zero solver re-execution.
2. **Exact Analytic Susceptibility (Percolation Derivative)**:
   $$\chi(p) = \frac{dR}{dp} = \sum_{k=0}^m c_k \left[ k p^{k-1} (1-p)^{m-k} - (m-k) p^k (1-p)^{m-k-1} \right]$$
3. **Finite-Size Percolation Threshold**:
   $$p_c = \arg\max_{p \in (0, 1)} \chi(p)$$
   Identifies the inflection point of the connectivity phase transition on finite planar topologies.

---

## 2. Experimental Design & Benchmark Topologies

The empirical study (`evidence/poly-wmc-001/`) evaluates 24 benchmark instances:

1. **Category A: Planar Grid Topologies ($s=(1,1), t=(R,C)$)**:
   - $2\times 3$ grid ($|V|=6, |E|=7$)
   - $2\times 4$ grid ($|V|=8, |E|=10$)
   - $2\times 5$ grid ($|V|=10, |E|=13$)
   - $2\times 6$ grid ($|V|=12, |E|=16$)
   - $2\times 7$ grid ($|V|=14, |E|=19$)
   - $3\times 3$ grid ($|V|=9, |E|=12$)
   - $3\times 4$ grid ($|V|=12, |E|=17$)
   - $3\times 5$ grid ($|V|=15, |E|=22$)
   - $3\times 6$ grid ($|V|=18, |E|=27$)
   - $4\times 4$ grid ($|V|=16, |E|=24$)
   - $4\times 5$ grid ($|V|=20, |E|=31$)

2. **Category B: Standard Canonical Graphs**:
   - Triangle $K_3$ ($|V|=3, |E|=3$)
   - Complete graph $K_4$ ($|V|=4, |E|=6$)
   - Complete graph $K_5$ ($|V|=5, |E|=10$)
   - Cycle $C_4$ ($|V|=4, |E|=4$)
   - Cycle $C_6$ ($|V|=6, |E|=6$)
   - Cycle $C_8$ ($|V|=8, |E|=8$)

3. **Category C: Bottleneck Barbells**:
   - $B(3, 3, 1)$ ($|V|=7, |E|=7$)
   - $B(4, 4, 1)$ ($|V|=9, |E|=13$)
   - $B(3, 3, 3)$ ($|V|=9, |E|=9$)

4. **Category D: Real-World Mission-Critical Systems**:
   - Cloud Multi-Region VPC
   - Transatlantic Subsea Optical Mesh
   - IEEE 14-Bus Power Grid (Bus 1 to Bus 14)
   - DO-178C Quad-Redundant Actuator

---

## 3. Independent Verification Protocol

For all instances where $|E| \le 16$, an independent brute-force state enumeration oracle (`brute_force_poly_oracle`) exhaustively tests all $2^{|E|}$ subgraphs, verifies $s-t$ connectivity, and bins the exact count by cardinality $k$:

$$\text{oracle\_c}[k] = |\{ E' \subseteq E : |E'| = k \text{ and } s \stackrel{E'}{\longleftrightarrow} t \}|$$

**Acceptance Criteria**:

1. **100% Exact Vector Agreement**: $\mathbf{c}_{\text{poly}} \equiv \mathbf{c}_{\text{oracle}}$ for all $k \in \{0, \dots, |E|\}$.
2. **Point Evaluation Consistency**: Evaluating $R(0.9)$ from the polynomial must identically match `to_cut_cnf` + `wmc_solve` down to the exact irreducible rational fraction.
3. **Analytic Consistency**: For $K_3$, $K_4$, and the Wheatstone bridge, the polynomial must match the known algebraic closed forms.
4. **Cryptographic Integrity**: All DIMACS CNF files, polynomial vectors, and execution logs recorded in `manifest.json` and `SHA256SUMS`.
