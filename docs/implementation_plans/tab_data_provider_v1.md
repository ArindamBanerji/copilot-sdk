# Tab Data Provider Architecture

## 1. Executive Summary

Trading, Purchasing, DataOps, and S2P tabs currently mount many independent auto-fetching panels. The worst Trading tabs issue roughly 20 to 23 reads on a single tab transition. The first proposal replaced those reads with one batched request. That reduces HTTP round trips, but it does not change the compute model: one batch containing 23 keys still computes 23 service functions during tab mount.

This design replaces request-batching with materialized tab state. Tab data becomes server-side state that is computed after mutations and served to tabs as a cache read.

The target model:

```text
MUTATION: score / verify / learn / reset / transfer / promote
  -> backend recomputes only affected static keys
  -> backend atomically replaces those cached entries
  -> mutation returns after Wave 1 critical recomputation
  -> Wave 2 deferred keys refresh without blocking tab reads

TAB MOUNT
  -> frontend calls GET /api/{copilot}/tab-state?keys=a,b,c
  -> backend reads cached static entries only
  -> no service functions run on warm tab mount
  -> tab renders in under 50 ms for materialized static data
```

Batching is insufficient because it keeps computation on the hot path. Materialized state moves static, read-heavy computation to the cold path. Dynamic keys that depend on a selected ticker, invoice, alert, supplier, item, or system are not materialized globally; they remain individual fetches keyed by user selection.

## 2. Architecture

The backend owns a per-copilot `TabStateCache`. Each cache has a declarative registry of materializable static keys. Each key has a compute function, invalidation events, and a criticality flag.

```python
{
    "vol-sharpe": {
        "compute": compute_vol_sharpe,
        "invalidated_by": ["score", "verify"],
        "critical": False,
    }
}
```

The tab-state endpoint is a read facade:

```http
GET /api/{copilot}/tab-state?keys=analytics,fingerprint,vol-sharpe
```

Response:

```json
{
  "analytics": { "data": {}, "error": null, "status": "ready" },
  "fingerprint": { "data": {}, "error": null, "status": "ready" },
  "vol-sharpe": { "data": null, "error": "not materialized", "status": "missing" }
}
```

Important rules:

- The read endpoint does not dispatch to analytics, scorer, graph traversal, or panel services after warm-up.
- If the cache is cold, the first tab-state request triggers synchronous warm-up for static keys only.
- Static keys are globally materializable per copilot.
- Dynamic parameterized keys remain individual endpoint calls.
- Derived keys should be computed from cached static values in the frontend or provider without another backend read.

Mutation invalidation uses a registered decorator or mutation-path registry, not hand-written one-off hooks in every route:

```python
@invalidates("score")
async def score_decision(request: ScoreRequest):
    result = scorer.score(request)
    return result
```

The decorator invalidates the affected cache keys after the handler returns successfully. If decorators are too invasive for shared SDK routes, middleware uses a `MUTATION_PATHS` table:

```python
MUTATION_PATHS = {
    "/api/score": "score",
    "/api/learn": "learn",
    "/api/purchasing/verify": "verify",
    "/api/trading/evolution/promote": "evolution",
    "/api/transfer/execute": "transfer",
}
```

The source scan shows why this registry is required: scorer mutations exist in shared SDK routes (`copilot_sdk/backend/scoring_router.py` for `/score` and `/learn`), per-copilot verify routes (`apps/purchasing/backend/app/routers/verify_router.py`), and other POST routes such as transfer, archetype apply, discovery refresh, journal, broker, market refresh, promotion, auto-order, match, and chain transfer. Missing one hook would leave stale materialized state.

## 3. Design Constraints

C1. Tab mount equals cache read. Zero service function calls on warm mount. O(1) regardless of static panel count. Target: under 50 ms for full materialized static tab data.

C2. Mutation equals selective recomputation. After `POST /api/score`, recompute only keys that depend on score results, such as trajectory, analytics, and conservation. Do not recompute fingerprint, archetypes, or regime history.

C3. Cold start. On first request after backend startup, the cache is empty. The first tab-state request triggers synchronous warm-up of static keys only. Alternative and preferred path: preseed populates the cache after preseed data exists.

C4. Panel registration is declarative. Adding a materialized panel requires one registry entry with key, compute function, invalidation events, criticality, and category.

C5. Individual endpoints remain. The cache system is a performance facade. Endpoints like `/api/fingerprint` stay for backward compatibility, tests, direct consumers, dynamic user-selection reads, and manual refresh.

C6. Cache consistency. The cache must not serve a key as fresh after a mutation if recomputation failed. If recomputation fails for an invalidated key, that entry becomes `{ data: null, error: "...", status: "invalidated_error" }`. It may retain `previous_data` for diagnostics, but `data` must not contain stale data for an invalidated failed key.

C7. Per-key error isolation. If one key's computation fails, other keys are unaffected. The failed key returns `{ data: null, error: "..." }`.

C8. No global lock. Mutations should not block tab reads. Cache updates are atomic per key. Reads copy current entries without waiting for unrelated key recomputation.

C9. Works with single-threaded uvicorn. Recompute work after mutation must not block the event loop for more than 500 ms total. The concrete protocol is Wave 1 and Wave 2:

- Wave 1 runs synchronously before the mutation response returns. It contains only critical keys that the frontend immediately rereads. Target: <=300 ms, usually three keys at about 100 ms each.
- Wave 2 runs after the mutation response returns. It contains non-critical below-fold keys. It is scheduled with `asyncio.create_task`, processes batches of at most three keys, and awaits `asyncio.sleep(0)` between batches so tab-state reads can run.
- Wave 2 entries return `status: "refreshing"` with previous cached data until recomputation completes. If the key had never been materialized, `data` remains null.

C10. Testable. Cache warm-up, invalidation, selective recomputation, cold start, version races, Wave 1 timing, Wave 2 refresh state, memory bounds, mutation-path registration, and error isolation must all be unit-testable without running a full backend.

## 4. Components

### 4.1 TabStateCache

Backend, one cache per copilot.

Responsibilities:

- Store an in-memory dict: `{ key: { data, previous_data, error, status, computed_at, version } }`.
- `register(key, compute_fn, invalidated_by, critical, category)`.
- `warm_up()`: compute registered static keys only.
- `get(keys)`: return cached values only after warm-up.
- `invalidate(event)`: recompute keys registered for that event using Wave 1/Wave 2.
- Replace cache entries atomically per key.
- Track whether warm-up has completed.

Concurrency protocol:

```text
On invalidate(event):
  1. Resolve affected static keys from the registry.
  2. For each affected key: key.version += 1.
  3. Record expected_version = key.version for that recomputation.
  4. Mark key as refreshing for Wave 2, or computing for Wave 1.
  5. Compute the new value outside the per-key swap section.
  6. Before storing: if key.version != expected_version, discard the result.
  7. If version matches, atomically replace data, error, status, computed_at, version.
  8. If recomputation fails and the key was invalidated, set data = null and status = invalidated_error.
```

This makes the latest invalidation win. If a user scores and immediately verifies, late score recomputations cannot overwrite newer verify recomputations for overlapping keys such as trajectory, analytics, and conservation.

### 4.2 Invalidation Registry

Backend registry maps mutation events to affected static keys and wave assignment.

Example:

```text
score:
  Wave 1: trajectory, analytics, conservation
  Wave 2: regime-analytics, vol-sharpe, measurement-state
```

Adding a static panel is a registry change, not a new mount-time service call.

### 4.3 Tab State Endpoint

```http
GET /api/{copilot}/tab-state?keys=analytics,fingerprint,vol-sharpe
```

Rules:

- Reads from cache only after warm-up.
- If cache is cold, runs synchronous warm-up once for static keys.
- Returns per-key envelopes.
- Unknown keys return `{ data: null, error: "unknown_key", status: "unknown_key" }`.
- Dynamic keys return `{ data: null, error: "dynamic_key_not_materialized", status: "dynamic" }`.
- Missing registered static keys return `{ data: null, error: "not materialized", status: "missing" }`.
- Computation failures return only the failed key as an error.

### 4.4 Mutation Hooks

Manual hook placement is fragile because mutations are spread across shared SDK and copilot-specific routers. The design uses two enforceable mechanisms:

1. Preferred: an `@invalidates(event)` decorator on mutation handlers.
2. Fallback: middleware that maps known POST paths to mutation events through `MUTATION_PATHS`.

Examples:

```python
@invalidates("learn")
def learn(request: LearnRequest) -> dict[str, Any]:
    ...
```

```python
MUTATION_PATHS = {
    ("POST", "/api/score"): "score",
    ("POST", "/api/learn"): "learn",
    ("POST", "/api/purchasing/verify"): "verify",
    ("POST", "/api/trading/evolution/promote"): "evolution",
    ("POST", "/api/trading/market/refresh"): "market_data_refresh",
    ("POST", "/api/transfer/execute"): "transfer",
}
```

Completeness is enforced by a scanner test:

- Enumerate registered POST routes.
- Flag routes whose handler source contains `scorer.score`, `scorer.learn`, `write_outcome`, `verify`, `promote`, `apply`, `transfer`, `reset`, or `refresh`.
- Require a matching decorator or `MUTATION_PATHS` entry.

### 4.5 TabDataProvider

Frontend React context.

Responsibilities:

- On tab mount, call `GET /api/{copilot}/tab-state?keys=...` for static keys.
- Provide `useTabData(key)`.
- Return `{ data, loading, error, refresh, status, refreshing }`.
- Keep dynamic keys as individual panel fetches.
- Do not call migrated static panel endpoints on mount.

State machine:

| status | data | loading | refreshing | Panel behavior |
|---|---|---:|---:|---|
| ready | current value | false | false | Render normally |
| refreshing | previous value | false | true | Render previous data with subtle refresh indicator |
| missing | null | true | false | Show loading spinner |
| invalidated_error | null | false | false | Show error state |
| dynamic | null | false | false | Panel should use individual endpoint |
| unknown_key | null | false | false | Panel should not exist |

During `refreshing`, `data` contains the previous cached value, not null. Panels should show previous data with a subtle indicator, such as a small spinner or reduced opacity. Exception: if the key was never materialized before, `data` remains null and the panel shows a loading spinner.

`refresh(key)` calls the individual endpoint for manual refresh or a diagnostic materialize endpoint if added later. Manual refresh must not silently diverge from cache state: it either updates local panel state explicitly or re-materializes the backend cache entry.

### 4.6 Warm-Up Strategy

Warm-up computes static keys only. Dynamic keys are not warmed because their parameter is unknown until the user selects an entity.

Warm-up sequence:

1. Backend starts. Cache is empty. No warm-up runs yet.
2. Preseed runs. As the final preseed step, preseed calls `cache.warm_up()` for each running copilot.
3. First tab-state request. If cache is cold and preseed has not run, trigger synchronous warm-up.
4. Warm-up computes static keys only.
5. Warm-up chunks work in batches of five keys and awaits `asyncio.sleep(0)` between batches.

Estimated static warm-up cost at 100 ms per key:

| Copilot | Static keys | Estimated warm-up |
|---|---:|---:|
| Trading | 43 | 4.3 s |
| Purchasing | 39 | 3.9 s |
| DataOps | 24 | 2.4 s |
| S2P | 39 | 3.9 s |
| Total | 145 | 14.5 s |

The 14.5 s total is not acceptable on the first user tab click, so preseed/startup must warm caches after data exists. The first-request warm-up path is a fallback for development and backend restarts. Trading warm-up must complete in <=5 s with preseed data.

### 4.7 Key Categories

STATIC keys:

- No user-selection parameter.
- Same response for all users on the same copilot state.
- Materializable.
- Examples: fingerprint, trajectory, conservation, analytics, vol-sharpe, cohort-status.

DYNAMIC keys:

- Parameterized by runtime user selection.
- Not globally materializable.
- Remain individual panel fetches.
- Examples: `/api/context/ticker/{ticker}`, `/api/context/waste-history/{item}`, `/api/s2p/evidence/audit-trail/{invoice}`, `/api/context/alert/{id}`, `/api/s2p/situation/{decision}`.
- POST endpoints with user-selected request bodies are dynamic unless the registry defines a named default materialization.

Counterfactual rule:

- `/api/trading/score/counterfactual` is a POST that requires `base_factors`, `perturbed_factors`, and `category`.
- The current Trading `CounterfactualCard` auto-runs one fixed default request on mount, so the materialized key is `counterfactual-default`, not generic `counterfactual`.
- `counterfactual-default` uses `category: "trend_following"`, base factors `{ signal_alignment: 0.8, market_regime: 0.7, position_sizing: 0.6, timing_quality: 0.6, risk_reward_actual: 0.7, emotional_indicator: 0.5 }`, and perturbed factors equal to base except `signal_alignment: 0.2`.
- Any future interactive counterfactual with user-selected factors remains dynamic and calls the POST endpoint directly.

DERIVED keys:

- Computed from other cached keys.
- No endpoint call needed.
- Examples: individual category status derived from conservation breakdown, small UI aggregates derived from analytics or trajectory.

The inventory contains these 18 parameterized dynamic endpoint patterns:

- `/api/ae/recommendation/{id}`
- `/api/archetypes/{name}`
- `/api/context/alert/{id}`
- `/api/context/alert/{id}/deps`
- `/api/context/alert/{id}/factors`
- `/api/context/alert/{id}/recurrence`
- `/api/context/bottleneck/{system}`
- `/api/context/cross-graph-insight/{alert}`
- `/api/context/item/{item}/profile`
- `/api/context/process-signals/{system}`
- `/api/context/schema-impact/{system}`
- `/api/context/system/{system}/history`
- `/api/context/ticker/{ticker}`
- `/api/context/waste-history/{item}`
- `/api/s2p/evidence/audit-trail/{invoice}`
- `/api/s2p/situation/{decision}`
- `/api/s2p/suppliers/{id}/heatmap`
- `/api/s2p/suppliers/{id}/history`

### 4.8 Recomputation Budget

Wave 1:

- Runs synchronously after mutation and before response.
- Contains only critical keys the frontend immediately rereads.
- Target: <=300 ms.
- Maximum default size: three keys.

Wave 2:

- Runs after mutation response.
- Contains non-critical below-fold keys.
- Uses `asyncio.create_task`.
- Processes batches of at most three keys.
- Awaits `asyncio.sleep(0)` between batches.
- Serves previous cached value with `status: "refreshing"` until the new value is ready.

Events exceeding the 500 ms all-at-once budget from the current maps:

| Copilot | Event | Keys | Estimated all-at-once |
|---|---|---:|---:|
| Trading | score | 9 | 900 ms |
| Trading | verify | 6 | 600 ms |
| Purchasing | score | 8 | 800 ms |
| Purchasing | verify | 8 | 800 ms |
| DataOps | score | 8 | 800 ms |
| DataOps | learn | 7 | 700 ms |
| DataOps | resolve_alert | 6 | 600 ms |
| DataOps | pipeline_refresh | 6 | 600 ms |
| S2P | score | 9 | 900 ms |
| S2P | learn | 7 | 700 ms |
| S2P | supplier_update | 8 | 800 ms |
| S2P | discovery_refresh | 7 | 700 ms |

### 4.9 Memory Budget

Live size probes against Trading on port 8010 returned:

| Endpoint | Size |
|---|---:|
| `/api/history` | 893845 bytes |
| `/api/context/analytics` | 6258 bytes |
| `/api/self/decisions?limit=50` | 57940 bytes |

Design implications:

- Full `/api/history` is large and frequently invalidated. It is a poor static cache candidate as-is.
- Prefer `history-summary` or a bounded recent-history key rather than caching the entire 894 KB payload.
- Cache static panel summaries, not unbounded raw histories.

Estimated cache budget after excluding full raw history and using bounded summaries:

| Copilot | Static keys | Estimated memory |
|---|---:|---:|
| Trading | 43 | 4 to 6 MB |
| Purchasing | 39 | 3 to 5 MB |
| DataOps | 24 | 2 to 4 MB |
| S2P | 39 | 3 to 5 MB |
| Total | 145 | 12 to 20 MB |

This is acceptable for the local demo and single-user Playwright profile. Production multi-tenant or multi-worker deployment should move the same cache interface to Redis or SQLite and apply per-key size limits.

Hard limits for the in-memory implementation:

- Warn when one key exceeds 1 MB.
- Reject or summarize keys that exceed 2 MB.
- Log total per-copilot cache size after warm-up.
- Keep only bounded histories in tab state.

### 4.10 Derived Key Pattern

Derived keys are client/provider transforms over registered static source keys. They do not have backend registry entries, compute functions, invalidation events, or direct tab-state cache entries.

Hook contract:

```tsx
function useDerivedData<S, D>(
  sourceKey: string,
  transform: (source: S) => D,
): { data: D | null; loading: boolean; refreshing: boolean; error?: string | null } {
  const source = useTabData<S>(sourceKey);
  return {
    data: source.data == null ? null : transform(source.data),
    loading: source.loading,
    refreshing: source.refreshing,
    error: source.error,
  };
}
```

State rules:

- If the source key is `ready`, derived data is computed from current source data.
- If the source key is `refreshing`, derived data is computed from the previous source value and returns `refreshing: true`.
- If the source key is `missing` or null, derived data is null and follows the source loading state.
- If the source key moves from version N to version N+1, React re-renders the derived hook from the new source object. A derived key cannot remain on version N independently because it has no separate cache entry.

Before:

```tsx
function CategoryStatusPanel() {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch("/api/context/conservation-breakdown")
      .then((response) => response.json())
      .then(setData);
  }, []);
  return <StatusView data={data} />;
}
```

After:

```tsx
function CategoryStatusPanel() {
  const { data, loading, refreshing } = useDerivedData(
    "conservation",
    (conservation) => conservation.categories,
  );
  return <StatusView data={data} loading={loading} refreshing={refreshing} />;
}
```

Derived inventory:

| Derived key | Source static key | Transform |
|---|---|---|
| `conservation-breakdown` | `conservation` | Select `categories`, `by_category`, or equivalent per-category conservation fields from the conservation payload. |
| `disruption-annotations` | `trajectory` plus static disruption annotation config | Join trajectory points to static annotation markers by timestamp or bucket. |
| Future category status cards | `analytics` or `conservation` | Select the panel-specific category slice instead of fetching a separate endpoint. |

### 4.11 Typed Key Manifest

The cache key must not be a raw string repeated independently in the backend registry, screen provider, panel component, and Playwright-visible DOM expectation. Raw string drift is silent:

- A panel calls `useTabData("webhook-history")`, but the screen only requests `webhook`.
- The registry computes `cohort-status`, but the frontend asks for `cohort`.
- The backend returns one payload shape while a panel expects another shape for the same key.

Each copilot must therefore own one typed manifest per runtime side.

Backend manifest:

```python
from enum import Enum

class TradingKey(str, Enum):
    TRAJECTORY = "trajectory"
    ANALYTICS = "analytics"
    CONSERVATION = "conservation"
    REGIME_STATUS = "regime-status"
    REGIME_ANALYTICS = "regime-analytics"
    VOL_SHARPE = "vol-sharpe"
    VRP_ATTRIBUTION = "vrp-attribution"
    WEBHOOK_HISTORY = "webhook-history"
    COHORT_STATUS = "cohort-status"

    @property
    def critical(self) -> bool:
        return self in _CRITICAL_KEYS

_CRITICAL_KEYS = {
    TradingKey.TRAJECTORY,
    TradingKey.ANALYTICS,
    TradingKey.CONSERVATION,
}
```

The registry must register enum values, not raw literals:

```python
cache.register(
    key=TradingKey.VOL_SHARPE.value,
    compute_fn=compute_vol_sharpe,
    invalidated_by=["score", "verify"],
    critical=False,
    category="STATIC",
)
```

Frontend manifest:

```tsx
export const TRADING_KEYS = {
  trajectory: "trajectory",
  analytics: "analytics",
  conservation: "conservation",
  regimeStatus: "regime-status",
  regimeAnalytics: "regime-analytics",
  volSharpe: "vol-sharpe",
  vrpAttribution: "vrp-attribution",
  webhookHistory: "webhook-history",
  cohortStatus: "cohort-status",
} as const;

export type TradingKey = typeof TRADING_KEYS[keyof typeof TRADING_KEYS];

export const PERFORMANCE_KEYS: readonly TradingKey[] = [
  TRADING_KEYS.trajectory,
  TRADING_KEYS.analytics,
  TRADING_KEYS.conservation,
  TRADING_KEYS.regimeStatus,
  TRADING_KEYS.regimeAnalytics,
  TRADING_KEYS.cohortStatus,
  TRADING_KEYS.volSharpe,
];
```

Compile-time contract:

- `TabDataProvider` accepts `readonly string[]`, while each copilot screen passes a narrowed `readonly TradingKey[]`.
- `useTabData` and `useDerivedData` call sites use `TRADING_KEYS.<name>`, not raw strings.
- A key typo in a panel or screen is caught by TypeScript when it references a missing manifest property.
- Per-screen arrays live in the manifest so tab ownership is reviewed in one file.

Test-time contract:

- Backend registry coverage test: every `TradingKey` enum value is registered, and no extra cache keys are registered outside the manifest.
- Warm-up contract test: every registered manifest key warms to `status: "ready"` under the backend test fixture.
- Screen completeness test: every direct `useTabData` or `useDerivedData` call in a Trading screen and its directly imported panels uses a key listed in that screen's manifest key list.

Migration rule:

- New migrated static panels must use `TRADING_KEYS.<name>`.
- New screen provider key lists must use the exported per-screen manifest arrays.
- Raw key strings are allowed only inside the manifest, backend enum definitions, tests that intentionally compare manifests, and endpoint maps that bridge cache keys to legacy individual endpoints.

## 5. Invalidation Maps

Keys are listed by wave. Wave 1 is synchronous and critical. Wave 2 is deferred.

### 5.1 Trading

```text
score:
  Wave 1 -> [trajectory, analytics, conservation]
  Wave 2 -> [regime-analytics, vol-sharpe, vrp-attribution, dispersion-follow, measurement-state, cohort-status]

verify:
  Wave 1 -> [trajectory, analytics, conservation]
  Wave 2 -> [measurement-state, regime-analytics, iks]

learn:
  Wave 1 -> [trajectory, conservation]
  Wave 2 -> []

regime_break:
  Wave 1 -> [regime-status]
  Wave 2 -> [regime-analytics]

reset:
  Wave 1 -> [archetypes, measurement-state, market-snapshot]
  Wave 2 -> [analytics, history-summary, trade-metadata, transfer-status, regime, patterns, accuracy, fingerprint, trajectory, conservation, vol-sharpe, vrp-attribution, dispersion-follow, cohort-status, counterfactual-default, evolution]

no invalidation -> [fingerprint, archetypes, correlation-config, regime-history, patterns]
```

### 5.2 Purchasing

```text
score:
  Wave 1 -> [history-summary, context-analytics, conservation]
  Wave 2 -> [trajectory, iks-summary, queue, match-queue, order-metadata]

verify:
  Wave 1 -> [conservation, trajectory, verify-summary]
  Wave 2 -> [history-summary, iks-summary, audit-pack, waste-summary, scorecard]

learn:
  Wave 1 -> [trajectory, conservation]
  Wave 2 -> [trust-weights, trust-insights, cohort-status]

inventory_change:
  Wave 1 -> [items, today-summary]
  Wave 2 -> [par-recommendations, par-status, predictive-par-week, delivery-today, delivery-week]

market_data_refresh:
  Wave 1 -> [commodity-status, weather]
  Wave 2 -> [commodity-indices, spend-summary, payment-timing, payment-summary]

reset:
  Wave 1 -> [spend-summary, weather, commodity-status]
  Wave 2 -> [items, today-summary, history-summary, order-metadata, analytics, evolution, commodity-indices, par-recommendations, par-status, auto-order-status, accuracy, transfer-status]

no invalidation -> [fingerprint, reason-codes, supplier-intelligence-config, transfer-status]
```

### 5.3 DataOps

```text
score:
  Wave 1 -> [conservation, trajectory, ae-recommendation-summary]
  Wave 2 -> [context-alert-summary, context-alert-factors-summary, accuracy-by-category, incident, decisions]

learn:
  Wave 1 -> [conservation, trajectory, ae-impact]
  Wave 2 -> [ae-conservation-history, operational-rules, transfer-status, centroid-history]

resolve_alert:
  Wave 1 -> [alerts, alert-groups, enterprise-health]
  Wave 2 -> [process-timeline, incident, decisions]

pipeline_refresh:
  Wave 1 -> [pipelines, enterprise-health]
  Wave 2 -> [process-timeline, bottleneck-summary, system-history-summary, schema-impact-summary]

discovery_refresh:
  Wave 1 -> [cross-system-discovery, pattern-origin]
  Wave 2 -> [evolution-history, promoted, transfer-status]

reset:
  Wave 1 -> [enterprise-health, pipelines, ae-impact]
  Wave 2 -> [alerts, alert-groups, conservation, ae-conservation-history, trajectory, process-timeline, accuracy, transfer-status, fingerprint, incident, decisions, discovery]

no invalidation -> [fingerprint, static-disruption-annotations, transfer-config]
```

### 5.4 S2P

```text
score:
  Wave 1 -> [preview-queue, preview-conservation, financial-impact]
  Wave 2 -> [situation-summary, counterfactual-summary, evidence-template, audit-trail-summary, factor-analysis, centroid-all]

learn:
  Wave 1 -> [conservation, performance-trajectory, performance-summary]
  Wave 2 -> [financial-impact-trend, auto-approve-stats, auto-approve-expansion-proof, cohort-status]

verify:
  Wave 1 -> [evidence-receipts, evidence-chain-integrity, compliance]
  Wave 2 -> [evidence-audit-trail-summary, governance-compliance-screening, audit-pack]

supplier_update:
  Wave 1 -> [suppliers, suppliers-declining, supplier-rationalization]
  Wave 2 -> [supplier-history-summary, supplier-clustering, supplier-payment-strategy, supplier-heatmap-summary, early-warnings]

discovery_refresh:
  Wave 1 -> [novelty-status, discovery-alerts, discovery-disruptions]
  Wave 2 -> [discovery-extended, process-fusion, process-signals-summary, cross-graph-summary]

reset:
  Wave 1 -> [preview-queue, preview-conservation, novelty-status]
  Wave 2 -> [transfer-status, discovery-disruptions, auto-approve-stats, auto-approve-expansion-proof, control-tower, financial-impact, process-fusion, early-warnings, centroid-all, discovery-extended]

no invalidation -> [transfer-status, static-rule-copy, pvg-config]
```

## 6. Performance Analysis

Dynamic keys do not benefit from global materialization. The real performance gain applies to static panel fetches. Dynamic selected-entity reads remain individual fetches.

Current Trading Performance, static-heavy:

```text
Tab mount: 23 fetches x ~100 ms = 2.3 s for one user
Under 4 concurrent: about 9.2 s queued
Adding 1 static panel: +100 ms per mount per user
```

Batch request design:

```text
Tab mount: 1 request, 23 keys x ~100 ms = 2.3 s for one user
Under 4 concurrent: about 9.2 s queued
Adding 1 static panel: +100 ms per mount per user
```

Materialized state:

```text
Static tab data mount: 1 cache read = <50 ms
Under 4 concurrent static reads: about 200 ms total
Adding 1 static panel: +0 ms per mount
Dynamic selected-entity panel: unchanged individual fetch
Mutation Wave 1: target <=300 ms
Mutation Wave 2: deferred batches of 3 keys
```

Static-only migration scope:

| Copilot | Static keys | Dynamic keys | Derived keys | Static warm mount cost |
|---|---:|---:|---:|---:|
| Trading | 43 | 3 | 1 | <50 ms |
| Purchasing | 39 | 2 | 0 | <50 ms |
| DataOps | 24 | 9 | 1 | <50 ms |
| S2P | 39 | 4 | 1 | <50 ms |

Warm-up is the expensive path, not tab mount. That is why warm-up runs after preseed and is chunked.

Scale constraint verification:

| Constraint | Verification |
|---|---|
| C1 tab mount cache read | Largest static tab request is Trading Performance at 15 registered static groups plus one derived value; all tabs are well below the suspicious 50-key threshold and remain one O(1) cache read by key list. |
| C2 selective recomputation | Reset now has explicit Dashboard-above-fold Wave 1 keys. Other mutation events still recompute only keys registered to that event. |
| C3 cold start | `copilot_sdk/demo/preseed.py` centralizes preseed in `DemoPreseed.preseed_all()`. The warm-up hook belongs immediately after `self.verify(self._result)` succeeds, or in the caller of `run_preseed()` after a successful result is returned. |
| C4 panel registration | Derived keys are excluded from the registry. Registry entries are static keys only: Trading 43, Purchasing 39, DataOps 24, S2P 39. |
| C5 individual endpoints remain | The inventory keeps every current endpoint as the backward-compatible implementation source or dynamic panel fetch. |
| C6 cache consistency | Derived values cannot have a separate stale version because they derive during render from the current source key object. |
| C7-C8 error isolation and no global lock | Per-key envelopes and per-key atomic replacement still apply; derived transforms inherit source errors. |
| C9 event loop budget | Every Wave 1 list is capped at three keys or fewer, including reset. Wave 2 is chunked in batches of three. |
| C10 testability | Testing strategy includes derived invalidation, reset Wave 1 timing, and counterfactual categorization. |

Large invalidation events:

- Normal score/verify/learn/update events are at or below 9 total keys.
- Reset touches all static keys for the copilot, which is intentionally larger than 12. Reset must use the same chunked warm-up protocol as preseed and must return after the three-key Wave 1 set.

Cross-copilot key naming:

- Shared SDK concepts should use canonical key names where payloads are equivalent: `trajectory`, `analytics`, `conservation`, `fingerprint`, `transfer-status`.
- Copilot-specific variants should keep distinct names when the payload differs materially, such as S2P `performance-trajectory` versus shared `/api/trajectory`, or `preview-conservation` versus full conservation status.

## 7. Current State Inventory

The `Category` column marks endpoint groups per row:

- STATIC: materializable tab-state keys.
- DYNAMIC: parameterized selected-entity keys that remain individual fetches.
- DERIVED: should be computed from cached data without another endpoint.

| Copilot | Tab | Screen file | Screen-level fetches | Panel-level fetches | Total | Category | Endpoints called |
|---|---|---|---:|---:|---:|---|---|
| Trading | Dashboard | `apps/trading/frontend/src/screens/DashboardScreen.tsx` | 4 + open tickers | 10 | 14 + open tickers | STATIC: analytics, history-summary, trade-metadata, market-snapshot, transfer-status, archetypes, measurement-state, regime, patterns, accuracy. DYNAMIC: ticker/{ticker}, archetypes/{name}. DERIVED: none. | `/api/context/analytics`, `/api/history`, `/api/context/trade-metadata`, `/api/context/market-snapshot`, `/api/context/ticker/{ticker}`, `/api/transfer/status`, `/api/archetypes?domain=trading`, `/api/archetypes/current`, `/api/archetypes/{name}`, `/api/trading/measurement-state`, `/api/trading/regime/current`, `/api/trading/regime/history?days=90`, `/api/trading/regime/performance`, `/api/context/patterns`, `/api/self/accuracy-by-category?threshold=0.7` |
| Trading | Analysis | `apps/trading/frontend/src/screens/AnalysisScreen.tsx` | 2 | 18 | 20 | STATIC: analytics, fingerprint, trust-analysis, regime, patterns, decisions-summary, vol-sharpe, vrp-attribution, regime-vrp, dispersion-follow, correlation, counterfactual-default, evolution. DYNAMIC: counterfactual-custom POST. DERIVED: none. | `/api/context/analytics`, `/api/fingerprint`, `/api/context/trust-analysis`, `/api/trading/regime/current`, `/api/trading/regime/history?days=90`, `/api/trading/regime/performance`, `/api/context/patterns`, `/api/self/decisions?limit=50`, `/api/trading/analytics/vol-sharpe`, `/api/trading/analytics/vrp-attribution`, `/api/trading/analytics/regime-vrp`, `/api/trading/analytics/dispersion-follow`, `/api/trading/correlation?window=20`, `/api/trading/score/counterfactual` with default `base_factors`, `perturbed_factors`, and `category`, `/api/evolution/variants`, `/api/evolution/history`, `/api/evolution/promoted` |
| Trading | Performance | `apps/trading/frontend/src/screens/PerformanceScreen.tsx` | 3 | 20 | 23 | STATIC: trajectory, analytics, conservation, centroid-history-summary, audit-trail-summary, regime-status, regime-analytics, promotion, rejection-summary, transfer, evolution, execution, webhook-history, cohort-status, vix. DYNAMIC: none. DERIVED: conservation-breakdown. | `/api/trajectory`, `/api/context/analytics`, `/api/conservation/status`, `/api/self/centroid-history?limit=50`, `/api/self/audit-trail?limit=50`, `/api/trading/regime-status`, `/api/trading/regime-analytics`, `/api/context/conservation-breakdown`, `/api/trading/promotion/dashboard`, `/api/trading/evolution/rejection-summary`, `/api/transfer/opportunities`, `/api/transfer/status`, `/api/trading/evolution/log?kind=variant`, `/api/trading/evolution/active`, `/api/trading/evolution/proposals`, `/api/trading/evolution/log?kind=parameter`, `/api/trading/execution/summary`, `/api/trading/webhook/history`, `/api/trading/cohort-status`, `/api/trading/vix-timing` |
| Trading | Journal | `apps/trading/frontend/src/screens/JournalScreen.tsx` | 3 | 0 on mount | 3 | STATIC: journal-trades-summary, analytics-by-category, analytics-by-subcategory. DYNAMIC: none. DERIVED: none. | `/api/trading/journal/trades`, `/api/trading/analytics?group_by=category`, `/api/trading/analytics?group_by=subcategory` |
| Trading | Log Trade | `apps/trading/frontend/src/screens/LogTradeScreen.tsx` | 3 | 0 on mount | 3 | STATIC: market-snapshot, fingerprint, analytics. DYNAMIC: ticker/{ticker} and user-action POST reads remain outside tab-state. DERIVED: none. | `/api/context/market-snapshot`, `/api/fingerprint`, `/api/context/analytics`; user actions call `/api/context/ticker/{ticker}`, `/api/trading/pre-score`, `/api/trading/prescore`, `/api/score`, `/api/learn`, `/api/context/similar`, `/api/context/trade-metadata` |
| Purchasing | Dashboard | `apps/purchasing/frontend/src/screens/DashboardScreen.tsx` | 6 + low-stock items | 10 | 16 + low-stock items | STATIC: items, today-summary, history-summary, order-metadata, analytics, evolution, spend, weather, commodity, par, auto-order, accuracy, transfer. DYNAMIC: waste-history/{item}. DERIVED: none. | `/api/context/items`, `/api/context/today-summary`, `/api/history`, `/api/context/order-metadata`, `/api/context/analytics`, `/api/evolution/variants`, `/api/context/waste-history/{item}`, `/api/purchasing/spend/summary`, `/api/context/weather`, `/api/purchasing/commodity/status`, `/api/purchasing/commodity/indices`, `/api/purchasing/par/recommendations`, `/api/purchasing/par/status`, `/api/purchasing/auto-order/status`, `/api/self/accuracy-by-category`, `/api/transfer/status` |
| Purchasing | Analysis | `apps/purchasing/frontend/src/screens/AnalysisScreen.tsx` | 2 | 6 | 8 | STATIC: analytics, fingerprint, trust-weights, decisions-summary, discovery, menu. DYNAMIC: none. DERIVED: none. | `/api/context/analytics`, `/api/fingerprint`, `/api/purchasing/trust-weights`, `/api/purchasing/trust-weights/expected`, `/api/purchasing/trust-weights/insights`, `/api/self/decisions`, `/api/purchasing/discovery/insights`, `/api/purchasing/discovery/digest`, `/api/purchasing/menu/analysis`, `/api/purchasing/menu/alerts`, `/api/purchasing/menu/summary` |
| Purchasing | Performance | `apps/purchasing/frontend/src/screens/PerformanceScreen.tsx` | 3 | 14 | 17 | STATIC: trajectory, analytics, conservation, chain, weekly-report, economic-model, disruption, payment, audit-pack, multi-unit, alerts, iks, cohort, suppliers-scorecards, centroid-history-summary, waste. DYNAMIC: none. DERIVED: none. | `/api/trajectory`, `/api/context/analytics`, `/api/conservation/status`, `/api/purchasing/chain/status`, `/api/purchasing/report/weekly`, `/api/purchasing/economic/model`, `/api/purchasing/disruption/status`, `/api/purchasing/disruption/history`, `/api/purchasing/payment/timing`, `/api/purchasing/payment/summary`, `/api/purchasing/audit/pack`, `/api/purchasing/multi-unit/dashboard`, `/api/purchasing/alerts`, `/api/purchasing/iks/summary`, `/api/purchasing/cohort-status`, `/api/purchasing/suppliers/scorecards`, `/api/self/centroid-history`, `/api/purchasing/waste/summary`, `/api/purchasing/waste/analysis` |
| Purchasing | Inventory | `apps/purchasing/frontend/src/screens/InventoryScreen.tsx` | 2 + item count | 11 | 13 + item count | STATIC: items, evolution, audit-trail-summary, supplier-intelligence, par-predict-week, events, delivery. DYNAMIC: waste-history/{item}. DERIVED: none. | `/api/context/items`, `/api/evolution/variants`, `/api/context/waste-history/{item}`, `/api/evolution/history`, `/api/evolution/promoted`, `/api/self/audit-trail`, `/api/purchasing/supplier-intelligence`, `/api/purchasing/par/predict-week`, `/api/purchasing/events/plan`, `/api/purchasing/events/history`, `/api/purchasing/delivery/today`, `/api/purchasing/delivery/week`, `/api/purchasing/delivery/consolidation` |
| Purchasing | Order | `apps/purchasing/frontend/src/screens/OrderScreen.tsx` | 6 initial + 2 selected item | 2 | 10 | STATIC: items, today-summary, weather, analytics, fingerprint, reason-codes, queue, match-queue. DYNAMIC: item/{item}/profile, waste-history/{item}. DERIVED: none. | `/api/context/items`, `/api/context/today-summary`, `/api/context/weather`, `/api/context/analytics`, `/api/fingerprint`, `/api/purchasing/verify/reason-codes`, `/api/context/item/{item}/profile`, `/api/context/waste-history/{item}`, `/api/purchasing/queue`, `/api/purchasing/match/queue`; user actions call `/api/score`, `/api/context/similar`, `/api/purchasing/verify`, `/api/context/order-metadata` |
| DataOps | Dashboard | `apps/dataops/frontend/src/screens/DashboardScreen.tsx` | 7 | 6 | 13 | STATIC: pipelines, alerts, alert-groups, conservation, ae-impact, ae-conservation-history, trajectory, enterprise-health, process-timeline, accuracy, transfer. DYNAMIC: none. DERIVED: none. | `/api/context/pipelines`, `/api/context/alerts`, `/api/context/alert-groups`, `/api/conservation/status`, `/api/ae/impact`, `/api/ae/conservation-history`, `/api/trajectory`, `/api/dataops/enterprise-health`, `/api/context/process-timeline`, `/api/self/accuracy-by-category`, `/api/transfer/status` |
| DataOps | Insight | `apps/dataops/frontend/src/screens/InsightScreen.tsx` | 2 | 8 | 10 | STATIC: fingerprint, incident, decisions, process-timeline, acquisitions, profiles, alert-groups, context-decisions. DYNAMIC: bottleneck/{system}, cross-graph-insight/{alert}. DERIVED: none. | `/api/fingerprint`, `/api/ae/incident`, `/api/self/decisions`, `/api/context/bottleneck/{system}`, `/api/context/process-timeline`, `/api/dataops/di/acquisitions`, `/api/di/profiles`, `/api/context/cross-graph-insight/{alert}`, `/api/context/alert-groups`, `/api/context/decisions` |
| DataOps | Triage | `apps/dataops/frontend/src/screens/TriageScreen.tsx` | 6 + conditional 3 | 1 | 10 | STATIC: fingerprint, similar. DYNAMIC: alert/{id}, alert deps/factors/recurrence, recommendation/{id}, process-signals/{system}, system/{system}/history, cross-graph-insight/{alert}. DERIVED: none. | `/api/context/alert/{id}`, `/api/context/alert/{id}/deps`, `/api/context/alert/{id}/factors`, `/api/context/alert/{id}/recurrence`, `/api/ae/recommendation/{id}`, `/api/fingerprint`, `/api/context/process-signals/{system}`, `/api/context/system/{system}/history`, `/api/context/similar`, `/api/context/cross-graph-insight/{alert}` |
| DataOps | Evidence | `apps/dataops/frontend/src/screens/EvidenceScreen.tsx` | 3 | 10 | 13 | STATIC: evolution, pattern-origin, ae-impact, cohort, discovery, audit-trail-summary, sap-purchase-orders, operational-rules, transfer-status. DYNAMIC: schema-impact/{system}. DERIVED: none. | `/api/evolution/variants`, `/api/ae/pattern-origin`, `/api/ae/impact`, `/api/dataops/cohort-status`, `/api/discovery/cross-system`, `/api/evolution/history`, `/api/evolution/promoted`, `/api/self/audit-trail`, `/api/context/sap/purchase-orders`, `/api/context/schema-impact/{system}`, `/api/ae/operational-rules`, `/api/ae/transfer-status` |
| DataOps | Curve | `apps/dataops/frontend/src/screens/CurveScreen.tsx` | 2 | 2 | 4 | STATIC: trajectory, centroid-history-summary. DYNAMIC: none. DERIVED: disruption annotations. | `/api/trajectory`, `/api/context/centroid-history`, `/api/self/centroid-history`, disruption annotation static data |
| S2P | Dashboard | `apps/s2p/frontend/src/screens/DashboardScreen.tsx` | 2 | 11 | 13 | STATIC: preview-queue, preview-conservation, transfer, novelty, discovery-disruptions, auto-approve, control-tower, financial-impact. DYNAMIC: none. DERIVED: none. | `/api/s2p/preview/queue`, `/api/s2p/preview/conservation`, `/api/transfer/status`, `/api/s2p/novelty/status`, `/api/s2p/discovery/disruptions`, `/api/s2p/auto-approve/stats`, `/api/s2p/auto-approve/expansion-proof`, `/api/s2p/control-tower/intents`, `/api/s2p/control-tower/queue`, `/api/s2p/financial-impact` |
| S2P | Insight | `apps/s2p/frontend/src/screens/InsightScreen.tsx` | 1 | 9 | 10 | STATIC: preview-queue, fingerprint, similar, cross-graph-summary, process-fusion, early-warnings, pvg-leakage, process-signals-summary, centroid, discovery-extended. DYNAMIC: none. DERIVED: none. | `/api/s2p/preview/queue`, `/api/s2p/insight/fingerprint`, `/api/s2p/insight/similar`, `/api/s2p/insight/cross-graph`, `/api/s2p/enterprise/process-fusion`, `/api/s2p/suppliers/early-warnings`, `/api/s2p/pvg/leakage`, `/api/s2p/insight/process-signals`, `/api/s2p/centroid/all`, `/api/s2p/discovery/extended` |
| S2P | Performance | `apps/s2p/frontend/src/screens/PerformanceScreen.tsx` | 1 | 5 | 6 | STATIC: conservation, trajectory, what-if, summary, financial-impact-trend, pvg-cycle-time. DYNAMIC: none. DERIVED: none. | `/api/conservation/status`, `/api/s2p/performance/trajectory`, `/api/s2p/performance/what-if`, `/api/s2p/performance/summary`, `/api/s2p/financial-impact/trend`, `/api/s2p/pvg/cycle-time` |
| S2P | Evidence | `apps/s2p/frontend/src/screens/EvidenceScreen.tsx` | 1 | 11 | 12 | STATIC: preview-queue, cohort, factor-analysis, evolution, discovery, rules, compliance, receipts, chain-integrity, audit-pack, governance. DYNAMIC: audit-trail/{invoice}. DERIVED: none. | `/api/s2p/preview/queue`, `/api/s2p/evidence/audit-trail/{invoice}`, `/api/s2p/cohort-status`, `/api/s2p/factors/analysis`, `/api/s2p/evolution/rules`, `/api/s2p/evolution/variants`, `/api/s2p/evolution/shadow-results`, `/api/s2p/evolution/promoted`, `/api/s2p/discovery/alerts`, `/api/s2p/discovery/disruptions`, `/api/s2p/evidence/rules`, `/api/s2p/evidence/compliance`, `/api/s2p/evidence/receipts`, `/api/s2p/evidence/chain-integrity`, `/api/s2p/evidence/audit-pack`, `/api/s2p/governance/compliance-screening` |
| S2P | Suppliers | `apps/s2p/frontend/src/screens/SuppliersScreen.tsx` | 3 | 5 | 8 | STATIC: suppliers, declining, clustering, payment-strategy, rationalization. DYNAMIC: supplier/{id}/history, supplier/{id}/heatmap. DERIVED: none. | `/api/s2p/suppliers`, `/api/s2p/suppliers/declining`, `/api/s2p/suppliers/{id}/history`, `/api/s2p/suppliers/clustering`, `/api/s2p/suppliers/payment-strategy`, `/api/s2p/governance/rationalization`, `/api/s2p/suppliers/{id}/heatmap` |
| S2P | Triage | `apps/s2p/frontend/src/screens/TriageScreen.tsx` | 2 | 7 | 9 | STATIC: preview-queue, conservation, novelty, counterfactual-summary, evidence-template, what-if. DYNAMIC: situation/{decision}. DERIVED: none. | `/api/s2p/preview/queue`, `/api/conservation/status`, `/api/s2p/novelty/status`, `/api/s2p/situation/{decision}`, `/api/s2p/score/counterfactual`, `/api/s2p/evidence/template`, `/api/s2p/performance/what-if`; user actions call `/api/s2p/score`, `/api/learn` |

## 8. Migration Strategy

Phase 1: TabStateCache, warm-up, and tab-state endpoint. Estimate: 1 day.

- Build the cache, registry, and `GET /api/{copilot}/tab-state` endpoint.
- Wire warm-up into preseed finalization, not blind backend startup.
- Preserve all individual endpoints.
- Unit-test cache read, cold start, warm-up, version races, memory budget, and per-key error envelopes.

Phase 2: Mutation registration. Estimate: 0.5 day.

- Add `@invalidates(event)` or `MUTATION_PATHS`.
- Register shared `/api/score` and `/api/learn`, Purchasing verify, and copilot-specific mutation POST routes.
- Add a scanner test that fails if a mutating POST route lacks invalidation metadata.

Phase 3: Migrate Trading static panels to `useTabData`. Estimate: 2 days.

- Start with Performance because it has the most static fetches.
- Then Analysis.
- Then Dashboard.
- Do not migrate dynamic selected-ticker or selected-archetype endpoints into tab state.

Phase 4: Migrate static keys in other copilots. Estimate: 1.5 days.

- Purchasing, DataOps, and S2P in highest-static-fetch-count order.
- Dynamic selected item, alert, invoice, supplier, and system reads stay panel-local.
- Derived values move into provider/client helpers where possible.

Phase 5: Playwright regression and performance spec. Estimate: 0.5 day.

- Full Playwright regression.
- New spec: tab-state endpoint returns static preseed data in under 100 ms after warm-up.
- New spec: Trading score Wave 1 recomputation completes in <=300 ms with preseed data.

Total estimate: about 5.5 days.

## 9. Panel Registration Pattern

Before:

```tsx
function VolSharpeCard() {
  const [data, setData] = useState<VolSharpeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/trading/analytics/vol-sharpe")
      .then((response) => response.json())
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch(() => {
        if (!cancelled) setData(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return <VolSharpeView data={data} loading={loading} />;
}
```

Backend registration:

```python
from app.state.key_manifest import TradingKey

cache.register(
    key=TradingKey.VOL_SHARPE.value,
    compute_fn=compute_vol_sharpe,
    invalidated_by=["score", "verify"],
    critical=False,
    category="STATIC",
)
```

After:

```tsx
import { TRADING_KEYS } from "../state/tradingKeys";

function VolSharpeCard() {
  const { data, loading, error, status, refreshing, refresh } =
    useTabData<VolSharpeResponse>(TRADING_KEYS.volSharpe);

  return (
    <VolSharpeView
      data={data}
      loading={loading}
      error={error}
      status={status}
      refreshing={refreshing}
      onRefresh={refresh}
    />
  );
}
```

Dynamic panel exception:

```tsx
function TickerPanel({ ticker }: { ticker: string }) {
  // Dynamic selected-entity data remains an individual fetch.
  return useTickerProfile(ticker);
}
```

The migrated static panel has no mount fetch, no direct backend URL, and no duplicate request behavior. Dynamic panels keep their parameterized endpoint calls.

Screen provider example:

```tsx
import { PERFORMANCE_KEYS } from "../state/tradingKeys";

function PerformanceScreen() {
  return (
    <TabDataProvider copilot="trading" keys={PERFORMANCE_KEYS}>
      <PerformanceContent />
    </TabDataProvider>
  );
}
```

Raw string keys must not appear in migrated panel calls or screen `keys` arrays. The manifest is the single source of truth for static cache keys.

## 10. Testing Strategy

Unit tests:

- `warm_up()` computes static keys only.
- `get(keys)` returns cached values without calling compute functions after warm-up.
- Cold first `get(keys)` triggers synchronous warm-up once.
- Warm-up completes in <=5 s for Trading with preseed data.
- Warm-up chunks keys in batches of five and yields between batches.
- `invalidate("score")` recomputes only keys registered for `score`.
- A key not registered for the event is not recomputed.
- Trading score Wave 1 completes in <=300 ms with preseed data.
- Wave 2 processes batches of at most three keys and yields between batches.
- During Wave 2, previous data is returned with `status: "refreshing"`.
- One failing key returns an error envelope and leaves other keys untouched.
- Failed recomputation of an invalidated key clears `data` and sets `status: "invalidated_error"`.
- Two overlapping invalidations produce the result of the later mutation, not the earlier one.
- Unknown keys return `unknown_key`.
- Dynamic keys requested from tab-state return `dynamic`.
- Derived keys recompute in React/provider state when the source key is invalidated and re-rendered.
- Derived keys inherit `refreshing` from their source key and use the previous source data while refreshing.
- Duplicate keys are de-duplicated.
- Per-key atomic replacement does not require a global read-blocking lock.
- Cache size warnings fire for keys over 1 MB.
- Reset Wave 1 completes in <=300 ms with preseed data for each copilot.
- No Wave 1 event contains more than three keys unless an explicit benchmark proves it still meets <=300 ms.
- Trading `counterfactual-default` is registered with the fixed mount-time factors from `CounterfactualCard`; arbitrary counterfactual POST bodies are categorized as dynamic.
- Every backend key manifest enum value is registered in the copilot cache, and the registry contains no extra keys outside the manifest.
- Every registered manifest key warms to `status: "ready"` under the backend test fixture.
- Every direct `useTabData` or `useDerivedData` call in a Trading screen and its directly imported panels uses a key present in that screen's exported manifest key list.

Backend route tests:

- `GET /api/{copilot}/tab-state?keys=...` returns cached values.
- Individual endpoints still return existing payloads.
- Decorator or middleware invalidates only after mutation success.
- Failed mutation does not invalidate cache.
- Every endpoint that mutates scorer state is registered in `MUTATION_PATHS` or decorated.
- A T0 scanner compares POST route registrations against handlers that call scorer `score`, `learn`, `write_outcome`, promote, apply, transfer, reset, or refresh.

Frontend tests:

- `TabDataProvider` reads only `tab-state` on static panel mount.
- `useTabData(key)` returns `{ data, loading, error, refresh, status, refreshing }`.
- `refreshing` renders previous data plus an indicator.
- `missing` renders loading.
- `invalidated_error` renders error.
- Migrated static panels render from provider state without direct `fetch`.
- Dynamic panels still call their parameterized individual endpoints.
- Panels migrated from derived endpoints use `useDerivedData(sourceKey, transform)` and do not fetch the derived endpoint on mount.

Playwright:

- Existing UI specs remain behaviorally unchanged.
- Add a performance spec after implementation: full static tab-state data returns in under 100 ms after warm-up with preseed.
- Add a network assertion for one migrated tab: one `tab-state` call and no legacy panel-local mount calls for migrated static keys.

## 11. Risk Assessment

Risk: Cache serves stale data after mutation.

Mitigation: Invalidated keys clear `data` if recomputation fails. Versioned invalidation discards older writes that complete after newer invalidations.

Risk: Mutation latency exceeds 500 ms.

Mitigation: Critical keys recompute in Wave 1 with a <=300 ms target. Non-critical keys are Wave 2 batches of three with event-loop yields.

Risk: Registry duplicates endpoint logic.

Mitigation: Registry entries call shared read service functions. If an endpoint has embedded logic, extract a read helper before registering the key.

Risk: Cold start makes the first tab mount slow.

Mitigation: Preseed finalization warms static caches after data exists. First-request warm-up is fallback only and is chunked.

Risk: Process-local cache is inconsistent across multiple uvicorn workers.

Mitigation: Initial target is the local demo and Playwright. Production multi-worker or multi-tenant deployment moves the same interface to Redis or SQLite.

Risk: Dynamic selected-entity endpoints are accidentally migrated.

Mitigation: Registry category is mandatory. Tab-state rejects dynamic keys with `status: "dynamic"`.

Risk: Memory grows too large.

Mitigation: Use summaries for large frequently invalidated keys, warn above 1 MB per key, reject or summarize above 2 MB, and log per-copilot cache totals.

Risk: Missing mutation hook causes stale cache.

Mitigation: Use decorators or `MUTATION_PATHS`, plus a scanner test that compares POST routes and mutation-looking handlers to invalidation registrations.

## 12. Open Questions

- Closed: key name drift between registry, screen keys, and panel hooks is handled by the typed key manifest and registry/screen contract tests.
- Which static keys should be reduced to summaries before registration because they exceed the 1 MB warning threshold?
- Should Wave 2 use plain `asyncio.create_task` initially, or should it use an explicit bounded task queue from day one?
- Should production use Redis or SQLite first if multi-worker cache consistency becomes required?
- Should `refresh(key)` call the individual endpoint as a local override or call a diagnostic materialize endpoint by default?
- What is the final Playwright budget after implementation: 50 ms target or 100 ms allowance for warmed tab-state reads?
- Should reset Wave 2 run through the same internal method as preseed warm-up so both paths share chunking, memory checks, and telemetry?
- Should copilot-specific names such as `performance-trajectory` be normalized to `trajectory` at the provider boundary, or kept distinct to avoid hiding payload differences?
- Should Purchasing, DataOps, and S2P each own separate manifests, or should shared keys such as `trajectory`, `analytics`, and `conservation` be defined in a common SDK manifest and extended per copilot?
