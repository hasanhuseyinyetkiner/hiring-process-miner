import { expect, test } from "@playwright/test"

test("accessibility smoke on overview, map, bottlenecks, and variants", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByRole("navigation", { name: /primary/i }).first()).toBeVisible()
  await expect(page.getByRole("main")).toBeVisible()
  await expect(page.getByLabel("Dataset")).toBeVisible()
  await expect(page.getByRole("button", { name: /dark|light/i })).toBeVisible()

  await page.getByRole("link", { name: "Process map" }).click()
  await expect(page.getByRole("main")).toBeVisible()
  await expect(page.getByTestId("node-Interview Scheduled")).toBeVisible({ timeout: 60_000 })

  await page.getByRole("link", { name: "Bottlenecks" }).click()
  await expect(page.getByRole("main")).toBeVisible()
  await expect(page.getByRole("heading", { name: "Bottlenecks" })).toBeVisible({ timeout: 60_000 })
  await expect(page.getByTestId("insight-card").first()).toBeVisible()

  await page.getByRole("link", { name: "Variants" }).click()
  await expect(page.getByRole("main")).toBeVisible()
  await expect(page.getByTestId("variant-row").first()).toBeVisible({ timeout: 60_000 })

  await page.getByRole("link", { name: "Import" }).click()
  await expect(page.getByRole("main")).toBeVisible()
  await expect(page.getByRole("button", { name: /Generate synthetic log/ })).toBeVisible()
})
