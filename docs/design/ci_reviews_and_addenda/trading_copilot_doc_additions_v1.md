# Trading Copilot Doc — Additions (v1)
*Additions/edits to `trading_copilot_product_definition_v1.md` (fileId 1vRiGKEGkY8TyjFH2ysyYoiVKZHPZAKT0). Operationalizes change-map v3; this is the clean "what to add to each section" version.*
**Two standing decisions:** (1) **NO regulatory exposure** is the overriding constraint — §A is the dominant change; (2) **NOTHING is cut** — scenarios are preserved and gated, never deleted. Final overall positioning is still an **open problem** (see §F). Counsel rules; this is framing for counsel.
**Why this doc needs more than the demo doc:** unlike the demo storyboard (already observation-framed and vol-evolved), this product-def doc is **pervasively advice-shaped** — that's the real exposure, and §A fixes it.

---

## §A — Convert the scenarios from advice to observation-only (the dominant edit). *§3, §3.5.*
Add a boxed rule at the top of §3 and §3.5, and extend the existing §C.3 rule ("frame as data, never judgment") **doc-wide**:
> Every on-screen line is a **past-tense observation about the trader's own verified decisions**, carrying its **N**. No forward directive (reduce / increase / rotate / hold / wait / skip), no present-tense market claim ("premium is rich," "IV is rich," "edge is ON"), and **never a market fact and a personalized claim in one sentence.** The conservation law governs the engine's **own** scoring autonomy, never the trader's account.

Worst offenders to rewrite (full per-scenario table in `trading_document_update_changemap_v3.md` §A):
- **T17** (the #1 fix): "IV/RV 1.72 (premium is rich)… edge is ON… increase allocation 30%" → keep only "when VRP (B7) was in its top quintile, **your** short-vol entries returned X% (N=34) vs Y%." *(Adopt the demo doc's already-observation-framed **TRD-V5** wording.)*
- **T5** (scale): "safe to increase $20K→$35K" → "at $35K-equivalent sizing your history clears α·q·V ≥ θ_min; at $50K it does not (insufficient verified trades)."
- **T16** (volatile edge): strip every INCREASE/DECREASE/ROTATE → "historically your income-strategy accuracy was 71% at VIX 25–35 vs 58% at VIX<20 (N=..)"; **rewrite the §3.5 "ROTATE to it" pitch line** (the most advice-shaped sentence in the doc).
- **T3, T4, T9, T14, T18, T20:** strip "Recommendation:/switch/reduce/hold/wait," append N (see change-map §A).

## §B — Add a Regulatory Posture section (expand §13-Q5 into its own §, or App F). *§13 / new App F.*
§13-Q5 answers "is this advice?" in three lines; make it load-bearing and match the now-observation-only scenarios:
- **Observation-only** stated as a product invariant (the §A rule).
- **Local-first as regulatory architecture, not a privacy feature** — personalized inference runs on the trader's machine; monetize impersonal infrastructure (hosting, connectors, seats) and **take no compensation for the personalized inference itself** *(this constrains the §6 business model — decide the OSS-vs-hosted line for the inference)*.
- **Self-governing engine boundary** — governs its own scoring/auto-sizing, issues no broker/account instruction.
- **No discretion, no execution, no account access.** Disclaimer + **counsel sign-off gate** before the `pip install` launch.

## §C — Positioning updates. *§4, §5, §7, §3.5, §E.*
- **§5 "Competitive Test" + §E competitors — refresh the stale 2022 frame.** Add **TradeZella + Zella AI** as the 2026 entrant; **demote capability #1 (the mirror) from differentiator to category-entry.** Re-lead §1/§5 on **abstention + the evidence gate + rigor.**
- **§4 + §7 — ADD capability/feature #8: the selection-adjusted evidence gate ("Claim Gate," F16).** BH-FDR across detectors + deflated Sharpe + discover-70%/confirm-30% + "23 hypotheses tested" badge. It is the #1 build, it **fixes T1** (the "favorite setup is worst" false-discovery risk must pass the gate), and it is §A's legal backbone (every claim ships with its N and effect). Frame: **the conservation law applied to claims instead of autonomy.**
- **§3 + §4 — ADD the abstention / autonomy-throttle capability** (currently absent from this doc; it's the demo's TRD-S3). Lowest legal exposure — governs the engine, not the account.
- **§E.4 "Why Competitors Can't Replicate" — reframe "can't" → "won't."** Vol math (#5/#7) and regime-conditioning (#2) are a groupby + a library, not structurally blocked; what's blocked by **business model** = abstention, the gate, local-first OSS. State that instead of the fragile "18 months of math" claim.
- **§3.5 — upgrade the vol math to the shipped B1–B8 substrate.** Replace `CorrelationMonitor`'s **Pearson** with **B5 basket-variance + B6 stress-conditioned tail dependence**; **un-defer T17** (B7 model-free VRP now ships); note B1/B2/B4 under the regime + deflated-Sharpe machinery.
- **§3 — ADD the clean-trader / D-null scenario:** the certificate (gate output) + edge-boundary map. Pure self-audit → safe.

## §D — Preserve & gate (nothing cut). *§3, §5, §E.*
T1, T3 (Friday), T20 (VIX timing) **stay** — routed through F16 so they surface only when they survive correction for that trader (N + effect shown). T11 (History Unified) **stays** as supporting import plumbing (§7 F1/F7). The gate replaces "kill" with "gate."

## §E — Extensions to add to the roadmap. *§7.5, App B.*
- **Pre-trade belief capture — the only *real* data moat.** Add a 10-second entry capture of conviction + planned invalidation (F9/B.5 record signals, not belief) — a prospective belief-trace that **can't be retro-filled from a broker export**, makes T1 causal, and answers "whose moat is it?" Local → safe.
- **Counterfactual replay / signed ".jmt" proof-of-edge artifact** — "your P&L had you followed your own rule" (about the past → safe); privacy-preserving export (no positions) for prop-firm/social proof. Extends §C.5.
- **Parasitic distribution — name it:** the §8 import connectors ARE the wedge — read *their* TradeZella/Tradervue export, don't race 500+ broker integrations.

## §F — Still open (record in the doc)
This de-risks the **language** (§A) and the **architecture** (§B) — the necessary foundation — but does **not** settle the overall positioning that keeps regulatory issues from arising (top-of-funnel description, how the pre-trade surfaces + belief-capture are framed without becoming forward-looking, the disclaimer/ToS posture, the OSS-vs-hosted line for the personalized inference). Next design problem, with counsel.
