"""Deterministic synthetic hiring log with a built-in interview-scheduling wait."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from hpm.domain.constants import (
    SYNTHETIC_CASE_MAX,
    SYNTHETIC_CASE_MIN,
    SYNTHETIC_TIMEZONE,
    TERMINAL_ACTIVITIES,
)

COLUMNS = (
    "case_id",
    "activity",
    "timestamp",
    "resource",
    "role",
    "channel",
    "outcome",
    "cost",
    "job_family",
)
COST = {
    "Applied": "0",
    "Screened": "25",
    "Interview Scheduled": "15",
    "Interview Completed": "120",
    "Offer": "0",
    "Hired": "0",
    "Rejected": "0",
    "Withdrawn": "0",
}
SHORT_WAIT = (4.0, 72.0)
LONG_WAIT = (240.0, 480.0)


def generate_cases(n_cases: int, seed: int) -> list[list[dict[str, str]]]:
    """Build cases whose Interview Scheduled → Interview Completed waits are long.

    Short transitions are drawn from Uniform(4, 72) hours. The interview-scheduling
    wait is drawn from Uniform(240, 480) hours. That separation is by construction
    in this synthetic generator; it is not an observation about a real employer.
    """
    if n_cases < SYNTHETIC_CASE_MIN or n_cases > SYNTHETIC_CASE_MAX:
        raise ValueError(
            f"Synthetic logs must contain between {SYNTHETIC_CASE_MIN} and "
            f"{SYNTHETIC_CASE_MAX} cases"
        )
    return _generate_cases(n_cases, seed)


def generate_benchmark_cases(n_cases: int, seed: int) -> list[list[dict[str, str]]]:
    """Offline performance fixtures only. Not exposed by the import API.

    Does not inject QX probe rows. Callers must not use this to inflate the
    documented ``generate_cases(800)`` eligible-case contract.
    """
    if n_cases < 1:
        raise ValueError("Benchmark case count must be at least 1")
    return _generate_cases(n_cases, seed)


def _generate_cases(n_cases: int, seed: int) -> list[list[dict[str, str]]]:
    rng = np.random.default_rng(seed)
    zone = ZoneInfo(SYNTHETIC_TIMEZONE)
    origin = datetime(2026, 1, 6, 10, 30, tzinfo=zone)
    channels = ("careers_page", "referral", "agency", "internal")
    families = ("engineering", "design", "sales", "operations")
    cases: list[list[dict[str, str]]] = []

    for index in range(1, n_cases + 1):
        case_id = f"C{index:04d}"
        channel = channels[int(rng.integers(0, len(channels)))]
        family = families[int(rng.integers(0, len(families)))]
        cursor = origin + timedelta(days=int(rng.integers(0, 160)), hours=int(rng.integers(0, 8)))
        rows: list[dict[str, str]] = []

        def add(activity: str, role: str, outcome: str = "") -> None:
            nonlocal cursor
            rows.append(
                {
                    "case_id": case_id,
                    "activity": activity,
                    "timestamp": cursor.isoformat(),
                    "resource": f"{role}-{int(rng.integers(1, 6))}",
                    "role": role,
                    "channel": channel,
                    "outcome": outcome,
                    "cost": COST[activity],
                    "job_family": family,
                }
            )

        def advance(long_wait: bool) -> None:
            nonlocal cursor
            low, high = LONG_WAIT if long_wait else SHORT_WAIT
            cursor = cursor + timedelta(hours=float(rng.uniform(low, high)))

        add("Applied", "coordinator")
        gate = float(rng.random())
        if gate < 0.07:
            advance(False)
            add("Withdrawn", "coordinator", "Withdrawn")
            cases.append(rows)
            continue
        if gate < 0.15:
            advance(False)
            add("Rejected", "recruiter", "Rejected")
            cases.append(rows)
            continue
        if float(rng.random()) >= 0.05:
            advance(False)
            add("Screened", "recruiter")
            if float(rng.random()) < 0.02:
                advance(False)
                add("Screened", "recruiter")
            after_screen = float(rng.random())
            if after_screen < 0.10:
                advance(False)
                add("Withdrawn", "coordinator", "Withdrawn")
                cases.append(rows)
                continue
            if after_screen < 0.22:
                advance(False)
                add("Rejected", "recruiter", "Rejected")
                cases.append(rows)
                continue
        advance(False)
        add("Interview Scheduled", "coordinator")
        after_schedule = float(rng.random())
        if after_schedule < 0.06:
            advance(False)
            add("Withdrawn", "coordinator", "Withdrawn")
            cases.append(rows)
            continue
        if after_schedule < 0.10:
            advance(False)
            add("Rejected", "recruiter", "Rejected")
            cases.append(rows)
            continue
        advance(True)
        add("Interview Completed", "interviewer")
        if float(rng.random()) < 0.18:
            advance(False)
            add("Interview Scheduled", "coordinator")
            advance(True)
            add("Interview Completed", "interviewer")
        after_interview = float(rng.random())
        if after_interview < 0.10:
            advance(False)
            add("Withdrawn", "coordinator", "Withdrawn")
            cases.append(rows)
            continue
        if after_interview < 0.25:
            advance(False)
            add("Rejected", "recruiter", "Rejected")
            cases.append(rows)
            continue
        advance(False)
        add("Offer", "hiring_manager")
        advance(False)
        decision = float(rng.random())
        if decision < 0.20:
            add("Rejected", "hiring_manager", "Rejected")
        elif decision < 0.35:
            add("Withdrawn", "coordinator", "Withdrawn")
        else:
            add("Hired", "hiring_manager", "Hired")
        cases.append(rows)

    for rows in cases:
        if rows[-1]["activity"] in TERMINAL_ACTIVITIES and float(rng.random()) < 0.08:
            rows.pop()
    return cases


def render_csv(cases: list[list[dict[str, str]]], *, inject_quality_rows: bool = True) -> str:
    flat = [row for case in cases for row in case]
    if inject_quality_rows and flat:
        flat.append(dict(flat[0]))
        flat.extend(
            [
                {
                    "case_id": "",
                    "activity": "Applied",
                    "timestamp": "2026-01-08T10:00:00+01:00",
                    "resource": "",
                    "role": "",
                    "channel": "",
                    "outcome": "",
                    "cost": "",
                    "job_family": "",
                },
                {
                    "case_id": "QX1",
                    "activity": "",
                    "timestamp": "2026-01-08T10:00:00+01:00",
                    "resource": "",
                    "role": "",
                    "channel": "",
                    "outcome": "",
                    "cost": "",
                    "job_family": "",
                },
                {
                    "case_id": "QX2",
                    "activity": "Applied",
                    "timestamp": "not-a-date",
                    "resource": "",
                    "role": "",
                    "channel": "",
                    "outcome": "",
                    "cost": "",
                    "job_family": "",
                },
                {
                    "case_id": "QX3",
                    "activity": "Applied",
                    "timestamp": "2026-10-25 02:30",
                    "resource": "",
                    "role": "",
                    "channel": "",
                    "outcome": "",
                    "cost": "nope",
                    "job_family": "",
                },
                {
                    "case_id": "QX4",
                    "activity": "Applied",
                    "timestamp": "2026-03-29 02:30",
                    "resource": "",
                    "role": "",
                    "channel": "",
                    "outcome": "",
                    "cost": "",
                    "job_family": "",
                },
            ]
        )
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(flat)
    return buffer.getvalue()


def render_seed_csv(n_cases: int = 800, seed: int = 42) -> str:
    return render_csv(generate_cases(n_cases, seed), inject_quality_rows=True)
