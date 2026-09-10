# VLD Implementation Design
**Version:** v4 · **Date:** Sep 8, 2026
**Supersedes:** v3 (reconciles our v3 + Astra review v3 + full experimental arc
Phase 1a→1b→value chain→geometry sprint→dual+abstention)

**Companion documents:**
- Architecture: `vld_graph_reasoning_architecture_v4.md`
- Astra review: `vld_implementation_review_and_design_v3_2026-09-08.md`
- Demo scenarios: `demo_scenarios_and_usecases_v2_8.md`
- Execution plan: `vld_execution_plan_v2.md`
- MAP addendum: `map_vld_addendum_v1.md`
- Simulation: `vld_validation_sims_v4.py` (6 experiments, 5000 cases each)
- R1 audit: `soc_rho_structural_feasibility_audit_2026-09-08.md`
- Patel et al.: arxiv 2609.03141 (persistent semantic context)
- Geometry sprint: `data/sprint/` (15 experiment outputs)

**SOC tag progression:** v5.139 (Phase 1a) → v5.140 (6-blocker fix) → v5.141
(Phase 1b ρ) → v5.142 (value chain fix) → v5.143 (value chain experiments +
centroid training) → v5.144 (geometry sprint) → v5.145 (dual+abstention)

---

## 1. Purpose

This document defines WHAT to build, HOW to verify it works, and
WHAT NUMBERS constitute success. Every component maps to an experiment
that produces a quantified result. No component exists without a
measurement plan.

**Framing (from Patel et al. 2026, arxiv 2609.03141):** As LLMs improve,
hand-engineered pipelines get subsumed. What endures is **persistent
semantic context** — curated knowledge about the environment, amortized
across decisions. CI's judgment graph IS persistent semantic context.
VLD is the adaptive acquisition policy over it. This document specifies
how to build and measure both.

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

### 2.2 VLD components (what Phase 1a built — SOC v5.139, 2346P 16S 0F)

```
Alert
  → FactorVectorProvider.compute() → v₀           [EXISTING]
  → InvestigationRouter.route(v₀, scorer) → pattern  [NEW - Phase 1a]
  → InvestigationPattern.execute(alert, graph) → evidence  [NEW - Phase 1a]
  → FactorVectorProvider.compute(enriched) → v₁   [EXISTING]
  → Damped update: v = (1-ε)v₀ + εv₁             [NEW - Phase 1a ⚠️ see §2.4]
  → InvestigationRouter.route(v, scorer) → next pattern  [loops]
  → ... (up to L_max steps, C4 halt)
  → ProfileScorer.score(v_final) → (action, confidence)  [EXISTING]
  → Conservation gate at emit                      [EXISTING]
```

**New files (Phase 1a, SOC repo, tag v5.139):**

| File | Role | Tests |
|---|---|---|
| `app/models/investigation.py` | InvestigationStep + InvestigationResult | 9 (in test_investigation_loop) |
| `app/services/investigation_patterns.py` | 6 category-specific patterns | 9 |
| `app/services/investigation_router.py` | Centroid-distance routing | 9 |
| `app/services/investigation_loop.py` | VLD executor with damping, halt, trace | 9 |
| `app/routers/triage.py` (addition) | POST /api/soc/investigate | 9 |
| `backend/tests/test_investigation_loop.py` | 9 tests covering loop, halt, trace | — |

**Phase 1a code-grounding corrections (applied during build):**
- SOC category: `insider_threat` (not `insider_behavioral` as in earlier docs)
- SOC factor 0: `privileged_identity_context` (not `travel_match`)
- Graph schema: patterns use ONLY existing nodes (Alert, User, Asset, Campaign,
  ThreatIndicator, AttackPattern). Process, Session, CloudResource do NOT exist
  in graph_schema.py — patterns adapted to use available schema.

### 2.4 Known gap: damping vs re-extraction

**Phase 1a code uses damped averaging (ε=0.3).** Simulation v4 Exp 3 showed
that re-extraction (average surface + all admitted evidence equally) is strictly
better at budget ≥ 2:

| Budget | VLD-damp | VLD-reext | Δ |
|---|---|---|---|
| 1 | 0.717 | 0.680 | damp +0.037 (damp better at budget=1) |
| 2 | 0.788 | 0.789 | tie |
| 3 | 0.815 | 0.874 | reext +0.059 |
| 6 | 0.517 | 0.810 | reext +0.293 |

**Decision:** Phase 1b must update investigation_loop.py to use re-extraction
as the canonical aggregation. Damping is acceptable at budget=1 (slightly better)
but collapses at budget > 3. Since the design targets budget=1-3, re-extraction
is the safer default.

**Implementation:** Replace the damped update line with:
```python
# Re-extraction: combine surface + all evidence equally
combined = surface_features.copy()
for ev in all_evidence.values():
    combined = combined + ev
v = combined / (1 + len(all_evidence))
```

### 2.5 What still needs building

| Component | Purpose | Phase | Experiment |
|---|---|---|---|
| **Re-extraction in investigation_loop.py** | Fix aggregation (§2.4) | **1b (first)** | All |
| `scripts/measure_rho.py` | ρ measurement on fixture data | 1b | E-ρ (§4.1) |
| `scripts/generate_score_keyed_alerts.py` | Synthetic alerts WITHOUT category labels | 1b | E-ρsk (§4.2) |
| `scripts/replay_investigation.py` | Replay verified decisions through VLD loop | 1b | E-Δ (§4.3) |
| `scripts/budget_sweep_soc.py` | Budget sweep on SOC data | 1b | E-budget (§4.4) |
| `app/services/investigation_comparators.py` | 5 comparison policies | 1b | All |
| **DataOps investigation patterns** | 5 category-specific DataOps patterns | **1b (parallel)** | E-ρ-DO |
| **DataOps ρ measurement** | Measure on pipeline alert fixtures | **1b (parallel)** | E-ρ-DO |
| S2P investigation patterns | Supplier/invoice-specific patterns | 2 | E-ρ-S2P |
| Investigation trace storage (AGE) | Persistent trace for self-computation | 2+ | — |

---

## 3. Component Design

### 3.1 InvestigationRouter — the VLD Ψ policy

**What it does:** Given current factor vector v_t and the scorer's
centroids μ, compute distance to each category's centroid cluster
and route to the closest non-investigated category.

**How routing works (score-keyed):**
```
for each category c in {credential_access, lateral_movement,
    data_exfiltration, insider_threat, cloud_infrastructure,
    malware_execution}:
    d_c = min over actions a: ||v_t - μ[c, a, :]||
route to argmin(d_c) among non-investigated categories
```

**Why this is score-keyed, not content-keyed:**
The alert's explicit category label is NOT used by the router. The routing
signal comes from the factor vector's GEOMETRIC POSITION relative to learned
centroid clusters. The router computes its OWN category inference from v_t —
the scorer doesn't infer category externally (R1 audit confirmed: category
is externally supplied via alert_type → literal map in config.py). VLD's
contribution is using centroid distances for investigation routing even
though the scorer doesn't use them for category assignment.

**Configuration (Phase 1a values):**
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

## 3B. Simulation Results (v4, Sep 8 2026)

Six experiments run with 5,000 synthetic decisions each, 6 branches
(matching SOC's 6 categories), 8-dimensional factor vectors.
Source: `vld_validation_sims_v4.py`.

### 3B.1 Exp 1 — Distractor Regime Sweep (THE KEY FINDING)

**Question:** Does VLD beat single-pass, and does it depend on whether
wrong-branch evidence is noise or actively misleading?

**Setup:** Sweep neutral_fraction from 0.0 (all wrong branches actively
mislead) to 1.0 (all wrong branches are noise). ρ=0.6, budget=1.

| Neutral fraction | VLD | Single-pass | Δ |
|---|---|---|---|
| 0.0 (all misleading) | 0.619 | 0.635 | −0.017 |
| 0.1 | 0.628 | 0.628 | 0.000 |
| **0.2** | **0.651** | **0.636** | **+0.014** ← crossover |
| 0.4 | 0.667 | 0.620 | +0.047 |
| 0.7 (realistic) | 0.726 | 0.636 | +0.090 |
| 1.0 (all noise) | 0.757 | 0.641 | +0.116 |

**Crossover at neutral_fraction ≈ 0.1-0.2.** When ≥20% of wrong-branch
evidence is neutral noise (realistic — most irrelevant evidence doesn't
actively mislead), VLD beats single-pass.

**Architectural implication:** VLD's value depends critically on the
evidence regime. If wrong investigation branches return actively
misleading evidence (adversarial setting), single-pass is safer.
In the realistic case (most wrong-branch evidence is irrelevant noise),
VLD provides +5 to +12pp accuracy improvement.

### 3B.2 Exp 2 — ρ Calibration (70% neutral, 6 branches)

**Setup:** Sweep ρ from 0.15 to 1.0 with realistic evidence (70% neutral,
30% misleading). Bootstrap 95% CIs.

| ρ | VLD [95% CI] | Single-pass | Content-rule | Δ VLD vs single |
|---|---|---|---|---|
| 0.15 | 0.642 [0.629,0.656] | 0.636 | 0.804 | +0.006 |
| 0.40 | 0.685 [0.671,0.699] | 0.633 | 0.800 | +0.052 |
| 0.60 | 0.706 [0.693,0.719] | 0.632 | 0.794 | +0.074 |
| 0.80 | 0.721 [0.709,0.733] | 0.638 | 0.794 | +0.083 |
| 1.00 | 0.710 [0.698,0.721] | 0.617 | 0.793 | +0.093 |

- **VLD > single-pass at 17/18 ρ values** (correlation 0.926)
- Content-rule (~0.80) dominates when labels exist — VLD never beats it
- VLD's value is exclusively in **score-keyed cases** (no labels)
- Selective VLD > single-pass at 17/18 ρ values

### 3B.3 Exp 3 — Budget × Distractor Interaction

**The aggregation finding:** damped averaging (ε=0.3) degrades at high budgets.
Re-extraction (average surface + all admitted evidence equally) is strictly
better at budget ≥ 2.

| Budget | ALL-NEUTRAL | | MIXED (70/30) | | ALL-MISLEADING | |
|---|---|---|---|---|---|---|
| | VLD-reext | Single | VLD-reext | Single | VLD-reext | Single |
| 1 | 0.759 | 0.641 | 0.680 | 0.639 | 0.463 | 0.635 |
| 2 | 0.869 | 0.641 | 0.789 | 0.639 | 0.664 | 0.635 |
| 3 | 0.931 | 0.641 | 0.874 | 0.639 | 0.715 | 0.635 |
| 6 | **0.994** | 0.641 | **0.810** | 0.639 | 0.001 | 0.635 |

**Key findings:**
1. **Re-extraction fixes the budget>1 reversal** from v3 simulation
2. **All-neutral budget=6: 99.4% accuracy** — near-perfect when wrong
   branches don't mislead and all evidence is aggregated equally
3. **All-misleading budget=6: 0.1%** — total collapse when all wrong
   branches actively mislead
4. **Mixed budget=3: 87.4%** — the realistic sweet spot
5. **Implementation decision: use re-extraction, not damped averaging**

### 3B.4 Exp 4 — Selective VLD Margin Gate

**Question:** Should VLD investigate ALL cases, or only uncertain ones?

**Setup:** At 70% neutral, sweep the margin gate (investigate when
margin < gate; single-pass when margin ≥ gate).

**Result:** Optimal gate = 0.40, which means investigate 100% of cases.
At 70% neutral, VLD-always (+9pp) beats every selective threshold.

**Interpretation:** With realistic evidence, VLD helps even on
"easy" cases. Selective investigation only helps in the ALL-MISLEADING
regime where wrong-branch reads are destructive.

### 3B.5 Exp 5 — Abstention Utility by Penalty Ratio

**Setup:** Three domain penalty ratios (SOC 20:1, S2P 5:1, Trading 3:1).
Sweep abstention threshold, compute utility.

| Domain | Penalty | Optimal threshold | Utility (no abstain → optimal) |
|---|---|---|---|
| **SOC (20:1)** | 20.0 | 0.35 | −4.75 → −0.97 (4.9× improvement) |
| **S2P (5:1)** | 5.0 | 0.20 | −0.64 → −0.37 (1.7× improvement) |
| **Trading (3:1)** | 3.0 | 0.05 | −0.10 → −0.09 (marginal) |

**Higher penalty → more abstention value.** SOC benefits enormously
from "know when to abstain" because incorrect triage is 20× more
costly than abstaining. Trading barely benefits because incorrect
trades are only 3× costlier.

**Product implication:** The abstention mechanism (conservation-bounded
deferral) is the strongest value driver for high-penalty domains.

### 3B.6 Exp 6 — Routing Quality Breakdown

**Per-category routing accuracy:**
- Categories 0, 5 (edge categories in centroid space): **80.5%, 80.6%**
- Categories 1-4 (interior categories): **14.4% - 16.7%**
- Overall: 37.6%

**Action accuracy conditioned on routing:**
- VLD on correctly-routed: **96.1%** (near-perfect)
- VLD on incorrectly-routed: **58.4%** (worse than single-pass 63.6%)

**The value equation:** VLD's net accuracy = 0.376 × 0.961 + 0.624 × 0.584
= 0.361 + 0.364 = 0.726. Single-pass = 0.636. Net gain = +0.090.
**Correct routing dominates despite only 37.6% routing accuracy** because
the 96.1% action accuracy on correct routes creates enough lift.

### 3B.7 Summary — What the Simulations Establish

| # | Finding | Implication |
|---|---|---|
| 1 | VLD beats single-pass when ≥20% of wrong-branch evidence is neutral | Real evidence is mostly neutral → VLD works in realistic settings |
| 2 | VLD beats single-pass at 17/18 ρ values with 70% neutral evidence | ρ calibration instrument is valid and shows consistent advantage |
| 3 | Re-extraction fixes the budget>1 reversal | **Use re-extraction, not damping** as the aggregation strategy |
| 4 | At 70% neutral, investigate ALL cases (no selective threshold) | Selective VLD matters only in adversarial evidence regimes |
| 5 | Abstention value scales with penalty ratio (SOC 4.9×, S2P 1.7×) | Conservation-bounded deferral is the strongest value driver for SOC |
| 6 | VLD on correct routes: 96.1%. On wrong routes: 58.4% | Even at 37.6% routing accuracy, net gain is +9pp |
| 7 | Content-rule always beats VLD when labels exist (~0.80 vs ~0.72) | VLD's value is EXCLUSIVELY in score-keyed cases |

### 3B.8 What the Simulations Do NOT Establish

- Whether real SOC evidence is 70% neutral or more/less
- Whether CI's real scorer achieves ρ > 0.15 on real cases
- Whether 37.6% routing accuracy is achievable with real centroids
- Whether the 6-category structure maps to real SOC investigation branches
- Whether re-extraction is implementable in the real factor provider
- Time savings for analysts (requires Phase 3 R5 measurement)

---

## 3C. Real-Data Experiments (Phase 1b through Geometry Sprint)

### 3C.1 Phase 1b: ρ Measurement (v5.141)

Gate 1b PASSED. Centroid-distance routing works on SOC fixture data.

| Metric | Value |
|---|---|
| ρ_VLD_scorekey | **0.685** |
| ρ_majority | 0.300 |
| VLD advantage | 2.3× majority |
| Δ_depth (VLD vs single-pass) | **−0.225** |
| VLD action accuracy | 0.313 |
| Single-pass accuracy | 0.538 |

**Routing works. Actions don't.** This launched the value chain investigation.

### 3C.2 Value Chain Diagnostic (v5.142)

H2 (scoring locked to routed category) was NOT confirmed on real data —
the loop already scored across all categories. The real causes:

- **H3 CONFIRMED:** Evidence/re-extraction dilution. Even correct-category
  evidence degrades action signal when re-extracted with surface features.
- **H4 CONFIRMED:** Routing interaction damage. Wrong-route evidence (31.5%
  of cases) actively hurts action accuracy.

### 3C.3 Value Chain Experiments (v5.143)

**Centroid quality gate FAILED (0.82 < 1.5).** All action accuracy is
measured against untrained centroids. Findings carry [SYNTHETIC CAVEAT]:

- Oracle (perfect routing + correct evidence) ≤ single-pass
- E-DIM: full-vector improved only 22% — evidence mostly moves away
  from action targets
- E-WRONG: correct-route VLD still underperforms single-pass

**Classification: EXPERIMENT DESIGN ISSUE.** The centroids are random
noise. Action accuracy measurement is meaningless until centroids are
trained from real verified outcomes.

### 3C.4 Centroid Training (v5.143)

Trained centroids from three sources:

| Source | Inter/intra ratio | Gate |
|---|---|---|
| Default (production) | 0.82 | FAIL |
| Fixture-derived | 0.89 | FAIL |
| **Synthetic (1200 rows, 50/cell)** | **10.13** | **PASS** |

With synthetic-trained centroids: ρ collapses (0.685 → 0.155) but
Δ_depth flips positive (−0.225 → +0.053). **One tensor cannot serve
both routing and action scoring.**

### 3C.5 Geometry Design Sprint — THE KEY FINDING (v5.144)

**DUAL-CENTROID RESOLVES the routing/action tension.**

| Metric | Single tensor (default) | Single tensor (trained) | Dual-centroid |
|---|---|---|---|
| ρ (routing) | **0.685** | 0.155 | **0.685** |
| Δ_depth (actions) | −0.225 | +0.053 | **+0.072** |
| Stability (5 seeds) | — | — | **±0.013** |

**Architecture decision:** route with μ_routing (default, optimized for
inter-category separation), score with μ_action (trained, optimized for
inter-action separation within categories). Investigation direction is
DECOUPLED from final action scoring.

The geometry sprint tested 7 options (B1-B7). Dual-centroid (B1) was
the clear winner. Joint training (B3) showed the tension as a Pareto
frontier — no single α achieves both ρ > 0.5 AND Δ > 0.

### 3C.6 Dual-Centroid + Abstention (v5.145)

Geometry disagreement as an abstention signal: **NOT INFORMATIVE.**

- Disagreement rate: 86.4% (the two centroid sets disagree on almost everything)
- VLD accuracy on disagreement (23%) ≈ on agreement (17.6%)
- Best SOC utility policy: abstain on ALL cases (degenerate)

**The disagreement signal is noise, not information.** If abstention is
needed, it must be calibrated from production outcomes, not from
centroid-set disagreement.

### 3C.7 Summary — What the Experimental Arc Established

| # | Finding | Confidence | Caveat |
|---|---|---|---|
| 1 | Routing works (ρ=0.685, 2.3× majority) | HIGH | None — measured on real fixtures |
| 2 | Single tensor cannot serve both routing and action | HIGH | None — structural finding |
| 3 | Dual-centroid resolves the tension (Δ=+0.072) | MEDIUM | [SYNTHETIC TRAINING CAVEAT] |
| 4 | Dual-centroid is stable (std ±0.013 over 5 seeds) | MEDIUM | [SYNTHETIC TRAINING CAVEAT] |
| 5 | Re-extraction is the correct aggregation | HIGH | Confirmed in sim + code |
| 6 | Abstention on geometry disagreement is noise | HIGH | 86% disagree — not informative |
| 7 | All absolute accuracy numbers are unreliable | — | Untrained/synthetic centroids |

### 3C.8 What Phase 2 Must Resolve

1. **Train action centroids from real verified SOC outcomes.** The quality
   gate (inter/intra ≥ 1.5) must pass with production data.
2. **Measure dual-centroid Δ with production centroids.** If Δ > 0 with
   real centroids → mechanism delivers real value.
3. **Calibrate abstention from production outcomes.** Margin-based
   abstention (not geometry disagreement) with real utility measurement.
4. **Measure neutral fraction on real evidence.** Sim v4 Exp 1 assumed
   70% neutral — validate with real SOC graph evidence.
5. **Analyst time savings (R5).** Phase 3 — requires production deployment.

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

### 7.2 DataOps patterns (Phase 2 → consider Phase 1b parallel)

**DataOps may be VLD's strongest use case.** Patel et al. (2026, arxiv
2609.03141) establish that 60%+ of data agent failures are environmental
knowledge failures — wrong data source, semantic misinterpretation,
entity/join mismatches. DataOps faces exactly these. The paper validates
persistent semantic context (+19pp on DAB); CI's DataOps judgment graph
is a learning, governed implementation of that context.

**Why DataOps may outperform SOC for VLD:**
- Richer navigable structure (9 pipeline systems with topology, dependencies,
  schema history vs SOC's alert/campaign graph)
- More inherently ambiguous alerts (same metric → 3+ root causes) = more
  score-keyed conditional decisions
- Process-Tech Fusion (SAP + Celonis) IS the paper's "context construction"
- Existing OE-1 through OE-5 panels provide the evidence infrastructure

**Recommendation:** Run DataOps ρ measurement in Phase 1b IN PARALLEL with
SOC, not deferred to Phase 2. If DataOps shows higher m_conditional and ρ
than SOC, it should become the VLD lead copilot for Phase 2 shadow runs.

**DataOps patterns (aligned with the paper's failure taxonomy):**

| Pattern | Category | Graph traversal | Paper's failure mode addressed |
|---|---|---|---|
| UpstreamSourcePattern | source_failure | Alert→Pipeline→upstream_dependency | Wrong data source |
| SchemaChangePattern | schema_impact | Alert→Pipeline→schema_changes→downstream | Entity/join mismatches |
| DataQualityPattern | quality_drift | Alert→Pipeline→validation_rules→historical | Semantic misinterpretation |
| BlastRadiusPattern | cross_system | Alert→Pipeline→downstream_systems (prioritized) | Missing schema knowledge |
| RecurringPattern | known_pattern | Alert→nearest cluster→known resolution | Stale metadata |

**DataOps investigation scenarios (from the paper's lens):**

**Scenario 1 — Schema change impact (paper's "entity/join mismatch"):**
Pipeline alert on billing_api. Throughput dropped 40%. Investigation router
routes to SchemaChangePattern (scorer's centroids closest to schema_impact
cluster). Pattern finds MATKL_V2 migration: 340K new material codes → join
fanout 9×. Traces downstream via BlastRadiusPattern: 7 systems affected,
3 critical. Recommends pre-join filter.
*Without VLD:* analyst checks upstream source first (wrong branch), then
schema changes. 15 minutes.
*With VLD:* scorer routes directly to schema → downstream. 3 minutes.
*Paper's framing:* the environmental knowledge (which schema change causes
which join failure) is the persistent semantic context. VLD navigates it.

**Scenario 2 — Recurring vs novel (paper's "stale metadata"):**
Pipeline alert signature similar to known "Monday batch delay" pattern.
Centroid distance to known_pattern cluster is small (0.15). Investigation
router dispatches RecurringPattern → finds the known resolution (increase
batch parallelism). But after applying the known fix, the alert persists.
Router re-scores: centroid distance to known cluster increases (0.45).
Now routes to DataQualityPattern → finds a new validation rule that
rejects 12% of records. Novel root cause behind a familiar signature.
*Paper's framing:* stale metadata (the "Monday batch delay" pattern) would
have led to the wrong fix. VLD's re-scoring detected that the known
pattern didn't fully explain the alert.

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
| Investigation patterns return empty | v unchanged, investigation useless | Check pattern.execute return in tests | Phase 1a tests |
| **Wrong-branch evidence is misleading (>80%)** | **VLD worse than single-pass (Exp 1 crossover)** | **Measure neutral fraction on real SOC evidence** | **Exp 1 regime characterization** |
| **Damped averaging degrades at budget>1** | **VLD reversal at high budgets** | **Use re-extraction aggregation (Exp 3 finding)** | **Budget sweep** |
| μ skew makes routing unreliable | ρ_scorekey low | Measure in E-μskew; consider v₀-specific centroids | E-μskew |
| No real disagreement cases | E-Δ has zero sample size | May need more diverse fixture data | E-Δ disagreement count |
| **Interior categories (1-4) have ~15% routing accuracy** | **VLD only helps edge categories** | **Improve centroid separation or reduce to fewer categories** | **Exp 6 per-category breakdown** |
| **Abstention threshold wrong for domain** | **Over/under-abstaining** | **Calibrate per domain penalty ratio (Exp 5)** | **Utility sweep** |

---

## 9. Implementation Sequence

```
DONE — Phase 0 (simulation):
  Simulation v4: 6 experiments, ρ calibration PASS (corr 0.986)
  Key decisions: re-extraction, always-investigate at 70% neutral,
  abstention value scales with penalty ratio

DONE — Phase 1a (infrastructure, SOC v5.139):
  Investigation loop, 6 patterns, centroid-distance router, trace, endpoint
  9 tests

DONE — Phase 1a Fix (6 blockers, SOC v5.140):
  Fix 1: centroid routing from step 0 (no content-forcing)
  Fix 2: scorer.score() called once (final only)
  Fix 3: patterns return differentiated evidence
  Fix 4: factor provider enriches v from evidence
  Fix 5: residual=0.05, flip halt at max_flips
  Fix 6: re-extraction replaces damped averaging
  +8 tests

DONE — Phase 1b (ρ measurement, SOC v5.141):
  ρ_scorekey=0.685 (2.3× majority). Gate 1b PASS.
  Δ_depth=−0.225 (actions worse). Launched value chain investigation.
  5 comparator policies, score-keyed alert generator, measure_rho.py
  +17 tests

DONE — Value chain investigation (SOC v5.142-v5.143):
  Diagnostic: H3 (dilution) + H4 (routing damage) confirmed.
  Centroid quality gate FAILED (0.82 < 1.5).
  Oracle ≤ SP with default centroids.
  Classification: EXPERIMENT DESIGN ISSUE (untrained centroids).
  5 experiment scripts, diagnostic framework.
  +12 tests

DONE — Geometry design sprint (SOC v5.144):
  DUAL-CENTROID RESOLVES: ρ=0.685 + Δ=+0.072 (stable ±0.013).
  Route with default μ, score with trained μ.
  7 architectural options tested (B1-B7).
  Joint training shows Pareto frontier — no single α works.
  +14 tests

DONE — Dual+abstention (SOC v5.145):
  Geometry disagreement is noise (86% disagree).
  Best SOC utility = all-abstain (degenerate).
  Abstention needs production calibration.
  +5 tests

  Total Phase 1: SOC v5.139 → v5.145, +72 tests (2337 → 2414P)
  ALL findings carry [SYNTHETIC TRAINING CAVEAT] for action accuracy.

───────────────────────────────────────────────────────────────

NEXT — Phase 2 (production validation):

  Phase 2a: Dual-centroid production loop (1-2 Codex slots)
    Implement dual-centroid in investigation_loop.py:
      - μ_routing loaded from production scorer (default centroids)
      - μ_action loaded from separate trained file
      - Router uses μ_routing. Final scoring uses μ_action.
    Tests: dual-centroid integration tests
    Gate: existing tests pass + new dual-centroid tests pass

  Phase 2b: Production centroid training (requires real data)
    Collect verified SOC outcomes (analyst confirm/override decisions)
    Train μ_action from verified outcomes
    Gate: inter/intra ratio ≥ 1.5 with REAL training data
    If fails: production data may not differentiate actions → VLD
    value claim limited to routing/triage (not action improvement)

  Phase 2c: Shadow run (requires live traffic)
    Run dual-centroid VLD alongside production single-pass
    Compare: Δ_depth on real decisions
    Measure: neutral fraction (sim v4 Exp 1 validation)
    Gate: Δ_depth > 0 on production data

  Phase 2d: DataOps parallel (per Patel et al. 2026)
    Build 5 DataOps investigation patterns (§7.2)
    Measure ρ on pipeline alert fixtures
    DataOps may be stronger VLD case (richer graph, more ambiguous alerts)

THEN — Phase 3 (customer validation):
  R5: analyst time measurement
  Margin-based abstention calibration (not geometry disagreement)
  Upgrade demo beats from ARCH to NEAR
  Investigation profile discovery artifact
```

---

## 10. Relationship to Other Documents

| Document | Version | This doc provides |
|---|---|---|
| Architecture | v4 | Build spec for Making It Real |
| Astra review | 106KB, 15 blocks | Corrections applied in Phase 1a Fix; remaining items reconciled here |
| Demo scenarios | v2.8 | Data backing for VLD beats |
| Execution plan | v2 | Component + experiment design per phase |
| MAP addendum | v1 | Queue items V-0 through V-4 |
| Simulation | v4 (6 experiments) | Controlled validation (§3B) |
| R1 structural audit | Sep 8 | What exists / doesn't exist in code |
| Patel et al. 2026 | arxiv 2609.03141 | Persistent semantic context thesis |
| VLD depth memo | v13 | Parent theoretical document |
| Phase 1a code | SOC v5.139-v5.145 | investigation_*.py — what was built |
| Geometry sprint | 15 experiments | Dual-centroid finding (§3C.5) |
| Value chain experiments | 5 experiments | H3/H4 confirmation (§3C.2-3) |

### Documents affected by VLD (not yet updated):

| Document | What VLD changes | Priority |
|---|---|---|
| cga_arxiv_short_v10_2 | Dual-centroid geometry, VLD as new mechanism | HIGH |
| math_synopsis_v21 | New claims: ρ (validated/sim), dual-centroid (validated/sim), geometry tension (boundary-defined) | HIGH |
| rl_sdk_design_v1 | VLD investigation-step credit assignment feeds RL sidecar | HIGH |
| innovation_note_v28 | VLD as governed decision-loop, persistent semantic context | MEDIUM |
| graph_native_reasoning_hero_v25 | Read/Route/Investigate/Reshape | MEDIUM |
| graph_native_separation_block_v9 | VLD at the engineering/native boundary | MEDIUM |
| jm_paper_draft_v11 | Investigation traces as judgment memory | LOW |
| ci_blog_v18 | Investigation clock, Patel et al. validation | MEDIUM |
