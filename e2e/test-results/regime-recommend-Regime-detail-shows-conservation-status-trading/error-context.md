# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: trading\regime-recommend.spec.ts >> Regime detail shows conservation status
- Location: trading\regime-recommend.spec.ts:35:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('section').filter({ has: getByRole('heading', { name: 'Market Regime' }) }).first().locator('div').filter({ has: getByRole('heading', { name: 'Detailed Recommendations' }) }).first()
Expected: visible
Timeout: 15000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 15000ms
  - waiting for locator('section').filter({ has: getByRole('heading', { name: 'Market Regime' }) }).first().locator('div').filter({ has: getByRole('heading', { name: 'Detailed Recommendations' }) }).first()

```

# Page snapshot

```yaml
- generic [ref=e4]:
  - banner [ref=e5]:
    - generic [ref=e6]:
      - generic [ref=e7]: $
      - generic [ref=e8]:
        - heading "Trading Copilot" [level=1] [ref=e9]
        - paragraph [ref=e10]: Compounding intelligence workspace
    - generic [ref=e11]:
      - generic "IKS 25" [ref=e12]:
        - generic [ref=e14]: "25"
      - generic [ref=e15]: IKS
  - navigation [ref=e16]:
    - button "Dashboard" [ref=e17] [cursor=pointer]
    - button "Log Trade" [ref=e18] [cursor=pointer]
    - button "Analysis" [ref=e19] [cursor=pointer]
    - button "Performance" [ref=e20] [cursor=pointer]
    - button "Journal" [ref=e21] [cursor=pointer]
    - button "Trade Detail" [ref=e22] [cursor=pointer]
  - main [ref=e23]:
    - generic [ref=e25]:
      - generic [ref=e26]: P
      - generic [ref=e27]: Paper
    - generic [ref=e28]:
      - heading "Dashboard unavailable" [level=2] [ref=e29]
      - paragraph [ref=e30]: Failed to fetch
```

# Test source

```ts
  1  | import type { Page } from "@playwright/test";
  2  | import { test, expect } from "../fixtures/copilot-fixture";
  3  | import { collectConsoleErrors, expectNoConsoleErrors, waitForAppShell } from "../helpers/ui";
  4  | 
  5  | function regimePanel(page: Page) {
  6  |   return page.locator("section", { has: page.getByRole("heading", { name: "Market Regime" }) }).first();
  7  | }
  8  | 
  9  | function detailPanel(page: Page) {
  10 |   return regimePanel(page).locator("div", { has: page.getByRole("heading", { name: "Detailed Recommendations" }) }).first();
  11 | }
  12 | 
  13 | test("Regime detail shows recommendations or unavailable state", async ({ page }) => {
  14 |   await page.goto("/");
  15 |   await waitForAppShell(page);
  16 | 
  17 |   const detail = detailPanel(page);
  18 |   await expect(detail).toBeVisible({ timeout: 15_000 });
  19 |   await expect(
  20 |     detail
  21 |       .getByText(/Allocation context|Shift suggestion|No detailed regime recommendations available|Detailed regime recommendations unavailable/i)
  22 |       .first(),
  23 |   ).toBeVisible();
  24 | });
  25 | 
  26 | test("Regime detail shows regime-neutral context or summary", async ({ page }) => {
  27 |   await page.goto("/");
  28 |   await waitForAppShell(page);
  29 | 
  30 |   const detail = detailPanel(page);
  31 |   await expect(detail).toBeVisible({ timeout: 15_000 });
  32 |   await expect(detail.getByText(/regime-neutral|regime-sensitive|avoid|reduce|increase|hold|Conservation not confirmed|Detailed regime recommendations unavailable|Allocation context/i).first()).toBeVisible();
  33 | });
  34 | 
  35 | test("Regime detail shows conservation status", async ({ page }) => {
  36 |   await page.goto("/");
  37 |   await waitForAppShell(page);
  38 | 
  39 |   const detail = detailPanel(page);
> 40 |   await expect(detail).toBeVisible({ timeout: 15_000 });
     |                        ^ Error: expect(locator).toBeVisible() failed
  41 |   await expect(detail.getByText(/Conservation confirmed|Conservation not confirmed|Loading detailed recommendations|Detailed regime recommendations unavailable/i).first()).toBeVisible();
  42 | });
  43 | 
  44 | test("Regime detail avoids investment-advice wording", async ({ page }) => {
  45 |   await page.goto("/");
  46 |   await waitForAppShell(page);
  47 | 
  48 |   const detail = detailPanel(page);
  49 |   await expect(detail).toBeVisible({ timeout: 15_000 });
  50 |   await expect(detail).not.toContainText(/you should buy|financial advice/i);
  51 | });
  52 | 
  53 | test("Regime detail has no console errors", async ({ page }) => {
  54 |   const errors = collectConsoleErrors(page);
  55 |   await page.goto("/");
  56 |   await waitForAppShell(page);
  57 |   await expect(detailPanel(page)).toBeVisible({ timeout: 15_000 });
  58 | 
  59 |   expectNoConsoleErrors(errors);
  60 | });
  61 | 
  62 | 
```