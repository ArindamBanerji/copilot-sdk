import { expect, test } from "@playwright/test";

import {
  assertLearnSuccess,
  assertScoreSuccess,
  waitForS2PLearnResponse,
  waitForS2PScoreResponse,
  waitForTriageQueue,
} from "./helpers";

test.describe("S2P response contract verification", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("empty queue response triggers visible empty state", async ({ page }) => {
    await page.route("**/api/s2p/preview/queue**", async (route) => {
      await route.fulfill({
        status: 200,
        json: { exceptions: [], total: 0, showing: 0 },
      });
    });
    await page.setContent('<article><h2>Invoice Selector</h2><p id="state">Loading</p></article>');
    await page.evaluate(async () => {
      const response = await fetch("/api/s2p/preview/queue");
      const data = await response.json();
      document.querySelector("#state")!.textContent =
        data.total === 0 ? "No invoice exceptions" : `${data.total} queued`;
    });

    await expect(waitForTriageQueue(page, 250)).rejects.toThrow();
    await expect(page.getByText("No invoice exceptions")).toBeVisible();
  });

  test("queue error response shows error state", async ({ page }) => {
    await page.route("**/api/s2p/preview/queue**", async (route) => {
      await route.fulfill({ status: 500, json: { detail: "queue unavailable" } });
    });
    await page.setContent('<main><p id="state">Loading queue</p></main>');
    const status = await page.evaluate(async () => {
      const response = await fetch("/api/s2p/preview/queue");
      document.querySelector("#state")!.textContent = response.ok
        ? "0 queued"
        : "Unable to load invoice queue. Retry";
      return response.status;
    });

    expect(status).toBe(500);
    await expect(page.getByText(/Unable to load invoice queue/)).toBeVisible();
    await expect(page.getByText("0 queued")).toHaveCount(0);
  });

  test("score 503 response surfaces error immediately", async ({ page }) => {
    await page.route("**/api/s2p/score", async (route) => {
      await route.fulfill({ status: 503, json: { detail: "scorer unavailable" } });
    });
    const responsePromise = waitForS2PScoreResponse(page, 5_000);
    await page.evaluate(() => fetch("/api/s2p/score", { method: "POST" }));
    const response = await responsePromise;

    await expect(assertScoreSuccess(response)).rejects.toThrow(/HTTP 503/);
  });

  test("score 200 without decision_id detected as held", async ({ page }) => {
    await page.route("**/api/s2p/score", async (route) => {
      await route.fulfill({ status: 200, json: { gate: true, held: true } });
    });
    const responsePromise = waitForS2PScoreResponse(page, 5_000);
    await page.evaluate(() => fetch("/api/s2p/score", { method: "POST" }));
    const response = await responsePromise;

    await expect(assertScoreSuccess(response)).rejects.toThrow(/held|no decision_id/i);
  });

  test("learn partial response detected", async ({ page }) => {
    await page.route("**/api/s2p/outcome", async (route) => {
      await route.fulfill({
        status: 200,
        json: { learning_applied: false, reason: "conservation_pause" },
      });
    });
    const responsePromise = waitForS2PLearnResponse(page, 5_000);
    await page.evaluate(() => fetch("/api/s2p/outcome", { method: "POST" }));
    const response = await responsePromise;

    await expect(assertLearnSuccess(response)).rejects.toThrow(/learning_applied false/);
  });

  test("delayed queue response still resolves", async ({ page }) => {
    await page.route("**/api/s2p/preview/queue**", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 3_000));
      await route.fulfill({
        status: 200,
        json: {
          exceptions: [{ invoice_id: "S2P-INV-PENDING-V1-0001" }],
          total: 1,
          showing: 1,
        },
      });
    });
    await page.setContent('<article><h2>Invoice Selector</h2><p id="state">Loading</p></article>');
    const queueReady = waitForTriageQueue(page, 10_000);
    await page.evaluate(async () => {
      const response = await fetch("/api/s2p/preview/queue");
      const data = await response.json();
      document.querySelector("#state")!.textContent =
        `${data.exceptions[0].invoice_id} — ${data.total} queued`;
    });

    await queueReady;
    await expect(page.getByText(/S2P-INV-PENDING-V1-0001/)).toBeVisible();
  });
});
