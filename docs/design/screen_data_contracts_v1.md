# Screen Data Contracts v1

## Executive Summary

Screen Data Contracts separate bounded, screen-shaped projections from raw
decision/history stores. The immediate Purchasing change is an Inventory
summary contract that removes the 20-item history fan-out; the parallel
Dashboard change is a compact order projection that replaces the unbounded
metadata transfer. The reusable platform pattern is a typed summary/detail
API over domain-scoped GraphStore queries, with request and payload budgets.

## Problem Statement

Purchasing Inventory currently requests items and variants, then one waste
history per returned item (InventoryScreen.tsx:95-110). The current catalog
has 20 items (measured `apps/purchasing/backend/app/items.json`), so the parent
starts 22 operations. It then mounts seven request-bearing card groups, adding
15 common-case operations (InventoryScreen.tsx:155-164; RuleGenealogyTree.tsx:13-31;
RuleLifecyclePanel.tsx:15-34; AuditTrailViewer.tsx:22-30;
SupplierIntelligencePanel.tsx:85-166; PredictiveParCard.tsx:18-38;
EventPlannerCard.tsx:17-36; DeliveryScheduleCard.tsx:15-36). The observed load is
20–30 seconds; a live sample measured small endpoint responses at about
2.0–3.7 seconds, consistent with backend contention.

Dashboard separately fetches the complete order-metadata map in its initial
`Promise.all` (DashboardScreen.tsx:103-117). The supplied live observation was
approximately 949KB; the current local snapshot measured 1,155,635 bytes,
1,105 entries, 18 unique display names, and a 61.39:1 entry/name ratio. The
backend returns the entire JSON object without projection, pagination, or a
limit (context_router.py:296-298). The two failures are related contract
problems but have different direct callers: Inventory does not call
`getOrderMetadata` (InventoryScreen.tsx:1-13), while Dashboard does
(DashboardScreen.tsx:110-116).

## Current State

### Purchasing Data Flow (per screen, with request counts)

| Screen | Source-backed request work | Baseline |
|---|---|---:|
| Dashboard | items, today summary, history, full metadata, analytics, variants, plus waste for low items | 6 + data-dependent waste calls (DashboardScreen.tsx:110-127) |
| Order | base data, reason codes, selected-item data, and verification actions | data-dependent (OrderScreen.tsx:246-317) |
| Analysis | analytics/fingerprint and conservation/promotion groups | 2 groups (AnalysisScreen.tsx:59-106) |
| Inventory | items + variants + one waste history per item; seven child groups | 22 initial; 37 common mounted operations (InventoryScreen.tsx:101-164) |
| Performance | trajectory and conservation data | data-dependent (PerformanceScreen.tsx:50-88) |

The count is source-level request operations, not guaranteed wire requests:
`Promise.all`, retries, browser caching, and React development behavior can
change observed events.

### Trading Data Flow

Trading has Dashboard, Analysis, Journal, LogTrade, Performance, and
TradeDetail screens (screen directory). Analysis uses analytics, fingerprint,
conservation, and promotion calls (apps/trading/frontend/src/screens/AnalysisScreen.tsx:76-106);
Dashboard uses history, metadata, analytics, and market calls
(apps/trading/frontend/src/screens/DashboardScreen.tsx:172-179); Journal has
trade/analytics loaders (JournalScreen.tsx:58-90); TradeDetail loads history
and metadata (TradeDetailScreen.tsx:90-103). No verified fixed Trading
per-item fan-out is present in the evidence, so its contract must follow a
request trace rather than copy Purchasing’s number.

### DataOps Data Flow

DataOps has Dashboard, Curve, Evidence, Insight, and Triage screens (screen
directory). Dashboard loads alert/trajectory groups (DashboardScreen.tsx:80-126),
Curve loads centroid history and trajectory (CurveScreen.tsx:16-58), Evidence
loads variants, pattern origin, and AE impact (EvidenceScreen.tsx:30-66),
Insight loads fingerprint and incident (InsightScreen.tsx:57-102), and Triage
loads alert/dependency data (TriageScreen.tsx:106-132). These are multi-resource
loaders, but no Purchasing-style item loop was verified.

## What-If Analysis

### WI-1 — `/api/inventory/summary`

Return one record per catalog item with the fields rendered by Inventory plus
waste aggregate/trend and variant count. Replace the `getItems()` call and
`nextItems.map(...getWasteHistory...)` loop (InventoryScreen.tsx:101-110) with
one request; retain existing category grouping and item-profile rendering
(InventoryScreen.tsx:132-139, 177-218). Parent operations fall from 22 to 1.
The 15 child operations remain until lazy-loading or child aggregation is
migrated, so the interim total is 16, not 1 for the fully mounted tree.
Inventory E2E assertions are content-oriented (e2e/purchasing/inventory.spec.ts;
e2e/purchasing/flows.spec.ts:152-163, 199-203), so the projection must
preserve category, waste, variant, and inventory text. Add backend contract
tests for one-record-per-item, empty history, stable names, and byte budget.

### WI-2 — Dashboard projection

Dashboard’s joining helper and order card need item, category, action, reward,
and date (DashboardScreen.tsx:70-86; OrderCard.tsx:22-27, 33). Add a versioned
projection rather than changing the raw route: backend tests explicitly cover
the old route (apps/purchasing/backend/tests/test_purchasing_backend.py:164-216),
and `getOrderMetadata` is called by Dashboard (api.ts:399-407). Keep the old
endpoint during migration, switch Dashboard to the projection, then deprecate
only after consumers are inventoried.

### WI-3 — JSON caching

`items()` and `waste_history()` parse JSON in the request path
(context_router.py:251-273); metadata does the same
(context_router.py:287-298). Caching parsed snapshots reduces repeated work,
but the metadata write path must invalidate after `write_purchasing_fixture`
(context_router.py:287-293). Caching cannot reduce response size or browser
request count, and stale data after preseed reruns is a material risk. It is a
quick win, not a substitute for summary endpoints.

### WI-4 — All copilots

Trading and DataOps have multi-resource loaders as cited above; S2P needs a
separate trace before any fan-out count is assigned. The common abstraction is
a domain-owned summary router and projection service over a shared,
domain-scoped GraphStore query. Summary routes return bounded latest-per-
entity data; detail routes return cursor-paginated records. Do not impose a
Purchasing-specific field model on the other domains.

### WI-5 — Preseed 200 → 60

The script targets 200 decisions (scripts/preseed_all_copilots.py:24,
530-538), cycles source records, and stamps sequence metadata
(scripts/preseed_all_copilots.py:266-280). Reducing to 60 can shorten demo
setup but does not fix an unbounded route (context_router.py:296-298), and may
weaken the learning-curve narrative. Keep 200 for contract work; evaluate 60
only with trajectory, conservation, and category-coverage acceptance tests.

### WI-6 — Lazy child cards

All seven Inventory cards mount immediately (InventoryScreen.tsx:155-164),
accounting for 15 common child operations. Explicit expand/click loading can
defer them, but E2E tests asserting child content after navigation must gain
an explicit interaction/readiness wait. Viewport lazy loading is less
deterministic. Apply after the summary contract.

### WI-7 — Request budget

Use a development warning and a stable Playwright assertion. Inventory’s
interim budget is 16 operations (one summary plus current children); after
lazy migration target at most five initial operations. Count only allow-listed
backend resources and account for retries/Strict Mode. A new component that
exceeds the budget should fail its owning screen test.

## Blast Radius Matrix

| Change | Backend | Frontend/types | Tests |
|---|---|---|---|
| Inventory summary | Purchasing context router or new inventory router/service | InventoryScreen.tsx, api.ts, types.ts | backend summary tests, inventory.spec.ts, purchasing flows |
| Dashboard projection | New versioned Purchasing projection handler | DashboardScreen.tsx, api.ts, projection type | new projection tests; retain metadata tests; dashboard specs |
| JSON cache | context_router.py/data helper | none | read/write invalidation tests |
| Child lazy loading | none | InventoryScreen and seven child boundaries | inventory, delivery, event, and flow PW specs |
| Preseed reduction | scripts/preseed_all_copilots.py and regenerated fixtures | none | preseed, trajectory, conservation tests |

The first three changes are Purchasing-only. Cross-copilot adoption adds one
router/projection, API module changes, types, and tests per adopting domain.

## Design Decisions

| # | Decision | Options | Recommendation | Reasoning |
|---:|---|---|---|---|
| 1 | Summary path | `/api/inventory/summary`; `/api/purchasing/inventory-summary`; `/api/context/inventory` | `/api/inventory/summary` | Clear screen-domain contract, separate from raw context routes (context_router.py:251-298). |
| 2 | Aggregation | route; service; GraphStore | projection service over GraphStore/source, thin router | Keeps latest-per-item and waste semantics out of React (InventoryScreen.tsx:132-190). |
| 3 | Dashboard | compact old route; new endpoint | versioned new projection, retain old route | Preserves existing tests and unknown consumers (test_purchasing_backend.py:164-216). |
| 4 | Cache | lru_cache; startup load; none | explicit cache with write invalidation | Reduces repeated parses without stale writes (context_router.py:287-293). |
| 5 | Children | eager; expand; viewport | eager summary, explicit lazy detail for expensive cards | Deterministic user/test interaction; current tree is eager (InventoryScreen.tsx:155-164). |
| 6 | Preseed | 200; 100; 60 | retain 200 initially | Smaller fixtures mask, rather than repair, unbounded growth. |
| 7 | Budget | warning; hard assertion; none | warning plus hard PW assertion | Detects recurrence while keeping production behavior independent of tests. |
| 8 | Timing | one prompt; separate prompts | separate copilot migrations | Each domain needs source-backed entity and request trace. |
| 9 | Types | reuse broad optional types; slim types | new slim summary/detail types | Existing Item and OrderMetadata are broad (types.ts:87-104, 166-190). |
| 10 | Compatibility | keep; deprecate; remove | keep old endpoints, add projections, deprecate later | Safe incremental rollout. |

## Proposed API Contract

### Summary Endpoints

Purchasing:

```text
GET /api/inventory/summary
```

Future domain-owned equivalents, only after trace-driven design:

```text
GET /api/trading/summary/{resource}
GET /api/dataops/summary/{resource}
GET /api/s2p/summary/{resource}
```

The resource is an allow-listed entity, never an arbitrary file/query name.

### Detail Endpoints

```text
GET /api/inventory/items/{item}/history?cursor=&limit=50
GET /api/{domain}/{resource}/{id}/history?cursor=&limit=50
```

Detail is bounded and cursor-paginated for drill-down, audit, and explorer
views, not initial catalog rendering.

### TypeScript Types (contract shapes)

```ts
type InventorySummaryItem = {
  id: string; name: string; displayName?: string; category: string;
  unit?: string; quantity?: number; wasteAveragePct: number;
  wasteTrend: "improving" | "stable" | "worsening" | "unknown";
  historyCount: number; latestVariantCount: number;
};
type InventorySummary = {
  items: InventorySummaryItem[]; categories: string[]; generatedAt: string;
};
type PagedDetail<T> = {
  items: T[]; nextCursor?: string; hasMore: boolean;
};
```

These deliberately omit raw factors and arbitrary metadata; the fields derive
from actual Inventory reads (InventoryScreen.tsx:39-53, 56-62, 177-218).

### Response Envelope

```text
{
  data: <typed projection>,
  meta: {
    domain: string, tenantId?: string, generatedAt: string,
    count: number, truncated: boolean, provenance: string
  }
}
```

The server derives domain/tenant scope and enforces it in the GraphStore
query. `truncated` is explicit whenever detail is omitted.

## Migration Plan

### Phase 0 — JSON caching (2–4 hours)

Change `apps/purchasing/backend/app/context_router.py` or its data helper.
Add read/write invalidation tests. Dependency: none. Main risk is stale
preseed/order data. Roll back by disabling cache while keeping routes.

### Phase 1 — Inventory summary (6–10 hours)

Add the Purchasing summary handler/service; update
`apps/purchasing/frontend/src/api.ts`, `types.ts`, and `InventoryScreen.tsx`.
Update/add Purchasing backend tests, `e2e/purchasing/inventory.spec.ts`, and
relevant flows. Dependency: shared envelope conventions; risk is field or
waste-trend mismatch. Roll back at the API adapter boundary to old calls.

### Phase 2 — Dashboard projection (4–8 hours)

Add a versioned projection handler and update Purchasing `api.ts` and
`DashboardScreen.tsx`. Add projection tests; retain old metadata tests and
dashboard specs. Verify fields against DashboardScreen.tsx:70-86 and
OrderCard.tsx:22-33. Roll back Dashboard to `getOrderMetadata()`.

### Phase 3 — Child loading (8–14 hours)

Update `InventoryScreen.tsx` and the seven child boundaries. Update inventory,
delivery, event, and flow PW tests with explicit interactions/readiness checks.
Dependency: Phase 1. Roll back to eager mounting while retaining summary use.

### Phase 4 — Cross-copilot adoption (12–24 hours per copilot)

Trace then migrate Trading, DataOps, and S2P independently: domain router/
projection, frontend API/types, target screen, backend tests, and PW tests.
Dependency: frozen envelope and summary semantics. Roll back each screen to
its existing endpoint independently.

### Phase 5 — Budget enforcement (4–8 hours)

Add E2E request/payload assertions and optional development telemetry after a
baseline exists. Count only allow-listed resources. Roll back hard assertions
to warnings without changing screen behavior.

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Summary omits a child field | High | derive from source reads; contract fixtures |
| Old metadata consumers break | High | add projection; retain old route/tests |
| Cache staleness | Medium | write invalidation and generation timestamp |
| Queue remains slow after compaction | High | measure concurrency separately; cache repeated reads |
| Lazy cards break PW | Medium | explicit interaction/readiness assertions |
| Cross-copilot over-generalization | High | shared envelope, domain-owned fields |
| Budget false positives | Medium | account for retries/Strict Mode and filter origins |
| Scope leak | Critical | GraphStore-enforced domain/tenant query scope |

## Cross-Copilot Pattern (Reusable Abstraction)

```text
Screen -> typed API client -> domain summary router
       -> projection service -> scoped GraphStore query -> bounded envelope

Interaction -> typed detail API -> cursor-paginated scoped query
```

The router owns HTTP validation, the projection service owns latest/entity
aggregation, and GraphStore owns durable scoped reads. The existing separation
between typed API functions and backend routes supports this pattern
(api.ts:152-236; context_router.py:251-298). Shared infrastructure is the
envelope, pagination, scope, and budgets—not a Purchasing-specific schema.

## Request Budget Enforcement

Each screen manifest declares screen ID, allowed initial endpoints, maximum
initial operations, maximum payload bytes, and first-usable-content deadline.
Inventory’s interim budget is 16; after child lazy loading the target is at
most 5. The existing readiness gate is 15 seconds (e2e/helpers/ui.ts:36-39),
so the content deadline must leave rendering margin. Enforce with development
warnings and Playwright assertions; do not increase readiness timeouts.

## Success Criteria

| Metric | Baseline | Target |
|---|---:|---:|
| Inventory initial operations | 22 (37 common mounted) | 1 parent; ≤5 after child migration |
| Inventory usable load | 20–30s observed | ≤5s on demo stack |
| Dashboard payload | ~949KB supplied; 1.10MiB local | ≤100KB projection target, measured |
| Metadata growth | 1,105 local entries / 18 names | bounded by visible projection, not decisions |
| Small endpoint latency | 2.0–3.7s sample | p95 ≤500ms for cached local reads; graph routes separate |
| Readiness failures | Inventory slow/flaky | zero readiness timeouts in repeat runs |

Targets are acceptance criteria and require repeatable cold/warm measurements.

## What This Does NOT Change

- It does not change scoring, learning, conservation, evolution, or decision
  semantics; it changes transport shape and scheduling only.
- It does not change GraphStore domain/tenant isolation.
- It does not remove or reshape `/api/context/order-metadata` in the first
  migration (context_router.py:296-298).
- It does not increase Playwright timeouts or change `waitForScreenReady`.
- It does not require reducing the preseed target (scripts/preseed_all_copilots.py:24).
- It does not assume Trading, DataOps, or S2P have Purchasing’s exact fan-out.
- It does not allow client-selected files, unscoped queries, silent truncation,
  or mock/fallback data.
