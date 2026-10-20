import type {
  CaseDetail,
  CasePage,
  Conformance,
  DatasetSummary,
  FieldMapping,
  FilterOptions,
  Funnel,
  Insights,
  Job,
  Meta,
  Methodology,
  Performance,
  Preview,
  ProcessGraph,
  QualityReport,
  Rework,
  VariantCompare,
  Variants,
} from "./types.ts"

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown }
    if (typeof body.detail === "string") return body.detail
    if (body.detail && typeof body.detail === "object" && "detail" in body.detail) {
      const nested = (body.detail as { detail?: unknown }).detail
      if (typeof nested === "string") return nested
    }
  } catch {
    return response.statusText || "Request failed"
  }
  return response.statusText || "Request failed"
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }
  const response = await fetch(path, { ...init, headers })
  if (!response.ok) throw new ApiError(response.status, await errorMessage(response))
  if (response.status === 204) return undefined as T
  const type = response.headers.get("content-type") ?? ""
  if (type.includes("text/html") || type.includes("text/csv")) return (await response.text()) as T
  return (await response.json()) as T
}

export const api = {
  meta: () => request<Meta>("/api/meta"),
  methodology: () => request<Methodology>("/api/methodology"),
  datasets: () => request<{ datasets: DatasetSummary[] }>("/api/datasets"),
  createDraft: (file: File) => {
    const body = new FormData()
    body.append("file", file)
    return request<{ draft_id: string; filename: string; row_count: number }>("/api/drafts", {
      method: "POST",
      body,
    })
  },
  createSynthetic: (cases: number, seed: number) =>
    request<{ draft_id: string; timezone_suggestion: string; row_count: number }>(
      "/api/drafts/synthetic",
      { method: "POST", body: JSON.stringify({ cases, seed }) },
    ),
  preview: (draftId: string, mapping: FieldMapping, timezone: string) =>
    request<Preview>(`/api/drafts/${draftId}/preview`, {
      method: "POST",
      body: JSON.stringify({ mapping, timezone }),
    }),
  startImport: (draftId: string, mapping: FieldMapping, timezone: string, name: string) =>
    request<Job>("/api/datasets/import", {
      method: "POST",
      body: JSON.stringify({ draft_id: draftId, mapping, timezone, name }),
    }),
  job: (jobId: string) => request<Job>(`/api/jobs/${jobId}`),
  quality: (datasetId: string) => request<QualityReport>(`/api/datasets/${datasetId}/quality`),
  process: (datasetId: string, query: string) =>
    request<ProcessGraph>(`/api/datasets/${datasetId}/process${query}`),
  performance: (datasetId: string, query: string) =>
    request<Performance>(`/api/datasets/${datasetId}/performance${query}`),
  funnel: (datasetId: string, query: string) =>
    request<Funnel>(`/api/datasets/${datasetId}/funnel${query}`),
  insights: (datasetId: string, query: string) =>
    request<Insights>(`/api/datasets/${datasetId}/insights${query}`),
  variants: (datasetId: string, query: string) =>
    request<Variants>(`/api/datasets/${datasetId}/variants${query}`),
  compareVariants: (datasetId: string, query: string, a: string, b: string) => {
    const params = new URLSearchParams(query.replace(/^\?/, ""))
    params.set("a", a)
    params.set("b", b)
    return request<VariantCompare>(`/api/datasets/${datasetId}/variants/compare?${params}`)
  },
  conformance: (datasetId: string, query: string) =>
    request<Conformance>(`/api/datasets/${datasetId}/conformance${query}`),
  saveConformance: (datasetId: string, transitions: Array<{ source: string; target: string }>) =>
    request<Conformance>(`/api/datasets/${datasetId}/conformance`, {
      method: "PUT",
      body: JSON.stringify({ transitions }),
    }),
  filters: (datasetId: string) => request<FilterOptions>(`/api/datasets/${datasetId}/filters`),
  cases: (datasetId: string, query: string) =>
    request<CasePage>(`/api/datasets/${datasetId}/cases${query}`),
  caseDetail: (datasetId: string, caseId: string) =>
    request<CaseDetail>(`/api/datasets/${datasetId}/cases/${encodeURIComponent(caseId)}`),
  rework: (datasetId: string, query: string) =>
    request<Rework>(`/api/datasets/${datasetId}/rework${query}`),
  removeDataset: (datasetId: string) =>
    request<void>(`/api/datasets/${datasetId}`, { method: "DELETE" }),
  exportSummaryCsv: (datasetId: string, query: string) =>
    request<string>(`/api/datasets/${datasetId}/export/summary.csv${query}`),
  exportReportHtml: (datasetId: string, query: string) =>
    request<string>(`/api/datasets/${datasetId}/export/report.html${query}`),
}

export async function waitForJob(jobId: string): Promise<Job> {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    const job = await api.job(jobId)
    if (job.status === "SUCCEEDED" || job.status === "FAILED") return job
    await new Promise((resolve) => setTimeout(resolve, 400))
  }
  throw new ApiError(408, "Import is still running. Refresh the job list in a moment.")
}
