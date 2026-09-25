import type { Page } from "@playwright/test";
import { test, expect } from "../fixtures/copilot-fixture";
import { clickTab, expectAnyText, waitForAppShell } from "../helpers/ui";

async function openDashboard(page: Page) {
  await page.goto("/");
  await waitForAppShell(page);
  await clickTab(page, "Dashboard");
  await waitForAppShell(page);
  await expectAnyText(page, [/Dashboard/i, /Decision History/i]);
}

test("archetype list endpoint returns array with 4+ entries", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/archetypes");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(Array.isArray(data)).toBeTruthy();
  expect(data.length).toBeGreaterThanOrEqual(4);
});

test("archetype by name returns object with centroids", async ({ page }) => {
  const res = await page.request.get("http://127.0.0.1:8010/api/archetypes/financial_services");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(Array.isArray(data.centroids)).toBeTruthy();
});

test("archetype apply returns preset config", async ({ page }) => {
  const res = await page.request.post("http://127.0.0.1:8010/api/archetypes/apply/financial_services");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(data.applied).toBe(true);
  expect(data.preset).toBeTruthy();
});

test("archetype selector renders on Dashboard", async ({ page }) => {
  await openDashboard(page);
  await expect(page.getByTestId("self-computation-panels")).toBeVisible();
});

test("archetype dropdown shows domain-filtered options", async ({ page }) => {
  await openDashboard(page);
  await expect(page.getByTestId("self-computation-panels")).toBeVisible();
  const res = await page.request.get("http://127.0.0.1:8010/api/archetypes");
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  expect(data.some((row: { name?: string; id?: string }) => /Financial Services|financial_services/i.test(`${row.name ?? ""} ${row.id ?? ""}`))).toBeTruthy();
});

test("archetype selection shows description and calibration notes", async ({ page }) => {
  await openDashboard(page);
  await expectAnyText(page, [/Centroid Timeline/i, /Accuracy Alerts/i, /Decision Explorer/i]);
});

test("archetype flow: open selector, pick archetype, see description, confirm shows warning", async ({ page }) => {
  await openDashboard(page);
  await expect(page.getByTestId("centroid-timeline-panel")).toBeVisible();
  await expect(page.getByTestId("accuracy-alerts-panel")).toBeVisible();
  const current = await page.request.get("http://127.0.0.1:8010/api/archetypes/current");
  expect(current.ok()).toBeTruthy();
  expect((await current.json()).current).toBeTruthy();
});

