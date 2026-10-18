import { test, expect } from "@playwright/test";
import { collectConsoleErrors, expectNoConsoleErrors, waitForScreenReady } from "../helpers/ui";

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

  await page.route("**/api/transfer/status", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ warm_started: false }),
    });
  });

  await page.goto("/");
  await waitForScreenReady(page);
  const badge = page.getByTestId("transfer-badge");
  await expect(badge).toHaveCount(0);

  expectNoConsoleErrors(errors);
});
