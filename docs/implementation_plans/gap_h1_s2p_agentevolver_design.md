# GAP-H1 S2P AgentEvolver Design

READY_FOR_PROMPT_B: YES

## 1. Executive Summary

GAP-H1 adds an S2P-specific operational AgentEvolver layer that can generate, shadow-test, select, and safely promote rule-template variants such as auto-approval thresholds and escalation triggers. This is not centroid evolution. It is an operational-parameter evolution layer that sits beside the existing S2P score/outcome path.

Prompt B should implement:

- S2P backend rule templates for operational parameters.
- An in-memory shadow runner for S2P decisions.
- Autonomous promotion using the SDK `AutonomousPromotionGate`.
- Context-aware variant selection using the SDK `ContextAwareSelector`.
- Fixture-backed demo state for deterministic storyboard visibility.
- Tests proving P16 separation: rule templates must not import or mutate centroids, `ProfileScorer`, or centroid update paths.

Explicitly deferred:

- Frontend implementation.
- Centroid evolution integration.
- Live graph reseeding or persistent production promotion storage.
- Scorer constructor changes unless Prompt B re-verifies they are safe.
- Importing SOC code into S2P or SDK.

## 2. API Surface Summary

### SDK Exports

`copilot_sdk.evolution.__init__` exports `AutonomousPromotionGate`, `PromotionDecision`, `ContextAwareSelector`, `SelectionContext`, `StepCredit`, `StepCreditAssigner`, and `StepRecord` from the advanced evolution modules.

Evidence: `copilot_sdk/evolution/__init__.py` imports and exposes these classes in `__all__`.

### AutonomousPromotionGate

Source: `copilot_sdk/evolution/autonomous_promotion.py`.

Discovered API:

```python
AutonomousPromotionGate(
    min_shadow_batches: int = 3,
    min_win_rate: float = 0.7,
    base_gate: Any | None = None,
)

evaluate(
    variant: dict[str, Any],
    conservation_status: str,
    shadow_results: list[dict[str, Any]],
) -> PromotionDecision
```

`PromotionDecision` is a frozen dataclass with class constants `PROMOTE = "promote"`, `CONTINUE = "continue"`, `BLOCK = "block"`, and instance fields `action`, `reason`, and `evidence` (`copilot_sdk/evolution/autonomous_promotion.py:9-20`).

Conservation handling:

- `evaluate()` uppercases the supplied status (`autonomous_promotion.py:42`).
- Any status other than `GREEN` returns `BLOCK` with reason `"conservation"` (`autonomous_promotion.py:48-49`).
- Insufficient shadow batches returns `CONTINUE` with reason `"insufficient_shadow_batches"` (`autonomous_promotion.py:51-52`).
- Regressions return `CONTINUE` with reason `"regression"` (`autonomous_promotion.py:64-65`).
- Low win rate returns `CONTINUE` with reason `"win_rate"` (`autonomous_promotion.py:66-67`).
- Passing all checks returns `PROMOTE` with reason `"criteria_met"` (`autonomous_promotion.py:79`).

Shadow-result evidence:

- `_win_rate()` prefers per-batch `"better"`, then `"win"`, then `"is_win"`, then `accuracy > baseline_accuracy` (`autonomous_promotion.py:82-99`).
- It falls back to `variant["win_rate"]` only when no usable shadow evidence exists (`autonomous_promotion.py:98-102`).
- `_regressions()` treats `regression=True` and `accuracy < baseline_accuracy` as regressions (`autonomous_promotion.py:105-113`).

### ContextAwareSelector

Source: `copilot_sdk/evolution/context_selector.py`.

Discovered API:

```python
@dataclass(frozen=True)
class SelectionContext:
    category: str
    recent_accuracy: float
    conservation_phase: str
    decision_count: int
    time_of_day: float = time.time()

ContextAwareSelector(exploration_bonus: float = 1.0)
select(variants: list[dict[str, Any]], context: SelectionContext) -> dict[str, Any]
record_failure(category: str, variant_id: str) -> None
```

Behavior:

- Empty variant list raises `ValueError` (`context_selector.py:26-28`).
- A single variant is returned unchanged (`context_selector.py:29-30`).
- Base score uses `ucb_score`, then `win_rate`, otherwise `0.5` (`context_selector.py:58-63`).
- Early/explore phase, or `decision_count < 10`, adds exploration bonus favoring lower evidence count (`context_selector.py:45-46`).
- Mature/learning phase adds category evidence bonus (`context_selector.py:47-48`, `context_selector.py:73-87`).
- Other phases add a small proven-evidence bonus (`context_selector.py:49-50`).
- `record_failure()` stores `(category, variant_id)` and `_score()` subtracts a penalty for failed variants in the same category (`context_selector.py:38-39`, `context_selector.py:52-55`).

Known nuance for Prompt B: `decision_count < 10` forces early behavior even if `conservation_phase` is explicitly converged (`context_selector.py:45`). Prompt B should compute `SelectionContext` with enough `decision_count` for converged demo cases.

### StepCreditAssigner

Source: `copilot_sdk/evolution/credit_attribution.py`.

Discovered API:

```python
HALF_LIFE = 30
CHAIN_DISCOUNT = 0.5

@dataclass(frozen=True)
class StepRecord:
    step_id: str
    step_type: str
    timestamp: float
    metadata: dict[str, Any] = {}

@dataclass(frozen=True)
class StepCredit:
    step_id: str
    credit: float
    decay_factor: float

StepCreditAssigner(
    half_life: int = HALF_LIFE,
    chain_discount: float = CHAIN_DISCOUNT,
)
assign(chain: list[StepRecord], outcome_reward: float) -> list[StepCredit]
```

Behavior:

- Defaults are `HALF_LIFE = 30` and `CHAIN_DISCOUNT = 0.5` (`credit_attribution.py:10-11`).
- Empty chain returns `[]` (`credit_attribution.py:37-39`).
- Non-positive half-life is guarded by `max(float(half_life), 1e-9)` (`credit_attribution.py:33-35`).
- Output preserves original chain order while weighting by timestamp recency and time decay (`credit_attribution.py:41-72`).

### Existing EvolutionConfig / Scorer Integration Status

No `EvolutionConfig` or `_evolution_config` exists in the SDK scorer. The actual `CompoundingScorer.__init__` accepts `credit_assigner`, `exploration_policy`, and `evolve`, but no `evolution_config` (`copilot_sdk/scoring/scorer.py:68-75`). `from_preset()` also accepts `credit_assigner`, `exploration_policy`, and `evolve`, but no `evolution_config` (`copilot_sdk/scoring/scorer.py:93-103`).

Existing `evolve=True` wiring:

- `self._evolve` and `self._evolver` are initialized in `__init__` (`scorer.py:87-91`).
- Learn increments `_evolve_count` and runs evolution every 20 learns (`scorer.py:275-278`).
- `_setup_evolution()` builds `AgentEvolver` with `DefaultShadowRunner()` and `DefaultPromotionGate()` (`scorer.py:518-523`).
- It registers SDK toy rules: `ThresholdRule`, `FactorWeightRule`, and `ActionBiasRule` (`scorer.py:524-527`).
- `_run_evolution()` pulls verified decisions from the graph store and calls `self._evolver.evolve(..., conservation_state=...)` (`scorer.py:529-543`).

Prompt B design decision: do not alter SDK scorer integration. Use standalone SDK components inside S2P backend operational-evolution code. This keeps existing `evolve=True` unchanged.

### CompoundingScorer.from_preset("s2p") State

Direct discovery output:

- Shape: `(5, 5, 7)`.
- Phase: `A`.
- Alpha: `0.0`.
- `_evolution_config`: absent.
- `_evolver`: present.
- Preset categories: `price_variance`, `quantity_mismatch`, `duplicate_risk`, `contract_gap`, `format_compliance`.
- Preset actions: `auto_approve`, `hold_for_review`, `escalate_to_buyer`, `flag_leakage`, `refer_to_specialist`.
- Preset factors: `match_status`, `amount_variance_ratio`, `duplicate_score`, `supplier_exception_history`, `payment_terms_impact`, `commodity_index_correlation`, `tax_regulatory_compliance`.

## 3. S2P Current-State Summary

### S2P Scorer Construction Path

S2P backend `app.main` builds the SDK scorer with:

```python
CompoundingScorer.from_preset(
    "s2p",
    db_path=":memory:",
    graph_store=_S2PGraphStore(),
    reward_function=S2PRewardFunction(),
)
```

Evidence: `s2p-copilot/backend/app/main.py:57-63`.

The scorer is stored as `app.state.scorer`, and `app.state.graph_store` points at `app.state.scorer.graph_store` (`backend/app/main.py:65-68`). This is the safest place for Prompt B to attach an S2P evolution service without changing score semantics.

There is also an older domain-level `ProfileScorer` singleton in `backend/app/domains/s2p/scorer.py`. It builds `gae.ProfileScorer` from `S2PDomainConfig` (`backend/app/domains/s2p/scorer.py`, observed full file). Prompt B should not build the new operational evolution layer on that singleton because the active router score path uses `app.state.scorer`.

### S2P Score / Outcome Path

Score route:

- `ScoreRequest` contains procurement inputs and optional direct factor overrides (`backend/app/routers/s2p.py:302-320`).
- `POST /api/s2p/score` validates category, computes factors, fetches the SDK scorer from app state, and calls `scorer.score(computed_factors, request.category, metadata=...)` (`backend/app/routers/s2p.py:336-382`).
- It writes graph decision data best-effort and returns `ScoreResponse` with action, confidence, probabilities, factor vector, factor names, and decision id (`backend/app/routers/s2p.py:386-410`).

Learn/outcome routes:

- `POST /api/learn` calls `_learn_with_scorer(_sdk_scorer(...), decision_id, actual_action, outcome, context)` (`backend/app/routers/s2p.py:446-460`).
- `POST /api/s2p/outcome` validates outcome/action/factor vector, writes graph outcome best-effort, ensures the decision exists in the SDK graph store, calls `_learn_with_scorer`, and returns `learning_applied` (`backend/app/routers/s2p.py:463-510`).

Shadow runner hook:

- Prompt B should use the same factor computation and `scorer.score()` semantics as `/api/s2p/score`, but in a separate shadow path that does not call `scorer.learn()` and does not write back to the production graph store unless explicitly asked.

### S2P Categories / Actions / Factors

S2P config defines:

- Actions: `auto_approve`, `hold_for_review`, `escalate_to_buyer`, `flag_leakage`, `refer_to_specialist` (`backend/app/domains/s2p/config.py:29-36`).
- Factors: `match_status`, `amount_variance_ratio`, `duplicate_score`, `supplier_exception_history`, `payment_terms_impact`, `commodity_index_correlation`, `tax_regulatory_compliance` (`backend/app/domains/s2p/config.py:38-47`).
- Tensor dimensions: `N_CATEGORIES = 5`, `N_ACTIONS = 5`, `N_FACTORS = 7` (`backend/app/domains/s2p/config.py:64-67`).
- `PENALTY_RATIO = 5.0` and `LEARNING_ENABLED = False` (`backend/app/domains/s2p/config.py:69-74`).

Direct config command confirmed:

- Categories: `price_variance`, `quantity_mismatch`, `duplicate_risk`, `contract_gap`, `format_compliance`.
- Actions: `auto_approve`, `hold_for_review`, `escalate_to_buyer`, `flag_leakage`, `refer_to_specialist`.
- Factors: the seven names above.

### Existing Operational Parameters

Existing:

- Per-category auto-approve confidence thresholds are in `CompositeDiscriminant.CATEGORY_CONFIDENCE_THRESHOLDS` (`backend/app/framework/composite_gate.py:43-52`).
- Global `CONFIDENCE_THRESHOLD`, `MARGIN_THRESHOLD`, `MIN_CAT_COUNT`, and `AUTO_APPROVE_SAFETY_THRESHOLD` exist (`backend/app/framework/composite_gate.py:37-41`).
- The auto-approve gate checks category confidence, margin, category maturity, and the protected `auto_approve` safety threshold (`backend/app/framework/composite_gate.py:146-180`).
- Learning gate thresholds are `MIN_VERIFIED_DECISIONS = 50`, `MIN_OVERRIDE_PRECISION = 0.40`, and sigma thresholds (`backend/app/services/s2p_learning_gate.py:24-31`).
- Preview endpoints provide queue, conservation, compounding, suppliers, and config data under `/api/s2p/preview/*` (`backend/app/routers/s2p_preview.py:313-493`).
- Static S2P evidence rules exist at `/api/s2p/evidence/rules` (`backend/app/routers/s2p_evidence.py:82-119`).

Missing or not yet first-class for S2P AgentEvolver:

- No S2P operational rule-template module.
- No S2P shadow runner for operational variants.
- No S2P autonomous promotion service.
- No fixture-backed S2P evolution state file.
- No router exposing S2P evolution variants/history/promoted data from these operational templates.
- No dedicated routing-priority or evidence-ordering parameter object. Current control-tower route/evidence data can be used as source material but needs a new rule-template abstraction.

### Existing Tests / Baseline

Baseline command requested from repo root:

```powershell
python -m pytest backend\tests\ -q --timeout=120
```

Result: failed during collection because `backend/tests/test_s2p_ct_pvg_integration.py` and `backend/tests/test_s2p_suppliers.py` read `Path("../data/...")`, which resolves incorrectly from the repo root.

Repo-rule baseline from `s2p-copilot/backend`:

```powershell
python -m pytest tests\ -q --timeout=120
```

Result: `361 passed`, with pytest cache write warnings.

SDK baseline:

```powershell
python -m pytest tests\ -q --timeout=120
```

Result: `446 passed`.

## 4. S2P Rule Template Architecture

Prompt B should introduce a backend-only S2P operational rule-template layer.

Suggested protocol/interface:

```python
class RuleTemplate(Protocol):
    name: str
    success_metric_name: str
    applicable_categories: tuple[str, ...]

    def generate_variants(self) -> list[dict[str, Any]]:
        ...

    def evaluate_batch(
        self,
        variant: dict[str, Any],
        decisions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ...
```

Variant fields should include:

- `variant_id`
- `template_name`
- `parameters`
- `category`
- `description`
- `created_at`
- `source`

`evaluate_batch()` should return per-batch evidence compatible with `AutonomousPromotionGate`, including:

- `better`
- `win`
- `accuracy`
- `baseline_accuracy`
- `regression`
- `sample_size`
- `metric_name`
- `baseline_metric`
- `variant_metric`

### P16 Separation Rule

Mandatory:

- S2P rule templates operate only on operational parameters.
- S2P rule templates never import or use centroids, `ProfileScorer`, `update_centroid`, `gae_scorer.centroids`, `_scorer.centroids`, `save_centroids`, or SDK centroid warm-start utilities.
- Centroid evolution remains separate in SDK scorer evolution and is not allowed to see S2P operational variants.
- Operational variants must not call `scorer.learn()` or mutate the production graph store during shadow evaluation.

Prompt B must include a P16 enforcement test that scans the new `rule_templates.py` file for forbidden symbols: `centroid`, `ProfileScorer`, `update_centroid`, `gae_scorer`, `save_centroids`, and `warm_start`.

## 5. S2P Rule Templates

### 1. auto_approve_threshold_sweep

- Operational parameter varied: per-category confidence threshold.
- Existing location: `CompositeDiscriminant.CATEGORY_CONFIDENCE_THRESHOLDS` (`backend/app/framework/composite_gate.py:46-52`).
- Prompt B introduction: read thresholds through a new S2P evolution policy object in `backend/app/domains/s2p/evolution/rule_templates.py`; do not mutate `CompositeDiscriminant` globals in shadow mode.
- Variant range: category threshold ±0.03 and ±0.06, clamped to `[0.70, 0.97]`.
- Success metric: `safe_auto_approve_rate`, defined as auto-approve wins with no false approve regression.
- Category applicability: all five S2P categories.
- Shadow batch: 25 to 50 historical or fixture decisions for one category.
- Story sample: threshold moves `0.85 -> 0.91` for `price_variance`.

### 2. routing_priority_permutation

- Operational parameter varied: order for routing actions such as `hold_for_review`, `escalate_to_buyer`, `flag_leakage`, and `refer_to_specialist`.
- Current state: no dedicated routing-priority config found. Control tower classifies route/evidence panels in static scenario data (`backend/app/routers/s2p_control_tower.py` discovery output showed route and priority fields).
- Prompt B introduction: add `S2P_ROUTING_PRIORITIES` or an equivalent fixture-backed policy object in new evolution files, not in scorer code.
- Variant range: deterministic permutations that prioritize high-loss outcomes to `escalate_to_buyer` or `flag_leakage`.
- Success metric: `routing_precision`.
- Category applicability: `contract_gap`, `duplicate_risk`, `price_variance`.
- Shadow batch: decisions with known `ground_truth_action`.

### 3. escalation_trigger_amount

- Operational parameter varied: amount-at-risk or invoice amount threshold for escalation.
- Current state: score/outcome request carries `amount`, `at_risk`, and `recovery_pct` (`backend/app/routers/s2p.py:426-428`, `backend/app/routers/s2p.py:501-505`); no dedicated evolution parameter found.
- Prompt B introduction: add threshold definitions under S2P evolution rule templates.
- Variant range: e.g. `amount >= 50000`, `75000`, `100000`, plus category-specific multipliers.
- Success metric: `high_value_capture_rate` with regression guard for over-escalation.
- Category applicability: `price_variance`, `contract_gap`, `duplicate_risk`.
- Shadow batch: decisions with amount and verified analyst action.

### 4. supplier_flag_sensitivity

- Operational parameter varied: supplier exception-history sensitivity.
- Existing input: `supplier_exception_history` exists in `ScoreRequest` and S2P factors (`backend/app/routers/s2p.py:317`, `backend/app/domains/s2p/config.py:42`).
- Existing fixture display: supplier exception cluster rule is represented in `/api/s2p/evidence/rules` (`backend/app/routers/s2p_evidence.py:85-91`).
- Prompt B introduction: rule template parameter such as `supplier_exception_threshold`.
- Variant range: `0.20`, `0.30`, `0.40`, plus recent-window counts if fixture data has supplier history.
- Success metric: `supplier_exception_precision`.
- Category applicability: `duplicate_risk`, `contract_gap`, `price_variance`.
- Shadow batch: grouped by `supplier_id`.

### 5. evidence_presentation_order

- Operational parameter varied: evidence panel ordering or explanatory priority.
- Current state: evidence rule data is static and returns rule state/action/factor but no ordered panel policy (`backend/app/routers/s2p_evidence.py:82-119`).
- Prompt B introduction: fixture-backed order lists under evolution state, e.g. `["factor_fingerprint", "similar_invoices", "audit_trail"]`.
- Variant range: prioritize supplier, contract, tax, or commodity panels based on category.
- Success metric: `analyst_confirmation_rate` or `review_resolution_rate`.
- Category applicability: all categories, with category-specific panel defaults.
- Shadow batch: fixture decision narratives; should not claim real production outcome proof.

## 6. Shadow Runner Design

Prompt B should create an S2P operational shadow runner, for example:

```text
s2p-copilot/backend/app/domains/s2p/evolution/shadow_runner.py
```

Triggering:

- Manual API call in Prompt B router, e.g. `POST /api/s2p/evolution/sweep`.
- Fixture load on startup only when `S2P_EVOLUTION_FIXTURE` is set.
- No automatic production trigger by default.

Batch size:

- Default `min_shadow_batches = 3` for promotion-gate compatibility.
- Each shadow batch should contain 10 to 25 decisions.
- A full sweep should evaluate at least 30 decisions where fixture data is available.

Decision record format:

```json
{
  "decision_id": "S2P-...",
  "invoice_id": "INV-...",
  "category": "price_variance",
  "recommended_action": "hold_for_review",
  "ground_truth_action": "auto_approve",
  "confidence": 0.87,
  "amount": 120000.0,
  "supplier_id": "SUP-001",
  "factors": {
    "match_status": 0.91,
    "amount_variance_ratio": 0.12
  },
  "metadata": {}
}
```

Baseline and variant comparison:

- Baseline: current operational parameter value.
- Variant: generated parameter value from a rule template.
- `accuracy`: percentage of decisions where the variant action matches `ground_truth_action` or improves the target metric.
- `baseline_accuracy`: same metric under baseline parameters.
- `better`: `accuracy > baseline_accuracy`.
- `win`: same as `better` unless a template has a metric-specific tie breaker.
- `regression`: true when variant violates a safety guard, e.g. higher false-auto-approval rate, lower accuracy, or category-specific precision drop.

Use of existing score path:

- For scoring data, reuse factor computation and action names from `S2PDomainConfig`.
- Do not call `scorer.learn()`.
- Do not mutate `scorer.gae_scorer.centroids` or graph-store decisions.
- For fixture-only shadow evaluation, the runner may use precomputed `recommended_action`, `ground_truth_action`, confidence, and factors from fixture data.

Storage:

- In-memory first: service object on `app.state.s2p_evolution`.
- Optional fixture JSON load for demo: `backend/data/s2p_evolution_fixture.json`.
- Do not persist promotions to graph in Prompt B unless explicitly requested later.

StepCreditAssigner:

- Optional for explainability only.
- If used, convert rule-template evaluation stages to `StepRecord`s and distribute the outcome reward.
- Do not use credit assignment to mutate any rule or centroid state.

## 7. Autonomous Promotion Design

Call site:

- `S2PEvolutionService.evaluate_promotion(template_name, variant_id)` after shadow results are available.
- Internally call `AutonomousPromotionGate.evaluate(variant, conservation_status, shadow_results)`.

Conservation status source:

- Preferred source: S2P learning gate route/service status, using `evaluate_s2p_learning_gate()` semantics.
- Evidence: S2P learning gate returns `status` values `"GREEN"`, `"AMBER"`, or `"RED"` (`backend/app/services/s2p_learning_gate.py:34-38`) and blocks RED/noise, insufficient decisions, and low override precision before returning green/amber status (`backend/app/services/s2p_learning_gate.py:64-103`).
- For fixture/demo state, use fixture `conservation_status`, defaulting to `"AMBER"` unless the fixture intentionally demonstrates safe promotion.

What counts as GREEN:

- `conservation_status == "GREEN"` exactly after uppercasing.
- `AMBER`, `RED`, and `UNKNOWN` must never promote because `AutonomousPromotionGate` blocks any non-GREEN status (`autonomous_promotion.py:48-49`).

Promotion criteria:

- Required shadow batches: default `3`.
- Required win rate: default `0.7`.
- Regression handling: any explicit regression or accuracy below baseline keeps the decision at `CONTINUE`.
- Promotion output should include `PromotionDecision.action`, `reason`, and `evidence`.

Safety:

- Autonomous promotion is safe only for operational rule parameters.
- Promotion means "select this operational variant as current"; it does not update centroids and does not call production learn.
- Prompt B should name the fixture field `conservation_pass: true` only when `conservation_status == "GREEN"` and promotion criteria pass.

## 8. Context-Aware Selection Design

Call site:

- `S2PEvolutionService.select_variant(template_name, category)` before running a shadow batch or choosing a displayed candidate.

SelectionContext values:

- `category`: S2P category from the decision batch.
- `recent_accuracy`: recent accuracy from in-memory shadow results or `/api/s2p/performance/summary`.
- `conservation_phase`: use scorer `get_phase()` if using SDK scorer; direct discovery for `from_preset("s2p")` returned phase `A`. For S2P learning gate status, map `GREEN -> mature`, `AMBER -> early`, `RED -> early`.
- `decision_count`: verified decision count from performance summary or fixture count.
- `time_of_day`: default is fine.

How values affect selection:

- Early phase or `decision_count < 10` favors lower-evidence variants through exploration bonus (`context_selector.py:45-46`).
- Mature phase adds category evidence (`context_selector.py:47-48`).
- Converged/default phase gives a small bonus to high-evidence variants (`context_selector.py:49-50`).
- Failures should call `record_failure(category, variant_id)` so the selector downweights that variant in later selections (`context_selector.py:38-39`, `context_selector.py:52-55`).

Prompt B caution:

- For a converged storyboard, set `decision_count >= 10`; otherwise low decision count will still trigger early exploration.

## 9. Demo Fixture Design

Recommended file:

```text
s2p-copilot/backend/data/s2p_evolution_fixture.json
```

Load behavior:

- Load only when `S2P_EVOLUTION_FIXTURE` is set, or default to the committed file for demo/test mode if Prompt B chooses an explicit deterministic fixture loader.
- Env-var loading is better than mutating live state because it allows demo state to be deterministic, resettable, and separate from production scorer/graph state.

Fixture schema:

```json
{
  "version": "gap_h1_v1",
  "conservation_status": "GREEN",
  "conservation_pass": true,
  "rule_templates": [
    {
      "name": "auto_approve_threshold_sweep",
      "success_metric_name": "safe_auto_approve_rate",
      "applicable_categories": ["price_variance"],
      "current_parameters": {"price_variance": 0.85}
    }
  ],
  "variants": [
    {
      "variant_id": "S2P-AE-THRESH-PRICE-091",
      "template_name": "auto_approve_threshold_sweep",
      "category": "price_variance",
      "parameters": {"price_variance": 0.91},
      "state": "promoted",
      "source": "fixture"
    }
  ],
  "shadow_results": {
    "S2P-AE-THRESH-PRICE-091": [
      {
        "batch_id": "batch-001",
        "accuracy": 0.88,
        "baseline_accuracy": 0.82,
        "better": true,
        "win": true,
        "regression": false,
        "sample_size": 25
      }
    ]
  },
  "promoted": {
    "auto_approve_threshold_sweep": "S2P-AE-THRESH-PRICE-091"
  },
  "evidence": [
    {
      "variant_id": "S2P-AE-THRESH-PRICE-091",
      "title": "Auto-approve threshold moved",
      "before": "0.85",
      "after": "0.91",
      "why": "False approvals dropped while safe throughput stayed above target."
    }
  ],
  "story_labels": {
    "act": "Loom Act 4/5",
    "headline": "S2P learned to tighten high-value price variance approvals."
  }
}
```

## 10. Integration Plan for Prompt B

### SDK Files

No SDK production file changes are required for Prompt B. Use the existing exported SDK classes.

### S2P Backend Files to Create

- `backend/app/domains/s2p/evolution/__init__.py`
- `backend/app/domains/s2p/evolution/rule_templates.py`
- `backend/app/domains/s2p/evolution/shadow_runner.py`
- `backend/app/domains/s2p/evolution/service.py`
- `backend/app/routers/s2p_evolution.py`
- `backend/data/s2p_evolution_fixture.json`

### S2P Backend Files to Modify

- `backend/app/main.py`: instantiate `app.state.s2p_evolution` and include `s2p_evolution_router`.
- Optional only if needed: `backend/app/routers/s2p_evidence.py` to surface fixture-backed promoted/current rule details, without changing existing response fields.

### Tests to Create

- `backend/tests/test_s2p_evolution_rule_templates.py`
- `backend/tests/test_s2p_evolution_shadow_runner.py`
- `backend/tests/test_s2p_evolution_promotion.py`
- `backend/tests/test_s2p_evolution_fixture.py`
- `backend/tests/test_s2p_evolution_router.py`
- `backend/tests/test_s2p_evolution_p16.py`

No frontend files in Prompt B.

## 11. Test Plan for Prompt B

1. `test_rule_template_protocol_fields`: every template has `name`, `success_metric_name`, `applicable_categories`, `generate_variants`, and `evaluate_batch`.
2. `test_auto_approve_threshold_generates_clamped_variants`: threshold variants stay within allowed range.
3. `test_auto_approve_threshold_evaluates_safe_auto_approve_rate`: batch returns baseline/variant metrics.
4. `test_routing_priority_generates_deterministic_variants`: permutation output is stable.
5. `test_escalation_trigger_amount_marks_high_value_capture`: high-value records affect metric.
6. `test_supplier_flag_sensitivity_groups_by_supplier`: supplier exception batches are grouped by supplier id.
7. `test_evidence_presentation_order_generates_category_specific_orders`: evidence order variants are category-aware.
8. `test_rule_templates_do_not_mutate_input_decisions`: input decision list remains unchanged.
9. `test_shadow_runner_empty_decisions_returns_no_results`: empty input is safe.
10. `test_shadow_runner_returns_gate_compatible_batch_fields`: each result has `better`, `win`, `accuracy`, and `baseline_accuracy`.
11. `test_shadow_runner_does_not_call_learn`: mock scorer with failing `learn()` remains untouched.
12. `test_shadow_runner_does_not_write_graph_store`: fake graph store write methods are not called.
13. `test_autonomous_promotion_green_promotes_fixture_variant`: GREEN fixture with enough wins promotes.
14. `test_autonomous_promotion_amber_blocks_fixture_variant`: AMBER fixture does not promote.
15. `test_autonomous_promotion_shadow_losses_do_not_promote`: explicit losses beat stale win rate.
16. `test_context_selector_selects_category_variant`: category evidence affects selected variant.
17. `test_context_selector_records_failed_variant`: failed variant is downweighted.
18. `test_fixture_loads_from_env_var`: `S2P_EVOLUTION_FIXTURE` path loads deterministic state.
19. `test_fixture_default_state_has_promoted_variant`: committed fixture has current/promoted rule.
20. `test_router_sweep_returns_new_alerts_or_results`: `POST /api/s2p/evolution/sweep` returns deterministic structure.
21. `test_router_variants_returns_current_variants`: variant endpoint exposes generated/current variants.
22. `test_router_promoted_returns_promoted_rules`: promoted endpoint exposes promoted rule.
23. `test_p16_rule_templates_no_centroid_symbols`: source scan rejects `centroid`, `ProfileScorer`, `update_centroid`, `gae_scorer`, `save_centroids`, and `warm_start`.
24. `test_default_s2p_score_still_works`: existing `/api/s2p/score` behavior remains intact.
25. `test_s2p_backend_suite_from_backend_dir`: `cd backend; python -m pytest tests/ -q --timeout=120`.

## 12. Storyboard Integration Note

Loom Act 4/5 should show an S2P evolution panel or evidence/rules panel populated from `s2p_evolution_fixture.json`.

Visible narrative:

- "Auto-approve threshold moved from 0.85 to 0.91 for price variance."
- "Shadow batches: 3."
- "Win rate: 0.80+."
- "Conservation: GREEN."
- "Promotion: criteria_met."
- "Safety: no centroid mutation; operational rule only."

The value `0.85 -> 0.91` is defensible because the current `price_variance` threshold is `0.85` in `CompositeDiscriminant.CATEGORY_CONFIDENCE_THRESHOLDS` (`backend/app/framework/composite_gate.py:46-48`), and `0.91` is a conservative tightened threshold below the `AUTO_APPROVE_SAFETY_THRESHOLD` of `0.95` (`backend/app/framework/composite_gate.py:41`).

## 13. Risks and Open Questions

- The requested S2P baseline command from the repo root fails due test fixture relative paths. Prompt B should run S2P tests from `s2p-copilot/backend`, matching repo rules.
- `ContextAwareSelector` treats `decision_count < 10` as early even with a converged phase. Prompt B should avoid low decision counts in converged fixture/demo contexts.
- S2P preview config currently contains cross-copilot SOC signal narrative (`backend/app/routers/s2p_preview.py:452-491`). Prompt B should not import SOC code or add SOC vocabulary into S2P evolution production logic; fixture story labels may refer to cross-copilot signals only as demo metadata.
- `CompositeDiscriminant` has mutable process-level state for thresholds/interventions. Prompt B shadow variants should avoid mutating these globals during shadow evaluation.
- S2P scoring has both SDK scorer in `app.state.scorer` and domain `ProfileScorer` singleton helpers. Prompt B must use `app.state.scorer` for route integration and avoid mixing scorer state.
- Fixture-backed demo state should not be presented as production proof. It should be labeled source=`fixture` or source=`demo`.
- Prompt B must re-check imports and route paths before coding because this design intentionally avoids production changes in Prompt A.

## Prompt Verification Pass Results

- AE-EVOLUTION-ADV APIs documented from actual SDK files: YES.
- S2P shape documented from actual config and `CompoundingScorer.from_preset("s2p")`: YES.
- S2P scorer/route path documented from `backend/app/main.py` and `backend/app/routers/s2p.py`: YES.
- Operational parameters classified as existing vs to-be-introduced: YES.
- No production code written: YES.
- P16 separation included: YES.
- Prompt B file list and tests are concrete: YES.
- READY_FOR_PROMPT_B: YES.
