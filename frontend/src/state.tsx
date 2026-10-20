import { useQuery } from "@tanstack/react-query"
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { api } from "./api/client.ts"
import type { DatasetSummary, Filters, Meta } from "./api/types.ts"
import { filterQuery } from "./lib/format.ts"

type Theme = "light" | "dark"

const ThemeContext = createContext<{ theme: Theme; toggle: () => void }>({
  theme: "light",
  toggle: () => undefined,
})

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem("hpm.theme")
    return stored === "dark" ? "dark" : "light"
  })
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark")
    localStorage.setItem("hpm.theme", theme)
  }, [theme])
  const value = useMemo(
    () => ({
      theme,
      toggle: () => setTheme((current) => (current === "dark" ? "light" : "dark")),
    }),
    [theme],
  )
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  return useContext(ThemeContext)
}

interface DatasetContextValue {
  datasets: DatasetSummary[]
  dataset: DatasetSummary | null
  datasetId: string | null
  setDatasetId: (id: string) => void
  loading: boolean
  meta: Meta | undefined
  filters: Filters
  setFilters: (filters: Filters) => void
  query: string
}

const DatasetContext = createContext<DatasetContextValue | null>(null)

const DEFAULT_FILTERS: Filters = {
  case_status: "all",
  channel: "",
  job_family: "",
  outcome: "",
}

export function DatasetProvider({ children }: { children: ReactNode }) {
  const metaQuery = useQuery({ queryKey: ["meta"], queryFn: api.meta })
  const listQuery = useQuery({ queryKey: ["datasets"], queryFn: api.datasets })
  const [datasetId, setDatasetIdState] = useState<string | null>(
    () => localStorage.getItem("hpm.datasetId"),
  )
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS)
  const datasets = listQuery.data?.datasets ?? []
  const dataset = datasets.find((item) => item.id === datasetId) ?? datasets[0] ?? null

  useEffect(() => {
    if (dataset && dataset.id !== datasetId) setDatasetIdState(dataset.id)
    if (dataset) localStorage.setItem("hpm.datasetId", dataset.id)
  }, [dataset, datasetId])

  const value = useMemo<DatasetContextValue>(
    () => ({
      datasets,
      dataset,
      datasetId: dataset?.id ?? null,
      setDatasetId: (id: string) => {
        localStorage.setItem("hpm.datasetId", id)
        setDatasetIdState(id)
        setFilters(DEFAULT_FILTERS)
      },
      loading: listQuery.isLoading,
      meta: metaQuery.data,
      filters,
      setFilters,
      query: filterQuery(filters),
    }),
    [datasets, dataset, filters, listQuery.isLoading, metaQuery.data],
  )
  return <DatasetContext.Provider value={value}>{children}</DatasetContext.Provider>
}

export function useDataset() {
  const value = useContext(DatasetContext)
  if (!value) throw new Error("useDataset must be used inside DatasetProvider")
  return value
}
