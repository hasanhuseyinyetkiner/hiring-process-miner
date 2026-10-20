"""CSV and HTML exports. Numbers come from the same analytics functions as the API."""

from __future__ import annotations

import csv
import html
import io

from hpm.domain.constants import CAUSAL_CAUTION, ORDERING_DESCRIPTION, PRIVACY_NOTICE
from hpm.models import Dataset


def _cell(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    text = "" if value is None else str(value)
    if text[:1] in "=@+":
        return "'" + text
    if text.startswith("-") and _not_number(text):
        return "'" + text
    return text


def _not_number(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return True
    return False


def render_summary_csv(dataset: Dataset, performance: dict, funnel_payload: dict) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["section", "name", "numerator", "sample_size", "value", "unit", "method"])
    cycle = performance["cycle_time"]
    writer.writerow(
        [
            "cycle_time",
            "median",
            _cell(cycle["sample_size"]),
            _cell(cycle["sample_size"]),
            _cell(cycle["median_seconds"]),
            "seconds",
            _cell(cycle["method"]),
        ]
    )
    for edge in performance["transitions"]:
        writer.writerow(
            [
                "transition",
                f"{edge['source']} → {edge['target']}",
                _cell(edge["frequency"]),
                _cell(edge["case_count"]),
                _cell(edge["median_delay_seconds"]),
                "seconds",
                "median transition delay; not processing time",
            ]
        )
    for stage in funnel_payload["stages"]:
        writer.writerow(
            [
                "funnel",
                stage["stage"],
                _cell(stage["cases_reached"]),
                _cell(funnel_payload["denominator"]),
                _cell(stage["share_of_denominator"]),
                "share_of_cases",
                _cell(funnel_payload["denominator_definition"]),
            ]
        )
    writer.writerow(
        [
            "dataset",
            dataset.name,
            "",
            _cell(dataset.case_count),
            dataset.timezone,
            "timezone",
            "synthetic" if dataset.synthetic else "upload",
        ]
    )
    return buffer.getvalue()


def render_html(
    dataset: Dataset,
    quality: dict,
    performance: dict,
    funnel_payload: dict,
    insight_payload: dict,
) -> str:
    cycle = performance["cycle_time"]

    def row(cells: list[object]) -> str:
        return "<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in cells) + "</tr>"

    transition_rows = "\n".join(
        row(
            [
                f"{edge['source']} → {edge['target']}",
                edge["frequency"],
                edge["case_count"],
                edge["median_delay_seconds"],
                edge["p90_delay_seconds"],
            ]
        )
        for edge in performance["transitions"]
    )
    funnel_rows = "\n".join(
        row(
            [
                stage["stage"],
                stage["cases_reached"],
                stage["share_of_denominator"],
                stage["drop_off_cases"],
            ]
        )
        for stage in funnel_payload["stages"]
    )
    cards = "\n".join(
        f"<section><h2>{html.escape(card['title'])}</h2>"
        f"<p>{html.escape(card['statement'])}</p>"
        f"<p>Numerator: {html.escape(str(card['numerator']))} "
        f"({html.escape(card['numerator_definition'])})</p>"
        f"<p>Sample size: {html.escape(str(card['sample_size']))} "
        f"({html.escape(card['sample_size_definition'])})</p>"
        f"<p>Value: {html.escape(str(card['value']))} {html.escape(card['unit'])}</p>"
        f"<p>Method: {html.escape(card['method'])}</p>"
        f"<p>{html.escape(card['caution'])}</p></section>"
        for card in insight_payload["cards"]
    )
    synthetic = "Yes — synthetic demo data, not real candidates." if dataset.synthetic else "No"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Hiring process report — {html.escape(dataset.name)}</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; line-height: 1.45; color: #1c1430; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    td, th {{ border: 1px solid #ddd; padding: 0.4rem 0.5rem; text-align: left; }}
    h1 {{ color: #7c3aed; }}
  </style>
</head>
<body>
  <h1>{html.escape(dataset.name)}</h1>
  <p>Synthetic dataset: {synthetic}</p>
  <p>Timezone used for naive timestamps: {html.escape(dataset.timezone)}</p>
  <p>Eligible events: {quality["eligible_event_count"]} of {quality["row_count"]} rows.
  Unique cases: {quality["unique_cases"]}.</p>
  <h2>Assumptions</h2>
  <ul>
    <li>{html.escape(ORDERING_DESCRIPTION)}</li>
    <li>{html.escape(str(cycle["method"]))}</li>
    <li>{html.escape(str(performance["processing_time_reason"]))}</li>
    <li>{html.escape(str(funnel_payload["denominator_definition"]))}</li>
    <li>{html.escape(CAUSAL_CAUTION)}</li>
    <li>{html.escape(PRIVACY_NOTICE)}</li>
  </ul>
  <h2>Cycle time</h2>
  <p>Median {cycle["median_seconds"]} seconds. P90 {cycle["p90_seconds"]} seconds.
  Sample size {cycle["sample_size"]} completed cases.</p>
  {cards}
  <h2>Transition delays</h2>
  <table>
    <tr><th>Edge</th><th>Transitions</th><th>Cases</th><th>Median seconds</th><th>P90 seconds</th></tr>
    {transition_rows}
  </table>
  <h2>Funnel</h2>
  <p>Denominator: {funnel_payload["denominator"]} cases.
  {html.escape(str(funnel_payload["denominator_definition"]))}</p>
  <table>
    <tr><th>Stage</th><th>Cases reached</th><th>Share</th><th>Drop-off from previous</th></tr>
    {funnel_rows}
  </table>
</body>
</html>
"""
