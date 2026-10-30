# Preregistration: Mixed Node-and-Edge Failure Network Reliability via Dual Mixed-Cut Monotone CNF Compilation (Hypothesis H13)

**Date**: 2026-10-29  
**Status**: Pre-registered prior to evidence generation  
**Target Campaign**: `evidence/mixed-wmc-001`  
**Primary Metric**: Exact rational reliability agreement between dual mixed-cut compilation and independent exhaustive state enumeration oracle, minimal mixed-cut clause counts, compilation time, search nodes, and solved fraction.  
**Falsification Condition**: Any discrepancy between dual mixed-cut compiled WMC and the independent brute-force mixed oracle on instances with $|V_{\text{internal}}| + |E| \le 16$, or compilation failure/memory exhaustion on structured mixed benchmark topologies.

---

## 1. Scientific Motivation & Theoretical Gap

Previous research in Boolean satisfiability and model counting for network reliability has largely enforced a bifurcated assumption:
1. **Pure Edge Failures**: Vertices (routers, servers, data centers) are assumed 100% reliable; only communication links fail ($G(V, E, p_e)$).
2. **Pure Vertex Failures**: Communication links are assumed 100% reliable; only vertices fail.

In actual production engineering—such as hyperscale cloud datacenters, subsea telecommunications, electrical power transmission grids, and aerospace avionics:
**Both nodes (servers, switches, substations, actuators) and edges (cables, fiber links, transmission lines) fail simultaneously and independently.**

Historically, encoding mixed node-and-edge failures in SAT required enumerating simple paths containing both vertices and edges, or introducing dual sets of indicator and flow variables with auxiliary linking constraints.

---

## 2. Hypothesis Formulation (H13)

**Hypothesis H13**:  
Dual mixed-cut monotone CNF compilation:
$$\Phi_{\text{mixed}}(G, s, t) = \bigwedge_{(V_C, E_C) \in \mathcal{C}_{\text{min}}^{\text{mixed}}(s, t)} \left( \bigvee_{v \in V_C} y_v \lor \bigvee_{e \in E_C} x_e \right)$$
where each $(V_C, E_C)$ is an inclusion-minimal mixed cut whose simultaneous failure destroys all $s-t$ operational paths:
1. Strictly encodes exact two-terminal connectivity under simultaneous, independent node and edge failures.
2. Requires strictly $|V_{\text{internal}}| + |E|$ Boolean variables with zero auxiliary variables or path indicators.
3. Achieves 100% exact rational agreement with independent exhaustive state-space enumeration.

### Theorem (Node-Splitting Dicut Projection)
Let $G = (V, E)$ be a network with source $s$, target $t$, vertex operational probabilities $q_v$, and edge probabilities $p_e$. Let $G^*$ be the augmented directed graph where each internal vertex $v \in V \setminus \{s, t\}$ is split into an arc $(v_{\text{in}}, v_{\text{out}})$ with weight $q_v$, and each edge $uv$ is split into directed arcs $(u_{\text{out}}, v_{\text{in}})$ and $(v_{\text{out}}, u_{\text{in}})$ both controlled by edge variable $x_{uv}$.
Then every inclusion-minimal directed cut in $G^*$ projects directly onto an inclusion-minimal mixed cut $(V_C, E_C)$ of $G$, and the resulting monotone CNF formula is sound, complete, and minimal.

---

## 3. Experimental Design & Benchmark Topologies

We construct a diverse benchmark catalog of 24 mixed network instances across 4 categories:
1. **Planar Grids with Mixed Failures**: $2\times 2$ to $3\times 4$ planar grids where internal switching nodes fail ($q_v \in [0.85, 0.95]$) alongside link failures ($p_e \in [0.90, 0.98]$).
2. **Layered Server Topologies**: Multi-tier architectures (Web $\to$ App $\to$ Cache $\to$ DB) subject to simultaneous server crashes and link drops.
3. **Bottleneck Barbells with Bridge Node/Edge Failures**: Clustered topologies linked by vulnerable gateway nodes and interconnect links.
4. **Mission-Critical Enterprise Systems**: Cloud multi-region architectures, subsea landing stations, and avionics flight-control systems.

---

## 4. Verification Protocol

- Every instance with $|V_{\text{internal}}| + |E| \le 16$ is independently evaluated against `brute_force_mixed_oracle` with 100% exact rational precision (`Fraction`).
- All runs will be logged in `evidence/mixed-wmc-001/` with cryptographic `manifest.json`, `SHA256SUMS`, and full artifact verification via `verify_evidence.py`.

