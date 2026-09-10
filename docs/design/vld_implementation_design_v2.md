# VLD Implementation Design
**Version:** v1 · **Date:** Sep 8, 2026
**Companion documents:**
- Architecture: `vld_graph_reasoning_architecture_v3.md`
- Demo scenarios: `demo_scenarios_vld_addendum_v1.md` (from Fable)
- Execution plan: `vld_execution_plan_v2.md`
- Simulation: `vld_validation_sims.py`

---

## 1. Purpose

This document defines WHAT to build, HOW to verify it works, and
WHAT NUMBERS constitute success. Every component maps to an experiment
that produces a quantified result. No component exists without a
measurement plan.

---

## 2. System Architecture — What Exists and What's New

### 2.1 Current platform (unchanged by VLD)

```
Alert/Invoice/Signal
  → FactorVectorProvider.compute() → v ∈ R^d
  → ProfileScorer.score(v) → (action, confidence, category)
  → Conservation gate → emit or abstain
  → If verified: scorer.learn(v, outcome) → update μ
```

This is the single-pass path. VLD does NOT replace it. VLD adds a
PARALLEL investigation path that runs alongside for comparison.

### 2.2 VLD components (what Phase 1a built)

```
Alert
  → FactorVectorProvider.compute() → v₀           [EXISTING]
  → InvestigationRouter.route(v₀, scorer) → pattern  [NEW - Phase 1a]
  → InvestigationPattern.execute(alert, graph) → evidence  [NEW - Phase 1a]
  → FactorVectorProvider.compute(enriched) → v₁   [EXISTING]
  → Damped update: v = (1-ε)v₀ + εv₁             [NEW - Phase 1a]
  → InvestigationRouter.route(v, scorer) → next pattern  [loops]
  → ... (up to L_max steps, C4 halt)
  → ProfileScorer.score(v_final) → (action, confidence)  [EXISTING]
  → Conservation gate at emit                      [EXISTING]
```

**New files (Phase 1a, SOC repo):**

| File | Role | Lines | Tests |
|---|---|---|---|
| `app/models/investigation.py` | InvestigationStep + InvestigationResult data models | ~60 | In test_investigation_loop |
| `app/services/investigation_patterns.py` | 6 category-specific SA patterns | ~200 | In test_investigation_loop |
| `app/services/investigation_router.py` | Score-keyed centroid-distance routing | ~80 | In test_investigation_loop |
| `app/services/investigation_loop.py` | VLD executor with damping, halt, trace | ~120 | 9 tests |
| `app/routers/triage.py` (addition) | POST /api/soc/investigate endpoint | ~30 | In test_investigation_loop |

### 2.3 What still needs building

| Component | Purpose | Experiment it enables |
|---|---|---|
| `scripts/measure_rho.py` | ρ measurement on fixture data | E-ρ (§4.1) |
| `scripts/generate_score_keyed_alerts.py` | Synthetic alerts WITHOUT category labels | E-ρsk (§4.2) |
| `scripts/replay_investigation.py` | Replay verified decisions through VLD loop | E-Δ (§4.3) |
| `scripts/budget_sweep_soc.py` | Budget sweep on SOC data | E-budget (§4.4) |
| `app/services/investigation_comparators.py` | Alternative routing policies for comparison | All experiments |
| Investigation trace storage (AGE schema) | Persistent trace for self-computation | Phase 2+ |
| DataOps investigation patterns | Category-specific DataOps patterns | Phase 2+ |
| S2P investigation patterns | Supplier/invoice-specific patterns | Phase 2+ |

---

## 3. Component Design

### 3.1 InvestigationRouter — the VLD Ψ policy

**What it does:** Given current factor vector v_t and the scorer's
centroids μ, compute distance to each category's centroid cluster
and route to the closest non-investigated category.

**How routing works (score-keyed):**
```
for each category c in {credential_access, ..., malware_execution}:
    d_c = min over actions a: ||v_t - μ[c, a, :]||
route to argmin(d_c) among non-investigated categories
```

**Why this is score-keyed, not content-keyed:**
The alert's explicit category label is NOT used. The routing signal
comes from the factor vector's GEOMETRIC POSITION relative to learned
centroid clusters. Two alerts with identical labels but different factor
vectors may route to different investigation patterns.

**Configuration:**
- L_max = 3 (initial + 2 investigation reads)
- ε = 0.3 (damping — weight on new evidence)
- RESIDUAL_THRESHOLD = 0.05 (halt when ||Δv|| / ||v|| < this)
- FLIP_COUNT_MAX = 2 (halt after 2 action changes)

### 3.2 Investigation Patterns — category-specific evidence retrieval

Each pattern follows the SA interface (supports/execute) and queries
ONLY existing graph schema nodes:

| Pattern | Category | Graph traversal | Enriches factors |
|---|---|---|---|
| CredentialInvestigation | credential_access | Alert→User→IAM/privilege edges | privileged_identity_context, pattern_history |
| MalwareInvestigation | malware_execution | Alert→ThreatIndicator→AttackPattern | threat_intel_enrichment, time_anomaly |
| LateralMovementInvestigation | lateral_movement | Alert→Asset→connected Assets | device_trust, privileged_identity_context |
| ExfiltrationInvestigation | data_exfiltration | Alert→Asset→data access patterns | asset_criticality, pattern_history |
| InsiderInvestigation | insider_threat | Alert→User→behavioral baseline | time_anomaly, pattern_history |
| CloudInfraInvestigation | cloud_infrastructure | Alert→Asset→cloud resource edges | asset_criticality, device_trust |

**Schema constraint (enforced in Phase 1a):** Patterns use ONLY node
types in graph_schema.py: Alert, User, Asset, Campaign, ThreatIndicator,
AttackPattern. No Process, Session, or CloudResource nodes (don't exist).

### 3.3 Investigation Loop — the VLD executor

**Algorithm:**
```
def investigate(alert, graph_store, scorer, factor_provider):
    v = factor_provider.compute(alert)
    investigated = set()
    trace = []

    for step in range(L_max):
        pattern = router.route(v, scorer, investigated)
        if pattern is None: break

        evidence = pattern.execute(alert, graph_store)
        investigated.add(pattern.category)

        v_new = factor_provider.compute({**alert, **evidence})
        v_old = v.copy()
        v = (1 - eps) * v + eps * v_new

        trace.append(InvestigationStep(...))

        if residual(v, v_old) < threshold: break
        if flip_count(trace) > max_flips: break

    return InvestigationResult(
        action=scorer.score(v).action,
        single_pass_action=scorer.score(factor_provider.compute(alert)).action,
        trace=trace,
        agreement=(VLD action == single-pass action)
    )
```

**Invariants:**
- Scorer and centroids are FROZEN during investigation (read-only)
- No learning triggered during investigation
- Conservation is checked at EMIT, not per-step
- Trace is complete and auditable

### 3.4 Comparison Policies (for experiments)

| Policy | How it routes | Purpose |
|---|---|---|
| **VLD** (score-keyed) | Centroid distance from v_t | The mechanism being tested |
| **Content-rule** | Alert's explicit category label → matching pattern | The content-keyed baseline |
| **Majority-branch** | Always dispatch the most common category's pattern | Naive baseline |
| **Random** | Uniform random pattern selection | Placebo |
| **Breadth** | Dispatch ALL patterns, aggregate evidence equally | Upper bound (budget-unlimited) |
| **Single-pass** | No investigation — score from surface only | Lower bound |

### 3.5 Investigation Trace Data Model

```python
@dataclass
class InvestigationStep:
    step: int                          # 0, 1, 2, ...
    pattern: str                       # category name dispatched
    v_before: list[float]              # factor vector before
    v_after: list[float]               # factor vector after
    cat_distances_before: dict         # distance to each cluster before
    cat_distances_after: dict          # distance to each cluster after
    evidence_keys: list[str]           # what evidence was admitted
    candidate_reads: list[str]         # what patterns were CONSIDERED
    propensity: float                  # P(this pattern | router state)
    cost: float                        # read cost (node count or latency)
    timestamp: str                     # ISO timestamp
    policy_version: str                # router version identifier
    residual: float                    # ||Δv|| / ||v||
    halt_reason: Optional[str]         # why stopped (if last step)

@dataclass
class InvestigationResult:
    action: str                        # VLD's final action
    confidence: float                  # VLD's final confidence
    category: str                      # VLD's inferred category
    trace: list[InvestigationStep]     # full investigation trace
    v_final: list[float]               # terminal factor vector
    steps: int                         # number of investigation steps
    single_pass_action: str            # what single-pass would have done
    single_pass_confidence: float      # single-pass confidence
    agreement: bool                    # VLD == single-pass?
    fixture_source: Optional[str]      # "planted" for fixture data
```

---

## 4. Experiments — Quantified Value Targets

Each experiment produces a specific number. Together, they answer:
"Is VLD worth building into the product?"

### 4.1 E-ρ: Scorer Routing Accuracy (Phase 1b)

**Question:** Does the scorer's centroid-distance routing match the
true category better than alternatives?

**Method:**
1. Load SOC fixture alerts with category labels
2. For each: compute v₀, run router, compare routed vs true category
3. Compute ρ for VLD, content-rule, majority, random

**Success criterion:** ρ_VLD > ρ_majority AND ρ_VLD > ρ_random

**Expected challenge:** Fixture alerts likely have explicit labels
(content-keyed fraction ≈ 1.0). In that case, ρ_content_rule = 1.0
and VLD can't beat it. This is expected — see E-ρsk.

**Quantified output:**
- ρ_VLD: ___
- ρ_content_rule: ___
- ρ_majority: ___
- ρ_random: 0.167
- Content-keyed fraction: ___

### 4.2 E-ρsk: Score-Keyed Routing (requires synthetic data)

**Question:** When category labels are REMOVED, does centroid-distance
routing still find the right investigation direction?

**Method:**
1. Take fixture alerts with known categories
2. Strip the category label (make them score-keyed)
3. Run VLD router on label-stripped alerts
4. Compare routed category against the hidden true category
5. This is the REAL test — can the scorer's geometry recover the
   investigation direction without being told?

**Success criterion:** ρ_VLD_scorekey > 0.5 (better than random among
6 categories, where chance = 0.167)

**Quantified output:**
- ρ_VLD_scorekey: ___
- Margin distribution for score-keyed cases: ___
- ρ by margin quartile: ___

**This is the go/no-go measurement.** If ρ_scorekey ≈ 0.167 (chance),
the scorer can't route without labels and VLD has no addressable market.
If ρ_scorekey > 0.5, the learned centroid geometry carries real
investigation routing information.

### 4.3 E-Δ: Investigation Depth Value (requires replay)

**Question:** Does VLD produce better actions than single-pass on
cases where the investigation trace changed the category routing?

**Method:**
1. Run all fixture alerts through both single-pass and VLD
2. Identify cases where VLD changed the action (agreement=false)
3. For those: which action was correct (compare against verified outcome)?
4. Δ_depth = accuracy(VLD) - accuracy(single-pass) on disagreement cases

**Success criterion:** Δ_depth > 0 on disagreement cases

**Quantified output:**
- Total alerts: ___
- Agreement rate: ___% (VLD == single-pass)
- Disagreement count: ___
- Of disagreements: VLD correct ___%, single-pass correct ___%
- Δ_depth: ___

**This is the value measurement.** If Δ_depth ≤ 0 even on disagreement
cases, VLD's routing changes the action but not for the better.
Publishable negative result.

### 4.4 E-budget: Budget Constraint Impact

**Question:** Does VLD's advantage concentrate at constrained budgets?

**Method:**
1. Sweep budget from 0 (surface only) to 6 (all categories)
2. Compare VLD, breadth, content-rule, random at each budget
3. Plot accuracy vs budget for each policy

**Success criterion:**
- VLD > random at budget=1-2
- VLD ≈ breadth at budget=6 (convergence)
- VLD advantage greatest at budget=1-2 (the realistic scenario)

**Quantified output:**
- Accuracy at budget=1: VLD ___, breadth ___, random ___
- Accuracy at budget=3: VLD ___, breadth ___, random ___
- Accuracy at budget=6: VLD ___, breadth ___, random ___
- Budget where VLD advantage peaks: ___

### 4.5 E-μskew: Centroid Representation Mismatch

**Question:** How much does the v₀ → μ distance differ from v_L → μ?

**Method:**
1. For each alert: compute v₀ (surface) and v_L (after VLD)
2. ||v_L - v₀|| shows how much investigation changes the vector
3. If large: routing with v₀ against μ (trained on v_L) is degraded

**Quantified output:**
- Mean ||v_L - v₀||: ___
- Median: ___
- P90: ___
- Correlation of ||v_L - v₀|| with routing accuracy: ___

### 4.6 Summary: Experiment → Value Gate Mapping

| Experiment | Measures | Gate | Blocks |
|---|---|---|---|
| E-ρ | Can scorer route at all? | ρ > majority | All |
| E-ρsk | Can scorer route WITHOUT labels? | ρ_sk > 0.5 | VLD product claim |
| E-Δ | Does routing improve actions? | Δ_depth > 0 | Build investment |
| E-budget | Where does VLD earn its value? | VLD > breadth at budget=1-2 | Product positioning |
| E-μskew | Is there a representation mismatch? | Informational | μ training strategy |

---

## 5. Demo Scenario Integration

Each experiment maps to a demo beat from the Fable addendum:

| Beat | What audience sees | Backed by experiment |
|---|---|---|
| **VLD-SOC-1** "Investigation Trace" | Investigation panel showing step-by-step routing | E-Δ (real traces from Phase 1b data) |
| **VLD-SOC-2** "Wrong-First-Step Recovery" | Router changes direction after first read | E-Δ (disagreement cases where VLD corrected) |
| **VLD-DO-1** "Three Systems One Root Cause" | Cross-system blast radius with priority routing | E-budget (VLD beats breadth at budget=1-2) |
| **VLD-DO-2** "Known Pattern New Twist" | Centroid distance as routing signal | E-ρsk (margin distribution, ρ by difficulty) |
| **VLD-S2P-1** "Supplier It Knew" | Supplier-specific routing | E-ρ (per-category ρ) |

**Honesty rule:** All beats are ARCH class until E-Δ shows Δ_depth > 0.
If E-Δ shows Δ_depth > 0 → beats upgrade to NEAR (infra exists, not
production-deployed). LIVE requires Phase 3 customer validation.

**Quantified claims in demo (when backed by data):**

| Claim | Source | When valid |
|---|---|---|
| "Routes to the right branch X% of the time" | E-ρsk result | After Phase 1b |
| "Changed direction and got it right Y% of the time" | E-Δ disagreement analysis | After Phase 1b |
| "Better than checking everything at budget=1" | E-budget result | After Phase 1b |
| "N× faster triage" | Phase 3 R5 analyst measurement | After Phase 3 ONLY |

Until Phase 3, time savings are "pilot targets, unvalidated."

---

## 6. Verification Plan

### 6.1 Component verification (unit/integration)

| Component | Verified by | Count |
|---|---|---|
| InvestigationRouter | test_investigation_loop.py | 9 tests (Phase 1a) |
| Investigation patterns | test_investigation_loop.py | 9 tests (Phase 1a) |
| InvestigationLoop | test_investigation_loop.py | 9 tests (Phase 1a) |
| POST /api/soc/investigate | test_investigation_loop.py | Endpoint test |
| measure_rho.py | Self-reporting + manual review | Phase 1b |
| Comparator policies | test_comparators.py (NEW) | Phase 1b |

### 6.2 Integration verification

| Check | How | When |
|---|---|---|
| VLD doesn't affect single-pass | Run single-pass before/after VLD code merge, compare results | Every commit |
| VLD doesn't trigger learning | Verify μ unchanged after investigation | test_investigation_loop test #7 |
| Conservation gate still works | Verify RED blocks emit after investigation | Integration test |
| Trace logging complete | Verify all InvestigationStep fields populated | test_investigation_loop test #6 |
| Existing SOC tests pass | Full SOC backend suite (2346+) | Every commit |

### 6.3 Experiment verification

| Experiment | Validity check | How |
|---|---|---|
| E-ρ | ρ_random ≈ 0.167 (sanity) | Computed automatically |
| E-ρsk | Label stripping complete (no leakage) | Verify stripped alerts have no category field |
| E-Δ | Single-pass arm uses same factor provider | Same FactorVectorProvider instance |
| E-budget | Budget constraint enforced (not just counted) | Router refuses to dispatch past budget |
| E-μskew | v₀ and v_L from same alert (not mixed) | Paired computation per alert |

---

## 7. Multi-Copilot Extension Plan

### 7.1 What's copilot-specific vs shared

| Component | Shared (SDK) | Per-copilot |
|---|---|---|
| InvestigationLoop | ✅ Core algorithm | Configuration only (L_max, ε, thresholds) |
| InvestigationRouter | ✅ Centroid-distance routing | Category names, centroid tensor shape |
| InvestigationStep/Result | ✅ Data models | — |
| Investigation patterns | — | ✅ Each copilot defines its own patterns |
| POST /api/{copilot}/investigate | ✅ Endpoint template | Route mounting per copilot |
| measure_rho.py | ✅ Measurement framework | Per-copilot fixture data |

### 7.2 DataOps patterns (Phase 2)

| Pattern | Category | Graph traversal |
|---|---|---|
| UpstreamSourcePattern | source_failure | Alert→Pipeline→upstream_dependency |
| SchemaChangePattern | schema_impact | Alert→Pipeline→schema_changes→downstream |
| DataQualityPattern | quality_drift | Alert→Pipeline→validation_rules→historical |
| BlastRadiusPattern | cross_system | Alert→Pipeline→downstream_systems (prioritized) |
| RecurringPattern | known_pattern | Alert→nearest campaign/cluster→known resolution |

### 7.3 S2P patterns (Phase 2)

| Pattern | Category | Graph traversal |
|---|---|---|
| GoodsReceiptPattern | receipt_mismatch | Invoice→PO→GoodsReceipt→delivery |
| ContractPricingPattern | price_mismatch | Invoice→PO→Contract→amendments |
| SupplierHistoryPattern | supplier_pattern | Invoice→Supplier→exception_history |
| PartialDeliveryPattern | quantity_mismatch | Invoice→PO→shipment_tracking |

### 7.4 Extension experiments

Each new copilot runs E-ρ, E-ρsk, E-Δ, E-budget against its own
fixture data. Results compared cross-copilot:

| Metric | SOC target | DataOps target | S2P target |
|---|---|---|---|
| ρ_scorekey | > 0.5 | > 0.5 | > 0.4 |
| Content-keyed fraction | < 0.8 | < 0.7 | < 0.6 |
| Δ_depth | > 0 | > 0 | > 0 |
| Budget advantage peak | budget=1-2 | budget=1-2 | budget=1 |

---

## 8. Risk Register (Implementation-Specific)

| Risk | Impact | Mitigation | Detected by |
|---|---|---|---|
| All fixture alerts content-keyed | E-ρsk unmeasurable | Generate synthetic label-stripped alerts | E-ρ content-keyed fraction |
| Centroids untrained (random seed) | ρ ≈ chance regardless | Use preseed data or train briefly | E-ρ ρ_random comparison |
| Investigation patterns return empty (no matching graph nodes) | v unchanged, investigation useless | Check pattern.execute return in tests | Phase 1a tests |
| Damping over-weights first read (Sim 2 finding) | VLD worse than breadth at budget > 1 | Test re-extraction (ε=1) as alternative | E-budget sweep |
| μ skew makes routing unreliable | ρ_scorekey low | Measure in E-μskew; consider v₀-specific centroids | E-μskew |
| No real disagreement cases | E-Δ has zero sample size | May need more diverse fixture data or synthetic generation | E-Δ disagreement count |

---

## 9. Implementation Sequence

```
DONE:
  Phase 1a: Investigation loop, patterns, router, trace, endpoint
  Simulation: ρ calibration (PASS), budget sweep (informative)

NEXT (Phase 1b — 1 Codex slot):
  scripts/measure_rho.py → runs E-ρ, E-ρsk, margin analysis, μ skew
  scripts/generate_score_keyed_alerts.py → synthetic label-stripped data
  app/services/investigation_comparators.py → 5 comparison policies
  Gate: ρ_scorekey > 0.5 AND Δ_depth > 0

THEN (Phase 2 — 2 Codex slots, if Gate passes):
  DataOps patterns + measurement
  S2P patterns + measurement
  Investigation trace storage in AGE
  Shadow-run on live traffic (R4)

THEN (Phase 3 — with customer):
  R5: analyst time measurement
  Upgrade demo beats from ARCH to NEAR
  Investigation profile discovery artifact
```

---

## 10. Relationship to Other Documents

| Document | This doc provides |
|---|---|
| Architecture v3 | The build specification for §8 (Making It Real) |
| Demo addendum (Fable) | The data backing for each VLD beat's quantified claims |
| Execution plan v2 | The detailed component + experiment design for each phase |
| Simulation script | The controlled validation that the implementation extends to real data |
| Phase 1a Codex prompt | The design this prompt was derived from |
| Phase 1b Codex prompt | The measurement plan this doc specifies |
