import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  timeout: 30_000,
  retries: 1,
  reporter: "line",
  use: { ...devices["Desktop Chrome"], headless: true },
});
