# Primary source register

Checked 2026-10-28. These references are mutable and have not been pinned or vendored. Do not infer an audited proof from this register. No external source code is included.

| ID | Source | Used for | Status |
| --- | --- | --- | --- |
| S1 | https://openai.com/index/building-scientific-understanding-with-academic-communities/ | Announcement, dates, collaboration | Read |
| S2 | https://github.com/openai/math/blob/main/lean/docs/378.md | Published formalization scope and differing bounds | Read |
| S3 | https://github.com/openai/math/blob/main/lean/ComparatorChallenges/SubexponentialSAT.lean | Comparator discovery | Located; dependency audit/build not run |
| S4 | https://github.com/openai/math/blob/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/paper.pdf | Full manuscript | Located; PDF extraction unavailable |
| S5 | https://github.com/crillab/d4v2 | Exact model-counting baseline candidate | Official repository located; not installed |
| S6 | https://github.com/arminbiere/cadical | Decision-SAT baseline candidate | Official repository located; not installed |

When integrating S5/S6, pin revisions, inspect licenses and build instructions, record binary hashes and exact command lines. S6 comparisons apply to decision SAT, not exact counting. Select an independently implemented exact counter for the counting track.
