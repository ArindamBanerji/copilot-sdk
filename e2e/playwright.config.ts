import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  timeout: 30_000,
  retries: 1,
  globalSetup: "./global-setup",
  reporter: [
    ["list"],
    ["html", { open: "never" }],
  ],
  use: {
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    actionTimeout: 10_000,
    ...devices["Desktop Chrome"],
  },
  expect: {
    timeout: 10_000,
  },
  projects: [
    {
      name: "trading",
      testDir: "./trading",
      use: {
        baseURL: "http://localhost:5174",
      },
    },
    {
      name: "purchasing",
      testDir: "./purchasing",
      use: {
        baseURL: "http://localhost:5175",
      },
    },
    {
      name: "dataops",
      testDir: "./dataops",
      use: {
        baseURL: "http://localhost:5176",
      },
    },
    {
      name: "s2p",
      testDir: "./s2p",
      timeout: 60_000,
      expect: { timeout: 10_000 },
      use: {
        baseURL: "http://localhost:5177",
      },
    },
  ],
});
