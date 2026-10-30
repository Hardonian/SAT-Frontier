# High-Core AMD EPYC Cut-Compiled Scaling Campaign Specification

## 1. Overview & Objective
This specification describes the deployment, execution, and verification of the **High-Core AMD EPYC Cut-Compiled Scaling Campaign (`epyc-cut-001`)**.

Previous campaigns established:
1. `epyc-cube-001` & `epyc-cube-002`: Cube-and-Conquer lookahead scales near-linearly on modular topologies across up to 64 workers (194M search nodes evaluated), but reveals sharp structural hardness cliffs at $2 \times 11$, $3 \times 7$, and $4 \times 4$ under path-based CNF compilation.
2. `cut-wmc-001` (Hypothesis H9): Dual Cut-based Monotone CNF compilation shatters the path-based hardness cliff, solving $3 \times 7$ in 2.13s and $2 \times 11$ in 0.12s.
3. `cut-cube-001`: Deeper lookahead ($d=6$, 64 cubes) solves $3 \times 8$ (3.26s) and $3 \times 9$ (11.52s, 1.4M nodes).

The **frontier benchmark suite** pushes into previously unsolvable regimes:
- $3 \times 10$ (47 vars, 8,351 clauses)
- $3 \times 11$ (52 vars, 16,954 clauses)
- $4 \times 6$ (38 vars, 5,024 clauses)
- $4 \times 7$ (45 vars, 18,187 clauses)
- $5 \times 5$ (40 vars, 8,742 clauses)
- Non-planar expander / regular graphs: `chvatal` (23 vars, 539 clauses), `barbell_6_3_6` (31 vars, 33 clauses).

---

## 2. Target Execution Environment
- **Architecture**: AMD EPYC 7002 / 7003 / 9004 series (64 physical cores / 128 threads or 64 logical cores).
- **RAM**: 168 GB DDR4 (or greater).
- **Operating System**: Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9).
- **Memory Management**: Multi-NUMA nodes bound with `numactl --interleave=all`.

---

## 3. Pre-Compiled Instances
The 10 frontier benchmark formulas are pre-compiled and cryptographically tracked in `instances/epyc-cut-frontier/`:

| Instance | Topo Family | Variables | Cut Clauses | Size (KB) | SHA-256 Digest (Prefix) |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `grid_3x8.cnf` | $3 \times 8$ Grid | 37 | 1,973 | 62.8 | `d635b4c30c04b65b...` |
| `grid_3x9.cnf` | $3 \times 9$ Grid | 42 | 4,082 | 146.4 | `02fdde8618206073...` |
| `grid_3x10.cnf` | $3 \times 10$ Grid | 47 | 8,351 | 338.6 | `57ca8fa20851c404...` |
| `grid_3x11.cnf` | $3 \times 11$ Grid | 52 | 16,954 | 772.3 | `49512aeba413fa7f...` |
| `grid_4x5.cnf` | $4 \times 5$ Grid | 31 | 1,353 | 37.9 | `2592429aa74f0d46...` |
| `grid_4x6.cnf` | $4 \times 6$ Grid | 38 | 5,024 | 170.5 | `14354f9a6a20bb5f...` |
| `grid_4x7.cnf` | $4 \times 7$ Grid | 45 | 18,187 | 733.8 | `faece45a06eb21de...` |
| `grid_5x5.cnf` | $5 \times 5$ Grid | 40 | 8,742 | 344.2 | `278fb3b371be8a32...` |
| `barbell_6_3_6.cnf`| 6-Clique Barbell | 31 | 33 | 2.1 | `caa211f16b0033f4...` |
| `chvatal.cnf` | Chvátal Graph | 23 | 539 | 11.2 | `f47d818d3b3dc185...` |

---

## 4. Execution Commands

### Turnkey One-Liner (Linux / Bash on EPYC)
```bash
chmod +x scripts/run_epyc_cut_campaign.sh
./scripts/run_epyc_cut_campaign.sh
```

### Direct Python Invocation with Custom Worker Count
```bash
# EPYC with 64 workers across depths 4, 6, 8:
numactl --interleave=all python3 scripts/run_epyc_cut_campaign.py \
    --workers 64 \
    --depths 4 6 8 \
    --seconds-per-cube 30.0 \
    --max-nodes-per-cube 200000
```

### Dry Run Verification
```bash
python3 scripts/run_epyc_cut_campaign.py --dry-run
```

---

## 5. Verification & Safety Protocols
1. **Evidence isolation**: Every invocation requires a new, nonexistent `--evidence-dir`. Dry runs create nothing. Partial campaigns retain logs, checkpoints and completed rows but cannot be resumed in place; choose a fresh directory for another invocation.
2. **Cross-depth invariance**: Exact counts or rational weights are compared across successful depths; any mismatch stops the campaign. This is not an independent correctness check.
3. **Evidence integrity**: Completed runs include raw results, logs, checkpoints, digest-addressed inputs and source hashes. Run `python3 verify_evidence.py <evidence-dir>` to check integrity against the same source tree. This does not establish scientific validity. Unknown results remain unknown; runner crashes stop the campaign without a complete manifest.

