# Trading Copilot — FINAL Consolidated Addendum (merge-ready)
**Base document:** `trading_copilot_product_definition_v1.md` (Drive design folder, id `1vRiGKEGkY8TyjFH2ysyYoiVKZHPZAKT0`).
**Merge state:** no Trading addenda are merged yet. **This file folds ALL THREE pending addenda** — `trading_copilot_doc_additions_v1` (the change-map v3 operationalized, §A–§F), `_v2` (the body-verified correction pass, §TV2-0..5), and `_v3` (the innovation-note/outreach/scenario-prompt alignment, §RV3-1..5).
**Two overriding constraints (both addenda):** (1) **NO regulatory exposure** — Trading is the public OSS copilot and it touches money, so §A (observation-only) is the dominant edit and counsel sign-off is a hard pre-ship gate; (2) **nothing is cut** — scenarios are *gated*, never deleted. Trading is deliberately the analytical **mirror**, not a bot: *"TensorTrade automates the trader; we make the trader see themselves."* Everything is observation on the trader's own past decisions — never a forward call, never execution.

---

## §3 / §3.5 — Convert scenarios from advice to observation-only (v1 §A + v2 §TV2-0) — the dominant edit
Add a boxed rule at the top of §3 and §3.5 and extend the §C.3 "frame as data, never judgment" rule **doc-wide**:
> Every on-screen line is a **past-tense observation about the trader's own verified decisions, carrying its N.** No forward directive (reduce / increase / rotate / hold / wait / skip), no present-tense market claim ("premium is rich," "IV is rich," "edge is ON"), and **never a market fact and a personalized claim in one sentence.** The conservation law governs the engine's **own** scoring autonomy, never the trader's account.

v2 §TV2-0 verified the advice-shaping is **pervasive** (verbatim: T17 *"premium is rich… EDGE IS ON… Recommendation: increase premium allocation 30%"*; T5 *"Safe to increase $20K→$35K"*; T16 *"INCREASE 40% … DECREASE 60% … ROTATING"*; §3.5 *"ROTATE to it"*; and T2/T3/T4/T7/T9/T13/T14/T18/T20 each close with a forward directive) — so **§A is not optional.** Worst offenders to rewrite (full table in `trading_document_update_changemap_v3.md` §A):
- **T17 (#1 fix):** → *"when VRP (B7) was in its top quintile, **your** short-vol entries returned X% (N=34) vs Y%"* (adopt the demo doc's observation-framed **TRD-V5**).
- **T5 (scale):** → *"at $35K-equivalent sizing your history clears α·q·V ≥ θ_min; at $50K it does not (insufficient verified trades)."*
- **T16 (volatile edge):** strip every INCREASE/DECREASE/ROTATE → *"historically your income-strategy accuracy was 71% at VIX 25–35 vs 58% at VIX<20 (N=..)"*; **rewrite the §3.5 "ROTATE to it" pitch line** (the most advice-shaped sentence in the doc).
- **T3, T4, T9, T14, T18, T20:** strip "Recommendation:/switch/reduce/hold/wait," append N.

## §13 / new App F — Regulatory Posture (v1 §B), a hard pre-ship gate (v2 §TV2-2)
Expand §13-Q5's three lines into a load-bearing Regulatory Posture section that matches the now-observation-only scenarios:
- **Observation-only** stated as a product invariant (the §3 rule).
- **Local-first as regulatory architecture, not a privacy feature** — personalized inference runs on the trader's machine; monetize impersonal infrastructure (hosting, connectors, seats) and **take no compensation for the personalized inference itself** *(this constrains the §6 business model — decide the OSS-vs-hosted line for the inference)*.
- **Self-governing engine boundary** — governs its own scoring/auto-sizing, issues no broker/account instruction. **No discretion, no execution, no account access.**
- **Counsel sign-off is a hard gate on ANY ship, the OSS core included** (v2 §TV2-2). `pip install ci-trading` is a public distribution of the advice-shaped surfaces until §A lands and counsel signs off. §A/§B make the product *reviewable*; they do not make it *cleared*.

## §4 / §5 / §7 / §3.5 / §E — Positioning + capabilities (v1 §C + v2 §TV2-3, §TV2-5)
- **§5 Competitive Test + §E competitors — refresh the stale 2022 frame.** Add **TradeZella + Zella AI** as the 2026 entrant (they market "the AI trading partner that remembers"); **demote capability #1 (the mirror) from differentiator to category-entry.** Re-lead §1/§5 on **abstention + the evidence gate + rigor.**
- **§4 + §7 — ADD capability/feature #8: the selection-adjusted evidence gate ("Claim Gate," F16).** BH-FDR across detectors + deflated Sharpe + discover-70/confirm-30 + "23 hypotheses tested" badge. **It is the #1 build** (v2 §TV2-3): it **fixes T1** (the "favorite setup is worst" false-discovery artifact — ~25 detectors × a few-hundred-trade history at α=0.05 hands even a leak-free trader 1–2 "expensive truths" by construction; a hostile quant kills the product on it otherwise), and it is **§A's legal backbone** (every claim ships with its N, effect, and survived-correction status — an observation that cleared a gate, not a recommendation). Build it as **Trading's instance of the shared platform evidence-gate SDK** ("K hypotheses tested, M survived"), not a bespoke one. Frame: the conservation law applied to claims instead of autonomy.
- **§3 + §4 — ADD abstention / autonomy-throttle** (the demo's TRD-S3; currently absent from this doc) — lowest legal exposure, governs the engine not the account. **Name abstention as a product capability** (v2 §TV2-5), don't leave it implicit (`skip_recommended` action 3 + conservation-pause on auto-sizing already exist as substrate).
- **§E.4 — reframe "can't" → "won't."** Vol math (#5/#7) and regime-conditioning (#2) are a groupby + a library, not structurally blocked; what's blocked by **business model** = abstention, the gate, local-first OSS. State that instead of the fragile "18+ months of math" claim.
- **§3.5 — upgrade the vol math to the shipped B1–B8 substrate.** Replace `CorrelationMonitor`'s Pearson with **B5 basket-variance + B6 stress-conditioned tail dependence**; **un-defer T17** (B7 model-free VRP now ships); note B1/B2/B4 under the regime + deflated-Sharpe machinery.
- **§3 — ADD the clean-trader / D-null scenario:** the certificate (gate output) + edge-boundary map — pure self-audit, safe.

## §3 / §5 / §E — Preserve & gate: nothing cut (v1 §D + v2 §TV2-1)
**T1, T3 (Friday), T20 (VIX timing) STAY**, routed through the F16 Claim Gate so they surface only when they survive correction for that trader (N + effect shown). T11 (History Unified) stays as supporting import plumbing (§7 F1/F7). **The gate replaces "kill" with "gate."**
> **★ Supersession (v2 §TV2-1):** `trading_review_consolidation_v1`'s "**Kill T3 / T20**" (its §1 and §7) is **SUPERSEDED — do NOT apply it to the design doc.** §D governs: gating, not deletion. This preserves "nothing removed" and still defuses the false-discovery risk.

## §7.5 / App B — Extensions (v1 §E), honestly tiered (v2 §TV2-4 + v3 §RV3-3)
- **Pre-trade belief capture — the only *real* data moat · ARCH-pending-BUILD-SPEC.** A 10-second entry capture of conviction + planned invalidation — a prospective belief-trace that **cannot be retro-filled from a broker export**, makes T1 *causal* not correlational, and is the answer to "whose moat is it?" It has **no build spec** — design it (capture UX, storage in the local `~/.ci-trading/` schema, how it feeds F9/B.5 without becoming a forward-looking signal); don't just name it.
- **Counterfactual replay / signed `.jmt` proof-of-edge** — *"your P&L had you followed your own rule"* (about the past → safe); privacy-preserving export (no positions) for prop-firm/social proof. **This is Trading's compounding-control artifact** (a day-1 frozen twin is less applicable here — v2 §TV2-5); treat the replay as the ARCH-pending-spec control.
- **Parasitic distribution · needs a concrete connector spec.** The §8 import connectors ARE the wedge — read *their* TradeZella/Tradervue CSV, don't race 500+ broker integrations. Needs a real spec: their export schema → `NormalizedTrade` mapping, per source. Until specced, it's a direction, not a deliverable.
- **Name Judgment Memory (⑥b) for Trading (v3 §RV3-3):** the graph remembers the trader's **judgment**, not just fills — **provenance** (verified-trade lineage) · **quality axis** (the gate's selection-adjusted confidence) · **counterfactual replay** (the `.jmt` artifact) · **pre-trade belief capture** (the causal layer). Tier honestly (belief capture + `.jmt` = ARCH-pending-BUILD-SPEC; regime-indexed JM = ARCH). This is what separates the mirror from TradeZella's compounding-memory claim: theirs remembers trades; ours remembers *judgment*, gated for false discovery.

## NEW hardening invariants — SAFE-2 + SAFE-4 as testable product invariants (v3 §RV3-2)
The scenario-improvement prompt encodes five SAFE items; §A (SAFE-1 advice→observation), §B (SAFE-3 posture), and F16 (SAFE-5 badged/day-zero numbers) are covered — **add SAFE-2 and SAFE-4 as first-class, testable ship-gates** (they gate the OSS launch as much as §A):
- **SAFE-2 — observation-only architecture (no execution path):** no reachable order/execution/broker-write endpoint in the OSS build; BYOD import writes **observations, not decisions** (`write_observation`, never `write_decision`). Tests: `test_no_execution_endpoint`, `test_byod_is_observation_only`.
- **SAFE-4 — data locality:** raw imported trade rows never leave the machine; stated in UI + README. Test: `test_no_trade_data_egress`.
These join §A/§B and the counsel sign-off as the OSS-launch gate set.

## Compounding tier (v2 §TV2-5 + v3 §RV3-5) — standing guard
Trading is the copilot where "compounding is live" is **least** true: the product is defined-not-built and the RL loop (§C.1 3-signal: outcome 0.3 + R-multiple 0.3 + execution-quality 0.4; prototype is the (5,3,6) tensor) is **DESIGNED, not WIRED.** The same one-grep check applies at build time; **never claim compounding as LIVE** until it does. Tiers: TRD-S3 throttle = LIVE(demo)/NEAR(product); vol beats = NEAR; **TRD-S7 re-convergence = ARCH** (the second-derivative story here, measured only by EXP-REGIME). Time-to-competence on a new strategy/regime — not IKS level, which saturates — is the non-saturating metric if one is wanted.

## §F / §6 — Still open (record in the doc) (v1 §F + v2 §TV2-2)
This de-risks the **language** (§A) and the **architecture** (§B) but does **not** settle overall positioning: top-of-funnel framing, how pre-trade surfaces + belief-capture are described without becoming forward-looking, the ToS/disclaimer posture, and the **OSS-vs-hosted line for the personalized inference.** Next design problem, with counsel.

## Moat name-which-of-two — applies only weakly (v3 §RV3-4)
The enterprise "cross-customer priors vs integration depth" frame does **not** transfer cleanly to a local-first individual-trader OSS tool (cross-customer priors would require pooling private trade data — contradicts SAFE-4/local-first). State *why*, so its absence reads as deliberate: Trading's moat is **"won't, not can't"** (abstention + the selection-adjusted gate + local-first OSS — an engagement-monetized tool won't ship the gate) **plus pre-trade belief capture** (the trader's own, exported with them).

---
> ### ⛔ Already-actioned cross-doc flag — do NOT merge into this design doc
> **v3 §RV3-1 — outreach Trading copy.** The outreach doc's advice-shaped Trading copy (the "ROTATE pitch," "premium is rich… edge is ON") and its stale 2022 competitor set were flagged; both were **fixed in `outreach_elevator_pitches_v6_1.md`** (→ "the regime read," past-tense observations, TradeZella foil). The Trading design doc already carries the observation-only rule (§A) and the TradeZella refresh (§C) — do **not** import the old outreach copy here. (Standing guard only.)

*FINAL consolidation of `trading_copilot_doc_additions_v1` (§A–§F) + `_v2` (§TV2-0..5) + `_v3` (§RV3-1..5) → `trading_copilot_product_definition_v1.md`. Supersession: v2 §TV2-1 — the review-consolidation's "kill T3/T20" is NOT applied (gated, not cut). Cross-doc flag §RV3-1 already actioned (outreach v6.1) — excluded. Overriding constraints unchanged: no regulatory exposure; nothing cut; counsel sign-off gates the OSS launch. Companion demo delta lives in the demo-scenarios track.*
