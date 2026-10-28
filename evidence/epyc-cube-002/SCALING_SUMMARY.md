# EPYC Cube-and-Conquer Scaling Summary
Generated: 2026-10-28

## Environment
- CPU: 64-core AMD EPYC
- Memory: 172 GB DDR5
- NUMA: single node, interleave mode
- Runner: resource-aware epyc_runner.py with checkpoint/resume

## Modular Network Scaling Results

### Grid Topology (p=9/10, WMC)
| Instance | Vars | Clauses | d5 | d6 | d7 | d8 | Hardness |
|----------|------|---------|----|----|----|----|----------|
| grid_2x5 | 29 | 121 | EXACT | EXACT | EXACT | EXACT | trivial |
| grid_2x6 | 48 | 289 | EXACT | EXACT | EXACT | EXACT | trivial |
| grid_3x3 | 24 | 77 | EXACT | EXACT | EXACT | EXACT | easy |
| grid_3x4 | 55 | 323 | EXACT | EXACT | EXACT | EXACT | easy |
| grid_3x5 | 147 | 1332 | EXACT | EXACT | EXACT | EXACT | moderate |
| grid_3x6 | 441 | 5297 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | hard |
| grid_4x4 | 208 | 2097 | EXACT | EXACT | EXACT | EXACT | moderate |
| grid_4x5 | 1007 | 14109 | UNKNOWN | UNKNOWN | UNKNOWN | N/A | hard |
| grid_5x5 | 8552 | 156945 | N/A | N/A | N/A | N/A | intractable |

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

1. **Scaling Cliff**: Grid hardness jumps sharply between 3x5 (exact) and 3x6 (UNKNOWN)
2. **Topology Matters**: Barbell k=6 decomposes well; k=8 exceeds budget despite graph separators
3. **Weight Consistency**: Weight fraction preserved across depths for same instance
4. **Resource Efficiency**: Peak RSS 20-83 MB; no memory pressure
5. **Parallel Scaling**: Near-linear scaling with depth due to independent cubes

## Research Implications

- Cube-and-Conquer is effective for **structured modular networks** with good separators
- Grid networks without separator hints benefit less from decomposition
- The 3x5/3x6 cliff suggests a phase transition in search space complexity
- For industrial WMC, instance family matters more than raw variable count

## Next Steps
1. Investigate 3x6 hardness: improve branching heuristic or variable ordering
2. Test hypercube/torus topologies for different scaling behavior
3. Implement dynamic depth adjustment based on partial results
4. Add clause-learning to reduce cube search redundancy
