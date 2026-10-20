import sys

import pytest


def test_importing_core_does_not_import_pm4py() -> None:
    sys.modules.pop("pm4py", None)
    import hpm.domain.metrics  # noqa: F401
    import hpm.pm4py_adapter as adapter

    assert "pm4py" not in sys.modules
    assert adapter.pm4py_installed() is False or adapter.pm4py_installed() is True
    assert "pm4py" not in sys.modules


def test_pm4py_dfg_edge_counts_match_pandas() -> None:
    pytest.importorskip("pm4py")
    from datetime import datetime

    from tests.helpers import frame

    from hpm.domain.metrics import directly_follows
    from hpm.pm4py_adapter import dfg_frequency

    stamp = datetime(2026, 1, 1, 0, 0, 0)
    data = frame(
        [
            {"case_id": "Z", "activity": "Screened", "timestamp": stamp, "source_row": 2},
            {"case_id": "Z", "activity": "Applied", "timestamp": stamp, "source_row": 1},
            {
                "case_id": "Z",
                "activity": "Hired",
                "timestamp": datetime(2026, 1, 3),
                "source_row": 3,
            },
        ]
    )
    pandas_edges = {
        (edge["source"], edge["target"]): edge["frequency"]
        for edge in directly_follows(data)["edges"]
    }
    assert pandas_edges == dfg_frequency(data)
    assert pandas_edges[("Applied", "Screened")] == 1
    assert pandas_edges[("Screened", "Hired")] == 1
