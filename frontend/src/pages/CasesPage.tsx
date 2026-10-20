import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { api } from "../api/client.ts"
import { FilterBar } from "../components/FilterBar.tsx"
import { EmptyBlock, ErrorBlock, ImportLink, LoadingBlock } from "../components/States.tsx"
import { formatCount, formatDuration } from "../lib/format.ts"
import { useDataset } from "../state.tsx"

export function CasesPage() {
  const { dataset, datasetId, query } = useDataset()
  const [selected, setSelected] = useState<string | null>(null)
  const cases = useQuery({
    queryKey: ["cases", datasetId, query],
    enabled: Boolean(datasetId),
    queryFn: () => api.cases(datasetId ?? "", query),
  })
  const detail = useQuery({
    queryKey: ["case", datasetId, selected],
    enabled: Boolean(datasetId && selected),
    queryFn: () => api.caseDetail(datasetId ?? "", selected ?? ""),
  })
  if (!dataset) {
    return <EmptyBlock title="No cases yet" body="Case traces appear after an import." action={<ImportLink />} />
  }
  if (cases.isLoading) return <LoadingBlock label="Loading cases" />
  if (cases.error || !cases.data) return <ErrorBlock message={cases.error?.message ?? "Could not load cases."} />
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Cases</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          {formatCount(cases.data.total)} cases in canonical order. Identifiers are anonymous.
        </p>
      </div>
      <FilterBar />
      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="overflow-x-auto rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)]">
          <table className="min-w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-[var(--color-muted)]">
              <tr>
                <th className="px-3 py-2">Case</th>
                <th className="px-3 py-2">Outcome</th>
                <th className="px-3 py-2">Events</th>
                <th className="px-3 py-2">Cycle</th>
              </tr>
            </thead>
            <tbody>
              {cases.data.cases.map((row) => (
                <tr key={row.case_id} className="border-t border-[var(--color-line)]">
                  <td className="px-3 py-2">
                    <button type="button" className="font-semibold text-accent" onClick={() => setSelected(row.case_id)}>
                      {row.case_id}
                    </button>
                  </td>
                  <td className="px-3 py-2">{row.outcome}</td>
                  <td className="tabular px-3 py-2">{row.event_count}</td>
                  <td className="px-3 py-2">{row.completed ? formatDuration(row.cycle_seconds) : "ongoing"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <aside className="rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)] p-4">
          {!selected ? <p className="text-sm text-[var(--color-muted)]">Select a case to read its trace.</p> : null}
          {detail.data ? (
            <div>
              <h2 className="text-lg font-semibold">{detail.data.case_id}</h2>
              <p className="text-sm text-[var(--color-muted)]">
                {detail.data.outcome} · {detail.data.completed ? formatDuration(detail.data.cycle_seconds) : "ongoing"}
              </p>
              <ol className="mt-3 space-y-2 text-sm">
                {detail.data.events.map((event) => (
                  <li key={`${event.source_row}-${event.activity}`} className="rounded-xl bg-[var(--color-canvas)] px-3 py-2">
                    <span className="font-semibold">{event.activity}</span>
                    <span className="mt-1 block text-xs text-[var(--color-muted)]">
                      {event.timestamp} · row {event.source_row}
                      {event.channel ? ` · ${event.channel}` : ""}
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          ) : null}
        </aside>
      </div>
    </div>
  )
}
