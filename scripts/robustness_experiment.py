"""Reproduce the synthetic timestamp-noise experiment described in docs/EVALUATION.md."""

from datetime import UTC, datetime, timedelta

import numpy as np

from hpm.domain.metrics import insights, performance
from hpm.domain.parsing import FieldMapping, parse_csv
from hpm.domain.seedgen import generate_cases, render_csv
from hpm.services.frames import frame_from_parsed

PLANTED = ("Interview Scheduled", "Interview Completed")
NOISE_HOURS = (0, 24, 72, 168)
SEEDS = range(10)
MAPPING = FieldMapping(case_id="case_id", activity="activity", timestamp="timestamp")


def run_one(seed: int, noise_hours: int, n_cases: int = 500) -> dict:
    cases = generate_cases(n_cases, seed)
    # The same per-event random draws are used at every noise level for each seed.
    rng = np.random.default_rng(seed + 10000)
    for case in cases:
        for event in case:
            timestamp = datetime.fromisoformat(event["timestamp"]).astimezone(UTC)
            jitter = float(rng.uniform(-noise_hours, noise_hours))
            event["timestamp"] = (timestamp + timedelta(hours=jitter)).isoformat()
    events = parse_csv(render_csv(cases, inject_quality_rows=False), MAPPING, "Europe/Berlin")
    frame = frame_from_parsed(events)
    card = insights(frame)["cards"][0]
    edges = performance(frame)["transitions"]
    planted = next((edge for edge in edges if (edge["source"], edge["target"]) == PLANTED), None)
    return {
        "seed": seed,
        "noise_hours": noise_hours,
        "selected": (card["source_activity"], card["target_activity"]),
        "eligible_edges": sum(edge["frequency"] >= 30 for edge in edges),
        "planted_frequency": planted["frequency"] if planted else 0,
        "planted_median_days": planted["median_delay_seconds"] / 86400 if planted else None,
    }


def main() -> None:
    for noise in NOISE_HOURS:
        results = [run_one(seed, noise) for seed in SEEDS]
        hits = sum(result["selected"] == PLANTED for result in results)
        eligible = [result["eligible_edges"] for result in results]
        frequencies = [result["planted_frequency"] for result in results]
        medians = [result["planted_median_days"] for result in results]
        print(f"+/-{noise}h: {hits}/{len(results)} hits; eligible edges {min(eligible)}-{max(eligible)}; "
              f"planted observations {min(frequencies)}-{max(frequencies)}; "
              f"planted median {min(medians):.2f}-{max(medians):.2f} days")
        for result in results:
            if result["selected"] != PLANTED:
                print(f"  seed {result['seed']}: selected {result['selected']}")


if __name__ == "__main__":
    main()
