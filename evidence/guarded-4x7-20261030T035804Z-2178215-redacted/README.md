# Guarded grid 4x7: interrupted timeout (partial evidence)

This is a privacy-redacted publication copy of a partial run, not an exact result. The 180-second outer timeout exited 124; no completed run records, result JSON, checkpoints, or final manifest were produced. No count, weight, cube completion, or hardness conclusion is asserted. Depth 8, 4 workers, 12 seconds and 100,000 nodes per cube were configured.

Cgroup capture reported peak memory 2,340,810,752 bytes and zero oom/oom_kill events; swap current was zero at capture. The capture was immediately after timeout, before remaining descendants were cleaned up; it does not establish every detail of termination.

The original files and original `partial-SHA256SUMS` remain untouched locally. The included original ledger records hashes of original bytes, and therefore will not verify the redacted files. `PUBLICATION-SHA256SUMS` covers this derived copy including the original ledger. Redactions replace local evidence paths and cgroup path in invocation.txt, console.log and campaign/config.json; all other original files are byte-preserved. Empty original directories are not represented in Git.

The recorded source revision is `4cda234278815873048b41de211c79c00e0e452c`, which is not an ancestor of the publication base. To make provenance independently inspectable, `source-snapshot/` contains the 59 files at that revision, each verified against the run's original `campaign/source-hashes.json`; this proves byte agreement for listed files, not a clean source tree or full environment. The instance SHA-256 is `faece45a06eb21debf27e85751978ad8bfd003f0b2f0e5fc7c8fbaadc2ed035d`.

Verify this copy: `sha256sum -c PUBLICATION-SHA256SUMS` from this directory. Verify the snapshot against `campaign/source-hashes.json` separately.
