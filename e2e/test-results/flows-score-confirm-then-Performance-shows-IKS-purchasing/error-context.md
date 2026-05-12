# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: purchasing\flows.spec.ts >> score confirm then Performance shows IKS
- Location: purchasing\flows.spec.ts:33:1

# Error details

```
Error: expect(received).toMatch(expected)

Expected pattern: /IKS[\s\S]{0,80}\d+(\.\d+)?/i
Received string:  "Loading performance..."
```

# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [ref=e4]:
    - banner [ref=e5]:
      - generic [ref=e6]:
        - generic [ref=e7]: PO
        - generic [ref=e8]:
          - heading "Purchasing Copilot" [level=1] [ref=e9]
          - paragraph [ref=e10]: Compounding intelligence workspace
      - generic [ref=e11]:
        - generic "IKS 36" [ref=e12]:
          - generic [ref=e14]: "36"
        - generic [ref=e15]: IKS
    - navigation [ref=e16]:
      - button "Dashboard" [ref=e17] [cursor=pointer]
      - button "Order" [ref=e18] [cursor=pointer]
      - button "Analysis" [ref=e19] [cursor=pointer]
      - button "Inventory" [ref=e20] [cursor=pointer]
      - button "Performance" [active] [ref=e21] [cursor=pointer]
    - main [ref=e22]:
      - generic [ref=e23]:
        - generic [ref=e24]:
          - paragraph [ref=e25]: Performance
          - heading "20 orders to learn what takes 11 years of gut instinct." [level=1] [ref=e26]
          - generic [ref=e27]:
            - generic [ref=e28]:
              - generic [ref=e29]: IKS
              - strong [ref=e30]: "35.8"
            - generic [ref=e31]:
              - generic [ref=e32]: Accuracy
              - strong [ref=e33]: 70%
            - generic [ref=e34]:
              - generic [ref=e35]: Orders
              - strong [ref=e36]: "20"
            - generic [ref=e37]:
              - generic [ref=e38]: Days active
              - strong [ref=e39]: "2.3"
        - generic [ref=e40]:
          - generic [ref=e42]:
            - heading "Trajectory" [level=2] [ref=e43]
            - paragraph [ref=e44]: 20 orders to learn what takes 11 years of gut instinct.
          - generic [ref=e45]:
            - generic [ref=e46]:
              - generic [ref=e47]: Current IKS
              - generic [ref=e48]: "35.8"
            - generic [ref=e49]:
              - generic [ref=e50]: Win Rate
              - generic [ref=e51]: 70%
            - generic [ref=e52]:
              - generic [ref=e53]: Decisions
              - generic [ref=e54]: "20"
            - generic [ref=e55]:
              - generic [ref=e56]: Days Active
              - generic [ref=e57]: "2.3"
          - img [ref=e61]:
            - generic [ref=e63]:
              - generic [ref=e65]: "0"
              - generic [ref=e67]: "10"
              - generic [ref=e69]: "20"
              - generic [ref=e71]: "30"
              - generic [ref=e73]: "40"
              - generic [ref=e75]: "50"
              - generic [ref=e77]: "60"
              - generic [ref=e79]: "65"
            - generic [ref=e81]:
              - generic [ref=e83]: "0"
              - generic [ref=e85]: "25"
              - generic [ref=e87]: "50"
              - generic [ref=e89]: "75"
              - generic [ref=e91]: "100"
            - generic [ref=e93]: Switching cost
        - generic [ref=e106]:
          - generic [ref=e107]:
            - heading "Automation Projection" [level=2] [ref=e108]
            - paragraph [ref=e109]: Estimates when higher automation levels are safe, based on verified decisions and current accuracy.
          - generic [ref=e110]:
            - generic [ref=e111]:
              - generic [ref=e112]: Current auto-resolve
              - generic [ref=e113]: unknown
            - generic [ref=e114]:
              - generic [ref=e115]: Status
              - generic [ref=e116]: GREEN
            - generic [ref=e117]:
              - generic [ref=e118]: Accuracy
              - generic [ref=e119]: 85%
            - generic [ref=e120]:
              - generic [ref=e121]: Verified decisions
              - generic [ref=e122]: "65"
          - generic [ref=e123]:
            - generic [ref=e124]:
              - generic [ref=e125]: OK
              - generic [ref=e126]:
                - generic [ref=e127]: Target 55% automation
                - paragraph [ref=e128]: Ready now. Current verified outcomes satisfy the conservation threshold.
            - generic [ref=e129]:
              - generic [ref=e130]: OK
              - generic [ref=e131]:
                - generic [ref=e132]: Target 75% automation
                - paragraph [ref=e133]: Ready now. Current verified outcomes satisfy the conservation threshold.
            - generic [ref=e134]:
              - generic [ref=e135]: OK
              - generic [ref=e136]:
                - generic [ref=e137]: Target 90% automation
                - paragraph [ref=e138]: Ready now. Current verified outcomes satisfy the conservation threshold.
          - generic [ref=e139]: "Pace: 198 decisions/week."
          - generic [ref=e140]: The system tells you WHEN. Not before.
        - generic [ref=e141]:
          - paragraph [ref=e142]: Cost impact
          - heading "Waste and stockouts are now measurable" [level=2] [ref=e143]
          - generic [ref=e144]:
            - generic [ref=e145]:
              - generic [ref=e146]: Waste reduction
              - strong [ref=e147]: 19.2%
            - generic [ref=e148]:
              - generic [ref=e149]: Stockout events
              - strong [ref=e150]: "2"
            - generic [ref=e151]:
              - generic [ref=e152]: Stockout cost
              - strong [ref=e153]: $920
            - generic [ref=e154]:
              - generic [ref=e155]: AE auto-decisions
              - strong [ref=e156]: "12"
        - generic [ref=e157]:
          - paragraph [ref=e158]: Waste cost
          - heading "The cost leak is concentrated" [level=2] [ref=e159]
          - generic [ref=e160]:
            - generic [ref=e161]:
              - generic [ref=e162]: Total waste 30d
              - strong [ref=e163]: $1,904
            - generic [ref=e164]:
              - generic [ref=e165]: Total stockout 30d
              - strong [ref=e166]: $920
            - generic [ref=e167]:
              - generic [ref=e168]: Waste / stockout
              - strong [ref=e169]: 2.1x
            - generic [ref=e170]:
              - generic [ref=e171]: Worst category
              - strong [ref=e172]: produce
            - generic [ref=e173]:
              - generic [ref=e174]: Worst day
              - strong [ref=e175]: friday
          - paragraph [ref=e176]: "Worst order: mixed_greens at $409."
        - generic [ref=e177]:
          - paragraph [ref=e178]: Category accuracy
          - heading "Where ordering is consistent" [level=2] [ref=e179]
          - generic [ref=e180]:
            - generic [ref=e181]:
              - generic [ref=e182]: protein
              - strong [ref=e185]: 67%
              - generic [ref=e186]: 6 orders
            - generic [ref=e187]:
              - generic [ref=e188]: produce
              - strong [ref=e191]: 50%
              - generic [ref=e192]: 6 orders
            - generic [ref=e193]:
              - generic [ref=e194]: dairy
              - strong [ref=e197]: 75%
              - generic [ref=e198]: 4 orders
            - generic [ref=e199]:
              - generic [ref=e200]: dry goods
              - strong [ref=e203]: 0%
              - generic [ref=e204]: 0 orders
            - generic [ref=e205]:
              - generic [ref=e206]: beverages
              - strong [ref=e209]: 100%
              - generic [ref=e210]: 2 orders
  - generic [ref=e211]: "25"
```

# Test source

```ts
  1   | import { type Page } from "@playwright/test";
  2   | import { test, expect } from "../fixtures/copilot-fixture";
  3   | import { clickTab, collectConsoleErrors, expectAnyText, expectNoConsoleErrors } from "../helpers/ui";
  4   | 
  5   | async function scoreCurrentOrder(page: Page) {
  6   |   await expect(page.getByText("Six scorer inputs")).toBeVisible();
  7   |   const scoreButton = page.getByRole("button", { name: "Score This Order" });
  8   |   await expect(scoreButton).toBeEnabled();
  9   |   const scoreResponse = page.waitForResponse((response) => response.url().includes("/api/score") && response.request().method() === "POST");
  10  |   await scoreButton.click();
  11  |   await scoreResponse;
  12  |   await expect(page.getByRole("button", { name: "Confirm" })).toBeVisible();
  13  | }
  14  | 
  15  | test("full order lifecycle: dashboard item, order, score, confirm", async ({ page }) => {
  16  |   test.setTimeout(60_000);
  17  |   await page.goto("/");
  18  | 
  19  |   const parMonitor = page.locator("section.par-monitor", { hasText: "Par level monitor" });
  20  |   const dashboardOrderButtons = parMonitor.getByRole("button", { name: /^Order$/ });
  21  |   if ((await dashboardOrderButtons.count()) > 0) {
  22  |     await dashboardOrderButtons.first().click();
  23  |   } else {
  24  |     await page.getByRole("button", { name: "Order Something Else" }).click();
  25  |   }
  26  | 
  27  |   await expect(page.getByRole("heading", { name: "Score the next purchase" })).toBeVisible();
  28  |   await scoreCurrentOrder(page);
  29  |   await page.getByRole("button", { name: "Confirm" }).click();
  30  |   await expectAnyText(page, [/system learned/i, /Confirming and storing order metadata/i, /ordering decision/i]);
  31  | });
  32  | 
  33  | test("score confirm then Performance shows IKS", async ({ page }) => {
  34  |   test.setTimeout(60_000);
  35  |   await page.goto("/");
  36  |   await clickTab(page, "Order");
  37  |   await expect(page.getByRole("heading", { name: "Score the next purchase" })).toBeVisible();
  38  | 
  39  |   const itemSelect = page.locator(".order-form-grid select").first();
  40  |   if (await itemSelect.isVisible().catch(() => false)) {
  41  |     const optionCount = await itemSelect.locator("option").count();
  42  |     if (optionCount > 1) {
  43  |       const secondValue = await itemSelect.locator("option").nth(1).getAttribute("value");
  44  |       if (secondValue) {
  45  |         await itemSelect.selectOption(secondValue);
  46  |       }
  47  |     }
  48  |   }
  49  | 
  50  |   await scoreCurrentOrder(page);
  51  |   const learnResponse = page.waitForResponse(
  52  |     (response) => response.url().includes("/api/learn") && response.request().method() === "POST" && response.ok(),
  53  |     { timeout: 15_000 },
  54  |   ).catch(() => null);
  55  |   await page.getByRole("button", { name: "Confirm" }).click();
  56  |   await learnResponse;
  57  |   await expectAnyText(page, [/system learned/i, /reward/i, /ordering decision/i, /IKS/i]);
  58  | 
  59  |   await clickTab(page, "Performance");
  60  |   await expectAnyText(page, [/IKS/i, /Trajectory/i, /orders to learn/i]);
  61  |   const mainText = await page.locator("main").innerText();
> 62  |   expect(mainText).toMatch(/IKS[\s\S]{0,80}\d+(\.\d+)?/i);
      |                    ^ Error: expect(received).toMatch(expected)
  63  | });
  64  | 
  65  | test("full round trip visits dashboard, order, analysis, inventory, and performance", async ({ page }) => {
  66  |   await page.goto("/");
  67  |   await expectAnyText(page, [/items need attention/i, /dashboard/i, /cover/i]);
  68  | 
  69  |   await clickTab(page, "Order");
  70  |   await expectAnyText(page, [/Score the next purchase/i, /stockout/i, /order/i]);
  71  | 
  72  |   await clickTab(page, "Analysis");
  73  |   await expectAnyText(page, [/YOUR TWO SELVES/i, /THE HISTORIAN/i, /Fingerprint/i]);
  74  | 
  75  |   await clickTab(page, "Inventory");
  76  |   await expectAnyText(page, [/System Improvements/i, /Inventory/i, /variant/i, /Category summary/i]);
  77  | 
  78  |   await clickTab(page, "Performance");
  79  |   await expectAnyText(page, [/IKS/i, /Trajectory/i, /orders to learn/i]);
  80  | });
  81  | 
  82  | test("tab navigation all 5 tabs", async ({ page }) => {
  83  |   const errors = collectConsoleErrors(page);
  84  |   await page.goto("/");
  85  | 
  86  |   for (const tab of ["Dashboard", "Order", "Analysis", "Inventory", "Performance"]) {
  87  |     await clickTab(page, tab);
  88  |     await expectAnyText(page, [new RegExp(tab, "i"), /Loading/i, /Score the next purchase/i, /System Improvements/i]);
  89  |   }
  90  | 
  91  |   expectNoConsoleErrors(errors);
  92  | });
  93  | 
  94  | test("analysis and inventory data consistency", async ({ page }) => {
  95  |   await page.goto("/");
  96  |   await clickTab(page, "Analysis");
  97  |   await expect(page.getByText("Category accuracy")).toBeVisible();
  98  |   await expectAnyText(page, [/protein/i, /produce/i, /dairy/i]);
  99  | 
  100 |   await clickTab(page, "Inventory");
  101 |   await expect(page.getByText("Category summary")).toBeVisible();
  102 |   await expectAnyText(page, [/protein/i, /produce/i, /dairy/i]);
  103 | });
  104 | 
  105 | test("order from dropdown versus dashboard item click", async ({ page }) => {
  106 |   await page.goto("/");
  107 |   await clickTab(page, "Order");
  108 |   await expect(page.getByRole("heading", { name: "Score the next purchase" })).toBeVisible();
  109 | 
  110 |   const itemSelect = page.locator(".order-form-grid select").first();
  111 |   await expect(itemSelect).toBeVisible();
  112 |   const optionCount = await itemSelect.locator("option").count();
  113 |   if (optionCount > 1) {
  114 |     const secondValue = await itemSelect.locator("option").nth(1).getAttribute("value");
  115 |     if (secondValue) {
  116 |       await itemSelect.selectOption(secondValue);
  117 |     }
  118 |   }
  119 | 
  120 |   await expect(page.getByText("Cost analysis")).toBeVisible();
  121 |   await expect(page.getByText("Six scorer inputs")).toBeVisible();
  122 | });
  123 | 
  124 | test("AE-managed and rejected items show different badges", async ({ page }) => {
  125 |   await page.goto("/");
  126 |   await expectAnyText(page, [/AE managed/i, /managed/i]);
  127 | 
  128 |   await clickTab(page, "Inventory");
  129 |   await expectAnyText(page, [/System Improvements/i, /variant/i, /produce/i, /dairy/i]);
  130 |   await expectAnyText(page, [/Reject aggressive dairy skip/i, /purchasing-skip-dairy-v1/i, /rejected/i, /excluded/i]);
  131 | });
  132 | 
  133 | test("inventory shows category groups and variant counts", async ({ page }) => {
  134 |   await page.goto("/");
  135 |   await clickTab(page, "Inventory");
  136 | 
  137 |   await expectAnyText(page, [/protein/i, /produce/i, /dairy/i]);
  138 |   await expectAnyText(page, [/System Improvements/i, /\d+\s+variants?/i, /variant/i]);
  139 | 
  140 |   await clickTab(page, "Performance");
  141 |   await expectAnyText(page, [/IKS/i, /Trajectory/i]);
  142 | });
  143 | 
  144 | test("Dashboard to Order score to confirm to Performance IKS", async ({ page }) => {
  145 |   test.setTimeout(60_000);
  146 |   await page.goto("/");
  147 |   await expectAnyText(page, [/items need attention/i, /cover/i, /Par level monitor/i]);
  148 | 
  149 |   await clickTab(page, "Order");
  150 |   await expectAnyText(page, [/Score the next purchase/i, /stockout/i, /order/i]);
  151 | 
  152 |   const itemSelect = page.locator(".order-form-grid select").first();
  153 |   if (await itemSelect.isVisible().catch(() => false)) {
  154 |     const optionCount = await itemSelect.locator("option").count();
  155 |     if (optionCount > 1) {
  156 |       const secondValue = await itemSelect.locator("option").nth(1).getAttribute("value");
  157 |       if (secondValue) {
  158 |         await itemSelect.selectOption(secondValue);
  159 |       }
  160 |     }
  161 |   }
  162 | 
```