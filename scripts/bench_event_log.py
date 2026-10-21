"""Measure parse + DFG latency (and optional peak RSS) for synthetic logs.

Offline benchmarks only. Uses ``generate_benchmark_cases`` (no QX probes, no API
case-count caps). Does not change the documented ``generate_cases(800)`` contract.

Example:
  uv run python scripts/bench_event_log.py --cases 10000 --reps 5
  uv run python scripts/bench_event_log.py --cases 100000 --reps 3
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hpm.domain.metrics import directly_follows  # noqa: E402
from hpm.domain.parsing import FieldMapping, parse_csv  # noqa: E402
from hpm.domain.seedgen import generate_benchmark_cases, render_csv  # noqa: E402
from hpm.services.frames import frame_from_parsed  # noqa: E402

MAPPING = FieldMapping(
    case_id="case_id",
    activity="activity",
    timestamp="timestamp",
    resource="resource",
    role="role",
    channel="channel",
    outcome="outcome",
    cost="cost",
    job_family="job_family",
)


def _stats(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)
    return {
        "n": len(ordered),
        "min_s": ordered[0],
        "median_s": statistics.median(ordered),
        "mean_s": statistics.mean(ordered),
        "max_s": ordered[-1],
        "stdev_s": statistics.stdev(ordered) if len(ordered) > 1 else 0.0,
    }


def run_once(cases: int, seed: int, *, track_memory: bool) -> dict[str, float | int]:
    csv_text = render_csv(generate_benchmark_cases(cases, seed), inject_quality_rows=False)
    if track_memory:
        tracemalloc.start()
    t0 = time.perf_counter()
    events = parse_csv(csv_text, MAPPING, "Europe/Berlin")
    parse_s = time.perf_counter() - t0
    frame = frame_from_parsed(events)
    t1 = time.perf_counter()
    graph = directly_follows(frame, min_case_ratio=0.0)
    dfg_s = time.perf_counter() - t1
    peak_mib = None
    if track_memory:
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_mib = peak / (1024 * 1024)
    return {
        "csv_chars": len(csv_text),
        "events": len(events),
        "cases": int(graph["total_cases"]),
        "edges": int(graph["edges_before_filter"]),
        "parse_s": parse_s,
        "dfg_s": dfg_s,
        "peak_tracemalloc_mib": peak_mib if peak_mib is not None else -1.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--reps", type=int, default=5)
    parser.add_argument("--track-memory", action="store_true")
    args = parser.parse_args()

    for _ in range(max(0, args.warmup)):
        run_once(args.cases, args.seed, track_memory=False)

    rows = [
        run_once(args.cases, args.seed, track_memory=args.track_memory) for _ in range(args.reps)
    ]
    payload = {
        "cases_requested": args.cases,
        "seed": args.seed,
        "warmup": args.warmup,
        "reps": args.reps,
        "track_memory": args.track_memory,
        "qx_injected": False,
        "parse": _stats([float(row["parse_s"]) for row in rows]),
        "dfg": _stats([float(row["dfg_s"]) for row in rows]),
        "last_run": rows[-1],
        "peak_tracemalloc_mib": _stats(
            [float(row["peak_tracemalloc_mib"]) for row in rows if float(row["peak_tracemalloc_mib"]) >= 0]
        )
        if args.track_memory
        else None,
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
