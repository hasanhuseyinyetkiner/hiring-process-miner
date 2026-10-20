export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) return "—"
  const sign = seconds < 0 ? "−" : ""
  const absolute = Math.abs(seconds)
  if (absolute < 60) return `${sign}${absolute.toFixed(0)}s`
  if (absolute < 3600) return `${sign}${(absolute / 60).toFixed(1)} min`
  if (absolute < 86_400) return `${sign}${(absolute / 3600).toFixed(1)} h`
  return `${sign}${(absolute / 86_400).toFixed(1)} d`
}

export function formatShare(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—"
  return `${(value * 100).toFixed(1)}%`
}

export function formatCount(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—"
  return new Intl.NumberFormat("en").format(value)
}

export function filterQuery(filters: {
  case_status: string
  channel: string
  job_family: string
  outcome: string
}): string {
  const params = new URLSearchParams()
  if (filters.case_status && filters.case_status !== "all") {
    params.set("case_status", filters.case_status)
  }
  if (filters.channel) params.append("channels", filters.channel)
  if (filters.job_family) params.append("job_families", filters.job_family)
  if (filters.outcome) params.append("outcomes", filters.outcome)
  const text = params.toString()
  return text ? `?${text}` : ""
}
