"""Distribution helpers. Median and p90 stay explicit so tests can recompute them."""

from __future__ import annotations

import numpy as np

from hpm.domain.constants import MEDIAN_METHOD, P90_METHOD


def distribution(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "n": 0,
            "median": None,
            "p90": None,
            "median_method": MEDIAN_METHOD,
            "p90_method": P90_METHOD,
        }
    array = np.asarray(values, dtype=float)
    return {
        "n": int(array.size),
        "median": float(np.median(array)),
        "p90": float(np.percentile(array, 90, method="linear")),
        "median_method": MEDIAN_METHOD,
        "p90_method": P90_METHOD,
    }
