import { test, expect } from "../fixtures/copilot-fixture";
import { expectAnyText, waitForAppShell } from "../helpers/ui";

test("weather endpoint returns forecast data", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:8020/api/context/weather");
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(typeof data).toBe("object");
});

test("weather endpoint returns category risk levels", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page, 20_000);
  const card = page.locator("section", { hasText: "Weather Intelligence" });
  await expect(card).toBeVisible({ timeout: 20_000 });
  await expect(card.getByText(/Checking the forecast/i)).toBeHidden({ timeout: 20_000 });
  await expect(card.getByText(/^Produce$/i)).toBeVisible();
  await expect(card.getByText(/^Seafood$/i)).toBeVisible();
  await expect(card.getByText(/^Dairy$/i)).toBeVisible();
  await expect(card.getByText(/^Dry goods$/i)).toBeVisible();
});

test("weather impact card renders on dashboard", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Weather Intelligence")).toBeVisible();
});

test("weather card shows provenance badge", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("OpenMeteo")).toBeVisible();
});

test("weather card shows storm alert or calm state", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Storm forecast tomorrow/i, /Calm forecast/i, /Heat tomorrow/i]);
});

test("weather flow verifies forecast strip and kitchen language", async ({ page }) => {
  await page.goto("/");
  await expectAnyText(page, [/Today/i, /Weather changes tomorrow/i]);
  await expectAnyText(page, [/Seafood/i, /normal ordering plan/i, /Check cooler space/i]);
  const card = page.locator("section", { hasText: "Weather Intelligence" });
  await expect(card).not.toContainText(/centroid|DK weight|sigma|factor vector|N=/i);
});
