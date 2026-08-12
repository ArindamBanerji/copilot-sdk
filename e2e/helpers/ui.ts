import { expect, type Page } from "@playwright/test";

export async function clickTab(page: Page, name: string | RegExp) {
  const tab = page.getByRole("tab", { name });
  if (await tab.count()) {
    await tab.first().click();
    return;
  }

  const button = page.getByRole("button", { name });
  if (await button.count()) {
    await button.first().click();
    return;
  }

  await page.getByText(name).first().click();
}

export async function waitForAppShell(page: Page, timeout = 25_000) {
  await page.waitForLoadState("domcontentloaded", { timeout });
  await page.locator("main").waitFor({ state: "attached", timeout });
  await expect(page.locator("main")).not.toBeEmpty({ timeout });
  await expect(page.locator("main")).not.toContainText(
    /^P?PaperLoading (analysis|performance|dashboard|journal|trade detail)\.\.\.$/i,
    { timeout },
  );
}

export async function gotoTab(page: Page, tabName: string, timeout = 15_000) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await waitForAppShell(page, timeout);
  await clickTab(page, tabName);
  await waitForAppShell(page, timeout);
}

export async function waitForScreenReady(page: Page, timeout = 15_000) {
  await page.locator('main > [data-screen-ready="true"]').waitFor({ state: "attached", timeout });
  await expect(page.locator('main [data-panel-ready="false"]')).toHaveCount(0, { timeout });
}

export async function navigateToTab(page: Page, tabName: string) {
  await clickTab(page, tabName);
}

export async function expectAnyText(
  page: Page,
  patterns: Array<RegExp | string>,
  options: { timeout?: number } = {},
) {
  const timeout = options.timeout ?? 10_000;
  const deadline = Date.now() + timeout;
  let lastError = "";

  while (Date.now() < deadline) {
    for (const pattern of patterns) {
      const locator = page.getByText(pattern).first();
      try {
        await expect(locator).toBeVisible({ timeout: 300 });
        return;
      } catch (error) {
        lastError = error instanceof Error ? error.message : String(error);
      }
    }
    await page.waitForTimeout(200);
  }

  throw new Error(
    `Expected one of these texts to become visible within ${timeout}ms: ${patterns
      .map(String)
      .join(", ")}${lastError ? `\nLast error: ${lastError}` : ""}`,
  );
}

export async function expectTrajectoryOrEmpty(page: Page) {
  const chart = page.locator("main svg").first();
  try {
    await expect(chart).toBeVisible({ timeout: 2_000 });
    return;
  } catch {
    await expectAnyText(page, [/No trajectory points available/i], { timeout: 8_000 });
  }
}

export function collectConsoleErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(message.text());
    }
  });
  page.on("pageerror", (error) => {
    errors.push(error.message);
  });
  return errors;
}

export function expectNoConsoleErrors(errors: string[]) {
  expect(errors, `Unexpected browser console errors:\n${errors.join("\n")}`).toEqual([]);
}
