# Tab Data Provider Architecture — v4.1

**Supersedes:** `tab_data_provider_v3.md` (v3/v3.1) and the v4 draft. **Date:** July 2026.

**Why v4 exists:** v3.1's transparent fetch proxy (frontend apiGet cache + inflight coalescing) was
architecturally sound but produced 4 PW failures on implementation. The failure reveals a deeper constraint that
v1, v2, and v3 all missed: **Playwright observes the browser network layer. Any optimization that reduces,
reorders, eliminates, or caches network calls is invisible to panels but visible to PW.** This constraint was
not in any prior version's design, and every client-side implementation hit it.

**What v4.1 adds:** v4 correctly assembled the failure history and the constraint, then stopped at "candidate
solutions — not yet decided." v4.1 **makes the decision** (§2): the §0.3 constraint eliminates every client-side
candidate, leaving `@cached_static` (backend endpoint caching) as the fix, with `--workers=1` as a zero-cost
reserve. The recommendation is grounded in a latency model (§2.1) that shows the "doesn't reduce request count"
objection is immaterial — the cost was recompute-per-request, not request count. **Net: ~1.25 days, 1 utility +
43 one-line annotations, zero panel changes, zero PW-spec changes.**

---

## 0. Complete failure history — what was tried, what broke, and why

### 0.0 The original problem

Trading tabs issue 20-23 independent HTTP requests on mount. Each panel calls `apiGet("/api/endpoint")` via `useEffect`. Under 4 parallel Playwright workers, 4 browsers hit the single-threaded uvicorn backend simultaneously. 4 × 23 = 92 concurrent requests. Response times degrade to 15-30 seconds. 2-3 PW specs timeout intermittently.

### 0.1 Attempt timeline

```
Baseline:                         239 passed, 2-3 flaky timeout. 7 minutes.
v1 (panel rewrite → useTabData):  23 failed. Contract drift between 4 layers.
v1 + manifest:                     5 failed. Compute shape mismatch.
v1 + manifest + fixes:            12 failed. React duplicate key from archetypes.
v2 (typed schemas + gates):      101 failed. Strict schemas reject valid data.
v3 revert to baseline:           239 passed, 1 flaky. Back to known-good.
v3 P2 (apiGet cache + coalesce):   4 failed. PW waitForResponse timeout.
```

### 0.2 The three failed strategies and their root causes

**Strategy A: Rewrite panels to consume a new abstraction (v1, v2)**

Replace `useEffect → apiGet → setState` with `useTabData(key)` backed by a React context that reads from a backend cache.

Result: 23-101 failures.

Why it fails: The rewrite introduces a 4-layer indirection chain (backend registry → frontend manifest → React context → panel destructuring). Each layer uses string keys and data shapes that can drift independently. No amount of typed contracts (v2) prevents the aggregate failure because:
- Codex writes code against source, not against the live DOM
- 43 schemas × 43 compute functions × 43 panel destructurings = 129 potential drift points
- Failures are silent (panel renders null) and only surface as PW timeouts
- The full integration can only be tested via PW, which only runs on the user's machine
- Batch migration (38 panels in one session) is untestable without PW

**Strategy B: Transparent frontend cache/proxy (v3, v3.1)**

Leave panels unchanged. Intercept `apiGet` calls with a frontend JS-level cache. If cached and fresh, return from cache without making a network call. Coalesce concurrent identical GETs.

Result: 4 failures.

Why it fails: PW specs use `page.waitForResponse(url => url.includes("/api/score"))` to detect when an API call completes. The JS-level cache serves responses from memory — the browser never makes the `fetch()` call — so `waitForResponse` never fires. The test waits forever and times out.

This is a fundamental constraint, not a fixable bug:
- `waitForResponse` listens on the browser's network layer
- A JS-level cache bypasses the network layer entirely
- The panel renders correctly (it received data from the cache)
- But PW can't observe that the panel received data because there was no network event

The workaround (disable cache in PW mode via `window.__PW_DISABLE_CACHE__`) defeats the purpose: PW tests the uncached path, so the cached path is never tested.

**Strategy C: Backend endpoint caching (proposed, not implemented)**

Leave panels unchanged. Leave apiGet unchanged. Add a `@cached_static` decorator to each of the 43 STATIC endpoints that reads from TabStateCache before calling the handler.

Why it would partially work: Network calls still happen (PW sees them), responses are just faster (cache read vs recompute). 23 requests × 5ms = 115ms instead of 2.3s.

Why it's still a hack: It doesn't reduce the number of HTTP requests. Under 4 workers, 92 concurrent requests still hit the backend. Each is faster (cache read), but the TCP/HTTP overhead is unchanged. With enough panels (50+), even cached responses queue behind each other in the single-threaded event loop's accept/parse/serialize cycle.

### 0.3 The constraint no version addressed

**The PW observation constraint:** Any optimization that changes when or whether a network call happens is observable by Playwright. PW specs that use `waitForResponse`, `page.route`, `page.on('response')`, or response interception will break if the optimization eliminates or reorders the call.

This constraint applies to:
- Frontend JS-level caching (eliminates calls)
- Frontend request batching (reorders/combines calls)
- Service workers (intercepts calls)
- Any client-side optimization that touches the network layer

It does NOT apply to:
- Backend-side optimizations (requests still happen, responses are faster)
- Backend request batching (one request in, one response out — PW sees the one request)
- Database/compute caching behind endpoints (transparent to the network)
- Reducing the number of panels (fewer calls, but each one still happens)

### 0.4 The question this document exists to answer

Given:
- 20-23 independent panel fetches per tab mount
- Single-threaded uvicorn backend
- 4 parallel PW workers
- PW specs that observe the network layer
- The optimization must not change what PW observes

What is the correct architectural solution?

**→ Answered in §2 (v4.1):** the constraint above eliminates every client-side option; the fix is backend
endpoint caching (`@cached_static`), which keeps all network calls observable while removing the per-request
recompute that was the actual cost.

---

## 1. What works (backend infrastructure — keep all of it)

All backend infrastructure from v1/v2/v3 is correct, tested, and stays:

- TabStateCache with version protocol, Wave 1/Wave 2
- KeySpec with schemas and urls, validate-on-produce
- @invalidates decorator + MUTATION_PATHS + scanner
- GET /api/{copilot}/static-urls endpoint
- X-Invalidated-Urls response header on mutations
- Output-equivalence tests
- Schema currency tests
- Memory guards
- Preseed-only warm-up (C-H)
- Per-key error isolation
- 1,213 Trading backend tests, 0 failures

This infrastructure is the foundation for whatever frontend optimization is chosen.

---

## 2. The decision (v4.1)

**v4 correctly stopped at "candidates for review." This section makes the call, because §0.3 already contains
the filter that decides it.**

### 2.0 The constraint filter eliminates all but one family

§0.3 is not one consideration among many — it is the **deciding constraint**, and applying it is the whole
decision:

> *Any optimization that changes when or whether a network call happens breaks Playwright's `waitForResponse`.*

Run every candidate through that filter:

| Candidate | Changes what PW observes? | Verdict |
|---|---|---|
| 2.2 Frontend batch (rewrite panels) | **Yes** — 23 calls become 1 (reorders/combines) | **Eliminated** — same class as v3's failure, plus it re-opens Strategy A's panel rewrite |
| 2.4 PW-aware branching | **Yes in prod, no in PW** — so the prod path is *never tested* | **Eliminated** — this is how you author a 5th failure history |
| 2.1 `@cached_static` (backend) | **No** — 23 calls still happen, each is faster | **Survives** |
| 2.3 `--workers=1` | **No** — calls unchanged, just serial | **Survives** (it's the risk-free floor) |

**Only backend-side optimizations survive, exactly as §0.3 predicts.** That leaves 2.1 and 2.3 — and they are
**not mutually exclusive.** The decision is not "which one"; it's "2.1 as the fix, with 2.3 available as a
zero-cost belt-and-suspenders."

### 2.1 The recommendation: `@cached_static` (2.1), optionally with `--workers=1` (2.3)

**Decision: implement `@cached_static` on the STATIC endpoints. Keep `--workers=1` for Trading in reserve (and
free to apply now, since 3 other copilots already use it).**

The document lists 2.1's "doesn't reduce request COUNT" as a con and worries it "doesn't scale to 50+ panels."
**The arithmetic says that worry is misplaced.** Model the single server thread as the bottleneck (correct per
§0.0 — 4 browsers, but *one* uvicorn thread), wall-time ≈ total_requests × per-request server time:

| Scenario | Requests | Wall time | vs PW timeout |
|---|---:|---:|---|
| **Current** (uncached, 4 workers, ~100 ms/req) | 92 | **~9.2 s** | fails (matches the observed 9–30 s) |
| **2.1** `@cached_static` (4 workers, ~6 ms/req) | 92 | **~0.6 s** | passes comfortably |
| **2.3** `--workers=1` (uncached) | 23 | ~2.3 s | passes |
| **2.1 + 2.3** (cached, 1 worker) | 23 | ~0.1 s | passes |
| **2.1 at 50 panels** (4 workers, ~6 ms) | 200 | **~1.2 s** | still passes |
| **2.1 at 50 panels** (pessimistic 12 ms) | 200 | ~2.4 s | still passes |

**The "request count" con is real but immaterial:** cutting per-request server time from ~100 ms to ~6 ms
collapses the 4-worker wall time from ~9 s to well under 1 s, and the *slope* stays gentle enough that even a
hypothetical 50-panel tab under 4 workers stays ~1–2 s. The problem was never the number of requests; it was
**~100 ms of recompute per request serialized on one thread.** `@cached_static` removes the recompute. That is
the actual fix.

**Why 2.1 beats the alternatives on their own terms:**
- vs **2.3 alone:** 2.3 masks the latency (7 min → 20 min PW; demo/prod still slow at 2.3 s/mount). 2.1 *fixes*
  it and speeds demo/prod. Use 2.3 only if a residual flake remains after 2.1.
- vs **2.2 / batch:** batch is architecturally tempting (23→1 request) but it either rewrites panels (Strategy A,
  23–101 failures) or batches in `apiGet` (Strategy B, breaks `waitForResponse`). **2.1 gets 90% of the benefit
  with 0% of the risk** and touches no panel and no PW spec.
- vs **2.4 / PW-aware:** never ship a production path PW doesn't exercise. Eliminated on principle.

**The backend batch endpoint (2.2) is not wasted** — it stays built, unused by the frontend, as the escape hatch
*if and only if* a real 50+-panel tab ever pushes cached 4-worker time toward the timeout (the table says it
won't for a long while). When that day comes, the correct consumer is a **backend-composed** batch (one request
in, one response out — PW sees one call), never a frontend batcher.

### 2.2 What `@cached_static` must actually do (so it doesn't become failure #5)

The decorator is small, but four details are load-bearing:

```python
def cached_static(key: str):
    def deco(handler):
        @wraps(handler)
        async def wrapper(*args, **kw):
            entry = cache.get(key)                      # versioned TabStateCache entry (Appendix §4.1)
            if entry and entry.status == "ready":
                return entry.data                       # cache HIT — no recompute, network call still happened
            result = await handler(*args, **kw)         # cache MISS — compute, then populate
            cache.set(key, result)                      # validate-on-produce (C-B) happens in cache.set
            return result
        return wrapper
    return deco
```

1. **The network call still happens.** The decorator sits *inside* the handler path; the HTTP request/response is
   unchanged, so `waitForResponse`, `page.on('response')`, and status assertions all still fire. **This is the
   entire reason 2.1 survives the §0.3 filter — do not "optimize" it into skipping the response.**
   *Precise claim:* `@cached_static` changes no network **event** and no response **body** — it changes response
   **timing** (much faster). That is safe for the assertions that actually broke this project (`waitForResponse`
   firing, status, call count — all unchanged). The only residual risk is the rare spec that asserts *slowness*
   (e.g. "the loading spinner is visible") or *inter-response ordering* under load; P3 checks for these. Do not
   claim "invisible to PW" — claim "changes only timing, in the safe direction."
2. **Decorator order matters (silent footgun).** `@cached_static` must sit **below** `@router.get` so FastAPI
   still registers the route and owns request parsing / response serialization:
   ```python
   @router.get("/api/trajectory")     # FastAPI registers the route (must be outermost)
   @cached_static("trajectory")       # cache read/populate wraps only the handler body
   async def get_trajectory(): ...
   ```
   Reversed, FastAPI would register the *wrapper's* signature and lose the handler's params/response model.
   `@wraps(handler)` preserves the signature, but order is still load-bearing — state it in the decorator's
   docstring.
3. **Invalidation is the existing path, not a new one.** Mutations already recompute and re-`cache.set` affected
   keys via `@invalidates` (Appendix §5). `@cached_static` only *reads* that same cache. No second invalidation
   map, no drift (the lesson from every prior version).
4. **Miss is correct, not just fast.** On a cold key the decorator calls the real handler — so a
   never-warmed key behaves exactly as today (just uncached). Preseed warm-up (C-H) makes the warm path the
   common case; the cold path is the pre-existing behavior, which means **2.1 can never render *less* than the
   current system does.** That property is why it can't regress the way v1/v2/v3 did.

### 2.3 Migration (replaces the v3.1 frontend plan entirely)

| Phase | Work | Files | Risk | Est. |
|---|---|---|---|---|
| **P1** | Confirm baseline: revert any v3 `apiGet` cache; PW green at 239/2. | api.ts | none | 0.25d |
| **P2** | `@cached_static` decorator + apply to the 43 STATIC endpoints (annotation only — handlers unchanged). | 1 util + N one-line annotations | LOW — miss path = current behavior | 0.5d |
| **P3** | PW full run. Assert: (a) all network calls still observed (`waitForResponse` fires); (b) warm-mount server time < 1 s under 4 workers; (c) no spec regresses vs 239/2; (d) **no timing/ordering-sensitive spec breaks** — scan for specs asserting spinner visibility or inter-response order, which faster responses could flip (§2.2 note 1). | 0 | — | 0.5d |
| **P4 (only if P3 flakes)** | Add `--workers=1` for Trading (matches DataOps/S2P/SOC). | PW config | none | 0.1d |
| **Total** | | **1 util + 43 annotations, 0 panel changes, 0 PW-spec changes** | | **~1.25d** |

**Hard rule (unchanged from v3): at no point may PW fail more than the 239/2 baseline. `@cached_static` is
additive and the miss-path is current behavior, so a regression means the decorator is skipping the response —
fix that, don't branch on PW.**

### 2.4 Invalidation Architecture Decision

**Decision: Option C, three-tier invalidation with lazy STANDARD recompute.**

The eager Wave 2 model recomputed STANDARD keys in a background task after mutation. That looked safe because it
returned the mutation response after Wave 1, but the background task still ran synchronous compute functions on
the event loop in batches. Under four Playwright workers, a mutation is often followed immediately by a tab
mount, so eager Wave 2 spent the worst possible moment recomputing keys that the next screen might not read.

The corrected rule is:

| Tier | Keys | Mutation behavior |
|---|---|---|
| CRITICAL | `trajectory`, `conservation`, `analytics` | Recompute synchronously in Wave 1. These are fresh before the mutation response completes. |
| STANDARD | Stateful non-critical keys | Delete the cache entry. Do not recompute. The next `@cached_static` miss lazily recomputes through the existing endpoint handler. |
| COLD | `archetypes`, `fingerprint`, `correlation-config` | Unchanged for ordinary mutations. Deleted/recomputed only on reset. |

Why not eager Wave 2:

- eager prefetch pays only when there is idle capacity and the next read set is predictable
- this workload has no quiet period: mutation flows immediately switch tabs
- Wave 2 recomputed roughly 21 keys on `score`, while the next screen might read only a subset
- eager recompute therefore did strictly more work than necessary at the exact contention point

Why Option C is safe:

- the worst case is a deleted STANDARD key followed by a normal endpoint handler call
- that is exactly the pre-cache baseline behavior for that key
- the best case is a cache hit
- the architecture cannot be worse than baseline for STANDARD keys unless the handler itself regresses

Implementation rules:

- non-reset events always include every CRITICAL key
- non-reset events delete only STANDARD keys whose event is in `invalidated_by`
- reset applies to every registered STATIC or QUASI_STATIC key
- COLD keys are unaffected by ordinary mutations
- no background STANDARD recompute task exists

A registry test still enforces that every STANDARD key has at least one known invalidation event. This is a
syntax/completeness floor, not a full Python call-graph proof.

### 2.5 `@cached_static` Eligibility Criteria

`@cached_static` is only valid on truly static GET endpoints:

- no query parameters
- no path parameters
- no request body
- same response shape and semantics for every request to that route

Parameterized endpoints must not be annotated. They can remain in the registry as materialized default or summary
keys, but the legacy endpoint itself must keep normal handler behavior because a single cache key cannot represent
all request variants.

v4.2 exception: a parameterized endpoint may use `@cached_quasi_static`, not `@cached_static`, when all of these
are true: the parameter space is small/known, the response is stable until mutation for an identical parameter
value, the default parameter set is declared in `KeySpec.default_params`, and measured warm compute time exceeds
500 ms. The cache key must include the parameter value, and invalidating the base key must clear every parameter
variant.

Removed/forbidden examples:

| Endpoint | Reason |
|---|---|
| `/api/trading/correlation?window=...` | query parameter changes the window |
| `/api/trading/journal/trades?...` | filters, limit, offset, search change the response |
| `/api/trading/analytics?group_by=...` | grouping and filters change the response |
| `/api/trading/evolution/log?kind=...` | query parameter filters the log |
| `/api/trading/regime/history?days=...` | query parameter changes the history window |
| `/api/archetypes?domain=...` | query parameter filters domains |
| `/api/self/centroid-history?...` | filters and limit change the response |
| `/api/self/accuracy-by-category?threshold=...` | threshold changes alert fields |
| `/api/self/decisions?...` | filters, limit, and verified_only change the response |
| `/api/self/audit-trail?...` | decision_id and limit change the response |

A test must scan decorated handlers and fail if any `@cached_static` handler accepts non-`Request` parameters.

### 2.6 Answering §2.5 ("other approaches")

Three were left open; for completeness, each fails the §0.3 filter or adds risk without payoff:
- **HTTP/2 multiplexing / keep-alive** — reduces TCP overhead, but the bottleneck is the single-threaded
  *event loop*, not connections; marginal, and infra-dependent.
- **Uvicorn `--workers=N` (multiprocess)** — would parallelize the backend, but the app's in-memory
  TabStateCache is per-process; correct multi-worker needs the Redis/SQLite move (Appendix §4.9) and is a
  production concern, not a PW-timeout fix. **Do this when you productionize, not now.**
- **Reduce panels per tab** — the only approach that cuts request count without touching the network semantics,
  but it's a product/UX change, not an architecture fix; keep it as a design-hygiene note, not a solution.

**Bottom line:** the failure history wasn't four wrong implementations of a good idea — it was three attempts at
the *wrong layer*. §0.3 says the fix must be backend-transparent-to-PW. The smallest such fix that removes the
actual cost (recompute) is `@cached_static`. Ship it.

### 2.7 Quasi-Static Caching

`@cached_static` is intentionally conservative: it is forbidden on any endpoint whose response varies by query
string, path parameter, or request body (§2.5). That rule is correct for a single cache slot, but it leaves one
important class uncovered: parameterized endpoints whose result is stable for the same parameter set until the
next mutation.

v4.2 adds a third materialization category:

| Category | Meaning | Cache key | Eligibility |
|---|---|---|---|
| STATIC | No request parameters; one response per copilot state | `key` | Always eligible for `@cached_static` |
| QUASI_STATIC | Parameterized, but finite/default parameter set and mutation-stable | `key:param_value` | Eligible only if >500 ms, small param space, mutation-stable |
| DYNAMIC | User-selected or effectively unbounded parameters | none | Never endpoint-cached |

`@cached_quasi_static(key, param_fn)` is the backend-only companion to `@cached_static`. The HTTP request still
reaches FastAPI, so Playwright still observes the network event. `param_fn(Request) -> str` extracts the
cache-varying value; for example `window=20` for `/api/trading/correlation?window=20`. The cache entry becomes
`correlation:window=20`, while mutation invalidation still names the base key `correlation` and clears every
`correlation:*` variant.

Warm-up precomputes default parameters only. A `KeySpec` may declare:

```python
KeySpec(
    name="correlation",
    url="/api/trading/correlation",
    category="QUASI_STATIC",
    default_params={"window": "20"},
    compute_fn=lambda: compute_correlation(window=20),
    ...
)
```

Requests for default params hit the preseed-warmed entry. A non-default request, such as `window=50`, computes
once through the original handler and stores `correlation:window=50`; subsequent identical requests hit cache.
Any successful mutation invalidates the HOT base key and deletes all parameter variants before recomputing the
default variant.

Measured on the running preseed backend for this implementation pass:

| Endpoint | Params | Time (ms, max of 3 warm runs) | Classification |
|---|---|---:|---|
| `/api/trading/correlation?window=20` | `window` | 154 | QUASI_STATIC candidate, not cached now (<500 ms warm) |
| `/api/trading/journal/trades` | filters, `limit`, `offset` | 97 | DYNAMIC (large user-selected filter space) |
| `/api/trading/analytics?group_by=category` | `group_by` | 57 | QUASI_STATIC candidate, not cached now (<500 ms) |
| `/api/trading/analytics?group_by=subcategory` | `group_by` | 169 | QUASI_STATIC candidate, not cached now (<500 ms) |
| `/api/trading/evolution/log` | `kind`, `limit` | 49 | DYNAMIC (filtered log view, fast) |
| `/api/trading/regime/history` | `days` | 13 | QUASI_STATIC candidate, not cached now (<500 ms) |
| `/api/archetypes?domain=trading` | `domain` | 11 | QUASI_STATIC candidate, not cached now (<500 ms) |
| `/api/self/centroid-history` | filters, `limit` | 10 | DYNAMIC (filtered history, fast) |
| `/api/self/accuracy-by-category` | `threshold` | 23 | QUASI_STATIC candidate, not cached now (<500 ms) |
| `/api/self/decisions?limit=50` | filters, `limit` | 66 | DYNAMIC (decision explorer filters) |
| `/api/self/audit-trail` | `decision_id`, `limit` | 51 | DYNAMIC (selected decision audit) |
| `/api/trading/promotion/dashboard` | none | 118 | STATIC/HOT, already covered by `@cached_static` |

Decision for this pass: implement the quasi-static infrastructure and tests, but annotate **zero** current
endpoints because no measured parameterized endpoint exceeds the >500 ms threshold on the warm preseed backend.
If cold-start or CI measurements later show `/api/trading/correlation?window=20` consistently above 500 ms, it
is the first endpoint to register as QUASI_STATIC with `default_params={"window": "20"}`.

### 2.8 Compute Offload Architecture

`@cached_static` and `@cached_quasi_static` remove recomputation from warm endpoint hits, but the cache itself
still computes during warm-up and invalidation. A later implementation offloaded synchronous cache compute with
`asyncio.to_thread`. Review evidence showed that was the wrong tradeoff for this codebase:

- FastAPI sync route handlers use AnyIO's thread pool, measured at 40 tokens.
- `asyncio.to_thread` uses the event loop's default executor, measured at 20 workers.
- The pools are separate, but they share CPU. Offloading Wave 2 cache recompute added CPU pressure while the
  route pool was already saturated by panel GET fanout.
- Wave 1 is intentionally small: at most three critical keys. The measured budget is about 15 ms, which is far
  below the 500 ms event-loop limit.

Design decision: do **not** offload TabStateCache invalidation compute to `asyncio.to_thread`. Synchronous
compute functions are called directly:

```python
if inspect.iscoroutinefunction(compute_fn):
    await compute_fn()
else:
    compute_fn()
```

Wave 1 blocks the event loop briefly and predictably. Wave 2 remains fire-and-forget and batched; each batch
uses direct compute and then yields with `sleep(0)` before the next batch. This removes the extra asyncio thread
pool pressure without changing cache correctness or response content.

Handler audit on the Trading routers and shared SDK backend routers still stands:

| Category | Definition | Count | Decision |
|---|---|---:|---|
| A | `async def` GET, no `await`, CPU compute | 0 | No route changes |
| B | `async def` GET, mixed await + CPU compute | 0 | No route changes |
| C | `async def` GET, I/O only | 0 in audited Trading/shared route set | No route changes |
| D | `def` GET, CPU/read compute already offloaded by FastAPI | 81 | Keep as-is |
| E | `@cached_static` endpoint | 27 | Keep as-is; hit path avoids compute, miss path already runs in FastAPI's route pool |

Layered defense after v4.3:

1. `@cached_static`: avoids recompute for truly static warm endpoint hits.
2. `@cached_quasi_static`: provides a parameter-aware cache path when a parameterized endpoint is both slow and
   mutation-stable.
3. Lazy STANDARD recompute: deletes non-critical cache entries and lets ordinary endpoint misses recompute only
   what is actually read.

### 2.9 Mutation-Invalidation Atomicity

The Trading/shared SDK route audit found that mutating handlers are synchronous `def` handlers. FastAPI runs those
handlers in its thread pool, so two Playwright workers can execute `score`, `learn`, promotion, transfer, import,
journal, broker, or webhook mutations concurrently against the same in-process scorer and graph state.

The invariant is stronger than "mutations are serialized": **mutation side effects and cache maintenance are one
critical section.** A mutation is not complete until CRITICAL keys have been recomputed and affected STANDARD keys
have been deleted while the same domain mutation lock is still held.

Two mutation patterns are supported:

```python
# Manual lock path used by shared score/learn routes.
with get_mutation_lock(domain):
    result = scorer.score(...)
    apply_cache_invalidation_event(domain, "score")

# Decorator path used by app-specific mutation routes.
@router.post("/trading/evolution/promote")
@serialize_mutation("trading", event="evolution")
def promote(...):
    ...
```

Inside the lock:

- recompute CRITICAL keys synchronously
- delete affected STANDARD keys
- leave COLD keys alone except on reset
- if cache recompute fails, log and delete both CRITICAL and STANDARD affected entries

Deleting on failure is fail-safe: a later GET falls back to the legacy endpoint path instead of serving stale cache
data. That fallback is safe only because Category A cached misses also synchronize scorer reads (§2.13).

`@invalidates` and the old post-response invalidation middleware are removed from the execution path. The
invalidation module remains as the owner of `MUTATION_PATHS`, cache registration/accessors,
`invalidate_cache_event()`, and the route scanner. A thin header middleware may still set
`X-Invalidated-Urls`, but it never performs invalidation.

Rules:

- Use `threading.Lock`, not `asyncio.Lock`, because mutation handlers run in worker threads.
- Use one lock per scorer/copilot domain, so Trading does not block Purchasing.
- Lock score, learn, verify/confirm, promotion/demotion, transfer execution, evolution mutations, journal writes,
  data import, market refresh, broker mutations, and webhook auto-score ingestion.
- Do not lock read-only POSTs such as counterfactual and pre-score.
- Keep handlers as `def`; the lock serializes writes while FastAPI keeps the event loop free for GET requests.
- `invalidate_cache_event(domain, event)` is for out-of-band paths that do not already hold the mutation lock. Code
  already inside the lock must call `apply_cache_invalidation_event()` directly to avoid deadlock on the
  non-reentrant domain lock.

FreshScorerProxy interaction: app backends that use `FreshScorerProxy` already serialize individual proxy methods
with a per-proxy `RLock`. That protects calls such as `proxy.score()` and `proxy.learn()`. It does not cover
surrounding route-level side effects or cache invalidation, so the outer domain lock remains required.

### 2.10 Thread Pool Budget

The local runtime has two relevant pools:

| Pool | Size | Used by |
|---|---:|---|
| AnyIO/FastAPI route pool | 40 tokens | sync `def` GET and POST handlers |
| asyncio default executor | 20 workers | `asyncio.to_thread` if introduced elsewhere |

Under four Playwright workers, a tab with twelve uncached sync GETs can request about 48 route-pool slots before
mutation traffic is counted. That already exceeds the 40-token AnyIO budget. `@cached_static` reduces handler
hold time for truly static endpoints, but it does not reduce request count, so the route pool remains the
capacity boundary.

Mitigations in this design:

- keep cached endpoint hit paths fast and side-effect free
- keep Wave 1 to three CRITICAL keys
- avoid `asyncio.to_thread` for cache recompute unless a measured event-loop budget violation returns
- delete STANDARD entries instead of eagerly recomputing them after mutation
- use single-flight on `@cached_static` misses so concurrent requests for one key produce one recompute

Production scaling requires an explicit resource plan: uvicorn worker count, AnyIO limiter sizing, cache storage
outside one process if multiple workers are used, and metrics for route-pool wait time and invalidation duration.

### 2.11 Schema Live Validation

Strict Pydantic schemas are only useful if they match the real endpoint payloads. A concrete failure proved the
gap: `/api/trajectory` returned `days_active` as a float, but the schema declared an int, so validate-on-produce
rejected the payload and left the cache entry `missing`.

Every registered non-DYNAMIC key must pass `schema.model_validate(response.json())` against the endpoint named
by its `KeySpec.url`. A backend test enforces this with the app's TestClient. Schema drift should fail in tests,
not surface as a warm-cache `missing` status during Playwright or production use.

If a CRITICAL schema is wrong, its key can remain `missing` until the schema is fixed and the cache is warmed
again. `@cached_static` deliberately does not populate CRITICAL keys on miss; CRITICAL freshness is owned by
warm-up and Wave 1 invalidation only.

### 2.12 Single-Flight Miss Recompute

Deleting STANDARD keys creates a thundering-herd risk: four Playwright workers can request the same endpoint
after one mutation and all see the same miss. `@cached_static` therefore uses a per-copilot/per-key
single-flight guard.

Behavior:

- first miss for `copilot:key` enters the real handler
- concurrent misses for the same `copilot:key` wait on a `threading.Event`
- when the first handler returns, waiters receive the same result
- if the wait times out, the waiter falls through to the handler, preserving baseline behavior
- successful STANDARD and COLD miss results are stored in TabStateCache
- CRITICAL miss results are never stored by the decorator

The waiting threads still occupy AnyIO route-pool slots, but they do not run duplicate compute. That keeps the
post-mutation worst case at one handler call per key instead of one handler call per key per worker.

### 2.13 Scorer Read Synchronization

Cached hits do not read scorer state and remain lock-free. Cached misses are different: the miss path runs the
legacy endpoint handler, and some handlers read scorer state. Those keys declare `reads_scorer=True` on their
`KeySpec`.

Category A (`reads_scorer=True`) keys:

- `measurement-state`
- `transfer-status`
- `fingerprint`
- `trust-analysis`
- `counterfactual-default`
- `trajectory`
- `conservation`
- `transfer`
- `iks`

On a Category A `@cached_static` miss, the handler executes under the same domain mutation lock used by mutation
handlers. Category B and Category C misses do not acquire the lock.

Single-flight interaction:

- first miss for a key becomes the computing thread
- concurrent misses for the same key wait on a `threading.Event`, not on the mutation lock
- if the computing key is Category A, only that computing thread holds the domain lock
- different Category A keys serialize behind the same domain lock, preventing torn scorer reads during a mutation

This keeps the uncontended warm path fast and only pays the lock cost on the rare path where a scorer-reading key is
not ready in cache.

### 2.14 Known Screen-Gate Fragility

The restored frontend screens still gate entire child trees behind `Promise.all` calls. The p99 of any single
gate request becomes the render latency for every nested panel on that screen. Option C removes the current
backend trigger for those stalls, but the gate remains fragile.

Future work: let screen shells render immediately and let children keep their independent fetch/error states.
That is not a panel rewrite and does not reintroduce `useTabData`; it only removes all-or-nothing screen gates.

---

## 3. Appendix: retained v3.1 content

The v3.1 document (§2.1-2.5, §3-7, and Appendix A) is preserved as reference. **Read it with the v4.1 decision
in mind:** the frontend proxy (v3.1 §2.1–2.5) is a *correct-but-rejected* approach — it is well-engineered and
its bugs were fixed, but it fails the §0.3 PW-observation constraint and is **not** the chosen solution. Keep it
as the record of why client-side optimization was ruled out. The **backend** sections (Appendix A: TabStateCache,
version protocol, schemas, invalidation, warm-up, gates) are implementation-ready and are exactly what
`@cached_static` (§2) reads from.

---

## 4. Appendix: retained v2 backend spec

(Unchanged from v3.1 Appendix A — the full backend spec including TabStateCache, version protocol, Wave 1/Wave 2, KeySpec, schemas, invalidation maps, warm-up, gates, and testing strategy.)

---

### 0. What went wrong in v2, and why contracts alone don't work (read first)

#### 0.0 The v2 implementation timeline (evidence)

```
Baseline (pre-migration):       239 passed, 2 flaky timeout (fetch fanout)
v1 migration (batch panels):     23 failed (key drift, wrong shapes, unmigrated panels)
v1 + manifest (typed keys):       5 failed (compute correctness, DOM mismatch)
v1 + manifest + fixes:           12 failed (React duplicate key from archetypes compute)
v2 P0 (schema spine + gates):     0 new failures (infrastructure only, no panel changes)
v2 P3 (panel re-migration):      23 failed (same class as v1 — shapes, keys, unmigrated)
v2 P3 + systemic P2 fixes:      101 failed (strict schemas reject valid endpoint data)
```

**Every migration attempt that touches panels in bulk produces a regression larger than the problem it solves.**

#### 0.1 v2's contracts were correct — the migration strategy was not

v2 correctly diagnosed that v1 failed because of unguarded seams between four layers. v2 added contracts (C-A through C-I) and gates to enforce them. **The contracts themselves are sound and preserved in v3.**

But v2's migration strategy (§6) said "migrate Trading STATIC panels to useTabData, one key at a time" — and the implementation migrated **38 panels in one Codex session**. The contracts existed (schemas, gates, equivalence tests) but they tested the *infrastructure*, not the *live integration*. The output-equivalence test compared compute_fn to service_fn in a unit test with synthetic data. It did not curl the live endpoint and compare.

The 101 failures have one root cause: **P2-3 (strict schemas) rejected valid endpoint responses.** When we changed schemas from `extra="allow"` to `extra="forbid"`, every endpoint that returns even one field not declared in the schema causes a ValidationError at recompute time. Every key becomes `invalidated_error`. Every panel sees `data=null`. Every spec times out.

This is the same failure class as v1 §13.2, inverted:
- v1: schemas too loose → wrong shapes pass silently → panels render garbage
- v2: schemas too strict → correct shapes rejected → panels render nothing

#### 0.2 The deeper problem: bulk migration is inherently fragile

The fetch-fanout problem affected 2-3 specs intermittently under parallel Playwright workers. The "fix" (materialized state) required changing ~38 panel components, 5 screen files, 43 compute functions, 43 schemas, and the provider infrastructure. Each change was individually correct but the aggregate was untestable without a full PW run — which only happens on the user's machine, not in Codex.

**v3's central insight: don't migrate panels. Migrate the fetch path.**

#### 0.3 The v3 approach: transparent proxy, not panel rewrite

Instead of rewriting 38 panels to use `useTabData`, intercept their existing `fetch`/`apiGet` calls at the network layer:

```
v1/v2 approach (panel rewrite):
  Panel: useEffect → fetch("/api/trajectory") → setState       ← REMOVED
  Panel: useTabData(TRADING_KEYS.trajectory) → data from cache  ← ADDED
  Result: 38 components rewritten. 101 failures.

v3 approach (transparent fetch proxy):
  Panel: useEffect → fetch("/api/trajectory")                   ← UNCHANGED
  Proxy: intercepts /api/trajectory → reads from TabStateCache  ← NEW
  Panel: receives same response shape as before                 ← UNCHANGED
  Result: 0 components rewritten. Panels don't know about the cache.
```

The proxy sits at the Vite dev server level (or a service worker, or an apiGet wrapper). When a panel fetches a STATIC key's URL, the proxy checks the cache first. If cached and fresh: return immediately without hitting the backend. If not cached: pass through to the backend as normal.

**Panels never change. The API surface never changes. The cache is an optimization layer, not a rewrite.**

#### 0.4 Why this works where v2 didn't

| Concern | v2 (panel rewrite) | v3 (transparent proxy) |
|---|---|---|
| Components changed | 38 | 0 |
| Schema drift risk | High (Pydantic strict vs endpoint reality) | Zero (responses pass through unmodified) |
| TypeScript type drift | High (generated types vs panel destructuring) | Zero (panels use their existing types) |
| Migration risk | All-or-nothing per screen | Incremental per URL |
| Rollback | Revert 38 files | Disable proxy |
| PW spec impact | Every spec that asserts panel content | Zero (panels render identically) |
| Console.error risk | High (provider fetch errors) | Zero (panels use their own error handling) |

#### 0.5 What v3 preserves from v2

Everything that works:
- TabStateCache backend (materialized state, version protocol, Wave 1/Wave 2)
- Invalidation registry + @invalidates decorator + MUTATION_PATHS
- Preseed-only warm-up (C-H)
- KeySpec with schemas (for backend validation, not frontend consumption)
- Per-key error isolation (C7)
- Memory guards (C9)
- Individual endpoints remain (C5)

What v3 drops:
- TabDataProvider React context (panels don't use it)
- useTabData / useDerivedData hooks (panels don't call them)
- Frontend manifest / TRADING_KEYS / per-screen key lists (panels don't reference keys)
- Generated TypeScript types from Pydantic schemas (panels keep their own types)
- C-A (single key source — no longer needed when panels don't reference keys)
- C-D (no-bypass-fetch — no longer relevant when panels ARE the fetch path)
- C-F (stable key arrays — no TabDataProvider keys prop)

What v3 redefines:
- C-B becomes: validate-on-produce in the cache, not in the frontend
- C-C preserved: compute_fn wraps one service function, equivalence-tested
- C-E preserved: no console.error from the proxy layer
- C-G becomes: E2E spec verifies tab mount time <2s (the actual goal)

#### 0.6 Updated contracts

| # | Contract | Enforced by | What changed from v2 |
|---|---|---|---|
| **C-A** | DROPPED. Panels don't reference keys. The cache uses KeySpec internally. | — | Was: single key source. Now: not needed. |
| **C-B** | Cache validates compute_fn output via schema before storing. Frontend never sees invalid data because the proxy returns the cache entry's `data` field (already validated). | Pydantic validation at recompute time | Enforcement moves from frontend to backend only. |
| **C-C** | compute_fn wraps one service function. Output-equivalence tested. | Same as v2 | Unchanged. |
| **C-D** | DROPPED. Panels fetch normally. The proxy intercepts. | — | Was: no fetch for STATIC URLs. Now: fetch IS the interface. |
| **C-E** | Proxy layer uses console.debug, never console.error. Panels keep their own error handling unchanged. | Lint rule on proxy code only | Scope reduced from 38 panels to 1 proxy module. |
| **C-F** | DROPPED. No TabDataProvider, no keys prop. | — | Was: stable key arrays. Now: not needed. |
| **C-G** | E2E spec: tab mount completes in <2s with preseed data (the ACTUAL goal); plus a spec that a mutation clears the relevant cached URLs so the next read is fresh (the §2.5 correctness point). | PW perf + invalidation spec | Simplified to timing, plus a stale-after-mutation guard. |
| **C-H** | Preseed-only warm-up. Unchanged from v2. | Version protocol | Unchanged. |
| **C-I** | Shared SDK schemas for shared keys. Unchanged from v2. | Manifest layering | Backend only — no frontend manifest needed. |

---

### 1. Executive Summary (updated for v3)

The fetch-fanout problem: Trading tabs issue ~20-23 reads per mount against a single-threaded backend. Under parallel PW workers, tab render times exceed 15-30s.

v1 solved this by rewriting panels to read from a React context. 23 failures.
v2 added typed schemas and contracts. 101 failures after implementation.
v3 solves this transparently: **panels don't change. A fetch proxy intercepts STATIC key URLs and serves from the backend cache.**

```text
MUTATION: score / verify / learn / reset
  → backend recomputes affected STATIC keys (unchanged from v1/v2)
  → validates via schema (C-B)
  → stores in TabStateCache

TAB MOUNT (v3 — panel perspective unchanged):
  → panel calls fetch("/api/trajectory") as it always has
  → apiGet wrapper checks: is this URL a STATIC key? Is cache warm?
    → YES: return cached response immediately (0ms, no backend call)
    → NO: pass through to backend normally
  → panel receives the same response shape it always received
  → panel renders as it always has
```

---

### 2. Implementation: The Fetch Proxy

#### 2.1 Where the proxy lives

Option A: **apiGet/apiPost wrapper** (recommended for SDK copilots).
All panels already call `apiGet(url)` or `fetch(BASE + url)` through shared helpers in `api.ts`. The proxy is a cache layer inside `apiGet`:

```typescript
// api.ts — the ONLY panel-facing file that changes.
// Correctness = mutation-invalidation (§2.3). Coalescing = the fan-out fix. TTL = dev-only staleness cap.
const STATIC_URL_CACHE = new Map<string, { data: unknown; at: number }>();
const inflight = new Map<string, Promise<unknown>>();   // de-dupe concurrent identical GETs (the fan-out fix)
const DEV_TTL_MS = 60_000;                               // fallback only; correctness comes from invalidation

// One canonical cache key per logical resource. Panels may pass "/api/x", BASE+"/api/x", or "/api/x?k=v";
// STATIC keys must be parameter-free (that's what makes them STATIC), so we key on the path only.
function cacheKey(url: string): string {
  const path = url.replace(BASE, "");
  const q = path.indexOf("?");
  return q === -1 ? path : path.slice(0, q);
}

export async function apiGet<T>(url: string): Promise<T> {
  const key = cacheKey(url);
  const isStatic = STATIC_URLS.has(key);           // STATIC_URLS is populated before first mount — see §2.2

  if (isStatic) {
    const hit = STATIC_URL_CACHE.get(key);
    if (hit && Date.now() - hit.at < DEV_TTL_MS) return hit.data as T;   // fresh until invalidated or TTL
    const pending = inflight.get(key);
    if (pending) return (await pending) as T;                            // coalesce concurrent mount fetches
  }

  const p = (async () => {
    const response = await fetch(`${BASE}${url}`);
    if (!response.ok) throw new ApiError(response.status, url);          // do NOT cache a failed response
    return normalize(await response.json());                            // normalize ONCE, here
  })();

  if (isStatic) inflight.set(key, p);
  try {
    const data = await p;
    if (isStatic) STATIC_URL_CACHE.set(key, { data, at: Date.now() });  // cache the normalized value, on success only
    return data as T;
  } finally {
    if (isStatic) inflight.delete(key);                                 // clear in-flight whether resolved or rejected
  }
}
```

Three correctness details a coding session must not skip:
- **Normalize exactly once.** The cache stores the post-`normalize()` value and hits return it directly; there is
  no second normalize on the hit path. (The v3 draft normalized inconsistently across the hit/miss branches.)
- **Never cache a failure.** `response.ok` is checked before caching; a 4xx/5xx or a thrown fetch leaves the
  cache untouched, so one transient error can't pin a bad entry for `DEV_TTL_MS`. The `finally` clears the
  in-flight entry on both resolve and reject, so a failed GET doesn't wedge every subsequent caller.
- **Key on the path, not the raw string.** `cacheKey()` strips `BASE` and any query string so `"/api/trajectory"`,
  `` `${BASE}/api/trajectory` ``, and a stray `"/api/trajectory?"` are one entry. STATIC keys are parameter-free
  by definition (§4.7 / Appendix); a URL that carries a selection parameter is DYNAMIC and won't be in
  `STATIC_URLS`.

Option B: **Batch-on-mount** (future optimization).
When a screen mounts and triggers 20 apiGet calls within 50ms, batch them into one `GET /api/{copilot}/tab-state?keys=...` call. Return individual responses to each caller. Panels still don't know about the batch.

**Referenced helpers (assumed to exist, or add them — they're small):**
- `BASE` — the API base URL prefix already used by the existing `api.ts`.
- `normalize(json)` — the existing response-normalizer already applied in `api.ts` today (v3 does not change it).
- `apiGetUncached<T>(url)` — a plain `fetch(BASE+url).then(r => r.json())` with **no** cache logic, used only by
  `initStaticUrls` to avoid a bootstrap cycle (the cache isn't populated yet).
- `ApiError(status, url)` — a trivial `Error` subclass so callers can distinguish HTTP failures; panels' existing
  error handling catches it exactly as they catch today's fetch rejections (behavior unchanged for panels).

#### 2.2 STATIC_URLS registry

`STATIC_URLS` must NOT be a hand-maintained frontend list — that would be a third copy of "which keys are
STATIC" (after the backend registry and the KeySpec table), and it would drift the moment someone adds a key.
**The backend already knows this. Serve it.**

This requires the `KeySpec` (Appendix §2) to carry the **`url`** of the legacy endpoint it materializes — add
that field (it's the same URL the output-equivalence test already curls, so it exists implicitly):

```python
# backend — one endpoint, derived from the KeySpec registry (single source of truth).
# Requires KeySpec.url (the legacy endpoint path this key materializes). See Appendix §2.
@router.get("/api/{copilot}/static-urls")
def static_urls(copilot: str) -> list[str]:
    return [spec.url for spec in registry(copilot).specs if spec.category == "STATIC"]
```

```typescript
// api.ts — fetched ONCE at app init, BEFORE any tab can mount. No hand-maintained list.
let STATIC_URLS = new Set<string>();
export async function initStaticUrls(copilot: string): Promise<void> {
  const urls = await apiGetUncached<string[]>(`/api/${copilot}/static-urls`);
  STATIC_URLS = new Set(urls.map(cacheKey));   // store canonical path form (matches apiGet's cacheKey)
}
```

> **Ordering is load-bearing (do not skip).** If a tab mounts before `initStaticUrls()` resolves, `STATIC_URLS`
> is empty, every URL is treated as non-STATIC, and **the very first mount — the worst one, 23 cold fetches —
> gets no coalescing.** That is exactly the case this design exists to fix. So `initStaticUrls(copilot)` must be
> **awaited during app bootstrap, before the router renders any copilot screen** (e.g. in a top-level loader /
> route guard that blocks first paint of a copilot tab until it resolves). It is one request, served from the
> registry, and it is cheap. A PW spec must assert the first Trading mount issues ≤1 backend call per STATIC URL
> (see §7 / C-G).

The URL→key mapping now lives in **exactly one place** (the backend KeySpec table). The frontend learns it at
startup. Adding or removing a STATIC key requires no frontend change at all.

#### 2.3 Cache invalidation on mutation

When a panel calls `apiPost("/api/score", ...)`, the affected cached URLs must be cleared **before** the panel
re-reads them. But the map of "which mutation invalidates which URLs" must **not** be re-typed on the frontend —
that is the same relationship the backend invalidation registry (Appendix §5) already owns, and two hand-kept
copies is exactly the drift class that caused v1. **Two options, both single-source:**

**Preferred — the backend tells the response what it invalidated.** The `@invalidates` decorator already knows
the affected keys; echo them in a response header:

```python
# backend: the mutation response already recomputed these — name them
response.headers["X-Invalidated-Urls"] = ",".join(url_for(k) for k in affected_keys)
```

```typescript
export async function apiPost<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE}${url}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  // Clear exactly what the backend says it invalidated — no frontend map to drift.
  const invalidated = response.headers.get("X-Invalidated-Urls");
  if (invalidated) {
    for (const u of invalidated.split(",")) STATIC_URL_CACHE.delete(cacheKey(u));  // canonicalize to match apiGet
  }
  if (!response.ok) throw new ApiError(response.status, url);
  return normalize(await response.json()) as T;
}
```

Two integration details that are easy to miss and will silently break the header path:
- **The `finally`/clear runs whether or not `response.ok`** — but only clear on a **successful** mutation (a
  failed mutation changed nothing, so nothing should be invalidated). The `ok` check therefore comes *after* the
  clear only if the backend sets the header solely on success; simplest is: backend sets `X-Invalidated-Urls`
  only when the mutation committed, and the frontend clears whatever it receives.
- **CORS/proxy must expose the header.** A custom response header is invisible to `fetch` unless the server sends
  `Access-Control-Expose-Headers: X-Invalidated-Urls` (and any dev proxy forwards it). If the header can't be
  guaranteed end-to-end, use the startup `invalidation-map` fallback below instead — do not fall back to a
  hand-typed map.

**Fallback (if headers are awkward through the stack):** fetch the invalidation map once at startup from
`GET /api/{copilot}/invalidation-map` (derived from the same registry) and apply it client-side. Either way the
relationship is defined **once**, on the backend.

> **Correctness note (the v3 bug this fixes):** a purely time-based 60s TTL would let a concurrent component hold
> pre-mutation data for up to a minute, and a GET racing the invalidation could re-cache a stale body. Clearing
> on the mutation response — synchronously, before the re-read — closes that window. The backend's version
> protocol (Appendix §4.1) remains the ultimate guard: even if a stale GET slips through, it fetches the
> backend cache entry, which is already versioned to the latest mutation.

#### 2.4 What about the backend TabStateCache?

It stays. Option A (frontend cache) solves the PW timeout problem immediately with ~1 file changed. Option B (batch-on-mount) uses the backend TabStateCache to serve batched responses. Both can coexist:

- Phase 1: Frontend apiGet cache (1 day, 1 file, 0 panel changes)
- Phase 2: Backend batch endpoint (already built) as an optimization
- Phase 3: apiGet batching (collect 50ms of calls, send one batch request)

Phase 1 alone solves the PW timeout problem. Phases 2-3 reduce backend load for production.

---

#### 2.5 The one principle that keeps v3 correct: consume the backend's truth, don't copy it

v3's proxy is a *cache*, and a cache is only safe if it invalidates on the same events as its source. The three
things the proxy needs — **which URLs are STATIC**, **which mutation invalidates which URLs**, and **whether a
cached entry is current** — are all already known to the backend (KeySpec registry, invalidation registry,
version protocol). The frontend must **read** them, never **re-declare** them:

| Proxy needs | ❌ Don't (drift) | ✅ Do (single source) |
|---|---|---|
| Which URLs are STATIC | hand-maintained `STATIC_URLS` set | `GET /static-urls` at init (§2.2) |
| What a mutation invalidates | hand-maintained `MUTATION_INVALIDATION` map | `X-Invalidated-Urls` response header (§2.3) |
| Is a cached entry stale | 60s TTL guess | cleared on mutation; backend entry is version-guarded (Appendix §4.1) |

This is the same lesson as v1/v2, one layer down: **every hand-maintained mirror of a backend fact is a future
drift bug.** v3 changes 1 panel-facing file (`api.ts`) — but it changes it to *ask the backend*, not to keep a
parallel copy. The TTL stays only as a dev-mode staleness cap, never as the correctness mechanism.

---

### 3. Migration strategy (v3)

| Phase | Work | Files changed | Risk | Est. |
|---|---|---|---|---|
| **P0: Backend endpoints** | Add `KeySpec.url`; add `GET /{copilot}/static-urls`; set `X-Invalidated-Urls` on mutation responses (+ `Access-Control-Expose-Headers`). Backend-only, additive. | ~3 backend files | LOW — additive | 0.5d |
| **P1: Revert frontend** | Revert all panel migrations to pre-`TabDataProvider` state. Keep the backend cache, schemas, gates, registry. | ~35 frontend files reverted | LOW — restoring known-good state | 0.5d |
| **P2: apiGet cache** | Add the cache + `inflight` coalescing + `cacheKey` + `initStaticUrls` (awaited in app bootstrap) + the `apiPost` header-clear. **No hand-maintained URL or invalidation maps** (both backend-served). | 1 file (`api.ts`) + 1 bootstrap hook | LOW — additive, panels unchanged | 0.5d |
| **P3: Verify** | Full PW. Must match or beat the pre-migration 239/2 baseline. Add the two specs below. | 0 | — | 0.5d |
| **P4: Backend batch (optional)** | Wire apiGet to batch concurrent calls into one `tab-state` request. | 1 file (`api.ts`) | LOW — transparent to panels | 1d |
| **Total** | | **~1 frontend file + a small backend endpoint set** | | **2–3d** |

**P3 must add two specs (they are the correctness guards for this design):**
1. **Fan-out:** on the first Trading tab mount (cold cache), assert ≤1 backend call per STATIC URL — proves
   coalescing + init-ordering work (guards the §2.2 race).
2. **Stale-after-mutation:** score → assert the next read of an invalidated URL returns post-mutation data,
   not the cached pre-mutation body — proves the `X-Invalidated-Urls` clear works (guards §2.3).

**Hard rule: at no point does PW fail more than the pre-migration baseline (2–3 flaky). If P2 introduces even 1 new failure, debug before P4.**

---

### 4. What v3 keeps from v1/v2 (backend — untouched)

All backend infrastructure stays:
- TabStateCache with version protocol, Wave 1/Wave 2
- KeySpec with schemas, validate-on-produce
- @invalidates decorator + MUTATION_PATHS + scanner
- Output-equivalence tests
- Schema currency tests
- Memory guards
- Preseed warm-up (C-H)

This infrastructure supports Phase 4 (backend batch) and is also the foundation for Purchasing/DataOps/S2P if we ever need it.

---

### 5. Lessons learned across v1/v2/v3

#### 5.1 Never rewrite consumers to match a new abstraction

v1 and v2 both rewrote 38 panel components to use a new data-fetching abstraction (useTabData). Each rewrite introduced drift between what the panel expected and what the abstraction provided. The abstraction was correct in isolation; the integration failed at scale.

**The proxy pattern succeeds because it doesn't rewrite consumers.** Panels keep their existing fetch calls. The optimization is invisible to them.

#### 5.2 Strict schemas on incomplete knowledge = total failure

v2 P2-3 changed schemas from extra="allow" to extra="forbid" without curling every endpoint to verify the schema covers every field. The result: every endpoint that returns an undeclared field causes a ValidationError, and 101 panels render nothing.

**Strict schemas are correct but require exhaustive verification against live data.** The v3 backend cache still validates with schemas, but schema failures affect only the cache — they never reach panels because panels fetch from the live endpoint as fallback.

#### 5.3 Batch migration is untestable without PW

Codex can't run Playwright. So a migration that changes 38 components can only be verified by backend tests and TypeScript build. The actual integration (does the panel render in the browser?) is only testable on the user's machine. Batch migration means discovering all failures at once, with no way to attribute them.

**v3's apiGet cache changes 1 file. If PW fails, the cause is that 1 file.**

#### 5.4 The actual requirement was never "materialized state"

The original problem: 23 concurrent fetches cause 15-30s tab render under parallel PW workers. The requirement: reduce concurrent fetches.

"Materialized state" was a correct architectural solution that required rewriting 38 components. "Frontend response cache" is a simpler solution that requires rewriting 0 components. Both reduce concurrent fetches to the same degree.

**Always solve for the requirement, not the architecture.**

---

### 6. Open questions

1. Should the frontend cache TTL be time-based (60s) or mutation-based (clear on apiPost)?
   **RESOLVED (v3.1): mutation-based is the correctness mechanism** (clear on the mutation response via
   `X-Invalidated-Urls`, §2.3); the 60s TTL is a dev-only staleness cap, never the primary guard. A purely
   time-based cache serves pre-mutation data across a score/verify — see §2.5.

2. Should the backend TabStateCache be removed since the frontend cache handles the PW problem?
   Recommendation: keep it. It's correct, tested, and enables Phase 4 batch optimization.

3. Should the backend batch endpoint (GET /api/{copilot}/tab-state) be used in Phase 4?
   Recommendation: yes, as an optimization. apiGet collects concurrent calls, sends one batch, distributes responses.

4. Should the Purchasing/DataOps/S2P frontends get the same apiGet cache?
   Recommendation: yes, same pattern. 1 file change per copilot.

---

### 7. Verification checklist (what "done" means for the frontend proxy)

Backend gates from v2 (Appendix §7) are unchanged. The **new** frontend proxy needs its own small, decisive
set — all runnable in CI or one PW pass:

- [ ] **Init ordering:** `initStaticUrls(copilot)` is awaited before any copilot screen renders; a unit test
      asserts `STATIC_URLS` is non-empty at first `apiGet`.
- [ ] **Coalescing (the fan-out fix):** N concurrent `apiGet` calls for the same cold STATIC URL produce exactly
      **1** `fetch`. (Unit test with a mocked fetch counter.)
- [ ] **Cache hit:** a second `apiGet` for a warm STATIC URL produces **0** `fetch`.
- [ ] **No-cache-on-failure:** a 500 response is not cached; the next call re-fetches. In-flight entry is cleared
      on rejection.
- [ ] **Canonicalization:** `"/api/x"`, `` `${BASE}/api/x` ``, and `"/api/x?y=1"` resolve to one cache entry.
- [ ] **Invalidation:** after `apiPost` returns `X-Invalidated-Urls`, those entries are gone; the next read
      re-fetches post-mutation data.
- [ ] **DYNAMIC untouched:** a parameterized URL (not in `STATIC_URLS`) is never cached and never coalesced.
- [ ] **PW parity:** full suite ≥ the pre-migration 239-pass / 2-flaky baseline, plus the two P3 specs.
- [ ] **Console purity (C-E):** the proxy emits no `console.error`; recoverable states use `console.debug`.

If all of these pass, the design's promise holds: **panels unchanged, fan-out eliminated, no stale-across-mutation
reads, one source of truth on the backend.**

---

*Tab Data Provider Architecture — v3.1. Supersedes v2 and the v3 draft.*
*v1: rewrite panels, 23 failures. v2: add contracts, 101 failures. v3: proxy the fetch, 0 panel changes.*
*v3.1: same proxy, made correct — coalesced + mutation-invalidated + single-source, with the init-race and*
*normalize/caching bugs fixed. The backend is v2's; the frontend integration is ~1 file that asks the backend*
*for its truth instead of copying it.*

---

## APPENDIX A — Backend reference (retained verbatim from v2)

> **Status: still valid.** v3 keeps the entire v2 **backend** (TabStateCache, version protocol, Wave 1/Wave 2,
> KeySpec + schemas, `@invalidates`/`MUTATION_PATHS`, preseed warm-up, output-equivalence + schema-currency
> tests, memory guards). This appendix is that backend spec, preserved from v2 for implementers.
>
> **What v3 DROPPED from v2 (ignore these parts of the appendix):** the *frontend* rewrite — `TabDataProvider`,
> `useTabData`/`useDerivedData`, the generated frontend TypeScript manifest, and contracts **C-A, C-D, C-F**
> (see §0.5/§0.6 of the main document for the drop rationale). Where the appendix describes the frontend
> provider or panel migration, v3 replaces it with the transparent proxy (§2 of the main document). The
> appendix's **backend** sections — the cache, schemas, invalidation maps, warm-up, and backend gates — are
> what v3 builds on.

*(Section numbers below are v2's own and are scoped to this appendix; they do not continue the v3 numbering above.)*

#### 1. Executive Summary

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

#### 2. Architecture

The backend owns a per-copilot `TabStateCache`. Its registry is a table of **KeySpecs** — the single definition
of a key (v2; replaces v1's loose `{compute, invalidated_by, critical}` dict, which typed nothing).

```python
# v2: one KeySpec IS the key. Name, schema, compute, invalidation, wave, criticality — together, once.
@dataclass(frozen=True)
class KeySpec:
    name: str                       # e.g. "vol-sharpe" — the ONLY place this literal appears (C-A)
    url: str                        # v3.1: the legacy endpoint this key materializes, e.g. "/api/trading/analytics/vol-sharpe"
                                    #       — used by GET /static-urls and X-Invalidated-Urls (main doc §2.2/§2.3)
                                    #       and it is the same URL the output-equivalence test already curls (§2.5.4)
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

#### 2.5 The schema layer (NEW — the spine of v2; build this FIRST despite the section number)

**This section is the reason v2 exists. It is Phase 0 (P0 in §6) and it precedes all migration — do it before §3/§4 work despite coming after them in the numbering.**

##### 2.5.1 One schema per key, two generated faces

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

##### 2.5.2 Validate-on-produce, not validate-on-read

`compute_fn` returns a **validated model instance** (`Model.model_validate(service_output)`). If the service
returns the wrong shape, the failure happens **at recompute time, in one key, with a clear error** — it becomes
that key's `invalidated_error` envelope (C7), never a silently-wrong payload that reaches React and warns across
12 specs (§13.3). The cache stores `model.model_dump()`; the envelope's `data` is therefore *always*
schema-valid or *explicitly* an error. There is no third state.

##### 2.5.3 The projection rule (this is what makes C-C enforceable)

A `compute_fn` may do exactly one of:
1. **Wrap:** `Model.model_validate(service_fn(...))` — return the service result unchanged.
2. **Project:** `Model.model_validate(SELECTORS[name](service_fn(...)))` — apply a **named, tested** selector
   (pure function, its own unit test) that narrows a larger payload to this key's schema.

It may **not** aggregate multiple endpoints, run its own query, or transform inline. The five v1 compute
functions that each grew their own bugs (§13.2: `history_summary`, `accuracy`, `archetypes`,
`counterfactual_default`, `evolution`) were all rule-3 ("arbitrary logic") — which v2 forbids. If a panel needs
data from three endpoints, that is either three keys the panel reads, or one **new service function** (tested
where service functions are tested), never an inline registry aggregation.

##### 2.5.4 The output-equivalence test (C-C, the teeth)

For every STATIC key with a legacy individual endpoint, a generated test asserts:

```
compute_fn()  ==  Model.model_validate( GET /legacy/endpoint )
```

So a compute function *cannot* diverge from the endpoint it replaces without failing a test. This is what turns
"registry entries should call shared read service functions" (a v1 *hope*, v1 §11) into a v1-§13.2-proof
**guarantee**. Keys with no 1:1 legacy endpoint (genuinely new summaries) instead assert against a golden
fixture.

---

#### 3. Design Constraints (v1 C1–C10, preserved; v2 additions marked)

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

#### 4. Components

*(v1 §4.1–4.10 are preserved; only the deltas that fix v1 §13 are restated. Unchanged mechanics are cited, not
repeated.)*

##### 4.1 TabStateCache — concurrency protocol (UNCHANGED from v1; it was correct)

In-memory `{ key: {data, previous_data, error, status, computed_at, version} }`; `register / warm_up / get /
invalidate`; atomic per-key replacement. The **version-race protocol is preserved verbatim** — bump
`key.version`, record `expected_version`, compute outside the swap, discard if `version != expected_version`,
else atomically replace. Latest invalidation wins; a late `score` recompute cannot overwrite a newer `verify`
recompute on overlapping keys. **This is the strongest part of v1 and is not touched.**

*v2 delta:* step 5 ("compute the new value") now includes `Model.model_validate(...)` (C-B); a validation
failure routes to step 8 (`invalidated_error`) exactly like a compute failure.

##### 4.5 TabDataProvider — state machine (UNCHANGED shape; v2 tightens console + identity)

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

##### 4.6 Warm-up ownership (CHANGED — this fixes v1 §13.7)

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

##### 4.7 Key categories & the counterfactual rule (UNCHANGED from v1)

STATIC (no user-selection param, globally materializable) / DYNAMIC (parameterized by selection, stays
individual) / DERIVED (computed from cached STATIC in the provider). The 18 dynamic parameterized endpoint
patterns and the `counterfactual-default` fixed-factor rule (v1 §4.7) are preserved exactly. **Do not migrate
dynamic selected-entity endpoints into tab state** (registry `category` is mandatory; tab-state rejects DYNAMIC
with `status:"dynamic"`).

##### 4.9 Memory budget (UNCHANGED from v1)

Full `/api/history` (~894 KB) is a poor static candidate → cache `history-summary`, not raw history. Per-copilot
budgets 2–6 MB, total 12–20 MB (local/single-user). Warn >1 MB/key, reject-or-summarize >2 MB, log per-copilot
totals. Production multi-worker/multi-tenant moves the same interface to Redis/SQLite.

##### 4.11 KeySpec manifest layering (REPLACES v1 §4.11; this is C-A + C-I)

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

#### 5. Invalidation Maps (UNCHANGED from v1 — preserved verbatim)

The per-copilot Wave 1 / Wave 2 invalidation maps for Trading, Purchasing, DataOps, and S2P (v1 §5.1–5.4) are
correct and carry forward unchanged. Wave 1 = critical/synchronous (≤3 keys, ≤300 ms); Wave 2 = deferred,
below-fold, batched. The `reset` event's large Wave 2 fan-out is expected (it re-materializes the whole tab set
off the hot path). See v1 §5 for the full key lists; v2 changes none of them.

*v2 note:* the "events exceeding 500 ms all-at-once" table (v1 §4.8 — Trading score 9 keys / 900 ms, etc.) is
exactly why Wave 1 caps at 3 keys and Wave 2 defers the rest. No change.

---

#### 6. Migration Strategy (v2 — reordered: schema layer FIRST)

> **⚠️ SUPERSEDED as the active plan.** This is v2's *frontend* migration strategy (panel rewrite). **v3 does
> NOT rewrite panels** — the migration you execute is **main-document §3** (transparent proxy). This subsection
> is retained only to explain what v2 attempted and why §3 replaces it. Its *backend* prerequisites
> (cache, schemas, `@invalidates`, warm-up) remain valid and are folded into §3's P0.

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

#### 7. Testing Strategy (v1 tests preserved; v2 adds the four gates + the missing E2E)

##### 7.1–7.3 Unit / route / frontend tests — UNCHANGED from v1 §10

All v1 unit tests (warm-up, selective invalidation, Wave 1 timing, Wave 2 batching, version races, error
isolation, memory warnings, counterfactual-default, registry/screen coverage) and route/frontend tests carry
forward. They were correct; they were just insufficient. v2 adds four gates and the missing E2E specs.

##### 7.4 The missing end-to-end specs (C-G — closes v1 §13.6)

- **Refreshing:** mutate → immediately GET tab-state → assert a Wave 2 key returns `status:"refreshing"` with
  **previous** data (not null); assert the panel shows previous data + the refresh indicator in the DOM.
- **Invalidated_error:** force a compute failure on an invalidated key → assert `status:"invalidated_error"`,
  `data:null`, panel renders the error state, and **no other key on the tab is affected** (C7).

##### 7.5 GATE 1 — Output-equivalence (C-C; closes v1 §13.2)

Generated per STATIC key with a legacy endpoint: `assert compute_fn() == Model.model_validate(GET legacy)`.
A compute function cannot diverge from the endpoint it replaces. Keys with no legacy 1:1 assert against a golden
fixture. **This is the gate that would have caught the empty promotion panel before it shipped.**

##### 7.6 GATE 2 — Schema currency (C-B; closes v1 §13.1/§13.2)

CI regenerates the TS types from the Pydantic schemas and fails if the committed `.ts` differs. Guarantees the
frontend type and the backend validator are the same shape. Hand-edited generated files fail here.

##### 7.7 GATE 3 — No-bypass-fetch scanner (C-D; closes v1 §13.4)

An AST/static scan: for every component rendered inside a `TabDataProvider`, assert it contains **no**
`fetch`/`apiGet`/`apiPost` call whose URL maps to a **STATIC** key. Flags the "panel is inside the provider but
still fetches independently" failure that silently defeated C1 for 13 v1 panels. (DYNAMIC-key fetches are
allowed and ignored.)

##### 7.8 GATE 4 — Console purity (C-E; closes v1 §13.3)

A Playwright helper asserts zero `console.error` across every migrated tab, **and** a lint rule bans
`console.error` in `provider/` and migrated `panels/`. React warnings are treated as failures (they indicate a
real shape bug, e.g. duplicate keys) — but because C-B/C-C now prevent wrong-shape payloads upstream, this gate
stops *catching* the same bug 12 times and starts *preventing* it once.

---

#### 8. Risks (v1 risks preserved; v2 status)

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

#### 9. Resolved Design Questions (was v1 §13.8 — every one is now answered in the spec)

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

#### 10. What a coding session must do differently this time (the one-paragraph handoff)

**Build §2.5 (the schema spine) and the four gates in §7.5–7.8 BEFORE migrating a single panel.** Then migrate
one key at a time, and never merge a key that is red on C-A (single definition), C-B (schema currency), C-C
(output-equivalence), or C-D (no bypass fetch). v1 failed because it moved computation off the hot path but left
four string-matched seams unguarded, so every mismatch became a silent empty render and a Playwright timeout.
v2's rule is simple: **a key is a typed schema defined once — make the drift a compile error, not a test you
hope someone runs.**

---

*Tab Data Provider Architecture — v2. Supersedes v1. The mechanism is v1's; the contracts are new.*
