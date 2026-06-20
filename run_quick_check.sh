#!/usr/bin/env bash
# Zero-dependency confidence check (no install, no network).
#   [1] Reproduces the full n=3 census (independent third-party verifier).
#   [2] Verifies the recorded certificates.
# Both steps use only the Python 3 standard library and require Python >= 3.10
# (the scripts use int.bit_count). This script auto-selects a suitable python.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"

pick_python() {
  for p in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$p" >/dev/null 2>&1 \
       && "$p" -c 'import sys;exit(0 if sys.version_info[:2]>=(3,10) else 1)' 2>/dev/null; then
      command -v "$p"; return 0
    fi
  done
  return 1
}

PY="$(pick_python)" || { echo "ERROR: need Python >= 3.10 on PATH (scripts use int.bit_count)."; exit 1; }
echo "Using: $PY ($("$PY" -V 2>&1))"

echo
echo "== [1/2] Independent n=3 census reproduction (stdlib only) =="
"$PY" "$here/independent_verification/ThreePortCensus-IndependentVerifier.py"

echo
echo "== [2/2] Certificate verification (stdlib only) =="
( cd "$here/certificate_supplement_20260610" && "$PY" verify_certificates.py )

echo
echo "Quick check complete — both steps reproduced with zero third-party dependencies."
