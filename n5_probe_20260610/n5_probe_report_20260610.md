# n=5 Probe Report

Date: 2026-06-10

## Executive Result

The bounded exact `n=5` probe found a genuine determinant-4 mechanism.
Consequently denominator-4 vertices occur by dimension `5`. Since the complete
`n=4` census has no denominator above `3`, this answers the "when does
denominator `4+` first occur?" question up to the first possible next
dimension: it occurs at `n=5`.

This is not a full `n=5` census. It is an exact certificate plus bounded
falsification evidence.

## Exact D4 Certificate

On coordinates `0,1,2,3,4`, let `R` be the union of the following five Boolean
intervals:

```text
+0   / -2,4
+1,3 / -4
+1,3 / -2
+0,1 / -2
+0,3 / --
```

The probe verifies that these five intervals are exactly `Can(R)`. The
canonical escape inequalities are:

```text
-x0 + x2 + x4 >= 0
1 - x1 - x3 + x4 >= 0
1 - x1 + x2 - x3 >= 0
1 - x0 - x1 + x2 >= 0
1 - x0 - x3 >= 0
```

They are all tight at

```text
(1/2, 3/4, 1/4, 1/2, 1/4).
```

The active coefficient determinant is `-4`, so this is a denominator-4 vertex.
The full vertex denominator spectrum of the canonical repair relaxation is:

```text
{1,2,4}
```

The region mask in the probe encoding is:

```text
2919820810
```

## Bounded Probe Results

Run parameters:

```text
seed: 20260610
workers: 8
random n=5 interval-region samples: 2500
active-row determinant samples: 30000
random n=5 parent samples for 5->4 shadows: 3000
Q4 seam-2 candidate limit: 12; candidates actually tested after the
small-state filter: 9
```

Observed results:

- Cylindrical lifts of all `155` non-integral `n=4` orbit representatives
  stayed within the known `n=4` denominator spectra: `{1,2}`, `{1,2,3}`,
  `{1,3}`.
- Random `n=5` interval-region samples found denominator-4 spectra:
  `{1,4}`, `{1,2,4}`, and `{1,2,3,4}`.
- Active-row search found candidate solution denominators above `3`; one
  denominator-4 candidate survived canonicalization and is the D4 certificate
  above.
- Among `3000` sampled `n=5` parents, `2103` were integral. Their `5591`
  mixed ports produced `297` non-integral `5->4` shadows, with spectra only
  in the known `n=4` list: `{1,2}` and `{1,3}`. No sampled `5->4` shadow had
  a denominator outside the complete `n=4` taxonomy.
- The seam-2 Q4 probe found one-hidden integral parents for `7` of `9`
  selected visible `n=5` non-integral examples that passed the small-state
  filter. The two misses had no face-integral seam-2 candidate under this
  narrow test; they are not counterexamples to reachability.

## Manuscript Impact

This should affect the paper, but only narrowly.

Recommended main-text change:

- Add a short `n=5` certificate paragraph after the `n=4` denominator table.
- State explicitly that this is an exact certificate, not a full `n=5` census.
- Update Q2's wording: denominator-4 mechanisms occur at `n=5`; the remaining
  classification problem is to understand higher-determinant active subsystems
  generally.

Do not import the random sample statistics into the main theorem spine.
