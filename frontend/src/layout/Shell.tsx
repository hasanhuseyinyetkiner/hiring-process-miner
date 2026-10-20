import {
  BookOpen,
  GitBranch,
  LayoutDashboard,
  ListTree,
  Moon,
  Sun,
  Timer,
  Upload,
  Waypoints,
} from "lucide-react"
import { NavLink, Outlet, useLocation } from "react-router-dom"
import { useDataset, useTheme } from "../state.tsx"

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/import", label: "Import", icon: Upload, end: false },
  { to: "/map", label: "Process map", icon: Waypoints, end: false },
  { to: "/bottlenecks", label: "Bottlenecks", icon: Timer, end: false },
  { to: "/variants", label: "Variants", icon: GitBranch, end: false },
  { to: "/cases", label: "Cases", icon: ListTree, end: false },
  { to: "/methodology", label: "Methodology", icon: BookOpen, end: false },
]

export function Shell() {
  const { theme, toggle } = useTheme()
  const { datasets, dataset, setDatasetId, meta } = useDataset()
  const location = useLocation()
  const fullBleed = location.pathname === "/map"
  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="hidden w-[248px] shrink-0 flex-col bg-[#140e22] text-white md:flex">
        <div className="px-5 pb-4 pt-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-200">
            Hiring
          </p>
          <p className="mt-1 text-lg font-semibold leading-6">Process Miner</p>
        </div>
        <nav aria-label="Primary" className="flex flex-1 flex-col gap-1 px-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-xl px-3 py-2 text-sm ${
                  isActive ? "bg-white/12 text-white" : "text-violet-100/80 hover:bg-white/8"
                }`
              }
            >
              <item.icon size={16} aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <p className="px-5 py-4 text-xs leading-5 text-violet-200/70">
          Local analytics. No candidate decisions are made here.
        </p>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-wrap items-center gap-3 border-b border-[var(--color-line)] px-4 py-3 md:px-6">
          <nav aria-label="Primary mobile" className="flex w-full gap-2 overflow-auto md:hidden">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className="shrink-0 rounded-full border border-[var(--color-line)] px-3 py-1 text-xs"
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <label className="grid min-w-[220px] flex-1 gap-1 text-xs font-medium text-[var(--color-muted)]">
            Dataset
            <select
              aria-label="Dataset"
              className="rounded-xl border border-[var(--color-line)] bg-[var(--color-card)] px-2 py-1.5 text-sm text-[var(--color-ink)]"
              value={dataset?.id ?? ""}
              onChange={(event) => setDatasetId(event.target.value)}
            >
              {datasets.length === 0 ? <option value="">No dataset yet</option> : null}
              {datasets.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} · {item.case_count} cases
                </option>
              ))}
            </select>
          </label>
          {dataset?.synthetic ? (
            <span className="rounded-full bg-violet-100 px-2 py-1 text-xs font-semibold text-violet-900 dark:bg-violet-950 dark:text-violet-100">
              Synthetic
            </span>
          ) : null}
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-full border border-[var(--color-line)] bg-[var(--color-card)] px-3 py-1.5 text-sm"
            aria-pressed={theme === "dark"}
            onClick={toggle}
          >
            {theme === "dark" ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
            {theme === "dark" ? "Light" : "Dark"}
          </button>
        </header>
        {meta?.demo_banner ? (
          <div className="bg-accent px-4 py-1.5 text-center text-xs font-semibold text-white">
            {meta.demo_banner_text}
          </div>
        ) : null}
        <main
          className={
            fullBleed
              ? "flex min-h-0 flex-1 flex-col overflow-hidden"
              : "min-h-0 flex-1 overflow-auto px-4 py-5 md:px-6"
          }
        >
          <Outlet />
        </main>
      </div>
    </div>
  )
}
