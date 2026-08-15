# DataOps Copilot — Design-Doc Additions v1
*Additions to `dataops_copilot_design_v1_8.md` (Drive/design), §29–41. Source: the consolidated 3-review verdict (`dataops_review_consolidation_v1.md`), read as one judgment. **Nothing in the 22 scenarios / 6 capabilities / 6-level hierarchy is removed — every change extends or adds.** Change-specs for a docs session; legal framing is for counsel; the whole earned-trust thesis is gated on the precondition in §0.*

**The decided view (one paragraph).** The category promise *"your data gets smarter every day"* stays as the campaign line — but the **hero and moat is Earned Trust**: an **agent-facing trust gateway** (H6) fused with **governed refusal + self-computing judgment memory** (H4/H3/W2), proven live (perturbation), with **abstention** as the trust API's primary return. The Intelligence Map (W1) is the *visualization* of the machinery; self-valuation (W4) is the *expansion*. The moat is not "we can't be copied" — it's **your estate's accumulated verified judgment** (you can copy the code, not the graph) plus **cross-cloud neutrality** (a substrate owner won't rate a competitor's table fairly).

## §0 — ★ PRECONDITION (add as a build-gate note before §29 ships to buyers)
Earned Trust depends on the **verified-decision → trust-update loop being live for DataOps.** The review reports it may be **configured, not wired** (no production `PromptVariantEvolver` instantiation; `record_outcome` path for DataOps unconfirmed) — which **contradicts §30's "Level-3 core loop 8/8 complete."** Resolve in the repo before any positioning ships: *does a verified DataOps decision measurably move a later trust/score end-to-end today?* No → wiring the loop is the only priority; the surfaces below are windows on a loop that isn't turning.

## §A — Hero + positioning (revise §29 Positioning Statement, §35 Competitive)
- **Keep** the category promise *"Your data gets smarter every day."*
- **Add the hero:** *"Your data estate learns from every verified decision — and every human and agent can see what it has earned the right to trust."* Supporting descriptor: *"A living trust and judgment layer between your data estate and the agents acting on it."* Proof line: *"Watch it learn. See exactly why. See what it rejected."*
- **Reframe the moat (§35).** Retire "they can't build this" → **"They can copy the feature. They cannot copy what your estate has already learned from two years of verified decisions."**
- **Retire "Level 3+ is empty for everyone" as load-bearing** (§35 matrix). It's falsifiable by one competitor release. Replace the competitive axis with one checkable question: **"does the number move because of your decisions?"** Keep the matrix as context, not as the argument.
- **Add cross-cloud neutrality** as the structural "won't": Databricks/Snowflake own the substrate and won't ship an open layer that rates a competitor's table equally — the reason a vendor-neutral trust gateway can be an independent company.

## §B — Provability as a product surface (new subsection; ties to §39A–F reification)
Promote provability from a demo beat to a **product surface — "Proof of Learning" / "no intelligence without receipts."** Fuse SC-TRUST + IKS-attribution + learning-forecast + digest + the rejection log into **one clickable drawer on every number** (trust, IKS, gold line): *computed from N verified decisions · last moved [date] by [named resolutions] · confidence band · **perturb this source →** · what it rejected · why it can / can't be automated.*
- **Honest empty state as a feature:** a source with 4 verified decisions reads *"insufficient evidence — not yet trusted,"* never a fabricated number.
- Build-tags: most is **reification of existing machinery** (§39A); **frozen-twin** and **"what would change my mind?" counterfactual** are **new (small) capabilities**.

## §C — The Agent-Trust Gateway (elevate H6 / D-I14 §36; extend §40 L.5 Trust API)
Make H6 the platform surface, not a feature panel. A **runtime trust gateway between the agent layer and the substrate:**
`GET /v1/trust/verify?entity=…&agent_id=…` → `200 OK` (trust score) or `403 GATED` (abstain / read-only), evaluating trust + provenance + the conservation gate.
- **Abstention is the primary return, not "safe for autonomous use."** Return **evidence + policy state + eligibility**; when evidence is thin, default to a deterministic **abstain / read-only** state. The gateway **enforces the customer's own audited policy thresholds** — it does not warrant truth.
- **Open the interface, not the intelligence:** publish a portable trust request/response schema (and a thin **MCP server** over it) any agent can call; keep the learned evidence graph proprietary. Open protocol + proprietary state.
- **API-language:** plain field names (`evidence_sufficient`, `basis`, `recommend`) — **no α·q·V / Greek in any surface an agent owner or CDO reads.**

## §D — Compounding reframe (revise §30 Level-4 and §41)
Replace "positive second derivative / gets better at getting better" with **acceleration under control**: accelerate far from a robust optimum, damp approaching one, re-accelerate after a regime shift — so governance reads as an *accelerator*, not a tax.
- **Held to the receipts bar:** the **damper** (conservation pausing auto-resolution when quality drops) is showable today; the "accelerate" half needs proof.
- **The falsifiable metric is non-saturating: time-to-competence on a NEW source/schema** (*"1st new source: X weeks to GREEN; 6th: Y days"* — same shape as D-I11), **not** IKS/coverage/accuracy (all saturate). **Frozen twin** is the control.

## §E — Gold-line de-risking (revise §30 Level-6, §33 D-I3/D-I7, §34 Map)
The gold-line dollar figures are the least provable claim and a correlation-mining false-discovery risk.
- **Pull the $ out of the hero path.** Re-render gold lines as **ranked hypotheses to test**, gated by **Benjamini-Hochberg FDR + a 30-day out-of-sample holdout + a domain-expert verification gate** — explicitly unvalidated until they clear.
- **Build a Value Provenance Ledger** (every claimed dollar traceable to observed/reconciled transactions → counterfactual baseline → range → confidence → verifier) **before** any autonomous valuation. Honest empty state: *"value not yet verified — N more outcomes required."*
- For CFO dollars now, use **D-M4 (14-day close → 7)** — realized time, not modeled value.

## §F — New & strengthened scenarios (extend §32/§33; nothing removed)
- **DI-EARNED** ("lose it on stage") · H1/L4 · reification · perturb a trusted source live → trust drops → revert with a provenance log entry.
- **DI-ABSTAIN** ("the system that says I don't know") · H6/L4 · reification · insufficient-evidence → not-yet-trusted / read-only.
- **DI-GATEWAY / DI-MCP** (the trust layer every agent can call) · H6/L4→5 · **new (thin MCP server over the trust API).**
- **DI-FIRSTVS6TH** ("competence, not coverage") · H1/H3/L4 · **new (small)** · time-to-competence 1st vs 6th source.
- **DI-TWIN** ("what March-us would have missed") · H3/H4/L4 · **new (centroid snapshot + replay).**
- **Gemini extensions:** D-I1-EXT cross-source reliability divergence (route through the reliable feed) · D-I3-EXT unqueried correlation (FDR+holdout-gated) · D-I11-EXT cross-pipeline fix transfer · D-I5-EXT self-pausing auto-resolution on schema drift.
- New capabilities to add to the §39 roadmap: **Frozen-Twin evaluator, Value Provenance Ledger, Open Agent-Trust API + MCP server, counterfactual ("what would change my mind?").**

## §G — Compliance (add a ranked subsection; frame, not counsel)
1. **Agent-autonomy liability (highest):** enforce the customer's audited policy + return evidence/eligibility/abstain, never "safe."
2. **Data monetization/licensing (D-I8):** out of buyer-facing story → roadmap slide only.
3. **Cross-tenant learning:** out; **cross-domain within one tenant** is the clean version.
4. **Regulatory (SOX/DORA):** "evidence designed to support your audit/control process," not "makes you compliant."

## §H — Pricing (new subsection)
Do **not** price on alert volume or estate messiness (a model that pays most when the customer is worst off shrinks as you deliver value). Price on **trust-API consumption and governed-source coverage** — both grow as the estate gets healthier and more agentic.

## §I — H1–H6 exploitation notes (extend §36)
H1 self-aware: every trust movement needs cause + provenance + uncertainty. H2 self-combining: **dangerous until FDR + out-of-sample gating** — don't hero raw correlation mining. H3 self-correcting: strengthen by proving **transfer to new pipelines**, not just faster recurrence. H4 self-governing: show autonomy **contracting**, not just expanding. H5 self-valuating: subordinate until the Value Provenance Ledger is mature. H6 agent-ready: make it a **platform/API**, not a panel.

## §J — Open decisions (flag in the doc; don't silently resolve)
(1) front-door emphasis — agent-forward gateway vs operational-relief/attrition-insurance land, likely **segmented by buyer**; (2) how open to make the trust API/standard; (3) pricing model commitment (§H).
