# CI Session Onboarding Note v4

**Last updated:** September 14, 2026 · **Supersedes:** v3 (Aug 31 — that note describes the LinkedIn-post /
graphics campaign and is stale for current work). **For:** a new Claude session picking up the CI work.
**Read this first, then the current docs in `ci_core`.**

---

## 1. What CI is (30-second orient)
Compounding Intelligence (CI): an enterprise-AI platform of **five domain copilots** — SOC (security
triage), S2P (source-to-pay), Trading, Purchasing, DataOps — on one shared substrate: **GAE**
(Graph Attention Engine; graph + prototype-scorer math) + **copilot-sdk** (the scoring/learning loop). The
one-line thesis: **most AI is static (alert #10,000 handled like #1); CI compounds — it gets measurably
better at the firm's own decisions from verified outcomes.** "Day 90 ≠ Day 1."

## 2. The current framing (this is what's new since v3)
- **RGI = Recursive Graph Improvement** — the coined term for CI's property: the decision geometry on the
  graph reshapes from *verified outcomes* and reasons better because of it. It is a **governed, bounded
  instance of Recursive Self-Improvement (RSI)**: L1–L3 demonstrated, **L5 (self-rewriting the objective)
  excluded by design** (self-poisoning risk). Abstraction direction: **CI-VLD ⊂ RGI ⊂ RSI** (CI-VLD is the
  *reference instance*; RGI the category; RSI the field agenda).
- **VLD** = the inference-time investigation mechanism: before committing, the scorer reads the 2–3 pieces
  of evidence its own geometry says are decisive (no LLM in the loop). **VLD-the-mechanism is commodity
  now** (adaptive/recurrent retrieval is a crowded 2025–26 area — RLT, 2607.07380, L2M); **the moat is the
  substrate it runs on** (verified-outcome-compounding judgment, conservation governance, no-LLM, firm-
  specific geometry). Claim the *composition*, never the mechanism.
- **The market is day-zero:** customers expect readiness before their data exists and won't grant
  experimentation windows. So **rigorous synthetic substantiation is a product capability**, not a
  placeholder. Substantiate *capability + mechanism* synthetically; **magnitude is pilot-only (T-R) and is
  never synthesized** — the honest boundary is itself the moat ("no vendor can hand you your magnitude on
  day one").

## 3. Evidence tiers (use these exactly; do not overstate)
- **REAL_COMPONENT** — exported production geometry (centroids, factor structure, σ, τ).
- **SIMULATED** — streams, decisions, verification, label sources.
- **GEOMETRY-DERIVED** — correctness computed from nearest-centroid distance over exported geometry
  (**this is what all current VLD experiments use** — NOT LLM-labeled; there is no LLM prior to remove).
- **T-R (pilot-only)** — real verified deployment outcomes; the true top tier, not synthesizable.
Honest labeling sentence for the paper: *"correctness is nearest-centroid assignment over exported
geometry — deterministic, no annotator/LLM variance; the limitation is that it is synthetic."*

## 4. Standing rules (always apply)
- **Honesty tiering (F-24): no claim above its evidence tier.** Retractions are a feature for this
  adversarial audience (CISOs/auditors/technical VCs).
- **"Operating envelope"/"boundary," never "failure" or "characterized negative."**
- **No git; no source-file modification** in experiments — new scripts + results only; reuse existing
  harnesses; `random_state` swept; deterministic JSON + two-rebuild check; pre-register metric before
  running; STEP-0 read-gate before any run.
- **Metric names are not interchangeable:** `routing_quality` ≠ `category_accuracy` ≠ `action_accuracy` —
  name which one every time (they disagree).
- **Frozen files** (`scorer.py`, `investigation.py`, `investigation_router.py`) are call-not-modify;
  `profile_scorer.py` (GAE, class `ProfileScorer`) is a *different* file, callable not modifiable.
- **No superintelligence framing.** Bounded/governed beats maximally-recursive for this audience.
- S2P + restaurant purchasing lead GTM; trading = open-source community; SOC + DataOps = expansion (and the
  strongest RGI signal).

## 5. Current state of the work (Sep 14)
**The main effort is the VLD/RGI technical paper** (good technical paper with good positioning — NOT a
position paper) and its outreach front.
- **Pre-paper:** `ci_vld_architecture_prepaper_v10.md` (evidence base) + the **Impact Core**
  `ci_rgi_impact_core_v7_3.md` (outreach front). Both under active revision.
- **Astra reviewed v7.3** (thorough, adversarial): found the printed conservation gate broken *as written*,
  headline ranges dropping S2P, tier leaks, and several recomputable defects. A change-list is in progress.
- **Experiments run & consolidated** (all REAL_COMPONENT + GEOMETRY-DERIVED, single-or-multi-seed):
  - **Moat (B2, corrected from a flawed B1):** an independent competitor on a *different* firm's stream does
    **not** reach parity on the incumbent's decisions — **routing gap SOC 19.6±5.4pp, DataOps 5.7±1.1pp,
    0/5 seeds parity** (EXP-1). **Labels are the asset** (gap closes only with ~50% of the incumbent's
    *labeled* stream). Moat is **routing-level data-specific** for both; **judgment-level (μ) specific for
    SOC (+15.9pp, 3/3 seeds), routing-only for DataOps** (EXP-2). Migration possible but with measured
    staleness cost. *Bimodal by evidence-richness — report it, don't average it.*
  - **Baseline (C1/PAPER-EXTERNAL):** VLD within **1.40pp** of a trained RF on category at matched budget
    **with zero labels**; ties on action. Honest headline = *matched-budget zero-label parity*, not raw
    supremacy.
  - **Calibration (C6):** held-out risk-coverage done for DataOps/Purchasing/SOC; post-investigation
    confidence works, surface signals fail; Trading/S2P pending.
- **Campaign v2 in flight** (`vld_strengthening_campaign_v2.md`): C2 μ×5, C3 label-breadth, C4 γ
  re-convergence (harness-existence gate; do NOT run the K-curve and call it γ), C5 conservation
  detection-lag, C7 looped-transformer (L1 tests A0; L3 matched-compute breadth), C8 action-value boundary
  (VLD action-value is **conditional on trained geometry** — on-record). **C1 oracle-sep deprioritized to
  P2** (labels already geometry-derived → not the tier upgrade once assumed).

## 6. Two live corrections a new session must know
1. **The moat wording is NOT "un-copyable."** It is **"deployment- and data-specific at the routing level
   (both copilots) + judgment-level for SOC; verified-outcome labels are the specific asset; migration has
   a measured switching cost."** (B1's "moat collapses" verdict was an artifact of a same-stream design
   flaw and is void.)
2. **The day-zero / honesty-is-the-moat argument rests on GEOMETRY-DERIVED-synthetic labels, NOT on
   LLM-identifiability.** The γ-identifiability result applies to a *separate* LLM-persona data track, not
   the VLD experiments. Do not carry the LLM-prior justification into the VLD paper.

## 7. Core document suite (resolve current versions from `ci_core.txt` — versions move)
1. **cga_arxiv_short** — arXiv math paper (conservation law, σ⊥μ two-engine separation, re-convergence γ).
2. **math_synopsis** — the claim/status ledger (proven / validated / boundary / retracted, at tier); the
   authoritative "what may be claimed."
3. **innovation_note** — innovation / IP / moat positioning.
4. **graph_native_reasoning_hero** — hero narrative (Stryker cold-open; read/route/reshape).
5. **graph_native_separation_block** — graph-engineering (read/route) vs graph-native reasoning (reshape).
6. **jm_paper_draft** — Judgment Memory as the fourth cognitive type (synthetic-tier).
7. **ci_blog** — public long-form (three generations; four clocks / four memory types; Read·Route·Reshape).
8. **rl_sdk_design** — domain-neutral RL control plane in `copilot_sdk/rl/` (reward / credit /
   conservation-bounded exploration); judgment scoring authoritative, RL confined to the sidecar.
9. **ci_rgi_impact_core (v7_3)** — the outreach front for the pre-paper.
Plus: **ci_vld_architecture_prepaper (v10)** = the VLD evidence base; the **MAP VLD Addendum** (latest).

## 8. Environment (for coding sessions)
`Set-Location "C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"`
then activate `...\proj-envs\python_expts_venv\Scripts\Activate.ps1`. Repos: copilot-sdk (shared runtime +
apps), gen-ai-roi-demo (SOC), s2p-copilot, graph-attention-engine. Experiment results → `experiments/vld/results/`.

## 9. Next actions (priority)
1. Land the in-flight campaign (C2/C3/C4/C5/C7/C8); analyze — **watch C7 (L2>L0 would revise the core
   thesis) and C8 (bounds the action-accuracy claim)** hardest.
2. Apply the paper change-list from the Astra review: **conservation → SDK composite gate** (Check-A
   75%/last-100 floor + Check-B cold-start signal); **moat → §6.1 wording**; **headline → budget-matched
   zero-label parity**; tier tags per-exhibit; math/precision fixes; length cut to a technical paper.
3. Propagate the **GEOMETRY-DERIVED** tier language + the corrected day-zero justification into the pre-paper
   (replace any "ORACLE-SEP"/LLM-identifiability wording).
4. Render the three figures (five-domain K-curves incl. S2P dip; moat catch-up; held-out risk-coverage).

## 10. Working style (what the operator expects)
Multi-response for big edits (don't try to update a large doc in one shot); ask for clarification when a
choice changes the output; put enough math/routing formalism in even where the audience won't parse it (it
builds credibility); LLM-judge / adversarial-question passes are used heavily and are welcome; **discuss
before weakening any capability claim — redesign the experiment instead.**
