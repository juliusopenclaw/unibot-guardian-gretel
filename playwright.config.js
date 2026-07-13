import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/browser",
  timeout: 30_000,
  fullyParallel: false,
  retries: 0,
  reporter: "line",
  use: {
    browserName: "chromium",
    headless: true,
    viewport: { width: 380, height: 780 },
    trace: "retain-on-failure"
  }
});
