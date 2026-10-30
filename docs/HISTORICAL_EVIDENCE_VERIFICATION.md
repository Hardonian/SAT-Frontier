# Historical evidence verification using a derived copy

The historical evidence manifests contain byte-level SHA-256 values. Some Git artifacts use LF line endings even though the recorded digests match CRLF bytes. The Git artifacts, commit history, and the ledgers must not be edited to make verification pass. A matching reconstructed byte stream is a derived representation consistent with the recorded hash; it does not prove where or when the original CRLF bytes were produced.

## Reproduce

From this checkout, with Git and Python 3.12 or later installed, choose a **new, nonexistent directory outside the repository** whose parent exists:

```sh
python3 scripts/verify_historical_copy.py /path/to/new-external-verification-directory --revision 935724f197af3f1c1b89211d0d38c2d2a3e621df
```

The default revision is HEAD, which may fail if source files have changed since the evidence was produced; use the explicit commit above to reproduce the result below. The script extracts a Git archive of that commit, ignoring uncommitted work. It checks artifact digests referenced in each of the 16 manifests and any SHA256SUMS file. Only when the Git bytes mismatch, contain LF but no CR or NUL, and their LF-to-CRLF transformation matches the unchanged ledger digest exactly, it writes the reconstructed bytes to the external copy and hashes them again. Any other mismatch, conflicting hashes, unsafe ledger path, missing file, unsupported archive member, or pre-existing destination fails closed. A failed attempt retains its partial external copy for inspection; choose another fresh directory for a retry.

It then invokes the 16 historical suite-specific verifiers in the copy. The generated `historical_reconstruction_report.json` records the full commit ID, every reconstructed file's Git-byte and reconstructed SHA-256, number of distinct ledger targets checked, and each verifier's command, exit status, stdout and stderr. The derived copy and report are not canonical evidence or a replacement for the Git artifacts. The script does not use the historical master verifier, which writes its own summary and also runs tests requiring Git metadata absent from a Git archive.

## Observed result

On commit `935724f197af3f1c1b89211d0d38c2d2a3e621df`, the external copy at `/home/scott/.hermes/cache/scratch/sat-historical-repro-20261029-b` checked 861 distinct ledger targets, reconstructed 32 files, and all 16 suite-specific verifier processes exited zero. The report in that directory contains the actual output. The local checkout's test suite separately passed 132 tests with one skipped external sharpSAT integration. The original master verifier was also tried in a reconstructed archive copy: its 16 suites passed but its bundled unit-test step failed because the archive has no `.git`; that is not a successful master-verifier run.

At published revision `62f09fc9ef69050263303a9900c4f985d149c6f2`, the same derived-copy procedure checked 861 targets and reconstructed 32 files, but only 6 of 16 verifiers passed: 10 failed on changed source hashes (`sat_frontier/wmc.py` or `sat_frontier/cube_conquer.py`). These failures are not bypassed; use the historical revision to reproduce its result. The original Git bytes are not a 16-suite pass.

Verifier scope varies: the generic verifier explicitly checks integrity rather than scientific validity; policy verifiers also independently recompute bounded oracle counts; EPYC verifiers check their stated invariants and ledger entries. These results do not independently establish every scientific claim, theorem, performance claim, ledger completeness, or original provenance. Existing ledger digests are trusted inputs, not authenticated signatures. Scratch paths may be pruned; rerun the command to regenerate the report.
