#!/usr/bin/env python3
"""Verify the compact certificate packet for the finite census claims."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import sys
import time
from collections import Counter
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
    hide_exists_rejected,
    hide_forall_rejected,
    hrep_rows,
    interval_statemask,
    lift_pair_to_region,
    region_polytope_data,
    vertices_of,
)


T0 = time.time()


def log(*parts: object) -> None:
    print(f"[{time.time() - T0:6.2f}s]", *parts, flush=True)


def assert_equal(got, expected, label: str) -> None:
    if got != expected:
        raise AssertionError(f"{label}: got {got!r}, expected {expected!r}")


def parse_fraction(value: str) -> Fraction:
    return Fraction(value)


def simple_universe(n: int):
    U = Universe.__new__(Universe)
    U.n = n
    U.full = (1 << n) - 1
    U.nstates = 1 << n
    U.intervals = all_intervals(n)
    U.smask = {iv: interval_statemask(*iv, n) for iv in U.intervals}
    return U


def region_from_intervals(U, intervals: list[tuple[int, int]]) -> int:
    R = 0
    for P, Q in intervals:
        R |= U.smask[(P, Q)]
    return R


def region_from_states(states: list[int]) -> int:
    R = 0
    for s in states:
        R |= 1 << s
    return R


def determinant(matrix: list[list[int | Fraction]]) -> Fraction:
    n = len(matrix)
    A = [[Fraction(x) for x in row] for row in matrix]
    det = Fraction(1)
    for i in range(n):
        pivot = next((r for r in range(i, n) if A[r][i]), None)
        if pivot is None:
            return Fraction(0)
        if pivot != i:
            A[i], A[pivot] = A[pivot], A[i]
            det = -det
        pv = A[i][i]
        det *= pv
        for r in range(i + 1, n):
            if not A[r][i]:
                continue
            factor = A[r][i] / pv
            for c in range(i, n):
                A[r][c] -= factor * A[i][c]
    return det


def lcm_den(vertex) -> int:
    d = 1
    for x in vertex:
        d = math.lcm(d, x.denominator)
    return d


def build_state_permutations(n: int) -> list[tuple[int, ...]]:
    nstates = 1 << n
    out = []
    for perm in itertools.permutations(range(n)):
        for flips in range(1 << n):
            sp = []
            for s in range(nstates):
                t = 0
                for i in range(n):
                    bit = ((s >> i) & 1) ^ ((flips >> i) & 1)
                    if bit:
                        t |= 1 << perm[i]
                sp.append(t)
            out.append(tuple(sp))
    return out


def count_cycles(sp: tuple[int, ...]) -> int:
    seen = [False] * len(sp)
    cycles = 0
    for i in range(len(sp)):
        if seen[i]:
            continue
        cycles += 1
        j = i
        while not seen[j]:
            seen[j] = True
            j = sp[j]
    return cycles


def burnside_orbit_count(n: int) -> int:
    perms = build_state_permutations(n)
    total = sum(1 << count_cycles(sp) for sp in perms)
    return total // len(perms)


def b4_orbit_denominator_spectrum() -> dict[str, int]:
    U4 = Universe(4)
    seen: set[int] = set()
    spectrum = Counter()
    for R in range(1 << U4.nstates):
        if R in seen:
            continue
        orb = U4.orbit(R)
        seen.update(orb)
        rep = min(orb)
        _, _, dens, _ = region_polytope_data(U4, rep)
        spectrum[str(tuple(sorted(dens)))] += 1
    return dict(sorted(spectrum.items()))


def orbit_decomposition(U, nregions: int):
    seen = bytearray(nregions)
    orbits = []
    orbit_of = {}
    for R in range(nregions):
        if seen[R]:
            continue
        orbit = sorted(U.orbit(R))
        for x in orbit:
            seen[x] = 1
            orbit_of[x] = len(orbits)
        orbits.append(orbit)
    return orbits, orbit_of


def project_interval(P: int, Q: int, n: int, h: int) -> tuple[int, int]:
    visible = [i for i in range(n) if i != h]

    def project(mask: int) -> int:
        return sum(1 << k for k, i in enumerate(visible) if (mask >> i) & 1)

    return project(P), project(Q)


def is_mixed(cans, h: int) -> bool:
    return any((P >> h) & 1 for P, _ in cans) and any(not ((Q >> h) & 1) for _, Q in cans)


def unbalanced_triangle(cans, n: int) -> bool:
    two_clauses = [c for c in (clause_of_interval(P, Q, n) for P, Q in cans) if len(c) == 2]
    for trio in itertools.combinations(two_clauses, 3):
        pairs = [frozenset(clause) for clause in trio]
        if len(set(pairs)) != 3 or len(set().union(*pairs)) != 3:
            continue
        if math.prod(sign for clause in trio for sign in clause.values()) == 1:
            return True
    return False


def down_closed(R: int, n: int) -> bool:
    for s in range(1 << n):
        if not ((R >> s) & 1):
            continue
        sub = s
        while True:
            if not ((R >> sub) & 1):
                return False
            if sub == 0:
                break
            sub = (sub - 1) & s
    return True


def integral_parent_checker():
    U5 = simple_universe(5)

    def integral5(parent: int) -> bool:
        cans = can_intervals(U5, parent)
        verts = vertices_of(hrep_rows(U5, cans))
        return all(x.denominator == 1 for v in verts for x in v)

    return integral5


def verify_finite_census_claims(packet: dict) -> None:
    claims = packet["claims"]["finite_census"]
    U3, U4 = Universe(3), Universe(4)

    data3 = {R: region_polytope_data(U3, R) for R in range(1 << U3.nstates)}
    data4 = {R: region_polytope_data(U4, R) for R in range(1 << U4.nstates)}

    assert_equal(sum(1 for R in data3 if data3[R][3]), claims["n3_integral"], "n=3 integral count")
    assert_equal(sum(1 for R in data4 if data4[R][3]), claims["n4_integral"], "n=4 integral count")
    assert_equal(len(data3), claims["n3_region_count"], "n=3 region count")
    assert_equal(len(data4), claims["n4_region_count"], "n=4 region count")

    orbits4, orbit_of4 = orbit_decomposition(U4, 1 << U4.nstates)

    identity_failures = 0
    existential_violations = 0
    universal_pairs = []
    for R in range(1 << U4.nstates):
        cans4, _, _, integral4 = data4[R]
        for h in range(4):
            down_exists = hide_exists_rejected(R, 4, h)
            saturated = {
                project_interval(P, Q, 4, h)
                for P, Q in cans4
                if not ((P >> h) & 1) and ((Q >> h) & 1)
            }
            if saturated != set(data3[down_exists][0]):
                identity_failures += 1
            if integral4 and not data3[down_exists][3]:
                existential_violations += 1
            if integral4 and not data3[hide_forall_rejected(R, 4, h)][3]:
                universal_pairs.append((R, h))

    assert_equal(identity_failures, claims["existential_identity_failures"], "existential identity failures")
    assert_equal(existential_violations, claims["existential_integrality_violations"], "existential integrality violations")
    assert_equal(len(universal_pairs), claims["universal_violating_pairs"], "universal violating pairs")
    assert_equal(len({R for R, _ in universal_pairs}), claims["universal_violating_regions"], "universal violating regions")

    seen_pairs = set()
    pair_orbits = 0
    for R, h in universal_pairs:
        if (R, h) in seen_pairs:
            continue
        pair_orbits += 1
        for perm, _, sp in U4.group:
            seen_pairs.add((U4.act_region(sp, R), perm[h]))
    assert_equal(pair_orbits, claims["universal_pair_orbits"], "universal pair orbits")
    assert_equal(len({orbit_of4[R] for R, _ in universal_pairs}), claims["universal_region_orbits"], "universal region orbits")

    half = Fraction(1, 2)
    for R, h in universal_pairs:
        for v in data3[hide_forall_rejected(R, 4, h)][1]:
            if any(x.denominator > 1 for x in v) and v != (half, half, half):
                raise AssertionError("universal violation has non-half fractional vertex")

    face_failures = 0
    for R in range(1 << U4.nstates):
        _, verts4, _, _ = data4[R]
        for h in range(4):
            for i, Ri in zip((0, 1), faces(R, 4, h)):
                projected_face = sorted(tuple(v[k] for k in range(4) if k != h) for v in verts4 if v[h] == i)
                if projected_face != sorted(data3[Ri][1]):
                    face_failures += 1
    assert_equal(face_failures, claims["face_lemma_failures"], "face lemma failures")
    assert_equal((1 << U4.nstates) * 4, claims["face_lemma_triples"], "reported face lemma port count")

    universal_pairset = set(universal_pairs)
    mixed_pairs = 0
    triangle_mismatches = 0
    for R in range(1 << U4.nstates):
        cans4, _, _, integral4 = data4[R]
        if not integral4:
            continue
        for h in range(4):
            if not is_mixed(cans4, h):
                continue
            mixed_pairs += 1
            prediction = unbalanced_triangle(data3[hide_forall_rejected(R, 4, h)][0], 3)
            if prediction != ((R, h) in universal_pairset):
                triangle_mismatches += 1
    assert_equal(mixed_pairs, claims["integral_mixed_pairs"], "integral mixed pairs")
    assert_equal(mixed_pairs - len(universal_pairs), claims["integral_mixed_safe"], "integral mixed safe")
    assert_equal(len(universal_pairs), claims["integral_mixed_violating"], "integral mixed violating")
    assert_equal(triangle_mismatches, claims["odd_triangle_classification_mismatches"], "odd-triangle classification mismatches")

    for n, U, data, stable_key, hereditary_key in (
        (3, U3, data3, "n3_stable", "n3_hereditary"),
        (4, U4, data4, "n4_stable", "n4_hereditary"),
    ):
        full = (1 << (1 << n)) - 1
        stable = sum(data[R][3] == data[full & ~R][3] for R in range(full + 1))
        hereditary = [R for R in range(full + 1) if down_closed(R, n)]
        hereditary_bad = [R for R in hereditary if data[R][3] != data[full & ~R][3]]
        assert_equal(stable, claims[stable_key], f"n={n} stable count")
        assert_equal(len(hereditary), claims[hereditary_key], f"n={n} hereditary count")
        assert_equal(len(hereditary_bad), claims["hereditary_instabilities"], f"n={n} hereditary instabilities")

    reachable3 = 0
    nonintegral3 = [R for R in range(1 << U3.nstates) if not data3[R][3]]
    for R in nonintegral3:
        states = [s for s in range(1 << U3.n) if (R >> s) & 1]
        found = False
        for x0 in states:
            for x1 in states:
                if x0 == x1:
                    continue
                parent = lift_pair_to_region(R & ~(1 << x0), R & ~(1 << x1), 3)
                if data4[parent][3]:
                    found = True
                    break
            if found:
                break
        reachable3 += found
    assert_equal(reachable3, claims["n3_nonintegral_reachable"], "n=3 reachable nonintegral count")
    assert_equal(len(nonintegral3), claims["n3_nonintegral_total"], "n=3 nonintegral total")

    integral5 = integral_parent_checker()
    seam_distribution = Counter()
    nonintegral4_reps = [orbit[0] for orbit in orbits4 if not data4[orbit[0]][3]]
    unresolved = []
    for R in nonintegral4_reps:
        states = [s for s in range(1 << U4.n) if (R >> s) & 1]
        good_faces = {k: [] for k in range(5)}
        for k in good_faces:
            for X in itertools.combinations(states, k):
                face = R
                for s in X:
                    face &= ~(1 << s)
                if data4[face][3]:
                    good_faces[k].append((frozenset(X), face))
        found = None
        for seam in range(2, 9):
            if found:
                break
            for s0 in range(1, seam):
                s1 = seam - s0
                if s1 < s0 or s0 > 4 or s1 > 4:
                    continue
                for X0, R0 in good_faces[s0]:
                    for X1, R1 in good_faces[s1]:
                        if X0 & X1:
                            continue
                        if integral5(lift_pair_to_region(R0, R1, 4)):
                            found = seam
                            break
                    if found:
                        break
                if found:
                    break
        if found:
            seam_distribution[str(found)] += 1
        else:
            unresolved.append(R)
    assert_equal(len(nonintegral4_reps), claims["n4_nonintegral_orbits_total"], "n=4 nonintegral orbit total")
    assert_equal(len(nonintegral4_reps) - len(unresolved), claims["n4_nonintegral_orbits_reachable"], "n=4 reachable orbit count")
    assert_equal(dict(sorted(seam_distribution.items())), claims["n4_min_seam_distribution"], "n=4 min seam distribution")

    log("finite census claims ok")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_hashes(packet: dict) -> None:
    for rel, expected in packet["hash_artifacts"].items():
        path = ROOT / rel
        if not path.exists():
            raise AssertionError(f"required hash artifact is absent: {rel}")
        assert_equal(file_sha256(path), expected, f"sha256 {rel}")
        log("hash ok", rel)


def verify_projection_fractional(cert: dict) -> None:
    U4 = Universe(4)
    U3 = Universe(3)
    intervals = [tuple(iv) for iv in cert["upstairs_region_intervals"]]
    R = region_from_intervals(U4, intervals)
    hidden = cert["hidden"]
    down = hide_forall_rejected(R, 4, hidden)
    up_data = region_polytope_data(U4, R)
    down_data = region_polytope_data(U3, down)
    assert_equal(set(up_data[0]), set(intervals), cert["id"] + " upstairs Can")
    assert_equal(up_data[3], cert["upstairs_integral"], cert["id"] + " upstairs integrality")
    assert_equal(set(down_data[0]), set(map(tuple, cert["downstairs_can"])), cert["id"] + " downstream Can")
    assert_equal(down_data[3], cert["downstairs_integral"], cert["id"] + " downstream integrality")
    vertex = tuple(parse_fraction(x) for x in cert["downstairs_vertex"])
    if vertex not in down_data[1]:
        raise AssertionError(f"{cert['id']}: missing downstream vertex {vertex}")
    log("certificate ok", cert["id"])


def verify_complement(cert: dict) -> None:
    U = Universe(cert["n"])
    R = region_from_states(cert["region_states"])
    full = (1 << U.nstates) - 1
    assert_equal(region_polytope_data(U, R)[3], cert["region_integral"], cert["id"] + " R integrality")
    assert_equal(region_polytope_data(U, full & ~R)[3], cert["complement_integral"], cert["id"] + " complement integrality")
    log("certificate ok", cert["id"])


def odd_cycle_region(m: int):
    n, h = m + 1, m
    U = simple_universe(n)
    full = U.full
    intervals = [
        ((1 << 0) | (1 << 1), full & ~(1 << h)),
        ((1 << 2) | (1 << ((2 + 1) % m)) | (1 << h), full),
    ]
    for i in range(m):
        if i in (0, 2):
            continue
        intervals.append(((1 << i) | (1 << ((i + 1) % m)), full))
    return U, intervals, region_from_intervals(U, intervals)


def verify_odd_cycle(cert: dict) -> None:
    half = Fraction(1, 2)
    for m in cert["cycle_lengths"]:
        Uc, expected_cans, Rc = odd_cycle_region(m)
        Uv = simple_universe(m)
        expected_down = tuple(((1 << i) | (1 << ((i + 1) % m)), Uv.full) for i in range(m))
        Rdown = hide_forall_rejected(Rc, m + 1, m)
        cans, _, _, integral = region_polytope_data(Uc, Rc)
        vcans, vverts, _, vintegral = region_polytope_data(Uv, Rdown)
        assert_equal(set(cans), set(expected_cans), f"{cert['id']} m={m} parent Can")
        assert_equal(integral, cert["parent_integral"], f"{cert['id']} m={m} parent integrality")
        assert_equal(set(vcans), set(expected_down), f"{cert['id']} m={m} visible Can")
        assert_equal(vintegral, cert["visible_integral"], f"{cert['id']} m={m} visible integrality")
        if tuple([half] * m) not in vverts:
            raise AssertionError(f"{cert['id']} m={m}: missing all-half vertex")
    log("certificate ok", cert["id"])


def verify_fractional_vertex(cert: dict) -> None:
    U = simple_universe(cert["n"])
    intervals = [tuple(iv) for iv in cert["canonical_intervals"]]
    R = region_from_intervals(U, intervals)
    assert_equal(R, cert["region"], cert["id"] + " region mask")
    cans, verts, dens, integral = region_polytope_data(U, R)
    assert_equal(set(cans), set(intervals), cert["id"] + " Can")
    point = tuple(parse_fraction(x) for x in cert["point"])
    if point not in verts:
        raise AssertionError(f"{cert['id']}: point is not a vertex")
    if integral:
        raise AssertionError(f"{cert['id']}: expected non-integral polytope")
    assert_equal(sorted(dens), cert["spectrum"], cert["id"] + " spectrum")
    rows = hrep_rows(U, intervals)[2 * cert["n"] :]
    active = []
    for row in rows:
        value = Fraction(row[0]) + sum(Fraction(row[i + 1]) * point[i] for i in range(cert["n"]))
        if value == 0:
            active.append(row[1:])
    assert_equal(len(active), cert["n"], cert["id"] + " active row count")
    assert_equal(str(determinant(active)), cert["determinant"], cert["id"] + " determinant")
    assert_equal(lcm_den(point), max(cert["spectrum"]), cert["id"] + " point denominator")
    log("certificate ok", cert["id"])


def verify_b5_summary(packet: dict) -> None:
    path = ROOT / "n5_orbit_census_20260610" / "b5_rep_eval_summary.json"
    if not path.exists():
        raise AssertionError("required B5 generated summary is absent")
    summary = json.loads(path.read_text(encoding="utf-8"))
    claims = packet["claims"]
    assert_equal(summary["complete"], True, "B5 summary complete")
    assert_equal(summary.get("range_coverage_complete"), True, "B5 summary range coverage")
    assert_equal(summary["completed"], claims["burnside_region_orbits"]["5"], "B5 completed reps")
    assert_equal(summary["max_denominator"], claims["b5_max_denominator"], "B5 max denominator")
    assert_equal(summary["denominator_4plus_count"], claims["b5_denominator_4plus_orbits"], "B5 denominator 4+ count")
    assert_equal(summary["spectra"], claims["b5_denominator_spectrum_by_orbit"], "B5 spectrum")
    denom5 = sum(count for key, count in summary["spectra"].items() if "5" in key)
    assert_equal(denom5, claims["b5_denominator_5_orbits"], "B5 denominator 5 count")
    log("B5 summary ok")


def main() -> None:
    packet_path = Path(__file__).with_name("certificates.json")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    verify_hashes(packet)

    for n_raw, expected in packet["claims"]["burnside_region_orbits"].items():
        n = int(n_raw)
        assert_equal(burnside_orbit_count(n), expected, f"B{n} Burnside orbit count")
        log("Burnside ok", f"n={n}", expected)

    assert_equal(
        b4_orbit_denominator_spectrum(),
        packet["claims"]["b4_denominator_spectrum_by_orbit"],
        "B4 denominator spectrum",
    )
    log("B4 denominator spectrum ok")

    verify_finite_census_claims(packet)

    for cert in packet["certificates"]:
        if cert["type"] == "projection_fractional":
            verify_projection_fractional(cert)
        elif cert["type"] == "complement_integrality":
            verify_complement(cert)
        elif cert["type"] == "odd_cycle_seam_family_instances":
            verify_odd_cycle(cert)
        elif cert["type"] == "fractional_vertex_determinant":
            verify_fractional_vertex(cert)
        else:
            raise AssertionError(f"unknown certificate type {cert['type']}")

    verify_b5_summary(packet)
    log("PASS compact certificate packet")


if __name__ == "__main__":
    main()
