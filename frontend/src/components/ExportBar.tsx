import { useState } from "react"
import { api } from "../api/client.ts"
import { downloadGraphPng, downloadGraphSvg, downloadText } from "../lib/graphExport.ts"
import { useDataset } from "../state.tsx"
import type { ProcessGraph } from "../api/types.ts"

export function ExportBar({ graph }: { graph?: ProcessGraph | null }) {
  const { datasetId, query } = useDataset()
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function run(label: string, action: () => Promise<void>) {
    if (!datasetId) return
    setBusy(label)
    setError(null)
    try {
      await action()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.")
    } finally {
      setBusy(null)
    }
  }

  if (!datasetId) return null

  return (
    <div data-testid="export-bar" className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--color-muted)]">Export</span>
      <button
        type="button"
        data-testid="export-csv"
        className="rounded-full border border-[var(--color-line)] bg-[var(--color-card)] px-3 py-1.5 text-xs font-semibold"
        disabled={busy !== null}
        onClick={() =>
          run("csv", async () => {
            const text = await api.exportSummaryCsv(datasetId, query)
            downloadText("hiring-summary.csv", text, "text/csv;charset=utf-8")
          })
        }
      >
        {busy === "csv" ? "CSV…" : "CSV"}
      </button>
      <button
        type="button"
        data-testid="export-html"
        className="rounded-full border border-[var(--color-line)] bg-[var(--color-card)] px-3 py-1.5 text-xs font-semibold"
        disabled={busy !== null}
        onClick={() =>
          run("html", async () => {
            const text = await api.exportReportHtml(datasetId, query)
            downloadText("hiring-report.html", text, "text/html;charset=utf-8")
          })
        }
      >
        {busy === "html" ? "HTML…" : "HTML"}
      </button>
      <button
        type="button"
        data-testid="export-svg"
        className="rounded-full border border-[var(--color-line)] bg-[var(--color-card)] px-3 py-1.5 text-xs font-semibold"
        disabled={busy !== null || !graph}
        onClick={() =>
          run("svg", async () => {
            if (!graph) return
            await downloadGraphSvg(graph)
          })
        }
      >
        {busy === "svg" ? "SVG…" : "SVG"}
      </button>
      <button
        type="button"
        data-testid="export-png"
        className="rounded-full border border-[var(--color-line)] bg-[var(--color-card)] px-3 py-1.5 text-xs font-semibold"
        disabled={busy !== null || !graph}
        onClick={() =>
          run("png", async () => {
            if (!graph) return
            await downloadGraphPng(graph)
          })
        }
      >
        {busy === "png" ? "PNG…" : "PNG"}
      </button>
      {error ? <p className="w-full text-xs text-rose-600">{error}</p> : null}
    </div>
  )
}
