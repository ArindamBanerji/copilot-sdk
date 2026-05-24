# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: s2p\flows.spec.ts >> triage select score confirm reward round trip
- Location: s2p\flows.spec.ts:85:1

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('article').filter({ hasText: 'Action index' })
Expected pattern: /Confidence/i
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toContainText" with timeout 10000ms
  - waiting for locator('article').filter({ hasText: 'Action index' })

```

# Page snapshot

```yaml
- generic [ref=e5]:
  - banner [ref=e6]:
    - generic [ref=e7]:
      - generic [ref=e8]: S2P
      - generic [ref=e9]:
        - heading "S2P Copilot" [level=1] [ref=e10]
        - paragraph [ref=e11]: Compounding intelligence workspace
    - generic [ref=e12]:
      - generic "IKS 0" [ref=e13]:
        - generic [ref=e15]: "0"
      - generic [ref=e16]: IKS
  - navigation [ref=e17]:
    - button "Dashboard" [ref=e18] [cursor=pointer]
    - button "Exception Triage" [ref=e19] [cursor=pointer]
    - button "Insight" [ref=e20] [cursor=pointer]
    - button "Evidence" [ref=e21] [cursor=pointer]
    - button "Suppliers" [ref=e22] [cursor=pointer]
    - button "Performance" [ref=e23] [cursor=pointer]
  - main [ref=e24]:
    - generic [ref=e25]:
      - generic [ref=e26]:
        - paragraph [ref=e27]: Invoice exception workflow
        - heading "Exception Triage" [level=1] [ref=e28]
        - paragraph [ref=e29]: Select an invoice, score the exception, inspect factors and process context, then confirm or override the recommendation so S2P can record reward.
      - generic [ref=e30]:
        - article [ref=e31]:
          - generic [ref=e32]:
            - heading "Invoice Selector" [level=2] [ref=e33]
            - generic [ref=e34]: 50 queued
          - generic [ref=e35]:
            - button "S2P-INV-0020 100% Helix Lab Supplies duplicate_risk · $7,241" [ref=e36] [cursor=pointer]:
              - generic [ref=e37]:
                - generic [ref=e38]: S2P-INV-0020
                - generic [ref=e39]: 100%
              - paragraph [ref=e40]: Helix Lab Supplies
              - paragraph [ref=e41]: duplicate_risk · $7,241
            - button "S2P-INV-0047 100% Boreal Equipment Maintenance duplicate_risk · $13,179" [ref=e42] [cursor=pointer]:
              - generic [ref=e43]:
                - generic [ref=e44]: S2P-INV-0047
                - generic [ref=e45]: 100%
              - paragraph [ref=e46]: Boreal Equipment Maintenance
              - paragraph [ref=e47]: duplicate_risk · $13,179
            - button "S2P-INV-0034 100% Novatek IT Services duplicate_risk · $33,320" [ref=e48] [cursor=pointer]:
              - generic [ref=e49]:
                - generic [ref=e50]: S2P-INV-0034
                - generic [ref=e51]: 100%
              - paragraph [ref=e52]: Novatek IT Services
              - paragraph [ref=e53]: duplicate_risk · $33,320
            - button "S2P-INV-0017 100% Boreal Equipment Maintenance duplicate_risk · $16,623" [ref=e54] [cursor=pointer]:
              - generic [ref=e55]:
                - generic [ref=e56]: S2P-INV-0017
                - generic [ref=e57]: 100%
              - paragraph [ref=e58]: Boreal Equipment Maintenance
              - paragraph [ref=e59]: duplicate_risk · $16,623
            - button "S2P-INV-0050 100% Helix Lab Supplies duplicate_risk · $9,218" [ref=e60] [cursor=pointer]:
              - generic [ref=e61]:
                - generic [ref=e62]: S2P-INV-0050
                - generic [ref=e63]: 100%
              - paragraph [ref=e64]: Helix Lab Supplies
              - paragraph [ref=e65]: duplicate_risk · $9,218
            - button "S2P-INV-0041 99% Aster Industrial Chemicals contract_gap · $14,827" [ref=e66] [cursor=pointer]:
              - generic [ref=e67]:
                - generic [ref=e68]: S2P-INV-0041
                - generic [ref=e69]: 99%
              - paragraph [ref=e70]: Aster Industrial Chemicals
              - paragraph [ref=e71]: contract_gap · $14,827
            - button "S2P-INV-0030 99% Helix Lab Supplies quantity_mismatch · $8,057" [ref=e72] [cursor=pointer]:
              - generic [ref=e73]:
                - generic [ref=e74]: S2P-INV-0030
                - generic [ref=e75]: 99%
              - paragraph [ref=e76]: Helix Lab Supplies
              - paragraph [ref=e77]: quantity_mismatch · $8,057
            - button "S2P-INV-0015 99% Yangtze Raw Materials format_compliance · $39,332" [ref=e78] [cursor=pointer]:
              - generic [ref=e79]:
                - generic [ref=e80]: S2P-INV-0015
                - generic [ref=e81]: 99%
              - paragraph [ref=e82]: Yangtze Raw Materials
              - paragraph [ref=e83]: format_compliance · $39,332
            - button "S2P-INV-0031 99% Aster Industrial Chemicals format_compliance · $17,711" [ref=e84] [cursor=pointer]:
              - generic [ref=e85]:
                - generic [ref=e86]: S2P-INV-0031
                - generic [ref=e87]: 99%
              - paragraph [ref=e88]: Aster Industrial Chemicals
              - paragraph [ref=e89]: format_compliance · $17,711
            - button "S2P-INV-0004 99% Novatek IT Services contract_gap · $30,171" [ref=e90] [cursor=pointer]:
              - generic [ref=e91]:
                - generic [ref=e92]: S2P-INV-0004
                - generic [ref=e93]: 99%
              - paragraph [ref=e94]: Novatek IT Services
              - paragraph [ref=e95]: contract_gap · $30,171
        - generic [ref=e96]:
          - article [ref=e97]:
            - generic [ref=e98]:
              - generic [ref=e99]:
                - heading "Selected Invoice" [level=2] [ref=e100]
                - generic [ref=e101]:
                  - generic [ref=e102]:
                    - paragraph [ref=e103]: Invoice
                    - paragraph [ref=e104]: S2P-INV-0020
                  - generic [ref=e105]:
                    - paragraph [ref=e106]: Supplier
                    - paragraph [ref=e107]: Helix Lab Supplies
                  - generic [ref=e108]:
                    - paragraph [ref=e109]: Amount
                    - paragraph [ref=e110]: $7,241
                  - generic [ref=e111]:
                    - paragraph [ref=e112]: Category
                    - paragraph [ref=e113]: duplicate_risk
              - button "Scoring..." [disabled] [ref=e114]
          - article [ref=e115]:
            - generic [ref=e116]:
              - generic [ref=e117]:
                - paragraph [ref=e118]: Evidence template
                - heading "Category explanation" [level=2] [ref=e119]
              - generic [ref=e120]: duplicate risk
            - paragraph [ref=e121]: "Invoice S2P-INV-0020 from Helix Lab Supplies. Similar: S2P-INV-0020-PRIOR dated 2026-02-14, amount 7241.13 (similarity 89.9%). possible duplicate. -> flag_leakage."
            - generic [ref=e122]:
              - generic [ref=e123]: "invoice id: S2P-INV-0020"
              - generic [ref=e124]: "supplier: Helix Lab Supplies"
              - generic [ref=e125]: "variance pct: 9.20"
              - generic [ref=e126]: "commodity: freight surcharge"
              - generic [ref=e127]: "commodity delta: 51.40"
          - article [ref=e128]:
            - generic [ref=e129]:
              - heading "Conservation Projection" [level=2] [ref=e130]
              - generic [ref=e131]: penalty 1:1
            - generic [ref=e132]:
              - generic [ref=e133]:
                - paragraph [ref=e134]: Status
                - paragraph [ref=e135]: RED
              - generic [ref=e136]:
                - paragraph [ref=e137]: q / accuracy
                - paragraph [ref=e138]: n/a
              - generic [ref=e139]:
                - paragraph [ref=e140]: Verified
                - paragraph [ref=e141]: "0"
              - generic [ref=e142]:
                - paragraph [ref=e143]: theta min
                - paragraph [ref=e144]: n/a
```

# Test source

```ts
  1   | import { test, expect } from "@playwright/test";
  2   | import { clickTab } from "../helpers/ui";
  3   | 
  4   | const tabs = [
  5   |   { name: "Dashboard", pattern: /Dashboard|Exception Queue/i },
  6   |   { name: "Exception Triage", pattern: /Exception Triage|Invoice Selector/i },
  7   |   { name: "Insight", pattern: /Insight|fingerprint/i },
  8   |   { name: "Evidence", pattern: /Evidence|audit trail/i },
  9   |   { name: "Suppliers", pattern: /Suppliers|supplier profiles/i },
  10  |   { name: "Performance", pattern: /Performance|trajectory/i },
  11  | ];
  12  | 
  13  | function main(page: import("@playwright/test").Page) {
  14  |   return page.locator("main");
  15  | }
  16  | 
  17  | function panel(page: import("@playwright/test").Page, text: string | RegExp) {
  18  |   return page.locator("article").filter({
  19  |     has: page.locator("h1, h2, h3, h4, p.font-semibold, [class*='font-semibold']", {
  20  |       hasText: text,
  21  |     }),
  22  |   });
  23  | }
  24  | 
  25  | function scoreResultPanel(page: import("@playwright/test").Page) {
  26  |   return page.locator("article", { hasText: "Action index" });
  27  | }
  28  | 
  29  | function recommendationControls(page: import("@playwright/test").Page) {
  30  |   return page.locator("article", { has: page.getByRole("button", { name: /Confirm recommendation/i }) });
  31  | }
  32  | 
  33  | async function clickScore(page: import("@playwright/test").Page) {
  34  |   await panel(page, "Selected Invoice").getByRole("button", { name: /^Score$/i }).click();
  35  | }
  36  | 
  37  | async function confirmRecommendation(page: import("@playwright/test").Page) {
  38  |   await recommendationControls(page).getByRole("button", { name: /Confirm recommendation/i }).click();
  39  | }
  40  | 
  41  | test("all 6 tabs load without blank screens", async ({ page }) => {
  42  |   await page.goto("/");
  43  | 
  44  |   for (const tab of tabs) {
  45  |     await clickTab(page, tab.name);
  46  |     await expect(page.locator("main")).not.toBeEmpty();
  47  |     await expect(main(page)).toContainText(tab.pattern);
  48  |   }
  49  | });
  50  | 
  51  | test("Dashboard shows preview data from S2P backend", async ({ page }) => {
  52  |   await page.goto("/");
  53  | 
  54  |   await expect(panel(page, "Exception Queue")).toContainText(/exception/i);
  55  |   const conservation = panel(page, "Conservation Status");
  56  |   await expect(conservation).toContainText(/conservation/i);
  57  |   await expect(conservation).toContainText(/GREEN|AMBER|RED/i);
  58  |   await expect(conservation).toContainText(/Verified decisions/i);
  59  | });
  60  | 
  61  | test("full round-trip Dashboard to all screens to Dashboard", async ({ page }) => {
  62  |   await page.goto("/");
  63  |   await expect(main(page)).toContainText(/Dashboard|Exception Queue/i);
  64  | 
  65  |   await clickTab(page, "Exception Triage");
  66  |   await expect(main(page)).toContainText(/Exception Triage|7 factors/i);
  67  | 
  68  |   await clickTab(page, "Insight");
  69  |   await expect(main(page)).toContainText(/Insight|Factor fingerprint|Similar invoices/i);
  70  | 
  71  |   await clickTab(page, "Evidence");
  72  |   await expect(main(page)).toContainText(/Evidence|rule lifecycle|audit trail/i);
  73  | 
  74  |   await clickTab(page, "Suppliers");
  75  |   await expect(main(page)).toContainText(/Suppliers|OTIF|profile/i);
  76  | 
  77  |   await clickTab(page, "Performance");
  78  |   await expect(main(page)).toContainText(/Performance|What-if simulator|Operational summary/i);
  79  | 
  80  |   await clickTab(page, "Dashboard");
  81  |   await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  82  |   await expect(main(page)).toContainText(/Exception Queue|Conservation Status/i);
  83  | });
  84  | 
  85  | test("triage select score confirm reward round trip", async ({ page }) => {
  86  |   await page.goto("/");
  87  |   await clickTab(page, "Exception Triage");
  88  | 
  89  |   await expect(panel(page, "Invoice Selector")).toContainText(/S2P-INV|queued/i);
  90  |   await clickScore(page);
> 91  |   await expect(scoreResultPanel(page)).toContainText(/Confidence/i);
      |                                        ^ Error: expect(locator).toContainText(expected) failed
  92  |   await confirmRecommendation(page);
  93  |   await expect(panel(page, "Learning Result")).toContainText(/Reward|confirm|recorded/i, { timeout: 15_000 });
  94  | });
  95  | 
  96  | test("score learn round trip preserves conservation projection", async ({ page }) => {
  97  |   await page.goto("/");
  98  |   await clickTab(page, "Exception Triage");
  99  | 
  100 |   await clickScore(page);
  101 |   await expect(main(page)).toContainText(/Recommendation|7-Factor Reasoning/i);
  102 |   await confirmRecommendation(page);
  103 |   await expect(panel(page, "Learning Result")).toContainText(/Reward/i, { timeout: 15_000 });
  104 |   await expect(panel(page, "Conservation Projection")).toContainText(/Verified|accuracy|penalty 5:1/i);
  105 | });
  106 | 
  107 | test("triage to dashboard navigation keeps dashboard preview visible", async ({ page }) => {
  108 |   await page.goto("/");
  109 |   await clickTab(page, "Exception Triage");
  110 |   await expect(panel(page, "Invoice Selector")).toContainText(/queued|S2P-INV/i);
  111 |   await expect(panel(page, "Selected Invoice").getByRole("button", { name: /^Score$/i })).toBeVisible();
  112 | 
  113 |   await clickTab(page, "Dashboard");
  114 |   await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  115 |   await expect(main(page)).toContainText(/Exception Queue|Conservation Status/i);
  116 | });
  117 | 
  118 | test("process context persists across reload after scoring", async ({ page }) => {
  119 |   await page.goto("/");
  120 |   await clickTab(page, "Exception Triage");
  121 |   await clickScore(page);
  122 |   await expect(panel(page, /Process Context/i)).toContainText(/Celonis/i);
  123 |   await expect(panel(page, /Process Context/i)).toContainText(/Match Invoice|bottleneck|42/i);
  124 | 
  125 |   await page.reload();
  126 |   await clickTab(page, "Exception Triage");
  127 |   await clickScore(page);
  128 |   await expect(panel(page, /Process Context/i)).toContainText(/Celonis/i);
  129 |   await expect(panel(page, /Process Context/i)).toContainText(/Match Invoice|bottleneck|42/i);
  130 | });
  131 | 
  132 | test("graded financial reward appears as decimal reward", async ({ page }) => {
  133 |   await page.goto("/");
  134 |   await clickTab(page, "Exception Triage");
  135 | 
  136 |   await clickScore(page);
  137 |   await confirmRecommendation(page);
  138 | 
  139 |   await expect(panel(page, "Learning Result")).toContainText(/Reward|Reward raw|\+1\.00|\+0\.[0-9]+|-0\.[0-9]+/, { timeout: 15_000 });
  140 | });
  141 | 
  142 | test("Process-Tech Fusion story spans all S2P screens", async ({ page }) => {
  143 |   await page.goto("/");
  144 |   await expect(main(page)).toContainText(/Exception Queue|Process context|Conservation mini-gauge/i);
  145 | 
  146 |   await clickTab(page, "Exception Triage");
  147 |   await expect(main(page)).toContainText(/Invoice Selector|7-Factor Reasoning|Process Context/i);
  148 | 
  149 |   await clickTab(page, "Insight");
  150 |   await expect(main(page)).toContainText(/Factor fingerprint|Similar invoices|Cross-graph signal|Process signals/i);
  151 | 
  152 |   await clickTab(page, "Evidence");
  153 |   await expect(main(page)).toContainText(/Invoice audit trail|Rule lifecycle|Compliance/i);
  154 | 
  155 |   await clickTab(page, "Performance");
  156 |   await expect(main(page)).toContainText(/Learning trajectory|What-if simulator|Operational summary/i);
  157 | });
  158 | 
  159 | test("cross-graph insight shows supplier impact ranking", async ({ page }) => {
  160 |   await page.goto("/");
  161 |   await clickTab(page, "Insight");
  162 | 
  163 |   const crossGraph = panel(page, "Supplier exceptions align with process delay");
  164 |   await expect(crossGraph).toContainText(/Supplier exceptions/i);
  165 |   await expect(crossGraph).toContainText(/Supplier|Commodity|Impact score|Aster/i);
  166 | });
  167 | 
  168 | test("evidence to performance connects compliance and conservation", async ({ page }) => {
  169 |   await page.goto("/");
  170 |   await clickTab(page, "Evidence");
  171 |   await expect(panel(page, /^Compliance$/i).first()).toContainText(/Flagged|Compliant/i);
  172 | 
  173 |   await clickTab(page, "Performance");
  174 |   await expect(panel(page, "Conservation mini-gauge")).toContainText(/penalty 5:1|verified/i);
  175 | });
  176 | 
  177 | test("performance what-if shows projected values", async ({ page }) => {
  178 |   await page.goto("/");
  179 |   await clickTab(page, "Performance");
  180 | 
  181 |   await expect(panel(page, "What-if simulator")).toContainText(/Projected q|Theta min|Status/i);
  182 | });
  183 | 
  184 | test("savings estimate is visible", async ({ page }) => {
  185 |   await page.goto("/");
  186 |   await clickTab(page, "Performance");
  187 | 
  188 |   await expect(panel(page, "Operational summary")).toContainText(/Savings estimate|Annual target|\$/i);
  189 | });
  190 | 
  191 | test("dashboard to triage drill-down path remains available", async ({ page }) => {
```