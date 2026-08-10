# JM Reference App + Customer-Value Upgrades — Executable Spec v3

**Date:** 2026-08-08 (v3; supersedes v2)
**v3 changelog:** added **APP-4 — the "Governed vs Ungoverned" RL Differentiation Harness** (DIFFERENTIATION KEYSTONE): a runnable, side-by-side demo that shows *why our RL approach is not a weekend contextual bandit* — the single most-attacked claim in VC diligence. It renders the T-G1 ablation, "governance causes faster improvement," and the safety divergence, all end-to-end. Pairs with APP-1 (APP-1 shows *that* it compounds; APP-4 shows *why it's different*).
**v2 changelog:** added §0 tying this package to the fundraise — the VC judge panel's compounding curve is the artifact the raise turns on, the wedge is **S2P**, APP-1's instrumentation (CC-1/2/3) is the measurement spine of the live S2P pilot curve, and **WP-1 (S2P conservation-bypass fix) is now lead-product-critical.** Added a reuse-don't-rebuild note: SOC already visualizes much of this well — inventory every copilot's tabs first.
**For:** coding session (execute directly) + one narrow LLM poll
**Repos in scope:** graph-attention-engine (GAE), copilot-sdk (SDK), gen-ai-roi-demo / trading (Trading)
**Ranking principle:** value contribution to the customer + credibility to a skeptical buyer — NOT mathematical interest. Every item leads with the customer-value reason it exists.

**How to use:** items are ordered by value. Each has LOCATE (grep anchors, not line numbers — the neo4j→graph_client rename shifted lines platform-wide), CHANGE, VERIFY, and a `[VERIFY-FIRST]` flag where the capability may already exist and must be confirmed against the current working tree before building. Do the VERIFY-FIRST check first; if it already exists, downgrade the item to "surface it in APP-1."

**One-line thesis this whole package serves:** convert "judgment memory compounds" from a claim into something a stranger runs on a laptop in minutes and watches happen — honestly — which is simultaneously the new-user onboarding aid, the JM end-to-end test, and the answer to the zero-day-readiness circularity (you can't show real-customer compounding pre-sale, so you show *honest synthetic* compounding via oracle separation, and ship the instrumentation that turns the customer's own pilot into the first real proof).

---

## 0. Why this matters NOW — the two things that move the needle (the fundraise connection)

A four-model VC judge panel (Gemini, GPT, Grok, Opus) converged on one point: **the single artifact that funds this company is the compounding curve** — performance vs. verified-decision-count (V=0→500) against a frozen non-learning baseline, tied to dollars, showing that *governance causes faster improvement, not merely constrains it.* Two founder-level moves follow, and they reset this package's priority:

1. **The wedge is S2P / procurement (3–1 across the panel).** It's the only wedge where the counterfactual dollar is directly CFO-auditable (PO savings, cycle time, maverick spend), where "your SAP gets more valuable" is literally true, and where the buyer already has a budget line for governed decisioning — and it's the founder's deepest domain (retail / supply-chain / procurement). Lead S2P; the other copilots are proof-of-generality, not five GTM motions.

2. **The real work all four judges point at: instrument ONE S2P pilot to produce the compounding curve.** This is bigger than the pitch, and it is what this package exists to enable. APP-1's honesty harness proves the *dynamics* on synthetic data pre-sale; the **same instrumentation — CC-1 (`centroid_distance_to_canonical`), CC-2 (ε_firm), CC-3 (IKS)** — is exactly what you point at the live S2P pilot to turn it into the *first real* compounding curve (pilot N becomes the proof for sale N+1). Build the measurement spine once; it serves both the demo and the raise. **This elevates CC-1/CC-2/CC-3 from "supporting surfaces" to the highest-priority items in the package.**

3. **If S2P is the wedge, WP-1 (the S2P conservation-bypass fix) is LEAD-PRODUCT-critical.** S2P's promotion currently passes a literal `conservation_state="GREEN"` instead of fetching live state — the one place the code is weaker than the "conservation-gated" claim. On the lead product, in front of a technical VC or a live pilot, that gap is a claim-breaker: fix it **before** the S2P pilot's curve is shown or the repo is walked. (Detail: the RL consolidation work package WP-1; boundary context: the SOC-G1 decision memo.)

**Reuse, don't rebuild — inventory every copilot's tabs first.** Before building APP-1's rendered surfaces from scratch, open the running apps and **check the tabs of all five copilots — the SOC copilot in particular already has a very well-visualized version** of much of this legibility story (compounding / IKS-style / conservation panels). Screenshot and inventory each copilot's tabs, lift SOC's visual patterns into APP-1's `report.html` and the S2P pilot surfaces rather than reinventing them, and record which surfaces are already live per copilot (this also feeds WP-4 telemetry parity in the RL consolidation package). The goal is one consistent, reused visual language across the demo, the reference app, and the pilot — not a new one.

---

## Part 1 — Apps to build (ranked)

### APP-1 — Judgment Memory End-to-End Reference App  *(KEYSTONE)*

**Customer value:** the single build that does the most. It (a) onboards a new GAE/SDK user with a 5-minute "watch it compound" first run, (b) is the JM end-to-end integration test across all loops, (c) is the demonstrable-compounding proof that sidesteps the circularity, and (d) exercises AgentEvolver (the least-proven loop) in the same harness. It is also the container into which every Part-2 surface (IKS, ε_firm, conservation panel, measurement_state) gets rendered — so building it forces those surfaces to be real.

**Location:** `copilot-sdk/examples/jm_reference/` (new dir). Depends only on copilot-sdk + gae. SQLite default, zero server.

**Honesty invariant (non-negotiable, from `synthetic_data_generation_analysis_v2.md`):** oracle separation. The synthetic generator produces **factor vectors only**; a **math oracle** labels correctness from centroid distance to a hidden ground-truth centroid. The LLM/generator NEVER sets `is_correct`. This is what makes the demonstrated compounding real dynamics rather than a generator-competence artifact. A test must assert the generator has no path to the correctness label.

**LOCATE (reuse existing symbols — do not reimplement):**
- Scorer construction: grep `def from_preset` in `copilot_sdk/scoring/scorer.py` → `CompoundingScorer.from_preset(domain, db_path=..., graph_store=..., profile=...)`.
- Store: grep `class SQLiteGraphStore` / `class InMemoryGraphStore` in `copilot_sdk/graph`. Use SQLite for the default run.
- Outcome write: grep `def write_outcome` (GraphStore protocol). Correctness flows in here.
- Conservation: grep `def conservation_status` in `gae/calibration.py` and `def _evolution_conservation_state` in `copilot_sdk/scoring/scorer.py`.
- Measurement state: grep `def compute_measurement_state` in `copilot_sdk/scoring/measurement_state.py`.
- Convergence stats: grep `def _conservation_stats` in `copilot_sdk/scoring/scorer.py`.

**CHANGE — build these modules:**
1. `generator.py` — synthetic factor-vector generator. Cold-start and post-disruption vector regimes (per Experiment A: per-factor within-batch variance > 0.02, regime differentiation). Deterministic by seed. Emits `(category, factor_vector)` only — no label.
2. `oracle.py` — ground-truth centroid `GT` per (category, action); `label_correct(chosen_action, factor_vector) = argmin_action ‖factor_vector − GT[category,action]‖ == chosen_action`. `ε_firm` is a config knob = normalized ‖GT − canonical_prior‖; default set **> 0.128** (genuine-learning regime) with a documented second config **< 0.128**.
3. `run.py` — the loop, using real SDK calls: `score()` → `oracle.label_correct()` → `write_outcome()` → centroid update (Level 1) → after ~200 decisions DK-weight learning (Phase 2) → `conservation_status()` each step → inject one category-sparse disruption at a set decision → trigger one AgentEvolver variant promotion through its four-condition gate.
4. `report.py` — prints trajectory and writes `report.json` + a single self-contained `report.html` (no external deps) rendering the surfaces below.

**Surfaces it must render (these ARE the product's legibility story):**
*(Reuse-first: inventory every copilot's tabs before building these — SOC already visualizes much of this well; lift its patterns, don't reinvent. See §0.)*
- `centroid_distance_to_canonical` over decisions (the clean, model-independent convergence signal — see CC-1) — must decrease monotonically.
- IKS rising curve (see CC-3).
- measurement_state ladder: 0 → INSTRUMENT_VALIDATED → ACCUMULATING → MEASURED (provenance `real_measured`, never `sample`).
- conservation status GREEN/AMBER/RED with α, q, V, θ_min and the 0.7×-baseline relative trigger (see CC-4).
- ε_firm measured, annotated against the 0.128 threshold (see CC-2).
- DK-weight concentration (3–4 of 6 dims) and per-factor σ noise fingerprint.
- one AgentEvolver promoted variant with its measured before/after decision-quality delta.

**Two-run honesty demo:**
- Run A (ε_firm > 0.128): Phase 1 genuine learning; after a category-sparse disruption, Phase 2 re-converges in fewer decisions → γ > 1 shown, measured on centroid-distance convergence (not noisy N_half).
- Run B (ε_firm < 0.128): γ ≤ 1 → visibly demonstrates the claim is *conditional*. Shipping both is the credibility move.

**VERIFY (acceptance):**
- One command, SQLite, no server: `python -m examples.jm_reference.run`.
- `centroid_distance_to_canonical` monotone-decreasing every phase/seed (the doc's invariant).
- Run A: N_half,2 (centroid-distance basis) < N_half,1; Run B: not. Assert both.
- measurement_state transitions correct; provenance `real_measured` at coverage.
- `test_oracle_separation`: generator has no code path that writes `is_correct`.
- Full loop touches Level 1, Phase 2, conservation, and one AgentEvolver promotion (assert an evolution event was written).

---

### APP-2 — `hello-gae` zero-infra quickstart sample  *(onboarding, small)*

**Customer value:** the 5-minute first success that decides whether a fresh open-source user stays or bounces. Smaller and simpler than APP-1 — the "does this even run on my machine" artifact.

**Location:** `graph-attention-engine/examples/hello_gae/` (new). SQLite-only, no Neo4j/AGE server.

**CHANGE:** ~40-line script: build a store, write ~10 decisions on a toy 3-category domain, run one `conservation_status()`, print the graph + status. Plus a `README.md` with copy-paste `pip install` → `python hello_gae.py`. Fold in the hardcoded-URL/port fix (grep `BACKEND_PORT`, `CORS_ORIGINS`, `localhost:80` across `apps/*/frontend` and `demo.py`) so a clean checkout runs without editing source.

**VERIFY:** fresh clone + `pip install` + run, no server, no source edits, exits 0 with a readable graph + GREEN/AMBER/RED line.

---

### APP-3 — Trading "clone-and-compound" variant  *(later; highest adoption pull, highest attack surface)*

**Customer value:** the most compelling OSS artifact — "point it at your data, watch it compound" — and the fastest way to manufacture real compounding curves at scale (breaking the circularity across many users, not one pilot). Gate it behind the connector-safety pass.

**CHANGE:** APP-1's harness retargeted to the Trading domain/preset, on synthetic-but-honest market factor vectors (oracle separation preserved). **Gate:** connectors default to paper-trading/read-only, no live-order path, no key required to run; seed data synthetic (not redistribution-limited vendor data). Do the secrets sweep (grep `api_key`, `secret`, `ALPACA`, `token`, `.env` across Trading + demo.py) before any public commit.

**VERIFY:** runs with zero credentials in paper/synthetic mode; no code path reaches a live order without explicit opt-in; secrets sweep clean.

---

### APP-4 — "Governed vs Ungoverned" RL Differentiation Harness  *(DIFFERENTIATION KEYSTONE — pairs with APP-1)*

**Customer value / why it exists:** APP-1 shows *that* judgment compounds. APP-4 shows *why our RL approach is different from a contextual bandit / reward-maximizer a competent team could build in a weekend* — which is the single most-attacked claim in VC diligence and the first thing a technical co-investor probes ("isn't this just RL with a graph?"). It converts that answer from an argument into something a skeptic runs and watches. It is the runnable form of the diligence FAQ answers A1 (learns-the-reward + ablation), A2 (governance causes improvement), and C2 (the inverted demo).

**Location:** `copilot-sdk/examples/rl_differentiation/` (new). Reuses APP-1's oracle-separated `generator.py` + `oracle.py` + the SDK scorer/evolution. SQLite default, zero server.

**Honesty invariant (non-negotiable — a hostile reviewer's first attack is "you strawmanned the baseline"):** all arms run on the **same oracle-separated data and seed**; the reward-maximizer baseline must be a *legitimate, well-implemented* contextual bandit / reward-maximizer over the same reward function — **not** a crippled one. The differentiation must come **entirely from the decision + governance architecture**, never from the data or a handicapped baseline. A test asserts the baseline is a faithful argmax-reward learner.

**Three arms (same domain, same seed):**
1. **CI (governed):** centroid decision + conservation-bounded exploration (proposal-only) + conservation-gated promotion — the real system.
2. **Reward-max baseline:** action = argmax over the reward function (a faithful contextual bandit); no centroid decision, no conservation gate.
3. **Hand-specified-reward ablation:** CI's architecture, but the reward/objective is hand-specified and frozen instead of learned — isolates the contribution of "learns the reward."

**Surfaces it must render (the differentiation, end-to-end, side-by-side):**
- **T-G1 — decision ≠ reward-maximizer (the ablation the judges demand):** swap the reward-function config mid-run; CI's recommended action + probabilities are **unchanged** for a fixed input; the reward-max baseline's action **flips**. Assert both. This is the runnable proof of "the decision is centroid, not reward-driven." *(Runs on the clean centroid path — exploration proposal-only, i.e. the SOC-G1 A/C target state; this app assumes and validates that state.)*
- **Governance causes faster + more robust improvement (Opus's bar):** decision-quality vs verified-decision-count for all three arms against a frozen non-learning baseline. Expected shape: CI separates from the frozen baseline and **stays robust** through an injected regime shift; the reward-max baseline wins **early** then **collapses** when an adversarial "quiet quarter" / regime shift is injected (Goodhart overfit); the hand-specified-reward arm trails CI (the learned objective does real work).
- **The safety divergence (the counterfactual cost of no governance = the inverted demo):** inject one self-proposed rule that scores **+8% in aggregate but −30% on the high-severity slice**. CI's gate **rejects** it with a real reason code (the Rejection Moment); the reward-max arm **promotes** it → and its quality then visibly collapses. Show the promotion arc first, the rejection second — this is exactly the pitch's inverted demo.
- **Second-order control:** CI's improvement rate accelerates then damps (converges robustly); the ungoverned arm oscillates/overshoots — the "we control learning, not just optimize it" story, made visual.

**VERIFY (acceptance):**
- One command, SQLite, no server; `report.html` renders the three-arm side-by-side.
- T-G1: assert CI action + probabilities invariant to a reward-config swap; assert the reward-max baseline's action flips.
- Governance-causes-improvement: assert CI's post-regime-shift quality > reward-max baseline's; assert the reward-max arm collapses after the injected shift; assert CI > the hand-specified-reward arm.
- Safety divergence: assert CI's gate rejects the poisoned rule (reason code present) and the reward-max arm promotes it and then degrades.
- `test_baseline_is_faithful`: the reward-max baseline is a legitimate argmax-reward learner, not handicapped (guards the honesty invariant).

**Ties to the fundraise:** point a technical VC at this instead of arguing the "isn't this a bandit" question. It also produces the assets for the pitch's inverted demo and for FAQ A1/A2/C2.

---

## Part 2 — Customer-value code changes (ranked, tagged by repo)

Each leads with the buyer-facing value. `[VERIFY-FIRST]` = confirm it doesn't already exist in the current tree before building.

### CC-1 — `centroid_distance_to_canonical` logging  *(SDK)*  — measurement spine
**Value:** turns "it compounds" from asserted to *measured*, on the one signal that's clean regardless of model or seed. Your own doc calls this "the single most important addition before pilot Day 1." APP-1 needs it; a real pilot needs it; they share it — which is what lets pilot N become the proof for sale N+1.
**LOCATE:** grep the decision/outcome logging path (BACKLOG-015 fields, rolling-accuracy / N_half logging) and the centroid store: grep `def write_outcome`, `def save_centroids`, `load_latest_centroids`. Canonical centroid: grep the expert-prior / `from_preset` centroid init and `CANONICAL` / `soc_calibration_profile`.
**CHANGE:** compute `np.linalg.norm(mu_current − CANONICAL_CENTROID)` (Frobenius over the centroid tensor) per verified decision; persist as a decision/diagnostic field. Add companion fields from the doc when cheap: `pattern_history_value`, `alert_category_distribution` (rolling-100 category mix).
**VERIFY:** field present per verified decision; monotone-decreasing under the APP-1 learning run; unit test on a synthetic converging sequence.

### CC-2 — ε_firm measurement + diagnostics surface  *(SDK / GAE)*  — protects the most attackable claim
**Value:** the re-convergence (γ>1) claim rests entirely on ε_firm > 0.128, and today ε_firm is a *deployment estimate*, not a measurement. Measuring it in week one and conditioning the promise on it converts a fragile assumption into a per-customer promise you can keep — and into a selling point ("we measure whether your environment clears the threshold"). `[VERIFY-FIRST]` — check for any existing `epsilon_firm` / `eps_firm` symbol.
**LOCATE:** grep `epsilon_firm`, `eps_firm`, `canonical` in SDK/GAE; centroids via `load_latest_centroids`; canonical prior via the preset expert-prior init.
**CHANGE:** `compute_epsilon_firm(domain) = normalized ‖μ_current − μ_canonical‖`; expose in the diagnostics/measurement surface (grep `diagnostics_models`, `measurement-state` endpoint) with the 0.128 threshold and a boolean "clears re-convergence threshold."
**VERIFY:** endpoint returns ε_firm + threshold flag; APP-1 Run A reports > 0.128, Run B < 0.128.

### CC-3 — IKS (Institutional Knowledge Score) as a first-class metric + endpoint  *(SDK)*  — the CFO/CISO's single number
**Value:** the buyer-legible proof of compounding — one number that rises as the system learns their environment. The blog already defines it; making it a live, exposed metric is direct customer value (a rising IKS is what a board sees). `[VERIFY-FIRST]` — grep `IKS`, `institutional_knowledge`.
**LOCATE:** centroid drift over the canonical prior (same inputs as CC-1/CC-2).
**CHANGE:** `IKS(t) = 100 · min(D(t)/κ*, 1.0)` where `D(t)` = mean centroid drift (Frobenius over cells); expose via `GET /api/{domain}/iks` and in diagnostics. Reuse CC-1's distance computation.
**VERIFY:** IKS = 0 at deployment, rises monotonically in APP-1 Run A, plateaus at firm-specific optimum; endpoint 200.

### CC-4 — Conservation status as an explainable panel payload  *(SDK)*  — the trust instrument that sells automation expansion
**Value:** the conservation law's value is *regulatory/trust*, not mathematical — it's what lets a buyer expand auto-close 15%→40% with a defensible story (EU AI Act Art. 9). Its value is realized only if it's *shown and explained*: status + the α·q·V vs θ_min headroom + the 0.7×-baseline relative trigger, with the "auto-pauses if accuracy drops below 0.7× its own baseline" narrative. `[VERIFY-FIRST]` — `conservation_status` exists; check whether a buyer-facing payload (status + components + relative-trigger baseline) is already exposed.
**LOCATE:** grep `def conservation_status`, `def check_conservation`, `update_conservation_state`, `get_conservation_state`.
**CHANGE:** ensure the exposed payload includes: status, α, q, V, θ_min, signal (α·q·V), headroom, baseline, relative-trigger threshold (0.7×), and a plain-language reason. Frame as "auditable safety gate," not "mathematical guarantee" (the demo RISK-2 reframe).
**VERIFY:** payload complete; APP-1 renders a GREEN→AMBER pause→recovery arc when a disruption is injected.

### CC-5 — Surface `measurement_state` in app/diagnostics  *(SDK)*  — "measured, not sampled" honesty, already built
**Value:** the day-zero honesty mechanism that makes a fresh install trustworthy (INSTRUMENT_VALIDATED instead of a fabricated number). Already SHIPPED in `measurement_state.py` — this item is *exposure*, not new logic.
**LOCATE:** grep `compute_measurement_state`, `MeasurementState`, `measurement-state` endpoint.
**CHANGE:** ensure APP-1 and the diagnostics surface render the ladder + provenance; no new math.
**VERIFY:** APP-1 shows 0→INSTRUMENT_VALIDATED→ACCUMULATING→MEASURED with provenance `real_measured`.

### CC-6 — θ_min hygiene  *(GAE)*  — pre-OSS credibility (do before any public commit)
**Value:** narrow but real — a skeptical buyer diffing the open-source math will find the code's own comment calling its published formula "structurally incorrect." Clean it so due diligence doesn't trip. Not a research task.
**LOCATE:** grep `def derive_theta_min`, `def compute_theta_min`, `three-judge consensus` in `gae/calibration.py`.
**CHANGE:** (a) delete/rewrite the stale April-16 note in `derive_theta_min` (it endorses the retired constant and calls the live 23.53/(α·V) wrong); KEEP the deprecation warning below it. (b) Reconcile α to category coverage across call sites — grep `verified_count / total`, `1 / ` n_categories, `conservation_status` — so α matches `check_conservation()` (the blog's own publication gate). (c) Consolidate the 3 `compute_theta_min` impls (None/raise/inf) into one shared function.
**VERIFY:** one θ_min impl; α semantics identical across call sites; existing θ_min tests still pin 0.4706 at (0.25,200); no comment contradicts the published formula.

### CC-7 — Zero-infra SQLite default + clean fresh-checkout run  *(SDK / Trading)*  — onboarding-critical
**Value:** for a runnable OSS product, the hardcoded-URL/port issue is promoted from cosmetic to "does a stranger's first run work." Gates adoption.
**LOCATE:** grep `BACKEND_PORT`, `CORS_ORIGINS`, `localhost:8`, hardcoded URLs across `apps/*/frontend/src` and `demo.py`; store default selection (SQLite vs AGE) in `from_preset` / app main.
**CHANGE:** SQLite is the no-config default (no Neo4j/AGE server required to run examples); read ports/URLs from env with working defaults.
**VERIFY:** fresh clone runs APP-1 and APP-2 with no server and no source edits.

**Deferred / gate items (not now, but tracked):** FreshScorerProxy per-call scorer reconstruction (grep `class FreshScorerProxy`; `scorer_cache_plan.md` ready) — matters when APP-3/Trading runs under real concurrency; AgentEvolver variant-promotion ledger surface — high value as the Level-2 proof, spec after APP-1 exercises one promotion end to end.

---

## Part 3 — LLM poll (narrow, ready to dispatch)

Poll only where independent review genuinely de-risks the build. Do NOT poll the ranking (a made judgment call) or CC-6 (settled).

**Q1 — Honesty harness (the core question):** "We will ship a Judgment-Memory reference app that demonstrates compounding on synthetic data using oracle separation (LLM/generator produces factor vectors only; a math oracle labels correctness from centroid distance to a hidden ground truth). Convergence is shown via `centroid_distance_to_canonical` (monotone), not N_half. Is this the right *minimal* construction to convince a skeptical technical buyer that the demonstrated compounding is real dynamics and not a generator-competence artifact? What is the smallest addition that would most increase its credibility, and what is the most likely way a hostile reviewer discredits it?"

**Q2 — ε_firm measurement:** "We define ε_firm as normalized ‖μ_current − μ_canonical‖ (Frobenius over the centroid tensor), used to test whether a deployment clears the γ>1 re-convergence threshold (~0.128). Is this a sound, buyer-defensible way to measure firm-specific deviation from the canonical prior at pilot week 1, and what confound most threatens it?"

---

## Part 4 — Suggested execution order

**Priority reset (v2):** the compounding curve is the fundraise, so the measurement spine (CC-1/CC-2/CC-3) leads and doubles as the live-pilot instrumentation.

0. **WP-1 — S2P conservation-bypass fix** (from the RL consolidation package) — lead-product-critical if S2P is the wedge; gate the S2P pilot's curve on it.
1. **CC-1** (centroid_distance_to_canonical) + **CC-2** (ε_firm) + **CC-3** (IKS) + **CC-6** (θ_min hygiene) — the measurement spine of BOTH APP-1 and the live S2P pilot curve; CC-6 clears the OSS credibility gate. Build once, point at both synthetic (APP-1) and the pilot.
2. **APP-1** (JM reference app) — the keystone; pulls in CC-4/CC-5 as rendered surfaces (build or verify-and-surface). Reuse SOC's tab visualizations (§0).
2b. **APP-4** (RL differentiation harness) — the differentiation keystone; reuses APP-1's generator/oracle. High priority for the fundraise: it's the runnable answer to "isn't this a bandit" and it produces the pitch's inverted-demo assets. Build right after APP-1's harness exists.
3. **Instrument the live S2P pilot with CC-1/2/3** → the first real compounding curve (governance-causes-improvement: curve the governed run against a frozen baseline). *This is the artifact the raise turns on.*
4. **CC-7 + APP-2** (zero-infra quickstart) — makes a stranger's first run work.
5. **Dispatch the 2-question LLM poll** in parallel with APP-1 (its answers refine the harness, not block it).
6. **APP-3 (Trading)** + connector-safety gate — after APP-1 proves the harness and the OSS-math is clean.

---

## Provenance & assumptions (honest)

- Symbol/path anchors are grep patterns, not line numbers, by design — the neo4j→graph_client rename shifted lines platform-wide. Confirm each against the current working tree (the Drive mirror lags the coding session's tree).
- `[VERIFY-FIRST]` items (CC-2 ε_firm, CC-3 IKS, CC-4 conservation payload) may already exist in part; check before building and downgrade to "surface in APP-1" if so.
- `measurement_state` (CC-5) is confirmed shipped and tested; it is exposure work, not new logic.
- The γ theorem, oracle-separation method, ε_firm threshold (~0.128), and `centroid_distance_to_canonical` as the clean signal are all from `synthetic_data_generation_analysis_v2.md` (CC-21 Tier 2). The reference app demonstrates the theorem's *direction* honestly; the *magnitude* remains a real-pilot (EXP-G1) quantity — do not let APP-1 imply a measured γ magnitude.
