#!/usr/bin/env bash
# ==============================================================================
# SAT-Frontier: EPYC High-Core Parallel Cube-and-Conquer Campaign Runner
# Target: AMD EPYC (up to 128 cores / 256 threads, multi-NUMA)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "========================================================================"
echo "SAT-Frontier: Parallel Cube-and-Conquer Campaign on High-Core Hardware"
echo "========================================================================"
echo "Host: $(uname -n) ($(uname -s) $(uname -m))"
echo "Date: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

# Detect CPU cores
AVAILABLE_CORES=$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)
echo "Detected available CPU execution contexts: ${AVAILABLE_CORES}"

if command -v lscpu >/dev/null 2>&1; then
    CPU_MODEL=$(lscpu | grep "Model name:" | sed 's/Model name:[ \t]*//' || true)
    NUMA_NODES=$(lscpu | grep "NUMA node(s):" | sed 's/NUMA node(s):[ \t]*//' || true)
    echo "CPU Model: ${CPU_MODEL:-unknown}"
    echo "NUMA Nodes: ${NUMA_NODES:-1}"
fi

# Determine core tiers up to available cores
CORE_TIERS="1"
for tier in 2 4 8 16 32 64 128; do
    if [ "${tier}" -le "${AVAILABLE_CORES}" ]; then
        CORE_TIERS="${CORE_TIERS},${tier}"
    fi
done

# If available cores is not a power of 2, append max cores
if ! echo ",${CORE_TIERS}," | grep -q ",${AVAILABLE_CORES},"; then
    CORE_TIERS="${CORE_TIERS},${AVAILABLE_CORES}"
fi

OUTPUT_DIR="${REPO_ROOT}/evidence/epyc-cube-conquer-001"
echo "Core scaling tiers: ${CORE_TIERS}"
echo "Output directory:   ${OUTPUT_DIR}"

# Run EPYC scaling benchmark
python3 -m sat_frontier.epyc_runner \
    --cores "${CORE_TIERS}" \
    --output "${OUTPUT_DIR}" \
    --depth 5 \
    --seconds 30.0

echo "Campaign complete. Verifying cryptographic evidence hashes..."
python3 verify_evidence.py "${OUTPUT_DIR}"

echo "All evidence verified successfully."

