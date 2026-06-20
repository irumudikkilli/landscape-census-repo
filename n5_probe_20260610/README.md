# n=5 Probe

This directory contains a bounded exact falsification probe for the structural
questions left beyond the `n=4` census in the computational supplement.

It is intentionally separate from `computational_supplement_20260610/`, which
contains the stable reproduction packet for the current paper. This probe is
exploratory evidence for whether the paper should be strengthened or whether
the frontier should remain a sequel program.

Run from the repository root:

```sh
cd n5_probe_20260610
ENV_PREFIX="${TMPDIR:-/tmp}/asym-elim-mamba-20260610"
N5_WORKERS=8 micromamba run -p "${ENV_PREFIX}" python n5_probe.py
```

The driver writes `n5_probe_results_20260610.json` and may create local census
caches `data4_probe.pkl`. Generated caches are not tracked.
