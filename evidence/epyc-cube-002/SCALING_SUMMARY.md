# EPYC Cube-and-Conquer Scaling Summary
Generated: 2026-10-28 (final v2)

## Environment
- CPU: 64-core AMD EPYC
- Memory: 172 GB DDR4
- NUMA: single node, interleave mode
- Runner: resource-aware epyc_runner.py with checkpoint/resume

## Modular Network Scaling Results

### Grid Topology (p=9/10, WMC)
| Instance | Vars | Clauses | Max Depth | Status | Hardness |
|----------|------|---------|-----------|--------|----------|
| grid_1x5 | 6 | 8 | 10 | EXACT | trivial |
| grid_1x10 | 11 | 13 | 10 | EXACT | trivial |
| grid_1x15 | 16 | 18 | 10 | EXACT | trivial |
| grid_1x20 | 21 | 23 | 10 | EXACT | trivial |
| grid_2x5 | 29 | 121 | 8 | EXACT | trivial |
| grid_2x6 | 48 | 289 | 8 | EXACT | trivial |
| grid_2x7 | 83 | 673 | 8 | EXACT | easy |
| grid_2x8 | 150 | 1537 | 8 | EXACT | easy |
| grid_2x9 | 281 | 3457 | 8 | EXACT | moderate |
| grid_2x10 | 540 | 7681 | 13 | EXACT | moderate |
| grid_2x11 | 1055 | 16897 | 5 | UNKNOWN | hard |
| grid_2x12 | 2082 | 36865 | 3 | UNKNOWN | hard |
| grid_3x3 | 24 | 77 | 8 | EXACT | easy |
| grid_3x4 | 55 | 323 | 8 | EXACT | easy |
| grid_3x5 | 147 | 1332 | 8 | EXACT | moderate |
| grid_3x6 | 441 | 5297 | 8 | EXACT* | moderate |
| grid_3x7 | 1401 | 20430 | 1 | UNKNOWN | hard |
| grid_3x8 | 4559 | 77111 | 1 | UNKNOWN | hard |
| grid_4x3 | 55 | 323 | 8 | EXACT | easy |
| grid_4x4 | 208 | 2097 | 17 | EXACT | moderate |
| grid_4x5 | 1007 | 14109 | 4 | UNKNOWN | hard |
| grid_5x5 | 8552 | 156945 | 2 | UNKNOWN | intractable |

*With 600s per-cube budget and 64 workers

### Barbell Topology (WMC)
| Instance | Vars | Clauses | Max Depth | Status | Hardness |
|----------|------|---------|-----------|--------|----------|
| barbell_k6 | ~200 | ~800 | 8 | EXACT | easy |
| barbell_k8 | 3971 | 27403 | 5 | UNKNOWN | hard |
| barbell_k10 | - | - | gen timeout | N/A | intractable |

### Policy Instances (Unweighted)
- 32/32 instances solved exactly at depth 4, 32 workers
- Wall times: 0.08-0.10s per instance
- Peak RSS: 20-21 MB

## Key Findings

1. **Scaling Cliffs**:
   - 2xN: hard at 2x11 (d3), exact to d13 for 2x10
   - 3xN: hard at 3x7 (d1), exact to d8 for 3x6 (with budget)
   - 4x4: exact to d17, timeout at d18
   - 4x5: hard at d4

2. **Structural Hardness Patterns**:
   - 3x7 and 3x8: hard even at d1 with 600s/cube
   - 2x11 and 2x12: hard at d3 and d1 respectively
   - Hardness is NOT just variable count - topology matters

3. **Weight Consistency**:
   - grid_3x6: weight=0.969984456181915 consistent across d4-d8
   - grid_4x4: weight=0.9750463495770658 consistent across d5-d17
   - barbell_k6: weight=0.799967877783281 consistent across d5-d8

4. **Resource Efficiency**:
   - Peak RSS: 20-163 MB (no memory pressure)
   - Parallel scaling: cubes/sec increases with depth due to decomposition

5. **Budget Sensitivity**:
   - grid_3x6: UNKNOWN at 60s/cube, EXACT at 600s/cube
   - Hardness at boundary instances is budget-sensitive
   - Structural hardness (3x7, 2x11+) persists even at d1 with high budget

## Evidence Manifest
All results stored in:
- evidence/epyc-cube-002/ (200+ result JSONs)
- evidence/epyc-cube-001/instances/ (30+ CNF instance files)
- evidence/epyc-cube-002/SCALING_SUMMARY.md (this document)

Total evidence: 200+ result JSONs, 30+ instance files, 1 summary document.

## Research Implications

- Cube-and-Conquer effective for **structured modular networks** with good separators
- Hardness is **topology-dependent**, not just size-dependent
- 3x7 and 2x11+ represent phase transitions in grid WMC complexity
- For industrial WMC, instance family matters more than raw variable count

## Next Steps
1. Investigate 3x7 hardness: improve branching heuristic or variable ordering
2. Test hypercube/torus topologies for different scaling behavior
3. Implement dynamic depth adjustment based on partial results
4. Add clause-learning to reduce cube search redundancy
5. Test 4x5 with high budget to see if budget or structure is the blocker
