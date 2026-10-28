# Decisions

- 2026-10-28 v0.2.1: Implement fail-closed holdout guards, atomic reservation, and execute the preregistered 1,200-run held-out evaluation on fresh seeds (30001–30030) across 4 families. Record the definitive negative result (no speedup, feature overhead dominates) and independent oracle verification without claiming algorithmic superiority or data leakage.
- 2026-10-28 v0.2: Preserve the exact original ZIP and bundle history in a private repository. The owner explicitly authorized private repository creation and a draft release; no public redistribution license has been chosen.
- Select pinned sharpSAT-TD as the independent counting baseline after retaining and minimizing a real disagreement with an earlier candidate. Decision-SAT tools are not #SAT comparators. Treat stdout as valid only after successful bounded execution and strict parse.
- Keep the policy search finite and train-only. Report its negative/limited result, retain all raw observations and node-limited unknowns, and do not run holdout with missing freeze or overlap guards.
- Treat the ETH audit and hosted CI as incomplete: the pinned Lean target and comparator did not finish, and GitHub reported a billing/spending-limit block before jobs started. Do not label either verified.

- 2026-10-28: Use working title SAT-Frontier; no GitHub namespace was created or claimed. Independent project because the request is new SAT/complexity research. Preserve existing labs.
- Keep the project useful whether the upstream claim is ultimately accepted, revised, or rejected. Algorithms and evidence do not depend on assuming ETH or its negation.
- Begin with exact counting because it exposes unsound preprocessing that decision SAT can hide. Mature counting and decision baselines remain distinct.
- Dependency-free Python prototype favors auditability. A native implementation must earn its added complexity through profiling and cross-language differential tests.
- CPU only in v0.1. GPU capability, load, placement, and correctness gates precede accelerator experiments. No accelerator or remote-host success is claimed.
- Use raw evidence and a hypothesis ledger. No novelty, asymptotic, or industrial-competitiveness claims from the smoke campaign.
- Do not choose a redistribution license on the owner's behalf. All code here was authored for this package; add the owner's chosen license before public release.
