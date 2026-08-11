# Demo Scenarios Demo Scenarios & Use Cases — Consolidated · v2.1 Use Cases — Consolidated · v2.2

**Date:** August 10, 2026 · **Version:** 2.5
**Purpose:** the single source of truth for the demo storyboard + use-case scenarios, **executable for
coding sessions** (every beat carries a surface, API, data need, DoD, and session owner).

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
   only by copilot. *10 of 13 rooms have a LIVE kill shot.*
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
| 8. SecOps copilots | "Microsoft Security Copilot already does this." | "Microsoft's copilot doesn't learn from your analysts' corrections. Ours does — and it remembers which analyst is best at which category. When your best analyst leaves, Microsoft's copilot doesn't notice. Ours retains their judgment — in dollars." |
| 9. Context / memory | "Rowboat does memory for agents." | "They compound notes. We compound judgment — and prove it moved the decision. Change a factor, watch the score move. That's not memory — that's institutional knowledge with a math proof." |
| 10. Agent infra (CopilotKit) | "CopilotKit has great agent tooling." | "They're the UI layer. We're the substrate — the thing underneath that makes agents get better, safely, across domains. We run five copilots on one engine. They'd need five separate implementations." |
| 11. AI governance | "We need compliance — is this audit-ready?" | "Every decision, hash-chained, tamper-evident. We don't fake your day-one number — we show you the instrument working and the proof it's calibrated. And we're sixteen months ahead of the EU high-risk deadline." |

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
| V1 | *The factor you trust most is your noisiest.* | "Before I show you anything — pick the factor you trust most. … 2,000 verified decisions say that's your *noisiest* predictor, highest σ on the board. You've been trusting the thing that lies to you most, and nothing but the decisions could have told you. That's the mirror." |
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

**The three silence beats:**

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
"where does it get the commodity data?" THEN say: "Every competitor auto-approves by rule. We reason
from context. That's the difference between automation and intelligence." The pause made the line land.

**SILENCE 3: The Rejection Table (V2 / E3, second 60-90)**

After you say "…and it rejected 35 others," the rejection table renders:
"18 correctness floor. 11 conservation. 6 variance."

STOP. Let them read the three numbers. The insight they need to arrive at is: "the rejections are
more important than the approvals." If you say that for them, it's a claim. If they think it, it's
a conviction.

*What to do:* Wait 5 seconds. Then, quietly: "The rejections are the point. Self-improvement without
a gate is a liability. We ship the gate." Lower your voice for this line — it's the close, not the
pitch.

**The meta-principle:** in a 7-minute demo, you have ~420 seconds. Spending 20 of them in deliberate
silence (5%) will feel uncomfortable. Do it anyway. The silence is where the decision happens.

---

## 3. Master scenario catalog (all 94 — the use-case reference)

Status ✅ demo-ready · ⚠️ deferred. "Cut" = which demo cut features it (V/TR/E) or — (catalog-only depth).
Full per-scenario BEFORE/AFTER narrative lives in `narrative_readiness_v3.md` Part II.

### Trading (20; 19 ready) — clusters A Signal/Pattern, B Scaling, C Self-Knowledge, D Self-Governance, E Data, F Disruption, G Volatility
`T1` Signal Trust Radar **[HERO, mirror]** ✅ Analysis (V1,TR2) · `T2` Post-Win Overtrading ✅ · `T3` Friday
Degradation ✅ · `T4` Regime Analysis ✅ · `T5` Scale This Strategy? ✅ Perf · `T6` Execution Gap ✅ ·
`T7` Revenge Trade Real-Time ✅ Log · `T8` Per-Trader Edge ✅ Dash (TR3) · `T9` Strategy Stopped Working ✅ ·
`T10` Prove It Before Real Money ✅ (P1) · `T11` History Unified ✅ · `T12` Playbook Transferred ✅ (P3) ·
`T13` Tariff Shock ✅ · `T14` Regime Shift ✅ · `T15` Revenge at VIX 32 ✅ · `T16` Edge Rotation ✅ ·
`T17` Premium IV/RV ⚠️ **deferred v1.1** (VIX proxy today) · `T18` Correlation Breakdown ✅ · `T19` Earnings
Split ✅ · `T20` VIX Mean-Reversion ✅

### Purchasing (22; 21 ready) — A Operational, B Intelligence, C Pattern, D Memory, E Scale
`I1` Supplier Trust Trap **[HERO, mirror]** ✅ Analysis · `M1` Food Cost Dash ✅ · `M2` Delivery Match ✅ ·
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
> *"The rule processed this invoice in 0.02 seconds. The reasoning took 0.3 seconds. The rule was wrong.
> That's $340K in false rejections this quarter — because rules don't read contracts."*

**Implementation:**
- The left column is COMPUTED, not hardcoded: apply a simple threshold rule (variance > 5% → reject)
  to the same invoice the SituationPanel is scoring.
- The right column is the existing SituationPanel output.
- The $ impact comes from: count of similar invoices × average value × delay cost.
- The data is from the preseed — not fabricated. Provenance badge shows tier.

**Where it appears in the demo:** Enterprise cut, beat E2 (the SILENCE 2 moment from §2.5). After the
silence, the presenter says: *"The rule on the left rejected this invoice. The reasoning on the right
accepted it. The rule was wrong — and it would have been wrong on 47 similar invoices this quarter.
That's $340K in false rejections. Rules don't read contracts."*

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


### §4.9.0 DataOps Cut Arc (v2.3 — mirror→moat sequence)

**Story spine:** Open with an expensive truth → prove it's real → show compounding → show governance → show strategy → extend to platform.

| # | Beat | Role in arc | Time |
|---|---|---|---|
| 1 | DI-TRUST (reframed as "Data Trust Trap") | **Mirror** — your most trusted source is your noisiest | 60s |
| 2 | **DI-PROOF** (NEW) | **Prove** — perturbation drops trust live | 90s |
| 3 | DI-TIMELINE | **Compound** — categories converging, IKS rising | 60s |
| 4 | DI-ADMITS-FAILURE | **Govern** — AgentEvolver rejects bad rules (moat) | 60s |
| 5 | DI-GOLD | **Strategize** — what data to buy (now believable) | 90s |
| 6 | DI-AGENT-TRUST | **Extend** — trust layer every agent needs | 60s |

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
Retire the claim that judgment lacks a reward function. Replace with: "The DECISION is centroid-distance, not reward-maximizing. Reward functions exist in the LEARNING path (exploration + credit), never in choosing the action. Exploration is conservation-bounded (`ConservationBoundedThompson`)."

**B3 — SOC Exploration Proposal-Only:** ⚠️ on-stage-truth
When SOC learning is ON, exploration can override centroid action. In demo profile: run exploration proposal-only (SOC-G1 target) so "decision is centroid" holds on stage. Or re-cut "watch it learn" to S2P via DIFF-1.

**B4 — CC-1 Two Distances:**
Canonical-distance INCREASES (production, = IKS rising). Ground-truth-distance DECREASES (oracle-only). DI-TIMELINE is consistent. Never reframe production curve as "distance to correct answers shrinking."
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
**Naming (F-25):** no beat, caption, or script says "RL" for the primary mechanism, and no beat/script claims judgment lacks a reward function — the reward runs in the learning path; the **decision** is centroid-distance (see §4.11 B2) — it is *decision-trace /
prototype learning from verified decisions*. **Claim scope (F-24):** "conservation governs our scoring,
exploration and scorer-evolution loops" — **not** "all loops" — until `C-GOV` lands. **Cross-copilot (F-26):**
*signals* transfer; judgment geometry is per-copilot.

---

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
| v2.5 | August 10, 2026 | **Fixer: propagate §4.10/§4.11 into primary sections.** (A) B2 RL naming applied — retired the outdated claim that judgment lacks a reward function from §0.2/§0.3/§5, replaced with centroid-distance reconciliation. (B) B1 rejection inversion applied — V2/E3 lead with promotion. (C) COMP-1 propagated into VC cut §2.1+§2.4 with CC-1 guard. (D) DIFF-1 propagated into §0.1 rooms 2/3. (E) L-CDK added to §7.2 Loom cuts. (F) SOC exploration proposal-only + DIFF-1/L-CDK datasets added to §5 preseed. (G) Doc control tables merged; §4.11 marked applied. |
| v2.1 | July 11, 2026 | **Presenter technique + competitive Q&A + S14 contrast.** (1) **§2.5 silence beats** — the three moments where the presenter STOPS TALKING (Mirror at V1 second 45-75, SituationPanel at E2 second 30-60, Rejection Table at V2 second 60-90); includes physical staging instructions and recovery lines. The meta-principle: 20 seconds of deliberate silence in a 420-second demo is where the decision happens. (2) **§0.3 competitive tear-down lines** — per-room "when they say X, you say Y" one-liners for 11 competitive rooms, plus a meta-pattern for unexpected competitors ("They solve [X]. We solve the layer underneath: how does the system that solves [X] get better over time, safely?"). (3) **§4.2.1 S14 rule-vs-reasoning contrast** — a two-column side-by-side showing what a threshold rule would have done (REJECT, $340K false rejections) vs what the SituationPanel produced (ACCEPT, confidence 0.91, contract cited). The contrast is COMPUTED, not hardcoded (same invoice, real threshold). ~0.5d frontend build. Appears at Enterprise E2 after SILENCE 2. |
| v2.2 | August 2, 2026 | **DataOps Data Intelligence beats.** Added §4.9 with 8 demo beats (DI-TRUST, DI-SOURCE, DI-PRODUCT, DI-GOLD, DI-TIMELINE, DI-ADMITS-FAILURE, DI-DIRTY-DATA, DI-AGENT-TRUST). Two new competitive rooms (#12 data quality, #13 data-as-product). Two new silence beats (#4, #5). Enterprise cut E5b. L-DATAOPS-DI Loom cut. Frontend build items. F-21/F-22 honesty guard. |
| v1.0 | July 10, 2026 | Initial consolidation. Fused the June-1 hero-doc narrative frame (mirror-not-moat, autonomy-vs-automation, four innovations) with the July-9 feature-complete state and the strategy's three differentiators/hero moments. §0 reconciles superseded hero-doc items (Mirror tab, #120-127, P0/L5/D2 gating). §1 unified frame; §2 three demo cuts (VC 7m / trader 3m / enterprise 12m) as beats with surface+API+timing; §3 full 94-scenario catalog (92 ready, 2 deferred) with cut+pillar mapping; §4 net-new hero-moment build items (Rejection/Counterfactual/Day-Zero + staged trust beats + BYOD) with owner/DoD/effort; §5 demo-base preseed requirements (flat-IKS = top risk); §6 internal-review + llm-judge record. |
| v1.1 | July 10, 2026 | **Scripts + Loom program.** §2.4 added — per-beat presenter microcopy (caption + spoken) for all three cuts, so the doc owns scripts end-to-end; captions double as the Loom overlay data. §7 added — the Loom demo program: the seam (harness = demo code now; recorded videos = outreach later), the beats-config design (the storyboard is the data), five harness build items (LOOM-1 record-mode deterministic state + connector freeze, LOOM-2 guided-tour spotlight+caption overlay, LOOM-3 hands-free auto-advance, LOOM-4 one-command reset/replay, LOOM-5 beats-config authoring; ~8d total), and the six-Loom cut list (VC/trader/SOC/S2P/PUR/DataOps) with dependency notes (L-TRADER after OSS launch, L-PUR after Toast). |
| v1.2 | July 10, 2026 | **Cross-doc reconciliation.** Aligned with `next_steps_strategy_v1_1.md`: the single coding build list is that doc's §9 Execution Synopsis (C-1..C-14); this doc is the spec it references. Made two shared items explicit to prevent double-building: **LOOM-1 ≡ strategy W1-1 = C-1** (one deterministic-preseed artifact), and **§4 DM-1/CF-1/DZ-1/ST-5 ≡ strategy HERO-1/2/3/4** (C-2/C-3/C-4). Title/companion refs updated. No scenario or beat changes. |
| v1.3 | July 10, 2026 | **Reconciled with the outreach catalog.** Added §3.1 aligning this doc with `outreach_use_scenario_catalog.md` (v1.0, May 21): established the two-lens relationship (catalog = scenario universe + outreach messaging + 23 heroes + one-liners + industry-data; this doc = demo-ready/surface-mapped), reconciled the counts (catalog 91 vs this 94 — differ by counting granularity + date, e.g. SOC 10 narrative units vs 20 per-tab scenarios; Trading 20 and S2P 16 match exactly; neither authoritative over the other), and mapped the demo beats to the outreach heroes with the proven one-liners + industry-data hooks for the presenter scripts (TRD-1 mirror, SOC-4 admits-failure, DO-4 $604K fusion, DO-2/PUR-3 departure, SOC-1 amnesia). No scenarios re-typed — the catalog stays the source for the full 91 + messaging; this doc guarantees demoability. Companion refs updated. |
| v1.4 | July 10, 2026 | **Positioning reconciliation with next_steps v1.8.** §1 pillars updated to the deployability framing — **Governed / Grounded / Compounding** (compounding demoted to support) — and the spine reframed to "Compounding Intelligence = the governed compounding layer" (above loop/context/harness engineering); situation-analysis (S14→P2) and context-graph synthesis flagged `[VERIFY shipped vs roadmap]` per next_steps C-VERIFY-L3L4. V7 close rewritten to the governance-bottleneck / governed-compounding-layer message ("loop engineering makes an agent finish a task; we make the whole system get better at every task, safely; the market spent 18 months proving 88% of pilots die on governance"). No scenario/beat/build changes. |
| v2.0 | July 10, 2026 | **Brought current with next_steps v1.21 + product_integrity v3.0.** (1) **§0.1 room→kill-shot map** — beats re-indexed by **competitive room** (not only by copilot), one weapon + one line per room; 10 of 13 rooms have a LIVE kill shot. (2) **Scenario classes LIVE / NEAR / ARCH** now travel with every beat (product_integrity §2.8): showing roadmap is allowed and expected; implying roadmap is LIVE is the only violation (F-27). (3) **§0.2 demo-truth constraints** — the three things the code says that the storyboard must respect: **SOC learning is DISABLED by default** (`soc/config.py:66`) so any SOC "watch it learn" beat won't fire unless enabled (C-1 DoD: prove a verified decision changes a later SOC score, or re-cut the beat); **naming (F-25)** — the primary mechanism is decision-trace/prototype learning from verified decisions, **not "RL"** (and judgment is not reward-maximizing; exploration is conservation-bounded by construction, C-18/C-19); **C-17 is scoped (F-24)** — prompt-variant promotion is ungated, so say "governs our scoring, exploration and scorer-evolution loops," never "all loops," until C-GOV lands; and no shared cross-copilot judgment claim (F-26). (4) **New §4.6** — Trading situation-conditioned + volatility beats (TRD-S1..S4, TRD-V1/V2/V5/V6/V7), leading with **TRD-S3 autonomy throttle**, **TRD-V1 short-vol illusion** and **TRD-V2 VRP edge-or-insurance**; all magnitudes flagged as illustrative formats, not measured results. (5) **New §4.7 — TRD-S7 "The Re-convergence Moment"** (⭐ the strongest technical beat available): replay a real 2020/2022 regime break, cold-start vs regime-indexed re-convergence = **γ>1 made visible against non-stationarity**, the failure that kills every RL trading system; class **ARCH** until C-REGIME P4 + EXP-REGIME. (6) **New §4.8 — ENT-1 "The Sunk-Investment Multiplier"** (the Celonis/enterprise wedge's missing beat: "your Celonis spend just became more valuable, not obsolete"), with a scope guard — surface *which decision to change*, not *we execute it in your ERP* (write-back is roadmap). (7) **§5 preseed** gains SOC-learning-enabled, Trading situational tags, and a real regime-break window; hard constraints gain the F-24/F-25/F-26 wording rules. (8) `SOC-V4` catalog entry renamed off "RL Safety Controls." |
