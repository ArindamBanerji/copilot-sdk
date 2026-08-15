# Demo Scenarios — DataOps Additions v1
*Additions to `demo_scenarios_and_usecases_*.md` (Drive/design), DataOps §4.9 layer. Source: the consolidated 3-review verdict. **Nothing removed — every change extends or adds.** Mapped to the demo doc's real structure (§0.1 rooms, §0.3 tear-down, §4.9 DI beats + §4.9.0 cut arc, §5 preseed, §7.2 Loom L-DATAOPS-DI). Classes (LIVE/NEAR/ARCH) travel with each beat per F-27.*

**Scoping note (surgical delta).** The demo doc is already evolved on DataOps: it has the DI beats (DI-TRUST/PROOF/TIMELINE/ADMITS-FAILURE/GOLD/AGENT-TRUST), the §4.9.0 mirror→moat cut arc, competitive rooms 12/13, and the L-DATAOPS-DI cut. This delta (1) re-sequences the cut so **machinery leads and the category story lands last**, (2) makes the **agent-trust gateway** the climax beat, (3) adds the **abstention, time-to-competence, and frozen-twin** beats, and (4) de-risks the gold-line $. It is not a rewrite.

## DD-0 — ★ PRECONDITION / honesty guard (add to §5 and every earned-trust beat)
The earned-trust and admits-failure beats are **LIVE only if the verified-decision → AgentEvolver loop is wired for DataOps** — currently unconfirmed (the design doc says built; the review says maybe configured-not-wired). Until a code check proves *a verified decision moves a later score end-to-end*, tag these beats **NEAR/ARCH honestly (F-27)** and do not stage them as LIVE. This is the demo's biggest truth risk.

## DD-1 — Re-sequence the DataOps cut: machinery first, category-story last (revise §4.9.0 arc, §7.2 L-DATAOPS-DI)
Replace the current arc order with the convergent sequence: **1) It learns** (DI-PROOF perturbation) → **2) It knows what it learned** (self-computation: the exact decisions responsible) → **3) It knows when it was wrong** (DI-ADMITS-FAILURE — promote to a first-three beat, the governance moat) → **4) It governs AI action** (the trust gateway — the new climax) → **5) It compounds** (frozen twin / 1st-vs-6th source) → **6) The estate becomes visibly smarter** (Intelligence Map — W1 now lands because they've seen the machinery) → **7) It values itself** (gold lines — crescendo, de-risked). Detection/lineage stay as **substrate framing**, not a beat to win.

## DD-2 — Strengthen DI-PROOF into the "Prove it" panel (extend §4.9 DI-PROOF)
Keep the live perturbation; add the **restore + provenance log**: after trust drops (94 → X) and reverts, show *"score restored via human resolution #482 (+1.2% delta)."* Generalize DI-PROOF from one beat into a **"prove it" affordance on every number** in the cut. **SILENCE beat:** after the number drops, stop — let them watch a savings/trust number move *because of a decision.* **Class: NEAR** (live what-if surface).

## DD-3 — NEW beat: DI-ABSTAIN — "the system that says I don't know" (add to §4.9, §2.3 enterprise cut)
The agent asks permission before acting; the gateway returns evidence + abstain. On screen: *"Agent request: use Workday feed for autonomous reconciliation. Decision: human review required. Evidence: 4 verified decisions — insufficient for this action."* **Note the deliberate absence of "safe."** **Class: NEAR** (trust-API + policy surface). The liability-shield + differentiator beat — no agent-trust layer ships "I don't know."

## DD-4 — NEW beat: the Agent-Trust Gateway climax (add to §4.9; §0.1 new room)
The "governs AI action" climax: *"Your Databricks agent asks us before it acts — `/v1/trust/verify` → trust, basis, or abstain. We're the runtime trust gateway between your agents and your data."* Add a **§0.1 competitive room** for the agent-trust layer with the kill line and the **cross-cloud-neutrality "won't"** (a substrate owner won't rate a competitor's table fairly). **Class: NEAR** (thin MCP server over the trust API).

## DD-5 — NEW beats: compounding made falsifiable (add to §4.9)
- **DI-FIRSTVS6TH** — *"1st new source: X weeks to GREEN. 6th: Y days."* — the non-saturating compounding metric (replaces IKS-rising as the compounding *proof*). **Class: NEAR** (instrumentation + snapshot).
- **DI-TWIN** — *"A version of us frozen in March would have missed 11 of these 14 catches — here they are."* — the control that makes compounding falsifiable. **Class: ARCH→NEAR** (centroid snapshot + replay).

## DD-6 — De-risk DI-GOLD in the demo (revise §4.9 DI-GOLD)
Pull the **$ figures off the hero path.** Render gold lines as **FDR + 30-day-holdout-gated ranked hypotheses**, explicitly unvalidated, with a **"value not yet verified — N more outcomes needed"** empty state. For CFO dollars in the cut, use **D-M4 (14-day close → 7)** — realized time. Keeps the map's wow without the vaporware tax.

## DD-7 — Competitive tear-down lines (extend §0.3)
- *"Isn't this Unity Catalog lineage + a dashboard?"* → *"Unity Catalog records static schema dependencies with zero memory of resolution outcomes. Ours shows Table A's trust drops on Tuesdays from vendor lags — and blocks an agent from writing to Table B until it's resolved."*
- *"Monte Carlo already learns patterns."* → *"Rolling thresholds on metrics that don't learn from human resolutions. Resolve a false positive here and it updates decision centroids across all 10 related pipelines."*
- *"Your gold lines are p-hacking."* → *"FDR-corrected and held out 30 days before a line is drawn."*
- **Retire the "Level 3+ is empty for everyone" claim from the room scripts** — replace with *"does the number move because of your decisions?"*

## DD-8 — Preseed additions (add to §5)
A **perturbation fixture** (inject anomalies into a trusted source → trust drops → clean revert + provenance log). A **rejected-rule log** (shadow-tested 45% → rejected) for DI-ADMITS-FAILURE. A **new-source ramp pair** (1st vs 6th, same schema class) for DI-FIRSTVS6TH. A **frozen-model snapshot** for DI-TWIN. An **insufficient-evidence source** (4 decisions) for DI-ABSTAIN. All $/trust magnitudes are **illustrative-from-preseed with provenance badges (F-21/F-22)** — never presented as measured outcomes; show the day-zero state when n < K.

## DD-9 — Buyer/agent-language guard (extend §5)
No centroid/DK/σ/**α·q·V** on any buyer-facing surface or in the agent-API JSON shown on stage — use plain field names (`evidence_sufficient`, `basis`, `recommend`). The conservation math stays in the engineering appendix, not the demo screen.

## Open decisions (flag; don't resolve on stage)
(1) whether L-DATAOPS-DI leads the agent-trust gateway (agent-forward buyer) or the operational-relief/attrition story (non-agent estate) — segment by buyer; (2) the earned-trust/admits-failure beats' LIVE status is gated on DD-0.
