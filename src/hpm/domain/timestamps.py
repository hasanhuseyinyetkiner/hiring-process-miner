"""DST-safe conversion of local timestamps to naive UTC."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def timezone_exists(name: str) -> bool:
    try:
        ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return False
    return True


def local_naive_to_utc(naive: datetime, timezone_name: str) -> tuple[datetime | None, str | None]:
    """Convert a naive local datetime to naive UTC.

    Nonexistent wall times are classified before ambiguous ones. On a spring-forward
    gap, fold offsets can differ and the wall time also fails to round-trip; that
    record is nonexistent, not ambiguous. Ambiguous fall-back times round-trip and
    have two distinct UTC instants. The default policy flags both and returns no
    instant, so they cannot enter canonical ordering.
    """
    if naive.tzinfo is not None:
        raise ValueError("local_naive_to_utc expects a naive datetime")
    zone = ZoneInfo(timezone_name)
    fold0 = naive.replace(tzinfo=zone, fold=0)
    roundtrip = fold0.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
    if roundtrip != naive:
        return None, "nonexistent_local_time"
    fold1 = naive.replace(tzinfo=zone, fold=1)
    if fold0.utcoffset() != fold1.utcoffset():
        return None, "ambiguous_local_time"
    return fold0.astimezone(UTC).replace(tzinfo=None), None


def aware_to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("aware_to_utc_naive expects an aware datetime")
    return value.astimezone(UTC).replace(tzinfo=None)
