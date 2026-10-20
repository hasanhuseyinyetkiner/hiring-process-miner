import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { api } from "../api/client.ts"
import { ErrorBlock, LoadingBlock } from "../components/States.tsx"
import { formatCount, formatDuration, formatShare } from "../lib/format.ts"
import { useDataset } from "../state.tsx"

export function OverviewPage() {
  const { dataset, datasetId, query } = useDataset()
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
  return (
    <div className="space-y-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-accent">{dataset.timezone}</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight">{dataset.name}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--color-muted)]">
          {dataset.notes ?? "Uploaded event log. Treat case identifiers as already anonymized."}
        </p>
      </div>
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
          <Link to="/map" className="mt-4 inline-flex text-sm font-semibold text-accent">
            Open the process map
          </Link>
        </section>
      ) : null}
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
