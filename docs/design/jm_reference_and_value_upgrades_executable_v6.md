# JM Reference App + Customer-Value Upgrades — Executable Spec v6

**Date:** 2026-08-08 (v6; supersedes v5)
**v6 changelog (correctness fix):** the v3–v5 spec said `centroid_distance_to_canonical` "must decrease monotonically" — **that was wrong; it conflated two different distances.** Distance to the **canonical prior INCREASES** during learning (the production learning signal, same basis as IKS/ε_firm — "how much has it learned from its starting point"). Distance to **ground truth DECREASES** during learning (the convergence proof; oracle-only). The reference app now tracks **both**, side by side; the "monotone-decreasing" convergence claim applies to the **ground-truth** distance only. Live pilot / buyer curve = IKS (canonical-distance rising); the decreasing ground-truth curve is the oracle-backed proof that learning is toward the *right* thing. CC-1 updated to log both (~0.5d, APP-1 polish). See CC-1.
**v5 changelog:** added **APP-5 (Level-2 YAML config)** and **APP-6 (Level-3 build-your-own copilot template)** — the two examples the **open-source copilot SDK (a.k.a. cdk-copilot / the CDK)** needs for the *"how do I make it mine?"* adoption path, mapped to the three-level adoption model. APP-6 ships **two** neutral starter domains — **personal email/inbox triage** + **reading/watch-later backlog triage** — same triage shape over one shared harness (two skins = the portability lesson; reuses the SOC triage decision-shape; synthetic metadata only), with the governed-vs-ungoverned toggle at the SDK level. `hello-copilot` (Level-1 15-liner) and a feature **cookbook** noted as tracked-but-later. See §0.7.
**v4 changelog:** **APP-4 is now a FULL DOMAIN APP** — an S2P (procurement) application built on the existing S2P copilot (real invoice/PO/supplier decisions, full backend + frontend, SOC-reused visualizations), not a synthetic CLI harness. Gate on WP-1.
**v3 changelog:** added **APP-4 — the "Governed vs Ungoverned" RL Differentiation Harness** (DIFFERENTIATION KEYSTONE): shows *why our RL approach is not a weekend contextual bandit*. Pairs with APP-1.
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

2. **The real work all four judges point at: instrument ONE S2P pilot to produce the compounding curve.** This is bigger than the pitch, and it is what this package exists to enable. APP-1's honesty harness proves the *dynamics* on synthetic data pre-sale; the **same instrumentation — CC-1 (`centroid_distance_to_canonical`), CC-2 (ε_firm), CC-3 (IKS)** — is exactly what you point at the live S2P pilot to turn it into the *first real* compounding curve (pilot N becomes the proof for sale N+1). **Note (see CC-1): the live pilot / buyer curve uses IKS — rising canonical-distance, production-available with no oracle; the *decreasing* ground-truth-distance curve is oracle-only (reference app + controlled experiments) and is the proof that the learning is toward the _right_ thing.** Build the measurement spine once; it serves both the demo and the raise. **This elevates CC-1/CC-2/CC-3 from "supporting surfaces" to the highest-priority items in the package.**

3. **If S2P is the wedge, WP-1 (the S2P conservation-bypass fix) is LEAD-PRODUCT-critical.** S2P's promotion currently passes a literal `conservation_state="GREEN"` instead of fetching live state — the one place the code is weaker than the "conservation-gated" claim. On the lead product, in front of a technical VC or a live pilot, that gap is a claim-breaker: fix it **before** the S2P pilot's curve is shown or the repo is walked. (Detail: the RL consolidation work package WP-1; boundary context: the SOC-G1 decision memo.)

**Reuse, don't rebuild — inventory every copilot's tabs first.** Before building APP-1's rendered surfaces from scratch, open the running apps and **check the tabs of all five copilots — the SOC copilot in particular already has a very well-visualized version** of much of this legibility story (compounding / IKS-style / conservation panels). Screenshot and inventory each copilot's tabs, lift SOC's visual patterns into APP-1's `report.html` and the S2P pilot surfaces rather than reinventing them, and record which surfaces are already live per copilot (this also feeds WP-4 telemetry parity in the RL consolidation package). The goal is one consistent, reused visual language across the demo, the reference app, and the pilot — not a new one.

## 0.7 Two audiences, two bars — the fundraise vs the open-source SDK (cdk-copilot / CDK)

The apps here serve two different bars; be explicit about which serves which so neither gets under-built:
- **Fundraise / differentiation (the raise turns on these):** **APP-1** (compounding proof) + **APP-4** (governed-vs-ungoverned on the S2P wedge) + the CC-1/2/3 instrumentation. They answer *"what does it do"* and *"why is it different."*
- **Open-source SDK adoption (the cdk-copilot / CDK launch turns on these):** they answer *"how do I make it mine,"* mapped to the three-level adoption model:
  - **Level 1 (5 min):** APP-2 `hello-gae` (GAE) + APP-1's one-command run. A `hello-copilot` (~15-line SDK first-touch) is a nice-to-have — **tracked-but-later**.
  - **Level 2 (30 min, YAML):** **APP-5** — configure a domain in YAML off a built-in preset, no Python. *(The tier was defined but had no worked example.)*
  - **Level 3 (SDK, days):** **APP-6** — a minimal, forkable "build a new copilot" template in **two neutral domains** (email/inbox triage + reading-backlog triage), same shape over one shared harness, with the governed-vs-ungoverned toggle at the SDK level.
- **Don't gold-plate:** APP-5 + APP-6 are the minimal set that clears the adoption model's day-one value bar. A feature **cookbook** (recipes: conservation gate, explorers, promotion gate, factors/DomainConfig) and an **"extend the SDK"** example (add a store backend / reward fn / explorer) grow *after* launch — **tracked, not launch-blocking**.
- **Sequencing:** APP-1 + APP-4 first (fundraise). **APP-5 + APP-6 before the public SDK drop** — the OSS day-one value bar (outreach §OSS) says a flat drop with no clean "build your own" path is a negative signal to the exact VCs it's meant to impress.

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
- `centroid_distance_to_canonical` over decisions — **INCREASES** as the system learns (distance from the generic prior grows; the model-independent *production* learning signal, same basis as IKS — see CC-1).
- `centroid_distance_to_ground_truth` over decisions — **DECREASES** monotonically (the oracle-backed *convergence* proof — the "monotone-decreasing" invariant lives here; oracle-only — see CC-1).
- IKS rising curve (see CC-3).
- measurement_state ladder: 0 → INSTRUMENT_VALIDATED → ACCUMULATING → MEASURED (provenance `real_measured`, never `sample`).
- conservation status GREEN/AMBER/RED with α, q, V, θ_min and the 0.7×-baseline relative trigger (see CC-4).
- ε_firm measured, annotated against the 0.128 threshold (see CC-2).
- DK-weight concentration (3–4 of 6 dims) and per-factor σ noise fingerprint.
- one AgentEvolver promoted variant with its measured before/after decision-quality delta.

**Two-run honesty demo:**
- Run A (ε_firm > 0.128): Phase 1 genuine learning; after a category-sparse disruption, Phase 2 re-converges in fewer decisions → γ > 1 shown, measured on **ground-truth-distance** convergence (the decreasing curve; not noisy N_half).
- Run B (ε_firm < 0.128): γ ≤ 1 → visibly demonstrates the claim is *conditional*. Shipping both is the credibility move.

**VERIFY (acceptance):**
- One command, SQLite, no server: `python -m examples.jm_reference.run`.
- `centroid_distance_to_canonical` monotone-**increasing** AND `centroid_distance_to_ground_truth` monotone-**decreasing** every phase/seed (both rendered side by side; the convergence invariant is on the ground-truth distance).
- Run A: N_half,2 (**ground-truth**-distance basis) < N_half,1; Run B: not. Assert both.
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

### APP-4 — S2P "Governed vs Ungoverned" **Full Domain** Differentiation App  *(DIFFERENTIATION KEYSTONE — pairs with APP-1)*

**Customer value / why it exists:** APP-1 shows *that* judgment compounds (SDK-level, synthetic). APP-4 shows *why our approach beats a reward-maximizer* — the most-attacked diligence claim ("isn't this a weekend bandit?") — as a **full, running procurement (S2P) application** on realistic invoice/PO decisions, not an abstract harness. It is the artifact you put in front of a technical VC: a real domain app where you toggle *governed* vs *ungoverned* and watch the difference **on the wedge domain that funds the company.** One build does four jobs: the S2P wedge demo, the runnable "isn't this a bandit" answer, the governed-vs-ungoverned compounding curve, and the pitch's inverted-demo asset.

**Location / build-on:** a full app — `apps/s2p_differentiation/` (backend + frontend) — **built on the existing S2P copilot**: reuse `apps/s2p` presets, factor definitions, decision types, and routes; reuse the SDK scorer/evolution; reuse APP-1's `generator.py`/`oracle.py` for the honest data path; **reuse SOC's tab visualizations** (§0) for the surfaces. SQLite default, zero server beyond the app itself.

**What makes it a FULL DOMAIN APP (not a harness):**
- **Real S2P decisions**, the actual copilot's types: invoice-exception triage, PO approval routing, duplicate / maverick-spend detection, supplier-risk scoring — run through the real S2P decision flow, not abstract categories.
- **A running backend** serving three arms over the same live decision stream, with the S2P copilot's real endpoints.
- **A full frontend** with the S2P copilot's tabs: a decision feed, the governed-vs-ungoverned comparison, the compounding curve, the conservation panel, and a Rejection-Moment feed with reason codes — plus a **"swap the reward" toggle** for the T-G1 demo. Lift SOC's visual patterns rather than reinventing them.
- **Realistic procurement data**: a synthetic-but-honest invoice/PO/supplier dataset via oracle separation (generator emits factor vectors only; a math oracle labels correctness from a hidden ground-truth centroid). Optional gated **BYOD** path (a user's anonymized invoice export) for a live "run it on your data" moment.

**The three arms (same S2P decisions, same seed):**
1. **CI (governed)** — the real S2P copilot: centroid decision + conservation-bounded exploration (proposal-only) + conservation-gated promotion.
2. **Reward-max baseline** — a faithful contextual bandit / reward-maximizer over the same reward on the same S2P decisions; no centroid, no conservation gate.
3. **Hand-specified-reward ablation** — CI's architecture with the reward hand-specified and frozen (isolates "learns the reward").

**The differentiation it renders — end-to-end, on procurement decisions:**
- **T-G1 (decision ≠ reward-maximizer):** in the UI, change the reward config (e.g., the penalty asymmetry for a false-approve vs a false-reject); **CI's recommended action on a fixed invoice is unchanged; the reward-max baseline's action flips.** The runnable proof of "the decision is centroid, not reward-driven," in the domain. *(Runs on the clean centroid path — exploration proposal-only, the SOC-G1 A/C target state — and validates it.)*
- **Governance causes faster + more robust improvement:** the S2P decision-quality-vs-verified-decisions curve for all three arms against a frozen baseline — **this IS the compounding curve, in the wedge domain.** When a new supplier-fraud pattern / regime shift is injected, the reward-max arm promotes a rule that catches +8% more exceptions in aggregate but misses 30% of the high-value fraud — wins early, then collapses; CI stays robust; the hand-specified-reward arm trails CI.
- **The safety divergence (the inverted demo, domain-grounded):** the poisoned rule = "auto-approve invoices matching pattern X," +8% in aggregate but −30% on the high-severity slice (large-dollar / new-vendor). CI's gate **rejects** it with a reason code (`unstable_improvement` / `conservation_not_green`); the ungoverned arm **promotes** it → a large fraudulent invoice slips → its quality visibly collapses. Show a genuinely-promoted good rule **first**, then this rejection — the pitch's inverted demo.
- **Second-order control:** CI's improvement rate accelerates then damps (robust convergence); the ungoverned arm oscillates/overshoots.

**Honesty invariant (non-negotiable):** same oracle separation as APP-1, and the reward-max baseline must be a **faithful, well-implemented** reward-maximizer on the same data — the differentiation comes entirely from the decision + governance architecture, never from a strawman baseline or the data. `test_baseline_is_faithful` guards this.

**VERIFY (acceptance):**
- The app runs (backend + frontend), SQLite, reproducible seed; the surfaces render on **real S2P decision types**.
- T-G1: CI action + probabilities invariant to a reward-config swap in the UI; the reward-max baseline's action flips.
- Governance-causes-improvement: CI's post-shift quality > reward-max baseline's; the reward-max arm collapses after the injected fraud-pattern shift; CI > hand-specified-reward arm.
- Safety divergence: CI's gate rejects the poisoned auto-approve rule (reason code present); the reward-max arm promotes it and then degrades on the high-severity slice.
- `test_baseline_is_faithful` passes.

**Ties to the fundraise:** the single highest-leverage build — wedge demo + differentiation proof + compounding curve + inverted-demo asset in one running S2P app. **Gate on WP-1** (the S2P conservation-bypass fix) so the governed arm is genuinely conservation-gated; reuse the S2P copilot and SOC's visualizations so it's weeks, not a rebuild.

---

### APP-5 — Level-2 YAML-Config Worked Example  *(SDK adoption — the 30-minute, no-Python tier)*

**Customer value:** proves the middle tier of the adoption model is *real*, not a promise. A developer takes a built-in preset, expresses or tweaks a domain in **YAML** (factors, weights, penalty asymmetry, thresholds), and runs a working copilot — **without writing Python.** This is the sweet spot for a large fraction of OSS adopters, and today it has no runnable example. Small build; high adoption leverage.

**Location:** `copilot-sdk/examples/yaml_config/` (a `domain.yaml` + a ~15-line runner + README). Depends only on copilot-sdk + gae. SQLite, zero server.

**`[VERIFY-FIRST]` (important):** the three-level model already promises "Level 2: 30 min YAML," so a **YAML/DomainConfig loader may already exist.** Grep for it first; if present, APP-5 is *surface-and-document* (write the canonical example + README against the existing loader), **not** new parsing code. Only if no loader exists does this include a minimal YAML→DomainConfig binding.

**LOCATE (reuse existing symbols — do not reimplement):**
- Preset construction: grep `def from_preset` in `copilot_sdk/scoring/scorer.py`; grep the **six built-in domain presets** and the DomainConfig type.
- Any existing config parsing: grep `yaml`, `DomainConfig`, `load_config`, `from_yaml`, `preset` across `copilot_sdk`.
- The loop + surfaces: reuse APP-1's `run.py` loop and the CC-1/CC-4/CC-5 surfaces (centroid-distance, conservation panel, measurement_state).

**CHANGE:**
1. `domain.yaml` — starts `from: <one of the six presets>` and overrides a few fields (a couple of factor weights, the penalty asymmetry, a threshold) with inline comments explaining each. This is the artifact a Level-2 adopter edits.
2. `run.py` (~15 lines) — load the YAML → build the scorer → run the loop on bundled sample data → print the compounding + conservation surfaces. No domain code.
3. `README.md` — the 30-minute path: install → copy `domain.yaml` → change one weight → re-run → *see the behavior change.*

**Honesty invariant (non-negotiable):** the YAML path must exercise the **same** SDK loop as the Python path — no reduced or faked capability behind the config front-end. `test_yaml_equals_python`: a YAML-configured copilot and the equivalent Python-configured one produce **identical** decisions on the same seed.

**VERIFY (acceptance):**
- `python -m examples.yaml_config.run domain.yaml` runs zero-infra, SQLite, no server, no source edits.
- Changing one weight in `domain.yaml` **visibly** changes behavior on the next run.
- `test_yaml_equals_python` passes (YAML ≡ Python on the same seed).
- A stranger can follow the README end-to-end in ~30 minutes.

---

### APP-6 — Level-3 "Build-Your-Own Copilot" Template  *(SDK-ADOPTION KEYSTONE — the fork-and-build scaffold)*

**Customer value:** the single most important open-source-SDK example — the minimal, documented, **forkable** "build a new copilot in a new domain from scratch" scaffold. The five production copilots are references but too heavy and coupled to fork; the six presets show the *end state*, not the *journey*. This is the journey. It's what converts a reader into an adopter, and it ships the **governed-vs-ungoverned toggle at the SDK level** so a developer proves the differentiation *to themselves* without standing up S2P.

**Neutral starter domains — TWO, same shape** (chosen so any *individual* developer groks them in 30 seconds, with zero product baggage):
- **(1) Personal email/inbox triage** — decide **{priority / normal / archive}** per incoming email. Maximally familiar: the learner spends all their budget on the *SDK*, none on the domain.
- **(2) Personal reading / watch-later backlog triage** — decide **{read now / save for later / let go}** per saved item. Fresher, and the governance divergence bites harder (see the toggle below).

Ship **both** — two templates in the same shape is itself the lesson: *the same copilot pattern ports across domains by swapping the domain skin while the scorer / gate / explorer stay put.* Both decide from **benign synthetic metadata only** (email: sender frequency, thread depth, subject-signal flags, time-of-day, has-attachment, prior-response-rate; reading: source, length, topic-match-to-history, age-in-backlog, prior-finish-rate — **never content** in either). Both use a **three-action triage shape structurally identical to SOC's alert triage** (escalate / confirm / dismiss), so each doubles as a worked example of *porting an existing copilot pattern to your own domain* — and shipping the pair proves the port is real.

**Location:** `copilot-sdk/examples/build_your_own/` — a complete-but-minimal copilot with **two domain skins** (`domains/email.py`, `domains/reading.py`) over one shared harness: `generator.py`, `oracle.py`, `run.py`, a tiny `report.html`, and a step-by-step **`TUTORIAL.md`**. SQLite, zero server.

**LOCATE (reuse — this app is mostly *re-skinning*, not new engine code):**
- **Triage decision-shape:** grep the SOC copilot's triage decision types + factor extraction + scorer wiring (`triage.py`, the SOC preset) — port the *shape*, not the security domain.
- **Honest data path:** reuse APP-1's oracle-separated `generator.py`/`oracle.py` pattern.
- **Governed-vs-ungoverned:** reuse **APP-4's** faithful reward-max baseline + `test_baseline_is_faithful`.
- **Scorer/gate/explorer:** grep `def from_preset`, `def conservation_status`, the promotion gate, and the exploration class — the template must wire the **real** primitives, not stubs.

**CHANGE — build these (minimal, heavily commented):**
1. `domains/email.py` and `domains/reading.py` — two `DomainConfig`s in the same shape: three actions, ~6 benign factors, and the **penalty asymmetry** (email: missing a priority costs more than a false-priority; reading: letting a worth-it piece go costs more than a false "read now"). **The two files side by side ARE the tutorial's centerpiece** — the diff between them is the "how you port to your domain" lesson.
2. `generator.py` + `oracle.py` — per-domain synthetic **metadata** + a hidden ground-truth oracle (email: "was this action-needed within N hours"; reading: "did you finish it and rate it worth your time"). Oracle separation preserved (generator emits factor vectors only; the oracle labels correctness; no content, no LLM label).
3. `run.py` — `--domain {email,reading}` + the loop (score → outcome → learn → conservation), plus a **`--ungoverned` flag** that swaps in APP-4's reward-max baseline.
4. `TUTORIAL.md` — "build a copilot for *your* domain in a day": read the two domain files, see what changes and what doesn't → define your actions/factors/asymmetry → wire your data (or use the generator) → run → read the surfaces → toggle governance. Points to the five copilots as the deeper reference.

**The governed-vs-ungoverned toggle (the differentiation, at the SDK level, in domains anyone feels) — shown in each:**
- **Email:** `--ungoverned` (reward-max) optimizes "what you *open*" → drifts to prioritizing newsletters/clickbait; the safety divergence = a rule "auto-archive senders you rarely open," +8% on volume but archives the one critical email from a rare sender. Governed **rejects** it (reason code); ungoverned **promotes** it → you miss something important.
- **Reading:** `--ungoverned` optimizes "what you *click*" → surfaces clickbait/short junk (the Goodhart everyone recognizes — "I keep reading garbage and never get to the good stuff"); the safety divergence = "always surface high-click sources," which buries the long, valuable piece. Governed learns "what you actually **finished and found worth your time**" and **rejects** it. *This failure is one a person genuinely regrets — which is why the governance point lands hardest here.*

**Honesty invariants (non-negotiable):**
- Oracle separation (generator → factors only; oracle → hidden ground truth; no content).
- The reward-max baseline is **faithful**, not strawmanned (`test_baseline_is_faithful`, reused from APP-4).
- The template wires the **real** SDK loop — `test_uses_real_primitives`: asserts it calls the real scorer / conservation gate / promotion gate / explorer, not toy reimplementations. (A fake scaffold that "looks easy" but doesn't exercise the real engine is worse than none — it teaches the wrong thing.)
- **Both domains run on the SAME harness** — `test_domains_share_harness`: email and reading differ only in their `domains/*.py` skin, not in the loop/scorer/gate. This *is* the portability claim, enforced.

**VERIFY (acceptance):**
- A stranger follows `TUTORIAL.md` and has a running triage copilot **in a day**, in either domain.
- `python -m examples.build_your_own.run --domain email` and `--domain reading` both show compounding (ground-truth-distance decreasing + canonical-distance/IKS increasing; conservation surfaces render).
- `--ungoverned` shows the divergence in each (email: drifts to "opens," promotes the unsafe auto-archive rule; reading: drifts to "clicks," promotes the surface-high-click rule; governed rejects both).
- `test_baseline_is_faithful` + `test_uses_real_primitives` + `test_domains_share_harness` pass; oracle-separation test passes.
- Uses **synthetic metadata only** — no content anywhere (privacy-clean by construction).

**Ties to the launch:** APP-6 is the OSS-SDK adoption keystone — it's the "make it yours" path the cdk-copilot launch turns on, and it carries the differentiation into domains an individual feels. Two skins over one harness *is* the portability proof. Reuse SOC's triage shape + APP-1's oracle + APP-4's baseline, so it's a packaging-and-docs effort, not new engine code.

---

## Part 2 — Customer-value code changes (ranked, tagged by repo)

Each leads with the buyer-facing value. `[VERIFY-FIRST]` = confirm it doesn't already exist in the current tree before building.

### CC-1 — centroid-distance logging (BOTH distances)  *(SDK)*  — measurement spine + convergence proof
**Value / direction (corrected 2026-08-08 — the v3–v5 spec conflated two distances that move opposite ways):**
- **`centroid_distance_to_canonical` — INCREASES during learning.** Distance from the generic deployment prior; it grows as the system learns the firm's environment. This is the **production measurement spine** (no oracle needed), the **same basis as IKS and ε_firm**, and it answers *"how much has the system learned from its starting point."* Already on `/api/self/diagnostics` for all 5 copilots. **This is the signal the live pilot and the buyer curve use (IKS rising).**
- **`centroid_distance_to_ground_truth` — DECREASES during learning.** Distance to the oracle's hidden ground-truth centroids; it shrinks as the system converges on the right answers. This is the **convergence proof** — the "monotonically decreasing" claim applies HERE, not to the canonical distance. **Oracle-only:** meaningful only in the reference app (APP-1/APP-4/APP-6) and controlled experiments.
- **Together = the credibility package:** canonical-distance/IKS shows *how much* it learned (production, no oracle); ground-truth-distance shows the learning is toward the *right thing* (oracle-backed proof).
**LOCATE:** decision/outcome logging path (BACKLOG-015 fields, rolling-accuracy / N_half logging) + centroid store: grep `def write_outcome`, `def save_centroids`, `load_latest_centroids`. Canonical centroid: grep the expert-prior / `from_preset` init and `CANONICAL` / `soc_calibration_profile`. Ground truth: `oracle.ground_truth_centroids` (already exposed).
**CHANGE:** compute and persist **both** per verified decision — `‖μ_current − CANONICAL_CENTROID‖` (production; increases) and, wherever an oracle exists (reference app / controlled experiments), `‖μ_current − GROUND_TRUTH_CENTROID‖` (decreases). Add companion fields when cheap: `pattern_history_value`, `alert_category_distribution` (rolling-100 category mix). `report.html` shows both curves side by side.
**VERIFY:** both fields present per verified decision; canonical-distance monotone-**increasing** and ground-truth-distance monotone-**decreasing** under the APP-1 learning run; unit tests on a synthetic converging sequence for each direction.

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

**Deferred / gate items (not now, but tracked):** FreshScorerProxy per-call scorer reconstruction (grep `class FreshScorerProxy`; `scorer_cache_plan.md` ready) — matters when APP-3/Trading runs under real concurrency; AgentEvolver variant-promotion ledger surface — high value as the Level-2 proof, spec after APP-1 exercises one promotion end to end. **SDK-adoption, post-launch:** `hello-copilot` (a ~15-line Level-1 SDK first-touch, below APP-1); a feature **cookbook** (recipes: conservation status, add an explorer, configure the promotion gate, define factors/DomainConfig); an **"extend the SDK"** example (add a store backend / reward function / explorer). All grow after the cdk-copilot launch — tracked, not launch-blocking.

---

## Part 3 — LLM poll (narrow, ready to dispatch)

Poll only where independent review genuinely de-risks the build. Do NOT poll the ranking (a made judgment call) or CC-6 (settled).

**Q1 — Honesty harness (the core question):** "We will ship a Judgment-Memory reference app that demonstrates compounding on synthetic data using oracle separation (LLM/generator produces factor vectors only; a math oracle labels correctness from centroid distance to a hidden ground truth). Convergence is shown via `centroid_distance_to_ground_truth` (**decreasing**; oracle-only), not N_half; the production learning signal is `centroid_distance_to_canonical` (**increasing**, = IKS). Is this the right *minimal* construction to convince a skeptical technical buyer that the demonstrated compounding is real dynamics and not a generator-competence artifact? What is the smallest addition that would most increase its credibility, and what is the most likely way a hostile reviewer discredits it?"

**Q2 — ε_firm measurement:** "We define ε_firm as normalized ‖μ_current − μ_canonical‖ (Frobenius over the centroid tensor), used to test whether a deployment clears the γ>1 re-convergence threshold (~0.128). Is this a sound, buyer-defensible way to measure firm-specific deviation from the canonical prior at pilot week 1, and what confound most threatens it?"

---

## Part 4 — Suggested execution order

**Priority reset:** the compounding curve is the fundraise, so the measurement spine (CC-1/CC-2/CC-3) leads and doubles as the live-pilot instrumentation.

0. **WP-1 — S2P conservation-bypass fix** (from the RL consolidation package) — lead-product-critical if S2P is the wedge; gate the S2P pilot's curve on it.
1. **CC-1** (centroid_distance_to_canonical) + **CC-2** (ε_firm) + **CC-3** (IKS) + **CC-6** (θ_min hygiene) — the measurement spine of BOTH APP-1 and the live S2P pilot curve; CC-6 clears the OSS credibility gate. Build once, point at both synthetic (APP-1) and the pilot.
2. **APP-1** (JM reference app) — the keystone; pulls in CC-4/CC-5 as rendered surfaces (build or verify-and-surface). Reuse SOC's tab visualizations (§0).
2b. **APP-4** (RL differentiation harness) — the differentiation keystone; reuses APP-1's generator/oracle. High priority for the fundraise: it's the runnable answer to "isn't this a bandit" and it produces the pitch's inverted-demo assets. Build right after APP-1's harness exists.
3. **Instrument the live S2P pilot with CC-1/2/3** → the first real compounding curve (governance-causes-improvement: curve the governed run against a frozen baseline). *This is the artifact the raise turns on.*
4. **CC-7 + APP-2** (zero-infra quickstart) — makes a stranger's first run work.
4b. **APP-5 + APP-6** (SDK OSS adoption: Level-2 YAML config + Level-3 build-your-own template in the neutral email-triage domain) — **gate the public cdk-copilot / CDK drop on these**; they're the "make it yours" path. `hello-copilot` and the feature cookbook are tracked-but-later.
5. **Dispatch the 2-question LLM poll** in parallel with APP-1 (its answers refine the harness, not block it).
6. **APP-3 (Trading)** + connector-safety gate — after APP-1 proves the harness and the OSS-math is clean.

---

## Provenance & assumptions (honest)

- Symbol/path anchors are grep patterns, not line numbers, by design — the neo4j→graph_client rename shifted lines platform-wide. Confirm each against the current working tree (the Drive mirror lags the coding session's tree).
- `[VERIFY-FIRST]` items (CC-2 ε_firm, CC-3 IKS, CC-4 conservation payload) may already exist in part; check before building and downgrade to "surface in APP-1" if so.
- `measurement_state` (CC-5) is confirmed shipped and tested; it is exposure work, not new logic.
- The γ theorem, oracle-separation method, ε_firm threshold (~0.128), and the centroid-distance signals are from `synthetic_data_generation_analysis_v2.md` (CC-21 Tier 2). Note the two distances (CC-1): canonical-distance **increases** (production/IKS), ground-truth-distance **decreases** (oracle-only convergence proof). The reference app demonstrates the theorem's *direction* honestly; the *magnitude* remains a real-pilot (EXP-G1) quantity — do not let APP-1 imply a measured γ magnitude.
