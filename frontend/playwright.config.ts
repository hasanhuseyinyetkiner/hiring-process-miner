import { defineConfig } from "@playwright/test"

const apiEnv = {
  ...process.env,
  APP_ENV: "demo",
  SEED_ON_STARTUP: "true",
  DATABASE_URL: "sqlite:///./data/screenshots.sqlite",
  HPM_RESET_DB: "1",
  HOST: "127.0.0.1",
  PORT: "8102",
  ALLOW_NETWORK_BIND: "false",
}

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  use: {
    baseURL: "http://127.0.0.1:5102",
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "uv run hpm",
      cwd: "..",
      url: "http://127.0.0.1:8102/ready",
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
      env: apiEnv,
    },
    {
      command: "pnpm exec vite --host 127.0.0.1 --port 5102 --strictPort",
      url: "http://127.0.0.1:5102",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: {
        browserName: "chromium",
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 2,
      },
    },
  ],
})
