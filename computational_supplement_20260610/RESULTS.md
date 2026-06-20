# Review and computational resolution of the open questions

**Paper:** *Asymmetric Elimination in Signed Admission Geometry* (K. Ravindran, draft 2026-06-10)
**Method:** exact rational arithmetic throughout (pycddlib/cddlib over GMP fractions). The run log is
the authoritative transcript for the computed S1--S6 checks; this file records the corresponding
review conclusions and finite-dimensional classification notes.
**Reproduction:** `python3 analysis.py` using `sag.py`.

---

## 1. Referee verdict

The mathematics is sound. Every theorem and proposition was checked line by line; every numerical
claim reproduces exactly. No howlers. The items below are presentational gaps, not errors.

### 1.1 Verification table

| Claim in paper | Recomputed | Status |
|---|---|---|
| n=3: 240/256 signed-ideal | 240/256 | ✓ |
| n=3: 22 B₃-orbits | 22 | ✓ |
| n=4: 39 416/65 536 signed-ideal | 39 416 | ✓ |
| n=4: 402 B₄-orbits | 402 | ✓ |
| Orbit denominator spectra {1}:247, {1,2}:137, {1,2,3}:11, {1,3}:7 | 246+1, 137, 11, 7 | ✓ (see §1.2 item 5) |
| 262 144 existential eliminations, canonical identity failures | 0 | ✓ |
| Existential hiding preserves signed-ideality (4→3) | 0 violations | ✓ |
| Universal violations: 5 632 (R,h) pairs | 5 632 | ✓ |
| Universal violations: 4 864 regions | 4 864 | ✓ |
| Universal violations: 27 B₄-orbits | 27 (pairs) and 27 (regions) | ✓ (ambiguous wording; both readings true) |
| All violating hidden ports canonically mixed | true | ✓ |
| All 4→3 violation vertices half-integral | every fractional vertex is literally (½,½,½) | ✓ (stronger than stated) |
| Active binary subsystem contains odd signed triangle | true in all 5 632 cases | ✓ |
| Thm 5 example: Can(R_U) = the three listed intervals; visible Can = three edges | both verified | ✓ |
| Odd-cycle seam instances m=3,5 | Can lists, parent integrality, visible all-half vertex | ✓ |
| Complement example (n=3): R non-ideal, complement ideal | verified | ✓ |
| LaTeX source in current tree | neutral, Springer, and Elsevier PDFs rebuilt; see `STATUS.md` | ✓ |

### 1.2 Suggested edits (ordered by importance)

1. **Prop. 7 (odd-cycle seam lift), one non-sequitur sentence.** "Each Jᵢ projects to … *Hence* the
   downstairs canonical rejected intervals are exactly the edge intervals." Projecting canonical
   intervals does not in general yield the downstairs canonical intervals in the universal
   direction — that asymmetry is the paper's own point. The conclusion is true here because
   ∃_h R_m is the up-closure of the edge antichain, so its maximal contained intervals are exactly
   the edge intervals. Add the one-line argument.
2. **Thm 5, two asserted computations.** That Can(R_U) is exactly the three listed intervals, and
   that Can(∃_h R) is exactly the three visible edges, should be backed by a short direct check.
   The current manuscript includes that direct check, and `analysis.py` verifies the same finite
   interval lists over the 16/8 states.
3. **Undefined terms used in statements.** *h-up-closed / h-down-closed* (used in Prop. 8's
   statement), *signed coordinate group* / the B_n action (used for all orbit counts — also note it
   preserves Can and integrality, which is what licenses orbit-level reporting), *denominator
   spectrum*, *active binary subsystem*, and the *sign convention*: the cleanest version consistent
   with all the paper's uses is σ(edge) = −(product of the two ±1 coefficients in ≥-form), i.e. an
   edge is negative iff its two literals have equal polarity; then "signed product −1" ⟺ the cycle's
   defining determinant has |det| = 2, uniformly in cycle length.
4. **"27 B₄-orbits".** Ambiguous between orbits of violating (region, port) pairs and orbits of
   violating regions; both equal 27, but say which is meant.
5. **Denominator table wording.** "{1}: 247" is 246 orbits with spectrum {1} plus the orbit of
   R = 2^U, whose polytope is empty (no vertices, hence no denominators). Defensible under the
   empty-is-integral convention; one clause fixes it.
6. **Remark's two-clause example** (y₁∨y₂ together with ¬y₁∨y₂) is not a canonical system — its
   prime implicate is the unit y₂. Fine for the point being made; worth a parenthetical.
7. **Worth one line each:** the integer points of P_Can(R) are exactly the admitted family A (makes
   "signed-ideal ⟺ P = conv(A)" transparent and explains why 1 ∈ spectrum whenever A ≠ ∅); and the
   face identity inside Prop. 8's corollary holds without the monotone hypothesis (see §2, Lemma F)
   — extracting it as a stand-alone lemma strengthens the section at zero cost.
8. **Bibliography metadata.** The current tree includes the bibliography file and the readiness
   pass records citation-key coverage; bibliographic metadata remains a normal submission
   proofreading item rather than a computational issue.

---

## 2. Q1 — Mixed-port universal safety: solved at one hidden coordinate over n=4

**Lemma F (general face identity).** For any region R and hidden coordinate h,
P_Can(R^i) equals the x_h = i face of P_Can(R), for both i — *without* the paper's monotone
hypothesis. The paper's own proof of the corollary to Prop. 8 works verbatim. Verified exhaustively:
0 failures over all 262 144 (R, h, face) triples at n=4. Consequence: integral upstairs ⟹ both face
systems signed-ideal, so universal hiding is the canonicalized union of two signed-ideal systems.

**Theorem (n=3 visible classification).** A 3-coordinate canonical system is non-signed-ideal iff
its canonical 2-clauses contain an odd (unbalanced) signed triangle; the unique fractional vertex is
then (½,½,½). Stronger: over all 256 systems, (½,½,½) is the *only* fractional vertex that occurs at
n=3 at all. (Sufficiency in three lines: the triangle is tight at the all-half point; Blake closure
forbids a unit clause coexisting with any canonical clause mentioning its variable, so every
canonical clause has length ≥ 2 and all-half is feasible; the triangle's |det| = 2 pins rank 3.
Necessity verified exhaustively: 0/256 mismatches.) Non-integral orbits: reps 23 = {∅,a,b,c}
(all-positive covering triangle) and 107 = {∅,a,ab,ac,bc} (mixed-sign triangle b+c≥1, c≥a, b≥a).

**Exact 4→3 classification.** For integral upstairs and canonically mixed h: universal hiding
destroys signed-ideality **iff the binary prime implicates of A⁰ ∧ A¹ contain an odd signed
triangle**. Verified with 0 mismatches over all 124 152 integral-mixed (R,h) pairs:
118 520 safe (436 pair-orbits) vs 5 632 violating (27 pair-orbits). Mixedness is necessary but far
from sufficient — 95.5 % of mixed ports are safe.

**Seam anatomy.** Tagging each obstruction-triangle edge by which face certifies it ('0', '1',
'01' = both, '' = joint-only, an implicate of the conjunction valid for neither face alone), the
5 632 violations realize exactly six profiles:

| profile (sorted edge tags) | violating pairs |
|---|---|
| ('', '1', '1') | 1 536 |
| ('', '0', '0') | 1 536 |
| ('', '', '0') | 768 |
| ('', '', '1') | 768 |
| ('0', '01', '1') | 768 |
| ('', '', '') | 256 |

No triangle is ever certified by a single face (consistent with Lemma F + face integrality), but the
naive "straddle" picture is wrong: in 256 violating pairs *all three* edges are joint-only
implicates.

**5→4 outlook.** By Q4 (§5), every non-integral n=4 system — all 155 orbits, including both
denominator-3 mechanisms — is the universal shadow of an integral 5-coordinate system. Therefore
any future safe/violating classification at 5→4 must already distinguish all four obstruction
cores of §3. No random 5→4 sweep is part of the logged reproduction run.

---

## 3. Q2 — Denominator-3 minimal active subsystems: solved at n=4

18 orbits carry denominator-3 vertices (11 with spectrum {1,2,3} + 7 with {1,3}, matching the
paper); 19 such vertices among orbit representatives, all with coordinates in {⅓, ⅔}⁴.

**Classification.** Up to the signed coordinate group there are exactly **two** inclusion-minimal
active subsystems certifying a denominator-3 vertex:

- **T1 (tetrahedral):** all four weight-3 clauses on the four triples — canonically
  x_i + x_j + x_k ≤ 2 for every triple; vertex (⅔,⅔,⅔,⅔); defining determinant det(J−I) = −3.
  Under the global flip this is the boxed covering system of the complete triple clutter on four
  elements.
- **T2 (star–triple):** x₀ + x_j ≤ 1 (j = 1,2,3) together with x₁ + x₂ + x₃ ≤ 2; vertex
  (⅓,⅔,⅔,⅔); determinant +3. Mixed arity — genuinely outside any arity-two mechanism.

**Coverage (the question's second part): yes.** Every denominator-3 orbit contains one of them.
Cross-table: spectrum {1,2,3} → 10 orbits exhibit T1 and 1 exhibits T2; spectrum {1,3} → all 7
exhibit T2.

**Bonus — complete fractional-vertex taxonomy at n=4.** Computing inclusion-minimal active
certificates *restricted to the free coordinates of each fractional vertex* (the restriction is
forced: a tight clause with a bound literal contributing 1 can have no free literal, so restricted
certificates are honest clause systems) yields exactly six mechanisms over all 65 536 systems:

| mechanism (canonical form) | certificates | denominator |
|---|---|---|
| UC3 — odd triangle | 249 | 2 |
| UC3 + pendant edge, sign variant a | 64 | 2 |
| UC3 + pendant edge, sign variant b | 6 | 2 |
| UC4 — odd 4-cycle (one mixed edge; all-negative C4 is balanced) | 15 | 2 |
| T1 | 11 | 3 |
| T2 | 8 | 3 |

Cores: {UC3, UC4} for denominator 2 (pendant edges only transmit tightness to a fourth free
coordinate), {T1, T2} for denominator 3. The restriction step is essential: the same predicate read
off the *raw* canonical clauses has zero false positives but misses 22 000 non-integral regions
(e.g. {∅,a,b,c} embedded at n=4 has only 3-clauses; its triangle appears after fixing d = 0).

---

## 4. Q3 — Complement-stable classes: hereditary regions, and the reason is Lehman

Stability counts (stable ⟺ R and 2^U∖R agree on signed-ideality): n=3: 240/256;
n=4: 47 888/65 536 (30 592 both-integral, 17 296 both-non, 17 648 unstable). Orbit pairing under the
complement involution at n=4: 166 both-integral non-self-paired, 57+57 unstable mirror pairs,
80 both-non, 24 self-paired integral, 18 self-paired non-integral (total 402 ✓).

**Theorem (hereditary stability = blocker duality).** Every down-closed (dually, up-closed) region
is complement-stable, and the equivalence *is* Lehman's theorem. For down-closed R:
Can(R) = {[∅,Q] : Q maximal in R}, the boxed covering system of the clutter B = {U∖Q}. The minimal
elements of 2^U∖R are exactly the minimal transversals of B, i.e. the blocker b(B); hence
Can(2^U∖R) is, after the global flip x ↦ 1−x, the boxed covering system of b(B). Boxing preserves
ideality in both directions for blocking-type systems (every vertex of the unbounded covering
polyhedron already lies in [0,1]^U; the x_i = 1 faces are covering systems of contractions, and
minors of ideal clutters are ideal). So "P_Can(R) integral ⟺ P_Can(2^U∖R) integral" for hereditary
R is precisely "B ideal ⟺ b(B) ideal".

Verified exhaustively: all 20 hereditary regions at n=3 and all 168 at n=4 (Dedekind numbers
confirm the class sizes) are stable; the blocker dictionary checks on examples (down-set generated
by {a,b},{a,c}: complement bottoms {d},{b,c} = blocker of {{c,d},{b,d}} ✓).

**Consequence for the paper's framing.** "The naive complement–Lehman analogue fails" should be
sharpened: restricted to hereditary regions, the signed complement literally implements the blocker
and the analogue *holds*; the failure (the paper's counterexample {∅,ab,ac,bc,abc} is not
down-closed) is a genuinely signed phenomenon.

**Smaller stable classes.** Single-interval regions (81 at n=4) are stable with a three-line proof:
Can(2^U∖[P,Q]) = {[∅,U∖i] : i∈P} ∪ {[{j},U] : j∉Q}, whose clauses pin the face x_P = 1, x_∉Q = 0.
Every region with |Can(R)| ≤ 2 (81 + 1 324 at n=4) is both-integral — verified, not proved.

---

## 5. Q4 — One-hidden lift reachability: every non-integral system is reachable through n=4

Parents on n+1 coordinates with ∃_h(parent) = R are parametrized by disjoint (X₀, X₁) ⊆ R with
faces R^i = R∖X_i; the trivial lift (X₀ = X₁ = ∅) provably never works (the h-face reproduces the
fractional vertex, Lemma F).

- **Visible n=3, exhaustive.** All 16 non-integral regions admit signed-ideal parents; the minimal
  seam |X₀|+|X₁| is always 2. Rep 23 has 44 integral parents of 3⁴ = 81; rep 107 has 132 of 243.
- **Visible n=4, all 155 non-integral orbits reachable.** Search = seam-size BFS with
  faces-must-be-integral pruning (sound by Lemma F) + exact cdd certification at n=5. Minimal seam
  distribution: 2 → 105 orbits, 3 → 22, 4 → 26, 5 → 1 (rep 6121, witness X₀={3,8}, X₁={0,5,9}),
  6 → 1 (rep 27606, witness X₀={6,9}, X₁={1,2,4,8}); the two largest values are true minima
  (unrestricted split search). The tetrahedral T1 region {S : |S| ≥ 3} (orbit rep 279) is repaired
  with seam 3 (X₀=[0], X₁=[1,2]); its parent was certified end-to-end: 6 canonical intervals,
  integral, ∃_h(parent) = R exactly.

**Answer to "determine when", through n=4: always.** Conjecture: every non-integral signed interval
system on n coordinates is the admitted-universal projection of a signed-ideal system on n+1
coordinates — one hidden bit of context suffices to explain away any of these fractional vertices.
Duality with Q1: reachability of *all* non-integral n=4 systems means the 5→4 violating shadows
exhaust all four obstruction cores (UC3, UC4, T1, T2), so the 5→4 safety boundary is at least as
rich as the full n=4 non-integrality classification of §3.

---

## 6. What remains open

Q1 beyond one hidden coordinate and beyond 4→3 in closed form (the 5→4 boundary now has a complete
target taxonomy via §3); Q2 beyond n=4 (do new denominator-3 cores appear at n=5, and when does
denominator 4+ first occur?); Q3's full characterization of stable regions (hereditary + the small
classes cover 168 + 1 405 of the 47 888 stable regions at n=4 — the bulk is unexplained);
Q4 beyond n=4 (the conjecture is exact-search-falsifiable at n=5 visible with the same pipeline).

## 7. Files

- `sag.py` — exact-arithmetic library: intervals, Can(R), escape H-representations, cdd vertex
  enumeration over fractions, hyperoctahedral group action, hiding/lift operations.
- `analysis.py` — single-pass reproduction of the logged S1–S6 checks and core counts.
- This document.
