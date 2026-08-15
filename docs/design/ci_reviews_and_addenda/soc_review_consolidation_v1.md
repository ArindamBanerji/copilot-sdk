# SOC — Review Consolidation (Judge Runs) v1
*Zip/bundle filename: `soc_review_consolidation_v1.md` — the SOC member of the per-copilot consolidation family (trading / dataops / purchasing / s2p / soc).*
*Consolidates the three LLM-judge runs of the SOC market-winner prompt — **GPT-5.x**, **Claude Opus**, **Gemini** — read as one judgment, not a vote. Companions: `soc_copilot_doc_additions_v1.md` (product-spine enhancement) and `demo_scenarios_soc_additions_v1.md` (demo beats). Grounded against the innovation note, `soc_copilot_product_definition_v1_2.md` (the product spine — already updated), and `soc_copilot_design_v5_8.md` (the engineering doc — §11.5 five tabs, §21 shadow, §22 IKS/referral/monitoring, §23 NL templates, §28 H7 honesty rule).*

> **Method note (honest).** The panel was run imperfectly: GPT saw an earlier instrument, and the brief was tightened between GPT's run and the others, which weakens the "three independent models converged" claim. Where a point is genuinely instrument-independent (a factual self-own, a market fact, a place two models agree for different reasons) it is treated as strong; where it may be an artifact of the brief, it is flagged. The corrections were already folded into the product spine (`soc_copilot_product_definition_v1_2.md`); this doc records the reasoning and routes the *net-new product* work to the two addenda.

---

## 0. The three runs, characterized (they came at the product from different angles — that's why the overlap matters)

- **GPT — positioning + packaging first.** Scored the pitch (architecture 9 / differentiation 8.5 / current positioning 7 / **customer-proof readiness 5–6** — the gap it called "the main company-building problem"). Reframed the wedge to a *promise* ("Provable Adaptive Triage" — prove what changed, that it improved, that it's reversible; geometry is the *how*, not the promise), led with Gate 1 + Gate 3a, and productized the primitives into surfaces (Learning Control Room, Frozen-Twin, new metrics, Earned-Autonomy ladder). Strongest on turning architecture into a buyer-visible product.
- **Opus — strategy + credibility first.** Caught the two positioning errors that matter most (consistency-vs-novelty buyer split; the exportability self-own), named the gap the brief hadn't asked about (cold-start), and pushed every number toward hard-dollar and measured-on-your-data. Strongest on *which buyer, which wound, which budget* — and on the honesty guards.
- **Gemini — prompt-execution first.** Ran the return format literally (wedge · per-gate · stack-fit · scenario cards · positioning-by-buyer · moat table · gauntlet · D-null/D-ext). Strongest on the stack-fit spec and the killer-objection (platform absorption) with its defense (cross-stack judgment gateway) — **but, like the S2P Gemini run, it committed the synthetic-vs-measured sin it correctly names as risk #1** (fabricated demo specifics) and rebuilt two overclaims it was handed. Harvest the structure; quarantine the invented numbers (§4).

---

## 1. Where all three converge — do these (strongest signal)

- **Synthetic-vs-measured is the #1 risk.** GPT (customer-proof readiness 5–6 is the whole company problem); Opus (lead unproven-claims flag = the numbers are synthetic); Gemini (explicit HIGHEST RISK, defusal = label controlled-synthetic + a shadow-mode pilot that computes the customer's own curve). **Unanimous.** The defusal is the same everywhere: label the 50-seed numbers as controlled synthetic evaluations and sell the **90-day shadow pilot as the measurement engagement** whose deliverable is the customer's live compounding curve. (Already the demo doc's H7 posture — §5.)
- **Position ABOVE the platforms, not beside them.** GPT ("decision-learning layer, not another agent — above MS/CrowdStrike/Splunk"); Gemini ("cross-stack judgment gateway… never lock centroid geometry to one data lake"); Opus (the "why not Security Copilot" answer is a layer answer, plus force the price-to-zero economics). **Unanimous.** Telemetry owners (Falcon/Sentinel/Splunk/Okta) become input + execution surfaces; the moat is the customer's accumulated verified-decision judgment across systems no single vendor owns.
- **Make the compounding visible as a product surface, not an architectural property.** GPT (Learning Control Room: BEFORE→CHANGE→EVIDENCE→EFFECT→SAFETY per promoted change; Frozen-Twin-as-product; Safety-Coverage Frontier + Recovery Half-Life as the compounding metrics); Opus (productize the no-precedent moment; earned-autonomy as a named promise); Gemini (Canary Rollback Visualizer, Circuit-Breaker state display, Process-Edit Safety Replay). **All three, independently** — the capabilities are real in code (Tab 2 both mechanisms, IKS, counterfactual replay, referral VETO, conservation) and under-exposed as product. Routed to `soc_copilot_doc_additions_v1` §A.
- **Earned Autonomy is the promise, not a footnote.** GPT (the Observed→Assisted→Shadow-qualified→Auto-approved→Circuit-broken ladder per alert class); Opus (make it the board-ready promise; it may matter commercially more than AgentEvolver). **Convergent** (Gemini's Circuit-Breaker display is the same idea at the mechanism layer). This is the packaging of surfaces the product already ships (referral VETO R1–R7 + conservation Circuit Breaker + per-category auto-approve + shadow mode).
- **Competitor naming: architectural contrast in public, names only in private/diligence.** GPT (a held tension — dial back named attacks in the primary motion, keep the taxonomy for diligence); Opus (unnamed taxonomy in the primary motion; named matrices in a diligence appendix — a named delta has a one-quarter half-life); Gemini (recommend architectural contrast in public decks, name competitors in private sales enablement). **Unanimous.**

---

## 2. Where two of three converge (strong — dissent noted and resolved)

- **The wedge = consistency + provability, with Stryker as proof.** Opus (the ICP's trigger is *inconsistent triage* — a consistency/auditability wound, one buyer, one budget; the LIVE assets are a consistency story; lead Gate 1 + Gate 3a and make Stryker *proof consistency survives no-precedent*, not the reason to buy) + GPT (hero = Gate 1 + Gate 3a: change + proof-of-change). Gemini led with the geometry+runtime-evolution *engine* and leaned novelty (Stryker as the hero) — **resolve toward Opus/GPT:** lead consistency + provability; novelty is the proof, not the pitch. (This also lets Gate 2 sit at true strength rather than straining to carry a novelty sale.) Already applied in product-def v1.2 §P0.2.
- **The two overclaims must go.** GPT flagged them as tier-catches (Gate 2 "evolve mid-incident" outruns the product → "policy evolves continuously from verified outcomes without a retrain or vendor release"; Gate 3b "make the class impossible" must not carry the current sale → land-triage / expand-detection / end-state-remediation). Gemini *reproduced both* when handed them (its Gate-2 line said "mutate live scoring weights mid-incident"; its Gate-3b line said "eliminate the attack class permanently") — which confirms they were **prompt-induced**, not product truth. **Resolve: corrected** (product-def v1.2 §P4.1). Opus independently reached the same place via the methodology critique.
- **Pilot economics: shadow-only yields a curve, not saved hours.** Opus (sell the pilot as a measurement engagement, deliverable is the customer's, conversion threshold pre-agreed before day 1) + Gemini (offer a 90-day shadow-mode pilot to generate their own live compounding curve as the synthetic-vs-measured defusal). **Convergent.** GPT's frozen-twin is the same artifact seen from the proof side.
- **Hard-dollar ROI.** Opus (soft-dollar analyst-hours get marked to zero; displace MDR/MSSP spend + tiered SIEM ingest) + Gemini (ROI in recovered analyst capacity, but its own gauntlet demands "which existing budget line does this replace"). **Resolve toward the hard-dollar line** — lead with the budget line being displaced; keep the frozen-ROI hours model as the supporting story. Already in product-def v1.2 §P6.

---

## 3. Single-run gems worth keeping

**GPT only:**
- **The customer-proof readiness score (5–6) as the company's central problem** — everything downstream (frozen-twin, pilot-as-measurement, the first real curve) serves closing it. This is the sharpest single diagnosis in the panel.
- **Safety-Coverage Frontier + Recovery Half-Life** as the metrics that express compounding better than raw accuracy (a non-saturating pair: how much safe coverage at a fixed safety bar, and how fast the system re-reaches competence after a new attack class). Routed to `soc_copilot_doc_additions_v1` §B.
- **Novel Attack Gauntlet** — generalize Stryker into a benchmark *class* (no-precedent / misleading-precedent / signal-inversion / regime-break / adversarial-context), so the novelty claim is a repeatable test, not one anecdote. Routed to §C.
- **Rename Judgment Memory externally → "Customer-Owned Judgment."**

**Opus only:**
- **The cold-start counter** (Torq Retrospect imports years of history to kill "you start at zero"): the answer is the expert-prior substrate for Day-1 competence + firm-specific deviation is what bends the curve (noisier/idiosyncratic environment → bigger delta). Nobody else raised it; the product had no answer on file. Now product-def v1.2 §P1.
- **The exportability self-own** — "own/export the centroid tensor = switching cost" is *backwards* (it's anti-lock-in). Correct: they own the judgment; CI owns the GAE that keeps learning and enriching it; the exported tensor alone is a data file. A factual fix, instrument-independent. Now product-def v1.2 §P2.
- **Force the Security Copilot price-to-zero economics** (bundled into E5-adjacent licensing at near-zero marginal price) — the epistemics answer (Four Clocks) must survive the price argument, not just the capability argument.

**Gemini only (harvest):**
- **Killer objection named: SIEM/EDR platform absorption** (CrowdStrike/Palo Alto/Microsoft shipping "good enough" native triage free in-console) — and the defense: the **cross-stack judgment gateway** (a fast-follower must rebuild non-parametric metric learning over *open* graph topologies, not fine-tune prompts in their own lake). Routed to `soc_copilot_doc_additions_v1` §D and the demo §SOC-ROOM.
- **SOAR-first liability recommendation** — push scored payloads to SOAR/ITSM queues, don't directly execute EDR host isolation (keeps separation of duties, reduces the write-back liability surface). A founder open decision (§F of the addendum).
- **Concrete Gate-1 UI widgets** worth folding into the surfaces: a *Falsifiable Distance Inspector* (the factor weights + nearest-prototype distance per scored alert → feeds F20 counterfactual) and a *Live Abstention Audit Counter* (analyst-hours saved vs alerts safely deferred by the referral VETO → feeds F17 earned-autonomy). Both are renderings of shipped primitives.
- **The clean genuine-moat-vs-now-table-stakes two-column table** (the prompt asked for it; Gemini rendered it cleanly).
- **D-null** (won't land: <500 alerts/day, or fully outsourced MSSP shops — no analyst capacity or data to feed compounding; refer out or MDR-integration package) and **D-ext** (insider-threat behavioral-centroid engine across HR/Git/DLP; automated SOC-audit-certificate generator, hash-chained SOC2/ISO evidence).

---

## 4. Gemini — QUARANTINE (must not propagate into the consolidation, decks, product doc, or demo)

- **Fabricated demo specifics presented as if measured:** "escalated Intune bulk-wipe anomaly **in 12 seconds**," "**99.4%** confidence distance," "auto-suppressed **450 benign developer SSH alerts**," "device_trust factor-trust weight **increased 1.4×**," "uncovered stealth C2 across **3 unmanaged endpoints**." These are exactly the synthetic-vs-measured sin the run itself names as risk #1. Any illustrative figure must render from preseed with a provenance badge and carry the H7 honesty label — never read as a realized outcome (design-doc §28.3).
- **The exportability line, rebuilt backwards:** Gemini's stack-fit §4 says "exportable tenant tensor… building an uncopyable operational switching moat." This is the self-own Opus corrected. **Do not propagate** — exportability is anti-lock-in; the moat is the accumulated judgment + the engine that compounds it.
- **The Gate-2 "mutate live scoring weights mid-incident" line** and **the Gate-3b "eliminate the attack class permanently" line** — both are the prompt-induced overclaims (§2). Strip to true strength (evolves from verified outcomes without a retrain/vendor release) and roadmap (land→expand→end-state).
- **Buyer-language leaks:** "centroid geometry," "α·q·V ≥ θ_min," "1/σ²," "L₂ distance," "DiagonalKernel metric" appear in Gemini's *buyer-facing* lines. Scrub to buyer language (which alert to trust, proof it's safe, coverage growing safely) — keep the math for technical-diligence rooms only.
- **The two-regime discipline Gemini ignored:** its "Does it actually work? … 78.9% at decision 1,000" answer must never sit next to the 97.89% centroidal-synthetic number, which validates the *math* and is **never customer-facing** (design-doc §4.4). None of the runs surfaced this guard — it is a SOC-specific hard rule (§5).

---

## 5. Advisor overlay (mine — not a fourth vote; the three runs under-weight these)

- **★ Engineer the crossover to land INSIDE the pilot window** — the survival move none of the three names for SOC. Shadow mode adds review structure before the frozen twin has diverged; a Learning Control Room that honestly documents "no measurable lift yet" in month two of a 90-day pilot loses the room. Pull the crossover forward with levers already in the build: **pre-seed with enriched μ₀** (CLAIM-62: +42.69pp Day-1 lift), **start auto-approve on the single safest category** (`cloud_infrastructure` clears conservation fastest; `insider_threat` is near-zero by design), and size the pilot to clear crossover with margin. Routed to `soc_copilot_doc_additions_v1` §E.
- **The two-regime rule is a SOC-only guard the panel missed.** 97.89% is mechanism-validation on centroidal-synthetic data and is *never* customer-facing; 71.7%/78.9% (50-seed realistic) is the product claim. Bake this into every beat and deck (demo §SOC-FIX).
- **Earned Autonomy already has its substrate in code** — it is not new engineering, it is packaging: referral VETO R1–R7 (organizational-context overrides) + conservation Circuit Breaker (AMBER auto-pauses learning) + per-category auto-approve thresholds + shadow mode. The ladder is a *rendering* of existing primitives; sequence it as a surface, not a rebuild.
- **The no-precedent surface has real backing** — the SimilarCasesService already suppresses the sidebar below 5 prior decisions and returns a defined empty state. Productizing "similar past cases: none — unprecedented here" (Stryker's line) is surfacing an existing honest empty state, not inventing a claim. The pixel a retrieval UI cannot draw.
- **Day-0 readiness cannot use *learned* factor-trust weights** (those need accumulated decisions) — build it on the enrichment layer available at day zero (source coverage, completeness, provenance, threat-intel connector health), same constraint the S2P analog carries.
- **Factor-0 is assumed reconciled** (`privileged_identity_context`, the Stryker signal) — if revalidation moves the numbers, they move in the doc; no panel item depends on the old `travel_match` semantics.

---

## 6. Net direction, and sequence

**The through-line all three share:** the architecture is real and the words are now commodity; win on the **provable, governed, closed loop** and make it a product a buyer can look at. Collapse to **one wedge** (consistency + provability), **one number** (safe auto-approve coverage growing, week over week, at a fixed safety bar), **one object** (the promoted-change record the Learning Control Room renders), **one proof** (the frozen twin on the customer's own alert stream).

**Sequence (dependency + goal):**
0. **The first-customer compounding curve** — the shadow-mode measurement pilot is the company's highest-priority artifact; every number is synthetic until it exists. Everything below serves producing it.
1. **The promoted-change record + Learning Control Room** (BEFORE→CHANGE→EVIDENCE→EFFECT→SAFETY) — renders existing primitives (Tab 2, IKS, counterfactual replay, evidence export). The base surface.
2. **Earned Autonomy ladder + Frozen Twin + the two metrics (Safety-Coverage Frontier, Recovery Half-Life)** — survive + prove; the frozen twin is the synthetic→measured converter, **with the crossover engineered in** (§5).
3. **No-Precedent surface + Counterfactual "what would flip it" + Day-0 readiness** — the trust/novelty/conversion surfaces.
4. **Positioning:** consistency-lead; above-the-platforms + cross-stack-gateway defense to the platform-absorption objection; unnamed taxonomy in the primary motion; hard-dollar ROI (MDR/MSSP + SIEM-ingest displacement); Security-Copilot price-to-zero answer.
5. **Novel Attack Gauntlet** — turn Stryker into a repeatable benchmark class (proof, not anecdote).

---

## 7. Source-doc reconciliation — where each decision already landed, and what's left

Reading the product spine and the engineering doc end-to-end confirms the split that makes the SOC family "slightly different" from the others:

**7.1 — The corrections are already IN the product spine.** Unlike the other copilots (where the doc-additions applied the judge feedback to a not-yet-updated product doc), the SOC corrections were folded directly into **`soc_copilot_product_definition_v1_2.md`**: consistency-lead wedge (§P0.2), Gate 2 at true strength + Gate 3b land/expand/end-state (§P4.1), exportability corrected (§P2), hard-dollar ROI (§P6), Earned Autonomy as a named promise (§P4.6), the cold-start counter (§P1), competitor-naming discipline (§P4.4), numbers labeled MEASURED-synthetic + pilot-as-measurement + frozen-twin (§P0.4/§P6). **So the doc-additions addendum is not a correction pass — it is the net-new PRODUCT ENHANCEMENT layer** (the buildable surfaces, the two new metrics, the benchmark class, the crossover engineering, the platform-absorption defense). That is `soc_copilot_doc_additions_v1.md`.

**7.2 — The surfaces the new beats extend are all real in the engineering doc.** §11.5 ships the five tabs (Tab 3 Triage / Tab 2 Runtime-Evolution + Learning-Impact, both mechanisms / Tab 4 Compounding / Tab 5 Exec Narrative v6.0 / Tab 1 Panel B Graph Explorer); §21 shadow mode (30-day/500-decision, never auto-activates); §22 IKS + §22.6 referral VETO R1–R7 + §22.7 three-signal conservation monitoring; §23 the 24 deterministic NL templates; §13/§28 the honesty discipline. The Learning Control Room, Earned-Autonomy ladder, No-Precedent surface, and counterfactual inspector are *renderings/packagings* of these — surfacing tasks, not new mechanisms (the frozen twin and the two metrics are the genuinely new builds).

**7.3 — The demo doc's honesty rules already encode the synthetic-labeling discipline.** The SOC world's H7 rule (§28.3) — *every UI value traces to a real computation OR carries a visible honesty label* — is the SOC-native version of the S2P F-21/F-22 illustrative-dollars rule, already enforced demo-side. The "product not demo" language rule (§13) and the never-say-"RL"-for-the-primary-mechanism discipline are the SOC analogs of F-25. So the synthetic-vs-measured defusal lands mostly as *product-doc* framing (already in v1.2 §P0.4); the demo addendum only has to keep new beats inside the existing H7 rules.

**7.4 — What each decision maps to, concretely:**
- Consistency-lead / one-wedge-number-object-proof → product-def v1.2 §P0.2 (done); demo **§SOC-LOOM spine**.
- Wedge corrections (Gate 2/3b, exportability, ROI, cold-start, competitor-naming, earned-autonomy-as-promise) → product-def v1.2 (done).
- Net-new product surfaces (Learning Control Room, Earned-Autonomy ladder, Frozen Twin, No-Precedent, Counterfactual, Day-0, Cold-start metric) → doc-additions **§A** (new F16–F22); demo **§SOC-NEW** (SOC-CONTROL / LADDER / TWIN / NOPRECEDENT / WHATIF / DAY0).
- New metrics (Safety-Coverage Frontier, Recovery Half-Life) → doc-additions **§B**; demo **SOC-FRONTIER**.
- Novel Attack Gauntlet → doc-additions **§C**; demo **SOC-GAUNTLET**.
- Platform-absorption defense + cross-stack gateway → doc-additions **§D**; demo **§SOC-ROOM**.
- Crossover engineering → doc-additions **§E**. Founder decisions (SOAR-first, pilot sequencing, naming, pricing) → doc-additions **§F**.

**7.5 — Standing verify-in-code items:** frozen-twin two-arm feasibility on a single seed; crossover reachability on real pilot volume; whether the Learning Control Room can render entirely from existing endpoints (Tab-2 evolution, IKS, counterfactual replay, evidence export) or needs a thin new aggregate. None can be settled from the docs alone.

**Net:** the panel's judgment holds; the SOC difference is that the corrections are already in the spine, so the addenda carry the *enhancement* layer (surfaces + metrics + benchmark + crossover + positioning defense), not a teardown.

---
*Consolidates the three SOC judge runs (GPT-5.x / Opus / Gemini) read as one. Corrections already applied to `soc_copilot_product_definition_v1_2.md`. Companions: `soc_copilot_doc_additions_v1.md` (net-new product surfaces), `demo_scenarios_soc_additions_v1.md` (demo beats). Highest-priority artifact per all three runs and the spine: the first-customer compounding curve from a shadow-mode pilot.*
