# Demo Scenarios — S2P Additions & Corrections v1
*Surgical delta to `demo_scenarios_and_usecases_v2_5.md` (Drive id 18u2TolimTPk1B33ppNd640GuKuSMoLlf, design folder). Adds the product surfaces from `s2p_review_consolidation_v1` as demo beats, and corrects one stale competitive line. Same shape as the trading / dataops / purchasing demo addenda. **Every new beat carries a surface + API + class (LIVE/NEAR/ARCH) + DoD**, and obeys the doc's existing honesty rules: F-21/F-22 (dollar figures are illustrative preseed formats, never measured outcomes), **F-25 (the mechanism is decision-trace/prototype learning from verified decisions — never "RL" and never "second-derivative RL" on stage)**, F-26 (signals transfer; judgment geometry is per-copilot), F-27 (showing roadmap is fine; implying roadmap is LIVE is the violation).*

> **Good news from the read:** the demo doc is already **more current than the product doc** on Celonis — §0.3 room 6 is already consume-don't-compete ("keep it… your Celonis spend just became more valuable, not obsolete"), and ENT-1 (§4.8) already guards "which decision to change, **not** we execute it in your ERP." So the demo needs *additions*, plus **one** correction (§S2P-FIX-1) and one framing retune, not the wholesale §PD4 rewrite the product doc needs.

---

## §S2P-FIX-1 — correct the "every competitor runs rules" overclaim (§2.5 SILENCE 2)

§2.5 SILENCE 2's payoff line reads *"Every competitor auto-approves by rule. We reason from context."* In 2026 that's false as a generalization (Coupa Navi and SAP Joule reason). **Keep the §4.2.1 S14 rule-vs-reasoning contrast** — it is category-defining and *true for a threshold rule* — but retune the spoken generalization:
> *(new SILENCE-2 payoff)* "A **threshold rule** rejected this — 5.2% over a 5% line. The reasoning read the contract and the commodity index and accepted it, correctly. The point isn't that others lack agents; it's that a rule fires on a number, and judgment reasons about *why*."

Same fix applies to the §4.2.1 killer-detail line: keep *"rules don't read contracts"* (true of the threshold rule shown), drop any implication that competitors have no reasoning at all.

---

## §S2P-NEW — new S2P demo beats (add to §3 S2P catalog and the L-S2P cut in §7.2)

These make the moat **visible** — the gap the three judge runs all named. Each extends an existing shipped surface where possible.

**S2P-LEDGER — "Earned Autonomy, week over week"** *(the Autonomy/Compounding Ledger)*
| Field | Value |
|---|---|
| Surface | S2P **Performance** (new AutonomyLedger panel) — extends the COMP-1 / DI-TIMELINE pattern to S2P |
| API | `/api/s2p/iks`, `/api/s2p/conservation`, `/api/s2p/financial-impact` (shipped) + coverage-over-time series |
| Class | **LIVE** (single-arm coverage + IKS) → **NEAR** (two-arm vs frozen baseline, ties S2P-TWIN) |
| Audience sees | Auto-approve coverage climbing (e.g., Jan 18% → Feb 31% → Mar 46%), plus review-hours avoided, abstain rate, bad-auto-approval rate, new-category time-to-trust, promotions/rollbacks; under every expansion, a plain-language *why* |
| Spoken | "One number that matters: the share of exceptions it safely handles on its own — growing every week, and here's the proof under each step." |
| DoD · Honesty | Coverage series renders from preseed; **F-21/F-22** — dollar tags are illustrative, provenance-badged. **No "RL"** (F-25). |

**S2P-EXTINCT — "Every recurring exception is a candidate for extinction"** *(the promotion workflow)*
| Field | Value |
|---|---|
| Surface | S2P **Exception Triage** → PromotionLedger (extends F12 AgentEvolver surface) |
| API | `/api/s2p/interventions` / promotion-gate logs (same pattern as DM-1 Rejection Moment §4.1) |
| Class | **NEAR** |
| Audience sees | The lifecycle on one class: **Discover → Shadow → Promote → Measure → Keep/Rollback → Transfer.** "This quantity-mismatch class was consistently buyer-approved → shadow → counterfactual → promoted day 34 → monitored → transferred to a second plant." |
| Spoken | "It doesn't just resolve exceptions — it makes classes of them *stop being exceptions*, one governed promotion at a time, and carries the win to the next plant." |
| DoD · Honesty | Reuses existing promotion/rejection logs — surfacing task, no new gate logic. Transfer = **signal/pattern transfer**, not shared judgment geometry (F-26). |

**S2P-TWIN — "The version we froze in March"** *(frozen-twin control)*
| Field | Value |
|---|---|
| Surface | S2P **Performance** (curve overlay: live vs frozen-at-day-1) — extends COMP-1 two-arm / DIFF-1 (§4.10) |
| API | frozen-baseline arm (APP-1/APP-4 pattern) over `/api/s2p/*` |
| Class | **NEAR** |
| Audience sees | Two curves on the customer's own data — a twin pinned at day-one config vs the live system — the live one pulling away; the gap is the compounding, in review-hours and dollars |
| Spoken | "A version of this we froze on day one is still running beside it. The distance between the two lines is the thing you're buying — measured on *your* decisions, not asserted." |
| DoD · Honesty | This is the artifact that converts CLAIM-59/62 from synthetic to **measured**; until it has run on real data, label the divergence **MODELED/PILOT-TARGET** (F-27). |

**S2P-WHATIF — "What would change this decision?"** *(counterfactual inspector)*
| Field | Value |
|---|---|
| Surface | S2P **Exception Triage** → SituationPanel, adds a "what would flip it" block — extends CF-1 (§4.2) / E2 |
| API | `/api/s2p/score` perturbation + F-26 gate |
| Class | **NEAR** |
| Audience sees | Beside "Why: 5.2% variance, copper +4.8%, §7.3 allows ≤110%, accept 0.91" → "Would flip to HOLD if: contract allowance < 4.8% / supplier exception history deteriorates / commodity correlation leaves trusted range / regulatory evidence incomplete" |
| Spoken | "Ask it not just why — but what would have changed its mind. That's a decision policy you can interrogate, not a black box." |
| DoD · Honesty | Perturbation is live and real; sample values refused into headline metrics (the V4/F-26 refusal). |

**S2P-DAY0 — "Here's what we can't trust yet"** *(day-0 readiness)*
| Field | Value |
|---|---|
| Surface | S2P fresh-tenant view — extends DZ-1 (§4.3) day-zero honesty |
| API | day-zero state (INSTRUMENT_VALIDATED → ACCUMULATING → MEASURED) over the enrichment layer |
| Class | **NEAR** |
| Audience sees | A week-one readiness read that leads with what the data **doesn't** support yet: source coverage/completeness/provenance/trust-tiers, and the honest empty state — **not** a fabricated ROI |
| Spoken | "Day one we don't hand you a number. We hand you the truth about your data — what we can act on, and what we'll abstain on until it earns trust. That's the paid discovery that becomes the pilot." |
| DoD · Honesty | **Cannot use learned factor-trust weights** (they need accumulated decisions) — built on the enrichment layer. No fabricated magnitude (F-21). |

**S2P-CONFIDENCE — "What I'm not confident about"** *(always-visible confidence state; answers S9)*
| Field | Value |
|---|---|
| Surface | S2P **Exception Triage** header — surfaces the built novelty tracker + self-pause (F6) as standing state, not an alarm |
| API | `/api/s2p/conservation` + novelty rate |
| Class | **LIVE** (novelty/self-pause built) → **NEAR** (always-visible panel) |
| Audience sees | A permanent confidence band per category — "electronics: novelty rising, auto-approve paused itself" — visible before anything breaks |
| Spoken | "The fear isn't that it's wrong — it's that it's wrong *quietly*. So it tells you, all the time, where it isn't sure. It paused itself here before a human noticed." |
| DoD · Honesty | This is the standing-visibility version of the S9 auto-pause; conservation scope per F-24 (scoring/exploration/scorer-evolution loops, not "all loops"). |

---

## §S2P-ROOM — new competitive-room line (add to §0.3): the cross-system neutrality kill-shot

Add a tear-down answer for the "a hyperscaler will just clone this inside their suite" objection (Gemini run's sharpest defusal):
| Room | When they say… | You say… |
|---|---|---|
| 6b. Suite AI (SAP/Coupa clone risk) | "SAP or Coupa will build judgment memory into their own stack." | "Inside their own walls, sure. But SAP's agent will never optimize a *Coupa-to-Celonis* cross-system workflow, and Coupa's won't reach into SAP's. Our moat is **neutrality across your whole stack** — we compound judgment over decisions that span systems no single suite owns. A suite vendor structurally can't match that." |

---

## §S2P-LOOM — update the L-S2P Loom cut (§7.2)

The L-S2P cut (§2.3 re-led on S2P, ~5 min, "S14 hero + cross-copilot signal") gains a **lead-simple spine**: open on the mirror-adjacent **S14** situation-analysis moment (SILENCE 2, corrected per §S2P-FIX-1) → **S2P-LEDGER** (the one number, growing) → **S2P-EXTINCT** (exception extinction) → **S2P-TWIN** (the frozen twin proves it) → close on the moat (time moat + "which decision to change," per ENT-1's write-back guard). Keep S6 continuity (E6) as the "your best buyer left; the judgment stayed" beat.

---

## §S2P-PRESEED — additions to §5 (demo-base requirements)

For the new beats to fire on a clean machine, §5 preseed must also guarantee:
- Non-flat **auto-approve coverage series** for S2P (the S2P-LEDGER trajectory) + a **frozen-twin baseline arm** on the same seed (S2P-TWIN).
- At least one **promoted + transferred** exception class in the S2P promotion logs (S2P-EXTINCT).
- A **day-zero S2P tenant** state available via toggle (S2P-DAY0), enrichment-layer only.
- Cross-copilot **Purchasing→S2P signal** already listed — keep (feeds continuity/compounding).
- **Honesty:** every dollar figure across the new S2P beats renders from preseed with a provenance badge; the frozen-twin divergence is labeled MODELED/PILOT-TARGET until measured on real data.

---

*Applies `s2p_review_consolidation_v1` (three-run: Opus/GPT/Gemini) to `demo_scenarios_and_usecases_v2_5.md`. Companion: `s2p_copilot_doc_additions_v1.md`. All new beats are stage/wire on shipped surfaces except the two-arm frozen-twin (NEAR) and the always-visible confidence panel (NEAR). No beat implies roadmap is LIVE (F-27); no beat says "RL" (F-25).*
