from datetime import datetime

from hpm.domain.timestamps import local_naive_to_utc


def test_berlin_fall_back_is_ambiguous_and_excluded() -> None:
    instant, reason = local_naive_to_utc(datetime(2026, 10, 25, 2, 30), "Europe/Berlin")
    assert instant is None
    assert reason == "ambiguous_local_time"


def test_berlin_spring_forward_is_nonexistent_and_excluded() -> None:
    instant, reason = local_naive_to_utc(datetime(2026, 3, 29, 2, 30), "Europe/Berlin")
    assert instant is None
    assert reason == "nonexistent_local_time"


def test_berlin_summer_and_winter_controls_convert() -> None:
    summer, summer_reason = local_naive_to_utc(datetime(2026, 6, 15, 12, 0), "Europe/Berlin")
    assert summer_reason is None
    assert summer == datetime(2026, 6, 15, 10, 0)
    winter, winter_reason = local_naive_to_utc(datetime(2026, 1, 15, 10, 30), "Europe/Berlin")
    assert winter_reason is None
    assert winter == datetime(2026, 1, 15, 9, 30)
    after_gap, gap_reason = local_naive_to_utc(datetime(2026, 3, 29, 3, 30), "Europe/Berlin")
    assert gap_reason is None
    assert after_gap == datetime(2026, 3, 29, 1, 30)
    after_fold, fold_reason = local_naive_to_utc(datetime(2026, 10, 25, 3, 30), "Europe/Berlin")
    assert fold_reason is None
    assert after_fold == datetime(2026, 10, 25, 2, 30)
