import { expect, test } from "@playwright/test"
import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const here = path.dirname(fileURLToPath(import.meta.url))

test("import a synthetic log and inspect the map, bottleneck, variants, and export", async ({
  page,
}) => {
  await page.goto("/import")
  await page.getByRole("button", { name: /Generate synthetic log/ }).click()
  await expect(page.getByTestId("mapping-case_id")).toHaveValue("case_id", { timeout: 60_000 })
  await expect(page.getByTestId("timezone")).toHaveValue("Europe/Berlin")
  await page.getByRole("button", { name: "Import dataset" }).click()
  const quality = page.getByTestId("quality-panel")
  await expect(quality).toBeVisible({ timeout: 60_000 })
  await expect(quality.getByTestId("quality-cases")).not.toHaveText("0")
  await expect(quality).toContainText("Ambiguous local times")
  await page.getByRole("link", { name: "Open process map" }).click()
  await expect(page.getByTestId("node-Interview Scheduled")).toBeVisible()
  const before = await page.getByTestId("visible-edges").innerText()
  await page.getByTestId("edge-slider").fill("50")
  await expect(page.getByTestId("visible-edges")).not.toHaveText(before)
  await page.getByTestId("node-Interview Scheduled").click()
  await expect(page.getByTestId("details-drawer")).toContainText("Cases")

  await expect(page.getByTestId("export-bar")).toBeVisible()
  const downloadDir = path.join(here, "..", "test-results", "exports")
  fs.mkdirSync(downloadDir, { recursive: true })
  const csvDownload = page.waitForEvent("download")
  await page.getByTestId("export-csv").click()
  const csv = await csvDownload
  await csv.saveAs(path.join(downloadDir, "hiring-summary.csv"))
  expect(csv.suggestedFilename()).toContain("csv")

  const svgDownload = page.waitForEvent("download")
  await page.getByTestId("export-svg").click()
  const svg = await svgDownload
  await svg.saveAs(path.join(downloadDir, "hiring-process-map.svg"))
  expect(svg.suggestedFilename()).toContain("svg")

  const htmlDownload = page.waitForEvent("download")
  await page.getByTestId("export-html").click()
  const html = await htmlDownload
  await html.saveAs(path.join(downloadDir, "hiring-report.html"))
  expect(html.suggestedFilename()).toContain("html")

  await page.goto("/bottlenecks")
  const card = page.getByTestId("insight-card").first()
  await expect(card).toContainText("Numerator")
  await expect(card).toContainText("Sample size")
  await expect(card).toContainText("Method")
  await expect(card).toContainText("Interview Scheduled")
  await expect(page.getByTestId("conformance-panel")).toBeVisible()
  await expect(page.getByTestId("conformance-model")).not.toHaveValue("")
  await page.goto("/variants")
  await expect(page.getByTestId("variant-row").first()).toBeVisible()
})
