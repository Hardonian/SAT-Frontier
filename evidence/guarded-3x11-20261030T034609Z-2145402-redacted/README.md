# Guarded grid 3x11 — redacted publication copy

The original local run is preserved unchanged. Paths identifying the local account, run location, and cgroup were replaced with placeholders. The campaign original-manifest.json and original-SHA256SUMS retain the original recorded checksums; they describe original bytes, not this redacted copy. campaign/manifest.json is regenerated to reflect the redacted campaign artifacts. SHA256SUMS at this directory covers the publication copy.

The recorded execution source was commit `4cda234278815873048b41de211c79c00e0e452c`, not the later publication parent. All 59 source hashes recorded in campaign/source-hashes.json were checked against Git blob bytes at that source commit; all matched. The source commit and publication parent are distinct histories; source hashes are the authoritative file-level provenance.

One run returned **unknown**, with 46 of 64 cubes incomplete; no exact total or probability is claimed. The campaign process returned 0 while the solver result returned 2. A completed campaign is not an exact solution. Independent verification here means an independent audit of recorded artifacts, hashes and internal consistency, not an independent solver rerun or verification of the numerical cube results.

The source commit is not an ancestor of the publication parent. `source-snapshot/` preserves the seven recorded source files whose bytes differ from that parent; the other 52 recorded source files match the publication parent. Together with campaign/source-hashes.json, this makes the recorded source bytes recoverable without claiming the publication parent was the run revision.
