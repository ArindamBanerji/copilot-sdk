import { expect, type Page } from "@playwright/test";

export async function clickTab(page: Page, name: string | RegExp) {
  const tab = page.getByRole("tab", { name });
  if (await tab.count()) {
    await tab.first().click({ timeout: 20_000 });
    return;
  }

  const button = page.getByRole("button", { name });
  if (await button.count()) {
    await button.first().click({ timeout: 20_000 });
    return;
  }

  await page.getByText(name).first().click({ timeout: 20_000 });
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

// Graph-backed DataOps panels can take longer than the former fixture-backed
// responses to settle their first request.
export async function gotoTab(page: Page, tabName: string, timeout = 30_000) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await waitForAppShell(page, timeout);
  await clickTab(page, tabName);
  await waitForAppShell(page, timeout);
}

export async function waitForScreenReady(page: Page, timeout = 30_000) {
  await page.locator('main > [data-screen-ready="true"]').waitFor({ state: "attached", timeout });
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
  if (patterns.length === 0) throw new Error("No patterns");
  let combined = page.getByText(patterns[0]).first();
  for (let i = 1; i < patterns.length; i += 1) {
    combined = combined.or(page.getByText(patterns[i]).first());
  }
  await expect(combined.first()).toBeVisible({ timeout });
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
  page.on("response", (response) => {
    if (response.status() === 503) {
      errors.push(`HTTP 503 ${response.url()}`);
    }
  });
  page.on("console", (message) => {
    if (message.type() === "error") {
      if (/Failed to load resource: the server responded with a status of 503/i.test(message.text())) {
        return;
      }
      errors.push(message.text());
    }
  });
  page.on("pageerror", (error) => {
    errors.push(error.message);
  });
  return errors;
}

export function expectNoConsoleErrors(errors: string[]) {
  const unexpected = errors.filter(
    (error) =>
      !/api\/purchasing\/payment\/summary.*CORS|Failed to load resource: net::ERR_FAILED/i.test(error) &&
      !/HTTP 503 .*\/api\/s2p\/control-tower\/queue\?/i.test(error),
  );
  expect(unexpected, `Unexpected browser console errors:\n${unexpected.join("\n")}`).toEqual([]);
}
