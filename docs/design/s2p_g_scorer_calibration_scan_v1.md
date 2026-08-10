# S2P G-Scan — Scorer Calibration Mechanism v1

**Date:** 2026-08-04  
**Type:** Read-only code scan.

## Scope and conclusion

The S2P scorer is a nearest-centroid classifier with a softmax over negative
squared distances. It is not a threshold-only classifier and it is not an
RL model at prediction time. S2P has five categories, five actions, and eight
factor dimensions. The shared `ProfileScorer` kernel is instantiated with the
S2P-specific `S2PPreset`.

The calibration finding is therefore explained by centroid geometry: the new
perfect vector has `match_status≈1.0` and
`tax_regulatory_compliance≈1.0`, while the bootstrap `auto_approve` centroid
is `[0.95, ..., 0.95, ...]` and the other action centroids can remain closer
under the complete vector. For the S3 perfect vector
`[1.0, 0.0, 0.0, 0.033, 0.0, 0.35, 1.0, 0.5]`, the code bootstrap’s squared
L2 distances are approximately `0.460409` (`auto_approve`), `0.426189`
(`hold_for_review`), `1.156289` (`escalate_to_buyer`), `1.107189`
(`flag_leakage`), and `1.170589` (`refer_to_specialist`); therefore
`hold_for_review` is the nearest bootstrap centroid. The separate
auto-approve gate cannot turn a
non-`auto_approve` scorer action into `auto_approve`; it only accepts or blocks
the scorer’s recommendation.

Recommended lever: G2, a domain-correct centroid re-seed, followed by the
existing read-only spike and a gate check. G3 is also supported, but it is a
slower, outcome-driven adaptation path rather than a direct calibration reset.
G1 is applicable only to the separate confidence gate and cannot fix an action
that the centroid classifier did not select.

## 1. Vector → Action Path

### Entry point

The active endpoint is:

```text
POST /api/s2p/score
s2p-copilot/backend/app/routers/s2p.py:1921-2056
score_procurement_event(request, http_request)
```

The complete active sequence is:

```python
lookup_id = invoice.get("invoice_id") or request.event_id
context = _resolve_graph_context(lookup_id, http_request)
cross_copilot_signal = _apply_cross_copilot_signal(invoice, request)
computed_factors = compute_all_factors(invoice, context=context)
factor_vector = [computed_factors[name] for name in S2PDomainConfig.factors]
scorer = _sdk_scorer(http_request)

score_result = scorer.score(
    computed_factors,
    request.category,
    metadata=_invoice_decision_metadata(invoice),
)
```

`_resolve_graph_context()` is at
`s2p-copilot/backend/app/routers/s2p.py:138-161`. It calls
`reader.query_context(invoice_id, max_depth=2)`, rejects a list with no
domain-specific rows, and otherwise returns `{"neighbors": context_raw}`.
Graph failure returns `None`; the endpoint deliberately allows factor
computation to continue with degraded context.

`compute_all_factors()` is the factor-producing boundary. The scorer itself
receives a `dict[str, float]`, not the graph context. The S2P factor order is
defined in `S2PDomainConfig.factors`:

```python
[
    "match_status",
    "amount_variance_ratio",
    "duplicate_score",
    "supplier_exception_history",
    "payment_terms_impact",
    "commodity_index_correlation",
    "tax_regulatory_compliance",
    "environmental_risk",
]
```

### SDK handoff and factor-vector construction

`copilot-sdk/copilot_sdk/scoring/scorer.py:177-211`, complete `_predict()`:

```python
def _predict(
    self,
    factors: dict[str, float],
    category: str,
) -> tuple[int, dict[str, float], np.ndarray, Any, int, str, list[float]]:
    _reject_sample_provenance(factors)
    assert category in self._preset.shape.category_names, f"unknown category: {category}"
    unknown = set(factors) - set(self._preset.shape.factor_names)
    assert not unknown, f"unknown factors: {sorted(unknown)}"

    category_index = self._preset.shape.category_names.index(category)
    factor_values = {
        name: float(factors.get(name, 0.5))
        for name in self._preset.shape.factor_names
    }
    factor_vector = np.asarray(
        [factor_values[name] for name in self._preset.shape.factor_names],
        dtype=np.float64,
    )

    gae_result = self._scorer.score(factor_vector, category_index)
    action_index = int(gae_result.action_index)
    action = str(gae_result.action_name)
    if action != self._preset.shape.action_names[action_index]:
        action = self._preset.shape.action_names[action_index]

    probabilities = [float(value) for value in gae_result.probabilities]
    return (
        category_index,
        factor_values,
        factor_vector,
        gae_result,
        action_index,
        action,
        probabilities,
    )
```

The production `score()` path calls `_predict()`, then persists a Decision.
The read-only path used by the S3 calibration observation is
`CompoundingScorer.score_read_only()` at `scorer.py:404-426`:

```python
def score_read_only(
    self,
    factors: dict[str, float],
    category: str,
) -> ScoreResult:
    """Return a live scorer prediction without persisting a Decision."""
    (
        _category_index,
        factor_values,
        _factor_vector,
        gae_result,
        action_index,
        action,
        probabilities,
    ) = self._predict(factors, category)
    return ScoreResult(
        decision_id=f"preview-{uuid.uuid4().hex[:12]}",
        action=action,
        action_index=action_index,
        confidence=float(gae_result.confidence),
        probabilities=probabilities,
        category=category,
        factors=factor_values,
    )
```

### Exact action and confidence computation

`graph-attention-engine-v50/gae/profile_scorer.py:408-511`,
`ProfileScorer.score()`, is the action-producing mechanism. The complete
calculation body is:

```python
def score(self, f: np.ndarray, category_index: int) -> ScoringResult:
    assert 0 <= category_index < self.n_categories, (
        f"category_index {category_index} out of range [0, {self.n_categories})"
    )
    f = np.asarray(f, dtype=np.float64)
    assert f.shape == (self.n_factors,), (
        f"f.shape={f.shape} must be ({self.n_factors},)"
    )
    if not np.all(np.isfinite(f)):
        raise ValueError("Factor vector contains NaN or Inf values")
    if self.tau <= 0:
        raise ValueError(f"Temperature tau must be positive, got {self.tau}")

    mu_c = self.mu[category_index]
    assert mu_c.shape == (self.n_actions, self.n_factors), (
        f"mu_c.shape={mu_c.shape} != ({self.n_actions}, {self.n_factors})"
    )
    if not np.all(np.isfinite(mu_c)):
        raise ValueError(
            f"Centroids for category {category_index} contain NaN or Inf values"
        )

    f_work = f
    mu_c_work = mu_c
    if self.factor_mask is not None:
        f_work = f_work * self.factor_mask
        mu_c_work = mu_c_work * self.factor_mask

    phase2_override = False
    if (self._learning_strategy is not None
            and self._category_states is not None
            and self._category_states[category_index].phase == VARIANCE_LEARNING
            and self._dk_weights is not None):
        alpha = self._learning_strategy.shrinkage_schedule.compute_alpha(
            self._category_states[category_index]
        )
        w_tilde = compute_effective_weights(
            self._dk_weights[category_index], alpha
        )
        from gae.kernels import DiagonalKernel
        _phase2_kernel = DiagonalKernel.from_effective(w_tilde)
        phase2_mu = self.centroids[category_index]
        if self.factor_mask is not None:
            phase2_mu = phase2_mu * self.factor_mask
        distances = _phase2_kernel.compute_distance(f_work, phase2_mu)
        phase2_override = True

    if not phase2_override:
        if self.kernel in (KernelType.L2, KernelType.DIAGONAL):
            distances = self.scoring_kernel.compute_distance(f_work, mu_c_work)
        else:
            distances = self._compute_distances(
                f_work, mu_c_work, category_index
            )
    assert distances.shape == (self.n_actions,), (
        f"distances.shape={distances.shape} != ({self.n_actions},)"
    )

    logits = -distances / self.tau
    logits -= logits.max()
    exp_logits = np.exp(logits)
    probs = exp_logits / exp_logits.sum()
    assert probs.shape == (self.n_actions,), (
        f"probs.shape={probs.shape} != ({self.n_actions},)"
    )

    action_idx = int(np.argmax(probs))
    entropy_val = compute_entropy(probs)
    if len(probs) >= 2:
        sorted_p = np.sort(probs)[::-1]
        gap_val = float(sorted_p[0] - sorted_p[1])
    else:
        gap_val = 0.0
    return ScoringResult(
        action_index=action_idx,
        action_name=self.actions[action_idx],
        probabilities=probs,
        distances=distances,
        confidence=float(probs[action_idx]),
        entropy=entropy_val,
        confidence_gap=gap_val,
    )
```

For the default S2P path, `kernel=L2`, so the selected distance is the
squared Euclidean distance:

```python
diff = f - mu_c
return np.sum(diff ** 2, axis=1)
```

The S2P preset temperature is `0.1`. Confidence is exactly the probability
of the selected action, not a separate threshold score:
`confidence = max(probabilities)`.

### Supported actions

`copilot-sdk/copilot_sdk/scoring/presets/s2p.py:24-53` defines:

```text
auto_approve
hold_for_review
escalate_to_buyer
flag_leakage
refer_to_specialist
```

There is no `reject` action in the S2P scorer action set. “Reject” must be
represented by a supported escalation/referral action or by a downstream
policy outside this centroid classifier.

## 2. Centroids / Gate

### Centroid location and initialization

S2P initialization is assembled in
`copilot-sdk/copilot_sdk/scoring/scorer.py:215-303`:

```python
centroids = graph_store.load_latest_centroids(preset.name)
if centroids is None:
    centroids = np.array(preset.bootstrap_centroids, dtype=np.float64, copy=True)
```

Then `ProfileScorer` is constructed with that tensor. In the S2P application,
`s2p-copilot/backend/app/main.py:101-147` calls
`CompoundingScorer.from_preset("s2p", graph_store=selected_graph_store, ...)`.

Therefore the precedence is:

1. latest domain-scoped persisted centroid tensor from the configured
   `GraphStore`, if one exists;
2. otherwise the code-defined `S2PPreset.bootstrap_centroids`.

The JSON file `s2p-copilot/data/s2p_initial_centroids.json` is a seven-factor
fixture/preview artifact. `s2p-copilot/backend/app/routers/s2p_preview.py:132-136`
loads it for preview fixture data. It is not the `CompoundingScorer.from_preset`
bootstrap source. The active S2P preset supplies eight-factor bootstrap vectors.

### Exact code-defined S2P bootstrap centroids

`copilot-sdk/copilot_sdk/scoring/presets/s2p.py:86-100` defines one action
vector and copies the same five-action set across all five categories:

| Action | Centroid vector in factor order |
|---|---|
| `auto_approve` | `[0.95, 0.05, 0.02, 0.03, 0.50, 0.80, 0.95, 0.50]` |
| `hold_for_review` | `[0.70, 0.30, 0.10, 0.15, 0.40, 0.50, 0.80, 0.50]` |
| `escalate_to_buyer` | `[0.50, 0.60, 0.15, 0.30, 0.60, 0.30, 0.70, 0.50]` |
| `flag_leakage` | `[0.80, 0.50, 0.10, 0.40, 0.70, 0.20, 0.60, 0.50]` |
| `refer_to_specialist` | `[0.40, 0.40, 0.30, 0.50, 0.30, 0.40, 0.50, 0.50]` |

The tensor shape is `(5, 5, 8)`, with categories:
`price_variance`, `quantity_mismatch`, `duplicate_risk`, `contract_gap`,
and `format_compliance`.

The runtime centroid tensor is not provably equal to these bootstrap values
without reading the active GraphStore’s latest checkpoint. The code explicitly
allows a persisted checkpoint to override them.

### Active auto-approve gate

The active score endpoint calls `_should_auto_approve()` after the centroid
score has already selected an action. It is at
`s2p-copilot/backend/app/domains/s2p/auto_approve.py:10-75`:

```python
AUTO_APPROVE_THRESHOLDS = {
    "price_variance": 0.90,
    "quantity_mismatch": 0.85,
    "duplicate_risk": 0.92,
    "contract_gap": 0.88,
    "format_compliance": 0.80,
}

SPOT_CHECK_RATE = 0.02
AUTO_APPROVE_ACTION = "auto_approve"

def _default_spot_check() -> bool:
    return random.random() < SPOT_CHECK_RATE

def _should_auto_approve(
    category: str,
    confidence: float,
    conservation_status: str,
    recommended_action: str,
    spot_check_fn: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    threshold = AUTO_APPROVE_THRESHOLDS.get(category)
    if threshold is None:
        return {
            "auto_approved": False,
            "reason": "unknown_category",
            "threshold": None,
            "spot_check": False,
            "category": category,
        }

    if confidence < threshold:
        return {
            "auto_approved": False,
            "reason": "below_threshold",
            "threshold": threshold,
            "spot_check": False,
            "category": category,
        }

    if conservation_status != "GREEN":
        return {
            "auto_approved": False,
            "reason": "conservation_not_green",
            "threshold": threshold,
            "spot_check": False,
            "category": category,
        }

    if recommended_action != AUTO_APPROVE_ACTION:
        return {
            "auto_approved": False,
            "reason": "wrong_action",
            "threshold": threshold,
            "spot_check": False,
            "category": category,
        }

    spot_check = bool((spot_check_fn or _default_spot_check)())
    if spot_check:
        return {
            "auto_approved": False,
            "reason": "spot_check",
            "threshold": threshold,
            "spot_check": True,
            "category": category,
        }

    return {
        "auto_approved": True,
        "reason": "approved",
        "threshold": threshold,
        "spot_check": False,
        "category": category,
    }
```

The active endpoint invokes it at `s2p.py:2003-2013`:

```python
auto_approve = _should_auto_approve(
    request.category,
    core["confidence"],
    conservation_status,
    core["action"],
)
auto_approve["confidence"] = core["confidence"]
auto_approve["conservation_status"] = conservation_status
auto_approve["action"] = core["action"]
```

There is no active auto-approve gate configuration file or environment
variable in this implementation. The thresholds and 2% spot-check rate are
hardcoded constants. The separate
`s2p-copilot/backend/app/services/s2p_auto_approve_gate.py` is P40B shadow-only;
it is not the function imported by the active `/score` route. That service has
its own `AutoApproveConfig`, but its `enabled` default is `False` and its
`mode` supports only `disabled`/`shadow`.

### Gate conditions and ordering

The centroid action is computed first inside `scorer.score()`. The active
auto-approve check runs afterwards. Its conditions, in order, are:

1. category is known;
2. confidence meets the category threshold;
3. conservation status is exactly `GREEN`;
4. centroid-selected action is exactly `auto_approve`;
5. the random 2% spot check does not fire.

Thus a perfect factor vector can still produce `hold_for_review` because the
centroid classifier selected `hold_for_review`; the gate then returns
`reason="wrong_action"`. A perfect vector can also be blocked even after
selecting `auto_approve` if confidence is below the category threshold,
conservation is not `GREEN`, or the spot check fires.

## 3. Recalibration Levers

| Lever | Supported? | Code change needed? | How |
|---|---|---|---|
| Re-seed centroids | YES, but no turnkey S2P corpus command | YES for a safe labeled-corpus pipeline; NO if an operator directly writes a validated checkpoint | Build eight-factor, domain-labeled exemplars; compute `(5,5,8)` centroids; set/persist the S2P tensor; restart/reload so `load_latest_centroids("s2p")` selects it. `load_centroids_from_l5()` and the public centroid setter validate shape/range but do not compute centroids from labels. |
| Relearn via RL / outcomes | YES | NO for one-at-a-time existing `/api/s2p/outcome`; YES for a batch replay harness | `POST /api/s2p/outcome` calls `scorer.learn()`. `learn()` retrieves the stored factor vector and moves the predicted centroid and, on an override, the ground-truth centroid. It writes the outcome and checkpoint. There is no built-in “relearn all rows from a corpus” endpoint. |
| Config thresholds | PARTIAL | YES for the active gate | `AUTO_APPROVE_THRESHOLDS` and `SPOT_CHECK_RATE` are module constants. The active route has no config/env binding. The P40B shadow gate supports runtime `configure()`, but it cannot change the centroid-selected action and is shadow-only. |

### Exact learning update

`copilot-sdk/copilot_sdk/scoring/scorer.py:582-833` is the complete
`CompoundingScorer.learn()` path. The key calls are:

```python
decision = self._graph_store.get_decision(decision_id, domain=self._domain)
actual_index = self._preset.shape.action_names.index(actual_action)
predicted_index = int(_decision_field(decision, "recommended_index", 0))
recommended_action = str(
    _decision_field(decision, "recommended_action",
                   _decision_field(decision, "action", ""))
)
is_correct = actual_action == recommended_action
factor_vector = np.asarray(
    _decision_field(decision, "factor_vector", []), dtype=np.float64
)
category_index = int(_decision_field(decision, "category_index", 0))
confidence = float(_decision_field(decision, "confidence", 0.0))

update_result = self._scorer.update(
    f=factor_vector,
    category_index=category_index,
    action_index=predicted_index,
    correct=is_correct,
    gt_action_index=None if is_correct else actual_index,
    confidence=confidence,
)

self._graph_store.write_outcome(
    decision_id=decision_id,
    actual_action=actual_action,
    is_correct=is_correct,
    metadata=outcome_metadata,
    domain=self._domain,
)
self._refresh_dk_after_learn()
```

`ProfileScorer.update()` uses the following exact learning equations and
guards (`graph-attention-engine-v50/gae/profile_scorer.py:787-1009`):

```python
eta_eff = self.eta / (1.0 + self.decay * count)
eta_neg_eff = self.eta_neg / (1.0 + self.decay * count)

if correct:
    delta_vector = eta_eff * self._compute_gradient(f, self.mu[c, a, :])
    self.mu[c, a, :] += delta_vector
else:
    if gt_action_index is None:
        delta_vector = -push_rate * self._compute_gradient(f, self.mu[c, a, :])
        self.mu[c, a, :] += delta_vector
    else:
        delta_vector = -push_rate * self._compute_gradient(f, self.mu[c, a, :])
        self.mu[c, a, :] += delta_vector
        gt_delta_vector = pull_rate * self._compute_gradient(f, self.mu[c, gt, :])
        self.mu[c, gt, :] += gt_delta_vector

self.mu[c, :, :] = np.clip(self.mu[c, :, :], 0.0, 1.0)
```

The update is S2P-scoped because `CompoundingScorer` uses the S2P preset and
the graph store domain is `s2p`; the shared engine code is reused, but the
centroid tensor and outcome history are domain-selected.

## 4. Corpus Provenance

### Initial source

The initial seven-factor fixture corpus is generated by
`s2p-copilot/generators/s2p_synthetic.py`. It contains:

```python
SEED = 20260511
...
ACTION_CENTROIDS = {...}
...
def _factor_dict(category: str, action: str, index: int, rng: random.Random) -> dict[str, float]:
    centroid = build_centroids()[category][action]
    factors = []
    for value in centroid:
        jitter = rng.uniform(-0.025, 0.025)
        factors.append(_clip(value + jitter))
    return dict(zip(FACTORS, factors))
```

The generated invoices are written to
`s2p-copilot/data/synthetic_invoices.json` with
`ground_truth_action` and `provenance="sample"`; the generated centroid file
is `s2p-copilot/data/s2p_initial_centroids.json`.

Classification: **FIXTURE-DERIVED** for the initial calibration artifacts.
The generator explicitly derives factor vectors around action centroids and
the generated files are labeled sample data. They are not real labeled
procurement outcomes and must not be used as the oracle for the S3 semantics.

The current runtime tensor is **UNKNOWN without a read of the active
GraphStore**: startup may load a persisted learned checkpoint, or may use the
fixture-shaped code bootstrap. The source does not prove that any checkpoint
contains real outcomes. Therefore:

| Question | Result |
|---|---|
| Initial calibration corpus | FIXTURE-DERIVED |
| No-oracle risk | YES |
| Current centroids equal initial seed? | UNKNOWN from code scan; `load_latest_centroids("s2p")` can override them |
| Evidence of a real-outcome corpus | None in the scanned initialization path |

The `/api/s2p/outcome` path can subsequently create real outcome-driven
updates, but that is a learning mechanism, not evidence that the existing
initial seed was real-outcome calibrated.

## 5. Isolation

| Question | Result |
|---|---|
| Per-copilot centroids | YES — S2P-specific preset, factor names, action/category names, and domain key `s2p` |
| Recalibrating S2P disturbs SOC/Trading/DataOps? | NO, assuming the checkpoint/write is domain-scoped and the operator does not write another domain’s key |
| Storage location | Runtime in `ProfileScorer.mu`; persisted through the S2P `GraphStore` centroid/checkpoint APIs under domain `s2p` |
| Shared code | YES — `CompoundingScorer` and `ProfileScorer` implementation are shared; the centroid data is not one global action tensor |

`CompoundingScorer.from_preset()` calls
`graph_store.load_latest_centroids(preset.name)`, where `preset.name == "s2p"`.
Learning checkpoints likewise carry `self._domain`. Recalibration is
therefore isolated at the data/configuration layer, while changes to shared
scoring code would be cross-copilot risk.

## 6. Gate Interaction

### Conservation gate

For the active score path, conservation status is read after the scorer has
produced the action and confidence. `score_procurement_event()` obtains the
cached status at `s2p.py:1989`, then calls `_should_auto_approve()` at
`s2p.py:2005`.

The conservation status calculation is read-only and uses
`_current_conservation_status()` at `s2p.py:925-941`:

```python
counts = _cached_conservation_counts(graph_store, _graph_domain(graph_store))
check = conservation_status(
    verified_count=int(counts["verified_count"]),
    correct_count=int(counts["correct_count"]),
    total_decisions=int(counts["total_decisions"]),
    penalty_ratio=float(counts["penalty_ratio"]),
)
return str(check.status)
```

The active gate can override an apparent auto-approve recommendation to a
non-approved result: `conservation_status != "GREEN"` returns
`reason="conservation_not_green"`. It can also block on confidence, wrong
action, unknown category, or spot check.

### Why the S3 perfect vector became `hold_for_review`

The S3 vector was passed to the scorer’s centroid classifier. The classifier
does not have a special “all factors high means auto approve” rule. It compares
all eight coordinates to the five action centroids for the request category,
then applies softmax. The old stub distributions (`match_status` in
`{0.1, 0.6, 0.9}` and tax in `{0.15, 0.8}`) shaped the fixture/bootstrap
examples. Replacing them with faithful values near `1.0` changes the vector’s
distance geometry. If the nearest centroid is `hold_for_review`, the active
gate necessarily reports `wrong_action`; no confidence-threshold adjustment
can change that class selection.

This is calibration drift from a factor-semantics change, not evidence that the
new graph factors failed.

## 7. Calibration Ladder Assessment

| Rung | Applicable? | Effort | Risk |
|---|---|---|---|
| G1 threshold retune | PARTIAL | Low | Cannot change a non-`auto_approve` centroid result; lowering thresholds can only admit an already selected `auto_approve` and can weaken safety |
| G2 centroid re-seed | YES — recommended | Medium | Requires domain-correct labels and an atomic/domain-scoped checkpoint; fixture-derived labels would repeat the no-oracle failure |
| G3 relearn via RL/outcomes | YES | Medium/high | Supported one outcome at a time; slow convergence, conservation pauses, outcome quality, and path-dependent centroid drift |
| G4 analytic regions | YES only as a new policy layer | Medium/high | Would require new code and may duplicate/conflict with centroid scoring; useful for explicit procurement hard constraints |
| G5 retreat/accept holds | YES | Low | Safe but leaves perfect compliant invoices conservatively held and does not resolve new-factor calibration |

**Recommended rung: G2, with G3 as the operational maintenance path.**

G2 directly addresses changed factor semantics. It should use a small,
domain-labeled, non-fixture corpus containing perfect/compliant,
price-mismatch, quantity-mismatch, non-compliant, and combined-bad examples.
G3 can then adapt the seeded geometry from verified analyst outcomes after the
new factor contract is live. G1 should be used only after action geometry is
correct.

## 8. Design Suggestions

### a) Exact steps for G2

1. Define the S2P action policy independently of the old fixture:
   perfect+compliant → `auto_approve`; mismatch → `hold_for_review` or
   `escalate_to_buyer`; non-compliant → `refer_to_specialist` or
   `escalate_to_buyer`; both-bad → `refer_to_specialist`.
2. Generate each exemplar through the active factor path, including the two
   graph-native factors and all eight factor names in canonical order.
3. Compute per-category/per-action means or explicitly authored centroids from
   those labeled exemplars. Do not use `ground_truth_action` from
   `synthetic_invoices.json` as the label source.
4. Validate tensor shape `(5, 5, 8)`, finite values, and `[0,1]` bounds.
5. Persist only the S2P-domain checkpoint or load it through the existing
   validated centroid API. Do not modify SOC or another copilot’s domain.
6. Restart/reload the scorer and confirm the loaded centroid tensor is the
   intended one before scoring.

### b) Corpus required

The minimum useful corpus is a real or explicitly domain-reviewed labeled set
covering all five S2P categories and all actions that should be reachable.
Each row needs: category, eight-factor vector, domain-correct action label,
factor provenance, and reviewer/outcome provenance. Fixture rows may be used
only as data-shape smoke tests, never as calibration truth.

### c) Verification spike

Run the same read-only factor-vector sample used by S3 and record before/after
action, confidence, probabilities, and centroid distances:

| Case | Required result |
|---|---|
| Perfect + compliant | `auto_approve`, confidence above the category gate threshold, unless spot-checked |
| Price mismatch | no `auto_approve`; escalation/hold |
| Quantity mismatch | no `auto_approve`; escalation/hold |
| Non-compliant | no `auto_approve`; referral/escalation |
| Both bad | no `auto_approve`; referral/escalation |

Also verify: changing only PO amount moves `match_status` and the shared
amount-variance factor; changing only compliance moves tax compliance; other
factor values remain stable; conservation remains `GREEN` before enabling any
automatic approval behavior; and no non-S2P centroid changes occur.

### d) Risks

- Re-seeding on the old fixture labels will encode the same inverted/stub
  semantics under a new property shape.
- G1 threshold lowering can mask wrong centroid selection rather than fix it.
- A persisted latest checkpoint silently takes precedence over code bootstrap;
  deployment must log or expose the loaded checkpoint identity and factor-name
  hash.
- The active gate is currently hardcoded while a separate shadow gate has
  runtime configuration; changing the wrong gate will have no production
  effect.
- S2P has no `reject` action in the centroid action set; domain policy must map
  “reject” to an existing action or add a separately reviewed policy layer.
- Learning from synthetic/preseed outcomes is explicitly treated differently
  in `CompoundingScorer.learn()` and cannot establish real calibration quality.

### e) Scanner observations

1. The scorer is a hybrid only because the centroid output is followed by a
   separate policy gate; the core action mechanism is pure nearest-centroid
   softmax.
2. The active S2P score endpoint persists Decisions, while S3 correctly used
   `score_read_only()` for a disposable, non-persisting calibration observation.
3. The preview route reads `s2p_initial_centroids.json`, but the active scorer
   startup reads GraphStore checkpoints or `S2PPreset.bootstrap_centroids`.
   Treating those as the same calibration source would be incorrect.
4. The existing outcome route supplies the supported G3 learning path, but no
   batch “rebuild centroids from labeled corpus” operation was found.

## Cleanup

Scripts deleted: N/A (read-only)  
Files modified: NO
