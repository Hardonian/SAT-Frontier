# Preregistration: Hypothesis H22 — The Multi-Commodity Leighton-Rao Routing Gap and Exact Concurrent Flow Duality

## 1. Background & Scientific Motivation

Multi-commodity network reliability concerns the probability that multiple independent demand pairs can concurrently route their traffic across a stochastic communication or transit network without violating shared physical edge capacities.

In literature and previous heuristics, engineers frequently rely on the **Multi-Commodity Cut Condition** (Seymour 1981, Leighton & Rao 1999): for every partition of nodes $(S, V \setminus S)$, the aggregate operational capacity of physical edges crossing the cut must be at least the aggregate demand separated by the cut:

$$\sum_{e \in \delta(S)} c_e x_e \ge \sum_{k: |S \cap \{s_k, t_k\}| = 1} d_k$$

While the celebrated Max-Flow Min-Cut Theorem guarantees that the cut condition is both necessary and sufficient for single-commodity flow, the Okamura-Seymour and Leighton-Rao theorems establish that for general multi-commodity flows, **the cut condition is strictly necessary but NOT sufficient**.

On topologies with crossing demands (such as $C_4$ with diagonally opposite endpoints or $K_{2,3}$ with complete bipartite demands), a network can have 100% of its cut conditions satisfied, yet have **zero simultaneous routing feasibility**. Relying solely on cut-condition counting introduces an unquantified optimistic bias—the **Leighton-Rao Routing Gap**—which can compromise safety-critical infrastructure.

## 2. Hypothesis Formulation

**Hypothesis H22**:
The Multi-Commodity Cut Condition Monotone CNF provides a certified mathematical upper bound on concurrent routing reliability:

$$R_{\text{routing}}(G, \mathcal{K}) \le R_{\text{cut-condition}}(G, \mathcal{K})$$

with exact equality holding if and only if $(G, \mathcal{K})$ satisfies the Seymour-Okamura topological routing conditions (e.g., planar networks with non-crossing boundary terminals or series-parallel topologies). On networks with crossing demands or $K_{2,3}$ / $K_5$ topological minors, a strictly positive Leighton-Rao gap emerges:

$$\Delta_{\text{LR}} = R_{\text{cut-condition}}(G, \mathcal{K}) - R_{\text{routing}}(G, \mathcal{K}) > 0$$

Exact Integer Multi-Commodity Flow (IMCF) compilation evaluates $R_{\text{routing}}(G, \mathcal{K})$ with 100% exact rational precision in $\mathbb{Q}$, certifying both the true routability and the exact Leighton-Rao gap.

**Falsification Criteria**:

1. Any instance where the true concurrent routing reliability exceeds the cut-condition reliability ($R_{\text{routing}} > R_{\text{cut-condition}}$).
2. Any planar series-parallel instance with non-crossing demands where the cut condition fails to match the true routing reliability ($\Delta_{\text{LR}} \neq 0$).
3. Failure to detect the provable routing gap on the canonical $C_4$ crossing instance ($\Delta_{\text{LR}} = 0.6561$) or the $K_{2,3}$ bipartite instance ($\Delta_{\text{LR}} = 0.531441$).
4. Mismatch between the IMCF evaluation and an independent exhaustive state-space oracle across 24 benchmark instances.

## 3. Mathematical Theorem & Proof

### Theorem 14 (The Leighton-Rao Routing Gap & Exact Concurrent Flow Duality)

Let $G = (V, E)$ be a network where physical edge $e \in E$ has integer capacity $c_e \ge 1$ and independent operational survival probability $p_e \in (0, 1]$. Let $\mathcal{K} = \{(s_1, t_1, d_1), \dots, (s_m, t_m, d_m)\}$ be $m$ concurrent commodity demands.

1. **Cut Condition Upper Bound**:
   In any physical state $x \in \{0, 1\}^E$, the existence of a valid concurrent routing $f = (f_1, \dots, f_m)$ requires that for every cut partition $S \subset V$:

   $$\sum_{e \in \delta(S)} c_e x_e \ge \sum_{k: |S \cap \{s_k, t_k\}| = 1} d_k$$

   Therefore, the set of routable states is a subset of the cut-satisfying states:

   $$\mathcal{S}_{\text{routing}} \subseteq \mathcal{S}_{\text{cut-condition}}$$

   Integrating over the probability measure $\mu(x) = \prod_{e: x_e=1} p_e \prod_{e: x_e=0} (1 - p_e)$ yields:

   $$R_{\text{routing}}(G, \mathcal{K}) \le R_{\text{cut-condition}}(G, \mathcal{K})$$

2. **Leighton-Rao Infeasibility Gap**:
   There exist networks where $\mathcal{S}_{\text{cut-condition}} \neq \emptyset$ yet $\mathcal{S}_{\text{routing}} = \emptyset$.
   *Proof*: Consider $C_4 = (V, E)$ with vertices $\{0, 1, 2, 3\}$, edges $E = \{(0, 1), (1, 2), (2, 3), (3, 0)\}$ of unit capacity, and demands $\mathcal{K} = \{(0, 2, 1), (1, 3, 1)\}$.
   Every cut partition $S$ has at least 2 edges crossing $S$, while separating at most 2 units of demand, so the cut condition holds with probability $(9/10)^4 = 6561/10000 = 0.6561$.
   However, commodity 1 requires at least 2 edges, and commodity 2 requires at least 2 edges. Any concurrent routing requires 4 edges; but the only two paths of length 2 for commodity 1 leave a disconnected pair of edges that cannot route commodity 2. Hence $\mathcal{S}_{\text{routing}} = \emptyset$, $R_{\text{routing}} = 0$, and $\Delta_{\text{LR}} = 0.6561$. $\square$

3. **Seymour-Okamura Exactness**:
   When $G$ is series-parallel or planar with terminals on the outer boundary and non-crossing demands, the cut condition is both necessary and sufficient for concurrent fractional/integer routing, yielding $\Delta_{\text{LR}} \equiv 0$.

## 4. Empirical Evaluation Protocol

The empirical study `evidence/routing-gap-001/` evaluates 24 benchmark instances partitioned across 4 topological families:

1. **Family 1 (Non-Crossing Planar / Series-Parallel Topologies)**: 6 instances (Trunk bottleneck, triangle, ladder, series-parallel, tree) where $\Delta_{\text{LR}} = 0$.
2. **Family 2 (Cycle Crossing Demands)**: 6 instances ($C_4, C_5, C_6$) with opposite and crossing endpoints where $\Delta_{\text{LR}} > 0$.
3. **Family 3 (Bipartite $K_{2,3}$ and $K_{2,4}$ Topologies)**: 6 instances with pairwise demands across the independent set where $\Delta_{\text{LR}} > 0$.
4. **Family 4 (Mesh & Grid Networks)**: 6 instances ($2 \times 3, 2 \times 4$ grids, diamond) under partial capacity bottlenecks.

Each instance records:

- Exact routing reliability in $\mathbb{Q}$ (`routing_reliability_exact`)
- Exact cut condition reliability in $\mathbb{Q}$ (`cut_condition_reliability_exact`)
- Exact Leighton-Rao gap in $\mathbb{Q}$ (`leighton_rao_gap_exact`)
- Independent verification against `brute_force_exact_routing_oracle`
- Wall-clock compilation and solving latencies
