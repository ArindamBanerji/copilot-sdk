# Counterfactual Endpoint — Executable Design (Option A: Centroid Ablation)
**Date:** 2026-08-06 · applies to C3 / Gap 3 of the implementation plan · resolves Addendum Correction 2

## 1. Decision and the honest claim

Ship **Option A — centroid ablation.** Fully honest with stored data, zero extra cost, and the more useful signal (isolates centroid improvement from kernel changes). Option B is a later, opt-in extension (§8).

- **What it computes:** for the last N verified decisions, re-score each one with checkpoint k's centroids AND with the latest centroids, holding the current DK-weight kernel W and temperature τ fixed in both, and count the flips.
- **What it means:** "Rolling centroids back to checkpoint k (kernel and temperature held at today) would change action on `change_rate` of the last N verified decisions."
- **What it is NOT:** a reconstruction of the scorer at time k. Checkpoint k does not store DK weights or temperature, so the endpoint never claims "the system would have decided X at time k." The label enforces this (§4).

## 2. Semantics

For each decision `d` with factors `f_d` and category `c_d`:

- `baseline(d) = argmax action of score(f_d, c_d | μ=latest, W=current, τ=current)`
- `counterfactual(d) = argmax action of score(f_d, c_d | μ=checkpoint_k, W=current, τ=current)`
- `changed(d) = baseline(d) != counterfactual(d)`
- `change_rate = |{d : changed(d)}| / N`

The ONLY variable is the centroid tensor μ. This is the invariant the design must guarantee—and it is directly testable by `test_ablation_identity_zero` (§6).

## 3. Helper — `score_with_centroids`

```python
# copilot-sdk/scoring/scorer.py — beside score_read_only (~:404-427)
def score_with_centroids(
    self,
    centroids: np.ndarray,
    factors: dict[str, float],
    category: str,
) -> ScoreResult:
    """Centroid ablation: score with `centroids` but the LIVE kernel + temperature.
    Isolates the centroid contribution. NOT a point-in-time replay."""
    category_index, factor_values, factor_vector, *_ = self._predict(factors, category)

    temporary = ProfileScorer(
        mu=np.asarray(centroids, dtype=np.float64).copy(),
        actions=list(self._preset.shape.action_names),
        categories=list(self._preset.shape.category_names),
        eta_override=0.0,
    )
    # Hold everything except μ at the live scorer's current state.
    live_dk = self.get_dk_weights()
    if live_dk is not None:
        temporary._dk_weights = np.asarray(live_dk, dtype=np.float64).copy()
    temporary.tau = self._scorer.tau  # [confirm attr in P-1]

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

`[confirm in P-1]`: verify the exact live `ProfileScorer` attribute names for DK weights and temperature, and the exact `CompoundingScorer.get_dk_weights()` contract. If direct construction proves fragile, compute `K=(f-μ)ᵀW(f-μ)` and `P=softmax(-K/τ)` directly with the current values. The implementation must not silently fall back to ProfileScorer defaults.

Read-only requirements: no `learn()`, no store write, and no assignment to `self._scorer.*`. The temporary scorer is discarded after the result is produced.

## 4. Endpoint contract

`GET /api/self/centroid-history/{checkpoint_id}/counterfactual?window=20`

Request constraints:

- `checkpoint_id` identifies a V2 checkpoint containing the full centroid tensor.
- `window` is an integer in `[1, 400]`; the endpoint selects the most recent verified decisions through the method confirmed in P-1.
- Missing checkpoint, missing factor vector, incompatible tensor shape, or factor-name hash mismatch returns a typed 404/409/422 response—not a fabricated result.

Response:

```json
{
  "checkpoint_id": "s2p:checkpoint:abc",
  "checkpoint_time": "2026-08-06T12:00:00Z",
  "analysis_type": "centroid_ablation",
  "held_fixed": ["dk_weights", "temperature"],
  "decisions_rescored": 20,
  "would_change": 3,
  "change_rate": 0.15,
  "details": [{"decision_id": "d-1", "original_action": "hold_for_review", "counterfactual_action": "auto_approve", "changed": true}]
}
```

`analysis_type` and `held_fixed` are contract fields. They prevent a downstream UI or report from upgrading centroid ablation into a point-in-time replay claim.

## 5. Algorithm

1. Load checkpoint k, including tensor, shape, factor-name hash, domain, and timestamp, through the protocol metadata reader.
2. Validate domain, tensor shape, factor-name hash, finite values, and `[0,1]` bounds where the current scorer contract requires them.
3. Load the last `window` verified decisions using the method confirmed in P-1. If the exact method is not `get_verified_decisions`, use the adapter’s canonical equivalent; do not access private store fields.
4. For every decision, compute the baseline with the current live centroid tensor through the isolated helper, then compute the counterfactual with checkpoint k’s tensor through the same helper.
5. Count action flips and divide by the number actually rescored. If zero decisions are available, return `decisions_rescored=0`, `would_change=0`, `change_rate=null`, and `status="no_verified_decisions"`.
6. Return the fixed analysis labels and detail rows. Do not persist a Decision, outcome, checkpoint, or learning update.

## 6. Tests

All tests use real stores/scorers and disposable data; no production graph is read or written.

1. **`test_ablation_identity_zero`** — pass the live scorer’s current μ as checkpoint μ; assert every baseline/counterfactual action is equal, `would_change == 0`, and `change_rate == 0.0`.
2. **`test_ablation_flip_count`** — use a tensor that changes exactly two of three decisions; assert `decisions_rescored == 3`, `would_change == 2`, and `change_rate == 2/3`.
3. **`test_ablation_contract_labels`** — assert `analysis_type == "centroid_ablation"` and exact ordered `held_fixed == ["dk_weights", "temperature"]`.
4. **`test_ablation_holds_live_kernel_and_temperature`** — alter checkpoint μ while keeping live W/τ fixed; assert the helper’s result matches a direct calculation using live W/τ and does not use ProfileScorer defaults.
5. **`test_ablation_is_read_only`** — snapshot live μ, DK state, checkpoint count, and decision count; call endpoint; assert all are unchanged.
6. **`test_ablation_rejects_hash_or_shape_mismatch`** — assert incompatible hash/shape returns typed 409/422 and does not score.
7. **`test_ablation_window_bound`** — assert `window=0` and `window=401` are rejected; `window=20` rescales no more than 20 rows.
8. **`test_ablation_no_verified_decisions`** — assert zero-row response has null `change_rate` and explicit no-data status.

## 7. UI and claim wording

Use the label **“Centroid contribution”** or **“Centroid ablation”**. The UI may say:

> Rolling centroids back to checkpoint k, with today’s kernel and temperature held fixed, would change X% of recent decisions.

The UI must not say “historical replay,” “what the system would have decided at checkpoint k,” or imply that DK weights/temperature were restored. Display `analysis_type` and `held_fixed` in API-derived metadata or documentation, and show an explicit no-data state for zero verified decisions.

## 8. Option B hook — point-in-time replay (deferred, additive)

A future point-in-time replay may store or retrieve DK weights, temperature, factor schema, and any other scorer calibration state alongside each checkpoint. It would then score with `{μ_k, W_k, τ_k}` and could make a historical-time claim. That is not part of C3/P2. Adding those fields later must be additive and must not change the semantics of this endpoint without a versioned `analysis_type`.
