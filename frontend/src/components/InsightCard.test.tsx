import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import type { InsightCard as Insight } from "../api/types.ts"
import { InsightCard } from "./InsightCard.tsx"

const card: Insight = {
  id: "highest_median_transition_delay",
  title: "Highest median transition delay",
  statement: "Interview Scheduled → Interview Completed has the highest median transition delay.",
  numerator: 120,
  numerator_definition: "Observed transitions of this edge.",
  sample_size: 110,
  sample_size_definition: "Distinct cases.",
  value: 1_209_600,
  unit: "seconds",
  method: "Median of elapsed time. Not processing time.",
  caution: "This is not a causal root cause.",
  source_activity: "Interview Scheduled",
  target_activity: "Interview Completed",
}

describe("InsightCard", () => {
  it("shows the numerator, sample size, and method from the API", () => {
    render(<InsightCard card={card} />)
    expect(screen.getByText("Numerator")).toBeInTheDocument()
    expect(screen.getByText("120")).toBeInTheDocument()
    expect(screen.getByText("Sample size")).toBeInTheDocument()
    expect(screen.getByText("110")).toBeInTheDocument()
    expect(screen.getByText(/Not processing time/)).toBeInTheDocument()
    expect(screen.getByText(/not a causal root cause/i)).toBeInTheDocument()
    expect(screen.getByText(/1209600 seconds/)).toBeInTheDocument()
  })
})
