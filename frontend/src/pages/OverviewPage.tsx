import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { api } from "../api/client.ts"
import { ExportBar } from "../components/ExportBar.tsx"
import { FilterBar } from "../components/FilterBar.tsx"
import { QualityPanel } from "../components/QualityPanel.tsx"
import { ErrorBlock, LoadingBlock } from "../components/States.tsx"
import { formatCount, formatDuration, formatShare } from "../lib/format.ts"
import { useDataset } from "../state.tsx"

export function OverviewPage() {
  const { dataset, datasetId, query, filters } = useDataset()
  const performance = useQuery({
    queryKey: ["performance", datasetId, query],
    enabled: Boolean(datasetId),
    queryFn: () => api.performance(datasetId ?? "", query),
  })
  const funnel = useQuery({
    queryKey: ["funnel", datasetId, query],
    enabled: Boolean(datasetId),
    queryFn: () => api.funnel(datasetId ?? "", query),
  })
  const conformance = useQuery({
    queryKey: ["conformance", datasetId, query],
    enabled: Boolean(datasetId),
    queryFn: () => api.conformance(datasetId ?? "", query),
  })
  const insights = useQuery({
    queryKey: ["insights", datasetId, query],
    enabled: Boolean(datasetId),
    queryFn: () => api.insights(datasetId ?? "", query),
  })
  const quality = useQuery({
    queryKey: ["quality", datasetId],
    enabled: Boolean(datasetId),
    queryFn: () => api.quality(datasetId ?? ""),
  })
  if (!dataset) {
    return (
      <section className="mx-auto max-w-3xl py-10">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Hiring operations</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">See the process the log actually contains.</h1>
        <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--color-muted)]">
          Import an anonymized event log, or generate the deterministic synthetic demo. Every figure on the next
          screens comes back from the API with its sample size and method.
        </p>
        <Link to="/import" className="mt-6 inline-flex rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white">
          Start an import
        </Link>
      </section>
    )
  }
  if (performance.isLoading || funnel.isLoading || insights.isLoading) return <LoadingBlock />
  if (performance.error || funnel.error) {
    return <ErrorBlock message={(performance.error ?? funnel.error)?.message ?? "Could not load the overview."} />
  }
  const cycle = performance.data?.cycle_time
  const hero = insights.data?.cards[0]
  const hired = funnel.data?.stages.find((stage) => stage.stage === "Hired")
  const filterActive =
    filters.case_status !== "all" ||
    Boolean(filters.channel) ||
    Boolean(filters.job_family) ||
    Boolean(filters.outcome)
  const topLatency = (performance.data?.transitions ?? [])
    .filter((edge) => edge.median_delay_seconds !== null && edge.delay_sample_size >= 30)
    .slice()
    .sort((a, b) => (b.median_delay_seconds ?? 0) - (a.median_delay_seconds ?? 0))[0]

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">{dataset.timezone}</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">{dataset.name}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--color-muted)]">
            {dataset.notes ?? "Uploaded event log. Treat case identifiers as already anonymized."}
          </p>
        </div>
        <ExportBar />
      </div>

      <section
        data-testid="ops-telemetry"
        className="rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)] p-4"
      >
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-[var(--color-muted)]">
            Operational telemetry
          </h2>
          <p className="text-xs text-[var(--color-muted)]">
            {filterActive ? "Cohort filters active — KPIs from API" : "All cases · KPIs from API"}
          </p>
        </div>
        <dl className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          <Telemetry label="Eligible cases" value={formatCount(performance.data?.total_cases)} hint="After filters" />
          <Telemetry
            label="Completed / ongoing"
            value={`${formatCount(performance.data?.completed_cases)} / ${formatCount(performance.data?.ongoing_cases)}`}
            hint="Terminal vs open"
          />
          <Telemetry
            label="Stored events"
            value={formatCount(dataset.eligible_event_count)}
            hint={`${formatCount(dataset.row_count)} rows imported`}
          />
          <Telemetry
            label="Excluded rows"
            value={formatCount(quality.data?.excluded_event_count ?? dataset.row_count - dataset.eligible_event_count)}
            hint="Not in analytics"
          />
          <Telemetry
            label="Top latency (≥30)"
            value={topLatency ? formatDuration(topLatency.median_delay_seconds) : "—"}
            hint={
              topLatency
                ? `${topLatency.source} → ${topLatency.target}`
                : "No edge meets sample floor"
            }
          />
        </dl>
      </section>

      <FilterBar />

      <section className="grid gap-3 md:grid-cols-4">
        <Kpi label="Cases" value={formatCount(performance.data?.total_cases)} detail={`${formatCount(performance.data?.ongoing_cases)} ongoing`} />
        <Kpi
          label="Median cycle time"
          value={formatDuration(cycle?.median_seconds)}
          detail={`Sample ${formatCount(cycle?.sample_size)} completed cases`}
        />
        <Kpi
          label="Reached hired"
          value={formatCount(hired?.cases_reached)}
          detail={`${formatShare(hired?.share_of_denominator)} of ${formatCount(funnel.data?.denominator)} cases`}
        />
        <Kpi
          label="Conformance fit"
          value={formatCount(conformance.data?.numerator)}
          detail={`of ${formatCount(conformance.data?.sample_size)} cases`}
        />
      </section>
      {hero ? (
        <section className="rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)] p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">Leading delay</p>
          <p className="mt-2 text-xl font-semibold">{hero.statement}</p>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            Numerator {formatCount(hero.numerator)}. Sample size {formatCount(hero.sample_size)}.{" "}
            {hero.caution}
          </p>
          <div className="mt-4 flex flex-wrap gap-4">
            <Link to="/map" className="inline-flex text-sm font-semibold text-accent">
              Open the process map
            </Link>
            <Link to="/bottlenecks" className="inline-flex text-sm font-semibold text-accent">
              Transition latency view
            </Link>
          </div>
        </section>
      ) : null}

      {quality.isLoading ? <LoadingBlock label="Loading data hygiene" /> : null}
      {quality.error ? <ErrorBlock message={quality.error.message} /> : null}
      {quality.data ? <QualityPanel quality={quality.data} compact testId="overview-hygiene" /> : null}
    </div>
  )
}

function Telemetry({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="rounded-2xl bg-[var(--color-canvas)] px-3 py-3">
      <dt className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--color-muted)]">{label}</dt>
      <dd className="tabular mt-1 text-xl font-semibold tracking-tight">{value}</dd>
      <p className="mt-0.5 text-[11px] text-[var(--color-muted)]">{hint}</p>
    </div>
  )
}

function Kpi({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <article className="rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)] px-4 py-4">
      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--color-muted)]">{label}</p>
      <p className="tabular mt-2 text-3xl font-semibold tracking-tight">{value}</p>
      <p className="mt-1 text-xs text-[var(--color-muted)]">{detail}</p>
    </article>
  )
}
