# VLD Pre-Paper v8 → v9 — Prioritized Fix-List + Two Draft-In Blocks

From the four-part review of `ci_vld_architecture_prepaper_v8.md`. Two parts: (A) a P0/P1/P2 fix-list to
hand to the v9 editor; (B) two drop-in blocks (the §10.4 tiering fix and the new §8.x competitor block).

---

## A. Prioritized fix-list

### P0 — must fix before v9 ships (correctness of *claims*, not of the work)

- **P0-1 — The §10.4 K-curve placeholder is cited as delivered evidence.** §0.10, §5.5, and §12.2 lean on
  §10.4 ("provides this evidence"), but §10.4 is `[PLACEHOLDER]`. The L3 / effective-recursion claim's
  *production* leg is not run. **Fix:** everywhere, state "L3 mechanism validated in **simulation** (§9.9,
  +25%); production-geometry effective-recursion curve **pending** (§10.4)." Delete "provides this
  evidence" in §5.5. *(Draft language in Part B.1.)* **This is the RSI claim — highest priority.**
- **P0-2 — "L1–L3 with production evidence" overstates L3 (§0.10).** L1–L2 have integration evidence (31
  tests); L3's evidence is simulation. **Fix:** per-level tiers — "L1–L2 production/integration-validated;
  L3 simulation-demonstrated, production-pending." (Same root as P0-1; fix together.)
- **P0-3 — Constructed-hard-tail caveat must ride inline with 57:0 / +22.8% / SP=0.100.** Astra (§10.2)
  and the sim mix (§10.2.1) are *built/selected* surface-wrong; these are **not** natural-prevalence
  uplift. **Fix:** append inline at every occurrence (abstract, §0.9-C3, §10.2): *"on constructed
  hard-tail scenarios; natural-prevalence uplift unmeasured (§12.1)."*
- **P0-4 — Add + distinguish the 2025–26 adaptive-retrieval competitors.** §8 misses the papers a reviewer
  will cite as prior art against C3/C6. **Fix:** add §8.x (Part B.2) and re-anchor C3/C6 on the
  substrate, not the mechanism.

### P1 — should fix (reviewer will attack these)

- **P1-1 — Reconcile headline numbers.** VLD 0.872/0.878/0.896; exhaustive 0.912/0.926/0.938; random
  0.748/0.780/0.796; and "85% of exhaustive" (§0.9-C1) vs 0.872/0.912 = **95.6%**. **Fix:** pick one
  canonical round (v6/v8) for abstract/§0 headlines; label all others "round vN, seed set X." Correct the
  85%↔95.6% contradiction in C1.
- **P1-2 — Re-anchor C6 (and C3) from mechanism to substrate.** "Only reasoning compounds / traversal is
  decision-conditioned" is a mechanism claim others also make. **Fix:** the un-copyable part is "the
  traversal priorities *are* the firm's compounding, verified-outcome judgment, governed by conservation"
  — not "traversal is adaptive." (Pairs with P0-4.)
- **P1-3 — §10.3 ρ-evaluator table needs a legend or cut.** As printed (ρ=0.50 control ❌ 0.900/1.000, no
  legend) it reads like a leakage/over-fit alarm. **Fix:** add legend + pass/fail semantics, or remove.
- **P1-4 — Scope the "ties the oracle" result to its headlines.** VLD ties the informative-dim oracle
  overall (0.872 vs 0.872); it dominates only S2/conditional. §0.9/abstract must not imply VLD beats
  oracle routing broadly.
- **P1-5 — Make C5's "prerequisite, not multiplier" framing govern the headline.** §8.5-C5 is honest
  (subadditive in fresh data); §0.9-C3/abstract still read as compounding *value*. Reconcile to the
  prerequisite framing.
- **P1-6 — Badge the S2P-SC2 "learned-K flips the decision" demo (§0.10, §11) as a PLANTED FIXTURE.**
  It's a designed mechanism demonstration, not a measured production event; your own VLD Guards require the
  badge.

### P2 — polish (credibility, cheap)

- **P2-1 — Faithful embedding baseline.** Replace/supplement the "centroid-mean distance (simplified
  proxy)" so "+0.078 vs embedding routing" isn't beating a proxy. Cheap: sentence-embedding over node
  text → cosine. *(Or stop letting +0.078 stand in for "beats embedding retrieval" in headlines.)*
- **P2-2 — Demote γ_total ≈ 1.28 (§5.4) out of any summary.** It's MODELED × unvalidated under an
  independence assumption §5.3 already falsifies. Keep in §5.4 with caveat; don't let it travel.
- **P2-3 — Appendix B tier nits.** INTERACTION "+0.053" → "+0.053 (stable-distribution only); ≈0
  fresh-data" (matches §9.6-H5). GAMMA: split theorem (MODELED) from ε_firm★≈0.125 (sim-tier).
- **P2-4 — Compress the Duan/EVOMAL challenge→answer mapping (§8.5)** to one sentence each for Challenges
  2 and 3 (Challenge 1 already done in §1.4).
- **P2-5 — Verify the companion-survey cite** (arXiv:2607.07663, "1,250 papers") — load-bearing and
  checkable.

---

## B. Two drop-in blocks

### B.1 — §10.4 tiering fix (replace the placeholder framing; make L3 airtight)

**Replace §10.4's `[PLACEHOLDER]` header and the §5.5 "provides this evidence" sentence with the
following, and mirror the status line in §0.10.**

> **§10.4 K-Utility Learning Curve on Production Geometry — STATUS: PENDING (protocol frozen).**
> Effective recursion (Duan et al., §2.2.2) requires a *measured* curve: decisions routed with K from
> round N must be measurably better than K from round 0, at matched budget. **This experiment is
> specified and its protocol frozen, but not yet run on production centroids; the L3 effective-recursion
> claim is therefore demonstrated in *simulation* (§9.9: +25% routing quality over 30 epochs) and remains
> *production-pending* here.** We state the L3 tier accordingly throughout: L1–L2 are
> integration-validated (31 tests, real scorer geometry + evidence providers); L3 is
> **simulation-demonstrated, production-pending.**
> *Protocol (frozen):* 500 synthetic decisions on DataOps production centroids (`real_centroids_v1.json`),
> K init uniform 0.5, updated per verified decision via `KUtilityStore`; 10 checkpoints (every 50
> decisions) evaluated on the frozen Astra 50-scenario suite; no-learning control (K fixed at 0.5) over
> the same 500 decisions. *Pre-registered outcome (from §9.9 simulation): +20–30% routing quality by
> decision 500.* Charts to be populated on run: `pub_k_learning_routing.png`, `pub_k_learning_accuracy.png`,
> `pub_k_heatmap_evolution.png`, `pub_k_convergence.png`.

**Companion edit — §5.5, replace:** "The K learning curve experiment (§10.4) provides this evidence: over
500 decisions, routing quality improves from ~30% to ~40%…"
**with:** "Effective recursion is demonstrated in simulation (§9.9: routing quality 30%→37.5% over 30
epochs). The production-geometry curve that would establish it on real centroids is specified but pending
(§10.4); until it runs, CI's effective-recursion claim is simulation-tier. Structural recursion (K
persists, accumulates from verified outcomes, changes future Q) is demonstrated; effective recursion —
that the persistence *helps* at matched budget — is simulation-demonstrated, production-pending."

**Companion edit — §0.10 (L3 paragraph), replace** "Routing quality improves from 30% to 37.5% (+25%).
This is not prompt tuning…" **with** "Routing quality improves from 30% to 37.5% (+25%) *in simulation
over 30 epochs (§9.9)*; the production-geometry curve is pending (§10.4). This is not prompt tuning or
model fine-tuning — it is the scoring geometry learning which graph edges are worth traversing —
demonstrated in simulation and specified for production validation."

### B.2 — New §8.x related-work block (close the 2025–26 competitor gap)

**Insert after §8.1 (Active Feature Acquisition), before §8.2.**

> **§8.1a Uncertainty-Conditioned Adaptive Retrieval and Reasoning (2025–2026).**
> A fast-moving line conditions *when* and *what* to retrieve on a model's own uncertainty — the same
> intuition VLD applies. Interpretable-uncertainty adaptive retrieval (arXiv:2607.07380, 2026)
> distinguishes knowledge insufficiency from ambiguity/conflict from model internals in a single forward
> pass, to trigger retrieval versus further reasoning. Step-level uncertainty timing ("When to Retrieve
> During Reasoning," SIGIR '26) decides *when* to retrieve during a reasoning chain without RL
> fine-tuning. Learning-to-Measure (L2M, arXiv:2510.12624, 2025) is an in-context, uncertainty-guided
> feature-acquisition agent maximizing conditional mutual information with no per-task retraining.
> Adaptive-RAG and self-knowledge-based retrieval (ACL 2025) select retrieval depth from query difficulty.
>
> VLD shares the *core intuition* (uncertainty-conditioned acquisition) with this line and does **not**
> claim novelty on the mechanism. The distinction is the **substrate**, on four axes none of these
> systems combine: (1) **no LLM in the loop** — routing is a closed-form read off a prototype scorer's
> geometry (σ, μ), sub-millisecond per hop, versus per-hop LLM/forward-pass cost; (2) **enterprise
> decisions, not QA** — the target is a verified action (approve/escalate/hold), not a retrieved answer;
> (3) **the acquisition function reuses the production scorer's parameters** with no separately trained
> router (versus L2M's learned acquisition agent or a fine-tuned uncertainty head); and (4) **the
> investigation feeds verified-outcome centroid learning**, so *what to investigate compounds* and is
> governed by a conservation gate — none of the above systems couple acquisition to a compounding,
> outcome-grounded judgment store. In short: the mechanism is shared and commoditizing; the contribution
> is composing it on a governed, compounding decision substrate. Where these systems make retrieval
> adaptive, VLD makes it *the firm's accumulating judgment* — which is why (C6) only the reasoning
> substrate, not the retrieval mechanism, compounds.

**Companion edit — C3 and C6 (Contributions), append the substrate re-anchor:**
- **C3 add:** "The novelty is not state-dependent retrieval per se (cf. §8.1a; step-level adaptive
  retrieval is established 2025–26) but that recomputation runs on a *prototype scorer's geometry with no
  LLM*, at matrix-vector cost."
- **C6 add:** "The compounding claim rests on the substrate, not the traversal: the traversal priorities
  *are* the firm's verified-outcome judgment (centroids μ, precision σ), so what compounds is the judgment
  the traversal reads from — a property adaptive-retrieval mechanisms (§8.1a) do not have, because their
  retrieval policy is not an outcome-grounded, conservation-governed decision geometry."
