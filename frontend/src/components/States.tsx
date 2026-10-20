import type { ReactNode } from "react"
import { Link } from "react-router-dom"

export function LoadingBlock({ label = "Loading analytics" }: { label?: string }) {
  return (
    <div role="status" className="grid gap-3" aria-live="polite">
      <span className="sr-only">{label}</span>
      <div className="h-24 animate-pulse rounded-2xl bg-white/70 dark:bg-white/5" />
      <div className="h-40 animate-pulse rounded-2xl bg-white/70 dark:bg-white/5" />
    </div>
  )
}

export function ErrorBlock({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-100"
    >
      {message}
    </div>
  )
}

export function EmptyBlock({
  title,
  body,
  action,
}: {
  title: string
  body: string
  action?: ReactNode
}) {
  return (
    <div className="rounded-3xl border border-dashed border-[var(--color-line)] bg-[var(--color-card)] px-6 py-12 text-center">
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="mx-auto mt-2 max-w-lg text-sm text-[var(--color-muted)]">{body}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  )
}

export function ImportLink() {
  return (
    <Link
      to="/import"
      className="inline-flex rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white"
    >
      Import an event log
    </Link>
  )
}
