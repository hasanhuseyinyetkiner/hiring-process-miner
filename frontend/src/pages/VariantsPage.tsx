import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { api } from "../api/client.ts"
import { FilterBar } from "../components/FilterBar.tsx"
import { EmptyBlock, ErrorBlock, ImportLink, LoadingBlock } from "../components/States.tsx"
import { formatCount, formatDuration, formatShare } from "../lib/format.ts"
import { useDataset } from "../state.tsx"

export function VariantsPage() {
  const { dataset, datasetId, query } = useDataset()
  const variants = useQuery({
    queryKey: ["variants", datasetId, query],
    enabled: Boolean(datasetId),
    queryFn: () => api.variants(datasetId ?? "", query),
  })
  const [left, setLeft] = useState("")
  const [right, setRight] = useState("")
  const compare = useQuery({
    queryKey: ["compare", datasetId, query, left, right],
    enabled: Boolean(datasetId && left && right),
    queryFn: () => api.compareVariants(datasetId ?? "", query, left, right),
  })
  if (!dataset) {
    return <EmptyBlock title="No variants yet" body="Variants are the distinct activity sequences in a log." action={<ImportLink />} />
  }
  if (variants.isLoading) return <LoadingBlock label="Loading variants" />
  if (variants.error || !variants.data) return <ErrorBlock message={variants.error?.message ?? "Could not load variants."} />
  const chart = variants.data.variants.slice(0, 8).map((variant, index) => ({
    label: `#${index + 1}`,
    cases: variant.case_count,
    key: variant.key,
  }))
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Variants</h1>
        <p className="mt-2 text-sm text-[var(--color-muted)]">
          {formatCount(variants.data.variant_count)} distinct sequences among {formatCount(variants.data.total_cases)} cases.
          Showing {formatCount(variants.data.shown)}.
        </p>
      </div>
      <FilterBar />
      <div className="h-56 rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)] p-3">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chart}>
            <XAxis dataKey="label" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="cases" fill="#7c3aed" radius={6} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="overflow-x-auto rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)]">
        <table className="min-w-full text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-[var(--color-muted)]">
            <tr>
              <th className="px-3 py-2">Sequence</th>
              <th className="px-3 py-2">Cases</th>
              <th className="px-3 py-2">Share</th>
              <th className="px-3 py-2">Median cycle</th>
              <th className="px-3 py-2">Outcomes</th>
            </tr>
          </thead>
          <tbody>
            {variants.data.variants.map((variant) => (
              <tr key={variant.key} data-testid="variant-row" className="border-t border-[var(--color-line)]">
                <td className="px-3 py-2">{variant.key}</td>
                <td className="tabular px-3 py-2">{formatCount(variant.case_count)}</td>
                <td className="px-3 py-2">{formatShare(variant.share)}</td>
                <td className="px-3 py-2">
                  mean {formatDuration(variant.mean_cycle_seconds)} · median{" "}
                  {formatDuration(variant.median_cycle_seconds)} · P90{" "}
                  {formatDuration(variant.p90_cycle_seconds)} · P95{" "}
                  {formatDuration(variant.p95_cycle_seconds)}
                  <span className="block text-xs text-[var(--color-muted)]">
                    n={formatCount(variant.cycle_sample_size)}
                  </span>
                </td>
                <td className="px-3 py-2">
                  {Object.entries(variant.outcomes)
                    .map(([name, count]) => `${name} ${count}`)
                    .join(", ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <section className="grid gap-3 rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)] p-4 md:grid-cols-2">
        <label className="grid gap-1 text-sm">
          Compare A
          <select className="rounded-xl border border-[var(--color-line)] bg-transparent px-2 py-1.5" value={left} onChange={(event) => setLeft(event.target.value)}>
            <option value="">Choose a variant</option>
            {variants.data.variants.map((variant) => (
              <option key={variant.key} value={variant.key}>
                {variant.key}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          Compare B
          <select className="rounded-xl border border-[var(--color-line)] bg-transparent px-2 py-1.5" value={right} onChange={(event) => setRight(event.target.value)}>
            <option value="">Choose a variant</option>
            {variants.data.variants.map((variant) => (
              <option key={variant.key} value={variant.key}>
                {variant.key}
              </option>
            ))}
          </select>
        </label>
        {compare.data ? (
          <div className="md:col-span-2 grid gap-3 md:grid-cols-2">
            <CompareCard title="A" variant={compare.data.a} />
            <CompareCard title="B" variant={compare.data.b} />
          </div>
        ) : null}
      </section>
    </div>
  )
}

function CompareCard({
  title,
  variant,
}: {
  title: string
  variant: {
    case_count: number
    mean_cycle_seconds: number | null
    median_cycle_seconds: number | null
    p90_cycle_seconds: number | null
    p95_cycle_seconds: number | null
    cycle_sample_size: number
    outcomes: Record<string, number>
  } | null
}) {
  if (!variant) return <p className="text-sm">Variant {title} was not in the current filter.</p>
  return (
    <article className="rounded-2xl bg-[var(--color-canvas)] p-3 text-sm">
      <h3 className="font-semibold">Variant {title}</h3>
      <p className="tabular mt-1">{formatCount(variant.case_count)} cases</p>
      <p>
        Mean {formatDuration(variant.mean_cycle_seconds)}, median{" "}
        {formatDuration(variant.median_cycle_seconds)}, P90{" "}
        {formatDuration(variant.p90_cycle_seconds)}, P95{" "}
        {formatDuration(variant.p95_cycle_seconds)} (n={formatCount(variant.cycle_sample_size)})
      </p>
      <p>{Object.entries(variant.outcomes).map(([name, count]) => `${name} ${count}`).join(", ")}</p>
    </article>
  )
}
