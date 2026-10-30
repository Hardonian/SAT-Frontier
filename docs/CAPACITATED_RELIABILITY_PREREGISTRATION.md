# Preregistration: Hypothesis H16 — Capacitated Network Flow Reliability via Dual Cut Threshold Compilation

## 1. Background & Scientific Motivation

In telecommunications (MPLS traffic engineering, 5G backhaul), energy distribution (substation capacity planning), supply chain logistics, and datacenter spine-and-leaf interconnects, binary connectivity (path existence) is insufficient. Network operators require **capacitated reliability**:
$$\mathbb{P}(\text{MaxFlow}(G, s, t) \ge D)$$
the probability that the surviving physical network can route at least $D$ units of simultaneous throughput under stochastic component failures.

Traditional exact approaches to capacitated reliability suffer from severe combinatorial intractability:

1. **Multi-commodity flow linear programming over all states**: Requires solving $2^{|E|}$ LP problems.
2. **Standard SAT/PB encodings**: Introduce hundreds to thousands of auxiliary flow conservation variables $f_{uv}$, capacity bounds $0 \le f_{uv} \le c_{uv} x_{uv}$, and demand sum constraints, yielding bloated CNFs with dense hyperedges and poor DPLL unit propagation.
3. **Approximation methods**: Monte Carlo failure injection gives high variance and fails to resolve high-nines reliability requirements.

## 2. Hypothesis Formulation

**Hypothesis H16**:
Dual Cut Threshold Monotone CNF Compilation encodes exact multi-unit demand connectivity $\mathbb{P}(\text{MaxFlow}(s, t) \ge D)$ with strictly $|E|$ Boolean decision variables and **zero auxiliary flow or routing variables**. The compilation maps minimal capacity-breaking subsets of minimal cuts into monotone positive clauses, enabling exact Weighted Model Counting in microsecond to millisecond latency on arbitrary meshed networks.

**Falsification Criteria**:

1. Any mathematical mismatch between the exact rational reliability computed by Dual Cut Threshold compilation and an independent Dinic maximum-flow truth-table oracle across all operational states.
2. Requirement of any auxiliary variable beyond the $|E|$ physical edge variables.
3. Failure to compute exact rational reliability across benchmark suites in sub-second CPU latency.

## 3. Mathematical Theorem & Proof

### Theorem (Capacitated Dual Cut Duality)

Let $G = (V, E)$ be a network where each edge $e \in E$ has integer capacity $c_e \ge 1$ and independent operational probability $p_e \in (0, 1]$. Let $D \ge 1$ be the target demand between source $s$ and target $t$.

Let $\mathcal{C}_{\text{min}}(s, t)$ be the set of all inclusion-minimal $s$-$t$ edge cuts in $G$.
For any minimal cut $C \in \mathcal{C}_{\text{min}}(s, t)$, let $F \subseteq C$ be an **inclusion-minimal capacity-breaking subset** if:
$$\sum_{e \in C \setminus F} c_e < D \quad \text{and} \quad \forall e \in F, \; \sum_{e' \in (C \setminus F) \cup \{e\}} c_{e'} \ge D$$
Let $\mathcal{F}_{\text{min}}(C, D)$ denote the set of all such minimal capacity-breaking subsets of $C$.

Then:

1. The maximum $s$-$t$ flow is at least $D$ under operational edge state $\mathbf{x} \in \{0, 1\}^{|E|}$ if and only if:
   $$\Phi_{\text{cap}}(G, s, t, D) = \bigwedge_{C \in \mathcal{C}_{\text{min}}(s, t)} \bigwedge_{F \in \mathcal{F}_{\text{min}}(C, D)} \left( \bigvee_{e \in F} x_e \right) = 1$$
2. $\Phi_{\text{cap}}$ is a monotone positive CNF containing strictly $|E|$ Boolean variables and zero auxiliary variables.
3. The exact capacitated reliability is:
   $$\mathbb{P}(\text{MaxFlow}(G, s, t) \ge D) = \text{WMC}(\Phi_{\text{cap}}, \mathbf{w})$$
   where literal weights are $w(e) = p_e$ and $w(\neg e) = 1 - p_e$.

### Proof

1. By the Max-Flow Min-Cut Theorem (Ford-Fulkerson), for any state $\mathbf{x} \in \{0, 1\}^{|E|}$, the maximum $s$-$t$ flow equals the minimum capacity among all $s$-$t$ cuts:
   $$\text{MaxFlow}(G_{\mathbf{x}}, s, t) = \min_{C \in \mathcal{C}_{\text{min}}(s, t)} \sum_{e \in C} c_e x_e$$
   Therefore, $\text{MaxFlow}(G_{\mathbf{x}}, s, t) \ge D$ if and only if for every minimal cut $C \in \mathcal{C}_{\text{min}}(s, t)$:
   $$\sum_{e \in C} c_e x_e \ge D$$
2. For a fixed cut $C$, let $E_{\text{fail}} = \{e \in C : x_e = 0\}$ be the set of failed edges in $C$. The surviving capacity is:
   $$\sum_{e \in C \setminus E_{\text{fail}}} c_e$$
   The capacity condition $\sum_{e \in C} c_e x_e < D$ holds if and only if $E_{\text{fail}}$ contains some capacity-breaking subset $F \subseteq C$ such that $\sum_{e \in C \setminus F} c_e < D$.
   By minimality, $E_{\text{fail}}$ breaks demand $D$ if and only if there exists $F \in \mathcal{F}_{\text{min}}(C, D)$ such that $F \subseteq E_{\text{fail}}$.
3. Taking the logical contrapositive: surviving capacity across $C$ is at least $D$ if and only if $E_{\text{fail}}$ does not contain any $F \in \mathcal{F}_{\text{min}}(C, D)$.
   That is, for every $F \in \mathcal{F}_{\text{min}}(C, D)$, $F \not\subseteq E_{\text{fail}}$, which means at least one edge $e \in F$ is not in $E_{\text{fail}}$ ($x_e = 1$):
   $$\sum_{e \in C} c_e x_e \ge D \iff \bigwedge_{F \in \mathcal{F}_{\text{min}}(C, D)} \left( \bigvee_{e \in F} x_e \right)$$
4. Conjoining over all minimal cuts $C \in \mathcal{C}_{\text{min}}(s, t)$ yields $\Phi_{\text{cap}}$.
5. Because every clause $\bigvee_{e \in F} x_e$ consists solely of positive literals representing physical edges $e \in E$, no auxiliary variables are created, and the formula is monotone.
   WMC over $\Phi_{\text{cap}}$ with exact edge operational weights $w(e) = p_e$ evaluates the probability measure of satisfying states, completing the proof. $\blacksquare$

## 4. Benchmark Catalog & Experimental Protocol

The benchmark suite evaluates 24 distinct configurations across 5 topological families:

- **Family 1: Multi-Channel Trunking**: $k$-out-of-$n$ parallel channel survivability ($n \in \{3, 4, 5, 6\}$, demands $2 \le D \le 4$).
- **Family 2: Heterogeneous Capacitated Wheatstone Bridge**: Non-uniform link capacities ($c_e \in \{1, 2\}$, demands $1 \le D \le 3$, probabilities $p \in \{0.85, 0.92\}$).
- **Family 3: 5-Node Dense Multi-Unit Mesh**: Backbone topologies with edge capacities up to 4 units under varying demands ($1 \le D \le 4$).
- **Family 4: 2xN Capacitated Ladders**: Grid-like distribution ladders under demands 1 and 2.
- **Family 5: Datacenter Spine-and-Leaf Fabric**: Multi-tier uplinks and downlinks connecting Leaf servers across redundant Spines under demands $1 \le D \le 4$.

Every instance is independently evaluated by:

1. Dual Cut Threshold Monotone CNF compilation and Weighted Model Counting.
2. Complete truth-table enumeration using Dinic's blocking flow algorithm on every surviving state subgraph.
The exact rational reliability values must match identically.
