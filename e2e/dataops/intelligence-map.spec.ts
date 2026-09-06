import { type Locator, type Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell } from "../helpers/ui";

const DATAOPS_FRONTEND_URL = process.env.DATAOPS_FRONTEND_URL ?? "http://127.0.0.1:5176";
const DATAOPS_API_URL = process.env.DATAOPS_API_URL ?? "http://127.0.0.1:8030";

function panelByHeading(page: Page, heading: string | RegExp): Locator {
  return page
    .locator("h1, h2, h3, h4, p", { hasText: heading })
    .locator("xpath=ancestor::*[self::article or self::section or contains(concat(' ', normalize-space(@class), ' '), ' copilot-card ')][1]")
    .first();
}

async function mockEmptyDIProfiles(page: Page) {
  await page.route(/https?:\/\/127\.0\.0\.1:8030\/api\/di\/profiles$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ sources: [], total: 0 }),
    });
  });
  await page.route(/https?:\/\/127\.0\.0\.1:8030\/api\/di\/intelligence-map$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ nodes: [], edges: [], gold_lines: [] }),
    });
  });
}

async function gotoInsight(page: Page) {
  await mockEmptyDIProfiles(page);
  await page.goto(DATAOPS_FRONTEND_URL);
  await waitForAppShell(page);
  await clickTab(page, "Insight");
  await expect(panelByHeading(page, "Intelligence Map")).toBeVisible({ timeout: 20_000 });
  await page.locator('[data-testid="intelligence-map"][data-screen-ready="true"]').waitFor({ timeout: 20_000 });
}

test.describe("DataOps Intelligence Map", () => {
  test("atomic: Intelligence Map panel appears on the Insight screen with empty state", async ({ page }) => {
    await gotoInsight(page);

    const map = panelByHeading(page, "Intelligence Map");
    await expect(map).toBeVisible();
    await expect(map.getByText("Source trust and quality graph")).toBeVisible();
    await expect(map.getByText("No connected sources.")).toBeVisible();
    await expect(map.getByText("Add connectors to build your intelligence map.")).toBeVisible();
  });

  test("atomic: empty DI registry does not render fabricated correlations or source labels", async ({ page }) => {
    await gotoInsight(page);

    const map = panelByHeading(page, "Intelligence Map");
    await expect(map.getByText("Add connectors to build your intelligence map.")).toBeVisible();
    await expect(map.getByText(/^SAP$/i)).toHaveCount(0);
    await expect(map.getByText(/^Celonis$/i)).toHaveCount(0);
    await expect(map.getByText(/^Graph$/i)).toHaveCount(0);
    await expect(map.getByText(/^source-\d+$/i)).toHaveCount(0);
    await expect(map.locator("svg line, svg path")).toHaveCount(0);
  });

  test("atomic: DI profiles API returns collection shape", async ({ request }) => {
    const response = await request.get(`${DATAOPS_API_URL}/api/di/profiles`);
    expect(response.status()).toBe(200);

    const payload = await response.json();
    expect(Array.isArray(payload.sources)).toBeTruthy();
    expect(typeof payload.total).toBe("number");
  });

  test("flow: dashboard navigation reaches Intelligence Map in Insight context", async ({ page }) => {
    await mockEmptyDIProfiles(page);
    await page.goto(DATAOPS_FRONTEND_URL);
    await waitForAppShell(page);
    await expect(page.getByRole("heading", { name: "DataOps Copilot" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Insight" })).toBeVisible();

    await clickTab(page, "Insight");
    await expect(panelByHeading(page, "Process Timeline")).toBeVisible();
    const map = panelByHeading(page, "Intelligence Map");
    await expect(map).toBeVisible();
    await page.locator('[data-testid="intelligence-map"][data-screen-ready="true"]').waitFor({ timeout: 20_000 });
    await expect(map.getByText("No connected sources.")).toBeVisible();
    await expect(map.getByText(/Could not load DI source profiles/i)).toHaveCount(0);
    await expect(panelByHeading(page, "Cross-Graph Insight")).toBeVisible();
  });

  test("flow: reload preserves a valid path back to the Intelligence Map", async ({ page }) => {
    await gotoInsight(page);
    await expect(panelByHeading(page, "Intelligence Map").getByText("No connected sources.")).toBeVisible();

    await page.reload();
    await waitForAppShell(page);
    if ((await panelByHeading(page, "Intelligence Map").count()) === 0) {
      await clickTab(page, "Insight");
    }

    const map = panelByHeading(page, "Intelligence Map");
    await expect(map).toBeVisible();
    await page.locator('[data-testid="intelligence-map"][data-screen-ready="true"]').waitFor({ timeout: 20_000 });
    await expect(map.getByText("No connected sources.")).toBeVisible();
    await expect(map.getByText(/Could not load DI source profiles/i)).toHaveCount(0);
  });
});
