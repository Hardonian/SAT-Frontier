# M0 local evidence

Smoke train run: `evidence/smoke-train`. Frozen configuration: two sizes (8/12), two clause/variable ratios (2/4), two train seeds and four families, evaluated by five variants. Every one of the 160 solver runs returned an exact count matching the independent exhaustive oracle. All 32 inputs are retained by SHA-256. No holdout campaign was run.

Total recursive nodes across the eight cases in each family:

| Family | baseline | memo | components | combined | balanced |
| --- | ---: | ---: | ---: | ---: | ---: |
| contradictory | 8 | 8 | 8 | 8 | 8 |
| disconnected | 298 | 220 | 153 | 153 | 151 |
| planted | 256 | 236 | 252 | 242 | 242 |
| random | 236 | 224 | 232 | 226 | 236 |

The disconnected positive control shows fewer nodes under decomposition in this tiny sample. Node reduction alone is not a wall-time improvement: component detection and caching cost time and memory. Timings are included in raw data but single repeats on tiny cases do not justify performance claims. No statistical confidence interval or mature-solver comparison has been performed. H1 receives preliminary support only for this smoke control; H2/H3 remain unresolved for useful workloads. No novel algorithm has been discovered.

The 20-test unittest suite additionally covers exact small-formula enumeration, random mixed-width formulas, edge-case counting, malformed inputs, resource exhaustion, cache limits, split separation and a real subprocess campaign. See `tests/test_core.py` and `evidence/tests.txt` for actual verification output.
