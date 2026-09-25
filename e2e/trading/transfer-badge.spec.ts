import { test, expect } from "@playwright/test";
import { collectConsoleErrors, expectNoConsoleErrors } from "../helpers/ui";

const BACKEND_URL = "http://127.0.0.1:8010";

test("transfer status controls dashboard badge", async ({ page, request }) => {
  const errors = collectConsoleErrors(page);
  const response = await request.get(`${BACKEND_URL}/api/transfer/status`);
  expect(response.ok()).toBeTruthy();

  const status = await response.json();
  expect(typeof status.warm_started).toBe("boolean");
  if (status.warm_started === true) {
    expect(typeof status.source_copilot).toBe("string");
    expect(typeof status.patterns_transferred).toBe("number");
  }

  await page.goto("/");
  await expect(page.getByTestId("self-computation-panels")).toBeVisible();
  const badge = page.getByTestId("transfer-badge");
  if ((await badge.count()) > 0) {
    await expect(badge).toContainText(/Warm-started|patterns/i);
  }

  expectNoConsoleErrors(errors);
});

