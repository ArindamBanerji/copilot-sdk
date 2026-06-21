import type { Page, Response } from "@playwright/test";

export async function waitForScorerResponse(
  page: Page,
  urlPattern: string,
  timeout = 30_000,
): Promise<Response> {
  return page.waitForResponse(
    (response) => response.url().includes(urlPattern) && response.status() < 500,
    { timeout },
  );
}
