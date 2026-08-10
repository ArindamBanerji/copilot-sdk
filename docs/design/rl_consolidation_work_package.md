# RL / Evolution — Design Verification, Finalization & Implementation Package
**Date:** 2026-08-08 · for the coding session (Codex) · **self-contained** (assumes no prior conversation)
**Grounded in:** the RL diagnostic scan (`rl_diagnostic_scan_consolidated_results.md`) — findings embedded below as claims to re-verify.
**What Codex should do with this doc, end to end:** **Phase A** verify the embedded current-state findings + resolve four open design unknowns against live code → **Phase B** finalize the shared design (contract, template, schema, test matrix, three decisions) → **Phase C** implement the work packages → **Phase D** prove done. Produce the Phase-A/B report at `docs/design/rl_consolidation_verification.md` BEFORE writing implementation code.
**Success criteria:** the RL/evolution loop is uniform, live, and conservation-gated across **all five copilots**, and the four product guarantees (§0.2) hold identically on each.

---

# §0. CONTEXT — read first (you have no prior conversation)

## 0.1 The product in one paragraph
"Compounding Intelligence" is a platform of **five domain copilots** — SOC (security), S2P (procurement), Trading, Purchasing, DataOps — on **one shared engine**. Each copilot *decides* (recommends an action per case) and *learns* from verified outcomes. Two distinct subsystems: **(a) the judgment core / scorer**, which chooses the action, and **(b) the evolution loop**, which proposes and safely adopts improvements to a copilot's own rules/prompts/thresholds. **This work is about (b).**

## 0.2 The four product guarantees (the WHY behind every acceptance test — do not break these)
- **G1 — The DECISION is centroid-based, not reward-maximizing.** The recommended action is chosen by nearest-centroid distance + softmax over negative distances (`graph-attention-engine-v50/gae/profile_scorer.py:408-496`). Reward functions run **only** in the *learning* path (the `learn()` "sidecar" at `copilot_sdk/scoring/scorer.py:871-882`, updating exploration + factor credit) and in the *evolution* loop. **Reward must never influence action selection.**
- **G2 — Self-improvement is CONSERVATION-GATED.** A variant is promoted to live **only when the copilot's current conservation state is GREEN**; blocked on AMBER/RED. ("Conservation" = the platform's live safety signal.)
- **G3 — Exploration is conservation-bounded.** The explorers (UCB1 + Thompson/Beta) only explore within the safety envelope.
- **G4 — Every promotion is earned.** A variant is shadow-tested against real decisions and must clear the gate (superiority + accuracy floor + variance + conservation) before going live; rejections carry a reason code.

## 0.3 Verified current state (from the scan — Phase A CONFIRMS each with `file:line`)
**Judgment core (GAE) — out of scope, do not touch:** `graph-attention-engine-v50/gae/profile_scorer.py` — `score()` = centroid distance + softmax (decision); `update()` = centroid pull/push. Not RL.

**RL/evolution (SDK + apps):**
- SDK: `copilot_sdk/rl/{reward.py, reward_functions.py, exploration.py, credit.py}`, `copilot_sdk/evolution/{evolver.py, prompt_evolver.py, gate.py, shadow.py, ledger.py, variant_store.py}`.
- Exploration: **UCB1** (`prompt_evolver.py`, `success_rate + c·√(ln(max(N,2))/n_i)`, default `c=1.414`) **+ conservation-bounded Thompson/Beta** (`rl/exploration.py`, samples only when GREEN).
- Reward: `RewardComputer` clips reward to [-1,1] and ×`penalty_ratio` on **negative** outcomes; four functions (Binary, GradedFinancial, PnL, WasteReduction); per-copilot `penalty_ratio` — **SOC 20, DataOps 10, S2P 5, Trading 3, Purchasing 3**.
- Gate (`gate.py` `DefaultPromotionGate`): 5pp superiority, 0.70 accuracy floor, 10 min shadow decisions, **fail-closed conservation** (accepts GREEN/VERIFIED/ACTIVE/overallSafe). `PlateauConfig(window=10, min_improvement_rate=0.2, cooldown=50)`.
- **`PromptEvolverConfig` already exposes a `conservation_state_provider: Callable[[],Any]` hook** — the key to WP-0.

**Per-copilot wiring — the matrix to make all-green (CONFIRM each in Phase A):**
| Copilot | Evolver instance | Variants registered at runtime | Live conservation gating | Key refs |
|---|---|---|---|---|
| SOC | ✅ SDK wrapper (+ separate `rl_engine.py` Beta policy) | ✅ 2 active / 2 shadow | VERIFY | `gen-ai-roi-demo-v4-v50/backend/app/services/{evolver.py,rl_engine.py}`; UCB `c=1.0` here |
| S2P | ✅ SDK `PromptVariantEvolver` | ✅ 4 / 4 (module load) | ❌ **literal "GREEN"** | `s2p-copilot/backend/app/services/s2p_evolver.py:64-66`, `app/routers/s2p_evolution.py:55-57` |
| Trading | ✅ custom `TradingAgentEvolver` (justified) | ❌ **starts with no variants** | ✅ `_conservation_green` + provider | `apps/trading/backend/app/services/trading_evolver.py:186-190` |
| Purchasing | ❌ **not instantiated** | (6/6 configured only) | — | `apps/purchasing/backend/app/main.py:689-696`, `.../evolution/evolver_config.py` |
| DataOps | ❌ **not instantiated** | (2/2 configured only) | — | `apps/dataops/backend/app/main.py:742-747`, `.../evolution/evolver_config.py` |

## 0.4 Design principle: one "evolution spine"
Every copilot shares the same five-part spine: (1) an evolver instance, (2) variants registered at startup, (3) the gate fed by a **live conservation provider** (never a literal), (4) **outcome recording** wired to verified decisions, (5) a **uniform evolution summary/history** surface + parity tests. The three defects/gaps flagged by the coding session plus two it missed (Trading registration; conservation-source non-uniformity) are all "spine part N is missing for copilot X."

## 0.5 Glossary
**Spine** = the five-part setup in §0.4. **Provider** = the `conservation_state_provider` callable returning live conservation state. **Sidecar** = reward/exploration/credit code called inside `learn()` that updates learning signals but does NOT choose the action (G1). **Rejection Moment** = the observable flow *propose variant → shadow-test → reject with reason if it fails the gate*; shown in demos, so telemetry must expose it uniformly (WP-4).

## 0.6 Guardrails — do NOT
- Wire any reward function into the recommendation/scoring path (violates G1).
- Hard-code any conservation state anywhere (that is the S2P defect).
- Promote a variant without shadow-test + gate (violates G4).
- Change exploration constants, gate thresholds, or Trading's algorithm as part of this work (those are §3 decisions).
- Modify the GAE judgment core (`profile_scorer.py`).

---

# §1. PHASE A — DESIGN VERIFICATION (do first; report before coding)
Confirm/contradict each §0.3 finding with `file:line` (status CONFIRMED / CONTRADICTED-with-truth / GAP), then resolve these **four unknowns** — each blocks a work package:

- **U1 — Live conservation source (blocks WP-0).** Per copilot, identify the canonical getter for current conservation state (GREEN/AMBER/RED/CALIBRATING) — is it a scorer method, an L5 conservation store row, or a service? Is it **synchronously callable at promotion time**? Is the getter uniform across copilots (→ one SDK helper) or per-app (→ a shared contract + per-app providers)? Also: **how does `check_for_promotion` consume conservation** — as a call arg (which S2P overrides with a literal) or via the config provider? Determine the exact seam to fix.
- **U2 — Outcome-recording path (blocks WP-2).** Per copilot, trace decision → verified outcome → `record_outcome(variant_id, success)`. Does this feedback loop exist for SOC/S2P/Trading, and does it exist AT ALL for Purchasing/DataOps? (Instantiating an evolver without this loop = a dead loop.)
- **U3 — Promotion trigger (blocks WP-2/WP-3).** Per copilot, what invokes `check_for_promotion` / `AgentEvolver.evolve` — an API route, a scheduled job, a per-N-decisions hook? Does a trigger exist for Purchasing/DataOps?
- **U4 — Telemetry surface (blocks WP-4).** Per copilot, enumerate the existing evolution summary/history endpoint(s) and their response shapes (SOC `OperationalImpact`, S2P `get_evolution_summary`, Trading's own). Produce the union → the target schema in §2.
**Phase-A deliverable:** `docs/design/rl_consolidation_verification.md` = the §0.3 validation ledger + U1–U4 resolutions + any correction to this package's assumptions.

# §2. PHASE B — FINALIZATION (produce these before WP coding)
1. **Live-conservation contract.** From U1: define `get_live_conservation_state(copilot) -> {"status": "GREEN|AMBER|RED|CALIBRATING", ...}` and whether it's one SDK helper or a per-app provider set. Must return a shape the gate already accepts (GREEN/VERIFIED/ACTIVE/overallSafe).
2. **Canonical wiring template.** One documented pattern for "instantiate evolver + register variants at startup + set provider + wire outcome recording + expose telemetry," derived from S2P (post-fix) + Trading, that Purchasing/DataOps follow.
3. **Telemetry schema (finalize + adopt on all five):**
   ```
   GET /api/self/evolution/summary
   { "domain", "evolution_enabled": bool, "conservation_state": "GREEN|AMBER|RED",
     "active_variant": {"id","family","version"},
     "inventory": {"active":[...], "shadow":[...]},
     "variant_stats": [{"variant_id","successes","total","success_rate"}],
     "recent_events": [{"event_type":"variant_generated|shadow_completed|promoted|rejected",
                        "variant_id","reason","timestamp","metrics":{...}}] }
   ```
4. **Test matrix (parametrized across all 5 copilots)** — §3 WP-5 implements it:
   | ID | Asserts | Guarantee |
   |---|---|---|
   | T-STARTUP | app instantiates exactly one evolver with variants registered at boot | wiring |
   | T-NOLIT | grep: zero literal `conservation_state="…"` in app code | G2 |
   | T-AMBER | live AMBER ⇒ promotion blocked, reason ∈ {conservation, conservation_not_green} | G2 |
   | T-GREEN | GREEN + improvement ≥ threshold + samples ≥ min ⇒ promoted | G2+G4 |
   | T-SUP | improvement < superiority margin ⇒ rejected (superiority/insufficient_improvement) | G4 |
   | T-VAR | variance > cap ⇒ rejected (variance/unstable_improvement) | G4 |
   | T-SAMP | samples/batches < min ⇒ rejected (sufficient_data/insufficient_batches) | G4 |
   | T-OUTCOME | `record_outcome` updates variant stats | feedback loop |
   | T-G1 | swap the reward-function config ⇒ the scorer's recommended action for a fixed input is UNCHANGED | **G1** |
5. **Decisions D1–D3 (see §4).**

# §3. PHASE C — IMPLEMENTATION (work packages; each cites its guarantee + acceptance)

**WP-0 — Shared live-conservation provider (spine fix; first).** Implement the §2.1 contract. Every copilot builds `PromptEvolverConfig(..., conservation_state_provider=<live getter>)`; every promotion path reads via the provider. *Acceptance:* T-NOLIT passes; T-AMBER passes per copilot. *(G2)* ~0.5d + folded into WP-1/2/3.

**WP-1 — DEFECT: S2P conservation.** `s2p_evolver.py:64-66` — replace literal `"GREEN"` with the provider; route `s2p_evolution.py:55-57` passes through. *Acceptance:* T-AMBER, T-GREEN pass for S2P; regression test added. *(G2)* ~0.5d.

**WP-2 — GAP: wire Purchasing + DataOps.** Instantiate one `PromptVariantEvolver` in `apps/purchasing/backend/app/main.py:689-696` and `apps/dataops/backend/app/main.py:742-747` per the §2.2 template: register configured variants at startup, wire the U2 outcome path (build it if absent), set the U3 promotion trigger (add a route/job if absent), set the provider, expose §2.3 telemetry. *Acceptance:* T-STARTUP, T-OUTCOME, T-AMBER, T-GREEN pass for both. *(G2+G4)* ~1d each.

**WP-3 — GAP: Trading variant registration.** Register Trading's configured variant specs at startup through `TradingAgentEvolver` (`trading_evolver.py:186-190`), parity with S2P. *Acceptance:* T-STARTUP passes for Trading; a shadow→promote cycle runs. ~0.5d.

**WP-4 — Telemetry parity.** Make all five expose the §2.3 schema (current variant, inventory, variant_stats, recent events with reason codes, live conservation_state). *Acceptance:* identical response shape on all five; Rejection Moment renders identically. ~1d.

**WP-5 — Reward-config + test parity.** Verify each preset binds the correct reward fn + ratio (SOC /20, DataOps /10, S2P /5, Trading PnL/3, Purchasing WasteReduction/3 — confirm SOC's & DataOps's reward-fn class) and the learn() sidecar is active. Implement the §2.4 matrix as one parametrized suite over all five. *Acceptance:* full matrix green on all five. *(G1–G4)* ~1–1.5d.

**WP-6 — Documentation.** Document the scorer RL sidecar (`scorer.py:871-882`) — runs reward in `learn()`, does NOT pick the action (G1). Write `docs/design/rl_architecture.md` (mechanisms, per-copilot config table, conservation contract, the G1 boundary). *Acceptance:* doc exists and matches code. ~0.5d.

# §4. DECISIONS (choose in Phase B — NOT refactor license)
- **D1 — SOC UCB `c=1.0` vs √2.** Recommend **keep + document** (changing an exploration constant without an eval is risk with no reward).
- **D2 — Trading custom evolver.** Justified (factor-weight perturbation + regime logic). **Keep custom, but it MUST consume the WP-0 provider + WP-4 telemetry** — parity of behavior, not code.
- **D3 — SOC standalone `rl_engine.py`.** Confirm intended (or dead); document which path is authoritative for SOC promotion.

# §5. PHASE D — DEFINITION OF DONE (executable gates)
1. §0.3 matrix all-green: every copilot has one evolver instance, variants registered at boot, live conservation gating via the provider, correct reward binding, §2.3 telemetry. 2. Zero literal `conservation_state` in app code (T-NOLIT). 3. §2.4 test matrix green on all five. 4. `rl_architecture.md` + the sidecar docstring exist. 5. The Rejection Moment runs identically on all five. → **G1–G4 hold identically on all five copilots.**

# §6. OUT OF SCOPE (do not gold-plate)
Rewriting Trading onto the SDK evolver; changing SOC's UCB constant or any gate threshold without a separate eval; anything in the GAE judgment core.

# §7. SEQUENCING & EFFORT
Phase A (verify + U1–U4) → Phase B (finalize) → WP-0 → WP-1 → WP-2 + WP-3 → WP-4 → WP-5 → WP-6. Implementation ~5–6d after A/B; A/B ~1–2d.
