# Policy holdout safety checkpoint — not executed

The v0.2 policy holdout remains **unconsumed and unrun**. No instance from
seeds 30001–30030 was generated or evaluated for this checkpoint. No result,
negative or positive, is claimed.

`sat_frontier/holdout_guard.py` adds building blocks: a byte-pinned historical
winner and train-source/verifier check, exact CNF-content overlap and duplicate
checking, and a create-only, fsync-backed local reservation. Tests exercise
winner/source/config tampering, renamed overlapping CNFs, duplicates, failure
during reservation, and an actual SIGKILL after reservation. Historical train
protocol and evidence remain unchanged.

## Stop condition

**These functions are not an executable holdout protocol. Do not use them to
start the holdout.** There is no integrated runner that guarantees guard order,
fixed output location and create-only raw CSV/JSONL from the first result,
independent per-instance oracle validation, complete timeout/error accounting,
rotated 1,200-run grid, and paired instance-level analysis. There is no new,
committed integrated-source holdout preregistration that freezes that runner,
configuration, winner, all imported source, and analysis before first use. The
reservation helper accepts a digest but does not authenticate a preregistration;
its existence alone must not be treated as such. The older generic `campaign`
can run a configured holdout without these policy-specific guards. Therefore
running any holdout now would risk irreversible exposure without enforcing the
scientific requirements, even though the train evidence verifies.

The local reservation directory is intentionally irreversible by the helper,
including when empty after a crash; it is not a security boundary against an
operator deleting it, Git history changes, other clones, or direct calls to an
unguarded solver. Any future design must explicitly account for these limits.
Exact byte hashes detect identical DIMACS files, not logically equivalent CNFs.
Do not reserve the actual split for tests. Do not delete a real reservation or
reuse a split after any attempted use or interruption.

Before first use, implement and test the complete integrated, fail-closed
runner and independent verifier, freeze every dependency and complete analysis
plan in a committed preregistration, establish a durable one-shot record, and
review exact overlap against all prior relevant evidence. Only then run the
fixed 30 seeds/family, five repeats, two policies, sequential CPU plan. Record
source revision and preregistration before first access, preserve raw records
on every failure, and do not tune against holdout data. The tiny synthetic study
alone does not satisfy the mature-baseline performance gate or establish
industrial performance.
