import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, waitForAppShell, waitForScreenReady } from "../helpers/ui";

const directiveText = /reduce\s+size|\bavoid\b|\bhold\s+sizing\b|\b(buy|sell)\b/i;

async function openTab(page: Parameters<typeof clickTab>[0], name: string) {
  await clickTab(page, name);
  await waitForAppShell(page);
}

test("SAFE-PW-01 trading tabs contain no directive phrases", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  for (const tab of ["Dashboard", "Analysis", "Performance", "Journal"]) {
    await openTab(page, tab);
    await expect(page.locator("main")).not.toContainText(directiveText);
  }
});

test("SAFE-PW-02 trading tabs expose no buy or sell action text", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  for (const tab of ["Dashboard", "Analysis", "Performance", "Journal"]) {
    await openTab(page, tab);
    await expect(page.locator("main")).not.toContainText(/(^|\s)(buy|sell)(\s|$)/i);
  }
});

test("SAFE-PW-03 pattern insights use observation language", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await openTab(page, "Analysis");
  await waitForScreenReady(page);
  const mainText = await page.locator("main").innerText();
  expect(mainText).not.toMatch(/reduce\s+size|\bavoid\b|\bhold\s+sizing\b/i);
  expect(mainText).toMatch(/Observation:|Behavioral Pattern Detection|Pattern detection unavailable/i);
});

test("SAFE-PW-04 regime panel uses observation language", async ({ page }) => {
  await page.goto("/");
  await waitForAppShell(page);
  await openTab(page, "Performance");
  const panel = page.getByTestId("regime-recommendation");
  await expect(panel).toBeVisible();
  await expect(panel).not.toContainText(/recommendation|reduce\s+size|\bavoid\b|\bhold\s+sizing\b/i);
  await expect(panel).toContainText(/observation|Loading/i);
});
