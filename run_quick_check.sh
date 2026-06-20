#!/usr/bin/env bash
# Confidence check.
#   [1] Reproduces the full n=3 census (independent third-party verifier) —
#       pure Python 3.10+ standard library, zero third-party dependencies.
#   [2] If pycddlib is available, also verifies the recorded certificates
#       (verify_certificates.py imports sag.py, which needs pycddlib).
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
echo "== [1/2] Independent n=3 census reproduction (stdlib only, zero deps) =="
"$PY" "$here/independent_verification/ThreePortCensus-IndependentVerifier.py"

echo
echo "== [2/2] Certificate verification =="
if "$PY" -c 'import cdd' >/dev/null 2>&1; then
  ( cd "$here/certificate_supplement_20260610" && "$PY" verify_certificates.py )
else
  echo "SKIP: pycddlib not available to $PY (run: python3 -m pip install -r requirements.txt)."
  echo "      Step [1] already reproduced the n=3 census with zero dependencies."
fi

echo
echo "Quick check complete."
