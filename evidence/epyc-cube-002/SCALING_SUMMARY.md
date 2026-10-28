# EPYC Cube-and-Conquer Scaling Summary
Generated: 2026-10-28 (updated)

## Environment
- CPU: 64-core AMD EPYC
- Memory: 172 GB DDR5
- NUMA: single node, interleave mode
- Runner: resource-aware epyc_runner.py with checkpoint/resume

## Modular Network Scaling Results

### Grid Topology (p=9/10, WMC, workers=32/64)
| Instance | Vars | Clauses | d4 | d5 | d6 | d7 | d8 | Hardness |
|----------|------|---------|----|----|----|----|----|----------|
| grid_2x5 | 29 | 121 | - | EXACT | EXACT | EXACT | EXACT | trivial |
| grid_2x6 | 48 | 289 | - | EXACT | EXACT | EXACT | EXACT | trivial |
| grid_3x3 | 24 | 77 | - | EXACT | EXACT | EXACT | EXACT | easy |
| grid_3x4 | 55 | 323 | - | EXACT | EXACT | EXACT | EXACT | easy |
| grid_3x5 | 147 | 1332 | - | EXACT | EXACT | EXACT | EXACT | moderate |
| grid_3x6 | 441 | 5297 | EXACT* | EXACT* | EXACT* | EXACT* | EXACT* | moderate |
| grid_3x7 | 1401 | 20430 | UNKNOWN | - | - | - | - | hard |
| grid_4x3 | 55 | 323 | - | EXACT | EXACT | EXACT | EXACT | easy (transpose) |
| grid_4x4 | 208 | 2097 | - | EXACT | EXACT | EXACT | EXACT | moderate |
| grid_4x5 | 1007 | 14109 | UNKNOWN | UNKNOWN | UNKNOWN | - | - | hard |
| grid_5x5 | 8552 | 156945 | UNKNOWN | - | - | - | - | intractable |

*With 600s per-cube budget and 64 workers

### Barbell Topology (WMC)
| Instance | Vars | Clauses | d5 | d6 | d7 | d8 | Hardness |
|----------|------|---------|----|----|----|----|----------|
| barbell_k6 | ~200 | ~800 | EXACT | EXACT | EXACT | EXACT | easy |
| barbell_k8 | 3971 | 27403 | UNKNOWN | N/A | N/A | N/A | hard |
| barbell_k10 | - | - | gen timeout | N/A | N/A | N/A | intractable |

### Policy Instances (Unweighted)
- 32/32 instances solved exactly at depth 4, 32 workers
- Wall times: 0.08-0.10s per instance
- Peak RSS: 20-21 MB

## Key Findings

1. **Scaling Cliffs**:
   - Grid: 3x6 tractable (with budget), 3x7 hard at d4
   - Grid: 4x4 tractable, 4x5 hard at d5
   - Pattern: ~20K clauses seems near boundary for tractable decomposition

2. **Weight Consistency**:
   - grid_3x6: weight=0.969984456181915 consistent across d4-d8
   - barbell_k6: weight=0.799967877783281 consistent across d5-d8
   - Confirms algorithmic correctness

3. **Resource Efficiency**:
   - Peak RSS: 20-83 MB (no memory pressure)
   - Parallel scaling: cubes/sec increases with depth due to decomposition

4. **Topology Matters**:
   - Transpose symmetry: grid_4x3 ≈ grid_3x4 (both easy)
   - Barbell separators enable decomposition for k=6, not k=8
   - Grid without good separators benefits less from lookahead

## Research Implications

- Cube-and-Conquer effective for **structured modular networks** with good separators
- Hardness is **budget-sensitive** at boundary instances (3x6 needs 600s/cube)
- ~20K clauses appears to be a practical tractability threshold for current heuristic
- Instance family and graph topology matter more than raw variable count

## Next Steps
1. Investigate 3x7 hardness: improve branching heuristic or variable ordering
2. Test hypercube/torus topologies for different scaling behavior
3. Implement dynamic depth adjustment based on partial results
4. Add clause-learning to reduce cube search redundancy
5. Test 4x4 at depth 7-8 with high budget to find its limit
