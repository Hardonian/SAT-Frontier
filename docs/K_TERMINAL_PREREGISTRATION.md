# Preregistration: Multi-Terminal Network Reliability via Dual K-Cut Monotone CNF Compilation (Hypothesis H10)

**Date**: 2026-10-28  
**Hypothesis ID**: H10  
**Target Domain**: Exact Multi-Terminal ($K$-Terminal) and All-Terminal Network Reliability (#P-complete)  
**Primary Metric**: Exact rational agreement with independent brute-force oracle and search node scaling  
**Falsification Condition**: Any discrepancy between dual K-cut WMC and the exact brute-force oracle, or failure of minimal K-cut enumeration on bounded planar grids.

---

## 1. Problem Formulation & Theoretical Duality

Given an undirected graph $G = (V, E)$, an operational probability $p_e \in [0, 1] \cap \mathbb{Q}$ for each edge $e \in E$, and a designated terminal subset $K \subseteq V$ with $|K| \ge 2$:

The **$K$-Terminal Network Reliability** $R_K(G, K, \mathbf{p})$ is the exact probability that all vertices in $K$ reside within the same connected component of the operational random subgraph $G[E']$:

$$R_K(G, K, \mathbf{p}) = \sum_{\substack{E' \subseteq E \\ \forall u, v \in K, \, u \stackrel{E'}{\longleftrightarrow} v}} \left( \prod_{e \in E'} p_e \prod_{e \notin E'} (1 - p_e) \right)$$

Special cases:

- $|K| = 2$: Two-Terminal Reliability ($s-t$).
- $|K| = |V|$: All-Terminal Reliability (Spanning network connectivity).
- $2 < |K| < |V|$: Multi-Terminal Reliability (e.g., quorum consensus, multi-region cloud VPCs).

### Path/Tree Pathology in Prior Art

Standard reductions to Boolean Satisfiability reduce $K$-terminal reliability by enumerating **Steiner trees** spanning $K$. The number of Steiner trees grows hyper-exponentially with $|V|$ and $|K|$, introducing $O(2^{|V|} \cdot |V|^{|K|-2})$ auxiliary variables and a single dense hyperedge clause spanning all trees, causing immediate solver stalls even on small graphs ($|V| \ge 8$).

### Generalized Dual Cut Duality Theorem

**Theorem (Generalized Cut Duality for $K$-Terminal Connectivity)**:  
The terminal set $K$ is connected in the operational subgraph $(V, E')$ if and only if $E'$ intersects every inclusion-minimal edge cut separating at least two vertices in $K$.

**Characterization of Minimal $K$-Cuts**:  
An edge cut $\delta(S)$ is an inclusion-minimal $K$-cut if and only if:

1. $G[S]$ is connected;
2. $G[V \setminus S]$ is connected;
3. $S \cap K \neq \emptyset$; and
4. $(V \setminus S) \cap K \neq \emptyset$.

**Dual $K$-Cut Monotone CNF Formulation**:  
Fixing a reference terminal $k_0 \in K$ and collecting all subsets $S \ni k_0$ satisfying the above four conditions yields the purely positive monotone CNF formula:

$$\Phi_{K\text{-cut}}(G, K) = \bigwedge_{C \in \mathcal{C}_{\text{min}}(K)} \left( \bigvee_{e \in C} x_e \right)$$

Properties:

- **Zero Auxiliary Variables**: Variables are strictly physical edge literals $\{x_e\}_{e \in E}$.
- **Monotone Structure**: Positive literals only; unit propagation activates immediately upon edge failure.
- **Unified**: Handles 2-terminal, $K$-terminal, and all-terminal connectivity within a single formulation.

---

## 2. Experimental Design & Benchmark Topologies

The empirical campaign (`evidence/k-terminal-wmc-001/`) evaluates 24 benchmark instances across four structural categories:

1. **Category A: All-Terminal Topologies ($K = V$)**:
   - Triangle ($K_3$)
   - 4-cycle ($C_4$)
   - 6-cycle ($C_6$)
   - Complete graph $K_4$
   - Complete graph $K_5$
   - Planar grid $2\times 3$
   - Planar grid $2\times 4$
   - Planar grid $3\times 3$

2. **Category B: Multi-Terminal Corner Connectivity ($K = \text{corners}$)**:
   - Planar grids with $K$ consisting of the 4 perimeter corners:
     - $2\times 3$ (4 corners)
     - $2\times 4$ (4 corners)
     - $2\times 5$ (4 corners)
     - $2\times 6$ (4 corners)
     - $3\times 3$ (4 corners)
     - $3\times 4$ (4 corners)
     - $3\times 5$ (4 corners)
     - $4\times 4$ (4 corners)

3. **Category C: Distributed Ring & Mesh Topologies**:
   - 6-node ring with 3 distributed terminals ($K=\{1, 3, 5\}$)
   - 8-node dual-ring with 4 cardinal terminals ($K=\{1, 3, 5, 7\}$)
   - Barbell graph $B(3, 3, 2)$ with terminals in opposite bells ($K=\{1, 2, 5, 6\}$)
   - Barbell graph $B(4, 4, 1)$ with 4 terminals ($K=\{1, 3, 6, 8\}$)

4. **Category D: Production Enterprise Multi-Terminal Systems**:
   - AWS Tri-Region VPC with 3 Availability Zones ($K=\{\text{AZ}_\text{East}, \text{AZ}_\text{Central}, \text{AZ}_\text{West}\}$)
   - Transatlantic Tri-City Optical Mesh ($K=\{\text{NewYork}, \text{London}, \text{Frankfurt}\}$)
   - IEEE 14-Bus Generator Quorum ($K=\{\text{Bus}_1, \text{Bus}_2, \text{Bus}_3, \text{Bus}_6, \text{Bus}_8\}$)
   - DO-178C Quad-Actuator Consensus ($K=\{\text{FCC}_1, \text{FCC}_2, \text{Actuator}_A, \text{Actuator}_B\}$)

---

## 3. Independent Verification Protocol

For all instances where $|E| \le 16$, an independent brute-force state enumeration oracle (`brute_force_k_terminal`) exhaustively iterates over all $2^{|E|}$ subgraphs, verifies terminal connectivity via BFS, and accumulates exact rational probabilities in $\mathbb{Q}$.

**Acceptance Criteria**:

1. 100% exact match between `to_k_cut_cnf` + `wmc_solve` and the independent brute force oracle (`bf_fraction == cut_fraction`). Zero discrepancies allowed.
2. For instances where $|K| = 2$, cuts and counts must match `find_all_minimal_cuts` and `to_cut_cnf` identically.
3. Node budget cap: 50,000 search nodes per run. Timeout cap: 30.0 seconds per instance.
4. Cryptographic integrity: All DIMACS instances, run logs, CSV tables, and config parameters hashed and recorded in `manifest.json` and `SHA256SUMS`.
