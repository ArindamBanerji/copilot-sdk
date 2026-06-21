# R18 — S2P Supplier Intelligence Profile

**Version:** 1.5
**Date:** June 15, 2026
**Status:** Roadmap-approved design — pending implementation review
**Source:** Codex pre-check (PLAN_REQUIRED) + Roadmap strategy review
**Depends on:** P39B (shipped), P36 (shipped), P38 (shipped)

---

## §1 — What R18 Actually Is

### 1.1 The Codex Pre-Check Finding

The Codex session returned `R18_PRECHECK_VERDICT: PLAN_REQUIRED`.
The original shallow prompt proposed new supplier profile files and
endpoints, but the pre-check found:

- Supplier profile routes already exist (`s2p_suppliers.py`)
- Supplier profile accumulator already exists
- P39B supplier enrichment already exists
- P36 lead-time service already exists
- Supplier preview fixture cards already exist
- Route namespace has collision risk
- Current profile endpoint blends accumulator + fixture data
- The product risk is provenance overclaim, not lack of files

R18 cannot safely proceed from the original prompt.

### 1.2 What R18 Should Be

R18 is the first product surface where the buyer SEES compiled
entity intelligence — and the primary buyer is the **category /
procurement manager** who owns supplier risk, personally feels
analyst-attrition pain, and would act on "Chen-Lin deteriorating."

The opening hook is DISCOVERY, not retention:

> "You've been wondering about Chen-Lin, haven't you? Here's the
> receipts — compiled from your own analysts' verified decisions,
> not our model, not a database lookup."

After R18, the category manager can see:

```
Supplier Intelligence Profile: Chen-Lin Electronics

Intelligence Depth: ████████░░ Deep
  4 of 6 metrics past threshold (exception_rate, accuracy,
  category_mix, quarterly_volume)
  150 verified decisions

  Optional (show only when source fields exist):
  · analyst count (requires analyst identity in decision metadata)
  · time span (requires verified timestamps on decisions)
  If unavailable, show "150 verified decisions" only — do not
  fabricate "3 analysts" or "8 months" from unsupported data.

What the system caught:
  ██ 12 real discrepancies confirmed by your team
     worth $148,800 in flagged invoice value
  ██ exception_rate: 15% (rising — was 8% in Q1)
  ██ accuracy: 78% (below category average of 89%)

What is still context-only:
  ░░ OTIF: 88% → connect ERP to verify
  ░░ lead_time: 6.2 days → connect logistics to verify
  ░░ payment_terms: Net 30 → connect AP system to verify

Risk: HIGH (learned — 150 verified decisions)
```

The ██ learned lines are the moat. The ░░ context lines are the
**upsell map** — each "connect X to verify" is a visible, buyer-
legible roadmap of what they can connect next. The absences sell
the expansion.

**Primary persona: Category / Procurement Manager.**

Optimize the default view for them (supplier risk, deterioration
detection, caught discrepancies). The CFO exposure number is
**escalation ammunition the category manager carries upward** —
not the centerpiece. The AP analyst sees operational detail on
drill-down.

No competitor has this screen. Coupa shows supplier master data.
Zycus shows spend analytics. Neither shows entity-level intelligence
compiled from verified operational decisions with provenance tags
distinguishing learned from context.

### 1.3 The Commercial Position

R18 is not a feature checkbox. It's a narrative milestone:

| Before R18 | After R18 |
|---|---|
| "The system gets smarter" (invisible, trust-me) | "Here's WHAT it learned about Chen-Lin" (visible, verifiable) |
| Compounding intelligence = engine internals | Compiled entity intelligence = buyer-facing |
| "15,000 decisions survive" = abstract claim | "Chen-Lin: 150 decisions, rising exception rate" = concrete |
| Fixture supplier cards = static, same for everyone | Intelligence profiles = learned, unique to YOUR operations |

---

## §2 — Architecture

### 2.1 The Composer Pattern

R18 is a READ-ONLY composer/facade over existing data sources.
No new enrichment pipeline. No GraphStore changes. No scorer
mutation.

```
┌──────────────────────────────────────────────┐
│          R18: Supplier Intelligence           │
│              Profile Composer                 │
│                                               │
│  Reads from:                                  │
│    P39B enrichment (verified metrics)    ██   │
│    P36 lead-time (invoice context)       ░░   │
│    Supplier accumulator (display)        ░░   │
│    Supplier fixture/context              ░░   │
│                                               │
│  Produces:                                    │
│    SupplierIntelligenceProfileResponse        │
│    - intelligence depth tier                  │
│    - risk tier with basis                     │
│    - per-metric provenance                    │
│    - economic exposure (mixed-source)         │
│    - trend (if sufficient verified history)   │
│    - new-manager summary                      │
└──────────────────────────────────────────────┘
```

### 2.2 Data Precedence Rule

When the same metric is available from multiple sources, the
composer follows a strict precedence:

```
1. P39B verified enrichment WINS (source="verified_outcomes")
2. Accumulator display values SUPPLEMENT (labeled as accumulator)
3. Fixture/context values provide IDENTITY (labeled as context)
4. Missing values become UNAVAILABLE (honest absence)
```

The precedence is enforced in code, not by convention:

```python
def resolve_metric(self, metric_name, supplier_id):
    # 1. Try P39B enrichment (authoritative)
    enrichment = self.enrichment_store.read_entity_enrichment(
        domain="s2p", entity_type="Supplier",
        entity_id=supplier_id, namespace="s2p_supplier_metrics")
    if metric_name in enrichment:
        return enrichment[metric_name]  # ProvenancedValue, provenance intact
    
    # 2. Try accumulator (display supplement)
    acc_value = self.accumulator.get(supplier_id, metric_name)
    if acc_value is not None:
        return ProvenancedValue.from_fixture(
            acc_value, label="computed from decision history (not outcome-verified)")
    
    # 3. Try fixture (context only)
    fixture_value = self.fixture.get(supplier_id, metric_name)
    if fixture_value is not None:
        return ProvenancedValue.from_fixture(fixture_value)
    
    # 4. Absent
    return ProvenancedValue.unavailable(f"{metric_name} not available")
```

Note: accumulator values use `from_fixture()` with a distinguishing
label — the accumulator is a live-computed display value, not
verified-outcome-backed enrichment. If future work verifies
accumulator values against outcomes, they would graduate to
`from_verified()`.

### 2.3 What R18 Does NOT Do

| Constraint | Why |
|---|---|
| No new enrichment writes | P39B is the enrichment producer. R18 consumes. |
| No GraphStore protocol changes | R18 reads through existing APIs. |
| No scorer factor feedback | `factor_eligible` is defined but not consumed (Half 2, deferred). |
| No conservation/DK mutation | R18 is display-only. |
| No raw sqlite3 | All reads through GraphStore or existing services. |
| No fixture values claiming measured/verified | Enforced by ProvenancedValue type guards. |
| No new router mount (v1) | Extend existing `/api/s2p/suppliers/{id}/profile` additively. |

---

## §3 — The Journey (Cold Start → Deep)

### 3.1 The Problem This Section Solves

The entire surface's value requires accumulated verified decisions.
A new buyer on day one has zero — every supplier reads "No
intelligence / INTEGRATION_PENDING." The most differentiated
screen in the product is BLANK for a new customer. A sharp buyer
doing diligence asks "so on day one, all my suppliers show 'no
intelligence'?" The honest answer is yes.

This is fixable, and the fix is itself a product feature.

### 3.2 Depth as Journey, Not Verdict

The depth bar is not a verdict on the supplier. It's a record
of accumulation-in-progress that the buyer is invested in growing:

```
Day 1:     ░░░░░░░░░░  No intelligence (0 decisions)
Week 2:    █░░░░░░░░░  Emerging (8 decisions)
Month 2:   ███░░░░░░░  Developing (35 decisions)
Month 5:   █████░░░░░  Reliable (72 decisions)
Month 8:   ████████░░  Deep (150 decisions)
```

"Watch this fill" is an engagement mechanic. No competitor's static
supplier master screen can show accumulation over time. The depth
bar makes compounding VISIBLE as a process the buyer is living
through.

### 3.3 Trajectory Projection

Show how fast intelligence is building, not just where it is:

```
Intelligence Depth: ███░░░░░░░ Developing (35 decisions)
At your current invoice volume: → Reliable in ~6 weeks
                                → Deep in ~4 months
```

The projection is labeled as a PROJECTION (per provenance
discipline — not a promise). It's computed from:

```python
def project_depth(self, current_count, weekly_decision_rate,
                  thresholds) -> dict:
    projections = {}
    for tier, threshold in thresholds.items():
        if current_count < threshold and weekly_decision_rate > 0:
            weeks = (threshold - current_count) / weekly_decision_rate
            projections[tier] = f"~{int(weeks)} weeks"
    return projections
```

This kills the blank-screen problem by selling the SLOPE instead
of the current point.

### 3.4 Pilot Import Bridge

A buyer who ran a pilot isn't at zero. The SQLite→AGE migration
(P29) imports existing decision history — pilot decisions seed
the intelligence depth immediately:

```
Intelligence Depth: ████░░░░░░ Developing (42 decisions)
Source: imported from pilot (Feb–Apr 2026)
```

Make "your pilot decisions already seeded this" explicit in the
onboarding flow. Cold-start only bites true greenfield deployments
— and even there, the trajectory projection shows when intelligence
arrives.

### 3.5 The Day-1 Screen

For a true greenfield supplier (zero decisions):

```
Supplier Intelligence Profile: New Supplier Inc.

Intelligence Depth: ░░░░░░░░░░ No intelligence yet
  At your invoice volume: → Emerging in ~2 weeks
                          → Developing in ~6 weeks

What the system knows:
  (no verified decisions yet)

What is available as context:
  ░░ supplier_name: New Supplier Inc. (source system)
  ░░ OTIF: 92% → connect ERP to verify
  ░░ payment_terms: Net 45 → connect AP system to verify

Risk: INTEGRATION_PENDING
  "Start processing invoices to build intelligence"
```

This screen is HONEST and COMPELLING: it shows the buyer exactly
what the system will learn, how fast, and what they can connect to
accelerate it. The emptiness sells the journey.

---

## §4 — Intelligence Depth (Honest, Not Overclaimed)

### 4.1 What It Is

The buyer thinks: "How much does the system know about this
supplier?" Intelligence depth answers honestly — PER METRIC, not
as a single inflated badge.

```
Intelligence Depth: ████████░░ Deep
  4 of 6 metrics past threshold

  ██ exception_rate:      Deep (150 decisions)
  ██ accuracy:            Deep (150 decisions)
  ██ category_mix:        Reliable (72 decisions)
  ██ quarterly_volume:    Developing (35 decisions)
  ░░ trend:               Emerging (12 decisions — needs 50)
  ░░ lead_time_pattern:   No data (0 decisions)
```

### 4.2 Why Not max()

Using max(source_count) across all metrics creates a subtle
overclaim: a supplier with 150 decisions on exception_rate and
2 on everything else displays "Deep (150)" — the badge implies
broad knowledge when the system really knows ONE thing deeply.
This is the fixture-as-real class of risk laundered through an
aggregation function.

### 4.3 Honest Depth Computation

The headline tier reflects BREADTH of deep knowledge:

```python
DEPTH_THRESHOLDS = {
    "s2p":        [0, 20, 50, 100],
    "soc":        [0, 50, 100, 200],
    "purchasing": [0, 10, 20, 50],
}

def intelligence_depth(self, enrichment: dict[str, ProvenancedValue],
                       domain: str = "s2p") -> dict:
    thresholds = DEPTH_THRESHOLDS.get(domain, [0, 20, 50, 100])

    # Per-metric depth
    metric_depths = {}
    for name, pv in enrichment.items():
        count = pv.source_count if hasattr(pv, 'source_count') else 0
        if count == 0: tier = "none"
        elif count < thresholds[1]: tier = "emerging"
        elif count < thresholds[2]: tier = "developing"
        elif count < thresholds[3]: tier = "reliable"
        else: tier = "deep"
        metric_depths[name] = {"tier": tier, "count": count}

    # Headline = breadth of reliable+ knowledge
    total = len(metric_depths)
    past = sum(1 for m in metric_depths.values()
               if m["tier"] in ("reliable", "deep"))
    has_deep = any(m["tier"] == "deep" for m in metric_depths.values())

    if total == 0: headline = "none"
    elif past == 0: headline = "emerging"
    elif past < total // 2: headline = "developing"
    elif past == total and has_deep: headline = "deep"
    elif past == total: headline = "comprehensive"  # all reliable, none deep
    else: headline = "reliable"

    return {
        "headline_tier": headline,
        "metrics_past_threshold": past,
        "metrics_total": total,
        "per_metric": metric_depths,
        "label": f"{past} of {total} metrics past threshold"
    }
```

---

## §5 — Risk Tier (Learned vs Context)

### 5.1 The Differentiator

Risk tier carries its BASIS — learned vs context. This is the
product differentiator. Every competitor shows a supplier risk
score. No competitor shows WHERE the risk assessment comes from.

```
Risk: HIGH
Basis: learned (150 verified decisions)
  ██ exception_rate: 15% (rising since Q2)
  ██ accuracy: 78% (below category average)
```

vs.

```
Risk: MONITOR
Basis: context only (integration pending)
  ░░ OTIF: 88% (fixture — ERP integration pending)
  ░░ lead_time: 6.2 days (invoice context)
```

### 5.2 Tier Rules

| Tier | Requirement | What it means |
|---|---|---|
| HIGH | Learned + sufficient sample (source_count ≥ N_min) + exception_rate > 0.12 OR accuracy < 0.80 OR trend = deteriorating | "Verified evidence: this supplier is risky" |
| MEDIUM | Learned + limited sample (0 < source_count < N_min) with negative signals | "Evidence suggests risk but sample is limited" |
| LOW | Learned + sufficient sample + exception_rate < 0.07 AND accuracy > 0.85 | "Verified evidence: this supplier performs well" |
| MONITOR | Context signals flag something but NO learned data available | "Context suggests attention — verify with decisions" |
| INSUFFICIENT_DATA | 0 < source_count < N_min (S2P: N_min=20) | "Not enough verified history to assess risk" |
| INTEGRATION_PENDING | No P39B enrichment at all for this supplier | "Supplier intelligence not yet available" |

**Key rule:** MEDIUM requires SOME learned data (source_count > 0).
It is not a "mixed learned + context" tier — context SUPPLEMENTS
the assessment narrative but does not DRIVE the tier assignment.
A supplier with zero verified decisions and concerning OTIF fixture
data gets MONITOR, not MEDIUM.

### 5.3 What Context CANNOT Do

Context values can produce MONITOR or INTEGRATION_PENDING. They
cannot produce HIGH, MEDIUM, or LOW. Learned-confidence risk tiers
require verified outcomes.

```
FORBIDDEN:
  risk_tier: HIGH
  basis: "OTIF 88% from fixture data"
  
CORRECT:
  risk_tier: MONITOR
  basis: "context — OTIF 88% from fixture, ERP integration pending"
```

---

## §6 — What the System Caught (Then Exposure)

### 6.1 Lead With Caught, Not Gross Exposure

"~$87K exception exposure" is the CFO-magnet — and the most
attacked number in the room. "Exposure to what? Most of those
exceptions were resolved fine."

The smaller, bulletproof number is what the system CAUGHT:

```
What the system caught (last quarter):
  ██ 12 real discrepancies confirmed by your team
     involving $148,800 in flagged invoice value
     caught because the system learned Chen-Lin's pattern

  Definition: caught = verified decisions where
    action ∈ {flag_leakage, hold_for_review, escalate_compliance}
    AND is_correct == True (analyst confirmed the flag was right)
  
  This is NOT all exceptions. It's exceptions the system flagged
  AND the analyst verified as genuine. The count is bulletproof.

Context: total exception exposure
  47 invoices × 15% exception rate × $12,400 avg = ~$87,420

  Source breakdown:
    ██ 47 invoices:    learned (decisions scored for this supplier)
    ██ 15% exception:  learned (from P39B verified decisions)
    ░░ $12,400 avg:    context (from invoice fixture amounts)

  → Connect ERP and we quantify the full exposure, not just
    what we caught.
```

The "caught" number is smaller, verified, MORE differentiated
(it's the compounding catch — no competitor can show it), and
sidesteps the F-19 trap entirely. The exposure figure stays as
context for the CFO escalation path.

### 6.2 What R18 Cannot Claim

| Claim | Status | Why |
|---|---|---|
| "Exception exposure ~$87K" | **ALLOWED** (with provenance breakdown) | Math is defensible, sources are labeled |
| "$87K recovered" | **FORBIDDEN** | Recovery requires action, not just detection |
| "$523K annual savings" | **FORBIDDEN** | Requires R16/P46 cost-impact model |
| "Confirmed leakage" | **FORBIDDEN** | "Leakage exposure" is defensible; "confirmed" requires audit |
| "ROI: 340%" | **FORBIDDEN** | Requires verified baseline + verified savings |

### 6.3 Why This Is Still Valuable

The buyer doesn't need "confirmed savings" at R18. The buyer needs:
"This supplier's exception rate is rising and the exposure is
material." That's an actionable intelligence signal that no
competitor provides from verified operational decisions.

The provenance breakdown IS the upgrade pitch: "Connect your ERP
and the $12,400 average becomes verified. The exposure calculation
becomes fully learned."

---

## §7 — The Demo Moment

### 7.1 The Story Arc (Discovery-First)

```
Act 1: DISCOVERY (the hook)
  "You've been wondering about Chen-Lin. Here's the receipts."
  → Intelligence depth: Deep (4 of 6 metrics)
  → What the system caught: 12 confirmed discrepancies

Act 2: EVIDENCE (the proof)
  "Here's exactly what it learned, and what it hasn't."
  → ██ learned metrics with per-metric depth
  → ░░ context metrics = your upgrade roadmap
  → "Connect ERP and these become verified"

Act 3: RISK (the action)
  "Chen-Lin is deteriorating. Here's the evidence."
  → Risk: HIGH (learned — 150 verified decisions)
  → exception_rate rising 8% → 15% over three quarters
  → The category manager can ACT on this today

Act 4: PORTFOLIO (the ambition — even before it's built)
  "Across your 200 suppliers, the system has identified 12
  that are deteriorating — ranked by verified evidence depth."
  → This is the money shot: the category manager's actual job
     is triage the supplier base
  → Even if v1 is single-supplier, SHOW the portfolio vision

Act 5: RETENTION (the moat-closer)
  "When your AP analyst leaves, all of this stays."
  → 150 decisions worth of supplier intelligence persists
  → The new category manager sees this on Day 1
```

Note: retention (Act 5) is the moat-closer for the economic buyer,
not the opening hook. Discovery (Act 1) is the gain and the gut-
confirmation that moves budget.

### 7.2 Portfolio Ambition (Design Now, Build in R18B)

Single-supplier is the v1 detail shot. The portfolio ranking is
the money shot:

```
Supplier Risk Dashboard (portfolio view — R18B)

Highest-risk suppliers ranked by learned evidence:

  1. Chen-Lin Electronics    HIGH   ████████░░  12 caught
  2. Pacific Components      HIGH   ██████░░░░   8 caught
  3. Sunrise Materials        MED   ████░░░░░░   3 caught
  ...
  
  15 suppliers deep   │ 32 developing │ 153 emerging
```

**Design the response shape in R18A so portfolio is a trivial
extension.** The `SupplierIntelligenceProfileResponse` structure
works identically for single-supplier (full detail) and portfolio
(summary list). Don't let "single-supplier v1" become a ceiling.

### 7.3 Product Integrity Demo Storyboard Update

Add to S2P demo story in Product Integrity v2.4 §5.1:

```
S2P: Invoice exception → explain (with provenance) → verify →
     conservation proof → auto-approve advisory →
     SUPPLIER INTELLIGENCE PROFILE

     "After 150 verified decisions, the system caught 12 real
     discrepancies at Chen-Lin. Intelligence depth: Deep (4 of 6
     metrics). Risk: HIGH (learned, not inferred). When your
     category manager leaves, this intelligence stays."
```

---

## §8 — Metric Policy

### 8.1 Learned / Verified Metrics (██)

Only from verified outcomes or P39B verified enrichment:

| Metric | Source | Status |
|---|---|---|
| verified_decision_count | P39B | learned |
| accuracy | P39B (verified decisions only) | learned |
| exception_rate | P39B (verified decisions only) | learned |
| category_distribution | P39B (verified decisions) | learned |
| decision_count_by_quarter | P39B (verified history) | learned |
| trend | P39B (with sufficient verified history) | learned |

### 8.2 Context / Fixture Metrics (░░)

Allowed but must be labeled:

| Metric | Source | Status |
|---|---|---|
| supplier identity | fixture/source-system | context |
| supplier category | fixture | context |
| OTIF | fixture | context (integration pending) |
| contractual lead time | supplier fixture | context |
| actual lead time (P36) | invoice dates | context (not receipt-verified) |
| payment terms | supplier fixture | context |
| average invoice amount | invoice fixture | context |

### 8.3 Unavailable / Deferred

| Metric | Status | What's needed |
|---|---|---|
| production OTIF | unavailable | ERP/GR/logistics integration |
| ERP-verified lead time | unavailable | verified delivery/receipt |
| external financial health | unavailable | connector integration |
| quality defects / returns | unavailable | outcome-backed data |
| precise dollar savings | deferred | R16/P46 cost-impact model |

---

## §9 — Execution Plan

### 9.1 Scope: R18A (API) + R18B (UI) Split

| Phase | What | Effort | Deliverable |
|---|---|---|---|
| R18A | API composer + intelligence depth + risk tier + economic exposure | 1-2d | Backend service + tests + additive endpoint fields |
| R18B | UI surface + provenance badges + demo storyboard | 1d | Frontend panel + Playwright E2E |

R18A ships first. R18B only if Roadmap declares R18 a demo
milestone (recommended: yes).

### 9.2 R18A Implementation

**Repo:** s2p-copilot

**Files to create:**

```
backend/app/services/supplier_intelligence.py
  - SupplierIntelligenceComposer
  - intelligence_depth() → headline_tier + per_metric + label
  - risk_tier() → tier + basis + contributing_metrics
  - caught_discrepancies() → count + flagged_value + source
  - economic_exposure() → amount + source_breakdown + caveats
  - trajectory_projection() → weeks_to_each_tier (if count > 0)
  - compose_profile(supplier_id) → SupplierIntelligenceProfileResponse
  - new_manager_summary() → template-based string (NOT LLM)

backend/tests/test_supplier_intelligence.py
  - Full test gates from §9.4
```

**Files to modify:**

```
backend/app/routers/s2p_suppliers.py
  - Stage 1 (discovery): read the existing profile endpoint response
    shape BEFORE modifying. Run:
    curl -s localhost:8002/api/s2p/suppliers/{known_id}/profile | python -m json.tool
    Record the current response fields. R18 adds to them additively.
  - Extend GET /api/s2p/suppliers/{supplier_id}/profile
  - Add intelligence block to response (see §9.3 JSON shape)
  - Existing fields unchanged (additive only)

backend/app/main.py
  - NO new router mount (v1 extends existing route)
```

**new_manager_summary generation (template-based):**

```python
def new_manager_summary(self, supplier_name, depth, risk,
                        caught, exposure) -> str:
    parts = [f"{supplier_name}"]
    if depth['metrics_past_threshold'] > 0:
        parts.append(f"has {depth['label']} "
                     f"({depth['metrics_past_threshold']} of "
                     f"{depth['metrics_total']} metrics)")
    else:
        parts.append("has no operational intelligence yet")
    if caught and caught.get('count', 0) > 0:
        parts.append(f"{caught['count']} confirmed discrepancies caught")
    if risk['tier'] in ('high', 'medium', 'low'):
        parts.append(f"Risk: {risk['tier'].upper()} ({risk['basis']})")
    return ". ".join(parts) + "."
```

**Files NOT modified:**

```
backend/app/services/s2p_enrichment.py      — P39B, consumed not modified
backend/app/services/s2p_context_builder.py — P38, unchanged
copilot_sdk/graph/enrichment.py             — P39A, unchanged
copilot_sdk/graph/graph_store.py            — unchanged
```

### 9.3 Response JSON Shape

**v1: Extend existing endpoint additively.**

```
GET /api/s2p/suppliers/{supplier_id}/profile

Response (existing fields preserved + new fields added):
{
  // Existing fields — unchanged
  "supplier_id": "chen-lin-electronics",
  "supplier_name": "Chen-Lin Electronics",
  ...existing profile fields...

  // NEW: R18 intelligence block (additive)
  "intelligence": {
    "depth": {
      "headline_tier": "deep",
      "metrics_past_threshold": 4,
      "metrics_total": 6,
      "label": "4 of 6 metrics past threshold",
      "per_metric": {
        "exception_rate": {"tier": "deep", "count": 150},
        "accuracy": {"tier": "deep", "count": 150},
        "category_mix": {"tier": "reliable", "count": 72},
        "quarterly_volume": {"tier": "developing", "count": 35},
        "trend": {"tier": "emerging", "count": 12},
        "lead_time_pattern": {"tier": "none", "count": 0}
      },
      "trajectory": {
        "trend_reliable": "~6 weeks at current volume",
        "trend_deep": "~4 months at current volume"
      }
    },
    "risk": {
      "tier": "high",
      "basis": "learned",
      "basis_detail": "150 verified decisions",
      "contributing_metrics": [
        {"metric": "exception_rate", "value": 0.15, "source": "learned",
         "trend": "rising", "source_count": 150},
        {"metric": "accuracy", "value": 0.78, "source": "learned",
         "source_count": 150}
      ]
    },
    "caught": {
      "count": 12,
      "flagged_invoice_value": 148800,
      "currency": "USD",
      "source": "verified_outcomes",
      "label": "12 real discrepancies confirmed by your team"
    },
    "behavioral_metrics": {
      "learned": {
        "exception_rate": {"value": 0.15, "source": "verified_outcomes",
                           "source_count": 150, "trend": "rising"},
        "accuracy": {"value": 0.78, "source": "verified_outcomes",
                     "source_count": 150},
        "category_distribution": {"value": {...}, "source": "verified_outcomes",
                                   "source_count": 150}
      },
      "context": {
        "otif": {"value": 0.88, "source": "fixture",
                 "label": "connect ERP to verify"},
        "lead_time_days": {"value": 6.2, "source": "fixture",
                           "label": "connect logistics to verify"},
        "payment_terms": {"value": "Net 30", "source": "fixture",
                          "label": "connect AP system to verify"}
      },
      "unavailable": ["erp_verified_lead_time", "quality_defects"]
    },
    "economic_exposure": {
      "last_quarter": {
        "amount": 87420,
        "currency": "USD",
        "computation": "47 decisions × 15% exception × $12,400 avg",
        "source_breakdown": {
          "decision_count": {"value": 47, "source": "learned"},
          "exception_rate": {"value": 0.15, "source": "learned"},
          "avg_invoice_amount": {"value": 12400, "source": "context"}
        },
        "caveat": "Invoice amounts are context data. Connect ERP for verified amounts."
      }
    },
    "new_manager_summary": "Chen-Lin Electronics has 4 of 6 metrics past threshold. 12 confirmed discrepancies caught. Risk: HIGH (learned)."
  }
}
```

**Design note:** This response shape works identically for single-
supplier (full detail) and portfolio listing (summary with subset
of fields). R18B portfolio view returns an array of these objects
with only depth/risk/caught at the top level.

Portfolio summary fields (always present, even when sparse):
```json
"portfolio_summary_fields": [
  "depth.headline_tier",
  "depth.metrics_past_threshold",
  "risk.tier",
  "risk.basis",
  "caught.count"
]
```

**Deferred to R18B or later:**

```
GET /api/s2p/suppliers/profiles        — collection/portfolio view
GET /api/s2p/suppliers/compare         — side-by-side comparison
```

### 9.4 R18A Test Gates

**Composer tests:**

- Per-metric depth returns correct tier for each threshold boundary
- Headline tier reflects breadth ("4 of 6") not peak (max)
- Headline "deep" requires ALL metrics past threshold
- Headline "none" when no enrichment exists
- Trajectory projection computes weeks from current count + rate
- Trajectory returns empty when count=0 or rate=0
- Risk tier requires verified metrics for HIGH/MEDIUM/LOW
- Risk tier returns MONITOR for context-only signals
- Risk tier returns INSUFFICIENT_DATA when some learned data < N_min
- Risk tier returns INTEGRATION_PENDING when no P39B enrichment
- Risk tier basis field distinguishes learned from context
- Caught discrepancies count from verified confirmed exceptions
- Caught returns zero/absent when no verified exceptions exist
- Economic exposure computation correct (learned × context)
- Economic exposure labeled with source breakdown
- Economic exposure returns null when insufficient data
- Composer falls back to fixture when no enrichment persisted
- Composer preserves ProvenancedValue provenance through composition
- new_manager_summary template generates correctly from depth + caught + risk

**Endpoint tests:**

- Existing profile fields unchanged (backward compatible)
- **Regression: profile response WITHOUT enrichment is identical
  to pre-R18 response (save pre-R18 output as fixture, compare)**
- Intelligence block added when enrichment available
- Intelligence block absent or minimal when no enrichment
- Supplier not found → safe response (existing behavior)
- Unknown supplier → safe response (not 500)

**Provenance tests:**

- No fixture value claims measured=True or verified=True
- No context metric produces HIGH/MEDIUM/LOW risk tier
- Learned metrics carry source_count
- Caught count derived from verified outcomes only
- Economic exposure shows source_breakdown with provenance per component
- OTIF labeled as fixture + "connect ERP to verify" (never measured)
- Lead time labeled as context + "connect logistics to verify"
- Per-metric depth shows tier per metric, not inflated aggregate

**Compatibility tests:**

- P39B enrichment endpoints unchanged
- P38 context builder unchanged
- P37 trust explanation unchanged
- P35 evidence templates unchanged
- Existing supplier profile response backward compatible

### 9.5 R18A Codex Prompt Template

```
WORKING DIRECTORY: s2p-copilot
ACTIVATE:
  & "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"
TASK: Implement R18A — S2P Supplier Intelligence Profile Composer.
TASK TYPE: New service + endpoint extension + tests.

Read r18_supplier_intelligence_profile (current version in
docs/design/) §2 (architecture), §4 (depth), §5 (risk tier),
§6 (caught), §9.3 (response JSON shape).

Stage 1 (discovery — do this FIRST):
  1. Find the existing profile endpoint and its response shape:
     grep -rn "suppliers.*profile\|supplier_id.*profile" \
       backend/app/routers/ --include="*.py"
     Read the route handler. Record current response fields.

  2. Find the existing supplier profile accumulator:
     grep -rn "SupplierProfile\|accumulator\|supplier.*accum" \
       backend/app/services/ --include="*.py"

  3. Verify P39B enrichment is available:
     grep -rn "read_entity_enrichment" \
       backend/app/ --include="*.py"

  4. CRITICAL — Discover actual S2P action names:
     grep -rn "actions_list\|DomainAction\|action.*id" \
       backend/app/ --include="*.py"
     The "caught" definition uses action ∈ {flag_leakage,
     hold_for_review, escalate_compliance}. These MUST match
     the actual S2P action taxonomy. If actual action IDs differ,
     map canonical S2P actions to "caught" categories. Do NOT
     hardcode action names that don't exist in the codebase.

Create:
  backend/app/services/supplier_intelligence.py
    - SupplierIntelligenceComposer(graph_store, accumulator, fixture)
    - intelligence_depth(enrichment, domain) → per-metric depth
    - risk_tier(enrichment) → tier + basis + contributing_metrics
    - caught_discrepancies(enrichment) → count + flagged_value
    - economic_exposure(enrichment, fixture) → amount + breakdown
    - trajectory_projection(depth, weekly_rate) → weeks per tier
    - new_manager_summary(name, depth, risk, caught) → string
    - compose_profile(supplier_id) → response dict

  backend/tests/test_supplier_intelligence.py
    - Test gates from §9.4 (all categories)

Modify:
  backend/app/routers/s2p_suppliers.py
    - Extend existing profile endpoint response
    - Add "intelligence" block (§9.3 JSON shape)
    - Existing fields UNCHANGED

NON-NEGOTIABLES:
  - Read-only composer. No writes. No new enrichment pipeline.
  - No raw sqlite3. No GraphStore protocol changes.
  - No scorer factor feedback. No conservation/DK mutation.
  - Fixture values CANNOT claim measured/verified (type guards).
  - Context metrics CANNOT produce HIGH/MEDIUM/LOW risk tier.
  - Per-metric depth, not max(). "4 of 6" not "Deep (150)".
  - Headline "deep" requires at least one metric at deep tier.
  - Caught actions MUST match actual S2P action taxonomy
    (discovered in Stage 1, step 4). Do not hardcode guesses.
  - BACKWARD COMPATIBILITY IS THE #1 TEST: save pre-R18 profile
    response as fixture baseline. Assert existing fields are
    IDENTICAL (same keys, same types, same values) when no
    enrichment exists. The new "intelligence" block may be absent
    or contain minimal content — but existing fields must not
    change in any way. If this test fails, R18 broke integrations.

RUN (Codex scope — automated tests only):
  pytest tests/test_supplier_intelligence.py -v --timeout=60
  pytest tests/ -q --timeout=120

EXIT: All tests pass. Backward compat test passes. Zero existing
test regressions.
```

### 9.6 R18A Manual / Live Validation (NOT Codex)

**Run manually after Codex completes R18A:**

```powershell
# Activate
& "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\proj-envs\python_expts_venv\Scripts\Activate.ps1"
cd s2p-copilot

# Start S2P backend
python demo.py --s2p --no-browser

# In a separate terminal:
# 1. Verify profile endpoint returns intelligence block
curl -s localhost:8002/api/s2p/suppliers/{known_id}/profile | python -m json.tool

# 2. Verify existing fields unchanged
# Compare against saved pre-R18 baseline

# 3. Verify intelligence block structure
# Check: depth.headline_tier, depth.per_metric, risk.tier,
#         risk.basis, caught.count, behavioral_metrics,
#         economic_exposure, new_manager_summary

# 4. Verify no-enrichment fallback
# Use a supplier_id with no enrichment — intelligence block
# should be absent or minimal, existing fields identical
```

### 9.7 R18B Implementation (Immediately After R18A Validation)

**Timing decision: R18A first, R18B immediately after API validation.**
R18B is not a separate future phase — it ships in the same batch.
The depth bar and provenance badges ARE the demo moment; deferring
them would ship the intelligence without the visual that sells it.

Frontend changes:

- Intelligence depth progress bar / tier badge
- Provenance badges (██ learned / ░░ context)
- Risk tier with basis callout
- Economic exposure with source breakdown
- "What improves with ERP integration" callout
- new_manager_summary display

Playwright E2E:

- Profile shows intelligence depth tier
- Profile shows learned metrics with ██
- Profile shows context metrics with ░░
- Profile shows risk tier with basis
- Profile shows economic exposure with source breakdown
- Profile degrades gracefully with no enrichment

---

## §10 — Product Integrity

### 10.1 Provenance Rules

Every metric on the profile carries provenance. The provenance
rendering makes compiled intelligence VISIBLE:

```
██ = learned from verified decisions (the moat)
░░ = context data (integration pending — upgradeable)
```

### 10.2 FORBIDDEN (additions to Product Integrity registry)

| ID | Forbidden | Correct alternative |
|---|---|---|
| F-16 | Fixture OTIF presented as measured supplier performance | OTIF labeled context / integration pending |
| F-17 | Invoice-context lead time presented as verified delivery | Lead time labeled context / invoice dates |
| F-18 | Context-only signals producing HIGH/MEDIUM/LOW risk tier | Context → MONITOR or INTEGRATION_PENDING |
| F-19 | Economic exposure presented as "confirmed savings" or "ROI" | "Exception exposure" with mixed-source breakdown |
| F-20 | Intelligence depth from unverified decisions | Depth = verified decision count only |

### 10.3 CANONICAL (additions)

| ID | Approved claim | Evidence |
|---|---|---|
| C-15 | "The system knows your supplier from YOUR team's decisions" | Intelligence depth tier from verified count |
| C-16 | "When your AP analyst leaves, supplier intelligence stays" | Profile persists via P39B enrichment |
| C-17 | "Risk assessment from verified evidence, not static rules" | Risk tier basis = learned |
| C-18 | "Connect your ERP and context becomes verified" | Provenance upgrade path visible |

---

## §11 — What R18 Changes in Existing Documents

| Document | Change | Priority |
|---|---|---|
| Product Integrity v2.4 | Add F-16..F-20, C-15..C-18, update S2P demo storyboard | P2 |
| cga_entity_enrichment_loop v1.5 | Cross-reference R18 as the display layer for entity enrichment (the 7th scoring pathway is now buyer-visible) | P2 |
| innovation_note v6 → v7 | R18 makes entity intelligence buyer-visible | P2 |
| cga_arxiv_short | No change (R18 is product, not research) | None |
| MAP | R18 = narrative milestone, not feature checkbox | P1 |
| S2P copilot design | Add Supplier Intelligence Profile section | P2 |

---

## §12 — Roadmap Decisions (Answer Before Implementation)

| # | Question | Recommended answer |
|---|---|---|
| 1 | API-only or API + UI? | **API + minimal UI** — intelligence depth bar + provenance badges ARE the demo moment |
| 2 | Rename to Supplier Intelligence Profile? | **Yes** — "Intelligence Profile" signals compiled knowledge |
| 3 | Extend existing endpoint or new route? | **Extend existing** `/suppliers/{id}/profile` — additive. Backward compat means: existing response keys, types, and values are IDENTICAL with or without enrichment. The new `intelligence` block is ADDED (not replacing existing fields). When no enrichment exists, `intelligence` may be absent entirely OR present with minimal content (depth: none, risk: integration_pending). Tests assert existing fields match a saved pre-R18 fixture baseline. |
| 4 | Compare/collection now or defer? | **Defer to R18B** — single-supplier is the v1 demo |
| 5 | P39B sufficient? | **Yes** — shipped, tested, type guards enforced |
| 6 | Risk tier from context? | **MONITOR/INTEGRATION_PENDING only** — learned-confidence requires verified |
| 7 | Lead-time in v1? | **Yes, as context** — the ░░ label IS the upgrade pitch |
| 8 | OTIF in v1? | **Yes, as context** — show what you have, label what you don't |
| 9 | R18A/R18B split? | **Yes** — API first, UI if demo-critical |
| 10 | MAP narrative milestone? | **Yes** — first time entity intelligence is buyer-visible |

---

## §13 — Execution Summary

```
Pre-work (Roadmap):
  Answer §11 questions → approve design plan

R18A (1-2d):
  SupplierIntelligenceComposer (read-only facade)
  Intelligence depth, risk tier, economic exposure
  Extend existing profile endpoint (additive)
  Tests: composer + endpoint + provenance + compatibility

R18B (1d, if demo-critical):
  UI surface: depth bar, provenance badges, risk basis
  Playwright E2E
  Demo storyboard integration

Zero GraphStore changes. Zero scorer changes. Zero new enrichment.
Consumes P39B. Labels everything honestly.
```

---

## Document Control

| Version | Date | Change |
|---|---|---|
| v1.0 | June 14, 2026 | Initial design. Intelligence depth concept. Risk tier with learned/context basis. Economic exposure with mixed-source breakdown. Demo storyboard. Composer architecture over P39B + P36 + fixture. Metric policy. Endpoint strategy (extend existing, additive). R18A/R18B split. 5 FORBIDDEN + 4 CANONICAL additions. 11 roadmap questions with recommendations. |
| v1.2 | June 14, 2026 | **Product-shape review applied (6 suggestions).** (1) Demo inverted to discovery-first: "you've been wondering about Chen-Lin" not "when Rosa leaves." Retention moved to Act 5 moat-closer. (2) §3 Journey section added: cold-start → deep as engagement mechanic, trajectory projection ("Deep in ~4 months"), pilot import bridge, Day-1 screen design. (3) Intelligence depth changed from max(source_count) to per-metric breadth ("4 of 6 metrics past threshold") — max() was overclaim laundered through aggregation. (4) Economic section reframed: lead with "12 confirmed discrepancies caught" (bulletproof), exposure as context for CFO escalation. (5) Portfolio ambition added to demo (Act 4) and response shape design note — single-supplier v1 but portfolio is the money shot. (6) Primary persona declared: category/procurement manager. CFO exposure = escalation ammunition, not centerpiece. ░░ context items reframed as upsell map ("connect X to verify"). |
| v1.3 | June 15, 2026 | **Made executable for Codex.** All subsection numbers fixed (were 10.x, now match parent §). §9.2: composer methods updated for new concepts (caught_discrepancies, trajectory_projection, per-metric depth). §9.3: response JSON shape rewritten — per-metric depth, caught block, trajectory projections, context labels as "connect X to verify" upsell map, portfolio-ready structure noted. §9.4: test gates expanded for per-metric depth (headline reflects breadth not peak), caught (verified only), trajectory, and cold-start regression. §9.5: Codex prompt template added (paste-ready with WORKING DIRECTORY, VENV, discovery step, NON-NEGOTIABLES). §7.3: demo storyboard updated ("12 caught discrepancies" not "$87K exposure"). new_manager_summary template updated for depth.metrics_past_threshold (not depth.count). |
| v1.4 | June 15, 2026 | **A+ review — 3 corrections + 4 suggestions applied.** (1) Codex prompt: venv activation path added. (2) Headline logic: "deep" requires ≥1 metric at deep tier; all-reliable-but-none-deep = "comprehensive." (3) Caught: precise definition — verified decisions where action ∈ {flag_leakage, hold_for_review, escalate_compliance} AND is_correct == True. (4) Accumulator label: "computed from decision history (not outcome-verified)" — distinguishes from both fixture and learned. (5) Backward compat promoted to #1 NON-NEGOTIABLE in Codex prompt. (6) Portfolio summary fields documented in §9.3 response shape. (7) INSUFFICIENT_DATA threshold specified: 0 < source_count < N_min (S2P: N_min=20). |
| v1.5 | June 15, 2026 | **Review guidance supplement (7 items).** (1) Version header fixed (was 1.0, now 1.5). (2) Codex prompt split: automated tests in §9.5, manual/live validation in §9.6 (Codex does not own server orchestration). (3) Venv: canonical `python_expts_venv` activation path, removed `.venv` reference. (4) S2P action taxonomy discovery step added to Stage 1 (step 4): caught action names must match actual codebase, not hardcoded guesses. (5) Analyst count and time-span marked optional — show only when source fields exist in decision metadata. (6) Backward compatibility sharpened: existing keys/types/values IDENTICAL; intelligence block absent or minimal when no enrichment. (7) R18B timing decided: immediately after R18A validation, same batch (not a separate future phase). §9.5→§9.7 renumbered (was duplicate §9.5). |
