# S2P learn/score handler performance design v1

Status: design-only review. No implementation is included in this document.

## §1 REQUEST PATH MAP

### `/api/s2p/score`

1. The request enters the S2P domain router at `score_procurement_event` (`s2p-copilot/backend/app/routers/s2p.py:1894-1898`). This is the S2P-specific score path, not the SDK scoring-router path.
2. The handler validates the category and constructs the procurement event (`s2p-copilot/backend/app/routers/s2p.py:1900-1926`). `[AUTH]` Validation must finish before a response can be formed.
3. It loads the fixture invoice, resolves the active variant, resolves graph context, applies the cross-copilot signal, computes all S2P factors, and obtains the SDK scorer (`s2p-copilot/backend/app/routers/s2p.py:1928-1940`). The graph-context lookup is `[AUTH]` for the current response because its result feeds factor computation; the variant and signal are `[DERIVED]` enrichments.
4. It acquires the per-domain mutation lock with `get_mutation_lock("s2p")` (`s2p-copilot/backend/app/routers/s2p.py:1942-1943`; `copilot-sdk/copilot_sdk/scoring/mutation_lock.py:17-31`). `[LOCK]` This serializes the authoritative scorer mutation for the S2P domain.
5. `scorer.score` predicts and writes the governed decision while the mutation lock is held (`s2p-copilot/backend/app/routers/s2p.py:1944-1948`; `copilot-sdk/copilot_sdk/scoring/scorer.py:314-370`). `[AUTH]` The decision write is the authoritative score result.
6. The handler builds the core response, reads the cached conservation status, snapshots centroids, and applies the score invalidation event (`s2p-copilot/backend/app/routers/s2p.py:1951-1974`). The cache read/write is `[CACHE]`; the centroid snapshot and invalidation are `[DERIVED]`/`[CACHE]` work. The conservation cache itself can execute graph counts on a miss while holding `_SCORE_CONSERVATION_STATUS_LOCK` (`s2p-copilot/backend/app/routers/s2p.py:883-898`, `941-968`).
7. The mutation lock is released when the `with` block ends after line 1975 (`s2p-copilot/backend/app/routers/s2p.py:1942-1975`). `[LOCK]`
8. The handler computes auto-approval, novelty, process context, and threshold decisions (`s2p-copilot/backend/app/routers/s2p.py:1976-2001`). These are `[DERIVED]` response enrichments; they are currently inline because their values are returned in the response (`s2p-copilot/backend/app/routers/s2p.py:2022-2032`).
9. It synchronously checks/creates the invoice decision edge (`s2p-copilot/backend/app/routers/s2p.py:2003-2008`). `[AUTH]` for the current S2P graph topology, although it is a candidate for a separately governed side-effect contract if callers do not require the edge before response.
10. Auto-approve recording and score-shadow recording are submitted to the bounded side-effect executor (`s2p-copilot/backend/app/routers/s2p.py:2009-2020`). `[SIDE]` They are not awaited. Completion failures are observed by a callback that logs them (`s2p-copilot/backend/app/routers/s2p.py:109-127`).
11. The response is validated and returned (`s2p-copilot/backend/app/routers/s2p.py:2022-2032`).

### `/api/learn`

1. The request enters `learn_decision` on the S2P SDK-shaped router (`s2p-copilot/backend/app/routers/s2p.py:2090-2092`). It validates the action and reason code, builds context, and obtains the scorer and graph reader (`s2p-copilot/backend/app/routers/s2p.py:2093-2103`). `[AUTH]`
2. It acquires the S2P mutation lock (`s2p-copilot/backend/app/routers/s2p.py:2105`; `copilot-sdk/copilot_sdk/scoring/mutation_lock.py:17-31`). `[LOCK]` All steps through the snapshot preparation are serialized per domain.
3. It reads the decision from the graph reader and reads the pre-update centroid (`s2p-copilot/backend/app/routers/s2p.py:2106-2115`). `[AUTH]` The decision is required input; the centroid is a derived-before snapshot.
4. It captures the pre-outcome conservation snapshot and appends the pre-outcome evidence receipt (`s2p-copilot/backend/app/routers/s2p.py:2116-2127`). `[AUTH]` The S2P contract deliberately places the evidence receipt before the outcome write; the helper raises or uses an outbox fallback when the receipt cannot be persisted (`s2p-copilot/backend/app/routers/s2p.py:1350-1424`).
5. `_learn_with_scorer` reads the decision again, checks the invoice link, derives learning context, and acquires `_GRAPH_LINK_ADVISORY_LOCK` (`s2p-copilot/backend/app/routers/s2p.py:1577-1592`). `[LOCK]` It then temporarily replaces the shared graph-store link method, calls `scorer.learn`, and restores the method in `finally` (`s2p-copilot/backend/app/routers/s2p.py:1592-1635`). This is a process-global monkeypatch guard, not one of the five L5/cache locks.
6. `CompoundingScorer.learn` performs the conflict check, conservation pause gate, profile update, authoritative outcome write, cache invalidation, evidence receipt, DK refresh, optional entity link, IKS, checkpoint/consolidation, reward, periodic evolution, archive, and persistence artifacts (`copilot-sdk/copilot_sdk/scoring/scorer.py:592-833`). `[AUTH]` The pause gate precedes the update (`copilot-sdk/copilot_sdk/scoring/scorer.py:604-685`); the outcome write is authoritative (`copilot-sdk/copilot_sdk/scoring/scorer.py:701-730`). The remaining steps are `[DERIVED]` or `[SIDE]` unless explicitly required by an audit contract.
7. After `scorer.learn` returns, S2P clears score/conservation caches and synchronously persists L5 centroid, conservation, and DK state (`s2p-copilot/backend/app/routers/s2p.py:2135-2150`). `[CACHE]` and `[DERIVED]`; these are major S2P-only handler costs.
8. It applies learn invalidation, invalidates the preview observation, takes the after-conservation snapshot, and copies the payload/decision (`s2p-copilot/backend/app/routers/s2p.py:2151-2155`). `[CACHE]`/`[DERIVED]`; the snapshots feed the audit receipt.
9. The mutation lock is released after line 2155 (`s2p-copilot/backend/app/routers/s2p.py:2105-2155`). `[LOCK]`
10. Outside the mutation lock, S2P records the outcome receipt, updates the supplier profile, records an evolver outcome, and writes an outcome shadow (`s2p-copilot/backend/app/routers/s2p.py:2157-2188`). The receipt is `[AUTH/AUDIT]` for the S2P audit contract; supplier profile, evolver, and shadow are `[SIDE]`/`[DERIVED]`. They are currently inline rather than submitted through `_SIDE_EFFECT_EXECUTOR` (`s2p-copilot/backend/app/routers/s2p.py:123-127`, `2157-2188`).
11. The handler returns the learned payload (`s2p-copilot/backend/app/routers/s2p.py:2189`).

## §2 LOCK ANALYSIS

The five requested locks are declared together (`s2p-copilot/backend/app/routers/s2p.py:67-72`). The per-domain mutation lock is a separate lock and serializes the S2P score/learn/outcome mutation paths (`copilot-sdk/copilot_sdk/scoring/mutation_lock.py:17-45`; `s2p-copilot/backend/app/routers/s2p.py:1942-1948`, `2105-2155`, `2221-2275`).

| Lock | Declared / acquired | Protects | Outside-scope access | Contention / verdict |
|---|---|---|---|---|
| `_SCORE_CONSERVATION_STATUS_LOCK` | Declared at `s2p-copilot/backend/app/routers/s2p.py:68`; acquired by count/status cache paths at `883-898`, `932-939`, `945-968` | TTL status and counts cache dictionaries | `_current_conservation_status` is called by auto-approve, evidence, governance, and other routers, not only by the score/learn mutation block (`s2p-copilot/backend/app/routers/s2p.py:909-924`; `s2p-copilot/backend/app/routers/s2p_auto_approve.py:14`, `62`, `125`; `s2p-copilot/backend/app/routers/s2p_evidence.py:170-178`) | **READER_WRITER.** It can contend with readers and currently holds the lock while a cache miss performs graph counts (`883-898`). Compute outside the lock, then publish an immutable per-domain snapshot with an atomic reference assignment; retain a short per-key single-flight mechanism if duplicate misses are unacceptable. |
| `_SCORE_PROCESS_CONTEXT_LOCK` | Declared at `s2p-copilot/backend/app/routers/s2p.py:69`; acquired at `207-213` | Process-context cache refresh and read | The score route reads/refreshes it after the mutation block (`s2p-copilot/backend/app/routers/s2p.py:1991-1996`); the cache helper is module-level and can be called by any future route | **READER_WRITER.** The lock is not redundant merely because score mutations are serialized: the access is outside the mutation block and the cache refresh can do loader work (`207-213`). Replace the lock with an atomic immutable snapshot plus generation/loader-id comparison where safe. |
| `_L5_CONSERVATION_STATE_LOCK` | Declared at `s2p-copilot/backend/app/routers/s2p.py:70`; acquired only at `595-638` | Read/modify/write of L5 conservation state | Production calls are from `/api/learn` and `/api/outcome`, each inside `get_mutation_lock("s2p")` (`s2p-copilot/backend/app/routers/s2p.py:2135-2145`, `2258-2268`) | **REDUNDANT for same-process router mutation serialization.** The two production call paths cannot overlap under the per-domain mutation lock (`copilot-sdk/copilot_sdk/scoring/mutation_lock.py:28-45`). The RLock does not protect another process or an external AGE writer, so it is not a cross-process correctness mechanism. Preserve database-level atomicity/transactions if the store requires them. |
| `_L5_DK_STATE_LOCK` | Declared at `s2p-copilot/backend/app/routers/s2p.py:71`; acquired at `698-742`; also acquired by tracker replacement at `97-103` | Mutable Welford tracker, DK re-estimation, and DK persistence | Tracker replacement is an explicit path outside the mutation endpoints (`s2p-copilot/backend/app/routers/s2p.py:97-103`); learn/outcome update it under the mutation lock (`s2p-copilot/backend/app/routers/s2p.py:2145-2150`, `2268-2273`) | **NECESSARY / READER_WRITER.** The lock has a real writer outside the request mutation scope. An immutable tracker snapshot or an atomic “replace whole tracker” operation could reduce lock duration, but `update` + `reestimate` + persistence must remain one serialized operation unless the tracker/store API is redesigned. |
| `_L5_CENTROID_STATE_LOCK` | Declared at `s2p-copilot/backend/app/routers/s2p.py:72`; acquired at `641-695`; production calls at `2136-2143` and `2259-2266` | L5 centroid persistence write | No corresponding non-mutation read/write in this module; runtime centroid reads occur before the write and are not protected by this persistence lock (`s2p-copilot/backend/app/routers/s2p.py:2111-2115`, `653-680`) | **REDUNDANT for same-process request writes.** Both production writers are already inside the S2P mutation scope. Removing it is safe only after confirming no external direct caller relies on this Python lock; store-level write atomicity remains required. |

The additional `_GRAPH_LINK_ADVISORY_LOCK` is not one of the five listed locks. It protects a temporary replacement of `scorer.graph_store.link_decision_to_entity` (`s2p-copilot/backend/app/routers/s2p.py:1592-1635`). The architectural fix should remove the monkeypatch and pass an explicit link policy/callback into `scorer.learn`; simply deleting this lock would expose unrelated callers to a process-global temporary method replacement.

## §3 DEFERRED WORK ANALYSIS

| Operation | Category | Current timing | Can defer? | Risk if deferred | Recovery mechanism |
|---|---|---|---|---|---|
| Decision scoring/write | AUTH | Inline under mutation lock (`s2p-copilot/backend/app/routers/s2p.py:1942-1948`; `copilot-sdk/copilot_sdk/scoring/scorer.py:314-370`) | No | Response could reference a decision that is not durable | Existing decision persistence/outbox path in scorer (`copilot-sdk/copilot_sdk/scoring/scorer.py:365-370`, `851-870`) |
| Conservation pause gate | AUTH / safety gate | Inline before profile update (`copilot-sdk/copilot_sdk/scoring/scorer.py:604-685`) | No | A deferred gate could allow learning while conservation is RED | Keep the gate inline; optimize its cached verified-decision/count inputs (`copilot-sdk/copilot_sdk/scoring/scorer.py:619-685`, `2005-2018`) |
| Outcome write | AUTH | Inline after scorer update (`copilot-sdk/copilot_sdk/scoring/scorer.py:701-730`) | No | Learning response would claim an outcome that is not recorded | Existing GraphStore write contract and scorer failure path (`copilot-sdk/copilot_sdk/scoring/scorer.py:722-730`) |
| Pre-outcome evidence receipt | AUTH / audit prerequisite | Inline before outcome (`s2p-copilot/backend/app/routers/s2p.py:2116-2127`) | No | Violates evidence-before-outcome ordering; the tests explicitly inspect that ordering (`s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:101-139`) | Append atomically or enqueue the documented outbox fallback before allowing the outcome (`s2p-copilot/backend/app/routers/s2p.py:1350-1424`; `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:153-219`) |
| Conflict detection / fingerprint read | DERIVED diagnostic | Inline on each non-preseed learn (`copilot-sdk/copilot_sdk/scoring/scorer.py:604-617`, `1724-1765`) | Yes, with a defined freshness policy | `last_conflict` can be stale or absent for one learn | Recompute on demand, on a bounded cadence, or when the verified-decision generation changes; keep the current fingerprint cache invalidation at outcome write (`copilot-sdk/copilot_sdk/scoring/scorer.py:722-730`, `835-849`) |
| IKS before/after | DERIVED and partly response-visible | Inline (`copilot-sdk/copilot_sdk/scoring/scorer.py:686-689`, `748-752`) | Only if the response contract changes | Returned IKS may describe an earlier snapshot | Compute from the authoritative generation and expose the generation in the response, or keep it inline |
| L5 conservation state | DERIVED operational read model | Inline after scorer learn (`s2p-copilot/backend/app/routers/s2p.py:2135-2145`; implementation `595-638`) | Yes | L5 readers may see the previous status/threshold until the worker completes | Durable derived-artifact queue/outbox, startup reconciliation, and an exposed pending/last-updated diagnostic |
| L5 centroid persistence | DERIVED persistence | Inline (`s2p-copilot/backend/app/routers/s2p.py:2136-2143`; implementation `641-695`) | Yes after the in-memory scorer update succeeds | L5 centroid rows lag the live scorer; tests currently expect immediate rows (`s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:395-414`; `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:135-140`) | Durable queue with idempotent `(domain, category, action, decision_id)` key and startup drain |
| L5 DK re-estimation/Welford persistence | DERIVED but affects future scoring | Inline (`s2p-copilot/backend/app/routers/s2p.py:2145-2150`; implementation `698-742`) | Re-estimation can be deferred only if the next score uses a stable snapshot and waits for pending updates | A subsequent score could use stale DK weights; tracker and store can diverge | Keep runtime update in the mutation transaction; queue only the durable projection, or make the next score await the pending generation |
| Fingerprint/conservation/checkpoint persistence | DERIVED artifacts | Scorer persists them inline after update (`copilot-sdk/copilot_sdk/scoring/scorer.py:810-821`, `872-994`) | Yes for persistence, not for safety gates | Fingerprint/checkpoint endpoints can lag; audit exports may be temporarily incomplete | Existing persistence failure/outbox mechanism (`copilot-sdk/copilot_sdk/scoring/scorer.py:851-870`, `1241-1321`, `1767-1856`) plus startup drain |
| Outcome receipt | AUTH / audit | Inline after the mutation lock (`s2p-copilot/backend/app/routers/s2p.py:2157-2171`) | Not without changing the audit response contract | API can return before the hash-chain receipt exists; receipt tests expect it immediately (`s2p-copilot/backend/tests/test_outcome_receipt.py:354-372`, `410-420`) | Durable receipt outbox with explicit `receipt_pending` state, never silent loss |
| Supplier profile, evolver outcome, outcome shadow | SIDE | Inline after the lock (`s2p-copilot/backend/app/routers/s2p.py:2172-2188`) | Yes | Profile/evolution/shadow views can lag or lose an event if no durable queue exists | Submit through the bounded executor only with durable retry/outbox semantics; current executor logs failures but does not provide a retry policy (`s2p-copilot/backend/app/routers/s2p.py:109-127`) |
| Score auto-approve, score shadow | DERIVED/SIDE | Auto-approve/link/enrichments are inline; shadow and auto-approve record are submitted (`s2p-copilot/backend/app/routers/s2p.py:1976-2020`) | Shadow yes; response-visible auto-approve no | Shadow lag is acceptable; response-visible action could change | Keep response enrichments inline; retain executor callback/error logging for side effects (`s2p-copilot/backend/app/routers/s2p.py:109-127`) |

## §4 CROSS-COPILOT BLAST RADIUS

### 4a. SDK-level versus S2P-only

The SDK scoring router owns a generic `/score` and `/learn`, including its own three L5 locks and inline L5 persistence (`copilot-sdk/copilot_sdk/backend/scoring_router.py:60-192`). S2P instead defines a separate `/api/s2p/score` and `/api/learn` with S2P-specific work (`s2p-copilot/backend/app/routers/s2p.py:1894-2032`, `2090-2189`). Therefore Option A and Option B can be S2P-only if they modify only the S2P router; changing `scorer.py` or `scoring_router.py` is SDK-wide.

### 4b. SDK-level change implications

Any change to `CompoundingScorer.learn` changes the shared authoritative update, cache invalidation, fingerprint/IKS, checkpoints, evolution, and archive sequence (`copilot-sdk/copilot_sdk/scoring/scorer.py:582-833`). Any change to the generic scoring router changes the response timing and L5 persistence for every app that mounts it (`copilot-sdk/copilot_sdk/backend/scoring_router.py:96-192`). Mutation-lock semantics are shared per domain (`copilot-sdk/copilot_sdk/scoring/mutation_lock.py:17-45`).

The regression plan for an SDK change must run:

- SDK scorer, conservation, fingerprint, persistence, outbox, and scoring-router tests, including immediate response-shape and L5 assertions (`copilot-sdk/tests/backend/test_scoring_router.py:655-725`, `866-1182`).
- Trading, Purchasing, and DataOps backend learn/score suites, because each mounts `create_scoring_router` directly: Trading (`copilot-sdk/apps/trading/backend/app/main.py:398-406`), Purchasing (`copilot-sdk/apps/purchasing/backend/app/main.py:679-687`), and DataOps (`copilot-sdk/apps/dataops/backend/app/main.py:607-615`).
- One sequential and one concurrent score→learn benchmark per domain, with verified-count, response-shape, and persistence assertions.

### 4c. S2P-only change implications

An S2P-only change is contained to the S2P custom router and S2P backend tests. It need not change the `/api/learn` response shape if it preserves the payload returned at `s2p-copilot/backend/app/routers/s2p.py:2189`. It does change the timing guarantee if derived work is deferred: the response must explicitly define which fields are authoritative at return and which projections may be pending. Existing S2P tests assert immediate L5 writes and immediate receipts (`s2p-copilot/backend/tests/test_l5_conservation_s2p_hook.py:171-210`, `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:341-455`, `s2p-copilot/backend/tests/test_outcome_receipt.py:354-420`).

### 4d–4f. Comparison backends

Trading mounts the SDK scoring router directly and does not add a second S2P-style `/api/learn` wrapper in its application assembly (`copilot-sdk/apps/trading/backend/app/main.py:398-406`). It mounts the generic conservation router separately (`copilot-sdk/apps/trading/backend/app/main.py:431-438`).

Purchasing likewise mounts the SDK scoring router directly (`copilot-sdk/apps/purchasing/backend/app/main.py:679-687`) and mounts the generic conservation router separately (`copilot-sdk/apps/purchasing/backend/app/main.py:699-706`). Its other handlers are application features, not a replacement around the generic learn route (`copilot-sdk/apps/purchasing/backend/app/main.py:632-678`, `714-750`).

DataOps mounts the SDK scoring router directly (`copilot-sdk/apps/dataops/backend/app/main.py:607-615`) and mounts the generic conservation router separately (`copilot-sdk/apps/dataops/backend/app/main.py:620-627`). Its startup assembly contains no S2P-equivalent custom learn wrapper (`copilot-sdk/apps/dataops/backend/app/main.py:616-683`).

This is the principal blast-radius boundary: the other three applications receive the SDK route’s work profile, while S2P adds pre-receipt, graph-link, L5, receipt, supplier, evolver, and shadow work around its own route (`s2p-copilot/backend/app/routers/s2p.py:2105-2189`).

## §5 SCORE VARIANCE ANALYSIS

### 5a. Score locks

The score handler acquires the per-domain mutation lock (`s2p-copilot/backend/app/routers/s2p.py:1942-1948`). It does not call the three L5 persistence functions; those are called from learn/outcome only (`s2p-copilot/backend/app/routers/s2p.py:2136-2150`, `2259-2273`). It does indirectly acquire `_SCORE_CONSERVATION_STATUS_LOCK` through the cached conservation read (`s2p-copilot/backend/app/routers/s2p.py:1962`; `957-968`). It also acquires no `_GRAPH_LINK_ADVISORY_LOCK`; invoice linking occurs after the mutation block (`s2p-copilot/backend/app/routers/s2p.py:2003-2008`).

### 5b. Inline L5 persistence

S2P score has no inline L5 persistence call. S2P learn does: centroid, conservation, and DK persistence all occur before the mutation lock is released (`s2p-copilot/backend/app/routers/s2p.py:2135-2155`). The generic SDK learn route also performs its three L5 persistence calls inline (`copilot-sdk/copilot_sdk/backend/scoring_router.py:157-192`).

### 5c–5d. Variance and cold start

The static path identifies several variable-cost boundaries, but not a single proven timing culprit without a fresh instrumented run:

- Graph context is resolved before scoring (`s2p-copilot/backend/app/routers/s2p.py:1935-1936`).
- The first scorer call can initialize the scorer through a lazy scorer factory in the generic router (`copilot-sdk/copilot_sdk/backend/scoring_router.py:77-94`); S2P obtains its scorer at the score boundary (`s2p-copilot/backend/app/routers/s2p.py:1940`).
- A conservation cache miss performs graph counts while holding the cache lock (`s2p-copilot/backend/app/routers/s2p.py:883-898`, `941-953`).
- The S2P mutation lock serializes score mutations (`s2p-copilot/backend/app/routers/s2p.py:1942-1948`), so a concurrent or queued request can observe the full time of a prior score.
- Invoice-link existence checks and writes are synchronous after the score (`s2p-copilot/backend/app/routers/s2p.py:2003-2008`).

The 8x score variance and cold-start latency should therefore be attributed to a combination of lazy initialization, graph-context/cache misses, serialized mutation, and synchronous graph linking only after a tracing run proves their individual shares. The source supports these candidate boundaries, but source inspection alone cannot assign milliseconds to each one.

### 5e. Warm-up

The generic router lazily initializes its scorer on first request (`copilot-sdk/copilot_sdk/backend/scoring_router.py:77-94`). A safe warm-up would construct the scorer and perform only read-only cache/connection initialization after the graph store is selected, before accepting browser traffic. It must not issue a synthetic score or learn, because those are authoritative mutations (`copilot-sdk/copilot_sdk/scoring/scorer.py:314-370`, `582-730`).

## §6 DESIGN OPTIONS

The latency ranges below are estimates, not measurements. The supplied review input reports a direct SDK learn around 2.4 seconds and slower S2P HTTP learn; the code evidence explains why S2P has additional work, but an implementation benchmark is required before treating any estimate as a guarantee.

### Option A — Remove redundant S2P locks and defer derived persistence

**Description.** Keep the mutation lock, the conservation safety gate, the authoritative outcome write, pre-outcome evidence, and the audit receipt contract. Remove the two L5 locks whose production writers are already inside the mutation scope; refactor cache locks to avoid holding them over graph I/O; keep the DK lock until tracker replacement and update semantics are redesigned. Queue only derived L5/conservation/fingerprint/checkpoint persistence after the authoritative update.

**Changes required.** `s2p-copilot/backend/app/routers/s2p.py:595-742, 883-968, 2135-2155`; a small durable derived-artifact dispatcher/outbox; S2P tests covering immediate authoritative outcomes and eventual L5 convergence. No SDK file is required.

**SDK changes:** NO.

**Expected latency:** Learn approximately approaches the scorer plus mandatory S2P pre-receipt/receipt work; a plausible target is 2.5–3.5 seconds, requiring measurement. Score should be unchanged except for cache-lock and warm-up improvements, plausibly 1–2 seconds after warm-up.

**Risk.** L5 state, fingerprint/checkpoint rows, and operational conservation projections can be stale for the queue interval. The current tests require immediate L5 state (`s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:135-163`) and would need an explicit eventual-consistency assertion. Losing a queued derived artifact without durable retry violates the current persistence-failure pattern (`copilot-sdk/copilot_sdk/scoring/scorer.py:851-870`).

**Rollback.** Feature-flag the deferred dispatcher; if the queue is unhealthy, synchronously drain it and restore inline persistence while retaining the authoritative outcome path.

### Option B — Move all post-learn work to `_SIDE_EFFECT_EXECUTOR`

**Description.** Return after the authoritative outcome and required pre-outcome evidence, submitting L5 persistence, post-outcome receipt, supplier profile, evolution, shadow, and derived artifacts to the existing executor.

**Changes required.** `s2p-copilot/backend/app/routers/s2p.py:2135-2188`; executor job payloads; durable queue/retry state; response fields indicating pending audit/derived work.

**SDK changes:** NO, if the custom S2P route remains the source of truth.

**Expected latency:** Potentially close to scorer learn plus pre-outcome evidence, plausibly 2.5–3 seconds; score is unchanged.

**Risk.** The executor is bounded to four workers and currently logs failures through a done callback (`s2p-copilot/backend/app/routers/s2p.py:65`, `109-127`); it is not itself a durable queue. Returning before the outcome receipt would conflict with receipt tests and audit consumers (`s2p-copilot/backend/tests/test_outcome_receipt.py:354-420`). Stale duration is queue backlog-dependent and unbounded without a recovery SLA.

**Rollback.** Stop accepting deferred jobs, drain/replay durable jobs, then run all required projections inline. This option is unsafe without the durable queue added in the same change.

### Option C — SDK scoring-router post-learn hook

**Description.** Add an explicit post-learn callback/deferred-artifact contract to `create_scoring_router`, rather than making each copilot wrap the route. The SDK route would preserve the mutation and response contract while invoking a typed hook after authoritative learn.

**Changes required.** `copilot-sdk/copilot_sdk/backend/scoring_router.py:60-192`; likely a new hook protocol and tests; S2P would still need to migrate or adapt its custom route because its learn endpoint is not the generic router (`s2p-copilot/backend/app/routers/s2p.py:2090-2189`). All three comparison backends would require compatibility testing at their router mounts (`copilot-sdk/apps/trading/backend/app/main.py:398-406`, `purchasing/backend/app/main.py:679-687`, `dataops/backend/app/main.py:607-615`).

**SDK changes:** YES.

**Expected latency:** Generic learn can approach scorer time plus the hook’s mandatory portion; exact S2P timing depends on migrating its custom pre/post receipt contract. Estimated 2.5–3.5 seconds only after that integration.

**Risk.** Highest blast radius. A hook can accidentally alter all five copilot response timings, ordering, or exception behavior. S2P’s pre-outcome evidence must remain before the SDK outcome write, so a post-learn hook alone cannot replace the existing S2P wrapper.

**Rollback.** Make the hook opt-in and default to the current inline behavior; remove only S2P registration if a cross-copilot regression appears.

### Staleness policy across options

Option A permits bounded staleness for derived operational rows, but not for the outcome, pre-outcome evidence, safety gate, or audit receipt. Option B permits the same staleness plus audit lag and is acceptable only with durable pending status. Option C has the same policy choices but adds SDK-wide compatibility risk. The acceptable policy is “derived state may lag until the durable queue’s recovery SLA; authoritative outcome and audit prerequisites may not.”

## §7 RECOMMENDATION

Recommend **Option A**, implemented in two controlled stages:

1. First, remove only the demonstrably redundant same-process L5 conservation and centroid RLocks, and refactor `_SCORE_CONSERVATION_STATUS_LOCK` so graph/count computation occurs outside the critical section before an atomic cache publication (`s2p-copilot/backend/app/routers/s2p.py:595-695`, `883-968`). Do not remove `_L5_DK_STATE_LOCK` until tracker replacement and update/reestimate semantics are covered by a snapshot design (`s2p-copilot/backend/app/routers/s2p.py:97-103`, `698-742`).
2. Then introduce a durable, idempotent derived-artifact queue for L5 conservation, centroid, DK persistence, fingerprints, and checkpoints. Keep the conservation pause, scorer outcome, pre-outcome evidence, and outcome receipt synchronous until an explicit audit contract says otherwise (`s2p-copilot/backend/app/routers/s2p.py:2116-2127`, `2157-2171`).
3. Remove the temporary graph-store monkeypatch by adding an explicit invoice-link policy to the scorer path; do not delete `_GRAPH_LINK_ADVISORY_LOCK` while the monkeypatch remains (`s2p-copilot/backend/app/routers/s2p.py:1592-1635`).
4. Add read-only startup warm-up for scorer/store/cache initialization, never a synthetic mutation (`copilot-sdk/copilot_sdk/backend/scoring_router.py:77-94`; `copilot-sdk/copilot_sdk/scoring/scorer.py:314-370`).

**Estimated effort:** 3–5 engineering days: one day tracing/lock refactor, two days durable derived queue and replay, one day contract/test updates, and one day cross-copilot performance verification.

**Test plan, in order:**

- Unit-test cache publication and lock behavior, including concurrent readers and reset/invalidation.
- Run S2P authoritative learn/receipt/evidence tests before enabling deferred projections (`s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:101-219`; `test_outcome_receipt.py:354-420`).
- Run L5 tests in both immediate and eventual modes, preserving the existing response shape (`s2p-copilot/backend/tests/test_l5_conservation_s2p_hook.py:171-267`; `test_l5_dk_s2p_hook.py:341-455`; `test_l5_full_flow_s2p.py:73-163`).
- Run generic SDK scoring-router tests and all three backend suites because their applications mount the shared router (`copilot-sdk/tests/backend/test_scoring_router.py:655-725`, `866-1182`; `copilot-sdk/apps/trading/backend/app/main.py:398-406`; `purchasing/backend/app/main.py:679-687`; `dataops/backend/app/main.py:607-615`).
- Run five sequential and four-concurrent score/learn measurements per copilot, then S2P Playwright at one and four workers.

**Verification criteria:**

- HTTP `/api/s2p/score` p95 below 2 seconds after warm-up and HTTP `/api/learn` p95 below 3 seconds under the recorded test load; these are acceptance targets, not source-derived guarantees.
- No loss or reordering of pre-outcome evidence and outcome writes.
- Derived queue has zero unacknowledged failures, idempotent replay, and a visible pending/failed diagnostic.
- S2P Playwright failures eliminated without reducing assertion coverage.
- Trading, Purchasing, DataOps, and SOC tests show zero new failures; SDK tests preserve response shapes and mutation-lock semantics.

## §8 S2P BACKEND TEST IMPACT

### 8a. Tests at risk by change

| Proposed change | Tests at risk | Why |
|---|---|---|
| Remove L5 conservation lock | `s2p-copilot/backend/tests/test_l5_conservation_s2p_hook.py:258-267`; `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:158-163` | One test directly asserts the injected lock wraps read/write; the full-flow test reads the resulting state immediately. |
| Remove L5 centroid lock | `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:395-414`; `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:135-140` | Tests assert immediate centroid rows and response shape. |
| Refactor conservation cache locking | `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:226-317`, especially the cache-expiry and concurrent coalescing tests | These tests assert cache reuse, expiry, and single/coalesced count behavior. |
| Defer derived L5 persistence | `s2p-copilot/backend/tests/test_l5_conservation_s2p_hook.py:171-210`; `test_l5_dk_s2p_hook.py:341-455`; `test_l5_full_flow_s2p.py:73-163` | They currently inspect L5 state immediately after the HTTP response. |
| Defer receipts or alter ordering | `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:101-219`, `257-362`; `test_outcome_receipt.py:354-420`, `466-528` | They assert pre-outcome ordering, outbox fallback, receipt chain, and before/after conservation fields. |
| Add a generic SDK hook | `copilot-sdk/tests/backend/test_scoring_router.py:655-725`, `866-1182` and every backend suite mounting the router | It changes shared `/learn` timing/order and can affect all copilot payloads. |

### 8b. Timing assertions

The inspected source/test inventory contains response and concurrency assertions, but no source evidence of a production latency assertion in the S2P backend tests. The key concurrency tests are `test_s2p_score_endpoint.py:135-150`, `260-317` and `copilot-sdk/tests/backend/test_scoring_router.py:1214-1277`; the new design should add explicit p50/p95 timing benchmarks rather than rely on browser timeout failures.

### 8c. Immediate conservation state

Yes. S2P’s full-flow test reads conservation state after a sequence of learns (`s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:158-163`). The S2P conservation-hook test also reads and validates the state after `/api/s2p/outcome` (`s2p-copilot/backend/tests/test_l5_conservation_s2p_hook.py:171-210`). Deferral requires polling/eventual-consistency assertions or a synchronous “authoritative state committed” field.

### 8d. Immediate centroid state

Yes. The S2P DK/centroid tests assert a centroid update immediately after `/api/learn` (`s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:395-414`) and the full-flow test reads persisted centroids and their causal decision id (`s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:115-140`).

### 8e. Learn-path test files

The primary S2P learn-path files are:

- `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:679-887` — SDK-shaped `/api/learn`, variant/evolver, accumulator, and reward paths.
- `s2p-copilot/backend/tests/test_learn_conservation_guard.py:69-139` — pause/guard behavior.
- `s2p-copilot/backend/tests/test_evidence_receipt_wiring.py:101-219`, `257-362` — evidence ordering and fallback.
- `s2p-copilot/backend/tests/test_outcome_receipt.py:354-620` — receipt creation, chain, conservation snapshots, and paused outcomes.
- `s2p-copilot/backend/tests/test_l5_conservation_s2p_hook.py:171-267` — L5 conservation.
- `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:207-455` — L5 DK and centroid endpoint hooks.
- `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:52-163` — end-to-end score/learn/L5 state flow.
- `s2p-copilot/backend/tests/test_s2p_active_age_live.py` and `test_s2p_active_age_parallel.py` — AGE-backed mutation/concurrency coverage; the file names and test scope are part of the S2P backend test inventory.

## VERDICT

**Option A — remove only redundant same-process L5 locks, move derived persistence behind a durable idempotent queue, retain authoritative gates/writes/receipts inline, and replace the graph-link monkeypatch before removing its advisory lock.** This is the smallest S2P-contained change that addresses the handler-only overhead without changing the shared SDK contract.

**SDK IMPACT:** NO for the first implementation; SDK changes should be deferred to a separately reviewed hook design because S2P does not currently use the generic learn handler.

**ESTIMATED EFFORT:** 3–5 engineering days.

**IMPLEMENTATION BLOCKED ON:** A fresh trace separating graph-context, cache-miss, invoice-link, pre-receipt, scorer, and L5 persistence time; an explicit audit decision on whether post-outcome receipts may ever be pending; and a durable queue/replay design before any work is moved off the request path.

READY: YES (design complete)
