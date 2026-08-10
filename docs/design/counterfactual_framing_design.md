# Counterfactual Endpoint — Executable Design (Option A: Centroid Ablation)
**Date:** 2026-08-06 · applies to C3 / Gap 3 of the implementation plan · resolves Addendum Correction 2

## 1. Decision and the honest claim
Ship **Option A — centroid ablation.** It is fully honest with the data we actually store, it's zero extra cost, and it's the *more useful* signal (it isolates the centroid improvement from kernel changes). Option B (point-in-time replay) is a later, opt-in extension gated on storing DK weights + temperature per checkpoint (§7).

- **What it computes:** for the last N verified decisions, re-score each decision's factor vector twice — once with the **latest** centroids, once with **checkpoint k's** centroids — while holding the **current** DK-weight kernel `W` and temperature `τ` fixed in both. Report how many decisions change action.
- **What it means:** "Rolling the centroids back to checkpoint k (kernel and temperature held at today) would change action on `change_rate` of the last N verified decisions." A rising `change_rate` as k recedes = the centroids have moved real decision boundaries = compounding is real in the centroid dimension.
- **What it is NOT:** a reconstruction of the scorer at time k. Checkpoint k does not store the DK weights or temperature in effect then, so the endpoint never claims "the system would have decided X at time k." The label enforces this (§4).

## 2. Semantics (both sides under the CURRENT kernel + temperature)
For each decision `d` with factors `f_d`, category `c_d`:
- `baseline(d)` = argmax action of `score(f_d, c_d | μ=latest, W=current, τ=current)`
- `counterfactual(d)` = argmax action of `score(f_d, c_d | μ=checkpoint_k, W=current, τ=current)`
- `changed(d)` = `baseline(d) ≠ counterfactual(d)`
- `change_rate` = `|{d : changed(d)}| / N`

The **only** variable is the centroid tensor μ. This is the invariant the design must guarantee — and it's directly testable (§6, `test_ablation_identity_zero`): passing checkpoint centroids equal to the latest centroids must yield `change_rate == 0`. If it doesn't, `W`/`τ` are not being held fixed and the analysis is invalid.

## 3. Helper — `score_with_centroids` (corrects the v2 snippet)
The v2 snippet built a temporary `ProfileScorer` with only `mu` + `eta_override=0.0`, which leaves `W` and `τ` at their **defaults** — that is neither an ablation-vs-current nor a replay. The helper MUST copy the live scorer's current `W` and `τ` so the only difference is μ.

```python
# copilot_sdk/scoring/scorer.py — beside score_read_only (~:404-427)
def score_with_centroids(
    self,
    centroids: np.ndarray,
    factors: dict[str, float],
    category: str,
) -> ScoreResult:
    """Centroid ablation: score with `centroids` but the LIVE kernel + temperature.
    Isolates the centroid contribution. NOT a point-in-time replay — checkpoint
    DK weights / temperature are not stored, so they are held at current."""
    category_index, factor_values, factor_vector, *_ = self._predict(factors, category)

    temporary = ProfileScorer(
        mu=np.asarray(centroids, dtype=np.float64).copy(),
        actions=list(self._preset.shape.action_names),
        categories=list(self._preset.shape.category_names),
        eta_override=0.0,
    )
    # Hold everything except μ at the live scorer's current state.
    live_dk = self.get_dk_weights()                       # current W (copy)
    if live_dk is not None:
        temporary._dk_weights = np.asarray(live_dk, dtype=np.float64).copy()
    temporary.temperature = self._scorer.temperature       # current τ   [confirm attr in P-1]
    # copy any non-default masks / kernel settings the live scorer uses  [confirm in P-1]

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

**[confirm in P-1]** the exact `ProfileScorer` attribute names for the DK-weight tensor and temperature (v2 cited `profile_scorer.py:156-170` init, `:227-239` mu copy, `:408-430` score). The *invariant* is fixed regardless: only μ differs from the live scorer. **Fallback if construction proves fragile:** compute the score directly in numpy from the canonical form `K_a=(f-μ_a)ᵀW(f-μ_a)`, `P=softmax(-K/τ)`, reusing the live `W`, `τ` — avoids any `ProfileScorer` construction but duplicates the kernel math, so prefer the temporary-scorer path.

**Read-only guarantees:** no `learn()`, no store write, no assignment to `self._scorer.*`. The temporary scorer is discarded. Baseline uses the existing `score_read_only` (live scorer = latest μ + current W/τ).

## 4. Endpoint contract
```
GET /api/self/centroid-history/{checkpoint_id}/counterfactual?window=20
```
- `window` ∈ [1, 400], default 20.
- **200 (populated):**
```json
{
  "analysis_type": "centroid_ablation",
  "description": "Decisions rescored with this checkpoint's centroids and the current kernel + temperature; isolates the centroid contribution. Not a point-in-time replay.",
  "checkpoint_id": "...",
  "checkpoint_time": "...",
  "baseline": "latest_centroids",
  "held_fixed": ["dk_weights", "temperature"],
  "window_requested": 20,
  "decisions_rescored": 20,
  "would_change": 7,
  "change_rate": 0.35,
  "details": [
    {"decision_id": "...", "category": "...", "baseline_action": "...", "counterfactual_action": "...", "changed": true}
  ]
}
```
- **200 (empty window):** `decisions_rescored: 0`, `change_rate: null`, `note: "no verified decisions in window"`.
- **404** checkpoint not found for domain · **409** `checkpoint_factor_mismatch` (shape or `factor_names_hash` ≠ current preset — can't ablate across a factor-schema change) · **422** `checkpoint_has_no_tensor` (legacy row without centroids).

The `analysis_type` and `held_fixed` fields are **contract**, not decoration — they are what keeps a downstream UI or pitch from silently upgrading the claim to "what would have happened."

## 5. Algorithm
1. Load checkpoint k → `centroids_k`, `shape_k`, `factor_names_hash_k` (reuse the `get_latest_centroid_checkpoint`/checkpoint-read seam from C5). 404 if absent, 422 if no tensor.
2. Validate `shape_k == preset.shape` and `factor_names_hash_k == hash(preset.factor_names)`. Else **409** (reuses C5's factor-hash validation).
3. `decisions = graph_store.get_verified_decisions(domain)[-window:]`. Empty → 200 empty.
4. For each `d`: `factors_d`, `category_d` from the decision;
   `baseline = self.score_read_only(factors_d, category_d).action`;
   `cf = self.score_with_centroids(centroids_k, factors_d, category_d).action`;
   `changed = baseline != cf`.
5. Aggregate `decisions_rescored`, `would_change`, `change_rate`, `details`; attach the labels.
6. **Assert read-only** after the loop (belt-and-suspenders): live μ byte-equal to pre-call; checkpoint count unchanged.

## 6. Tests
- `test_ablation_identity_zero` — **the load-bearing test.** Pass checkpoint centroids equal to the latest → `change_rate == 0` and every `changed == false`. Proves W/τ are held fixed (only μ varies). If this fails, the helper isn't copying the live kernel.
- `test_counterfactual_exact_change_count` — seed a checkpoint + 3 verified decisions with known factors chosen so k-vs-latest flips a known number; assert `would_change` and `change_rate`.
- `test_score_with_centroids_does_not_mutate_live_mu` — live `mu` byte-equal before/after; store checkpoint count unchanged.
- `test_counterfactual_is_read_only` — no new decisions/outcomes/checkpoints after N requests.
- `test_counterfactual_factor_mismatch_409` — checkpoint with a different `factor_names_hash` → 409.
- `test_counterfactual_legacy_no_tensor_422`.
- `test_counterfactual_empty_window` — no verified decisions → 200, `decisions_rescored=0`, `change_rate=null`.
- `test_counterfactual_response_labels_ablation` — `analysis_type=="centroid_ablation"`, `held_fixed` contains `dk_weights` and `temperature`.

## 7. UI / claim wording (honest by construction)
- Surface label: **"Centroid contribution"** (or "Centroid ablation"). Never "historical replay" / "what the system would have done."
- Copy template: *"Rolling centroids back to {checkpoint_time} would change {change_rate:.0%} of the last {N} verified decisions — kernel and temperature held at current."*
- The DataOps Panel (Additional-D) renders this beside `rolling_accuracy`; legacy checkpoints (no tensor / pre-C3) show "not available for this checkpoint," never a fabricated number.

## 8. Option B hook — point-in-time replay (only if the roadmap chooses it later)
To honestly claim "at time k the system would have decided X," checkpoint k must also carry the kernel state:
- Add `dk_weights_json` + `temperature` to the V2 checkpoint (extends the C3 schema across protocol + SQLite + AGE + Memory) and to the write path (`_save_centroids_checkpoint`).
- Replace the ablation helper with `score_at_checkpoint`, restoring **μ, W, and τ** from checkpoint k.
- Response `analysis_type: "point_in_time_replay"`, `held_fixed: []`.
- Cost ≈ +2 days (schema migration ×3 stores + the restore path + tests).
- **Honesty gate:** legacy checkpoints written before this change have no DK/τ and can never be replayed — they must fall back to `centroid_ablation` and be labeled as such. So even under Option B, the ablation label and path remain; Option B is additive, not a replacement.

**Recommendation stands: ship A now, keep B as a labeled, additive upgrade.** The ablation is the signal that proves centroid compounding without overclaiming; point-in-time replay is a nice-to-have that only becomes truthful after the schema carries the kernel — and even then only for checkpoints written after it.
