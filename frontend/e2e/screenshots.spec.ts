import { expect, test, type Page } from "@playwright/test"

async function openDemo(page: Page, theme: "light" | "dark") {
  const response = await page.request.get("http://127.0.0.1:8102/api/datasets")
  const body = (await response.json()) as { datasets: Array<{ id: string; name: string }> }
  const demo =
    body.datasets.find((dataset) => dataset.name === "Demo hiring funnel") ??
    body.datasets.find((dataset) => dataset.name === "Synthetic hiring log") ??
    body.datasets[0]
  expect(demo).toBeTruthy()
  await page.addInitScript(
    ({ id, themeName }) => {
      localStorage.setItem("hpm.datasetId", id)
      localStorage.setItem("hpm.theme", themeName)
    },
    { id: demo.id, themeName: theme },
  )
}

async function shot(page: Page, name: string) {
  await page.screenshot({
    path: `../docs/screenshots/${name}.png`,
    fullPage: false,
  })
}

for (const theme of ["light", "dark"] as const) {
  test(`capture ${theme} screens`, async ({ page }) => {
    await openDemo(page, theme)
    await page.goto("/map")
    await expect(page.getByTestId("node-Interview Scheduled")).toBeVisible()
    await page.getByTestId("node-Interview Scheduled").click()
    await expect(page.getByTestId("details-drawer")).toBeVisible()
    await shot(page, `process-map-${theme}`)

    await page.goto("/bottlenecks")
    await expect(page.getByTestId("insight-card").first()).toContainText("Interview Scheduled")
    await shot(page, `bottlenecks-${theme}`)

    await page.goto("/variants")
    await expect(page.getByTestId("variant-row").first()).toBeVisible()
    await shot(page, `variants-${theme}`)
  })
}
