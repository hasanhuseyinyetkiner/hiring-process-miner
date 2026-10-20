import { describe, expect, it } from "vitest"
import { filterQuery, formatDuration, formatShare } from "./format.ts"

describe("formatDuration", () => {
  it("renders API seconds without inventing a new unit system", () => {
    expect(formatDuration(null)).toBe("—")
    expect(formatDuration(0)).toBe("0s")
    expect(formatDuration(86_400)).toBe("1.0 d")
    expect(formatDuration(1_123_200)).toBe("13.0 d")
  })
})

describe("formatShare", () => {
  it("shows one decimal percent", () => {
    expect(formatShare(0.5)).toBe("50.0%")
    expect(formatShare(null)).toBe("—")
  })
})

describe("filterQuery", () => {
  it("omits the default case status and repeats attribute filters", () => {
    expect(
      filterQuery({ case_status: "all", channel: "", job_family: "", outcome: "" }),
    ).toBe("")
    expect(
      filterQuery({
        case_status: "completed",
        channel: "referral",
        job_family: "engineering",
        outcome: "Hired",
      }),
    ).toBe("?case_status=completed&channels=referral&job_families=engineering&outcomes=Hired")
  })
})
