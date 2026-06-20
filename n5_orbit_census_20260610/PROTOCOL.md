# Optimized B5 Orbit Census Protocol

Date: 2026-06-10

## Goal

Determine whether a full `n=5` orbit-representative census is practical, and
provide a correct generator path if it is.

## Correctness Criteria

- Burnside count for `n=4` must be `402`.
- Full generated representative count for `n=4` must be `402`.
- Burnside count for `n=5` must be `1,228,158`.
- The generator must use the full signed coordinate group `B_n`, not only
  coordinate permutations.
- The Rust helper and the TypeScript reference must agree on the `n=4` full
  count and the `n=5` Burnside count before any `n=5` full run is treated as
  production evidence.

## Performance Criteria

- Measure transform throughput for `B_5`.
- Measure prefix-scan throughput with the real `512 MiB` bitset.
- Estimate full `n=5` runtime before launching `full 5`.

## Interpretation

If `full 5` is projected under a few hours on this machine, run it locally and
then feed representatives to the exact polytope evaluator in batches.

If it is projected at days, either implement a lower-level helper or use a
multi-worker design with duplicate-safe representative de-duplication.

## Executables

- `orbit_census.ts`: readable TypeScript/Bun reference implementation.
- `rust-helper`: dependency-free Rust implementation for production scans.

## Completed Results

- Full Rust `B_5` orbit generation completed in `54.516762708` seconds.
- Generated `1,228,158` representatives and marked all `4,294,967,296`
  region masks.
- Exact representative evaluation completed in `183.5` seconds with `8`
  workers and `1000` representatives per batch.
- Maximum denominator at `n=5` is `5`.
- Denominator `4+` appears in `36,583` region orbits.
