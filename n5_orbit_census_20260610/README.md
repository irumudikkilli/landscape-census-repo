# n=5 Orbit Census Tool

This directory contains a TypeScript/Bun prototype for optimized orbit
enumeration under the signed coordinate group `B_n`.

It also contains a dependency-free Rust helper in `rust-helper/` for production
runs. The Rust helper implements the same algorithm as the TypeScript reference
and is the preferred executable for full `n=5` scans.

The key optimization is a byte-table representation of each signed state
permutation. For `n=5`, the tool uses:

- `512 MiB` visited bitset for all `2^32` regions;
- about `16 MiB` of transform tables for the `3840` signed coordinate maps;
- one `uint32` representative per discovered orbit.

Run examples from this directory:

```sh
bun orbit_census.ts burnside 5
bun orbit_census.ts full 4
bun orbit_census.ts bench-transform 5 20000
bun orbit_census.ts scan-prefix 5 1000000
```

The `full 5` mode is implemented but should be launched only after the
benchmarks are reviewed:

```sh
bun orbit_census.ts full 5 reps_b5.bin
```

`reps_b5.bin` is a binary little-endian `uint32` list of orbit representatives.
Generated binary/checkpoint files are not tracked.

Rust helper examples:

```sh
cd rust-helper
cargo run --release -- burnside 5
cargo run --release -- full 4
cargo run --release -- bench-transform 5 20000
cargo run --release -- scan-prefix 5 10000000
cargo run --release -- full 5 ../reps_b5_rust.bin
```

Exact evaluation of the representatives is resumable:

```sh
cd n5_orbit_census_20260610
ENV_PREFIX="$(micromamba env list | awk '/asym-elim-mamba-20260610/ {print $NF; exit}')"
micromamba run -p "${ENV_PREFIX}" python eval_b5_reps.py reps_b5_rust.bin \
  --workers 8 --batch-size 1000
```

The evaluator writes append-only batch summaries to
`b5_rep_eval_batches.jsonl` and a merged summary to
`b5_rep_eval_summary.json`. Re-running the same command skips completed batch
ranges for the same representative-file SHA-256.
