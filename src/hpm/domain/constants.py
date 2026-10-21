"""Shared vocabulary for analytics, the API, and the methodology page."""

ORDERING_CONTRACT = "utc_timestamp_then_source_row"
ORDERING_DESCRIPTION = (
    "Events are ordered by UTC timestamp ascending, then by original source row number "
    "ascending. Every analytics function sorts with this contract itself; callers are "
    "not trusted to pre-sort."
)

TERMINAL_ACTIVITIES = frozenset({"Hired", "Rejected", "Withdrawn"})
HAPPY_PATH = (
    "Applied",
    "Screened",
    "Interview Scheduled",
    "Interview Completed",
    "Offer",
    "Hired",
)
EXIT_ACTIVITIES = ("Rejected", "Withdrawn")

# Reference hiring flow. Skips, self-loops, and repeated interviews are deviations
# so conformance can see them. The model is editable per dataset.
DEFAULT_ALLOWED_TRANSITIONS: tuple[tuple[str, str], ...] = (
    ("Applied", "Screened"),
    ("Applied", "Rejected"),
    ("Applied", "Withdrawn"),
    ("Screened", "Interview Scheduled"),
    ("Screened", "Rejected"),
    ("Screened", "Withdrawn"),
    ("Interview Scheduled", "Interview Completed"),
    ("Interview Scheduled", "Rejected"),
    ("Interview Scheduled", "Withdrawn"),
    ("Interview Completed", "Offer"),
    ("Interview Completed", "Rejected"),
    ("Interview Completed", "Withdrawn"),
    ("Offer", "Hired"),
    ("Offer", "Rejected"),
    ("Offer", "Withdrawn"),
)

MIN_OBSERVATIONS = 30
DUPLICATE_RULE = (
    "A later row is a duplicate when it matches an earlier eligible row on case_id, "
    "activity, UTC timestamp, resource, role, channel, outcome, cost, and job_family. "
    "The smallest source_row is kept. The same activity at a different timestamp is a "
    "repeat, not a duplicate, and is retained."
)
DELAY_DEFINITION = (
    "Transition delay is the elapsed UTC time between two consecutive events in a case "
    "after canonical ordering. Each event has one timestamp, so this is not processing "
    "time and it is not labeled as active work."
)
CYCLE_TIME_DEFINITION = (
    "Case cycle time is the UTC elapsed time from the earliest event in the case to the "
    "earliest terminal event (Hired, Rejected, or Withdrawn). Cases with no terminal "
    "event are ongoing and are excluded from the cycle-time distribution. A negative "
    "span is discarded and counted, not clamped."
)
FUNNEL_DENOMINATOR = (
    "Distinct case_id values among analytics-eligible events after filters. A case "
    "reaches a stage when at least one remaining event has that activity. Funnel "
    "counts are presence-based, not order-based."
)
DROP_OFF_DEFINITION = (
    "Cases that reached the previous happy-path stage but not this stage. This is a "
    "set difference of case ids, not a claim that the case exited at that step."
)
AS_OF_DEFINITION = (
    "Active-case aging uses an explicit as_of instant. When as_of is omitted it is the "
    "latest event timestamp in the filtered log, so the figure is reproducible and is "
    "not the wall clock."
)
CAUSAL_CAUTION = (
    "This describes the recorded event log only. It is not a causal root cause, and it "
    "is not a recommendation to reject or advance a candidate."
)
PRIVACY_NOTICE = (
    "Do not upload candidate names, email addresses, phone numbers, resumes, or "
    "demographic data. Case identifiers should already be anonymized. This local demo "
    "has no authentication and is only for synthetic or already anonymized logs."
)
PROCESSING_TIME_REASON = (
    "Each event has one timestamp, so transition delay is not labeled as processing time."
)
MEAN_METHOD = "numpy.mean (arithmetic mean of the sample)"
MEDIAN_METHOD = "numpy.median (average of the two central values when the count is even)"
P90_METHOD = "numpy.percentile(values, 90, method='linear')"
P95_METHOD = "numpy.percentile(values, 95, method='linear')"
TIMESTAMP_OUTLIER_POLICY = (
    "Timestamp outliers are handled at parse time, not by clamping delays. "
    "Ambiguous DST fall-back and nonexistent spring-forward local times are excluded "
    "(no single UTC instant). Unparseable timestamps are excluded. Aware offsets convert "
    "directly to UTC; naive stamps use the declared IANA timezone. Extreme but parseable "
    "instants remain eligible — analytics do not drop far-past or far-future values. "
    "Negative elapsed spans are discarded and counted, never clamped to zero."
)
PM4PY_UNAVAILABLE = (
    "Token replay and alignment conformance need the optional pm4py extra "
    "(AGPL-3.0-or-later). It is not installed. The rule-based conformance result does "
    "not use PM4Py."
)
PM4PY_NOT_USED = (
    "PM4Py is installed, but this response is the pandas/NumPy rule-based conformance "
    "result. Token replay is not run by this endpoint."
)

SYNTHETIC_CASE_MIN = 500
SYNTHETIC_CASE_MAX = 2000
SYNTHETIC_TIMEZONE = "Europe/Berlin"
DEMO_BANNER_TEXT = "Local demo · synthetic data"
