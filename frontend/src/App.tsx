import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter, Route, Routes } from "react-router-dom"
import { Shell } from "./layout/Shell.tsx"
import { BottlenecksPage } from "./pages/BottlenecksPage.tsx"
import { CasesPage } from "./pages/CasesPage.tsx"
import { ImportPage } from "./pages/ImportPage.tsx"
import { MapPage } from "./pages/MapPage.tsx"
import { MethodologyPage } from "./pages/MethodologyPage.tsx"
import { OverviewPage } from "./pages/OverviewPage.tsx"
import { VariantsPage } from "./pages/VariantsPage.tsx"
import { DatasetProvider, ThemeProvider } from "./state.tsx"

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <DatasetProvider>
          <BrowserRouter>
            <Routes>
              <Route element={<Shell />}>
                <Route index element={<OverviewPage />} />
                <Route path="import" element={<ImportPage />} />
                <Route path="map" element={<MapPage />} />
                <Route path="bottlenecks" element={<BottlenecksPage />} />
                <Route path="variants" element={<VariantsPage />} />
                <Route path="cases" element={<CasesPage />} />
                <Route path="methodology" element={<MethodologyPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </DatasetProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
