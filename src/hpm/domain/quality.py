"""Data-quality counts. Missing-field counters can overlap; exclusions do not."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from hpm.domain.constants import DUPLICATE_RULE, PRIVACY_NOTICE


def _raw_was_aware(raw: str | None) -> bool:
    if not raw:
        return False
    text = raw.strip()
    if text.endswith("Z"):
        return True
    return len(text) >= 6 and text[-3] == ":" and text[-6] in "+-"


def quality_report(events: Iterable[object], *, timezone: str) -> dict[str, object]:
    rows = list(events)
    exclusion_counts: Counter[str] = Counter()
    missing_case_id = 0
    missing_activity = 0
    missing_timestamp = 0
    aware = 0
    naive = 0
    eligible_cases: set[str] = set()
    issues: list[dict[str, object]] = []
    for event in rows:
        case_id = event.case_id
        activity = event.activity
        raw = event.raw_timestamp
        if not case_id:
            missing_case_id += 1
        if not activity:
            missing_activity += 1
        if not raw:
            missing_timestamp += 1
        elif _raw_was_aware(raw):
            aware += 1
        else:
            naive += 1
        reason = event.exclusion_reason
        if reason:
            exclusion_counts[reason] += 1
            if len(issues) < 50:
                issues.append(
                    {
                        "source_row": int(event.source_row),
                        "case_id": case_id,
                        "activity": activity,
                        "raw_timestamp": raw,
                        "exclusion_reason": reason,
                        "warning": event.warning,
                    }
                )
        elif case_id:
            eligible_cases.add(str(case_id))
            if event.warning and len(issues) < 50:
                issues.append(
                    {
                        "source_row": int(event.source_row),
                        "case_id": case_id,
                        "activity": activity,
                        "raw_timestamp": raw,
                        "exclusion_reason": None,
                        "warning": event.warning,
                    }
                )
    warnings: list[str] = []
    if exclusion_counts["ambiguous_local_time"] or exclusion_counts["nonexistent_local_time"]:
        warnings.append(
            f"Naive timestamps in {timezone} that fall in a DST gap or overlap were flagged "
            "and excluded from analytics because they have no single UTC instant."
        )
    if aware and naive:
        warnings.append(
            "The file mixes offset timestamps and naive timestamps. Offset values were "
            f"converted to UTC directly. Naive values were interpreted in {timezone}."
        )
    if exclusion_counts["duplicate"]:
        warnings.append(DUPLICATE_RULE)
    eligible = sum(1 for event in rows if event.exclusion_reason is None)
    return {
        "row_count": len(rows),
        "eligible_event_count": eligible,
        "excluded_event_count": len(rows) - eligible,
        "unique_cases": len(eligible_cases),
        "missing_case_id": missing_case_id,
        "missing_activity": missing_activity,
        "missing_timestamp": missing_timestamp,
        "parse_failures": int(exclusion_counts["timestamp_parse_failure"]),
        "ambiguous_timestamps": int(exclusion_counts["ambiguous_local_time"]),
        "nonexistent_timestamps": int(exclusion_counts["nonexistent_local_time"]),
        "duplicate_count": int(exclusion_counts["duplicate"]),
        "invalid_cost_warnings": sum(1 for event in rows if event.warning == "invalid_cost"),
        "exclusion_breakdown": dict(sorted(exclusion_counts.items())),
        "timezone": timezone,
        "timezone_warnings": warnings,
        "aware_timestamps": aware,
        "naive_timestamps": naive,
        "duplicate_rule": DUPLICATE_RULE,
        "privacy_notice": PRIVACY_NOTICE,
        "eligible_definition": (
            "A row is analytics-eligible when it has a case id, an activity, and one "
            "unambiguous UTC timestamp, and it is not a documented duplicate."
        ),
        "issue_sample": issues,
    }
