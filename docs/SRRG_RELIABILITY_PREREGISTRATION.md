# Preregistration: Hypothesis H14 — Shared-Risk Resource Group (SRRG) Correlated Failure Reliability via Dual SRRG-Cut Monotone CNF Compilation

## 1. Background & Scientific Motivation
In real-world mission-critical cyber-physical networks (such as transoceanic subsea fiber consortia, optical dense wavelength division multiplexing (DWDM) fabrics, multi-region cloud VPC backbones, and smart power grids), transmission links and routing vertices do not fail in isolation. Instead, physical links share common underlying infrastructure subject to common-cause failure events:
- Multiple optical wavelengths share a physical glass fiber sheath.
- Multiple fiber cables share a terrestrial highway conduit, trench, or subsea cable landing station.
- Multiple redundant virtual routers share an Availability Zone (AZ) power distribution unit (PDU) or top-of-rack (ToR) switch.

This phenomenon is standardized in optical networking as **Shared-Risk Resource Groups (SRRG)** or **Shared-Risk Link Groups (SRLG)**. When an SRRG fails, all constituent edges fail simultaneously (fate-sharing).

Traditional reliability algorithms either:
1. Ignore correlated failures, assuming independent edge failures and underestimating catastrophic network outage risks by orders of magnitude;
2. Enumerate exponentially many SRRG-disjoint paths via integer linear programming (ILP) or heuristic k-shortest paths, failing to yield exact closed-form reliability; or
3. Introduce massive systems of binary routing indicators and flow conservation constraints in CNF/WMC, resulting in exponential clause bloat.

## 2. Hypothesis Formulation
**Hypothesis H14**:
Dual SRRG-Cut Monotone CNF Compilation directly compiles network connectivity under arbitrary Shared-Risk Resource Group mappings into a monotone CNF over risk group survival variables alone:
$$\Phi_{\text{srrg\_conn}}(G, s, t) = \bigwedge_{K \in \mathcal{K}_{\text{min}}^{\text{SRRG}}(s, t)} \left( \bigvee_{g \in K} y_g \right)$$
where each clause represents an inclusion-minimal SRRG cut $K \subseteq \mathcal{R}$, and $y_g$ is the boolean indicator that risk group $g$ is operational (weighted by $p_g$).

**Falsification Criteria**:
1. Any disagreement between the compiled WMC reliability and the independent brute-force state enumeration oracle across $2^{|\mathcal{R}|}$ configurations.
2. The necessity of any auxiliary indicator or routing flow variables in the resulting CNF.
3. Inability to compile and evaluate exact closed-form rational reliability across cyclic meshes, dense topologies, and commercial cloud/subsea benchmarks in sub-second CPU latency.

## 3. Mathematical Theorem & Proof

### Definition (SRRG Network Model)
Let $G = (V, E)$ be a network with terminals $s, t \in V$. Let $\mathcal{R} = \{g_1, \dots, g_m\}$ be a finite set of Shared-Risk Resource Groups. Each group $g \in \mathcal{R}$ has independent operational probability $p_g \in (0, 1]$ and failure probability $q_g = 1 - p_g$.
Each edge $e \in E$ is associated with a non-empty set of risk groups $\mathcal{R}(e) \subseteq \mathcal{R}$. An edge $e$ operates if and only if all of its associated risk groups operate:
$$\text{state}(e) = \bigwedge_{g \in \mathcal{R}(e)} y_g$$

### Definition (Path Risk Set & SRRG Cut)
Let $\mathcal{P}(s, t)$ be the set of simple $s-t$ paths in $G$. For each path $P \in \mathcal{P}(s, t)$, its path risk set is $\mathcal{R}(P) = \bigcup_{e \in P} \mathcal{R}(e)$.
A subset of risk groups $K \subseteq \mathcal{R}$ is an **SRRG $s-t$ cut** if the simultaneous failure of all groups in $K$ disrupts all simple paths between $s$ and $t$:
$$\forall P \in \mathcal{P}(s, t), \quad K \cap \mathcal{R}(P) \neq \emptyset$$
An SRRG cut $K$ is **inclusion-minimal** if no proper subset $K' \subset K$ is an SRRG cut. We denote the family of inclusion-minimal SRRG cuts as $\mathcal{K}_{\text{min}}^{\text{SRRG}}(s, t)$.

### Theorem (Dual SRRG-Cut Monotone CNF Duality)
Terminals $s$ and $t$ are connected in $G$ under risk state $\mathbf{y} \in \{0, 1\}^{|\mathcal{R}|}$ if and only if:
$$\Phi_{\text{srrg\_conn}}(\mathbf{y}) = \bigwedge_{K \in \mathcal{K}_{\text{min}}^{\text{SRRG}}(s, t)} \left( \bigvee_{g \in K} y_g \right) = 1$$

*Proof*:
$(\implies)$ Suppose $s$ and $t$ are connected under state $\mathbf{y}$. Then there exists a path $P^* \in \mathcal{P}(s, t)$ such that all edges $e \in P^*$ operate, meaning for every $g \in \mathcal{R}(P^*)$, $y_g = 1$. Let $K \in \mathcal{K}_{\text{min}}^{\text{SRRG}}(s, t)$ be any minimal SRRG cut. By definition of an SRRG cut, $K \cap \mathcal{R}(P^*) \neq \emptyset$. Let $g^* \in K \cap \mathcal{R}(P^*)$. Since $g^* \in \mathcal{R}(P^*)$, we have $y_{g^*} = 1$. Therefore, the clause $\bigvee_{g \in K} y_g$ evaluates to 1. Since this holds for all $K \in \mathcal{K}_{\text{min}}^{\text{SRRG}}(s, t)$, $\Phi_{\text{srrg\_conn}}(\mathbf{y}) = 1$.

$(\impliedby)$ Suppose $\Phi_{\text{srrg\_conn}}(\mathbf{y}) = 1$. Assume for contradiction that $s$ and $t$ are disconnected. Then the set of failed risk groups $F = \{g \in \mathcal{R} \mid y_g = 0\}$ disconnects all paths $P \in \mathcal{P}(s, t)$. Thus $F$ is an SRRG cut. Therefore, $F$ must contain at least one inclusion-minimal SRRG cut $K^* \subseteq F$. For this cut $K^*$, every group $g \in K^*$ has $y_g = 0$, which implies that the clause $\bigvee_{g \in K^*} y_g = 0$, contradicting the assumption that $\Phi_{\text{srrg\_conn}}(\mathbf{y}) = 1$.

Hence, exact connectivity is logically equivalent to $\Phi_{\text{srrg\_conn}}$, which contains strictly $|\mathcal{R}|$ variables and zero auxiliary variables. $\blacksquare$

## 4. Empirical Protocol
- Benchmark Suite: 24 topologies across 8 families in `evidence/srrg-wmc-001/`.
- Independent Verification: For all topologies with $\le 16$ risk groups, compare exact rational reliability against the independent $2^{|\mathcal{R}|}$ state enumeration oracle `brute_force_srrg_oracle`.
- Precision Requirement: 100% exact rational agreement via Python `fractions.Fraction`.

