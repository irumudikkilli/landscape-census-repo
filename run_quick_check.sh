#!/usr/bin/env bash
# Zero-dependency confidence check.
#   [1] Reproduces the full n=3 census with the Python standard library only.
#   [2] Verifies recorded certificates if pycddlib is available (else skips).
# No network or install is required for step [1].
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"

echo "== [1/2] Independent n=3 census reproduction (stdlib only) =="
python3 "$here/independent_verification/ThreePortCensus-IndependentVerifier.py"

echo
echo "== [2/2] Certificate verification =="
if python3 -c 'import cdd' >/dev/null 2>&1; then
  ( cd "$here/certificate_supplement_20260610" && python3 verify_certificates.py )
else
  echo "SKIP: pycddlib not installed (run: python3 -m pip install -r requirements.txt)."
  echo "      The n=3 reproduction in step [1] already passed with zero dependencies."
fi

echo
echo "Quick check complete."
