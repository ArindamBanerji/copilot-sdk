# GS-CONFLICT + GS-CONSOLIDATE Architecture Plan

## 1. Executive Summary

Current state: `CompoundingScorer` accepts a preset, `DecisionStore`, `ProfileScorer`, optional `GraphStore`, and optional RL/evolution collaborators; it does not expose conflict detection or centroid persistence consolidation parameters today (`copilot_sdk/scoring/scorer.py:87-97`). `learn()` currently loads the decision, checks conservation, updates in-memory GAE centroids, writes the verified outcome, and saves a centroid checkpoint on every successful learn (`copilot_sdk/scoring/scorer.py:220-292`). A search for `surprising_failure`, `surprising_success`, `last_conflict`, and `flush_centroids` found no existing implementation in `copilot_sdk`, `tests`, or `apps`.

Target state: add diagnostic judgment conflict detection and optional centroid persistence consolidation to `CompoundingScorer` while keeping existing default behavior unchanged. Conflict detection is diagnostic only and never gates learning. Consolidation changes checkpoint frequency only when explicitly enabled; in-memory centroid updates and outcome writes still happen on every `learn()`.

Classification: PLAN_READY.

Default behavior guarantee: with default constructor and `learn()` parameters, the current save-on-every-successful-learn behavior remains unchanged. Existing callers such as `scorer.learn(decision_id, actual_action, outcome)` in the scoring router (`copilot_sdk/backend/scoring_router.py:89-93`) and `FreshScorerProxy.learn()` (`copilot_sdk/backend/scorer_proxy.py:41-45`) require no changes.

This is a plan-only document. No source, test, app, or config files are changed by this planning prompt.

## 2. Current Architecture

`CompoundingScorer.__init__` currently takes `preset`, `store`, `scorer`, optional `graph_store`, optional reward/credit/exploration collaborators, and `evolve=False` (`copilot_sdk/scoring/scorer.py:87-97`). If no graph store is supplied, it creates a `SQLiteGraphStore` using the decision store path and preset name (`copilot_sdk/scoring/scorer.py:101-105`).

`from_preset()` builds a preset, opens a `DecisionStore`, loads latest centroids if available, creates a `SQLiteGraphStore` by default, constructs the GAE `ProfileScorer`, and delegates to `CompoundingScorer.__init__` (`copilot_sdk/scoring/scorer.py:116-160`). Any new constructor parameter must either be defaulted or threaded through `from_preset()` with a default so existing calls remain compatible.

`learn()` currently has signature `learn(decision_id, actual_action, outcome="confirmed", *, context=None)` (`copilot_sdk/scoring/scorer.py:220-227`). It reads the decision from `self._graph_store`, validates `actual_action`, derives actual/predicted indexes, correctness, factor vector, category index, and confidence (`copilot_sdk/scoring/scorer.py:228-240`). Conservation is checked before mutation, and a pause returns early (`copilot_sdk/scoring/scorer.py:241-244`). If not paused, it records `iks_before`, snapshots centroids, updates the GAE scorer, computes centroid delta, writes outcome metadata, optionally links an invoice entity, computes `iks_after`, and persists centroids (`copilot_sdk/scoring/scorer.py:244-292`).

Centroid update location: the in-memory GAE centroid tensor is updated by `self._scorer.update(...)` inside `learn()` (`copilot_sdk/scoring/scorer.py:247-263`). The delta is then computed against `before_centroids` (`copilot_sdk/scoring/scorer.py:268`).

Current checkpoint behavior: `learn()` calls `self._graph_store.save_centroids(decision_id, category, self._scorer.centroids, metadata={"iks": iks_after})` on every successful non-paused learn (`copilot_sdk/scoring/scorer.py:286-292`). Tests assert this behavior: `test_scorer_learn_writes_centroids_to_graph_store` expects one checkpoint after one learn (`tests/scoring/test_scorer.py:203-215`), and `test_learn_changes_centroids` checks the latest checkpoint `iks` after learn (`tests/scoring/test_scorer.py:177-185`).

GraphStore save signature: the public protocol requires `save_centroids(decision_id: str, category: str, centroids: Any, metadata: dict | None = None) -> None` (`copilot_sdk/graph/protocol.py:54-60`). `InMemoryGraphStore.save_centroids()` uses the same shape and stores metadata in a checkpoint (`copilot_sdk/graph/memory_store.py:112-127`). `SQLiteGraphStore.save_centroids()` adapts the same protocol to `DecisionStore.save_centroids(...)` (`copilot_sdk/graph/sqlite_store.py:137-155`). `DecisionStore.save_centroids()` persists checkpoint rows with metadata and an `iks` field (`copilot_sdk/scoring/storage.py:172-198`).

Fingerprint behavior: `CompoundingScorer.fingerprint()` calls `compute_fingerprint(self._graph_store.get_verified_decisions(), factor_names)` (`copilot_sdk/scoring/scorer.py:323-327`). `compute_fingerprint()` returns `FactorFingerprint` entries with `name`, `sigma`, `weight`, and `interpretation` (`copilot_sdk/scoring/fingerprint.py:10-24`). With fewer than 5 decisions, factor weights are `0.0` and interpretation is `insufficient data` (`copilot_sdk/scoring/fingerprint.py:26-43`). With enough decisions, it computes per-factor sigmas, inverse-square raw weights, normalizes by maximum raw weight, and returns rounded weights (`copilot_sdk/scoring/fingerprint.py:45-78`).

Domain shape: `DomainShape` carries `n_categories`, `n_actions`, `n_factors`, and name tuples for categories, actions, and factors (`copilot_sdk/scoring/config.py:13-23`), and validates count/name consistency in `__post_init__` (`copilot_sdk/scoring/config.py:24-30`). `DomainPreset` exposes `shape`, `penalty_ratio`, `bootstrap_centroids`, learning rates, temperature, and optional plateau config (`copilot_sdk/scoring/config.py:41-51`).

Callers: a repository-wide `.learn(`/`CompoundingScorer(`/`from_preset(` search mapped current SDK/app/test call sites to existing constructor/factory/learn signatures; no current caller passes a consolidation argument. The backend scoring router calls `scorer.learn(request.decision_id, request.actual_action, request.outcome)` with no optional consolidation argument (`copilot_sdk/backend/scoring_router.py:74-93`). `FreshScorerProxy.learn()` forwards the same three positional arguments (`copilot_sdk/backend/scorer_proxy.py:41-45`). App backends mount the shared scoring router and conservation router rather than custom learning paths, for example DataOps (`apps/dataops/backend/app/main.py:85-101`), purchasing (`apps/purchasing/backend/app/main.py:122-145`), and trading (`apps/trading/backend/app/main.py:68-94`). Tests use current direct-constructor, `from_preset`, and `.learn(...)` shapes across scorer, context, proxy, graph-link, evolution, and preset suites; representative compatibility evidence includes direct construction (`tests/scoring/test_scorer.py:27-48`; `tests/test_learn_context.py:70-76`), positional learn calls (`tests/scoring/test_scorer.py:177-215`; `tests/backend/test_scorer_proxy.py:32-41`), and keyword-only `context` calls (`tests/test_learn_context.py:83-104`, `137-150`, `202-230`).

Conservation boundary: `CompoundingScorer.learn()` has an internal `_conservation_pause()` check before centroid update and outcome persistence (`copilot_sdk/scoring/scorer.py:241-244`). The router-level conservation status reads counts from a state provider or graph-store-like object, using `count_verified`, `count_correct`, and `get_all_decisions`, with no dependency on centroid checkpoints (`copilot_sdk/backend/conservation_router.py:100-144`). Conservation tests assert the router uses those counts (`tests/backend/test_conservation_router.py:36-80`). Therefore GS-CONSOLIDATE must not alter decision/outcome writes or conservation router code.

## 3. GS-CONFLICT Design

Add `copilot_sdk/scoring/conflict.py`.

Public API:

```python
CONFLICT_LOW_THRESHOLD = 0.30
CONFLICT_HIGH_THRESHOLD = 0.70

@dataclass(frozen=True)
class JudgmentConflict:
    decision_id: str
    conflict_type: str  # "surprising_failure" | "surprising_success"
    predicted_success: float
    actual_correct: bool
    factors: dict[str, float]
    contradicting_factors: list[tuple[str, float, float]]
    message: str

def detect_conflict(
    *,
    decision_id: str,
    predicted_success: float,
    actual_correct: bool,
    factors: Mapping[str, Any] | Sequence[Any] | np.ndarray,
    fingerprint_weights: Mapping[str, float],
    factor_names: Sequence[str],
    low_threshold: float = CONFLICT_LOW_THRESHOLD,
    high_threshold: float = CONFLICT_HIGH_THRESHOLD,
) -> JudgmentConflict | None:
    ...
```

`conflict.py` must be standalone and not import `copilot_sdk`; it may use stdlib dataclasses/typing/math and optionally NumPy only if needed for array conversion. It must not write to graph/store and must not mutate centroids.

Semantic timing: conflict detection should use the pre-learn fingerprint and the decision's predicted success. The phrase "contradicts the existing fingerprint" points to the model state before the new verified outcome is incorporated. Live code also computes and uses decision fields before mutation (`copilot_sdk/scoring/scorer.py:228-240`) and only later writes outcome/checkpoints (`copilot_sdk/scoring/scorer.py:276-292`). Using pre-learn avoids explaining a result with a fingerprint that already includes that same result.

Predicted success:
- Use the decision's stored probability for the recommended action where available. `score()` stores `recommended_index` and `probabilities` in decision metadata (`copilot_sdk/scoring/scorer.py:191-199`), and `learn()` already extracts `predicted_index` (`copilot_sdk/scoring/scorer.py:233-235`).
- Fallback to stored confidence if probabilities are missing. `learn()` already extracts confidence from the decision (`copilot_sdk/scoring/scorer.py:239`).
- Clamp to `[0, 1]`.

Conflict rules:
- `surprising_failure`: `predicted_success >= 0.70` and `actual_correct is False`.
- `surprising_success`: `predicted_success <= 0.30` and `actual_correct is True`.
- Otherwise return `None`.

Factor conversion:
- Dict input: use `factor_names` order and coerce known values to finite floats.
- List/tuple/np.ndarray input: require length equal to `factor_names`; zip names to values.
- Missing/non-finite values default to `0.0` only if the current decision stored that shape; otherwise raise `ValueError` in direct unit tests for `detect_conflict()`. In scorer integration, invalid stored decision vectors should not block learning; catch conversion errors and set `last_conflict=None` while logging if needed.

Contradicting factors:
- Use `fingerprint_weights` from the pre-learn fingerprint; names come from `preset.shape.factor_names` (`copilot_sdk/scoring/config.py:20-22`).
- For a diagnostic list, compute a simple surprise contribution such as `abs(value - 0.5) * weight` for each factor. Sort descending by contribution and include `(factor_name, value, weight)`.
- This is diagnostic only; it does not change update inputs or learning rates.

Scorer integration:
- Add `self.last_conflict: JudgmentConflict | None = None` in `__init__`.
- At the start of every `learn()` after the decision is loaded and correctness/predicted success can be computed, set `self.last_conflict = None`, compute `pre_fingerprint = self.fingerprint()`, build a `fingerprint_weights` mapping, and call `detect_conflict(...)`.
- Store the result on `self.last_conflict`.
- Do not add conflict to `LearnResult` in the first implementation unless a test proves response serialization compatibility; expose it as a property/attribute to keep `LearnResult` backward compatible.
- Run conflict detection before `_conservation_pause()` returns, because the feature must detect surprises on every learn attempt. If conservation pauses, no learning occurs, but the diagnostic can still describe the incoming verified outcome. This does not gate learning; it only records diagnostic state.

## 4. Fingerprint Weight Design

Preferred path: reuse existing `CompoundingScorer.fingerprint()` and `FactorFingerprint.weight`, because the repo already computes normalized factor weights from verified decision history (`copilot_sdk/scoring/scorer.py:323-327`; `copilot_sdk/scoring/fingerprint.py:59-78`).

Implementation helper:

```python
def _fingerprint_weight_map(self) -> dict[str, float]:
    result = self.fingerprint()
    return {
        factor.name: max(0.0, min(float(factor.weight), 1.0))
        for factor in result.factors
    }
```

If direct centroid-geometry weights are needed later, they must be added behind tests. Do not use naive `1.0 - variance` unless the variance is normalized to a documented range. A safe centroid fallback would compute per-factor variance across `(category, action)` cells, divide by the maximum finite variance in the current tensor, clip to `[0, 1]`, and map by `preset.shape.factor_names`. This fallback is not required for initial implementation because current fingerprint weights exist.

Tests should assert:
- With insufficient fingerprint history, weights are `0.0` as existing code specifies (`copilot_sdk/scoring/fingerprint.py:29-43`).
- With varied verified history, weights are finite and clipped to `[0, 1]` as existing code specifies through max-weight normalization (`copilot_sdk/scoring/fingerprint.py:59-78`).

## 5. GS-CONSOLIDATE Design

Add optional parameters:
- `CompoundingScorer.__init__(..., consolidation_enabled: bool = False)`
- `CompoundingScorer.from_preset(..., consolidation_enabled: bool = False)`
- `CompoundingScorer.learn(..., consolidate: bool = False, context: dict | None = None)`

Because `learn()` currently has `context` as keyword-only (`copilot_sdk/scoring/scorer.py:220-227`), add `consolidate` as a keyword-only parameter next to `context` to preserve all existing positional callers. Existing router and proxy callers pass no new argument (`copilot_sdk/backend/scoring_router.py:89-93`; `copilot_sdk/backend/scorer_proxy.py:41-45`).

Internal state:
- `self._consolidation_enabled = bool(consolidation_enabled)`
- `self._batch_decision_count = 0`
- `self._last_checkpoint_decision_id: str | None = None`
- `self._last_checkpoint_category: str | None = None`
- optional `self._last_checkpoint_iks: float | None = None`

Default behavior:
- If `self._consolidation_enabled` is false, keep the existing `save_centroids(...)` call after each successful learn exactly as current code does (`copilot_sdk/scoring/scorer.py:286-292`).

When enabled:
- In-memory update via `self._scorer.update(...)` still happens on every learn (`copilot_sdk/scoring/scorer.py:247-263`).
- Outcome write still happens on every learn (`copilot_sdk/scoring/scorer.py:276-281`).
- Conservation counts still see every outcome because router status uses `count_verified`/`count_correct`, not centroid checkpoints (`copilot_sdk/backend/conservation_router.py:100-144`).
- Increment `_batch_decision_count` after a successful centroid update/outcome write.
- Skip `save_centroids` unless `consolidate=True`.
- If `consolidate=True`, save once with current centroids and metadata:
  - `iks`
  - `boundary`: `"learn"`
  - `decisions_in_batch`
  - `consolidation`: `True`
- Reset `_batch_decision_count` after saving.

Add:

```python
def flush_centroids(self, reason: str = "manual") -> int:
    ...
```

Flush behavior:
- If consolidation is disabled, return `0` and do not alter default per-learn checkpoint behavior.
- If enabled and `_batch_decision_count == 0`, return `0` and do not call `save_centroids`.
- If enabled and buffered decisions exist, save current centroids through the existing GraphStore signature (`copilot_sdk/graph/protocol.py:54-60`) using the last decision/category and metadata:
  - `iks`: latest computed or recomputed IKS
  - `boundary`: `reason`
  - `decisions_in_batch`
  - `consolidation`: `True`
- Return the number of decisions flushed and reset `_batch_decision_count` to `0`.

No GraphStore protocol changes are required. Metadata already accepts arbitrary dicts in the protocol (`copilot_sdk/graph/protocol.py:54-60`), in-memory store (`copilot_sdk/graph/memory_store.py:112-127`), SQLite adapter (`copilot_sdk/graph/sqlite_store.py:137-155`), and DecisionStore (`copilot_sdk/scoring/storage.py:172-198`).

## 6. Interaction Rules

Conflict detection runs on every `learn()` call after the decision is loaded and before centroid update/checkpoint persistence. It is not delayed by consolidation.

Conflict detection is diagnostic only:
- It sets `self.last_conflict`.
- It never changes `is_correct`, `actual_action`, `factor_vector`, learning rates, `gt_action_index`, outcome writes, or conservation results.

Consolidation only affects centroid checkpoint persistence. It does not affect:
- `self._scorer.update(...)` in-memory centroid mutation (`copilot_sdk/scoring/scorer.py:247-263`).
- `write_outcome(...)` verified decision stream (`copilot_sdk/scoring/scorer.py:276-281`).
- conservation counts and status (`copilot_sdk/backend/conservation_router.py:100-144`).
- reward/exploration/credit assignment after learn (`copilot_sdk/scoring/scorer.py:293-305`).
- evolution cadence, unless tests later show checkpoint frequency is part of an evolution contract. Current evolution increments `_evolve_count` per learn (`copilot_sdk/scoring/scorer.py:306-309`).

Neither feature gates learning.

## 7. Backward Compatibility

`__init__` parameter default keeps direct test constructors working. Existing direct construction in tests passes positional `preset`, `store`, `gae_scorer` and optional named collaborators (`tests/scoring/test_scorer.py:27-48`; `tests/test_learn_context.py:70-76`), so adding a defaulted keyword at the end is safe.

`from_preset()` parameter default keeps app backends and tests compatible. Existing calls pass `domain`, optional `db_path`, `graph_store`, RL collaborators, and `evolve` (`copilot_sdk/scoring/scorer.py:116-160`; `tests/scoring/test_scorer.py:64-120`).

`learn()` parameter default keeps existing callers compatible. Current app and test callers use positional `decision_id`, `actual_action`, optional `outcome`, and sometimes keyword `context` (`copilot_sdk/backend/scoring_router.py:89-93`; `copilot_sdk/backend/scorer_proxy.py:41-45`; `tests/test_learn_context.py:83-104`).

Default save behavior is testable by preserving current tests expecting a checkpoint after every successful learn (`tests/scoring/test_scorer.py:177-215`).

GraphStore structural implementations are not broken because no protocol method signature changes are needed (`copilot_sdk/graph/protocol.py:54-60`), and tests explicitly validate the protocol shape (`tests/graph/test_protocol.py:11-40`).

## 8. Implementation Scope

Future production files:
- `copilot_sdk/scoring/conflict.py`
- `copilot_sdk/scoring/scorer.py`

Future test files:
- `tests/test_judgment_conflict.py`
- `tests/test_consolidation.py`
- small additions to `tests/scoring/test_scorer.py` only if needed to assert default save behavior remains unchanged.

Forbidden for the implementation prompts:
- `copilot_sdk/backend/conservation_router.py`
- `copilot_sdk/graph/protocol.py` unless a later implementation discovers a hard blocker; current plan does not require it.
- app frontend/backend changes unless caller compatibility tests expose a real integration issue.
- external repos.
- conservation behavior changes.

## 9. Test Plan

Conflict tests:
- `test_detect_conflict_none_when_expected`
- `test_detect_conflict_surprising_success`
- `test_detect_conflict_surprising_failure`
- `test_detect_conflict_empty_or_zero_fingerprint_returns_conflict_with_empty_contradictions_or_none_as_specified`
- `test_contradicting_factors_sorted_by_contribution`
- `test_conflict_message_includes_predicted_percentage`
- `test_thresholds_importable`
- `test_factor_dict_conversion`
- `test_factor_list_tuple_numpy_conversion`
- `test_scorer_last_conflict_resets_on_next_learn`
- `test_scorer_uses_pre_learn_fingerprint_for_conflict_detection`
- `test_conflict_detection_does_not_block_centroid_update_or_outcome_write`
- `test_conflict_detection_runs_before_conservation_pause_without_changing_pause_result`

Consolidation tests:
- `test_default_behavior_saves_centroids_every_successful_learn`
- `test_consolidation_enabled_buffers_persistence`
- `test_consolidation_in_memory_centroids_update_while_buffered`
- `test_consolidate_true_saves_checkpoint_with_metadata`
- `test_flush_centroids_saves_and_resets_count`
- `test_flush_centroids_empty_returns_zero_without_save`
- `test_conflict_detection_not_delayed_by_consolidation`
- `test_write_outcome_still_runs_every_learn_when_buffered`
- `test_conservation_router_has_no_consolidation_dependency`
- `test_existing_callers_remain_compatible`
- `test_consolidated_learn_context_keyword_remains_compatible`

Use fake/recording graph stores where needed to count `save_centroids` calls. Keep tests offline and deterministic.

## 10. Validation Commands

Future implementation validation:

```powershell
python -m pytest tests/test_judgment_conflict.py tests/test_consolidation.py -v --timeout=120
python -m pytest tests/scoring/test_scorer.py tests/test_learn_context.py tests/backend/test_scorer_proxy.py -v --timeout=120
python -m pytest tests/backend/test_conservation_router.py tests/test_conservation_formula.py -v --timeout=120
python -m pytest tests/ -q --timeout=120
python -m pytest apps/dataops/backend/tests/ apps/purchasing/backend/tests/ apps/trading/backend/tests/ -q --timeout=120
```

Do not hardcode expected pass counts.

## 11. Risks and Mitigations

Pre/post fingerprint semantic drift:
- Mitigation: document and test pre-learn semantics. The current decision is read before mutation (`copilot_sdk/scoring/scorer.py:228-240`), and mutation follows later (`copilot_sdk/scoring/scorer.py:247-292`).

GraphStore save signature mismatch:
- Mitigation: use the existing `save_centroids(decision_id, category, centroids, metadata=None)` protocol (`copilot_sdk/graph/protocol.py:54-60`).

App caller breakage:
- Mitigation: add only defaulted parameters and keep `context` keyword-only; app routers and proxy use existing signatures (`copilot_sdk/backend/scoring_router.py:89-93`; `copilot_sdk/backend/scorer_proxy.py:41-45`).

Conservation accidental coupling:
- Mitigation: do not modify conservation router. It reads count methods, not checkpoints (`copilot_sdk/backend/conservation_router.py:100-144`).

Batch count off-by-one:
- Mitigation: increment only after successful update/outcome write. Tests must cover one, two, and flush-empty cases.

Save metadata mismatch:
- Mitigation: metadata is already persisted by all stores (`copilot_sdk/graph/memory_store.py:112-127`; `copilot_sdk/graph/sqlite_store.py:137-155`; `copilot_sdk/scoring/storage.py:172-198`).

NumPy/list factor conversion:
- Mitigation: test dict, list, tuple, and ndarray conversion against `DomainShape.factor_names` (`copilot_sdk/scoring/config.py:20-22`).

Structural protocol break:
- Mitigation: do not change `GraphStore`; protocol tests validate current required methods (`tests/graph/test_protocol.py:11-40`).

Hidden state/reset issues:
- Mitigation: keep state instance-local on `CompoundingScorer`; test separate scorer instances.

Conservation pause interaction:
- Mitigation: because current `learn()` returns early on conservation pause (`copilot_sdk/scoring/scorer.py:241-244`), tests must define whether `last_conflict` is still set for paused learns. This plan requires conflict detection before pause and no learning gate.

Evolution interaction:
- Mitigation: do not change `_evolve_count` cadence, which is currently per successful learn (`copilot_sdk/scoring/scorer.py:306-309`).

## 12. Reading Log

- `CLAUDE.md:1-70` - repo rules and grounding contract.
- `copilot_sdk/scoring/scorer.py:84-160` - constructor and `from_preset`.
- `copilot_sdk/scoring/scorer.py:220-327` - `learn()`, checkpoint save, fingerprint.
- `copilot_sdk/scoring/scorer.py:455-510` - IKS and conservation pause.
- `copilot_sdk/scoring/config.py:13-51` - `DomainShape` and `DomainPreset`.
- `copilot_sdk/scoring/fingerprint.py:10-105` - fingerprint result and weights.
- `copilot_sdk/graph/protocol.py:8-76` - GraphStore protocol.
- `copilot_sdk/graph/memory_store.py:12-133` - in-memory save/checkpoint behavior.
- `copilot_sdk/graph/sqlite_store.py:14-162` - SQLite graph save/checkpoint behavior.
- `copilot_sdk/scoring/storage.py:32-80`, `172-209`, `220-235`, `269-303` - DecisionStore schema, centroid persistence, verified decisions, counts.
- `copilot_sdk/backend/scoring_router.py:21-120` - score/learn/fingerprint/trajectory router callers.
- `copilot_sdk/backend/scorer_proxy.py:15-60` - fresh scorer proxy callers.
- `copilot_sdk/backend/conservation_router.py:37-181` - conservation status/count boundary.
- `tests/scoring/test_scorer.py:27-48`, `177-215`, `243-259`, `620-649`, `652-715` - scorer construction, learn save expectations, conservation pause, direct store guard, centroid state tests.
- `tests/test_learn_context.py:70-104`, `137-150` - learn context caller compatibility.
- `tests/backend/test_scorer_proxy.py:25-41` - proxy learn caller.
- `tests/backend/test_conservation_router.py:1-80` - conservation router count behavior.
- `tests/graph/test_protocol.py:11-40` - GraphStore protocol method tests.
- `tests/graph/test_memory_store.py:87-140` - in-memory centroid checkpoint tests.
- `tests/graph/test_sqlite_store.py:75-130` - SQLite centroid checkpoint tests.
- `apps/dataops/backend/app/main.py:85-112`, `apps/purchasing/backend/app/main.py:130-147`, `apps/trading/backend/app/main.py:87-96` - app router mounting and conservation boundaries.

## Prompt Verification Pass

1. Current learn save behavior is proven by code (`copilot_sdk/scoring/scorer.py:286-292`) and tests (`tests/scoring/test_scorer.py:203-215`).
2. Existing callers are mapped in backend router/proxy and representative tests (`copilot_sdk/backend/scoring_router.py:89-93`; `copilot_sdk/backend/scorer_proxy.py:41-45`; `tests/test_learn_context.py:83-104`).
3. Default behavior equivalence is testable with existing save-on-learn tests (`tests/scoring/test_scorer.py:177-215`).
4. Conflict timing is explicitly pre-learn.
5. Conservation is not touched; conservation reads decision counts, not centroid checkpoints (`copilot_sdk/backend/conservation_router.py:100-144`).
6. GraphStore save signature is respected (`copilot_sdk/graph/protocol.py:54-60`).
7. State is instance-local on `CompoundingScorer`.
8. Tests cover interaction rules.
9. Implementation can be done without frontend/app changes unless compatibility tests reveal a real issue.
