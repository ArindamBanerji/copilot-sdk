# Demo Scenarios & Use Cases — Consolidated · v2.9

**Date:** September 13, 2026 · **Version:** 2.9
**Purpose:** the single source of truth for the demo storyboard + use-case scenarios, **executable for
coding sessions** (every beat carries a surface, API, data need, DoD, and session owner).

**New in v2.9:** four Trading/Purchasing VLD beats; nine total ARCH investigation beats; domain wiring and preseed contracts; Room-16 and Loom extensions; Q, starvation, missing-evidence, experiment and terminology corrections.

**v2.2 — DataOps DI beats + v2.1 presenter technique + competitive Q&A + S14 contrast enhancement.**
1. **§2.5 "silence beats" added** — the three moments where the presenter STOPS TALKING and lets the
   audience read the screen. These are emotional, not informational — the silence is the technique.
2. **§0.3 competitive tear-down lines** — per-room "when they say X, you say Y" one-liners for live
   Q&A. The §2.4 scripts are monologues; a VC will interrupt. These are the interruption answers.
3. **§4.2.1 S14 rule-vs-reasoning contrast** — a side-by-side showing what a rule-based system would
   have done with the same invoice, next to what the SituationPanel produced. The contrast makes
   S14 category-defining, not just impressive. ~0.5d frontend build.

**v2.0 — brought current with `next_steps_strategy_v1_21` and `product_integrity_execution_strategy_v3_0`:**
1. **Scenario classes (LIVE / NEAR / ARCH)** now travel with every beat (product_integrity §2.8). Showing
   roadmap is *allowed and expected* — implying roadmap is LIVE is the only violation (**F-27**).
2. **§0.1 room→kill-shot map** — beats are now indexed by **competitive room** (next_steps §2.2/§2.3), not
   only by copilot. *10 of 15 rooms have a LIVE kill shot.*
3. **Naming purge (F-25):** the primary learning mechanism is **decision-trace / prototype learning from
   verified decisions — NOT "RL."** (Genuine bandits exist and may be named as such.)
4. **⚠️ SOC learning is DISABLED by default** — a **demo-truth** constraint on every SOC "watch it learn"
   beat (§5).
5. **New Trading material:** TRD-S1..S7 (situation-conditioned) and TRD-V1..V7 (volatility) — including
   **TRD-S7 "The Re-convergence Moment"**, the strongest technical beat available to us.
6. **New enterprise beat: ENT-1 "The Sunk-Investment Multiplier"** (the Celonis wedge).
7. **C-17 is scoped** (one open F-24): say *"one conservation law governs our scoring, exploration and
   scorer-evolution loops"* — **not "all loops"** — until `C-GOV` lands.

**Companion to:** `next_steps_strategy_v1_21.md` (strategy + §9 build list),
`product_integrity_execution_strategy_v3_0.md` (the gates), `outreach_use_scenario_catalog.md` (§3.1),
`narrative_readiness_v3.md` (platform state).

**Prior versions:** v1.3 reconciled with `outreach_use_scenario_catalog.md` (§3.1); v1.2/v1.1 reconciled with
next_steps §9 and added presenter scripts + the Loom program. **Extracted from:** `demo_build_hero_doc`
(June 1, 2026) — its narrative frame and beat structure are preserved; its build list and gating are
reconciled to current reality below. **Not in scope:** outreach/collateral. This doc gives *clarity on what
the demo shows and what coding sessions must guarantee.*

---

## 0.1 The room → kill-shot map (index beats by *competitive room*, not by copilot)

**Why this exists.** Beats were indexed by copilot — a *product-internal* taxonomy. Nobody in a room asks "show
me your Purchasing scenarios"; they ask *"why are you better than Celonis / TensorTrade / Microsoft?"* This map
(from next_steps §2.2/§2.3) turns the catalog into **one weapon per room**.

**Scenario classes travel with every beat** (product_integrity §2.8): **LIVE** = runs today on the pinned
preseed · **NEAR** = shipping this wave (build item exists) · **ARCH** = architecture enables it, labeled
roadmap. *Showing ARCH is allowed and expected. Implying ARCH is LIVE is the violation (**F-27**).*

| # | Room | Kill-shot beat | The line | Class |
|---|---|---|---|---|
| 1 | Agentic governance | **Rejection Moment** (§4.1 / DM-1) | "It promoted an improvement live — then rejected 35 others, and can tell you why each failed." | **LIVE** |
| 2 | Self-improving agents | Rejection + **Counterfactual** (§4.2) | "We shipped the bounded-risk promotion gate the frontier lists as an open problem. Run it: governed vs reward-maximized, same data, side by side (DIFF-1, §4.10, **NEAR**)." | **LIVE** |
| 3 | RL trading (TensorTrade) | **TRD-S3 autonomy throttle** (§4.6) | "It **reduced its own autonomy** because it saw the regime change. No reward-maximizing agent can do that." | **NEAR** (~2d) |
| 3b | RL trading — deep cut | **TRD-S7 Re-convergence Moment** ⭐ (§4.7) | "Replay March 2020. Cold-start relearns from zero. We re-converge faster — we kept the geometry from the last vol spike." | **ARCH** → NEAR on C-REGIME P4 |
| 4 | Volatility / risk | **TRD-V1 + V2** (§4.6) | "Half your 'edge' is unpaid tail risk." / "You're **selling insurance in calm weather**." | **NEAR** (~2d) |
| 5 | Decision intelligence | **The cold mirror** (T1 / TRD-1) | "Your favorite setup is your **worst** setup." | **LIVE** |
| 6 | Process intelligence (Celonis) | **ENT-1** (§4.8) + E5 fusion | "Celonis sees WHERE. SAP sees WHAT. **Only we see WHY** — and the $604K." | LIVE (fusion) / **NEAR** (ENT-1) |
| 7 | Data observability | **DO-4** | "The **$604K** nobody saw." | **LIVE** |
| 8 | SecOps (MS Security Copilot) | **SOC-4 admits failure** + per-analyst η | "The system that **admits failure** — and remembers *your* analysts' judgment." | **LIVE** ⚠️ (see §0.2) |
| 9 | Context / memory (Rowboat) | **Counterfactual** (§4.2) | "They compound **notes**. We compound **judgment** — and prove it moved the decision." | **LIVE** |
| 10 | Agent infra (CopilotKit) | 5 copilots on one engine + cross-copilot signal | "They're the **UI**. We're the **substrate**." | **LIVE** |
| 11 | AI governance / compliance | **Day-Zero honesty** (§4.3) + audit chain | "We **don't fake your number** — and it's audit-traceable." | **LIVE** |
| 12 | Data quality / observability | **DI-TRUST: "Every data asset gets a trust score"** | "Monte Carlo tells you when data breaks. We tell you which data is *worth buying* — ranked by projected ROI to your decision quality." | **LIVE** |
| 13 | Data-as-product / CDO | **DI-PRODUCT: "Data products with IKS"** | "Your customer-360 has IKS 72, GREEN. Any agent can consume it autonomously. Your ESG product: IKS 8, AMBER. The system *measured* the difference from 3,400 verified decisions — not a label in a catalog." | **LIVE** |
| 14 | Agent-trust gateway | **DI-GATEWAY: "We're the runtime trust layer between your agents and your data"** | "Your Databricks agent asks us before it acts — `/v1/trust/verify` → trust, basis, or abstain. A substrate owner won't rate a competitor's table fairly." | **NEAR** |
| 15 | Purchasing / food-cost | **PUR-CONTINUITY: "Everything in this kitchen turns over. This doesn't."** | "They record what you bought. We remember what you learned — and prove what it saved." | **NEAR** |
| 16 | Score-conditioned investigation | VLD-SOC-1; domain alternatives VLD-TRD-1 / VLD-PUR-1; coverage/continuity deep cuts VLD-TRD-2 / VLD-PUR-2 | “The trace shows which evidence was selected first, what it changed, and what remained unchecked. The priority comes from the retained scorer state; the records let you inspect it.” | **ARCH**. NEAR requires the branch-policy prototype, trajectory store and beat-specific domain wiring. LIVE additionally requires the matched deployment evaluation specified in §4.18. |

*Room-16 framing note:* The demonstration establishes an inspectable, scorer-conditioned order on a labeled fixture. A fixed checklist, a static scorer-conditioned plan and an adaptive scorer-conditioned policy are different comparators. The supplied experiment favored static planning on routing, while RNN had higher final accuracy; this does not establish an adaptive-routing advantage. The product hypothesis concerns the value of the retained, verified-outcome-grounded substrate and its governance. Evaluate routing policy separately.

## 0.2 Demo-truth constraints (read before staging any beat — product_integrity v3.0)

Three things the code says that the storyboard must respect. **These are demo-truth (§5 alignment), not
nitpicks — a beat that implies otherwise is a T3 failure.**

1. **⚠️ SOC learning is DISABLED by default** (`soc/config.py:66`; gated at `triage.py:1961-1968`). Trading /
   Purchasing / DataOps / S2P are BUILT end-to-end. **SOC is the flagship VC cut** — so any *"watch it learn /
   compounding"* beat on SOC **will not fire** unless learning is explicitly enabled in the demo profile.
   **C-1 DoD: enable it and prove a verified decision changes a later SOC score — or re-cut the beat to a
   copilot where learning is live.**
2. **Naming (F-25):** the primary mechanism is **not "RL."** It is **decision-trace / prototype learning from
   verified human decisions** — the signal is a *correctness label, not a reward*. Genuine bandits (Thompson /
   UCB) exist and may be named as such. *The reconciled line (v2.5): **"The decision — which action we recommend — is nearest-centroid distance, not reward-maximizing. Reward functions exist in the learning path (exploration + credit), never in choosing the action"
   for judgment"** — exactly what a reward-maximizing agent cannot say (C-18). And **exploration is
   conservation-bounded by construction** (`ConservationBoundedThompson`, C-19).
3. **C-17 is scoped — one open gap (F-24).** Prompt-variant promotion is **not** conservation-gated. Until
   `C-GOV` (~0.5-1d) lands, the spoken line is *"one conservation law governs our **scoring, exploration and
   scorer-evolution** loops"* — **never "all loops."** Also: **no claim of shared cross-copilot judgment
   state** (F-26) — *signals* transfer, judgment geometry is per-copilot.

## 0.3 Competitive tear-down lines (when they interrupt — and they will)

**Why this exists.** The §2.4 scripts are monologues. A VC will interrupt at V2 with "how is this different
from [X]?" An enterprise buyer will say "we already have Celonis." These are the answers. Memorize the
pattern: **acknowledge → reframe → kill shot.** Never dismiss the competitor — elevate the conversation.

| Room | When they say… | You say… |
|---|---|---|
| 1. Agentic governance | "Isn't this just guardrails?" | "Guardrails stop bad things. We do that — AND we let the system propose improvements, test them in shadow, and promote only what survives the conservation gate. Show me another system that *rejected 35 of its own suggestions* and can tell you *exactly why each one failed.*" |
| 2. Self-improving agents | "The frontier labs are working on this." | "They are. They published the open problem last year: self-modify without losing the safety guarantee. We shipped the answer. And we open-sourced it so you can read the gate yourself." |
| 3. RL trading (TensorTrade) | "How is this different from TensorTrade?" | "TensorTrade maximizes a reward function. We don't choose the action by maximizing a reward — the decision is centroid-distance. A reward-maximizer overfits your calm regime; ours doesn't — and you can watch it, governed vs reward-maximized, same data, side by side (DIFF-1, §4.10). Their canonical failure is regime overfitting: train on calm, blow up on crisis. Our system *reduced its own autonomy* because it detected the regime break." |
| 4. Volatility / risk | "We already have risk systems." | "Your risk system measures risk. Ours measures *whether your edge is real or a clustering artifact*. Your calm-regime Sharpe of 2.1 is 1.2 after clustering adjustment. Half your 'edge' is tail risk you aren't paid for. We show you that — your risk system can't." |
| 5. Decision intelligence | "This is just better analytics." | "Analytics tells you what happened. We tell you *what you believe that's wrong* — with proof from your own decisions. Your favorite setup is your worst setup. No dashboard can show you that because it requires learning from verified outcomes, not displaying metrics." |
| 6. Process intelligence (Celonis) | "We already have Celonis." | "Good — keep it. Celonis tells you WHERE the process breaks. We ingest its output and tell you WHY and WHICH DECISION to change. Your Celonis spend just became more valuable, not obsolete. We're the only vendor in this room who makes your existing investment worth *more*." |
| 7. Data observability | "Monte Carlo already does this." | "Monte Carlo tells you when data breaks. We tell you which data is *worth buying* — ranked by projected ROI to your decision quality. That's a different question. Nobody else answers it." |
| 8. SecOps copilots | "Microsoft Security Copilot already does this." | "Bundled copilots answer from what the vendor's model knows. We start you on a strong prior and then learn where **your** analysts' corrections disagree with it — per analyst, per category. When your best analyst leaves, that retained judgment is what a bundled copilot can't reconstruct — and we show it to you in dollars." |
| 9. Context / memory | "Rowboat does memory for agents." | "They compound notes. We compound judgment — and prove it moved the decision. Change a factor, watch the score move. That's not memory — that's institutional knowledge with a math proof." |
| 10. Agent infra (CopilotKit) | "CopilotKit has great agent tooling." | "They're the UI layer. We're the substrate — the thing underneath that makes agents get better, safely, across domains. We run five copilots on one engine. They'd need five separate implementations." |
| 11. AI governance | "We need compliance — is this audit-ready?" | "Every decision, hash-chained, tamper-evident. We don't fake your day-one number — we show you the instrument working and the proof it's calibrated. And we're sixteen months ahead of the EU high-risk deadline." |

| 5. Trading journal (TradeZella) | "TradeZella already does an AI trading journal." | "Good — that proves the category. The difference is what happens when the data's thin: TradeZella always has an insight for you; ours refuses the ones that don't survive correction, and it reduces its own autonomy when the regime breaks. A journal that always talks can't do either." |
| 14. Agent-trust gateway | "We already have Databricks/Snowflake governance." | "They govern WHO may act. We govern WHETHER the action should be trusted — from verified outcomes, not from permissions. A substrate owner won't rate a competitor's table fairly; we're cloud-neutral." |
| 15. Purchasing/food-cost tools | "We already have MarketMan / xtraCHEF." | "Keep it — it stores your orders and invoices. We sit on top and improve the decisions, and we prove it in dollars you can defend. Their number is a marketing estimate; ours subtracts what you'd have caught anyway." |
| 12. Data quality (Unity Catalog) | "Isn't this Unity Catalog lineage + a dashboard?" | "Unity Catalog records static schema dependencies with zero memory of resolution outcomes. Ours shows Table A's trust drops on Tuesdays from vendor lags — and blocks an agent from writing to Table B until it's resolved." |
| 12. Data quality (Monte Carlo) | "Monte Carlo already learns patterns." | "Rolling thresholds on metrics that don't learn from human resolutions. Resolve a false positive here and it updates decision centroids across all 10 related pipelines." |
| 12. Data quality (p-hacking) | "Your gold lines are p-hacking." | "FDR-corrected and held out 30 days before a line is drawn." |
| 16. Investigation | “Our agents investigate too.” | “Then compare the evidence priority, its recorded basis, and the stopping behavior. This preview makes all three inspectable. Whether that improves decisions at the same budget is an empirical question.” |
| 16. Investigation | “We have graph-based reasoning.” | “Graph access is useful here too. Our proposed contribution is a scorer-conditioned choice of what to retrieve, with an evidence trace and a bounded action gate. Graph access alone does not establish the value of that choice.” |
| 16. Investigation | “We use RAG with reasoning.” | “Iterative retrieval can also change its next query. Our comparison asks whether priority derived from this deployment's verified decisions improves results under the same evidence budget. We need to demonstrate that, rather than infer it from the architecture.” |
| 16. Trading | “We already measure portfolio correlation.” | “Keep that source. In this planted historical replay, the score selected the portfolio check first and the retrieved exposure changed the assessment. The trace connects the source to the decision.” |
| 16. Trading | “Does checking more factors solve the problem?” | “Coverage and routing quality are different. Our supplied experiment reduced unvisited Trading pairs with exploration, but routing worsened. This preview shows an unchecked options factor explicitly; it doesn't promise that more reads solve it.” |
| 16. Purchasing | “Our purchasing system stores supplier history.” | “That history is an input. This preview shows when delivery evidence was requested, how it changed this order's assessment, and which verified records the incoming manager can inspect.” |
| 16. Purchasing | “An ordering rule can check demand and waste.” | “It can. Here you can inspect why the event check preceded the waste check for this case. A static plan may work just as well; the comparison must use the same evidence and budget.” |

**Standing caveat for Room 16 (F-27):** “These Trading and Purchasing domain paths are an architecture preview. The supplied materials report investigation preseeds and offline experiments; this document does not establish that the production entity links, historical filters, providers and trace surface are shipped. We will show the implementation status and distinguish a computed fixture replay from a proposed storyboard.”

**The meta-pattern for any unexpected competitor:** *"They solve [X problem] well. We solve the layer underneath: how does the system that solves [X] get better over time, safely, without authority creep? That's the missing layer — and it's why 88% of AI pilots fail on governance."*

| 12. Data quality | "We already have Monte Carlo / Great Expectations." | "They tell you when data breaks. We tell you which data *to buy next* — ranked by projected ROI. We derived that from DK weights on your verified decisions. Nobody else connects data quality to decision quality." |
| 13. Data-as-product | "We have a data catalog with quality scores." | "Your catalog labels assets manually. We *measure* trust from verified outcomes — 3,400 decisions prove your SAP data is 94% reliable and your Salesforce is 67%. That's not a label, it's a theorem." |

---

## 0. Reconciliation — what changed since the June-1 hero doc (read first)

The hero doc was written when the platform was mid-build and conservation was RED. **It is now
feature-complete (122/122, 27/27 tabs, ~9,315 tests, 0 failures).** So most of its "build" items are now
"stage/wire," and its gating is cleared. Coding sessions must not resurrect superseded items:

| Hero-doc item | Then | Now | Action |
|---|---|---|---|
| **P0 — conservation RED (Ghost Problem)** | blocked the refusal beat | **GREEN / working** (V=verified-only) | cleared — refusal beat is stageable |
| **L5 — Mirror substrate to AGE** | pending | **DONE** (AGE live, centroid/DK persisted) | cleared |
| **D2 — SOC α = "Option C"** | gated SOC numbers | assume resolved — `[VERIFY]` SOC conservation numbers before quoting | verify, don't rebuild |
| **"Mirror tab" (#120)** | proposed new leftmost tab | **NOT built as a tab** — the mirror *moment* lives in **Analysis** (Trading T1 Trust Radar, Purchasing I1) | **do not build a Mirror tab**; stage the mirror from Analysis |
| **#121-#127 build list** | net-new | mostly **shipped** under existing surfaces | treat as stage/wire; see Part 4 for the genuinely net-new |

**What survives from the hero doc (and is preserved here):** the narrative frame (§1), the mirror-open
sequencing, and the beat inventory (folded into §2/§4).

---

## 1. The narrative frame (unified — hero-doc spine × the three differentiators)

**The spine (umbrella line):**
> **Automation executes what it was told. Autonomy discerns what's right.** Everyone else ships a faster
> script over a static graph; we ship judgment over a living one — and we *prove* it, *govern* it, and
> *compound* it across five domains.

**The sequencing principle (from the hero doc — keep):** *open on the mirror, close on the moat.* A live
audience decides in ~90 seconds. Open with the emotional, provable "I need this" (the mirror: *the factor you
trust most is statistically your worst predictor — here's proof about you*), then earn the rational "and I
can't lose it once I have it" (the moat: compounding).

**The three proof pillars — *deployability* (reconciled with next_steps v1.8 §2.0/§3): the demo makes these
*visible*, not asserted.** Frame: self-improvement is table stakes; the demo proves *deployable* self-
improvement — **Compounding Intelligence = the governed compounding layer** (the layer above loop/context/
harness engineering; loop engineering makes an agent finish a task, we make the whole system get better at
every task, safely).

| Pillar | The claim (deployability property) | Made visible by | The gap it fills |
|---|---|---|---|
| **P1 · Governed** | every self-modification/autonomy expansion gated by the conservation-law safety proof (one gate, all loops) | Authoring beat + **Rejection Moment** (§4.1) | 88% of pilots fail on governance; "authority creep" |
| **P2 · Grounded** | improvement grounded in *your verified decisions* (provenance tiers), not benchmarks | ProvenanceBadge + **Counterfactual** (§4.2) + **Day-Zero** (§4.3) + S14 | frontier optimizes benchmarks (23% of human on real tasks) |
| **P3 · Compounding** | *and* it compounds across your domains (cross-copilot signals) | Transfer lineage + cross-copilot signal | (support — the frontier commoditized cross-domain) |

**The four capabilities (hero-doc innovations, mapped under the pillars):** situation analysis (S14 → P2)
`[VERIFY shipped vs roadmap — next_steps C-VERIFY-L3L4]`, process-tech fusion (CrossGraph → P2/P3),
AgentEvolver/self-computing operations (→ P1), context-graph synthesis (→ P1) `[VERIFY]`. **Plus the honesty
layer** (day-zero + provenance) — the P2 core.

**The "I need this" mechanic:** tell the buyer an *expensive truth about their own judgment* they couldn't
learn any other way, *with proof*, *fast* — then compound the correction.

---

## 2. The demo cuts (storyboard) — ordered beats, each with surface + API + timing

Three cuts. Every beat below is **stageable on shipped surfaces** unless tagged `[NET-NEW]` (→ §4).
All open on the mirror, close on the moat.

### 2.1 VC cut (~7 min) — platform story

| # | Beat | Pillar | Surface | API / data | Time |
|---|---|---|---|---|---|
| V1 | **Cold-mirror open** — "pick the factor you trust most… it's your noisiest, here's proof" | P2 | Trading **Analysis** (Trust Radar / T1) | `/api/fingerprint` + `/api/context/trust-analysis` | 90s |
| COMP-1 | **The compounding curve** — decision-quality vs verified decisions, governed vs frozen baseline; IKS rising | P3 | DI-TIMELINE (single-arm **LIVE**) → two-arm governed-vs-frozen (**NEAR**) | `/api/dataops/cohort-status`, DI-TIMELINE surface | 90s |
| V2 | **Governed self-improvement** — **V2a:** promotion live ("8-point gain, promoted — that's the compounding") **V2b:** Rejection Moment ("and it rejected 35 others — here's why") | P1 | SOC **Runtime Evolution** | `/api/admin/shadow-start`,`/promote-evaluate`; rejection log `[NET-NEW §4.1]` | 90s |
| V3 | **Cross-domain compounding** — transfer lineage: a fix born in security → procurement → dataops, one engine | P3 | Purchasing/DataOps **Performance** (`RuleGenealogyTree`) | genealogy endpoint (shipped) | 60s |
| V4 | **Prove-it's-real** — Counterfactual ("change factor → score moves; feed a sample → refused") | P2 | any scoring surface | `/api/score` perturbation + F-26 gate `[NET-NEW §4.2]` | 60s |
| V5 | **The refusal / red-team** — fire `simulate_failure`, conservation auto-pauses to AMBER | P1 | SOC **Compounding** | `/api/eval/simulate-failure` (shipped) | 60s |
| V6 | **Day-zero honesty** — "day one we show the instrument, not a fake number; it fills in on your data" | P2 | any copilot, fresh-tenant view | day-zero state `[NET-NEW §4.3]` | 45s |
| V7 | Close montage — "loop engineering makes an agent finish a task; **we're the governed compounding layer** that makes the whole system get better at every task, safely. The market spent 18 months proving it: 88% of pilots die on governance. We built that layer first — and open-sourced the proof." | — | — | — | 30s |

### 2.2 Trader self-serve cut (~3 min) — mostly built; open-source lands here

| # | Beat | Surface | API / data | Time |
|---|---|---|---|---|
| TR1 | **BYOD** — import your trades | Trading | `/api/trading/import/csv` (shipped; **observation path**, not decision) | live |
| TR2 | **Mirror on your data** — radar resolves on *you* | Trading **Analysis** | `/api/context/trust-analysis` + `/api/fingerprint` | 60s |
| TR3 | **Edge drift + Rejection Moment** — your edge over time + "the AE tested 47, promoted 12" | Trading **Performance** | `/traders/{id}/edge`; rejection log `[NET-NEW §4.1]` | 60s |

### 2.3 Enterprise cut (~12 min) — buyer-led (SOC shown; swap lead per buyer, §5 of strategy)

| # | Beat | Pillar | Surface | API / data | Time |
|---|---|---|---|---|---|
| E1 | Cold-mirror overlay → authored rule + shadow pass | P1/P2 | SOC **Runtime Evolution** | `/api/admin/shadow-start`,`/promote-evaluate` | 120s |
| E2 | **Why?** — situation analysis explains a decision (cite, don't assert) | P2 | SOC **Alert Triage** | `/api/soc/judgment/explain` | 120s |
| E3 | **Promotion + Rejection** — AE promotes a winner ("8-point gain, live"), THEN conservation declines an expansion; AE rejects variants | P1 | SOC **Compounding** | `/api/soc/interventions`; rejection log `[NET-NEW §4.1]` | 90s |
| E4 | **Red-team** — `simulate_failure` → AMBER | P1 | SOC **Compounding** | `/api/eval/simulate-failure` | 60s |
| E5 | **Process-tech fusion climax** — Celonis shrugs, SAP shrugs, the graph answers ($/month resolves) → apply-fix | P2/P3 | DataOps **Insight** → `ApplyFixModal` | `/api/s2p/insight/cross-graph`, `/api/context/apply-fix` | climax |
| E5b | **Data Intelligence** — "your data has a trust score, and it tells you what additional data to buy" | P2/P3 | DataOps **Dashboard** (TrustCard → Products → Intelligence Map) | `/api/dataops/trust`, `/api/di/products`, `/api/di/intelligence-map` | 90s |
| E6 | **Continuity / Departure** — "$ of judgment retained when your best person leaves" | P3 | SOC **Executive Narrative** / S2P Performance | `/api/soc/centroid-support`,`/learning-state` | 60s |
| E7 | **Acts in your stack** — the ServiceNow ticket / Sentinel write-back it filed itself | P3 | SOC **Evidence Room** | `/api/servicenow/create-incident`,`/api/sentinel/writeback-test` | 45s |
| E8 | Close on the moat + audit trail (Evidence Room hash-chain) | P2 | SOC **Evidence Room** | evidence ledger export | 30s |

### 2.4 Presenter scripts — per-beat microcopy (caption + spoken line)

Two columns per beat: **Caption** = the short on-screen annotation the Loom guided-tour overlay renders
(§7 consumes this verbatim as `beats[].caption`); **Spoken** = the presenter's line (live or Loom voiceover).
Honesty guardrails apply: no fabricated numbers on day-zero surfaces; vision-level capabilities not asserted
as shipped.

**VC cut**
| Beat | Caption (on-screen) | Spoken |
|---|---|---|
| V1 | *The factor you trust most is your noisiest — and it survived correction.* | "Before I show you anything — pick the factor you trust most. … 2,000 verified decisions say that's your *noisiest* predictor, highest σ on the board. You've been trusting the thing that lies to you most, and nothing but the decisions could have told you. That's the mirror. …and before you ask if that's a fluke: we tested twenty-three patterns on you, three had the power to conclude anything, and this is the one that held after correction. It's not the loudest number — it's the true one." |
| COMP-1 | *The system getting better — and the governance is why you can trust it.* | "This is the graph the thesis rests on: quality climbing with every verified decision, governed the whole way. Ungoverned, it wins early and overfits; governed, it compounds." ⚠️ CC-1: production curve = IKS rising. Oracle decreasing curve = reference-app only. |
| V2 | *Promoted live — then 35 rejected.* | "This rule didn't exist this morning. The system wrote it, shadow-tested it, promoted it — base model never changed. And it *rejected 35* others: 18 failed the correctness floor, 11 conservation, 6 variance. The rejections are the point — self-improvement without a gate is a liability. We ship the gate." |
| V3 | *One engine. Five domains.* | "Born in security at 68%, transferred to procurement at 69%, matured in data ops at 83% — auto-fired in a Brazil plant in four minutes. When you ask 'isn't that five companies?' — it's one, and each domain makes the others smarter." |
| V4 | *Change a factor → the score moves. Feed a sample → refused.* | "Real or theater? Watch — I change this factor, the score moves, live. Now I try to sneak demo data into a real metric… refused. It won't let a sample number pose as a measured one. That's a system of record, not a dashboard." |
| V5 | *Poisoned signal → auto-pause (AMBER).* | "Let me try to break it. Poisoned signal in… conservation auto-pauses, amber. It stopped itself. A script can't say 'not yet.' This does." |
| V6 | *Day one: the instrument, not a fake number.* | "Day one, before a single decision, we don't hand you a fake ROI. We show the instrument working and the proof it's calibrated — then the number fills in on *your* data. Anyone who hands you your ROI on day one is showing you synthetic data." |
| V7 | *The frontier's open problem, shipped — and open-sourced.* | "The self-improving-agents frontier published its open problem this year: change yourself without losing the safety guarantee. We shipped the answer — and we're open-sourcing the engine and the trading copilot so you can read the gate yourself." |

**Trader self-serve cut**
| Beat | Caption | Spoken |
|---|---|---|
| TR1 | *Your last 500 trades, 30 seconds.* | "Drop your trades in. CSV. Thirty seconds." |
| TR2 | *Your radar — on you, not a demo.* | "The setup you're most confident in? Your noisiest. Your edge is somewhere you're not looking." |
| TR3 | *It keeps only what survives the gate.* | "Your edge over the quarter — and the system tuning itself: 47 configs tested, 12 kept, the rest rejected because they'd have made you worse. It's open source; the gate's in the repo." |

**Enterprise cut** (buyer-toned; swap the domain nouns per buyer)
| Beat | Caption | Spoken |
|---|---|---|
| E1 | *The system wrote this rule this morning.* | "This rule is hours old. It wrote it, shadow-tested it on real outcomes, promoted it — model frozen." |
| E2 | *Why it decided — cited, not asserted.* | "Ask it why. Not 'it matched a rule' — 'copper rose 4.8%, contract §7.3 allows pass-through to 110%, 5.2% is within bounds.' It cites." |
| E3 | *It declined an expansion on its own.* | "What your VP will remember isn't what it automated — it's what it *refused*. Accuracy below the safety line: declined, itself." |
| E4 | *Red-team → AMBER.* | "Watch us break it. Poisoned signal… it auto-pauses." |
| E5 | *Neither system alone produced this.* | "Celonis sees where it's slow, the ERP sees what happened, neither sees why-now. Fuse them — the cause and the $/month appear. Fix applied." |
| E6 | *$ of judgment retained when your best person leaves.* | "Your best analyst leaves Friday. Here's the judgment the system kept — in dollars." |
| E7 | *It filed the ticket itself.* | "It opened the ServiceNow ticket and wrote back to Sentinel — no human in the loop for the mechanical part." |
| E8 | *Every decision, hash-chained.* | "And all of it is here — every decision, its evidence, its confidence, hash-chained. Audit-ready today, sixteen months before the EU high-risk deadline." |

### 2.5 Silence beats — when to STOP TALKING (the technique that sells)

**Why this exists.** The beats above have timing (60s, 90s) but they're all TALK. The three most powerful
moments in the demo aren't things you say — they're things you *don't* say. The audience reads the screen,
processes the implication, and sells themselves. A presenter who talks through these moments kills them.

**Silence beats:**

**SILENCE 1: The Mirror (V1 / TR2, second 45-75)**

After you say "…the factor you trust most is statistically your worst predictor," STOP. Point at the
Trust Radar. Let the audience read the σ values. Count to five in your head. The silence is where they
think "wait — is this about MY judgment?" That's the hook. If you explain it, you answer a question
they haven't asked yet, and the hook dies.

*What to do:* After "…here's proof about you," physically step back from the screen. Let the radar
speak. The next sentence should come from THEM ("so what does the green one mean?"), not from you.
If they don't ask within 8 seconds, resume with "The green bar? That's your real edge — the one
you're not trading enough."

**SILENCE 2: The SituationPanel (E2, second 30-60)**

After you say "Ask it why. Not 'it matched a rule'…" click Score. The SituationPanel renders:
"5.2% price variance. Copper rose 4.8%. Contract §7.3 allows pass-through up to 110%. Within bounds.
Accept. Confidence: 0.91."

STOP. Let them read every line. This is the category-defining moment. If you summarize what they
can see, you rob them of the realization. The realization is: "this isn't pattern matching — it's
reasoning." They need to arrive at that conclusion themselves.

*What to do:* Point at the screen. Say nothing. Wait until someone says "it cited the contract?" or
"where does it get the commodity data?" THEN say: "A threshold rule rejected this — 5.2% over a 5% line. The reasoning read the contract and the commodity index and accepted it, correctly. The point isn't that others lack agents; it's that a rule fires on a number, and judgment reasons about *why*." The pause made the line land.

**SILENCE 3: The Rejection Table (V2 / E3, second 60-90)**

After you say "…and it rejected 35 others," the rejection table renders:
"18 correctness floor. 11 conservation. 6 variance."

STOP. Let them read the three numbers. The insight they need to arrive at is: "the rejections are
more important than the approvals." If you say that for them, it's a claim. If they think it, it's
a conviction.

*What to do:* Wait 5 seconds. Then, quietly: "The rejections are the point. Self-improvement without
a gate is a liability. We ship the gate." Lower your voice for this line — it's the close, not the
pitch.

**SILENCE 7: The Investigation Order (VLD-SOC-1; recovery variant VLD-SOC-2).** Say: “Here is a planted preview of the investigation order.” Reveal the persisted trace if available; otherwise identify it as a storyboard. Pause for five seconds when the selected auth check and its admitted evidence appear. For SOC-2, pause on the successfully queried negative result and subsequent process check; unavailable evidence uses the distinct missing-source control. Resume: “The record shows what was selected, what came back and why the next selection was eligible.” Do not say a rule always reads both or that a changed direction proves better routing. Keep PLANTED FIXTURE, ROADMAP and the deployment routing-accuracy badge visible throughout. If asked about the numbers: “These are fixture values. The offline results are separate, and deployment routing accuracy has not been established.”

**SILENCE 8: VLD-TRD-1 (§4.17).** Pause for five seconds when `1 · Position sizing → three linked positions` appears above the still-unread thesis entry. Keep the roadmap and provenance badges visible. Resume: “The first check was the portfolio.”

**SILENCE 9: VLD-TRD-2 (§4.17).** Pause for five seconds with `2 · Timing quality — unavailable` beside `IV percentile — not queried / provider absent`. Let the missing check remain visible before opening the manual replay.

**SILENCE 10: VLD-PUR-1 (§4.17).** Pause for five seconds when the second row reveals `expiry before service` directly below `event confirmed`. Resume: “More demand did not make this delivery usable.”

**SILENCE 11: VLD-PUR-2 (§4.17).** Pause for five seconds on the second row: `supplier arrival after service cutoff`, with the prior manager's verified delivery record visible beneath it. Resume: “The incoming manager can see what was retained.”

**The meta-principle:** in a 7-minute demo, you have ~420 seconds. Spending 20 of them in deliberate
silence (5%) will feel uncomfortable. Do it anyway. The silence is where the decision happens.

---

## 3. Master scenario catalog (all 94 — the use-case reference)

Status ✅ demo-ready · ⚠️ deferred. "Cut" = which demo cut features it (V/TR/E) or — (catalog-only depth).
Full per-scenario BEFORE/AFTER narrative lives in `narrative_readiness_v3.md` Part II.

### Trading (20; 19 ready) — clusters A Signal/Pattern, B Scaling, C Self-Knowledge, D Self-Governance, E Data, F Disruption, G Volatility
`T1` Signal Trust Radar **[HERO, mirror]** ✅ Analysis (V1,TR2) · `T2` Post-Win Overtrading ✅ · `T3` Friday
Degradation ✅ · `T4` Regime Analysis ✅ *(→ folds into TRD-S1 at demo)* · `T5` Scale This Strategy? ✅ Perf · `T6` Execution Gap ✅ ·
`T7` Revenge Trade Real-Time ✅ Log · `T8` Per-Trader Edge ✅ Dash (TR3) · `T9` Strategy Stopped Working ✅ ·
`T10` Prove It Before Real Money ✅ (P1) · `T11` History Unified ✅ · `T12` Playbook Transferred ✅ (P3) ·
`T13` Tariff Shock ✅ · `T14` Regime Shift ✅ *(→ folds into TRD-S1 at demo)* · `T15` Revenge at VIX 32 ✅ · `T16` Edge Rotation ✅ ·
`T17` Premium IV/RV ⚠️ **deferred v1.1** (VIX proxy today) · `T18` Correlation Breakdown ✅ · `T19` Earnings
Split ✅ · `T20` VIX Mean-Reversion ✅

### Purchasing (22; 21 ready) — A Operational, B Intelligence, C Pattern, D Memory, E Scale
`I1` Signal Reliability / Invoice-Variance Profile **[mirror, discovery-open]** ✅ Analysis · `M1` Food Cost Dash ✅ · `M2` Delivery Match ✅ ·
`P1` Smart Ordering ✅ · `P2` Waste Tracking ✅ · `P3` Conservation-Gated Auto-Order ✅ (P1) · `P4`
Evidence-Based Ordering ✅ · `P5` Supplier Scorecard ✅ · `P7` Per-Item Auto-Approve ✅ · `P9` Demand
Forecast ✅ · `M8` Commodity Decomposition ✅ **FRED LIVE** · `F1` Weather Intel ✅ **OpenMeteo LIVE** · `F2`
Event Intel ✅ · `F3` Day-of-Week ✅ · `P6` Supplier Consolidation ✅ · `P8` Cross-System Discovery ✅ (P3) ·
`I4` Cross-Category Insight ✅ · `I2` Price Memory ✅ · `I5` Self-Tuning Ops ✅ (P1) · `I7` IKS Growth ✅ ·
`I8` Chain Learning Transfer ✅ (P3) · `P10` Disruption Recovery ⚠️ **deferred v2.0**

### DataOps (16; all ready) — L1-4 core, L5 data-intelligence, L6 data-to-buy
`D-M1` Pipeline Triage ✅ Triage · `D-M2` Process Timeline ✅ · `D-M3` Evidence Resolution ✅ · `D-M4`
Conservation Safety Net ✅ (P1) · `D-M5` AE Self-Tuning ✅ (P1) · `DI-1` Source Profiler ✅ · `DI-2`
Intelligence Map v1 ✅ · `DI-3` NL Query ✅ · `DI-4` Prompt Integrator ✅ · `DI-5` Combination Discovery ✅ ·
`DI-6` Data Valuation ✅ · `DI-7` **Intelligence Map v2 (gold lines) [HERO, Level 6]** ✅ Insight (E5) · `DI-8`
Acquisition Advisor ✅ · `DI-9/10/11` Snowflake/dbt/Airflow connectors ✅ (mock)

### S2P (16; all ready) — A Invoice/AP, B Supplier Intel, C Cross-System, D Capital, E Disruption
`S14` **Not a Script — A Decision [HERO, category-defining]** ✅ Exception Triage (E2) · `S1` Exception Rate
Drops ✅ · `S2` Autopilot Nobody Trusts ✅ (P1) · `S9` Automation Broke Silently ✅ · `S13` System Tunes
Itself ✅ (P1) · `S15` Caution Over Speed ✅ (P1) · `S6` Expertise Walks Out ✅ (P3, continuity) · `S7` 47
Duplicates ✅ · `S8` ERP Lead Time Wrong ✅ · `S11` Supplier Fine Until It Wasn't ✅ (cross-copilot signal) ·
`S5` Pattern Nobody Queried ✅ · `S10` Consultant Findings Evaporate ✅ · `S16` Where Celonis Stops ✅ (P2/P3,
fusion) · `S12` Working Capital Trap ✅ · `S3` Same Tariff, Same Recovery ✅ · `S4` Cleanup Never Ends ✅

### SOC (20; all ready — investor surface) — D Dashboard, A Analytics, T Triage, C Compounding, E Executive, P Preview, V Evidence
`SOC-D8` **Campaign Timeline [HERO]** ✅ Runtime Evolution · `SOC-D1` IKS Tracking ✅ · `SOC-D2` Conservation
Monitoring ✅ (P1) · `SOC-D3` Category Accuracy ✅ · `SOC-D6` Campaign Intelligence ✅ Analytics · `SOC-D7`
Auto-Approve Rate ✅ · `SOC-A1` Fingerprint ✅ (mirror) · `SOC-A6` Centroid Drift ✅ · `SOC-T1` 6-Factor
Scoring ✅ · `SOC-T4` Referral R1-R7 ✅ · `SOC-T5` Score→Confirm→Learn ✅ · `SOC-C1` Compounding Trajectory ✅
· `SOC-C4` Three-Channel Error Budget ✅ · `SOC-C5` Simulation ✅ · `SOC-E1` Exec Summary ✅ · `SOC-E2`
Learning Narrative ✅ · `SOC-P1` S2P Preview ✅ · `SOC-V1` Evidence Ledger ✅ (E8) · `SOC-V3` AE Impact ✅ ·
`SOC-V4` Safety Controls (conservation + bounded exploration) ✅

**Totals: 94 scenarios · 92 demo-ready · 2 deferred (T17 v1.1, P10 v2.0).** Five hero scenarios (one per
copilot) + the three cross-cutting hero *moments* (§4). **Count reconciliation with the outreach catalog: §3.1.**

### 3.1 Reconciliation with `outreach_use_scenario_catalog.md`

The two documents are **two lenses on the same capability set, from two dates** — they don't conflict:

| | `outreach_use_scenario_catalog.md` (v1.0, May 21) | **This doc** (July 10) |
|---|---|---|
| Lens | scenario **universe + outreach messaging** (from the product definitions) | **demo-ready**, mapped to surfaces/APIs/cuts |
| Organized by | narrative theme (Market / Innovation / Volatility / Food-Service) + 23 outreach **heroes** + one-liners + industry-data | demo cut + copilot tab + build DoD |
| Count | **91** (DataOps 22, SOC 10, Purchasing 23, Trading 20, S2P 16) | **94** (Trading 20, Purchasing 22, DataOps 16, S2P 16, SOC 20) |

**Why the per-copilot counts differ (and neither is wrong):** Trading (20) and S2P (16) match exactly. The
others differ by *counting granularity + date*: the catalog groups **SOC into 10 narrative units**; this doc
counts **20 per-tab demo scenarios** (finer-grained). Conversely the catalog's **DataOps 22 / Purchasing 23**
include full-PD scenarios not all surfaced as separate demo beats (this doc maps 16 / 22 demo-ready). Rule of
thumb: **use the catalog for "what scenarios exist and how to say them"; use this doc for "what's demoable and
where it lives."** Neither count is authoritative over the other — they answer different questions.

**Hero mapping — adopt the catalog's proven one-liners in the presenter scripts (§2.4/§4):** the outreach
heroes map onto this doc's demo beats; use the catalog title/one-liner as the spoken hook (it's already
audience-tested and industry-data-grounded).

| Demo beat (this doc) | Outreach hero (catalog) | One-liner to use | Industry-data hook |
|---|---|---|---|
| V1/TR2 cold-mirror (Trading T1) | **TRD-1** My Favorite Setup Is My Worst Setup | "Your favorite setup is your worst setup" | Odean 1999: traders overtrade familiar setups 2-4× regardless of performance |
| mirror (Purchasing I1) | **PUR-1** The Trust Trap | "The supplier you trust most is costing you most" | NRA: food cost 28-35% of revenue; 1-3pt = $15-45K/yr |
| V2/TR3/E3 Rejection + prove-it (C-2) | **TRD-4** Prove It Before Real Money | "Prove it before real money" | — (conservation gate) |
| V5/E4 refusal + red-team (C-5/ST-2) | **SOC-4** The System That Admits Failure | "The system that admits failure" | Gartner: AI + integrated trust/safety → 50% fewer AI failures; #1 CISO fear = uncontrolled automation |
| E5 fusion climax | **DO-4** Cross-Graph — The $604K Nobody Saw / **S2P-4** Three Systems, One Answer | "Celonis sees where. SAP sees what. Only we see why — and the $604K" | — |
| E6 continuity/departure | **DO-2** The Consultant Who Left / **PUR-3** The $28K Departure | "She left. Her knowledge didn't." | — |
| cross-theme (amnesia) | **SOC-1** The Amnesia Problem | "Your system has amnesia" | — |

Full hero narratives, the remaining 16 outreach heroes, the 91-scenario index, and all one-liners/industry-
data live in the outreach catalog — **not duplicated here.** When the outreach pass runs (post-demo), it draws
from that catalog; this doc guarantees the beats it references are demoable.

---

## 4. Net-new hero-moment build items (the executable coding-session work)

These are the only genuinely net-new builds for the demo; everything else in §2/§3 is shipped (stage/wire).
Owners: Session A = copilot-sdk, Session C = gen-ai-roi-demo (SOC), Content = script.
**Cross-ref:** these are the strategy doc's hero moments — **DM-1 = HERO-1 (C-2)**, **CF-1 = HERO-2 (C-3)**,
**DZ-1 = HERO-3 (C-4)**, **ST-5 = HERO-4**. The consolidated coding build list is `next_steps_strategy_v1_1.md`
§9 (C-1..C-14); this section is the spec it points to.

### 4.1 Rejection Moment (P1 — answers the Darwin Gödel frontier)

[VLD integration: see VLD-SOC-1 for investigation trace]
| ID | Surface | API / data | DoD | Owner | Effort |
|---|---|---|---|---|---|
| DM-1 | Trading **Performance** (+ SOC Runtime Evolution) | existing promotion-gate logs — surface rejected variants + failed clause | table shows "N tested / M promoted / **K rejected**" with per-variant failed clause (correctness floor / conservation / variance); data from existing logs, **no new gate logic** | A (+C) | 1d |

Discovery: `grep -rn "promotion|rejected|conservation_gate|variance_stability|correctness_floor" apps/trading/backend` —
confirm rejection reasons are logged (the gate computes them); if not surfaced, this is the surfacing task.

### 4.2 Counterfactual "prove it's real" (P2 — answers TradingAgents)
| ID | Surface | API / data | DoD | Owner | Effort |
|---|---|---|---|---|---|
| CF-1 | ≥2 copilots, any scoring surface | `/api/score` perturbation + the F-26 gate | presenter perturbs a factor → sees real score delta; attempts to feed a `sample` value into a computed metric → **refused** (F-26), visible on stage | A + C | 1d |

### 4.2.1 S14 rule-vs-reasoning contrast (the side-by-side that makes S14 category-defining)

[VLD integration: see VLD-S2P-1 for investigation trace]

**Why this exists.** The SituationPanel already shows the reasoning — but it doesn't show what a rule-based
system would have done with the SAME invoice. Without the contrast, the audience thinks "nice explanation."
With the contrast, they think "the rule was WRONG and the reasoning was RIGHT — that's a different product."

**The build:**
| ID | Surface | What it shows | DoD | Owner | Effort |
|---|---|---|---|---|---|
| S14-CONTRAST | S2P **Exception Triage** — above or beside the SituationPanel | Two-column display: **LEFT** = "Rule-based decision" (what a threshold system would have done). **RIGHT** = "Situation-aware decision" (what the SituationPanel produced). | Side-by-side renders on the same invoice; the rule rejects, the reasoning accepts; the $ impact of the wrong rejection is visible | A / S2P | 0.5d |

**How it works:**
- **Left column (the rule):** "Price variance 5.2% exceeds 5.0% threshold. **REJECT.** Route to manual review.
  Estimated cost: $2,400 analyst time + $340K delayed payment across 47 similar invoices this quarter."
- **Right column (the reasoning):** "Price variance 5.2%. Copper rose 4.8% (Bloomberg, 30d). Contract §7.3
  allows commodity pass-through up to 110% of index. 5.2% ≤ 110% × 4.8% = 5.28%. **ACCEPT.**
  Confidence: 0.91. Provenance: contract_clause=verified, commodity=scraped_external."

**The killer detail:** below both columns, a single line:
> *“The displayed threshold-only baseline rejected this fixture. The contract-aware assessment used additional evidence and reached a different result.”*

**Implementation:**
- The left column is COMPUTED, not hardcoded: apply a simple threshold rule (variance > 5% → reject)
  to the same invoice the SituationPanel is scoring.
- The right column is the existing SituationPanel output.
- The $ impact comes from: count of similar invoices × average value × delay cost.
- The data is from the preseed — not fabricated. Provenance badge shows tier.

**Where it appears in the demo:** Enterprise cut, beat E2 (the SILENCE 2 moment from §2.5). After the
silence, the presenter says: *“The displayed threshold-only baseline rejected this fixture. The contract-aware assessment used additional evidence and reached a different result.”*

### 4.3 Day-Zero honesty (P2 — the cold-start wedge; no competitor addresses it)
| ID | Surface | API / data | DoD | Owner | Effort |
|---|---|---|---|---|---|
| DZ-1 | fresh-tenant view, ≥1 copilot | the day-zero state (INSTRUMENT_VALIDATED → ACCUMULATING → MEASURED) | day one shows instrument-validated + proven + scraped-context (no fabricated magnitude); a toggle shows the transition to measured | A/C | 1-2d |

### 4.4 Staged trust beats (shipped — script + light wire only, ~0.5d each)
| ID | Beat | Surface | API |
|---|---|---|---|
| ST-1 | Refusal ("the system said no") | SOC Compounding | `/api/soc/interventions` (shipped) |
| ST-2 | Red-team (`simulate_failure` → AMBER) | SOC Compounding | `/api/eval/simulate-failure` (shipped) |
| ST-3 | Cold-mirror overlay (open beat) | Trading/Purchasing Analysis | `/api/fingerprint` (shipped) |
| ST-4 | Acts-in-your-stack | SOC Evidence Room | Sentinel/ServiceNow (shipped) |
| ST-5 | S14 script rewrite ("they debate; we cite and measure") | S2P Exception Triage | — (Content) |

### 4.5 BYOD / "your data" (P3 — the biggest "I need this" lever; mixed)
| ID | Note | Owner | Effort |
|---|---|---|---|
| BYOD-1 | Trading CSV + SOC Sentinel ingest **exist** — surface only. Purchasing/DataOps/S2P need a CSV→score→learn importer **on the `write_observation` path, not `write_decision`** (or it recreates the ghost-decision problem). Overlaps the Toast connector in the strategy (W3-2). | A | 3-4d (deferrable per demo need) |

---

### 4.6 Trading — situation-conditioned & volatility beats (NEW; next_steps §4.4/§4.5, builds C-TRD-SIT / C-TRD-VOL)

**The frame:** decision-trace learning *alone* gives an **unconditional** mirror ("your favorite setup is your
noisiest"). Add **situational awareness** and it becomes **conditional** — *"your discipline holds when trends
persist; in choppy regimes you trade 2.1× more and lose 12%."* Traders have **regime-dependent** biases, so the
unconditional mirror **hides the most expensive truth.** Mostly **wiring** (the quant regime features and the
SDK `SituationAnalyzer` are already built).

| ID | Beat | What the trader sees | Class | Build |
|---|---|---|---|---|
| **TRD-S3** ⭐ | **Autonomy throttle** (the room-3 kill shot) | local-Hurst detects the break → conservation **AMBER** → *"the regime is breaking; I'm reducing my own autonomy until I re-converge."* **A system that voluntarily gives up authority.** | **NEAR** | C-TRD-SIT Step 2 (~2d) |
| **TRD-V1** ⭐ | **The short-vol illusion** | "Your calm-regime Sharpe of 2.1 is **1.2** after clustering adjustment (inflation 1.8×). Half your 'edge' is tail risk you aren't paid for." | **NEAR** | C-TRD-VOL (~1d) |
| **TRD-V2** ⭐ | **VRP — edge or insurance?** | "78% of your VRP capture came in **low**-tail-dependence windows. You're not harvesting a premium — you're **selling insurance in calm weather**." | **NEAR** | C-TRD-VOL (~1d) |
| **TRD-S1** | Regime-conditioned mirror | "Your edge is real when trends persist; in choppy regimes you trade 2.1× more and lose 12%." | **NEAR** | C-TRD-SIT 3a |
| **TRD-S2 / V3** | Situational abstention | "I've seen only **4** of your decisions in *this* regime — I won't score this trade yet." (per-regime day-zero) | **NEAR** | C-TRD-SIT 3a |
| **TRD-S4** | Regime-scoped rejection | "35 variants rejected — **11 because they only worked in one regime**." | **NEAR** | C-TRD-SIT 3a |
| **TRD-V5** | Regime-conditioned rich/cheap (upgrades T17) | "IV is rich at the 85th pct *for this regime* — but in trending regimes you've been wrong 60% of the time fading rich IV." | **NEAR** | C-TRD-VOL |
| **TRD-V6** | Dispersion follow-rate | "Your signal fired 12×; you followed 4. The 8 you skipped were **+$62K**." | **NEAR** | C-TRD-VOL |
| **TRD-V7** | Effective bets in a tail (upgrades T18) | "6 positions = 2.3 effective bets — **1.2 in a tail**. You're single-position exactly when it matters." | **NEAR** | ships with C-OSS-1Q |

**⚠️ All magnitudes above are *illustrative formats, not measured results*** — they render from the sample
trader / BYOD import with a provenance badge, and show the **day-zero state** when `n < K` (product_integrity
§2.6). Never present them as measured customer outcomes (F-21/F-22).

### 4.7 ⭐ TRD-S7 — The Re-convergence Moment (the strongest technical beat available to us)

**The beat.** Replay a **real** regime break (2020-03 or 2022) on real market history. A cold-start learner must
relearn from zero. CI **re-initializes from the nearest prior regime's judgment geometry** and re-converges
faster. Show the two curves side by side.

**Why it is the strongest beat.** It is **γ>1 made visible, on real history, against non-stationarity** — the
exact failure that kills every RL trading system (a reward-maximizing agent has no notion of its own competence
boundary and cannot abstain). It is an **architectural** answer, not a tuning trick. *No competitor can show
this.*

- **Surface:** Trading → Performance / Runtime-Evolution (curve overlay: cold-start vs regime-indexed).
- **Needs:** **C-REGIME P4** (regime-indexed judgment memory) + the **EXP-REGIME** experiment.
- **Class:** **ARCH today** (label it roadmap in any deck) → **NEAR** when C-REGIME P4 lands → **LIVE** once
  EXP-REGIME passes and the result is carried into `math_synopsis` (T-A).
- **Honesty:** until EXP-REGIME passes, this is a **vision slide, explicitly labeled** — showing it is fine;
  implying it runs today is **F-27**.

### 4.8 ENT-1 — The Sunk-Investment Multiplier (the enterprise/Celonis wedge's missing beat)

[VLD integration: see VLD-DO-1 for investigation trace]

**The beat (CFO/CTO room).** *"You've spent $2M on Celonis. It tells you **where** the process breaks. We ingest
its process graph plus your EDW metadata and tell you **why** — and **which decision to change**. Your Celonis
investment just became **more valuable, not obsolete**."*

**Why it matters:** row 6 is our strongest enterprise wedge and had the weakest beat support. Every competing
"AI platform" is a rip-and-replace threat; **we raise the value of their sunk spend.** No rip-and-replace
vendor can say that sentence.

- **Surface:** DataOps / S2P cross-graph fusion (the E5 climax, re-framed for the buyer).
- **Class:** **NEAR** (the fusion beat is LIVE; the *sunk-investment framing* + a real process-mining export are the new work).
- **⚠️ Scope guard:** surface **"which decision to change"** — **not** "we execute it in your ERP." Process→ERP
  **write-back is roadmap** (next_steps C-VERIFY); claiming execution is **F-21**.

---

## §4.9 Data Intelligence Demo Beats (NEW — shipped August 2, 2026)


### §4.9.0 DataOps Cut Arc (v2.6 — machinery-first, category-story-last)

**Story spine:** Machinery leads → category story lands last. Detection/lineage stay as substrate framing, not beats to win.

| # | Beat | Role in arc | Time |
|---|---|---|---|
| 1 | **DI-PROOF** | **It learns** — perturbation drops trust live, restores with provenance | 90s |
| 2 | Self-computation | **It knows what it learned** — the exact decisions responsible | 60s |
| 3 | **DI-ADMITS-FAILURE** | **It knows when it was wrong** — governance moat (promoted to top 3) | 60s |
| 4 | **DI-ABSTAIN** (NEW) + **DI-GATEWAY** (NEW) | **It governs AI action** — abstention + agent-trust gateway (climax) | 90s |
| 5 | **DI-FIRSTVS6TH** (NEW) + **DI-TWIN** (NEW) | **It compounds** — falsifiable: 1st source vs 6th + frozen-twin control | 90s |
| 6 | Intelligence Map | **The estate becomes visibly smarter** — W1 lands because they've seen the machinery | 60s |
| 7 | **DI-GOLD** (de-risked) | **It values itself** — gold lines as FDR-gated ranked hypotheses, $ off hero path | 90s |

---

### DI-PROOF: "Earned, Not Asserted" (the credibility linchpin — NEW v2.3)

| Field | Value |
|---|---|
| **Surface** | DataOps **Dashboard** → TrustCard with live what-if control |
| **API** | `GET /api/dataops/trust` + scoped what-if (perturb source outcomes) |
| **Class** | **NEAR** — capability proven (perturbation experiment); live what-if surface ~2-3d build |
| **What audience sees** | Presenter picks highest-trust source (SAP, 0.94). Feeds decisions where SAP led to wrong outcome. Trust drops live. DK weight moves. Conservation ticks toward AMBER. Revert — climbs back. |
| **Effort** | ~2-3d (live what-if surface on TrustCard) |

**Presenter script:**

| Caption | Spoken |
|---|---|
| *This isn't a number I typed.* | "Watch — I feed it decisions where SAP was wrong, and the trust drops, live. It's *earned* from your outcomes. Every other data-quality score is a label. This is a measurement." |

**SILENCE BEAT 6 (new):** After the trust bar drops, stop. Let them watch it. Then, quietly: "A label can't do that. A measurement can."

**Why it's the linchpin:** Credibility floor under DI-PRODUCT (IKS), DI-GOLD (what to buy), and DI-AGENT-TRUST — all of which "sound too good" without it. Grounding: perturbation experiment already proven (source-property perturbation moved only its factor, graph mode, clean revert).

---
### DI-TRUST: "Every Data Asset Gets a Trust Score" (the Data Quality room kill-shot)

| Field | Value |
|---|---|
| **Surface** | DataOps **Dashboard** → TrustCard |
| **API** | `GET /api/dataops/trust` |
| **What audience sees** | 6 horizontal bars showing per-factor DK weights. Color coded: green (reliable), amber (moderate), red (noisy). Overall trust score 0.48. Conservation GREEN. Narrative: "source_reliability (0.94) is your most predictive factor. data_freshness (0.23) is noise." |
| **Class** | **LIVE** |
| **Effort** | Shipped — SC-TRUST (6 BE tests, 4 PW tests) |

**Presenter script:**

| Caption (on-screen) | Spoken |
|---|---|
| *Six factors. Six trust scores. Earned, not labeled.* | "Every data asset in your pipeline has a trust score — not a label someone typed into a catalog, but a score the system *earned* from verified decisions. Source_reliability: 0.94 — that's SAP. You can trust it. Data_freshness: 0.23 — that's your Airflow metadata. It's noise. You've been treating both as equally reliable. They're not, and only 400 verified decisions could have told you that." |

**SILENCE BEAT 4 (new):** After showing the red bar for data_freshness (0.23), STOP. Let the audience read the number. The insight they need to arrive at: "we've been weighting noisy data the same as reliable data." Wait 5 seconds. Then: "That gap is $180K/year in wrong decisions based on stale freshness data. The trust score found it. A dashboard can't."

---

### DI-SOURCE: "Your Data Has a Reputation" (Source Profiler deep-dive)

| Field | Value |
|---|---|
| **Surface** | DataOps **Insight** → navigate to source profile via API |
| **API** | `GET /api/di/sources/{id}/trust` + `GET /api/di/sources/{id}/consumers` |
| **What audience sees** | Per-source trust card: SAP S/4HANA trust 0.94 ("reliable"), 2 consumers, per-column quality. Salesforce trust 0.67 ("moderate"), 3 consumers, 2 noisy columns flagged. |
| **Class** | **LIVE** |
| **Effort** | Shipped — DI-1 remaining 3 endpoints (9 BE tests, 3 E2E tests) |

**Presenter script:**

| Caption | Spoken |
|---|---|
| *Per-source, per-column. Earned from decisions.* | "Click into SAP. Trust 0.94 — reliable. Now click Salesforce. Trust 0.67. Two columns are noisy: satisfaction_score and churn_indicator. The system learned this from 400 decisions where those columns didn't predict the outcome. Every source gets a reputation — earned, not assigned." |

---

### DI-PRODUCT: "Data Products with IKS" (the CDO room kill-shot)

| Field | Value |
|---|---|
| **Surface** | DataOps **Dashboard** or **Insight** → Products panel |
| **API** | `GET /api/di/products` |
| **What audience sees** | 3 data products with IKS, conservation status, maturity label. Customer-360: IKS 72, GREEN, "mature." ESG-compliance: IKS 8, AMBER, "learning." |
| **Class** | **LIVE** |
| **Effort** | Shipped — DI-1 products endpoint |

**Presenter script:**

| Caption | Spoken |
|---|---|
| *Data-as-a-product. Measured, not labeled.* | "Your customer-360 data product: IKS 72, GREEN, 3,400 verified decisions. Any agent can consume it autonomously — the trust is proven. Your ESG data product: IKS 8, AMBER, 120 decisions. Still learning. Require human review. THIS is what data-as-a-product actually looks like — not a label in a catalog, but a measured maturity score from verified outcomes." |

---

### DI-GOLD: "Your Data Tells You What Data to Buy" (the Level 6 differentiator)

| Field | Value |
|---|---|
| **Surface** | DataOps **Insight** → Intelligence Map with gold dotted lines |
| **API** | `GET /api/di/combinations` + `GET /api/di/acquisition-advice` + `GET /api/di/intelligence-map` |
| **What audience sees** | Force-directed graph. Nodes = sources (brightness = trust). Lines = correlations. **Gold dotted lines** = suggested new connections with dollar values. "Weather API → $180K/year value." |
| **Class** | **LIVE** (endpoints) / **NEAR** (gold line rendering on map) |
| **Effort** | Shipped — DI-5 endpoints (9 BE tests, 3 E2E tests). Frontend gold line rendering: ~1 week |

**Presenter script:**

| Caption | Spoken |
|---|---|
| *The gold lines are connections the system discovered — ranked by ROI.* | "See the gold dotted lines? Those are data sources you DON'T HAVE yet — but the system computed their value from what it's already learned. Weather data: $180K/year in better demand prediction. Commodity index: $120K/year in pricing accuracy. The system didn't just learn from your data — it learned what ADDITIONAL data would make it smarter. Your data tells you what data to buy. Nobody else can show you this." |

**SILENCE BEAT 5 (new):** After the gold lines appear, STOP. Let them read the dollar values on each gold line. The insight: "the system isn't just using our data — it's recommending what to buy next." Wait 5 seconds. Then, quietly: "That's not a data catalog. That's a data strategy."

---

### DI-TIMELINE: "The Learning Journey" (Centroid Timeline)

| Field | Value |
|---|---|
| **Surface** | DataOps **Insight** → CentroidTimelinePanel |
| **API** | `GET /api/self/centroid-history` |
| **What audience sees** | Line chart showing centroid drift over decisions. 6 category curves converging. IKS overlay rising. Phase markers: bootstrap → learning → converged. |
| **Class** | **LIVE** |
| **Effort** | Shipped — SC-11 (4 PW tests) |

**Presenter script:**

| Caption | Spoken |
|---|---|
| *The trajectory of intelligence. Every curve is a category learning your environment.* | "This is the compounding curve in action. Each line is a category — pipeline_failure, schema_change, resource_quota — converging from the generic prior toward YOUR operational pattern. The IKS is rising. It took 200 decisions for pipeline_failure to converge. Schema_change needed 350 — it's harder. The system knows how much it's learned AND how much it hasn't. No other platform can show you this." |

---

### DI-ADMITS-FAILURE: "The System That Admits Failure" (Rule Genealogy)

| Field | Value |
|---|---|
| **Surface** | DataOps **Evidence** → RuleGenealogyPanel + AccuracyAlertsPanel |
| **API** | `GET /api/ae/operational-rules` + `GET /api/self/accuracy-by-category` |
| **What audience sees** | Rules with promoted (green) and rejected (red) badges. Accuracy alerts with per-category bars. A rejected rule: "auto-resolve recurring timeouts — 45% accuracy — REJECTED." |
| **Class** | **LIVE** |
| **Effort** | Shipped — SC-12 + SC-13 (8 PW tests) |

**Presenter script:**

| Caption | Spoken |
|---|---|
| *12 promoted. 35 rejected. The rejections are the point.* | "The system tried to auto-resolve recurring timeouts. Shadow-tested on 15 decisions. 45% accuracy. Rejected. Meanwhile, auto-escalating first-time failures: 73%. Promoted. The system doesn't just learn what works — it learns what DOESN'T work and refuses to promote it. The rejections are the point. Self-improvement without a gate is a liability. We ship the gate." |

---

### DI-DIRTY-DATA: "Deploy on Dirty Data, Day 1" (the cold-start wedge)

| Field | Value |
|---|---|
| **Surface** | DataOps **Dashboard** → TrustCard (same surface as DI-TRUST, different framing) |
| **API** | `GET /api/dataops/trust` |
| **What audience sees** | Same 6 bars — but the presenter frames it differently: "We didn't clean your data first. We deployed on it. The system learned which sources to trust and which to ignore. data_freshness: 0.23 — the system figured that out in 400 decisions, not a 12-month cleanup project." |
| **Class** | **LIVE** |
| **Effort** | Shipped (same as DI-TRUST — different script, same surface) |

**Presenter script:**

| Caption | Spoken |
|---|---|
| *No cleanup. No 12-month project. Deploy and learn.* | "Every competitor starts with: 'First, 6-12 months of data cleanup. $1.5M.' We deployed on your data as-is. Day 1. The system learned which sources to trust — SAP at 0.94, your Airflow metadata at 0.23. It didn't need clean data. It needed verified decisions. 400 of them later, it knows more about your data quality than any catalog could tell you." |

**Target audience:** CIO/CDO who's been burned by data cleanup projects that go stale within a year.

---

### DI-AGENT-TRUST: "The Autonomy License" (Agent Trust API)

| Field | Value |
|---|---|
| **Surface** | DataOps **Insight** → Source Profile trust card |
| **API** | `GET /api/di/sources/{id}/trust` |
| **What audience sees** | Trust card with recommendation: "Safe for autonomous agent consumption" (trust > 0.8) or "Require human review" (trust < 0.5). Per-column breakdown. |
| **Class** | **LIVE** |
| **Effort** | Shipped — DI-1 trust endpoint |

**Presenter script:**

| Caption | Spoken |
|---|---|
| *Trust 0.94: autonomous. Trust 0.23: human review required.* | "Your agents need to know which data they can trust. SAP at 0.94: safe for autonomous consumption — the system proved it over 3,400 decisions. Your ESG feed at 0.23: require human review. The IKS IS the autonomy license. No other platform gives your agents a measured, earned trust score per data source." |

**Target audience:** Teams building autonomous AI agents who need data governance.

---

**⚠️ Honesty guard (F-21/F-22):** All dollar amounts in DI-GOLD ($180K, $120K) and DI-TRUST ($180K gap) are **illustrative formats derived from preseed fixture data**, not measured customer outcomes. They render from the sample data with a provenance badge. Never present them as measured results. The trust scores (0.94, 0.23, 0.67) are computed from the preseed's verified decisions — real computation on sample data, labeled as such.

---

### Cross-Copilot Signal: DI Benefits All Domains

The Source Profiler (DI-1) and Trust API are domain-agnostic. The demo can show:

| Copilot | What DI provides | The line |
|---|---|---|
| SOC | Per-SIEM trust (Sentinel vs Splunk reliability) | "Your Sentinel feed: 0.96. Your custom SIEM: 0.71. The system knows which alerts to weight." |
| S2P | Per-supplier data trust | "Supplier X's self-reported lead times: 0.34 trust. UPS tracking: 0.97. Trust the tracking, not the supplier." |
| Trading | Per-data-source signal quality | "Bloomberg at 0.98. Your spreadsheet at 0.41. Your 'edge' is built on 0.41 data." |
| Purchasing | Per-POS reliability | "Toast POS: 0.93. Manual inventory counts: 0.52. Stop trusting the clipboard." |

This is a **one-engine-five-domains** beat (V3/E5 amplifier). The DI infrastructure makes each copilot's data quality visible — and the trust scores transfer across domains via the shared DK mechanism.

---

---

## §4.10 Reference & Differentiation Beats (v2.4 — August 8, 2026)

**Source:** jm_reference_and_value_upgrades_executable_v6.md + vc_pitch_judge_consolidation.md

### DIFF-1 — "Governed vs Ungoverned" (the runnable "isn't this a bandit" rebuttal) ⭐

| Field | Value |
|---|---|
| **Surface** | `apps/s2p_differentiation/` (backend + frontend; reuses SOC viz) |
| **Class** | **NEAR** (gate on WP-1) |
| **Rooms** | 2 (self-improving agents) + 3 (RL trading) — runnable kill-shot |
| **The beat** | (1) T-G1 toggle: CI action holds, reward-max flips. (2) Governed arm stays robust after regime shift; reward-max collapses. (3) Safety: CI gate rejects poisoned rule; ungoverned promotes it. |
| **Spoken** | "Don't take 'we're not a bandit' on faith — here it is, governed vs reward-maximized, same data, side by side." |
| **Honesty** | `test_baseline_is_faithful` — reward-max baseline must not be strawmanned. |

### COMP-1 — The Compounding Curve (the fundable artifact) ⭐

| Field | Value |
|---|---|
| **Surface** | DI-TIMELINE (single-arm LIVE) → two-arm governed-vs-frozen (NEAR, from APP-1/APP-4) |
| **Class** | **LIVE** (single-arm IKS) → **NEAR** (two-arm) |
| **Cut** | VC cut — lead beat after V1 mirror |
| **Spoken** | "The system getting measurably better at every task, and the governance is WHY the improvement is trustworthy." |
| **⚠️ CC-1** | Production curve = IKS RISING (canonical-distance increasing). Oracle-only curve = ground-truth-distance DECREASING. Never show oracle curve in production beat. |

### L-CDK — SDK / Open-Source Developer Cut (NEW cut)

| Beat | APP | What | Class |
|---|---|---|---|
| 1 | APP-2 hello-gae | 5-minute GAE quickstart, conservation gate fires | NEAR |
| 2 | APP-5 YAML config | 30-minute no-Python domain config | NEAR |
| 3 | APP-6 build-your-own | Email + reading triage skins, governed-vs-ungoverned toggle at SDK level | NEAR |

**Audience:** Self-serve developers. **Gate:** Public SDK drop.

---

## §4.11 Beat Corrections (v2.4 — **APPLIED in v2.5**, see §0.2/§0.3/§2.1/§2.4/§5)

**B1 — Invert the Rejection Moment (V2/E3):**
Reorder: promotion FIRST ("8-point gain, promoted live — that's the compounding"), THEN rejection table + SILENCE 3. No new gate logic — both arcs in existing promotion-gate logs.

**B2 — RL Naming Reconciliation (§0.2, §0.3 room 3, §5 F-25):** ⚠️ on-stage-truth
Retire the "no-RF-for-judgment" claim. Replace with: "The DECISION is centroid-distance, not reward-maximizing. Reward functions exist in the LEARNING path (exploration + credit), never in choosing the action. Exploration is conservation-bounded (`ConservationBoundedThompson`)."

**B3 — SOC Exploration Proposal-Only:** ⚠️ on-stage-truth
When SOC learning is ON, exploration can override centroid action. In demo profile: run exploration proposal-only (SOC-G1 target) so "decision is centroid" holds on stage. Or re-cut "watch it learn" to S2P via DIFF-1.

**B4 — CC-1 Two Distances:**
Canonical-distance INCREASES (production, = IKS rising). Ground-truth-distance DECREASES (oracle-only). DI-TIMELINE is consistent. Never reframe production curve as "distance to correct answers shrinking."


## §4.12 Trading Additions (v2.6)

**TRD-CLAIM-GATE — "The Claim Gate"** ⭐ The mirror ran ~25 detectors; before any "expensive truth" reaches the screen it passes a selection-adjusted evidence gate — Benjamini-Hochberg FDR, deflated Sharpe, discovered on older 70%, confirmed on held-out 30%. Badge: "23 patterns tested · 3 had power · 1 survived correction." Surface: Trading Analysis + Performance. **Class: NEAR.**

**TRD-CERTIFICATE — "The Certificate"** For a clean trader: "23 detectors, 1,847 decisions, none survive correction — you're genuinely clean," plus an edge-boundary map. **Class: NEAR.**

**TRD-GATE-DIVIDEND — "The Gate's Dividend"** "Over 90 days the gate withheld 22 findings that didn't survive correction; replayed, acting on them would have cost −$18.4K." ⚠️ magnitude illustrative. **Class: NEAR.**

**TRD-D6 — Observation-only guard:** No beat states a present-tense market call; every line is a past-tense observation about the trader's own decisions.

**TRD-D7 — B1-B8 quant substrate:** Name the shipped package once for quant-room credibility. Harden TRD-S3 trigger = multi-primitive regime break (B2 Hurst + B6 tail-dependence) with block-bootstrap p-value (B4).

**TRD-D3 — TradeZella:** 2026 entrant; mirror is now category-entry. Re-lead room 5 on the gate + abstention, mirror as opener.

**TRD-D8 — T4/T14 → TRD-S1 merge:** T4 (Regime Analysis) and T14 (Regime Shift) fold into TRD-S1 at demo time.

---

## §4.13 Purchasing Additions (v2.6)

**PUR-HERO — Mirror-open, continuity-close:** Open on I1 (gated, renamed). Close on PUR-3 + The Handoff: "Everything in this kitchen turns over. This doesn't."

**PUR-GATE — Rename + gate I1:** Rename from "Supplier Trust Trap" to signal reliability / invoice-variance profile. Ban trap/padding/stress/fraud from microcopy. Gate: partial pooling + out-of-sample + evidence floor.

**PUR-PROOF-LEDGER** (two-curve + SILENCE): Proof Curve (gated dollars, allowed to fall) + Competence Curve (rising even when dollars fall). Caption: "Every dollar we claim, we can defend — including the weeks we claim zero." **Class: NEAR.**

**PUR-NOT-YET — "Not Yet" / Quiet Week:** (1) "No supplier factor is reliably misleading yet — ~60 more deliveries." (2) "$0 incremental this week. Coverage 94%." **Class: LIVE.**

**PUR-REFUSAL — Self-pause on manager drift:** Conservation detects drift → auto-approve pauses itself. "It gave up its own authority." **Class: NEAR.**

**PUR-RAMP — Time-to-competence:** "Last GM left → 7 weeks. This time → 12 days." Non-saturating acceleration. **Class: NEAR.**

**PUR-DATA-MATURITY:** Tag beats by data maturity (P4/P7/F1/F2 need 18-24 months).

---

## §4.14 DataOps Additions (v2.6)

**DD-0 ⚠️ PRECONDITION:** Earned-trust beats are LIVE only if verified-decision → AgentEvolver loop is wired for DataOps — currently unconfirmed. Tag NEAR/ARCH honestly (F-27) until confirmed. Biggest truth risk.

**DI-ABSTAIN — "I don't know":** Agent asks permission; gateway returns evidence + abstain. "4 verified decisions — insufficient for this action." Note deliberate absence of "safe." **Class: NEAR.**

**DI-GATEWAY — Agent-Trust Gateway climax:** "/v1/trust/verify → trust, basis, or abstain." The runtime trust gateway. **Class: NEAR.**

**DI-FIRSTVS6TH — Compounding falsifiable:** "1st new source: X weeks to GREEN. 6th: Y days." **Class: NEAR.**

**DI-TWIN — Frozen-twin control:** "Frozen in March would have missed 11 of 14 catches." **Class: NEAR-HEAVY** (~2-3 wks, depends on centroid checkpoint persistence RL-PERSIST).

**DD-2 — Strengthen DI-PROOF:** Add restore + provenance log. Generalize into "prove it" affordance on every number.

**DD-6 — De-risk DI-GOLD:** $ off hero path. Gold lines as FDR + 30-day-holdout-gated hypotheses. "Value not yet verified — N more outcomes needed" empty state.

**DD-9 — Buyer/agent-language guard:** No centroid/DK/σ/α·q·V on buyer-facing surfaces. Use plain field names.

**DD-7 — Retire absolutist claims:** Replace "Level 3+ is empty for everyone" with "does the number move because of your decisions?"

## 5. Demo-base & preseed requirements (coding sessions must guarantee these)

The single biggest live-demo risk (per `narrative_readiness_v3`): a fresh install without preseed shows
**flat IKS** — and the compounding story *is* the trajectory. Preseed must guarantee, on a clean machine:

| Requirement | Why |
|---|---|
| Non-flat IKS on all 5 copilots | the trajectory is the story |
| ≥1 pending alert (SOC) + ≥1 order queue (Purchasing) | Alert Triage / 3-way match demo moments need them |
| Rejected AE variants present in logs | the Rejection Moment (§4.1) needs data |
| A `sample`-labeled value present but **never in a headline metric** | the Counterfactual F-26 refusal (§4.2) needs a clean example |
| FRED key set; QBO vars cleared; AGE started if SOC graph in the cut | no "sample" fallback / no console warnings / no empty graph |
| Cross-copilot signal seeded (Purchasing→S2P) | the compounding beat (P3) needs the banner |
| **⚠️ SOC learning ENABLED in the demo profile** (`soc/config.py:66` disables it by default) | **SOC is the flagship VC cut** — any "watch it learn / compounding" beat **will not fire** otherwise. **DoD: prove a verified decision changes a later SOC score.** If it can't be enabled cleanly, **re-cut the beat** to Trading/S2P/DataOps/Purchasing (all BUILT end-to-end). |
| **Situational tags on Trading decisions** (regime, vol_state, hurst) | TRD-S1..S4 and TRD-V1/V2/V5/V6 are **read-side analytics over tagged decisions** (C-TRD-SIT Step 1) |
| **Real regime-break window** in the Trading history (2020-03 / 2022) | TRD-S3 (throttle) and TRD-S7 (re-convergence) replay it |
| **DIFF-1 datasets:** faithful reward-max baseline on same oracle/seed (`test_baseline_is_faithful`), injected supplier-fraud regime shift, +8%-aggregate/−30%-high-severity poisoned auto-approve rule | DIFF-1 (§4.10) governed-vs-ungoverned rebuttal |
| **L-CDK datasets:** two neutral-domain datasets (email triage + reading triage), synthetic metadata only | L-CDK (§4.10) developer cut |

**Hard constraints:** BYOD imports score via `write_observation`; L5 writes are persist-before-cache;
`[VERIFY]` SOC conservation numbers (old D2 "Option C") before quoting any SOC α figure on stage.
**Naming (F-25):** no beat, caption, or script says "RL" for the primary mechanism, and no beat/script uses the retired "no-RF" claim — the reward runs in the learning path; the **decision** is centroid-distance (see §4.11 B2) — it is *decision-trace /
prototype learning from verified decisions*. **Claim scope (F-24):** "conservation governs our scoring,
exploration and scorer-evolution loops" — **not** "all loops" — until `C-GOV` lands. **Cross-copilot (F-26):**
*signals* transfer; judgment geometry is per-copilot.

### VLD preseed additions (v2.9)

#### Canonical factor and provider contract

Use this mapping to validate fixture IDs before running them. “Reported” means listed in the supplied prompt, not code-inspected in this review.

| Copilot | Dim | Factor | Reported provider / gap |
|---|---:|---|---|
| Trading | 0 | thesis_strength | No provider listed |
| Trading | 1 | market_regime | correlation_engine |
| Trading | 2 | position_sizing | portfolio_engine |
| Trading | 3 | timing_quality | No provider listed; reported TRD-2 attempt returns None |
| Trading | 4 | risk_reward | No provider listed |
| Trading | 5 | catalyst_proximity | event_scanner |
| Trading | 6 | portfolio_concentration | No provider listed |
| Trading | 7 | sector_exposure | portfolio_engine |
| Trading | 8 | options_delta_exposure | No provider listed; proposed options adapter |
| Trading | 9 | options_iv_percentile | No provider listed; proposed options adapter |
| Purchasing | 0 | cost_deviation | invoice_analytics |
| Purchasing | 1 | supplier_reliability | supplier_scorecard |
| Purchasing | 2 | expected_demand | demand_forecast |
| Purchasing | 3 | supplier_lead_time | No provider listed; new supplier delivery adapter |
| Purchasing | 4 | waste_risk | waste_tracker |
| Purchasing | 5 | event_flag | No provider listed; new event adapter |
| Purchasing | 6 | price_memory_index | No provider listed; new matched-price-history adapter |

**Do not alias away the schema conflict:** `signal_confidence` and `options_gamma_risk`, named in the Trading starvation prose, do not occur in the provided ten-factor list. Record them as unresolved experiment-schema labels. Do not silently map them to thesis strength, timing quality, delta exposure or IV percentile. The aggregate 24/50 is reportable as the supplied result; factor-specific claims require the run's exact dimension map and update counts. Provider coverage in the application and learning coverage in the experiment are separate inventories.

#### Fixtures, evidence and honest expectations

The values below are **proposed synthetic raw records**, not observed output from the named preseeds. They make each story concrete. The implementation must apply the real normalization and scorer to them; if the target route or action is not reproduced, revise the fixture transparently or the storyboard, never the computation. All fixtures carry stable IDs, version, content hash, category, action enum version and a common historical cutoff.

| Beat / seed | Required planted evidence | Required replay / limits |
|---|---|---|
| **VLD-TRD-1**, extended portfolio fixture | Synthetic instrument `SYN-ALPHA`; three held positions `SYN-BETA/GAMMA/DELTA`. Proposed same-window historical return correlations 0.82/0.76/0.71, with the underlying return series retained. Freeze holdings and the sizing inputs before the candidate trade. Attach a historical market-regime record. | Correlations are computed from the planted series, not typed badges. They are pairwise associations, not a calculation of effective bets or proof of risk reduction. Record the portfolio-engine mapping into dim 2, then dim 1. Target `[2,1]`, final strong→partial. |
| **VLD-TRD-2**, legacy + diagnostic | A separate historical income-strategy case; dim 2 evidence sufficient for the reported initial flip; dim 3 missing/unavailable. Proposed options diagnostic: IV percentile **94**, based on a declared historical window ending at cutoff, with an internally consistent synthetic options snapshot. | Legacy `[2,3(None)]`, strong→partial. No factor/action change from None. Diagnostic manually admits dim 9 in a new episode; an additional action flip is unverified until computed. IV percentile is not implied volatility of 94%, a probability of loss, or a recommendation. |
| **VLD-PUR-1** / `VLD-PUR-DEMAND-SPIKE` | Protein case: baseline **120** covers and a confirmed **180**-cover event. Proposed extra lot expires before that event; include lot quantities, existing usable stock, refrigerated capacity, service time and a separately documented later delivery opportunity. | Compute event_flag and waste_risk using their actual semantics. Target `[5,4]`, more→less for the selected delivery. Do not claim the alternative delivery is booked or guaranteed. |
| **VLD-PUR-2** / `VLD-PUR-VENDOR-CASCADE` | Dairy case: **12 hours** until service, supplier arrival **30 hours** away, expiry/usable-stock records establishing the gap. Proposed supplier on-time record: **17 on-time deliveries out of 50** eligible verified deliveries, hence 0.34. Plant two approved alternative-supplier records, with availability allowed to be unknown. | Target `[4,3]`, planned→skip for this order. “On time” and the 50-record cohort are defined explicitly. The 0.34 is a supplier delivery statistic; it is neither a K value nor data-source trust. Alternatives are content-keyed and separately costed. |
| **PUR-2 price-memory depth card** | Same item, grade, pack size, currency and delivery terms: proposed current unit price **22**, matched historical median **20** from **12** eligible prior invoices. | Raw deviation is 10%; this is not automatically the normalized price_memory_index. New dim 6 provider required. No causal K story, action flip or savings claim unless separately replayed. |
| **VLD-TRD-S1** | Budget=0 version with initial strong_execution. | Zero provider calls; identical vector/action; explicit budget-zero halt; unsupported dimensions stay visible. |
| **VLD-PUR-S1-STANDARD** | Budget=0 version with initial order_more. | Zero provider calls; identical vector/action; explicit budget-zero halt. |

**Mandatory control fixtures:** missing provider; unavailable evidence from an otherwise registered provider; successful query with an informative negative result; future-dated record; stale record; exhausted candidate set; budget zero; and a conservation-blocked emit. These distinguish evidence absence, negative evidence, policy choice and authority. Do not infer an “unresolvable” case solely from budget exhaustion.

#### Domain wiring that must be built

| Wiring item | Trading | Purchasing | Acceptance evidence |
|---|---|---|---|
| Decision attachment | `decision_id → trade_id → ticker → historical position` | `decision_id → order_id → item → supplier` | Stable tenant/account/site-scoped IDs; missing/ambiguous links return explicit unavailable status. No latest-record fallback. Imported observations do not become verified decisions by virtue of import. |
| Domain traversal | Candidate trade → portfolio as of case time → correlated positions via portfolio_engine | Item/order → approved supplier relationships → alternatives via supplier_scorecard | Actual edges/queries and source references recorded; labels distinguish content-keyed traversal from Q dimension selection. An analytics panel does not prove a traversable investigation path. |
| Historical cutoff | Historical trades, holdings, prices, returns, corporate/event records and verification times | Orders, supplier commitments, receipt/waste outcomes, invoices, event revisions and verification times | Require both event time and information-availability/verification time to be no later than the case cutoff. A later correction must not leak into the replay. |
| Historical learned state | Model/K snapshot trained only on outcomes available by cutoff | Same, including pre-handoff retained state | Snapshot provenance and training cutoff logged. Filtering evidence while using future-trained K is still leakage. |
| Missing providers | Register timing, options and any proposed thesis/risk readers explicitly | Register event, lead time and price memory explicitly | Report real registry coverage. Define provider eligibility and failure behavior; keep the legacy None trace separately versioned. |
| Source-to-factor mapping | Portfolio correlations can inform documented sizing/exposure factors | Shelf life, arrivals and prices map through documented normalization | Record changed dimensions and evidence lineage. If one read updates multiple factors, disclose all of them and any bundled source work. |

Historical correlation computation also needs a declared return frequency, lookback, missing-data treatment and minimum support. Historical supplier/price matching needs item/site/pack/terms scope and a declared cohort. Do not use current holdings, subsequently revised delivery promises or the eventual outcome of the case under investigation.

**Conservation configuration:** the supplied update reports penalty ratios of **Trading 2:1** and **Purchasing 3:1**. Record and verify the actual pinned configuration and the error directions those ratios weight; do not silently change application policy to match this document. These are reported model settings, not evidence that Trading decisions are inherently low-stakes. Each replay records the real emit-gate result independently of its investigation order.

#### Policy, budget and trace contract

Use the supplied Q equation, not the older dominant-factor or confidence-threshold dispatch story:

```text
Q_d = K_d * G_d
G_d = 1 / (100 * max(sigma_d^2, 0.001))
      + abs(mu[a1,d] - mu[a2,d])
      + abs((v[d] - mu[a1,d])^2 - (v[d] - mu[a2,d])^2)
```

The implementation must declare how a1/a2, category, K and variance are indexed; the prompt does not fully specify those contracts. Freeze learned μ, σ and K during each episode. Recompute Q after admitted evidence changes the case state, using the actual action pair. Record eligibility changes separately. This is a score-based priority heuristic, not a calibrated expected-value-of-information estimate or an optimality guarantee.

For any claim that learned K caused d to precede j, record the actual comparison `K_d G_d > K_j G_j`, the unit-K order and the real learned checkpoint. With positive weights, the crossing condition is `K_d/K_j > G_j/G_d`; actual K bounds and update rules determine whether it is reachable. Since those bounds and checkpoint values were not supplied, no specific K-dependent ordering is certified here. Do not plant arbitrary values such as K=0.9/0.3 and call them learned.

**Budget convention proposed for v2.9:** B=2 means at most two evidence-request attempts, including failed attempts. A bundle of provider queries is not free: record underlying request count and cost as well. Capture separately attempted reads, successful reads, admitted observations, exclusions and unvisited candidates. If the runtime uses different accounting, document it and update the caption; never relabel an attempt as a free read to preserve a scene.

Under provider-aware eligibility, an unregistered dimension is excluded without issuing a request. Under the legacy TRD-2 behavior, the failed dispatch attempt is visible and consumes its configured cost. A successful “no relevant records found” query may admit negative evidence only with adequate query coverage and a defined transform. `None`/unavailable supplies no such evidence. Re-scoring the same vector with the same frozen scorer must not invent an action flip.

Do not hardcode “halt after two” if the real policy halts earlier. Preseed must establish the actual stopping path. Store the runtime halt reason and all concurrently reached limits. Map budget exhaustion, unavailable/exhausted candidates, residual stopping, instability/flip limit, timeout and emit refusal distinctly. A halt can mean incomplete evidence; it does not mean certainty. Conservation is an emit-gate snapshot within the episode under the stated design, not the branch selector or evidence of routing accuracy.

**Persisted trace requirements (schema requirements, not a claim that these field names already exist):**

- Case/entity IDs; synthetic provenance; case and verification cutoffs; model/K/normalizer/provider/policy versions; category and exact action enums.
- Initial candidate inventory and eligibility; per-candidate Q components; selected dimension and tie-break; consumed cost; source record IDs; query coverage; availability status; admitted changes; raw evidence reference.
- Initial and per-step action/scores, exact flip step, halt reason, emit-gate outcome, and single-pass comparison on the identical initial state.
- Learning-support counts by category/dimension, with zero support distinguished from missing counters. Counterfactual/manual replay parent ID and independent budget.
- Engineering view may show formula quantities. Buyer view shows check order, evidence, assessment change, unresolved checks, budget and halt; no centroid/DK/σ/v_t/margin jargon or calibrated-confidence implication.

Persist append-only audit traces as the explicit allowed write; keep authoritative scorer, decision/outcome state and source graph unchanged during investigation. This resolves v2.8's simultaneous “read-only graph” and “persist trajectory in AGE” requirements. Never feed a fixture trace into customer verification metrics or the learning path.

#### Work packages and acceptance

| Package | Owner | Definition of done |
|---|---|---|
| SDK domain investigation wiring | **Session A** | Entity bindings, historical cutoffs, provider eligibility and transforms implemented for the four routes; truthful missing-provider behavior; existing score/learn APIs retain their semantics. |
| Shared trace and record mode | **Session A**, **Session C** for SOC parity | Persisted traces drive InvestigationTracePanel and recorded cuts; badges survive transitions, empty states and manual comparisons. Frozen model state remains unchanged. |
| Fixture and claim review | **Content + A/C** | Manifest links routes, computed numbers and legal K snapshots; missing evidence is shown honestly; scripts match actual traces and class status. |

Effort is **not estimated** without repository discovery; these are coherent packages, not claimed one-day wiring tasks. During implementation, include targeted backend checks plus Playwright coverage for an atomic investigation and the full mirror→trace→diagnostic/handoff flow. Review both line-by-line correctness and architecture/product conformance, including blast radius across the shared SDK and SOC surface. Report measured request latency, case/graph size, connection mode and rendering overhead separately from unmeasured analyst-time benefit.

---

*Merged from `demo_scenarios_and_usecases_v2_8.md` and `demo_scenarios_v29_trading_purchasing_additions.md`; `ci_vld_architecture_prepaper_v7 (1).md` was read for experiment context. Older companions retained as unverified references: `vld_graph_reasoning_architecture_v3.md`, `soc_rho_structural_feasibility_audit_2026-09-08.md`, `ci_vld_depth_memo_v13.md`, and `vld_depth_p1_decision_graph_topology_report.md`. All nine beats are **ARCH** on planted fixtures; deployment routing accuracy is not yet measured. Reported offline experiments are separate from fixture computation and production readiness; none implies roadmap is LIVE (F-27), and no VLD analyst-time savings are claimed.*

---



---

## §4.15 S2P Additions (v2.6)

### S2P-FIX-1 — Correct "every competitor runs rules" overclaim
§2.5 SILENCE 2's payoff line reads "Every competitor auto-approves by rule. We reason from context." In 2026 that's false (Coupa Navi and SAP Joule reason). **Keep the S14 rule-vs-reasoning contrast** — it's true for a threshold rule — but retune: *"A threshold rule rejected this — 5.2% over a 5% line. The reasoning read the contract and the commodity index and accepted it, correctly. The point isn't that others lack agents; it's that a rule fires on a number, and judgment reasons about why."*

### S2P-LEDGER — "Earned Autonomy, week over week" ⭐
Auto-approve coverage climbing (Jan 18% → Feb 31% → Mar 46%), plus review-hours avoided, abstain rate, bad-auto-approval rate, new-category time-to-trust, promotions/rollbacks; under every expansion, a plain-language *why*. Surface: S2P **Performance** (AutonomyLedger panel). **Class: LIVE** (single-arm) → **NEAR** (two-arm vs frozen).

### S2P-EXTINCT — "Exception extinction" (the promotion workflow)
The lifecycle on one class: **Discover → Shadow → Promote → Measure → Keep/Rollback → Transfer.** "This quantity-mismatch class was consistently buyer-approved → shadow → counterfactual → promoted day 34 → monitored → transferred to a second plant." **Class: NEAR.** Reuses existing promotion/rejection logs — surfacing task, no new gate logic.

### S2P-TWIN — "The version we froze in March" (frozen-twin control)
Two curves on the customer's own data — a twin pinned at day-one config vs the live system — the live one pulling away; the gap is the compounding. "The distance between the two lines is the thing you're buying — measured on *your* decisions, not asserted." **Class: NEAR-HEAVY** (~2-3 wks, depends on centroid checkpoint persistence RL-PERSIST). Label divergence MODELED/PILOT-TARGET until measured on real data (F-27).

### S2P-WHATIF — "What would change this decision?" (counterfactual inspector)
Beside "Why: 5.2% variance, copper +4.8%, §7.3 allows ≤110%, accept 0.91" → "Would flip to HOLD if: contract allowance < 4.8% / supplier exception history deteriorates / commodity correlation leaves trusted range / regulatory evidence incomplete." **Class: NEAR.**

### S2P-DAY0 — "Here's what we can't trust yet" (day-0 readiness)
Week-one readiness read leading with what the data **doesn't** support yet: source coverage/completeness/provenance/trust-tiers, and the honest empty state — **not** a fabricated ROI. "Day one we don't hand you a number. We hand you the truth about your data." **Class: NEAR.** Cannot use learned factor-trust weights (they need accumulated decisions) — built on enrichment layer.

### S2P-CONFIDENCE — "What I'm not confident about" (always-visible)
Permanent confidence band per category — "electronics: novelty rising, auto-approve paused itself" — visible before anything breaks. "The fear isn't that it's wrong — it's that it's wrong *quietly*. So it tells you, all the time, where it isn't sure." **Class: LIVE** (novelty/self-pause built) → **NEAR** (always-visible panel).

### S2P-ROOM — Cross-system neutrality tear-down
"SAP or Coupa will build judgment memory into their own stack." → "Inside their own walls, sure. But SAP's agent will never optimize a *Coupa-to-Celonis* cross-system workflow, and Coupa's won't reach into SAP's. Our moat is **neutrality across your whole stack** — we compound judgment over decisions that span systems no single suite owns."

### S2P-LOOM — Update L-S2P cut (§7.2)
Lead-simple spine: S14 situation-analysis (SILENCE 2, corrected) → S2P-LEDGER → S2P-EXTINCT → S2P-TWIN → close on moat + "which decision to change" (ENT-1 guard). Keep S6 continuity (E6) as the "your best buyer left; the judgment stayed" beat.


---

## §4.16 SOC Additions (v2.6)

### SOC-FIX-1 — Retire "we compound, they don't" / "they start at zero"
Any beat that leads with "our SOC learns and theirs doesn't" is 2026-false (Torq/Simbian/Prophet/Stellar all claim learning; Torq Retrospect imports years of case history). **Replace with cold-start counter:**
> "Imported history makes you good at the last firm's incidents. We start you on a strong prior and then learn where *your* environment disagrees with it — and that disagreement is the compounding curve. The noisier your environment, the bigger the gap we open."

### SOC-FIX-2 — Two-regime guard + two overclaims to strip
- 97.89% centroidal-synthetic number NEVER on the same surface as 78.9% product number (§4.4)
- No beat says AgentEvolver "evolves the deployment mid-incident" → say *policy evolves continuously from verified outcomes without a retrain or vendor release*
- No beat says tech-process fusion "makes the attack class impossible" in SOC today → ARCH-for-SOC, demonstrated on S2P/DataOps

### SOC-CONTROL — "How do you know it got better?" (Learning Control Room, F16) ⭐
One promoted change told in five faces: **BEFORE** (policy) → **CHANGE** (which variant) → **EVIDENCE** (verified outcomes that caused it, with provenance) → **EFFECT** (which past decisions flip, via replay) → **SAFETY** (shadow-test + conservation + rollback target). Surface: Tab 2 Runtime-Evolution. **Class: LIVE** primitives → **NEAR** (unified panel).
"Every change the system makes to itself shows up here: what changed, the outcomes that earned it, which past calls it would flip, and the safety check — with a rollback button."

### SOC-LADDER — "Autonomy it has to earn" (F17)
Per category, the rung: **Observed → Assisted → Shadow-qualified → Auto-approved → Circuit-broken.** `cloud_infrastructure` auto-approved, `insider_threat` held at Observed by design, one category circuit-broken this week with the reason. Surface: Tab 4 Compounding header + Tab 3 per-alert badge. **Class: LIVE** → **NEAR** (visible per-class ladder).

### SOC-TWIN — "The version we froze on day one" (F18)
Two curves on the customer's own alerts — a twin pinned at bootstrap μ₀ (no learning) vs the live system pulling away; the gap is the compounding, in safe coverage and Recovery Half-Life. Surface: Tab 4 Compounding. **Class: NEAR-HEAVY** (~2-3 wks, depends on centroid checkpoint persistence RL-PERSIST). Label divergence MODELED/PILOT-TARGET until measured (H7).

### SOC-NOPRECEDENT — "Similar past cases: none" (F19 — the Stryker beat)
The similar-cases sidebar's honest empty state, surfaced beside a high-confidence action. The Stryker alert: privileged_identity_context elevated on a service-tier identity issuing bulk Intune ops, MFA/device clean, "**similar past cases: none — unprecedented here**," ESCALATE at high confidence. **Class: LIVE.**
"A retrieval system is blindest exactly here — no precedent, nothing to recall. Ours scores the identity risk geometrically and escalates anyway, and it tells you plainly it's never seen this before."

### SOC-WHATIF — "What would change this decision?" (F20)
Beside "Why: privileged identity 0.9, threat-intel 0.8, velocity anomaly" → "Would drop to INVESTIGATE if: identity tier were standard / MFA clean / no velocity anomaly / no threat-intel enrichment." Surface: Tab 3 Triage. **Class: NEAR.**

### SOC-DAY0 — "Here's what we can't trust yet" (F21)
Week-one readiness read: source coverage, completeness, provenance, connector health (Pulsedive/CISA KEV/NVD), and the honest empty state. No fabricated ROI. Surface: fresh-tenant SOC view. **Class: NEAR.** Cannot use learned factor-trust weights — enrichment layer only.

### SOC-FRONTIER — "Coverage that grows at a fixed safety bar" (§B)
Replaces raw-accuracy hero with two compounding metrics: safe auto-approve coverage climbing at constant safety bar (per category), and Recovery Half-Life (decisions + days to re-reach competence bar after regime break). Surface: Tab 4 Compounding. **Class: LIVE** (single-arm) → **NEAR** (two-arm vs frozen twin).

### SOC-GAUNTLET — "Run the novelty test yourself" (§C)
Five perturbations: no-precedent (Stryker) / misleading-precedent / signal-inversion / regime-break / adversarial-context — each showing act-or-abstain, the no-precedent surface, and Recovery Half-Life. Surface: Tab 3 Triage, scripted five-beat sequence. **Class: LIVE** decision path → **NEAR** packaged benchmark.
"Stryker isn't a lucky anecdote — it's one of five ways we stress the no-precedent claim. Run them on your own stream."

### SOC-ROOM — Platform-absorption kill-shot (CrowdStrike/MS/Palo Alto)
"CrowdStrike and Microsoft will just ship good-enough triage free in the console." → "Inside their own console, sure — locked to their own data lake. Ours is the **cross-stack judgment gateway**: it compounds *your firm's* verified-decision judgment across CrowdStrike **and** Sentinel **and** Okta at once, over decisions that span systems no single platform owns."

"Security Copilot comes bundled in E5 for near-zero." → "A bundled per-seat copilot doesn't touch the budget line this replaces — MDR/MSSP and SIEM ingest — and it can't show you your own compounding curve."

### SOC-LOOM — Updated L-SOC cut (§7.2)
Lead-simple spine: SOC-NOPRECEDENT (Stryker no-precedent) → SOC-CONTROL (how you know it got better) → SOC-LADDER (autonomy it earns) → SOC-TWIN (frozen twin proves it) → close on moat (customer-owned judgment + SOAR-first write-back). Keep cross-copilot beat as *signal transfer, not shared judgment*.

---

## §4.17 VLD Investigation Beats (Room 16)

### VLD Investigation Beats (Room 16)

**All nine beats share an investigation trace contract.** The supplied update reports Q-based investigate endpoints, preseeds and offline experiments; it does not verify shipped production domain wiring or a deployed shared trace surface. The buyer panel displays evidence order, admitted records, changed assessment, unread evidence, consumed budget and halt reason. Internal views expose Q components and scorer quantities. Every planted preview carries PLANTED FIXTURE, ROADMAP and ROUTING ACCURACY: not yet measured for this deployment. A single-pass contrast uses exactly the same initial case, model and gate. Frozen learned state is read during the episode; only the append-only trace is written. All nine beats remain ARCH. Release requires the implementation and deployment evidence specified below.

**REPORTED OFFLINE EXPERIMENT**

| Copilot | Reported tensor | Routing change | Accuracy change | Starvation | Hurts |
|---|---|---:|---:|---:|---:|
| DataOps | 6×5×6 = 180 | +0.190 (+43% relative) | +0.320 | 8.3% | 0 |
| Purchasing | 5×4×7 = 140 | +0.210 (+41% relative) | +0.300 | 28.6% | 0 |
| Trading | 5×4×10 = 200 | +0.120 (+19% relative) | +0.140 | 48.0% | 0 |
| SOC | 6×4×6 = 144 | +0.120 (+17% relative) | +0.140 | 36.1% | 0 |
| S2P | 5×5×8 = 200 | +0.030 (+5% relative) | +0.060 | 22.5% | 0 |

These are the supplied K-learning results using production centroids in an offline experiment. For rate metrics, +0.120 is **+12 percentage points**, not +12% relative. “Hurts=0” is a reported experiment statistic whose unit and denominator were not provided; it is not proof that no future decision can be harmed. The non-starved 52% of Trading pairs is not “52% that works,” nor is starvation the fraction of trades left uninvestigated.

| Variant | Reported routing | Reported accuracy |
|---|---:|---:|
| Static | 57.8% | 73.6% |
| RNN | 56.3% | 77.6% |
| GRU | 48.8% | 69.2% |
| LSTM | 47.0% | 66.4% |

**Precise conclusion:** Static exceeded RNN routing by **1.5 percentage points**; RNN exceeded Static accuracy by **4.0 points** in the reported comparison. Neither universal Static superiority nor an adaptive-routing advantage follows. No sample sizes, uncertainty intervals or matched ablation details were supplied. This comparison must not be conflated with the Trading-specific greedy/bandit table, where 73.6% denotes **routing**, not Static accuracy.

The supplied Trading exploration comparison reports greedy starvation/routing **48% / 73.6%**, Thompson **0% / 53.0%**, UCB **0% / 65.0%**. Coverage improved while routing fell by **20.6** and **8.6** points respectively. The reported greedy K curve approaches a plateau around **500 decisions**, with the cited starvation series **19%→14% at 2,000**; its aggregation is unspecified and must not replace Trading's 48% figure. Continued data collection alone is not evidence of unbounded compounding under unchanged greedy selection.

Between-decision K learning (`REC-R2`) is the stronger supported design direction, but the table does not prove that an RNN is necessary to implement it. A static planner can in principle consume an updated K snapshot between decisions. Test that baseline before crediting the benefit to the recurrent architecture. Remaining priorities are legal K learning, evidence access, coverage and governance; route variant is an independently tested choice.

**VLD-SOC-1 — "The Investigation Trace"** *(the honest version of "it investigated like an analyst")*
| Field | Value |
|---|---|
| Surface | SOC **Alert Triage** (Tab 3) → InvestigationTracePanel beside the existing SituationPanel |
| API | `POST /api/soc/investigate` (new, ARCH); reads `DECIDED_ON` → `MEMBER_OF` → `CONTINUES` campaign topology (P1-confirmed) + the six SOC factor computers via the existing provider |
| Class | **ARCH** |
| Audience sees | A planted mixed-indicator alert retains content-keyed `lateral_movement` dispatch. Q, computed over eligible evidence dimensions, selects the identity-related auth read first. That read admits the documented credential evidence and the actual scorer determines the action change. A linked campaign/pivot traversal is shown as a disclosed content-keyed subread or a separately budgeted read. Do not claim a second Q-selected lateral-movement check unless its own recorded Q selection exists. Display actual budget and halt. |
| Spoken | “In this planted alert, the retained score selected the auth check first. The record shows what came back and what changed the assessment. Any linked campaign lookup is labeled separately. This demonstrates the proposed order; it does not establish that adaptive routing beats a static plan.” |
| DoD · Honesty | Replace the 0.9-versus-0.3 dominant-factor rationale with logged Q components and the chosen dimension. The old 0.04/0.31 margins may appear only if actually reproduced. Resolve the old inconsistency between a one-read step list and a trace claiming two investigations. `conservation GREEN` appears only from the configured emit gate. SOC learning may remain off during frozen-state routing. |

Add optional engineering presenter note: “The supplied SOC experiment left 36.1% of category–dimension pairs without learning updates.” Do not imply that this alert's chosen dimension was starved without its per-pair counter.

**VLD-SOC-2 — "The Wrong-First-Step Recovery"** *(the correction is the demo moment)*
| Field | Value |
|---|---|
| Surface | SOC **Alert Triage** (Tab 3) → InvestigationTracePanel |
| API | `POST /api/soc/investigate` with budget B_max = 2 branches; C4 per-step halt (normalized residual + budget + flip-count) |
| Class | **ARCH** |
| Audience sees | Case A, the main recovery scene: the auth query executes successfully over a documented window and returns a **verified negative finding**, admitted through a defined factor transform. Re-score, record Q for remaining eligible dimensions, then select the process-tree read if it wins. The process read finds the planted injection and the actual scorer determines the final action. Case B, the missing-evidence control: the auth source is unavailable/None, so no factor or action change is attributed to it; the next selection may follow candidate exclusion alone. Both attempts and failures remain visible. |
| Spoken | “The first check found no credential-reuse evidence in its covered window. After that finding was admitted, this replay selected the process check. The trace shows the change of direction. A static plan could select the same two checks; this case demonstrates a legible recovery, not a measured routing advantage.” |
| DoD · Honesty | Exactly two evidence attempts at B=2, with the final re-score numbered as a computation rather than a third read. Do not infer a flip from `None`, or say the halt controller chose the next branch. Re-score/Q select; halt logic decides whether to continue. Remove the claim that one wrong-first case proves ρ<½: a single failure does not estimate a routing rate. At full evidence budget, exhaustive retrieval could inspect the same evidence. |

The reported SOC model values and the negative-evidence transform are not supplied, so the action-flip trajectory remains a fixture acceptance condition. A fixed precomputed order may match it; compare the remaining-candidate ranking at S0 with that after admission before calling it adaptive rerouting.

**VLD-DO-1 — "Three Systems, One Root Cause"** *(DataOps triage)*
| Field | Value |
|---|---|
| Surface | DataOps **Triage** (D-M1) → InvestigationTracePanel; hand-off into **Insight** → `ApplyFixModal` (E5) |
| API | `POST /api/dataops/investigate` (new, ARCH) over the existing system-keyed decision history (`context_router.py:913-931`, P1: low m_topological) + `/api/s2p/insight/cross-graph`, `/api/context/apply-fix` (shipped, E5) |
| Class | **ARCH** (and DD-0 still applies: DataOps learning loop unconfirmed — the routing here reads frozen μ and does not depend on it) |
| Audience sees | A planted billing_api case has competing schema-change and upstream-failure hypotheses. Bind those hypotheses to the actual DataOps factor/action schema; do not assume their names are action centroids. Log Q for the eligible evidence dimensions and the adapter that maps the winner to schema-history retrieval. Admit the MATKL_V2 record, re-score and halt according to policy. The downstream lineage expansion to three systems is visibly CONTENT-KEYED / PREREQUISITE and separately costed. |
| Spoken | “This planted replay selected schema history first, and that read found the migration. The downstream lineage view shows the affected systems. The trace separates the scorer-selected check from the ordinary lineage lookup.” |
| DoD · Honesty | Retained-state provenance replaces unsupported pipeline-specific learning claims. Factor-level weights do not automatically rank systems: either specify and validate a factor-to-system impact aggregation, or show affected systems without a learned ranking. The result recommends a fix; the VLD trace does not execute ERP write-back. Decision→Pipeline attachment and as-of evidence remain required. |

Technical note: DataOps' reported K gains are the largest in this five-copilot table, but DD-0 and the production wiring gates remain. Its 8.3% starvation figure belongs in the coverage view, not in a claim that every source is learned.

**VLD-DO-2 — "Known Pattern, New Twist"** *(coverage-aware investigation and abstention — policy extension)*
| Field | Value |
|---|---|
| Surface | DataOps **Insight** → InvestigationTracePanel beside the CentroidTimelinePanel (DI-TIMELINE) |
| API | `POST /api/dataops/investigate`; Q ranks available dimensions. A separate proposed coverage/abstention controller must be specified if the scene dispatches a broad-read bundle. |
| Class | **ARCH** |
| Audience sees | Two planted cases contrast a supported history match with sparse or conflicting support. Q selects eligible dimensions; a broad-read fallback, if built, is labeled as a separate controller action and charged for its underlying reads. If the resulting support is insufficient, emit the actual review/referral action. Show “similar resolved cases: none” only from a query with a stated similarity criterion, window and cutoff. |
| Spoken | “The stored cases gave limited support for this combination. This architecture preview shows the additional checks and the point where it would refer the case for review. The broader-read policy needs its own implementation and evaluation.” |
| DoD · Honesty | Retire hand-pinned 0.62/0.93 values and the claim that low softmax margin itself implements broad-vs-deep routing in the supplied Q equation. A softmax score is not automatically calibrated confidence, and a large top-two margin does not establish proximity to known data. Define absolute support/distance, match criteria and calibration separately. No claim that a “new cause” or absence of precedent follows from margin alone. |

This scene stays in the catalog as an explicitly broader ARCH design. It must not be staged as evidence that the currently described Q mechanism already provides novelty detection or broad-read dispatch.

**VLD-S2P-1 — "The Supplier It Knew"** *(learned supplier pattern orders the investigation)*
| Field | Value |
|---|---|
| Surface | S2P **Exception Triage** → SituationPanel + InvestigationTracePanel; extends S14-CONTRAST (§4.2.1) with an **investigation-order strip** |
| API | `POST /api/s2p/investigate` (new, ARCH) through the **S2P Context Builder / Traversal Context** and supplier-keyed prior-decision matcher (`s2p_context_builder.py:150-174`); as-of supplier matcher required. No native graph traversal claim without runtime query evidence. |
| Class | **ARCH** |
| Audience sees | A separate planted Supplier Aster dual-mismatch case starts with both price and quantity questions unresolved. Pre-cutoff verified history provides a derived prior, proposed fixture counts 31 partial-delivery and 10 pricing-error cases (3.1× within that defined cohort). Record how that prior enters the scored state or learned snapshot. Q must then independently select the evidence dimension mapped to the goods receipt. Receipt evidence is admitted; the actual action enum and halt are computed. No uncounted contract read occurs first. |
| Spoken | “In this planted case, the supplier history was an input to the score, and the score selected the receipt first. That receipt resolved the mismatch in this fixture. The comparator shown here is our declared contract-first baseline; a receipt-first static plan could make the same selection.” |
| DoD · Honesty | History ratio, Q order and resulting action must all be replayed. A 3.1× ratio alone neither proves Q priority nor the correct action. `partial_delivery` may be a cause label; `accept-with-adjustment` must be validated against the actual action enum, not invented as an API result. Invoice adjustment is not automatic execution. Include the cost of history acquisition and prerequisites. “One fewer read” is allowed only when observed against a named internal baseline with the same initial information and stopping rule; never generalized to all rule engines. |

The supplied S2P routing gain is +0.030, the smallest in this comparison; that is a reason for measured positioning, not an invented explanation of diminishing returns. Supplier-specific conditional state, action mappings and query cutoffs remain to be verified.

**VLD-TRD-1 — “The Position Wasn’t Alone”**

**Story:** portfolio exposure changes the investigation order before the historical execution assessment changes. This is the positive, supported-provider story; it does not imply that Trading's unvisited factors are unimportant.

| Field | Value |
|---|---|
| **Surface** | Trading **Analysis** → new `InvestigationTracePanel`, opened from a selected historical trade beside the existing Trust Radar. Add a portfolio-evidence drawer; proposed UI, not an existing tab. |
| **API** | `POST /api/trading/investigate`. Request is anchored to a decision, historical trade, frozen portfolio snapshot and `as_of` time. Route target: **dim 2 `position_sizing` → dim 1 `market_regime`**. |
| **Class** | **ARCH**. The prompt reports both dimension providers; Decision→Trade attachment, portfolio correlation traversal and temporal filtering remain unbuilt. |
| **What audience sees** | (0) A synthetic historical `trend_following` case has single-pass action `strong_execution`. Its thesis looks attractive, but the trace lists position sizing as the first selected evidence dimension. (1) The portfolio read reveals three other positions sharing exposure with this trade. Their identities are reached by the portfolio provider's entity traversal, labeled `CONTENT-KEYED / PREREQUISITE`; Q selected the **dimension**, not each position. Evidence is admitted into the documented factor transformation. (2) After re-scoring, market regime is the next selected dimension. Its historical evidence completes the assessment. The reported preseed's final target is `partial_execution`; the trace must locate the actual flip at the step where it occurs. (3) The panel halts at the configured budget and displays the original and investigated assessment. |
| **Caption** | *The historical setup looked strong. The portfolio changed the assessment.* |
| **Spoken** | “In this planted historical case, the score selected portfolio exposure first. That read connected the trade to three positions already on the book. It then checked the market regime, and the assessment ended at partial execution. The trace shows the selected order and the records behind it. Correlation supplied the evidence; the scorer selected when to request it.” |
| **Silence beat** | **SILENCE 8.** Pause for five seconds when `1 · Position sizing → three linked positions` appears above the still-unread thesis entry. Keep the roadmap and provenance badges visible. Resume: “The first check was the portfolio.” |
| **DoD / Honesty** | Preserve `VLD-TRD-1` as the reported regression ID; introduce the expanded portfolio fixture with a versioned suffix, rather than claiming those edges existed in the original seed. Replay must produce route `[2,1]`, final `strong_execution → partial_execution`, actual intermediate actions, evidence references and Q ordering. No assertion that every volatile case checks risk first. No investment return, risk reduction or timing claim. Routing accuracy remains unmeasured for deployment. Where the configured budget covers every eligible read, say exhaustive retrieval could also inspect them all; otherwise say unvisited reads remain. |

**Internal validation contrast:** use the same frozen scorer and policy on a paired portfolio snapshot with reduced shared exposure. Preserve the thesis inputs and log all changed exposure inputs. A different order is a **test target**, not a promised result; show it only if Q actually changes the ranking. A source named `portfolio_engine` does not independently establish why that dimension won.

**Optional regime contrast:** connect to TRD-S1 only after a paired calm/volatile replay proves a route difference. The given Q formula does not itself establish regime-indexed K or a general “thesis in calm / risk-reward in volatility” policy. `risk_reward` and `thesis_strength` have no registered evidence providers in the supplied inventory, so that suggested contrast needs additional wiring.

**VLD-TRD-2 — “The Check It Never Made”**

**Story:** an apparently reasonable investigation ends with a visible evidence blind spot. The distinction from TRD-1 is **coverage failure and missing evidence**, not another successful portfolio flip.

| Field | Value |
|---|---|
| **Surface** | Trading **Analysis** → `InvestigationTracePanel`, with an “Unvisited evidence” drawer and a separately labeled diagnostic replay. Connect to TRD-CERTIFICATE's evidence-boundary story. |
| **API** | Main replay: `POST /api/trading/investigate`, reported route **dim 2 `position_sizing` → dim 3 `timing_quality`, returning `None`**. Diagnostic: a separate proposed sandbox replay admitting dim 9 `options_iv_percentile`; no invented production endpoint or silent provider addition. |
| **Class** | **ARCH**. Dim 3 has no provider in the reported registry. Neither dim 8 nor dim 9 has one. A legacy missing-provider attempt must be distinguished from an eligible evidence read. |
| **What audience sees** | (0) A synthetic historical `income_strategy` case starts at `strong_execution`. (1) Position-sizing evidence changes it to `partial_execution`. (2) The reported legacy route attempts timing quality and receives no evidence. Display `UNAVAILABLE / NO EVIDENCE ADMITTED`; do not change the factor vector or action merely because `None` arrived. (3) Halt with the coverage gap visible. The inventory lists options delta exposure and IV percentile as unavailable through the current provider configuration, independently of any learning-coverage status. (4) Open a separate `MANUAL EVIDENCE REPLAY — NOT POLICY-SELECTED` card: a planted historical IV percentile is admitted through a proposed adapter and the scorer is run again. The desired diagnostic is a further assessment change; publish the actual result, including no change if that is what the scorer produces. |
| **Caption** | *An investigation can finish with an important check still missing.* |
| **Spoken** | “This planted replay checked position sizing first. Its next attempt returned no evidence, and the trace kept that gap visible. The options check was never made. This separate replay asks what the missing IV evidence would have changed; it does not show that the policy selected it. In the supplied offline Trading experiment, 24 of 50 category–dimension pairs received no learning updates. That is a coverage limit we need to measure, not hide.” |
| **Silence beat** | **SILENCE 9.** Pause for five seconds with `2 · Timing quality — unavailable` beside `IV percentile — not queried / provider absent`. Let the missing check remain visible before opening the manual replay. |
| **DoD / Honesty** | Keep the reported `VLD-TRD-2` result `[2,3(None)]`, `strong_execution → partial_execution`, as a legacy regression target. In a provider-aware policy, dim 3 should be excluded before dispatch; the new trace may therefore differ and must carry a different policy version. Never force an unavailable dimension to preserve the choreography. The diagnostic read is a new episode with its own costs and badges. It cannot be counted as part of the original two-attempt budget, credited to Q, or represented as an automatic starvation cure. |

**The options action change is gated:** high IV percentile alone does not establish a worse trade. Plant an explicitly described historical strategy and evidence transformation consistent with that strategy; require a faithful scorer counterfactual. If admitting IV leaves the action unchanged, show changed support or the remaining uncertainty, or withhold the action-change vignette. Do not assign a favorable or unfavorable options interpretation by hand.

**Optional technical extension:** after the options provider and a legally reachable learned-K checkpoint exist, replace the manual card with a **separate** matched comparison of unit K and learned K under the same scorer geometry, candidates and budget. Show “learned K selected IV first” only if the recorded Q ranking proves it. Greedy learning cannot be presumed to teach a factor that receives no updates. The reported Thompson/UCB coverage improvement came with poorer Trading routing; it is not a ready-made production fix.

**VLD-PUR-1 — “Demand Wasn’t the Limiting Factor”**

**Story:** a real demand increase within the synthetic scene fails to justify a larger order because usable shelf life constrains supply. The differentiator is the **event check followed by the waste check**, with category-specific priorities demonstrated only where supported by replay.

| Field | Value |
|---|---|
| **Surface** | Purchasing **Analysis** → selected P1 Smart Ordering case → `InvestigationTracePanel` beside an order-evidence drawer. This placement is a proposed integration with the existing ordering surface. |
| **API** | `POST /api/purchasing/investigate`. Bind to a historical order and item. Reported fixture alias: `VLD-PUR-DEMAND-SPIKE`. Route target: **dim 5 `event_flag` → dim 4 `waste_risk`**. |
| **Class** | **ARCH**. `waste_tracker` is reported registered; the event evidence adapter, Decision→Order attachment and historical cutoff are not established. |
| **What audience sees** | (0) A protein order starts at `order_more` because the current factor state supports increased demand. (1) The selected event read confirms the scheduled service and expected covers; no cancellation is manufactured to make the ending easy. (2) Re-scoring selects waste risk next. Lot expiry, usable inventory, storage limits and the next feasible delivery show that increasing **this delivery** would strand perishables. (3) The assessment ends at `order_less`, as targeted by the reported seed. The trace identifies which read caused the change. It does not claim the later service demand vanished. (4) The evidence drawer links the relevant prior verified deliveries and waste outcomes to the retained snapshot used after the manager handoff. |
| **Caption** | *The event was real. This delivery would not keep.* |
| **Spoken** | “The first check confirmed the event. The next checked whether the extra stock would still be usable. In this planted case, the order changed from more to less for this delivery. The next manager can inspect the delivery and waste records behind that assessment. The investigation is designed to carry retained knowledge into a new order.” |
| **Silence beat** | **SILENCE 10.** Pause for five seconds when the second row reveals `expiry before service` directly below `event confirmed`. Resume: “More demand did not make this delivery usable.” |
| **DoD / Honesty** | Canonical beat ID `VLD-PUR-1` maps explicitly to the existing seed ID. The event read cannot run until an adapter for dim 5 exists; having F2 Event Intel elsewhere in the product does not prove an investigation provider is registered. Enforce route `[5,4]` and target `order_more → order_less` through the actual scorer, with no hardcoded event→waste branch. Persist source-to-factor transformation and category. No order placement, spoilage savings, manager ramp-time or guaranteed next-decision improvement is claimed. Both standing provenance/accuracy badges remain visible. |

**Category contrast for a technical cut:** pair this protein fixture with a dry-goods fixture whose replay places `cost_deviation` first. Use one real learned checkpoint with category-specific provenance, and log differences in the food data. Label this an illustrative category comparison, not an isolated causal test of K. To isolate K, hold category, geometry and evidence fixed and compare legal K checkpoints separately. Never say “protein always checks waste first”: this main beat explicitly checks the event first.

**VLD-PUR-2 — “The Handoff Kept the Delivery History”**

**Story:** the incoming manager can inspect why an apparently routine supplier order becomes unsuitable and what retained evidence supported the sequence. This is **continuity plus delivery feasibility**, distinct from PUR-1's event/shelf-life conflict.

| Field | Value |
|---|---|
| **Surface** | Purchasing **Analysis** → P1 Smart Ordering case → `InvestigationTracePanel`; evidence drawer links to P5 Supplier Scorecard. Close beside PUR-HERO / The Handoff, without implying that the full continuity feature is already LIVE. |
| **API** | `POST /api/purchasing/investigate`. Reported fixture alias: `VLD-PUR-VENDOR-CASCADE`. Route target: **dim 4 `waste_risk` → dim 3 `supplier_lead_time`**. Alternative-supplier lookup is a proposed content-keyed follow-up through `supplier_scorecard`. |
| **Class** | **ARCH**. Lead-time evidence registration, Decision→Order linkage, supply-chain traversal and as-of history filtering are build requirements. |
| **What audience sees** | (0) A dairy order at the manager handoff starts at `order_as_planned`. (1) Waste evidence establishes how long the current usable stock can cover service; the scorer then selects supplier lead time. (2) A timestamped delivery record and supplier history show that this order cannot arrive within the usable-stock/service window. The final target becomes `skip` **for this order**, not “stop supplying the kitchen.” (3) Only after the assessment, an optional `CONTENT-KEYED / ALTERNATIVE-SUPPLIER LOOKUP` lists approved alternatives and their known delivery windows. This is a separately costed follow-up, not a hidden third VLD read or an automatically placed replacement order. (4) The drawer shows the prior manager's verified delivery records, their dates, the frozen retained snapshot and the incoming manager's access to that evidence. |
| **Caption** | *The manager changed. The delivery record remained inspectable.* |
| **Spoken** | “This planted replay checked usable stock first, then whether this supplier could arrive in time. It ended at skip for this order. The delivery evidence is linked to verified records from before the manager changed. The alternative-supplier list is an ordinary lookup, labeled separately. Everything in this kitchen turns over. This record doesn't.” |
| **Silence beat** | **SILENCE 11.** Pause for five seconds on the second row: `supplier arrival after service cutoff`, with the prior manager's verified delivery record visible beneath it. Resume: “The incoming manager can see what was retained.” |
| **DoD / Honesty** | Map `VLD-PUR-2` to the reported vendor-cascade seed without silently renaming its stored ID. Replay route `[4,3]` and final `order_as_planned → skip`; log actual intermediate actions. Prior delivery outcomes must predate the case and actually contribute to either scorer state or admitted evidence as documented. A visible old note alone is not proof of learned judgment. The alternative supplier must be approved for this item/site and is never invented to guarantee resolution. Keep ARCH, fixture and unmeasured-routing badges visible. |

**Continuity control:** replay the same case and frozen snapshot before/after changing only manager identity and authorized access context. The retained evidence, ranking and assessment should remain invariant when manager identity is not a scorer input. If the actual policy conditions on manager identity, disclose and test that contract instead. This verifies retained state; it does not measure better replacement-manager performance or weeks saved.

**Supplier reliability and price-memory depth cards:** §5 VLD preseeds provide a synthetic on-time history of 17/50 and a matched historical unit-price comparison. These are potential evidence sources, not automatic reasons for the route `[4,3]`. “Reliability before demand” requires a separately replayed `[1,2]` comparison. `price_memory_index` (dim 6) remains an unavailable investigation input until a provider exists; any manual price replay is labeled exactly like the options diagnostic in TRD-2. Do not conflate supplier delivery reliability with trust in a supplier's data feed.

### VLD integration notes

**VLD-SOC-1 ↔ DM-1 (Rejection Moment, §4.1) — same governance story, deeper investigation.**
Spoken bridge, after SILENCE 3: *"Same three parts you just saw. The investigation loop produces the trace. AgentEvolver may propose bounded routing-parameter variants — branch weights, read order — through the same shadow → promote gate, and the gate rejects the ones that don't survive. Conservation gates the action at emit. Deeper investigation, same governance."* **Guard (N3):** AE evolves Ψ *parameters*, never Ψ *structure* (which patterns exist, how they compose); and this AE→routing path is itself **ARCH** — say "may propose," not "evolves."

**VLD-DO-1 ↔ ENT-1 (Sunk-Investment Multiplier, §4.8) — your Celonis data becomes investigation evidence.**
Spoken bridge: *"Your Celonis process graph and your SAP records become investigation evidence — the loop reads them in the order the scorer's experience says matters most, and tells you which decision to change first."* **Guard:** read-only ingestion; "which decision to change," never "we execute it in your ERP" (ENT-1 scope guard, F-21).

**VLD-S2P-1 ↔ S14 (rule-vs-reasoning contrast, §4.2.1) — extend the two-column contrast with an order strip.**
“The S14 case showed a contract-aware assessment. Now this separate dual-mismatch case starts before either mismatch document has been checked. Its retained score selects the receipt first. The history lookup is a labeled prerequisite, and the trace records the selected evidence order.” Preserve S2P-FIX-1's scoped comparison with the displayed threshold baseline. Retire the additive claim that rules cannot read contracts or know which document to request second.

| Bridge | Placement and presenter text | Scope |
|---|---|---|
| **TRD-CLAIM-GATE / TRD-CERTIFICATE → VLD-TRD-1** | After the evidence-gated mirror: “The mirror establishes what this historical record supports. This architecture preview shows which evidence the scorer would request for an individual case.” | Statistical claim admission and evidence selection are different functions; one does not validate the other. |
| **VLD-TRD-1 → TRD-S1 / TRD-V7** | “The portfolio read gives the regime and exposure views a concrete place in the investigation trace.” | Preserve each parent beat's class. No claim that its analytics are already investigation providers. No claim of fast regime reconvergence. |
| **VLD-TRD-2 → TRD-CERTIFICATE / TRD-GATE-DIVIDEND** | “An unsupported check belongs on the record, just as an unsupported finding belongs outside the claim gate.” | No options diagnostic P&L, no blanket conclusion that missing evidence is harmless. |
| **PUR-HERO open → VLD-PUR-1** | After gated I1: “Now take one order. Which evidence should the investigation request before changing it?” | Keep the signal reliability / invoice-variance profile naming; no accusation of supplier misconduct. |
| **VLD-PUR-2 → PUR-HERO / The Handoff** | “Here are the decisions, delivery records and retained snapshot the next manager can inspect.” Then the existing continuity close. | Provenance supports the retention story; a causal performance claim needs a separate baseline. |
| **VLD-PUR-2 → PUR-REFUSAL / PUR-PROOF-LEDGER** | “The investigation can change an assessment. The authority gate determines whether an action may be emitted.” | Keep the gate separate from Q and halt logic. No automatically placed order or VLD savings figures. |

**Shared technical bridge — RGI:** “CI calls this Recursive Graph Improvement, or RGI: a governed, verified-outcome-grounded instance of RSI, bounded at L3, with L5 excluded by design. This preview uses a frozen retained snapshot during the investigation; updates from verified outcomes belong to the between-decision learning path.”

Use the full expansion **Recursive Self-Improvement** only when defining the established field term RSI, never as the name of CI's mechanism. Architectural L3/L5 boundaries are distinct from `REC-R3`/`REC-R5`; their detailed authority model is not supplied here. This definition is the required positioning, not fresh evidence that every proposed loop is implemented or gated. AE may propose routing **parameter** variants through the stated governance path; structure evolution and automatic authority expansion are not implied.

---

## §4.18 Standing Guards and Learning-Loop Class Preconditions (v2.9)

### Standing guards (no body edit — these are authoring constraints for future beats)

**FIX-2 (SOC two-regime + overclaims):** Not present in the demo body. If a future SOC beat is drafted: (a) never put 97.89% beside 78.9% on a customer surface; (b) say "policy evolves continuously from verified outcomes," not "mid-incident"; (c) frame tech-process fusion as land→expand→end-state (ARCH-for-SOC).

**FIX-3 (DataOps "Level 3+ empty"):** Not present in the demo body. If any companion room-script carries it, replace with "does the number move because of your decisions?"

**FIX-8 (Competitor-API / named-performance guard):** No beat calls a competitor's API, runs a competitor's product, or asserts a named-competitor performance number. SOC-GAUNTLET confirmed own-stream only. Any named-competitor claim → counsel sign-off before external use. Any "vendor X is supplier-monetized" line → verify per named competitor before staging.

### K reachability, recurrence and claim-status audit

| Beat | Can the K-dependent claim currently be certified? | Required correction |
|---|---|---|
| SOC-1 | **No.** 0.9/0.3 are described as factor weights, not authenticated K checkpoints; full Q absent. | Compute/log complete Q. A dominant input is not automatically the selected dimension. |
| SOC-2 | **No.** No post-admission vector, legal K or remaining-candidate ranking supplied. | Distinguish admitted negative evidence from None; verify reranking rather than narrating it. |
| DO-1 | **No.** No complete factor/action map, pipeline-conditioned state or Q trace supplied. | Ground adapter selection and retained-state attribution. |
| DO-2 | **Not a K reachability question yet.** The proposed broad/deep controller is absent from the given formula. | Specify that separate policy before claiming the behavior. |
| S2P-1 | **No.** A supplier ratio does not specify K or Q. | Trace history→state→Q→receipt; enforce historical cutoff. |
| TRD-1 / TRD-2 | **No new K story certified.** Reported routes are regression targets; expanded evidence and options contrast are proposed. | Produce legal snapshot/eligibility manifests; distinguish policy selection from manual replay. |
| PUR-1 / PUR-2 | **No new K story certified.** Provider gaps precede the ranking question. | Build missing providers, then replay actual Q and action transitions. |

An unreachable or absent K snapshot blocks the claim, not the entire design document. The record must include update rule, initialization, bounds/clipping, category indexing, verified support and checkpoint hash. Unit K does not by itself mean an untrained scorer: μ/σ can already carry learned information. Likewise, an adaptive loop with frozen K can still recompute Q as v changes; frozen learning state is not a frozen case state.

**Taxonomy replacement for any new terminology note:** `REC-R0 static baseline; REC-R1 within-decision; REC-R2 between-decision K learning; REC-R3 cross-episode; REC-R4 cross-copilot; REC-R5 temporal`. Existing “R3 Ψ”, “R4 shadow-run”, “R5 analyst measurement” and “R1 audit” references become `BUILD-R3`, `BUILD-R4`, `BUILD-R5` and `BUILD-R1` locally to avoid collisions. The prompt does not operationally distinguish R2 from R3; do not assign a shipped cross-episode mechanism from its name. RGI's architectural L5 exclusion is unrelated to a temporal recurrence level labeled R5. Cross-copilot signals are not shared cross-copilot judgment geometry.

### VLD-GUARD — VLD honesty constraints (v2.9)

**VLD-GUARD-1 — Class:** all nine beats ARCH. NEAR requires `BUILD-R3` Ψ prototype, E-1 trajectory persistence, surfaced trace and beat-specific provider/entity/cutoff work. Retain the original LIVE gate: `BUILD-R4` shadow-run must show **Δ_depth > 0 against the declared rule-based routing baseline on real cases**; an offline benchmark does not satisfy it. Extend the matched study to include **static planning on the same learned substrate**, adaptive Q, single-pass and full retrieval where affordable. Predefine the Δ_depth measure, primary task-quality/cost measure, budget and uncertainty assessment. Do not promote an “adaptive is better” claim if the static comparator matches or wins.

**VLD-GUARD-2 — Language:** VLD is investigation, trace, route, re-score, admit and halt. No reasoning/thinking/deliberating language or RL label for its primary mechanism. Use RGI for CI's named mechanism; RSI only as the field reference. Customer microcopy avoids “self” for CI's mechanism.

**VLD-GUARD-3 — Provenance/status:** PLANTED FIXTURE, ROADMAP and ROUTING ACCURACY: not yet measured for this deployment remain visible. Reported offline experiments are explicitly separate from fixture computation and production readiness. Retire stale assertions of universal branch-policy or trace-record nonexistence; state verified status per component.

**VLD-GUARD-4 — Attribution:** category dispatch, entity resolution, supplier/portfolio/lineage walks and evidence-directed expansions are CONTENT-KEYED / PREREQUISITE unless their own Q-selected step is demonstrated. Manual comparisons are NOT POLICY-SELECTED. Count their costs.

**VLD-GUARD-5 — Value/time:** no VLD time-savings figures. Analyst benefit is a pilot question. Editorial video durations and instrumented API latency are clearly distinguished from analyst-time savings.

**VLD-GUARD-6 — Learning:** no “next time it routes better.” Freeze learned state within a beat. Between-decision K learning requires its actual verified-outcome update path; it does not inherently require AgentEvolver to evolve routing parameters. The AE→routing path is a separate ARCH claim. Zero-support pairs and the reported greedy plateau limit the compounding story.

**VLD-GUARD-7 — Budget:** display attempted, admitted and unvisited reads plus halt reason. If all eligible evidence fits, acknowledge that full retrieval can inspect it too. No accuracy or speed advantage inferred from a chosen order alone. No hidden third read, free bundle, or rerun outside the labeled budget.

**VLD-GUARD-8 — Numbers:** all scene values are computed from and linked to labeled planted data. Proposed numbers are acceptance inputs until replayed. Experiment results carry experiment provenance; do not call them fixture outputs. No measured customer ROI, unsupported confidence calibration, or literal fake node count.

**VLD-GUARD-9 — Buyer language:** no centroid/DK/σ/v_t/margin or raw Q equation on buyer panels. Show check order, supporting records, changed assessment, unresolved checks and halt. Internal views retain full quantities. Do not relabel a raw margin as calibrated confidence.

**VLD-GUARD-10 — Competition:** no competitor API/product execution or named performance claim. Describe the internal baseline exactly; avoid universal statements about what other agents, graphs, rule engines or retrieval systems cannot do.

**Implementation truth versus efficacy:** a working endpoint may be recorded as implemented while its benefit remains unvalidated. Retain the document's conservative ARCH/NEAR/LIVE release policy, but track `implementation status` and `comparative evidence status` separately so a failed superiority test is not confused with nonexistent functionality.

### VLD Guard Compliance Checklist

**PASS below means the proposed written beat obeys the guard. It does not certify runtime behavior.** All four remain ARCH; runtime status is **NOT VERIFIED**. Shared guards in §4.18 are part of each beat's specification.

| Beat | Guard | Pass/fail | Note |
|---|---|---|---|
| VLD-TRD-1 | 1 · ARCH | PASS | Entity/correlation/cutoff wiring and replay remain gated. |
| VLD-TRD-1 | 2 · Language | PASS | Historical investigation/assessment vocabulary. |
| VLD-TRD-1 | 3 · Fixture/status | PASS | Standing fixture, roadmap and deployment-accuracy badges. |
| VLD-TRD-1 | 4 · Attribution | PASS | Q selects dimension; portfolio expansion is content-keyed. |
| VLD-TRD-1 | 5 · Time/value | PASS | No analyst-time, profit or risk-reduction claim. |
| VLD-TRD-1 | 6 · Learning | PASS | Frozen snapshot; paired order change is a test target. |
| VLD-TRD-1 | 7 · Budget | PASS | Counts all reads; full-retrieval caveat where applicable. |
| VLD-TRD-1 | 8 · Numbers | PASS | Three positions/correlations are planted; scores must compute. |
| VLD-TRD-1 | 9 · Buyer language | PASS | Plain exposure/check labels; raw Q in internal audit only. |
| VLD-TRD-1 | 10 · Competition | PASS | Internal comparisons only. |
| VLD-TRD-2 | 1 · ARCH | PASS | Missing timing/options providers are explicit. |
| VLD-TRD-2 | 2 · Language | PASS | Coverage gap and manual evidence replay. |
| VLD-TRD-2 | 3 · Fixture/status | PASS | Diagnostic and offline statistic have separate provenance. |
| VLD-TRD-2 | 4 · Attribution | PASS | Manual IV admission is NOT POLICY-SELECTED. |
| VLD-TRD-2 | 5 · Time/value | PASS | No trading outcome or saved-time claim. |
| VLD-TRD-2 | 6 · Learning | PASS | No automatic starvation cure or guaranteed next-case improvement. |
| VLD-TRD-2 | 7 · Budget | PASS | Legacy failed attempt visible; diagnostic is a new episode. |
| VLD-TRD-2 | 8 · Numbers | PASS | 48%=24/50 is reported update coverage, not failed trades. |
| VLD-TRD-2 | 9 · Buyer language | PASS | “Unavailable” and “not queried” stay distinct. |
| VLD-TRD-2 | 10 · Competition | PASS | No external performance comparison. |
| VLD-PUR-1 | 1 · ARCH | PASS | Event provider and historical order linkage are build items. |
| VLD-PUR-1 | 2 · Language | PASS | Evidence/check/order-assessment vocabulary. |
| VLD-PUR-1 | 3 · Fixture/status | PASS | Planted event, shelf life and roadmap clearly marked. |
| VLD-PUR-1 | 4 · Attribution | PASS | Event availability does not hardcode waste as the next check. |
| VLD-PUR-1 | 5 · Time/value | PASS | No spoilage savings or manager ramp-time claim. |
| VLD-PUR-1 | 6 · Learning | PASS | Retained snapshot; category contrast is illustrative. |
| VLD-PUR-1 | 7 · Budget | PASS | Two request attempts; no uncounted replacement order work. |
| VLD-PUR-1 | 8 · Numbers | PASS | Covers and expiry inputs synthetic; final action must replay. |
| VLD-PUR-1 | 9 · Buyer language | PASS | Usable stock, event and delivery labels. |
| VLD-PUR-1 | 10 · Competition | PASS | Acknowledges an ordering rule can inspect the same evidence. |
| VLD-PUR-2 | 1 · ARCH | PASS | Lead-time provider and supply-chain links remain required. |
| VLD-PUR-2 | 2 · Language | PASS | Retention and delivery evidence vocabulary. |
| VLD-PUR-2 | 3 · Fixture/status | PASS | Prior-manager history and proposed diagnostic labeled. |
| VLD-PUR-2 | 4 · Attribution | PASS | Alternative-supplier lookup content-keyed; price card manual. |
| VLD-PUR-2 | 5 · Time/value | PASS | No reduced onboarding time or prevented-loss figure. |
| VLD-PUR-2 | 6 · Learning | PASS | Continuity verifies retained state, not automatic future benefit. |
| VLD-PUR-2 | 7 · Budget | PASS | Supplier lookup outside the two-read trace separately costed. |
| VLD-PUR-2 | 8 · Numbers | PASS | 17/50=0.34 is an explicit synthetic delivery statistic. |
| VLD-PUR-2 | 9 · Buyer language | PASS | Delivery cutoff, assessment and source records. |
| VLD-PUR-2 | 10 · Competition | PASS | No named competitor or exclusivity assertion. |

**Before staging any computed beat, the acceptance record must show:** the actual route and flip step; immutable model-state comparison; complete provider/cutoff provenance; candidate and read-cost accounting; successful missing-evidence and budget-zero controls; actual halt and emit behavior; visible badges; and a script that matches the persisted trace. A manual or storyboard example remains labeled as such. Passing the authoring checklist does not satisfy these runtime gates.

### FIX-7 — Learning-loop precondition: per-copilot class tags

The honest class of any earned-trust beat depends on: **does a verified decision measurably move a later score end-to-end for that copilot?**

| Copilot | Centroid-learning loop | AgentEvolver-promotion loop | Acceleration | Net class for earned-trust beats |
|---|---|---|---|---|
| **SOC** | Verified LIVE (§8 10-cycle test) | Confirm-before-LIVE (Gate 2) | MODELED | LIVE (centroid-grounded) / NEAR (promotion-dependent) |
| **DataOps** | Unconfirmed (DD-0, OD-1) | Unconfirmed | MODELED | **NEAR/ARCH until confirmed** — biggest truth risk |
| **S2P** | Same test needed | Same test needed | MODELED | NEAR until confirmed |
| **Purchasing** | Same test needed | Same test needed | MODELED | NEAR until confirmed |
| **Trading** | Same test needed | Same test needed | MODELED | NEAR until confirmed |

### §5 Preseed Additions (v2.6 — from all 3 copilot reviews)

**Trading preseed (§4.12):**
- Discover/confirm split in trading history (older 70% / held-out recent 30%)
- ≥1 detector that fires but fails FDR on the sample trader (for TRD-CLAIM-GATE + TRD-CERTIFICATE)
- Hypotheses-tested counter ("23 tested / 3 powered / 1 survived") surfaced from the gate

**Purchasing preseed (§4.13):**
- Staffing-change window in purchasing history (de-identified, for PUR-HERO / The Handoff)
- New-supplier pair with different ramp lengths (for PUR-RAMP time-to-competence)
- Gated-I1 empty-state fixture (clean buyer where no factor survives hold-out, for PUR-NOT-YET)
- Quiet Week fixture ($0 incremental, coverage high)
- Manager-drift decisions (for PUR-REFUSAL self-pause)

**DataOps preseed (§4.14):**
- Perturbation fixture (inject anomalies → trust drops → clean revert + provenance log)
- Rejected-rule log (shadow-tested 45% → rejected) for DI-ADMITS-FAILURE
- New-source ramp pair (1st vs 6th, same schema class) for DI-FIRSTVS6TH
- Frozen-model snapshot for DI-TWIN
- Insufficient-evidence source (4 decisions) for DI-ABSTAIN

**S2P preseed (§4.15):**
- Non-flat auto-approve coverage series (S2P-LEDGER trajectory)
- Frozen-twin baseline arm on same seed (S2P-TWIN)
- At least one promoted + transferred exception class in S2P promotion logs (S2P-EXTINCT)
- Day-zero S2P tenant state available via toggle (S2P-DAY0), enrichment-layer only
- Cross-copilot Purchasing→S2P signal (feeds continuity/compounding)
- Frozen-twin divergence labeled MODELED/PILOT-TARGET until measured on real data (F-27)

**SOC preseed (§4.16):**
- Non-flat auto-approve coverage series at fixed safety bar per category (SOC-FRONTIER)
- Frozen-twin baseline arm on same seed (SOC-TWIN)
- At least one promoted + rolled-back change in AgentEvolver logs with evidence + counterfactual (SOC-CONTROL)
- One circuit-broken category (SOC-LADDER)
- Day-zero SOC tenant state via toggle, enrichment-layer only (SOC-DAY0)
- Five Novel Attack Gauntlet beats seeded including regime-break with measurable Recovery Half-Life (SOC-GAUNTLET)
- Stryker no-precedent alert (SOC-NOPRECEDENT)
- 97.89% mechanism number NEVER on customer-facing surface (SOC-FIX-2)
- Frozen-twin divergence labeled MODELED/PILOT-TARGET until measured on real data

**All copilots:** $/trust magnitudes are **illustrative-from-preseed with provenance badges (F-21/F-22)** — never presented as measured outcomes; show the day-zero state when n < K.

## 6. Internal review + llm-judge record (the process applied to this doc)

### 6.1 Internal review (self-check against an executability checklist)
| Check | Result |
|---|---|
| Every demo beat has a surface + API? | ✅ (§2) |
| Every net-new item has owner + DoD + effort? | ✅ (§4) |
| No superseded hero-doc item resurrected (Mirror tab, #120-127, P0/L5)? | ✅ (§0 reconciliation guards this) |
| All 94 scenarios accounted for, deferrals flagged? | ✅ (§3; 92 ready, 2 deferred) |
| Competitive alignment (each pillar tied to a competitor it beats)? | ✅ (§1 table) |
| Honesty guardrails (no overclaim; self-extending context marked vision-level; day-zero no fake number)? | ✅ (§1, §4.3, §5) |
| Preseed risk (flat IKS) surfaced as a hard requirement? | ✅ (§5) |

**Findings fixed during review:** (a) removed the "Mirror tab" build (it doesn't exist; mirror lives in
Analysis) and re-pointed the cold-mirror beat to Analysis; (b) reconciled the hero-doc Refusal (C5) and the
strategy Rejection Moment as *distinct* beats (conservation declines an *expansion* vs AE rejects a
*variant*) rather than duplicating; (c) tagged the two deferred scenarios so no cut depends on them.

### 6.2 LLM-judge rubric (score this doc 1-5; ready for your llm-judge as a second pass)
| Criterion | Target | Self-score | Note |
|---|---|---|---|
| Executability (a coding session can act without asking) | 5 | 4 | §4 items are actionable; DM-1/CF-1 still need the discovery grep run to confirm log fields exist |
| Scenario coverage (all 94, correctly mapped) | 5 | 5 | full catalog, deferrals flagged |
| Narrative coherence (spine → pillars → beats) | 5 | 5 | unified frame; mirror-open preserved |
| Competitive alignment (each pillar beats a named reference) | 5 | 5 | P1/P2/P3 mapped |
| Honesty (no overclaim; verifiable) | 5 | 5 | vision-level items flagged; day-zero honest |
| Current-state accuracy (no stale gating) | 5 | 4 | `[VERIFY]` SOC α numbers is the one open confirm |

**Two items for the llm-judge / coding sessions to close before build:** (1) run the DM-1 discovery grep to
confirm AE rejection reasons are logged (if not, DM-1 grows from surfacing to light backend); (2) `[VERIFY]`
SOC conservation numbers so no stale α figure is quoted.

---

## 7. Loom demo program — the code setup coding sessions start now

The line between demo and outreach is thin, but it has a clean seam: **the Loom *harness* is demo code
(coding sessions, now); the recorded Loom *videos* and their distribution are outreach (later).** Build the
harness now so recording is a same-day activity, not a re-engineering effort. This is the current-state
successor to the hero-doc's `#88 LOOM-V1`.

**Why Loom needs its own code (not just "hit record on the live demo"):** a Loom must be *deterministic*
(same numbers every take), *self-annotating* (captions on screen, since there's no live presenter pointing),
*resilient* (a live connector that's down mid-record must not break the take), and *resettable* (re-record
one beat without redoing the whole flow). None of that is true of the live demo today.

**The design that makes the doc executable:** the §2 beats + §2.4 captions are a **beats config** the harness
consumes — the storyboard is the data, the harness is the player. One JSON per cut:
```
demo/loom/cuts/{vc,trader,enterprise}.json
  [ { id:"V1", copilot:"trading", tab:"analysis", surface_selector:"...",
      caption:"The factor you trust most is your noisiest.", spoken:"…",
      duration_s:90, spotlight:"#trust-radar", api_warmup:["/api/fingerprint"] }, … ]
```

### 7.1 Loom harness build items

| ID | Item | Surface / where | DoD | Owner | Effort |
|---|---|---|---|---|---|
| **LOOM-1** | **Record-mode deterministic state** — a pinned seed (fixed IKS, fixed rejection counts, fixed cross-copilot signal) + **connector freeze** (FRED/OpenMeteo/mock all serve cached values, labeled) so every take is identical. **≡ strategy W1-1 = build C-1 (one deterministic-preseed artifact; do not build twice).** | `demo.py --record-mode` + a pinned seed file | two runs produce byte-identical demo numbers; no live-connector variance; provenance labels intact | A + C | 2d |
| **LOOM-2** | **Guided-tour overlay** — a spotlight + caption component driven by the beats config; advances on click or timer; renders `caption` on screen | shared overlay in `copilot_sdk/frontend` (1× SDK) + 1× SOC | overlay reads a cut JSON and walks the beats with spotlight + caption on both frontend worlds | A + C | 3d |
| **LOOM-3** | **Auto-advance runner (hands-free)** — optional timer-driven playback for a fully self-running Loom (no presenter), using `duration_s` | overlay flag `?loom=auto` | a cut plays start-to-finish unattended, hitting each beat's duration | A | 1d |
| **LOOM-4** | **One-command reset/replay** — restore the exact record-mode state to re-shoot a single beat or the whole cut | `demo.py --record-reset [--beat V4]` | resets to the pinned state in <30s; single-beat reset lands on that beat's surface | A + C | 1d |
| **LOOM-5** | **Beats config authoring** — encode the three cuts (§2) + captions (§2.4) as the three cut JSONs | `demo/loom/cuts/*.json` | the three cuts load in LOOM-2 and match this doc's beats/captions exactly | Content + A | 1d |

**Total Loom harness ≈ 8 days**, parallelizable across A/C, and it is **demo infrastructure that outlasts any
one Loom** — every future recording reuses it. Sequence it *after* Wave-1 demo-base hardening (LOOM-1 extends
the same preseed work) and *alongside* the §4 hero-moment builds (the hero moments are beats the harness will
record).

### 7.2 The Loom cut list (what gets recorded — outreach executes later)

| Loom | Cut | Audience | Length | Notes |
|---|---|---|---|---|
| L-VC | §2.1 VC cut | investors | ~7 min | the platform story; leads with governed self-improvement |
| L-TRADER | §2.2 trader | self-serve devs/traders | ~3 min | pairs with the Trading open-source launch (strategy W3) |
| L-SOC | §2.3 enterprise (SOC lead) | CISO | ~12 min → trim to ~5 for cold outreach | investor surface |
| L-S2P | §2.3 re-led on S2P | CFO/procurement | ~5 min | S14 hero + cross-copilot signal |
| L-PUR | §2.3 re-led on Purchasing | ops/GM | ~5 min | "your covers" once Toast lands |
| L-DATAOPS | §2.3 re-led on DataOps | CTO/data | ~5 min | Intelligence Map + Acquisition Advisor |
| L-DATAOPS-DI | §4.9 DataOps Data Intelligence | CTO/CDO/data teams | ~5 min | DI-TRUST → DI-SOURCE → DI-PRODUCT → DI-GOLD → DI-TIMELINE. Level 5-6 preview. |
| L-CDK | SDK / open-source developer cut | Self-serve developers | ~5 min | APP-2 hello-gae → APP-5 YAML → APP-6 build-your-own (email + reading skins, governed-vs-ungoverned toggle). **Gate:** public SDK drop. |

| Loom | Insertion | Note |
|---|---|---|
| L-SOC | after E2 (Why?) → **VLD-SOC-1** (SILENCE 7) → **VLD-SOC-2** → continue to E3 | ~2.5 min added; both beats captioned **ROADMAP** in the overlay (`class: "ARCH"` in the cut JSON so LOOM-2 renders the badge) |
| L-DATAOPS | after E5 fusion climax → **VLD-DO-1** (hands off into ApplyFixModal) → **VLD-DO-2** beside DI-TIMELINE | ~2 min added; DD-0 precondition banner stays visible |
| L-S2P | after S14 / SILENCE 2 → **VLD-S2P-1** as the S14-CONTRAST order-strip extension | ~1 min added; S2P-FIX-1 wording preserved |
| **L-VLD** (new, optional) | Room-16 standalone: VLD-SOC-1 → VLD-SOC-2 → VLD-S2P-1 → close on the three tear-down lines | ~4 min; **explicitly a roadmap Loom** — title card reads "Investigation loop — architecture preview"; not for cold outreach until NEAR |
| **L-TRADING / L-TRADER** | Existing TR1 import → TR2 mirror, with TRD-CLAIM-GATE/TRD-CERTIFICATE where staged → **ROADMAP title card → VLD-TRD-1 / SILENCE 8 → optional VLD-TRD-2 / SILENCE 9** → existing TR3 edge drift and governed promotion/rejection close. | Core TRD-1 insertion: **75 seconds** planned video duration. TRD-2 deep cut: **90 seconds**. Full existing ~3-minute cut becomes ~5:45 if both are appended without trimming. These are editorial durations, never time saved by the product. |
| **L-PURCHASING / L-PUR** | PUR-HERO's gated I1 mirror → **ROADMAP title card → VLD-PUR-1 / SILENCE 10** → applicable ledger/refusal beat at its own class → **VLD-PUR-2 / SILENCE 11** → PUR-HERO / The Handoff close. | PUR-1 **75 seconds**, PUR-2 **90 seconds** planned. Full existing ~5-minute cut becomes ~7:45 without trimming. For a five-minute cut, retain one 75–90-second VLD insertion and deliberately trim the feature tour; do not pretend all additions fit unchanged. |

The short Trading cut favors TRD-1; the technical version includes the coverage failure. The short Purchasing cut favors PUR-2 because it earns the continuity close. Each beat has a silence moment, but a compressed cut may use one principal silence and move the other beat to an appendix. All simulated-user-data transitions explicitly return to planted data; importing the viewer's CSV does not make the VLD fixture their data.

Every VLD entry carries `class: "ARCH"`, `badges: ["PLANTED_FIXTURE", "RHO_UNMEASURED"]`, a visible ROADMAP title, fixture/version reference, caption and silence cue. Preserve actual canonical cut IDs. Required new metadata must be implemented in the harness before it is assumed supported. Use an already persisted, deterministic trace for playback. If a POST investigation preflight is needed, invoke it explicitly with its actual method, body, fixture and isolated record-mode context; `/investigate` must not be placed in a path-only GET warm-up list. A retry must not update learning state, double-count metrics or execute actions. No prerecorded trace is presented as a fresh live endpoint result.

**Existing-cut corrections:** L-SOC retains its placement after E2 but uses the corrected SOC sequence in §4.17. L-DATAOPS retains its insertion locations and DD-0 banner; DO-2 is labeled a coverage/abstention preview until its policy exists. L-S2P retains the S14 insertion but uses a distinct receipt-first case and its corrected bridge. Optional L-VLD closes on the revised Room-16 answers; adding all four new beats requires a newly budgeted version, not the old four-minute label. ARCH-only cuts remain explicit architecture previews under the existing outreach rule.

**Dependency note:** L-TRADER should follow the Trading OSS launch; L-PUR's "your data" beat wants Toast
(strategy W3-2); the rest can record as soon as the harness (7.1) + §4 hero moments are in.

---

## Frontend Build Items for Demo-Readiness

| ID | What | Surface | Effort | Status |
|---|---|---|---|---|
| DI-GOLD-FE | Gold dotted lines on IntelligenceMapPanel | Insight screen | 1w | NOT BUILT — DI-5 endpoints return gold_lines data but the frontend doesn't render them yet |
| DI-PRODUCT-FE | Data Products panel on Dashboard or Insight | Dashboard/Insight | 0.5d | PARTIALLY — endpoint exists, needs dedicated card |
| SC-14-FE | Decision Explorer on Insight | Insight | Pending Codex | Prompt sent (SC-14+15+16) |
| SC-15-FE | Rule Lifecycle timeline on Evidence | Evidence | Pending Codex | Prompt sent |
| SC-16-FE | Audit Trail on Evidence | Evidence | Pending Codex | Prompt sent |
| D-CEL-FE | Enterprise Health card + SAP/Celonis badges | Dashboard | Pending Codex | Prompt sent |

---

## Document Control

| Version | Date | Change |
|---|---|---|
| v2.2 | August 2, 2026 | **DataOps Data Intelligence beats.** Added §4.9 with 6 new demo beats (DI-TRUST, DI-SOURCE, DI-PRODUCT, DI-GOLD, DI-TIMELINE, DI-ADMITS-FAILURE) covering all shipped DI features. Two new competitive rooms (#12 data quality, #13 data-as-product) with kill-shot lines and tear-down answers. Two new silence beats (#4 trust gap, #5 gold lines). Enterprise cut E5b insertion. L-DATAOPS-DI Loom cut. Frontend build items for demo-readiness. All beats tagged with class (LIVE/NEAR) and API references. |
| v2.3 | August 4, 2026 | **DI-PROOF linchpin beat + mirror→moat arc.** Added §4.9.0 DataOps cut arc (6-beat sequence). Added DI-PROOF ("Earned, Not Asserted") — live perturbation of trust score, ~2-3d build, NEAR class. Silence beat #6. Resequenced 8 beats from feature tour → story spine. Strengthening themes from dataops_data_intelligence_strengthening_v1.md. |
| v2.4 | August 8, 2026 | **Reference + differentiation beats.** Added §4.10: DIFF-1 governed-vs-ungoverned rebuttal (⭐ rooms 2+3), COMP-1 compounding curve (⭐ VC lead beat), L-CDK developer cut (3 beats). Added §4.11: B1-B4 beat corrections from VC judge panel (rejection inversion, RL naming, SOC exploration proposal-only, CC-1 two distances). |
| v2.5 | August 10, 2026 | **Fixer: propagate §4.10/§4.11 into primary sections.** (A) B2 RL naming applied — retired the "no-RF" claim from §0.2/§0.3/§5, replaced with centroid-distance reconciliation. (B) B1 rejection inversion applied — V2/E3 lead with promotion. (C) COMP-1 propagated into VC cut §2.1+§2.4 with CC-1 guard. (D) DIFF-1 propagated into §0.1 rooms 2/3. (E) L-CDK added to §7.2 Loom cuts. (F) SOC exploration proposal-only + DIFF-1/L-CDK datasets added to §5 preseed. (G) Doc control tables merged; §4.11 marked applied. |
| v2.6 | August 15, 2026 | **Five-copilot review additions.** Merged 5 addenda from consolidated 3-LLM reviews: §4.12 Trading (TRD-CLAIM-GATE, TRD-CERTIFICATE, TRD-GATE-DIVIDEND, TradeZella competitive, B1-B8 naming, observation-only guard), §4.13 Purchasing (PUR-HERO, PUR-GATE, PUR-PROOF-LEDGER, PUR-NOT-YET, PUR-REFUSAL, PUR-RAMP, data-maturity tags), §4.14 DataOps (DD-0 precondition, DI-ABSTAIN, DI-GATEWAY, DI-FIRSTVS6TH, DI-TWIN, DI-PROOF strengthen, DI-GOLD de-risk, buyer-language guard), §4.15 S2P (S2P-LEDGER, S2P-EXTINCT, S2P-TWIN, S2P-WHATIF, S2P-DAY0, S2P-CONFIDENCE, cross-system neutrality), §4.16 SOC (SOC-CONTROL, SOC-LADDER, SOC-TWIN, SOC-NOPRECEDENT, SOC-WHATIF, SOC-DAY0, SOC-FRONTIER, SOC-GAUNTLET, platform-absorption kill-shot). Corrections: S2P-FIX-1 (SILENCE 2 overclaim), SOC-FIX-1 (cold-start counter), SOC-FIX-2 (two-regime guard). 2 new rooms (#14 agent-trust, #15 purchasing). 6 new tear-downs. 5 preseed sections. DataOps arc re-sequenced to 7-beat machinery-first. V1 gated with correction survival. |
| v2.7 | August 15, 2026 | **Fixer: propagate §4.12-§4.16 into body + class-honesty corrections.** FIX-1: SOC room-8 tear-down opener retuned (cold-start counter). FIX-4: Purchasing I1 renamed (signal reliability / invoice-variance profile). FIX-5: Trading T4/T14 fold notes added. FIX-6: All frozen-twin beats re-tagged NEAR-HEAVY (~2-3 wks, RL-PERSIST). FIX-7: Per-copilot RL-loop class precondition table (§4.17). FIX-2/3/8: Standing guards (no body edit needed). |
| v2.1 | July 11, 2026 | **Presenter technique + competitive Q&A + S14 contrast.** (1) **§2.5 silence beats** — the three moments where the presenter STOPS TALKING (Mirror at V1 second 45-75, SituationPanel at E2 second 30-60, Rejection Table at V2 second 60-90); includes physical staging instructions and recovery lines. The meta-principle: 20 seconds of deliberate silence in a 420-second demo is where the decision happens. (2) **§0.3 competitive tear-down lines** — per-room "when they say X, you say Y" one-liners for 11 competitive rooms, plus a meta-pattern for unexpected competitors ("They solve [X]. We solve the layer underneath: how does the system that solves [X] get better over time, safely?"). (3) **§4.2.1 S14 rule-vs-reasoning contrast** — a two-column side-by-side showing what a threshold rule would have done (REJECT, $340K false rejections) vs what the SituationPanel produced (ACCEPT, confidence 0.91, contract cited). The contrast is COMPUTED, not hardcoded (same invoice, real threshold). ~0.5d frontend build. Appears at Enterprise E2 after SILENCE 2. |
| v2.2 | August 2, 2026 | **DataOps Data Intelligence beats.** Added §4.9 with 8 demo beats (DI-TRUST, DI-SOURCE, DI-PRODUCT, DI-GOLD, DI-TIMELINE, DI-ADMITS-FAILURE, DI-DIRTY-DATA, DI-AGENT-TRUST). Two new competitive rooms (#12 data quality, #13 data-as-product). Two new silence beats (#4, #5). Enterprise cut E5b. L-DATAOPS-DI Loom cut. Frontend build items. F-21/F-22 honesty guard. |
| v1.0 | July 10, 2026 | Initial consolidation. Fused the June-1 hero-doc narrative frame (mirror-not-moat, autonomy-vs-automation, four innovations) with the July-9 feature-complete state and the strategy's three differentiators/hero moments. §0 reconciles superseded hero-doc items (Mirror tab, #120-127, P0/L5/D2 gating). §1 unified frame; §2 three demo cuts (VC 7m / trader 3m / enterprise 12m) as beats with surface+API+timing; §3 full 94-scenario catalog (92 ready, 2 deferred) with cut+pillar mapping; §4 net-new hero-moment build items (Rejection/Counterfactual/Day-Zero + staged trust beats + BYOD) with owner/DoD/effort; §5 demo-base preseed requirements (flat-IKS = top risk); §6 internal-review + llm-judge record. |
| v1.1 | July 10, 2026 | **Scripts + Loom program.** §2.4 added — per-beat presenter microcopy (caption + spoken) for all three cuts, so the doc owns scripts end-to-end; captions double as the Loom overlay data. §7 added — the Loom demo program: the seam (harness = demo code now; recorded videos = outreach later), the beats-config design (the storyboard is the data), five harness build items (LOOM-1 record-mode deterministic state + connector freeze, LOOM-2 guided-tour spotlight+caption overlay, LOOM-3 hands-free auto-advance, LOOM-4 one-command reset/replay, LOOM-5 beats-config authoring; ~8d total), and the six-Loom cut list (VC/trader/SOC/S2P/PUR/DataOps) with dependency notes (L-TRADER after OSS launch, L-PUR after Toast). |
| v1.2 | July 10, 2026 | **Cross-doc reconciliation.** Aligned with `next_steps_strategy_v1_1.md`: the single coding build list is that doc's §9 Execution Synopsis (C-1..C-14); this doc is the spec it references. Made two shared items explicit to prevent double-building: **LOOM-1 ≡ strategy W1-1 = C-1** (one deterministic-preseed artifact), and **§4 DM-1/CF-1/DZ-1/ST-5 ≡ strategy HERO-1/2/3/4** (C-2/C-3/C-4). Title/companion refs updated. No scenario or beat changes. |
| v1.3 | July 10, 2026 | **Reconciled with the outreach catalog.** Added §3.1 aligning this doc with `outreach_use_scenario_catalog.md` (v1.0, May 21): established the two-lens relationship (catalog = scenario universe + outreach messaging + 23 heroes + one-liners + industry-data; this doc = demo-ready/surface-mapped), reconciled the counts (catalog 91 vs this 94 — differ by counting granularity + date, e.g. SOC 10 narrative units vs 20 per-tab scenarios; Trading 20 and S2P 16 match exactly; neither authoritative over the other), and mapped the demo beats to the outreach heroes with the proven one-liners + industry-data hooks for the presenter scripts (TRD-1 mirror, SOC-4 admits-failure, DO-4 $604K fusion, DO-2/PUR-3 departure, SOC-1 amnesia). No scenarios re-typed — the catalog stays the source for the full 91 + messaging; this doc guarantees demoability. Companion refs updated. |
| v1.4 | July 10, 2026 | **Positioning reconciliation with next_steps v1.8.** §1 pillars updated to the deployability framing — **Governed / Grounded / Compounding** (compounding demoted to support) — and the spine reframed to "Compounding Intelligence = the governed compounding layer" (above loop/context/harness engineering); situation-analysis (S14→P2) and context-graph synthesis flagged `[VERIFY shipped vs roadmap]` per next_steps C-VERIFY-L3L4. V7 close rewritten to the governance-bottleneck / governed-compounding-layer message ("loop engineering makes an agent finish a task; we make the whole system get better at every task, safely; the market spent 18 months proving 88% of pilots die on governance"). No scenario/beat/build changes. |
| v2.0 | July 10, 2026 | **Brought current with next_steps v1.21 + product_integrity v3.0.** (1) **§0.1 room→kill-shot map** — beats re-indexed by **competitive room** (not only by copilot), one weapon + one line per room; 10 of 15 rooms have a LIVE kill shot. (2) **Scenario classes LIVE / NEAR / ARCH** now travel with every beat (product_integrity §2.8): showing roadmap is allowed and expected; implying roadmap is LIVE is the only violation (F-27). (3) **§0.2 demo-truth constraints** — the three things the code says that the storyboard must respect: **SOC learning is DISABLED by default** (`soc/config.py:66`) so any SOC "watch it learn" beat won't fire unless enabled (C-1 DoD: prove a verified decision changes a later SOC score, or re-cut the beat); **naming (F-25)** — the primary mechanism is decision-trace/prototype learning from verified decisions, **not "RL"** (and the honest line is stronger: the "no-RF" claim (C-18); exploration is conservation-bounded by construction, C-19); **C-17 is scoped (F-24)** — prompt-variant promotion is ungated, so say "governs our scoring, exploration and scorer-evolution loops," never "all loops," until C-GOV lands; and no shared cross-copilot judgment claim (F-26). (4) **New §4.6** — Trading situation-conditioned + volatility beats (TRD-S1..S4, TRD-V1/V2/V5/V6/V7), leading with **TRD-S3 autonomy throttle**, **TRD-V1 short-vol illusion** and **TRD-V2 VRP edge-or-insurance**; all magnitudes flagged as illustrative formats, not measured results. (5) **New §4.7 — TRD-S7 "The Re-convergence Moment"** (⭐ the strongest technical beat available): replay a real 2020/2022 regime break, cold-start vs regime-indexed re-convergence = **γ>1 made visible against non-stationarity**, the failure that kills every RL trading system; class **ARCH** until C-REGIME P4 + EXP-REGIME. (6) **New §4.8 — ENT-1 "The Sunk-Investment Multiplier"** (the Celonis/enterprise wedge's missing beat: "your Celonis spend just became more valuable, not obsolete"), with a scope guard — surface *which decision to change*, not *we execute it in your ERP* (write-back is roadmap). (7) **§5 preseed** gains SOC-learning-enabled, Trading situational tags, and a real regime-break window; hard constraints gain the F-24/F-25/F-26 wording rules. (8) `SOC-V4` catalog entry renamed off "RL Safety Controls." |
| v2.8 | August 15, 2026 | VLD investigation beats (VLD-SOC-1/2, VLD-DO-1/2, VLD-S2P-1). Room 16 (Adaptive Investigation). All ARCH class. |
| v2.9 | September 13, 2026 | Added VLD-TRD-1/2 and VLD-PUR-1/2; reconciled canonical factor/provider maps and seed aliases; added temporal/entity wiring, Loom and Room-16 deltas; corrected all existing VLD scripts for Q selection, missing evidence, budget accounting, reported static/RNN results, starvation, RGI terminology and deployment-truth guards. |
