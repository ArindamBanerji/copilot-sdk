# S2P Copilot — Unified Design & Product Definition
**Version:** v1.3 (merged) · **Date:** May 22, 2026
**Supersedes:** s2p_copilot_design_v0_7 (parts 1+2) + s2p_product_definition_v1_3
**Structure:** §1-§17 Engineering Design (from v0.7) + §PD1-§PD12
Product Definition (from v1.3). ONE document per copilot.

**Changes (merge):** Combined three documents into one. No content
changes. Engineering design (architecture, factors, screens,
storyboard) + Product definition (16 scenarios, competitive
positioning, engineering specs, value model) in single file.

---

# PART I — ENGINEERING DESIGN (v0.7)

*Architecture, factor space, graph schema, screens, storyboard,
source integration, IKS, shadow mode, NL templates, evaluation.*

---


> **Changes from v0.6 → v0.7 (April 8, 2026):**
>
> **(1) Re-Convergence Theorem (CC-21 Tier 2) applied to S2P.** γ > 1 proven analytically.
>     ε_firm★ = α_cat · ‖Δ‖ / (1−α_cat) ≈ 0.125. S2P archetype-conditional (see Part 2 §17.6).
>     Formula corrected: θ cancels; was 0.128, correct value 0.125 (diff = 0.003).
>
> **(2) Block 8.5 AGE/PostgreSQL migration.** S2P graph entities move to PostgreSQL+AGE.
>     S2P-specific Cypher queries need AGE dialect verification. See Part 2 §17.6 + §17.3.
>
> **(3) gae/synthetic.py + gae/convergence.py.** S2P validation tools added to §17.1.
>     centroid_distance_to_canonical is the primary S2P convergence metric.
>
> **(4) Test counts: GAE 527→536, SOC 532→558, ci-platform 102→107, S2P 46→58, total ~1,389.**

> **Changes from v0.5 → v0.6 (April 6, 2026 — V-CGA-FROZEN PASS + Phase D):**
>
> **(1) V-CGA-FROZEN PASS → CLAIM-59 UNCONDITIONAL + CLAIM-62 UNCONDITIONAL.**
>     SVM-003 (V-CGA-FROZEN v4, March 26) + V-CGA-FROZEN PASS (April 6, 2026):
>     - CLAIM-59: graph enrichment compounds independently of centroid learning.
>       54.4% fewer decisions to reach 85% accuracy after centroid unfreeze.
>       p<0.0001, 26/30 seed pairs consistent. THIRD compounding pathway confirmed.
>     - CLAIM-62: enriched μ₀ initialization delivers +42.69pp Day-1 lift (production
>       config: enriched μ₀ + DiagonalKernel). +40.93pp from enrichment alone.
>       Confirmed across healthcare, FinServ, midmarket environments.
>     - §17.5 Cross-graph discovery quality issue → CLOSED. §16.2 updated.
>     - §20 V-CGA-FROZEN row → CLOSED.
>
> **(2) Phase D (S2P demo readiness) added to §18.** §18.4 NEW: Phase D planning —
>     S2P tab content Tier 1+2, V-NARRATIVE-S2P gate, S2P worked example (Block 3.8).
>     Block 7.5 circular dependency documented: ACCP routing across copilots requires
>     both SOC and S2P live. Phase D.1 (worked example) → Phase D.2 (tab content) →
>     Phase D.3 (V-NARRATIVE-S2P gate) → first CISO demo with S2P.
>
> **(3) CL-ECON-MEASURED + Economics.** Innovation 10 CLOSED (March 26, 2026):
>     30.85 min/alert savings (SANS-calibrated). S2P parallel: CL-ECON-S2P
>     UNCONDITIONAL (31 min/PO decision, Hackett anchor). Both domains validated.
>     CC-14 (cross-domain conservation law) → demo-able when Phase D complete.
>
> **(4) GAE version: v0.7.18 → v0.7.20.** raw_weights property added (CLAIM-64
>     requires raw_weights, not weights — silent footgun in v0.7.19). Block 9.1-9.5
>     shipped (CLAIM-66-70). 518 → 527 → 536 GAE tests (Block 9.1–9.5, KERNELSEL-001, raw_weights, +gae/synthetic.py + gae/convergence.py).
>
> **(5) Test counts updated.** GAE 518→527. SOC 294→558 backend + 120/121 E2E.
>     ci-platform 98→107. S2P 46→58. Total: ~1,389 tests.
>
> **(6) Companion docs updated.** gae_design_v10_2→v10_3. claims_registry_v8_4→v9.0.
>     platform_roadmap_v20→MAP v5.17. All S2P reuse components confirmed v0.7.20.

> **Changes from v0.4 → v0.5 (March 25, 2026 — status + currency update):**
>
> **(1) STATUS: Design only → Build-ready, Phase 3 Priority 2.** S2P is no longer a
>     future design aspiration. It is the next build target per master_action_plan_v4.6.
>     S2P build triggers the CopilotFramework extraction from SOC into ci-platform.
>     See §18 (Version Placement) for the updated build sequence.
>
> **(2) CopilotFramework extraction documented.** S2P will be built ON the framework,
>     not as a SOC fork. SOC shrinks to ~800 lines. S2P builds at ~1,200 lines.
>     The extraction happens as the FIRST step of S2P build, before any S2P-specific
>     code is written. See gae_opensource_strategy_v5 §Part 14 for extraction sequence.
>
> **(3) GAE version: v0.7.0 → v0.7.18.** Phase 2 complete (15 issues fixed, 518 GAE
>     tests, 294 SOC tests, 98 ci-platform tests). INT-TEST-1 (P28 end-to-end) and
>     INT-TEST-2 (W2 read path) now passing. All S2P reuse components validated.
>     *(Note: current version is v0.7.20 — see v0.5→v0.6 changelog above.)*
>
> **(4) Companion documents updated.** gae_design_v9.2→v10_2, design_note_v2→v3,
>     platform_roadmap_v19→v20, claims_registry_v6→v8.4. Two new docs added:
>     gae_opensource_strategy_v5 (CopilotFramework, W2 boundary, MCP schemas),
>     master_action_plan_v4.6 (Phase 3 coding session brief, OSS strategy).
>
> **(5) V-CGA-FROZEN status updated.** Previously "OPEN ⚠️ Priority 2 HIGH" with
>     undefined methodology. Now SVM-003 — fully specified 60-persona Colab Pro
>     experiment queued for Phase 3 Priority 0. See §17.5 and §20 for updated status.
>
> **(6) OLSMonitor added to validation checklist §17.4.** Missing from v0.4.
>     OLSMonitor is domain-agnostic (GAE v0.7.11). CLAIM-OLS-01 validated (0% miss
>     rate, p90≥50d lead time). S2P gets Flywheel Health Monitor for free.
>
> **(7) §16.2 experiments: SVM methodology noted.** Each required experiment
>     (S2P-EVAL-1, S2P-V3B, S2P-GATE-R, S2P-PROD-4) runs via SVM (Colab Pro,
>     LLM-judge personas). No "real deployment data" required for any of these.
>
> **(8) §20 summary table and bottom-line text updated.** GAE test count and version
>     corrected. CopilotFramework extraction added as a new finding/action row.

---

> **Changes from v0.3 → v0.4 (March 21, 2026):**
>
> **(1) FACTOR ARCHITECTURE: d=6 → d=8.** Six operational factors replaced by eight
>     domain-level risk scores: Supplier, Logistics, Demand, Inventory, Regulatory,
>     Geopolitical, Financial, Environmental. Each domain score aggregates multiple
>     signals from its respective risk domain. The 8-domain framework aligns with
>     industry-standard supply chain risk cockpit structure (Gartner, McKinsey, BCI).
>     Tensor shape: (5, 5, 6) → **(5, 5, 8)**. All centroid values redesigned.
>
> **(2) DiagonalKernel is v6.0/v6.5 DEFAULT.** V-MV-KERNEL factorial validated DiagonalKernel
>     on S2P: +6.8pp on heterogeneous data. ShrinkageKernel adds -0.2pp (negligible even
>     with dense correlations, avg ρ≈0.43). CalibrationProfile.kernel_type updated.
>     KernelSelector ships: noise_ratio>1.5→diagonal, rolling 100-window, 250 decisions.
>
> **(3) Two-judge validated correlation research integrated.** 28-pair structural correlation
>     matrix (GPT-4o + Opus). Three correlation clusters, two coupling backbones, one
>     intersection node (Supplier). 5 disruption archetypes. 3 regimes (pre-COVID, post-COVID,
>     post-Ukraine). Asymmetric correlations documented. Industry-specific ρ variations.
>     8×8 Σ matrix (Regime A baseline). This research informs domain understanding and
>     residual analysis but does NOT affect kernel selection (noise ratio only — Explanation A).
>
> **(4) CovarianceEstimator integration.** Collects full 8×8 covariance matrix at v6.5.
>     NOT used for scoring. Research asset for v7.0 shrinkage investigation.
>     Exponential decay (half-life ~300 decisions) for regime tracking.
>
> **(5) V-MV-KERNEL experimental results on S2P.** 18-cell V-S2P-HETERO experiment:
>     Diagonal +7.4pp over L2. Shrinkage -0.2pp vs diagonal. Explanation A confirmed for S2P:
>     noise ratio determines kernel advantage, not correlation structure.
>
> **(6) Version placement updated.** 10-scenario demo: v6.5 (with DiagonalKernel comparison).
>     Full S2P: v7.0. Was v7.0 demo / v7.5 full in v0.3.
>
> **(7) Penalty_ratio confirmed at 5:1.** Three open items from v0.3: τ calibration (S2P-V3B
>     still needed), penalty_ratio (5:1 confirmed as design estimate, cost-benefit analysis
>     still needed), NL template strings (still need domain expert authoring).
>
> **(8) Companion docs updated.** claims_registry_v6 (58 claims, 6 kernel-validated),
>     platform_roadmap_v19 (DiagonalKernel at v6.0, S2P demo at v6.5),
>     multivariate_foundation_design_note_v2 (390-cell factorial, S2P correlation research).

---

## 1. The S2P Decision Problem

### 1.1 What Is Being Triaged?

*(Unchanged from v0.3 — procurement judgment compounding story remains the same.)*

A Source-to-Pay (S2P) copilot triages **purchase requisitions** (PRs). The compounding
intelligence claim is identical to SOC: after 1,000 verified PR decisions, the system
develops firm-specific procurement judgment. Under DiagonalKernel, the distance metric
itself adapts to the firm's risk-domain noise profile — a third compounding pathway
alongside centroids and graph enrichment.

**The IKS story for S2P:** "Your S2P system has an IKS of 34.7. At deployment it was 0.
Procurement centroids have moved 35% from bootstrap priors toward your firm's actual
contract patterns. The kernel weights show your Financial Risk data is reliable (weight 0.9)
while your Environmental Risk data is noisy (weight 0.15). Every contract decision your
analysts have verified is compiled into this number."

### 1.2 Why This Is a Good Validation Target

S2P differs from SOC in ways that stress-test the GAE abstractions:

| Dimension | SOC | S2P | Design Stress |
|---|---|---|---|
| Time pressure | Seconds (active threat) | Hours/days (procurement cycle) | CalibrationProfile.temperature must support softer distributions (S2P-V3B required) |
| Penalty asymmetry | 20:1 (missed threat = breach) | 5:1 (bad approval = overspend) | CalibrationProfile.penalty_ratio configurable ✅ |
| Factor semantics | Security signals (d=6) | **Domain-level risk scores (d=8)** | FactorComputer protocol domain-free ✅ |
| **Factor dimensionality** | **d=6** | **d=8** | **ProfileScorer accepts any d. DiagonalKernel accepts any d.** ✅ |
| **Noise structure** | **Ratio ≈ 2.6×** | **Ratio ≈ 1.8×** | **DiagonalKernel advantage +13.2pp SOC vs +6.8pp S2P (proportional)** |
| **Correlation density** | Sparse (few ρ>0.5) | **Dense (5 pairs ρ>0.60, avg ρ≈0.43)** | **Off-diagonal adds <1pp (CLAIM-57). Noise ratio only.** |
| Decay classes | campaign/standard/permanent | permanent/standard/campaign | CalibrationProfile accepts any string key ✅ |
| ATT&CK techniques | T1078, T1566, etc. | N/A | EvaluationScenario: no technique_id ✅ |
| Graph structure | Users, Alerts, ThreatIntel | Suppliers, POs, Contracts, Commodities | DomainConfig ABC accepts any schema ✅ |
| Bootstrap volume | 1,200 decisions (SOC) | 800 decisions (fewer PR categories) | n_decisions configurable ✅ |
| Shadow mode threshold | 300 decisions (SOC) | **250 decisions (KernelSelector stabilization)** | Configurable. Data-driven, not calendar. |

### 1.3 S2P Domain Context

*(Unchanged from v0.3 — multi-agent blog relationship, platform claim.)*

**The platform claim this validates:** "Same engine, different domain, same accuracy trajectory."
S2P is not a separate product — it is the evidence that GAE, ci-platform, and the evaluation
framework are genuinely domain-agnostic. **V-MV-KERNEL factorial already validated this:**
DiagonalKernel works on both SOC (d=6, +13.2pp) and S2P (d=8, +6.8pp). Same kernel, different
factor space, both improve.

---

## 2. S2P Categories (C=5)

*(Unchanged from v0.3. Categories are routing, not scoring.)*

**ORDER IS PERMANENT** — bound to centroid tensor axis 0. Never reorder.

| Index | Category | Description | SOC Analog |
|---|---|---|---|
| 0 | `routine_purchase` | Standard recurring from approved suppliers, within budget, < $10K | travel_anomaly |
| 1 | `high_value_contract` | > $50K (configurable), requires additional scrutiny | credential_access |
| 2 | `compliance_sensitive` | OFAC-adjacent, SOX-sensitive, FCPA-risk, strategic reserve | threat_intel_match |
| 3 | `sole_source` | Single-supplier, no qualified alternative | insider_threat |
| 4 | `emergency_procurement` | Urgency flag set, bypass standard review | cloud_infrastructure |

---

## 3. S2P Factors (d=8) — REDESIGNED v0.4

**MAJOR CHANGE from v0.3:** Six operational factors replaced by eight domain-level risk
scores. Each domain score is a [0,1] aggregation of multiple signals within its risk domain.

**Rationale for d=8 (from multivariate_foundation_design_note_v3 §6.2):**
- 8×8 covariance matrix = 36 free parameters. Estimable from ~80-100 decisions.
- 40×40 (raw factors) = 820 free parameters. Needs 500+ decisions.
- Domain scores are the natural aggregation layer — each domain model handles
  within-domain correlations internally.
- Factor completeness (residual analysis) operates at domain level: "you're missing
  a domain" is more actionable than "you're missing factor 37 of 50."

**ORDER IS PERMANENT** — bound to centroid tensor axis 2. Never reorder.

| Index | Factor (Domain Score) | Decay Class | Rate | Aggregates |
|---|---|---|---|---|
| 0 | `supplier_risk` | permanent | 0.0001 | Supplier tier, delivery history, quality scores, financial health (D&B), OFAC clearance. Categorical encoding at copilot layer. |
| 1 | `logistics_risk` | campaign | 0.005 | Lead times, transit reliability, route disruptions, port congestion, mode availability. Evolves over weeks with logistics conditions. |
| 2 | `demand_risk` | standard | 0.001 | Forecast accuracy, demand volatility, order pattern changes, seasonal adjustments, bullwhip indicators. |
| 3 | `inventory_risk` | standard | 0.001 | Safety stock levels, stockout frequency, days of supply, obsolescence risk, buffer adequacy. |
| 4 | `regulatory_risk` | campaign | 0.005 | OFAC/SOX/FCPA compliance status, trade restrictions, export controls, sanctions exposure, jurisdiction risk. |
| 5 | `geopolitical_risk` | campaign | 0.005 | Country risk, conflict exposure, sanctions, trade policy instability, supply route security. |
| 6 | `financial_risk` | standard | 0.001 | Supplier credit health, FX exposure, commodity price pass-through, cost of capital, working capital stress. |
| 7 | `environmental_risk` | campaign | 0.005 | Climate disruption exposure, resource scarcity, sustainability compliance, route weather risk. |

**Decay class distribution:** 1 permanent (supplier master data), 3 standard (business cycles),
4 campaign (event-driven risk domains that evolve over weeks). The transient class from v0.3
(price_variance at 0.02) is absorbed into financial_risk (standard decay) — commodity price
volatility is one input to the financial domain score, not a standalone factor.

**Mapping from v0.3 factors → v0.4 domains:**

| v0.3 Factor | v0.4 Domain | Notes |
|---|---|---|
| supplier_reliability | supplier_risk (index 0) | Broadened: adds D&B financial health, OFAC status |
| spend_compliance | Split: financial_risk (6) + regulatory_risk (4) | Budget is financial; SOX/FCPA is regulatory |
| dual_source | supplier_risk (0) + logistics_risk (1) | Dual-source is supplier availability + logistics alternatives |
| geopolitical_risk | geopolitical_risk (5) | Unchanged domain, broader inputs |
| historical_approval | Absorbed into ALL domains (via decay) | Historical patterns compound through centroid evolution, not a standalone factor |
| price_variance | financial_risk (6) | One input to financial domain score |

**Two NEW domains (not in v0.3):**
- **demand_risk (index 2):** Demand volatility was invisible in v0.3. Critical for manufacturing/retail.
- **environmental_risk (index 7):** Climate disruption was implicit in geopolitical_risk. Now independent — food & agriculture sectors need it as primary risk driver.

### 3.1 Cross-Domain Correlation Structure

**Two-judge validated (GPT-4o + Opus). Full details in
multivariate_foundation_design_note_v3 §6.3 and s2p_correlation_research_prompt.**

**Three overlapping clusters with two coupling backbones:**
```
Policy-Statecraft Backbone:  Geopolitical → Regulatory → Financial → Supplier
Flow-Buffer Backbone:        Logistics → Inventory → Supplier → Demand
Physical-World Cluster:      Environmental → Logistics → Supplier
Intersection Node:           Supplier (sits in both backbones)
```

**Top 5 strong pairs (ρ > 0.60):**

| Pair | Est. ρ | Mechanism |
|---|---|---|
| Geopolitical ↔ Regulatory | 0.72 | Sanctions, export controls, tariffs |
| Supplier ↔ Financial | 0.70 | Credit stress degrades supplier performance |
| Geopolitical ↔ Financial | 0.68 | Conflict reprices FX, commodities, sovereign risk |
| Demand ↔ Inventory | 0.65 | Forecast error → stockouts directly |
| Logistics ↔ Inventory | 0.60 | Lead-time volatility → safety stock inadequacy |

**8×8 Σ matrix (Regime A baseline, domain ordering SUP/LOG/DEM/INV/REG/GEO/FIN/ENV):**
```
      SUP   LOG   DEM   INV   REG   GEO   FIN   ENV
SUP [1.00, 0.48, 0.35, 0.62, 0.45, 0.58, 0.70, 0.50]
LOG [0.48, 1.00, 0.42, 0.60, 0.40, 0.55, 0.38, 0.65]
DEM [0.35, 0.42, 1.00, 0.65, 0.18, 0.28, 0.40, 0.25]
INV [0.62, 0.60, 0.65, 1.00, 0.30, 0.30, 0.48, 0.35]
REG [0.45, 0.40, 0.18, 0.30, 1.00, 0.72, 0.52, 0.30]
GEO [0.58, 0.55, 0.28, 0.30, 0.72, 1.00, 0.68, 0.35]
FIN [0.70, 0.38, 0.40, 0.48, 0.52, 0.68, 1.00, 0.35]
ENV [0.50, 0.65, 0.25, 0.35, 0.30, 0.35, 0.35, 1.00]
```

**Critical finding from V-MV-KERNEL (CLAIM-57):** Despite this dense correlation structure
(5 pairs above ρ=0.60, avg ρ≈0.43), off-diagonal correlations add <1pp to scoring accuracy.
DiagonalKernel (1/σ²) captures the entire kernel advantage. The Σ matrix informs domain
understanding and residual analysis, NOT kernel selection.

---

## 4. S2P Actions (A=5)

*(Unchanged from v0.3. Same 5 actions, same ordering.)*

| Index | Action | SOC Analog |
|---|---|---|
| 0 | `approve` | suppress |
| 1 | `hold_for_review` | investigate |
| 2 | `reject` | (no direct analog) |
| 3 | `escalate_compliance` | escalate |
| 4 | `refer_to_analyst` | refer_to_analyst |

---

## 5. S2P Graph Schema

### 5.1 Entities

*(Largely unchanged from v0.3. Added DomainRiskScore node for d=8 architecture.)*

All v0.3 entities retained: Supplier, PurchaseRequisition, Contract, Commodity, BudgetCenter,
ComplianceRule, Decision, ProfileSnapshot, GeopoliticalEvent, MarketIndex, TradeSanction.

**New entity (v0.4):**

| Label | Key Properties | Purpose |
|---|---|---|
| **DomainRiskScore** | domain (str), score (float), computed_at (datetime), pr_id (str), factor_vector_index (int) | Stores per-PR domain-level risk score with provenance. Links computed score back to source entities. Enables residual analysis (design_note_v3 §5.1). |

### 5.2 Relationships

*(v0.3 relationships retained. Added SCORED_BY for domain risk provenance.)*

New relationship:
- DomainRiskScore → SCORED_BY → {Supplier, Commodity, Contract, GeopoliticalEvent, MarketIndex, TradeSanction, ...}

### 5.3 domain_schema.yaml (v0.4 — updated for d=8)

```yaml
domain: s2p
version: "0.4"
description: "Source-to-Pay procurement copilot — 8 domain-level risk scores"

categories:
  - routine_purchase       # index 0
  - high_value_contract    # index 1
  - compliance_sensitive   # index 2
  - sole_source            # index 3
  - emergency_procurement  # index 4

actions:
  - approve               # index 0
  - hold_for_review       # index 1
  - reject                # index 2
  - escalate_compliance   # index 3
  - refer_to_analyst      # index 4

factors:
  - name: supplier_risk        # index 0
    decay_class: permanent
  - name: logistics_risk       # index 1
    decay_class: campaign
  - name: demand_risk          # index 2
    decay_class: standard
  - name: inventory_risk       # index 3
    decay_class: standard
  - name: regulatory_risk      # index 4
    decay_class: campaign
  - name: geopolitical_risk    # index 5
    decay_class: campaign
  - name: financial_risk       # index 6
    decay_class: standard
  - name: environmental_risk   # index 7
    decay_class: campaign

decay_class_rates:
  permanent: 0.0001
  standard:  0.001
  campaign:  0.005

kernel:
  default: diagonal          # v0.4 NEW — DiagonalKernel is default
  cold_start: l2             # Before P28 measures per-factor σ
  selector_rule: "noise_ratio > 1.5 → diagonal"
  selector_min_decisions: 250
```

---

## 6. S2P Factor Implementations (Design) — REDESIGNED v0.4

All 8 implement `FactorComputer.compute(entity_id: str, context: dict) → float`.
Each domain score aggregates multiple graph signals into a single [0,1] value.
All Cypher queries MUST traverse relationships, not read properties (P10 discipline).

### 6.1 SupplierRiskFactor (index 0)

```python
class SupplierRiskFactor(FactorComputer):
    """Domain-level supplier risk score. Aggregates: tier, delivery,
    quality, financial health (D&B), OFAC clearance, contract status.
    
    Graph traversal:
      MATCH (pr)-[:SUBMITTED_BY]->(s:Supplier)-[:HAS_CONTRACT]->(c:Contract)
      OPTIONAL MATCH (s)-[:CLEARED_AGAINST]->(ts:TradeSanction {status:'active'})
      RETURN s.tier, s.risk_rating, c.compliance_status, ts.sanction_id,
             s.financial_health_score, s.delivery_on_time_pct
    
    Encoding: weighted composite of sub-signals.
      Active sanction → 0.0 (HARD FLOOR)
      Otherwise: 0.3*tier_score + 0.25*financial_health + 0.25*delivery +
                 0.1*contract_compliance + 0.1*risk_rating_inverse
    
    Decay: permanent (supplier master data changes over months).
    """
    name = "supplier_risk"
    decay_class = "permanent"
```

### 6.2 LogisticsRiskFactor (index 1)

```python
class LogisticsRiskFactor(FactorComputer):
    """Domain-level logistics risk. Aggregates: lead times, transit
    reliability, route disruptions, port status, mode availability.
    
    Graph traversal:
      MATCH (pr)-[:SUBMITTED_BY]->(s:Supplier)-[:LOCATED_IN]->(region)
      OPTIONAL MATCH (ge:GeopoliticalEvent)-[:AFFECTS_REGION]->(region)
        WHERE ge.severity IN ['HIGH','MEDIUM'] AND ge.start_date > datetime()-duration({days:90})
      MATCH (pr)-[:REQUIRES]->(com:Commodity)<-[:DELIVERS]-(s)
      RETURN s.avg_lead_time_days, s.on_time_delivery_pct,
             count(ge) AS active_disruptions, com.supply_route_risk
    
    Encoding:
      Active route disruption (HIGH severity) → 0.1
      on_time < 70% → 0.2
      on_time 70-85% + no disruptions → 0.5
      on_time 85-95% → 0.7
      on_time > 95% + stable routes → 1.0
    
    Decay: campaign (0.005). Logistics conditions evolve over weeks.
    """
    name = "logistics_risk"
    decay_class = "campaign"
```

### 6.3 DemandRiskFactor (index 2)

```python
class DemandRiskFactor(FactorComputer):
    """Domain-level demand risk. Aggregates: forecast accuracy, demand
    volatility, order pattern changes, seasonal adjustments.
    
    Graph traversal:
      MATCH (pr)-[:REQUIRES]->(com:Commodity)
      OPTIONAL MATCH (com)<-[:REQUIRES]-(prev:PurchaseRequisition)
        WHERE prev.created_at > datetime()-duration({days:90})
      RETURN count(prev) AS recent_pr_count,
             stdev(prev.amount) AS amount_volatility,
             avg(prev.amount) AS avg_amount,
             pr.amount AS current_amount
    
    Encoding:
      CV (amount_volatility/avg_amount) > 0.5 → 0.2 (high demand uncertainty)
      CV 0.3-0.5 → 0.5
      CV 0.1-0.3 → 0.7
      CV < 0.1 → 0.9 (stable demand)
      Adjustment: if current_amount > 2× avg_amount → reduce by 0.2 (demand spike)
    
    Decay: standard (0.001). Demand patterns evolve over business cycles.
    """
    name = "demand_risk"
    decay_class = "standard"
```

### 6.4 InventoryRiskFactor (index 3)

```python
class InventoryRiskFactor(FactorComputer):
    """Domain-level inventory risk. Aggregates: safety stock, stockout
    frequency, days of supply, buffer adequacy.
    
    Graph traversal:
      MATCH (pr)-[:REQUIRES]->(com:Commodity)
      OPTIONAL MATCH (com)-[:TRACKED_BY]->(mi:MarketIndex)
      RETURN com.safety_stock_days, com.current_stock_days,
             com.stockout_count_90d, com.strategic_flag
    
    Encoding:
      current_stock < safety_stock → 0.1 (below safety stock — critical)
      current_stock < 2× safety_stock → 0.4
      current_stock 2-4× safety_stock → 0.7
      current_stock > 4× safety_stock → 0.9 (well buffered)
      Strategic commodity with low stock: additional -0.2 penalty
    
    Decay: standard (0.001). Inventory levels adjust over business cycles.
    """
    name = "inventory_risk"
    decay_class = "standard"
```

### 6.5 RegulatoryRiskFactor (index 4)

```python
class RegulatoryRiskFactor(FactorComputer):
    """Domain-level regulatory risk. Aggregates: OFAC/SOX/FCPA status,
    export controls, trade restrictions, jurisdiction risk.
    
    Graph traversal:
      MATCH (pr)-[:REQUIRES]->(com:Commodity)
      OPTIONAL MATCH (cr:ComplianceRule)-[:APPLIES_TO]->(com)
        WHERE cr.active = true
      MATCH (pr)-[:SUBMITTED_BY]->(s:Supplier)-[:LOCATED_IN]->(region)
      OPTIONAL MATCH (s)-[:CLEARED_AGAINST]->(ts:TradeSanction {status:'active'})
      RETURN count(cr) AS active_rules, ts.authority,
             region.sanctions_risk_level, pr.amount
    
    Encoding:
      Active sanction on supplier → 0.0 (HARD FLOOR)
      active_rules > 3 AND amount > threshold → 0.2
      active_rules 1-3 → 0.4
      No active rules, compliant jurisdiction → 0.9
      Clean supplier + clean commodity + clean jurisdiction → 1.0
    
    Decay: campaign (0.005). Regulatory landscape shifts with policy events.
    """
    name = "regulatory_risk"
    decay_class = "campaign"
```

### 6.6 GeopoliticalRiskFactor (index 5)

```python
class GeopoliticalRiskFactor(FactorComputer):
    """Domain-level geopolitical risk. Aggregates: country risk, conflict
    exposure, trade policy instability, supply route security.
    
    (Same traversal logic as v0.3 §6.4 — broadened to include trade policy
    and route security signals alongside sanctions and events.)
    
    Encoding:
      Active sanction (any authority) → 0.0 (HARD FLOOR)
      Active GeopoliticalEvent HIGH → 0.1
      Active GeopoliticalEvent MEDIUM → 0.3
      Trade policy instability (tariff changes <90 days) → 0.4
      Stable region, no events → 1.0
    
    Decay: campaign (0.005).
    """
    name = "geopolitical_risk"
    decay_class = "campaign"
```

### 6.7 FinancialRiskFactor (index 6)

```python
class FinancialRiskFactor(FactorComputer):
    """Domain-level financial risk. Aggregates: supplier credit health,
    FX exposure, commodity price pass-through, spend compliance, working capital.
    
    Graph traversal:
      MATCH (pr)-[:SUBMITTED_BY]->(s:Supplier)
      OPTIONAL MATCH (s)-[:HAS_CONTRACT]->(c:Contract)
      MATCH (pr)-[:CHARGES_TO]->(bc:BudgetCenter)
      OPTIONAL MATCH (pr)-[:REQUIRES]->(com:Commodity)-[:TRACKED_BY]->(mi:MarketIndex)
      RETURN s.financial_health_score, s.credit_rating,
             pr.amount, bc.annual_budget, bc.ytd_spend,
             mi.current_value, mi.30d_change_pct,
             c.spend_limit
    
    Encoding: weighted composite.
      0.30 * spend_compliance (pr.amount / budget_remaining)
      0.25 * supplier_credit (D&B normalized)
      0.25 * price_stability (1 - abs(mi.30d_change_pct))
      0.20 * contract_headroom (1 - spend_vs_limit)
      
      All sub-scores [0,1]. Composite clipped to [0,1].
    
    Decay: standard (0.001). Financial conditions shift with business cycles.
    Note: Absorbs v0.3's spend_compliance and price_variance factors.
    """
    name = "financial_risk"
    decay_class = "standard"
```

### 6.8 EnvironmentalRiskFactor (index 7)

```python
class EnvironmentalRiskFactor(FactorComputer):
    """Domain-level environmental risk. Aggregates: climate disruption
    exposure, resource scarcity, sustainability compliance, route weather.
    
    Graph traversal:
      MATCH (pr)-[:SUBMITTED_BY]->(s:Supplier)-[:LOCATED_IN]->(region)
      OPTIONAL MATCH (ge:GeopoliticalEvent)-[:AFFECTS_REGION]->(region)
        WHERE ge.event_type = 'environmental'
        AND ge.start_date > datetime()-duration({days:90})
      MATCH (pr)-[:REQUIRES]->(com:Commodity)
      RETURN ge.severity, ge.description, com.climate_sensitivity,
             region.environmental_risk_score
    
    Encoding:
      Active environmental event HIGH (drought, flood, wildfire) → 0.1
      Active environmental event MEDIUM → 0.4
      Climate-sensitive commodity + vulnerable region → 0.3
      Stable region, resilient commodity → 0.9
      No environmental exposure → 1.0
    
    Decay: campaign (0.005). Environmental conditions shift over weeks.
    
    Industry note: For food & agriculture, this is the PRIMARY risk driver.
    DomainConfig.factor_weight_prior should upweight environmental_risk for
    food sector deployments (from two-judge correlation research §6.3).
    """
    name = "environmental_risk"
    decay_class = "campaign"
```

---

## 7. S2P Profile Centroids μ₀ (Design) — RESHAPED v0.4

### 7.1 Shape and Axes

```
μ₀.shape = (5, 5, 8)
  Axis 0: category  [routine_purchase, high_value_contract, compliance_sensitive,
                      sole_source, emergency_procurement]
  Axis 1: action    [approve, hold_for_review, reject, escalate_compliance,
                      refer_to_analyst]
  Axis 2: factor    [supplier_risk, logistics_risk, demand_risk, inventory_risk,
                      regulatory_risk, geopolitical_risk, financial_risk,
                      environmental_risk]

All values in [0.0, 1.0]. Clipping enforced on every update.

DiagonalKernel weights = 1/σ² per factor from P28 measurement.
Factor ordering matches the 8×8 Σ matrix (SUP/LOG/DEM/INV/REG/GEO/FIN/ENV).
```

### 7.2 Category 0: routine_purchase

```python
routine_purchase = np.array([
    # approve: all domains green — reliable supplier, stable logistics, steady demand,
    #          good inventory, no regulatory issues, stable geo, healthy financials, no env risk
    [0.90, 0.85, 0.80, 0.80, 0.85, 0.85, 0.80, 0.85],
    # hold_for_review: ambiguous in one domain
    [0.55, 0.55, 0.55, 0.55, 0.60, 0.65, 0.50, 0.55],
    # reject: financial domain broken (budget exceeded or price spike)
    [0.40, 0.55, 0.50, 0.45, 0.60, 0.60, 0.10, 0.55],
    # escalate_compliance: regulatory or geo signal on routine PR
    [0.65, 0.60, 0.60, 0.55, 0.15, 0.15, 0.60, 0.60],
    # refer_to_analyst: borderline on one domain
    [0.65, 0.60, 0.60, 0.60, 0.60, 0.60, 0.55, 0.60],
])
```

### 7.3 Category 1: high_value_contract

```python
high_value_contract = np.array([
    # approve: all domains strongly green — high bar for high value
    [0.92, 0.85, 0.80, 0.75, 0.85, 0.85, 0.80, 0.80],
    # hold_for_review: high-value always merits review unless all strongly green
    [0.55, 0.55, 0.55, 0.55, 0.60, 0.60, 0.55, 0.55],
    # reject: financial or inventory crisis at high value
    [0.45, 0.50, 0.45, 0.35, 0.55, 0.55, 0.08, 0.50],
    # escalate_compliance: high-value + regulatory/geo/supplier concern
    [0.55, 0.50, 0.50, 0.45, 0.20, 0.20, 0.40, 0.45],
    # refer_to_analyst: moderate signals — specialist review at this value
    [0.60, 0.55, 0.55, 0.55, 0.55, 0.55, 0.50, 0.55],
])
```

### 7.4 Category 2: compliance_sensitive

```python
compliance_sensitive = np.array([
    # approve: all compliance-adjacent domains green
    [0.88, 0.80, 0.75, 0.75, 0.90, 0.90, 0.80, 0.80],
    # hold_for_review: some compliance uncertainty
    [0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.50, 0.50],
    # reject: clear compliance violation in financial domain
    [0.40, 0.50, 0.45, 0.40, 0.50, 0.50, 0.10, 0.45],
    # escalate_compliance: THE DOMINANT ACTION — regulatory + geo signals
    [0.50, 0.45, 0.45, 0.40, 0.10, 0.10, 0.40, 0.40],
    # refer_to_analyst: borderline compliance
    [0.55, 0.50, 0.50, 0.50, 0.45, 0.45, 0.48, 0.50],
])
```

### 7.5 Category 3: sole_source

```python
sole_source = np.array([
    # approve: near impossible — requires extraordinary strength across all domains
    # supplier_risk still high because sole-source doesn't mean unreliable
    [0.90, 0.85, 0.80, 0.75, 0.90, 0.90, 0.85, 0.85],
    # hold_for_review: sole source with good but not exceptional signals
    [0.70, 0.65, 0.60, 0.55, 0.75, 0.75, 0.65, 0.65],
    # reject: sole source + financial/inventory crisis
    [0.40, 0.45, 0.40, 0.20, 0.55, 0.55, 0.15, 0.40],
    # escalate_compliance: sole source waiver needed — default escalation
    [0.55, 0.50, 0.50, 0.45, 0.40, 0.40, 0.50, 0.50],
    # refer_to_analyst: most sole source PRs need specialist
    [0.62, 0.58, 0.55, 0.52, 0.65, 0.65, 0.55, 0.58],
])
```

### 7.6 Category 4: emergency_procurement

```python
emergency_procurement = np.array([
    # approve: genuine emergency + all domains reasonably green
    [0.80, 0.75, 0.65, 0.60, 0.80, 0.80, 0.75, 0.75],
    # hold_for_review: emergency flag frequently misused — default to review
    [0.55, 0.55, 0.50, 0.50, 0.55, 0.55, 0.50, 0.50],
    # reject: emergency + financial domain broken
    [0.40, 0.50, 0.40, 0.35, 0.55, 0.55, 0.10, 0.45],
    # escalate_compliance: emergency + regulatory/geo signal
    [0.55, 0.50, 0.45, 0.40, 0.20, 0.20, 0.40, 0.45],
    # refer_to_analyst: ambiguous emergency — borderline confidence
    [0.55, 0.52, 0.48, 0.48, 0.55, 0.55, 0.48, 0.50],
])
```

### 7.7 Full μ₀ Tensor Construction

```python
import numpy as np

def get_profile_centroids() -> np.ndarray:
    """μ₀: (5, 5, 8) — 5 categories × 5 actions × 8 domain risk scores.
    
    v0.4: Reshaped from (5,5,6) to (5,5,8). Domain-level risk scores.
    DiagonalKernel weights (1/σ²) applied during scoring — weights come from
    P28 Phase 2 per-factor σ measurement, not from this tensor.
    
    DESIGN STATUS: Expert-initialized. Requires S2P-EVAL-1 bootstrap validation.
    """
    centroids = np.stack([
        routine_purchase,        # category 0
        high_value_contract,     # category 1
        compliance_sensitive,    # category 2
        sole_source,             # category 3
        emergency_procurement,   # category 4
    ])  # shape: (5, 5, 8)
    
    assert centroids.shape == (5, 5, 8), f"Expected (5,5,8), got {centroids.shape}"
    assert centroids.min() >= 0.0 and centroids.max() <= 1.0
    return centroids
```

---

## 8. S2P Domain Configuration — UPDATED v0.4

### 8.1 S2PDomainConfig (key changes from v0.3)

```python
class S2PDomainConfig:
    """S2P domain configuration — v0.4.
    
    SHAPE: (C=5, A=5, d=8).  ← was d=6 in v0.3
    DiagonalKernel is default. KernelSelector determines at P28 Phase 2.
    CovarianceEstimator collects 8×8 Σ (research asset for v7.0).
    """
    
    @staticmethod
    def get_factors() -> list[str]:
        """d=8. ORDER IS PERMANENT — bound to centroid axis 2.
        v0.4: Domain-level risk scores replace operational factors."""
        return [
            "supplier_risk",        # index 0
            "logistics_risk",       # index 1
            "demand_risk",          # index 2
            "inventory_risk",       # index 3
            "regulatory_risk",      # index 4
            "geopolitical_risk",    # index 5
            "financial_risk",       # index 6
            "environmental_risk",   # index 7
        ]
    
    @staticmethod
    def get_calibration_profile() -> CalibrationProfile:
        """S2P learning hyperparameters — v0.4 update.
        
        KERNEL: DiagonalKernel is default (V-MV-KERNEL validated: +6.8pp S2P).
        KernelSelector Phase 2 rule: noise_ratio > 1.5 → diagonal.
        L2 is cold-start fallback before P28 measures per-factor σ.
        
        TEMPERATURE: τ=0.1 (SOC-validated). S2P-V3B still required to confirm.
        
        PENALTY: 5:1 (design estimate). Cost-benefit analysis still needed.
        """
        return CalibrationProfile(
            temperature=0.1,
            penalty_ratio=5.0,
            extensions={
                "eta":         0.05,
                "eta_neg":     0.05,
                "eta_override": 0.01,  # v0.4 NEW: asymmetric η validated
                "count_decay": 0.001,
                "kernel":      "diagonal",  # v0.4: was "l2"
            },
            decay_class_rates={
                "permanent":  0.0001,
                "standard":   0.001,
                "campaign":   0.005,
                # "transient" removed — absorbed into financial_risk (standard)
            },
        )
    
    @staticmethod
    def get_factor_decay_classes() -> dict[str, str]:
        """v0.4: 8 domain-level risk scores."""
        return {
            "supplier_risk":      "permanent",
            "logistics_risk":     "campaign",
            "demand_risk":        "standard",
            "inventory_risk":     "standard",
            "regulatory_risk":    "campaign",
            "geopolitical_risk":  "campaign",
            "financial_risk":     "standard",
            "environmental_risk": "campaign",
        }
    
    @staticmethod
    def get_kernel_config() -> dict:
        """v0.4 NEW: Kernel configuration for DiagonalKernel + KernelSelector.
        
        DiagonalKernel validated on S2P: +6.8pp (V-S2P-HETERO, 18 cells).
        ShrinkageKernel adds -0.2pp vs diagonal (even with dense ρ≈0.43).
        Noise ratio determines kernel, not correlation structure (Explanation A).
        """
        return {
            "default_kernel":       "diagonal",
            "cold_start_kernel":    "l2",
            "selector_rule":        "noise_ratio > 1.5",
            "selector_window":      100,    # rolling 100-decision window
            "selector_min_decisions": 250,  # lock at 250 verified decisions
            "covariance_collect":   True,   # CovarianceEstimator active
            "covariance_scoring":   False,  # NOT used for scoring at v6.5
            "covariance_half_life": 300,    # exponential decay for regime tracking
        }
    
    @staticmethod
    def get_correlation_prior() -> dict:
        """v0.4 NEW: Two-judge validated correlation structure for this domain.
        
        NOT used for kernel selection (noise ratio only).
        Used for: residual analysis, disruption archetype detection (v7.0),
        factor weight priors, industry-specific DomainConfig.
        
        See multivariate_foundation_design_note_v3 §6.3 and
        s2p_correlation_research_prompt for full 28-pair matrix.
        """
        return {
            "strong_pairs": [
                ("geopolitical_risk", "regulatory_risk", 0.72),
                ("supplier_risk", "financial_risk", 0.70),
                ("geopolitical_risk", "financial_risk", 0.68),
                ("demand_risk", "inventory_risk", 0.65),
                ("logistics_risk", "inventory_risk", 0.60),
            ],
            "cluster_backbones": {
                "policy_statecraft": ["geopolitical_risk", "regulatory_risk",
                                      "financial_risk", "supplier_risk"],
                "flow_buffer": ["logistics_risk", "inventory_risk",
                                "supplier_risk", "demand_risk"],
            },
            "intersection_node": "supplier_risk",
            "regime_a_avg_rho": 0.43,
        }
    
    @staticmethod
    def get_shadow_config() -> dict:
        """v0.4 update: 250 decisions (was 200 in v0.3).
        Aligned with KernelSelector stabilization threshold."""
        return {
            "shadow_mode_active":           False,
            "shadow_decision_count_target": 250,    # was 200; aligned with KernelSelector
            "shadow_report_by_category":    True,
            "auto_activate_threshold":      None,
            "store_analyst_action":         True,
            "activation_requires_confirm":  True,
        }
    
    # get_actions(), get_categories(), get_profile_centroids(),
    # get_category_thresholds(), get_pr_category_mapping(),
    # get_drift_bounds(), get_checkpoint_config(), get_domain_constraint_spec(),
    # get_source_connectors(), get_graph_schema(), get_bootstrap_config(),
    # get_semantic_concepts(), get_query_catalog()
    # — all retain v0.3 structure with d=8 shape updates where applicable.
    # Full implementations in companion code spec.
```

### 8.2 build_profile_scorer() for S2P (v0.4)

```python
def build_s2p_profile_scorer() -> ProfileScorer:
    """Factory function for S2P ProfileScorer — v0.4.
    
    v0.4 changes: DiagonalKernel default, d=8 domain scores.
    KernelSelector determines kernel at P28 Phase 2.
    """
    config = S2PDomainConfig()
    mu = config.get_profile_centroids()  # (5, 5, 8) — was (5, 5, 6)
    actions = config.get_actions()       # 5 actions
    calibration = config.get_calibration_profile()
    kernel_config = config.get_kernel_config()
    
    scorer = build_profile_scorer(
        mu=mu,
        actions=actions,
        calibration=calibration,
        kernel_type=kernel_config["default_kernel"],  # "diagonal"
    )
    
    # Bootstrap
    bootstrap_cfg = config.get_bootstrap_config()
    learning_state = LearningState(profile_scorer=scorer, calibration=calibration)
    learning_state.bootstrap_calibrate(
        n_decisions=bootstrap_cfg["n_decisions"],
        seed=bootstrap_cfg["seed"],
    )
    
    return scorer
```

---

*End of Part 1. Part 2 covers §9-20: connectors, hooks, IKS, NL templates,
intelligence layer, experiments (updated with V-MV-KERNEL results + SVM methodology),
validation checklist (updated: OLSMonitor added, V-CGA-FROZEN→SVM-003, Phase 2 components),
version placement (updated: Phase 3 Priority 2 + CopilotFramework extraction),
co-design constraints, and summary.*

*S2P Copilot — Design Document v0.5 Part 1 · March 25, 2026*


## 9. S2P Source Integration

### 9.1 The "First Mile" in Procurement

*(Unchanged from v0.3 — same SourceConnectorProtocol pattern.)*

The same pattern as SOC: the compounding engine needs data flowing before it can compound.
The d=8 domain-level risk scores aggregate signals from 10+ procurement data sources. Until
these sources flow into the context graph, the domain-level factor computers have nothing
to compute on.

### 9.2 S2P Data Sources (updated for d=8)

| Source | Tier | Entity Types | Feeds Domain Factors | Update |
|---|---|---|---|---|
| **OFAC Sanctions List** | 1 | TradeSanction + SANCTIONED_BY | regulatory_risk, geopolitical_risk, supplier_risk | Daily |
| **D&B / Bloomberg** | 1 | Supplier (financial health, credit) | supplier_risk, financial_risk | Weekly |
| **LME / CME / USDA** | 2 | MarketIndex (price, 30d_change) | financial_risk, environmental_risk (agri) | Daily |
| **Recorded Future / RANE** | 2 | GeopoliticalEvent | geopolitical_risk, logistics_risk, environmental_risk | Hourly |
| **Internal ERP** (SAP/Oracle) | 1 | Supplier, Contract, BudgetCenter, PR, PO | supplier_risk, financial_risk, demand_risk, inventory_risk | Real-time (Phase 4) |
| **Trade press / analyst reports** | 3 | Supplier (news, M&A, disruptions) | supplier_risk, financial_risk | Periodic (Phase 4+) |
| **Logistics tracking** (Flexport, project44) | 2 | ShipmentStatus, RouteDisruption | logistics_risk, inventory_risk | Daily |
| **Weather / climate feeds** | 2 | EnvironmentalEvent | environmental_risk, logistics_risk | Daily |

**New sources (v0.4):** Logistics tracking and weather/climate feeds are needed to populate
logistics_risk and environmental_risk — the two new domain factors not in v0.3.

### 9.3 Source Trust Tiers

*(Unchanged from v0.3 — same SourceTrustWeighting class.)*

| Tier | S2P Sources | Multiplier |
|---|---|---|
| 1 (Authoritative) | OFAC, D&B, Internal ERP | 1.00 |
| 2 (Vendor) | LME/CME, GeoRisk, Logistics tracking, Weather | 0.85 |
| 3 (Research) | Trade press, analyst reports | 0.65 |
| 4 (OSINT) | Industry forums, social signals | 0.40 |

### 9.4 Connector Specifications

*(v0.3 connectors retained: OFACConnector, DunBradstreetConnector, CommodityIndexConnector,
GeoRiskConnector, SAPConnector. Two new connectors added for d=8 domains.)*

```python
class LogisticsTrackingConnector(SourceConnector):
    """Logistics visibility connector (Flexport, project44, or equivalent).
    
    Tier 2 (vendor). Daily update cadence.
    Produces: ShipmentStatus nodes, RouteDisruption nodes.
    Feeds: logistics_risk, inventory_risk domain scores.
    
    entity_type: "ShipmentStatus" / "RouteDisruption"
    MERGE on (shipment_id) — idempotent.
    
    Version gate: Phase 4 (S2P full). Not needed for Phase 3 Priority 2 demo.
    """

class WeatherClimateConnector(SourceConnector):
    """Weather and climate disruption feed connector.
    
    Tier 2 (vendor). Daily update cadence.
    Produces: EnvironmentalEvent nodes linked to regions.
    Feeds: environmental_risk, logistics_risk domain scores.
    
    entity_type: "EnvironmentalEvent"
    Pattern: Same as GeopoliticalEvent — TTL-based, campaign decay (0.005).
    
    Industry note: For food & agriculture, this is the PRIMARY data source.
    DomainConfig.factor_weight_prior should upweight environmental_risk for food.
    
    Version gate: Phase 4. Demo at Phase 3 Priority 2 uses static environmental risk scores.
    """
```

### 9.5 The Cross-Source Compounding Insight

*(Updated for d=8 domain model.)*

A supplier's D&B credit downgrade (financial_risk ↑) combined with a geopolitical event in
their region (geopolitical_risk ↑) combined with a commodity price spike (financial_risk ↑↑)
combined with a port closure near their facility (logistics_risk ↑) creates a compound risk
signal that no single source contains. The graph holds the connections. The domain-level
factor computers aggregate from the enriched graph. The centroids learn which domain
combinations matter. DiagonalKernel weights the domains by reliability — financial_risk at
weight 0.9 (reliable D&B data) while environmental_risk at weight 0.15 (sparse, noisy).

**This is the moat narrative for S2P:** "After 1,000 decisions, the system knows which
domain risk combinations YOUR firm cares about. D&B knows supplier financials. We know how
YOUR firm weighs financial risk against logistics risk against geopolitical risk — and the
kernel weights show you which domains have reliable data and which don't."

### 9.6 Prior Architecture Delta

*(Unchanged from v0.3 — same comparison with 2025 multi-agent blog.)*

---

## 10. Data Preservation Hooks

*(Same three hooks as v0.3. Factor vector shape updated to d=8.)*

| Hook | When | What | Why |
|---|---|---|---|
| **Hook 1: DecisionRecord** | EVERY ProfileScorer.score() | decision_id, action, confidence, factor_vector **(d=8)**, category, kernel_type, kernel_weights, shadow_mode, dispatch_tier | IKS history, GATE-R, similar past PRs |
| **Hook 2: OutcomeRecord** | EVERY ProfileScorer.update() | decision_id, action, correct, outcome, centroid_delta_norm | Chart A, learning audit |
| **Hook 3: ProfileSnapshot** | Every 50 decisions + operator start | centroid_array **(5,5,8)**, observation_counts, t_decision, kernel_weights | IKS, rollback, Level 2 substrate |

**v0.4 additions to Hook 1:** kernel_type ("diagonal" or "l2"), kernel_weights (d=8 vector
of 1/σ² values). These are needed for Adjustment G (epistemic state indicator) and EU AI Act
Art. 15 provenance. Without kernel metadata in Hook 1, the compliance trail is incomplete.

---

## 11. S2P Institutional Knowledge Score (IKS)

### 11.1 Formula

```
IKS_S2P(t) = 100 × min(mean_drift(t) / D_MAX, 1.0)

Where:
  mean_drift(t) = mean over all (c, a) pairs of ‖μ(t)[c,a,:] − μ₀[c,a,:]‖₂
  μ₀ = bootstrap centroid state (post-bootstrap, pre-first-operational-decision)
  d = 8 (domain-level risk scores)
  D_MAX = 0.30  (same as SOC — V2 centroid analysis applies cross-domain)
```

Same formula. Same D_MAX. Same IKSService class (domain-agnostic). The L2 norm operates on
d=8 vectors instead of d=6 — no code change needed (numpy handles variable dimensions).

### 11.2 CPO Framing (updated for d=8 + kernel weights)

| SOC (CISO) | S2P (CPO) |
|---|---|
| "IKS 47.3: Your system knows your environment." | "IKS 34.7: Procurement centroids have moved 35% toward your firm's contract patterns. The kernel weights show financial_risk data is reliable (weight 0.9) while environmental_risk is noisy (weight 0.15)." |
| "847 alerts. 347 auto-approved at 86%." | "847 PRs. 291 auto-approved at 88%. 43 analyst hours recovered. The kernel learned which risk domains to trust." |

### 11.3 IKS Display Locations

*(Unchanged from v0.3 — Tab 2 header, Tab 5 Panel A, Tab 4 ROI block.)*

---

## 12. Shadow Mode

### 12.1 Configuration (updated v0.4)

- `shadow_decision_count_target`: **250** (was 200 in v0.3). Aligned with KernelSelector
  stabilization threshold. At typical procurement volume: 4-8 weeks.
- KernelSelector runs during shadow: BOTH L2 and DiagonalKernel scored on every PR.
  Rolling 100-decision window tracks per-kernel agreement rate.
- KernelSelector locks recommendation at 250 decisions.
- `activation_confirmed_by`: CPO or procurement director. Never auto-activates.

### 12.2 ACTIVATE LIVE MODE Constraint

*(Unchanged from v0.3 — explicit CPO confirmation required.)*

### 12.3 Shadow Report (v0.4 additions)

Shadow report now includes:
- Agreement rate by procurement category (unchanged)
- Top disagreements with NL explanation (unchanged)
- **Kernel recommendation:** "KernelSelector recommends DiagonalKernel (noise_ratio=1.8×,
  confirmed at 250 decisions). 4/4 correct in validation suite."
- **Per-domain noise profile:** "supplier_risk: σ=0.12 (reliable), logistics_risk: σ=0.22
  (noisy), environmental_risk: σ=0.28 (very noisy). The kernel down-weights noisy domains."

---

## 13. NL Template Engine (S2P)

*(Architecture unchanged from v0.3. Template content updated for d=8 domain scores.)*

### 13.1 Three-Layer Model (updated for d=8)

| Layer | Audience | Example Output |
|---|---|---|
| **L1 — Analyst** | Procurement analyst | "APPROVE recommended (91%). Gold-tier supplier (supplier_risk=0.92, weight 0.85). Stable logistics (logistics_risk=0.88, weight 0.40 — noisy region data). Within budget (financial_risk=0.85, weight 0.90). No regulatory concerns." |
| **L2 — CPO** | CPO briefing | "847 PRs this week. 291 auto-approved (34%). IKS 34.7 (+2.1). Top centroid shift: sole_source escalation learned 4 new geopolitical risk patterns. Kernel weights: financial_risk most trusted (0.9), environmental_risk least trusted (0.15)." |
| **L3 — Auditor** | Compliance | "Decision PR-2891: compliance_sensitive. Action: ESCALATE_COMPLIANCE (0.923). Factor vector (d=8): [0.60, 0.55, 0.70, 0.65, 0.12, 0.10, 0.78, 0.40]. Kernel: diagonal (ratio=1.8×). Kernel weights: [0.85, 0.40, 0.60, 0.55, 0.70, 0.80, 0.90, 0.15]. Snapshot: ps-S2P-0047." |

### 13.2 Kernel Weight Integration in Templates

**v0.4 NEW:** Every template can reference kernel weights alongside factor values. The
NLTemplateEngine receives `kernel_weights: np.ndarray` (d=8) alongside `factor_vector`.

Template variable additions:
- `{factor_name}_weight`: kernel weight for each domain (e.g., `{supplier_risk_weight}` → "0.85")
- `{factor_name}_trust`: human-readable trust label ("reliable" / "moderate" / "noisy")
  derived from weight thresholds (>0.5 = reliable, 0.2-0.5 = moderate, <0.2 = noisy)
- `{most_trusted_domain}`: domain with highest kernel weight
- `{least_trusted_domain}`: domain with lowest kernel weight

---

## 14. Intelligence Layer Applicability (S2P)

### 14.1 S2P σ — Synthesis Bias Sources (updated for d=8)

| SOC σ Source | S2P σ Equivalent | Affected Domains |
|---|---|---|
| CISA KEV active exploit | OFAC sanctions alert | regulatory_risk, geopolitical_risk, supplier_risk |
| Active threat campaign | Commodity supply disruption | logistics_risk, inventory_risk, financial_risk |
| CISO directive | CPO directive (expedite/restrict) | All domains (directive-specific) |
| CVE severity score | Commodity price shock | financial_risk, demand_risk |
| Vendor advisory | D&B credit downgrade | supplier_risk, financial_risk |
| Internal incident | Internal compliance finding | regulatory_risk, supplier_risk |
| (no SOC analog) | Environmental disruption (v0.4 NEW) | environmental_risk, logistics_risk |

### 14.2 S2P Action Directions (d=8 domain scores)

```python
# v0.4: action directions updated for 8 domain-level risk scores
# Directions apply to the relevant domain factors, not all 8

"active_sanctions_event": {
    "approve":              +0.8,   # sanctions → strongly LESS likely to approve
    "hold_for_review":      -0.1,
    "reject":               -0.1,
    "escalate_compliance":  -0.8,   # sanctions → strongly MORE likely to escalate
    "refer_to_analyst":     -0.2,
    # Primarily affects: regulatory_risk, geopolitical_risk, supplier_risk
}

"supply_disruption": {
    "approve":              +0.4,
    "hold_for_review":      -0.3,
    "reject":               +0.0,
    "escalate_compliance":  -0.2,
    "refer_to_analyst":     -0.2,
    # Primarily affects: logistics_risk, inventory_risk, supplier_risk
}

"environmental_disruption": {    # v0.4 NEW
    "approve":              +0.3,
    "hold_for_review":      -0.2,
    "reject":               +0.0,
    "escalate_compliance":  -0.1,
    "refer_to_analyst":     -0.2,
    # Primarily affects: environmental_risk, logistics_risk
}

# cpo_directive_expedite and commodity_price_shock unchanged from v0.3
```

### 14.3 Loop 4 Firewall

*(Unchanged from v0.3 — permanent. μ NEVER updated from σ.)*

### 14.4 S2P GATE-M Prerequisites

*(Unchanged from v0.3 — same four experiments, same gate structure.)*

---

## 15. Evaluation Scenarios (Updated for d=8)

EvaluationScenario v5.0 API: name, description, f (d=8 np.ndarray), category_index,
expected_action, expected_action_index.

### S2P-ROUTINE-01: Standard routine approval

```python
EvaluationScenario(
    name="s2p_routine_office_supplies_gold",
    description="Gold-tier supplier, stable across all 8 risk domains",
    f=np.array([0.92, 0.88, 0.80, 0.82, 0.90, 0.90, 0.85, 0.88]),
    # [supplier_risk=0.92 (Gold+active), logistics_risk=0.88 (stable),
    #  demand_risk=0.80 (steady), inventory_risk=0.82 (buffered),
    #  regulatory_risk=0.90 (clean), geopolitical_risk=0.90 (stable),
    #  financial_risk=0.85 (within budget), environmental_risk=0.88 (no events)]
    category_index=0,           # routine_purchase
    expected_action="approve",
    expected_action_index=0,
)
```

### S2P-SOLE-SOURCE-01: Single-source escalation

```python
EvaluationScenario(
    name="s2p_sole_source_titanium_alloy",
    description="Single-supplier titanium. Taiwan tension. Supply chain stress.",
    f=np.array([0.60, 0.35, 0.50, 0.30, 0.40, 0.15, 0.55, 0.45]),
    # [supplier_risk=0.60 (Silver), logistics_risk=0.35 (route disruption),
    #  demand_risk=0.50 (moderate), inventory_risk=0.30 (low stock on strategic),
    #  regulatory_risk=0.40 (export controls), geopolitical_risk=0.15 (HIGH event),
    #  financial_risk=0.55 (ok), environmental_risk=0.45 (moderate)]
    category_index=3,           # sole_source
    expected_action="escalate_compliance",
    expected_action_index=3,
)
```

### S2P-PRICE-SPIKE-01: Financial risk hold

```python
EvaluationScenario(
    name="s2p_steel_plate_price_spike",
    description="Gold supplier, stable logistics, but 2x commodity price spike.",
    f=np.array([0.90, 0.80, 0.60, 0.70, 0.85, 0.85, 0.10, 0.80]),
    # [supplier_risk=0.90, logistics_risk=0.80, demand_risk=0.60,
    #  inventory_risk=0.70, regulatory_risk=0.85, geopolitical_risk=0.85,
    #  financial_risk=0.10 (2x price spike → budget blown), environmental_risk=0.80]
    category_index=1,           # high_value_contract
    expected_action="hold_for_review",
    expected_action_index=1,
)
```

### S2P-LEARN-01: Learning prerequisite scenario

```python
EvaluationScenario(
    name="s2p_office_supplies_learned_approval",
    description="Borderline Silver supplier, but 15 prior approved decisions compound.",
    f=np.array([0.60, 0.70, 0.75, 0.75, 0.85, 0.85, 0.65, 0.80]),
    # All domains moderate — approval depends on accumulated centroid history.
    # Without learning: hold_for_review. With 15 prior approvals: approve.
    category_index=0,           # routine_purchase
    expected_action="approve",
    expected_action_index=0,
)
```

### S2P-SANCTIONS-01: OFAC compliance escalation

```python
EvaluationScenario(
    name="s2p_ofac_adjacent_supplier",
    description="Acceptable supplier BUT active TradeSanction. Regulatory and geo = 0.0.",
    f=np.array([0.70, 0.65, 0.70, 0.70, 0.00, 0.00, 0.75, 0.65]),
    # regulatory_risk=0.00 and geopolitical_risk=0.00 signal active sanctions.
    # Both policy-statecraft backbone domains fire simultaneously.
    category_index=2,           # compliance_sensitive
    expected_action="escalate_compliance",
    expected_action_index=3,
)
```

### S2P-COMPOUND-01: Multi-domain compound shock (v0.4 NEW)

```python
EvaluationScenario(
    name="s2p_compound_shock_geo_logistics_env",
    description="Red Sea rerouting + drought + sanctions = triple compound shock. "
                "Tests whether 8-domain model captures cross-backbone propagation.",
    f=np.array([0.45, 0.15, 0.50, 0.25, 0.30, 0.10, 0.40, 0.15]),
    # All three clusters stressed: policy-statecraft (geo=0.10, reg=0.30),
    # flow-buffer (logistics=0.15, inventory=0.25), physical (env=0.15).
    # Only demand and financial relatively stable.
    category_index=1,           # high_value_contract
    expected_action="escalate_compliance",
    expected_action_index=3,
)
```

---

## 16. Required Experiments Before S2P Implementation

### 16.1 Completed Experiments (V-MV-KERNEL — S2P validated alongside SOC)

| Experiment | Cells | Result | Impact on S2P |
|---|---|---|---|
| V-MV-KERNEL (S2P uniform) | 108 | L2 = Diagonal (expected) | Uniform σ: no kernel difference |
| V-MV-KERNEL (S2P hetero) | 18 | **Diagonal +6.8pp (shared factorial) / +7.4pp (S2P-dedicated cells)** | **DiagonalKernel is S2P default** |
| V-S2P-HETERO (shrinkage) | 18 | Shrinkage -0.2pp vs diagonal | **Shrinkage adds nothing for S2P** |
| V-HC-CONFIG-SHRINKAGE | 3 | Off-diagonal -0.8pp on SOC | Explanation A confirmed across domains |

**Definitive result:** DiagonalKernel captures the full kernel advantage for S2P even with
dense correlation structure (5 pairs ρ>0.60, avg ρ≈0.43). ShrinkageKernel deprioritized.

### 16.2 Still Required Before S2P Ships

All experiments in this table run via SVM methodology (Colab Pro, LLM-judge personas).
No real deployment data required for any of these — see MAP v5.24 SYNTHETIC VALIDATION
METHODOLOGY section for the full SVM SOP.

> **Note (v0.7):** For oracle separation experiments (validating γ>1 for S2P), use
> `gae/synthetic.py` `OracleSeparationExperiment` with parametric S2P factor vectors
> (no LLM required). See gae_design_v10.6 §10.13 for the API. The S2P experiment
> is `S2P-ORACLE-SEP-1` — add to SVM SOP when running Phase D.1.

> **Note (v0.6):** V-CGA-FROZEN (SVM-003, previously listed here as QUEUED) is now
> COMPLETE. CLAIM-59 UNCONDITIONAL (54.4% faster, p<0.0001) + CLAIM-62 UNCONDITIONAL
> (+42.69pp). See §17.5 for closed status. Graph enrichment confirmed for S2P.

| Experiment | What It Tests | Priority | Platform |
|---|---|---|---|
| **S2P-EVAL-1** | Bootstrap calibration on d=8 centroids. Convergence criterion: drift <0.01. | **HIGH** — validates μ₀ | Colab Pro, LLM-judge |
| **S2P-V3B** | τ calibration on S2P scenarios (d=8). Grid search τ ∈ {0.05-0.40}. Is τ=0.1 optimal for procurement? | **HIGH** — gates τ decision | Colab Pro, LLM-judge |
| **S2P-GATE-R** | Routing accuracy on S2P categories. Same CLAIM-01 issue exists. | **HIGH** — gates accuracy claim | Colab Pro, LLM-judge |
| **S2P-PROD-4** | Per-category auto-approve thresholds. 50-seed validation. ≥20% coverage, ≥85% per-category. | **HIGH** — gates auto-approve | Colab Pro, LLM-judge |
| **S2P-DIAGONAL** | DiagonalKernel on 10-scenario demo. L2 vs Diagonal head-to-head on S2P evaluation scenarios (§15). | **MEDIUM** — Phase 3 Priority 2 demo comparison | Local, deterministic |
| V-MV-REGIME (S2P) | Regime A→B at decision 500. Tests CovarianceEstimator regime tracking. | **LOW** — Phase 4 research. Factorial personas already generated (18 cells). | Colab Pro |
| V-MV-INCOMPLETE (S2P) | Financial Risk factor omitted. Tests d=7 robustness. | **LOW** — Phase 4 factor extensibility. Factorial personas generated (36 cells). | Colab Pro |

### 16.3 Experiments NOT Required (resolved by V-MV-KERNEL)

| Previously Required | Why No Longer Needed |
|---|---|
| S2P kernel comparison (L2 vs weighted) | **Resolved.** V-S2P-HETERO: Diagonal +7.4pp. |
| S2P shrinkage investigation | **Resolved.** Off-diagonal adds -0.2pp. Deprioritized to Phase 4. |
| S2P correlation impact on scoring | **Resolved.** CLAIM-57: off-diagonal <1pp across all tests. |

---

## 17. Design Validation Checklist (Updated for v0.4)

### 17.1 GAE v0.7.20 Interface Validation (Phase 2 ✅ Phase 3 Priority 1 ✅ — 536 tests)

| Interface | S2P Requirement | Status |
|---|---|---|
| `ProfileScorer(mu, actions, calibration, kernel)` | (5,5,8) μ₀, 5 actions, S2P CalibrationProfile, DiagonalKernel | ✅ |
| `L2Kernel` + `DiagonalKernel` | Cold-start L2, default Diagonal | ✅ 527 tests |
| `KernelSelector` | Rolling 100-window, ratio>1.5 rule, 250 decisions | ✅ 4/4 correct |
| `CovarianceEstimator(d=8)` | Collects 8×8 Σ. Not scoring. Research asset. | ✅ |
| `ProfileScorer.score(f, category_index)` | f shape (8,), category_index 0–4 | ✅ Generic |
| `ProfileScorer.update(f, c, a, correct)` | Kernel-aware gradient. penalty_ratio=5.0 | ✅ |
| `CalibrationProfile(penalty_ratio=5.0)` | Lower asymmetry than SOC | ✅ |
| `CalibrationProfile.extensions["kernel"]="diagonal"` | DiagonalKernel default | ✅ |
| `CalibrationProfile.extensions["eta_override"]=0.01` | Asymmetric η (v0.4 NEW) | ✅ |
| `DiagonalKernel.raw_weights` | True 1/σ² for η_eff + enrichment ROI. Do NOT use `.weights` — silent scale cancellation. GAE v0.7.20 required. | ✅ |
| `centroid_distance_to_canonical(mu, canonical)` | Frobenius distance from current S2P μ tensor to canonical snapshot. Primary convergence metric — more reliable than N_half for S2P (supply chain disruptions can bias rolling window). `gae/convergence.py` | ✅ |
| `gamma_threshold(alpha_cat, delta_norm, theta)` | Computes ε_firm★ ≈ 0.125 for S2P production parameters (α_cat≈0.40, ‖Δ‖≈0.25, θ=0.85). S2P gamma condition: ε_firm > 0.125. `gae/convergence.py` | ✅ |
| `OracleSeparationExperiment` (S2P) | Phase 1/2 oracle separation for S2P procurement scenarios. Validates γ>1 for supply chain disruptions without LLM competence prior. `gae/synthetic.py` (parametric only, no LLM) | ✅ — pending S2P-ORACLE-SEP-1 run |
| τ=0.1 default | Must NOT hardcode other τ until S2P-V3B | ⚠️ S2P-V3B required |
| `τ_modifier` absent | Permanently rejected (OP series) | ✅ Never add |
| `LearningState.bootstrap_calibrate(n_decisions=800)` | S2P bootstrap on d=8 | ✅ |
| `ProfileScorer.checkpoint()` + rollback | TD-033 applies identically | ✅ |

### 17.2 Evaluation Framework Validation

| Interface | S2P Requirement | Status |
|---|---|---|
| `EvaluationScenario.f` | shape (8,) — was (6,) in v0.3 | ✅ Generic np.ndarray |
| `EvaluationScenario.category_index` | int 0–4 | ✅ |
| `EvaluationReport.per_category_accuracy` | 5 S2P categories | ✅ Fixed in v5.0 |
| `run_evaluation()`, `run_ablation()`, `compute_judgment()` | Same functions, d=8 inputs | ✅ |

### 17.3 Platform Validation (ci-platform)

> **Block 8.5 (April 8, 2026):** AGE/PostgreSQL migration moves ci-platform from
> Neo4j Aura to PostgreSQL+AGE (pre-VPS). S2P graph entities (Supplier, PurchaseOrder,
> ContractEvent, TRIGGERED_EVOLUTION S2P edges) move automatically. S2P-specific Cypher
> queries need AGE dialect verification before S2P ships. See §17.6 for full spec.
> ci-platform tests: 102 → 107 (Block 8.5 will add ≥6 AGE-specific tests).

| Interface | S2P Requirement | Status |
|---|---|---|
| `DomainConfig ABC` | S2PDomainConfig extends, d=8 factors | ✅ |
| `SourceConnector` protocol | OFAC, D&B, Logistics, Weather connectors | ✅ |
| `GraphIngester` | MERGE on S2P entities (Supplier, DomainRiskScore) | ✅ |
| `ConservationMonitor` | α·q·V ≥ θ_min. Var(q) logged. AMBER auto-pause. | ✅ |
| P28 pipeline | 6 phases. KernelSelector. 250-decision shadow. Kernel-dependent thresholds. | ✅ INT-TEST-1 passing |
| `CopilotFramework` (v0.5 NEW) | S2P built ON the framework — not forked from SOC. ~3,000 lines of shared pipeline (P28, shadow, evidence ledger, IKS, conservation, dispatch, UI) extracted into ci-platform before S2P build starts. S2PDomainConfig registered via `CopilotFramework.register()`. | 🔲 Extract at S2P build start |

### 17.4 New Services (v0.4 + v0.5 additions)

| Service | S2P Requirement | Status |
|---|---|---|
| `KernelSelector` | Selects DiagonalKernel for S2P (ratio≈1.8× > 1.5 threshold) | ✅ |
| `CovarianceEstimator` | Collects 8×8 Σ. Half-life 300. Regime tracking. | ✅ |
| `IKSService(domain_config)` | μ₀ from get_profile_centroids() shape (5,5,8) | ✅ Domain-agnostic |
| `ShadowModeService` | 250-decision target. Multi-kernel shadow. | ✅ |
| `NLTemplateEngine` | d=8 factor names + kernel weights in templates | ⚠️ Templates need authoring |
| `ResidualTracker` | Log confident-but-wrong decisions. d=8 factor vectors. | ✅ (~30 lines, log only) |
| `OLSMonitor` (v0.5 NEW) | CUSUM on OLS, h=5.0, plateau-snapshot baseline. Flywheel Health Monitor for S2P — domain-agnostic. CLAIM-OLS-01: 0% miss rate, p90≥50d lead time. Ships in GAE v0.7.11. | ✅ Domain-agnostic — free reuse |

### 17.5 Issues Summary (v0.6)

| Issue | Status | Action |
|---|---|---|
| τ=0.1 vs S2P-optimal τ | **OPEN ⚠️** | S2P-V3B required. Deploy with τ=0.1 + WARNING. |
| penalty_ratio=5.0 not empirically derived | **DESIGN ESTIMATE ⚠️** | Procurement cost-benefit analysis needed. Ship with 5.0; flag. |
| NL template content (d=8 domain language) | **REQUIRES WORK ⚠️** | Architecture ready; 8-domain template strings need authoring. |
| ~~EvaluationReport.by_technique~~ | **CLOSED ✅** | Fixed in GAE v5.0 |
| ~~Kernel selection for S2P~~ | **CLOSED ✅ (v0.4)** | V-S2P-HETERO: Diagonal +7.4pp. Shrinkage -0.2pp. |
| ~~Correlation impact on scoring~~ | **CLOSED ✅ (v0.4)** | CLAIM-57: off-diagonal <1pp. |
| ~~d=6 vs d=8 factor architecture~~ | **CLOSED ✅ (v0.4)** | d=8 domain-level scores adopted. design_note_v3 §6.2. |
| ~~Cross-graph discovery quality~~ | **CLOSED ✅ (March 26 + April 6, 2026)** | CLAIM-59 UNCONDITIONAL (54.4% faster, p<0.0001, 26/30 seeds). CLAIM-62 UNCONDITIONAL (+42.69pp Day-1 lift). Graph enrichment confirmed for S2P. Third compounding pathway validated. |

---

### 17.6 Re-Convergence Theorem — S2P Applicability [NEW v0.7]

**CC-21 (Tier 2) applies to S2P without modification.** The theorem is domain-agnostic:

**Theorem:** γ = N_half,1 / N_half,2 > 1 ⇔ ε_firm > α_cat · ‖Δ‖ / (1 − α_cat) ≈ 0.125

**S2P-specific parameters:**

| Parameter | S2P Value | SOC Value | Notes |
|---|---|---|---|
| α_cat (fraction disrupted) | 0.40–0.60 | ≈0.33 | Supply chain disruptions typically affect 2–3 of 5 categories (e.g., compliance_sensitive + sole_source during a geopolitical event) |
| ‖Δ‖ (disruption magnitude) | 0.20–0.35 | ≈0.25 | Supplier bankruptcy, OFAC sanctions shift factor profiles substantially |
| ε_firm (firm-specific deviation) | 0.20–0.45 | 0.15–0.40 | Procurement environments vary widely by industry (manufacturing vs. pharma vs. defense) |
| ε_firm★ (threshold) | ≈0.125 | ≈0.125 | Same formula; same computed threshold |

**S2P disruption archetypes and γ applicability:**

| Archetype | Categories disrupted | Threshold check | γ > 1? |
|---|---|---|---|
| Geopolitical shock (Russia-Ukraine style) | geopolitical_sensitive + sole_source + compliance_sensitive (3/5 = α=0.60) | ε_firm★ = 0.60·0.30/(1−0.60) = 0.45 | Only if ε_firm > 0.45 — conditional |
| Single-supplier bankruptcy | sole_source + high_value_contract (2/5 = α=0.40) | ε_firm★ = 0.40·0.25/(1−0.40) = 0.167 | Yes for most procurement environments |
| Regulatory change (EU AI Act scope) | compliance_sensitive only (1/5 = α=0.20) | ε_firm★ = 0.20·0.20/(1−0.20) = 0.05 | Yes unconditionally |

**Key insight for S2P:** The geopolitical shock archetype (3/5 categories disrupted,
α=0.60) produces a higher threshold (0.45). Not all procurement environments have
ε_firm > 0.45. S2P's CC-21 claim must be stated with archetype:

> "After supply chain disruption affecting 1–2 procurement categories, re-convergence is
> faster than initial calibration — proven analytically. For large-scale geopolitical
> disruptions affecting 3+ categories, the condition depends on firm-specific deviation."

**S2P EXP-G1 equivalent:** Log `centroid_distance_to_canonical` per verified procurement
decision via BACKLOG-015 equivalent (S2P triage path). Measure γ as convergence rate ratio
across a simulated disruption event. S2P-ORACLE-SEP-1 (see §16.2) validates this parametrically.

**Implementation:** `gae/convergence.py` `gamma_threshold(alpha_cat=0.40, delta_norm=0.25)`
returns 0.167 for single-supplier archetype. `phase2_effective_threshold(0.40)` returns
p_d★ = (0.85 − 0.60) / 0.40 = 0.625 (S2P needs higher disrupted-category accuracy
than SOC because fewer undisrupted categories carry the rolling window).

---

## 18. Version Placement & Build Path (updated v0.4)

### 18.1 When S2P Ships

**Phase 3 Priority 2: CopilotFramework extraction + 10-scenario demo** (previously labeled v6.5)

Step 1 — CopilotFramework extraction (before any S2P-specific code):
- Extract ~3,000 lines of shared infrastructure from SOC into ci-platform CopilotFramework
- Re-wire SOC onto the framework. All 294+ tests must continue passing.
- SOC shrinks to ~800 lines. This validates the abstraction with a single domain.
- Estimated effort: ~2 weeks refactoring.

Step 2 — Build S2P on the framework (~1,200 lines of S2P-specific code):
- S2PDomainConfig (d=8) ✅ DESIGNED (this document)
- DiagonalKernel validated (+6.8pp) ✅ COMPLETE
- 10 evaluation scenarios (§15) ✅ DESIGNED (6 scenarios, 4 more needed)
- S2P-DIAGONAL: "same kernel, different domain, +6.8pp from kernel alone"
- Estimated effort: ~2 weeks S2P-specific code.

At S2P launch: Open-source ci-platform (CopilotFramework, W2FactorComputerBase, MCP schemas).
See gae_opensource_strategy_v5 §Part 14 for the full sequencing.

**Phase 4: Full S2P copilot** (previously labeled v7.0)
- All connectors (D&B, OFAC, Logistics, Weather, ERP)
- Full P28 pipeline with 250-decision shadow and KernelSelector
- S2P-EVAL-1, S2P-V3B, S2P-GATE-R, S2P-PROD-4 all passed (via SVM, Colab Pro)
- NL templates authored (L1/L2/L3)
- Cross-domain queries: "Which sole-source suppliers have active SOC alerts?"

### 18.2 What S2P Needs That SOC Has Already Built

| Component | Built for SOC | S2P Re-Use |
|---|---|---|
| **CopilotFramework** (v0.5 NEW) | 🔲 Extracted from SOC at S2P build start | Entire shared pipeline (P28, shadow, evidence, IKS, conservation, dispatch, UI) free via `CopilotFramework.register()`. S2P builds at ~1,200 lines total. |
| ProfileScorer + DiagonalKernel + KernelSelector | ✅ GAE v0.7.20 (527 tests) | Import unchanged. d=8 accepted. INT-TEST-2 (W2 read path) passing. |
| CovarianceEstimator | ✅ GAE v0.7.20 | New instance with d=8. |
| CalibrationProfile | ✅ v5.0 | New instance with S2P values + kernel="diagonal" |
| Data preservation hooks (3) | ✅ v5.0 | Identical write path. factor_vector d=8. |
| IKSService | ✅ v5.5 | New instance with S2P μ₀ (5,5,8) |
| ShadowModeService | ✅ v5.5 | New config (250 target, multi-kernel) |
| NLTemplateEngine (architecture) | ✅ v5.5 | New templates for d=8 + kernel weights |
| ConservationMonitor + AMBER auto-pause | ✅ GAE v0.7.20 | Identical. Var(q) logged. |
| OLSMonitor (Flywheel Health Monitor) | ✅ GAE v0.7.11. CLAIM-OLS-01 validated. | Identical. CUSUM on OLS, h=5.0, plateau-snapshot. S2P gets 0% miss rate flywheel monitoring for free. |
| P28 pipeline (6 phases, KernelSelector) | ✅ ci-platform v1.0 (102 tests). INT-TEST-1 passing. | Same pipeline, S2P kernel config |
| Residual tracker | ✅ GAE v0.7.20 | Identical (~30 lines). d=8 factor vectors. |
| Docker Compose deployment | ✅ v5.5 | Second service in docker-compose.yml |

**What S2P must build:** S2PDomainConfig (§8) + 8 DomainRiskScore factor computers (§6) +
centroid tensor (§7) + NL template strings (d=8 + kernel) + concepts.yaml + queries.yaml +
6 connector implementations (OFAC, D&B, Commodity, GeoRisk, Logistics, Weather) + seed data.

Note: The CopilotFramework extraction means S2P does NOT need to build any pipeline
infrastructure — it registers a DomainConfig and gets the full pipeline for free.

### 18.3 S2P Demo Narrative (updated for kernel)

"Same learning engine. Same kernel. Different domain. +6.8pp from kernel alone."

Demo flow:
1. Show SOC copilot with IKS = 76.8 (DiagonalKernel active, 527 tests, BACKLOG-020 fixed).
2. Switch to S2P copilot in same session.
3. S2P IKS = 0.0 at demo start.
4. Run 100 synthetic procurement decisions with DiagonalKernel.
5. S2P IKS = 8.4 (moving from zero).
6. Show kernel weights: "supplier_risk: weight 0.85 (reliable). environmental_risk:
   weight 0.15 (noisy — sparse data). The kernel learned your data quality profile."
7. "The math is the same. The kernel is the same. The graph is different.
   The moat is firm-specific in both cases — centroids AND kernel weights."

---

### 18.4 Phase D — S2P Demo Readiness [NEW v0.6]

Phase D is the path from "S2P design complete" to "first CISO demo includes S2P."
Three sequential steps, all deferred until Loom demo v1 (SOC-only) is recorded.

**Phase D.1 — S2P Worked Example (Block 3.8, ~3 days)**
Produce a worked example demonstrating the S2P compounding story end-to-end using
synthetic procurement decisions. Covers: cold-start at 90.6%, DiagonalKernel noise
fingerprint for d=8 risk scores, convergence curve, IKS progression, and a
cross-domain query example. This is the content foundation for Phase D.2 tab tests.
Status: ⏳ DEFERRED — after Loom demo v1 recorded.

**Phase D.2 — S2P Tab Content Tests (~40-50 tests)**
Validate all five S2P tabs with the same LLM-judge rubric used for SOC (Tier 1 + Tier 2).
Requires Phase D.1 worked example as the reference answer for factual accuracy checks.
Mirrors the SOC tab content test pattern (54 tests completed April 6, 2026).
Status: ⏳ DEFERRED — after Phase D.1 complete.

**Phase D.3 — V-NARRATIVE-S2P Gate**
Run V-NARRATIVE-S2P: GPT-5.4 judges S2P narrative across all five tabs. Gate:
5/5 PASS (same gate as V-NARRATIVE-CISO v13 GATE PASS, April 1, 2026).
Required before any CISO demo that includes S2P in the demo flow.
Status: ⏳ DEFERRED — after Phase D.2 complete.

**Block 7.5 — Cross-Copilot ACCP Routing (circular dependency flagged)**
Cross-domain queries ("which sole-source suppliers have active SOC alerts?") require
both SOC and S2P live simultaneously. Block 7.5 cannot be triggered in demo mode.
CC-14 (cross-domain conservation law demo) is blocked by Block 7.5.
Resolves only after S2P is live in production alongside SOC.

**Phase D gate:** Loom demo v1 recorded → Phase D.1 → D.2 → D.3 → S2P CISO demo ready.
**Phase D authority:** MAP v5.24.

---

## 19. Co-Design Constraints (Updated v0.4)

| S2P Decision | SOC Constraint | Status |
|---|---|---|
| `d=8` domain factors | SOC: `d=6` | ProfileScorer accepts any d ✅ |
| `actions = 5` | SOC: same 5 | get_actions() returns any list ✅ |
| `C=5` categories | SOC: C=5 | ProfileScorer constructor accepts any C ✅ |
| `kernel="diagonal"` | SOC: `kernel="diagonal"` (v6.0) | Same default. KernelSelector same. ✅ |
| `penalty_ratio=5.0` | SOC: `penalty_ratio=20.0` | Configurable field ✅ |
| `temperature=0.1` (pending V3B) | SOC: `temperature=0.1` (V3B validated) | ⚠️ S2P-V3B needed |
| `eta_override=0.01` | SOC: same | Asymmetric η validated ✅ |
| `decay_classes: {permanent, standard, campaign}` | SOC: same | Dict accepts any string key ✅ |
| KernelSelector (ratio>1.5, 250 decisions) | SOC: same | Domain-agnostic ✅ |
| CovarianceEstimator (d=8, collects only) | SOC: d=6, collects only | Accepts any d ✅ |
| Shadow mode 250-decision target | SOC: 250-decision target | Aligned at v0.4 ✅ |
| P28 pipeline (6 phases) | SOC: same 6 phases | Domain-agnostic pipeline ✅ |
| AMBER auto-pause | SOC: same | Domain-agnostic ✅ |
| Var(q) per-analyst observation | SOC: same | Domain-agnostic ✅ |
| Residual tracking (log only) | SOC: same | Domain-agnostic ✅ |
| 8×8 Σ matrix collection | SOC: 6×6 Σ collection | CovarianceEstimator accepts any d ✅ |
| Hook 1: kernel_type + kernel_weights | SOC: same fields | Adjustment G metadata ✅ |
| NL template strings (CPO/analyst/auditor) | SOC: CISO/analyst/auditor | Architecture identical; content different ⚠️ |
| Correlation prior (§8.1) | SOC: (not implemented) | S2P-specific. Research data, not scoring. ✅ |

---

## 20. Summary of Design Impact (v0.4)

| Finding | Impact | Action | When |
|---|---|---|---|
| d=6 → d=8 | **Architecture change** — all factor references, centroids, evaluation scenarios reshaped | Reflected throughout v0.4 | Done |
| DiagonalKernel validated on S2P | **+6.8pp.** kernel="diagonal" default | CalibrationProfile + KernelSelector updated | Done |
| Shrinkage adds nothing for S2P | **Off-diagonal <1pp** despite dense correlations | ShrinkageKernel deprioritized to Phase 4 | Done |
| 8×8 Σ matrix (two-judge) | **Domain understanding** — NOT scoring | get_correlation_prior() added. Informs residual analysis. | Done |
| V-MV-KERNEL S2P validation | **Platform claim strengthened** | "Same kernel, different domain, +6.8pp" | Done |
| τ=0.1 vs S2P-optimal | **Open ⚠️** | S2P-V3B must run (Colab Pro, LLM-judge) | Before Phase 4 |
| penalty_ratio=5.0 estimate | **Open ⚠️** | Cost-benefit analysis | Before Phase 4 |
| NL template content (d=8) | **Requires authoring ⚠️** | 8-domain template strings | During implementation |
| ~~V-CGA-FROZEN~~ | **CLOSED ✅** — CLAIM-59 UNCONDITIONAL (54.4% faster, p<0.0001) + CLAIM-62 UNCONDITIONAL (+42.69pp) | Graph enrichment confirmed. Third compounding pathway. S2P enrichment story strengthened. | Done (March 26 + April 6, 2026) |
| All GAE v0.7.20 interfaces | **Clean for d=8** ✅ | 527 tests. Phase 2 ✅ Phase 3 Priority 1 ✅. DiagonalKernel + raw_weights. KernelSelector. OLSMonitor. Block 9.1-9.5. | Done |
| All platform interfaces | **Domain-agnostic** ✅ | P28 (INT-TEST-1 ✅), ConservationMonitor, hooks, IKS, shadow. ci-platform 102 tests. | Done |
| **CopilotFramework extraction** (v0.5 NEW) | **Architecture decision** — S2P built ON framework, not forked | Extract from SOC into ci-platform as first step of S2P build. SOC shrinks to ~800 lines. S2P builds at ~1,200 lines. | First step of Phase 3 Priority 2 |
| **Phase D — S2P Demo Readiness** (v0.6 NEW) | **Sequencing** — three steps to first S2P CISO demo | D.1 worked example → D.2 tab content tests → D.3 V-NARRATIVE-S2P gate. Block 7.5 circular dependency flagged. CC-14 blocked by Block 7.5. | After Loom demo v1 |

**Bottom line (v0.6):** Three open items from v0.3 remain (τ calibration, penalty_ratio
derivation, NL template strings). V-CGA-FROZEN is CLOSED — CLAIM-59 (third compounding pathway, 54.4% faster) and
CLAIM-62 (+42.69pp) both UNCONDITIONAL. CopilotFramework
extraction is the first step of the S2P build — S2P registers a DomainConfig and gets the
entire pipeline infrastructure for free. Phase D (S2P demo readiness) is the path
to first CISO demo with S2P. All remaining open items are domain-knowledge gaps
or sequencing decisions, not architecture gaps.

The architecture validates more cleanly than v0.3 because:
1. **DiagonalKernel is experimentally confirmed** on S2P (+6.8pp, 18-cell factorial). CLAIM-59 (54.4% faster) and CLAIM-62 (+42.69pp) also confirmed.
2. **d=8 aligns with industry frameworks** (Gartner, McKinsey risk cockpit structure).
3. **Correlation research provides domain model** (two-judge, 28 pairs, 3 regimes)
   even though it doesn't affect scoring (Explanation A: noise ratio only).
4. **KernelSelector, CovarianceEstimator, P28 pipeline, conservation extensions** —
   all built for SOC, all work for S2P without modification.

> **"Same engine, same kernel, different domain, different data sources, different judgment.
> +6.8pp from kernel alone. The moat is firm-specific in both cases — centroids AND
> kernel weights encode THIS firm's procurement reality."**

---

*S2P Copilot — Design Document v0.6 · April 6, 2026*
*Build-ready — Phase 3 Priority 2. CopilotFramework extraction is the first build step.*
*v0.6: V-CGA-FROZEN CLOSED (CLAIM-59+62). Phase D added. GAE v0.7.20. 527 tests.*
*GAE v0.7.20: 536 GAE + 558 SOC backend + 107 ci-platform + 58 S2P = ~1,389 total. Phase 2 ✅ Phase 3 Priority 1 ✅. Loom demo v1 unblocked.*
*DiagonalKernel +6.8pp (V-S2P-HETERO). Shrinkage -0.2pp. Noise ratio is the whole story.*
*Two-judge correlation research: 28 pairs, 3 regimes, 8×8 Σ matrix.*
*Demo: Phase 3 Priority 2 (10 scenarios + DiagonalKernel comparison). Full: Phase 4.*
*Three open items: τ (S2P-V3B), penalty_ratio derivation, NL template strings.*
*V-CGA-FROZEN CLOSED: CLAIM-59 (54.4% faster, p<0.0001) + CLAIM-62 (+42.69pp). CL-ECON-S2P: 31 min/PO.*
*~175 experiments. claims_registry_v10.2. SOC A=4 / S2P A=5 (intentional asymmetry).*
*CC-21 Tier 2: γ > 1 proven (ε_firm > 0.125). S2P archetype-conditional. See §17.6.*
*Block 8.5 (AGE migration) pre-VPS: S2P graph entities move to PostgreSQL+AGE. See §17.6.*
*"The math is the same. The kernel is the same. The graph is different."*
*"The framework is shared. The domain expertise is the moat. The graph compounds while centroids wait."*


---

# PART II — PRODUCT DEFINITION (v1.3)

*16 scenarios, competitive positioning, feature specifications,
value model, engineering specs (M1-M9). This section uses §PD
prefix to avoid collision with Part I section numbers.*

*Note: §PD references below correspond to the original §1-§12
in s2p_product_definition_v1_3.md.*

---

## §PD1 — The Problem Nobody Has Solved

Every procurement AI tool on the market today shares one structural
limitation: **decision 10,000 is processed exactly like decision 1.**

Zycus Merlin auto-processes invoices — same logic on Day 365 as Day 1.
Celonis finds bottlenecks — same method in December as January. McKinsey
finds $7M in savings — then they leave and the savings evaporate.

The root cause: existing tools process transactions. They don't learn
from outcomes. They don't reason about context. They don't tune
themselves. They don't value caution over speed.

**What we build: procurement that learns from every verified decision,
reasons from cross-system context, tunes its own operations, and gets
measurably better every quarter.**

---

## §PD2 — 16 Scenarios of Change

Each scenario is a specific, recognizable problem a CSCO, CPO, or CFO
faces today. The "AFTER" is uniquely enabled by our architecture.

### Cluster A: Invoice & AP Learning (Ship First)

**S1: "The Exception Rate That Never Drops"**
BEFORE: Exception rate: 20% for 3 years. System doesn't learn from
resolutions. AFTER: Month 1: 18%. Month 6: 11%. Month 12: 7%. The
system learned which supplier-format-commodity patterns produce
exceptions and routes them differently BEFORE they become exceptions.

**S2: "The Autopilot Nobody Trusts to Expand"**
BEFORE: Auto-approve stuck at 20%. Nobody can prove 50% is safe.
AFTER: Week 6: system proves 35% is safe (4,200 verified decisions,
accuracy above threshold). Month 4: 50%. Month 8: 65%. If quality
dips, system pauses ITSELF.

**S9: "The Automation That Broke Silently"**
BEFORE: Accuracy dropped from 95% to 82% over 3 weeks. Nobody noticed.
$340K in incorrect payments. AFTER: Day 1 of drop: novelty detection
fires. Day 2: conservation → AMBER. Auto-approvals pause. 12 invoices
held. Exposure: $8K instead of $340K.

**S13: "The System That Tunes Itself While You Sleep" [NEW v1.1]**
BEFORE: System configured by consultant 18 months ago. Configuration
stale. $50K/quarter to re-tune. AP team discovered that presenting
contract references before price deltas resolves electronics exceptions
3× faster — but no way to feed this back. AFTER: Month 6: 47
configuration evolutions — evidence ordering, routing thresholds,
escalation criteria — each tested against conservation law before
promotion. Resolution speed improved 12%. Consultant re-tuning: gone.

**S14: "Not a Script — A Decision" [NEW v1.1]**
BEFORE: AP automation follows rules. "If price > PO by 3%, flag."
When a legitimate reason exists (commodity pass-through, FX, volume
tier), the rule fires anyway. False-positive exception rate: 35%.
During 2025 tariff shock, 40% of invoices hit novel situations rules
didn't cover. AFTER: Situation Analyzer reasons from context graph:
"5.2% variance. Copper rose 4.8%. Contract §7.3 allows pass-through
up to 110% of index. Within bounds. Accept." False-positive rate: 8%.
During 2026 tariff shock: 92% handled without human review (vs 40%).

**S15: "The System That Values Caution" [NEW v1.1]**
BEFORE: AP automation optimizes for speed. Borderline cases get auto-
approved to meet throughput targets. 200 borderline approvals × $5K
= $1M in leakage over 12 months. AFTER: 5:1 penalty asymmetry in
reward signal. System is structurally conservative — never auto-
approves borderline to improve speed. Auto-approve at 55%, zero
borderline leaks. Auditors trust the expansion because the system is
DESIGNED to value caution.

### Cluster B: Supplier Behavioral Learning (Emerges from A)

**S6: "The Expertise That Walks Out the Door"**
BEFORE: Best category manager retires. Replacement makes $2M in
avoidable mistakes over 6 months. AFTER: 15,000 verified decisions
compiled. "Chen-Lin: Q3 delivery drops to 72%. Houston emergency POs:
94% legitimate. Denver: 38% — escalate."

**S7: "47 Suppliers Doing the Same Job"**
BEFORE: 47 MRO suppliers. Consultant finds 12 obvious duplicates.
AFTER: System identifies 31 behavioral duplicates from 10,000 POs.
Consolidate to 16. Save $2.4M/year.

**S8: "The ERP Lead Time That's Always Wrong in November"**
BEFORE: ERP says 14 days. Q4 reality: 21 days. Stock out every
November. AFTER: "14.2 days Q1-Q3. 21.4 days Q4. 28+ when volume
exceeds 500 units in Q4." Cross-graph adds: "Copper > $4.50 predicts
Q4 delays 6 weeks early."

**S11: "The Supplier That Was Fine Until It Wasn't"**
BEFORE: Supplier X: A-rated, OTIF 96%. Then misses critical delivery.
Post-mortem: three declining signals in three systems, each below
alarm individually. AFTER: Three months early: "OTIF trending down +
exception rate doubled + financial health declined. Cross-system
pattern: financial stress → delivery failure. Qualify backup NOW."

### Cluster C: Cross-System Discovery (Month 4+)

**S5: "The Pattern Nobody Queried"**
BEFORE: Four dashboards. Nobody connects Celonis bottleneck + D&B
financial decline + commodity spike + exception concentration.
AFTER: "Supplier X financial stress + commodity trajectory + Chicago
exception concentration = price increase risk in 6 weeks."

**S10: "The Consultant's Findings That Evaporate"**
BEFORE: McKinsey finds $7M. Leaves. Savings drift. Returns, finds
$6M — same issues re-emerged. AFTER: Findings emerge continuously.
Persist in centroids. No consultant needed.

**S16: "Where Celonis Stops, We Start" [NEW v1.1]**
BEFORE: Celonis shows Chicago AP is 3× slower than Houston. 4-week
investigation to find WHY. AFTER: Cross-graph attention: "Chicago is
slow because Suppliers X/Y/Z use non-standard formats. Supplier X
changed format 6 months ago. Supplier Y's exception rate spiked from
40% PO volume increase." System routes to specialized queue. Resolution
drops from 12 days to 2 days. AgentEvolver promotes the routing
variant. Next similar bottleneck at ANY plant: handled automatically.

### Cluster D: Capital Optimization (Month 6-12)

**S12: "The Working Capital Trap"**
BEFORE: Blanket Net-45. Miss $800K in discounts. Strain key supplier.
AFTER: "Supplier W: always takes early pay ($340K/year value). Supplier
Y: deprioritizes when payment > 50 days. Supplier Z: no correlation."
Per-supplier strategy replaces blanket policy.

### Cluster E: Disruption Recovery (Cross-Cutting)

**S3: "The Same Tariff Shock, The Same 3-Month Recovery"**
BEFORE: Same shock, same 3-month recovery, same $15M — twice.
AFTER: Second shock: 2 weeks, $2M. Third: 3 days, $500K. Each
recovery faster because system accumulated disruption-response pattern.

**S4: "The Data Cleanup Project That Never Ends"**
BEFORE: "First, 6-12 months of data cleanup. $1.5M." Done in 2023.
Stale by 2024. Told to do it again. AFTER: Deploy Day 1. System
learns which sources to trust. "Environmental_risk: 3% signal.
Tariff_exposure: 22%. Trust that one."

---

## §PD3 — Technology Value → Business Value

| Innovation | Technology | CSCO Sees | Scenarios |
|-----------|-----------|-----------|-----------|
| Centroid learning | Verified decisions move learned vectors | Exception rate drops, doesn't plateau | 1, 6, 7, 8 |
| Conservation law | Mathematical quality invariant | "Proof that 50% auto-approve is safe" | 2, 9, 15 |
| DiagonalKernel | Learns which data dimensions to trust | Deploy Day 1 on messy data | 4 |
| Cross-graph attention | Discovers patterns across data sources | "Connection nobody queried across 4 systems" | 5, 10, 11, 16 |
| Re-Convergence (γ>1) | Recovery faster after each disruption | Third tariff shock: 3 days, not 3 months | 3 |
| Novelty detection | Detects shifts before accuracy drops | Auto-pause fires before $340K leaks | 9 |
| Two-phase learning | Phase 1: patterns. Phase 2: which dimensions matter | New hire inherits 15,000 decisions | 6, 8 |
| Asymmetric η | Protects knowledge from noisy decisions | System guards itself during crisis | 3 |
| Promotion gate | No update deploys without quality proof | Working capital uses TESTED parameters | 12 |
| **Situation Analyzer** | Reasons from graph context, not rules | False-positive exception rate 35% → 8% | **14** |
| **AgentEvolver** | Runtime evolution of operational config | 47 self-improvements, no consultant | **13, 16** |
| **RL reward asymmetry** | 5:1 penalty makes system conservative | Zero borderline leaks at 55% auto-approve | **15** |
| **Process-tech fusion** | WHERE→WHY→WHAT→LEARN loop | Celonis bottleneck explained AND fixed AND remembered | **16** |
| ACCP three-loop | One control plane governs all copilots | One system, 16 scenarios, cross-copilot learning | All |

---

## §PD4 — Differentiation & Positioning

### The Competitive Test

| Question | Zycus | Celonis | Coupa | Us |
|----------|-------|---------|-------|-----|
| After 10,000 decisions, show me the compounding curve | Can't | Can't | Can't | Here it is |
| Prove that 50% auto-approve is safe | Promise | N/A | N/A | Theorem + audit trail |
| Why is Chicago AP slow — not THAT it's slow, but WHY | No | WHERE but not WHY | No | WHY + fix + learn + transfer to other plants |
| Does your system REASON about why a variance exists? | Rules | N/A | Rules | Context-graph reasoning (S14) |
| Does your system tune its own configuration? | No | No | No | 47 evolutions in 6 months (S13) |
| After the third tariff shock, how fast? | Same speed | N/A | N/A | Faster each time (γ > 1) |
| When my category manager leaves, what survives? | Nothing | Nothing | Rules | 15,000 verified decisions in centroids |
| Why should I trust your auto-approve won't leak? | We're careful | N/A | Rules | 5:1 penalty: system DESIGNED to be cautious |

### Positioning by Buyer

| Buyer | What They Hear |
|-------|---------------|
| CFO | Exception rate 15%→7%. Auto-approve 20%→65% with proof. $340K leakage prevented by auto-pause. Zero borderline leaks. |
| CPO | When Maria left, exception rate didn't spike. System finds $1M+ patterns quarterly without consultants. |
| VP Procurement Ops | System resolved 92% of tariff-variant invoices automatically. Tunes itself — no $50K quarterly consultant. |
| CSCO | Third tariff shock: 3 days. Supplier X failure predicted 3 months early. Celonis bottleneck explained, fixed, and transferred. |
| CIO / CDO | Deploys on dirty data. Learns which sources to trust. No 12-month data cleanup prerequisite. |

### Celonis Positioning
Celonis = the mirror (shows WHERE). We = the brain + hands + memory
(explains WHY, fixes WHAT, LEARNS from outcome, TRANSFERS fix to other
plants). Scenario 16 demonstrates the full loop.

---

## §PD5 — Unlocks (Revised)

| # | Unlock | Scenarios | KPI | Y1 Value |
|---|--------|-----------|-----|----------|
| 1 | Exception rate drops every quarter | 1, 14 | Exception % (declining) | ~$4-6M |
| 2 | Auto-approve expands with proof | 2, 9, 15 | Auto-approve % (20%→65%) | ~$8-10M |
| 3 | Deploy on dirty data, Day 1 | 4 | Time to deploy (12mo → 30d) | ~$3-5M |
| 4 | Cross-system patterns nobody queried | 5, 10, 11, 16 | Discoveries/quarter | ~$6-12M |
| 5 | Third disruption: days, not months | 3 | Recovery time (declining) | ~$8-20M |
| 6 | Knowledge survives turnover | 6, 8 | IKS score, ramp time | ~$4-5M |
| 7 | 47 suppliers → 16 | 7 | Supplier count, txn cost | ~$3-5M |
| 8 | Payment timing from verified behavior | 12 | DPO, discounts, OTIF | ~$3-5M |
| **9** | **System tunes itself — no consultant** | **13, 16** | **Config evolutions, resolution speed** | **~$2-3M** |
| | **PORTFOLIO** | | | **$41-71M** |

---

## §PD6 — Architecture & Feature Sets

### 6.1 Three-Layer Product Architecture

**Layer 1 — Operational Decision Learning** (100-1,000+ decisions/day)
Processes transactions. Learns from every resolution. Reasons from
context. Tunes its own operations. Verification: hours to days.

**Layer 2 — Supplier & Spend Intelligence** (emerges from Layer 1)
Builds supplier profiles from accumulated operational data. Lead time
learning, behavioral clustering, trend correlation, early warning.
No separate implementation — emerges automatically.

**Layer 3 — Strategic Optimization** (Phase 2, Month 6+)
Uses learned parameters for strategic decisions. Payment timing,
supplier rationalization, disruption simulation, compliance.

### 6.2 Copilot Architecture

| Copilot | Layer | Priority | Scenarios |
|---------|-------|----------|-----------|
| Invoice Exception Copilot | 1 | **PILOT (v1.0)** | 1, 9, 13, 14, 15 |
| Price Leakage Guardian | 1 | **v1.1** | 5, 10, 16 |
| Requisition Copilot | 1 | v1.2 | 2 |
| Receipt & Quality Gate | 1 | v1.3 | 11 |
| Supplier Reliability Copilot | 2 | v1.2+ | 6, 7, 8, 11 |
| Working Capital Copilot | 3 | v2.0 | 12 |
| Sourcing Strategy Copilot | 3 | v2.0 | 3, 5, 10 |
| Compliance Sentinel | 2-3 | v2.0+ | Cross-cutting |
| **Control Tower** | Platform | **v1.0** | All |

### 6.3 Pilot Factor Space: Invoice Exception + Price Leakage

**Shared canonical (all copilots):** supplier_identity,
contract_linkage, spend_category, data_quality_score.

**Specialized (pilot):**
1. match_status — PO/GR/invoice match quality
2. amount_variance_ratio — invoice vs PO/contract delta
3. duplicate_score — duplicate invoice probability
4. supplier_exception_history — this supplier's prior exception rate
5. payment_terms_impact — discount/DPO/cash implication
6. commodity_index_correlation — commodity movement explaining variance
7. tax_regulatory_compliance — threshold, policy, audit exposure

**Actions (A=5):** auto_approve, hold_for_review, escalate_to_buyer,
flag_leakage, refer_to_specialist.

**Categories (C=5):** price_variance, quantity_mismatch, duplicate_risk,
contract_gap, format_compliance.

**Tensor:** 5×5×7 = 175 values per copilot.

### 6.4 Feature Specifications — Day 1 (v1.0)

**F1: Exception Triage Dashboard**
Queue of incoming invoice exceptions prioritized by financial impact ×
confidence × aging. Each item shows: supplier name, PO reference,
variance amount, category (price/quantity/duplicate/contract/format),
system recommendation with confidence score, and evidence summary.
Filters by category, supplier, amount range, aging. SLA timer per item.
Sort by priority score (default), amount, or age.
*Scenario: S1. Engineering: React dashboard consuming ProfileScorer API.*

**F2: Situation-Aware Evidence Panel**
For each exception, the Situation Analyzer traverses the context graph
and produces a REASONED evidence chain — not just factor scores but
the logical connection between them. Example: "5.2% price variance.
Copper rose 4.8% (Bloomberg feed, last 30 days). Contract §7.3 allows
commodity pass-through ≤110% of index movement. 5.2% is within 110%
of 4.8%. Recommendation: commodity-driven, accept. Confidence: 0.91."
The evidence chain includes: (a) the data sources consulted, (b) the
reasoning path, (c) the confidence score, (d) which factors drove
the score highest/lowest. Clickable links to source documents (PO,
contract clause, commodity index, GR).
*Scenario: S14. Engineering: SituationAnalyzer graph traversal +
NL template rendering. Requires 47-node traversal implementation
for S2P intent types.*

**F3: One-Click Verification Console**
In-line confirm/override. NOT a separate workflow — embedded in the
evidence panel. Confirm = one click (centroid pull toward this
decision). Override = select correct action + reason code from
dropdown (centroid push/pull with asymmetric η). Reason codes:
wrong_category, wrong_action, missing_context, system_correct_but_
override_policy, novel_situation. Each verification writes to the
evidence ledger as a DecisionEntry → OutcomeEntry pair.
Must be fast: target <15 seconds per decision for confirmations,
<45 seconds for overrides with reason. At 200 decisions/day, this is
~1 hour of analyst time (vs 15 min/exception manual = 50 hours).
*Scenario: All. Engineering: Extend SOC override UX with reason codes.
Wire to ProfileScorer.update() with S2P penalty ratio 5:1.*

**F4: Conservation Dashboard**
Real-time conservation status per copilot: GREEN (learning active,
auto-approve expanding) / AMBER (quality dipping, learning paused,
auto-approvals held) / RED (quality below threshold, all decisions
require human review). Shows: α(t)·q(t)·V(t) vs θ_min as a live
chart. Per-category breakdown (which categories are GREEN/AMBER/RED).
One-click manual pause button. Expansion proof panel: "This category
can safely move from 35% to 50% auto-approve. Here is the evidence:
2,100 verified decisions in this category, accuracy 93.2%, no category
degraded. Rollback to 35% available."
*Scenario: S2, S9. Engineering: ConservationMonitor real-time feed +
React dashboard. P28-style qualification display for expansion proofs.*

**F5: Auto-Approve Engine**
Processes decisions that meet conservation-approved confidence
thresholds. Per-category thresholds (not global). Expansion governed
by conservation law: threshold can only lower (expand auto-approve)
when conservation proof passes. RL reward signal with 5:1 penalty
asymmetry ensures conservative scoring. Decisions that auto-approve
still write DecisionEntry to the ledger (no gap in audit trail).
Auto-approved decisions display in a separate "Auto-Resolved" tab
with spot-check sampling (2% random presented for human verification
to maintain q measurement).
*Scenario: S2, S15. Engineering: ProfileScorer confidence gate +
ConservationMonitor threshold management + RL reward integration.
Spot-check sampling from conservation q-window (400 decisions).*

**F6: Novelty Detection & Auto-Pause** *(ships v1.1, not Day 1)*
Monitors incoming decision patterns against learned distributions.
When novelty rate exceeds threshold (>20% of recent decisions are
patterns the system hasn't seen), triggers: (a) alert to AP director
with novelty summary, (b) conservation status review, (c) if
conservation product dips → automatic AMBER pause on affected
categories. Dashboard shows novelty rate trend per category.
Historical view: "Last novelty spike was March 2026 (tariff shock).
System paused electronics for 3 days. Recovered to GREEN after 47
verified decisions."
*Scenario: S9, S3. Engineering: NoveltyTracker from framework v4 +
per-category novelty rate computation + alert pipeline.*

**F7: Centroid Explorer**
Visual explanation of WHY the system scored this way. For a selected
decision: radar chart showing each factor's contribution to the score.
Centroid position overlay showing where THIS invoice sits relative to
the learned centroid for each action. "This invoice is closest to
'hold_for_review' because match_status is 0.73 (below centroid mean
of 0.89 for auto_approve) and supplier_exception_history is 0.91
(this supplier rarely has exceptions — but this one does)." Historical
centroid drift visualization: how this category's centroids have
moved over 30/90/180 days. Factor trust weights (DK): which factors
the system trusts most for this category.
*Scenario: S1, S2. Engineering: New visualization component. Reads
ProfileScorer centroid state + DK weights. React + D3/Recharts.*

**F8: Factor Proposer**
Periodic analysis (weekly or after N decisions) that evaluates each
factor's contribution to decision quality. Presents recommendations:
"Your environmental_risk factor contributes 3% of classification
signal for invoice exceptions. It is noise for your firm. Replacing
with tariff_exposure would improve accuracy by an estimated +4pp based
on 1,200 decisions." Accept/reject interface. Accepted replacements
go through P28 re-qualification (shadow mode validation before live).
*Scenario: S4. Engineering: Factor contribution analysis from DK
weights + proposed factor swap + P28 re-qualification pipeline.*

**F9: IKS Tracker (Institutional Knowledge Score)**
Board-visible metric: "IKS = 0 at deployment. IKS = 47 after 3 months.
IKS = 72 after 6 months." Computed from: number of verified decisions,
centroid convergence (distance from initial μ₀), number of DK weight
updates, number of AgentEvolver promotions. Trend chart. Per-category
breakdown. "Your fasteners category has IKS=89 (mature). Your new
electronics category has IKS=12 (still learning)."
*Scenario: S6. Engineering: IKSService already domain-agnostic in
ci-platform. Wire to S2P DomainConfig. Add trend visualization.*

**F10: Financial Impact Ledger** *(ships v1.1, not Day 1)*
Per-decision economic measurement. Each resolved exception tagged with:
amount at risk, amount recovered/avoided, cycle time saved, discount
captured/missed. Aggregated views: daily/weekly/monthly by category,
supplier, resolution type. "This month: $142K in leakage caught.
$38K in discounts captured. 3,200 analyst-hours saved." ROI calculator:
customer inputs their own cost parameters.
*Scenario: S1, S12. Engineering: Extend SOC CL-ECON model. S2P-specific
value tags on DecisionEntry. Aggregation pipeline. React dashboard.*

**F11: Audit & Export Pack**
SOX-ready export of all decisions: DecisionEntry/OutcomeEntry chain,
conservation status history, auto-approve expansion proofs, centroid
drift log, override reason distribution. Per-period audit bundle.
Tamper-evident (hash chain from ci-platform). EU AI Act Article 14
traceability: every auto-approved decision traceable to evidence,
confidence, conservation state, and human override option.
*Scenario: S2, S9. Engineering: ci-platform evidence ledger export +
report generation. Extend XR-BUG-1 fix for S2P.*

### 6.5 Feature Specifications — Month 2-6 (v1.1-v1.3)

**F12: AgentEvolver — Self-Tuning Operations**
Runtime evolution of operational configurations: evidence presentation
order, routing thresholds, escalation criteria, triage priority weights.
AgentEvolver tests variants against the conservation law's promotion
gate (superiority 5pp + correctness floor + conservation check +
variance stability). Promoted variants deploy automatically. Evolution
log: "47 configurations tested. 12 promoted. Resolution speed +12%.
Analyst confirmation time -8 seconds average."
*Scenario: S13, S16. Engineering: AgentEvolver from SOC extended with
S2P-specific variant dimensions. Requires S2P promotion gate criteria.*

**F13: Supplier Behavioral Profile Builder**
Accumulates per-supplier profiles from operational data. Every invoice,
PO, GR, and payment carries supplier signals. After N verified
transactions per supplier: delivery reliability by season, exception
rate trend, pricing behavior, quality patterns, payment response.
Profile display: "Supplier Chen-Lin: OTIF 94% (Q1-Q2), 72% (Q3).
Exception rate: 3% (normal), 11% (post-format-change in June 2026).
Financial health trend: declining 2pp/quarter for 3 quarters."
*Scenario: S6, S7, S8, S11. Engineering: SupplierProfileAccumulator
reading verified DecisionEntry/OutcomeEntry. Per-supplier centroid
tensors. Trend computation on rolling windows.*

**F14: Lead Time Intelligence**
Learns actual lead time distributions from GR timestamps vs PO dates.
Per-supplier × per-product-category × per-season × per-volume-band.
Read-only initially (advisory). Display: "Contractual: 14 days.
Actual Q1-Q3: 14.2 ± 1.8 days. Actual Q4: 21.4 ± 3.2 days. Actual
Q4 when volume > 500 units: 28.1 ± 4.7 days." Cross-graph enrichment:
identifies leading indicators from commodity/logistics/financial data
that predict lead time changes before they manifest.
*Scenario: S8. Engineering: LeadTimeTracker from GR/PO timestamp
deltas. Conditional distribution estimator. Cross-graph correlation
with commodity/financial feeds.*

**F15: Supplier Trend Correlation & Early Warning**
Cross-system trend detection. Correlates: OTIF trend (from GR data) ×
exception rate trend (from invoice data) × financial health trend
(from D&B feed) × commodity exposure (from market feeds). Generates
early warning when multiple signals decline simultaneously even if
each is below individual alarm thresholds. Alert: "Supplier X: 3
signals declining simultaneously. Pattern consistent with financial
stress → delivery failure. Confidence: 0.78. Recommend: qualify backup."
*Scenario: S11. Engineering: Multi-signal trend correlator. Threshold
on combined deterioration score. Requires G8 (cross-system discovery).*

**F16: Behavioral Clustering**
Groups suppliers by operational behavior (not by spend category or
parent company). Clustering dimensions: delivery timing pattern,
pricing behavior, exception rate, quality profile, payment response.
Output: "Cluster 7 contains suppliers A, B, C, F. Delivery correlation:
r=0.94-0.97. Pricing spread: ±1.8%. Recommend: consolidate to 1-2."
Visualization: supplier similarity map (2D projection of behavioral
vectors).
*Scenario: S7. Engineering: Centroid-based clustering on supplier
behavioral vectors. Requires F13 (profiles) as prerequisite.*

**F17: Cross-System Discovery Alerts (Shadow Mode)**
Runs cross-graph attention sweeps across connected data sources
(ERP × supplier × commodity × logistics × process mining). Surfaces
discoveries as advisory alerts — no auto-action initially.
"Discovery: Chicago AP cycle time correlates with Supplier X/Y/Z
invoice format patterns (r=0.89) AND 40% PO volume increase for
Supplier Y. Neither signal alone explains the bottleneck."
Weekly discovery digest for CPO/CSCO.
*Scenario: S5, S10, S16. Engineering: Cross-graph attention engine
(Innovation 7) with S2P data sources. Shadow mode = alert only.*

**F18: Process-Tech Fusion Loop**
Full WHERE→WHY→WHAT→LEARN cycle when Celonis is connected. Celonis
process mining data feeds into UCL as one context source. Cross-graph
attention explains WHY bottlenecks exist. System recommends action
(routing change, supplier flag, escalation). RL scores outcome.
AgentEvolver promotes successful interventions. Next similar bottleneck
at any plant: handled automatically from the promoted variant.
*Scenario: S16. Engineering: Celonis MCP connector → UCL ingestion →
cross-graph sweep → action recommendation → RL feedback → AgentEvolver
promotion. Requires F12 + F17 + Celonis integration.*

### 6.6 Feature Specifications — Month 6-12 (v2.0)

**F19: Payment Timing Optimization**
Per-supplier payment strategy from verified outcomes. Learns: which
suppliers respond to early payment (and at what discount rate), which
deprioritize orders when payment is delayed, which have no correlation
between payment timing and performance. Recommendation engine: "Early-
pay Supplier W (captures $340K/year). On-time Supplier Y (avoids OTIF
drop). Extend Supplier Z (no performance impact, improves DPO by 8
days)."
*Scenario: S12. Engineering: Payment behavior learner from
DecisionEntry/OutcomeEntry on payment decisions. Supplier OTIF
correlation with payment timing. Requires F13 as prerequisite.*

**F20: Centroid-to-Optimizer API**
Structured export of learned parameters for external optimization
engines. Exports: actual lead time distributions (F14), supplier
reliability profiles (F13), DK trust weights, exception likelihood by
supplier × category, cost variance patterns. API format: JSON schema
consumable by Gurobi, AIMMS, OR-Tools, Celonis optimization modules.
*Scenario: S3, S8, S12. Engineering: API design + parameter
serialization. 2 weeks design, 2 weeks implement.*

**F21: Disruption Simulation Sandbox**
"What if" scenario modeling using learned parameters. "What if Supplier
X delays 2 weeks? Impact on 3 categories, 12 POs, estimated cost
$140K. Alternative suppliers available: Y (OTIF 91%, lead time +3
days) and Z (OTIF 87%, lead time +5 days, $2K higher per unit)."
Uses accumulated centroid knowledge as the simulation substrate.
*Scenario: S3. Engineering: Scenario engine consuming F13 + F14 +
centroid state. Advisory output, not auto-action.*

**F22: Compliance Screening with Conservation Proof**
UFLPA / CSDDD / Scope 3 screening decisions that improve over time.
Conservation law proves screening quality: "Screened 94% of high-risk
transactions at 91% accuracy this quarter. Tamper-evident audit trail
attached." Initially cross-cutting via Control Tower (routes compliance
intents to Supplier Reliability Copilot). Dedicated Compliance Sentinel
copilot when regulatory volume justifies.
*Scenario: Cross-cutting. Engineering: Compliance intent types in
Control Tower taxonomy. Compliance-specific factors (sanctions_match,
tier2_supplier_risk, scope3_exposure). Dedicated factor space when
Compliance Sentinel ships.*

### 6.7 Verification Architecture

| Class | Decisions | Time | Signal | Features |
|-------|-----------|------|--------|----------|
| Fast operational | Invoice resolve, PO approve, PR route | Hours | Binary + reason code | F3, F5 |
| Delayed operational | Compliance flag, supplier risk, quality | Days-weeks | Binary + graded risk | F3, F15 |
| Optimization | Sourcing, rebalancing, lead time | Weeks-months | Graded (KPI delta) | F19, F20, F21 |

**Outcome Receipt Object (v1.1):**
```
{
  event_type, event_id, timestamp,
  recommended_action, confidence, evidence_chain,
  conservation_state, copilot_id,
  human_action (confirm/override), reason_code,
  financial_impact { amount_at_risk, amount_recovered, cycle_time_saved },
  learning_update { centroid_moved: bool, weight_updated: bool },
  audit_status { hash, prev_hash, exportable: bool }
}
```

---

## §PD7 — Architectural Gaps

### 7.1 Gaps (v0.7 → v1.0)

| Gap | Description | Effort | Priority |
|-----|-------------|--------|----------|
| G1 | Per-copilot factor spaces with shared canonical layer | 1-2 wk | P0 |
| G2 | Invoice-specific categories & actions (5×5) | 1 wk | P0 |
| G3 | Verification UX (in-line confirm/override + reason codes) | 2 wk | P0 |
| G4 | Centroid Explorer (visual "why") | 1-2 wk | P1 |
| G5 | Conservation Dashboard (GREEN/AMBER/RED, expansion proofs) | 1 wk | P1 |
| G6 | Multi-copilot Control Tower routing (15-18 S2P intents) | 2-3 wk | P0 |
| G7 | Supplier behavioral profile accumulation | 2-3 wk | P1 |
| G8 | Cross-system discovery engine (S2P graph attention) | 3-4 wk | P2 |
| G9 | Centroid-to-optimizer API | 3-4 wk | P2 |
| G10 | Outcome receipt object | 1 wk | P1 |
| G11 | Financial impact ledger (CL-ECON-S2P) | 2 wk | P1 |
| **G12** | **Situation Analyzer S2P reasoning (47-node traversal for procurement intents, contract/commodity/supplier context chain)** | **3-4 wk** | **P1** |
| **G13** | **AgentEvolver S2P variant dimensions (evidence ordering, routing thresholds, escalation criteria, triage weights)** | **2-3 wk** | **P1** |
| **G14** | **RL reward signal calibration for S2P (penalty ratio per copilot, reward structure per decision type)** | **1-2 wk** | **P1** |

### 7.2 Reuse from SOC/GAE

| Component | Status | S2P Reuse |
|-----------|--------|-----------|
| ProfileScorer + centroid learning | ✅ Shipped | Direct — change factors, categories, actions |
| DiagonalKernel + KernelSelector | ✅ Shipped | Direct — per-copilot σ from P28 |
| Conservation law + AMBER auto-pause | ✅ Shipped | Direct — penalty ratio 5:1 |
| Two-phase learning + batch pipeline | ✅ Framework v4 | Implement from v10.8 spec |
| AgentEvolver + promotion gate | ✅ Shipped (SOC) | Extend with S2P variant dimensions (G13) |
| Situation Analyzer | ✅ Design | S2P intent taxonomy + graph traversal (G6, G12) |
| RL reward signal | ✅ Shipped (SOC) | Re-calibrate for S2P penalty ratios (G14) |
| IKS measurement | ✅ Shipped | Direct — domain-agnostic |
| P28 deployment qualification | ✅ Shipped | Direct — S2P DomainConfig |
| Evidence ledger + audit chain | ✅ Shipped | Direct — DecisionEntry/OutcomeEntry |
| Novelty detection | ✅ Framework v4 | Implement from v15 spec |
| Re-Convergence Theorem | ✅ Proven | S2P parameters validated (v0.7 §17.6) |

### 7.3 Effort Estimate

| Milestone | Gaps | Weeks |
|-----------|------|-------|
| Phase 0 (Preview Tab) | M1+M3+M5 | ~2 |
| Minimum viable pilot | +G1+G2+G3 | +6-8 |
| Demo-ready pilot | +G4+G5+G12 | +3-5 |
| Full v1.0 (all P0+P1) | +G6+G7+G10+G11+G13+G14 | +5-7 |
| **Total to full v1.0** | | **~16-22 weeks** |

Note: §13 critical path shows ~10 weeks for Phase 1 (minimum pilot) +
~10 weeks for Phase 1.1 (full v1.0 + Situation Analyzer). The
difference from §7.3 is that §13 sequences tasks on the CRITICAL PATH
while §7.3 counts total effort. Some tasks parallelize (e.g., G4
Centroid Explorer can build while G3 Verification UX progresses).

---

## §PD8 — What Ships When

| Version | What | Weeks | Scenarios | Key Features |
|---------|------|-------|-----------|-------------|
| **Phase 0** | **S2P Preview Tab in SOC demo** | **1-2** | **1, 2, 6, 8** | **Mini F1, F4, F9 + supplier preview (§12)** |
| **v1.0** | Invoice Exception Copilot + Control Tower | 3-10 | 1, 2, 9, 15 | F1-F5, F7, F9, F11 |
| **v1.1** | + Price Leakage Guardian. Situation Analyzer reasoning. AgentEvolver. Outcome receipts. | 8-16 | +5, 10, 13, 14, 16 | F2 (full), F6, F8, F10, F12 |
| **v1.2** | + Supplier profiles auto-building. Lead time learning. Requisition Copilot. | 12-20 | +6, 7, 8 | F13, F14, F16 |
| **v1.3** | + Cross-system discovery (shadow). Trend correlation. | 16-24 | +11 | F15, F17, F18 |
| **v2.0** | + Working Capital Copilot. Optimizer API. Compliance. Disruption sim. | 22-34 | +3, 12 | F19-F22 |

---

## §PD9 — Value Model

| Cluster | Scenarios | Y1 Value | How Measured |
|---------|-----------|----------|-------------|
| A: Invoice/AP Learning | 1, 2, 9, 13, 14, 15 | $14-19M | Exception rate, auto-approve %, leakage, self-tuning savings |
| B: Supplier Intelligence | 6, 7, 8, 11 | $8-12M | Consolidation, stockout reduction, early warning |
| C: Cross-System Discovery | 5, 10, 16 | $6-12M | Discoveries/quarter × impact. Process-tech fusion savings |
| D: Capital Optimization | 12 | $3-5M | DPO, discounts, supplier OTIF |
| E: Disruption Recovery | 3, 4 | $10-23M | Recovery time × disruption cost/day |
| **TOTAL** | | **$41-71M** | |

---

## §PD10 — Open Questions

1. **Pilot customer profile:** SAP vs Oracle, Coupa presence, exception
   rate, supplier count, recent disruption experience.
2. **Per-copilot penalty ratios:** **RESOLVED for v1.0: 5:1 for all
   S2P copilots at pilot.** Per-copilot calibration (Invoice 5:1 vs
   Compliance 15-20:1) is a v1.1 research item. Rationale: S2P invoice
   exception errors are less severe than SOC misclassifications (20:1).
   5:1 is conservative enough for AP without over-constraining learning.
3. **Compliance Sentinel timing:** When does regulatory volume justify
   dedicated copilot vs cross-cutting?
4. **Cross-copilot signal propagation:** When Supplier Reliability
   detects OTIF decline, should Invoice Exception auto-tighten for
   that supplier? Policy needed.
5. **CL-ECON-S2P-MEASURED:** Hackett-calibrated $/exception. Grounds
   the value model.
6. **Red Inventory / network optimization:** When does multi-DC
   rebalancing enter the roadmap? Which external solver?
7. **Situation Analyzer depth for S2P:** How many graph traversal
   patterns for invoice reasoning? Contract clause lookup? Commodity
   correlation? Supplier behavioral context? This determines G12 scope.
8. **AgentEvolver variant space for S2P:** What operational dimensions
   should the system be allowed to self-tune? Evidence ordering, yes.
   Routing thresholds, yes. Penalty ratios? Conservation parameters?
   Where's the boundary of what Loop 2 can evolve vs what Loop 3 fixes?

---

## §PD11 — Missing Engineering Specifications

These items are NOT in §7 (architectural gaps between v0.7 and v1.0).
These are specifications that the FEATURES in §6 reference but don't
define with enough precision for a coding session to implement.

### M1: S2PDomainConfig Class [BLOCKS EVERYTHING]

**Migration note:** The existing S2P codebase uses (C=6, A=4, D=6)
from the SOC template (BACKLOG-051). This document specifies (C=5,
A=5, D=7) as the target for invoice exception triage. Step 0.1
migrates the DomainConfig from (6,4,6) to (5,5,7). All existing S2P
tests (70 unit tests) will need updating. The existing `/api/s2p/score`
endpoint uses the old shape — the Preview Tab creates a NEW namespace
`/api/s2p/preview/*` to avoid breaking the existing endpoint during
migration.

The ProfileScorer needs a DomainConfig to instantiate. SOC has
SOCDomainConfig. S2P needs:

```python
class S2PDomainConfig:
    domain = "s2p"
    categories = {0: "price_variance", 1: "quantity_mismatch",
                  2: "duplicate_risk", 3: "contract_gap",
                  4: "format_compliance"}
    actions = {0: "auto_approve", 1: "hold_for_review",
               2: "escalate_to_buyer", 3: "flag_leakage",
               4: "refer_to_specialist"}
    factors = ["match_status", "amount_variance_ratio",
               "duplicate_score", "supplier_exception_history",
               "payment_terms_impact", "commodity_index_correlation",
               "tax_regulatory_compliance"]
    canonical_factors = ["supplier_identity", "contract_linkage",
                         "spend_category", "data_quality_score"]
    penalty_ratio = 5.0
    η_confirm = 0.05
    η_override = 0.01  # Decision D3 RESOLVED: use 0.01 (SOC value)
                       # for pilot. Re-derive from S2P analyst quality
                       # data during pilot (measure q̄_worst for AP
                       # analysts; if q̄_worst > 0.60, η_override
                       # increases via η_confirm × (2q̄_worst − 1)).
    τ = 0.1            # SOC-validated. S2P-V3B calibration experiment
                       # still required per v0.7 §17. Use 0.1 until
                       # S2P-V3B runs. (v0.7 considered τ=0.4 for
                       # softer distributions but did not confirm.)
    q_window = 400
    α_window = 50
```

**Decision D1:** Do conservation parameters (θ_min formula, q_window,
α_window) stay identical to SOC? At V=200/day, math works. At V=50/day
(smaller firm), θ_min = 23.53/(0.15×50) = 3.14 — doesn't make sense.
**For now: use SOC formula unchanged. The 23.53 constant was derived
from accuracy thresholds and is domain-agnostic. At low volume, θ_min
becomes high, which means the conservation law is MORE conservative
(harder to leave GREEN). This is actually correct behavior — low volume
= less evidence = more caution. Revisit if pilot shows false AMBER
triggers at low volume.**

### M2: Factor Computers [BLOCKS PILOT]

Each factor needs a computation spec — function from raw data → [0,1]:

| Factor | Input | Computation (v1 — simple) |
|--------|-------|--------------------------|
| match_status | PO lines, GR quantities, invoice amounts | Fraction of lines where all three match within tolerance |
| amount_variance_ratio | Invoice total, PO total | min(abs(inv-PO)/PO, 1.0) |
| duplicate_score | Invoice #, supplier, amount, date vs history | max(fuzzy_match_score across candidates) |
| supplier_exception_history | Prior invoices from this supplier | exception_count / total_count, trailing 200 invoices |
| payment_terms_impact | Discount %, days to discount, current DPO | (discount_value / invoice_amount) normalized |
| commodity_index_correlation | Commodity Δ%, price Δ% | abs(price_delta - commodity_delta) / max(price_delta, 0.01) |
| tax_regulatory_compliance | Tax calc, regulatory flags | 1.0 - (violation_count / rules_checked) |

These are v1 simple formulas. DK will learn which to trust. Phase 2
will refine the weights. The formulas just need to be REASONABLE, not
optimal — the learning corrects for imprecision.

### M3: Initial Centroid Values (μ₀) [BLOCKS PILOT + DEMO]

25 cells (5 categories × 5 actions). Each cell needs 7 factor values.
Example for 2 cells:

**price_variance × auto_approve:** [0.95, 0.05, 0.02, 0.03, 0.50,
0.80, 0.95] — high match, tiny variance, no duplicate, clean history,
neutral payment, commodity explains it, tax clean.

**price_variance × flag_leakage:** [0.90, 0.40, 0.05, 0.25, 0.70,
0.15, 0.85] — match OK, significant variance, not duplicate, some
history, payment matters, commodity does NOT explain it, mostly clean.

Full 25-cell specification needed. Can be generated systematically
from domain heuristics in a coding session.

### M4: Typed Intent Taxonomy [BLOCKS G6]

Not in this document. Judge synthesis produced 18-20 intents. For pilot,
5 intents needed:

| Intent | Copilot | Trigger |
|--------|---------|---------|
| invoice_match_failure | Invoice Exception | 3-way match failure |
| invoice_price_variance | Invoice Exception / PVG | Price delta > threshold |
| invoice_duplicate_risk | Invoice Exception | Similarity score > 0.8 |
| commodity_price_correlation | Price Leakage Guardian | Commodity index spike |
| po_auto_approve_candidate | Invoice Exception | Routine PO under threshold |

Full taxonomy (15-18 intents) in §8 timeline for v1.1+.

### M5: S2P Synthetic Data Generator [BLOCKS DEMO + TESTING]

Needs to produce:
- Synthetic invoices (50 for demo, 5,000+ for testing) with controlled
  factor distributions and known ground truth actions
- Synthetic suppliers (10 for demo, 100+ for testing) with behavioral
  profiles (exception rates, lead times, pricing patterns)
- Noise injection (analyst quality levels, per B5B-PROXY methodology)
- Oracle ground truth labels per invoice

Architecture: extend SOC's synthetic_alert_generator pattern. Replace
alert categories with invoice categories. Replace security factors
with procurement factors. Same noise/oracle infrastructure.

### M6: Feature Dependency Graph

```
M1 (DomainConfig)
├── M5 (synthetic data) → M3 (centroids) → Preview Tab
├── M2 (factor computers) → F1 (dashboard) → F3 (verification)
│   └── F2 (evidence) ← G12 (Situation Analyzer) ← M8 (templates)
├── F4 (conservation) → F5 (auto-approve) ← G14 (RL calibration)
├── F6 (novelty) ← M5 (baseline distributions)
├── F7 (centroid explorer)
├── F9 (IKS) — already built, wire to DomainConfig
├── F10 (financial impact) ← G11 + F3
├── F11 (audit) ← F3
├── G6 (Control Tower) ← M4 (intents) → F12 (AgentEvolver) ← G13
├── F13 (supplier profiles) ← G7 + F3 (accumulated decisions)
│   ├── F14 (lead times) ← GR/PO timestamps
│   ├── F16 (clustering) ← F13
│   └── F15 (trend correlation) ← F13 + G8
├── F17 (discovery) ← G8
├── F18 (process-tech) ← F12 + F17
└── F19-F22 ← various v2.0 deps
```

### M7: API Endpoint Specification

| Endpoint | Method | Purpose | Phase |
|----------|--------|---------|-------|
| /api/s2p/score | POST | Score an invoice exception | v1.0 |
| /api/s2p/queue | GET | Prioritized exception queue | v1.0 |
| /api/s2p/verify | POST | Submit confirm/override + reason | v1.0 |
| /api/s2p/conservation | GET | Conservation status per copilot | v1.0 |
| /api/s2p/iks | GET | IKS score and trend | v1.0 |
| /api/s2p/centroid/{cat}/{act} | GET | Centroid state for explorer | v1.0 |
| /api/s2p/financial-impact | GET | Aggregated financial impact | v1.1 |
| /api/s2p/supplier/{id}/profile | GET | Supplier behavioral profile | v1.2 |
| /api/s2p/discovery/digest | GET | Weekly discovery alerts | v1.3 |
| /api/s2p/preview/* | GET | Simplified endpoints for demo tab | Preview |

### M8: Evidence Templates (F2)

One NL reasoning template per category:

- **price_variance:** "{variance_pct}% price delta. {commodity} moved
  {commodity_delta}% in {lookback} days. Contract {ref} {allows/blocks}
  pass-through up to {threshold}%. {Within/Exceeds} bounds. → {action}.
  Confidence: {score}."
- **quantity_mismatch:** "Invoice qty {inv} vs PO {po} (Δ {delta}).
  GR confirms {gr} received. {Matches/Partial/Discrepancy}. → {action}."
- **duplicate_risk:** "Invoice {id} from {supplier}. Similar: {match_id}
  dated {date}, amount {amt} (similarity {sim}%). {Duplicate/Variant/
  Distinct}. → {action}."
- **contract_gap:** "PO {po_id}. Contract {ref} covers {scope}.
  {covered_pct}% covered. Gap: {items}. → {action}."
- **format_compliance:** "Invoice from {supplier} fails {n} format rules.
  Issues: {list}. Historical compliance: {pct}%. → {action}."

### M9: Shared vs Specialized Factor Architecture

**Decision: Option C.** 7-factor tensor for scoring. Canonical factors
as pre-filters and SituationAnalyzer context, NOT in centroid distance.

**Option A (rejected):** 11-factor tensor (4+7 = 5×5×11=275). Larger
tensor, slower convergence. Canonical factors dilute scoring signal.

**Option B (rejected):** 7-factor scoring only. Canonical factors
invisible to scoring. Misses supplier_identity as a pre-filter.

**Option C (adopted):** 7-factor scoring (175-value tensor). Canonical
factors used for: (a) pre-filtering ("only score if supplier resolves"),
(b) SituationAnalyzer reasoning (F2 evidence chains), (c) Control
Tower routing. ProfileScorer uses 7 specialized factors only.
FactorComputers produce both canonical and specialized; ProfileScorer
consumes only specialized.

---

## §PD12 — S2P Preview Tab (SOC Demo Enhancement)

### Purpose
6th tab in the existing SOC demo. Shows S2P capabilities on synthetic
data. Proves platform is domain-agnostic. Makes SOC demo compelling
for investors/customers who want platform breadth.

### Four Panels

**Panel A: Invoice Exception Queue (Mini F1)**
5 synthetic invoice exceptions in a triage queue. Each: supplier name,
variance type, amount, recommendation, confidence. Click → simplified
evidence panel showing **7 procurement-specific factors** (not the 6
SOC security factors — this is the visual proof of domain-agnosticism).
Canonical factors (supplier_identity, etc.) appear in the evidence
context but NOT in the scoring radar/bar chart.

**Panel B: Conservation Status (Mini F4)**
Single gauge: GREEN/AMBER/RED. Auto-approve %. Verified decision count.
"S2P Copilot: GREEN. Auto-approve: 45%. 2,100 verified decisions."

**Panel C: Compounding Curve (reuses SOC Tab 4 chart)**
Accuracy trajectory chart — same visualization as SOC Tab 4 compounding
dashboard. Shows the SAME engine compounding in a different domain.

**Panel D: Supplier Intelligence Preview (Mini F13)**
1-2 supplier cards. "Supplier Chen-Lin: OTIF 94% (Q1-Q2), 72% (Q3).
Exception rate: 3% baseline, 11% since June. Lead time: 14 days
contractual, 21 days actual Q4." Read-only. **Data source:** JSON
fixture file `s2p_demo_suppliers.json` seeded by M5 synthetic
generator. Pre-computed (not live-scored — supplier profiles require
accumulated history that can't be generated in real-time for demo).

**Header:** All four panels display "Powered by Graph Attention Engine
v0.7.23" — same version string visible on SOC tabs. Makes the "same
engine" claim visually provable.

### What NOT to Show
Full triage workflow, AgentEvolver, Situation Analyzer, cross-system
discovery, payment optimization, process-tech fusion. These are full
product features, not demo preview.

### Demo Script
1. Finish SOC walkthrough (Tabs 1-5)
2. Click "S2P Preview" → procurement context
3. "Same engine, different domain."
4. Panel A: "5 exceptions. System auto-approves #1 (commodity-driven,
   0.94 confidence), holds #3 (duplicate risk, 0.87)."
5. Panel B: "Conservation GREEN at 45% auto-approve."
6. Panel C: "Compounding curve — 72% → 84% over 1,000 decisions."
7. Panel D: "Supplier Chen-Lin: Q3 delivery drops, format change spiked
   exceptions. New category manager sees this Day 1."
8. "The engine is domain-agnostic. The intelligence is firm-specific."

### Engineering (Minimal New Code)
- S2PDomainConfig (M1) — needed anyway, migrates (6,4,6) → (5,5,7)
- Synthetic generator (M5, 50 invoices, 10 suppliers) + `s2p_demo_suppliers.json`
- Initial centroids (M3, 25 cells)
- S2PPreviewTab.tsx (~300-400 lines, reuses SOC component patterns)
- 3 preview API endpoints under `/api/s2p/preview/*` namespace
  (does NOT modify existing `/api/s2p/score` endpoint)
- Reuses: ProfileScorer, ConservationMonitor, IKSService, chart viz

**Queue alignment:** Coding queue G-04 scoped the tab at 2-3 days.
This is the TAB ONLY. Prerequisites: M1 (1-2 days) + M5 minimal
(1 day) + M3 (0.5 day) = ~3-4 days before the tab. Total including
prerequisites: ~6-7 days ≈ ~2 weeks.

**Effort: ~2 weeks** (including M1/M3/M5 prerequisites).

### Preview Tab Scoring Approach
The Preview Tab uses LIVE ProfileScorer scoring (not pre-computed).
The 50 synthetic invoices are scored by the actual ProfileScorer with
S2PDomainConfig, producing real confidence scores and conservation
state. This ensures: (a) the demo is credible (same engine, provably),
(b) the DomainConfig is validated by real scoring before Phase 1, and
(c) the Preview Tab can show live centroid updates if an analyst clicks
confirm/override during the demo. Pre-computed data is used only for
Panel D (supplier profiles — these need accumulated history that can't
be live-generated in a demo).

### Testing Strategy (All Phases)
Follow SOC testing patterns. S2P target: ~170 tests at Preview Tab,
~500 at v1.0, ~800 at v1.1. Per-phase:
- **Phase 0:** DomainConfig validation + synthetic data + ProfileScorer
  scoring with S2P config (~100 GAE/backend tests for M1/M3/M5).
  Preview Tab API integration (~50 tests). E2E: tab renders, panels
  display, scoring returns valid results (~20 tests). Total: ~170.
  Note: existing 70 S2P tests need updating for (5,5,7) shape.
- **Phase 1:** Factor computer edge cases (~50 tests). Verification
  flow integration (~30 tests). Conservation law with S2P parameters
  (~30 tests). Auto-approve gate tests (~20 tests). Centroid update
  correctness (~30 tests). E2E: full triage workflow (~15 tests).
- **Phase 1.1:** Control Tower routing tests per intent (~30 tests).
  Situation Analyzer traversal tests per category (~25 tests).
  AgentEvolver promotion gate tests (~20 tests).
- Use SOC's existing test infrastructure (pytest, E2E framework).

### Graph Schema Reference
Factor computers (M2) pull data from the S2P UCL graph. The graph
schema is defined in S2P Design v0.7 §5 (graph nodes: suppliers,
purchase_orders, invoices, goods_receipts, contracts, commodities)
and §9 (connectors: SAP, Coupa, D&B). The coding session should
reference v0.7 for graph traversal patterns. Key dependency:
M2 factor computers → v0.7 §5 graph nodes → v0.7 §9 connectors.

---

## §PD13 — Coding Sequence (Critical Path)

### Phase 0: S2P Preview Tab (~2 weeks)

| Step | What | Days | Prereq |
|------|------|------|--------|
| 0.1 | S2PDomainConfig (M1) | 1-2 | None |
| 0.2 | Synthetic data generator (M5, minimal) | 2-3 | 0.1 |
| 0.3 | Initial centroids (M3, 25 cells) | 1 | 0.1 |
| 0.4 | Preview API endpoints | 2 | 0.1-0.3 |
| 0.5 | S2PPreviewTab.tsx (4 panels) | 2-3 | 0.4 |

### Phase 1: Invoice Exception Copilot v1.0 (~8-12 weeks)

| Step | What | Weeks | Prereq |
|------|------|-------|--------|
| 1.1 | Factor computers (M2, all 7) | 1-2 | Phase 0 |
| 1.2 | Invoice categories & actions (G2) | 1 | Phase 0 |
| 1.3 | Verification UX + reason codes (G3/F3) | 2 | 1.2 |
| 1.4 | Exception triage dashboard (F1, full) | 1-2 | 1.1, 1.3 |
| 1.5 | Conservation dashboard (G5/F4, full) | 1 | Phase 0 |
| 1.6 | Auto-approve engine (F5) + RL calibration (G14) | 1-2 | 1.5 |
| 1.7 | Centroid Explorer (G4/F7) | 1-2 | 1.1 |
| 1.8 | IKS tracker (F9) | 0.5 | Phase 0 |
| 1.9 | Audit pack (F11) | 1 | 1.3 |

### Phase 1.1: Price Leakage + Situation Analyzer (~8-12 weeks)

| Step | What | Weeks | Prereq |
|------|------|-------|--------|
| 1.1.1 | Control Tower routing (G6, 5 intents) | 2-3 | Phase 1 |
| 1.1.2 | Situation Analyzer traversals (G12) | 3-4 | 1.1.1 |
| 1.1.3 | Evidence templates (M8) | 1 | 1.1.2 |
| 1.1.4 | PVG factor space + centroids | 1 | 1.1.1 |
| 1.1.5 | Financial impact ledger (G11/F10) | 2 | Phase 1 |
| 1.1.6 | Novelty detection (F6) | 1-2 | Phase 1 |
| 1.1.7 | AgentEvolver S2P (G13/F12) | 2-3 | Phase 1 |
| 1.1.8 | Outcome receipt object (G10) | 1 | 1.3 |

### Critical Path

```
M1 (DomainConfig, 2 days)
  → M5 (synthetic, 3 days) + M3 (centroids, 1 day)
    → Preview Tab (5 days)
      → M2 (factor computers, 2 weeks)
        → G3 (verification UX, 2 weeks)
          → F1 (full dashboard, 2 weeks)
            → Phase 1 complete (~10 weeks from M1)
              → G6 (Control Tower, 3 weeks)
                → G12 (Situation Analyzer, 4 weeks)
                  → Phase 1.1 complete (~20 weeks from M1)
```

**First coding action: M1 (S2PDomainConfig). Unblocks everything.**

---

*S2P Product Definition v1.3 · April 30, 2026*
*16 scenarios. 5 clusters. 9 unlocks. 22 features. 14 gaps.*
*9 missing specs (all resolved or defaulted). S2P Preview Tab designed.*
*Coding sequence: M1 → Preview Tab (~2 wk) → v1.0 (~10 wk) → v1.1 (~20 wk)*
*Tensor migration: (6,4,6) → (5,5,7). Preview: /api/s2p/preview/*.*
*Procurement that learns, reasons, tunes itself, and values caution.*


---

*S2P Copilot — Unified Design & Product Definition v1.3*
*Part I: Engineering Design (§1-§17 from v0.7)*
*Part II: Product Definition (§PD1-§PD12 from v1.3)*
*ONE document. Architecture + Scenarios + Engineering Specs.*
*16 scenarios. 5 clusters. $680K/year leakage. 50% exception reduction.*
