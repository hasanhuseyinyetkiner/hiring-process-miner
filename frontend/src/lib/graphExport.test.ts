import { describe, expect, it } from "vitest"
import { graphToSvg } from "./graphExport.ts"
import type { ProcessGraph } from "../api/types.ts"

const SAMPLE: ProcessGraph = {
  ordering: "utc_timestamp_then_source_row",
  delay_definition: "Elapsed seconds between consecutive events.",
  total_cases: 2,
  total_events: 4,
  edges_before_filter: 2,
  edges_after_filter: 2,
  min_case_ratio: 0,
  nodes: [
    { id: "Applied", activity: "Applied", case_count: 2, event_count: 2 },
    { id: "Screened", activity: "Screened", case_count: 2, event_count: 2 },
  ],
  edges: [
    {
      id: "Applied->Screened",
      source: "Applied",
      target: "Screened",
      frequency: 2,
      case_count: 2,
      case_ratio: 1,
      mean_delay_seconds: 86_400,
      median_delay_seconds: 86_400,
      p90_delay_seconds: 86_400,
      p95_delay_seconds: 86_400,
      delay_sample_size: 2,
    },
  ],
}

describe("graphToSvg", () => {
  it("embeds stage labels and stays well-formed", () => {
    const svg = graphToSvg(SAMPLE)
    expect(svg).toContain("<svg")
    expect(svg).toContain("Applied")
    expect(svg).toContain("Screened")
    expect(svg).toContain("</svg>")
  })
})
