import { useQuery } from "@tanstack/react-query"
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { api } from "../api/client.ts"
import { FilterBar } from "../components/FilterBar.tsx"
import { InsightCard } from "../components/InsightCard.tsx"
import { EmptyBlock, ErrorBlock, ImportLink, LoadingBlock } from "../components/States.tsx"
import { formatCount, formatDuration, formatShare } from "../lib/format.ts"
import { useDataset } from "../state.tsx"

export function BottlenecksPage() {
  const { dataset, datasetId, query } = useDataset()
  const insights = useQuery({
    queryKey: ["insights", datasetId, query],
    enabled: Boolean(datasetId),
    queryFn: () => api.insights(datasetId ?? "", query),
  })
  const performance = useQuery({
    queryKey: ["performance", datasetId, query],
    enabled: Boolean(datasetId),
    queryFn: () => api.performance(datasetId ?? "", query),
  })
  const conformance = useQuery({
    queryKey: ["conformance", datasetId, query],
    enabled: Boolean(datasetId),
    queryFn: () => api.conformance(datasetId ?? "", query),
  })
  if (!dataset) {
    return <EmptyBlock title="No event log yet" body="Bottleneck cards appear after an import." action={<ImportLink />} />
  }
  if (insights.isLoading || performance.isLoading) return <LoadingBlock label="Loading bottlenecks" />
  if (insights.error || performance.error) {
    return <ErrorBlock message={(insights.error ?? performance.error)?.message ?? "Could not load bottlenecks."} />
  }
  const chart = (performance.data?.transitions ?? []).slice(0, 8).map((edge) => ({
    label: `${edge.source} → ${edge.target}`,
    days: edge.median_delay_seconds === null ? 0 : edge.median_delay_seconds / 86_400,
    seconds: edge.median_delay_seconds,
    frequency: edge.frequency,
  }))
  const [hero, ...rest] = insights.data?.cards ?? []
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Bottlenecks</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--color-muted)]">
          Delays are elapsed time between consecutive events. They are not processing time, and they are not a cause.
        </p>
      </div>
      <FilterBar />
      {hero ? <InsightCard card={hero} featured /> : null}
      <div className="grid gap-4 lg:grid-cols-3">
        {rest.map((card) => (
          <InsightCard key={card.id} card={card} />
        ))}
      </div>
      <section className="rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)] p-4">
        <h2 className="text-lg font-semibold">Median transition delay</h2>
        <p className="text-xs text-[var(--color-muted)]">
          Bar height is median seconds divided by 86,400 for display. The tooltip keeps the API seconds.
        </p>
        <div className="mt-3 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart} layout="vertical" margin={{ left: 24, right: 12 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" unit=" d" />
              <YAxis type="category" dataKey="label" width={180} tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value, _name, item) => {
                  const seconds = (item.payload as { seconds?: number | null }).seconds
                  return [`${value} d · ${seconds ?? "—"} seconds`, "Median"]
                }}
              />
              <Bar dataKey="days" fill="#7c3aed" radius={6} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
      {conformance.data ? (
        <section className="rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)] p-5">
          <h2 className="text-lg font-semibold">Rule-based conformance</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">{conformance.data.method}</p>
          <p className="tabular mt-3 text-3xl font-semibold">
            {formatCount(conformance.data.numerator)}
            <span className="text-base font-medium text-[var(--color-muted)]">
              {" "}
              / {formatCount(conformance.data.sample_size)} cases · {formatShare(conformance.data.fit_rate)}
            </span>
          </p>
          <p className="mt-1 text-xs text-[var(--color-muted)]">{conformance.data.numerator_definition}</p>
          <p className="mt-3 text-sm">{conformance.data.pm4py.message}</p>
          <ul className="mt-3 space-y-1 text-sm">
            {conformance.data.deviations.slice(0, 6).map((item) => (
              <li key={`${item.source}-${item.target}`}>
                {item.source} → {item.target}: {formatCount(item.case_count)} cases,{" "}
                {formatCount(item.frequency)} transitions
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {performance.data ? (
        <p className="text-xs text-[var(--color-muted)]">
          Cycle-time median {formatDuration(performance.data.cycle_time.median_seconds)} on{" "}
          {formatCount(performance.data.cycle_time.sample_size)} completed cases.{" "}
          {performance.data.processing_time_reason}
        </p>
      ) : null}
    </div>
  )
}
