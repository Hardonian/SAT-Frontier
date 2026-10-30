# PRESS RELEASE

**FOR IMMEDIATE RELEASE**  
**Date**: October 28, 2026  
**Contact**: SAT-Frontier Research Lab  
**Repository**: [github.com/Hardonian/SAT-Frontier](https://github.com/Hardonian/SAT-Frontier)  

---

## SAT-Frontier Unveils Breakthrough Dual Cut Compilation for Exact Network Reliability (#WMC) and Releases Independent Formal Audit of OpenAI's ETH Refutation

**SEATTLE, WA** — The SAT-Frontier Research Lab today announced a dual milestone in computational complexity and automated reasoning: the invention and empirical verification of **Dual Cut Monotone CNF Compilation**, solving a decades-old structural hardness bottleneck in exact Two-Terminal Network Reliability (#WMC), alongside the release of the first comprehensive, independent formal audit and verification harness for OpenAI's claimed refutation of the Exponential Time Hypothesis (ETH).

Exact counting (#SAT) and Weighted Model Counting (#WMC) sit at the theoretical apex of computer science. While standard Boolean Satisfiability (SAT) determines whether at least one solution exists (NP-complete), exact model counting determines the exact number or probabilistic weight of all satisfying configurations (#P-complete). This capability is fundamental to evaluating mission-critical infrastructure, including telecom routing backbones, smart electrical grids, aerospace fault trees, and cloud multi-region availability.

---

### The Algorithmic Breakthrough: Breaking the Path-Explosion Hardness Cliff

For decades, evaluating exact two-terminal network reliability has relied on enumerating operational paths. On planar mesh and grid networks, however, the number of self-avoiding paths grows exponentially ($O(2^{|V|})$). In empirical campaigns conducted on high-core AMD EPYC servers, path-based CNF compilation triggered an impassable structural cliff: on a modest $3\times 7$ grid, path enumeration generated **1,401 variables**, **20,430 clauses**, and a single 1,368-literal hyperedge clause, causing modern exact solvers to stall indefinitely (>600 seconds per cube).

To overcome this fundamental limit, SAT-Frontier formulated the connectivity problem through the lens of Menger's Duality and the Max-Flow Min-Cut Theorem:
$$\text{Connected}(s, t) \iff \bigwedge_{C \in \mathcal{C}_{\text{min}}(s, t)} \left( \bigvee_{e \in C} e \right)$$

By compiling connectivity directly over minimal $s-t$ edge cuts:

1. **Zero Auxiliary Variables**: Variables correspond strictly to physical network edges, slashing formula variables on $3\times 7$ from 1,401 down to **32**.
2. **Immediate Conflict Pruning**: Clause lengths are bounded by cut sizes (2–5 literals), enabling unit propagation to detect edge failures and cut disconnections instantaneously.
3. **Hardness Cliff Shattered**: In rigorous empirical evaluations across 24 benchmark topologies:
   - `grid_3x7`: Accelerated from >600s timeout down to **2.13 seconds** (80,925 nodes).
   - `grid_2x11`: Accelerated from >600s timeout down to **0.12 seconds** (7,901 nodes).
   - `barbell_k6`: Delivered a **122.1x reduction** in search nodes (from 85,246 to 698 nodes).
   - **100% Mathematical Soundness**: Verified zero discrepancies across all mutually solved instances against truth-table oracles.

When combined with distributed Cube-and-Conquer lookahead across 20 cores, this dual cut compilation unlocked exact solutions for previously intractable instances, solving `grid_3x8` in 3.26s, `grid_3x9` in 11.52s (1.4 million search nodes), and `grid_4x6` in 11.06s (1.3 million search nodes).

---

### The Independent Audit of OpenAI's Subexponential SAT Formalization

SAT-Frontier also published its comprehensive audit of OpenAI's formal mathematics repository (`openai/math`, commit `7ef5c0c`), which claims a deterministic algorithm solving 3-SAT in subexponential time ($2^{O(n / \sqrt{\log n})}$), refuting the Exponential Time Hypothesis.

Key findings from the SAT-Frontier audit include:

1. **Formal Comparator Gap**: The public comparator challenge (`ComparatorChallenges/SubexponentialSAT.lean`) is declared with `sorry` as a specification challenge; it does not constitute a proof of the theorem.
2. **Transitive Dependency Fanout**: The upstream solution imports 3,091 transitive modules. In automated builds, this triggers an unconstrained multi-process compiler fanout, exceeding an 11.9 GB RSS memory ceiling and terminating with `exit 137` / timeout prior to Lean 4 kernel verification or axiom generation.
3. **Turnkey Bounded-Memory Verification Harness**: SAT-Frontier has created and open-sourced an isolated verification script (`scripts/run_lean4_audit.sh`) and Lean axiom extractor (`scripts/extract_axioms.lean`) designed to constrain Lake compiler concurrency (`-j 4`) and enable formal verification without memory exhaustion.

---

### Uncompromising Verification: 2,577 Cryptographically Pinned Runs

In accordance with strict scientific reproducibility protocols:

- SAT-Frontier has executed and verified **2,577 empirical runs** across 10 distinct research campaigns.
- Every run is cryptographically anchored with SHA-256 ledgers, raw DIMACS formulas, and JSONL event streams.
- A single master verification script (`verify_all_evidence.py`) validates the cryptographic integrity of all 2,577 runs and passes all 67 unit and metamorphic tests in under 15 seconds.
- Distribution archives and wheel packages for Release v0.2.2 are pinned and available locally in `artifacts/release/`.

---

### Availability

The complete source code, test suites, empirical evidence directories, replication runners, and audit dossiers are available in the repository:

- **Repository**: [https://github.com/Hardonian/SAT-Frontier](https://github.com/Hardonian/SAT-Frontier)
- **Technical Whitepaper**: `docs/RESEARCH_PAPERS/DUAL_CUT_WMC_PAPER.md`
- **ETH Audit Dossier**: `docs/ETH_AUDIT_V02.md` & `docs/OPENAI_ETH_ANALYSIS.md`
- **Commercialization Blueprint**: `docs/COMMERCIAL_APPLICATIONS.md`

### About SAT-Frontier

SAT-Frontier is an independent, CPU-first exact-counting research laboratory dedicated to advancing exact model counting, structural decomposition, and automated theorem verification.
