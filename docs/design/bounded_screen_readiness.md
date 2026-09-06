## Problem Statement

Screen-mount `useEffect` fetches can use an API helper with no deadline. If a
backend request hangs, the screen remains at `data-screen-ready="false"` and
`e2e/helpers/ui.ts:36-39` waits until its 15-second timeout. This makes the
safe path require extra effort while the unbounded path is the default.

## Design Decision

Use Option A: make each copilot's shared `apiGet` bounded by delegating to its
existing timeout implementation or an equivalent local implementation. This
is the smallest consistent boundary: screen loaders already call API-layer
functions, so no screen must remember a special helper and all existing
`safeApiGet` callers inherit the deadline. The change is confined to the
three copilot API modules and does not alter the Playwright helper or backend.

Purchasing already has `apiGetWithTimeout` at `apps/purchasing/frontend/src/api.ts:111-123`.
Trading and DataOps have unbounded `apiGet` functions at
`apps/trading/frontend/src/api.ts:71-77` and
`apps/dataops/frontend/src/api.ts:177-183`; they receive the same local
AbortController implementation.

## Timeout Value

The default API deadline is 5 seconds. `waitForScreenReady` allows 15 seconds
at `e2e/helpers/ui.ts:36-39`; Purchasing Inventory has two sequential bounded
request phases, so a 5-second per-request default keeps the aggregate loader
within the gate while leaving time for React to render the error branch.
Existing explicit 10-second calls remain explicit. A timeout rejects the API
promise; existing screen `catch`/`finally` branches set an error or safe empty
state and set loading false, making `data-screen-ready="true"` reachable.

## Scope Audit

| Copilot | Screen files | Readiness state | API boundary before change | PW status in supplied context |
|---|---|---|---|---|
| Purchasing | `DashboardScreen.tsx`, `AnalysisScreen.tsx`, `InventoryScreen.tsx`, `OrderScreen.tsx`, `PerformanceScreen.tsx` | All expose false and true branches (`DashboardScreen.tsx:163-178`, `AnalysisScreen.tsx:88-110`, `InventoryScreen.tsx:142-156`, `OrderScreen.tsx:458-463`, `PerformanceScreen.tsx:90-104`). | `apiGet` unbounded at `apps/purchasing/frontend/src/api.ts:103-109`; existing timeout helper at `:111-123`. | Dashboard 10/10, Order 8/8, Analysis 5/6, Inventory 0/3; Performance untested. |
| Trading | `DashboardScreen.tsx`, `AnalysisScreen.tsx`, `JournalScreen.tsx`, `LogTradeScreen.tsx`, `PerformanceScreen.tsx`, `TradeDetailScreen.tsx` | Readiness branches exist at `apps/trading/frontend/src/screens/DashboardScreen.tsx:199-212`, `AnalysisScreen.tsx:139-153`, `JournalScreen.tsx:119`, `PerformanceScreen.tsx:102-116`, and `TradeDetailScreen.tsx:138-163`; Log Trade uses `initialReady` at `LogTradeScreen.tsx:314`. | `apiGet` and `safeApiGet` are unbounded at `apps/trading/frontend/src/api.ts:71-83`. | Not specified for this diagnosis. |
| DataOps | `DashboardScreen.tsx`, `CurveScreen.tsx`, `EvidenceScreen.tsx`, `InsightScreen.tsx`, `TriageScreen.tsx` | Readiness is computed in Dashboard (`DashboardScreen.tsx:177-190`), Curve (`CurveScreen.tsx:50-58`), Evidence (`EvidenceScreen.tsx:59-66`), Insight (`InsightScreen.tsx:95-102`), and Triage (`TriageScreen.tsx:349-354`). | `apiGet` and `safeApiGet` are unbounded at `apps/dataops/frontend/src/api.ts:177-190`. | Not specified for this diagnosis. |

The shared SDK SC panels have rejection handling and readiness finalization,
but their raw `fetch` calls are independently bounded in the follow-up code
review. The app mounts them against the correct backend `/api/self` base URL
(`apps/purchasing/frontend/src/App.tsx:64`, `apps/trading/frontend/src/App.tsx:83`,
`apps/dataops/frontend/src/App.tsx:95`).

## Migration Plan

1. Add a 5-second AbortController-based implementation to Trading and
   DataOps `api.ts`; make Purchasing `apiGet` delegate to its existing helper.
2. Leave all screen readiness branches and `waitForScreenReady` unchanged.
3. Add rejection handling to the Purchasing app-level SC-14 component if its
   promise chain lacks a catch/finally; its current loading chain is at
   `apps/purchasing/frontend/src/components/DecisionExplorerPanel.tsx:21-32`.
4. Verify all three frontend typechecks, E2E typecheck, and screen/dashboard
   Playwright suites with the demo-managed backend stack.

Expected blast radius is API-call timing and error presentation only. Normal
responses complete unchanged; requests exceeding 10 seconds now select the
screen's existing error/empty-state branch instead of blocking readiness.
