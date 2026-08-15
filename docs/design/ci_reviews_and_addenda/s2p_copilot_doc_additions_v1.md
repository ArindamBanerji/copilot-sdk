# S2P Copilot — Document Additions & Corrections v1
*Change-spec for `s2p_copilot_unified_v1_3.md` (Drive id 18kvjYsHopNWSeKwU8gGmxP4viZ57g0Yd, design folder). Applies the consolidated three-run judgment (`s2p_review_consolidation_v1`) to the product-definition half (§PD1–§PD13). Same deliverable shape as the trading / dataops / purchasing copilot addenda: each block says WHERE it lands and WHAT changes. Nothing is deleted from the product; the cuts below are **positioning** cuts (what the market story leads with), not product cuts.*

> **Reader's orientation.** The doc holds two architectures: **Part I (§1–§20)** designs the 8-domain risk cockpit — tensor **(5,5,8)** — and **Part II (§PD)** ships the Invoice-Exception + Price-Leakage pilot — tensor **(5,5,7)=175** (§PD6.3, §PD11-M1). These additions land almost entirely in Part II and treat the pilot as the product; Part I's (5,5,8) is roadmap engineering, not the story (§H).

---

## §0 — NEW front-matter block (insert after the Part II header, before §PD1): "Lead simple — the product story"

The architecture is ambitious enough; the product story must be **radically simpler than the architecture**. Add this as the governing frame for all of Part II:

- **Product thesis (S2P):** *Earned Autonomy for Source-to-Pay* — S2P decides with evidence, learns from verified outcomes, and expands automation only where the customer's own history proves it safe.
- **Platform thesis:** *Compounding Judgment.*
- **One outcome** to sell: auto-approve coverage that grows **safely, week over week**. **One number** on the wall (that coverage). **One object** the whole product emits (the *decision-change proposal* — §D). **One proof** (the *frozen twin* — §D).
- **Four-beat market story:** (1) enterprises keep resolving the same procurement exceptions forever; (2) S2P makes the decision, shows the evidence, and abstains when it hasn't earned trust; (3) verified outcomes teach it which decisions can safely become automatic; (4) the enterprise accumulates a governed memory of judgment that gets harder to replace with every verified decision.
- **The four capability axes (situation analysis, learning velocity, self-computation/process fusion, cross-graph risk) are the *architecture of the advantage*, not four co-equal reasons to buy.** Re-ranked by market role in §C.

---

## §A — CORRECT §PD1 ("The Problem Nobody Has Solved"): retire the 2026-false competitive claims

§PD1 currently reads *"Zycus Merlin auto-processes invoices… Celonis finds bottlenecks… they don't learn, don't reason, don't tune."* As of 2026 this is **factually wrong and a buyer punctures it on sight** — Celonis ships an Orchestration Engine, AgentC, a Context Model, an MCP server and Ikigai; Coupa ships Navi/Compose/Agent-Studio/autonomous sourcing; SAP ships Joule across Ariba/Fieldglass. **Replace the "they can't reason/act/tune" framing** with the durable one:

> Every incumbent now ships agents, orchestration, and MCP. What none of them ships is a system that **compounds the firm's judgment** — that gets measurably better at *this firm's* decisions from verified outcomes, and can prove it's safe to expand autonomy. Decision #10,000 is still processed like decision #1 everywhere else. That is the gap S2P fills — not "we act and they don't."

Keep the closing line ("procurement that learns from every verified decision, reasons from cross-system context, tunes its own operations, and gets measurably better every quarter") — it's the right claim; only the competitor teardown changes.

---

## §B — §PD2 (16 Scenarios): preserve all 16 in the product; narrow the *market spine* to 5

Two different rules, made explicit (this resolves the standing "nothing removed" tension):
- **Product preservation:** all 16 scenarios (S1–S16) stay in the product and the doc. Extend/add; never remove.
- **Positioning preservation:** the *market-facing spine* leads with **five** — **S14** (situation analysis, the category-definer), **S2** (autonomy expanding with proof), **S15** (values-caution), **S9** (silent-break detection), **S16** (process-fusion). The other eleven are roadmap depth produced **on request**, not the front door. Sixteen scenarios + a $41–71M portfolio reads unfocused to a Series-A room (see §H).

Add a one-line tag to §PD2 marking the five spine scenarios as **[SPINE]** so downstream collateral inherits the lead set.

---

## §C — REPLACE §PD4 ("Differentiation & Positioning"): the biggest correction in this addendum

§PD4 currently carries two **retired** framings that must not survive to any buyer:
1. The Competitive Test row *"Does your system REASON… | Rules | N/A | Rules | Context-graph reasoning"* — Coupa/SAP agents reason now.
2. **"Celonis Positioning: Celonis = the mirror (shows WHERE). We = the brain + hands + memory."** — Celonis acts, orchestrates, and has decision intelligence in 2026.

Replace §PD4 wholesale with:

**C.1 — Re-rank the four axes by market role** (they are *not* equally valuable at the point of sale):

| Market role | Axis | Positioning line |
|---|---|---|
| **Lead — gets you bought** | Situation analysis | "Make the right exception decision, with evidence." |
| **Differentiator / expansion engine** | Self-computation / process fusion | "Learn which exception classes can safely stop being exceptions." |
| **Proof of compounding** | Accelerating learning | "Each new supplier/category/disruption reaches trusted performance faster." |
| **Expansion surface / TAM** | Cross-graph risk | "Bring external risk into today's decision, not another dashboard." |

**C.2 — The competitive test, 2026-true.** Keep the two rows that survive (they're defensible): *"After 10,000 decisions, show me the compounding curve"* (here it is; everyone else can't) and *"Prove 50% auto-approve is safe"* (conservation gate + audit trail). **Delete** the "Rules vs reasoning" row. Add the honest layer-delta rows: *"After 10,000 decisions, does the system get measurably better at YOUR decisions?"* and *"Can you prove it's safe to expand autonomy, on your data?"*

**C.3 — Consume-don't-compete (replaces "Celonis = mirror").** The incumbent stack is **substrate to sit on top of**, consumed via MCP:
- **Celonis** (2026-true layer delta): models the *process* (a descriptive/diagnostic twin) and triggers actions on thresholds — it **doesn't compound the firm's judgment, doesn't reason-and-abstain among actions, doesn't learn inside the edit, and is process-siloed.** S2P ingests Celonis's Process Intelligence Graph via its MCP server and adds the layer it lacks. (S2P already lists Celonis among its MCP connectors — competitor *and* customer.)
- **SAP Ariba/Joule, Coupa Navi:** agents inside their own system-of-record — no compounding of firm-specific judgment across the decision history, no conservation-gated proof that expanding autonomy is safe.

**C.4 — The stack slot to own** (§G): SAP/Oracle = transactions · Coupa/Ariba = workflows · Celonis = process context · **S2P = the learned decision system.**

Keep the "Positioning by Buyer" table in §PD4 but retune the CIO/CDO line to add *"…without locking your judgment inside one foundation model"* (the model-swap durability of judgment memory).

---

## §D — EXTEND §PD6 (Feature Sets): make the moat visible — surfaces a buyer can look at

The capabilities are real in code and invisible in the product. Add these as first-class surfaces. Most are **views on one object** — build the object once.

- **F23 — Decision-Change Proposal (the base object) [P0].** Evidence chain + expected KPI delta + confidence + rollback path, emitted into the existing SAP/Coupa approval queue for review. Monetizes the safe side of the write-back line today; reduces full autonomy to a config flag, not a rebuild. *Extends F2 (evidence panel) + F5 (auto-approve). Every ledger below renders this object.*
- **F24 — Autonomy / Compounding Ledger [P0].** A first-class surface (not a pilot analysis): auto-approve coverage climbing over calendar time, plus review-hours avoided, dollars recovered, abstain rate, bad-auto-approval rate, new-category time-to-trust, promotions/rollbacks, and **incremental result vs the frozen baseline** — with a plain-language *why* under every expansion. This is what makes Judgment Memory economically visible. *Extends F9 (IKS) + F10 (financial ledger).*
- **F25 — Decision-Class Promotion Workflow [P0].** The lifecycle of F23: **Discover → Shadow → Promote → Measure → Keep/Rollback → Transfer.** ("This exception class has been consistently buyer-approved → propose auto-approve → shadow → show counterfactual → promote → monitor → auto-rollback on degradation → transfer to another plant.") The product form of *"every recurring exception is a candidate for extinction."* *Extends F12 (AgentEvolver) with the visible promotion/transfer ledger.*
- **F26 — Frozen Twin [P0].** A shadow instance pinned at day-one config, running permanently alongside live. Only credible proof of acceleration-not-just-improvement; converts CLAIM-59/CLAIM-62 from synthetic to **measured on the customer's data by ~day 90**; doubles as a rollback/trust feature. *New; pairs with F24.*
- **F27 — Counterfactual "What Would Change My Mind" Inspector [P1].** Beside *"Why this decision?"* put *"What would have changed it?"* ("would flip to HOLD if contract allowance < 4.8% / supplier exception history deteriorates / commodity correlation leaves trusted range"). Falsifiability, not explanation — materially different from agent "explainable AI," and it makes Judgment Memory tangible without exposing centroid terminology. *Extends F2 + F7.*
- **F28 — Confidence Panel ("what I'm not confident about") [P1].** Surface the already-built novelty tracker + self-pause (F6) as a **permanent, always-visible confidence state**, not an alarm that fires. Standing visibility survives the audit conversation and answers S9's deepest fear (wrong *quietly*).
- **F29 — Day-0 Data-Readiness Assessment [P1, the conversion engine].** A paid discovery deliverable generated in week one of connection: here's what your data supports, here's what we'll abstain on until it improves, here's the honest empty state. Leads with what you *can't* trust (nobody else does); converts into the pilot. **Build note:** day-0 cannot use *learned* factor-trust weights (those need accumulated decisions) — build it on the enrichment layer available at day zero (source coverage, completeness, provenance, trust tiers).
- **F30 — Cold-Start / Transfer Measurement [P1].** The falsifiable *customer* metric for the acceleration thesis: new supplier #6 reaches trusted automation in ~40 verified decisions vs ~120 for #1 (illustrative, MODELED). Feeds the "learning velocity" positioning (§J).
- **F31 — Rollback + Degradation Detection [P1].** For promoted policies (F25) — the safety half; makes expanded autonomy enterprise-safe.

Risk-enrichment (Axis 4) stays **inside today's decision** (P2) — "normally-safe supplier; auto-approval temporarily suspended because financial-risk + logistics changed the downside" — not a second product tab (§H). The optimizer/solver export is already F20; keep it, correctly subordinate.

---

## §E — NEW under §PD6/§PD8: engineer the crossover to land INSIDE the pilot window (the survival move)

Under the 5:1 penalty, day one **adds** review load (every abstain is labor the customer pays for) while the frozen twin hasn't diverged yet — the trough where pilots die. A ledger (F24) that honestly documents a loss in month four of a 90-day pilot loses the account. Pull the crossover forward with levers already in the design:
- **Pre-seed judgment memory with domain priors** — this is exactly what CLAIM-62's enriched-μ₀ (+42.69pp Day-1 lift) buys: day-one competence, not a cold start.
- **Start auto-approve on the single safest category** where conservation clears fastest, not across all five.
- **Size the pilot** to clear the crossover with margin.

This makes F24 a product that *wins* rather than one that scores a defeat. **Verify-in-code before committing:** whether the crossover is reachable on the pilot's real volume.

---

## §F — §PD4/§PD5: moat reframe — a TIME moat, and commit to portability

Retire *"You can copy the code; you cannot copy your graph"* as the lead moat line — to a procurement buyer it reads as a **lock-in red flag** (these are professional lock-in-avoiders). Replace:
> The moat isn't algorithms a competitor can't build — it's **customer-specific verified judgment they can't retroactively manufacture.** It compounds with elapsed verified decisions: Day-1 S2P may be copyable; Day-400 S2P is hard to displace because replacement means discarding a mature decision policy.

**Commit to judgment-memory portability/export** at termination (a commercial commitment, landed at MSA). It costs almost nothing — the moat is the accumulation over months, not the file — and buys disproportionate trust in exactly the room where trust is scarce.

---

## §G — §PD4: the stack slot, stated once, cleanly

Add as a standalone positioning line: **SAP/Oracle keep the transactions. Coupa/Ariba/Zycus keep the workflows. Celonis/Signavio keep the process context. S2P keeps what the enterprise has *learned about making the decision*** — the learned decision system. That distinction survives technological convergence (it isn't "better agents / better graph / we orchestrate").

---

## §H — §PD1(Part I)/§PD9: cut the 8-domain risk cockpit from the *story* (not necessarily the code)

All three judge runs converge here. The 8-domain risk cockpit (Part I, (5,5,8)) is a **second product on terrain where the moat doesn't exist** — it's largely external-*data* aggregation (supplier/geopolitical/weather), measured against Everstream/Interos/Resilinc and the suites' risk modules, who own external-data moats S2P doesn't. Everything valuable survives as **enrichment that makes invoice decisions better today** (§D, Axis 4 into the decision).
- **Positioning cut (do now):** stop showing the 8-domain cockpit as a destination in §PD1/§PD9. Narrow the headline value from the $41–71M portfolio to **the pilot number** (safe auto-approve coverage growing). Keep the portfolio as roadmap depth, not the front door.
- **Code decision (separate — verify before ripping):** the doc itself shows the pilot is (5,5,7) (§PD6.3, §PD11-M1: migration (6,4,6)→(5,5,7)) while Part I designs (5,5,8). Confirm the **live tensor shape** before any code change; keeping an 8th risk factor as a *quiet enrichment input* is harmless and separate from ever selling a "risk cockpit."

---

## §I — §PD10/§PD11-M1: commercial — derive 5:1 from data; price on outcomes

- **Derive the 5:1 penalty from the customer's data at onboarding** (§PD11-M1 currently carries 5.0 as a design estimate; §PD10-Q2 flags it). Compute it from their actual cost of a bad approval vs a hold — a magic number becomes a defensible configurable knob, and the derivation is a procurement-fluency discovery conversation.
- **Pricing basis:** decisions-under-management / recovered value / auto-approve coverage — **not per-seat** (per-seat disincentivizes enterprise-wide adoption). Add as a §PD10 open decision with this recommendation.

---

## §J — global honesty pass (Part II)

- Tag every quantified claim with **maturity** (LIVE/NEAR/ARCH) and **evidence** (DEMO-PROVEN/MEASURED/MODELED/PILOT-TARGET). CLAIM-59 (54.4% fewer decisions), CLAIM-62 (+42.69pp), and the $41–71M model are **synthetic-validated (SVM/LLM-judge), not real-deployment** — never let them read as realized. This is the #1 credibility exposure.
- **Externally, sell "learning velocity," not "second-derivative RL."** Keep the second-order model for technical-diligence rooms only. (This is also consistent with the demo doc's F-25 naming rule.)
- **Drop the n(n−1)/2 super-linearity claim** from positioning → *"each new trusted domain must prove incremental decision value before S2P relies on it."*

---

## §K — §PD12/§PD13: demo-risk — fix the score-path stall before S2P is a live demo

The 30–43s lock stalls (pool-exhaustion/warm-fallback) are **production-real**, not a WSL artifact. S2P is the lead wedge; one 30-second freeze in front of a CPO costs more than any positioning gain. The fail-closed bounded acquire-and-write timeout is the highest value-per-effort item; the structural fix is making the score-write **atomic** — the same work already in the calibration commit, same lock region, so sequence them together. Stage any live S2P demo single-worker with the pool pre-warmed. *(Cross-ref the S2P perf/FIX-B engineering track.)*

---

## §L — §PD10: open decisions the founder must make (don't silently resolve)

Add to §PD10: (1) the write-back boundary — decision-change proposal into the queue (ship now) vs autonomous ERP posting (roadmap + liability); (2) pilot-vs-8-domain sequencing (§H); (3) pricing basis (§I); (4) compete-vs-complement stance toward Celonis (recommend complement/consume-via-MCP).

---

*Applies `s2p_review_consolidation_v1` (three-run: Opus/GPT/Gemini) to `s2p_copilot_unified_v1_3.md` §PD1–§PD13. Companion: `demo_scenarios_s2p_additions_v1.md`. Verify-in-code items: live tensor shape (5,5,7 vs 5,5,8); crossover reachability on pilot volume; score-path atomic-write status.*
