"""Signed admission geometry toolkit (exact arithmetic throughout).

States on n coordinates  <-> integers 0..2^n-1 (bit i = coordinate i present).
A region R subseteq 2^U  <-> integer bitmask over the 2^n states
                             (bit s of Rmask set  <=>  state s in R).
Interval [P,Q] (P subseteq Q) <-> pair of coordinate masks.
"""
from fractions import Fraction
from functools import lru_cache
from itertools import permutations, product
import cdd

# ---------------------------------------------------------------- intervals
def submasks(Q):
    """all submasks of Q, including 0 and Q"""
    s = Q
    while True:
        yield s
        if s == 0:
            return
        s = (s - 1) & Q

def all_intervals(n):
    full = (1 << n) - 1
    out = []
    for Q in range(1 << n):
        for P in submasks(Q):
            out.append((P, Q))
    return out

def interval_statemask(P, Q, n):
    m = 0
    free = Q & ~P
    for s in submasks(free):
        m |= 1 << (P | s)
    return m

class Universe:
    """precomputed structures for a fixed n"""
    def __init__(self, n):
        self.n = n
        self.full = (1 << n) - 1
        self.nstates = 1 << n
        self.intervals = all_intervals(n)
        self.smask = {iv: interval_statemask(iv[0], iv[1], n) for iv in self.intervals}
        # group: signed permutations, as state-permutation tuples
        self.group = self._build_group()

    def _build_group(self):
        n = self.n
        elems = []
        for perm in permutations(range(n)):
            for flips in range(1 << n):
                sp = [0] * self.nstates
                for s in range(self.nstates):
                    t = 0
                    for i in range(n):
                        bit = ((s >> i) & 1) ^ ((flips >> i) & 1)
                        if bit:
                            t |= 1 << perm[i]
                    sp[s] = t
                elems.append((perm, flips, tuple(sp)))
        return elems

    def act_region(self, sp, Rmask):
        out = 0
        for s in range(self.nstates):
            if (Rmask >> s) & 1:
                out |= 1 << sp[s]
        return out

    def canon_region(self, Rmask):
        best = None
        for (_, _, sp) in self.group:
            v = self.act_region(sp, Rmask)
            if best is None or v < best:
                best = v
        return best

    def orbit(self, Rmask):
        return {self.act_region(sp, Rmask) for (_, _, sp) in self.group}

# ---------------------------------------------------------------- Can(R)
def can_intervals(U, Rmask):
    """inclusion-maximal Boolean intervals contained in R"""
    contained = [iv for iv in U.intervals if (U.smask[iv] & ~Rmask) == 0]
    out = []
    for (P, Q) in contained:
        maximal = True
        for (P2, Q2) in contained:
            if (P2, Q2) != (P, Q) and (P2 & ~P) == 0 and (Q & ~Q2) == 0:
                maximal = False
                break
        if maximal:
            out.append((P, Q))
    return out

def clause_of_interval(P, Q, n):
    """escape clause as dict coord -> +1 (positive literal y_j, j notin Q)
       or -1 (negative literal, i in P)."""
    full = (1 << n) - 1
    lits = {}
    for i in range(n):
        if (P >> i) & 1:
            lits[i] = -1
        elif not ((Q >> i) & 1):
            lits[i] = +1
    return lits

# ---------------------------------------------------------------- polytope
def hrep_rows(U, cans):
    """rows [b, a_1..a_n] meaning b + a.x >= 0 ; box + escape inequalities"""
    n = U.n
    rows = []
    for i in range(n):
        rows.append([0] + [1 if j == i else 0 for j in range(n)])     # x_i >= 0
        rows.append([1] + [-1 if j == i else 0 for j in range(n)])    # 1 - x_i >= 0
    for (P, Q) in cans:
        lits = clause_of_interval(P, Q, n)
        b = sum(1 for v in lits.values() if v == -1) - 1
        a = [0] * n
        for i, sgn in lits.items():
            a[i] = sgn
        rows.append([b] + a)
    return rows

def vertices_of(rows):
    """exact vertices; returns list of tuples of Fractions ([] if empty)"""
    m = cdd.Matrix(rows, number_type='fraction')
    m.rep_type = cdd.RepType.INEQUALITY
    try:
        g = cdd.Polyhedron(m).get_generators()
    except RuntimeError:
        # numerical impossibility shouldn't occur with fraction type
        raise
    verts = []
    for r in g:
        if r[0] == 1:
            verts.append(tuple(Fraction(x) for x in r[1:]))
        # rays impossible: bounded by box (and infeasible -> no rows)
    return verts

def region_polytope_data(U, Rmask, cans=None):
    """returns (cans, vertices, denominators_set, integral_bool)"""
    if cans is None:
        cans = can_intervals(U, Rmask)
    rows = hrep_rows(U, cans)
    verts = vertices_of(rows)
    dens = set()
    for v in verts:
        d = 1
        for x in v:
            d = d * x.denominator // _gcd(d, x.denominator)
        dens.add(d)
    integral = all(d == 1 for d in dens)  # empty -> integral
    return cans, verts, dens, integral

def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a

# ---------------------------------------------------------------- hiding (last coordinate h = bit n-1 of an (n)-coordinate universe)
def faces(Rmask, n, h):
    """R^0, R^1 as regions on n-1 coordinates obtained by fixing coordinate h.
       Coordinates are renumbered: visible coords = all except h, in order."""
    vis = [i for i in range(n) if i != h]
    R0 = 0
    R1 = 0
    for s in range(1 << n):
        if not ((Rmask >> s) & 1):
            continue
        t = 0
        for k, i in enumerate(vis):
            if (s >> i) & 1:
                t |= 1 << k
        if (s >> h) & 1:
            R1 |= 1 << t
        else:
            R0 |= 1 << t
    return R0, R1

def hide_exists_rejected(Rmask, n, h):
    """rejected side of admitted-existential hiding = forall_h R = R0 AND R1"""
    R0, R1 = faces(Rmask, n, h)
    return R0 & R1

def hide_forall_rejected(Rmask, n, h):
    """rejected side of admitted-universal hiding = exists_h R = R0 OR R1"""
    R0, R1 = faces(Rmask, n, h)
    return R0 | R1

def lift_pair_to_region(R0, R1, nv, h_position_last=True):
    """build the n=(nv+1)-coordinate region whose h=0 face is R0, h=1 face R1
       (h is the last coordinate)."""
    R = 0
    for t in range(1 << nv):
        if (R0 >> t) & 1:
            R |= 1 << t
        if (R1 >> t) & 1:
            R |= 1 << (t | (1 << nv))
    return R

def h_polarity(U, cans, h):
    """(forces_present_exists, forces_absent_exists) for coordinate h in Can list"""
    fp = any((P >> h) & 1 for (P, Q) in cans)
    fa = any(not ((Q >> h) & 1) for (P, Q) in cans)
    return fp, fa
