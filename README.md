# Signed Admission Geometry — Computational Census (reviewer-runnable supplement)

Exact-arithmetic computational supplement for the finite census results in:

- **Book:** *The Landscape Is the Meaning*, Part V (Chapters 11–12), "Counting the Desert."
- **Paper:** *Variable Elimination for Prime-Implicate 0-1 Relaxations of Boolean Constraints* (K. Ravindran), submitted to *Discrete Applied Mathematics*.

Every count below is produced by **exact rational arithmetic** (no floating point) and is reproducible by re-running the scripts here — by any reader, on any machine, with no dependence on a particular AI model. An **independent third-party reimplementation** (an adversarial external review, 20 June 2026) reproduced the entire *n* = 3 census from scratch with **zero third-party dependencies**; its script and recorded output are in [`independent_verification/`](independent_verification/).

## Headline results

| Coords | Object | Result | Verified by |
|---|---|---|---|
| **n = 3** (B₃) | signed-ideal families | **240 / 256** | `analysis.py` + independent verifier |
| | non-ideal families | 16 (two B₃-orbits of 8) | both |
| | orbits under signed group B₃ | **22** | both |
| | only fractional vertex that occurs | **(½, ½, ½)** | both |
| **n = 4** (B₄) | signed-ideal families | **39 416 / 65 536** | `analysis.py` |
| | orbits under B₄ | **402** (TypeScript + Rust agree) | `analysis.py`, `orbit_census.ts`, rust-helper |
| | maximum vertex denominator | **3** | `analysis.py` |
| | existential hiding 4 → 3, ideality violations | **0** | `analysis.py` |
| | universal hiding 4 → 3 violations | 5 632 (R,h) pairs / 4 864 regions / 27 orbits | `analysis.py` |
| | denominator-3 minimal cores | exactly two: **T1** (tetrahedral), **T2** (star–triple) | `analysis.py` |
| **n = 5** (B₅) | regions | 2³² = 4 294 967 296 (all masks marked) | rust-helper |
| | orbits under B₅ (Burnside) | **1 228 158** (TypeScript + Rust agree) | `orbit_census.ts`, rust-helper |
| | maximum vertex denominator | **5** | `eval_b5_reps.py` |
| | denominator-5 representatives | 5 191 | `eval_b5_reps.py` |
| | compact denominator-5 certificate | rep 428, vertex (⅕,⅕,⅕,⅖,⅖), det = −5 | `b5_orbit_census_report` |

Full row-by-row claim/recompute tables are in `computational_supplement_20260610/RESULTS.md` (n = 3, 4) and `n5_orbit_census_20260610/b5_orbit_census_report_20260610.md` (n = 5).

## Quick start (zero dependencies, ~seconds)

Reproduces the full *n* = 3 census with the Python standard library only (**Python 3.10+**) — no install, no network:

```sh
python3 independent_verification/ThreePortCensus-IndependentVerifier.py
```

Expected final line:

```
PASS: all manuscript n=3 census targets reproduced exactly.
```

Or run the bundled check (n = 3 reproduction, then certificates if `pycddlib` is present):

```sh
./run_quick_check.sh
```

## Repository layout

| Path | What it is | Languages / deps |
|---|---|---|
| `independent_verification/` | Third-party stdlib reproduction of the *n* = 3 census + recorded output | Python 3.10+ stdlib (no deps) |
| `computational_supplement_20260610/` | `sag.py` (exact-arithmetic library), `analysis.py` (n = 3/4 census + hiding checks), `RESULTS.md`, run log | Python 3 + **pycddlib** |
| `certificate_supplement_20260610/` | `certificates.json` + `verify_certificates.py` + `MANIFEST.sha256` | Python 3.10+ + pycddlib |
| `n5_orbit_census_20260610/` | `orbit_census.ts` (reference) + `rust-helper/` (fast Burnside generation) + `eval_b5_reps.py` (exact evaluation) + reports | TypeScript (Bun), Rust (cargo), Python 3 |
| `n5_probe_20260610/` | targeted *n* = 5 probes + recorded results | Python 3 |

## Full reproduction

**Dependencies.** `analysis.py`, `verify_certificates.py` (via `sag.py`), and the *n* = 5 evaluation (`eval_b5_reps.py`) use exact polyhedral vertex enumeration via **pycddlib** (cddlib over GMP). The *n* = 5 orbit *generation* uses **Bun** (TypeScript) and **cargo** (Rust). The only fully self-contained check is the independent *n* = 3 verifier in `independent_verification/` — **pure standard library, Python 3.10+, no install**.

```sh
python3 -m pip install -r requirements.txt      # pycddlib
# Bun:   https://bun.sh        Rust/cargo: https://rustup.rs
```

The original runs used a `micromamba` environment to provide `pycddlib`; any environment supplying the package works equally.

**n = 3 / n = 4 census, hiding, denominators** (seconds, exact) — reproduces every row of `RESULTS.md §1.1`:

```sh
cd computational_supplement_20260610 && python3 analysis.py
```

**Fast certificate check** (verifies recorded certificates without recomputing the census):

```sh
cd certificate_supplement_20260610 && python3 verify_certificates.py
```

**n = 5 orbit census** (~1 min generation + ~3 min exact evaluation):

```sh
cd n5_orbit_census_20260610/rust-helper && cargo run --release -- full 5 ../reps_b5_rust.bin
cd .. && python3 eval_b5_reps.py reps_b5_rust.bin --workers 8 --batch-size 1000
```

Expected: `1 228 158` representatives; denominator spectrum topping out at denominator 5 (`b5_orbit_census_report_20260610.md`).

## Integrity

`MANIFEST.sha256` carries SHA-256 for every shipped file:

```sh
shasum -a 256 -c MANIFEST.sha256
```

The two large generated binaries (`reps_b5_rust.bin`, `b5_rep_eval_batches.jsonl`) are present for immediate runnability and are git-ignored; for publication, host them as a release/Zenodo asset and rely on the checksums plus the `cargo`/`eval` regeneration path above. This package descends from the author's vetted supplement (`asymmetric-elimination-computational-supplement.zip`, SHA-256 `e5d2c9ee…600a`).

## License & citation

Code and certificates are released under MIT (see `LICENSE`; change if you prefer). Please cite the book and the *Discrete Applied Mathematics* submission — see `CITATION.cff`.
