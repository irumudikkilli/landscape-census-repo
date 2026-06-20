"""Bounded exact n=5 falsification probe for signed admission geometry.

This is not a full n=5 census. It probes structured and randomized exact
families for: denominator >=4 examples, new n=5 active mechanisms, unexpected
5->4 universal shadows from integral parents, and small-seam Q4 failures.
"""

from __future__ import annotations

import itertools
import ast
import json
import math
import os
import pickle
import random
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "computational_supplement_20260610"))

from sag import (  # noqa: E402
    Universe,
    all_intervals,
    can_intervals,
    clause_of_interval,
    faces,
    h_polarity,
    hide_forall_rejected,
    hrep_rows,
    interval_statemask,
    lift_pair_to_region,
    region_polytope_data,
    vertices_of,
)

T0 = time.time()


def log(*parts: object) -> None:
    print(f"[{time.time() - T0:7.1f}s]", *parts, flush=True)


def popcount(x: int) -> int:
    return x.bit_count()


def simple_universe(n: int):
    U = Universe.__new__(Universe)
    U.n = n
    U.full = (1 << n) - 1
    U.nstates = 1 << n
    U.intervals = all_intervals(n)
    U.smask = {iv: interval_statemask(*iv, n) for iv in U.intervals}
    return U


def region_from_intervals(U, intervals):
    R = 0
    for iv in intervals:
        R |= U.smask[iv]
    return R


def clause_arity(P: int, Q: int, n: int) -> int:
    return popcount(P) + (n - popcount(Q))


def spectrum_key(dens) -> tuple[int, ...]:
    return tuple(sorted(dens))


def lcm_den(v) -> int:
    d = 1
    for x in v:
        d = math.lcm(d, x.denominator)
    return d


def finite_spectrum(verts) -> tuple[int, ...]:
    dens = {lcm_den(v) for v in verts}
    return tuple(sorted(dens))


def orbit_decomposition(U, nregions):
    seen = bytearray(nregions)
    orbits = []
    for R in range(nregions):
        if seen[R]:
            continue
        orb = sorted(U.orbit(R))
        for x in orb:
            seen[x] = 1
        orbits.append(orb)
    return orbits


def census4(cache="data4_probe.pkl"):
    U4 = Universe(4)
    if Path(cache).exists():
        with open(cache, "rb") as f:
            data4 = pickle.load(f)
    else:
        data4 = {}
        for R in range(1 << U4.nstates):
            data4[R] = region_polytope_data(U4, R)
        with open(cache, "wb") as f:
            pickle.dump(data4, f)
    orbits4 = orbit_decomposition(U4, 1 << U4.nstates)
    return U4, data4, orbits4


def cylinder_region(R4: int) -> int:
    out = 0
    for s in range(16):
        if (R4 >> s) & 1:
            out |= 1 << s
            out |= 1 << (s | 16)
    return out


def row_of_interval(P: int, Q: int, n: int):
    lits = clause_of_interval(P, Q, n)
    b = sum(1 for v in lits.values() if v == -1) - 1
    a = [0] * n
    for i, s in lits.items():
        a[i] = s
    return [b] + a


def determinant(matrix):
    n = len(matrix)
    M = [[Fraction(x) for x in row] for row in matrix]
    det = Fraction(1)
    sign = 1
    for c in range(n):
        p = next((i for i in range(c, n) if M[i][c]), None)
        if p is None:
            return Fraction(0)
        if p != c:
            M[c], M[p] = M[p], M[c]
            sign *= -1
        pivot = M[c][c]
        det *= pivot
        for i in range(c + 1, n):
            if M[i][c]:
                f = M[i][c] / pivot
                for j in range(c, n):
                    M[i][j] -= f * M[c][j]
    return det * sign


def solve_square(rows, n: int):
    M = [[Fraction(x) for x in row[1:]] + [Fraction(-row[0])] for row in rows]
    r = 0
    for c in range(n):
        p = next((i for i in range(r, n) if M[i][c]), None)
        if p is None:
            return None
        M[r], M[p] = M[p], M[r]
        pivot = M[r][c]
        M[r] = [x / pivot for x in M[r]]
        for i in range(n):
            if i != r and M[i][c]:
                f = M[i][c]
                M[i] = [x - f * y for x, y in zip(M[i], M[r])]
        r += 1
    return tuple(M[i][-1] for i in range(n))


def interval_label(iv, n: int) -> str:
    P, Q = iv
    present = [str(i) for i in range(n) if (P >> i) & 1]
    absent = [str(i) for i in range(n) if not ((Q >> i) & 1)]
    return f"+{','.join(present) or '-'} / -{','.join(absent) or '-'}"


def random_interval_set(U, rng, min_k=3, max_k=8, min_arity=2, max_arity=None):
    if max_arity is None:
        max_arity = U.n
    pool = [iv for iv in U.intervals if min_arity <= clause_arity(*iv, U.n) <= max_arity]
    k = rng.randint(min_k, max_k)
    return tuple(rng.sample(pool, k))


def test_cylindrical_lifts(U5, data4, orbits4):
    nonintegral_reps = [orb[0] for orb in orbits4 if not data4[orb[0]][3]]
    spectra = Counter()
    denom4_hits = []
    changed = []
    for R4 in nonintegral_reps:
        R5 = cylinder_region(R4)
        _, verts5, dens5, integral5 = region_polytope_data(U5, R5)
        key4 = spectrum_key(data4[R4][2])
        key5 = spectrum_key(dens5)
        spectra[key5] += 1
        if integral5:
            changed.append({"R4": R4, "from": key4, "to": key5})
        if any(d >= 4 for d in key5):
            denom4_hits.append({"R4": R4, "spectrum": key5, "vertices": [str(v) for v in verts5[:3]]})
    return {
        "nonintegral_orbits": len(nonintegral_reps),
        "spectra": {str(k): v for k, v in sorted(spectra.items())},
        "integrality_changed": changed[:10],
        "denominator_4plus_hits": denom4_hits,
    }


def verify_d4_certificate(U5):
    intervals = (
        ((1 << 0), U5.full & ~((1 << 2) | (1 << 4))),
        ((1 << 1) | (1 << 3), U5.full & ~(1 << 4)),
        ((1 << 1) | (1 << 3), U5.full & ~(1 << 2)),
        ((1 << 0) | (1 << 1), U5.full & ~(1 << 2)),
        ((1 << 0) | (1 << 3), U5.full),
    )
    R = region_from_intervals(U5, intervals)
    cans, verts, dens, integral = region_polytope_data(U5, R)
    vertex = (Fraction(1, 2), Fraction(3, 4), Fraction(1, 4),
              Fraction(1, 2), Fraction(1, 4))
    rows = [row_of_interval(*iv, 5) for iv in intervals]
    det = determinant([row[1:] for row in rows])
    assert set(cans) == set(intervals)
    assert vertex in verts
    assert lcm_den(vertex) == 4
    assert abs(det) == 4
    assert all(Fraction(row[0]) + sum(Fraction(row[i + 1]) * vertex[i] for i in range(5)) == 0
               for row in rows)
    assert not integral
    return {
        "R": R,
        "states": popcount(R),
        "canonical_count": len(cans),
        "spectrum": spectrum_key(dens),
        "vertex": str(vertex),
        "determinant": str(det),
        "canonical_intervals": [interval_label(iv, 5) for iv in intervals],
    }


def random_n5_regions(U5, rng, samples: int, progress=True):
    spectra = Counter()
    denom4_hits = []
    nonintegral_examples = []
    max_den = 1
    for t in range(samples):
        intervals = random_interval_set(U5, rng)
        R = region_from_intervals(U5, intervals)
        cans, verts, dens, integral = region_polytope_data(U5, R)
        key = spectrum_key(dens)
        spectra[key] += 1
        local_max = max(key or (1,))
        max_den = max(max_den, local_max)
        if not integral and len(nonintegral_examples) < 25:
            nonintegral_examples.append({
                "R": R,
                "intervals": [interval_label(iv, 5) for iv in intervals],
                "canonical_count": len(cans),
                "spectrum": key,
                "states": popcount(R),
            })
        if local_max >= 4 and len(denom4_hits) < 10:
            denom4_hits.append({
                "R": R,
                "intervals": [interval_label(iv, 5) for iv in intervals],
                "canonical_count": len(cans),
                "spectrum": key,
                "vertices": [str(v) for v in verts if lcm_den(v) >= 4][:5],
            })
        if progress and (t + 1) % 250 == 0:
            log("random n=5 regions", t + 1, "samples; max denominator", max_den)
    return {
        "samples": samples,
        "spectra": {str(k): v for k, v in sorted(spectra.items())},
        "max_denominator": max_den,
        "denominator_4plus_hits": denom4_hits,
        "nonintegral_examples": nonintegral_examples,
    }


def active_row_search(U5, rng, samples: int, progress=True):
    pool = [iv for iv in U5.intervals if 2 <= clause_arity(*iv, 5) <= 5]
    candidate_denoms = Counter()
    survived = []
    tested_candidates = 0
    for t in range(samples):
        active = tuple(rng.sample(pool, 5))
        rows = [row_of_interval(*iv, 5) for iv in active]
        x = solve_square(rows, 5)
        if x is None or not all(0 < xi < 1 for xi in x):
            continue
        d = lcm_den(x)
        if d < 4:
            continue
        tested_candidates += 1
        candidate_denoms[d] += 1
        R = region_from_intervals(U5, active)
        _, verts, dens, _ = region_polytope_data(U5, R)
        hit_vertices = [v for v in verts if lcm_den(v) >= 4]
        if hit_vertices and len(survived) < 10:
            survived.append({
                "candidate": str(x),
                "candidate_denominator": d,
                "spectrum": spectrum_key(dens),
                "active": [interval_label(iv, 5) for iv in active],
                "vertices": [str(v) for v in hit_vertices[:5]],
            })
        if progress and (t + 1) % 5000 == 0:
            log("active-row samples", t + 1, "candidate denom>=4 systems", tested_candidates)
    return {
        "samples": samples,
        "candidate_denominators": {str(k): v for k, v in sorted(candidate_denoms.items())},
        "surviving_denominator_4plus_hits": survived,
    }


def universal_shadow_sample(U5, data4, rng, samples: int, progress=True):
    spectra = Counter()
    integral_parents = 0
    mixed_ports = 0
    violations = 0
    outside_n4 = []
    for t in range(samples):
        intervals = random_interval_set(U5, rng, min_k=3, max_k=9)
        R = region_from_intervals(U5, intervals)
        cans, _, _, integral = region_polytope_data(U5, R)
        if not integral:
            continue
        integral_parents += 1
        for h in range(5):
            fp, fa = h_polarity(U5, cans, h)
            if not (fp and fa):
                continue
            mixed_ports += 1
            down = hide_forall_rejected(R, 5, h)
            key = spectrum_key(data4[down][2])
            spectra[key] += 1
            if not data4[down][3]:
                violations += 1
            if any(d >= 4 for d in key) and len(outside_n4) < 10:
                outside_n4.append({"parent": R, "h": h, "visible": down, "spectrum": key})
        if progress and (t + 1) % 250 == 0:
            log("5->4 parent samples", t + 1, "integral parents", integral_parents,
                "mixed ports", mixed_ports, "violations", violations)
    return {
        "samples": samples,
        "integral_parents": integral_parents,
        "mixed_ports": mixed_ports,
        "violations": violations,
        "shadow_spectra": {str(k): v for k, v in sorted(spectra.items())},
        "outside_n4_denominator_hits": outside_n4,
    }


def split_counts(total: int, workers: int) -> list[int]:
    workers = max(1, min(workers, total if total > 0 else 1))
    base, rem = divmod(total, workers)
    return [base + (1 if i < rem else 0) for i in range(workers)]


def merge_spectrum_dicts(dicts):
    out = Counter()
    for d in dicts:
        out.update(d)
    return {str(k): v for k, v in sorted(out.items(), key=lambda kv: kv[0])}


def random_region_worker(args):
    seed, count = args
    return random_n5_regions(simple_universe(5), random.Random(seed), count, progress=False)


def active_row_worker(args):
    seed, count = args
    return active_row_search(simple_universe(5), random.Random(seed), count, progress=False)


def shadow_worker(args):
    seed, count, cache = args
    with open(cache, "rb") as f:
        data4 = pickle.load(f)
    return universal_shadow_sample(simple_universe(5), data4, random.Random(seed), count, progress=False)


def parallel_random_regions(seed: int, samples: int, workers: int):
    if workers <= 1:
        return random_n5_regions(simple_universe(5), random.Random(seed), samples)
    parts = split_counts(samples, workers)
    results = []
    with ProcessPoolExecutor(max_workers=len(parts)) as pool:
        futures = [pool.submit(random_region_worker, (seed + 1009 * i, count))
                   for i, count in enumerate(parts) if count]
        for fut in as_completed(futures):
            results.append(fut.result())
            log("random-region worker complete", len(results), "/", len(futures))
    spectra = Counter()
    examples = []
    hits = []
    max_den = 1
    for r in results:
        spectra.update({ast.literal_eval(k): v for k, v in r["spectra"].items()})
        examples.extend(r["nonintegral_examples"])
        hits.extend(r["denominator_4plus_hits"])
        max_den = max(max_den, r["max_denominator"])
    return {
        "samples": samples,
        "spectra": {str(k): v for k, v in sorted(spectra.items())},
        "max_denominator": max_den,
        "denominator_4plus_hits": hits[:10],
        "nonintegral_examples": examples[:25],
    }


def parallel_active_rows(seed: int, samples: int, workers: int):
    if workers <= 1:
        return active_row_search(simple_universe(5), random.Random(seed), samples)
    parts = split_counts(samples, workers)
    results = []
    with ProcessPoolExecutor(max_workers=len(parts)) as pool:
        futures = [pool.submit(active_row_worker, (seed + 2003 * i, count))
                   for i, count in enumerate(parts) if count]
        for fut in as_completed(futures):
            results.append(fut.result())
            log("active-row worker complete", len(results), "/", len(futures))
    denoms = Counter()
    survived = []
    for r in results:
        denoms.update({int(k): v for k, v in r["candidate_denominators"].items()})
        survived.extend(r["surviving_denominator_4plus_hits"])
    return {
        "samples": samples,
        "candidate_denominators": {str(k): v for k, v in sorted(denoms.items())},
        "surviving_denominator_4plus_hits": survived[:10],
    }


def parallel_shadows(seed: int, samples: int, workers: int, cache: str):
    if workers <= 1:
        with open(cache, "rb") as f:
            data4 = pickle.load(f)
        return universal_shadow_sample(simple_universe(5), data4, random.Random(seed), samples)
    parts = split_counts(samples, workers)
    results = []
    with ProcessPoolExecutor(max_workers=len(parts)) as pool:
        futures = [pool.submit(shadow_worker, (seed + 3001 * i, count, cache))
                   for i, count in enumerate(parts) if count]
        for fut in as_completed(futures):
            results.append(fut.result())
            log("shadow worker complete", len(results), "/", len(futures))
    spectra = Counter()
    outside = []
    integral_parents = mixed_ports = violations = 0
    for r in results:
        spectra.update({ast.literal_eval(k): v for k, v in r["shadow_spectra"].items()})
        outside.extend(r["outside_n4_denominator_hits"])
        integral_parents += r["integral_parents"]
        mixed_ports += r["mixed_ports"]
        violations += r["violations"]
    return {
        "samples": samples,
        "integral_parents": integral_parents,
        "mixed_ports": mixed_ports,
        "violations": violations,
        "shadow_spectra": {str(k): v for k, v in sorted(spectra.items())},
        "outside_n4_denominator_hits": outside[:10],
    }


def q4_small_seam_probe(U5, rng, examples, max_candidates: int):
    U6 = simple_universe(6)
    tested = []
    for ex in examples:
        if len(tested) >= max_candidates:
            break
        R = ex["R"]
        states = [s for s in range(32) if (R >> s) & 1]
        if not (2 <= len(states) <= 14):
            continue
        found = None
        pairs_tested = 0
        for x0 in states:
            R0 = R & ~(1 << x0)
            if not region_polytope_data(U5, R0)[3]:
                continue
            for x1 in states:
                if x1 == x0:
                    continue
                R1 = R & ~(1 << x1)
                if not region_polytope_data(U5, R1)[3]:
                    continue
                pairs_tested += 1
                parent = lift_pair_to_region(R0, R1, 5)
                cans6 = can_intervals(U6, parent)
                verts6 = vertices_of(hrep_rows(U6, cans6))
                if all(lcm_den(v) == 1 for v in verts6):
                    found = {"x0": x0, "x1": x1, "canonical_parent_count": len(cans6)}
                    break
            if found:
                break
        tested.append({
            "R": R,
            "states": len(states),
            "spectrum": ex["spectrum"],
            "seam2_parent_found": found,
            "pairs_tested_after_face_filter": pairs_tested,
        })
        log("Q4 seam-2 candidate", len(tested), "states", len(states), "found", bool(found))
    return {"tested": tested, "candidate_limit": max_candidates}


def main():
    seed = int(os.environ.get("N5_PROBE_SEED", "20260610"))
    region_samples = int(os.environ.get("N5_REGION_SAMPLES", "2500"))
    active_samples = int(os.environ.get("N5_ACTIVE_SAMPLES", "30000"))
    parent_samples = int(os.environ.get("N5_PARENT_SAMPLES", "3000"))
    q4_candidates = int(os.environ.get("N5_Q4_CANDIDATES", "12"))
    workers = int(os.environ.get("N5_WORKERS", str(max(1, min(8, (os.cpu_count() or 2) // 2)))))
    rng = random.Random(seed)

    log("starting n=5 probe", {
        "seed": seed,
        "region_samples": region_samples,
        "active_samples": active_samples,
        "parent_samples": parent_samples,
        "q4_candidates": q4_candidates,
        "workers": workers,
    })
    U4, data4, orbits4 = census4()
    U5 = simple_universe(5)
    log("loaded n=4 census/orbits", len(data4), len(orbits4))

    result = {
        "seed": seed,
        "region_samples": region_samples,
        "active_samples": active_samples,
        "parent_samples": parent_samples,
        "q4_candidates": q4_candidates,
        "workers": workers,
    }

    log("checking cylindrical lifts of all nonintegral n=4 orbit reps")
    result["cylindrical_lifts"] = test_cylindrical_lifts(U5, data4, orbits4)

    log("verifying explicit n=5 determinant-4 certificate")
    result["d4_certificate"] = verify_d4_certificate(U5)

    log("sampling random n=5 interval-generated regions")
    result["random_n5_regions"] = parallel_random_regions(seed + 11, region_samples, workers)

    log("searching random active-row determinant systems")
    result["active_row_search"] = parallel_active_rows(seed + 23, active_samples, workers)

    log("sampling 5->4 universal shadows from integral n=5 parents")
    result["universal_shadow_sample"] = parallel_shadows(
        seed + 37, parent_samples, workers, "data4_probe.pkl"
    )

    log("probing seam-2 one-hidden repair for selected visible n=5 examples")
    result["q4_small_seam_probe"] = q4_small_seam_probe(
        U5, rng, result["random_n5_regions"]["nonintegral_examples"], q4_candidates
    )

    hard_hits = []
    if result["cylindrical_lifts"]["denominator_4plus_hits"]:
        hard_hits.append("cylindrical_lift_denominator_4plus")
    if result["random_n5_regions"]["denominator_4plus_hits"]:
        hard_hits.append("random_region_denominator_4plus")
    if result["active_row_search"]["surviving_denominator_4plus_hits"]:
        hard_hits.append("active_row_denominator_4plus")
    if result["d4_certificate"]:
        hard_hits.append("explicit_d4_certificate")
    if result["universal_shadow_sample"]["outside_n4_denominator_hits"]:
        hard_hits.append("5_to_4_shadow_outside_n4_spectra")
    result["hard_hits"] = hard_hits

    out = Path("n5_probe_results_20260610.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    log("hard hits", hard_hits or "none")
    log("wrote", out)


if __name__ == "__main__":
    main()
