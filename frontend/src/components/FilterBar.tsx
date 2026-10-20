import { useQuery } from "@tanstack/react-query"
import { api } from "../api/client.ts"
import { useDataset } from "../state.tsx"

export function FilterBar() {
  const { datasetId, filters, setFilters } = useDataset()
  const options = useQuery({
    queryKey: ["filters", datasetId],
    enabled: Boolean(datasetId),
    queryFn: () => api.filters(datasetId ?? ""),
  })
  return (
    <fieldset className="flex flex-wrap items-end gap-3 rounded-2xl border border-[var(--color-line)] bg-[var(--color-card)] px-3 py-3">
      <legend className="px-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--color-muted)]">
        Filters
      </legend>
      <label className="grid gap-1 text-xs font-medium">
        Case status
        <select
          aria-label="Case status"
          className="rounded-xl border border-[var(--color-line)] bg-transparent px-2 py-1.5"
          value={filters.case_status}
          onChange={(event) =>
            setFilters({
              ...filters,
              case_status: event.target.value as typeof filters.case_status,
            })
          }
        >
          <option value="all">All cases</option>
          <option value="completed">Completed</option>
          <option value="ongoing">Ongoing</option>
        </select>
      </label>
      <label className="grid gap-1 text-xs font-medium">
        Channel
        <select
          aria-label="Channel"
          className="rounded-xl border border-[var(--color-line)] bg-transparent px-2 py-1.5"
          value={filters.channel}
          onChange={(event) => setFilters({ ...filters, channel: event.target.value })}
        >
          <option value="">All channels</option>
          {(options.data?.channels ?? []).map((channel) => (
            <option key={channel} value={channel}>
              {channel}
            </option>
          ))}
        </select>
      </label>
      <label className="grid gap-1 text-xs font-medium">
        Job family
        <select
          aria-label="Job family"
          className="rounded-xl border border-[var(--color-line)] bg-transparent px-2 py-1.5"
          value={filters.job_family}
          onChange={(event) => setFilters({ ...filters, job_family: event.target.value })}
        >
          <option value="">All families</option>
          {(options.data?.job_families ?? []).map((family) => (
            <option key={family} value={family}>
              {family}
            </option>
          ))}
        </select>
      </label>
      <label className="grid gap-1 text-xs font-medium">
        Outcome
        <select
          aria-label="Outcome"
          className="rounded-xl border border-[var(--color-line)] bg-transparent px-2 py-1.5"
          value={filters.outcome}
          onChange={(event) => setFilters({ ...filters, outcome: event.target.value })}
        >
          <option value="">All outcomes</option>
          {(options.data?.outcomes ?? []).map((outcome) => (
            <option key={outcome} value={outcome}>
              {outcome}
            </option>
          ))}
        </select>
      </label>
    </fieldset>
  )
}
