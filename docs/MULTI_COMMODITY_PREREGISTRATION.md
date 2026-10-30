# Preregistration: Hypothesis H18 — Multi-Commodity Capacitated Flow Reliability via Dual Cut Duality

## 1. Background & Scientific Motivation

In multi-tenant cloud backbones, 5G network slicing, and multi-datacenter replication, network operators must satisfy concurrent multi-point bandwidth allocations:
$$\mathbb{P}\left(\forall k \in \{1, \dots, K\}, \; \text{ConcurrentFlow}(G_{\mathbf{x}}, s_k, t_k) \ge d_k\right)$$
where multiple source-destination pairs $(s_k, t_k)$ concurrently compete for shared bottleneck edge capacities $c_e$ under stochastic physical edge failures.

Standard multi-commodity flow exact evaluation requires:

1. Solving $2^{|E|}$ multi-commodity flow linear programs, or
2. Encoding massive multicommodity multicommodity flow conservation constraints into SAT/PB formulas with $O(K \cdot |E|)$ auxiliary flow variables.

## 2. Hypothesis Formulation

**Hypothesis H18**:
Dual Multi-Cut Threshold Monotone CNF Compilation encodes concurrent multi-commodity demand feasibility with strictly $|E|$ physical edge variables and **zero auxiliary flow or commodity routing variables**. The compilation maps minimal capacity-breaking subsets across all commodity-separating cut partitions into monotone positive clauses, enabling exact Weighted Model Counting with 100% rational precision.

**Falsification Criteria**:

1. Any numerical or rational discrepancy between compiled Dual Cut WMC and an exhaustive $2^{|E|}$ multi-commodity cut verification oracle across all benchmark instances.
2. Introduction of any auxiliary variables beyond the $|E|$ physical edge variables.
3. Execution failure or non-terminating search on standard benchmark topologies.

## 3. Mathematical Theorem & Proof

### Theorem 10 (Multi-Commodity Dual Cut Duality Theorem)

Let $G = (V, E, \mathbf{c})$ be a capacitated network where each edge $e \in E$ has integer capacity $c_e \ge 1$ and operational probability $p_e \in (0, 1]$. Let $K = \{(s_1, t_1, d_1), \dots, (s_m, t_m, d_m)\}$ be a set of $m$ concurrent commodity demands.

For any cut partition $(S, V \setminus S)$, let $K(S) = \{k : |S \cap \{s_k, t_k\}| = 1\}$ be the set of commodities separated by cut $S$, with aggregate crossing demand:
$$D(S) = \sum_{k \in K(S)} d_k$$

In any operational state $\mathbf{x} \in \{0, 1\}^{|E|}$, concurrent demand feasibility requires that for every cut partition $S$ with $D(S) > 0$:
$$\sum_{e \in \Delta(S)} c_e x_e \ge D(S)$$

For each cut partition $S$, let $\mathcal{F}_{\min}(\Delta(S), D(S))$ be the set of inclusion-minimal capacity-breaking edge subsets. Then:

1. The capacity requirement across $S$ compiles into monotone positive clauses:
   $$\sum_{e \in \Delta(S)} c_e x_e \ge D(S) \iff \bigwedge_{F \in \mathcal{F}_{\min}(\Delta(S), D(S))} \left( \bigvee_{e \in F} x_e \right)$$
2. The exact multi-commodity reliability formula is:
   $$\Phi_{\text{mc}}(G, K) = \bigwedge_{S: D(S) > 0} \bigwedge_{F \in \mathcal{F}_{\min}(\Delta(S), D(S))} \left( \bigvee_{e \in F} x_e \right)$$
3. $\Phi_{\text{mc}}$ contains strictly $|E|$ variables and zero auxiliary variables.

### Proof

1. **Necessity**: In any valid concurrent flow, the total flow routed across cut partition $(S, V \setminus S)$ must equal or exceed the total demand of all commodities whose endpoints lie on opposite sides of the cut, $\sum_{k \in K(S)} d_k = D(S)$. By flow conservation, the maximum flow that can physically cross $S$ in state $\mathbf{x}$ cannot exceed the total surviving capacity $\sum_{e \in \Delta(S)} c_e x_e$. Therefore, $\sum_{e \in \Delta(S)} c_e x_e \ge D(S)$ is a necessary condition for feasibility for every cut partition $S$.
2. **Monotone Clause Representation**: A subset of edges $F \subseteq \Delta(S)$ fails to meet demand $D(S)$ if $\sum_{e \in \Delta(S) \setminus F} c_e < D(S)$. To satisfy the demand, not all edges in $F$ can fail simultaneously. Thus, at least one edge in each inclusion-minimal failing subset $F$ must survive: $\bigvee_{e \in F} x_e = 1$.
3. **Variable Bound**: Every literal in $\Phi_{\text{mc}}$ corresponds directly to an edge index $e \in \{1, \dots, |E|\}$. No auxiliary flow variables $f_{uv}^k$, path variables, or step counters are introduced. $\Phi_{\text{mc}}$ contains strictly $|E|$ variables. $\blacksquare$

## 4. Benchmark Protocol

1. 24 benchmark instances spanning:
   - Line networks with shared transit links
   - Star topologies with central hubs
   - Complete graphs $K_4, K_5$ with competing multi-terminal commodities
   - Ring backbones with multi-point ingress/egress
   - Grid and ladder mesh topologies ($2 \times 3, 2 \times 4, 3 \times 3$)
2. Independent verification: every instance evaluated against exhaustive $2^{|E|}$ truth-table oracle checks.
3. Zero tolerance: 100% exact rational agreement required.
