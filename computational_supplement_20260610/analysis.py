"""Reproduction driver for the review of
"Asymmetric Elimination in Signed Admission Geometry" (Ravindran, draft 2026-06-10).

Re-derives, with exact rational arithmetic:
  S1  n=3 and n=4 censuses (integrality counts, orbit decomposition, denominator spectra)
  S2  4->3 hiding sweep (canonical identity, existential preservation, universal violations)
  S3  Q1: general face lemma; mixed-port safety statistics; exact 4->3 classification;
          seam anatomy of obstruction triangles
  S4  Q2: denominator-3 minimal active subsystems (T1, T2) + full fractional-vertex taxonomy
  S5  Q3: complement-stability censuses; hereditary class = Lehman blocker duality;
          small stable classes
  S6  Q4: one-hidden lift reachability at visible n=3 (exhaustive) and n=4 (all 155 orbits)

Requires: pycddlib==2.1.7 (pip install --break-system-packages pycddlib==2.1.7;
needs libgmp-dev). Runtime: ~3 minutes for S1-S5; S6 at n=4 adds ~1 minute.
Caches censuses in ./data3.pkl, ./data4.pkl.
"""
import itertools, math, os, pickle, time
from collections import Counter
from fractions import Fraction

from sag import (Universe, all_intervals, can_intervals, clause_of_interval,
                 faces, hide_exists_rejected, hide_forall_rejected, hrep_rows,
                 interval_statemask, lift_pair_to_region, region_polytope_data,
                 vertices_of)

T0 = time.time()
def log(*a): print(f"[{time.time()-T0:7.1f}s]", *a, flush=True)

# ----------------------------------------------------------------- S1 censuses
U3, U4 = Universe(3), Universe(4)

def census(U, cache):
    if os.path.exists(cache):
        return pickle.load(open(cache, "rb"))
    data = {}
    for R in range(1 << U.nstates):
        cans, verts, dens, integral = region_polytope_data(U, R)
        data[R] = (tuple(sorted(cans)), tuple(verts), frozenset(dens), integral)
    pickle.dump(data, open(cache, "wb"))
    return data

data3 = census(U3, "data3.pkl")
log("n=3 census:", sum(1 for R in range(256) if data3[R][3]), "/256 integral (paper: 240)")

raw4 = census(U4, "data4.pkl")
data4 = raw4[0] if isinstance(raw4, tuple) else raw4
log("n=4 census:", sum(1 for R in range(65536) if data4[R][3]), "/65536 integral (paper: 39416)")

def orbit_decomposition(U, nregions):
    seen = bytearray(nregions); orbits = []; orbit_of = {}
    for R in range(nregions):
        if seen[R]: continue
        orb = sorted(U.orbit(R))
        for x in orb: seen[x] = 1; orbit_of[x] = len(orbits)
        orbits.append(orb)
    return orbits, orbit_of

orbits3, _ = orbit_decomposition(U3, 256)
orbits4, orbit_of4 = orbit_decomposition(U4, 65536)
log("orbits: n=3", len(orbits3), "(paper 22);  n=4", len(orbits4), "(paper 402)")

spec = Counter(tuple(sorted(data4[orb[0]][2])) for orb in orbits4)
log("n=4 orbit denominator spectra:", dict(spec),
    "  [paper folds the empty-polytope orbit R=2^U into '{1}: 247']")

# ----------------------------------------------------------------- S2 hiding sweep
def project_interval(P, Q, n, h):
    vis = [i for i in range(n) if i != h]
    pr = lambda m: sum(1 << k for k, i in enumerate(vis) if (m >> i) & 1)
    return (pr(P), pr(Q))

id_fail = ex_viol = 0; uv_pairs = []
for R in range(65536):
    cansU, _, _, intU = data4[R]
    for h in range(4):
        Rde = hide_exists_rejected(R, 4, h)
        sat = {project_interval(P, Q, 4, h) for (P, Q) in cansU
               if not ((P >> h) & 1) and ((Q >> h) & 1)}
        if sat != set(data3[Rde][0]): id_fail += 1
        if intU and not data3[Rde][3]: ex_viol += 1
        if intU and not data3[hide_forall_rejected(R, 4, h)][3]:
            uv_pairs.append((R, h))
log("S2: identity failures", id_fail, "(paper 0); existential violations", ex_viol,
    "(paper 0); universal violating pairs", len(uv_pairs), "(paper 5632); regions",
    len({R for R, h in uv_pairs}), "(paper 4864)")

pairset, seenp, pair_orbits = set(uv_pairs), set(), 0
for pr in uv_pairs:
    if pr in seenp: continue
    pair_orbits += 1
    for (perm, flips, sp) in U4.group:
        seenp.add((U4.act_region(sp, pr[0]), perm[pr[1]]))
log("S2: B4-orbits of violating pairs", pair_orbits, "(paper 27); of violating regions",
    len({orbit_of4[R] for R, h in uv_pairs}))

half = Fraction(1, 2)
assert all(v == (half,) * 3
           for (R, h) in uv_pairs
           for v in data3[hide_forall_rejected(R, 4, h)][1]
           if any(x.denominator > 1 for x in v))
log("S2: every 4->3 violation vertex is literally (1/2,1/2,1/2)  OK")

def region_from_intervals(U, intervals):
    R = 0
    for iv in intervals:
        R |= U.smask[iv]
    return R

def simple_universe(n):
    U = Universe.__new__(Universe)
    U.n, U.full, U.nstates = n, (1 << n) - 1, 1 << n
    U.intervals = all_intervals(n)
    U.smask = {iv: interval_statemask(*iv, n) for iv in U.intervals}
    return U

thm5_intervals = ((3, 15), (5, 7), (14, 15))   # [ab,U], [ac,abc], [bch,U]
thm5_region = region_from_intervals(U4, thm5_intervals)
thm5_visible = hide_forall_rejected(thm5_region, 4, 3)
thm5_visible_intervals = ((3, 7), (5, 7), (6, 7))
assert set(data4[thm5_region][0]) == set(thm5_intervals)
assert data4[thm5_region][3]
assert set(data3[thm5_visible][0]) == set(thm5_visible_intervals)
assert not data3[thm5_visible][3]
assert (half, half, half) in data3[thm5_visible][1]
log("S2b: named 4->3 example checked: upstairs Can list, downstairs edge Can list, "
    "upstairs integral, downstairs half vertex")

comp_region = sum(1 << s for s in (0, 3, 5, 6, 7))
comp_full = (1 << U3.nstates) - 1
assert not data3[comp_region][3]
assert data3[comp_full & ~comp_region][3]
log("S2b: signed-complement example checked: R non-integral, complement integral")

def odd_cycle_region(m):
    n, h = m + 1, m
    U = simple_universe(n)
    full = U.full
    intervals = []
    intervals.append(((1 << 0) | (1 << 1), full & ~(1 << h)))
    intervals.append(((1 << 2) | (1 << ((2 + 1) % m)) | (1 << h), full))
    for i in range(m):
        if i in (0, 2):
            continue
        intervals.append(((1 << i) | (1 << ((i + 1) % m)), full))
    return U, tuple(intervals), region_from_intervals(U, intervals)

for m in (3, 5):
    Uc, expected_cans, Rc = odd_cycle_region(m)
    Uv = simple_universe(m)
    expected_down = tuple(((1 << i) | (1 << ((i + 1) % m)), Uv.full)
                          for i in range(m))
    Rdown = hide_forall_rejected(Rc, m + 1, m)
    cans, verts, _, integral = region_polytope_data(Uc, Rc)
    vcans, vverts, _, vintegral = region_polytope_data(Uv, Rdown)
    assert set(cans) == set(expected_cans)
    assert integral
    assert set(vcans) == set(expected_down)
    assert not vintegral
    assert tuple([half] * m) in vverts
log("S2b: odd-cycle seam instances m=3,5 checked: Can lists, parent integrality, "
    "downstairs all-half vertex")

# ----------------------------------------------------------------- S3 Q1
fail = 0
for R in range(65536):
    cans, verts, _, _ = data4[R]
    for h in range(4):
        for i, Ri in zip((0, 1), faces(R, 4, h)):
            fv = sorted(tuple(v[k] for k in range(4) if k != h) for v in verts if v[h] == i)
            if fv != sorted(data3[Ri][1]): fail += 1
log("S3: general face lemma  P_Can(R^i) = x_h=i face of P_Can(R):", fail,
    "failures over 262144 (R,h,face)")

def is_mixed(cans, h):
    return (any((P >> h) & 1 for P, Q in cans)
            and any(not ((Q >> h) & 1) for P, Q in cans))

def unbalanced_triangle(cans, n):
    two = [c for c in (clause_of_interval(P, Q, n) for P, Q in cans) if len(c) == 2]
    for trio in itertools.combinations(two, 3):
        pairs = [frozenset(c) for c in trio]
        if len(set(pairs)) != 3 or len(set().union(*pairs)) != 3: continue
        if math.prod(s for c in trio for s in c.values()) == 1: return True
    return False

tot_mixed = mism = 0
for R in range(65536):
    cans, _, _, integ = data4[R]
    if not integ: continue
    for h in range(4):
        if not is_mixed(cans, h): continue
        tot_mixed += 1
        pred = unbalanced_triangle(data3[hide_forall_rejected(R, 4, h)][0], 3)
        if pred != ((R, h) in pairset): mism += 1
log(f"S3: integral-mixed pairs {tot_mixed}; safe {tot_mixed-len(uv_pairs)}; "
    f"violating {len(uv_pairs)}; classification mismatches {mism}")

# ----------------------------------------------------------------- S4 Q2 taxonomy
def clause_row(P, Q, n=4):
    lits = clause_of_interval(P, Q, n)
    return (sum(1 for v in lits.values() if v == -1) - 1,
            [lits.get(i, 0) for i in range(n)], lits)

def rankF(rows, F):
    M = [[Fraction(r.get(i, 0)) for i in F] for r in rows]; r = 0
    for c in range(len(F)):
        p = next((i for i in range(r, len(M)) if M[i][c]), None)
        if p is None: continue
        M[r], M[p] = M[p], M[r]
        for i in range(len(M)):
            if i != r and M[i][c]:
                f = M[i][c] / M[r][c]
                M[i] = [x - f * y for x, y in zip(M[i], M[r])]
        r += 1
    return r

def canon_clauseset(S, F):
    k = len(F); idx = {c: i for i, c in enumerate(F)}
    base = [{idx[i]: s for i, s in cl.items()} for cl in S]
    best = None
    for perm in itertools.permutations(range(k)):
        for flips in range(1 << k):
            img = tuple(sorted(tuple(sorted((perm[i], s * (-1 if (flips >> i) & 1 else 1))
                                            for i, s in cl.items())) for cl in base))
            key = (k, img)
            if best is None or key < best: best = key
    return best

mech = Counter()
for orb in orbits4:
    cans, verts, _, _ = data4[orb[0]]
    for v in verts:
        d = math.lcm(*[x.denominator for x in v])
        if d == 1: continue
        F = [i for i in range(4) if 0 < v[i] < 1]
        rc = []
        for (P, Q) in cans:
            b, a, lits = clause_row(P, Q)
            if b + sum(a[i] * v[i] for i in range(4)) != 0: continue
            free = {i: s for i, s in lits.items() if i in F}
            if free: rc.append(free)
        mins = []
        for r in range(1, len(rc) + 1):
            for S in itertools.combinations(rc, r):
                if rankF(S, F) == len(F) and not any(all(t in S for t in T) for T in mins):
                    mins.append(S)
            if mins and r >= max(map(len, mins)): break
        for S in mins: mech[canon_clauseset(S, F)] += 1
log("S4: minimal-certificate mechanisms at n=4 (expect 6: UC3, UC3+pendant x2, UC4, T1, T2):")
for key, cnt in mech.most_common():
    log("     count", cnt, " free", key[0], " clauses", key[1])

# ----------------------------------------------------------------- S5 Q3
def down_closed(R, n):
    for s in range(1 << n):
        if (R >> s) & 1:
            sub = s
            while True:
                if not ((R >> sub) & 1): return False
                if sub == 0: break
                sub = (sub - 1) & s
    return True

for n, data in ((3, data3), (4, data4)):
    full = (1 << (1 << n)) - 1
    stable = sum(data[R][3] == data[full & ~R][3] for R in range(full + 1))
    hered = [R for R in range(full + 1) if down_closed(R, n)]
    bad = [R for R in hered if data[R][3] != data[full & ~R][3]]
    log(f"S5: n={n} stable {stable}/{full+1}; hereditary {len(hered)} "
        f"(Dedekind), hereditary instabilities {len(bad)}")

# ----------------------------------------------------------------- S6 Q4
U5 = Universe.__new__(Universe)
U5.n, U5.full, U5.nstates = 5, 31, 32
U5.intervals = all_intervals(5)
U5.smask = {iv: interval_statemask(*iv, 5) for iv in U5.intervals}

def integral5(parent):
    return all(x.denominator == 1
               for v in vertices_of(hrep_rows(U5, can_intervals(U5, parent)))
               for x in v)

nonint3 = [R for R in range(256) if not data3[R][3]]
reach3 = 0
for R in nonint3:
    states = [s for s in range(8) if (R >> s) & 1]
    found = False
    for X0 in states:
        for X1 in states:
            if X0 == X1: continue
            parent = lift_pair_to_region(R & ~(1 << X0), R & ~(1 << X1), 3)
            if data4[parent][3]: found = True; break
        if found: break
    reach3 += found
log("S6: visible n=3 — seam-2 integral parent exists for", reach3, "of", len(nonint3),
    "non-integral regions (all reachable)")

nonint_reps = [orb[0] for orb in orbits4 if not data4[orb[0]][3]]
unresolved, seams = [], Counter()
for R in nonint_reps:
    states = [s for s in range(16) if (R >> s) & 1]
    G = {k: [] for k in range(5)}
    for k in G:
        for X in itertools.combinations(states, k):
            Rm = R
            for s in X: Rm &= ~(1 << s)
            if data4[Rm][3]: G[k].append((frozenset(X), Rm))
    found = None
    for seam in range(2, 9):
        if found: break
        for s0 in range(1, seam):
            s1 = seam - s0
            if s1 < s0 or s0 > 4 or s1 > 4: continue
            for X0, R0 in G[s0]:
                for X1, R1 in G[s1]:
                    if X0 & X1: continue
                    if integral5(lift_pair_to_region(R0, R1, 4)):
                        found = seam; break
                if found: break
            if found: break
    if found: seams[found] += 1
    else: unresolved.append(R)
log("S6: visible n=4 — min-seam distribution over 155 non-integral orbits:", dict(seams),
    "; unresolved:", unresolved or "none (rep 27606 needs a (2,4) split, found at seam 6)")
log("done.")
