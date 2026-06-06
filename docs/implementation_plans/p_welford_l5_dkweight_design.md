# P-WELFORD L5 DKWeight Design

## Executive decision

* Ready for implementation: NO for runtime-complete P-WELFORD.
* Recommended protocol option: B, extend the current DK signature with optional keyword-only Welford state while preserving the existing positional `weight_tensor`, `n_decisions_used`, and `computed_at` contract.
* Whether Roadmap clarification is needed: YES.

The storage/protocol hardening portion is straightforward, but a full implementation must not proceed as a single runtime package yet. Discovery found that `update_dk_weights()` is currently storage/test plumbing in `copilot-sdk` and `ci-platform`; no SDK learn/outcome path calls it. The actual coordinate-descent DK estimator exists in the imported `graph-attention-engine-v50` package, not in `copilot-sdk` or `ci-platform`, and the SDK wrapper does not call `ProfileScorer.reestimate_dk()` or persist its output to L5 DKWeight storage.

The key Roadmap decision is whether P-WELFORD may wire `copilot_sdk.scoring.CompoundingScorer.learn()` to call GAE DK re-estimation and then persist weights, or whether that runtime estimator wiring belongs to a separate GAE integration phase. Without that decision, P-WELFORD can only safely implement backward-compatible storage fields and pure accumulator utilities.

## Current DK implementation

* protocol signature: `L5LearningStore.update_dk_weights(domain, weight_tensor, n_decisions_used, computed_at) -> None`; `get_dk_weights(domain) -> dict[str, object] | None`.
* SQLite shape: `l5_dk_weights` has `id`, `domain`, `weight_json`, `n_decisions_used`, `computed_at`, `supersedes_id`, `is_current`, and `created_at`. Current rows are selected by `domain` plus `is_current = 1`.
* InMemory shape: `_l5_dk_weights: dict[str, list[dict[str, object]]]` stores versioned rows with `id`, `domain`, `weight_json`, `n_decisions_used`, `computed_at`, `supersedes_id`, `is_current`, and `created_at`.
* AGE shape: `L5DKWeight` current nodes and `L5DKWeightArchive` archive nodes. Current properties include `dk_weight_id`, `domain`, `weight_json`, `n_decisions_used`, `computed_at`, `created_at`, and `supersedes_id`. Archives copy previous current properties and are linked from the new current by `(new:L5DKWeight)-[:SUPERSEDES]->(archive:L5DKWeightArchive)`.
* runtime update path: no `copilot-sdk` runtime path calls `update_dk_weights()`. Workspace search found calls only in storage tests, AGE tests, AGE adapter delegation, and store implementations.
* whether DK is runtime-wired: NO in the `copilot-sdk` and `ci-platform` repositories. The GAE scorer has DK machinery, but the SDK wrapper does not persist those weights.

The actual estimator owner is `graph-attention-engine-v50/gae/dk_estimator.py`. `CoordinateDescentEstimator.estimate()` returns a `(n_categories, n_dims)` weight matrix from decisions shaped as `(factor_vector, category_index, correct_action_index)` and the centroid tensor. `ProfileScorer.reestimate_dk()` filters its internal `_decision_buffer` to correct decisions only, calls the estimator, and stores `_dk_weights`. That path is not currently reached by the SDK default scorer setup, because `CompoundingScorer.from_preset()` constructs `ProfileScorer(...)` directly rather than `ProfileScorer.for_soc_twophase(...)`.

## Welford computation source

* factor vector source: `CompoundingScorer.score()` writes `factor_vector` into decision metadata as the preset-ordered dense vector derived from `preset.shape.factor_names`. `get_verified_decisions()` returns that vector joined with outcome fields.
* confirmed population: verified decisions where `is_correct is True`, equivalently the actual action matched the stored recommended action in the current SDK learn flow.
* overridden population: verified decisions where `is_correct is False`, equivalently the actual action differed from the stored recommended action in the current SDK learn flow.
* all verified population: every row returned by `get_verified_decisions(domain)`, regardless of correctness.
* dimensionality: runtime factor vectors are 1D with width `preset.shape.n_factors`. Current DK storage stores a 2D tensor. GAE coordinate descent produces `(n_categories, n_factors)`, which is 2D and matches the current storage validator.
* cold start: initialize Welford count to zero and all six vectors to zero arrays of length `n_factors`; do not emit Welford state with a DK row until at least one verified decision has been processed.
* warm start: restore `welford_state` from `get_dk_weights(domain)` when present. If missing, rebuild from verified decisions if Roadmap allows a replay pass; otherwise start a new accumulator and keep old DK row readable with `welford_state=None`.

The mismatch is resolved as follows: Welford tracks one-dimensional factor statistics per population, while DKWeight continues to store the 2D `(category, factor)` weight tensor. Welford vectors explain the distributional evidence behind factor precision; the category dimension is produced by the estimator using category-specific decision subsets and centroids. If Roadmap requires category-specific Welford, the six required vectors must become six matrices, which is a breaking semantic change and must be approved before implementation.

## Protocol design

* exact proposed update_dk_weights signature:

```python
def update_dk_weights(
    self,
    domain: str,
    weight_tensor: list[list[float]],
    n_decisions_used: int,
    computed_at: float,
    *,
    welford_state: dict[str, object] | None = None,
    n_confirmed: int | None = None,
    n_overridden: int | None = None,
    entity_group: str | None = None,
) -> None:
    ...
```

* get_dk_weights return shape: preserve existing keys and add `welford_state`, `n_confirmed`, `n_overridden`, and `entity_group`. `welford_state` is either `None` or a dict containing `confirmed_mean`, `confirmed_m2`, `overridden_mean`, `overridden_m2`, `all_mean`, `all_m2`, and `n_all`.
* backward compatibility policy: old positional calls remain valid. Old rows with no Welford columns/properties return `welford_state=None` and nullable count fields. Exact-shape tests must be updated intentionally.
* migration policy: add nullable columns/properties only. Do not rewrite historical DK rows and do not require Welford on read for existing rows.

Option B is safest because option A replaces the P23/P24 signature and would break existing storage tests and adapter parity; option C splits the weight tensor from the audit chain and risks non-atomic mismatches; option D adds storage fields but cannot write a meaningful audit chain.

## Storage design

### SQLite

* schema changes: add nullable columns to `l5_dk_weights`:
  * `confirmed_mean_json TEXT`
  * `confirmed_m2_json TEXT`
  * `overridden_mean_json TEXT`
  * `overridden_m2_json TEXT`
  * `all_mean_json TEXT`
  * `all_m2_json TEXT`
  * `n_confirmed INTEGER`
  * `n_overridden INTEGER`
  * `entity_group TEXT`
* ALTER/new table strategy: new table creation includes these nullable columns. Existing DB initialization checks `PRAGMA table_info(l5_dk_weights)` and applies idempotent `ALTER TABLE ... ADD COLUMN` for missing fields.
* read behavior: if all six JSON columns are absent or NULL, return `welford_state=None`. If any are present, require all six vectors plus valid counts and revalidate dimensions.
* backward compatibility: existing P23 rows remain readable. SQLite current-row index and version behavior remain unchanged.

### InMemory

* state shape: each DK version row stores optional `welford_state`, `n_confirmed`, `n_overridden`, and `entity_group` alongside current DK fields.
* copy safety: deep-copy Welford dicts and vectors on write and read. Mutating a returned `welford_state` must not alter store state.

### AGE

* node properties: add nullable properties to `L5DKWeight`:
  * `confirmed_mean_json`
  * `confirmed_m2_json`
  * `overridden_mean_json`
  * `overridden_m2_json`
  * `all_mean_json`
  * `all_m2_json`
  * `n_confirmed`
  * `n_overridden`
  * `entity_group`
* serialization: compact JSON strings for each vector, using the same `_S()` string-escaping style as existing AGE storage.
* read validation: decode and validate all six vectors if any Welford property exists. Required validation: non-empty 1D numeric vectors, equal width, counts non-negative, `n_confirmed + n_overridden == n_all` only if Roadmap declares confirmed/overridden exhaustive. Otherwise validate `n_all == n_decisions_used` and counts individually.
* backward compatibility: old `L5DKWeight` nodes lacking Welford properties return `welford_state=None`. Archive nodes must copy Welford properties when archiving current rows.

## Runtime wiring design

* where Welford accumulators live: in a new pure SDK module, for example `copilot_sdk/scoring/dk_welford.py`. Do not put computation in graph stores.
* where they are updated: after verified learn/outcome is accepted, using the persisted decision's `factor_vector` and `is_correct` classification.
* where update_dk_weights is called: only after Roadmap approves how SDK should trigger DK re-estimation. The likely insertion point is `CompoundingScorer.learn()` after `write_outcome()` and after any GAE DK re-estimation succeeds, not inside GraphStore.
* failure policy: Welford/DK persistence failure is non-fatal for learn/outcome, matching P25b/P25c L5 persistence policy. Calculation errors should log and skip the DK write rather than write partial audit state.
* concurrency policy: reuse the same per-router/domain serialization principle used for P25b conservation persistence if wiring through API routers. If wiring inside `CompoundingScorer.learn()`, serialize accumulator restore/update/reestimate/persist for each scorer instance. Multi-process AGE duplicate-current risk remains P3 unless runtime deployment uses multiple workers for the same domain.

The accumulator API should be deterministic and independent of storage:

```python
class WelfordAccumulator:
    def update(self, vector: Sequence[float]) -> None: ...
    def to_state(self) -> dict[str, object]: ...
    @classmethod
    def from_state(cls, state: dict[str, object]) -> "WelfordAccumulator": ...
```

A domain-level holder should contain three accumulators: `confirmed`, `overridden`, and `all`.

## Test 58 design

* recomputation formula: first validate the Welford math itself:
  * `mean` and `m2` must match a direct batch computation for known vectors.
  * sample variance is `m2 / (n - 1)` when `n > 1`.
  * population variance is `m2 / n` when the estimator explicitly needs population variance.
* exact expected assertions:
  * restored Welford state reproduces means and variances from the original verified decision vectors.
  * confirmed, overridden, and all populations have the right counts and are disjoint where `is_correct` is boolean.
  * if Roadmap approves a Welford-derived precision formula, recomputed precision vectors match the stored vectors within a strict tolerance.
  * if using GAE `CoordinateDescentEstimator`, a deterministic test with fixed centroids and fixed decision set must show `weight_tensor` equals `CoordinateDescentEstimator.estimate(...)`; Welford state alone cannot prove the coordinate descent output because the estimator requires labeled decisions and centroids, not just means and M2.
* limitations: GAE coordinate descent optimizes candidate weights against classification accuracy. Its result is not directly reconstructible from the six required Welford vectors alone. Therefore a fake test that only roundtrips Welford fields is insufficient, but a test claiming to recompute coordinate-descent weights from Welford alone would also be false.
* stop conditions if recomputation cannot be proven:
  * stop if Roadmap requires exact coordinate-descent recomputation from only six Welford vectors.
  * stop if Roadmap requires Welford vectors to replace the existing estimator without approving an algorithm change.
  * stop if category-specific DK weights must be explained but only domain-level Welford vectors are allowed.

## Regression matrix

* copilot-sdk targeted:
  * `python -m pytest tests/test_l5_dk_weight_storage.py tests/test_l5_protocol_extension.py tests/graph/test_protocol.py tests/graph/test_protocol_v2_conformance.py -q --timeout=120`
  * new `tests/test_l5_dk_welford_storage.py`
  * new `tests/scoring/test_dk_welford.py`
* copilot-sdk full:
  * `python -m pytest tests/ -q --timeout=120`
  * app backend suites if runtime wiring touches `CompoundingScorer.learn()` or scoring routers.
* ci-platform targeted:
  * `python -m pytest tests/test_age_graph_store.py tests/test_age_sdk_adapter.py -q --timeout=120`
  * `python -m mypy ci_platform/graph --ignore-missing-imports --no-incremental --show-error-codes --pretty`
* ci-platform full:
  * `python -m pytest tests/ -q --timeout=120`
* app backend tests if needed:
  * trading, purchasing, dataops, and S2P learn/outcome suites only if P-WELFORD implementation wires runtime DK writes.

## Stop conditions for implementation

* current DK computation path cannot be found in the implementation scope.
* current DK weights are not computed at runtime and Roadmap has not approved wiring `ProfileScorer.reestimate_dk()`.
* Welford recomputation is required to match coordinate descent from Welford vectors alone.
* protocol change would break existing routes/tests because old positional `update_dk_weights()` calls are not preserved.
* vector dimensionality mismatch cannot be resolved as domain-level 1D Welford vectors plus 2D `(category, factor)` DK weights.
* adding Welford requires changing conservation formulas, scorer decision behavior, or centroid update behavior beyond tracking and persistence.
* confirmed/overridden classification cannot be mapped from `is_correct`.
* AGE implementation would require `MERGE`.

## Proposed next prompt

Roadmap clarification request:

* Confirm whether P-WELFORD may wire the SDK wrapper to GAE DK runtime behavior by calling `ProfileScorer.reestimate_dk()` after verified learn/outcome, then persisting `_dk_weights` through L5 DKWeight storage.
* Confirm whether the six Welford vectors are domain-level factor vectors or category-specific matrices.
* Confirm whether Test 58 should validate Welford statistical audit correctness plus coordinate-descent parity from raw verified decisions, or whether Roadmap expects a new Welford-derived DK algorithm.
* Confirm whether `update_dk_weights()` should keep return type `None` for compatibility or migrate to `str` in a separate protocol-breaking phase.

If Roadmap approves the above, the implementation should be split:

1. P-WELFORD-A: protocol-compatible storage extension and WelfordAccumulator tests across SQLite, InMemory, AGE, and AGEGraphStoreAdapter.
2. P-WELFORD-B: SDK scorer runtime integration with GAE DK re-estimation, non-fatal L5 persistence, and app backend regressions.
3. P-WELFORD-C: Test 58 audit conformance using raw verified decisions, centroids, stored DK weights, and stored Welford state.
