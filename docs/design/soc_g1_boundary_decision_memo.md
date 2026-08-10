# Decision Memo — SOC-G1-BOUNDARY: Live-Action Exploration Override
**Date:** 2026-08-08 · **Type:** founder decision + Phase-A design gate · **Blocks:** WP-0 of the RL consolidation package
**Audience:** founder (decision) + coding session / Codex (design verification & implementation of the chosen option)
**Status:** OPEN — recommendation below; awaiting founder sign-off before WP-0.

> **Governing principle for this decision (and the platform generally):** decide on **product value for the customer first.** The recommendation below (Option A) is chosen because it is the **better product** — better live decisions, more trust, more auditable, more architecturally coherent. That it also makes a marketing claim true again is a *consequence* of building the safer, more valuable product, not the reason for it. The direction of causation matters: build the better product, and the honest claim follows.

---

## 0. Context (self-contained — for a reader with no prior thread)

**The product.** "Compounding Intelligence" is a platform of five domain copilots (SOC/security, S2P/procurement, Trading, Purchasing, DataOps) on one shared engine. Each copilot *decides* (recommends an action per case) and *learns* from verified outcomes. Two subsystems, deliberately separate: the **judgment core / scorer** (chooses the action via nearest-centroid distance + softmax, `graph-attention-engine-v50/gae/profile_scorer.py:408-496`) and the **RL/evolution machinery** (explores variants, gates promotions).

**G1 — the guarantee at issue.** One of four product guarantees: *"The DECISION (which action a copilot recommends) is centroid-based, not reward-maximizing."* Reward/RL is supposed to live only in the *learning* path and the *evolution* loop — never in action selection. G1 is both a **market claim** (the central differentiator in the pitch, blog addendum, and outreach math section) and, more fundamentally, a **product property**: a governed copilot returns its best learned judgment, not an experiment, on a live decision.

**The SOC RL engine.** SOC (uniquely) runs a standalone RL engine (`rl_engine.py`) providing reward/exploration/credit, invoked from the decision path in `triage.py` (`:684-687, 1940-1942, 2028-2032`). Exploration intensity is gated by a `headroom_ratio` from `LearningHealthMonitor` (`learning_health.py:215-249`). A prior verification pass flagged SOC as the one place a live RL component touches decisions; this memo is the result.

---

## 1. The finding (verified by the coding session, 2026-08-08)
**SOC's RL exploration CAN overwrite the centroid-selected action on a live decision.** At `triage.py:700-703`, when **both** `RL_EXPLORATION_ENABLED == True` **and** SOC learning is enabled (**now default ON**), the exploration policy's proposed action **replaces** `selected_action` (`:701`).

Flow: (1) centroid scorer picks the action; (2) the exploration policy proposes an alternative — conservation-bounded, using `headroom_ratio`; (3) if exploration fired **and** learning enabled → `selected_action = explored_action`; (4) tagged `decision_method = "gae_scoring_explored"` (auditable).

**Mitigating factors (real but partial):** conservation-bounded (suppressed under AMBER/RED); dual-gated (needs `RL_EXPLORATION_ENABLED` + learning on); auditable (`decision_method`); proposal-only when learning is disabled (`:704-705`).

## 2. G1 impact
When exploration fires the action returned is **not** the centroid one, so **G1 is technically false for SOC in that state.** Nuances: the explored action is Thompson/UCB sampling bounded by conservation — **not** reward-maximizing — so the pitch's *spirit* survives, its *letter* does not; and the gate is a **global** `headroom_ratio`, **not per-decision stakes**, so nothing stops an exploratory non-best action on a high-severity alert.

## 3. Options
| Option | Design | Product-safety | Claim | Cost |
|---|---|---|---|---|
| **A — strict** | Disable the override (`:701`); exploration becomes a proposal/learning signal only; `selected_action` is always the centroid action. | Best. | Strongest, true. | Simplest code; *apparent* learning-speed cost (§4). |
| **B — refine G1** | Keep the override; redefine G1 as "centroid baseline; conservation-bounded exploration may override within the envelope." | Live experimentation persists, unstakes-gated. | Weaker; matches code. | Large downstream rewrite of pitch/blog/outreach. |
| **C — prod flag off** | Keep code; `RL_EXPLORATION_ENABLED = False` in production; exploration only in research/eval. | Safe in prod. | Holds in prod. | Trivial; interim. |

## 4. PRODUCT-VALUE ASSESSMENT (the primary lens — decide here first)
Set the pitch aside; evaluate on the customer alone. **Even then, A is the better product in security.**

**(1) Decision quality actually delivered.** Under B, on some fraction of live alerts the copilot **deliberately returns a non-best-judged action to gather information** — by its own judgment, the customer gets a worse triage on those alerts. Under A, every live decision is the best available judgment. A doesn't just protect a claim; it **strictly improves the decisions the customer receives.** In security, a deliberately-suboptimal action on a maybe-breach is not a rounding error.

**(2) Trust → deployment depth → compounding duration (the sharpest point).** The governed-compounding thesis only pays off if the customer keeps the system **in the loop on real decisions over time**; trust is the binding constraint on that duration. A security team that knows "it always gives its best judgment and experiments only in shadow" deploys it in the loop. A team that learns "it experiments on my live alerts" keeps it advisory, restricts it, or doesn't renew — and a system parked in shadow **compounds nothing.** So B *appears* to help the moat (faster per-decision learning) while actually **threatening the trust that lets the loop run at all.** A protects the exact condition the moat depends on.

**(3) Determinism & auditability.** A makes the decision path certifiable to a CISO/regulator — "the recommended action is always the best-scored one." B is something you must defend.

**(4) Architectural coherence.** Under A, exploration becomes a *proposal that must earn adoption through the same promotion gate* that governs everything else. B leaves a **second, ungated path that bypasses the very gate that IS the safety story** — a governance hole in the controller. A closes it.

**The honest cost of A (there is one).** The genuine case for live exploration is **action-dependent (true bandit) feedback**: for decisions where the outcome you observe depends on the action you took, you can only learn the explored action's value by taking it (why recommenders/ads explore live). If SOC has such decisions (e.g., dismiss an alert → never investigate → never learn it was a true positive), A forgoes that signal. **Two things blunt it, security-specifically:** most alert ground truth is **action-independent** (a threat is a threat whether or not you escalated) → the explored action can be scored **counterfactually against ground truth without ever being taken** (Codex to verify the signal exists); and for the residual action-dependent cases, the right fix is **deliberate, controlled investigation of a sample**, not silently handing the customer a worse live action.

**Net:** A enhances real product value — decisions delivered, trust, adoption depth, auditability, coherence — at the cost of a narrow, security-favorable, largely-recoverable slice of learning. B's advantage is mostly **narrative** value delivered through the pitch, bought by spending live decision quality and trust. That is the wrong trade.

## 5. The value-ENHANCING reframe (turn the finding into a feature, not just a fix)
The best answer isn't "A everywhere, forever." It is to make live-vs-shadow exploration a **governed, per-domain, stakes-aware policy**:
- **High-stakes / irreversible domains (security, and similar) default to shadow-only** exploration.
- A **low-stakes, action-dependent-feedback** domain could *opt into* **stakes-gated live exploration** (never on high-severity/irreversible actions), where the economics favor it.
- The boundary is **visible to and set by the customer.**

This reframes the finding from "a bug to disable" into an **explore/exploit policy surface** — and *governed* explore/exploit, where the enterprise can see and control the line, is itself a **feature customers pay for.** This is the version where product value is **unambiguously enhanced**: you are not removing a capability, you are putting it under the same governance as everything else. It also makes the pitch story stronger and *true*: "the system explores to learn — under a governance policy you control, and never on your high-stakes live decisions."

## 6. Recommendation: **A, reached via C now — extended to the governed policy of §5**
- **Immediately (C):** set `RL_EXPLORATION_ENABLED = False` in production. G1 true today, zero cost, closes the safety exposure.
- **Permanently (A):** relocate exploration from the decision path to the learning path — it *proposes*, the live decision stays centroid, proposals are shadow-evaluated and adopted only through the promotion gate.
- **As the product matures (§5):** expose live-vs-shadow exploration as a **governed, per-domain, stakes-aware policy** — shadow-only for security by default; opt-in stakes-gated live exploration where it adds value, always customer-visible.
- **Not B:** to a CISO, "AI experiments on my live alerts" is alarming, not sophisticated; to a diligence VC, B re-opens the exact reward-maximizer objection the centroid story closes. B doesn't weaken the shipped claim; it **inverts it into the objection** — trading credibility with the buyers who decide for approval from the one who doesn't.

## 7. Codex design-verification tasks (before/at WP-0)
Produce `docs/design/soc_g1_boundary_verification.md` answering, with `file:line`:
1. **Confirm the override** at `triage.py:700-705`; confirm `selected_action = explored_action` only under `RL_EXPLORATION_ENABLED && learning_enabled`; confirm `decision_method` tagging.
2. **Confirm the flag path (C):** `RL_EXPLORATION_ENABLED` fully gates the override, no second override path; where prod config sets it.
3. **Sweep all five copilots:** does any other copilot let exploration override the live action, or is this SOC-only? `file:line` or "SOC-only."
4. **Confirm A is complete:** enumerate every site where an explored/RL-proposed action can reach `selected_action`; confirm disabling the override + routing the proposal to learning/shadow leaves the centroid action authoritative everywhere.
5. **Confirm the counterfactual-learning premise (drives the §4 cost):** is there a verified ground-truth signal per SOC decision **independent of the action taken**, so the explored action can be scored without being taken? Cite the source; if yes, A's learning cost ≈ nil; if no, quantify the loss.
6. **Assess the §5 policy surface:** what would a per-domain, stakes-aware exploration policy require (a per-decision stakes/severity signal to gate live exploration; a customer-facing policy config)? Identify the seams; flag effort. (Design only — not necessarily WP-0 scope.)
7. **Define the code + config change** for A/C (the one-line prod flag; the override-removal + proposal/shadow routing).
8. **Specify the SOC-specific G1 test (extend T-G1):** with prod config, `decision_method` is **never** `"gae_scoring_explored"` on a live decision; and swapping SOC's rl_engine reward/exploration config leaves the recommended action + probabilities unchanged for a fixed input. Real SOC ProfileScorer/CompoundingScorer path, no mock.

## 8. If the founder chooses B instead (impact to flag)
B requires rewriting the G1 claim wherever it appears — `vc_pitch_3min_script.md`, `ci_blog_v16_addendum.md`, `outreach_math_formalism_addendum.md` — from "the decision is centroid-based" to "centroid baseline with conservation-bounded exploration that may override within the safety envelope." Do **not** ship B silently against the current claim text; code and artifacts would then disagree, which is exactly what a diligence read catches. And note: on the §4 product-value axes, B remains the weaker product regardless of how the claim is worded.

## 9. How this gates the work package
Phase-A gate resolved **before WP-0** of `rl_consolidation_work_package.md`. On A/C: WP-5's T-G1 becomes a true invariant test across all five, and the pitch/blog/outreach need no change. On B: update those artifacts first; WP-5's T-G1 becomes an audit-of-`decision_method` test. Either way, the §5 governed-policy direction is the value-enhancing target the roadmap should carry forward.
