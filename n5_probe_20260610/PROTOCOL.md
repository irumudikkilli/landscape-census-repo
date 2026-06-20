# n=5 Probe Protocol

Date: 2026-06-10

## Research Question

Can a bounded exact probe at dimension `n=5` find evidence that changes how the
paper should frame its four structural classification directions?

Full `n=5` census is not attempted: it would require `2^32` regions. This probe
is a falsification-oriented search over structured and randomized exact
families.

## Pre-Registered Outcomes

Primary outcomes:

- Find any `n=5` canonical repair relaxation with denominator `4` or larger.
- Find any `n=5` fractional active mechanism not reducible to the known
  `n=4` restricted cores under the tested families.
- Find any `5->4` admitted-universal shadow from an integral parent whose
  visible denominator spectrum falls outside the complete `n=4` taxonomy.
- Find a small-seam counterexample to one-hidden reachability for selected
  visible `n=5` non-integral systems.

Secondary outcomes:

- Confirm that embedded `n=4` obstruction representatives remain explained
  when cylindrically lifted to `n=5`.
- Estimate, without statistical overclaim, how often the tested integral
  `n=5` parents create non-integral `4`-coordinate shadows.

## Stopping Rules

The default run stops after:

- all `n=4` orbit representatives have been cylindrically lifted and checked;
- the configured random `n=5` interval-region sample count is exhausted;
- the configured random active-row determinant sample count is exhausted;
- the configured random parent sample count for `5->4` shadows is exhausted;
- the configured number of small visible `n=5` Q4 candidates has been tested.

Any denominator `4+` example, new visible `5->4` spectrum outside `{1,2,3}`,
or small-seam reachability counterexample is logged as a hard hit.

## Interpretation Rules

- A hit is actionable and should be inspected mathematically before changing the
  manuscript.
- No hit is evidence only for the tested families. It does not prove the
  higher-dimensional conjectures.
- Main-paper changes should stay conservative unless the probe produces a clean
  theorem or a small explicit counterexample.
