import { defineConfig, devices } from "@playwright/test";

const HOST = process.env.COPILOT_HOST || "127.0.0.1";

export default defineConfig({
  timeout: 30_000,
  retries: 1,
  workers: parseInt(process.env.CI_WORKERS || "1", 10),
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
        baseURL: `http://${HOST}:5174`,
      },
    },
    {
      name: "graph-integration",
      testDir: "./graph-integration",
      testMatch: /.*\.spec\.ts/,
      workers: 1,
      use: {
        baseURL: `http://${HOST}:5174`,
        extraHTTPHeaders: { "X-Graph-Integration": "age" },
      },
    },
    {
      name: "purchasing",
      testDir: "./purchasing",
      use: {
        baseURL: `http://${HOST}:5175`,
      },
    },
    {
      name: "dataops",
      testDir: "./dataops",
      use: {
        baseURL: `http://${HOST}:5176`,
      },
    },
    {
      name: "s2p",
      testDir: "./s2p",
      timeout: 60_000,
      expect: { timeout: 10_000 },
      use: {
        baseURL: `http://${HOST}:5177`,
      },
    },
    {
      name: "demo-cuts",
      testDir: "./demo-cuts",
      testMatch: ["vc-cut.spec.ts", "trader-cut.spec.ts", "enterprise-cut.spec.ts"],
      workers: 1,
      use: {},
    },
    {
      name: "demo",
      testDir: "./demo",
      testMatch: ["platform/**/*.spec.ts", "machine/**/*.spec.ts", "pilot/**/*.spec.ts", "fork/**/*.spec.ts"],
      workers: 1,
      use: {},
    },
    {
      name: "demo-soc",
      testDir: "./demo/soc",
      testMatch: /.*\.spec\.ts/,
      workers: 1,
      use: {},
    },
    {
      name: "demo-s2p",
      testDir: "./demo/s2p",
      testMatch: /.*\.spec\.ts/,
      workers: 1,
      use: {},
    },
    {
      name: "demo-purchasing",
      testDir: "./demo/purchasing",
      testMatch: /.*\.spec\.ts/,
      workers: 1,
      use: {},
    },
    {
      name: "demo-trading",
      testDir: "./demo/trading",
      testMatch: /.*\.spec\.ts/,
      workers: 1,
      use: {},
    },
    {
      name: "demo-dataops",
      testDir: "./demo/dataops",
      testMatch: /.*\.spec\.ts/,
      workers: 1,
      use: {},
    },
  ],
});
