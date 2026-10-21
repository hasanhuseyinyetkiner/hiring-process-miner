"""Distribution helpers. Mean, median, p90, and p95 stay explicit so tests can recompute them."""

from __future__ import annotations

import numpy as np

from hpm.domain.constants import MEAN_METHOD, MEDIAN_METHOD, P90_METHOD, P95_METHOD


def distribution(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "p90": None,
            "p95": None,
            "mean_method": MEAN_METHOD,
            "median_method": MEDIAN_METHOD,
            "p90_method": P90_METHOD,
            "p95_method": P95_METHOD,
        }
    array = np.asarray(values, dtype=float)
    return {
        "n": int(array.size),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "p90": float(np.percentile(array, 90, method="linear")),
        "p95": float(np.percentile(array, 95, method="linear")),
        "mean_method": MEAN_METHOD,
        "median_method": MEDIAN_METHOD,
        "p90_method": P90_METHOD,
        "p95_method": P95_METHOD,
    }
