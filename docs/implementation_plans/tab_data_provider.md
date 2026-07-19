# Tab Data Provider Architecture — v2

**Supersedes:** `tab_data_provider.md` (v1). **Date:** July 2026.
**Why v2 exists:** the v1 architecture was sound; the v1 *implementation* produced ~23 Playwright failures. This
document keeps v1's mechanism (materialized tab state, wave-based recomputation, version races) and adds the
one thing v1 lacked — **enforced contracts between the four layers that reference a key.** Every "Unresolved
Design Question" in v1 §13.8 is answered here and promoted from an appendix into the spec.

---

## 0. What went wrong in v1, and the one idea that fixes it (read first)

### 0.1 The failures were not caching failures

v1 optimized **recomputation** (when to recompute, in what wave, without blocking the event loop). That axis
was well designed and is preserved verbatim. But **every failure in v1 §13 was a *contract* failure, not a
recomputation failure:**

| v1 symptom | Real cause | Layer seam that was unguarded |
|---|---|---|
| §13.1 — 23 PW timeouts, panels render null | key **name** drift across 4 layers | registry ↔ provider ↔ hook ↔ DOM |
| §13.2 — promotion panel empty | compute returns wrong **shape** (`{items:[]}` vs `data.dashboard`) | compute_fn ↔ panel |
| §13.3 — 12 "no console error" specs fail | one wrong-shape payload → React warning → cross-tab contamination | compute_fn ↔ React |
| §13.4 — C1 silently defeated | 13 panels never migrated, still `fetch()` | provider ↔ panel |
| §13.5 — infinite refetch loop | unstable `keys` array identity | screen ↔ provider |

v1 introduced a new indirection chain (**registry key → provider list → `useTabData` → rendered DOM**) and
secured none of the seams between its links. So it traded ~20 HTTP reads for a distributed four-layer
string-matching problem — and, worse, moved every failure from a *loud* fetch error to a *silent* empty render
that only surfaces as a Playwright timeout.

### 0.2 The fix: a key is a **typed schema**, defined once, not a string repeated four times

v1's manifest (v1 §4.11) typed the key **name** but not the key **payload**. That is why a key could be
registered, listed, typed — and still return the wrong shape (§13.2). v2's central change:

> **Each key is defined exactly once, as a schema:** a Pydantic model on the backend and its generated
> TypeScript type on the frontend. The registry requires `compute_fn -> ThatModel`. The panel consumes
> `ThatModel`. Name drift becomes impossible (one symbol, both sides); shape drift becomes a **type error**,
> caught at build time, not a Playwright timeout.

**Contracts-as-tests catch drift *after* it happens. A shared schema makes drift *unrepresentable*.** That is
the difference between v1 and v2.

### 0.3 §0 CONTRACTS — non-negotiable, enforced, and the reason v2 won't regress

Every one of these is a *gate* (a test or a compile error), not a guideline. The v1 §13.8 question each one
closes is noted. **No panel migrates until its key satisfies C-A and C-B.**

| # | Contract | Enforced by | Closes |
|---|---|---|---|
| **C-A** | A key exists in **one** place: a `KeySpec` with `{name, schema, compute_fn, invalidated_by, wave, critical, category}`. No raw key string anywhere except inside the KeySpec table. | `grep` gate (T0) + TS `as const` narrowing | 13.1, 13.8-Q1 |
| **C-B** | `compute_fn` returns an instance of the key's `schema` (validated), and the frontend consumes the **generated** type of that schema. | Pydantic validation at register + generated `.d.ts` + build | 13.2, 13.8-Q1 |
| **C-C** | `compute_fn` **calls exactly one existing read service function** and returns its result unmodified (a *projection* is allowed only via a declared, tested selector). No inline aggregation/queries in the registry. | output-equivalence test vs the legacy endpoint | 13.2, 13.8-Q2 |
| **C-D** | A component inside a `TabDataProvider` **must not** call `fetch`/`apiGet`/`apiPost` for a URL that maps to a **STATIC** key. | AST scanner test (T0) | 13.4, 13.8-Q4 |
| **C-E** | The provider and every migrated panel **never** emit `console.error`; recoverable states use `console.debug`. | console-purity Playwright gate + lint rule | 13.3, 13.8-Q3 |
| **C-F** | Screens pass **only** stable, module-level key arrays from the manifest; inline array literals are forbidden. | ESLint rule + provider identity assertion | 13.5 |
| **C-G** | Every "refreshing" and "invalidated_error" state has an explicit end-to-end Playwright spec. | PW specs (see §10.4) | 13.6, 13.8-Q5 |
| **C-H** | **Exactly one** warm-up trigger owns correctness: preseed finalization. Startup warm-up is removed; cold-first-request is a dev-only fallback that never overwrites newer data. | version protocol + removed startup hook | 13.7, 13.8-Q6 |
| **C-I** | A key's schema and `KeySpec` live in a **shared SDK manifest** when the key is shared (`trajectory`, `analytics`, `conservation`, `cohort-status`), and per-copilot only for copilot-specific keys. | manifest layering (§4.11) | 13.8-Q7 |

**If a coding session internalizes one thing:** *drift is the enemy, and the schema is the weapon.* Build the
schema layer (§4.0) **before** migrating a single panel. v1 migrated panels first and discovered the contracts
by failing Playwright 23 times.

---

## 1. Executive Summary

Trading, Purchasing, DataOps, and S2P tabs mount many independent auto-fetching panels; the worst Trading tabs
issue ~20–23 reads on a single tab transition. Request-batching would cut HTTP round trips but not the compute
model (one batch of 23 keys still computes 23 service functions on the hot path).

v2 keeps v1's answer — **materialized tab state**: tab data is server-side state, recomputed *after mutations*
and served to tabs as a cache read — and adds the **schema-contract spine** (§0.2) that v1 lacked.

```text
MUTATION: score / verify / learn / reset / transfer / promote
  -> backend recomputes only affected STATIC keys (by invalidation registry)
  -> each recompute validates against the key's schema before it is stored   [v2: C-B]
  -> backend atomically replaces those cached entries (version-guarded)
  -> mutation returns after Wave 1 critical recomputation (<=300 ms)
  -> Wave 2 deferred keys refresh without blocking tab reads

TAB MOUNT
  -> frontend calls GET /api/{copilot}/tab-state?keys=a,b,c    (keys from the manifest, not literals) [C-A/C-F]
  -> backend reads cached static entries only (no service functions run on warm mount)
  -> tab renders in <50 ms for materialized static data
```

Batching keeps computation on the hot path; materialization moves static, read-heavy computation to the cold
path. Dynamic keys (parameterized by a selected ticker/invoice/alert/supplier/item/system) are **not**
materialized globally and remain individual fetches keyed by user selection.

**What is unchanged from v1 (sound, preserved):** the version-race protocol (§4.1), Wave 1/Wave 2 budget (§4.8),
per-key error isolation, memory bounds (§4.9), key categories STATIC/DYNAMIC/DERIVED (§4.7), invalidation maps
(§5), counterfactual-default rule (§4.7).
**What is new in v2:** the schema spine (§2.5), the KeySpec single-definition (§4.11), the four enforcement
gates (§10.5–10.8), the corrected warm-up ownership (§4.6), and §13 recast as *resolved*.

---

## 2. Architecture

The backend owns a per-copilot `TabStateCache`. Its registry is a table of **KeySpecs** — the single definition
of a key (v2; replaces v1's loose `{compute, invalidated_by, critical}` dict, which typed nothing).

```python
# v2: one KeySpec IS the key. Name, schema, compute, invalidation, wave, criticality — together, once.
@dataclass(frozen=True)
class KeySpec:
    name: str                       # e.g. "vol-sharpe" — the ONLY place this literal appears (C-A)
    schema: type[BaseModel]         # the Pydantic model compute_fn must return (C-B)
    compute_fn: Callable[..., BaseModel]
    service_fn: Callable            # the ONE existing read service compute_fn wraps (C-C)
    invalidated_by: tuple[str, ...] # mutation events
    wave: Literal[1, 2]             # Wave 1 = critical/synchronous, Wave 2 = deferred
    category: Literal["STATIC", "DYNAMIC", "DERIVED"]

    @property
    def critical(self) -> bool:
        return self.wave == 1
```

```python
# registration is data, not code — no lambdas, no inline logic (C-C)
VOL_SHARPE = KeySpec(
    name="vol-sharpe",
    schema=VolSharpeResponse,                 # <- the contract
    compute_fn=lambda: VolSharpeResponse.model_validate(get_vol_sharpe()),  # validate-on-produce (C-B)
    service_fn=get_vol_sharpe,                 # the legacy /api/trading/analytics/vol-sharpe handler's service
    invalidated_by=("score", "verify"),
    wave=2,
    category="STATIC",
)
```

The tab-state endpoint is a **read facade** — it never dispatches to analytics/scorer/graph/panel services
after warm-up:

```http
GET /api/{copilot}/tab-state?keys=analytics,fingerprint,vol-sharpe
```

```json
{
  "analytics":   { "data": { }, "error": null, "status": "ready" },
  "fingerprint": { "data": { }, "error": null, "status": "ready" },
  "vol-sharpe":  { "data": null, "error": "not materialized", "status": "missing" }
}
```

**Rules (unchanged from v1, still correct):** cold cache triggers a one-time synchronous warm-up of STATIC keys
only; STATIC keys are globally materializable per copilot; DYNAMIC parameterized keys stay individual calls;
DERIVED keys are computed from cached STATIC values in the provider without another backend read.

**Mutation invalidation** uses a registered decorator or a `MUTATION_PATHS` middleware table (v1 §4.4,
preserved) — never hand-written one-off hooks. Completeness is enforced by the scanner test (§10.3). This is
correct in v1 and unchanged.

---

## 2.5 The schema layer (NEW — the spine of v2; build this FIRST despite the section number)

**This section is the reason v2 exists. It is Phase 0 (P0 in §6) and it precedes all migration — do it before §3/§4 work despite coming after them in the numbering.**

### 2.5.1 One schema per key, two generated faces

```
backend/app/state/schemas/trading.py     # Pydantic models — the source of truth
      VolSharpeResponse(BaseModel): sharpe: float; adjusted_sharpe: float; inflation: float; ...
              |
              |  (codegen: pydantic -> json-schema -> typescript, run in CI)
              v
frontend/src/state/schemas/trading.ts     # GENERATED — never hand-edited
      export interface VolSharpeResponse { sharpe: number; adjustedSharpe: number; inflation: number; ... }
```

- The Pydantic model is authored **once**, next to the KeySpec.
- The TypeScript type is **generated** (e.g. `datamodel-code-generator` / `pydantic2ts`) in CI and committed;
  a drifted checkout fails the "generated types are current" test. Hand-editing the `.ts` is forbidden.
- `useTabData<VolSharpeResponse>(TRADING_KEYS.volSharpe)` is now type-checked against the *same* shape the
  backend validates. **Shape drift (§13.2) cannot compile.**

### 2.5.2 Validate-on-produce, not validate-on-read

`compute_fn` returns a **validated model instance** (`Model.model_validate(service_output)`). If the service
returns the wrong shape, the failure happens **at recompute time, in one key, with a clear error** — it becomes
that key's `invalidated_error` envelope (C7), never a silently-wrong payload that reaches React and warns across
12 specs (§13.3). The cache stores `model.model_dump()`; the envelope's `data` is therefore *always*
schema-valid or *explicitly* an error. There is no third state.

### 2.5.3 The projection rule (this is what makes C-C enforceable)

A `compute_fn` may do exactly one of:
1. **Wrap:** `Model.model_validate(service_fn(...))` — return the service result unchanged.
2. **Project:** `Model.model_validate(SELECTORS[name](service_fn(...)))` — apply a **named, tested** selector
   (pure function, its own unit test) that narrows a larger payload to this key's schema.

It may **not** aggregate multiple endpoints, run its own query, or transform inline. The five v1 compute
functions that each grew their own bugs (§13.2: `history_summary`, `accuracy`, `archetypes`,
`counterfactual_default`, `evolution`) were all rule-3 ("arbitrary logic") — which v2 forbids. If a panel needs
data from three endpoints, that is either three keys the panel reads, or one **new service function** (tested
where service functions are tested), never an inline registry aggregation.

### 2.5.4 The output-equivalence test (C-C, the teeth)

For every STATIC key with a legacy individual endpoint, a generated test asserts:

```
compute_fn()  ==  Model.model_validate( GET /legacy/endpoint )
```

So a compute function *cannot* diverge from the endpoint it replaces without failing a test. This is what turns
"registry entries should call shared read service functions" (a v1 *hope*, v1 §11) into a v1-§13.2-proof
**guarantee**. Keys with no 1:1 legacy endpoint (genuinely new summaries) instead assert against a golden
fixture.

---

## 3. Design Constraints (v1 C1–C10, preserved; v2 additions marked)

C1. **Tab mount = cache read.** Zero service-function calls on warm mount. O(1) regardless of static panel
count. Target <50 ms for full materialized static tab data.
C2. **Mutation = selective recomputation.** After `POST /api/score`, recompute only keys that depend on score
(trajectory, analytics, conservation). Do not recompute fingerprint, archetypes, or regime history.
C3. **Cold start.** First request after startup finds an empty cache → one-time synchronous warm-up of STATIC
keys. **Preferred path: preseed warms the cache after data exists (C-H; see §4.6).**
C4. **Declarative registration.** Adding a materialized panel = one **KeySpec** (v2: which now includes the
schema). No new mount-time service call.
C5. **Individual endpoints remain.** The cache is a performance facade. `/api/fingerprint` etc. stay for
back-compat, tests, direct consumers, dynamic reads, and manual refresh.
C6. **Cache consistency.** A key never serves as fresh after a mutation if recomputation failed → it becomes
`{data:null, error:..., status:"invalidated_error"}` (may keep `previous_data` for diagnostics; `data` must not
be stale).
C7. **Per-key error isolation.** One key's failure returns its own error envelope; other keys unaffected.
C8. **No global lock.** Mutations don't block reads. Cache updates are atomic per key; reads copy current
entries without waiting on unrelated recomputes.
C9. **Single-threaded uvicorn safe.** Post-mutation recompute must not block the loop >500 ms. Wave 1 (critical,
synchronous, <=300 ms, <=3 keys) before the response; Wave 2 (`asyncio.create_task`, batches of <=3, `sleep(0)`
between) after.
C10. **Testable.** Warm-up, invalidation, selective recompute, cold start, version races, Wave 1 timing, Wave 2
refresh state, memory bounds, mutation-path registration, error isolation — all unit-testable without a full
backend.
**C11 (v2). Contract-safe.** No key may be migrated until C-A..C-C hold for it (schema exists, single
definition, output-equivalent compute). The four enforcement gates (§10.5–10.8) run in CI.
**C12 (v2). Silent-failure-free.** Every failure mode surfaces as a *typed* error envelope or a *compile* error
— never an empty render. (This is the constraint v1 violated 23 times.)

---

## 4. Components

*(v1 §4.1–4.10 are preserved; only the deltas that fix v1 §13 are restated. Unchanged mechanics are cited, not
repeated.)*

### 4.1 TabStateCache — concurrency protocol (UNCHANGED from v1; it was correct)

In-memory `{ key: {data, previous_data, error, status, computed_at, version} }`; `register / warm_up / get /
invalidate`; atomic per-key replacement. The **version-race protocol is preserved verbatim** — bump
`key.version`, record `expected_version`, compute outside the swap, discard if `version != expected_version`,
else atomically replace. Latest invalidation wins; a late `score` recompute cannot overwrite a newer `verify`
recompute on overlapping keys. **This is the strongest part of v1 and is not touched.**

*v2 delta:* step 5 ("compute the new value") now includes `Model.model_validate(...)` (C-B); a validation
failure routes to step 8 (`invalidated_error`) exactly like a compute failure.

### 4.5 TabDataProvider — state machine (UNCHANGED shape; v2 tightens console + identity)

`useTabData(key) -> { data, loading, error, refresh, status, refreshing }`. State table (v1 §4.5) preserved:
`ready / refreshing / missing / invalidated_error / dynamic / unknown_key`. During `refreshing`, `data` is the
**previous** value (not null) unless the key was never materialized.

*v2 deltas (the §13.3 / §13.5 fixes):*
- **Console purity (C-E):** the provider catches all recoverable conditions to `console.debug`. It emits
  `console.error` **never** — not on warm-up, stale read, or fetch failure. Lint rule bans `console.error` in
  `provider/` and migrated `panels/`. (This is what stops one bad payload from failing 12 "no console error"
  specs.)
- **Stable keys (C-F):** `TabDataProvider` accepts `readonly TradingKey[]` and asserts a stable identity in
  dev (warns if the `keys` array identity changes between renders without contents changing). Screens pass
  module-level constants (`PERFORMANCE_KEYS`), never inline literals. An ESLint rule flags inline array
  literals in the `keys=` prop. (Fixes the §13.5 infinite-refetch loop at the source, not with
  `JSON.stringify` memoization as a band-aid.)

### 4.6 Warm-up ownership (CHANGED — this fixes v1 §13.7)

v1 had **two** warm-up triggers (startup fallback + preseed) with no defined interaction, so startup could warm
an empty cache and preseed's real data might never replace it. v2 makes ownership singular:

1. **Backend startup does NOT warm the cache.** (The v1 startup warm-up hook is removed.)
2. **Preseed finalization is the sole correctness-bearing warm-up** — its last step calls `cache.warm_up()` per
   running copilot, after preseed data exists.
3. **Cold-first-request warm-up is a dev/restart fallback only**, and it is **version-guarded**: it computes a
   key only if that key has no `computed_at` (never overwrites a preseed-populated entry). So a fallback warm-up
   racing a preseed warm-up cannot clobber real data with empty data.

Warm-up computes STATIC keys only, in batches of five with `sleep(0)` between. Trading must warm in <=5 s with
preseed data. (First-request cold warm-up of all 145 keys ~14.5 s is dev-only and acceptable there.)

### 4.7 Key categories & the counterfactual rule (UNCHANGED from v1)

STATIC (no user-selection param, globally materializable) / DYNAMIC (parameterized by selection, stays
individual) / DERIVED (computed from cached STATIC in the provider). The 18 dynamic parameterized endpoint
patterns and the `counterfactual-default` fixed-factor rule (v1 §4.7) are preserved exactly. **Do not migrate
dynamic selected-entity endpoints into tab state** (registry `category` is mandatory; tab-state rejects DYNAMIC
with `status:"dynamic"`).

### 4.9 Memory budget (UNCHANGED from v1)

Full `/api/history` (~894 KB) is a poor static candidate → cache `history-summary`, not raw history. Per-copilot
budgets 2–6 MB, total 12–20 MB (local/single-user). Warn >1 MB/key, reject-or-summarize >2 MB, log per-copilot
totals. Production multi-worker/multi-tenant moves the same interface to Redis/SQLite.

### 4.11 KeySpec manifest layering (REPLACES v1 §4.11; this is C-A + C-I)

**One literal, one place.** The key name string `"vol-sharpe"` appears **only** inside its `KeySpec`. Backend
and frontend both import from the manifest; a raw literal anywhere else is a grep-gate failure.

```
backend/app/state/manifest/
    shared_sdk.py     # KeySpecs for keys shared across copilots: trajectory, analytics,
                      # conservation, cohort-status, fingerprint   (C-I: define once)
    trading.py        # Trading-specific KeySpecs; imports+extends shared_sdk
    purchasing.py  dataops.py  s2p.py

frontend/src/state/manifest/
    shared.ts         # GENERATED key-name consts + per-screen arrays for shared keys
    trading.ts  ...   # GENERATED; TRADING_KEYS, PERFORMANCE_KEYS, ANALYSIS_KEYS, DASHBOARD_KEYS
```

Compile-time contract: `TabDataProvider` takes `readonly string[]`; screens pass a narrowed
`readonly TradingKey[]`; `useTabData`/`useDerivedData` call `TRADING_KEYS.<name>`; a typo references a missing
manifest property → TS error.

Test-time contract (the §10.1 registry/screen tests) closes the loop: registry ⊇ manifest, manifest ⊇ every
screen's key list, every screen list ⊇ its panels' `useTabData` calls. **v2 adds the fourth link C-B:** every
key's `compute_fn` output validates against its schema, and the generated TS type is current.

---

## 5. Invalidation Maps (UNCHANGED from v1 — preserved verbatim)

The per-copilot Wave 1 / Wave 2 invalidation maps for Trading, Purchasing, DataOps, and S2P (v1 §5.1–5.4) are
correct and carry forward unchanged. Wave 1 = critical/synchronous (≤3 keys, ≤300 ms); Wave 2 = deferred,
below-fold, batched. The `reset` event's large Wave 2 fan-out is expected (it re-materializes the whole tab set
off the hot path). See v1 §5 for the full key lists; v2 changes none of them.

*v2 note:* the "events exceeding 500 ms all-at-once" table (v1 §4.8 — Trading score 9 keys / 900 ms, etc.) is
exactly why Wave 1 caps at 3 keys and Wave 2 defers the rest. No change.

---

## 6. Migration Strategy (v2 — reordered: schema layer FIRST)

The critical change from v1: **build and enforce the contract layer before migrating any panel.** v1 migrated
~30 panels, then discovered the missing contracts by failing Playwright 23 times and back-filling. v2 front-loads
the contracts so migration is mechanical and failures are compile-time.

| Phase | Work | Est. | Gate to exit the phase |
|---|---|---:|---|
| **P0 (NEW) — Schema spine** | Author Pydantic schemas for all STATIC keys next to their KeySpecs; wire pydantic→TS codegen into CI; stand up the four enforcement gates (§10.5–10.8) even before keys exist. | 1.5d | codegen runs in CI; empty gates green |
| **P1 — Cache + endpoint** | `TabStateCache`, KeySpec registry, `GET /tab-state`. Preseed-only warm-up (C-H; **remove startup warm-up**). Unit-test cache read, cold start, version races, memory, error envelopes. | 1d | §10.1 cache unit tests green |
| **P2 — Mutation registration** | `@invalidates` / `MUTATION_PATHS` + the scanner test (§10.3). | 0.5d | scanner test fails on an unhooked mutating route |
| **P3 — Trading migration** | Migrate Trading STATIC panels to `useTabData`, **one key at a time**, each behind C-A..C-C. Order: Performance → Analysis → Dashboard. Each panel: (a) schema exists, (b) compute wraps one service fn, (c) output-equivalence test passes, (d) panel reads the generated type. | 2d | per-key: all four gates green; **no panel merges red** |
| **P4 — Other copilots** | Purchasing, DataOps, S2P by static-fetch count. Shared keys use the SDK manifest (C-I); only copilot-specific keys are new. | 1.5d | same per-key gates |
| **P5 — Regression + perf + the missing E2E specs** | Full Playwright regression; the refreshing/invalidated_error E2E specs (C-G, §10.4); perf specs (<100 ms warm read; ≤300 ms Wave 1). | 1d | all green incl. the v1-§13.6 gaps |

Total ≈ **7.5 days** (v1 was 5.5d and produced 23 failures + a rework tail; the extra ~2 days is the schema
spine and the four gates, which is *less* than the v1 debugging tail cost).

**Hard migration rule:** *a panel is migrated only when its key is green on C-A, C-B, C-C, C-D.* No "migrate 30,
fix later." The gates make "later" impossible to skip.

---

## 7. Testing Strategy (v1 tests preserved; v2 adds the four gates + the missing E2E)

### 7.1–7.3 Unit / route / frontend tests — UNCHANGED from v1 §10

All v1 unit tests (warm-up, selective invalidation, Wave 1 timing, Wave 2 batching, version races, error
isolation, memory warnings, counterfactual-default, registry/screen coverage) and route/frontend tests carry
forward. They were correct; they were just insufficient. v2 adds four gates and the missing E2E specs.

### 7.4 The missing end-to-end specs (C-G — closes v1 §13.6)

- **Refreshing:** mutate → immediately GET tab-state → assert a Wave 2 key returns `status:"refreshing"` with
  **previous** data (not null); assert the panel shows previous data + the refresh indicator in the DOM.
- **Invalidated_error:** force a compute failure on an invalidated key → assert `status:"invalidated_error"`,
  `data:null`, panel renders the error state, and **no other key on the tab is affected** (C7).

### 7.5 GATE 1 — Output-equivalence (C-C; closes v1 §13.2)

Generated per STATIC key with a legacy endpoint: `assert compute_fn() == Model.model_validate(GET legacy)`.
A compute function cannot diverge from the endpoint it replaces. Keys with no legacy 1:1 assert against a golden
fixture. **This is the gate that would have caught the empty promotion panel before it shipped.**

### 7.6 GATE 2 — Schema currency (C-B; closes v1 §13.1/§13.2)

CI regenerates the TS types from the Pydantic schemas and fails if the committed `.ts` differs. Guarantees the
frontend type and the backend validator are the same shape. Hand-edited generated files fail here.

### 7.7 GATE 3 — No-bypass-fetch scanner (C-D; closes v1 §13.4)

An AST/static scan: for every component rendered inside a `TabDataProvider`, assert it contains **no**
`fetch`/`apiGet`/`apiPost` call whose URL maps to a **STATIC** key. Flags the "panel is inside the provider but
still fetches independently" failure that silently defeated C1 for 13 v1 panels. (DYNAMIC-key fetches are
allowed and ignored.)

### 7.8 GATE 4 — Console purity (C-E; closes v1 §13.3)

A Playwright helper asserts zero `console.error` across every migrated tab, **and** a lint rule bans
`console.error` in `provider/` and migrated `panels/`. React warnings are treated as failures (they indicate a
real shape bug, e.g. duplicate keys) — but because C-B/C-C now prevent wrong-shape payloads upstream, this gate
stops *catching* the same bug 12 times and starts *preventing* it once.

---

## 8. Risks (v1 risks preserved; v2 status)

All v1 §11 risks and mitigations carry forward. v2 upgrades three from "mitigated by hope" to "enforced":

| Risk | v1 status | v2 status |
|---|---|---|
| Registry duplicates endpoint logic | "extract a read helper" (unenforced) | **C-C output-equivalence gate** — enforced |
| Key name/shape drift | typed name only | **C-A single-definition + C-B schema currency** — drift won't compile |
| Panel bypasses the provider | undetectable | **C-D scanner gate** — detected in CI |
| Console-error fragility | undefined contract | **C-E purity gate + lint** — enforced |
| Cold start / double warm-up race | two triggers, undefined | **C-H single owner + version-guarded fallback** |

Unchanged, still-open operational risks: multi-worker cache consistency (→ Redis/SQLite when needed);
per-key memory ceilings (warn 1 MB / cap 2 MB).

---

## 9. Resolved Design Questions (was v1 §13.8 — every one is now answered in the spec)

| v1 §13.8 question | v2 answer | Where |
|---|---|---|
| 1. Manifest defines response **types** per key? | **Yes.** Schema per key, single definition, generated TS. | §0.2, §4.0, §4.11 (C-A/C-B) |
| 2. Compute fn = exactly one service fn, equivalence-tested? | **Yes.** Wrap-or-projection only; output-equivalence gate. | §2.5.3–2.5.4, §7.5 (C-C) |
| 3. Provider/panels never emit `console.error`? | **Yes.** Purity gate + lint. | §4.5, §7.8 (C-E) |
| 4. Build-time check: no `fetch()` for a STATIC key inside a provider? | **Yes.** AST scanner gate. | §7.7 (C-D) |
| 5. E2E spec for `refreshing`? | **Yes.** Plus `invalidated_error`. | §7.4 (C-G) |
| 6. Remove startup warm-up? | **Yes.** Preseed-only owner; version-guarded dev fallback. | §4.6 (C-H) |
| 7. Shared manifest vs per-copilot? | **Shared SDK base + per-copilot extensions.** | §4.11 (C-I) |

**v1 §13 (the implementation-issues synopsis) is therefore retired as an open list** — its seven failure
categories map 1:1 onto the C-A..C-I contracts above, each now enforced by a gate.

---

## 10. What a coding session must do differently this time (the one-paragraph handoff)

**Build §2.5 (the schema spine) and the four gates in §7.5–7.8 BEFORE migrating a single panel.** Then migrate
one key at a time, and never merge a key that is red on C-A (single definition), C-B (schema currency), C-C
(output-equivalence), or C-D (no bypass fetch). v1 failed because it moved computation off the hot path but left
four string-matched seams unguarded, so every mismatch became a silent empty render and a Playwright timeout.
v2's rule is simple: **a key is a typed schema defined once — make the drift a compile error, not a test you
hope someone runs.**

---

*Tab Data Provider Architecture — v2. Supersedes v1. The mechanism is v1's; the contracts are new.*
