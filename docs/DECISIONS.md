# Decisions

- 2026-10-28: Use working title SAT-Frontier; no GitHub namespace was created or claimed. Independent project because the request is new SAT/complexity research. Preserve existing labs.
- Keep the project useful whether the upstream claim is ultimately accepted, revised, or rejected. Algorithms and evidence do not depend on assuming ETH or its negation.
- Begin with exact counting because it exposes unsound preprocessing that decision SAT can hide. Mature counting and decision baselines remain distinct.
- Dependency-free Python prototype favors auditability. A native implementation must earn its added complexity through profiling and cross-language differential tests.
- CPU only in v0.1. GPU capability, load, placement, and correctness gates precede accelerator experiments. No accelerator or remote-host success is claimed.
- Use raw evidence and a hypothesis ledger. No novelty, asymptotic, or industrial-competitiveness claims from the smoke campaign.
- Do not choose a redistribution license on the owner's behalf. All code here was authored for this package; add the owner's chosen license before public release.
