import type { QualityReport } from "../api/types.ts"
import { formatCount } from "../lib/format.ts"

const TILES: Array<{ key: keyof QualityReport; label: string; testId?: string }> = [
  { key: "row_count", label: "Rows" },
  { key: "eligible_event_count", label: "Eligible events" },
  { key: "unique_cases", label: "Unique cases", testId: "quality-cases" },
  { key: "excluded_event_count", label: "Excluded rows" },
  { key: "missing_case_id", label: "Missing case id" },
  { key: "missing_activity", label: "Missing activity" },
  { key: "missing_timestamp", label: "Missing timestamp" },
  { key: "parse_failures", label: "Parse failures" },
  { key: "duplicate_count", label: "Duplicates" },
  { key: "ambiguous_timestamps", label: "Ambiguous local times" },
  { key: "nonexistent_timestamps", label: "Nonexistent local times" },
]

function isProbeCase(caseId: string | null | undefined): boolean {
  return Boolean(caseId && /^QX\d+/i.test(caseId))
}

export function QualityPanel({
  quality,
  testId = "quality-panel",
  compact = false,
}: {
  quality: QualityReport
  testId?: string
  compact?: boolean
}) {
  const breakdown = Object.entries(quality.exclusion_breakdown ?? {}).sort(
    (a, b) => b[1] - a[1],
  )
  const excluded = quality.issue_sample.filter((issue) => issue.exclusion_reason)
  const probes = excluded.filter((issue) => isProbeCase(issue.case_id))

  return (
    <section data-testid={testId} className="space-y-4" aria-labelledby={`${testId}-heading`}>
      <div>
        <h2 id={`${testId}-heading`} className="text-lg font-semibold">
          Data hygiene
        </h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">{quality.eligible_definition}</p>
      </div>
      <dl className={`grid gap-3 ${compact ? "sm:grid-cols-2 xl:grid-cols-4" : "sm:grid-cols-2 xl:grid-cols-4"}`}>
        {TILES.map((tile) => (
          <div
            key={tile.key}
            className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-card)] px-3 py-3"
          >
            <dt className="text-[11px] font-semibold uppercase tracking-wide text-[var(--color-muted)]">
              {tile.label}
            </dt>
            <dd data-testid={tile.testId} className="tabular mt-1 text-2xl font-semibold">
              {formatCount(Number(quality[tile.key] ?? 0))}
            </dd>
          </div>
        ))}
      </dl>
      {breakdown.length > 0 ? (
        <div data-testid="exclusion-breakdown" className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-card)] p-4">
          <h3 className="text-sm font-semibold">Exclusion reasons</h3>
          <ul className="mt-2 grid gap-1 text-sm sm:grid-cols-2">
            {breakdown.map(([reason, count]) => (
              <li key={reason} className="flex justify-between gap-3 border-b border-[var(--color-line)] py-1 last:border-0">
                <span className="font-mono text-xs">{reason}</span>
                <span className="tabular font-semibold">{formatCount(count)}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {quality.timezone_warnings.length > 0 ? (
        <ul className="space-y-2 text-sm">
          {quality.timezone_warnings.map((warning) => (
            <li
              key={warning}
              className="rounded-2xl bg-amber-50 px-3 py-2 text-amber-950 dark:bg-amber-950/40 dark:text-amber-100"
            >
              {warning}
            </li>
          ))}
        </ul>
      ) : null}
      <p className="text-sm text-[var(--color-muted)]">{quality.privacy_notice}</p>
      {excluded.length > 0 ? (
        <div data-testid="excluded-events" className="overflow-x-auto rounded-2xl border border-[var(--color-line)]">
          <table className="min-w-full text-left text-sm">
            <caption className="border-b border-[var(--color-line)] px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-[var(--color-muted)]">
              Excluded events
              {probes.length > 0
                ? ` · ${probes.length} quality probe${probes.length === 1 ? "" : "s"} (QX*)`
                : ""}
            </caption>
            <thead className="bg-[var(--color-canvas)] text-xs uppercase tracking-wide text-[var(--color-muted)]">
              <tr>
                <th className="px-3 py-2">Row</th>
                <th className="px-3 py-2">Case</th>
                <th className="px-3 py-2">Activity</th>
                <th className="px-3 py-2">Raw timestamp</th>
                <th className="px-3 py-2">Reason</th>
              </tr>
            </thead>
            <tbody>
              {excluded.slice(0, compact ? 12 : 24).map((issue) => {
                const probe = isProbeCase(issue.case_id)
                return (
                  <tr
                    key={`${issue.source_row}-${issue.exclusion_reason}`}
                    className={`border-t border-[var(--color-line)] ${
                      probe ? "bg-violet-50/80 dark:bg-violet-950/30" : ""
                    }`}
                    data-probe={probe ? "true" : undefined}
                  >
                    <td className="tabular px-3 py-2">{issue.source_row}</td>
                    <td className="px-3 py-2">
                      {issue.case_id || "—"}
                      {probe ? (
                        <span className="ml-2 rounded bg-accent/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-accent">
                          Probe
                        </span>
                      ) : null}
                    </td>
                    <td className="px-3 py-2">{issue.activity || "—"}</td>
                    <td className="max-w-[14rem] truncate px-3 py-2 font-mono text-xs">
                      {issue.raw_timestamp || "—"}
                    </td>
                    <td className="px-3 py-2">{issue.exclusion_reason || issue.warning || "—"}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  )
}
