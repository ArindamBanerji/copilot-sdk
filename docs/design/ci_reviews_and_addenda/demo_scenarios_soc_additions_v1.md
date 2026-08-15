# Demo Scenarios — SOC Additions & Corrections v1
*Surgical delta to `demo_scenarios_and_usecases_v2_5.md` (Drive design folder). Adds the product surfaces from `soc_review_consolidation_v1` / `soc_copilot_doc_additions_v1` as SOC demo beats, and corrects two stale framings. Same shape as the trading / dataops / purchasing / s2p demo addenda. **Every new beat carries a surface + API + class (LIVE/NEAR/ARCH) + DoD**, and obeys the SOC world's honesty rules — the SOC-native equivalents of the S2P F-rules:*
> *• **H7** (design-doc §28.3): every UI value traces to a real computation OR carries a visible honesty label ("projected", "demo data", "illustrative", "MODELED"). This is the SOC version of F-21/F-22 (illustrative dollars).*
> *• **"product" not "demo" language** (§13) and **never say "RL"** for the primary mechanism on stage — it is decision-trace / prototype learning from verified decisions, and never "second-derivative RL." (SOC version of F-25.)*
> *• **Signals transfer; judgment geometry is per-copilot** — a SOC→S2P handoff is signal/pattern transfer, not shared judgment. (SOC version of F-26.)*
> *• **Showing roadmap is fine; implying roadmap is LIVE is the violation** (§11.6 gates). (SOC version of F-27.)*
> *• **The two-regime rule** (§4.4): the 97.89% centroidal-synthetic number validates the math and is **never** customer-facing; 71.7% static / 78.9% @1,000 (50-seed) is the product claim. Never mix.*

> **Good news from the read:** the five SOC surfaces already ship (§11.5 Tab 3 Triage / Tab 2 Runtime-Evolution + Learning-Impact / Tab 4 Compounding / Tab 5 Exec Narrative / Tab 1 Graph Explorer), shadow mode is real (§21, never auto-activates), and the H7 rule already enforces the synthetic-labeling discipline demo-side. So the demo needs *additions*, plus **two** corrections (§SOC-FIX-1, §SOC-FIX-2) — not a wholesale rewrite.

---

## §SOC-FIX-1 — retire "we compound, they don't" / "they start at zero" (cold-start counter)

Any beat or room line that leads with "our SOC learns and theirs doesn't," "we compound and they don't," or "they start from zero" is 2026-false on sight (Torq/Simbian/Prophet/Stellar all claim learning; Torq Retrospect imports years of case history). **Replace with the cold-start counter** (product-def v1.2 §P1):
> *(new framing)* "Imported history makes you good at the last firm's incidents. We start you on a strong prior and then learn where *your* environment disagrees with it — and that disagreement is the compounding curve. The noisier your environment, the bigger the gap we open over a system replaying someone else's history."

Keep the provable-loop contrast (which alert changed the next decision, and proof it got better) — that is the durable wedge, not "we learn."

## §SOC-FIX-2 — never let the mechanism number sit next to the product number; kill two overclaims

- **Two-regime guard:** anywhere a demo cites "78.9% at decision 1,000," the 97.89% centroidal-synthetic number must not appear on the same surface — it validates the math, is never customer-facing (§4.4). Label the 50-seed numbers as controlled synthetic evaluations until the pilot curve exists.
- **Two overclaims to strip** (prompt-induced, corrected in v1.2 §P4.1): no beat says AgentEvolver "evolves the deployment **mid-incident**" — say *policy evolves continuously from verified outcomes without a retrain or vendor release*. No beat says tech-process fusion "makes the attack class impossible" in the SOC today — it is ARCH-for-SOC, framed land→expand→end-state, demonstrated on S2P/DataOps.

---

## §SOC-NEW — new SOC demo beats (add to the SOC catalog and the L-SOC cut)

These make the moat **visible** — the gap all three judge runs named. Each extends an existing shipped surface where possible; the frozen twin and the two metrics are the genuinely new builds.

**SOC-CONTROL — "How do you know it got better?"** *(the Learning Control Room, F16)*
| Field | Value |
|---|---|
| Surface | Tab 2 Runtime-Evolution → LearningControlRoom panel (renders the promoted-change record) |
| API | `/api/soc/centroid-evolution`, `/api/soc/learning-state`, IKS (`/api/soc/profile`), counterfactual replay, evidence export (all shipped) |
| Class | **LIVE** primitives → **NEAR** (the unified five-face panel) |
| Audience sees | One promoted change told in five faces: **BEFORE** (policy) → **CHANGE** (which routing/scoring-weight variant) → **EVIDENCE** (the verified outcomes that caused it, with provenance) → **EFFECT** (which past decisions flip, via replay) → **SAFETY** (shadow-test + conservation state + rollback target) |
| Spoken | "Every change the system makes to itself shows up here: what changed, the verified outcomes that earned it, which past calls it would flip, and the safety check that let it through — with a rollback button." |
| DoD · Honesty | Renders from existing endpoints; **no "RL"** on stage (decision-trace learning); every value traces to a computation (H7). |

**SOC-LADDER — "Autonomy it has to earn"** *(the Earned Autonomy ladder, F17)*
| Field | Value |
|---|---|
| Surface | Tab 4 Compounding header + Tab 3 per-alert badge (renders referral VETO + conservation + per-category thresholds as a standing ladder) |
| API | `/api/soc/conservation` (Circuit Breaker), referral engine R1–R7, per-category auto-approve thresholds, shadow status |
| Class | **LIVE** primitives → **NEAR** (the visible per-class ladder) |
| Audience sees | Per category, the rung: **Observed → Assisted → Shadow-qualified → Auto-approved → Circuit-broken** — `cloud_infrastructure` auto-approved, `insider_threat` held at Observed by design, one category circuit-broken this week with the reason |
| Spoken | "We don't switch autonomy on. Each alert class earns its way up the ladder, and the math pulls it back the moment learning quality drops — here's a class that just got circuit-broken." |
| DoD · Honesty | Standing-visibility rendering of shipped primitives (§22.6/§22.7); conservation scope per the design doc (scoring/exploration/scorer-evolution loops, not "all loops"). |

**SOC-TWIN — "The version we froze on day one"** *(the Frozen Twin, F18)*
| Field | Value |
|---|---|
| Surface | Tab 4 Compounding (curve overlay: live vs frozen-at-day-1 clone on the same alert stream) |
| API | frozen-baseline arm over `/api/soc/*` + the two-arm Safety-Coverage Frontier |
| Class | **NEAR** |
| Audience sees | Two curves on the customer's own alerts — a twin pinned at bootstrap μ₀ (no learning) vs the live system pulling away; the gap is the compounding, in safe coverage and Recovery Half-Life |
| Spoken | "A version of this we froze on day one is still running beside it on your data. The distance between the two lines is exactly what you're buying — measured, not asserted." |
| DoD · Honesty | The artifact that converts the 50-seed numbers from synthetic to **measured**; until it has run on real data, label the divergence **MODELED/PILOT-TARGET** (H7). |

**SOC-NOPRECEDENT — "Similar past cases: none"** *(the No-Precedent surface, F19 — the Stryker beat)*
| Field | Value |
|---|---|
| Surface | Tab 3 Triage — the similar-cases sidebar's honest empty state, surfaced beside a high-confidence action |
| API | SimilarCasesService (suppresses below 5 priors, §23.4) + the six-factor breakdown |
| Class | **LIVE** |
| Audience sees | The Stryker alert: privileged_identity_context elevated on a service-tier identity issuing bulk Intune ops, MFA/device clean, "**similar past cases: none — unprecedented here**," ESCALATE at high confidence with the factor breakdown |
| Spoken | "A retrieval system is blindest exactly here — no precedent, nothing to recall. Ours scores the identity risk geometrically and escalates anyway, and it tells you plainly it's never seen this before." |
| DoD · Honesty | Surfaces an existing empty state — the pixel a retrieval UI can't draw. Factor 0 = privileged_identity_context (the Stryker signal). |

**SOC-WHATIF — "What would change this decision?"** *(the Counterfactual inspector, F20)*
| Field | Value |
|---|---|
| Surface | Tab 3 Triage → factor panel, adds a "what would flip it" block |
| API | counterfactual replay / score perturbation |
| Class | **NEAR** |
| Audience sees | Beside "Why: privileged identity 0.9, threat-intel 0.8, pattern-history velocity anomaly" → "Would drop to INVESTIGATE if: identity tier were standard / MFA signals clean / no velocity anomaly / no threat-intel enrichment" |
| Spoken | "Ask it not just why — but what would have changed its mind. That's a decision policy you can interrogate, not a black box." |
| DoD · Honesty | Perturbation is real; sample values never promoted into headline metrics (H7). |

**SOC-DAY0 — "Here's what we can't trust yet"** *(Day-0 readiness, F21)*
| Field | Value |
|---|---|
| Surface | Fresh-tenant SOC view — leads with what the data doesn't support yet |
| API | day-zero state over the enrichment layer + threat-intel connector health (Pulsedive/CISA KEV/NVD) |
| Class | **NEAR** |
| Audience sees | A week-one readiness read: source coverage, completeness, provenance, connector health, and the honest empty state — **not** a fabricated ROI number |
| Spoken | "Day one we don't hand you a number. We hand you the truth about your data — what we can act on, and what we'll abstain on until it earns trust. That's the paid discovery that becomes the pilot." |
| DoD · Honesty | **Cannot** use learned factor-trust weights (they need accumulated decisions) — enrichment-layer only. No fabricated magnitude (H7). |

**SOC-FRONTIER — "Coverage that grows at a fixed safety bar"** *(Safety-Coverage Frontier + Recovery Half-Life, §B)*
| Field | Value |
|---|---|
| Surface | Tab 4 Compounding — replaces raw-accuracy hero with the two compounding metrics |
| API | per-category auto-approve coverage series + bad-auto-approval rate + re-convergence logger |
| Class | **LIVE** (single-arm coverage + IKS) → **NEAR** (two-arm frontier vs frozen twin) |
| Audience sees | Safe auto-approve coverage climbing at a constant safety bar (per category), and — after a regime break — the Recovery Half-Life (decisions + days to re-reach the competence bar) |
| Spoken | "Accuracy plateaus and hides the story. The number that matters is how much it safely handles on its own without the bad-call rate rising — and how fast it recovers when the threat landscape shifts." |
| DoD · Honesty | Both MEASURED-synthetic until the pilot; two-regime guard (never show 97.89% here). No "RL." |

**SOC-GAUNTLET — "Run the novelty test yourself"** *(the Novel Attack Gauntlet, §C)*
| Field | Value |
|---|---|
| Surface | Tab 3 Triage, run as a scripted five-beat sequence (extends the Stryker scenario) |
| API | triage + referral VETO + no-precedent surface + Recovery Half-Life |
| Class | **LIVE** decision path; **NEAR** as a packaged benchmark |
| Audience sees | Five perturbations — no-precedent (Stryker) / misleading-precedent / signal-inversion / regime-break / adversarial-context — each showing act-or-abstain, the no-precedent surface, and (over the run) Recovery Half-Life |
| Spoken | "Stryker isn't a lucky anecdote — it's one of five ways we stress the no-precedent claim. Run them on your own stream; that's the falsifiable version of 'acts when there's no precedent.'" |
| DoD · Honesty | Adversarial-context beat uses the conservation gate + 20:1 asymmetry (real); no fabricated hit-rates (H7). Preserves all five SOC scenarios — extends, never replaces. |

---

## §SOC-ROOM — new competitive-room line (add to the room catalog): the platform-absorption kill-shot

Add a teardown answer for the killer objection all three runs named (native free triage in Falcon/Sentinel/Cortex):
| Room | When they say… | You say… |
|---|---|---|
| Platform absorption (CrowdStrike / MS / Palo Alto) | "CrowdStrike and Microsoft will just ship good-enough triage free in the console." | "Inside their own console, sure — locked to their own data lake. Ours is the **cross-stack judgment gateway**: it compounds *your firm's* verified-decision judgment across CrowdStrike **and** Sentinel **and** Okta at once, over decisions that span systems no single platform owns. To fast-follow, they'd have to rebuild non-parametric metric learning on open topologies — and the judgment graph is yours, not theirs." |
| Security Copilot price-to-zero | "Security Copilot comes bundled in E5 for near-zero." | "A bundled per-seat copilot doesn't touch the budget line this replaces — MDR/MSSP and SIEM ingest — and it can't show you your own compounding curve. We're the governed decision-learning layer above the stack, not another copilot inside it." |

---

## §SOC-LOOM — update the L-SOC Loom cut

The SOC Loom cut gains a **lead-simple spine** (consistency + provability, per v1.2 §P0.2): open on **SOC-NOPRECEDENT** (the Stryker no-precedent moment — proof consistency survives) → **SOC-CONTROL** (how you know it got better) → **SOC-LADDER** (autonomy it earns) → **SOC-TWIN** (the frozen twin proves it on your data) → close on the moat (customer-owned judgment + the engine that compounds it; SOAR-first write-back). Keep the cross-copilot beat as *signal transfer, not shared judgment* (SOC honesty rule / F-26 analog). Never cite the mechanism number (§SOC-FIX-2).

---

## §SOC-PRESEED — additions to the demo-base requirements

For the new beats to fire on a clean machine, preseed must also guarantee:
- A non-flat **auto-approve coverage series at a fixed safety bar** per category (SOC-FRONTIER) + a **frozen-twin baseline arm** on the same seed (SOC-TWIN).
- At least one **promoted + rolled-back** change in the AgentEvolver logs with its evidence + counterfactual (SOC-CONTROL), and one **circuit-broken** category (SOC-LADDER).
- A **day-zero SOC tenant** state available via toggle, enrichment-layer only (SOC-DAY0).
- The five **Novel Attack Gauntlet** beats seeded, including a regime-break that produces a measurable Recovery Half-Life (SOC-GAUNTLET), and the Stryker no-precedent alert (SOC-NOPRECEDENT).
- **Honesty:** every number across the new beats renders from preseed with a provenance badge or an H7 label; the frozen-twin divergence and both compounding metrics are labeled MODELED/PILOT-TARGET until measured on real data; the 97.89% mechanism number never appears on a customer-facing surface.

---
*Applies `soc_review_consolidation_v1` (three-run: GPT/Opus/Gemini) to `demo_scenarios_and_usecases_v2_5.md`. Companion: `soc_copilot_doc_additions_v1.md`. New beats are stage/wire on shipped surfaces except the frozen twin, the two-arm Safety-Coverage Frontier, and the unified Learning Control Room (NEAR). No beat implies roadmap is LIVE (§11.6 gates); no beat says "RL"; no beat shows the 97.89% mechanism number; all five SOC scenarios preserved.*
