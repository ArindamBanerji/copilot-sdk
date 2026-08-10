# JM Frozen Contracts v1

**Date:** 2026-08-06  
**Scope:** P-1 verification for the judgment-history surface and P1 store foundation.

## 1. Confirmed Items

| Item | Status | Frozen value / finding | Evidence |
|---|---|---|---|
| CONFIRM-1 | CONFIRMED | The live `ProfileScorer` temperature attribute is `tau`. A counterfactual scorer must copy live `tau`; `temperature` is not the runtime attribute. | `graph-attention-engine-v50/gae/profile_scorer.py:243-250` |
| CONFIRM-2 | CONFIRMED | DK state is stored in `ProfileScorer._dk_weights`; the public accessor is `get_dk_weights(category_index)`. The counterfactual helper must copy the live DK state and must not use defaults. | `graph-attention-engine-v50/gae/profile_scorer.py:297-306,1030-1034` |
| CONFIRM-3 | CONFIRMED | `get_verified_decisions(domain)` is the canonical protocol method. It exists in the shared protocol and concrete Memory/SQLite/dual-write adapters. AGE-backed access must expose the same protocol method. | `copilot-sdk/copilot_sdk/graph/protocol.py:64-69`; `copilot-sdk/copilot_sdk/graph/memory_store.py:1138`; `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2235`; `copilot-sdk/copilot_sdk/graph/dual_write_store.py:405` |
| CONFIRM-4 | GAP | SQLite assigns `created_at` at insert time, and its loader orders by `created_at DESC, id DESC`. AGE accepts `metadata.created_at` when supplied and otherwise uses current time. Therefore monotonicity is guaranteed only when callers do not backfill AGE metadata timestamps; this needs a P1 write-contract test/guard. | `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1627-1645`; `ci-platform/ci_platform/graph/age_graph_store.py:1088-1108`; `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2639-2645` |
| CONFIRM-5 | GAP | Canonical JM IKS is the centroid-drift formula in `framework.iks_base`, also used by the SOC wrapper. The SDK scorer's `_compute_iks` is a separate composite experience/quality metric and is currently passed into checkpoint writes. The checkpoint `iks` meaning is therefore not unified. | `copilot-sdk/copilot_sdk/framework/iks_base.py:7-17,34-50,94-96`; `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:8-17,77-97`; `copilot-sdk/copilot_sdk/scoring/scorer.py:1570-1610,1841-1854` |
| CONFIRM-6 | CONFIRMED | The DataOps compatibility route has runtime callers in `api.ts` and `CurveScreen.tsx`; backend tests explicitly cover legacy format and the default envelope. No separate `getCentroidHistory` caller was found under `copilot-sdk/e2e/dataops`. The compatibility route cannot be deleted in P1. | `copilot-sdk/apps/dataops/frontend/src/api.ts:401-413`; `copilot-sdk/apps/dataops/frontend/src/screens/CurveScreen.tsx:1-40`; `copilot-sdk/apps/dataops/backend/tests/test_dataops_backend.py:818-851` |

### P-1 interpretation of the two gaps

These are implementation blockers, not reasons to weaken the contract:

1. P1 must make checkpoint timestamp ownership explicit. A normal write uses adapter-assigned current time; migration/backfill may supply an immutable historical timestamp only through an explicitly named migration path.
2. P1 must choose one meaning for checkpoint `iks`. The JM canonical value is centroid-drift IKS. The scorer composite metric must be renamed or stored under a separate field before checkpoint history is treated as cross-copilot comparable.

## 2. Frozen Contracts

### 2.1 CentroidHistoryResponse

The canonical shared envelope is:

```python
class CentroidHistoryResponse(BaseModel):
    checkpoints: list[dict[str, Any]]
    total: int
```

JSON shape:

```json
{
  "checkpoints": [],
  "total": 0
}
```

`checkpoints` is an ordered list of checkpoint records. The envelope is returned with HTTP 200 for empty history. Legacy domain-specific routes may remain as compatibility projections, but the shared route must retain this envelope. Evidence: `copilot-sdk/copilot_sdk/backend/models.py:177-180`.

### 2.2 Checkpoint Write Contract

The required V2 write arguments are:

```python
write_centroid_checkpoint(
    checkpoint_id: str,
    domain: str,
    category: str,
    action: str,
    centroids: Any,
    decisions_count: int,
    verified_count: int,
    iks: float,
    shape: list[int],
    factor_names_hash: str,
    metadata: dict[str, Any] | None = None,
) -> None
```

Required invariants:

- `checkpoint_id`, `domain`, category, action, tensor, counts, shape, and factor hash are present.
- `checkpoint_id` is immutable: identical repeat writes are idempotent; conflicting payloads are rejected.
- `domain` is persisted and used on every read.
- `shape` matches the tensor and `factor_names_hash` matches the active factor order.
- `created_at` is assigned by the adapter at write time for ordinary writes. Historical timestamps require an explicit migration-only path and must never be silently accepted from ordinary metadata.
- `include_v2=False` remains the compatibility default for the protocol list method; history surfaces that promise full history must pass `include_v2=True`. Evidence: `copilot-sdk/copilot_sdk/graph/protocol.py:96-102,267-281`; `copilot-sdk/copilot_sdk/backend/self_computation_router.py:58-59`.

Quality fields are optional until P1 schema work lands; unknown historical quality remains `null`, never fabricated as zero.

### 2.3 Counterfactual Endpoint

Route:

```text
GET /api/self/centroid-history/{checkpoint_id}/counterfactual?window=20
```

Request contract:

- `checkpoint_id` must identify a V2 checkpoint containing a full centroid tensor.
- `window` is an integer from 1 through 400.
- The endpoint loads the last `window` verified decisions through `get_verified_decisions(domain)`.
- Missing checkpoint, missing factor vector, shape mismatch, or factor-hash mismatch returns a typed 404/409/422 error and never fabricates a result.

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

This is a centroid ablation, not historical replay. The helper must copy the live scorer's `tau` and DK state (`_dk_weights`) while replacing only `mu`. It must not mutate or persist the live scorer. Source contract: `copilot-sdk/docs/design/counterfactual_framing_design_v1.md:65-99` and attribute evidence above.

### 2.4 Quality Axis Fields

New V2 checkpoints shall expose an explicit quality object:

```json
{
  "quality": {
    "window_size": 400,
    "verified_count": 37,
    "correct_count": 35,
    "rolling_accuracy": 0.945946,
    "window_end": "...",
    "policy_version": "quality.v1",
    "source": "checkpoint"
  }
}
```

Storage fields:

```text
quality_window_size       integer
quality_verified_count    integer
quality_correct_count     integer
rolling_accuracy          real, nullable when verified_count == 0
quality_window_end        timestamp or decision id
quality_policy_version    text
```

Quality is computed from the last 400 verified outcomes, not `verified_count / decisions_count`. Legacy checkpoints return `quality: null` or an explicit unavailable source. Evidence: `copilot-sdk/docs/design/solution_quality_snapshot_v1.md:95-110,149-169,185-203`.

### 2.5 Warm-start Guard

Before reading or mutating centroid state, `warm_start()` must inspect the complete checkpoint set:

```python
existing = graph_store.get_centroid_checkpoints(
    domain,
    limit=None,
    include_v2=True,
)
if any(record.get("category") != "warm_start" for record in existing):
    logger.info("Skipping warm-start: learned checkpoint exists")
    return
```

The return must occur before computing/blending or assigning `self._scorer.centroids`, and before `save_centroids()`. `limit=None` is mandatory so a newer warm-start row cannot hide an older learned row. Current implementation is not yet conformant: `warm_start()` reads and blends at `scorer.py:1416-1432` and only later saves at `1514-1527`; no guard exists.

### 2.6 Loader Precedence

The target P1 behavior is:

```text
newest by created_at_epoch, with deterministic id/checkpoint tie-break,
across both legacy null-id and V2 non-null-id rows
```

There must be no `checkpoint_id IS NULL` filter in `load_latest_centroids`. SQLite currently orders all rows by `created_at DESC, id DESC` at `sqlite_store.py:2639-2645`; the same precedence must hold for AGE, Memory, and any adapter projection.

## 3. Baseline Test Counts

P-1's requested full-suite command was started, but the aggregate command did not complete within the execution window and was terminated before producing reliable per-repository summaries. No baseline count is claimed from that incomplete run.

Verified existing targeted baselines available before this document:

| Suite | Result |
|---|---|
| SDK targeted router/factory/parity tests | 34 passed |
| S2P enrichment/reader backend tests | 51 passed |
| SOC outcome-route regression tests | 2 passed |
| SOC backend suite previously observed | 2,218 passed, 14 skipped, 8 pre-existing failures |
| SOC Playwright baseline | 407/420 passed |

The eight SOC backend failures were previously identified as unrelated pre-existing graph-contract/ServiceNow/removed-Neo4j compatibility failures; they must remain excluded from regression comparisons until separately resolved.

## 4. P1 Go/No-Go

**Decision: P1 NO-GO for implementation against the contracts as currently implemented.**

Contracts are frozen, but two blockers remain:

1. Warm-start must gain the pre-mutation learned-checkpoint guard in §2.5.
2. Checkpoint `iks` must be separated from or changed to the canonical centroid-drift IKS before cross-copilot history is declared comparable.

P1 may proceed only after those two decisions are implemented and covered by adapter contract tests, plus a completed full-suite baseline run. The frozen response, checkpoint, counterfactual, quality, warm-start, and loader contracts above are the acceptance criteria for that gate.
