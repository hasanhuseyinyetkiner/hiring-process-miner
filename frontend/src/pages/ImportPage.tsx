import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { Link } from "react-router-dom"
import { api, ApiError, waitForJob } from "../api/client.ts"
import type { FieldMapping, Preview } from "../api/types.ts"
import { EMPTY_MAPPING } from "../api/types.ts"
import { QualityPanel } from "../components/QualityPanel.tsx"
import { useDataset } from "../state.tsx"

const FIELDS: Array<{ key: keyof FieldMapping; label: string; required?: boolean }> = [
  { key: "case_id", label: "Case id", required: true },
  { key: "activity", label: "Activity", required: true },
  { key: "timestamp", label: "Timestamp", required: true },
  { key: "resource", label: "Resource" },
  { key: "role", label: "Role" },
  { key: "channel", label: "Channel" },
  { key: "outcome", label: "Outcome" },
  { key: "cost", label: "Cost" },
  { key: "job_family", label: "Job family" },
]

export function ImportPage() {
  const queryClient = useQueryClient()
  const { setDatasetId, meta } = useDataset()
  const [draftId, setDraftId] = useState<string | null>(null)
  const [timezone, setTimezone] = useState("UTC")
  const [name, setName] = useState("Synthetic hiring log")
  const [mapping, setMapping] = useState<FieldMapping>(EMPTY_MAPPING)
  const [headers, setHeaders] = useState<string[]>([])
  const [preview, setPreview] = useState<Preview | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [importedId, setImportedId] = useState<string | null>(null)

  async function openPreview(id: string, zone: string, current: FieldMapping) {
    const next = await api.preview(id, current, zone)
    setPreview(next)
    setHeaders(next.headers)
    setMapping(next.applied_mapping)
  }

  async function generate() {
    setBusy(true)
    setMessage(null)
    try {
      const draft = await api.createSynthetic(800, 42)
      setDraftId(draft.draft_id)
      setTimezone(draft.timezone_suggestion)
      setName("Synthetic hiring log")
      await openPreview(draft.draft_id, draft.timezone_suggestion, EMPTY_MAPPING)
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Could not generate the synthetic log.")
    } finally {
      setBusy(false)
    }
  }

  async function upload(file: File) {
    setBusy(true)
    setMessage(null)
    try {
      const draft = await api.createDraft(file)
      setDraftId(draft.draft_id)
      setName(file.name.replace(/\.csv$/i, ""))
      setTimezone("UTC")
      await openPreview(draft.draft_id, "UTC", EMPTY_MAPPING)
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Could not read that file.")
    } finally {
      setBusy(false)
    }
  }

  async function refreshPreview(nextMapping: FieldMapping, nextZone: string) {
    if (!draftId) return
    setMapping(nextMapping)
    setTimezone(nextZone)
    try {
      await openPreview(draftId, nextZone, nextMapping)
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Preview failed.")
    }
  }

  async function commit() {
    if (!draftId) return
    setBusy(true)
    setMessage(null)
    try {
      const job = await api.startImport(draftId, mapping, timezone, name)
      const finished = await waitForJob(job.id)
      if (finished.status !== "SUCCEEDED" || !finished.dataset_id) {
        setMessage(finished.error ?? "Import failed.")
        return
      }
      setImportedId(finished.dataset_id)
      setDatasetId(finished.dataset_id)
      await queryClient.invalidateQueries({ queryKey: ["datasets"] })
      setMessage(null)
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Import failed.")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Import</h1>
        <p className="mt-2 text-sm leading-6 text-[var(--color-muted)]">{meta?.privacy_notice}</p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => void generate()}
          className="rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)] p-5 text-left"
        >
          <p className="text-sm font-semibold">Generate synthetic log</p>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            800 seeded cases with a long interview-scheduling wait. Includes a few rows that should fail validation.
          </p>
        </button>
        <label className="rounded-3xl border border-dashed border-[var(--color-line)] bg-[var(--color-card)] p-5 text-sm">
          Upload CSV
          <input
            aria-label="Upload CSV"
            type="file"
            accept=".csv,text/csv"
            className="mt-3 block w-full text-sm"
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) void upload(file)
            }}
          />
        </label>
      </div>
      {message ? (
        <p role="alert" className="rounded-2xl bg-rose-50 px-3 py-2 text-sm text-rose-900 dark:bg-rose-950/40 dark:text-rose-100">
          {message}
        </p>
      ) : null}
      {busy ? <p role="status">Working…</p> : null}
      {draftId && headers.length > 0 ? (
        <section className="space-y-4 rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)] p-5">
          <h2 className="text-lg font-semibold">Field mapping</h2>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="grid gap-1 text-sm">
              Dataset name
              <input
                className="rounded-xl border border-[var(--color-line)] bg-transparent px-2 py-1.5"
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </label>
            <label className="grid gap-1 text-sm">
              Timezone for naive timestamps
              <input
                data-testid="timezone"
                className="rounded-xl border border-[var(--color-line)] bg-transparent px-2 py-1.5"
                value={timezone}
                onChange={(event) => void refreshPreview(mapping, event.target.value)}
              />
            </label>
            {FIELDS.map((field) => (
              <label key={field.key} className="grid gap-1 text-sm">
                {field.label}
                {field.required ? " (required)" : ""}
                <select
                  data-testid={`mapping-${field.key}`}
                  aria-label={field.label}
                  className="rounded-xl border border-[var(--color-line)] bg-transparent px-2 py-1.5"
                  value={mapping[field.key] ?? ""}
                  onChange={(event) => {
                    const next = { ...mapping, [field.key]: event.target.value || null }
                    void refreshPreview(next, timezone)
                  }}
                >
                  <option value="">{field.required ? "Choose a column" : "Not mapped"}</option>
                  {headers.map((header) => (
                    <option key={header} value={header}>
                      {header}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={() => void commit()}
            className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white"
          >
            Import dataset
          </button>
        </section>
      ) : null}
      {preview?.quality ? <QualityPanel quality={preview.quality} testId="preview-quality" /> : null}
      {importedId ? <ImportedQuality datasetId={importedId} /> : null}
    </div>
  )
}

function ImportedQuality({ datasetId }: { datasetId: string }) {
  const quality = useQuery({
    queryKey: ["quality", datasetId],
    queryFn: () => api.quality(datasetId),
  })
  if (!quality.data) return <p role="status">Loading data quality…</p>
  return (
    <div className="space-y-3">
      <QualityPanel quality={quality.data} />
      <Link to="/map" className="inline-flex text-sm font-semibold text-accent">
        Open process map
      </Link>
    </div>
  )
}
