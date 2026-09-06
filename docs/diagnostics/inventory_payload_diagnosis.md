# Purchasing Inventory payload diagnosis

## Summary

The evidence does not support `/api/context/order-metadata` as a direct
Inventory-screen request. `InventoryScreen` imports and calls `getItems`,
`getEvolutionVariants`, and `getWasteHistory`, while `getOrderMetadata` is
called by `DashboardScreen` (InventoryScreen.tsx:1-13, 95-125; api.ts:156-157,
235-236, 399-413; DashboardScreen.tsx:103-117). The Inventory load path does
have a substantial fan-out: two initial requests, one waste-history request
per item, and several child-card request groups after the screen mounts
(InventoryScreen.tsx:101-110, 155-164). The supplied 949KB metadata observation
is a real payload problem for Dashboard and any future consumer, but it is not
the measured direct cause of Inventory’s 20–30 second load. In the current
workspace snapshot, `order_metadata.json` is 1,155,635 bytes with 1,105 entries
and 18 unique display names; the live GET did not finish reading within 8
seconds during this audit. The most defensible root cause is combined backend
request contention plus Inventory’s request fan-out, with payload/rendering as
secondary factors.

## Data Flow Diagram (text)

```text
Browser -> Purchasing App -> InventoryScreen
                              |
                              +-- GET /api/context/items
                              +-- GET /api/evolution/variants
                              +-- for each item:
                              |      GET /api/context/waste-history/{item}
                              |
                              +-- mounted child cards:
                                     evolution variants/history/promoted
                                     self audit trail
                                     QBO status/vendors/bills
                                     predictive par week
                                     event plan/history
                                     delivery today/week/consolidation

Browser -> Purchasing App -> DashboardScreen (separate path)
                              |
                              +-- GET /api/context/order-metadata
                                  returns the complete order_metadata.json map
```

The Inventory branch is selected by the app when `activeTab === "inventory"`
and is distinct from the Dashboard branch (App.tsx:59-64). The server’s
`/items` route reads `items.json` and the waste route reads the complete waste
history file before selecting one item (context_router.py:251-273). The
metadata route reads the complete JSON object and returns it unchanged
(context_router.py:296-298).

## Payload Analysis

### Measured values

| Measurement | Result | Evidence |
|---|---:|---|
| Supplied live payload baseline | approximately 949KB | User-provided verified measurement |
| Current local `order_metadata.json` | 1,155,635 bytes (1.10 MiB) | Measured with `os.path.getsize` during this audit |
| Current metadata entries | 1,105 | `len(json.load(order_metadata.json))`, measured during this audit |
| Current unique display names | 18 | Set of `display_name`/item fields, measured during this audit |
| Current entries per unique display name | 61.39 | `1105 / 18`, measured during this audit |
| Current bytes per metadata entry | approximately 1,045 | `1,155,635 / 1,105`, measured during this audit |
| Current Purchasing item definitions | 20 | `len(app/items.json)`, measured during this audit |
| `_preseed_sequence` range in metadata | 1–200 | Parsed from current metadata, measured during this audit |

The local snapshot differs from the supplied 949KB live baseline, so both are
reported rather than conflated. In either case, the response is an entry map
keyed by decision ID, not a compact one-record-per-item view: the backend
returns `_load_json(_DATA_DIR / "order_metadata.json")` directly
(context_router.py:296-298). The preseed script sets the default target to
200 decisions per copilot (scripts/preseed_all_copilots.py:22-26), expands
records by cycling the source seed, and stamps `_preseed_sequence`
(scripts/preseed_all_copilots.py:266-280). It also tops up until that target
is reached (scripts/preseed_all_copilots.py:530-538).

### Bloat ratio and field waste

For the current local snapshot, the raw metadata map contains 1,105 entries
for 18 unique display names, a 61.39:1 entry-to-name ratio. The Inventory
screen does not consume this map. Its item cards receive an `Item`, one
`WasteHistory`, and matching `Variant` objects (InventoryScreen.tsx:197-218).
The fields directly read from `Item` are `category`, `name`, `displayName`,
`itemId`, and the category grouping; waste uses `wastePct`; variant mapping
uses identifiers, description, metadata/graph context, magnitude, status, and
matching categories (InventoryScreen.tsx:39-53, 56-62, 78-85, 132-140,
177-190, 212-218). The `Item` type contains substantially more optional
fields—unit, par level, quantities, price, supplier, sensitivity, usage range,
and lead time—which are not read by this screen (types.ts:87-104).

For Dashboard, `OrderMetadata` declares at least 24 named fields plus an
index signature (types.ts:166-190), but the Dashboard’s order-joining helper
reads metadata to identify/display item, category, action, reward, and date
through `OrderCard` (DashboardScreen.tsx:70-86; OrderCard.tsx:22-27, 33).
Therefore the exact unused-field count depends on the active Dashboard child
and should not be inferred as an Inventory count. The architectural finding
is precise: the metadata endpoint returns full decision records while the
consumer’s visible order card needs a small projection.

## Endpoint Timing Table

The following timings were measured from the repository root against
`http://localhost:8020` during this audit. Each request included response-body
reading, not only connection time.

| Endpoint | Result |
|---|---|
| `/api/health` | 200, 1,929 bytes, 2,319ms |
| `/api/context/items` | 200, 6,426 bytes, 2,056ms |
| `/api/evolution/variants` | 200, 6,418 bytes, 3,708ms |
| `/api/context/waste-history/chicken_breast` | 200, 74 bytes, 2,040ms |
| `/api/context/order-metadata` | read timed out after 8,000ms in the audit run |
| `/api/self/centroid-timeline`, `/accuracy-alerts`, `/rule-genealogy`, `/decisions`, `/audit-trail` | not independently completed in the audit run because the preceding service timing showed live request contention |

These results are not a stable benchmark: they are one live-stack sample and
the user supplied the verified endpoint payload baseline. They do establish
that small endpoints themselves took roughly 2–4 seconds, so 20–30 seconds
can arise from request scheduling/contention even when individual JSON bodies
are small. The server handlers for items and waste history perform synchronous
file reads in the request path (context_router.py:251-273), and each Inventory
waste request repeats the JSON read (context_router.py:269-273).

## Screen Rendering Analysis

Inventory’s initial loading promise is:

1. `getItems()` and `getEvolutionVariants()` run concurrently
   (InventoryScreen.tsx:100-102).
2. After both finish, the screen starts one `getWasteHistory(item.name)` call
   for every returned item, concurrently via `Promise.all`
   (InventoryScreen.tsx:102-110).
3. It stores the results and renders the screen (InventoryScreen.tsx:111-124).

The current `items.json` contains 20 item definitions, so the expected initial
request count is 22: two initial requests plus 20 waste-history requests. The
exact count is data-dependent because the code maps over the response from
`getItems()` rather than a hard-coded constant (InventoryScreen.tsx:102-109).

The rendered main inventory content is five category rows plus one item
profile for each item in a nonempty category; it groups by category and
computes average waste from the fetched histories (InventoryScreen.tsx:132-139,
166-195, 197-223). It does not render hundreds of order-metadata entries.

After the root screen becomes ready, Inventory mounts additional components
that issue their own requests. `RuleGenealogyTree` requests variants and
history (RuleGenealogyTree.tsx:13-31); `RuleLifecyclePanel` requests variants,
history, and promoted rules (RuleLifecyclePanel.tsx:15-34); `AuditTrailViewer`
requests the audit trail (AuditTrailViewer.tsx:18-30); supplier intelligence
requests status, vendors, and bills and can request selected-supplier details
(SupplierIntelligencePanel.tsx:85-112, 129-166); predictive par requests one
weekly result (PredictiveParCard.tsx:18-38); event planning requests plan and
history (EventPlannerCard.tsx:17-36); delivery requests today, week, and
consolidation data (DeliveryScheduleCard.tsx:15-36). Thus the full mounted
Inventory view has 37 request operations in the common no-selection case:
22 initial Inventory requests + 2 + 3 + 1 + 3 + 1 + 2 + 3 child requests.
This is a request-operation count, not necessarily 37 sequential round trips,
because several groups use `Promise.all`.

The current API helper bounds ordinary GETs at 5 seconds using
`AbortController`, so a request should eventually settle even if the backend
does not respond (api.ts:103-118). Inventory’s per-item waste failure is
converted into an empty history, allowing the parent promise to settle for
that branch (InventoryScreen.tsx:103-108). The initial items/variants failure
still takes the outer error path (InventoryScreen.tsx:100-124).

## Root Cause (ranked)

1. **Request fan-out and backend contention — primary.** Inventory performs
   22 initial operations and mounts additional request groups immediately
   after the parent succeeds (InventoryScreen.tsx:101-164). The measured
   2.0–3.7 second latency for small endpoints means concurrent requests can
   queue behind the same backend process or shared graph/data resources. The
   synchronous JSON reads for every waste-history request reinforce the
   contention mechanism (context_router.py:269-273).

2. **Unbounded data access pattern — primary for Dashboard, secondary for
   Inventory.** `/api/context/order-metadata` returns the entire metadata map
   without a limit, projection, or aggregation (context_router.py:296-298).
   The current snapshot is 1.10MiB and 1,105 records, with a 61.39:1 ratio of
   records to unique display names. This can make Dashboard and any shared
   startup/navigation workload expensive, but Inventory itself has no call to
   `getOrderMetadata` (InventoryScreen.tsx:1-13; DashboardScreen.tsx:110-116).

3. **Repeated file parsing — secondary.** Every waste-history request parses
   `waste_history.json` afresh (context_router.py:269-273), multiplying work
   by the item count. The response body is small, so the cost is primarily
   repeated server-side work and scheduling, not transfer size.

4. **React rendering — secondary.** The screen renders 20 item profiles in
   the current catalog plus seven data-driven cards and category summaries
   (InventoryScreen.tsx:155-223). This is material DOM work, but the source
   does not render the 1,105 metadata entries, and no evidence establishes it
   as the dominant 20–30 second component.

5. **Payload transfer — real but not Inventory’s direct cause.** A 949KB
   response is wasteful and grows with decision count, but the only source
   call found is DashboardScreen’s metadata load (DashboardScreen.tsx:110-116;
   api.ts:399-402). It should be fixed independently of the Inventory fan-out.

## Fix Options (ranked by impact × effort)

| Option | Impact | Effort | Assessment |
|---|---|---|---|
| Backend compact summary for inventory/order views | High | Medium | Return one latest/aggregated record per item with only display fields; removes duplicate transfer and shifts aggregation to the server. |
| Eliminate per-item waste-history fan-out | High | Medium | Add a batch or summary response containing histories/trends for all catalog items; replaces 20 requests with one. |
| Cache parsed context files in the backend | Medium–High | Low–Medium | Avoids reparsing the same JSON for each request, but must define invalidation after fixture writes. |
| Pagination for raw order metadata/history | High for large histories | Medium | Appropriate for explorer/history UX; not sufficient for Inventory’s fixed catalog summary. |
| Client-side deduplication | Medium | Low | Reduces React data/DOM work only after the full 949KB/1.10MiB payload has transferred; not a complete fix. |
| Reduce preseed count | Medium for demo startup | Low | Decreases demo data, but hides the production growth problem and changes narrative density. |
| Make `order-metadata` compact in place | High for Dashboard | Medium | Good if all callers need only the projection; safer as a versioned summary endpoint because `OrderMetadata` is also used for order details. |

## Design What-If Analysis

### Growth Trajectory (D1)

The current preseed target is 200 decisions per copilot
(scripts/preseed_all_copilots.py:24, 530-538), while the current metadata
snapshot has 1,105 records and 1,155,635 bytes. At the observed local average
of approximately 1,045 bytes per entry, 10,000 raw records would be roughly
10.5MB before HTTP/container overhead. That is a linear projection, not a
measured future benchmark. The endpoint has no pagination or limit
(context_router.py:296-298), so response size and JSON parse work continue to
grow with record count. There is no code evidence for a precise browser
failure threshold; a practical tipping point should be established with a
load test at 1MB, 5MB, 10MB, and 25MB, including the backend queue and React
parse/render timings.

### Endpoint Contract Redesign (D2)

The code supports separating two contracts. The current metadata route is a
raw decision-metadata map (context_router.py:296-298). Inventory’s actual
contract is item definitions plus waste history and matching evolution rules
(InventoryScreen.tsx:101-110, 212-218). A better API would therefore be:

```text
GET /api/inventory/items
  [{ id, name, display_name, category, quantity, waste_avg, waste_trend,
     latest_variant_count }]

GET /api/inventory/items/{item}/history
  { item, waste_pct, count, optional decision/history details }
```

The exact paths are a design proposal, not existing routes. The screen would
replace `getItems()` plus the 20 `getWasteHistory()` calls with one summary
call, and fetch detailed history only when an item profile is expanded. The
existing `getOrderMetadata()` contract should remain available for Dashboard
or be versioned because it is explicitly called there (DashboardScreen.tsx:110-116;
api.ts:399-407).

### Aggregation Layer (D3)

“Group by item, show latest, compute waste trend” belongs in a backend query or
service projection, not in the browser. The current browser groups only the
20 `Item` records and computes averages from histories (InventoryScreen.tsx:132-139,
177-190); the backend currently exposes raw JSON reads for items, histories,
and metadata (context_router.py:251-273, 296-298). The GraphStore should remain
the durable source/query layer, while a Purchasing router/service should
return the typed inventory projection. This preserves a single source of
truth and keeps transport payloads aligned with the screen’s UX.

### Cross-Copilot Pattern (D4)

The repository search found the exact `order-metadata` route and
`getOrderMetadata()` consumer only under Purchasing; Trading has a documentation
mention of richer order metadata, not this route (repository search during this
audit; apps/trading/backend/docs/broker_integration.md:97). The reusable pattern
is a **domain-specific summary router over a common GraphStore query**, not a
single Purchasing-shaped endpoint. Trading log, DataOps decisions, and S2P
exceptions can each expose latest-per-entity summaries and paginated detail,
while the underlying query enforces domain scope. This follows the current
separation between typed frontend API functions and backend routes
(purchasing api.ts:152-236; context_router.py:251-298).

### Pagination vs Summary (D5)

Summary is the better fit for Inventory because the screen renders a fixed
catalog grouped by category and computes category-level waste metrics
(InventoryScreen.tsx:166-223). Pagination is better for an explorer or audit
history where users intentionally browse individual decisions; it would add
scroll state and still require a separate aggregation for the category cards.
For the demo narrative, “all inventory items at a glance” favors a compact
summary, while detailed decision history can be paginated behind an item or
decision interaction.

### Preseed Calibration (D6)

The preseed script intentionally targets 200 decisions (scripts/preseed_all_copilots.py:24,
530-538), and its expansion cycles seed records while adding sequence metadata
(scripts/preseed_all_copilots.py:266-280). Reducing to 3–5 observations per
item would lower demo data volume, but the code does not define a minimum
number required to demonstrate a learning curve. A defensible demo calibration
is to retain enough points for before/after and at least one variation per
category, then verify the visible trajectory and conservation panels; the
exact count requires a visual/product acceptance test, not inference from the
payload alone.

### Waste-History Fan-Out (D7)

The current implementation makes one request per item after the initial pair
(InventoryScreen.tsx:102-110), and the backend reads the same history JSON for
each request (context_router.py:268-273). A summary endpoint that includes
`waste_avg`, trend, and optionally the short series would reduce the common
path from 20 history requests to one. Detailed per-item history can remain a
separate endpoint for drill-down. This is the highest-leverage Inventory-
specific change because it directly removes the known N-request loop.

### Data-Screen Contract (D8)

A typed manifest would make the screen’s data budget explicit and prevent a
raw decision-store fetch from becoming a default dependency:

```ts
type ScreenDataManifest = {
  screen: "inventory" | "dashboard" | "analysis" | "performance";
  resources: Array<
    | { kind: "inventory-summary"; fields: Array<"name" | "category" | "wasteTrend"> }
    | { kind: "decision-history"; pageSize: number; cursor?: string }
    | { kind: "evolution-summary" }
  >;
  maxPayloadBytes: number;
};
```

The backend can validate the manifest against an allow-listed projection and
return a typed response envelope. This complements, rather than replaces,
GraphStore domain scoping: the manifest controls shape and volume, while the
query layer controls tenant/domain authorization.

## Recommended Fix — Immediate (unblock PW)

1. Add one Purchasing inventory-summary endpoint that returns the 20 catalog
   items with the fields rendered by `InventoryScreen` and includes waste
   aggregates/trends. Replace the initial `getItems()` plus per-item
   `getWasteHistory()` sequence with that one request. The target is to remove
   the loop at InventoryScreen.tsx:102-110, not to alter Playwright timeout
   helpers.
2. Keep `getOrderMetadata()` out of the Inventory path; separately stop
   Dashboard from loading the full raw metadata map by introducing a compact
   Dashboard order projection or pagination. Dashboard is the verified caller
   (DashboardScreen.tsx:110-116).
3. Instrument browser performance marks around the initial pair, summary
   response, React commit, and child-card requests. The present live timings
   show that backend contention must be measured alongside payload size.

## Recommended Design — Medium Term (prevent recurrence)

Use a versioned, typed summary/detail API pattern across copilots: summary
routes return latest-per-entity projections, detail routes are paginated, and
the GraphStore performs domain-scoped aggregation. Add payload-size and
request-count budgets to screen tests, for example: summary under a defined
byte budget, no N-per-item requests on initial mount, and a performance mark
for first usable content. Keep the existing bounded `apiGet` behavior as a
last-resort network guard (api.ts:103-118), but do not treat client timeouts as
a substitute for compact server contracts.

## Cross-Copilot Impact

The immediate Inventory fan-out fix is Purchasing-specific because the route,
screen, item catalog, and waste-history handlers are Purchasing files
(InventoryScreen.tsx:3, 101-110; api.ts:156-157, 235-236; context_router.py:251-273).
The summary/detail contract and GraphStore aggregation pattern should be
reused by Trading, DataOps, and S2P, but the audit found no equivalent
Purchasing `order-metadata` consumer in Trading or DataOps. No application
files were modified by this diagnostic work; this report is the only intended
file output.
