import { defineConfig, devices } from "@playwright/test";

// Overridable so a manual verification run can use scratch ports instead of colliding
// with a backend/frontend you already have running for everyday development.
const BACKEND_PORT = process.env.PW_BACKEND_PORT ?? "8010";
const FRONTEND_PORT = process.env.PW_FRONTEND_PORT ?? "3100";
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const FRONTEND_URL = `http://127.0.0.1:${FRONTEND_PORT}`;
const isCI = !!process.env.CI;

/**
 * Full-stack end-to-end tests: a real browser against a real backend, database and
 * frontend build. No mocks anywhere in this suite (that's what the unit/component
 * tests are for).
 *
 * Locally, both servers are self-managed (see `webServer` below): if you already have
 * them running (e.g. while manually testing) Playwright reuses them; otherwise it
 * starts its own. Either way, the backend reads its normal `backend/.env`, so it uses
 * whatever database you already have configured there.
 *
 * In CI, `reuseExistingServer` is off, so a fresh backend and frontend are always
 * started against the Postgres service container, using the env vars the workflow
 * sets (see .github/workflows/ci.yml).
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // every test shares one player-generated dataset; keep it simple
  retries: isCI ? 1 : 0, // a flaky CI runner gets one retry; a local failure should be real
  reporter: isCI ? [["github"], ["html", { open: "never" }]] : "list",
  timeout: 60_000,
  // A freshly-started stack (first migration, first seed, first query, first compile)
  // is visibly slower than a warm one; the default 5s per assertion is too tight for
  // that first minute, without being so long that a genuine hang goes unnoticed.
  expect: { timeout: 15_000 },
  use: {
    baseURL: FRONTEND_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      // Real installed Chrome, not Playwright's bundled Chromium: it's already present
      // on this machine and on GitHub's ubuntu runners, so no separate browser download
      // (`playwright install`) is needed anywhere.
      use: { ...devices["Desktop Chrome"], channel: "chrome" },
    },
  ],
  webServer: [
    {
      command:
        `uv run alembic upgrade head && uv run python -m scripts.seed && uv run uvicorn app.main:app --port ${BACKEND_PORT}`,
      cwd: "../backend",
      url: `${BACKEND_URL}/health/ready`,
      reuseExistingServer: !isCI,
      timeout: 120_000,
      stdout: "pipe",
    },
    {
      // Built, not `next dev`: a real production build is both faster to run
      // repeatedly and closer to what actually ships.
      command: `npm run build && npm run start -- -p ${FRONTEND_PORT}`,
      cwd: ".",
      url: FRONTEND_URL,
      reuseExistingServer: !isCI,
      timeout: 180_000,
      env: { BACKEND_URL },
      stdout: "pipe",
    },
  ],
});
