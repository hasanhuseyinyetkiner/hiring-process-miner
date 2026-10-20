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

export function QualityPanel({
  quality,
  testId = "quality-panel",
}: {
  quality: QualityReport
  testId?: string
}) {
  return (
    <section data-testid={testId} className="space-y-4" aria-labelledby={`${testId}-heading`}>
      <div>
        <h2 id={`${testId}-heading`} className="text-lg font-semibold">
          Data quality
        </h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">{quality.eligible_definition}</p>
      </div>
      <dl className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
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
      {quality.issue_sample.length > 0 ? (
        <div className="overflow-x-auto rounded-2xl border border-[var(--color-line)]">
          <table className="min-w-full text-left text-sm">
            <caption className="sr-only">Sample of excluded or warned rows</caption>
            <thead className="bg-[var(--color-canvas)] text-xs uppercase tracking-wide text-[var(--color-muted)]">
              <tr>
                <th className="px-3 py-2">Row</th>
                <th className="px-3 py-2">Case</th>
                <th className="px-3 py-2">Activity</th>
                <th className="px-3 py-2">Reason</th>
              </tr>
            </thead>
            <tbody>
              {quality.issue_sample.slice(0, 8).map((issue) => (
                <tr key={`${issue.source_row}-${issue.exclusion_reason}`} className="border-t border-[var(--color-line)]">
                  <td className="px-3 py-2">{issue.source_row}</td>
                  <td className="px-3 py-2">{issue.case_id || "—"}</td>
                  <td className="px-3 py-2">{issue.activity || "—"}</td>
                  <td className="px-3 py-2">{issue.exclusion_reason || issue.warning || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  )
}
