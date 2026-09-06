import { chromium } from "@playwright/test";

const HOST = process.env.COPILOT_HOST || "127.0.0.1";

const FRONTENDS = [
  `http://${HOST}:5174`,
  `http://${HOST}:5175`,
  `http://${HOST}:5176`,
  `http://${HOST}:5177`,
];

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export default async function globalSetup() {
  const browser = await chromium.launch();
  try {
    await Promise.all(
      FRONTENDS.map(async (url) => {
        const page = await browser.newPage();
        try {
          await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30_000 });
          await page.locator("main").waitFor({ state: "attached", timeout: 15_000 });
        } catch (error) {
          console.warn(`[global-setup] frontend warmup skipped for ${url}: ${errorMessage(error)}`);
        } finally {
          await page.close();
        }
      }),
    );
  } finally {
    await browser.close();
  }
}
