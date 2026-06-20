# B5 Orbit Census Report

Date: 2026-06-10

## Scope

This packet implements and records a complete orbit-representative census for
all `2^32` signed regions on five coordinates under the signed coordinate group
`B_5`, followed by exact rational evaluation of every representative.

The representative census is used to avoid evaluating all `4,294,967,296`
regions directly. Burnside gives `1,228,158` region orbits, and the Rust helper
generated exactly that many representatives while marking every region mask.

## Correctness Gates

- TypeScript reference Burnside count for `n=4`: `402`.
- TypeScript reference Burnside count for `n=5`: `1,228,158`.
- TypeScript reference full generation for `n=4`: `402` representatives.
- Rust helper Burnside count for `n=4`: `402`.
- Rust helper Burnside count for `n=5`: `1,228,158`.
- Rust helper full generation for `n=4`: `402` representatives.
- Rust helper full generation for `n=5`: `1,228,158` representatives and
  `4,294,967,296` marked masks.

## Orbit Generation

Command:

```sh
cd n5_orbit_census_20260610/rust-helper
cargo run --release -- full 5 ../reps_b5_rust.bin
```

Observed result:

```text
elapsed: 54.516762708 seconds
group order: 3840
visited bitset: 536870912 bytes
transform table: 15728640 bytes
representatives: 1228158
marked masks: 4294967296
transforms: 4716126720
representative file bytes: 4912632
```

Representative file SHA-256:

```text
feda61b119ec53bd697897387f3df9806643a43ac136308cf8a9ddab71629ce4
```

The representative binary is generated and is not tracked in git.

## Exact Representative Evaluation

Command:

```sh
cd n5_orbit_census_20260610
ENV_PREFIX="$(micromamba env list | awk '/asym-elim-mamba-20260610/ {print $NF; exit}')"
micromamba run -p "${ENV_PREFIX}" python eval_b5_reps.py reps_b5_rust.bin \
  --workers 8 --batch-size 1000
```

Observed result:

```text
elapsed: 183.5 seconds
batches: 1229
completed representatives: 1228158
complete: true
```

Generated artifact hashes:

```text
d9f539488d118028d0f2468858a0fc3ddc5a88bfd1c41639a289187864457458  b5_rep_eval_batches.jsonl
589b9b4729dedf93aca7c415e6aac356fd77611e0d0fa3847bf0d98f0f3a7af9  b5_rep_eval_summary.json
```

These generated files are reproducible outputs and are not tracked in git.

## Denominator Spectrum by Orbit

```text
()                1
(1,)              127703
(1, 2)            786263
(1, 2, 3)         258477
(1, 2, 3, 4)      26501
(1, 2, 3, 4, 5)  30
(1, 2, 3, 5)      4542
(1, 2, 4)         4830
(1, 2, 5)         619
(1, 3)            19131
(1, 3, 4)         1
(1, 4)            60
```

Consequences:

- Maximum denominator at `n=5` is `5`.
- Integral or empty representatives: `127704`.
- Non-integral representatives: `1100454`.
- Representatives with denominator at least `4`: `36583`.
- Representatives with denominator `5`: `5191`.

## Small Denominator-5 Certificate

Representative index: `428`

Region mask: `65919`

Canonical interval count: `5`

Canonical intervals on `U_5={a,b,c,d,e}`:

```text
[empty,{a,b}]
[empty,{a,c}]
[empty,{b,c}]
[empty,{d}]
[empty,{e}]
```

High-denominator vertex:

```text
(1/5, 1/5, 1/5, 2/5, 2/5)
```

Active coefficient matrix:

```text
0 0 1 1 1
0 1 0 1 1
1 0 0 1 1
1 1 1 0 1
1 1 1 1 0
```

Determinant:

```text
-5
```

This gives a compact exact certificate that denominator `5` occurs already at
`n=5`.
