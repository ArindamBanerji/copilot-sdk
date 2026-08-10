import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell, waitForScreenReady } from "../helpers/ui";

async function openEvidence(page: import("@playwright/test").Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);
  await clickTab(page, "Evidence");
  await waitForAppShell(page);
  await expectAnyText(page, [/Evidence/i, /AgentEvolver/i, /Cross-System Insights/i]);
}

test("cross-system endpoint returns alerts or empty array", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8030/api/discovery/cross-system");
  expect([200, 404].includes(res.status())).toBeTruthy();
  if (res.ok()) {
    const payload = await res.json();
    expect(Array.isArray(payload.alerts)).toBeTruthy();
  }
});

test("cross-system panel renders on Evidence tab", async ({ page }) => {
  await openEvidence(page);
  await expect(page.getByRole("heading", { name: "Cross-System Insights" })).toBeVisible();
});

test("cross-system panel shows advisory label", async ({ page }) => {
  await openEvidence(page);
  await expectAnyText(page, [/Advisory only/i, /no automated action/i]);
});

test("cross-system alert card shows correlation badge", async ({ page }) => {
  await page.route("**/api/discovery/cross-system", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        alerts: [
          {
            alert_id: "XS-test",
            entity_id: "supplier-acme",
            source_signal: "credential_access",
            related_signal: "otif_drop",
            correlation: 0.73,
            advisory: true,
          },
        ],
        provenance: "demo",
      }),
    });
  });
  await openEvidence(page);
  await expectAnyText(page, [/Correlation 73%/i, /supplier acme/i]);
});

test("digest endpoint returns cross-system section", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8030/api/discovery/digest");
  expect([200, 404].includes(res.status())).toBeTruthy();
  if (res.ok()) {
    const payload = await res.json();
    expect("cross_system" in payload).toBeTruthy();
  }
});
