import { test, expect, PORTS, gotoCopilot, gotoTab } from "./demo-fixture";

test.describe.serial("Trader Cut (TR1-TR3)", () => {
  test.beforeEach(async ({ demoReady }) => {
    test.skip(!demoReady, "Demo cut skipped: backends must be healthy and preseeded (IKS > 0)");
  });

  test("TR1: Dashboard shows portfolio, IKS, trust, and Day-Zero state", async ({ page }) => {
    await gotoCopilot(page, "trading");
    await expect(page.getByText("Portfolio Summary")).toBeVisible();
    await expect(page.getByText("IKS", { exact: true }).first()).toBeVisible();
    await expect(page.getByTestId("data-trust-badge")).toBeVisible();
    await expect(page.getByTestId("day-zero-card")).toBeVisible();
    await expect(page.getByTestId("day-zero-card")).toContainText(/instrument|accumulating|measured/i);
  });

  test("TR2: Log Trade score flow shows factors, reasoning, and similar trades", async ({ page }) => {
    await gotoTab(page, "trading", "Log Trade");
    await expect(page.getByTestId("pre-score-panel")).toBeVisible();
    await expect(page.getByTestId("pre-score-button")).toBeVisible();

    const response = page.waitForResponse(
      (item) => item.url().includes("/api/trading/pre-score") && item.request().method() === "POST",
    );
    await page.getByTestId("pre-score-button").click();
    await response;

    await expect(page.getByTestId("pre-score-similar")).toBeVisible();
    await expect(page.getByTestId("pre-score-accuracy")).toBeVisible();
    await expect(page.locator("main")).toContainText(/factor|reasoning|recommended action/i);
  });

  test("TR3: Analysis to Performance shows fingerprint, counterfactual, trajectory, and conservation", async ({ page }) => {
    await gotoTab(page, "trading", "Analysis");
    await expect(page.getByTestId("regime-panel")).toBeVisible();
    await expect(page.getByTestId("counterfactual-card")).toBeVisible();
    await expect(page.getByText(/fingerprint|factor/i).first()).toBeVisible();

    await page.getByRole("button", { name: "Performance", exact: true }).click();
    await expect(page.getByTestId("reconvergence-panel")).toBeVisible();
    await expect(page.getByText(/trajectory|Centroid Timeline/i).first()).toBeVisible();
    await expect(page.getByText(/conservation|automation|projection/i).first()).toBeVisible();
  });
});
