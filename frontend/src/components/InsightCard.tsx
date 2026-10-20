import type { InsightCard as Insight } from "../api/types.ts"
import { formatCount, formatDuration } from "../lib/format.ts"

function displayValue(card: Insight): string {
  if (card.value === null) return "—"
  if (card.unit === "seconds") return formatDuration(card.value)
  if (card.unit === "cases") return formatCount(card.value)
  return String(card.value)
}

export function InsightCard({ card, featured = false }: { card: Insight; featured?: boolean }) {
  return (
    <article
      data-testid="insight-card"
      className={`rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)] p-5 shadow-sm ${
        featured ? "md:p-7" : ""
      }`}
    >
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-accent">
        Observed pattern
      </p>
      <h3 className={`mt-2 font-semibold ${featured ? "text-2xl" : "text-lg"}`}>{card.title}</h3>
      <p className="mt-2 text-sm leading-6 text-[var(--color-muted)]">{card.statement}</p>
      <p className="tabular mt-4 text-4xl font-semibold tracking-tight text-accent">
        {displayValue(card)}
      </p>
      <p className="mt-1 text-xs text-[var(--color-muted)]">
        Exact API value: {card.value === null ? "none" : card.value} {card.unit}
      </p>
      <dl className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl bg-[var(--color-canvas)] px-3 py-2">
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-[var(--color-muted)]">
            Numerator
          </dt>
          <dd className="tabular text-xl font-semibold">{formatCount(card.numerator)}</dd>
          <p className="text-xs leading-5 text-[var(--color-muted)]">{card.numerator_definition}</p>
        </div>
        <div className="rounded-2xl bg-[var(--color-canvas)] px-3 py-2">
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-[var(--color-muted)]">
            Sample size
          </dt>
          <dd className="tabular text-xl font-semibold">{formatCount(card.sample_size)}</dd>
          <p className="text-xs leading-5 text-[var(--color-muted)]">{card.sample_size_definition}</p>
        </div>
      </dl>
      <p className="mt-4 text-sm leading-6">
        <span className="font-semibold">Method. </span>
        {card.method}
      </p>
      <p className="mt-3 rounded-2xl bg-amber-50 px-3 py-2 text-sm leading-6 text-amber-950 dark:bg-amber-950/40 dark:text-amber-100">
        {card.caution}
      </p>
    </article>
  )
}
