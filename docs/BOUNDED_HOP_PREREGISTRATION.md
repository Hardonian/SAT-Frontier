# Preregistration: Hypothesis H17 — Bounded-Diameter / Latency-Constrained Network Reliability via Dual L-Hop Cut Compilation

## 1. Background & Scientific Motivation
In modern real-time communications, including High-Frequency Trading (HFT) optical routes, 5G Ultra-Reliable Low-Latency Communications (URLLC), and avionics switched buses (ARINC 664 / AFDX), simple connectivity (path existence) is insufficient. Packets that traverse a path exceeding a strict hop count or latency deadline $L$ violate deterministic timing budgets and are discarded. Operators require **bounded-hop reliability**:
$$R_L(G, s, t) = \mathbb{P}(\text{dist}_{G_{\mathbf{x}}}(s, t) \le L)$$
the probability that an operational path of length at most $L$ connects source $s$ and target $t$ under stochastic link failures.

Prior exact approaches suffer from:
1. Enumerating simple paths of length $\le L$ and asserting their disjunction via auxiliary variables, which suffers from path-explosion on meshed grids;
2. Time-expanded layered DAG formulations which inflate the graph by a factor of $L$, introducing $O(L |V|)$ auxiliary nodes and arcs;
3. Monte Carlo simulations which have high variance for high-nines latency SLAs.

## 2. Hypothesis Formulation
**Hypothesis H17**:
Dual Length-Bounded Cut Monotone CNF Compilation encodes exact bounded-hop reliability $\mathbb{P}(\text{dist}_{G_{\mathbf{x}}}(s, t) \le L)$ with strictly $|E|$ Boolean decision variables and **zero auxiliary routing or layer-expansion variables**. Minimal $L$-hop cuts map directly into monotone positive clauses, enabling exact Weighted Model Counting in sub-millisecond CPU latency on arbitrary meshed networks.

**Falsification Criteria**:
1. Any mathematical mismatch between the exact rational reliability computed by Dual $L$-Hop Cut compilation and an independent BFS shortest-path truth-table oracle across all operational states.
2. Requirement of any auxiliary variable beyond the $|E|$ physical edge variables.
3. Failure to compute exact rational reliability across benchmark suites in sub-second CPU latency.

## 3. Mathematical Theorem & Proof

### Theorem (Dual L-Hop Cut Duality)
Let $G = (V, E)$ be a network where each edge $e \in E$ has operational probability $p_e \in (0, 1]$. Let $L \ge 1$ be the maximum allowable hop count (latency deadline).
An edge subset $C \subseteq E$ is an **$s-t$ $L$-hop cut** if $G \setminus C$ contains no path between $s$ and $t$ of length $\le L$.
$C$ is an **inclusion-minimal $L$-hop cut** if for every $e \in C$, $(G \setminus C) \cup \{e\}$ contains at least one path between $s$ and $t$ of length $\le L$.
Let $\mathcal{C}_{\text{min}}(s, t, L)$ be the set of all inclusion-minimal $L$-hop cuts in $G$.

Then:
1. An operational path of length $\le L$ connects $s$ and $t$ under operational edge state $\mathbf{x} \in \{0, 1\}^{|E|}$ if and only if:
   $$\Phi_L(G, s, t) = \bigwedge_{C \in \mathcal{C}_{\text{min}}(s, t, L)} \left( \bigvee_{e \in C} x_e \right) = 1$$
2. $\Phi_L$ is a monotone positive CNF containing strictly $|E|$ Boolean variables and zero auxiliary variables.
3. The exact bounded-hop reliability is:
   $$\mathbb{P}(\text{dist}_{G_{\mathbf{x}}}(s, t) \le L) = \text{WMC}(\Phi_L, \mathbf{w})$$
   where literal weights are $w(e) = p_e$ and $w(\neg e) = 1 - p_e$.

### Proof
$(\implies)$ Suppose $\text{dist}_{G_{\mathbf{x}}}(s, t) \le L$. There exists an operational path $P \subseteq E$ connecting $s$ and $t$ with $|P| \le L$ such that $x_e = 1$ for all $e \in P$.
By definition of an $L$-hop cut, every $L$-hop cut $C$ must intersect every path of length $\le L$. Therefore, $C \cap P \neq \emptyset$.
For any edge $e^* \in C \cap P$, we have $x_{e^*} = 1$. Hence, $\bigvee_{e \in C} x_e$ evaluates to true for every minimal $L$-cut $C$.

$(\impliedby)$ Suppose $\text{dist}_{G_{\mathbf{x}}}(s, t) > L$.
Let $E_{\text{fail}} = \{e \in E : x_e = 0\}$ be the set of failed edges.
Then in $G \setminus E_{\text{fail}} = G_{\mathbf{x}}$, there is no path between $s$ and $t$ of length $\le L$.
Therefore, $E_{\text{fail}}$ is an $L$-hop cut separating $s$ and $t$.
Every $L$-hop cut contains at least one inclusion-minimal $L$-hop cut $C^* \subseteq E_{\text{fail}}$.
Since $C^* \subseteq E_{\text{fail}}$, $x_e = 0$ for all $e \in C^*$.
Consequently, $\bigvee_{e \in C^*} x_e = 0$, which falsifies the formula $\Phi_L$. $\blacksquare$

## 4. Benchmark Catalog & Experimental Protocol
The benchmark suite evaluates 24 distinct configurations across 5 topological families:
- **Family 1: Wheatstone Bridge under Varying Deadlines**: $L=2$ (shortest paths only) versus $L=3$ (all paths), across $p \in \{0.80, 0.88, 0.92, 0.95\}$.
- **Family 2: 2x3 Ladder Grid**: $L \in \{2, 3, 4\}$ across $p \in \{0.85, 0.92\}$.
- **Family 3: 2x4 Ladder Grid**: $L \in \{3, 4, 5\}$ under $p = 0.90$.
- **Family 4: 5-Node Dense Backbone Mesh**: $L \in \{2, 3\}$ under $p \in \{0.85, 0.95\}$.
- **Family 5: Datacenter Spine-and-Leaf Fabric**: $L \in \{2, 3, 4\}$ under $p = 0.95$.

Every instance is independently evaluated by:
1. Dual $L$-Hop Cut Monotone CNF compilation and Weighted Model Counting.
2. Complete truth-table enumeration using Breadth-First Search (BFS) shortest-path calculations on every surviving state subgraph.
The exact rational reliability values must match identically.

