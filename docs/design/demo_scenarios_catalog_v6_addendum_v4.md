# Demo Scenarios Catalog — v6 Addendum v4 (for Codex integration)

**Target file:** `demo_scenarios_catalog_v5.md` (ci_core) → save as `demo_scenarios_catalog_v6.md`.
**Why an addendum:** the catalog is too large to edit in a chat session; these are the exact adds/changes to apply.
**Scope:** 2 new scenarios (DO-09, MACH-06) + 3 inline convergence captions on existing beats + housekeeping (playlists, class rollup, counts, title). No existing scenario IDs are renumbered — both new scenarios append, so nothing downstream shifts.

**Execution rules for Codex:**
- Anchors below are given as **plain readable text**. Match them by their human-readable content and **ignore markdown-escaping differences** (the stored file escapes `#`, `*`, `-`; match the words, not the markup).
- Format every inserted block to **match the surrounding file's own convention** (same escaping, same bullet style, same `###` heading style).
- These are **additive**. Do not delete or reword existing scenarios. Keep all existing honesty riders intact.
- After editing, verify the two endpoint questions flagged in DO-09 and MACH-06 against the code before finalizing the `class` tag; leave the conservative tag if unverified.

---

## REFERENCE (for the convergence captions — context only; do NOT paste this block into the catalog body)

- **rrsi** (Google Research, `github.com/google-research/rrsi`): "Regularized Recursive Self-Improvement." Evolves the agent *harness* around a frozen LLM. Its selection side uses a **noise-adjusted floor that blocks gains inside measurement variance**, a cost rule, and pruning — the same discipline as CI's conservation gate, reached from the other direction. CI's difference: CI reshapes the *decision boundary* from *verified production outcomes* at runtime, under a signable conservation bound.
- **GEPA** (arXiv 2507.19457, ICLR 2026 oral): reflective prompt evolution **outperforms RL at ~90× lower cost** — independent corroboration of CI's own recurrence-ladder null (RL inside the scorer is not the default winner).
- **jev** (Hugging Face, paidaxccc): a "System One" **typed-decision** model — structured state in, a **typed answer + probability + confidence** out (Choice / Score / Noul). Tagline: *"Jev answers the question. Your system owns the move."* This is CI's decision contract; CI's code already emits it (`recommended_action` + `confidence` + `provenance`) and adds a **provenance tier** jev does not have.
- **Honesty rule for all captions:** cite these as *category/direction* convergence, never as our numbers. Different task domains.

---

## ADD 1 — New DataOps scenario `DO-09` (the RSI evolution-gate loop)

**Placement:** in the `# DataOps — Northwind Logistics (Priya Rao, Head of Data)` section, insert immediately **after the DO-04 scenario block** (the one whose gut-punch ends "…without a human asking. That's governance.") and **before** the `### DO-05` heading.

**Insert this scenario (match surrounding format/escaping):**

### DO-09 · "It Tested Its Fixes, Kept Only What Cleared the Floor" · PLANT · ~2:30 · rooms: CDO, risk, VC · [RSI]
- **Stakes:** Priya's real fear about auto-remediation — "if it starts fixing data issues on its own, what stops it from pushing a bad fix across 200 tables?"
- **Turn:** *(setup)* the Runtime Evolution tab for DataOps: a set of candidate fixes under test — AgentEvolver-proposed auto-approve-threshold and scheduling-criteria variants; hold 2s. *(reveal)* the promoted set beside the rejected set — each rejection carries not just a reason code (correctness / conservation / variance) but **per-category accuracy deltas** across the 6 DataOps categories (e.g., "variance: +8% scheduling, −12% permission → net unstable"), so the room sees the system weighing tradeoffs, not checking a single number. One promoted variant shows a **cross-system transfer trail** — originated at `sap_integration`, shadow-tested and promoted at `billing_api` — knowledge compounding across the landscape. Alongside sits a **conservation-boundary panel**: of the 6 categories, 3 at auto-approve confidence, 2 still human-gated, 1 improving toward threshold. **Counts come from the seeded/real ledger — do not hard-code a number; target shape ~7 rejected / ~1 promoted / ~1–2 active across ~8–10 entries.**
- **Gut-punch:** "It kept the one fix that cleared the floor on two different pipelines and threw out the seven that only worked on paper — and for each one it shows you which categories it helped and which it hurt. It knows where it's earned the right to act, and where it hasn't yet."
- **Caption (GATE-STAT):** the promotion gate is the same SDK machinery as SOC-03, configured for DataOps: `promotion_min_samples=50`, `promotion_improvement_threshold=0.05` (the noise floor). Cite DataOps's own config here — the SOC-measured "80.6% power / 4.9% false-promote (1,000-decision window)" is SOC's number, **not** DataOps's; do not reuse it for DataOps absent a DataOps measurement.
- **Surface:** Runtime Evolution (DataOps) → PromotionDashboard, RejectionMomentPanel, + a conservation-boundary (category × automation-eligibility) mini-panel; `/api/evolution/*` (DataOps-scoped). **PW-claim:** promoted + rejected counts render for DataOps with per-rejection reasons, `category_deltas` in each rejection detail, a cross-system transfer trail (`origin_system` → `transfer_target`) on the promoted variant, and a 6-category eligibility panel. **Class note — PLANT (verified against code 2026-10-01):** DataOps evolution already exists — `DataOpsPreset`, `apps/dataops/backend/app/evolution.py` (`DATAOPS_EVOLVER_CONFIG` noise floor `promotion_min_samples=50` / `promotion_improvement_threshold=0.05`, 4 variants in 2 families + a persisted variant), live `GET /api/evolution/variants` (`domain:"dataops"`), the generic SDK loop (driven end-to-end by S2P's `s2p_evolver.py`), and conservation status + per-category accuracy (both already built). **The gap is:** a rejected-with-reasons view (tested / promoted / **rejected** + `rejection_breakdown` + `rejected_variants[]`, **each carrying `category_deltas`**; modeled on Trading's `/rejection-summary`); a seeded ledger of ~8–10 entries with **one cross-system transfer** (`origin_system`/`transfer_target`); the conservation-boundary panel binding; FE wiring; and PW tests. **Check first** whether a DataOps rejection/ledger view already exists before building. Full build spec: companion note `do09_dataops_rsi_demo_note_v2.md`.
- **Convergence caption (technical rooms):** "This is the selection discipline Google's rrsi arrived at independently — a noise-adjusted floor that blocks gains inside measurement variance — running on verified production outcomes under a gate you can sign." *(external reference, not our number)*
- **Honesty:** magnitude pilot-only; tested/promoted/rejected counts must trace to the seeded/real ledger (4 variants today — no fabricated totals; a system that rejects ~7 of 10 with clear reasons is more credible than one claiming 200 tested); the beat shows the loop mostly *declining* candidates — restraint is the point, not volume.

---

## ADD 2 — New Machine scenario `MACH-06` (the jev typed-decision contract)

**Placement:** in the `# The Machine (…)` section, insert immediately **after the MACH-02 scenario block** (the "Reshape, Not Retrieve" beat, whose PW-claim line reads "the no-precedent path renders (shares SOC-02).") and **before** the `### MACH-03` heading.

**Insert this scenario (match surrounding format/escaping):**

### MACH-06 · "The Decision Your Software Can Read" · LIVE · ~2:00 · rooms: CTO, CDO, dev · [jev]
- **Stakes:** the integration architect's real question — "my systems don't need another paragraph; they need a value with a known shape they can branch on." Every LLM tool hands back prose to parse.
- **Turn:** *(setup)* the raw API response for one scored S2P decision on screen. *(reveal)* it is a typed object, not prose: a typed **action** (ACCEPT / ESCALATE / HOLD — a Choice over an approved set), a **confidence** (0.91), and a **provenance tier** on every field (`sample < context < proven < learned`) with the weakest link surfaced — and the **gate, not the model, owns** whether it emits or pauses.
- **Gut-punch:** "No paragraph to parse. A typed decision with a probability your code can route on — and a provenance tier that tells you how much of it was earned. The engine answers; your policy owns the move."
- **Surface:** Exception Triage → ScoreResultCard + provenance block; `POST /api/s2p/score`, `GET /api/s2p/situation/{decision_id}`. **PW-claim:** the response renders a typed action + a confidence + a provenance block (`nl_explanation` / `confidence` / `overall` tiers). **LIVE** — the endpoint returns `recommended_action` + `confidence` + `provenance` today.
- **Convergence caption (CTO/VC):** "jev gives software a typed answer + confidence; this adds a provenance tier jev doesn't have — and runs under a signable gate. The category of 'typed machine decisions' is forming; we're the governed, verified-outcome corner of it." *(external reference, not our number)*
- **Honesty:** if latency is shown, the deep situation-context path is bounded at 8s (not <150ms — that is the routing layer); provenance tiers are the shipped model; demo data illustrative-from-preseed.

---

## ADD 3 — Three inline convergence captions on existing beats

For each, find the anchor line and **insert the new bullet immediately after it**, matching the file's bullet format.

**3a. SOC-03.** Anchor — the bullet ending with: `80.6% power / 4.9% false-promote (GATE-STAT).`
Insert after it:
- **Convergence caption (technical rooms):** "Google's rrsi arrived at the same selection rule from the other direction — a noise-adjusted floor blocking gains inside measurement variance. Ours runs on verified production outcomes, under a gate you can sign." *(external reference, not our number)*

**3b. MACH-02.** Anchor — the PW-claim line ending with: `the no-precedent path renders (shares SOC-02).`
Insert after it:
- **Convergence caption (CTO/VC):** "Two 2025 results bracket this. jev: software wants typed decisions, not prose. rrsi / GEPA: systems improve by governed recursion, not by retraining weights. RGI is where they meet — it reshapes the decision surface from verified outcomes under a conservation bound." *(external reference, not our number)*

**3c. PLAT-05.** Anchor — the line ending with: `K14 stated as experiment (n=240, Sep 2026).`
Insert after it:
- **Optional convergence line:** "The category is forming around us — jev (typed machine decisions), rrsi and GEPA (improve the system without retraining weights). We're the one doing it on verified production outcomes under a signable gate." *(external reference, not our number)*

---

## ADD 4 — Housekeeping (precise find/replace)

**4a. Title.** Find `Demo Scenarios Catalog — v5` → replace `Demo Scenarios Catalog — v6`.

**4b. DataOps playlist.** Find the playlist line beginning `**CDO / DataOps**` (the one reading `DO-01 (which data) → DO-02 … → DO-06 (Jan vs now) close.`). Replace its sequence with:
`DO-01 (which data) → DO-02 (source lost trust) → DO-03 (twelve years in six numbers) → DO-04 (rule proved itself wrong) → DO-09 (kept only what cleared the floor) → DO-05 (K14) → DO-07 (what to buy, ROADMAP) → DO-06 (Jan vs now) close.`

**4c. CTO/Machine playlist.** Find the playlist line beginning `**CTO / The Machine**`. Insert `→ MACH-06 (decision software can read)` immediately after `MACH-02 (reshape not retrieve)` in that sequence.

**4d. Class rollup — LIVE now.** Find the `LIVE now (record immediately):` list and add `MACH-06` to it (near the other MACH entries).

**4e. Class rollup — PLANT.** Find the `PLANT (endpoint exists, seed the data):` list and add `DO-09 (DataOps evolution — seed the rejected-with-reasons ledger; a small rejection-summary surface + FE binding may be needed)`. (Verified 2026-10-01: DataOps evolution already exists — preset, noise-floor config, 4 variants, and `/api/evolution/variants`; the only possible code add is a rejected-with-reasons view, so this is PLANT, not BUILD. Add a BUILD entry only if the rejection-summary check in DO-09 shows that view is missing.)

**4f. Footer count line.** Find `Catalog v5 · 47 scenarios` → replace `Catalog v6 · 49 scenarios`. In the same footer, update the per-domain tallies `DataOps(8)` → `DataOps(9)` and `Machine(5)` → `Machine(6)`. If the footer carries the phrase "one RSI beat per domain", change it to "one RSI beat per domain (DataOps: DO-04 self-demotion + DO-09 evolution-gate)".

**4g. (Optional) Validation-tiers front-matter.** The line beginning `Validation tiers carried from the API check` may optionally gain, in its LIVE list, "typed-decision contract (action + confidence + provenance)". Skip if it risks a merge conflict — it is cosmetic.

---

## Verification checklist for Codex (FINAL STEP)
1. DO-09 and MACH-06 render under their correct domain headings; no existing ID shifted.
2. The three convergence captions each landed after the correct anchor and nowhere else (anchors are unique strings).
3. Playlist, class-rollup, and footer edits are internally consistent (DO-09 class tag matches which rollup list it's in).
4. Endpoint reality confirmed: for DO-09, whether a DataOps rejected-with-reasons view exists (beyond `/api/evolution/variants`) — if not, add a small `/rejection-summary`-style surface modeled on Trading; for MACH-06, `/api/s2p/score` + `/api/s2p/situation/{decision_id}` return typed action + confidence + provenance. Adjust class tags if the code says otherwise.
5. All convergence captions carry the "external reference, not our number" rider.
