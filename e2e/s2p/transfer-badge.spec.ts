import { test, expect, type APIRequestContext } from "@playwright/test";
import { collectConsoleErrors, expectNoConsoleErrors } from "../helpers/ui";

const FRONTEND = "http://127.0.0.1:5177";
const BACKEND = "http://127.0.0.1:8002";

interface TransferStatus {
  warm_started?: boolean;
  source_copilot?: string;
  patterns_transferred?: number;
  transferred_at?: string | null;
}

async function fetchTransferStatus(request: APIRequestContext): Promise<TransferStatus> {
  const response = await request.get(`${BACKEND}/api/transfer/status`);
  expect(response.ok()).toBeTruthy();
  return response.json();
}

function assertTransferStatusShape(status: TransferStatus) {
  expect(typeof status.warm_started).toBe("boolean");
  if (status.warm_started) {
    expect(typeof status.source_copilot).toBe("string");
    expect(typeof status.patterns_transferred).toBe("number");
    expect(status.patterns_transferred).toBeGreaterThan(0);
    if (status.transferred_at !== null && status.transferred_at !== undefined) {
      expect(typeof status.transferred_at).toBe("string");
    }
  }
}

test("transfer status API returns valid shape", async ({ request }) => {
  const status = await fetchTransferStatus(request);

  assertTransferStatusShape(status);
});

test("transfer status controls dashboard badge", async ({ page }) => {
  const status = await fetchTransferStatus(page.request);

  await page.goto(FRONTEND);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

  const badge = page.getByTestId("transfer-badge");
  if (status.warm_started) {
    await expect(badge).toBeVisible();
    await expect(badge).toContainText(`Warm-started from ${status.source_copilot}`);
    await expect(badge).toContainText(`${status.patterns_transferred} patterns`);
  } else {
    await expect(badge).toHaveCount(0);
  }
});

test("dashboard with transfer badge has no console errors", async ({ page }) => {
  const errors = collectConsoleErrors(page);

  await page.goto(FRONTEND);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await page.waitForTimeout(500);

  expectNoConsoleErrors(errors);
});
