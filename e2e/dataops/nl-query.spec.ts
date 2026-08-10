import { test, expect } from "../fixtures/copilot-fixture";
import type { Page, Route } from "@playwright/test";
import { waitForAppShell, waitForScreenReady } from "../helpers/ui";

const SUCCESS_RESPONSE = {
  answer: "417",
  confidence: 0.92,
  confidence_label: "high",
  source_attribution: [
    { source_id: "snowflake", source: "snowflake", trust: 1, contribution: "primary", weight: 0.7 },
    { source_id: "airflow", source: "airflow", trust: 0.66, contribution: "supporting", weight: 0.3 },
  ],
  computation_path: ["AGE GraphStore", "domain=dataops", "decision_count → 417"],
  quality_warning: null,
  evidence: "417 governed records contributed.",
};

async function gotoDashboard(page: Page) {
  await page.goto("/");
  await waitForScreenReady(page);
  await waitForAppShell(page);
  await expect(page.getByTestId("nl-query-panel")).toBeVisible({ timeout: 15_000 });
}

async function mockQuery(page: Page, body: object) {
  await page.route("**/api/di/query", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });
}

test("test_query_panel_visible_on_dashboard", async ({ page }) => {
  await gotoDashboard(page);

  await expect(page.getByText("Ask Your Data", { exact: true })).toBeVisible();
  await expect(page.getByPlaceholder("Ask about your data...")).toBeVisible();
  await expect(page.getByRole("button", { name: "Ask" })).toBeVisible();
});

test("test_query_input_accepts_text", async ({ page }) => {
  await gotoDashboard(page);

  const input = page.getByPlaceholder("Ask about your data...");
  await input.fill("How many decisions?");
  await expect(input).toHaveValue("How many decisions?");
});

test("test_example_question_populates_input", async ({ page }) => {
  await gotoDashboard(page);

  await page.getByRole("button", { name: "What is accuracy?", exact: true }).click();
  await expect(page.getByPlaceholder("Ask about your data...")).toHaveValue("What is accuracy?");
});

test("test_successful_query_shows_confidence", async ({ page }) => {
  await mockQuery(page, SUCCESS_RESPONSE);
  await gotoDashboard(page);

  await page.getByPlaceholder("Ask about your data...").fill("How many decisions?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  await expect(page.getByTestId("query-answer")).toHaveText("417");
  await expect(page.getByTestId("query-confidence")).toContainText("high");
  await expect(page.getByTestId("query-confidence")).toContainText("92%");
});

test("test_source_attribution_bars_visible", async ({ page }) => {
  await mockQuery(page, SUCCESS_RESPONSE);
  await gotoDashboard(page);

  await page.getByPlaceholder("Ask about your data...").fill("Which source is most reliable?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  await expect(page.getByTestId("source-attribution")).toBeVisible();
  await expect(page.getByTestId("source-attribution-bar")).toHaveCount(2);
  await expect(page.getByText("snowflake", { exact: true })).toBeVisible();
});

test("test_computation_path_expandable", async ({ page }) => {
  await mockQuery(page, SUCCESS_RESPONSE);
  await gotoDashboard(page);

  await page.getByPlaceholder("Ask about your data...").fill("How many decisions?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  const path = page.getByTestId("computation-path");
  await path.locator("summary").click();
  await expect(path.getByText("AGE GraphStore", { exact: true })).toBeVisible();
  await expect(path.getByText("decision_count → 417", { exact: true })).toBeVisible();
});

test("test_quality_warning_when_present", async ({ page }) => {
  await mockQuery(page, {
    ...SUCCESS_RESPONSE,
    quality_warning: "Sources are stale by more than 24 hours.",
  });
  await gotoDashboard(page);

  await page.getByPlaceholder("Ask about your data...").fill("What is accuracy?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await expect(page.getByTestId("query-quality-warning")).toHaveText("Sources are stale by more than 24 hours.");
});

test("test_insufficient_response_honest", async ({ page }) => {
  await mockQuery(page, {
    answer: "There is not enough evidence to answer this question.",
    confidence: 0.1,
    confidence_label: "insufficient",
    source_attribution: [],
    computation_path: ["No supported metric found"],
    quality_warning: "The question could not be answered from governed data.",
    evidence: "",
  });
  await gotoDashboard(page);

  await page.getByPlaceholder("Ask about your data...").fill("Tell me something unknown.");
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await expect(page.getByTestId("query-confidence")).toContainText("insufficient");
  await expect(page.getByTestId("query-answer")).toContainText("not enough evidence");
  await expect(page.getByTestId("query-quality-warning")).toBeVisible();
});
