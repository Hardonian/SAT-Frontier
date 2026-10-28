#!/usr/bin/env bash
# ==============================================================================
# SAT-Frontier: Upstream ETH Lean 4 Proof Build and Axiom Audit Runner
# Target: High-RAM environment (32GB+ RAM required for Mathlib dependency graph)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "========================================================================"
echo "SAT-Frontier: Formal Theorem Audit & Kernel Axiom Verification"
echo "========================================================================"
echo "Host: $(uname -n)"
echo "Date: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

if ! command -v lake >/dev/null 2>&1; then
    echo "ERROR: lake (Lean 4 build system) not found on PATH."
    echo "Please ensure elan/lean4 is activated: source \$HOME/.elan/env"
    exit 1
fi

echo "Lean version: $(lean --version)"
echo "Lake version: $(lake --version)"

# Check available memory
if [ -f /proc/meminfo ]; then
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
    echo "Total System RAM: ${TOTAL_RAM_GB} GB"
    if [ "${TOTAL_RAM_GB}" -lt 16 ]; then
        echo "WARNING: Less than 16GB RAM detected. Lean compilation may exit 137 (OOM)."
    fi
fi

# Determine safe worker concurrency to prevent RAM exhaustion
# Upstream Lean workers peak at ~1.5 - 2.5 GB RSS per worker
if [ -n "${TOTAL_RAM_GB:-}" ]; then
    SAFE_JOBS=$((TOTAL_RAM_GB / 4))
    if [ "${SAFE_JOBS}" -lt 1 ]; then SAFE_JOBS=1; fi
    if [ "${SAFE_JOBS}" -gt 16 ]; then SAFE_JOBS=16; fi
else
    SAFE_JOBS=4
fi
echo "Using worker concurrency: lake build -j ${SAFE_JOBS}"

AUDIT_DIR="${REPO_ROOT}/evidence/lean4-audit-001"
mkdir -p "${AUDIT_DIR}"

BUILD_LOG="${AUDIT_DIR}/lake_build.log"
AXIOM_LOG="${AUDIT_DIR}/axioms.log"

echo "Step 1: Building upstream formal target with bounded concurrency..."
BUILD_START=$(date +%s)
if lake build -j "${SAFE_JOBS}" > "${BUILD_LOG}" 2>&1; then
    echo "Lake build succeeded in $(( $(date +%s) - BUILD_START )) seconds."
    BUILD_STATUS="success"
else
    BUILD_EXIT=$?
    echo "Lake build exited with code ${BUILD_EXIT}."
    BUILD_STATUS="failed"
fi

echo "Step 2: Inspecting axioms on formal comparator..."
if [ "${BUILD_STATUS}" = "success" ]; then
    # Run axiom extraction
    if lean --run scripts/extract_axioms.lean > "${AXIOM_LOG}" 2>&1; then
        echo "Axiom extraction succeeded."
    else
        echo "Axiom extraction failed. Checking raw output..."
    fi
else
    echo "Build incomplete. Inspecting last 30 lines of build log:"
    tail -n 30 "${BUILD_LOG}"
fi

cat <<EOF > "${AUDIT_DIR}/summary.json"
{
  "build_status": "${BUILD_STATUS}",
  "concurrency": ${SAFE_JOBS},
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "build_log": "lake_build.log",
  "axiom_log": "axioms.log"
}
EOF

echo "Audit results written to ${AUDIT_DIR}/summary.json"
