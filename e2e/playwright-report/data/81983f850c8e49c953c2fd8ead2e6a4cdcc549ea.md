# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dataops\insight.spec.ts >> decision explorer shows real categories not just unknown
- Location: dataops\insight.spec.ts:58:1

# Error details

```
Error: dataops backend is not healthy at http://localhost:8030/health. Start the live stack before running E2E tests. apiRequestContext.get: read ECONNRESET
Call log:
  - → GET http://localhost:8030/health
    - user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.7727.15 Safari/537.36
    - accept: */*
    - accept-encoding: gzip,deflate,br

```

# Test source

```ts
  1  | import { test as base, expect } from "@playwright/test";
  2  | 
  3  | const BACKEND_PORTS = {
  4  |   trading: 8010,
  5  |   purchasing: 8020,
  6  |   dataops: 8030,
  7  | } as const;
  8  | 
  9  | type CopilotProject = keyof typeof BACKEND_PORTS;
  10 | 
  11 | function isCopilotProject(name: string): name is CopilotProject {
  12 |   return name in BACKEND_PORTS;
  13 | }
  14 | 
  15 | export const test = base.extend<{ backendHealth: void }>({
  16 |   backendHealth: [
  17 |     async ({ request }, use, testInfo) => {
  18 |       const projectName = testInfo.project.name;
  19 |       if (!isCopilotProject(projectName)) {
  20 |         throw new Error(`Unknown copilot Playwright project "${projectName}". Expected trading, purchasing, or dataops.`);
  21 |       }
  22 | 
  23 |       const port = BACKEND_PORTS[projectName];
  24 |       const healthUrl = `http://localhost:${port}/health`;
  25 |       let responseText = "";
  26 | 
  27 |       try {
  28 |         const response = await request.get(healthUrl, { timeout: 5_000 });
  29 |         responseText = await response.text().catch(() => "");
  30 |         if (!response.ok()) {
  31 |           throw new Error(`HTTP ${response.status()} ${response.statusText()} ${responseText}`.trim());
  32 |         }
  33 |       } catch (error) {
  34 |         const message = error instanceof Error ? error.message : String(error);
> 35 |         throw new Error(
     |               ^ Error: dataops backend is not healthy at http://localhost:8030/health. Start the live stack before running E2E tests. apiRequestContext.get: read ECONNRESET
  36 |           `${projectName} backend is not healthy at ${healthUrl}. Start the live stack before running E2E tests. ${message}`,
  37 |         );
  38 |       }
  39 | 
  40 |       await use();
  41 |     },
  42 |     { auto: true },
  43 |   ],
  44 | });
  45 | 
  46 | export { expect };
  47 | 
```