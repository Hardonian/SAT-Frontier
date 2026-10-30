# EPYC 3×10 cross-depth evidence and independent validation

Two 4-worker runs of the pinned grid_3x10 weighted CNF completed exactly, at depths 6 and 8 (64 and 256 cubes, respectively; no incomplete cubes). Both returned the rational weight

`48223721615170979353976679548137128229909096749/50000000000000000000000000000000000000000000000`.

The independent graph-connectivity frontier transfer program reproduces this weight and agrees with brute-force enumeration on 2×2, 2×3, and 3×3 grids. This is an independent algorithmic cross-check, not a formal proof; the comparison assumes the pinned CNF represents the same grid. The CNF SHA-256 is `57ca8fa20851c40417d13bf6ff344b793a225a84ea3f5d8237bfaa2187a19d62`. Run `python3 evidence/epyc-independent-validation-20261030T032834Z-2096631/validate.py` from the repository root.

## Interrupted work

- The separate 32-worker escalation recorded one exact 3×10 depth-8 result before interruption; its campaign listed three instances but did not complete. The captured resource log reports status 124 and a 1400-second timeout command but only 3:28.28 elapsed; the reason for this discrepancy is not established. Do not infer results for the remaining instances.
- The separate 4×7 depth-8 attempt was interrupted by the foreground tool timeout at 420 seconds, before its planned 480-second outer timeout. Its status record reports no result or checkpoint. This is neither a new exact result nor a new solver-returned unknown.

## Publication copies and integrity

The five associated evidence directories are publication copies. Local absolute paths were redacted only in copies; originals were not altered. Each copy has `PUBLICATION_REDACTIONS.json`, listing the original and publication hashes of changed files, and `PUBLICATION_SHA256SUMS`, checking all other files in that directory, including the original checksum ledgers and manifests. Verify with `cd evidence/<directory> && sha256sum -c PUBLICATION_SHA256SUMS`.

Original `SHA256SUMS` and `manifest.json` retain their historical semantics and hashes: they identify original unredacted bytes, so their checks of redacted files intentionally do not match publication-copy bytes. Original cross-depth `SHA256SUMS` was checked against all 331 original files successfully before copying; the original validation and interruption ledgers also passed. The redaction map links original to published file hashes; it does not claim the redacted bytes have the original digest. Source hashes identify the code used at run time and are not claims that later repository revisions have identical source bytes.
