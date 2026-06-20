# Computational Supplement

This directory contains the exact-arithmetic reproduction packet for
`Asymmetric Elimination in Signed Admission Geometry`, draft of 2026-06-10.

## Files

- `sag.py`: exact signed-admission geometry primitives, including canonical
  intervals, escape inequalities, hiding maps, lift maps, and signed-coordinate
  group actions.
- `analysis.py`: one-pass reproduction driver for the finite censuses, hiding
  sweeps, denominator mechanisms, complement-stability checks, and one-hidden
  lift searches.
- `RESULTS.md`: reviewer-style mathematical summary of the run and the finite
  Q1-Q4 resolutions.
- `reproduction_run_20260610.log`: successful local run log from 2026-06-10.

## Source Packet

The supplement files were extracted locally from:

```text
<HOME>/Downloads/files.zip
```

with SHA-256:

```text
40ea333cf80c3fa1a7aa7d8db05b335c90a2a64614c188cef5894fa32ad622c3
```

## Reproduction Environment

The recorded run used:

```text
Python 3.11.15
pycddlib 2.1.7
cddlib 0.94n
gmp 6.3.0
```

One reproducible setup, assuming `micromamba` is on `PATH`, is:

```sh
ENV_PREFIX="${TMPDIR:-/tmp}/asym-elim-mamba-20260610"

micromamba create -y \
  -p "${ENV_PREFIX}" \
  -c conda-forge python=3.11 pip setuptools wheel cython gmp cddlib

CFLAGS="-I${ENV_PREFIX}/include" \
LDFLAGS="-L${ENV_PREFIX}/lib" \
  micromamba run \
  -p "${ENV_PREFIX}" \
  python -m pip install pycddlib==2.1.7
```

Then run:

```sh
cd computational_supplement_20260610
micromamba run -p "${ENV_PREFIX}" python -m py_compile analysis.py sag.py
micromamba run -p "${ENV_PREFIX}" python analysis.py
```

The driver creates `data3.pkl` and `data4.pkl` census caches in this directory.
They are generated artifacts and are intentionally not tracked.

## Recorded Source And Log Hashes

```text
b7191b97c0ade227ea35f5dc3f736ca3603291f2265da51b22669f7a9cde0aa9  RESULTS.md
350c04a521c3ccaa1ff8b6476027163cd33e395a93306236d8a3e87bea916f8f  analysis.py
4f707aa60506db283cfa106add40afbd6a6473f56a41a8f038192d72398e98ca  sag.py
e952bee130b104a29be965fc03206fbbbc8459bca90d05ade7939752bfaf229c  reproduction_run_20260610.log
```
