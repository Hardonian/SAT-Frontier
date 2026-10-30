#!/usr/bin/env bash
# ==============================================================================
# SAT-Frontier: High-Core EPYC Parallel Cut-Compilation Campaign Launcher
# Optimized for 64-core AMD EPYC server with high-capacity DDR4 RAM
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "========================================================================"
echo " SAT-Frontier: High-Core EPYC Cut-Compilation Scaling Campaign"
echo "========================================================================"
echo "Host:       $(uname -n) ($(uname -s) $(uname -m))"
echo "Date (UTC): $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

AVAILABLE_CORES=$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)
echo "Execution Contexts Detected: ${AVAILABLE_CORES}"

# Recommend worker allocation
if [ "${AVAILABLE_CORES}" -ge 64 ]; then
    WORKERS=64
elif [ "${AVAILABLE_CORES}" -ge 32 ]; then
    WORKERS=32
elif [ "${AVAILABLE_CORES}" -ge 16 ]; then
    WORKERS=16
else
    WORKERS="${AVAILABLE_CORES}"
fi

echo "Allocated Worker Count: ${WORKERS}"

# NUMA Interleaving on Linux EPYC systems
NUMA_CMD=""
if command -v numactl >/dev/null 2>&1; then
    NUMA_NODES=$(numactl --show | grep "nodebind" | awk '{print NF-1}' || echo 1)
    if [ "${NUMA_NODES}" -gt 1 ]; then
        echo "Multi-NUMA Topology Detected (${NUMA_NODES} nodes). Enabling memory interleaving..."
        NUMA_CMD="numactl --interleave=all"
    fi
fi

# Ensure pre-compiled frontier cut instances exist
if [ ! -d "instances/epyc-cut-frontier" ] || [ -z "$(ls -A instances/epyc-cut-frontier/*.cnf 2>/dev/null)" ]; then
    echo "Frontier cut instances not found. Pre-compiling..."
    python3 scripts/prepare_epyc_cut_campaign.py
fi

echo "Launching High-Core EPYC Cut Campaign across depths 4, 6, 8..."
${NUMA_CMD} python3 scripts/run_epyc_cut_campaign.py \
    --workers "${WORKERS}" \
    --depths 4 6 8 \
    --seconds-per-cube 30.0 \
    --max-nodes-per-cube 200000

echo "Verifying cryptographic evidence hashes..."
python3 verify_evidence.py evidence/epyc-cut-001

echo "========================================================================"
echo " EPYC CAMPAIGN COMPLETED AND VERIFIED"
echo "========================================================================"
