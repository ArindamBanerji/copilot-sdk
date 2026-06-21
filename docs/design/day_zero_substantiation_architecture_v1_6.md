# Day-Zero Substantiation Architecture — Cross-Copilot Framework

**Version:** 1.6
**Date:** June 19, 2026
**Status:** Design — for roadmap + llm-judge iteration
**v1.6 adds (execution layer):** P39A/P39B are SHIPPED (instance-2 is new scope, not an
amendment); session/repo mapping (P-SUBST-CORE + commodity + PUR-audit are Session-A
copilot-sdk work, not "no overlap"); P-FIXTURE-LABEL-AUDIT split per-repo per-session;
Class-A dependency chain (audit → K4 connector → P68/P72 re-source) with explicit fix
prompts; §17 declaration placed in Stage 2 + Stage 3 checklist + Playbook §3.12; Class B
reframed as ClaimRegistry population (data entry, not prompt edits); P-SOC-ORACLE-PLUMB
Session-C sequencing.
**Applies to:** all copilots (SOC, S2P, Trading, Purchasing, DataOps)
**Anchors:** γ theorem audit (synthetic_data_generation_v2), campaign holdout/oracle
(soc_campaign_v6 + narrative_evaluation_v2), product_integrity_execution_strategy_v2_4
(FORBIDDEN/CANONICAL + ██/░░)

---

## Part 0 — Thesis (the narrative this architecture encodes)

The market changed: customers now expect **day-zero readiness** — a product that works
and substantiates its claims before their data exists. Much of this is hype, but it's the
expectation we sell into. The temptation it creates is to manufacture readiness with
LLM-persona data.

The γ audit is the standing proof of why that's fatal, and it draws the line this whole
architecture is built around. META-4 didn't fail on prompt quality; it failed because the
**LLM competence prior IS the data-generating mechanism** — so a synthetic stream measures
the simulator, not the system. That's an identifiability result, not a tooling gap, and it
generalizes to every copilot:

> **Synthetic / LLM-persona data can substantiate *capability* and *mechanism*. It
> structurally cannot substantiate the *magnitude* of a behavioral or learning effect that
> depends on the real agent.** "Does the system form campaigns / surface enrichment /
> re-converge" — simulable. "Does it change *this* analyst's behavior by X%, is *this*
> firm's γ = 4" — never simulable, by the same argument that retired META-4.

So day-zero readiness is not "the magnitude claim is proven on day zero." It is an **arc**:
on day zero the product is **populated** (real external data), **proven** (analytic claims),
and **instrumented** (a validated measurement pipeline, pre-wired and labeled); then, over
the first weeks of real use, the customer's own decisions convert estimate→measured and
░░context→██learned, and the instrument reports *their* magnitude.

That arc *is* the compounding thesis delivered honestly — and in a market about to fill
with synthetic-data overclaimers who fail technical diligence, **the honest day-zero arc is
the position that survives.** Honesty is the moat, precisely because the magnitude number
is the thing no one can fake without getting caught.

This document turns that into a build discipline that works for all five copilots.

---

## Part 0.1 — The narrative, up front (what we actually say)

The commercially load-bearing content leads, so no one has to read the type theory to reach
the payoff.

**The day-zero arc pitch:**
> "Day one you get a working product populated with real data and a mathematically proven
> mechanism, with the measurement instrument already running and labeled. As your team
> operates, context becomes learned and we measure the lift on *your* data with the
> instrument you can see today. The one thing nobody can hand you on day one is *your*
> magnitude number — anyone who claims to is showing you synthetic data."

**The one-liner:** *Day-zero readiness = scraped-real context (░░) + analytic proof + a
validated instrument; magnitude is pre-committed and instrumented, never synthesized.*

**Honesty as moat:** in a market filling with synthetic-magnitude overclaimers, the four-tier
arc is the position that survives a buyer's technical advisor asking "where did that number
come from." This is the "measurement is the asset / stay advisory" logic scaled to strategy.

**What we may say at each tier** (the gate behind every public claim — `ClaimRegistry.sales_safe`):

| Tier | Honest language |
|---|---|
| **T-A Analytic** | "Proven mathematically that the mechanism holds (conditions stated); magnitude measured on your data at pilot." |
| **T-S Scraped (░░)** | "Populated day-zero with real external data, labeled context (░░) vs learned (██) — it becomes yours as your team operates." |
| **T-O Oracle** | "The capability runs and the measurement instrument is validated to detect the effect — wired in and visible today." |
| **T-R Real (██)** | "Measured on your operations: \<magnitude\> (verified decisions)." |

Everything below is the discipline that makes these four lines *true*. (Detail and
publication anchors: Part 6 + Part 12.)

---

## Part 1 — The four substantiation tiers

Every commercial claim is substantiated by exactly one tier. The tiers differ in what they
*can* prove, and the bright line runs between T-O and T-R.

| Tier | Source | Substantiates | Does NOT substantiate | ██/░░ |
|---|---|---|---|---|
| **T-A Analytic** | Math proof / theorem (math poll) | Existence + direction + a *bound* on an effect, day-zero | A specific realized magnitude for a given customer | — |
| **T-S Scraped/External** | Real external data (feeds, filings, market data, catalogs) — **real, just not customer-specific** | A populated, real day-zero product; context claims | "Learned from YOUR operations" | ░░ context |
| **T-O Oracle-Synthetic** | Parametric oracle + synthetic stream | **Capability** ("the mechanism runs") + **pipeline validity** ("the instrument detects a known injected effect") | **Any magnitude of a real-agent effect** (the META-4 line) | — |
| **T-R Real-Measured** | Customer's verified decisions (pilot+) | Customer-specific magnitude; learned intelligence | (nothing pulled forward — only source of T-R is real use) | ██ learned |

**The two fixes this table bakes in:**

1. **Scraped ≠ synthetic.** T-S is *real data* — it just isn't this customer's operational
   history. Conflating "scraped" with "LLM-persona" is how you back into META-4 under market
   pressure. T-S populates a genuinely real day-zero product (the ░░ tier); T-O populates a
   *demonstration*, never a claim of magnitude. Keep them separate tiers.
2. **T-O is capability + pipeline only.** The oracle validates that the instrument detects a
   *known injected* effect — never the real effect's size. (This is the campaign-oracle
   scope, corrected.)

```python
# copilot_sdk/substantiation/tiers.py
from enum import Enum
from dataclasses import dataclass, field

class Tier(str, Enum):
    ANALYTIC = "analytic"            # T-A: proof
    SCRAPED  = "scraped_external"    # T-S: real external (░░ context)
    ORACLE   = "oracle_synthetic"    # T-O: capability + pipeline only
    REAL     = "real_measured"       # T-R: customer-verified (██ learned)

# Strict ordering of evidential strength FOR A MAGNITUDE CLAIM.
# Only REAL substantiates customer-specific magnitude. ORACLE/ANALYTIC never do.
_MAGNITUDE_OK = {Tier.REAL}

@dataclass(frozen=True)
class ClaimProvenance:
    """Provenance is part of a claim's identity — like a type at the evidence boundary."""
    claim_id: str
    text: str
    tier: Tier
    evidence_ref: str               # theorem id / data source / oracle test / pilot metric id
    is_magnitude_claim: bool        # does the claim assert a SIZE of a real-agent effect?
    copilot: str                    # soc | s2p | trading | purchasing | dataops
    feature: str

    def is_valid(self) -> tuple[bool, str]:
        if self.is_magnitude_claim and self.tier not in _MAGNITUDE_OK:
            return False, (f"Magnitude claim substantiated only by {self.tier.value}; "
                           f"customer-specific magnitude requires REAL (META-4 line).")
        return True, "ok"
```

---

## Part 2 — The claim-provenance registry (the gate)

This extends the existing FORBIDDEN/CANONICAL registry. Every commercial claim is tagged
with its tier and evidence; the registry enforces the one rule that prevents the
company-killer:

> **No claim may silently migrate to `REAL`.** Promotion to a higher tier requires an
> explicit, evidence-bearing promotion event. A claim's tier is part of its definition —
> the same discipline that kept CC-21 at Tier 2 (analytic) and refused to call it Tier 1
> (real) until EXP-G1.

```python
# copilot_sdk/substantiation/registry.py
from dataclasses import dataclass, field
from .tiers import ClaimProvenance, Tier

@dataclass
class PromotionEvent:
    claim_id: str
    from_tier: Tier
    to_tier: Tier
    evidence_ref: str               # the pilot metric / theorem / oracle test that justifies it
    approved_by: str                # roadmap | llm-judge | named reviewer
    date: str

class ClaimRegistry:
    def __init__(self):
        self._claims: dict[str, ClaimProvenance] = {}
        self._history: list[PromotionEvent] = []

    def register(self, claim: ClaimProvenance) -> None:
        ok, why = claim.is_valid()
        if not ok:
            raise ValueError(f"FORBIDDEN (F-24): {why}  [{claim.claim_id}: {claim.text!r}]")
        self._claims[claim.claim_id] = claim

    def promote(self, ev: PromotionEvent) -> None:
        from dataclasses import asdict
        cur = self._claims[ev.claim_id]
        if ev.to_tier == Tier.REAL and not ev.evidence_ref:
            raise ValueError("Promotion to REAL requires a pilot evidence_ref (no silent migration).")
        # asdict (not cur.__dict__) — robust for frozen dataclasses; Enum members survive intact.
        self._claims[ev.claim_id] = ClaimProvenance(
            **{**asdict(cur), "tier": ev.to_tier, "evidence_ref": ev.evidence_ref})
        self._history.append(ev)

    def sales_safe(self, claim_id: str) -> str:
        """What a claim may honestly say, given its tier (Part 6 maps tier→language)."""
        return TIER_LANGUAGE[self._claims[claim_id].tier]
```

**Registry additions (extends product_integrity v2.4):**

| ID | Type | Statement |
|---|---|---|
| F-24 | FORBIDDEN | Any claim presented at a tier higher than its evidence (esp. ORACLE/ANALYTIC magnitude asserted as REAL) |
| F-25 | FORBIDDEN | Scraped/external data (T-S, ░░) presented as customer-learned (██) |
| C-21 | CANONICAL | "Mechanism proven analytically; magnitude measured on your data at pilot" (T-A + pre-committed T-R) |
| C-22 | CANONICAL | "Populated day-zero with real external data, labeled context vs learned" (T-S, honest ░░/██) |

**F-24 is not a new rule — it is a generalization of one already enforced.** CC-21 (the γ
claim) has been held at **Tier 2 (analytic)** and explicitly refused promotion to **Tier 1
(real)** except via EXP-G1 on pilot data, for 2+ months. That Tier-2→Tier-1 discipline *is*
F-24 applied to a single claim. This framework generalizes that one enforced practice into a
registry gate covering every claim on every copilot. Reviewers should read F-24 as
"institutionalize the CC-21 discipline," not "adopt a new constraint."

---

## Part 3 — The day-zero readiness contract (definition-of-done)

Every **measurement-gated / intelligence feature**, on any copilot, ships day-zero only when
all four layers are present. This is a gate, runnable in CI as a checklist assertion.

```python
# copilot_sdk/substantiation/readiness.py
from dataclasses import dataclass

@dataclass
class DayZeroReadiness:
    feature: str
    copilot: str
    populated: bool        # T-S/T-A present: no blank screens; real external context, labeled ░░
    proven: bool           # T-A claim registered where the mechanism is provable (or N/A, justified)
    instrumented: bool     # T-O validated pipeline pre-wired: holdout assigns, outcome persists,
                           #   lift computable, oracle detects a KNOWN injected effect
    real_path_committed: bool  # T-R defined + pre-wired (decision-node fields, metric, pilot trigger)
    labels_honest: bool    # every surfaced value carries ██ learned / ░░ context / proven / sample

    def gate(self) -> tuple[bool, list[str]]:
        missing = [k for k in ("populated","proven","instrumented",
                               "real_path_committed","labels_honest")
                   if not getattr(self, k)]
        return (not missing), missing
```

**The architectural fix encoded here (from the campaign-oracle review):** `instrumented`
means the *plumbing* is validated — holdout assigns ~the configured %, the outcome variable
persists to the decision node, treatment/control join correctly, **both lift AND accuracy
are computable**, and the oracle recovers a known injected lift *and* a known injected
accuracy effect. It does **not** mean any magnitude is known.

Two distinctions that must not collapse:

1. **Lift validation vs accuracy validation.** The decision gate is "positive lift AND
   treatment accuracy ≥ control accuracy." A pipeline that validates only lift leaves the
   accuracy half untested — which is exactly the gap the `correct:True` bug created (Part 11).
   The oracle must model *correctness*, not just action, so the accuracy guard is exercisable
   (see the `Oracle` protocol below and P-SOC-ORACLE-PLUMB).

2. **Floor power-analysis (now) vs calibrated power-analysis (pilot).** The oracle *can* run
   a power analysis now, but its gaussian noise is best-case, so it yields a **lower bound** on
   required N: "if the holdout can't detect a 5pp lift here with clean gaussian noise, it
   certainly can't under real overdispersion (clustered decisions, within-campaign
   correlation)." That floor is cheap and belongs in the now-work. The *calibrated* power
   answer — the real required N — needs pilot overdispersion structure and is pilot-run-up.
   Do not let the floor be read as the answer.

Never bundle the cheap plumbing+floor smoke-test with calibrated power-analysis, and never
let "instrumented" drift into "measured."

---

## Part 4 — The cross-copilot architecture

The unifying abstraction: for each intelligence claim, a copilot supplies **four providers**,
one per tier. **Only the three discipline types ship now** (`ClaimProvenance`,
`ClaimRegistry` in Part 2; `DayZeroReadiness` in Part 3). The four *provider protocols*
(ScrapedContextProvider, AnalyticClaim, HoldoutAssigner, Oracle, RealInstrument) are
**candidate contracts deferred to Part 5** — they're defined from one instance (SOC) and will
change when S2P's conditional holdout reveals a different shape, so they're not NOW code.

### Per-copilot substantiation map (with MAP cross-refs)

Every copilot instantiates the same four tiers; only the domain content differs. **This is
the proof the architecture is cross-copilot, not SOC-shaped.** MAP item shown where one
exists; **(no item)** flags work that needs a MAP# before it can be scheduled.

| Copilot | T-S Scraped (░░) | T-A Analytic | T-O Oracle | T-R Real (██, pilot) |
|---|---|---|---|---|
| **SOC** | threat-intel feeds, MITRE, CVE/NVD — **(no MAP item — needs one)** | γ theorem (ε_firm>0.128) ✅ | `AnalystOracle` (Campaign Step 1 instrumented ✅; plumbing pending) | analyst escalation lift; EXP-G1 γ |
| **S2P** | supplier filings/registries — **(no item; folds into P39)** | enrichment-loop math (candidate, math-poll) | `BuyerOracle` (P39/R18) | buyer hold-rate lift; supplier accuracy |
| **Trading** | **real** market data — **P50 ✅** (the K4 exemplar) | regime/DK bounds (candidate) | `TraderOracle` (P53 radar shipped; oracle new) | follow-rate lift |
| **Purchasing** | QBO vendor data **P66 ✅**; commodity prices/catalogs **(no item — P-PUR-COMMODITY-K4)** | — (none yet — honest gap) | `ChefOracle` (treatment = P73 par / P75 trust) | order-change lift |
| **DataOps** | schema/DQ benchmarks — **(no item)** | — (none yet) | `DataOpsOracle` (treatment = P34 map) | remediation-acceptance lift |

**Reading the map honestly:** SOC is the only copilot with a *proven* T-A today (γ). The
**(no MAP item)** flags are the real scheduling gaps — SOC threat-intel, Purchasing commodity
prices, DataOps benchmarks all need MAP#s (see Part 11.4 / §3A slotting). The registry will
not let a copilot claim a tier it hasn't built.

> **MAP state note (through P72):** Purchasing P68 (food-cost dashboard) and P72 (full
> conservation + auto-approve) are **DONE and surfacing computed metrics now.** If those
> metrics are computed from the K3 archetype data (50 suppliers / 500 orders, P64), that is a
> **live F-26 exposure today**, not a future risk — which moves P-FIXTURE-LABEL-AUDIT
> (Purchasing) and P-PUR-COMMODITY-K4 from "sprint" to "near-immediate." P73/P75 (the
> ChefOracle measurement-gated features) are NEXT and will need substantiation declarations.

---

## Part 5 — Extraction discipline + the candidate provider protocols

**The discipline:** the shared *implementation* (oracle base, holdout, instrument) — and even
the provider *protocols* — get finalized in `copilot_sdk/substantiation/` only when a
**second real instance** exists and reveals which parts were SOC-specific. Rule-of-three,
applied to this framework's own SDK surface.

**Candidate provider protocols (defined from SOC only — DO NOT ship as the contract yet):**

```python
# CANDIDATE — validate/finalize after instance 2 (S2P). Shape WILL change (conditional holdout).
from typing import Protocol

class ScrapedContextProvider(Protocol):     # T-S: real external → ░░ population
    def populate(self, entity_id: str) -> dict: ...        # provenance-tagged context values

class AnalyticClaim(Protocol):              # T-A: proof reference
    theorem_ref: str; conditions: list[str]; bound: str | None

class HoldoutAssigner(Protocol):            # deterministic per-entity, persisted to decision node
    def suppressed(self, entity_id: str, pct: int) -> bool: ...
    # ⚠ SOC = unconditional per-alert. S2P = CONDITIONAL (enrichment-exists gate). The
    #   protocol must absorb both before extraction — this is what instance 2 reveals.

class Oracle(Protocol):                     # T-O: parametric, validates pipeline (NOT magnitude)
    known_effect: float                     # injected lift the pipeline must recover
    known_accuracy_effect: float            # injected accuracy delta (may be NEGATIVE — Exp 4)
    def synthetic_outcome(self, *, shown: bool, system_action: str) -> dict: ...
        # MUST return {action, was_override, quality_signal, correct} — `correct` MODELED
        # (p_correct = base_accuracy + accuracy_lift if shown), never hard-coded True.

class RealInstrument(Protocol):             # T-R: pilot-gated measurement
    decision_node_fields: list[str]         # treatment flag + outcome + accuracy
    def measure(self, cohort) -> dict: ...  # lift + accuracy + power
```

```
Instance 1 (DONE):     SOC — AnalystOracle, banner_suppressed, decision-node persistence.
                       App-local in gen-ai-roi-demo-v4-v50. Do NOT generalize yet.

Instance 2 (NEXT):     S2P — **P39A (ProvenancedValue type guards) + P39B (supplier
                       enrichment hooks) already SHIPPED.** Instance-2 is NEW scope ON TOP of
                       that shipped code: build BuyerOracle + scraped-supplier T-S + the
                       conditional holdout (new buyer has no enrichment for most suppliers —
                       the SOC-divergent shape instance 2 must reveal before the protocols
                       freeze). This is a fresh prompt (P-S2P-BUYER-ORACLE), not a P39 edit.

THEN (~1d):            Extract copilot_sdk/substantiation/ from the TWO real shapes:
                       tiers/registry/readiness.py  (safe NOW — pure discipline)
                       holdout/oracle/instrument.py (extract HERE, validated on SOC + S2P)
```

**Safe to define NOW (Parts 1–3 — discipline, not instance code):** the tier model, the claim
registry + F-24/F-25/C-21/C-22, the day-zero readiness contract.

**Concrete T-S win — R18 cold-start:** the blank-screen problem on a new buyer (most suppliers
un-enriched day zero) is solved by **scraping real supplier signals** to fill ░░ — real,
labeled — not by generating fake decision history. T-S doing its job: a populated, honest
day-zero product whose ░░ converts to ██ as the buyer's decisions accrue.

---

## Part 6 — Narrative integration (detail)

The pitch, one-liner, and tier→language map are in **Part 0.1** (front of document). This
section keeps the implementation hook and the deeper strategic point.

**`sales_safe` wiring** (the gate behind every public claim):

```python
TIER_LANGUAGE = {
  Tier.ANALYTIC: "Proven mathematically that the mechanism holds (conditions stated); "
                 "magnitude measured on your data at pilot.",
  Tier.SCRAPED:  "Populated day-zero with real external data, labeled context (░░) vs "
                 "learned (██) — it becomes yours as your team operates.",
  Tier.ORACLE:   "The capability runs and the measurement instrument is validated to detect "
                 "the effect — wired in and visible today.",
  Tier.REAL:     "Measured on your operations: <magnitude> (verified decisions).",
}
```

**Honesty as moat (the strategic point):** the four-tier arc is the position that survives a
buyer's technical advisor asking "where did that number come from." Every competitor under
the same day-zero market pressure will be tempted to manufacture a magnitude with persona
data (K1/K2 surfaced — F-27). When their number doesn't survive diligence and ours does —
because ours is either proven (T-A), real-external (T-S), or honestly pending (T-R) — the
*honesty itself* is the differentiator. This is the company-strategy generalization of "the
measurement is the asset / stay advisory."

---

## Part 7 — Execution & sequencing (for roadmap)

```
STEP 0 — ✅ CLOSED (no longer a task). Campaign v6.0 closeout Scan 2 (June 19, 2026,
  campaign_v6_closeout_verification_scans.md) already verified outcome persistence end-to-end:
  analyst_action="escalate_tier2", was_override=true, quality_signal=1.0 all persisted through
  the outcome endpoint, and the Decision node carries BOTH campaign treatment flags AND the
  outcome fields. The cohort join the plumbing test depends on is proven. Nothing to run here.

NOW (parallel discipline sprint — honest effort ~3.75d; does NOT block §4):
  1. P-SUBST-CORE (~0.5d): Parts 1-3 → copilot_sdk/substantiation/{tiers,registry,readiness}.py
     + F-24..F-27, Rules 66/67. (Pure types — realistic at 0.5d.)
  2. P-SOC-ORACLE-PLUMB (~1-2d): AnalystOracle (design source: narrative_evaluation_v2_0 §9.2-9.3)
     + the v1.4 corrections (correctness modeling, Experiment 4) + 4 experiments + FLOOR power.
     Outcome wiring is NOT needed — Step 0 is closed.
  3. P-FIXTURE-LABEL-AUDIT (~1d, Phase 1): all 5 copilots; per-FACTOR K3/K4 determination for
     SOC is the slow part. Purchasing first (P68/P72 are live metric surfaces — see below).
     (Phase 2 runtime labeling mechanism may be additional — see 11.4.)
  Retro-tag existing SOC campaign claims (γ=T-A, CONTINUES=T-S/capability, behavior-lift=T-R-pending).

NEAR-IMMEDIATE (P72-done makes this live, not future):
  P-PUR-COMMODITY-K4 (~1-2d): Purchasing K4 connectors. Demo-credibility prerequisite — P68
     food-cost dashboard + P72 auto-approve already surface metrics; if computed from K3
     archetype data they're a live F-26 today.

INSTANCE 2 (S2P / R18 — when enrichment reaches measurement stage):
  Build BuyerOracle (with correctness model) + scraped-supplier T-S provider app-local. Note
  the CONDITIONAL
     holdout (enrichment-exists gate) — do not force SOC's shape.
  holdout (enrichment-exists gate) — do not force SOC's shape. THEN extract
  copilot_sdk/substantiation/{holdout,oracle,instrument}.py from SOC+S2P.

PILOT-GATED (per copilot, no calendar dates):
  T-R measurement starts when real users exist. Promote ANALYTIC/ORACLE → REAL only via a
  registry PromotionEvent with a pilot evidence_ref. Calibrated power-analysis here too.

DEFER (explicitly):
  - Calibrated/behavioral power-analysis (real overdispersion) → pilot run-up. (The gaussian
    FLOOR runs now in the plumbing test; it's a lower bound, not the answer.)
  - The full SDK measurement surface + the provider protocols → instance 2 (Part 5).
```

**Session/repo slotting (correcting the "no overlap" claim).** Several of these items DO
touch copilot-sdk — that is Session A's repo (running P66-P75) — so "no copilot-sdk overlap"
was wrong. They must be sequenced *inside* the owning session, not asserted parallel:

| Item | Repo | Session | Slot |
|---|---|---|---|
| P-SUBST-CORE | copilot-sdk | **A** | BEFORE P73 (first measurement-gated Purchasing prompt → first to need a real declaration) |
| P-FIXTURE-AUDIT-PUR | copilot-sdk (Purchasing) | **A** | URGENT — before/with P73 (P68/P72 live) |
| P-PUR-COMMODITY-K4 + P68/P72-FIX | copilot-sdk (Purchasing) | **A** | after audit confirms the K3 dependency |
| P-FIXTURE-AUDIT-TRADING / -DATAOPS | copilot-sdk | **A** | low priority (Trading already has ProvenanceBadge) |
| P-FIXTURE-AUDIT-S2P | s2p-copilot | **B** | F-16/F-17 OTIF/lead-time |
| P-S2P-BUYER-ORACLE | s2p-copilot | **B** | instance 2, on shipped P39A/P39B |
| P-FIXTURE-AUDIT-SOC / P-SOC-ORACLE-PLUMB | gen-ai-roi-demo | **C** | after Step-5 fix + P89 SOC-TAB5 (Session C has capacity — it was the lighter session) |

They stay *parallel to the §4 feature queue* in the sense of not blocking it, but they are
real work in real sessions — schedule accordingly (full sequencing in 11.5).

---

## Part 8 — Open for roadmap + llm-judge

1. **Analytic inventory:** SOC has γ. Are there provable T-A claims for S2P (enrichment
   recovery?), Trading (regime/DK?), or do those stay ORACLE+REAL only? (Math-poll candidates.)
2. **Scraped-data sourcing:** per-copilot real external sources + their ToS/licensing/refresh
   — T-S is only honest if the data is legitimately obtained and labeled (and refreshed, so
   "sample" data isn't obviously stale in a demo).
3. **Registry ownership:** who owns ClaimRegistry and approves PromotionEvents — Roadmap,
   llm-judge, or a named reviewer? (The migration guard is only as strong as its approver.)
4. **The conditional-holdout generalization (R18):** confirm at instance 2 whether the
   enrichment-exists gate is the right shape before extracting it to the SDK.
5. **Readiness gate enforcement:** advisory checklist, or a hard CI gate that blocks a
   feature ship until `DayZeroReadiness.gate()` passes?

---

## Part 9 — The generated-data taxonomy (what we actually generate)

"Synthetic data" is four distinct kinds with different rules. Conflating them is the
failure mode. This taxonomy refines the platform's existing provenance system (Rule 63:
source label + provenance tier) rather than duplicating it.

| Kind | Generator | Tier | Substantiates | Rule-63 tier | The hard rule |
|---|---|---|---|---|---|
| **K1 Oracle-behavioral** | parametric oracle (AnalystOracle, BuyerOracle…) | T-O | pipeline validity + capability | n/a (test-only) | Never leaves the test harness. Validates the instrument detects a KNOWN injected effect. Never a magnitude claim. |
| **K2 Factor-vector oracle** | LLM generates factor vectors → math oracle labels correctness | T-O | learning *mechanism* (direction, bound) | n/a (test-only) | The γ pattern. Substantiates γ>1 direction, never realized γ. Logs `centroid_distance_to_canonical`. |
| **K3 Demo-population fixture** | LLM-persona / archetype generator | **none** | **nothing** (demo realism only) | `context` → **`sample`** (new) | **The dangerous one — it looks real.** Labeled `sample`; NEVER in a metric, alert, or claim. |
| **K4 Scraped/external real** | scraper/connector (real source) | T-S | real context (░░) | `context` → `scraped_external` | Real, just not customer-specific. Honest ░░. Carries source + freshness + ToS-clean. |

**Two bright lines, encoded:**
- **K1/K2 never surface.** They are test-harness inputs that validate mechanism/pipeline.
  If oracle output ever reaches a user-facing value, that's META-4 (F-27).
- **K3 ≠ K4.** Archetype-generated demo data (K3) substantiates *nothing* and is the
  highest fixture-as-real risk; scraped real data (K4) is legitimate ░░ context. The
  platform currently blurs these — Rule 67 (Part 11) splits them with distinct labels.

This extends Rule 63's tiers: `context` splits into `scraped_external` (K4, ░░) and
`sample` (K3); `learned` stays ██ (T-R); a new `proven` tier covers analytic claims (T-A)
that have no per-decision data at all.

---

## Part 10 — Per-copilot synthetic-data specification (grounded in MAP v5.190)

Per copilot: the concrete data of each kind, its generator, MAP status, work delta.
**Status:** ✅ exists+compliant · ⚠️ exists, needs labeling audit · 🔨 new build.

### SOC (AGE; reference instance)

| Kind | Concrete data | Generator | Status |
|---|---|---|---|
| K2 factor-vector | factor vectors + centroid-distance correctness labels; `SYN/SYNP/SYNZ/SYNW` prefixes | LLM-vectors + math-oracle (γ audit) | ✅ DONE (Apr 8; CC-21 Tier 2) |
| K1 oracle | `AnalystOracle` → `{analyst_action∈{escalate_tier2,investigate,dismiss}, was_override, quality_signal, correct}`; params `base_rate, treatment_lift, base_accuracy, accuracy_lift` | parametric | 🔨 design in narrative_eval §9; outcome persistence ✅ (closeout Scan 2); plumbing test pending |
| K4 scraped | MITRE ATT&CK, CVE/NVD, threat-intel feeds → ░░ threat context | feed connector | 🔨 new (partial via fixtures) |
| K3 demo-fixture | seeded campaigns/alerts (269 campaigns) | seed script | ⚠️ label `sample` |

> **SOC oracle design source:** `campaign_arc_narrative_evaluation_v2_0.md` §9 (oracle class,
> pipeline-validation tests, artifact discipline, sequencing). **Division of authority:** THIS
> document is the cross-copilot FRAMEWORK (tier model + registry + taxonomy); the narrative
> evaluation is the SOC-specific APPLICATION (the oracle *code* lives there). P-SOC-ORACLE-PLUMB
> extends that §9 design with only the v1.4 corrections (correctness model + Experiment 4).

> **⚠ SOC's live K3-inside-the-scorer risk:** SOC already uses `threat_intel_enrichment`
> as a **factor value**. If that value is fixture-sourced (not from a real feed), it is K3
> feeding a *score* — a live **F-26** candidate (K3 in a computed value), and more dangerous
> than a dashboard metric because it's invisible (a factor, not a labeled badge).
> P-FIXTURE-LABEL-AUDIT must determine, per SOC factor, whether each value is K4 (real feed →
> label ░░/`scraped_external`) or K3 (fixture → label `sample` and confirm it doesn't
> masquerade as a learned/real signal). Resolve this before the SOC AGE-ready sign-off.

### S2P (instance 2 — SDK-extraction trigger)

| Kind | Concrete data | Generator | Status |
|---|---|---|---|
| K1 oracle | `BuyerOracle` → `{buyer_action∈{auto_approve,hold_for_review,escalate}, was_override, quality_signal}`; **CONDITIONAL holdout** (enrichment-exists gate — cold-start shape, NOT SOC's per-alert split) | parametric | 🔨 new (P39/R18) |
| K4 scraped | supplier public filings, business registries, trade data → ░░ (**dissolves R18 cold-start blank screen**) | registry/filing connector | 🔨 new |
| K3 demo-fixture | supplier cards, OTIF/lead-time fixtures | fixture set | ⚠️ audit (F-16/F-17: OTIF/lead-time = `sample`/░░, never measured) |

### Trading (the T-S/K4 done-right exemplar)

| Kind | Concrete data | Generator | Status |
|---|---|---|---|
| K4 scraped | **real** market data (OHLCV, VIX, fundamentals) | `MarketDataProvider` (yfinance/Alpaca, cache cascade) | ✅ DONE (P50, F-21 `ProvenanceBadge`) — **the model to copy** |
| K1 oracle | `TraderOracle` → `{trader_action∈{strong_execution,partial_execution,skip}}`; treatment = trust-radar (P53) shown vs not | parametric | 🔨 new (radar shipped; holdout+oracle new) |
| K3 demo-fixture | `market_snapshot.json` fallback | fixture | ✅ labeled `sample` via F-21 cascade |

### Purchasing (K3 risk concentration)

| Kind | Concrete data | Generator | Status |
|---|---|---|---|
| K3 demo-population | **50 suppliers, 500 orders, 12 archetypes** | archetype generator (P64) | ⚠️ **EXISTS, highest K3 risk** — `sample`, never in a metric/par/score |
| K4 scraped | commodity prices (real), supplier catalogs; QBO vendor data | connectors (QBO P66 = real ✅) | ⚠️/🔨 QBO real ✅; commodity prices new |
| K1 oracle | `ChefOracle` → `{chef_action∈{order_as_planned,order_more,order_less,skip}}`; treatment = par-intelligence (P73)/trust (P75) shown | parametric | 🔨 new (at P73/P75) |

> **Day-zero demo composition (the K3 label is necessary but NOT sufficient) — and it's LIVE:**
> ```
> QBO vendor data:          K4 (real, ░░)   — exists (P66)
> Commodity prices:         K4 (real, ░░)   — 🔨 new (P-PUR-COMMODITY-K4)
> Supplier catalogs:        K4 (real, ░░)   — 🔨 new
> 50 suppliers/500 orders:  K3 (sample)     — exists (P64); label audit URGENT
> Computed metrics:         P68 food-cost dashboard + P72 auto-approve/conservation are DONE
>                           and SURFACING — if they compute from the K3 set, that's a LIVE F-26
> ```
> **Honest assessment (sharpened by P72-done):** P68 and P72 already render computed metrics.
> If those are derived from the K3 archetype data, the violation is **today**, not at some
> future demo. Labeling K3 `sample` is correct but commercially dead — a screen where every
> metric reads "sample, not from your operations" sells nothing. The fix is not the label;
> it's **shipping the K4 sources** so the demo shows real ░░ data ("real commodity prices
> today; your operations replace the rest"), `sample` only on the archetype scaffolding. Same
> cold-start shape as R18: **the K3 label prevents the lie; the K4 connector makes the demo
> real.** So two things move up: the Purchasing K3 audit (now — it's live) and
> P-PUR-COMMODITY-K4 (immediately after).

### DataOps

| Kind | Concrete data | Generator | Status |
|---|---|---|---|
| K4 scraped | schema/catalog standards, public DQ benchmarks → ░░ | connector | 🔨 new |
| K1 oracle | `DataOpsOracle` → `{action∈{accept,modify,reject}}`; treatment = intelligence-map (P34)/recommendation shown | parametric | 🔨 new |
| K3 demo-fixture | source profiles (P30/P32) | profiler fixtures | ⚠️ label `sample` |

**Cross-copilot reading:** the only proven T-A today is SOC's γ. Trading is the K4 exemplar
(copy its `ProvenanceBadge`/cascade everywhere). Purchasing concentrates the K3 risk **and it
is now live** (P68/P72 surface metrics). Every copilot needs a K1 oracle for its
measurement-gated feature — those are **pilot-run-up** builds, except SOC's plumbing test
(now). The honest NOW work is ~3.75d (Part 7; Step 0 already closed), not a half-day.

---

## Part 11 — Prompt & rule changes (executable delta to MAP v5.190)

### 11.1 §17 template addition — SUBSTANTIATION DECLARATION (intelligence/metric prompts only)

**Trigger (not every prompt — only when the feature touches substantiation):**

```
SUBSTANTIATION DECLARATION required when the feature:
  - surfaces a metric, score, par, rating, or intelligence value, OR
  - displays advisory context (campaign, enrichment, trust), OR
  - shows data labeled ░░ or ██, OR
  - creates demo/fixture data that could be mistaken for real.
NOT required for: CLI tools, packaging/PyPI, infra, SQLite→AGE migration,
  internal refactoring, test fixes, or backend performance work (e.g. Phase 3/3B).
  (P29, P52, P62 carry nothing to substantiate — they get no declaration.)
```

When triggered, add this block alongside the existing BACKEND COMPATIBILITY block:

```
SUBSTANTIATION DECLARATION (Rule 66):
- Surfaced values/claims: [every metric/badge/advisory this feature shows a user]
- Tier per value:  proven(T-A) | scraped(T-S,░░) | sample(K3) | real-pending(T-R,██)
- Generated data this prompt creates: none | K1-oracle | K2-factor-oracle | K3-demo-fixture
- Labeling (Rule 67): every surfaced value carries ██learned / ░░context / proven / sample
- Magnitude guard (F-24): no value asserted at REAL(██) without a pilot evidence_ref
- K3 guard (F-26): demo-fixture values NEVER appear in a metric, score, par, or claim
- If measurement-gated: decision-node fields = [treatment_flag, outcome_var, accuracy_var];
  holdout assigner = <name>; K1 oracle class = <name>; pipeline smoke-test = <test file>
```

Makes substantiation a *declared, reviewable* property of every intelligence feature — the
way BACKEND COMPATIBILITY made GraphStore discipline declared.

**Where it lives in the 3-stage prompt (the integration point):**
- **Stage 2 (implementation):** the SUBSTANTIATION DECLARATION sits as its own section
  alongside `BACKEND COMPATIBILITY` and `NON-NEGOTIABLES`. The author fills it from the
  per-copilot default below.
- **Stage 3 (architecture review):** add one checklist item — *"SUBSTANTIATION DECLARATION
  matches implementation: tier labels present on every surfaced value; no K3 (`sample`) value
  feeds a metric/score (F-26); measurement fields persist + join."* This is what the GPT-5.5
  review stage verifies against the code.
- **Codex CLI Playbook §3.12 (architecture audit):** add the same check to the standing audit
  list so it runs on every intelligence prompt, not just when remembered.

**Per-copilot DEFAULT templates (fill-in, not blank-slate — cuts ~10 min → ~2 min/prompt).**
The author overrides only the lines that differ; the reviewer checks deltas, not the whole block.

```
Purchasing default (P73-P75):
  Tier per value: scraped(░░) unless from verified decisions(██)
  Generated data: K3 demo-fixture (archetype suppliers/orders, P64)
  K3 guard: archetype values EXCLUDED from computed metrics (food-cost, par, score)
  Measurement-gated (P73 par / P75 trust): treatment_flag=<...>, outcome=chef_action, ChefOracle

S2P default (P39/R18):
  Tier per value: scraped(░░ filings) | real-pending(██ from verified outcomes) | sample(fixtures)
  Generated data: K1 BuyerOracle (test only); K4 scraped supplier
  Holdout: CONDITIONAL on enrichment-exists

Trading default (P53+):  market data=scraped(░░, P50 ProvenanceBadge); radar=real-pending(██); TraderOracle
DataOps default (P34+):  benchmarks=scraped(░░); map=real-pending(██); DataOpsOracle
SOC default:             threat-intel=scraped(░░) OR sample if fixture (resolve per-factor); γ=proven(T-A)
```

### 11.2 New standing rules (66–67) — relationship to existing 63/64 made explicit

**Rule 66 EXTENDS Rule 63 (it is not a parallel rule).** Rule 63 already requires a
*provenance* tier (learned/context/fixture); Rule 66 adds the *substantiation* tier on the
same value. One review pass checks both. **Rule 67 is NEW** (the K1–K4 generation taxonomy,
which Rule 63 doesn't cover). Rule 64 (counterfactual faithfulness) is untouched.

```
| 66 | Rule 63 EXTENDED — substantiation tier required ALONGSIDE provenance tier. Every
     | user-facing value carries BOTH: provenance (Rule 63: learned/context/fixture) AND
     | substantiation (T-A proven / T-S scraped / T-O oracle / T-R real). Tagged in
     | ClaimRegistry. No magnitude claim below REAL (F-24); promotion to REAL needs a pilot
     | evidence_ref + approved PromotionEvent. (Reviewer checks 63 and 66 together, once.)
| 67 | NEW — generated-data labeling by kind (K1–K4). K1/K2 oracle data NEVER surfaces (test
     | harness only). K3 demo-fixtures labeled `sample`, NEVER in a metric/score/par/alert/
     | claim. K4 scraped labeled `scraped_external`/░░ with source+freshness. Conflating K3
     | with K4, or surfacing K1/K2, is a P1 fix before tag.
```

FORBIDDEN additions (extend F-24/F-25 from Part 2):

```
| F-26 | K3 demo-fixture value used in a metric/score/par/claim → label `sample`, exclude from computed values
| F-27 | K1/K2 oracle output surfaced to a user or used as a magnitude claim → the META-4 line
```

### 11.3 Existing-prompt audit — exactly which prompts change (including shipped ones)

**Summary count:** ~37 existing prompts touched — **4 need code changes (live F-26 risk),
~26 need a declaration added to already-shipped work, ~8 pending prompts get it at authoring,
and ~11 are explicitly EXEMPT.** Classified below; "DONE" prompts still change because a
shipped metric with no tier label is exactly the exposure this framework closes.

#### Class A — CODE + LABEL (load-bearing: live F-26 risk or measurement plumbing) — 4 prompts

| P# | ID | Status | What it surfaces | Required change |
|---|---|---|---|---|
| **P64** | PUR-SYNTH-DATA | DONE | the K3 archetype generator itself (50 suppliers / 500 orders / 12 archetypes) | **Source-label all output `sample`.** Add `provenance:"sample"` to every generated record so every downstream consumer inherits it. This is the K3 origin — fixing it here is what makes F-26 enforceable everywhere else. |
| **P68** | PUR-SPEND-DASH | DONE | food-cost dashboard metrics | **AUDIT + fix:** are the food-cost numbers computed from P64 K3 data? If yes → **live F-26 today.** Re-source from K4 (P-PUR-COMMODITY-K4) or label the metric `sample`. |
| **P72** | PUR-CONSERVATION-FULL | DONE | conservation projection + auto-approve | **AUDIT + fix:** conservation/auto-approve computed over K3 orders = **live F-26.** Same resolution as P68. |
| **P71** | PUR-VERIFY | DONE | confirm/override + hash-chain | **This is Purchasing's outcome instrumentation** — chef confirm/override is the ChefOracle outcome variable (Purchasing's analog of SOC `analyst_action`). Verify it persists + **joins to any treatment flag**, exactly the Step-0 check applied to Purchasing. Without the join, Purchasing measurement is impossible. |

**Class-A discovery commands (run BEFORE any code change — Codex needs patterns, not prose).**
The CLAUDE_* repo-root vars apply; use the repo-configured runner, not literal `pytest`.

```
P68 — does food-cost compute from K3 (P64 archetype) or K4 (QBO/real)?
  grep -rn "supplier\|order\|archetype\|fixture\|demo_data\|seed_data\|generate" \
    <purchasing>/backend/app/services/spend_dashboard*.py \
    <purchasing>/backend/app/services/food_cost*.py
  IF it references the P64 archetype generator → LIVE F-26:
    (a) label archetype-derived metrics `sample`, AND
    (b) wire P-PUR-COMMODITY-K4 to replace the K3 inputs with K4
  IF QBO/real → label ░░ scraped_external, no F-26.

P72 — same pattern for conservation/auto-approve:
  grep -rn "supplier\|order\|archetype\|fixture\|seed_data\|generate" \
    <purchasing>/backend/app/services/conservation*.py \
    <purchasing>/backend/app/services/*auto*approve*.py

P64 — confirm the generator is the K3 origin and label at source:
  grep -rn "def generate\|archetype\|class .*Generator\|return .*supplier" \
    <purchasing>/backend/app/**/*synth*.py <purchasing>/backend/app/**/*seed*.py
  → add provenance:"sample" to every emitted record.

P71 — confirm the outcome var persists AND joins to a treatment flag:
  grep -rn "chef_action\|confirm\|override\|outcome\|verify\|hash_chain\|treatment" \
    <purchasing>/backend/app/routers/*verify*.py <purchasing>/backend/app/services/*verify*.py
  → one persisted record must carry BOTH the outcome and any treatment flag (SOC Step-0 discipline).
```

**Class-A is a chain, not four parallel fixes — audit ≠ fix, and the fix has a dependency.**
The discovery only *confirms or denies* the live F-26. If P68/P72 do compute from K3, the fix
can't land until the K4 connector exists (re-sourcing) — the only K3-free alternative is
labeling the metric `sample`, which is commercially dead. So:

```
P-FIXTURE-AUDIT-PUR  (Session A, ~2h, read-only)  → confirm/deny K3-in-metric for P68/P72
        │
        ├─ if QBO/real → label ░░, DONE (no F-26)
        └─ if K3 → P64-LABEL (label generator output `sample`, ~0.5d)        [Session A]
                 → P-PUR-COMMODITY-K4 (build K4 connector, 1-2d)              [Session A]
                 → P68-FIX + P72-FIX (re-source food-cost/conservation to K4, [Session A]
                     remove K3 from the computed metric, ~0.5d)
P71-VERIFY (Session A, ~2h) — confirm chef outcome persists + joins (independent of the above)
```

P68-FIX / P72-FIX are **new Stage-2 implementation prompts**, gated on P-PUR-COMMODITY-K4.
Do not collapse them into "near-immediate" — the connector is the long pole.

#### Class B — REGISTRY POPULATION, not prompt edits (shipped code can't take a new declaration) — ~18

You cannot retroactively add a Codex SUBSTANTIATION DECLARATION to a *shipped* prompt — the
code already exists and there is no prompt to run. What these ~18 features actually need is a
**`ClaimProvenance` registry entry** (claim text + tier + evidence_ref) recording what each
surfaces and at what tier. That's a **data-entry task against the ClaimRegistry**, not a
coding prompt: ~15–20 min per feature (read it, determine the tier, write the entry) ≈ 5–6h.
Ship it as a **registry-population script / fixture inside P-SUBST-CORE** (or a one-off
`populate_claim_registry.py`), reviewed once — not as 18 separate Codex prompts. The audit
phase (P-FIXTURE-AUDIT-*) supplies the K3/K4 determination each entry needs.

**The ~18 registry entries to create (claim → tier):**

| P# | ID | Surfaces | Registry tier (the `ClaimProvenance.tier`) |
|---|---|---|---|
| P36 | S2P-LEAD-TIME | lead-time | lead-time from invoice context = ░░ scraped, never ██ measured (F-17) |
| P37 | S2P-NL-TRUST | trust-weighted NL evidence | trust source tier-tagged |
| P40 | S2P-AUTO-APPROVE | auto-approve advisory (shadow) | advisory = real-pending; never ██ from fixtures |
| P41 | S2P-CENTROID-EXPLORER | factor values (FactorRadar) | per-factor provenance (K3/K4/██) |
| P46 | PUR-WEEKLY-REPORT | weekly report metrics | tier per metric in the report |
| P47 | POLARITY-FIX | 30 factor polarities (display) | display-only, scorer-independent; factor provenance |
| P49 | TRD-REGIME-RECOMMENDER | regime recommendation | regime derived from K4 market data (░░) |
| P53 | TRD-TRUST-RADAR | DK radar / trust (F2 HERO) | measurement-gated → declaration + TraderOracle holdout-ready |
| P54 | TRD-REMAINING-FACTORS | factors | per-factor provenance |
| P55 | TRD-PATTERN-DETECTOR | statistical patterns | computed from K4 vs K3 — label the inputs |
| P63 | TRD-EVIDENCE-NL | evidence NL + DK trust inline | evidence provenance (already polarity-aware) |
| P69 | PUR-MATCH-ENGINE | three-way match results | match over K3/K4 inputs — label inputs |
| P70 | PUR-ORDER-QUEUE | smart queue + NL evidence | queue-intelligence provenance |
| P42 | DI-3-NL-QUERY | NL query results | deterministic, no LLM — light declaration |
| P43 | DI-5-COMBINATION-DISCOVERY | discovered combinations | **non-causal** labeling required |
| P34 | DI-2-INTELLIGENCE-MAP | intelligence map (DataOps) | measurement-gated → DataOpsOracle treatment |
| P30/P32 | DI-1-SOURCE-PROFILER | source profiles | K3 fixture profiles → `sample` |
| P45 | TOAST-POS | POS sales data | K4 real → ░░ (borderline B/C — real connector) |

#### Class C — DECLARATION-ONLY (shipped, already provenance-aware: confirm tier) — ~7

| P# | ID | Why it's light |
|---|---|---|
| P38 | S2P Context Builder | already source-labeled — confirm tier maps to T-S/sample |
| P44 | DI-5-GRAPH-ENRICHMENT | BaseGraphEnricher already provenance-safe — confirm |
| **P50** | TRD-MarketDataProvider | **the K4 exemplar** (F-21 ProvenanceBadge) — confirm + this is the pattern P-PUR-COMMODITY-K4 copies |
| P59 | TRD-IBKR | real broker data — confirm K4 ░░ |
| P60 | TRD-CSV-IMPORT | imported trades — confirm imported-data provenance |
| P66 | PUR-QBO-CONNECTOR | real QBO vendor data — confirm K4 ░░ (Purchasing's existing good K4) |

#### Class D — PENDING / QUEUED: full declaration at authoring (not retrofit) — ~8

| P# | ID | Note |
|---|---|---|
| ~~P39~~ | S2P-GRAPH-ENRICHMENT | **P39A/P39B SHIPPED** — not pending. The instance-2 substantiation work (scraped-supplier ░░ + conditional `BuyerOracle` holdout) is NEW scope → **P-S2P-BUYER-ORACLE** (11.4), built on top of the shipped enrichment, not a P39 edit. |
| P73 | PUR-PAR-INTELLIGENCE | measurement-gated → ChefOracle treatment; learned par = ██ real-pending |
| P75 | PUR-TRUST-ANALYSIS | measurement-gated → ChefOracle treatment (F11 HERO) |
| P74 | PUR-IKS-SCORECARD | scorecard tiers per metric |
| P81 | TRD-REGIME-CLASSIFIER | regime from K4 |
| P82 | TRD-REALTIME-SCORE | measurement-gated candidate |
| P83 | TRD-PROMOTION-ENGINE | conservation-gated promotion |
| P84 | TRD-AGENT-EVOLVER-FULL | learned policy = ██ real-pending |
| R18 | S2P-SUPPLIER-INTEL | instance-2 with P39: full declaration, conditional holdout |

#### Class E — EXEMPT (no declaration — listed so the exclusion is explicit) — ~11

P29 (SQLite→AGE migration), P48 (TRD-DOMAIN-CONFIG, base classes), P52 / P61 / P62 (CLI /
packaging / PyPI), P57 (TRD-JOURNAL — user-authored content, not a system claim), P76
(mypy), P77 (SOC-OPTION-C — verify at authoring), P78 (outbox worker), P79 (L5 proof), P80
(SDK docs). None surface a system-generated metric or intelligence claim.

#### Not P-numbered but in scope — SOC factor sourcing

SOC predates P-numbering (gen-ai-roi-demo repo). Its factor values — **especially
`threat_intel_enrichment`** — must be audited per-factor for K4 (real feed → ░░) vs K3
(fixture → `sample`); a fixture-sourced factor feeding the score is a **live F-26**. Handled
by P-FIXTURE-LABEL-AUDIT (11.4), not a new P#.

---

### 11.4 New prompts to add — assigned to sessions/repos (roadmap assigns MAP#s)

These run parallel to the §4 feature queue (they don't block it) but they are **real work in
real sessions** — each is assigned to its owning repo's session below, not asserted as
"no-overlap." **Honest NOW effort ≈ 3.75d** (Step 0 CLOSED).

**The new prompts at a glance** (Step 0 done; audit split per-repo; P68/P72 fixes added):

| New prompt | Session/repo | When | Effort | Purpose |
|---|---|---|---|---|
| ~~P-SUBST-STEP0~~ | — | ✅ CLOSED | — | Outcome persistence proven (closeout Scan 2) |
| **P-SUBST-CORE** | A / copilot-sdk | before P73 | 0.5d | discipline SDK + §17 block + Rules 66/67 + F-24..F-27 + ClaimRegistry population (Class B) |
| **P-FIXTURE-AUDIT-PUR** | A / copilot-sdk | URGENT | ~2h | read-only: does P68/P72 compute from K3? |
| **P-FIXTURE-AUDIT-S2P** | B / s2p-copilot | NOW | ~2h | F-16/F-17 OTIF/lead-time source |
| **P-FIXTURE-AUDIT-SOC** | C / gen-ai-roi | NOW | ~2h | per-factor K3/K4 (threat_intel_enrichment) |
| **P-FIXTURE-AUDIT-SDK-TRD/DO** | A / copilot-sdk | low pri | ~2h | Trading (has badge) + DataOps profiles |
| **P-SOC-ORACLE-PLUMB** | C / gen-ai-roi | after Step-5 fix + P89 | 1-2d | AnalystOracle pipeline test (narrative_eval §9 + Exp 4) |
| **P64-LABEL** | A / copilot-sdk | if audit=K3 | 0.5d | label archetype generator output `sample` at source |
| **P-PUR-COMMODITY-K4** | A / copilot-sdk | if audit=K3 | 1-2d | real commodity K4 connector (the long pole) |
| **P68-FIX / P72-FIX** | A / copilot-sdk | after K4 | 0.5d | re-source metrics to K4; remove K3 from computation |
| **P-S2P-BUYER-ORACLE** | B / s2p-copilot | instance 2 | 1d | BuyerOracle + scraped ░░ + conditional holdout → then extract SDK |
| **TraderOracle / ChefOracle / DataOpsOracle** | A | pilot run-up | per-copilot | K1 oracle + K4 provider + calibrated power |

Detailed specs:

```
P-SUBST-STEP0       ✅ CLOSED  Campaign v6.0 closeout Scan 2 (campaign_v6_closeout_verification_
                            scans.md, June 19 2026) proved analyst_action / was_override /
                            quality_signal persist through the outcome endpoint and the Decision
                            node carries BOTH treatment flags AND outcome fields. No work remains.

P-SUBST-CORE        ~0.5d   [Session A — copilot-sdk; slot BEFORE P73]
                            copilot_sdk/substantiation/{tiers,registry,readiness}.py
                            + §17 SUBSTANTIATION DECLARATION block + per-copilot templates
                            + Rules 66/67 + F-24..F-27
                            + populate_claim_registry.py: the ~18 Class-B ClaimProvenance entries
                              (data entry, fed by the AUDIT prompts). Reviewed once.

P-SOC-ORACLE-PLUMB  ~1-2d   [Session C — gen-ai-roi; AFTER Step-5 fix (5min) + P89 SOC-TAB5 (2d).
                            Session C has capacity — it was the lighter session — but say so:
                            this is ~4d of Session-C work in total. NOT blocking other sessions.]
                            SOC AnalystOracle pipeline-validation test.
                            DESIGN SOURCE: campaign_arc_narrative_evaluation_v2_0.md §9.2 (oracle
                              class) + §9.3 (pipeline tests). Do NOT re-specify — extend with:
                              - base_accuracy + accuracy_lift params (correctness model)
                              - `correct` field in outcome (NOT hard-coded True)
                              - Experiment 4: +lift / −accuracy → gate correctly REJECTS
                              - FLOOR power-analysis caveat (gaussian = lower bound)
                            Step-0 outcome wiring NOT needed (closed). §9.3 covers Exp 1/2/3.

P-FIXTURE-AUDIT-*           [SPLIT per repo — it spans 3 repos / 3 sessions, can't be one prompt]
  -PUR  (Session A, ~2h)    Purchasing 50/500 archetype set — URGENT (P68/P72 live). Run the
                            Class-A greps; output the K3/K4 determination for food-cost +
                            conservation + auto-approve. Gates P64-LABEL / commodity / P68-FIX.
  -SOC  (Session C, ~2h)    per-FACTOR source (threat_intel_enrichment esp.): K4 feed→░░ vs
                            K3 fixture→`sample`; fixture-sourced factor in score = live F-26.
  -S2P  (Session B, ~2h)    OTIF/lead-time (F-16/F-17) source.
  -SDK-TRD/DO (Session A, ~2h, low pri)  Trading (already labeled via ProvenanceBadge — light)
                            + DataOps source profiles.
  All are READ-ONLY discovery. Output feeds the ClaimRegistry population (P-SUBST-CORE) and
  the Phase-2 labeling decision below.

PHASE 2 LABELING (not in the 3.75d) — mechanism does NOT exist outside Trading: only Trading
                            has a runtime provenance display (`ProvenanceBadge`, F-21/P50).
                            Purchasing/S2P/DataOps have NO field/badge to write `sample`/░░ to:
                              (a) extend ProvenanceBadge to other copilots — >1d UI work
                              (b) add a `provenance` field to each copilot's data model —
                                  simpler; the minimum that makes F-26 ENFORCEABLE in tests
                                  (assert no record with provenance=="sample" feeds a metric)
                              (c) document-only — honest, no runtime enforcement
                            RECOMMENDED: (b) now (enforcement substrate) + (a) per copilot as a
                            follow-on at each copilot's demo. Phase 2 is NOT inside the 3.75d.

P-PUR-COMMODITY-K4  ~1-2d   NEAR-IMMEDIATE (P68/P72 live). Real K4 connectors for Purchasing.
                            Concrete spec (copy Trading P50 MarketDataProvider exactly):
                            - Source candidates (roadmap picks per ToS): USDA ERS / FRED
                              commodity series (free, public, food-relevant) for prices;
                              a supplier-catalog/产品 reference feed for catalogs. Confirm
                              license + refresh in Part 8 Q2 before wiring.
                            - Provider: CommodityDataProvider with the SAME cache cascade as
                              MarketDataProvider — live → cached → fixture(`sample`), each
                              tagged via F-21 ProvenanceBadge.
                            - Refresh: daily (commodity prices move slowly); cache TTL 24h;
                              weekend/holiday serves `cached` (honest, labeled).
                            - Fallback: when the feed is down/rate-limited → last cached
                              (░░ cached) → K3 archetype (`sample`). NEVER unlabeled.
                            - Wires into P68 food-cost + P73 par as the ██/░░ inputs that
                              replace K3 in computed metrics.

P64-LABEL           ~0.5d   [Session A — only if P-FIXTURE-AUDIT-PUR finds K3-in-metric]
                            Add provenance:"sample" at the archetype generator (the K3 origin);
                            every downstream consumer inherits it. Enforcement substrate for F-26.

P68-FIX / P72-FIX   ~0.5d   [Session A — GATED on P-PUR-COMMODITY-K4 being done]
                            Re-source food-cost / conservation / auto-approve from the K4
                            connector; remove K3 archetype values from the computed metric (or,
                            where a value is intrinsically demo-only, label it `sample` and drop
                            it from the headline number). Closes the live F-26. Cannot precede
                            the connector — that's the long pole, not "near-immediate."

P-S2P-BUYER-ORACLE  ~1d     [Session B — instance 2, builds ON shipped P39A/P39B (NOT after an
                            unexecuted P39)] BuyerOracle (correctness model) + scraped-supplier
                            ░░ + conditional holdout. THEN extract
                            copilot_sdk/substantiation/{holdout,oracle,instrument}.py +
                            finalize the Part-5 candidate protocols (validated on SOC+S2P).

[pilot run-up, per copilot]  TraderOracle / ChefOracle / DataOpsOracle + scraped providers +
                            CALIBRATED power-analysis, built at each copilot's pilot.
```

### 11.5 Sequencing against the live MAP (session-keyed)

```
STEP 0: ✅ CLOSED (closeout Scan 2). No action.

SESSION A (copilot-sdk; interleaved with P66-P75):
  1. P-SUBST-CORE (0.5d) — BEFORE P73 (first measurement-gated Purchasing prompt).
     Includes the ClaimRegistry population (the ~18 Class-B entries).
  2. P-FIXTURE-AUDIT-PUR (~2h) — URGENT, read-only. Confirms/denies K3-in-metric for P68/P72.
        if K3 →  P64-LABEL (0.5d) → P-PUR-COMMODITY-K4 (1-2d) → P68-FIX/P72-FIX (0.5d)
        if real → label ░░, done.
  3. P71-VERIFY (~2h) — Purchasing outcome persists+joins (independent).
  4. P-FIXTURE-AUDIT-SDK-TRD/DO (~2h, low priority).

SESSION B (s2p-copilot):
  P-FIXTURE-AUDIT-S2P (~2h). Then, at instance 2 (on shipped P39A/P39B):
  P-S2P-BUYER-ORACLE (1d) → extract SDK measurement module + finalize Part-5 protocols.

SESSION C (gen-ai-roi / SOC; after Step-5 fix + P89 SOC-TAB5):
  P-FIXTURE-AUDIT-SOC (~2h) + P-SOC-ORACLE-PLUMB (1-2d). ~4d of Session-C work total;
  Session C has the capacity (it was the lighter session). Not blocking A or B.

PILOT RUN-UP (per copilot, no calendar dates):
  per-copilot K1 oracle + K4 provider; CALIBRATED power-analysis;
  PHASE 2 labeling mechanism (provenance field + badge) per copilot at its demo;
  promote ANALYTIC/ORACLE → REAL only via PromotionEvent + pilot evidence_ref.
```

Honest accounting: the NOW discipline work is **~3.75d** (mostly Session A's 0.5d core +
audits, plus Session C's oracle test), Step 0 closed. **The non-deferrable item is the
Purchasing K3 audit** (P-FIXTURE-AUDIT-PUR): P68/P72 are live metric surfaces *now*, so a
K3-fed metric is a live F-26 today — but note the *fix* is a chain, not instant: audit →
P64-LABEL → P-PUR-COMMODITY-K4 (the long pole) → P68-FIX/P72-FIX. Everything domain-specific
past that (the other oracles, scraped providers, calibrated power, Phase-2 display) stays
pilot-run-up — never speculative.

---

## Part 12 — Publication anchors (internal discipline → external narrative)

This framework is an *internal* discipline; the market sees it only through what we publish.
The tier→language map (Part 6) is the bridge, but it must reach the actual publication
pipeline or the discipline stays invisible. Concrete anchors:

| Artifact | File / status | Required connection |
|---|---|---|
| **arXiv short** | `cga_arxiv_short_v7_6.md` (project knowledge; newer than the v7.2 cited earlier — use v7.6) | Reference the four-tier model. The framework + the META-4 identifiability line is itself a publishable *AI-product-integrity* contribution ("what synthetic data can and cannot substantiate"), generalizing the γ oracle-separation result the paper already rests on. |
| **CI blog** | `ci_blog_v15.md` (project knowledge — exists) | Frame the **day-zero arc** (░░→██ conversion) as the *honest alternative* to synthetic-magnitude claims: "anyone who hands you your magnitude number on day one is showing you synthetic data." |
| **gen-ai-roi blog (E-06)** | **roadmap item — not yet written** | When written, map the CC-23 three deployment tiers onto T-A/T-S/T-O/T-R explicitly (they don't align yet — fix at authoring, not retrofit). |
| **Demo scripts (all copilots)** | exist per copilot | Each demo narrates the ░░→██ transition: "real external context today; after your team operates, it becomes learned — measured with the instrument you can see running now." The transition *is* the compounding thesis shown live. |

These are mostly a consistency gate, not new writing: each publication must use the same tier
vocabulary, or the external story and internal discipline drift — itself an F-24-class risk at
the company-narrative level (claiming more than the evidence tier supports, in print). Confirm
the current arXiv version in project knowledge before citing (v7.6 supersedes v7.2).

---

## Document control

| Version | Date | Change |
|---|---|---|
| v1.0 | June 19, 2026 | Initial cross-copilot framework. Four-tier substantiation model (Analytic/Scraped/Oracle/Real) with the META-4 line (synthetic substantiates capability+pipeline, never real-agent magnitude). Claim-provenance registry + migration guard (F-24/F-25, C-21/C-22). Day-zero readiness contract (populated/proven/instrumented/real-path/labels). Per-copilot substantiation map (all 5). Extract-on-second-instance discipline (SOC=1, S2P/R18=2). Scraped≠synthetic fix; oracle=pipeline-not-magnitude fix; plumbing-vs-power split. Narrative integration (tier→sales language, day-zero arc, honesty-as-moat). Sequencing + open questions for roadmap/llm-judge. |
| v1.1 | June 19, 2026 | **Specificity pass — grounded in MAP v5.190.** (Part 9) Generated-data taxonomy: 4 kinds — K1 oracle-behavioral, K2 factor-vector oracle, K3 demo-population fixture, K4 scraped-external — each mapped to substantiation tier + Rule-63 provenance tier, with the K1/K2-never-surface and K3≠K4 bright lines. (Part 10) Per-copilot synthetic-data spec with concrete schemas, generators, and MAP status (✅/⚠️/🔨): SOC γ-oracle DONE + AnalystOracle pending; Trading MarketDataProvider as the K4 exemplar; Purchasing 50/500/12-archetype generator as the highest K3 risk; S2P BuyerOracle conditional holdout as instance-2; DataOps oracles new. (Part 11) Exact MAP delta: §17 SUBSTANTIATION DECLARATION block; Rules 66/67; F-26/F-27; P39 amended as instance-2 anchor; new items P-SUBST-CORE / P-SOC-ORACLE-PLUMB / P-FIXTURE-LABEL-AUDIT / P-S2P-BUYER-ORACLE; ~1.5d discipline sprint sequenced parallel to the feature queue. |
| v1.2 | June 19, 2026 | **Review-completion pass (7 items + narrative bridge).** Load-bearing: (1) Oracle now models CORRECTNESS not just action (`known_accuracy_effect`, `correct` in outcome) — fixes the `correct:True` bug that made the accuracy guard untestable; P-SOC-ORACLE-PLUMB gains Experiment 4 (positive lift + negative accuracy → gate correctly rejects). (2) Purchasing day-zero demo composition stated honestly (>80% K3 until K4 ships); added P-PUR-COMMODITY-K4 as a demo-credibility prerequisite. (3) Power-analysis split into FLOOR (gaussian, now, lower-bound) vs CALIBRATED (pilot) — resolves the §9.3-vs-defer contradiction. Refinements: (4) §17 declaration trigger narrowed to intelligence/metric features (CLI/packaging/infra/migration exempt). (5) SOC threat_intel_enrichment K3/K4 ambiguity flagged as a live F-26 candidate; P-FIXTURE-LABEL-AUDIT resolves per-factor source. (6) Noted F-24 is the generalization of the already-enforced CC-21 Tier-2→Tier-1 discipline. (7) `promote()` uses `asdict()` not `__dict__`. Plus Part 12 publication anchors (arxiv v7.2 / ci_blog v15 / gen-ai-roi E-06 / demo scripts) tying the internal discipline to the external narrative. |
| v1.3 | June 19, 2026 | **Executability pass (10 items) — reflects MAP through P72 done.** (1) Honest effort: NOW sprint is ~4d not 1.5d (P-SOC-ORACLE-PLUMB 1-2d, P-FIXTURE-LABEL-AUDIT 1d). (2) Provider protocols (Oracle/HoldoutAssigner/RealInstrument/…) moved from Part 4 to Part 5 as *candidate contracts* validated after instance 2; only ClaimProvenance/ClaimRegistry/DayZeroReadiness ship now. (3) Concrete P-PUR-COMMODITY-K4 spec (CommodityDataProvider, USDA-ERS/FRED candidates, MarketDataProvider cascade, 24h TTL, labeled fallback). (4) Per-copilot DEFAULT declaration templates (fill-in, ~10min→~2min). (5) Rule 66 stated explicitly as EXTENDING Rule 63 (one review pass, not duplicate); Rule 67 is the new K-taxonomy. (6) Narrative moved to FRONT (Part 0.1: pitch + one-liner + tier→language); Part 6 trimmed to the strategic detail. (7) `analyst_action` escalated to a TODAY Step 0 (P-SUBST-STEP0) — reconciled with Campaign Step 1 CLOSED: verify it persists AND joins to campaign_context_shown. (8) Items slotted into §3A as a parallel Substantiation Sprint with real-MAP#-pending. (9) Per-copilot map now carries MAP cross-refs + flags (no MAP item) gaps. (10) §3A dependency note (parallel to Tier 5, no copilot-sdk file overlap). **P72-done sharpening:** P68 food-cost + P72 auto-approve are LIVE metric surfaces → any K3-fed metric is a live F-26 today; Purchasing K3 audit + P-PUR-COMMODITY-K4 are near-immediate, not future. |
| v1.4 | June 19, 2026 | **Prompt-audit focus pass (§11.3+).** Expanded §11.3 from a 3-row sketch into a full prompt-by-prompt audit of the live MAP: ~37 existing prompts touched, classified **A** CODE+LABEL (4 — P64 label-at-source, P68/P72 live-F-26 audit, P71 Purchasing outcome-join), **B** DECLARATION+LABEL-CHECK (~18 shipped prompts surfacing metrics: P36/P37/P40/P41/P46/P47/P49/P53/P54/P55/P63/P69/P70/P42/P43/P34/P30-P32/P45), **C** DECLARATION-ONLY (~7 already provenance-aware: P38/P44/P50-exemplar/P59/P60/P66), **D** PENDING full-declaration-at-authoring (~8: P39/P73/P74/P75/P81-P84/R18), **E** EXEMPT (~11: P29/P48/P52/P57/P61/P62/P76-P80) + SOC factor-source audit (non-P#). §11.4 gains a 7-row new-prompts summary table (P-SUBST-STEP0/CORE, P-SOC-ORACLE-PLUMB, P-FIXTURE-LABEL-AUDIT, P-PUR-COMMODITY-K4, P-S2P-BUYER-ORACLE, pilot-run-up oracles). No direction change; specificity only. |
| v1.5 | June 19, 2026 | **Review pass (7 items) — connects the framework to the campaign-arc closeout.** (1) P-SUBST-STEP0 → ✅ CLOSED: Campaign v6.0 closeout Scan 2 already proved outcome persistence (analyst_action/was_override/quality_signal persist; Decision node carries both treatment flags + outcome) → sprint ~4d → **~3.75d**. (2) Class-A prompts gain concrete discovery grep commands (P64/P68/P72/P71) so each audit is Codex-executable. (3) P-FIXTURE-LABEL-AUDIT split into Phase 1 (audit, in the 3.75d) and Phase 2 (labeling mechanism — only Trading has `ProvenanceBadge` today; recommended: add a `provenance` data-model field for enforcement, badge display as per-copilot follow-on). (4) P-SOC-ORACLE-PLUMB cross-references narrative_evaluation_v2_0 §9.2-9.3 as the oracle design source, extending (not re-specifying) it with the v1.4 corrections. (5) Class-B honest effort ~15-20 min/prompt (read+determine+discover), ~5-6h total, absorbed into the audit. (6) Part 12 publications get file versions + existence (arXiv = v7.6 supersedes v7.2; ci_blog_v15 exists; gen-ai-roi E-06 not yet written). (7) Part 10 SOC states the division of authority: THIS doc = cross-copilot framework; narrative_evaluation = SOC-specific application (oracle code lives there). |
| v1.6 | June 19, 2026 | **Execution-layer pass (7 items) — session/repo + prompt-stage integration.** (1) P39A/P39B are SHIPPED → instance-2 is new scope (P-S2P-BUYER-ORACLE), not a P39 amendment; all "amend P39" references corrected (Parts 5/7/11.3). (2) Corrected the wrong "no copilot-sdk overlap" claim: P-SUBST-CORE / commodity / PUR-audit are Session-A copilot-sdk work → added a session/repo mapping; P-SUBST-CORE slots BEFORE P73. (3) P-FIXTURE-LABEL-AUDIT split per-repo per-session: AUDIT-PUR (A), AUDIT-S2P (B), AUDIT-SOC (C), AUDIT-SDK-TRD/DO (A) — each ~2h read-only. (4) Class-A made a dependency chain (audit → P64-LABEL → P-PUR-COMMODITY-K4 → P68-FIX/P72-FIX) with explicit fix prompts; the connector is the long pole, not "near-immediate." (5) §17 declaration placed in Stage 2 (alongside BACKEND COMPATIBILITY/NON-NEGOTIABLES) + Stage 3 review checklist item + Codex Playbook §3.12. (6) Class B reframed: shipped code can't take a declaration — it needs ClaimRegistry *entries* (data entry via populate_claim_registry.py inside P-SUBST-CORE), not 18 prompt edits. (7) P-SOC-ORACLE-PLUMB sequenced in Session C after Step-5 fix + P89 (~4d Session-C total; capacity noted). 11.5 rewritten session-keyed. |
