#!/usr/bin/env python3
"""Independent exact-rational check of the manuscript's three-port census.

For each admission family A subseteq {0,1}^3, the script:
  1. forms the rejected set R;
  2. computes maximal Boolean intervals [P,Q] contained in R;
  3. builds the canonical clause relaxation;
  4. enumerates all polyhedral vertices over Fraction arithmetic;
  5. tests ideality; and
  6. computes orbits under coordinate permutations and signed complements.

No third-party packages are required.
"""
from __future__ import annotations

from fractions import Fraction
from itertools import combinations, permutations, product

N = 3
POINTS = tuple(range(1 << N))
FULL = (1 << N) - 1


def subsets(mask: int):
    sub = mask
    while True:
        yield sub
        if sub == 0:
            return
        sub = (sub - 1) & mask


def interval_points(p: int, q: int) -> frozenset[int]:
    assert p & ~q == 0
    free = q & ~p
    return frozenset(p | s for s in subsets(free))


ALL_INTERVALS = tuple(
    (p, q, interval_points(p, q))
    for p in POINTS
    for q in POINTS
    if p & ~q == 0
)


def maximal_rejected_intervals(admission_mask: int) -> tuple[tuple[int, int], ...]:
    rejected = frozenset(k for k in POINTS if not ((admission_mask >> k) & 1))
    contained = [(p, q) for p, q, pts in ALL_INTERVALS if pts <= rejected]
    maximal = []
    for p, q in contained:
        # [p,q] is contained in [p2,q2] iff p2 subseteq p and q subseteq q2.
        if not any(
            (p2, q2) != (p, q)
            and (p2 & ~p) == 0
            and (q & ~q2) == 0
            for p2, q2 in contained
        ):
            maximal.append((p, q))
    return tuple(sorted(maximal))


def canonical_constraints(admission_mask: int):
    """Return inequalities a.x >= b, including 0 <= x <= 1."""
    constraints: list[tuple[tuple[Fraction, ...], Fraction]] = []
    for i in range(N):
        a = [Fraction(0) for _ in range(N)]
        a[i] = Fraction(1)
        constraints.append((tuple(a), Fraction(0)))       # x_i >= 0
        a = [Fraction(0) for _ in range(N)]
        a[i] = Fraction(-1)
        constraints.append((tuple(a), Fraction(-1)))      # x_i <= 1

    for p, q in maximal_rejected_intervals(admission_mask):
        # sum_{i in p}(1-x_i) + sum_{i notin q} x_i >= 1
        a = []
        for i in range(N):
            bit = 1 << i
            a.append(Fraction(-1 if p & bit else (1 if not (q & bit) else 0)))
        b = Fraction(1 - p.bit_count())
        constraints.append((tuple(a), b))
    return tuple(constraints)


def solve_square(rows):
    """Solve a 3x3 exact linear system; return None if singular."""
    m = [list(a) + [b] for a, b in rows]
    for col in range(N):
        pivot = next((r for r in range(col, N) if m[r][col] != 0), None)
        if pivot is None:
            return None
        m[col], m[pivot] = m[pivot], m[col]
        scale = m[col][col]
        m[col] = [v / scale for v in m[col]]
        for r in range(N):
            if r == col:
                continue
            factor = m[r][col]
            if factor:
                m[r] = [m[r][c] - factor * m[col][c] for c in range(N + 1)]
    return tuple(m[i][-1] for i in range(N))


def dot(a, x):
    return sum((ai * xi for ai, xi in zip(a, x)), Fraction(0))


def vertices(admission_mask: int) -> tuple[tuple[Fraction, ...], ...]:
    constraints = canonical_constraints(admission_mask)
    out = set()
    for idxs in combinations(range(len(constraints)), N):
        x = solve_square([constraints[i] for i in idxs])
        if x is None:
            continue
        if all(dot(a, x) >= b for a, b in constraints):
            out.add(x)
    return tuple(sorted(out))


def is_ideal(admission_mask: int) -> bool:
    return all(all(v.denominator == 1 for v in x) for x in vertices(admission_mask))


PERMS = tuple(permutations(range(N)))
SIGNS = tuple(range(1 << N))


def transform_point(point: int, perm: tuple[int, ...], sign: int) -> int:
    out = 0
    for new_i, old_i in enumerate(perm):
        bit = (point >> old_i) & 1
        bit ^= (sign >> new_i) & 1
        out |= bit << new_i
    return out


def transform_family(mask: int, perm: tuple[int, ...], sign: int) -> int:
    out = 0
    for p in POINTS:
        if (mask >> p) & 1:
            out |= 1 << transform_point(p, perm, sign)
    return out


def orbit(mask: int) -> frozenset[int]:
    return frozenset(transform_family(mask, perm, sign) for perm in PERMS for sign in SIGNS)


def main() -> None:
    ideal = []
    nonideal = []
    fractional_vertices = set()
    for admission_mask in range(1 << len(POINTS)):
        verts = vertices(admission_mask)
        frac = [x for x in verts if any(v.denominator != 1 for v in x)]
        if frac:
            nonideal.append(admission_mask)
            fractional_vertices.update(frac)
        else:
            ideal.append(admission_mask)

    unseen = set(range(1 << len(POINTS)))
    all_orbits = []
    while unseen:
        seed = min(unseen)
        orb = orbit(seed)
        all_orbits.append(orb)
        unseen -= orb

    unseen_nonideal = set(nonideal)
    nonideal_orbits = []
    while unseen_nonideal:
        seed = min(unseen_nonideal)
        orb = orbit(seed) & set(nonideal)
        nonideal_orbits.append(orb)
        unseen_nonideal -= orb

    print(f"ideal families: {len(ideal)}")
    print(f"nonideal families: {len(nonideal)}")
    print(f"signed-shuffle orbits: {len(all_orbits)}")
    print("nonideal orbit sizes:", sorted(len(o) for o in nonideal_orbits))
    print("fractional vertices:", sorted(fractional_vertices))

    assert len(ideal) == 240
    assert len(nonideal) == 16
    assert len(all_orbits) == 22
    assert sorted(len(o) for o in nonideal_orbits) == [8, 8]
    assert fractional_vertices == {(Fraction(1, 2),) * 3}
    print("PASS: all manuscript n=3 census targets reproduced exactly.")


if __name__ == "__main__":
    main()
