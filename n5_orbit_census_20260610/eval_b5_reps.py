#!/usr/bin/env python3
"""Resumable exact evaluation of B5 orbit representatives.

Input is the little-endian uint32 representative file produced by the Rust
orbit-census helper. Output is append-only JSONL, one completed batch per line,
so interrupted runs can resume without redoing finished batches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "computational_supplement_20260610"))

from sag import (  # noqa: E402
    Universe,
    all_intervals,
    interval_statemask,
    region_polytope_data,
)


T0 = time.time()


def log(*parts: object) -> None:
    print(f"[{time.time() - T0:7.1f}s]", *parts, flush=True)


def simple_universe(n: int):
    """Construct only the interval data needed by region_polytope_data."""
    U = Universe.__new__(Universe)
    U.n = n
    U.full = (1 << n) - 1
    U.nstates = 1 << n
    U.intervals = all_intervals(n)
    U.smask = {iv: interval_statemask(*iv, n) for iv in U.intervals}
    return U


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_reps(path: Path) -> list[int]:
    data = path.read_bytes()
    if len(data) % 4:
        raise ValueError(f"{path} length is not divisible by 4")
    return [int.from_bytes(data[i : i + 4], "little") for i in range(0, len(data), 4)]


def spectrum_key(dens: Iterable[int]) -> tuple[int, ...]:
    return tuple(sorted(dens))


def lcm_den(vertex) -> int:
    d = 1
    for x in vertex:
        d = math.lcm(d, x.denominator)
    return d


def evaluate_batch(args: tuple[int, list[int], int]) -> dict:
    start, reps, examples_per_batch = args
    U5 = simple_universe(5)
    spectra: Counter[str] = Counter()
    max_denominator = 1
    integral_count = 0
    nonintegral_count = 0
    denominator_4plus_count = 0
    examples = []
    denominator_4plus_examples = []
    denominator_5_examples = []

    for offset, R in enumerate(reps):
        cans, verts, dens, integral = region_polytope_data(U5, R)
        spectrum = spectrum_key(dens)
        local_max = max(spectrum or (1,))
        spectra[str(spectrum)] += 1
        max_denominator = max(max_denominator, local_max)
        if integral:
            integral_count += 1
        else:
            nonintegral_count += 1
        if local_max >= 4:
            denominator_4plus_count += 1

        example = None
        if not integral or local_max >= 4:
            high_vertices = [str(v) for v in verts if lcm_den(v) >= 4][:3]
            example = {
                "index": start + offset,
                "R": R,
                "states": R.bit_count(),
                "canonical_count": len(cans),
                "spectrum": str(spectrum),
                "integral": integral,
                "denominator_4plus_vertices": high_vertices,
            }
        if example is not None and len(examples) < examples_per_batch:
            examples.append(example)
        if example is not None and local_max >= 4 and len(denominator_4plus_examples) < examples_per_batch:
            denominator_4plus_examples.append(example)
        if example is not None and local_max >= 5 and len(denominator_5_examples) < examples_per_batch:
            denominator_5_examples.append(example)

    return {
        "event": "batch",
        "start": start,
        "stop": start + len(reps),
        "count": len(reps),
        "spectra": dict(sorted(spectra.items())),
        "max_denominator": max_denominator,
        "integral_count": integral_count,
        "nonintegral_count": nonintegral_count,
        "denominator_4plus_count": denominator_4plus_count,
        "examples": examples,
        "denominator_4plus_examples": denominator_4plus_examples,
        "denominator_5_examples": denominator_5_examples,
    }


def _merge_ranges(ranges: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, stop in sorted(ranges):
        if start >= stop:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], stop))
        else:
            merged.append((start, stop))
    return merged


def _range_covered(merged_ranges: list[tuple[int, int]], start: int, stop: int) -> bool:
    return any(r_start <= start and stop <= r_stop for r_start, r_stop in merged_ranges)


def _uncovered_segments(
    start: int, stop: int, merged_ranges: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    out = []
    cursor = start
    for r_start, r_stop in merged_ranges:
        if r_stop <= cursor:
            continue
        if r_start >= stop:
            break
        if cursor < r_start:
            out.append((cursor, min(r_start, stop)))
        cursor = max(cursor, r_stop)
        if cursor >= stop:
            break
    if cursor < stop:
        out.append((cursor, stop))
    return out


def completed_ranges(path: Path, rep_sha256: str) -> list[tuple[int, int]]:
    done: list[tuple[int, int]] = []
    if not path.exists():
        return done
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("event") != "batch":
                continue
            if record.get("rep_file_sha256") != rep_sha256:
                continue
            done.append((int(record["start"]), int(record["stop"])))
    return _merge_ranges(done)


def aggregate_batches(path: Path, rep_sha256: str, expected: int) -> dict:
    spectra: Counter[str] = Counter()
    max_denominator = 1
    integral_count = 0
    nonintegral_count = 0
    denominator_4plus_count = 0
    completed = 0
    batches = 0
    examples = []
    denominator_4plus_examples = []
    denominator_5_examples = []
    seen_ranges: set[tuple[int, int]] = set()

    batch_records = []
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("event") != "batch":
                    continue
                if record.get("rep_file_sha256") != rep_sha256:
                    continue
                batch_range = (int(record["start"]), int(record["stop"]))
                if batch_range in seen_ranges:
                    continue
                seen_ranges.add(batch_range)
                batch_records.append((batch_range, record))

    last_stop = 0
    for (start, stop), record in sorted(batch_records):
        if start < last_stop:
            raise ValueError(
                f"overlapping batch ranges in {path}: previous stop {last_stop}, "
                f"next range {(start, stop)}"
            )
        last_stop = stop
        batches += 1
        completed += int(record["count"])
        spectra.update(record["spectra"])
        max_denominator = max(max_denominator, int(record["max_denominator"]))
        integral_count += int(record["integral_count"])
        nonintegral_count += int(record["nonintegral_count"])
        denominator_4plus_count += int(record["denominator_4plus_count"])
        examples.extend(record.get("examples", []))
        denominator_4plus_examples.extend(record.get("denominator_4plus_examples", []))
        denominator_5_examples.extend(record.get("denominator_5_examples", []))

    return {
        "event": "summary",
        "rep_file_sha256": rep_sha256,
        "expected": expected,
        "completed": completed,
        "complete": completed == expected,
        "range_coverage_complete": _merge_ranges(seen_ranges) == [(0, expected)],
        "batches": batches,
        "spectra": dict(sorted(spectra.items())),
        "max_denominator": max_denominator,
        "integral_count": integral_count,
        "nonintegral_count": nonintegral_count,
        "denominator_4plus_count": denominator_4plus_count,
        "examples": examples[:25],
        "denominator_4plus_examples": denominator_4plus_examples[:25],
        "denominator_5_examples": denominator_5_examples[:25],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reps", type=Path, help="little-endian uint32 reps file")
    parser.add_argument("--out-jsonl", type=Path, default=Path("b5_rep_eval_batches.jsonl"))
    parser.add_argument("--summary", type=Path, default=Path("b5_rep_eval_summary.json"))
    parser.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) // 2)))
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--limit", type=int, default=None, help="evaluate only the first N reps")
    parser.add_argument("--examples-per-batch", type=int, default=3)
    args = parser.parse_args()

    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")
    if args.workers <= 0:
        raise SystemExit("--workers must be positive")

    rep_sha = file_sha256(args.reps)
    reps = read_reps(args.reps)
    if args.limit is not None:
        reps = reps[: args.limit]

    expected = len(reps)
    done = completed_ranges(args.out_jsonl, rep_sha)
    batches = []
    for start in range(0, expected, args.batch_size):
        stop = min(start + args.batch_size, expected)
        if _range_covered(done, start, stop):
            continue
        for seg_start, seg_stop in _uncovered_segments(start, stop, done):
            batches.append((seg_start, reps[seg_start:seg_stop], args.examples_per_batch))

    log(
        "loaded reps",
        expected,
        "sha256",
        rep_sha,
        "completed batches",
        len(done),
        "remaining",
        len(batches),
    )

    args.out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.out_jsonl.open("a", encoding="utf-8") as out:
        if batches:
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                futures = [pool.submit(evaluate_batch, batch) for batch in batches]
                for k, fut in enumerate(as_completed(futures), 1):
                    record = fut.result()
                    record["rep_file"] = str(args.reps)
                    record["rep_file_sha256"] = rep_sha
                    out.write(json.dumps(record, sort_keys=True) + "\n")
                    out.flush()
                    os.fsync(out.fileno())
                    if k % max(1, min(10, len(futures))) == 0 or k == len(futures):
                        log("completed new batches", k, "/", len(futures))

    summary = aggregate_batches(args.out_jsonl, rep_sha, expected)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    log("wrote", args.summary, "complete", summary["complete"], "completed", summary["completed"])


if __name__ == "__main__":
    main()
