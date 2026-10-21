import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { api } from "../api/client.ts"
import { ExportBar } from "../components/ExportBar.tsx"
import { FilterBar } from "../components/FilterBar.tsx"
import { delayLabel, ProcessMap } from "../components/ProcessMap.tsx"
import { EmptyBlock, ErrorBlock, ImportLink, LoadingBlock } from "../components/States.tsx"
import { formatCount, formatShare } from "../lib/format.ts"
import { useDataset } from "../state.tsx"
import type { ProcessEdge, ProcessNode } from "../api/types.ts"

type Selection = { kind: "node"; node: ProcessNode } | { kind: "edge"; edge: ProcessEdge } | null

export function MapPage() {
  const { dataset, datasetId, query } = useDataset()
  const [ratio, setRatio] = useState(0)
  const [selection, setSelection] = useState<Selection>(null)
  const graph = useQuery({
    queryKey: ["process", datasetId, query, ratio],
    enabled: Boolean(datasetId),
    queryFn: () => {
      const params = new URLSearchParams(query.replace(/^\?/, ""))
      params.set("min_case_ratio", String(ratio / 100))
      return api.process(datasetId ?? "", `?${params.toString()}`)
    },
  })
  if (!dataset) {
    return <EmptyBlock title="No event log yet" body="Import a CSV or generate the synthetic hiring log." action={<ImportLink />} />
  }
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex flex-wrap items-end justify-between gap-3 border-b border-[var(--color-line)] px-4 py-3 md:px-6">
        <div>
          <h1 className="text-lg font-semibold">Process map</h1>
          <p data-testid="visible-edges" className="text-xs text-[var(--color-muted)]">
            Showing {graph.data?.edges_after_filter ?? "—"} of {graph.data?.edges_before_filter ?? "—"} edges
            · {formatCount(graph.data?.total_cases)} cases
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <label className="grid min-w-[220px] gap-1 text-xs font-medium">
            Minimum edge frequency {ratio}% of cases
            <input
              data-testid="edge-slider"
              type="range"
              min={0}
              max={80}
              step={1}
              value={ratio}
              aria-valuemin={0}
              aria-valuemax={80}
              aria-valuenow={ratio}
              aria-label="Minimum edge frequency as percent of cases"
              onChange={(event) => {
                setRatio(Number(event.target.value))
                setSelection(null)
              }}
            />
          </label>
          <ExportBar graph={graph.data} />
        </div>
      </div>
      <div className="border-b border-[var(--color-line)] px-4 py-2 md:px-6">
        <FilterBar />
      </div>
      <div className="relative min-h-0 flex-1">
        {graph.isLoading ? <LoadingBlock /> : null}
        {graph.error ? <ErrorBlock message={graph.error.message} /> : null}
        {graph.data && graph.data.nodes.length === 0 ? (
          <EmptyBlock title="No activities in this filter" body="Widen the filters or lower the edge slider." />
        ) : null}
        {graph.data && graph.data.nodes.length > 0 ? (
          <ProcessMap
            graph={graph.data}
            onNode={(node) => setSelection({ kind: "node", node })}
            onEdge={(edge) => setSelection({ kind: "edge", edge })}
          />
        ) : null}
        {selection ? (
          <aside
            data-testid="details-drawer"
            className="absolute inset-y-0 right-0 z-10 w-full max-w-[380px] overflow-auto border-l border-[var(--color-line)] bg-[var(--color-card)] p-5 shadow-xl"
          >
            <div className="flex items-start justify-between gap-3">
              <h2 className="text-lg font-semibold">
                {selection.kind === "node"
                  ? selection.node.activity
                  : `${selection.edge.source} → ${selection.edge.target}`}
              </h2>
              <button type="button" className="text-sm font-semibold text-accent" onClick={() => setSelection(null)}>
                Close
              </button>
            </div>
            {selection.kind === "node" ? (
              <dl className="mt-4 space-y-3 text-sm">
                <Row term="Cases" value={formatCount(selection.node.case_count)} />
                <Row term="Events" value={formatCount(selection.node.event_count)} />
                <p className="text-[var(--color-muted)]">
                  Case count is the number of distinct cases with at least one event of this activity.
                </p>
              </dl>
            ) : (
              <dl className="mt-4 space-y-3 text-sm">
                <Row term="Transitions" value={formatCount(selection.edge.frequency)} />
                <Row term="Cases" value={formatCount(selection.edge.case_count)} />
                <Row term="Share of cases" value={formatShare(selection.edge.case_ratio)} />
                <Row term="Mean delay" value={delayLabel(selection.edge.mean_delay_seconds)} />
                <Row term="Median delay" value={delayLabel(selection.edge.median_delay_seconds)} />
                <Row term="P90 delay" value={delayLabel(selection.edge.p90_delay_seconds)} />
                <Row term="P95 delay" value={delayLabel(selection.edge.p95_delay_seconds)} />
                <Row term="Delay sample" value={formatCount(selection.edge.delay_sample_size)} />
                <p className="text-[var(--color-muted)]">{graph.data?.delay_definition}</p>
              </dl>
            )}
          </aside>
        ) : null}
      </div>
    </div>
  )
}

function Row({ term, value }: { term: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <dt className="text-[var(--color-muted)]">{term}</dt>
      <dd className="tabular font-semibold">{value}</dd>
    </div>
  )
}
