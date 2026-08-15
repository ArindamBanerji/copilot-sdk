# SOC Copilot — Document Additions & Enhancements v1
*Enhancement addendum to the SOC product spine — `soc_copilot_product_definition_v1_2.md` (Part II), companion to the engineering doc `soc_copilot_design_v5_8.md` (Part I). Applies the net-new product layer from the three-run judgment (`soc_review_consolidation_v1`). Same deliverable family as the trading / dataops / purchasing / s2p copilot addenda — each block says WHERE it lands and WHAT it adds. Nothing is deleted; the five scenarios and all surfaces are preserved and extended.*

> **Why this one is different from the other copilots' addenda.** For trading/dataops/purchasing/s2p, the doc-additions file *corrected* a product doc that had not yet absorbed the judge feedback. The SOC corrections were already folded into the spine **v1.2** — consistency-lead wedge (§P0.2), Gate 2 at true strength + Gate 3b land/expand/end-state (§P4.1), exportability fixed to anti-lock-in (§P2), hard-dollar ROI (§P6), Earned Autonomy as a named promise (§P4.6), the cold-start counter (§P1), competitor-naming discipline (§P4.4), numbers labeled MEASURED-synthetic (§P0.4). **So this addendum is not a teardown — it is the buildable PRODUCT-ENHANCEMENT layer on top of v1.2:** the surfaces that make the moat visible, the two compounding metrics, the benchmark class, the crossover engineering, and the platform-absorption defense. Where a correction already lives in v1.2, this doc references it rather than repeating it.

> **Reader's orientation.** The engineering doc ships the real primitives these surfaces render: §11.5 five tabs (Tab 3 Triage / Tab 2 Runtime-Evolution + Learning-Impact / Tab 4 Compounding / Tab 5 Exec-Narrative v6.0 / Tab 1 Panel B Graph Explorer); §21 shadow mode; §22 IKS + §22.6 referral VETO R1–R7 + §22.7 conservation monitoring; §23 the 24 deterministic NL templates; §28 the H7 honesty rule. Most surfaces below are *views on primitives that already exist* — the genuinely new builds are the Frozen Twin and the two metrics.

---

## §0 — NEW front-matter block (insert at the head of the enhancement layer): "One wedge, one number, one object, one proof"

The spine (v1.2) already fixes the positioning. This layer makes it a product a buyer can look at. Governing frame for everything below:

- **One wedge:** consistency + provability (Gate 1 + Gate 3a, both LIVE, matched to the ICP's "inconsistent triage" trigger). Stryker is the proof consistency survives no precedent — not the reason to buy. *(v1.2 §P0.2.)*
- **One number** on the wall: safe auto-approve **coverage growing week over week at a fixed safety bar** (not raw accuracy — see §B).
- **One object** the product emits: the **promoted-change record** (what changed in the deployed policy, the verified outcomes that caused it, which past decisions flip, measured effect, safety) — rendered by the Learning Control Room (§A, F16).
- **One proof:** the **frozen twin** on the customer's own alert stream (§A, F18) — the synthetic→measured converter and the answer to the panel's #1 risk.

The four capability axes (situation-analysis geometry, runtime evolution, self-computation/process-fusion, cross-graph discovery) are the *architecture of the advantage*, not four co-equal reasons to buy — ranked by market role in v1.2 §P4.

---

## §A — EXTEND §P5 (Features & surfaces): make the moat visible — surfaces a buyer can look at

The capabilities are real in code and under-exposed as product. Add these as first-class surfaces. Most are **renderings of existing primitives** — build the promoted-change record once (F16); the ladder, no-precedent, and counterfactual surfaces are views on primitives already shipped. New F-numbers continue the engineering doc's F1–F15 series.

- **F16 — Learning Control Room (the base surface) [P0].** One place that renders every promoted change as a record with five faces: **BEFORE** (the policy before) → **CHANGE** (what evolved — a routing/scoring-weight variant) → **EVIDENCE** (the verified outcomes that caused it, with provenance) → **EFFECT** (measured impact + which past decisions flip, via counterfactual replay) → **SAFETY** (shadow-test result, conservation state, rollback target). *Renders existing primitives: Tab 2 Runtime-Evolution (AgentEvolver promotion/rollback), §22 IKS, §22.7 Circuit Breaker, counterfactual replay (self-computation router), §13 evidence export.* This is the literal answer to "how do I know it got better?" — the market's #1 barrier. **Verify-in-code:** whether it renders entirely from existing endpoints or needs a thin aggregate.
- **F17 — Earned Autonomy Ladder (the promise, as a surface) [P0].** The per-alert-class ladder from v1.2 §P4.6 made visible: **Observed → Assisted → Shadow-qualified → Auto-approved → Circuit-broken**, per category, with the reason autonomy was granted or withdrawn under each rung. *Packages existing primitives — referral VETO R1–R7 (§22.6), conservation Circuit Breaker AMBER auto-pause (§22.7), per-category auto-approve thresholds (§14), shadow mode (§21). No new mechanism — a rendering + state model.* Answers "what happens when it's wrong?" before it's asked; may matter commercially more than AgentEvolver itself.
- **F18 — Frozen Twin [P0, the proof].** A shadow instance pinned at day-one config (bootstrap μ₀, no learning), running permanently beside the live system on the same alert stream. Report adaptive-vs-frozen: coverage at a fixed safety bar, critical misses, analyst disagreement, time-to-competence on a new attack class, harmful proposed changes blocked. *New build; pairs with F16 and the Tab-4 compounding surface.* This is the only credible proof of acceleration-not-just-improvement and the direct answer to the synthetic-numbers risk: **"don't take our synthetic numbers — run us against ourselves on your data."** Until it has run on real data, label the divergence MODELED/PILOT-TARGET.
- **F19 — No-Precedent Surface [P1].** Productize the moment Stryker creates: "**similar past cases: none — unprecedented here**," shown beside a high-confidence action and the factor breakdown (privileged_identity_context elevated on the identity itself). *Surfaces an existing honest empty state — the SimilarCasesService already suppresses the sidebar below 5 prior decisions (§23.4). This is the pixel a retrieval-based UI cannot draw:* a retrieval learner is least confident exactly here; the geometry acts anyway.
- **F20 — Counterfactual "What Would Flip This" Inspector [P1].** Beside "Why this decision?" put "What would have changed it?" ("would drop to INVESTIGATE if the identity's privilege tier were standard / MFA signals were clean / no pattern-history velocity anomaly / threat-intel enrichment absent"). *Extends counterfactual replay + the Tab-3 factor breakdown.* Falsifiability, not explanation — materially different from "explainable AI," and it makes judgment interrogable without exposing centroid terminology.
- **F21 — Day-0 Readiness Assessment [P1, the conversion engine].** A paid-discovery deliverable generated in week one of connection that **leads with what the data can't support yet**: source coverage, completeness, provenance, threat-intel connector health (Pulsedive/CISA KEV/NVD), and the honest empty state — not a fabricated ROI. Converts into the shadow pilot. **Build note:** day-0 cannot use *learned* factor-trust weights (they need accumulated decisions) — build it on the enrichment layer available at day zero.
- **F22 — Cold-Start / Transfer Measurement [P1].** The falsifiable *customer* metric behind the cold-start answer (v1.2 §P1): seed an expert-prior substrate (enriched μ₀, CLAIM-62 +42.69pp Day-1 lift) for Day-1 competence, then measure the firm-specific deviation from that prior — the noisier/more idiosyncratic the environment, the larger the delta over an imported-history system. Feeds the "learning velocity" story and the frozen-twin comparison.

---

## §B — EXTEND §P6 (Value & ROI): the metrics that express compounding better than accuracy

Raw accuracy plateaus and undersells the moat. Add two non-saturating metrics as the core compounding measures (they beat "78.9% at decision 1,000"):

- **Safety-Coverage Frontier.** The curve of *safe auto-approve coverage at a fixed safety bar* over calendar time — how much of the alert stream the system safely handles on its own without the bad-auto-approval rate rising. It is the honest form of "the one number on the wall" (§0): coverage climbing at constant safety, per category (`insider_threat` correctly near-zero by design; `cloud_infrastructure`/`threat_intel_match` leading). Measured against the frozen twin (F18).
- **Recovery Half-Life.** After a regime break or a genuinely new attack class, the number of verified decisions (and calendar days) to re-reach the category's competence bar — the operational form of the acceleration/re-convergence claim. Non-saturating: it keeps mattering as long as the threat landscape changes. Report it with the frozen-twin control so "faster than a non-learning clone" is measured, not asserted.

Both are **MEASURED-synthetic until the pilot** (v1.2 §P0.4). Lead the ROI conversation with the hard budget line being displaced (MDR/MSSP + tiered SIEM ingest, v1.2 §P6); use these two metrics as the compounding proof, and the frozen twin as the evidence.

---

## §C — NEW under §P3 (Scenarios): the Novel Attack Gauntlet — turn Stryker into a benchmark class

Stryker is one anecdote; the novelty claim needs a repeatable test. Add a **benchmark class** (preserves all five scenarios — this extends, never replaces) that a skeptical buyer can run on their own stream: five perturbation types, each stressing the no-precedent claim in a different way —

1. **No-precedent** (Stryker itself: privileged service-tier identity, authorized bulk Intune ops, MFA/device clean).
2. **Misleading-precedent** (an attack that resembles a routine, previously-suppressed pattern — the retrieval learner's blind spot).
3. **Signal-inversion** (a factor that normally means "safe" now means "hostile" — tests whether the geometry can re-weight).
4. **Regime-break** (a distribution shift across a category — feeds Recovery Half-Life, §B).
5. **Adversarial-context** (deliberately poisoned enrichment or feedback — tests the conservation gate + 20:1 asymmetry).

For each, the buyer sees: the decision, whether the system acted or abstained (referral VETO), the no-precedent surface (F19), and — over a run — the Recovery Half-Life. This is the falsifiable version of "act with confidence when there's no precedent," and it doubles as the second-meeting demo.

---

## §D — EXTEND §P4/§P5 (Positioning): the platform-absorption defense and the cross-stack gateway

All three runs put **SIEM/EDR platform absorption** as the killer objection (CrowdStrike/Palo Alto/Microsoft shipping "good enough" native triage free in-console). Add the defense as a first-class positioning line (v1.2 already positions above the platforms; this names the objection and the moat):

- **The category is the cross-stack judgment gateway.** The platforms will lock any centroid-geometry judgment layer to *their own* data lake. CI's defensibility is neutrality: it compounds the firm's verified-decision judgment across CrowdStrike **and** Sentinel **and** Okta **and** Splunk simultaneously — decisions that span systems no single platform owns. A fast-follower must rebuild non-parametric metric learning over *open* graph topologies (not fine-tune prompts in one lake) **and** the judgment graph is the customer's, not theirs.
- **Answer the price-to-zero move directly.** When Security Copilot is bundled into E5-adjacent licensing at near-zero marginal price, the answer is not "we're a better copilot" — it's the layer answer plus the economics: a bundled per-seat copilot doesn't displace the **MDR/MSSP + SIEM-ingest** budget line (v1.2 §P6), and it can't show the customer's own compounding curve.
- **Write-back boundary = SOAR-first (liability).** Safe surface = scored decision + inspectable evidence into the SIEM/SOAR/ITSM queue; autonomous EDR host-isolation stays human-approved by default; shadow mode governs activation. (Founder decision, §F.)

---

## §E — NEW under §P6/§P7: engineer the crossover to land INSIDE the pilot window (the survival move)

A shadow-only pilot adds review structure before the frozen twin has diverged — the trough where pilots die. A Learning Control Room that honestly reports "no measurable lift yet" in month two of a 90-day pilot loses the account. Pull the crossover forward with levers already in the build:
- **Pre-seed with enriched μ₀** — CLAIM-62's +42.69pp Day-1 lift is exactly this: day-one competence, not a cold start (also the cold-start answer, §F22).
- **Start auto-approve on the single safest category** (`cloud_infrastructure` clears conservation fastest; hold `insider_threat` near-zero by design), not across all six.
- **Size the pilot** to clear the crossover with margin, and pre-agree the conversion threshold before day 1 (v1.2 §P6 pilot-as-measurement).

This makes F18's frozen-twin curve a product that *wins* rather than one that documents a loss. **Verify-in-code:** crossover reachability on the pilot's real volume.

---

## §F — NEW under §P7: open decisions the founder must make (don't silently resolve)

Add to the roadmap's open-questions: (1) **write-back boundary** — scored decision into the SOAR/ITSM queue (ship now) vs autonomous EDR host-isolation (roadmap + liability) → recommend SOAR-first; (2) **pilot sequencing** — lead with credential/cloud false-positive suppression for hard ROI, use Stryker for the executive demo (all three runs converge); (3) **competitor naming** — architectural contrast in public, names in private enablement/diligence (v1.2 §P4.4, restated as a standing GTM rule); (4) **pricing basis** — per-SOC-team anchored to displaced MDR/MSSP + SIEM-ingest spend, not per-seat or per-alert.

---

*Applies `soc_review_consolidation_v1` (three-run: GPT/Opus/Gemini) as the enhancement layer on `soc_copilot_product_definition_v1_2.md`, rendering primitives from `soc_copilot_design_v5_8.md` (§11.5, §21, §22, §23, §28). Companion: `demo_scenarios_soc_additions_v1.md`. New surfaces F16–F22 continue the engineering doc's F-series. Verify-in-code items: Learning Control Room render-from-existing-endpoints; frozen-twin two-arm feasibility; crossover reachability on pilot volume. All numbers MEASURED-synthetic until the first-customer pilot curve (v1.2 §P0.4).*
