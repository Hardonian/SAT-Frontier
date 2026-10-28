# Independent exact-counting development baseline

This is development correctness evidence, **not** a performance benchmark, a holdout evaluation, or a proof. Decision SAT and #SAT remain separate. All binaries and third-party source are outside this repository; no license for this project is implied.

## Selection and provenance

The selected independent implementation is [sharpSAT-TD](https://github.com/Laakeri/sharpsat-td), official commit `0c234c11b77115bad89484e80e1d2fc95dd42317`. Its README identifies exact unweighted model counting and the 2024 model-counting competition output format. The upstream project's `LICENSE` is MIT (SHA-256 `271473073462783410126a469252a7c541da4bbc5432f13b598a897771af4dee`); included flowcutter's `LICENSE` is BSD-2-Clause (SHA-256 `8e6dd335e858988592fc6af52e20151f90bac3e0dd6dba97e1f5e6a74b555b7a`) and clhash is Apache-2.0 (SHA-256 `b40930bbcf80744c86c46a12bc9da056641d722716c378f5659b9e555ef833e1`). Check dependency notices and obligations before any distribution. No third-party binary/source is distributed here.

The tested Linux binary SHA-256 is `85b94b45c3967df384f5ced2e4670fe270f3fc77ee67ca943b6b390ac75f92b5`. This is a build-specific hash, not a claim that all builds reproduce it. The evidence manifest records hashes of the resolved shared libraries as well as Python, source, tests, config, binary and Git dirty state. A newly supplied binary is not proven to originate from that revision; `matches_tested_binary` is an exact byte comparison only.

On this Ubuntu 24.04 WSL node, g++ was `13.3.0` and CMake `3.28.3`. The machine lacked dev packages and passwordless sudo. The following commands reproduce the *actual build technique*: download Ubuntu packages without system installation, extract them into scratch, and use absolute dynamic-library paths. Use a fresh scratch directory; apt versions can change, in which case compare package hashes and investigate. The local `libgmp-dev` package was `2:6.3.0+dfsg-2ubuntu6.1` SHA-256 `a9847b5ecfff791a46cb198f29a06d9d23a20afdfdd434812f2b44ccfb61d46a`; `libgmpxx4ldbl` SHA-256 `6f59344240b6dc139ed23ef236b8aa146e5d25e23aa90e79f814e2e4cc4b5752`; `libmpfr-dev` `4.2.1-1build1.1` SHA-256 `362fcdeb7dff545af83e65a3a972519185efd4a231c23e13d519cf97a5c8e3e4`.

```bash
# Scratch is outside SAT-Frontier; no root installs.
S=/home/scott/.hermes/cache/scratch
mkdir -p "$S/sat-local-gmp" "$S/sat-local-mpfr"
(cd "$S/sat-local-gmp" && apt-get download libgmp-dev libgmpxx4ldbl && for f in ./*.deb; do dpkg-deb -x "$f" root; done && sha256sum ./*.deb)
(cd "$S/sat-local-mpfr" && apt-get download libmpfr-dev && for f in ./*.deb; do dpkg-deb -x "$f" root; done && sha256sum ./*.deb)
git clone https://github.com/Laakeri/sharpsat-td.git "$S/sharpsat-td-rebuild"
git -C "$S/sharpsat-td-rebuild" checkout --detach 0c234c11b77115bad89484e80e1d2fc95dd42317
D="$S/sat-local-gmp/root/usr"; M="$S/sat-local-mpfr/root/usr"
export CPLUS_INCLUDE_PATH="$D/include:$D/include/x86_64-linux-gnu:$M/include"
export C_INCLUDE_PATH="$CPLUS_INCLUDE_PATH"
export LIBRARY_PATH="$D/lib/x86_64-linux-gnu:$M/lib/x86_64-linux-gnu"
export LD_LIBRARY_PATH="$LIBRARY_PATH"
cmake -S "$S/sharpsat-td-rebuild" -B "$S/sharpsat-td-rebuild/build" -DCMAKE_BUILD_TYPE=Release \
  -DGMP_LIB=/lib/x86_64-linux-gnu/libgmp.so.10 \
  -DGMPXX_LIB="$D/lib/x86_64-linux-gnu/libgmpxx.so" \
  -DMPFR_LIB=/lib/x86_64-linux-gnu/libmpfr.so.6
cmake --build "$S/sharpsat-td-rebuild/build" -j2
sha256sum "$S/sharpsat-td-rebuild/build/sharpSAT"
```

The actual run used `/home/scott/.hermes/cache/scratch/sat-d4v2-upstream/deps/root/usr` for `D` and `/home/scott/.hermes/cache/scratch/sat-deps-mpfr/root/usr` for `M`; `evidence/v02-baseline-provenance/sharpsat-td-build.log` preserves compiler output, including warnings. The upstream `setupdev.sh` uses unbounded `make`; the direct CMake equivalent above caps builds at two workers. `-decot 0` deliberately disables the expensive flowcutter time budget. The adapter invokes the tested binary as `sharpSAT -decot 0 -decow 100 -tmpdir <private-temp> -cs 64 <input.cnf>` and accepts exactly one `c s exact arb int <nonnegative integer>` line only after successful exit. It never maps a decision-SAT status to a count.

## Development evidence and limits

```bash
# These exact paths reference the local tested build; set LD_LIBRARY_PATH as above.
export SAT_FRONTIER_SHARPSAT=/home/scott/.hermes/cache/scratch/sat-sharpsat-td/build/sharpSAT
export LD_LIBRARY_PATH=/home/scott/.hermes/cache/scratch/sat-d4v2-upstream/deps/root/usr/lib/x86_64-linux-gnu
python3 -m unittest discover -s tests -v
python3 -m sat_frontier.crosscheck --binary "$SAT_FRONTIER_SHARPSAT" --out evidence/v02-independent-development-004
python3 verify_evidence.py evidence/v02-independent-development-004 --source-root evidence/v02-independent-development-004/source-snapshot
```

The `--out` directory is intentionally create-only: the recorded run already exists, so choose a new name to reproduce it. The actual run completed **168/168** exact paired comparisons, with zero mismatches; 24 base formulas across random, planted, disconnected and contradictory families at 18, 24 and 32 variables, each with seven deterministic variants (identity, variable reversal, clause/literal reorder, duplicate clause, tautology, forced fresh variable and unused fresh variable). Two seeds per family/size are development inputs, not holdout. 28 tests passed with the actual binary, including the exhaustive small-formula suite and process failures, malformed output, timeout, memory failure, metamorphic relations, retention/minimization and legacy evidence verification. Without the binary environment variable the real executable test explicitly skips.

Rows store independent stdout/stderr, statuses, exact counts, per-worker wall times and RSS fields. They stop on any error, unknown, mismatch or metamorphic failure; original evidence is flushed before deterministic clause/literal deletion minimizes a confirmed mismatch. An inconclusive minimization aborts and retains the original. The historical related-counter campaign still labels large results `unchecked`; independent comparisons are in the dedicated development campaign, not silently retrofitted into old runs.

Linux direct children use a 536,870,912-byte `RLIMIT_AS` hard address-space limit; this is not an RSS cap, and does not aggregate descendant memory. The kernel kills/denies allocations as applicable; an allocation failure is not a zero count. Linux `wait4` / `getrusage` report peak RSS in **KiB**, including startup and potentially an inherited fork high-water floor. The observed ranges were 29,524–29,780 KiB for both process types; the identical floor makes these unsuitable for comparative solver-memory claims. Timeout/error workers can have null measurements; unsupported platforms explicitly return null/unsupported and reject requested hard limits. The dedicated counter timeout kills its Linux process group. The standard `campaign` accepts optional positive integer `memory_bytes`; without it there is no hard memory cap. No GPU was used.

## A preserved independent-counter failure

An earlier candidate, official [sharpSAT](https://github.com/marcthurley/sharpSAT) commit `edfbde3424ce17d72d7f8d8f5b8681f2247f4932` (MIT; license SHA-256 `411946f783f657a896a796a7dac6884a7218aecf212432a141b79364e9fb8cf1`), built with g++ using `-include cstdint` and the local GMP dev files. Its binary SHA-256 was `faf96ca7cab5dfab4b8e6f00058ed78be2b1eab1ffab65dc8f7c27ab2ac1e5fa`. It returned **61** versus SAT-Frontier's **0** on a generated 18-variable contradictory formula. Deterministic reduction found `p cnf 18 1\n0\n`: exhaustive oracle **0**, sharpSAT **262144**. Original and minimized CNFs, raw logs, replay, frozen source snapshot and hashes are in `evidence/sharpsat-legacy-disagreement/`. The run is intentionally marked incomplete, not green. The older upstream README itself notes a prior counting bug; this observed specific failure is not a blanket finding about other versions. Switching to sharpSAT-TD did not erase the failure.

The alternative official d4v2 candidate at `15eff31962466804a48374826b9e5a746fc2766e` was also inspected (LGPL-2.1 license SHA-256 `787614cbf8a88a1d2cfd3f82245be054d7692b815bab70e31a6402c7c2755ffa`). Its unmodified build first lacked Boost and then failed because `3rdParty/patoh/libpatoh.a` was absent. See preserved logs; it is **not** the selected binary. Builds were affinity-limited to two CPUs and made no privileged installation.

## Historic integrity and scan

The original smoke evidence is unchanged. Its source hashes intentionally refer to the original files, not current files. Verify against the original archive without weakening source checks:

```bash
mkdir -p /home/scott/.hermes/cache/scratch/sat-original-verify
unzip -q artifacts/bootstrap/sat-frontier-v0.1.0.zip -d /home/scott/.hermes/cache/scratch/sat-original-verify
python3 verify_evidence.py evidence/smoke-train --source-root /home/scott/.hermes/cache/scratch/sat-original-verify/sat-frontier
```

The default remains the current checkout and must fail on mismatching historical source. The legacy tests exercise both matching and tampered source roots. Each new development run has its own matching source snapshot; `sha256sum -c SHA256SUMS` from each evidence directory checks all captured files without running solvers. These checks establish integrity, not validity.

Bandit was run on live changed Python and all retained Python snapshots; logs are `evidence/v02-baseline-provenance/bandit-{live,snapshots}.txt`. Live: exit 1, 15 low, 0 medium/high. Snapshots: exit 1, 79 low, 0 medium/high. Nothing was suppressed. The B404/B603/B606 subprocess/exec findings are real trust-boundary cautions: the user-supplied binary is executed, not sandboxed, and `ldd` is used on it, so only use trusted binaries. Arguments are arrays without a shell; the CNF and working directory are private temporary files. B607 flags PATH lookup for `git`/`ldd`; run under a trusted PATH. B311 in historical snapshots concerns intentionally deterministic research/test PRNGs, not cryptographic uses. These limitations are not a claim of security hardening.
