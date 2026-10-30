#!/usr/bin/env bash
# Bounded aggregate cgroup; all arguments pass through to the campaign.
set -euo pipefail
cd "$(dirname "$0")/.."
# Timeout bounds hangs after a worker OOM; it signals the process group.
exec systemd-run --user --scope --quiet \
    -p MemoryMax=8G -p MemorySwapMax=0 -p TasksMax=32 \
    timeout --signal=TERM --kill-after=10s 900s \
    python3 scripts/run_epyc_cut_campaign.py "$@"
