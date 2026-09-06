## Summary

The selector is not failing because `>` cannot reach the screen: `CopilotShell` renders a direct `<main>` whose children are the application content, and each Purchasing screen places its `data-screen-ready` root at that level (`copilot_sdk/frontend/CopilotShell.tsx:30-83`; `apps/purchasing/frontend/src/App.tsx:59-64`). Dashboard and Order become ready because their screen-level loading promises settle. Analysis and Inventory can remain in their loading branches because their required data requests have no client timeout, and Inventory additionally waits for every per-item waste-history request (`apps/purchasing/frontend/src/screens/AnalysisScreen.tsx:59-84`; `apps/purchasing/frontend/src/screens/InventoryScreen.tsx:95-130`). The shared SC panels are a separate issue: they are rendered as siblings of the active screen, and their readiness is descendant-scanned after the screen is ready (`apps/purchasing/frontend/src/App.tsx:59-65`; `e2e/helpers/ui.ts:36-39`).

## Symptom Table

| Area | Observed result | Code evidence | Diagnostic meaning |
|---|---:|---|---|
| Dashboard | 10/10 pass | The screen has loading, error-ready, and success-ready branches (`apps/purchasing/frontend/src/screens/DashboardScreen.tsx:103-155`, `:163-178`). | Its dashboard requests settle in the tested environment. |
| Order | 8/8 pass, with one verification timeout | Order waits for its initial `Promise.all` and then exposes a ready root (`apps/purchasing/frontend/src/screens/OrderScreen.tsx:458-463`; verification is awaited at `e2e/purchasing/order.spec.ts:90-93`). | Initial screen readiness is independent of the later verify request. |
| Analysis | 5/6 pass; SC-14 case reaches the readiness timeout | All six tests use the same `gotoAnalysis` helper (`e2e/purchasing/analysis.spec.ts:4-11`, `:13-55`). Analysis stays false until `getAnalytics()` and `getFingerprint()` settle (`apps/purchasing/frontend/src/screens/AnalysisScreen.tsx:59-84`, `:88-110`). | There is no test-6 navigation split; the difference is timing/request state, not routing. |
| Inventory | 0/3 pass | All three tests call `gotoInventory`, which waits for screen readiness after the tab click (`e2e/purchasing/helpers.ts:5-10`; `e2e/purchasing/inventory.spec.ts:5-24`). | The screen remains loading when its initial items/variants request or any item waste-history request remains pending (`apps/purchasing/frontend/src/screens/InventoryScreen.tsx:95-130`, `:142-156`). |
| Performance | Not run; same risk | Performance has the same false-loading and true-ready root branches (`apps/purchasing/frontend/src/screens/PerformanceScreen.tsx:50-80`, `:90-104`). | It can exhibit the same behavior if its initial requests do not settle. |

## DOM Hierarchy

`CopilotShell` has no wrapper between `main` and its children. Its JSX is:

```tsx
<main className="min-h-[32rem]">{children}</main>
```

This is `copilot_sdk/frontend/CopilotShell.tsx:80-83`. Purchasing passes the active screen and the persistent SC wrapper as siblings (`apps/purchasing/frontend/src/App.tsx:59-65`), so the effective structure is:

```text
main
├── active screen root
│   └── data-screen-ready="false" or "true"
└── SelfComputationPanels root
    └── six panel roots with data-panel-ready
```

The screen root is therefore a direct child of `main` for Dashboard, Analysis, Inventory, Order, and Performance. The screen branches provide direct evidence: Dashboard (`apps/purchasing/frontend/src/screens/DashboardScreen.tsx:164-178`), Analysis (`apps/purchasing/frontend/src/screens/AnalysisScreen.tsx:88-110`), Inventory (`apps/purchasing/frontend/src/screens/InventoryScreen.tsx:142-156`), Order (`apps/purchasing/frontend/src/screens/OrderScreen.tsx:458-463`), and Performance (`apps/purchasing/frontend/src/screens/PerformanceScreen.tsx:90-104`).

The helper deliberately uses two different scopes: direct-child selection for the screen and descendant selection for panel readiness (`e2e/helpers/ui.ts:36-39`). Thus `main [data-screen-ready="true"]` would match a descendant, but changing the selector is unnecessary for the current JSX; the screen roots are already direct children.

## Navigation Helpers

Analysis tests 1–6 all call the same `gotoAnalysis` function. It performs `page.goto`, waits for the app shell, clicks Analysis, waits for the app shell again, and then waits for `data-screen-ready` (`e2e/purchasing/analysis.spec.ts:4-11`). Test 6 has no alternate navigation code; it only changes the assertions after the same helper (`e2e/purchasing/analysis.spec.ts:50-55`).

Inventory tests also share one helper. `gotoInventory` performs `page.goto`, waits for readiness, clicks Inventory, waits for readiness again, and checks the screen text (`e2e/purchasing/helpers.ts:5-10`). All three Inventory tests call it (`e2e/purchasing/inventory.spec.ts:5-24`).

Dashboard tests navigate directly with `page.goto` and then call `waitForScreenReady` (`e2e/purchasing/dashboard.spec.ts:4-10`, `:13-19`, `:22-29`). Order uses its own helper with the same initial readiness sequence and then clicks Order (`e2e/purchasing/order.spec.ts:7-12`). Performance uses the same pattern as Analysis/Inventory (`e2e/purchasing/performance.spec.ts:4-10`).

## Root Cause

The single root cause supported by the source is an asynchronous readiness contract with no bounded completion for several screen loaders, not a CSS selector mismatch or an extra shell wrapper.

1. `waitForScreenReady` requires a direct child with `data-screen-ready="true"` (`e2e/helpers/ui.ts:36-38`).
2. Analysis initially renders a direct child with `data-screen-ready="false"` (`apps/purchasing/frontend/src/screens/AnalysisScreen.tsx:88-94`). It sets `loading` false only in the `finally` block after the combined analytics/fingerprint promise settles (`apps/purchasing/frontend/src/screens/AnalysisScreen.tsx:64-78`).
3. `getAnalytics` and `getFingerprint` use `apiGet`, while `apiGet` has no timeout (`apps/purchasing/frontend/src/api.ts:103-109`, `:156-162`, `:449-451`). A request that remains pending prevents the `finally` block from running.
4. Inventory waits for `getItems()` and `getEvolutionVariants()`, then awaits a `Promise.all` over one `getWasteHistory()` request per item (`apps/purchasing/frontend/src/screens/InventoryScreen.tsx:100-109`). `getWasteHistory` also uses the unbounded `apiGet` (`apps/purchasing/frontend/src/api.ts:239-241`).
5. Inventory remains false until that entire operation completes (`apps/purchasing/frontend/src/screens/InventoryScreen.tsx:111-124`, `:142-156`).

The evidence rules out the proposed alternatives. There is no intermediate `main` wrapper (`copilot_sdk/frontend/CopilotShell.tsx:80-83`), Analysis test 6 does not use a different helper (`e2e/purchasing/analysis.spec.ts:4-11`, `:50-55`), and the selector’s direct-child relation matches the JSX (`apps/purchasing/frontend/src/App.tsx:59-64`).

The SC-14 Purchasing component has a separate boundedness defect: its fetch sets local `loading` false only in the success handler and has no rejection handler (`apps/purchasing/frontend/src/components/DecisionExplorerPanel.tsx:21-32`). It does not itself control the screen-ready selector because it has no `data-screen-ready` attribute (`apps/purchasing/frontend/src/components/DecisionExplorerPanel.tsx:40-45`), but it can remain visually stuck after the screen root becomes ready.

## Why Dashboard Works

Dashboard’s root has the required direct-child attribute and transitions from false to true in its own loader (`apps/purchasing/frontend/src/screens/DashboardScreen.tsx:103-155`, `:163-178`). The observed pass result means those requests settle within the test window. The screen’s later child components do not change the direct-child readiness condition.

The persistent SC wrapper is also correctly configured for Purchasing: the app supplies the Purchasing backend `/api/self` base URL (`apps/purchasing/frontend/src/App.tsx:2-3`, `:64`), and the shared panels expose their own readiness attributes with `catch`/`finally` completion (`copilot_sdk/frontend/CentroidTimelinePanel.tsx:9-23`; `copilot_sdk/frontend/AccuracyAlertsPanel.tsx:6-11`; `copilot_sdk/frontend/RuleGenealogyPanel.tsx:5-10`; `copilot_sdk/frontend/DecisionExplorerPanel.tsx:5-10`; `copilot_sdk/frontend/RuleLifecyclePanel.tsx:5-11`; `copilot_sdk/frontend/AuditTrailPanel.tsx:5-10`).

## Why Analysis Test 6 Fails

There is no source-level navigation distinction between tests 1–5 and test 6. All six run `gotoAnalysis` (`e2e/purchasing/analysis.spec.ts:4-11`, `:13-55`). Test 6 is the first test whose assertion explicitly requests the SC-14 content (`e2e/purchasing/analysis.spec.ts:50-55`), but the reported timeout occurs inside `waitForScreenReady`, before those assertions.

The screen root can remain false because Analysis waits on an unbounded `Promise.all` for analytics and fingerprint data (`apps/purchasing/frontend/src/screens/AnalysisScreen.tsx:64-78`; `apps/purchasing/frontend/src/api.ts:103-109`, `:156-158`, `:449-451`). Concurrent SC requests are initiated by the persistent wrapper on every app load (`apps/purchasing/frontend/src/SelfComputationPanels.tsx:10-11`), so request timing can expose this condition even when the backend endpoints themselves return valid responses.

## Why Inventory Fails Completely

Every Inventory test uses the same readiness helper (`e2e/purchasing/helpers.ts:5-10`). Inventory’s ready transition waits for the initial items/variants calls and then waits for all item waste-history calls (`apps/purchasing/frontend/src/screens/InventoryScreen.tsx:100-115`). The per-item calls use unbounded `apiGet` (`apps/purchasing/frontend/src/api.ts:103-109`, `:239-241`). If one remains pending, the `Promise.all` never reaches the `finally` block that sets `loading` false (`apps/purchasing/frontend/src/screens/InventoryScreen.tsx:116-124`). Consequently, the direct child remains `data-screen-ready="false"` (`apps/purchasing/frontend/src/screens/InventoryScreen.tsx:142-143`) and all three tests time out at the same helper.

## Cross-Copilot Impact (Trading, DataOps)

Trading uses the same `CopilotShell` and keeps `SelfComputationPanels` as a child alongside its active screen (`apps/trading/frontend/src/App.tsx:55-84`). Its Dashboard, Analysis, Performance, and Trade Detail screens also expose false/true screen-readiness branches (`apps/trading/frontend/src/screens/DashboardScreen.tsx:199-212`; `apps/trading/frontend/src/screens/AnalysisScreen.tsx:140-153`; `apps/trading/frontend/src/screens/PerformanceScreen.tsx:103-116`; `apps/trading/frontend/src/screens/TradeDetailScreen.tsx:139-163`). Therefore the same persistent-panel readiness gate applies, although the exact screen-loader risks depend on each screen’s API implementation.

DataOps likewise renders active `content` and `SelfComputationPanels` as siblings inside `CopilotShell` (`apps/dataops/frontend/src/App.tsx:45-71`, `:73-96`). Its Dashboard exposes a computed ready state (`apps/dataops/frontend/src/screens/DashboardScreen.tsx:177-190`), while Insight, Evidence, and Curve also have screen-ready roots (`apps/dataops/frontend/src/screens/InsightScreen.tsx:102-134`; `apps/dataops/frontend/src/screens/EvidenceScreen.tsx:66-91`; `apps/dataops/frontend/src/screens/CurveScreen.tsx:58-86`). The architecture can reproduce the same class of issue if one of those loaders never settles; this report does not claim a specific DataOps failing request without a runtime trace.

## Recommended Fix

The minimal robust fix is one Purchasing API-layer change, plus the existing screen branches remain unchanged:

1. Extend the already-present `apiGetWithTimeout` path (`apps/purchasing/frontend/src/api.ts:111-123`) to the initial Analysis and Inventory reads: `getAnalytics`, `getFingerprint`, `getItems`, and `getWasteHistory` (`apps/purchasing/frontend/src/api.ts:156-162`, `:239-241`, `:449-451`). Use the existing timeout mechanism rather than changing Playwright timeouts.
2. Update the Purchasing SC-14 component to handle rejection and settle its local loading state (`apps/purchasing/frontend/src/components/DecisionExplorerPanel.tsx:21-32`). This is needed for visible SC-14 error/empty behavior, though it is not the direct-child screen gate.
3. Keep `waitForScreenReady` unchanged. Its direct-child selector matches the actual shell hierarchy (`e2e/helpers/ui.ts:36-39`; `copilot_sdk/frontend/CopilotShell.tsx:80-83`).

Recommended scope: **2 Purchasing frontend files**, primarily `apps/purchasing/frontend/src/api.ts` and `apps/purchasing/frontend/src/components/DecisionExplorerPanel.tsx`; no backend, SDK shell, Playwright helper, or test changes are required by the diagnosis. The same SC base-URL/readiness pattern is shared by all three copilots through the app-specific `SelfComputationPanels` mounts (`apps/purchasing/frontend/src/App.tsx:64`; `apps/trading/frontend/src/App.tsx:83`; `apps/dataops/frontend/src/App.tsx:95`), so the shared panel fix has cross-copilot impact, while the unbounded loader fix identified here is Purchasing-specific.

## Files Read (complete list)

- `CLAUDE.md`
- `e2e/helpers/ui.ts`
- `e2e/purchasing/helpers.ts`
- `e2e/purchasing/analysis.spec.ts`
- `e2e/purchasing/inventory.spec.ts`
- `e2e/purchasing/dashboard.spec.ts`
- `e2e/purchasing/order.spec.ts`
- `e2e/purchasing/performance.spec.ts`
- `e2e/fixtures/copilot-fixture.ts`
- `copilot_sdk/frontend/CopilotShell.tsx`
- `copilot_sdk/frontend/index.ts`
- `copilot_sdk/frontend/SelfComputationPanels.tsx`
- `copilot_sdk/frontend/CentroidTimelinePanel.tsx`
- `copilot_sdk/frontend/AccuracyAlertsPanel.tsx`
- `copilot_sdk/frontend/RuleGenealogyPanel.tsx`
- `copilot_sdk/frontend/DecisionExplorerPanel.tsx`
- `copilot_sdk/frontend/RuleLifecyclePanel.tsx`
- `copilot_sdk/frontend/AuditTrailPanel.tsx`
- `apps/purchasing/frontend/src/App.tsx`
- `apps/purchasing/frontend/src/api.ts`
- `apps/purchasing/frontend/src/screens/DashboardScreen.tsx`
- `apps/purchasing/frontend/src/screens/AnalysisScreen.tsx`
- `apps/purchasing/frontend/src/screens/InventoryScreen.tsx`
- `apps/purchasing/frontend/src/screens/OrderScreen.tsx`
- `apps/purchasing/frontend/src/screens/PerformanceScreen.tsx`
- `apps/purchasing/frontend/src/components/DecisionExplorerPanel.tsx`
- `apps/purchasing/frontend/src/components/RuleLifecyclePanel.tsx`
- `apps/trading/frontend/src/App.tsx`
- `apps/trading/frontend/src/screens/DashboardScreen.tsx`
- `apps/dataops/frontend/src/App.tsx`
- `apps/dataops/frontend/src/screens/DashboardScreen.tsx`
- `apps/dataops/frontend/src/screens/InsightScreen.tsx`
- `apps/dataops/frontend/src/screens/EvidenceScreen.tsx`
- `apps/dataops/frontend/src/screens/CurveScreen.tsx`
