# S2P — Review Consolidation (Judge Runs) v3 (supersedes v1, v2)
*Zip/bundle filename: `s2p_review_consolidation_v1.md` — the S2P member of the per-copilot consolidation family (trading / dataops / purchasing / s2p). Internal version is v3.*
*Consolidates the three LLM-judge runs of `s2p_market_winner_prompt_v3` — **Opus**, **GPT**, **Gemini** — read as one judgment, not a vote.*

> **v3 update.** Reviewed and grounded against the actual Drive design-folder docs (`s2p_copilot_unified_v1_3.md` and `demo_scenarios_and_usecases_v2_5.md`), read in full. All v2 decisions survive the read; §7 records what the read added and where each decision lands in the real doc structure. The two addenda (`s2p_copilot_doc_additions_v1`, `demo_scenarios_s2p_additions_v1`) are the executable form of this consolidation.
>
> **Correction vs v1.** v1 mislabeled its sources: it treated the Opus run as a generic "product-surface review," inserted my own advisor synthesis as a co-equal third source, and predated the Gemini run. This is the clean three-run consolidation. Convergence across the three *independent* models is the strongest signal; my advisor overlay (§5) is marked separately and is **not** a fourth vote. (GPT = the "Overall assessment" run by elimination — flag if mis-attributed.)

---

## 0. The three runs, characterized (they came at the product from different angles — that's why the overlap matters)

- **Opus — product-first.** Converts the architecture into buyer-visible surfaces (Tier 1/2/3). Strongest on the build list; explicitly names the through-line: *"the gap isn't the argument — the four capabilities are real in code and invisible in the product."*
- **GPT — positioning-first.** *"Make the product story radically simpler than the architecture."* Lead with one purchaseable outcome, re-rank the axes by market role, and fix the prompt's own persuasiveness. Strongest on market architecture.
- **Gemini — prompt-execution.** Ran the return format literally (wedge · per-axis · stack-fit · scenario cards · moat table · ranked risks · D-null/D-ext). Strongest on the stack-fit spec and concrete artifacts — **but it committed, in its own scenario cards, the synthetic-vs-measured sin it correctly names as risk #1** (fabricated specifics). Harvest the structure; quarantine the invented numbers (§4).

---

## 1. Where all three converge — do these (strongest signal)

- **Cut / defer the 8-domain risk cockpit.** Opus (Tier 3, "the scope call I'd push hardest on"); GPT (§7, don't launch as a second story); Gemini (§8, "lead 100% with the 7-factor pilot; keep the cockpit as vision roadmap"). **Unanimous.**
- **Frozen twin as the proof mechanism.** Opus (Tier 1, shipped artifact — converts CLAIM-59/62 synthetic→measured by day 90); GPT (P0, frozen-twin measurement built into pilot/runtime); Gemini (Axis 2 buyer-verification bar = "the Frozen-Twin Control Experiment"). **Unanimous.**
- **Make the loop a visible ledger/object, not an architectural property.** Opus (decision-change proposal as a first-class object + transferred-improvement ledger + abstain-economics ROI ledger); GPT (P0 Autonomy/Compounding Ledger + decision-class promotion workflow + Discover→Shadow→Promote→Measure→Keep/Rollback→Transfer); Gemini (Process-Mutation Ledger + Edit-Retention Dashboard). **All three, independently.**
- **Synthetic-vs-measured is the #1 risk; defuse it with a historical-data audit on the customer's own ERP logs.** Gemini names it explicitly (HIGHEST RISK) and proposes a *"free 30-day historical-data audit that computes their actual compounding curve from their own ERP logs"*; Opus reaches the same place via the frozen twin; GPT via the honesty discipline. **Convergent** — and the historical-audit framing is the sharpest expression.
- **Pricing anchored to decisions-under-management / recovered value, not per-seat.** Gemini explicit (§3.6); Opus (Tier 3 commercial); GPT (roadmap/packaging). **Convergent.**
- **Consume-don't-compete via MCP; Celonis as substrate, not foil.** Gemini (full stack-fit spec, MCP client *and* server exposing learned trust scores back); GPT (§10 stack slot); Opus (product-focused, consistent by implication). **Convergent, no dissent.**

---

## 2. Where two of three converge (strong — dissent noted and resolved)

- **Time-moat + judgment-memory portability.** Opus (Tier 3: commit to JM export; *"you can't copy your graph" is your moat line and your lock-in problem in a procurement room*) + GPT (§6: a *time* moat, not a feature moat — customer-specific verified judgment they can't retroactively manufacture). Gemini leans on "private verified-decision graph" and is silent on the lock-in reframe. **Resolve toward Opus/GPT:** portability *strengthens* the moat (the moat is accumulation over months, not the file).
- **Re-rank the axes: Axis 3 differentiator, Axis 2 proof.** GPT (explicit market-role table) + Opus (leads Tier 2 with Axis 3's transferred-improvement ledger; treats the twin/Axis 2 as proof). Gemini kept four co-equal axes — **but it ran on v3, which predates the re-rank**, so this is not a real dissent, just an artifact of prompt version.
- **Narrow the scenario spine.** Opus (explicit: S14 / S2 / S15 / S9 / S16 + one number) + GPT (via the four-beat story and "the buyer misses the one they should buy first"). Gemini *added* five cards instead of narrowing — but its **Card 5 (key-person / retired-buyer judgment retention)** is a genuine add worth keeping as roadmap depth (maps to S6).
- **Counterfactual "what would change my mind."** GPT (§9, falsifiability-not-explanation) + Gemini (Axis 1: inspectable, falsifiable evidence chain; "Falsifiable Evidence Graph Widget"). Opus's confidence panel is adjacent. **Convergent.**

---

## 3. Single-run gems worth keeping

**Opus only:**
- **Fix the score-path stall before S2P is the live demo** — pool-exhaustion/warm-fallback is production-real; one 30s freeze in front of a CPO costs more than any positioning gain; the fail-closed bounded timeout is the highest value-per-effort item. *(No other run touches operational demo-risk.)*
- **Day-0 readiness assessment that leads with what you *can't* trust** — nobody else leads there; converts a paid discovery into the pilot.
- **Abstain-economics as the crossover, told in the customer's P&L** — review-hours added, dollars recovered, crossover point, weekly.

**GPT only:**
- The **four-beat market architecture** (problem / product / compounding / moat) and the one-sentence category story.
- The **axis market-role table** (lead / differentiator / proof / expansion).
- **"Second-derivative RL" → "learning velocity"** in external copy (keep the second-order model for technical-diligence rooms); **drop the n(n−1)/2** super-linearity claim (describes possible pairwise relationships, not value).
- The **prompt-is-too-persuasive** critique → the v4 changes (§6 below).
- *"Stop automating workflows. Start eliminating exceptions."*

**Gemini only (harvest):**
- **Cross-system *neutrality* as the anti-commoditization defusal:** *"SAP Joule will never optimize a Coupa→Celonis cross-system workflow."* The right answer to "a hyperscaler clones judgment memory inside its own walls" — the moat is neutrality across the stack, which a suite vendor structurally can't match.
- **Card 5 — key-person / institutional-memory retention** (concrete CPO scenario; keep for roadmap depth).
- The explicit **genuine-moat-vs-now-table-stakes table** (clean two-column framing the prompt asked for).
- **D-null** (mid-market <500 invoices/month lacks the complexity for compounding to show value — lead with OCR/three-way-match or pass) and **D-ext** (supplier-negotiation playbook agent; CBAM/carbon compliance gate).

---

## 4. Gemini — QUARANTINE (must not propagate into the consolidation, decks, or v4)

- **Fabricated specifics presented as if measured:** "$42,100 on copper cabling," "avoiding $180K in air-freight," "84% insolvency risk," "1,200 zero-defect transactions," **"N₁=45 → N₆=8 decisions."** The last *contradicts* the canonical CLAIM-59 (54.4% fewer decisions) and GPT's illustrative figure (**supplier #6 = 40 verified decisions vs #1 = 120**) — **three different numbers now circulate for one claim.** Canonicalize on GPT's 40-vs-120 as the single illustrative figure, tag it MODELED, and never let a fabricated dollar figure read as a realized outcome. This is the exact risk #1 the run itself names — it violated its own top guard.
- **Competitor-behavior overclaims:** "SAP Joule flags all price variances >2% indiscriminately"; "Coupa Navi requires manual re-configuration following macro breaks." Unsupported claims about tools the buyer may own — a Coupa-aware buyer disputes the second on sight. Strip to the structural layer-delta (they don't compound firm-specific judgment); never characterize what the incumbent does *badly*.
- **Tier-2-insolvency-from-invoice-format mechanism:** speculative, carries defamation exposure (Gemini flags this itself), and *amplifies the very cockpit we're cutting*. Pull back to "risk as better evidence for today's invoice decision."
- **Buyer-language leaks:** "centroid geometry" and "α·q·V ≥ θ_min" drifting toward buyer-adjacent surfaces; the CPO line with "GTM scale" in the buyer's mouth (that's the founder's concern). Scrub.

---

## 5. Advisor overlay (mine — not a fourth vote; the three runs under-weight these)

- **★ Engineer the crossover to land *inside* the pilot window.** Under 5:1, day one adds review load while the twin hasn't diverged — the trough where pilots die. Pull crossover forward: pre-seed judgment memory with domain priors (what the +42.69pp enriched-μ₀ result buys), start auto-approve on the single safest category, size the pilot to clear crossover with margin. This makes the ledger a product that *wins*, not one that documents a loss. **Co-critical with the ledger itself** — and none of the three runs has it.
- **Views on one object.** The decision-change proposal is the base build; every ledger (autonomy, abstain-economics, transferred-improvement, process-mutation) is a *rendering* of it; the promotion workflow is its *lifecycle*. Build the object once — it sequences first.
- **Day-0 readiness can't use *learned* factor-trust weights** (those need accumulated decisions). Build it on the enrichment layer available at day zero: source coverage, completeness, provenance, trust tiers.
- **Score-path structural fix = atomic score-write = the same work already in the calibration commit,** same lock region — sequence them together, and stage the live demo single-worker with the pool pre-warmed.
- **Cockpit: separate the *positioning* cut (do now) from the *code* decision** — the build may already sit on the (5,5,8) tensor with an 8th factor wired; keeping it as a quiet enrichment input is harmless. Verify before ripping.

---

## 6. Net direction, prompt→v4, and sequence

**The through-line all three share:** the architecture is ambitious enough; make the product story radically simpler than it, and turn the four real-in-code capabilities into surfaces a buyer can look at. Collapse to **one outcome** (Earned Autonomy for S2P / Compounding Judgment platform), **one number** (auto-approve coverage growing safely, week over week), **one object** (the decision-change proposal), **one proof** (the frozen twin).

**Prompt → v4** (GPT's critique + my own ready-review flag):
1. Insert an adversarial **falsification pass before sharpening** ("assume the four-axis thesis may be wrong; which axes are differentiated vs implementation-detail vs incumbent-replicable vs insufficient-evidence; is a simpler wedge a stronger company — only then sharpen").
2. Split **"nothing removed"** → product-preservation (keep scenarios/capabilities; extend/add — standing rule) vs positioning-preservation (judge may demote / hide / merge / **exclude** from the market story).
3. **"Why incumbents can't fast-follow" → "what makes the position structurally difficult or time-consuming to replicate"** (don't ask the judge to prove a negative).
4. Demote the axes to "architecture of the advantage"; reframe inversion #4 to **learning velocity**; drop **n(n−1)/2**.

**Sequence (dependency + goal):**
0. Score-path fail-closed + demo staging — unblocks any live S2P demo.
1. The decision-change object — the base everything renders from.
2. Autonomy Ledger + promotion workflow + frozen twin, **with the crossover engineered in** — survive + prove.
3. Day-0 readiness + derive-5:1 + historical-data audit — convert (and the synthetic→measured defusal).
4. Counterfactual inspector + confidence panel + rollback/degradation — trust/safety.
5. Positioning rewrite — v4 prompt + product/positioning docs: lead simple, re-rank axes, time moat + portability, stack slot ("learned decision system"), cross-system-neutrality defusal, cut the cockpit from the story, "learning velocity" not "second-derivative RL."
6. Risk-enrichment into current decisions + optimizer export — expand without diluting.

Portability = a commercial commitment (land it at MSA), independent of build order.

---

## 7. Source-doc reconciliation (v3 — after reading the actual Drive docs in full)

Reading `s2p_copilot_unified_v1_3.md` and `demo_scenarios_and_usecases_v2_5.md` end-to-end confirmed every v2 decision and surfaced three things worth pinning:

**7.1 — The product doc carries the retired teardown; the demo doc mostly doesn't.** `s2p_copilot_unified_v1_3.md` §PD4 still says verbatim *"Celonis = the mirror (shows WHERE). We = the brain + hands + memory"* and has a competitive-test row *"REASON… Rules | N/A | Rules | Context-graph reasoning."* Both are 2026-false and must be rewritten (handled in `s2p_copilot_doc_additions_v1` §A/§C). The **demo doc is already correct** on Celonis (§0.3 room 6 is consume-don't-compete; ENT-1 §4.8 already guards "which decision to change, not we execute in your ERP") — it needs only one fix: §2.5 SILENCE-2's *"every competitor auto-approves by rule"* overclaim (handled in `demo_scenarios_s2p_additions_v1` §S2P-FIX-1). So the "kill the teardown" work is real but asymmetric — heavy in the product doc, light in the demo doc.

**7.2 — The (5,5,7)-pilot vs (5,5,8)-cockpit split is confirmed *inside* the doc.** Part II ships the Invoice-Exception + Price-Leakage pilot at **(5,5,7)=175** (§PD6.3, and §PD11-M1 which specifies the migration (6,4,6)→(5,5,7)); Part I designs the 8-domain risk cockpit at **(5,5,8)**. This validates the v2 call to **separate the positioning cut from the code decision**: cutting the cockpit from the *story* (§PD1/§PD9) is safe and immediate; the *code* may sit on either shape and must be verified before any change. The 8th factor (`environmental_risk`) can stay as a quiet enrichment input regardless.

**7.3 — The demo doc's honesty rules already encode two of our recommendations.** F-25 forbids saying "RL" for the primary mechanism on stage (it's "decision-trace/prototype learning from verified decisions") — which *is* the "sell learning velocity, not second-derivative RL" recommendation, already enforced demo-side. And F-21/F-22 already require dollar figures to be labeled illustrative-not-measured — the synthetic-vs-measured guard, already enforced demo-side. So those two land as **product-doc** changes (§J of the copilot addendum), since the demo doc is already disciplined; the demo addendum only has to keep new beats inside the existing rules.

**7.4 — What each decision maps to, concretely:**
- Lead-simple / one-outcome-number-object-proof → copilot addendum **§0**; demo **L-S2P spine**.
- Axis re-rank + kill §PD4 teardown + stack slot → copilot **§C/§G**.
- Product surfaces (ledger, decision-change object, promotion workflow, frozen twin, counterfactual, confidence panel, day-0, cold-start) → copilot **§D/§E** (new F23–F31); demo **§S2P-NEW** (S2P-LEDGER/EXTINCT/TWIN/WHATIF/DAY0/CONFIDENCE).
- Time moat + portability → copilot **§F**. Cockpit cut → copilot **§H**. 5:1 + pricing → copilot **§I**. Learning-velocity + drop n(n−1)/2 → copilot **§J**. Score-path demo-risk → copilot **§K**. Cross-system neutrality → demo **§S2P-ROOM**.

**7.5 — Standing verify-in-code items (unchanged, now precise):** live tensor shape (§PD6.3/§PD11-M1 say (5,5,7); Part I says (5,5,8) — confirm what the build runs); crossover reachability on real pilot volume; score-path atomic-write status. None can be settled from the docs alone.

**Net:** v2's judgment holds without amendment; the read only sharpened *where* each change lands and revealed that the teardown-removal is concentrated in the product doc. The two addenda carry it all.
