import { useQuery } from "@tanstack/react-query"
import { api } from "../api/client.ts"
import { ErrorBlock, LoadingBlock } from "../components/States.tsx"

export function MethodologyPage() {
  const methodology = useQuery({ queryKey: ["methodology"], queryFn: api.methodology })
  if (methodology.isLoading) return <LoadingBlock label="Loading methodology" />
  if (methodology.error || !methodology.data) {
    return <ErrorBlock message={methodology.error?.message ?? "Could not load methodology."} />
  }
  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Methodology</h1>
        <p className="mt-2 text-sm text-[var(--color-muted)]">
          Contract <code>{methodology.data.ordering_contract}</code>. These paragraphs are served by the API so the
          screen matches the code that computed the numbers.
        </p>
      </div>
      {methodology.data.sections.map((section) => (
        <section key={section.id} className="rounded-3xl border border-[var(--color-line)] bg-[var(--color-card)] p-5">
          <h2 className="text-lg font-semibold">{section.title}</h2>
          <p className="mt-2 text-sm leading-6 text-[var(--color-muted)]">{section.body}</p>
        </section>
      ))}
    </div>
  )
}
