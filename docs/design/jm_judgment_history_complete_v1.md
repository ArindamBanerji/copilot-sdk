# Judgment History Surface — Complete Design and Implementation Plan v1

**Date:** 2026-08-06  
**Scope:** P-1 through P2. Program B migration, fleet cutover, full lineage traversal, and cross-artifact atomicity remain deferred.  
**Status:** Implementation-ready after the P-1 confirmation gate.  
**Production source modified:** No.

This document consolidates:

1. `jm_judgment_history_surface_v6.md`
2. `jm_judgment_history_implementation_plan_v2.md`
3. `counterfactual_framing_design_v1.md`

## 1. Objective and stop line

Provide one credible centroid-history surface across SOC, S2P, Trading, Purchasing, and DataOps, with an explicit rolling-accuracy quality axis and an honest centroid-ablation analysis.

Stop after P2. Do not delete SQLite, migrate the fleet to AGE, backfill complete historical lineage, or claim point-in-time replay.

## 2. Verified architecture

### 2.1 Current store and route behavior

| Area | Current evidence | Consequence |
|---|---|---|
| SQLite startup loader | `copilot_sdk/graph/sqlite_store.py:2626-2637` filters `checkpoint_id IS NULL`, orders by `id DESC` | Learned V2 checkpoints are hidden. |
| Memory startup loader | `copilot_sdk/graph/memory_store.py:1370-1378` reads only legacy append order | Memory ignores V2 startup checkpoints. |
| Shared history route | `copilot_sdk/backend/self_computation_router.py:19-51` exposes `/api/self/centroid-history` but does not pass `include_v2=True` | Shared history can omit learned checkpoints. |
| Response model | `copilot_sdk/backend/models.py:177-180` has `checkpoints` and `total` only | Quality must be added compatibly. |
| SOC legacy route | `../gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:107-171`; Decision query at `:129-153` | Keep it as Decision drift, not checkpoint history. |
| S2P routes | `../s2p-copilot/backend/app/routers/centroid_router.py:17-62`; mounted at `main.py:247-253` | Add canonical shared route while preserving explorer routes. |
| DataOps custom route | `apps/dataops/backend/app/context_router.py:1037-1068`; caller `apps/dataops/frontend/src/api.ts:401-408`; tests `apps/dataops/backend/tests/test_dataops_backend.py:817-848` | Migrate callers before deletion. |

### 2.2 Timestamp contract

Checkpoint timestamps are heterogeneous:

- AGE legacy writes ISO timestamps at `../ci-platform/ci_platform/graph/age_graph_store.py:2620-2642`.
- AGE V2 writes numeric timestamps at `:1356-1420`.
- SQLite writes numeric timestamps at `copilot_sdk/graph/sqlite_store.py:2591-2624` and `:1556-1640`.
- Memory mixes ISO legacy timestamps at `memory_store.py:1363` and numeric V2 timestamps at `:813`.

Therefore, a bare `ORDER BY created_at DESC` is not the cross-adapter contract. The implementation adds numeric `created_at_epoch` and selects the greatest epoch regardless of `checkpoint_id`.

### 2.3 Checkpoint metadata

The scorer writes full V2 tensors and `factor_names_hash` at `copilot_sdk/scoring/scorer.py:1767-1839`. Startup currently loads only a tensor at `scorer.py:250-282`, so metadata validation and identity logging require a metadata reader.

`ProfileScorer` accepts injected `mu` at `../graph-attention-engine-v50/gae/profile_scorer.py:156-170`, copies it at `:227-239`, uses DK weights in `_dk_weights` at `:301-305`, and uses temperature `tau` at `:245-250`.

The verified-decision method exists as `get_verified_decisions(domain)` in:

- `copilot_sdk/graph/protocol.py:68`
- `copilot_sdk/graph/memory_store.py:1124`
- `copilot_sdk/graph/sqlite_store.py:2222`
- `copilot_sdk/graph/dual_write_store.py:405`

## 3. Canonical route and compatibility contract

### 3.1 Canonical route

`GET /api/self/centroid-history`

The shared handler at `copilot_sdk/backend/self_computation_router.py:19-51` must:

1. Accept either a concrete `GraphStore` or lazy `Callable[[], GraphStore]` provider.
2. Call `get_centroid_checkpoints(domain, include_v2=True, limit=N, ...)`.
3. Return the canonical envelope:

```json
{
  "checkpoints": [],
  "total": 0
}
```

Legacy checkpoints expose `quality: null`; new checkpoints expose the typed quality object described in §5.

### 3.2 SOC compatibility route

Keep `/api/soc/centroid-evolution` in `../gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:107-171`.

It remains a projection of the existing Decision query at `framework_router.py:129-153`, reading `Decision.centroid_delta_norm`. It must not read checkpoint rows. The only P0 behavior change is:

- Empty Decision result → HTTP 200 with `[]`.
- Non-empty result → existing array projection.

The canonical `/api/self/centroid-history` route is mounted separately and reads `CentroidCheckpoint` rows.

### 3.3 S2P compatibility routes

Preserve the existing S2P routes at `../s2p-copilot/backend/app/routers/centroid_router.py:17-62`:

- `/api/s2p/centroid/all`
- `/api/s2p/centroid/explain/{decision_id}`
- `/api/s2p/centroid/drift/{category}/{action}`
- `/api/s2p/centroid/{category}/{action}`

Add `/api/self/centroid-history` beside them; do not replace cell/explorer semantics with the history envelope.

### 3.4 Wiring pattern

Both apps already import the SDK:

- SOC: `../gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:35,240`, `domains/soc/scorer_adapter.py:12`.
- S2P: `../s2p-copilot/backend/app/main.py:10-16`.

Use direct SDK import and mount, not a proxy or local reimplementation.

SOC mount at `main.py:131-143`:

```python
from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from app.services.gae_state import get_profile_scorer

mount_self_computation_router(
    app,
    lambda: get_profile_scorer().graph_store,
)
```

The lazy provider reuses the authoritative scorer store and avoids a second graph connection.

S2P store creation is at `../s2p-copilot/backend/app/main.py:123-146`, assignment at `:168-175`:

```python
from copilot_sdk.backend.self_computation_router import mount_self_computation_router

mount_self_computation_router(app, app.state.graph_store)
```

## 4. Checkpoint precedence and warm-start safety

### 4.1 Loader rule

Add `created_at_epoch` to legacy and V2 checkpoint payloads at:

- `copilot_sdk/graph/protocol.py:83-102,267-281`
- `copilot_sdk/graph/sqlite_store.py:1556-1640,2591-2637`
- `copilot_sdk/graph/memory_store.py:777-815,1346-1419`
- `../ci-platform/ci_platform/graph/age_graph_store.py:1356-1420,2620-2670`

Selection rule:

> The checkpoint with the greatest `created_at_epoch` wins, regardless of whether `checkpoint_id` is null or non-null.

Backfill existing SQLite and AGE timestamps. Preserve existing `created_at` for API compatibility.

### 4.2 Warm-start guard

Warm-start currently saves unconditionally at `copilot_sdk/scoring/scorer.py:1514-1527`. The guard must cover the entire method, before centroid mutation:

```python
existing = self._graph_store.get_centroid_checkpoints(
    self._domain,
    limit=None,
    include_v2=True,
)
if existing and any(c.get("category") != "warm_start" for c in existing):
    logger.info("Skipping warm-start: learned checkpoint exists")
    return

self._scorer.mu = blend(source_centroids, self._scorer.mu, ...)
self._graph_store.save_centroids(...)
```

`limit=None` is mandatory. A newer stale warm-start must not hide an older learned checkpoint. Existing warm-start metadata remains available to the transfer router at `copilot_sdk/backend/transfer_router.py:181-203`.

## 5. Quality axis

New checkpoints add nullable fields through:

- Protocol: `copilot_sdk/graph/protocol.py:267-281`
- Scorer writer: `copilot_sdk/scoring/scorer.py:1767-1839`
- AGE writer/read: `../ci-platform/ci_platform/graph/age_graph_store.py:1356-1420,2834-2853`
- SQLite writer/schema: `copilot_sdk/graph/sqlite_store.py:1556-1640`
- Memory writer/read: `copilot_sdk/graph/memory_store.py:777-815,1387-1419`
- Response model: `copilot_sdk/backend/models.py:177-180`

Quality fields:

```json
{
  "quality_window_size": 400,
  "quality_verified_count": 120,
  "quality_correct_count": 112,
  "rolling_accuracy": 0.9333,
  "quality_window_end": "...",
  "quality_policy_version": "quality.v1",
  "source": "outcome_store"
}
```

Legacy checkpoints return `quality: null`; no quality is fabricated from verification rate. The headline metric is rolling accuracy `correct / verified` over the last 400 outcomes. IKS remains supporting context.

## 6. Counterfactual design — centroid ablation

### 6.1 Decision and honest claim

Ship Option A: centroid ablation. It compares latest μ with checkpoint-k μ while holding today’s kernel weights W and temperature τ fixed.

Honest claim:

> Rolling centroids back to checkpoint k, with today’s kernel and temperature held fixed, would change action on X% of recent verified decisions.

This is not a reconstruction of scorer state at checkpoint k. Checkpoints do not store historical DK weights or temperature.

### 6.2 Semantics

For each decision with factors `f` and category `c`:

```text
baseline       = score(f, c | μ=latest, W=current, τ=current)
counterfactual = score(f, c | μ=checkpoint_k, W=current, τ=current)
changed        = baseline.action != counterfactual.action
change_rate    = changed_count / rescored_count
```

The only variable is μ.

### 6.3 Helper

Add beside `score_read_only` at `copilot_sdk/scoring/scorer.py:404-427`:

```python
def score_with_centroids(
    self,
    centroids: np.ndarray,
    factors: dict[str, float],
    category: str,
) -> ScoreResult:
    """Centroid ablation using live W and tau; never persists or learns."""
    category_index, factor_values, factor_vector, *_ = self._predict(factors, category)
    temporary = ProfileScorer(
        mu=np.asarray(centroids, dtype=np.float64).copy(),
        actions=list(self._preset.shape.action_names),
        categories=list(self._preset.shape.category_names),
        eta_override=0.0,
    )
    live_dk = self.get_dk_weights()
    if live_dk is not None:
        temporary._dk_weights = np.asarray(live_dk, dtype=np.float64).copy()
    temporary.tau = float(self._scorer.tau)
    result = temporary.score(factor_vector, category_index)
    return ScoreResult(
        decision_id=f"cf-{uuid.uuid4().hex[:12]}",
        action=result.action_name,
        action_index=int(result.action_index),
        confidence=float(result.confidence),
        probabilities=[float(v) for v in result.probabilities],
        category=category,
        factors=factor_values,
    )
```

The live DK getter is `CompoundingScorer.get_dk_weights` at `scorer.py:471-476`; live temperature is `ProfileScorer.tau` at `profile_scorer.py:245-250`. No assignment to `self._scorer.mu`, no `learn()`, and no store write is permitted.

### 6.4 Endpoint

`GET /api/self/centroid-history/{checkpoint_id}/counterfactual?window=20`

Response contract:

```json
{
  "checkpoint_id": "s2p:checkpoint:abc",
  "checkpoint_time": "2026-08-06T12:00:00Z",
  "analysis_type": "centroid_ablation",
  "held_fixed": ["dk_weights", "temperature"],
  "decisions_rescored": 20,
  "would_change": 3,
  "change_rate": 0.15,
  "details": [
    {
      "decision_id": "d-1",
      "original_action": "hold_for_review",
      "counterfactual_action": "auto_approve",
      "changed": true
    }
  ]
}
```

`analysis_type` and `held_fixed` are contract fields. They prevent downstream claims from becoming “historical replay.” Window is bounded to 1..400. Missing checkpoint, missing factors, incompatible shape, and hash mismatch return typed errors.

### 6.5 Algorithm

1. Load checkpoint metadata and full tensor.
2. Validate domain, shape, factor hash, finite values, and bounds.
3. Load the most recent verified decisions through `get_verified_decisions(domain)` (`protocol.py:68`; adapter implementations at `memory_store.py:1124`, `sqlite_store.py:2222`, `dual_write_store.py:405`). Confirm ordering/limit semantics in P-1.
4. Score baseline and counterfactual for every row using the isolated helper.
5. Aggregate flips. With no rows, return `decisions_rescored=0`, `would_change=0`, `change_rate=null`, `status="no_verified_decisions"`.
6. Return the fixed labels and details without persistence.

### 6.6 Counterfactual tests

1. `test_ablation_identity_zero`: current μ as checkpoint μ → zero flips and rate 0.0.
2. `test_ablation_flip_count`: exactly two of three decisions flip → count 2 and rate 2/3.
3. `test_ablation_contract_labels`: exact `analysis_type` and `held_fixed` fields.
4. `test_ablation_holds_live_kernel_and_temperature`: result matches direct calculation using current W/τ, not defaults.
5. `test_ablation_is_read_only`: live μ, DK state, checkpoint count, and decision count unchanged.
6. `test_ablation_rejects_hash_or_shape_mismatch`: typed 409/422 and no scoring.
7. `test_ablation_window_bound`: 0 and 401 rejected; 20 caps rows.
8. `test_ablation_no_verified_decisions`: null rate and explicit no-data status.

### 6.7 Option B hook

Point-in-time replay is deferred. A future version may store `{μ, W, τ, factor_schema}` per checkpoint and introduce a versioned analysis type. It must not silently change the semantics of centroid ablation.

## 7. Phase plan

### P-1 — Verify and freeze, one day

1. Confirm all RMAP items against protocol, SQLite, Memory, AGE, routes, models, and replay helpers at the cited locations.
2. Confirm `get_verified_decisions` ordering and limit semantics.
3. Confirm `ProfileScorer._dk_weights`, `ProfileScorer.tau`, and `CompoundingScorer.get_dk_weights`.
4. Freeze `created_at_epoch`, combined legacy/V2 precedence, `quality:null`, SOC Decision drift semantics, and counterfactual contract fields.
5. Freeze nine invariant gaps: #13 and #17 in P0-P2; #6, #7, #9, #10, #11, #15, #16 deferred.

**Gate:** no unresolved RMAP contradiction; exact verified-decision and scorer-state methods confirmed.

### P0 — Surface normalization, one to two days

1. Extend `CentroidHistoryResponse` at `copilot_sdk/backend/models.py:177-180`.
2. Make `self_computation_router.py:19-51` provider-aware and pass `include_v2=True`.
3. Mount canonical route in SOC at `main.py:131-143` and S2P after store creation at `main.py:168-175`.
4. Preserve SOC Decision alias at `framework_router.py:107-171`; change empty response from 503 to 200 `[]`.
5. Migrate DataOps route callers/tests at `api.ts:401-413` and `test_dataops_backend.py:817-848`; retain compatibility route during migration.

**Gate:** five canonical OpenAPI routes, prescribed empty responses, no centroid-history 503 requirement.

### P1 — Store foundation, four to five days

1. Add epoch fields and metadata reads to protocol and adapters at §4 locations.
2. Rewrite Memory’s four history methods:
   - `write_centroid_checkpoint` `memory_store.py:777-815`: 10–15 lines, tweak.
   - `save_centroids` `:1346-1368`: 8–12 lines, tweak.
   - `load_latest_centroids` `:1370-1378`: 18–25 lines, rewrite.
   - `get_centroid_checkpoints` `:1387-1419`: 20–30 lines, rewrite.
3. Add hash/shape validation and startup identity logging at `scorer.py:250-282`.
4. Add the full-method warm-start guard at `scorer.py:1514-1527`.
5. Enable bounded AGE pool at `age_client.py:118-129,182-187`; PgBouncer remains Program B.
6. Add SOC outcome/checkpoint transaction using `run_transaction` at `age_graph_store.py:1600-1674`, wired around `gae_state.py:396-437` and `triage.py:2322-2332`.

**Gate:** mixed legacy/V2 precedence, warm-start preservation, hash fallback, conservation stability, pool bound, and atomic rollback pass.

### P2 — Quality, ablation, lineage, and UI, one to one-and-a-half weeks

1. Add quality fields across protocol/store/writer/response locations in §5.
2. Add isolated `score_with_centroids` and the centroid-ablation endpoint.
3. Add SOC `SNAPSHOT_AFTER` edge creation; defer traversal and parity to Program B.
4. Validate factor hash on every startup load.
5. Update DataOps types/API/Panel at `types.ts:656-672`, `api.ts:410-413`, and `CentroidTimelinePanel.tsx:18-24,102-155`; render accuracy and explicit legacy no-data.
6. Delete DataOps custom route only after zero-caller search and visual snapshot.

**Gate:** outcome-backed quality, ablation identity/fixed-state tests, lineage edge creation, and five-copilot UI/API regression pass.

## 8. Test plan and conformance

### Adapter and loader tests

| Test | Assertion | Store |
|---|---|---|
| `test_history_includes_legacy_and_v2` | Both IDs present; total is 2 | SQLite |
| `test_latest_mixed_legacy_v2_epoch_precedence` | Greatest epoch wins in both insertion orders | Memory/SQLite/disposable AGE |
| `test_legacy_null_id_is_loadable` | Null-ID legacy row loads | all adapters |
| `test_memory_v2_and_legacy_history_merge` | Combined sorted history contains both rows | Memory |
| `test_memory_checkpoint_conflict_is_rejected` | Conflicting ID raises `ValueError` | Memory |
| `test_factor_hash_match_loads` | Matching hash selects checkpoint | SQLite |
| `test_factor_hash_mismatch_bootstraps` | Wrong hash selects bootstrap and logs identity | SQLite |
| `test_shape_mismatch_bootstraps` | Wrong shape selects bootstrap | SQLite |
| `test_startup_identity_log` | Checkpoint/bootstrap source record emitted | SQLite |
| `test_warm_start_does_not_override_newer_v2` | No mutation and no new warm row when learned row exists | Memory/SQLite |
| `test_warm_start_bootstraps_empty_domain` | Empty domain receives and loads warm-start row | Memory/SQLite |
| `test_conservation_unchanged_by_centroid_precedence` | L5 conservation unchanged by C1 | SQLite |

### Route and UI tests

| Test | Assertion |
|---|---|
| `test_empty_shared_history` | HTTP 200 `{checkpoints: [], total: 0}` |
| `test_soc_legacy_empty_history` | HTTP 200 `[]`, never 503 |
| `test_all_apps_mount_shared_history` | Canonical route in five OpenAPI documents |
| `test_dataops_old_route_compatibility` | Compatibility route returns shared envelope |
| `test_soc_legacy_projection_shape` | Decision-derived array contains delta/category/action fields |
| `test_quality_panel_renders_new_and_legacy_states` | Accuracy appears for new checkpoint; no-data for legacy |

### Counterfactual tests

Use the eight tests in §6.6. The load-bearing test is `test_ablation_identity_zero`.

### Transaction and operations tests

| Test | Assertion |
|---|---|
| `test_soc_outcome_checkpoint_atomic_failure` | Failed transaction leaves no Outcome/checkpoint/edges |
| `test_soc_snapshot_after_success` | Matching Decision→SNAPSHOT_AFTER→Checkpoint edge exists |
| `test_pool_bound` | AGE max pool is five and mode is logged |
| `test_dataops_route_callers_migrated` | No active custom-route callers before deletion |
| `test_deferred_invariants_manifest` | Seven deferred IDs explicitly listed |

Run deterministic protocol tests from:

- `tests/graph/test_protocol_v2_conformance.py`
- `tests/graph/test_correctness_conformance.py`
- `tests/graph/test_domain_required_conformance.py`
- `tests/graph/test_link_domain_conformance.py`

Use temporary SQLite and Memory for SDK tests, disposable AGE graphs for ci-platform tests (`../ci-platform/tests/test_age_graph_store.py`, `test_age_graph_store_v.py`, and topology tests), and live backends only for HTTP/OpenAPI/Playwright smoke. Never use production graph state as a conformance fixture.

## 9. Playwright blast radius

- SOC `checklist.spec.ts:1022-1031`: no change; legacy alias remains 200 array.
- SOC `feature_learning.spec.ts:27-43`: no change; expects 200 array and optional fields.
- SOC `feature_model_swap.spec.ts:8-15`: no change; its 503 is for model swap.
- SOC `feature_factor_proposer.spec.ts:12-20`: no change; its 503 is for factor analysis.
- DataOps `e2e/dataops/insight.spec.ts:167-182`: canonical route already expected; add quality assertion in P2.

Add a source scan that fails if any centroid-history test requires 503.

## 10. Risks and mitigations

| Risk | Severity | Mitigation | Evidence |
|---|---|---|---|
| Mixed timestamp ordering | P1 | `created_at_epoch`, backfill, coexistence test | AGE `:1356-1420,2620-2670`; SQLite `:2591-2637` |
| Memory divergence | P1 | Four-method rewrite and adapter parity | `memory_store.py:777-815,1346-1419` |
| Warm-start overwrites learned state | P1 | Early return before blend/save, `limit=None` | `scorer.py:1514-1527` |
| Wrong factor schema | P1 | Hash/shape validation and visible bootstrap | `scorer.py:1822-1839`, `:250-282` |
| SOC stale/zero drift alias | P0 | Keep Decision query; only empty branch changes | `framework_router.py:129-153,161-171` |
| SOC duplicate graph connection | P0 | Lazy scorer-store provider | SOC `main.py:131-143`; SDK router `:19-27` |
| Counterfactual uses default W/τ | P2 | Copy live `_dk_weights` and `tau`; fixed-state test | ProfileScorer `:245-305`; scorer `:471-476` |
| Counterfactual overstated as replay | P2 | Contract fields and approved wording | This document §6; counterfactual design |
| Quality mistaken for verification rate | P2 | Outcome-backed `correct/verified`; legacy null | checkpoint schema/write locations §5 |
| Partial SOC persistence | P1 | One AGE transaction and rollback test | AGE `:1600-1674`; SOC writer locations |
| Hidden DataOps callers | P0/P2 | Compatibility window and zero-caller gate | `api.ts:401-408`; tests `:817-848` |
| SNAPSHOT_AFTER has no reader | P2 | Edge-creation test only; traversal deferred | AGE writer `:1103-1125,1421-1426` |
| Pool deployment drift | P1 | Startup pool logging and max-five config | `age_client.py:118-129,182-187` |

## 11. Cross-repo ownership and sequencing

### copilot-sdk

Owns `protocol.py`, `models.py`, `self_computation_router.py`, `scorer.py`, `sqlite_store.py`, `memory_store.py`, graph conformance tests, and counterfactual helper.

### ci-platform

Owns AGE checkpoint epoch normalization/history, transaction use, pool configuration, and disposable AGE tests at the cited AGE locations.

### SOC

Owns shared-router mount at `main.py:131-143`, Decision drift alias at `framework_router.py:107-171`, and atomic outcome/checkpoint persistence at `gae_state.py:396-437` and `triage.py:2322-2332`.

### S2P

Owns canonical route mount after `main.py:168-175`, legacy explorer compatibility, and route/OpenAPI tests.

### DataOps

Owns custom-route caller migration and timeline update at `context_router.py:1037-1068`, `api.ts:401-413`, `types.ts:656-672`, and `CentroidTimelinePanel.tsx:18-155`.

### Dependency order

```text
P-1 confirmations
  → P0 model/provider/routes/empty states
  → P1 epoch precedence/Memory/hash/warm-start/pool/transaction
  → P2 quality/centroid ablation/SNAPSHOT_AFTER/UI
  → STOP
```

## 12. Deferred Program B work

- SQLite→AGE history migration and null-ID deterministic IDs.
- Learned-state snapshot/replay for L5, DK, and conservation.
- Warm-start first-class migration records.
- Full SNAPSHOT_AFTER traversal and SQLite parity.
- Full cross-artifact atomicity.
- PgBouncer deployment.
- GAE invariant gaps #6, #7, #9, #10, #11, #15, #16.
- Option B point-in-time replay with historical W/τ.

## Final readiness

**Execution-ready after P-1.** The plan contains 28 planned files across 4 repositories, 30 concrete tests, exact route/source contracts, corrected warm-start behavior, corrected SOC data-source semantics, and honest centroid-ablation framing. Estimated effort: 9–11.5 engineering days. No production source files were modified.
