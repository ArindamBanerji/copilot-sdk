import { test, expect } from "@playwright/test";
import { collectConsoleErrors, expectNoConsoleErrors } from "../helpers/ui";

const BACKEND_URL = "http://127.0.0.1:8020";

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
  const badge = page.getByTestId("transfer-badge");

  if (status.warm_started === true) {
    await expect(badge).toBeVisible();
    await expect(badge).toContainText(`Warm-started from ${status.source_copilot}`);
    await expect(badge).toContainText(`${status.patterns_transferred} patterns`);
  } else {
    await expect(badge).toHaveCount(0);
  }

  expectNoConsoleErrors(errors);
});
