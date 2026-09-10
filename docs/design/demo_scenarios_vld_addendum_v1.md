# Demo Scenarios — VLD Investigation Additions v1
*Surgical delta to `demo_scenarios_and_usecases_v2_7.md` (Drive id 1zxb2o0XHy0uzg2G1QXIhSRsfxpSL_4KU, ci_core folder). Adds the VLD investigation loop (`vld_graph_reasoning_architecture_v3.md`) as demo beats, one new competitive room, three tear-down lines, one silence beat, and the preseed the beats need. Same shape as the trading / dataops / purchasing / S2P demo addenda. **Every new beat carries a surface + API + class (LIVE/NEAR/ARCH) + DoD**, and obeys the doc's existing honesty rules: F-21/F-22 (figures are illustrative preseed formats, never measured outcomes), **F-25 (VLD is "investigation-trace / score-conditioned evidence retrieval" — never "reasoning" or "thinking" in a way that implies LLM-style internal deliberation, and never "RL")**, F-26 (signals transfer; judgment geometry is per-copilot), F-27 (showing roadmap is fine; implying roadmap is LIVE is the violation).*

> **Read-first from the R1 structural audit (`soc_rho_structural_feasibility_audit_2026-09-08.md`):** every VLD beat below is **Class: ARCH**, and the reason is specific, not cautious. (1) SOC's scorer chooses an action *within an externally supplied category* (alert_type → literal map, `config.py:308`); it does not infer a category or dispatch an auth-trail vs process-tree investigation. (2) `SituationAnalyzer` dispatches **one** bulk-context pattern per decision (`soc_alert_context` → `get_security_context(alert_id)`), selected by `supports(intent)`, never by v_t; production triage calls the legacy `analyze_situation()`. (3) **Zero** investigation trajectory records exist — no first-read records, no branch labels, no scorer-to-branch policy. (4) The 432 campaign-bearing decisions are 48 alerts × 9 synthetic repeats with no intermediate scoring state. So the scorer-to-branch policy (R3) and the trajectory store (E-1) are the build; the beats are stageable **only on planted fixtures**, and every screen says so. The `nodes_consulted = 47` value the SOC pattern reports is a query literal, not a measured count — it never appears on a VLD surface.

> **Good news from the read:** the VLD beats do **not** depend on the SOC-learning gate (§0.2 #1). Routing reads the *frozen* judgment state (μ, DK, τ) at decision time — Θ is frozen for the whole episode — so VLD-SOC-1/2 can stage with `SOC_LEARNING_ENABLED` off. The one line that *would* need learning on ("next time it routes better") is banned below (§VLD-GUARD #6).

---

## §VLD-ROOM — new room entry for §0.1 (room → kill-shot map)

| # | Room | Kill-shot beat | The line | Class |
|---|---|---|---|---|
| 16 | Adaptive investigation / autonomous reasoning agents | **VLD-SOC-1 The Investigation Trace** (+ VLD-SOC-2 as the deep cut) | "A rule checks the threshold. We checked the contract, then the supplier's history, then the goods receipt — **in that order**, because the second question depended on the first answer. And you can read the order." | **ARCH** (→ NEAR when R3 Ψ prototype + trajectory store ship; → LIVE only after R4 shadow-run shows Δ_depth > 0 against rule-based routing) |

*Room-16 framing note:* the line is the **order** of the reads, not the reads themselves. Any competitor with a retrieval graph can fetch the same three documents; the claim is that the *sequence* was chosen by the scorer's intermediate state, not by a fixed checklist — and that the sequence is on screen. Until R4 passes, presenters say "this is how the investigation loop is designed to work" (F-27), never "this is how it works today."

---

## §VLD-NEW — the five VLD beats (add to §3 catalogs and the Loom cuts in §7.2)

All five share one new SDK surface and one API shape:

- **Surface:** `InvestigationTracePanel` (new; shared `copilot_sdk/frontend` component, 1× SDK + 1× SOC — same dual-world pattern as LOOM-2). Renders per step: *pattern dispatched · evidence admitted · v_t shift · nearest centroid + margin · branch chosen · budget used · halt reason*. Header carries two standing badges: **`PLANTED FIXTURE`** (provenance) and **`ROUTING ACCURACY: not yet measured (R1 pending)`**.
- **API:** `POST /api/{copilot}/investigate` (new). Returns the trajectory τ = [(S₀,v₀), (S₁,v₁), …, (S_L,v_L)] + per-step trace record (E-1 schema: candidate reads, selected edge, propensity if any, cost, timestamp, policy version, stopping reason). Read-only against μ and the graph during the episode (Inference Side-Effect Contract).
- **Contrast strip:** beneath the trace, the single-pass result on the same case ("what the copilot does today"), so the audience sees the delta, not just the trace.
- **Class:** **ARCH** for all five (audit above). No beat implies the branch policy exists in production.

**VLD-SOC-1 — "The Investigation Trace"** *(the honest version of "it investigated like an analyst")*
| Field | Value |
|---|---|
| Surface | SOC **Alert Triage** (Tab 3) → InvestigationTracePanel beside the existing SituationPanel |
| API | `POST /api/soc/investigate` (new, ARCH); reads `DECIDED_ON` → `MEMBER_OF` → `CONTINUES` campaign topology (P1-confirmed) + the six SOC factor computers via the existing provider |
| Class | **ARCH** |
| Audience sees | A **mixed-indicator alert** (credential AND process AND network anomalies — category `lateral_movement`, supplied by alert_type as today). Step 0: single-pass v₀, margin 0.04 between `investigate` and `escalate` — ambiguous. Step 1: the branch policy reads v₀'s factor weights (privileged_identity_context 0.9 dominant over device_trust 0.3) → dispatches the **auth-trail** pattern. Step 2: admitted evidence shifts v₁; margin widens to 0.31 toward `escalate`; residual below δ → halt. Final: ESCALATE, conservation GREEN at emit. Trace reads: *"checked auth trail (privileged-identity weight led) → found credential reuse across 3 hosts → therefore checked lateral-movement chain → found pivot → escalate."* Contrast strip: single-pass would have returned INVESTIGATE at 0.04 margin — i.e. *"go look."* |
| Spoken | "Today it says 'go look.' The investigation loop *went and looked* — and it tells you what it checked first and why: the identity weight was the strongest thing in the score, so it pulled the auth trail before the process tree. That order isn't a checklist. It came from the scorer's state." |
| DoD · Honesty | Trace renders **from a persisted trajectory record**, not from a script; each step's `branch chosen` cites the v_t quantity that chose it (dominant factor + margin). PLANTED badge on the alert; ρ-unmeasured badge in the header. The alert's *category* is content-keyed (alert_type) and the screen says so — the score-keyed part is the **branch within the category**, and that is the only part claimed for VLD. No "reasoning/thinking" microcopy (F-25). Single-pass contrast shown every time. |

**VLD-SOC-2 — "The Wrong-First-Step Recovery"** *(the correction is the demo moment)*
| Field | Value |
|---|---|
| Surface | SOC **Alert Triage** (Tab 3) → InvestigationTracePanel |
| API | `POST /api/soc/investigate` with budget B_max = 2 branches; C4 per-step halt (normalized residual + budget + flip-count) |
| Class | **ARCH** |
| Audience sees | Same panel, different planted case. Step 1: policy routes to **auth trail** (identity weight led). Evidence comes back **empty** — no credential reuse. Step 2: re-score; v₁ barely moves (residual above δ), and the flip-count ticks — the top-1 action changes from `escalate` back to `investigate`. The policy re-reads v₁: with identity evidence exhausted, process-anomaly weight now dominates → dispatches **process tree**. Step 3: finds the injection; margin widens; halt. Trace reads: *"checked auth trail → nothing → re-scored → identity path exhausted → checked process tree → found injection."* The wrong first step is shown in red, not hidden. |
| Spoken | "Watch the second line. It went to the auth trail first — and found nothing. It didn't keep going. It re-scored, saw the identity path was exhausted, and changed direction. It didn't just investigate; it changed course when the evidence didn't match. And the wrong step is on the record, in red." |
| DoD · Honesty | The pivot is produced by the **C4 halt + branch policy**, not scripted; the trace shows budget consumed (2 of 2). **Honesty line the presenter must say:** at budget = branches, exhaustive retrieval would have found the same thing — what this beat demonstrates is the *order*, the *legible correction*, and that the loop **stops itself**; it is **not** a value claim over breadth (Sim 2, budget=2). This case is exactly the ρ < ½ failure mode the value model warns about; showing it is the honest move, provided the caption says "when the first step is wrong." Never say "it reasoned." |

**VLD-DO-1 — "Three Systems, One Root Cause"** *(DataOps triage)*
| Field | Value |
|---|---|
| Surface | DataOps **Triage** (D-M1) → InvestigationTracePanel; hand-off into **Insight** → `ApplyFixModal` (E5) |
| API | `POST /api/dataops/investigate` (new, ARCH) over the existing system-keyed decision history (`context_router.py:913-931`, P1: low m_topological) + `/api/s2p/insight/cross-graph`, `/api/context/apply-fix` (shipped, E5) |
| Class | **ARCH** (and DD-0 still applies: DataOps learning loop unconfirmed — the routing here reads frozen μ and does not depend on it) |
| Audience sees | Ambiguous `billing_api` alert: throughput drop **and** value anomaly — consistent with upstream outage, schema change, or data-quality regression. Step 1: v₀ sits between `schema_change` and `pipeline_failure` centroids; the pattern-history factor (prior alerts on this pipeline) tips margin toward `schema_change` → policy dispatches the **schema-change history** pattern. Step 2: finds the `MATKL_V2` migration; margin widens; halt. Step 3 *(content-keyed, labeled as such on screen)*: lineage walk to downstream consumers → three systems; ranked by DK weight of the affected factors. Recommendation: fix the transformation layer first. |
| Spoken | "Celonis shows WHERE the bottleneck is. The investigation loop found WHY — it went to schema history first because the scorer's experience with this pipeline pointed there, not because a rule said so — and told you WHICH system to fix first. The blast-radius walk after that? A rule could do that part. We say so on screen." |
| DoD · Honesty | The **only** step claimed for VLD is step 1 (schema vs upstream — score-keyed). Step 3's lineage walk is tagged **`CONTENT-KEYED / PREREQUISITE`** in the panel — a rule engine can do it. "Which system first" is a **recommendation**; write-back is roadmap (ENT-1 scope guard, F-21). "Learned impact weights" = the existing per-factor DK weights, not per-system weights — the caption uses plain field names (DD-9). Requires Decision→Pipeline entity attachment in production (Tier 2 wiring) before it can leave ARCH. |

**VLD-DO-2 — "Known Pattern, New Twist"** *(centroid distance as the routing signal)*
| Field | Value |
|---|---|
| Surface | DataOps **Insight** → InvestigationTracePanel beside the CentroidTimelinePanel (DI-TIMELINE) |
| API | `POST /api/dataops/investigate`; routing keyed on **confidence** = softmax margin to the nearest centroid |
| Class | **ARCH** |
| Audience sees | An alert that lands **near** the `resource_quota` cluster but not inside it — nearest-centroid confidence 0.62 (below the follow-known-path threshold). Step 1: because confidence is *low*, the policy does **not** follow the known resolution path; it dispatches the **broad-read** pattern (the breadth arm). Step 2: the broad read surfaces a new cause (a quota change *plus* a partition-key drift); v₁ moves toward a region with no centroid nearby; the panel shows the SOC-NOPRECEDENT-style empty state: *"similar resolved cases: none for this combination."* Halt on budget; emit INVESTIGATE with `refer_to_analyst`. Sister case shown second: confidence 0.93 → follows the known path in one read. |
| Spoken | "It recognized the pattern — and didn't trust the recognition. Confidence was too low to follow the usual fix, so it read wide instead of deep, and found the new cause. When it's sure, it goes straight there. When it isn't, it says so and looks around. That's the difference between a script and a loop with a floor." |
| DoD · Honesty | Both branches (follow-known vs read-wide) are driven by the **same** margin threshold, pre-registered and shown on screen; the low-confidence branch *is* the breadth arm, and the caption says "reads wide" not "reasons." The empty state reuses SOC-NOPRECEDENT's honest-empty pattern. No "$" magnitude on this beat. |

**VLD-S2P-1 — "The Supplier It Knew"** *(learned supplier pattern orders the investigation)*
| Field | Value |
|---|---|
| Surface | S2P **Exception Triage** → SituationPanel + InvestigationTracePanel; extends S14-CONTRAST (§4.2.1) with an **investigation-order strip** |
| API | `POST /api/s2p/investigate` (new, ARCH) over Decision→Invoice→Supplier→Invoice→Decision (P1-confirmed) + the supplier-keyed prior-decision matcher (`s2p_context_builder.py:150-174`) |
| Class | **ARCH** |
| Audience sees | **Dual mismatch** on a Supplier Aster invoice — PO amount *and* delivery quantity both off; the mismatch record does **not** say which is primary. Step 1: v₀ is scored against the supplier-conditioned prior decisions; Aster's verified history sits in the `partial_delivery` region (planted: partial deliveries **3.1×** more frequent than pricing errors for this supplier — badge: *illustrative from preseed*). Policy dispatches **goods receipt** first. Step 2: receipt confirms a partial delivery that explains both mismatches; margin widens to `accept-with-adjustment`; halt after one read. Contrast strip: rule-based = check both paths in fixed order (contract first); single-pass = "route to manual review." |
| Spoken | "A rule checks both paths, contract first, every time. We checked the receipt first — because on this supplier, the verified history says partial delivery is three times likelier than a pricing error. One read instead of two. And when the receipt explained both numbers, it stopped." |
| DoD · Honesty | The 3.1× ratio is **computed from preseed verified decisions**, provenance-badged (F-21/F-22), never presented as a customer measurement. The as-of cutoff on the supplier matcher (currently absent, `S2C:150-174`) must be enforced before this beat leaves ARCH — otherwise the "history" can include the future. Presenter states the budget caveat: with budget for both reads, a rule gets the same answer; the claim is **order + one fewer read**, and the time saved is a **pilot target, unvalidated** (R5). |

---

## §VLD-LINES — competitive tear-down lines (add to §0.3)

Pattern as always: **acknowledge → reframe → kill shot.** These three answer the interruptions Room 16 will get. All three are safe under FIX-8 (no named-competitor performance number; the Adaptive-RAG line describes a published mechanism, not a vendor).

| Room | When they say… | You say… |
|---|---|---|
| 16. Adaptive investigation | "Our agents investigate too." | "They do — and that's good. Investigation without judgment routing is a checklist: the same reads in the same order for every case. Ours changes direction based on what it finds — the second question depends on the first answer, and the answer comes from the scorer's state, not from a rule. That's judgment routing, not a workflow. And the order is on the screen." |
| 16. Adaptive investigation | "We have graph-based reasoning." | "Graph retrieval is one read — you fetch the neighborhood and score it. We re-read based on what we learned from the first read, and we stop when the score stops moving. That's investigation, not retrieval. Show me the trace where your second read depended on your first." |
| 16. Adaptive investigation | "We use RAG with reasoning." | "Single-shot RAG retrieves once. Adaptive-RAG routes by *predicted complexity* — how hard the question looks. We route by *learned judgment* — where this case sits against your firm's verified decisions determines what to check next. Different signal, and yours can't produce it without our judgment graph." |

**Standing caveat for all three (F-27):** if the room asks "is that running today?", the answer is "the loop is designed and the trace store is being built; what's running today is single-pass scoring — I'll show you both." Never bluff Room 16.

---

## §VLD-LINK — integration with existing beats

**VLD-SOC-1 ↔ DM-1 (Rejection Moment, §4.1) — same governance story, deeper investigation.**
Spoken bridge, after SILENCE 3: *"Same three parts you just saw. The investigation loop produces the trace. AgentEvolver may propose bounded routing-parameter variants — branch weights, read order — through the same shadow → promote gate, and the gate rejects the ones that don't survive. Conservation gates the action at emit. Deeper investigation, same governance."* **Guard (N3):** AE evolves Ψ *parameters*, never Ψ *structure* (which patterns exist, how they compose); and this AE→routing path is itself **ARCH** — say "may propose," not "evolves."

**VLD-DO-1 ↔ ENT-1 (Sunk-Investment Multiplier, §4.8) — your Celonis data becomes investigation evidence.**
Spoken bridge: *"Your Celonis process graph and your SAP records become investigation evidence — the loop reads them in the order the scorer's experience says matters most, and tells you which decision to change first."* **Guard:** read-only ingestion; "which decision to change," never "we execute it in your ERP" (ENT-1 scope guard, F-21).

**VLD-S2P-1 ↔ S14 (rule-vs-reasoning contrast, §4.2.1) — extend the two-column contrast with an order strip.**
Spoken bridge, after SILENCE 2: *"The rule checks a 5% threshold. The investigation loop checked the contract, then the supplier's history, then the goods receipt — in that order, because after the contract came back clean, the scorer's experience with this supplier said check the receipt next."* **Guard:** the contract check is **content-keyed** — a rule does it; the receipt-next step is the **score-keyed** part and is the only part attributed to VLD. The S14-CONTRAST killer line ("rules don't read contracts") stays as-is; the VLD line is *additive* ("and they don't know which document to read second").

---

## §VLD-GUARD — honesty constraints on every VLD beat (mandatory)

1. **Class: ARCH, all five, until Phase 2 ships the Ψ prototype** (R3) **and** the trajectory store (E-1). Promote to NEAR when both exist on a shipped surface; to LIVE only after R4 shadow-run shows Δ_depth > 0 against rule-based routing on real cases. No beat, caption, or deck implies otherwise (F-27).
2. **F-25 for VLD:** the mechanism is *investigation-trace / score-conditioned evidence retrieval*. Never "reasoning," "thinking," "deliberating," or anything implying LLM-style internal deliberation; never "RL." Allowed nouns: *investigation, trace, route, re-score, admit, halt.*
3. **The R1 facts travel with the beat:** the scorer-to-branch policy does not exist yet; SA dispatches one bulk pattern, not conditional branches; zero trajectory records exist. Any screen showing conditional routing carries the `PLANTED FIXTURE` and `ROUTING ACCURACY: not yet measured` badges.
4. **Content-keyed steps are labeled and not claimed.** Where the evidence itself says where to go next (mismatch_type, alert category, lineage walk), the panel tags the step `CONTENT-KEYED` and the presenter says "a rule could do this part; VLD adds value on the score-keyed part."
5. **Time savings are "pilot targets, unvalidated"** until R5 analyst measurement completes. No "4–10×," no "40–60%," no minutes-saved on any VLD surface.
6. **No "next time it routes better."** That line requires the learning loop *and* the AE→routing path, both unconfirmed/ARCH; it also collides with §0.2 #1 on SOC. The VLD beats read frozen state and say so.
7. **Budget honesty:** wherever the budget covers all branches, the presenter says that exhaustive retrieval would reach the same answer; the claim is *order, legibility, and self-stopping* — not accuracy over breadth (Sim 2).
8. **Numbers:** 3.1× (S2P), margins, confidences — all computed from preseed fixtures with a provenance badge (F-21/F-22). The SOC pattern's `nodes_consulted = 47` literal never appears.
9. **DD-9 buyer-language guard:** no "centroid / DK / v_t / margin" on the customer-facing panel — use "closest match," "confidence," "what the score pointed to." (Internal/engineering cuts may show the raw quantities.)
10. **FIX-8:** no competitor's product is run, no named-competitor performance number is asserted in Room 16.

---

## §VLD-SILENCE — SILENCE 7: The Investigation Trace (VLD-SOC-1, second 40–70) *(add to §2.5)*

After you say *"Today it says 'go look.' The investigation loop went and looked,"* click **Investigate**. The trace renders, one line at a time:

> checked auth trail — identity weight led → found credential reuse on 3 hosts → therefore checked lateral-movement chain → found pivot → ESCALATE · conservation GREEN

**STOP.** Do not read it aloud. The audience reads the arrows. The realization they need to reach on their own is: *"the second line depends on the first — this isn't a checklist."* If you say "notice the order," it's a claim. If they notice, it's a conviction.

*What to do:* step back, point at the second arrow, say nothing for five seconds. The next sentence should come from them ("why the auth trail first?"). If nobody asks within 8 seconds, resume with: *"The identity weight was the strongest thing in the score. So it pulled the auth trail before the process tree. A rule would have pulled both, in the same order, every time."*

*Recovery variant (VLD-SOC-2):* on the wrong-first-step case, use the same silence at the **red** line — "checked auth trail → nothing → re-scored" — and let them see the pivot before you say *"it changed course."* One silence beat, two cases; do not run both silences in one cut.

*Honesty during the silence:* the `PLANTED FIXTURE` and `ROUTING ACCURACY: not yet measured` badges are visible in the panel header the whole time. If someone reads the badge aloud, answer plainly: "Right — it's a designed fixture. The loop is built to produce this; the measurement of how often it picks the right first step is the pilot."

---

## §VLD-LOOM — Loom cut placements (§7.2)

| Loom | Insertion | Note |
|---|---|---|
| L-SOC | after E2 (Why?) → **VLD-SOC-1** (SILENCE 7) → **VLD-SOC-2** → continue to E3 | ~2.5 min added; both beats captioned **ROADMAP** in the overlay (`class: "ARCH"` in the cut JSON so LOOM-2 renders the badge) |
| L-DATAOPS | after E5 fusion climax → **VLD-DO-1** (hands off into ApplyFixModal) → **VLD-DO-2** beside DI-TIMELINE | ~2 min added; DD-0 precondition banner stays visible |
| L-S2P | after S14 / SILENCE 2 → **VLD-S2P-1** as the S14-CONTRAST order-strip extension | ~1 min added; S2P-FIX-1 wording preserved |
| **L-VLD** (new, optional) | Room-16 standalone: VLD-SOC-1 → VLD-SOC-2 → VLD-S2P-1 → close on the three tear-down lines | ~4 min; **explicitly a roadmap Loom** — title card reads "Investigation loop — architecture preview"; not for cold outreach until NEAR |

Beats-config additions (LOOM-5): each VLD beat's JSON entry carries `class: "ARCH"`, `badges: ["PLANTED_FIXTURE","RHO_UNMEASURED"]`, and `api_warmup: ["/api/{copilot}/investigate"]`.

---

## §VLD-PRESEED — additions to §5 (demo-base requirements)

For the VLD beats to fire on a clean machine, §5 preseed must also guarantee:
- **Planted investigation fixtures**, one per beat, each with: S₀ snapshot, available branch set at S₁, planted evidence per branch (including an **empty** branch for VLD-SOC-2), and an adjudicated productive branch — labeled `PLANTED` in provenance. These are the R1 audit's "what must be supplied" fields, materialized synthetically.
- **A versioned scorer-to-branch policy** (`frozen_branch_policy`, R3) mapping the SOC six-factor v_t and the DataOps/S2P vectors to SA pattern dispatch — with the dominant-factor and margin thresholds pre-registered and visible on the panel.
- **Trajectory store (E-1)** schema in AGE for `InvestigationTrace` records — candidate reads, selected edge, cost, timestamp, policy version, stopping reason — so the panel renders from the record, not from a script.
- **C4 per-step halt** implemented (normalized residual with floor + budget + flip-count) and **conservation as emit-gate only** (constant within the episode) — the VLD-SOC-2 pivot depends on both.
- **SOC:** campaign topology (DECIDED_ON → MEMBER_OF → CONTINUES) present in the demo graph; the two planted alerts share a campaign so the reverse path resolves. Learning may stay **off** (frozen-state routing).
- **DataOps:** Decision→Pipeline entity attachment persisted (Tier 2 wiring) for the `billing_api` fixture; the `MATKL_V2` schema-change node linked; a second fixture near-but-outside the `resource_quota` cluster with confidence pinned ≈0.62 (VLD-DO-2).
- **S2P:** Supplier Aster with ≥ N verified prior decisions such that the partial-delivery : pricing-error ratio computes to ≈3.1 from the seed (provenance-badged); **as-of cutoff enforced** on the supplier matcher before the fixture is admitted.
- **Contrast data:** the single-pass result for each fixture is stored alongside, so the contrast strip is computed, not typed.
- **Honesty:** `PLANTED FIXTURE` + `ROUTING ACCURACY: not yet measured (R1 pending)` badges render on every InvestigationTracePanel by default; no VLD surface shows a time-savings figure; the `nodes_consulted` literal is not surfaced.

---

*Applies `vld_graph_reasoning_architecture_v3.md` (§2.2 controller placement, §4.2 content-keyed vs score-keyed, §8 R1–R6) and `soc_rho_structural_feasibility_audit_2026-09-08.md` (Part A inventory, Part F verdict) to `demo_scenarios_and_usecases_v2_7.md`. Companions: `ci_vld_depth_memo_v13.md` (parent memo), `vld_depth_p1_decision_graph_topology_report.md` (per-copilot traversability). All five beats are **ARCH** on planted fixtures; none implies roadmap is LIVE (F-27); none says "reasoning" or "RL" (F-25); all time-savings language is "pilot target, unvalidated" (R5).*
