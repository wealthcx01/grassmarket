import { defineConfig, devices } from "@playwright/test";

/**
 * Browser end-to-end tests (GRS-0019). These drive a REAL browser against a locally-running app,
 * so we know the deliverables workflow works for a human, not just in jsdom.
 *
 * Prerequisites (a developer's normal local setup):
 *   1. Backend running + seeded:  uv run python scripts/seed_dev.py  then
 *      GM_JWT_SECRET=… uv run uvicorn grassmarket.web.main:app --port 8000
 *   2. Frontend running:          npm run dev   (http://localhost:3000)
 * Override the base URL with E2E_BASE_URL if needed.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    headless: true,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
