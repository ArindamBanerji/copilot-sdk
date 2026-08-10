# JM Judgment History — Executable Implementation Plan v2

**Date:** 2026-08-06  
**Scope:** P-1 through P2 only; Program B migration remains out of scope.  
**Source policy:** This plan is source-verified. No production source files were modified during the scan. Counterfactual semantics are specified in `docs/design/counterfactual_framing_design_v1.md`.

## 1. RMAP Verification Results

| Item | Result | Evidence and consequence |
|---|---|---|
| RMAP-1 | CONFIRMED, with drift | `copilot_sdk/graph/sqlite_store.py:2626-2637` filters `checkpoint_id IS NULL` and orders by `id DESC`; it does not use `created_at`. C1 must change both behaviors. |
| RMAP-2 | CONTRADICTED | `copilot_sdk/graph/memory_store.py:1370-1378` filters only by domain, returns the last legacy list entry, and ignores V2 `_protocol_centroid_checkpoints`. |
| RMAP-3 | CONFIRMED, incomplete | `copilot_sdk/backend/self_computation_router.py:19-51` implements `/api/self/centroid-history`, but line 49 does not pass `include_v2=True`. |
| RMAP-4 | CONFIRMED only for the envelope | `copilot_sdk/backend/models.py:177-180` defines `checkpoints` and `total`; no typed `quality` object exists yet. |
| RMAP-5 | CONFIRMED, incomplete for C3 | Legacy protocol methods are declared at `copilot_sdk/graph/protocol.py:83-102`; V2 `write_centroid_checkpoint` is `:267-281`. Neither includes the six C3 quality fields. |
| RMAP-6 | CONFIRMED | Memory has separate V2 write (`memory_store.py:777-815`), L5 update (`:1182-1205`), legacy save (`:1346-1368`), and history merge (`:1387-1419`). Its startup loader (`:1370-1378`) is not adapter-conformant. |
| RMAP-7 | CONFIRMED | `copilot_sdk/migrate/verify_state.py:247-311` replays decisions in chronological order; `copilot_sdk/migrate/shadow_scorer.py:46-231` provides score, learn, and state comparison. |
| RMAP-8 | CONFIRMED for the legacy route; contradicted for shared mounting | SOC `/api/soc/centroid-evolution` is `../gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:107-171`; 503 is raised at `:161-171`. SOC mounts that router at `main.py:132-142`, not the shared self router. |
| RMAP-9 | CONFIRMED | S2P routes are `../s2p-copilot/backend/app/routers/centroid_router.py:17-62` and are mounted at `../s2p-copilot/backend/app/main.py:247-253`. The shared history route is not mounted. |
| RMAP-10 | CONTRADICTED as a zero-caller assumption | DataOps custom history exists at `apps/dataops/backend/app/context_router.py:1037-1068`; `apps/dataops/frontend/src/api.ts:401-408` calls it and `apps/dataops/backend/tests/test_dataops_backend.py:817-848` asserts its `snapshots` shape. The Panel uses shared history through `api.ts:410-413`. |

### Source facts carried forward from v1

1. Checkpoint timestamps are heterogeneous: AGE legacy writes ISO `created_at` at `../ci-platform/ci_platform/graph/age_graph_store.py:2620-2642`, AGE V2 writes a numeric epoch at `:1356-1420`, SQLite writes numeric epochs at `copilot_sdk/graph/sqlite_store.py:2591-2624` and `:1556-1640`, and Memory mixes ISO (`memory_store.py:1363`) with numeric (`:813`). Therefore C1 cannot safely use a bare cross-adapter `ORDER BY created_at DESC`.
2. The scorer writes full V2 tensors and `factor_names_hash` at `copilot_sdk/scoring/scorer.py:1767-1839`, but startup receives only a tensor at `scorer.py:266-268`; factor-hash validation needs a metadata read seam.
3. DataOps, Trading, and Purchasing mount the shared router at `apps/dataops/backend/app/main.py:749-751`, `apps/trading/backend/app/main.py:439-440`, and `apps/purchasing/backend/app/main.py:707-709`. SOC and S2P require explicit mounts.
4. The gap count is nine, not seven: #6, #7, #9, #10, #11, #13, #15, #16, #17. P0-P2 address #13 and #17; #6, #7, #9, #10, #11, #15, and #16 remain deferred to GAE/Program B conformance.

## 2. Gap Resolutions

### Gap 1 — C1 loader ordering and `created_at` monotonicity

**Evidence.** SQLite filters null IDs and orders by autoincrement `id` (`sqlite_store.py:2626-2637`). AGE orders mixed representations (`age_graph_store.py:2661-2670`). Memory’s loader is append-order only (`memory_store.py:1370-1378`).

**Resolution.** Add canonical numeric `created_at_epoch` to every legacy and V2 checkpoint. Preserve existing `created_at` for API compatibility. Loaders sort by `created_at_epoch DESC`, then a stable timestamp/ID tie-breaker. Backfill SQLite existing rows and add AGE compatibility conversion for existing ISO rows. The authoritative rule is: the most recent checkpoint by `created_at_epoch` wins regardless of `checkpoint_id` being null or non-null.

**Files.** `copilot_sdk/graph/protocol.py:83-102,267-281`; `copilot_sdk/graph/sqlite_store.py:1556-1640,2591-2637`; `copilot_sdk/graph/memory_store.py:777-815,1346-1419`; `../ci-platform/ci_platform/graph/age_graph_store.py:1356-1420,2620-2670`; `copilot_sdk/scoring/scorer.py:1767-1839` only for payload metadata.

**Tests.** Seed one legacy null-ID row at epoch 200 and one V2 non-null row at epoch 100, with insertion order reversed; assert the loader returns the legacy row. Repeat with epochs reversed and assert the V2 row wins.

### Gap 2 — C2 DataOps custom route deletion

**Evidence.** The custom response is implemented at `apps/dataops/backend/app/context_router.py:1037-1068`; API and test callers are at `apps/dataops/frontend/src/api.ts:401-408` and `apps/dataops/backend/tests/test_dataops_backend.py:817-848`. The current timeline already calls shared history at `api.ts:410-413`.

**Resolution.** Migrate `getCentroidHistory` and its tests to the shared envelope. Keep `/api/context/centroid-history` as a compatibility endpoint returning `{checkpoints, total}` for one release. Delete the handler only after repository search finds no active caller and the visual timeline test passes.

**Files/tests.** `api.ts:401-413`, `context_router.py:1037-1068`, `test_dataops_backend.py:817-848`, and any caller found by the P2 search. Assert no active test expects `snapshots` after deletion.

### Gap 3 — C3 counterfactual replay

**Evidence.** V2 checkpoints persist full tensors at `scorer.py:1826-1839`. `ProfileScorer.__init__` accepts `mu` directly at `../graph-attention-engine-v50/gae/profile_scorer.py:156-170` and copies it at `:227-239`; `ProfileScorer.score` accepts a factor vector at `:408-430`. It does not need to load a graph store. The verified-decision method exists as `get_verified_decisions(domain)` in `copilot_sdk/graph/protocol.py:68`, `memory_store.py:1124`, `sqlite_store.py:2222`, and `dual_write_store.py:405`; the endpoint must still confirm adapter ordering/limit semantics in P-1.

**Resolution.** Add `CompoundingScorer.score_with_centroids(centroids: np.ndarray, factors: dict[str, float], category: str) -> ScoreResult` beside `score_read_only` at `copilot_sdk/scoring/scorer.py:404-427`. It prepares the factor vector exactly as `_predict` does (`scorer.py:177-205`), constructs a temporary `ProfileScorer(mu=centroids.copy(), actions=..., categories=...)`, copies the live full DK tensor from `CompoundingScorer.get_dk_weights` (`scorer.py:471-476`) into the temporary `_dk_weights`, copies live temperature from `ProfileScorer.tau` (`../graph-attention-engine-v50/gae/profile_scorer.py:245-250`), and returns a `ScoreResult`. It must not assign to `self._scorer.mu`, call `learn`, or write the store.

Endpoint: `GET /api/self/centroid-history/{checkpoint_id}/counterfactual?window=20`. Response contains `checkpoint_id`, `checkpoint_time`, `decisions_rescored`, `would_change`, `change_rate`, and detail rows with decision ID, original action, alternate action, and `changed`. Window is 1..400. Missing tensor, wrong shape, or factor-hash mismatch returns a typed 409/422 response.

### Gap 4 — C6 atomicity

**Evidence.** AGE already provides `run_transaction` at `../ci-platform/ci_platform/graph/age_graph_store.py:1600-1674`. SOC currently writes L5 state at `../gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:396-437` and Decision delta fields at `../gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2322-2332`.

**Resolution.** Commit to one SOC transaction for Outcome, V2 CentroidCheckpoint, Decision→Outcome, and Decision→SNAPSHOT_AFTER→CentroidCheckpoint. The transaction begins before the first Outcome statement and ends after the final edge. Failure leaves none of those artifacts. Full evidence/conservation cross-artifact atomicity remains Program B.

### Gap 5 — invariant count

**Resolution.** Track nine gaps explicitly. P2 tests #13 rolling accuracy and #17 factor-version consistency. Mark #6, #7, #9, #10, #11, #15, and #16 as deferred; do not report them as P2-complete.

### Gap 6 — pool/PgBouncer

**Evidence.** Pool settings and construction are at `../ci-platform/ci_platform/graph/age_client.py:118-129,182-187`. No PgBouncer configuration was found. The five-copilot bounded calculation is 25 connections at max five per copilot.

**Resolution.** P1 sets `AGE_USE_POOL=true` and `AGE_POOL_MAX_SIZE=5` per AGE deployment and logs pool mode/max. PgBouncer is Program B operations, not P1-blocking.

### Gap 7 — SOC empty history

**Evidence.** The current SOC route raises 503 at `framework_router.py:161-171`.

**Resolution.** Canonical shared route returns HTTP 200 `{checkpoints: [], total: 0}`. Existing `/api/soc/centroid-evolution` remains in `framework_router.py` and returns HTTP 200 `[]` when empty. It is a compatibility projection, not a second canonical data model.

### Gap 8 — read/write-splitting scope

**Evidence.** `CompoundingScorer.from_preset` selects one store and loads it at `scorer.py:250-282`; `CompoundingScorer.__init__` stores one `_graph_store` at `scorer.py:126-150`.

**Resolution.** Store flags belong at each app factory. They select the one store injected into that copilot’s scorer. P1 does not split read/write handles inside the scorer.

### Additional gap 1 — timestamp schema migration

**Resolution.** This is a required C1 subtask, not an implementation detail: add `created_at_epoch` to SQLite schema/migration and AGE/Memory payloads, parse existing ISO strings, and test mixed legacy/V2 rows. A plan that merely changes `ORDER BY created_at` is rejected.

### Additional gap 2 — factor hash needs checkpoint metadata

**Evidence.** Hash is written at `scorer.py:1822-1839`, while startup only gets tensor data at `:266-268`.

**Resolution.** Add `get_latest_centroid_checkpoint(domain: str, include_v2: bool = True) -> dict[str, Any] | None` to `protocol.py:267-281` and all adapters. `from_preset` validates shape and hash before using it; mismatch logs domain/ID and uses bootstrap.

### Additional gap 3 — startup identity

**Resolution.** At `scorer.py:250-282`, log domain, source, checkpoint ID, epoch, shape, and factor hash. Never log the full tensor. Add checkpoint and bootstrap log tests.

## 2b. Review Concern Resolutions

### Concern 1 — exact SOC empty-state alias

**Code evidence.** SOC registers `framework_router.router` with prefix `/api` at `../gen-ai-roi-demo-v4-v50/backend/app/main.py:137-143`; the existing handler is in `framework_router.py:107-171`. The shared router factory currently takes a concrete store at `copilot_sdk/backend/self_computation_router.py:19-27` and mounts `/api/self` at `:180-182`.

**Chosen design.** Keep the legacy handler in `framework_router.py`; mount the shared router separately. The shared router is extended to accept a lazy provider so SOC does not create a second graph connection. The legacy handler continues using its existing Decision query, not checkpoint rows.

```python
# copilot_sdk/backend/self_computation_router.py:19-27,180-182
from collections.abc import Callable

StoreProvider = GraphStore | Callable[[], GraphStore]

def create_self_computation_router(store: StoreProvider) -> APIRouter:
    router = APIRouter(prefix="/api/self", tags=["self-computation"])

    def _gs() -> GraphStore:
        return store() if callable(store) else store

    def _domain() -> str:
        return str(getattr(_gs(), "domain", "") or "")

    @router.get("/centroid-history", response_model=CentroidHistoryResponse)
    def centroid_history(...):
        rows = _gs().get_centroid_checkpoints(
            _domain(), include_v2=True, limit=limit, **active_filters
        )
        return {"checkpoints": [_json_safe(row) for row in rows], "total": len(rows)}

def mount_self_computation_router(app: Any, store: StoreProvider) -> None:
    app.include_router(create_self_computation_router(store))
```

SOC already imports `copilot_sdk` in `graph_schema.py:35,240` and `domains/soc/scorer_adapter.py:12`; therefore direct import is supported. Add after the existing router imports/registration in `main.py:131-143`:

```python
from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from app.services.gae_state import get_profile_scorer

mount_self_computation_router(
    app,
    lambda: get_profile_scorer().graph_store,
)
```

The lambda is evaluated per request and reuses the scorer’s authoritative GraphStore. No proxy and no local duplicate of the shared envelope are introduced.

The compatibility handler remains at `framework_router.py:107-171`:

```python
@router.get("/soc/centroid-evolution")
def get_centroid_evolution(n: int = Query(200, ge=1, le=500), category: Optional[str] = None) -> list[dict[str, Any]]:
    # Keep the existing Decision.centroid_delta_norm query at
    # framework_router.py:129-153. Only its empty branch changes to return [].
    rows = await _get_age_client().run_query(existing_decision_drift_cypher, ...)
    return normalize_decision_drift_rows(rows)
```

When `rows == []`, this returns HTTP 200 `[]`; it never raises the current 503 branch. The canonical SOC response is only `/api/self/centroid-history` and is `{checkpoints, total}`. Thus the two routes deliberately have two sources: Decision drift versus CentroidCheckpoint history.

### Concern 2 — scoped Memory adapter rewrite

The four history methods, not the L5 current-state method, are the required scope. `update_centroid` at `memory_store.py:1182-1205` remains an L5 current-state write and is intentionally not converted into checkpoint history.

| Method | Current behavior | Required behavior | Change estimate | Type |
|---|---|---|---:|---|
| `write_centroid_checkpoint` `memory_store.py:777-815` | Stores V2 in a private dict with numeric `created_at`, but no canonical epoch/quality normalization. | Accepts the protocol’s epoch/quality fields, stores a normalized payload, and rejects conflicting IDs exactly as SQLite/AGE do. | 10–15 lines | Tweak |
| `save_centroids` `memory_store.py:1346-1368` | Appends legacy rows with no explicit `checkpoint_id` and ISO-only `created_at`. | Stores `checkpoint_id=None`, `created_at_epoch`, legacy metadata, and nullable quality fields while preserving warm-start metadata. | 8–12 lines | Tweak |
| `load_latest_centroids` `memory_store.py:1370-1378` | Reads only `_centroid_checkpoints`, uses append order, and ignores V2. | Merges legacy and V2 rows for the domain, chooses max `created_at_epoch`, and returns that tensor. | 18–25 lines | Rewrite |
| `get_centroid_checkpoints` `memory_store.py:1387-1419` | Merges V2 only when requested, applies filters only to legacy rows, and sorts only after V2 extension. | Applies filters to both stores, normalizes fields, sorts one combined list by epoch, and applies limit after sorting. | 20–30 lines | Rewrite |

**Effort.** 0.75–1.0 engineering day including adapter tests. P1 increases from 3–4 days to **4–5 days** because this is a semantic rewrite plus cross-adapter parity, not a one-line tweak.

### Concern 3 — legacy + V2 coexistence ordering test

Add `test_latest_mixed_legacy_v2_epoch_precedence` to the graph conformance suite. It must:

```python
store.save_centroids("demo", "warm_start", legacy_tensor,
                     checkpoint_time="1970-01-01T00:03:20Z")  # epoch 200
store.write_centroid_checkpoint(
    checkpoint_id="v2-old", domain="demo", category="cat", action="act",
    centroids=v2_tensor, decisions_count=1, verified_count=0, iks=0.0,
    shape=[1, 1, 2], factor_names_hash="h",
    created_at_epoch=100,
)
assert np.array_equal(store.load_latest_centroids("demo"), legacy_tensor)
```

Run the inverse epoch ordering too. The assertion is specifically “most recent by `created_at_epoch` wins, regardless of checkpoint ID presence.” Run it on Memory, SQLite, and disposable AGE.

### Concern 4 — SOC/S2P wiring pattern

**Chosen pattern: (a) direct import and mount of the SDK shared router.** Both apps already import the SDK: SOC evidence is `graph_schema.py:35,240` and `domains/soc/scorer_adapter.py:12`; S2P imports shared backend/scoring/factory APIs at `../s2p-copilot/backend/app/main.py:10-16` and uses `create_graph_store` at `:123-133`.

S2P has an authoritative store at `main.py:168-175`. Add:

```python
from copilot_sdk.backend.self_computation_router import mount_self_computation_router

# after app.state.graph_store is assigned, main.py:168-175
mount_self_computation_router(app, app.state.graph_store)
```

Keep S2P’s existing centroid routes at `centroid_router.py:17-62` unchanged as compatibility/cell views. Do not proxy through HTTP and do not reimplement the response model. SOC uses the lazy provider above because its scorer is initialized through `gae_state`; S2P passes its already-created store directly.

### Concern 5 — isolated counterfactual scorer

`ProfileScorer` already accepts `mu` directly at `profile_scorer.py:156-170` and copies it at `:227-239`; it does not load a store. Therefore no constructor change is needed.

Add this exact helper to `CompoundingScorer` beside `score_read_only` (`scorer.py:404-427`):

```python
def score_with_centroids(
    self,
    centroids: np.ndarray,
    factors: dict[str, float],
    category: str,
) -> ScoreResult:
    """Score without mutating or persisting the live scorer."""
    category_index, factor_values, factor_vector, _, _, _, _ = self._predict(factors, category)
    temporary = ProfileScorer(
        mu=np.asarray(centroids, dtype=np.float64).copy(),
        actions=list(self._preset.shape.action_names),
        categories=list(self._preset.shape.category_names),
        eta_override=0.0,
    )
    # Copy live W and τ; do not use ProfileScorer defaults.
    live_dk = self.get_dk_weights()
    if live_dk is not None:
        temporary._dk_weights = np.asarray(live_dk, dtype=np.float64).copy()
    temporary.tau = float(self._scorer.tau)
    result = temporary.score(factor_vector, category_index)
    return ScoreResult(
        decision_id=f"counterfactual-{uuid.uuid4().hex[:12]}",
        action=result.action_name,
        action_index=int(result.action_index),
        confidence=float(result.confidence),
        probabilities=[float(v) for v in result.probabilities],
        category=category,
        factors=factor_values,
    )
```

The P-1 source check confirms the full DK getter at `scorer.py:471-476`, the ProfileScorer `_dk_weights` slot at `profile_scorer.py:301-305`, and temperature `tau` at `profile_scorer.py:245-250`. If a future adapter lacks that state, compute the distance/softmax directly with live W and τ rather than using defaults. The endpoint contract must include `analysis_type: "centroid_ablation"` and `held_fixed: ["dk_weights", "temperature"]`. This is not historical replay. `eta_override=0.0` and no `learn()` ensure no mutation. The endpoint must assert the live scorer tensor and store checkpoint count are unchanged after every request.

## 2c. Additional Gaps Found

### Additional-A — Playwright blast radius

| Spec | Evidence | Required action |
|---|---|---|
| SOC `checklist.spec.ts:1022-1031` | Calls legacy `/api/soc/centroid-evolution`, asserts `resp.ok()` and truthy JSON, not 503 or a strict shape. | No assertion change; preserve legacy array alias. |
| SOC `feature_learning.spec.ts:27-43` | Requires status 200 and array; validates fields only when non-empty. | No change; alias continues returning an array and 200. |
| SOC `feature_model_swap.spec.ts:8-15` | Handles 503 for model-swap, not centroid history. | No change. |
| SOC `feature_factor_proposer.spec.ts:12-20` | Handles 503 for factor-analysis, not centroid history. | No change. |
| DataOps `e2e/dataops/insight.spec.ts:167-182` | Waits for `/api/self/centroid-history` and checks status 200/timeline visibility. | No route change; add quality visibility assertion after C3. |
| SDK `e2e/trading/*` | Existing timeline tests use the shared route/client; no strict 503 history assertion was found in the scan. | No change; run regression. |

The compatibility alias is therefore necessary for SOC’s two strict array consumers, while the shared DataOps route is already the expected route. Add a source scan gate that fails if a test still requires 503 for centroid history.

### Additional-B — warm-start can overwrite learned V2 on the next restart

**Evidence.** Warm-start unconditionally calls `save_centroids(..., "warm_start", ...)` at `copilot_sdk/scoring/scorer.py:1514-1527`. After C1, a newly written warm-start row could become the newest row and displace a learned V2 checkpoint on the next restart.

**Resolution.** Gate the entire warm-start method before mutation. At `copilot_sdk/scoring/scorer.py:1514-1527`, query `get_centroid_checkpoints(self._domain, limit=None, include_v2=True)`. If any row has `category != "warm_start"`, log and return before blending `self._scorer.mu` and before `save_centroids`. `limit=None` is mandatory: a newer stale warm-start must not hide an older learned checkpoint. Only a domain with no learned checkpoint may blend and persist a warm-start row; historical warm-start metadata remains available to `transfer_router.py:181-203`.

**Test.** `test_warm_start_does_not_override_newer_v2`: seed V2 epoch 200, invoke warm-start, assert no new warm-start row is written and `load_latest_centroids` remains the V2 tensor. `test_warm_start_bootstraps_empty_domain`: with no rows, invoke warm-start and assert one warm-start row is written and loaded.

### Additional-C — conservation state is a separate L5 path

**Evidence.** Checkpoint startup load is only at `scorer.py:266-268`. Conservation is persisted/read separately through `copilot_sdk/backend/scoring_router.py:171-177,383-426`; diagnostics reads `get_conservation_state` at `copilot_sdk/backend/diagnostics_models.py:377-396`. S2P also restores L5 runtime state at `../s2p-copilot/backend/app/main.py:16,169-194`.

**Resolution.** C1 changes centroid precedence only; it does not reload or recompute conservation. Add a restart test that changes the selected checkpoint tensor while keeping L5 conservation state fixed and asserts the conservation payload is unchanged. Do not put conservation state into the checkpoint loader in P0-P2.

### Additional-D — quality fields require a frontend change

**Evidence.** The Panel currently renders only drift and IKS (`apps/dataops/frontend/src/components/CentroidTimelinePanel.tsx:102-115`) and `CentroidCheckpoint` has no quality fields (`apps/dataops/frontend/src/types.ts:656-672`).

**Resolution.** Extend `CentroidCheckpoint` with nullable `quality` containing `rollingAccuracy`, `verifiedCount`, `correctCount`, `windowSize`, `source`, and `status`. Add a nullable accuracy series/summary to `CentroidTimelinePanel.tsx:18-24,126-155`; render `No quality data` when legacy quality is null. Add `data-testid="centroid-current-accuracy"` and keep IKS as supporting context, not the headline metric.

**Tests.** Seed one legacy and one C3 checkpoint; assert the component shows the accuracy value for the new row and the explicit no-data label for legacy-only data. Existing drift/IKS test remains.

### Additional-E — conformance must be fixture/disposable-store based, not live-only

**Evidence.** Existing cross-adapter tests are in `tests/graph/test_protocol_v2_conformance.py`, `test_correctness_conformance.py`, `test_domain_required_conformance.py`, and `test_link_domain_conformance.py`; AGE-specific tests are under `../ci-platform/tests/test_age_graph_store.py`, `test_age_graph_store_v.py`, and `test_age_graph_store_topology.py`.

**Resolution.** Put deterministic protocol assertions in SDK conformance tests using Memory and temporary SQLite. Add AGE variants using a disposable test graph in ci-platform. Use live backends only for the five-app HTTP/OpenAPI smoke matrix; never use production graph state as a conformance fixture.

### Additional-F — shared route currently has bounded pagination but not V2 visibility

**Evidence.** `self_computation_router.py:29-51` bounds `limit` to 500 but does not request `include_v2`; this explains an apparently empty/short history even when V2 rows exist.

**Resolution.** Make `include_v2=True` explicit in the shared handler and add a mixed legacy/V2 HTTP test. This is a P0 correctness fix, not a DataOps timeout workaround.

## 3. Phase-by-Phase Implementation Plan

### P-1 — verify and freeze (1 day, no product code)

1. Re-read the protocol and adapter methods at `protocol.py:83-102,267-281`, SQLite `:1556-1640,2591-2637`, Memory `:777-815,1182-1205,1346-1419`, and AGE `:1356-1420,2620-2670`. Freeze the canonical epoch and combined legacy/V2 precedence rule.
2. Confirm router mounts: DataOps `main.py:749-751`, Trading `:439-440`, Purchasing `:707-709`, SOC `main.py:137-143`, S2P `main.py:168-175,247-253`. Confirm direct SDK imports in SOC `graph_schema.py:35,240` and S2P `main.py:10-16`.
3. Search all old URLs and classify the PW callers in Additional-A. Expected result: two SOC strict array consumers, one DataOps shared consumer, no history-specific 503 assertion.
4. Inspect warm-start (`scorer.py:1514-1527`) and conservation (`scoring_router.py:171-177,383-426`) and freeze the rule that warm-start cannot displace an existing non-warm checkpoint and C1 does not alter L5 conservation.
5. Confirm the exact verified-decision read method by searching `copilot_sdk/graph` for `def get_verified`, `def get_decisions`, and `def get_outcome`; tag the selected method `[confirm in P-1]` in the endpoint implementation.
6. Confirm the live ProfileScorer DK-weight and temperature attributes at `../graph-attention-engine-v50/gae/profile_scorer.py:156-239`; do not assume `_dk_weights`, `temperature`, or the getter/setter names in the design helper.
7. Freeze the nine-gap manifest and the `quality:null` legacy contract. Resolve IKS naming before UI labels; IKS remains supporting composite, rolling accuracy is the headline.

**P-1 gate:** every RMAP and concern has a source citation; timestamp, route, provider, warm-start, and quality contracts are written as exact assertions.

### P0 — surfaces and empty states (1–2 days)

1. Extend `CentroidHistoryResponse` at `models.py:177-180` with optional quality fields while retaining `checkpoints` and `total`.
2. Change `self_computation_router.py:19-51` to accept a store/provider and call `include_v2=True`; preserve limit 1..500.
3. Mount the direct shared router in SOC at `main.py:131-143` with `lambda: get_profile_scorer().graph_store`; mount directly in S2P after `main.py:168-175` and before/alongside `:247-253` router registration.
4. Keep the SOC legacy route in `framework_router.py:107-171`, project to an array, and replace empty 503 with 200 `[]`.
5. Migrate DataOps API/tests from `api.ts:401-408` and `test_dataops_backend.py:817-848` to shared shape; retain compatibility route during migration.

**P0 tests/gate:** five OpenAPI paths exist; canonical empty response is exactly `{checkpoints: [], total: 0}`; SOC legacy empty response is exactly `[]`; DataOps timeline receives 200; no centroid-history test requires 503.

### P1 — adapters, precedence, identity, pools, and SOC transaction (4–5 days)

1. Add `created_at_epoch` and metadata access to protocol and all stores. Rewrite the four Memory history methods as scoped in §2b. Backfill SQLite/AGE legacy timestamps.
2. Implement C1 selection over combined legacy+V2 rows. Add factor hash/shape validation and startup identity logging at `scorer.py:250-282`.
3. Add warm-start conditional write at `scorer.py:1514-1527`; preserve historical warm-start metadata for `transfer_router.py:181-203`.
4. Enable AGE pool max five at `age_client.py:118-129,182-187`; log pool settings. PgBouncer remains Program B.
5. Add SOC atomic Outcome/checkpoint writer around `gae_state.py:396-437` and `triage.py:2322-2332` using AGE `run_transaction` (`age_graph_store.py:1600-1674`).
6. Add adapter/conformance tests on Memory, temporary SQLite, and disposable AGE. Do not use live production stores.

**P1 gate:** mixed legacy/V2 precedence, warm-start preservation, hash mismatch fallback, conservation stability, pool bound, and atomic rollback all pass.

### P2 — quality, counterfactuals, lineage, and frontend (1–1.5 weeks)

1. Extend protocol/store checkpoint payloads at `protocol.py:267-281` and adapter write/read points with the six nullable quality fields. Compute `_recent_quality(window=400)` at the write path; legacy quality remains null.
2. Add the centroid-ablation `score_with_centroids` helper at `scorer.py:404-427` and the counterfactual history endpoint. Hold current DK weights and temperature fixed, include `analysis_type="centroid_ablation"` and `held_fixed=["dk_weights","temperature"]`, and assert read-only behavior and deterministic change counts. Do not call this historical replay.
3. Ensure SOC writer creates `SNAPSHOT_AFTER`; test edge creation only. Full traversal/SQLite parity is Program B.
4. Validate factor hash on every checkpoint startup load and expose visible source/identity.
5. Update DataOps types/API/Panel at `types.ts:656-672`, `api.ts:410-413`, and `CentroidTimelinePanel.tsx:18-24,102-155` to display rolling accuracy and explicit legacy no-data.
6. Delete DataOps custom route only after caller search/test migration is clean. Preserve compatibility until that gate.

**P2 gate:** quality is sourced from outcomes, counterfactual replay is isolated, new SOC checkpoints have lineage edges, and the five-app UI/API regression is green.

### STOP

Stop after surface + quality. Do not migrate SQLite history, delete SQLite, perform fleet cutover, add full SNAPSHOT_AFTER traversal, or claim the seven deferred math gaps are complete.

## 4. Test Plan

| Test | Concrete assertion | Store/surface | Phase |
|---|---|---|---|
| `test_history_includes_legacy_and_v2` | Shared response contains both IDs and `total == 2` | SQLite/router | P0 |
| `test_latest_mixed_legacy_v2_epoch_precedence` | Epoch 200 legacy beats epoch 100 V2; inverse ordering reverses winner | Memory/SQLite/AGE | P1 |
| `test_legacy_null_id_is_loadable` | Null-ID legacy row is returned by startup loader | all adapters | P1 |
| `test_memory_v2_and_legacy_history_merge` | Memory `include_v2=True` returns both normalized rows in epoch order | Memory | P1 |
| `test_memory_checkpoint_conflict_is_rejected` | Reusing a checkpoint ID with changed payload raises `ValueError` | Memory | P1 |
| `test_factor_hash_match_loads` | Matching hash and shape select checkpoint tensor | SQLite | P1 |
| `test_factor_hash_mismatch_bootstraps` | Wrong hash selects bootstrap and warning includes domain/ID | SQLite | P1 |
| `test_shape_mismatch_bootstraps` | Wrong tensor shape selects bootstrap | SQLite | P1 |
| `test_startup_identity_log` | Checkpoint and bootstrap paths each emit structured source/identity log | SQLite | P1 |
| `test_warm_start_does_not_override_newer_v2` | Existing V2 remains loaded and no newer warm-start row is written | SQLite/Memory | P1 |
| `test_warm_start_bootstraps_empty_domain` | Empty domain receives one warm-start row and loads it | SQLite/Memory | P1 |
| `test_conservation_unchanged_by_centroid_precedence` | L5 conservation payload is identical before/after checkpoint selection | SQLite | P1 |
| `test_empty_shared_history` | HTTP 200 body is exactly `{'checkpoints': [], 'total': 0}` | shared route | P0 |
| `test_soc_legacy_empty_history` | HTTP 200 body is exactly `[]`, never 503 | SOC | P0 |
| `test_all_apps_mount_shared_history` | OpenAPI contains canonical route in all five apps | five apps | P0 |
| `test_dataops_old_route_compatibility` | Compatibility route returns `{checkpoints,total}`, not `snapshots` | DataOps | P0 |
| `test_soc_legacy_projection_shape` | Non-empty alias rows contain decision number, delta, category, action, drift type | SOC | P0 |
| `test_counterfactual_exact_change_count` | Known tensor/three decisions produce expected `would_change` and rate | SQLite | P2 |
| `test_counterfactual_is_read_only` | Live tensor, checkpoint count, and store writes are unchanged | SQLite | P2 |
| `test_score_with_centroids_does_not_mutate_live_mu` | Live `mu` is byte-equal before/after alternate scoring | SQLite | P2 |
| `test_ablation_identity_zero` | Passing current μ as checkpoint μ yields zero flips and `change_rate == 0.0` | SQLite | P2 |
| `test_ablation_contract_labels_and_fixed_state` | Response has exact `analysis_type` and ordered `held_fixed`; direct score matches current W/τ | SQLite | P2 |
| `test_quality_uses_outcome_counts` | `correct/total` equals last-400 outcome correctness, not verification rate | SQLite | P2/#13 |
| `test_quality_legacy_is_null` | Legacy checkpoint quality is null with explicit legacy status | SQLite/Memory | P2 |
| `test_quality_panel_renders_new_and_legacy_states` | New row shows accuracy; legacy-only state shows no-data label | DataOps frontend | P2 |
| `test_soc_outcome_checkpoint_atomic_failure` | Failure leaves no Outcome, checkpoint, or linking edges | disposable AGE/SOC | P1/P2 |
| `test_soc_snapshot_after_success` | Success creates Decision→SNAPSHOT_AFTER→Checkpoint with matching identity | disposable AGE/SOC | P2 |
| `test_dataops_route_callers_migrated` | Source/test search finds no active custom-route caller before deletion | DataOps | P2 |
| `test_pool_bound` | AGE pool max is five and startup reports pool mode | ci-platform | P1 |
| `test_deferred_invariants_manifest` | IDs 6,7,9,10,11,15,16 are explicitly deferred | SDK manifest | P0 |

**Conformance execution model.** Use existing SDK graph conformance suites at `tests/graph/test_protocol_v2_conformance.py`, `test_correctness_conformance.py`, `test_domain_required_conformance.py`, and `test_link_domain_conformance.py` for Memory/temporary SQLite. Add AGE disposable-graph variants under `../ci-platform/tests/test_age_graph_store.py`, `test_age_graph_store_v.py`, or a dedicated checkpoint conformance file. Live backends run only HTTP/OpenAPI/PW smoke tests; no production graph is used as a fixture.

**PW impact.** `../gen-ai-roi-demo-v4-v50/frontend/tests/e2e/checklist.spec.ts:1022-1031` and `feature_learning.spec.ts:27-43` require the SOC legacy array/200 contract and therefore need no assertion change when the alias is preserved. `e2e/dataops/insight.spec.ts:167-182` already waits on the canonical shared route and needs only the new accuracy assertion in P2. `feature_model_swap.spec.ts:8-15` and `feature_factor_proposer.spec.ts:12-20` handle 503 for unrelated endpoints and need no change.

Tests must use real stores/scorers. The repository testing rules in `CLAUDE.md:Testing Rules` prohibit fake GraphStore, scorer, learn, or outcome implementations.

## 5. Risk Register

| Risk | Severity | Mitigation | Owner |
|---|---|---|---|
| Mixed timestamp representations select the wrong checkpoint | P1 | Canonical numeric epoch, backfill, and reversed-order coexistence test | P1 |
| Memory history rewrite diverges from AGE/SQLite | P1 | Four-method scope, adapter parity tests, disposable AGE comparison | P1 |
| Null-ID legacy rows disappear | P1 | Remove null filter and test legacy/V2 coexistence | P1 |
| Warm-start overwrites learned V2 after restart | P1 | Skip new warm-start when any non-warm checkpoint exists; test both empty/non-empty domains | P1 |
| Factor hash mismatch applies wrong semantics | P1 | Validate hash/shape and visibly bootstrap | P1 |
| SOC shared route creates a second connection or stale store | P0 | Direct SDK import with lazy `get_profile_scorer().graph_store` provider | SOC/P0 |
| SOC legacy clients receive envelope instead of array | P0 | Keep projection in `framework_router.py` and test exact array shape | SOC/P0 |
| DataOps custom route deletion breaks hidden caller | P0/P2 | Compatibility window plus source/test zero-caller gate | DataOps |
| SOC/S2P package import/version drift | P0 | Both already import SDK; add startup/OpenAPI tests before deletion | Cross-repo |
| Counterfactual ablation silently uses default W/τ | P2 | Confirm live attribute names in P-1; copy current W/τ or use direct K/softmax; identity/fixed-state test | SDK |
| Counterfactual result is misrepresented as historical replay | P2 | Contract fields `analysis_type="centroid_ablation"` and `held_fixed=["dk_weights","temperature"]`; approved wording in counterfactual design | SDK/DataOps |
| Quality is confused with verification rate | P2 | Compute only from outcome correctness and render legacy null/no-data | SDK/DataOps |
| Outcome/checkpoint partial persistence | P1 | One AGE transaction and failure rollback test | SOC/ci-platform |
| SNAPSHOT_AFTER exists but has no reader | P2 | Edge creation test only; traversal explicitly Program B | Program B |
| Pool settings safe in test but not deployment | P1 | Startup logging and five-copilot max calculation | ci-platform |
| Seven deferred math gaps are overstated as complete | P0 | Explicit nine-gap manifest and deferred IDs | P0 |

## 6. Dependency Map

```text
P-1 source/route/timestamp/warm-start freeze
  ├── P0 shared model + provider router + SOC/S2P mounts + aliases
  │     └── P1 store precedence + Memory rewrite + hash/identity + warm-start guard
  │           ├── P2 quality schema and frontend
  │           ├── P2 isolated counterfactual scorer
  │           └── P2 SOC atomic writer + SNAPSHOT_AFTER edge
  └── P1 conformance fixtures and pool setup
        └── P2 quality/counterfactual/lineage gates
```

Critical path: protocol/store metadata contract → loader precedence → shared route provider → SOC/S2P mounts → warm-start guard → quality/counterfactual → SOC atomic writer. DataOps deletion is dependent on caller migration but does not block the loader while the compatibility endpoint remains.

## 7. Cross-Repo Coordination

### `copilot-sdk`

Owns `protocol.py`, `models.py`, `self_computation_router.py`, `scorer.py`, `sqlite_store.py`, `memory_store.py`, graph conformance tests, and the isolated counterfactual helper. It defines the canonical response and provider contract.

### `ci-platform`

Owns AGE epoch normalization/history precedence at `age_graph_store.py:1356-1420,2620-2853`, transaction support at `:1600-1674`, pool behavior at `age_client.py:118-129,182-187`, and disposable AGE tests.

### `gen-ai-roi-demo-v4-v50` (SOC)

Owns the direct shared-router mount at `main.py:131-143`, the legacy array projection at `framework_router.py:107-171`, and atomic Outcome/checkpoint persistence at `gae_state.py:396-437` and `triage.py:2322-2332`. SOC depends on the SDK provider contract and ci-platform transaction API.

### `s2p-copilot`

Owns direct shared-router mounting after `main.py:168-175`, preserves `centroid_router.py:17-62`, and adds route/OpenAPI tests. It already imports SDK APIs at `main.py:10-16`.

### DataOps, Trading, Purchasing

DataOps owns the custom-route migration and timeline update at `context_router.py:1037-1068`, `api.ts:401-413`, `types.ts:656-672`, and `CentroidTimelinePanel.tsx:18-155`. Trading/Purchasing need shared-route regression only because they already mount the router at the lines above.

### Independent versus coordinated work

- Independent after P-1: Memory rewrite/tests, DataOps caller migration, Trading/Purchasing route tests, SDK counterfactual helper.
- Coordinated: protocol changes with every adapter; response model with SOC/S2P/DataOps; SOC writer with AGE transaction API; frontend deletion with DataOps backend tests.
- Deferred: SQLite→AGE historical migration, full lineage traversal, cross-copilot backfill, PgBouncer deployment, and seven out-of-scope math gaps.

## Exit Criteria

**Implementation plan v2 ready. 28 planned files across 4 repositories. 30 concrete tests. All 5 review concerns resolved. 6 additional gaps addressed. Estimated effort: 9–11.5 engineering days** (P-1 one day, P0 one to two, P1 four to five, P2 one to one-and-a-half weeks with parallel work). Production source was not modified.
