# Certificate Supplement

Date: 2026-06-10

This directory contains a compact certificate packet for the finite
computational claims used by the asymmetric-elimination paper. It is meant as a
reviewer-facing fast-check surface, not as a replacement for the full
reproduction scripts.

## Files

- `certificates.json`: claims, hashes, and small exact certificates.
- `verify_certificates.py`: exact verifier for the compact packet.
- `verification_run_20260610.log`: local successful verifier run.
- `MANIFEST.sha256`: hashes for the tracked certificate-packet files.

The verifier reuses `computational_supplement_20260610/sag.py` for canonical
intervals and exact rational vertex enumeration. It is therefore a fast exact
audit layer over the same primitives, not an independent reimplementation of
the geometry library. It checks:

- Required source/log/generated artifact hashes. The full generated `B_5`
  representative and evaluation artifacts must be present for a passing strict
  run.
- Burnside orbit counts for `B_3`, `B_4`, and `B_5`.
- The named finite census counts used in the manuscript: integrality counts,
  existential-hiding zero failures, universal-hiding violation counts,
  mixed-port odd-triangle classification, face-lemma failures,
  complement-stability counts, hereditary stability, and one-hidden
  reachability through `n=4`.
- The full `B_4` orbit-level denominator spectrum.
- The named `4->3` universal counterexample.
- The signed-complement failure example.
- Odd-cycle seam instances for lengths `3` and `5`.
- The determinant-4 and determinant-5 `n=5` vertex certificates.
- Hashes of recorded source/log/generated artifacts when those artifacts are
  present locally.

Run from the repository root:

```sh
ENV_PREFIX="$(micromamba env list | awk '/asym-elim-mamba-20260610/ {print $NF; exit}')"
micromamba run -p "${ENV_PREFIX}" python certificate_supplement_20260610/verify_certificates.py
```

The generated full `B_5` representative/evaluation files are intentionally not
tracked in git, but a strict certificate run requires them to be present and to
match the hashes in `certificates.json`.
