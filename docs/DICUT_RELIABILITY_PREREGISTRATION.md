# Preregistration: Directed Network Reliability via Dual Dicut Monotone CNF Compilation (Hypothesis H12)

**Date**: 2026-10-29  
**Status**: Pre-registered prior to evidence generation  
**Target Campaign**: `evidence/dicut-wmc-001`  
**Primary Metric**: Exact rational reliability agreement between dual dicut compilation and brute-force state enumeration oracle, compilation time, search nodes, and solved fraction.  
**Falsification Condition**: Any discrepancy between dual dicut compiled WMC and the independent brute-force directed oracle on instances with $|A| \le 16$, or compilation failure/memory exhaustion on structured directed benchmark graphs.

---

## 1. Background & Scientific Motivation

In distributed computing, microservices, asymmetric communication networks, and directed transaction systems (such as interbank settlement and payment routing), connections are inherently **directed** ($u \to v \neq v \to u$).

Computing **Directed Two-Terminal Reliability** ($s \leadsto t$) is #P-complete (Valiant 1979). Previous attempts to formulate directed reliability in Boolean satisfiability suffered from:
1. **Exponential Path Enumeration**: Finding all directed simple paths from $s$ to $t$ is #P-complete on general DAGs and intractable on cyclic directed graphs.
2. **Auxiliary Variable Explosion**: Path indicator variables and cycle-breaking/subtour elimination constraints (e.g. Miller-Tucker-Zemlin) drastically inflate formula size.
3. **Feedback Cycles**: Directed graphs with cycles create circular dependencies that cause naive SAT reductions to produce spurious reachability models.

---

## 2. Hypothesis Formulation (H12)

**Hypothesis H12**:  
Dual directed cut (dicut) monotone CNF compilation:
$$\Phi_{\text{dicut}}(D, s, t) = \bigwedge_{S \in \mathcal{S}_{\text{min}}} \left( \bigvee_{e \in \delta^+(S)} x_e \right)$$
where each $\delta^+(S)$ is an inclusion-minimal directed $s-t$ cut, strictly encodes directed reachability $s \leadsto t$ with **strictly $|A|$ variables** and zero auxiliary variables, achieving 100% exact rational agreement with independent exhaustive state enumeration and scaling exact directed reliability computation to dense layered DAGs and cyclic networks.

### Theorem (Characterization of Inclusion-Minimal Dicuts)
Let $D = (V, A)$ be a directed graph, with source $s$ and destination $t$. An arc cut $\delta^+(S) = \{(u, v) \in A : u \in S, v \in V \setminus S\}$ with $s \in S, t \in V \setminus S$ is an inclusion-minimal directed $s-t$ cut if and only if:
1. Every vertex $u \in S$ is reachable from $s$ in the induced subgraph $D[S]$.
2. For every arc $(u, v) \in \delta^+(S)$, the head vertex $v$ can reach $t$ in the induced subgraph $D[V \setminus S]$.

---

## 3. Experimental Design & Benchmark Topologies

We design a suite of 24 benchmark instances spanning 4 diverse directed topologies:
1. **Layered DAGs**: Multi-stage feedforward architectures (2 to 4 layers, width 2 to 4) representing microservices, pipeline workflows, and deep neural layer dropouts.
2. **Cyclic Directed Meshes**: Planar grid topologies with directed and bi-directed edges, feedback loops, and cycles.
3. **Bottleneck Directed Barbells**: Two strongly connected components linked by asymmetric bottleneck directed bridges.
4. **Mission-Critical Commercial Topologies**: Real-world directed dependency graphs (Kubernetes Microservices, Airflow ETL DAG, Fedwire Payment Settlement, Autonomous Vehicle RPC Pipeline).

---

## 4. Verification Protocol

- Every instance with $|A| \le 16$ will be verified against an independent brute-force state enumeration oracle (`brute_force_directed_oracle`).
- Exact rational equality (`Fraction`) is strictly required: 0 tolerance for floating-point approximation error.
- All runs will be logged in `evidence/dicut-wmc-001/` with cryptographically verified `manifest.json` and `SHA256SUMS`.
