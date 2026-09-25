# RL Architecture: The Sidecar That Makes Judgment Compound
*Outreach-ready. Aligned with F-25 (RL never selects actions), science baseline (γ>1 proved and simulation-confirmed (γ ≈ 1.2, 270 production-faithful runs); DK boundary-defined; +28pp withdrawn), and operating-envelope framing.*

---


*[GRAPHIC: RL-HERO — "The Sidecar That Makes Judgment Compound."

**Layout:** Two-panel side-by-side, light background, dark text. Center vertical divider.

**LEFT PANEL (red/gray tint — "Traditional RL"):**
- Title: "Traditional RL" (large, red)
- Flow (vertical, top to bottom): State → Reward Function → Policy (weight matrix) → Action
- Single loop arrow from Action back to State
- Callout boxes (red outline): "Reward IS the learning signal" / "Policy IS the model weights" / "No competence boundary" / "Swap model = lose policy"
- Bottom label: "First derivative only. d²/dt² ≈ 0."

**RIGHT PANEL (green/teal tint — "CI Sidecar"):**
- Title: "Compounding Intelligence" (large, teal)
- PRIMARY PATH (bold, top): Verified Input → Centroid Scorer (L2 distance + softmax) → Recommended Action
- Label on primary path: "AUTHORITATIVE — geometry, not reward"
- SIDECAR PATH (thinner, branching from scorer, parallel): learn() → Reward/Exploration → Variant Proposal → Shadow Test → Conservation Gate → Promote / Rollback
- Label on sidecar: "ADVISORY — proposes, never overrides"
- Conservation badge (amber): "α·q·V ≥ θ_min — fail-closed"
- Callout boxes (green outline): "Decision IS the explanation" / "Centroid tensor survives model swaps" / "57%→14% adversarial resilience" / "d²/dt² > 0 at inflection"

**CENTER DIVIDER:**
- Bold vertical line
- Text (large, centered): "THE LINE"
- Subtitle: "Action selection is never reward maximization."

**BOTTOM STRIP (dark background):**
- Four guarantee badges in a row: G1 (action ≠ reward) / G2 (conservation fail-closed) / G3 (promotion gated) / G4 (auditable + domain-scoped)
- Each badge: icon + 3-4 word label

**FOOTER:** "Compounding Intelligence — dakshineshwari.net"

**Canvas:** 1920×1080 primary. Also produce 1200×630 (LinkedIn OG).
**Style:** Light background, bullets/fragments not prose, NBP generation.
**Reference:** `A1_rl_sidecar_architecture.jpg` shows the right-panel architecture — use as structural reference for the CI side. The hero adds the left-panel contrast and the four badges.

✅ EXISTS in renamed_rl_arch/ · rl_hero_sidecar_that_makes_judgment_compound.jpg.]*

*[GRAPHIC: RL-SIDECAR-SUMMARY-HERO — "Reinforcement Learning That Knows Its Place." Standalone five-band hero: (1) THE LINE — "Action selection is never reward maximization"; (2) Architecture — geometry (P(a|f,c) = softmax(−‖f−μ_c‖²/τ), authoritative) vs sidecar (advisory, +6.8/+6.5 enrichment); (3) Measured results — t^1.387 advantage, D(n)~n^2.15 discovery, 57%→14% resilience; (4) Safety — three-layer gate (allow ⟺ G-ABS ∧ G-REL ∧ G-RATE), adversarial RL bounded (fitted-Q collapsed −32.75 out-of-dist); (5) Four guarantees G1–G4. 1920×1080 + 1200×630 LinkedIn OG + 1080×1080 square. See Appendix A in rl_architecture_v6_2_graphics_review.md for full description. | TO GENERATE.]*

## The One-Sentence Summary

The centroid scorer makes every decision. RL proposes operational improvements from the side. Conservation gates them. The architecture preserves judgment — not reward.

---

## 1. Why This Architecture Exists

Enterprise AI has a decision problem that traditional RL can't solve.

Traditional RL selects actions by maximizing expected reward. That's the textbook architecture. It's also why most enterprise AI can't answer three questions a regulator will ask:

- **Why did it do that?** "It maximized reward" is not an answer the EU AI Act Article 13 accepts.
- **Can you reverse it?** A reward-maximizing policy is a weight matrix. You can't point to the cell that caused the decision.
- **What happens when the reward signal is poisoned?** The agent learns wrong behaviors. There is no mechanism to detect this — the reward IS the learning signal.

Compounding Intelligence inverts the architecture. The judgment core (centroid scorer) is authoritative. RL is advisory. Conservation governs both.

---

## 2. The Architecture

```
verified input → scorer → centroid distance + softmax → recommended action
                   |
                   +→ learn() → reward / exploration / credit sidecar
                   |
                   +→ variant proposal → shadow test
                                          → conservation gate
                                          → promotion / rollback
```

**Scorer** performs action selection from learned centroids (Eq.1: P(a|f,c) = softmax(−‖f−μ_c‖²/τ)). Reward is NOT an action selector.

**learn()** records verified feedback and runs the reward, exploration, and credit sidecar. It does NOT rewrite the action returned for the decision.

**Evolution** proposes active/shadow variants, shadow-tests them, and promotes only when the gate accepts sufficient data, superiority, accuracy, variance, AND conservation.

The gate is fail-closed: missing, unknown, or unsafe conservation state blocks promotion. No fallback literal state.

**The conservation gate is three layers, not one.** It was designed with two — an absolute floor (protects cold-start) and a relative trigger (protects against slow, sustained drift). A characterization experiment found a gap neither covers: a *sudden* accuracy drop in steady state is invisible to the relative trigger, because that trigger compares against a rolling long baseline and a sudden drop averages into its own baseline before the ratio would trip — and the absolute floor has long since cleared (it clears in ~3 decisions). So a third layer was added and tuned: a **rate detector** that compares the last 20 decisions to the long baseline at 0.85×, which is not averaged into its own baseline and so catches the step. Measured: 86.7% of sudden drops caught at 0.87% false alarms. The three-layer gate — floor, drift trigger, rate detector — covers every failure regime tested. This is the operating-envelope story done right: we designed two layers, measured where they left a gap, and closed it with a third, measured. The gate catches sustained decline, drift, and sudden breaks; sparse targeted poisoning is a harder, named boundary — we say where it stops, not just where it works. *(Measured, per threat model.)*

*[GRAPHIC: three-layer safety — cold-start / sudden-drop / sustained-poison × gate configs; 86.7% detection at 0.87% false-pause. | pub_safety_layers_r2.png EXISTS in charts/. | 980×500.]*

*[GRAPHIC: `A1_rl_sidecar_architecture.jpg` — Scorer (top, authoritative) → RL sidecar (parallel, advisory) → variant proposal → shadow test → conservation gate → promote/rollback. Per-copilot config strip: SOC 20:1, S2P 5:1, Trading 2:1, Purchasing 3:1, DataOps 10:1. G1-G4 annotated. | ✅ EXISTS in graphics-renamed/. | 980×600.]*


---

## 3. What This Architecture Unlocks — Business Value

### 3.1 Auditable decisions that survive regulatory scrutiny

Traditional RL: "The agent selected action X because it maximized expected reward." The reward function is a black-box optimization — you can show the reward value, but not WHY that reward led to THAT action over alternatives.

CI sidecar: "The agent selected action X because it is the nearest centroid in L2 space (distance: 0.034). Here are the 6 factors. Here is the centroid shaped by 847 verified decisions. The RL sidecar proposed a variant threshold — it is running in shadow, has not been promoted yet."

The decision IS the explanation. EU AI Act Article 13 (transparency), Article 14 (human oversight), and Article 9 (risk management) are satisfied by architecture, not by a separate explainability layer bolted on after the fact.

There is a second, sharper reason the reward signal cannot be the correctness signal: an LLM asked to *judge* whether a decision was right is blind on exactly the decisions that matter. Measured across 240 real LLM judgments, an LLM judge agreed with ground truth ~86% of the time on decisions resolvable from the surface, but only ~12% on decisions that require investigating non-surface evidence — while a geometry-derived check agreed ~76% on the same hard decisions. The learning here is validated against verified outcomes and geometry, never against an LLM's read of the surface — which is why the compounding is real and not a measurement of the judge.

**Evidence:** Conservation law maps directly to five EU AI Act articles. 9,826 conservation checks, zero violations, five copilots.

*[GRAPHIC: `C10_eu_ai_act_compliance.jpg` — Five EU AI Act articles × CI mechanisms. Art.9→conservation, Art.13→centroid transparency, Art.14→human oversight. | ✅ EXISTS in graphics-renamed/. | 980×400.]*

### 3.2 Judgment that survives model swaps

Traditional RL: The learned policy IS the model weights. Swap GPT-4 for Claude? The policy is gone. Every reward signal, every episode, every learned behavior — tied to that specific model's weight space. The vendor lock-in is architectural.

CI sidecar: The centroid tensor is small and readable — for SOC, 24 prototype vectors of 6 factors each (144 parameters). Across five copilots, ~844 parameters total — the whole learned asset, auditable by hand. Swap the LLM that generates factor vectors — the centroids, the σ fingerprint, the conservation state all persist. The +36.89pp advantage is in the geometry, not the model (EXP-C1, zero-learning controlled).

**Experiment:** EXP-C1 — +36.89pp is architecture accuracy, measured with zero learning. The LLM is a replaceable input. Direct model-swap measurement is a pilot-phase experiment.

### 3.3 Quantified resilience under adversarial conditions

Traditional RL: Poisoned rewards corrupt the policy directly. The agent learns wrong behaviors and has no mechanism to detect it. The reward IS the learning signal — poison the reward, poison the policy. Recovery is manual: retrain from scratch.

CI sidecar: Poisoned feedback moves centroids. Three defense layers:

1. **Asymmetric η** — damped learning from overrides (η_override = 0.01 vs η_confirm = 0.05). A single adversarial event moves the centroid 5× less than a confirmed decision.
2. **Conservation gate** — α·q·V drops below θ_min → PAUSE. The system stops acting in the affected category.
3. **AgentEvolver** — detects centroid drift, shadow-tests rollback, promotes recovery under statistical gate (n≥30, α=0.05).

Result: 57% → 14% non-recovery (EXP-AE-DECISION). The 57%→14% number is the insurance policy.

**Experiment:** EXP-AE-DECISION — 20% adversarial injection. Without AE: 57% non-recovery. With AE: 14%. AE triggered 4-6 rollback+damping actions within ~50-100 decisions of adversarial onset. Per-category recovery: 1 decision (vs 1-9 frozen). Centroid drift reduced 60%.

*[GRAPHIC: `MOD2_H9_agent_protected_v5b.jpg` — AE 57%→14%. Three colored mechanism boxes: asymmetric η (blue), conservation gate (amber), AgentEvolver rollback (green). | ✅ EXISTS in renamed_gap_v1/. | 980×500.]*

### 3.4 Second-derivative learning — capital, not expense

Traditional RL: First derivative only. The policy improves with each episode. d/dt(quality) > 0. But the RATE of improvement is constant — each episode adds approximately the same marginal value. d²/dt² ≈ 0. This is operating expense: constant return per dollar invested.

CI sidecar: AgentEvolver proposes operational improvements (threshold adjustments, factor weights, scoring parameters). Each improvement makes SUBSEQUENT centroid learning more efficient — the geometry now scores from a better-calibrated configuration. The rate of improvement increases at the inflection. d²/dt² > 0.

**The logistic shape (measured):** The 100th decision moves the centroid geometry further from initialization than the 1,000th — the per-decision impact is largest early and diminishes as the geometry calibrates. This is a property of the convergence math, not a CI-specific claim.

**The capital framing (positioning):** But the per-decision impact diminishing does not mean the asset stops growing — the *accumulated* geometry keeps compounding. A well-calibrated scorer is worth more than a poorly-calibrated one, and every decision that calibrated it is embedded in the tensor. This is capital investment: the judgment asset appreciates even as the marginal contribution of each new decision shrinks.

**Measured (EXP-RL-DIRECT):** The baseline learning curve is logistic (R² = 0.879). d²/dt² is positive before the inflection (~330 decisions) and negative after. Three operational regions: steep learning → transition → plateau. This curvature is a property of the LOGISTIC CURVE SHAPE — any centroid-based learning system with this update rule would exhibit it.

**Hypothesis (not yet measured):** AE-mediated operational improvements (threshold tuning, factor weight adjustment) increase d²/dt² beyond the baseline logistic curvature. The mechanism: each AE improvement makes the scorer configuration better, so subsequent centroid learning is more efficient. This is the "sidecar-mediated compounding" hypothesis — it would confirm that the sidecar contributes acceleration BEYOND what the centroid geometry produces alone.

*[GRAPHIC: `ADD2_second_derivative_chart.jpg` — Two curves: linear IMPROVE (d²/dt²≈0, operating expense) vs logistic COMPOUND (d²/dt²>0 at inflection, capital investment). Annotation at inflection point. | ✅ EXISTS in renamed_gap_v1/. | 980×400.]*

**Potential experiment:** EXP-AE-SECONDDERIV — measure d²/dt² at inflection WITH vs WITHOUT AE to confirm AE contribution to acceleration.

### 3.5 Five domains. One sidecar. Different judgment in each.

Traditional RL: Each domain needs a different RL architecture. SOC (missed escalation costs 20× a false positive) requires fundamentally different reward shaping than Purchasing (waste costs 3× a missed savings). Five domains = five separate RL systems.

CI sidecar: Same architecture, same conservation law, same promotion gate, same four guarantees. The ONLY domain-specific element is the reward function and penalty ratio:

| Copilot | Reward function | Penalty ratio | UCB c | Variants |
|---|---|---|---|---|
| SOC | SOC binary + severity | 20:1 | 1.0 | SOC-configured |
| S2P | GradedFinancialReward | 5:1 | 1.414 | S2P-configured |
| Trading | PnLReward | 2:1 | 1.414 | 10 (5+5) |
| Purchasing | WasteReductionReward | 3:1 | 1.414 | 12 (6+6) |
| DataOps | GradedFinancialReward | 10:1 | 1.414 | 4 (2+2) |

Build the sidecar once, configure per domain. The fifth copilot doesn't require a fifth RL architecture — it requires a fifth reward function and a penalty ratio.

*[GRAPHIC: `GM02_five_copilots_ten_pairs.jpg` — Five copilots on shared graph, 10 discovery pairs. D(n) ∝ n^2.15 (measured). Same sidecar, different judgment. | ✅ EXISTS in fixed-renamed/. | 980×500.]*

**Platform economics:** D(n) = n(n-1)/2 discovery pairs. Five copilots = 10 pairs. Four copilots = 6. The fifth doesn't add — it multiplies.

---

### 3.6 RL earns its keep in one specific loop — spending investigation, not selecting actions

The sharpest evidence that RL belongs in the sidecar, not the decision, is that it *wins* in exactly one place and *loses* in the other — and the architecture puts it where it wins.

**Where RL loses (and should):** routing RL reward into the scorer's own learning rate does not beat a plain uniform rate — three strategies (EMA-smoothed, Thompson sampling, hybrid) each failed to beat uniform. That is the confirmation that action selection stays with the geometry, not the reward (the sidecar boundary, proved by a negative).

**Where RL wins:** the one loop RL controls with real, safe value is *how much to investigate per decision* — the enrichment budget. A learned budget controller spends one read when the decision is easy and more when it is hard, and the result is **higher decision quality at fewer reads**: +6.8 points (source-to-pay) and +6.5 points (security) at ~1.4–1.7 reads versus a fixed 2.0, with zero clean-stream pauses and full sustained-poison detection. And it is safe by construction, not by tuning: sweeping the safety-constraint penalty, the best operating point was *no explicit penalty at all* — the safety came from the substrate (the conservation gate, the per-domain floors, persistent judgment state), not from a knob. RL tuned the investigation; it never touched the decision.

| Copilot | Baseline (fixed 2 reads) | Controlled | Quality gain | Reads/decision | Clean-pause | Poison detection |
|---|---|---|---|---|---|---|
| S2P | 63.4% | 70.2% | **+6.8 pts** | 1.43 (vs 2.0) | 3.27% → **0%** | **100%** |
| SOC | 76.5% | 83.0% | **+6.5 pts** | 1.75 (vs 2.0) | → **0%** | **100%** |

It genuinely requires learning: a rule-based budget heuristic *hurt* (−2.1 pts on S2P). *(Two copilots — in-distribution; geometry-derived + simulated.)*

*This is the whole thesis in one result: reinforcement learning makes the system spend its attention smarter, while the geometry — not the reward — still makes every call.*

*[GRAPHIC: enrichment-controller adaptive-vs-uniform — +6.8/+6.5 pts at fewer reads, 0% clean-pause. | pub_ri7_adaptive_vs_uniform.png EXISTS in charts/. | 980×400.]*

**Note:** This is a different mechanism from the learning-curve acceleration hypothesized in §3.4 — the enrichment controller allocates investigation effort; §3.4's d²/dt² claim is about whether AE accelerates centroid learning itself.

---

### 3.7 The adversarial question: "Why not just use RL for routing?"

The objection writes itself: *"Offline RL on your verified outcomes would beat the closed-form router — you just under-powered it."* Tested directly. A learned router (fitted-Q) beat the closed-form router by +10–21 points *in-distribution* — and collapsed **−32.75 points out-of-distribution**, overfitting the training firm's structure. A fitted-*linear* router — the closest inspectable form — *hurt* (−35.6%), so the gain is genuinely nonlinear, which is exactly what does not port.

The conclusion is not "RL wins" or "RL loses" but: **learned routing is a per-deployment upgrade a firm can exercise once it has enough verified decisions; the closed-form router is the portable, inspectable, day-zero default.** Offline RL trains on verified outcomes (so it avoids self-poisoning), but it forfeits inspectability and portability — exactly the properties the sidecar architecture is built to preserve.

*[GRAPHIC: RL-OFFLINE-ROUTING — "Why not just use RL for routing?" Horizontal bar chart: fitted-Q +10–21 in-dist (green) / −32.75 out-of-dist (red) / fitted-linear −35.6% (red). Zero line = closed-form router. Callout: "Learned routing = per-deployment upgrade. Closed-form = portable default." | TO GENERATE. | 980×500.]*

---

### The RL Sidecar in Five Equations

*[EQUATION GRAPHIC | eq_rl_sidecar_consolidated | the RL sidecar in five equations | rl_eq_cards/ | 1600×1000]*

**The decision:** P(a|f,c) = softmax(−‖f−μ_c‖²/τ) — geometry, not reward.
**The gate (3 layers):** allow ⟺ G-ABS ∧ G-REL ∧ G-RATE — floor (α·q·V ≥ θ_min) + drift (0.7× rolling baseline) + rate (W=20, 0.85× threshold).
**Asymmetric learning:** η_override = 0.01, η_confirm = 0.05 — one bad event moves the centroid 5× less.
**Re-convergence:** re-convergence ratio γ = N₁/N₂ > 1 (a different quantity from the advantage scaling) — proved (4 paths), simulation-confirmed (γ ≈ 1.2, 270 runs). Pilot magnitude: EXP-G1 Tier 1 gate.
**Platform:** D(n) ~ n^2.15 — five copilots, ten discovery pairs. *(Measured, JM apparatus.)*

*Action selection is never reward maximization.*

**Where does more machinery help?** The investigation loop can be run at increasing levels of recurrence — from a single scoring pass, through state-conditioned acquisition (the VLD loop that powers the enrichment controller), up to carried or gated recurrent state and a learned routing policy. Value appears at the acquisition level and does *not* increase as machinery is added above it: on a paired study, a closed-form static router reached 60.8% routing quality; adding carried recurrent state reached only 56.6%, and gated variants underperformed both. The one loop RL controls with gain is *how much to acquire* — not how much depth to add over fixed evidence. *(Geometry-derived.)*

*[GRAPHIC: RL-RECURRENCE-LADDER — "Where does more RL machinery help?" Step chart: value at acquisition (60.8%, green) > carried recurrent state (56.6%, amber) > gated variants (gray). Annotation: "Value appears at acquisition. More machinery does not help." | TO GENERATE. | 980×400.]*

## 4. Four Guarantees

| Guarantee | What it means | Evidence |
|---|---|---|
| **G1** — Action selection is never reward maximization | Centroid scorer selects. RL proposes. The action path and the learning path are architecturally separate. | SOC production: RL_EXPLORATION_ENABLED=False. Centroid action authoritative. G1 boundary memo §§3, 6-9. |
| **G2** — Conservation is live and fail-closed | UNKNOWN, AMBER, RED, stale, missing, or provider-error → blocks promotion. No caller supplies a literal safe state. | 9,826 checks, zero violations. ScorerBackedProvider (SDK) or CachedAsyncProvider (SOC). |
| **G3** — Promotion requires measurable improvement with sufficient evidence | min n=30, paired bootstrap, FPR<5%, superiority, variance, conservation. Both gates must pass. | DefaultPromotionGate: 5pp superiority, 0.70 accuracy floor, 10+ shadow decisions. |
| **G4** — Variant state and outcomes are auditable and domain-scoped | Every variant proposal, shadow result, gate decision, promotion, and rollback is logged. Domain-scoped — Trading variants don't affect SOC centroids. | In-memory variant ledger. Production decisions use GraphStore/AGE path. |

---

*[GRAPHIC: `C12_ae1_detect_propose_shadow.jpg` — Six-step AE lifecycle: detect drift → propose variant → shadow test → conservation gate → promote/rollback → monitor. Shows the full promotion pipeline. | ✅ EXISTS in graphics-renamed/. | 980×400.]*

## 5. The G1 Boundary — SOC Specific

SOC uses Option A strict: RL_EXPLORATION_ENABLED=False in production. Exploration is retained as a proposal/shadow-learning signal — it proposes, it doesn't override. The centroid action is authoritative. Promotion is the governed path for adoption.

Why SOC is strictest: 20:1 penalty ratio. A missed escalation in a SOC costs 20× a false positive. The cost of a wrong autonomous action is too high for exploration to override judgment. The sidecar learns; the scorer decides; conservation governs.

---

## 6. Difference from Traditional Directional Reward Functions

| Dimension | Traditional RL | CI Architecture |
|---|---|---|
| **What selects the action?** | Reward-maximizing policy (ε-greedy, softmax over Q-values, policy gradient) | Centroid geometry (L2 distance to nearest prototype, softmax). Deterministic. Inspectable. |
| **What the reward does** | Directly updates the policy. Higher reward → more likely to repeat action. The reward IS the learning signal. | Computes a signal for the AgentEvolver sidecar. The reward informs operational improvements — it does NOT select actions. |
| **Learning signal** | Reward (noisy, shaped, potentially manipulated) | Verified outcome (analyst confirms or overrides). Binary ground truth + graded financial impact. |
| **Competence boundary** | None. The policy always selects an action. A novel state gets the same treatment as a well-explored one. | Conservation law: α·q·V ≥ θ_min. Novel category → α low → ABSTAIN. The system earns the right to act. |
| **Adversarial robustness** | None built-in. Poisoned rewards corrupt the policy. Detection is external. | Three layers: asymmetric η (damped override learning), conservation gate (quality-based pause), AE (drift detection + rollback). 57%→14%. |
| **Model dependency** | Policy IS the model weights. Swap model = lose policy. | Policy IS the centroid geometry. Model-independent. Swap model = keep judgment. +36.89pp is in the geometry (EXP-C1). |
| **Auditability** | "Maximized expected reward" — opaque. | "Nearest centroid at distance 0.034 on 6 factors" — inspectable, reversible. |
| **Improvement rate** | d/dt > 0, d²/dt² ≈ 0. Linear improvement. Each episode adds same marginal value. | d/dt > 0, d²/dt² > 0 at inflection (measured, EXP-RL-DIRECT — logistic baseline). AE-mediated acceleration beyond baseline: hypothesis for pilot. |
| **What survives disruption?** | Nothing — retrain from scratch after regime break. | Centroid geometry provides warm-start. Re-convergence ratio γ = N₁/N₂ > 1 (a different quantity from the advantage scaling; proved, 4 paths; γ ≈ 1.2 in production-faithful simulation, 270 runs). Pilot measurement: EXP-G1 Tier 1 gate. Recovery faster than initial calibration. |
| **Cross-domain discovery** | Not architecturally possible. Each domain has its own policy. | D(n) ∝ n^2.15 (measured). Five domains, 10 discovery pairs. Attention sweeps across shared graph. |

---

*[GRAPHIC: `C11_recov1_recovery_faster_initial.jpg` — Two-arm re-convergence: N₁ vs N₂. γ = 1.43 (oracle-separation run) vs γ ≈ 1.2 (production-faithful, 270 runs). Recovery faster than initial calibration. | ✅ EXISTS in graphics-renamed/. | 980×400.]*

> **Honesty note on d²/dt²:** The positive second derivative before the inflection point is a property of the logistic learning curve (measured, EXP-RL-DIRECT, 3 seeds). Any system with this convergence shape exhibits it. The claim that AE makes d²/dt² LARGER than the baseline — that the sidecar adds acceleration beyond what the centroid geometry produces alone — is a hypothesis, correctly flagged as EXP-AE-SECONDDERIV in §7. Until that experiment runs, the "capital not expense" argument rests on the measured logistic shape, not on AE-specific acceleration.

---

## 7. Experiments — Validated and Potential

### Validated (have IDs, published)

| Experiment | Result | What it proves about the sidecar |
|---|---|---|
| EXP-C1 | +36.89pp (L2 vs dot, zero-learning) | Architecture accuracy is in the geometry, not the RL signal |
| EXP-AE-DECISION | 57%→14% non-recovery | AE + conservation recover from adversarial poisoning |
| EXP-RL-SCORER | 3 RL strategies (EMA, Thompson, hybrid), none beat uniform η=0.05 | RL belongs in AE sidecar, NOT in scorer — confirms separation |
| RL-CTRL-2C | +6.8pp S2P / +6.5pp SOC at fewer reads; safe at λ=0 | RL controls the enrichment budget — wins in the sidecar loop, never in the scorer |
| EXP-RL-DIRECT | Logistic fit R²=0.879, three regions | Learning curve shape is logistic (amenable to d²/dt² analysis) |
| V-CGA-FROZEN | +5.9pp Day-1 (p=1e-6) | SituationAnalyzer context enrichment is independent of RL |
| EXP-G1 | γ>1, all cells, 50 seeds; γ ≈ 1.2 (L2, 270 production-faithful runs) | Recovery after disruption is faster than initial learning. Tier 1 (pilot magnitude): pending |

### Potential (would strengthen the business case)

| Experiment | What it would show | Priority |
|---|---|---|
| EXP-AE-CONVERGENCE | Decisions to 80% quality WITH vs WITHOUT AE — quantifies AE contribution in decision-count terms | HIGH — gives a concrete "AE saves N decisions" number |
| EXP-AE-SECONDDERIV | Measure d²/dt² at inflection WITH vs WITHOUT AE — confirms AE is the mechanism behind acceleration | MEDIUM — strengthens CFO "capital not expense" argument |
| EXP-SIDECAR-COST | Business cost of reward-in-scorer (wasted decisions, accuracy gap) vs sidecar | LOW — EXP-RL-SCORER already covers this technically; business framing would add value |

---

## 8. Graphics (15 total: 12 exist, 3 to generate)

| # | Marker / File | Location | Use in doc | Status |
|---|---|---|---|---|
| 1 | rl_hero_sidecar_that_makes_judgment_compound.jpg | renamed_rl_arch/ | Opening — traditional RL vs CI sidecar, G1-G4 badges | ✅ EXISTS |
| 2 | `pub_safety_layers_r2.png` | charts/ | §2 Three-layer safety gate characterization | ✅ EXISTS |
| 3 | `A1_rl_sidecar_architecture.jpg` | graphics-renamed/ | §2 Architecture diagram | ✅ EXISTS |
| 4 | `C10_eu_ai_act_compliance.jpg` | graphics-renamed/ | §3.1 Auditability — EU AI Act mapping | ✅ EXISTS |
| 5 | `MOD2_H9_agent_protected_v5b.jpg` | renamed_gap_v1/ | §3.3 Adversarial resilience — 57%→14% | ✅ EXISTS |
| 6 | `ADD2_second_derivative_chart.jpg` | renamed_gap_v1/ | §3.4 Second derivative — capital vs expense | ✅ EXISTS |
| 7 | `GM02_five_copilots_ten_pairs.jpg` | fixed-renamed/ | §3.5 Platform economics — D(n) ∝ n^2.15 (measured) | ✅ EXISTS |
| 8 | `pub_ri7_adaptive_vs_uniform.png` | charts/ | §3.6 RL enrichment controller — adaptive vs uniform | ✅ EXISTS |
| 9 | RL-OFFLINE-ROUTING | TBD | §3.7 — Why not just use RL for routing? | TO GENERATE |
| 10 | `eq_rl_sidecar_consolidated` | rl_eq_cards/ | Five Equations box — all five equations, THE LINE footer | ✅ EXISTS |
| 11 | RL-RECURRENCE-LADDER | TBD | Between §3/§4 — Recurrence ladder value plateau | TO GENERATE |
| 12 | `C12_ae1_detect_propose_shadow.jpg` | graphics-renamed/ | §4/§5 boundary — AE lifecycle | ✅ EXISTS |
| 13 | `C11_recov1_recovery_faster_initial.jpg` | graphics-renamed/ | §6 Comparison table — γ>1 recovery | ✅ EXISTS |
| 14 | `P6_seven_components_v2.jpg` | renamed_broad_themes/ | Reference — full platform context | ✅ EXISTS |
| 15 | RL-SIDECAR-SUMMARY-HERO | TBD | Top of doc — Standalone hero, all RL concepts (1920×1080 + LinkedIn OG + square) | TO GENERATE |

---

## 9. Honesty Constraints (from demo_scenarios_v2.7)

- **F-25:** Never say "RL" for the primary decision mechanism. The primary mechanism is centroid-distance scoring from verified decisions. RL is a sidecar.
- **F-26:** Signals transfer across copilots; judgment geometry is per-copilot. No shared cross-copilot judgment claim.
- **F-27:** Roadmap (ARCH) is fine. Implying ARCH is LIVE is the violation.
- **SOC learning:** DISABLED by default (RL_EXPLORATION_ENABLED=False). Any "watch it learn" beat on SOC won't fire unless explicitly enabled.

---

*v6.2 (Sep 2026): JM redesign results propagated from jm_redesign_results_note_v6 — discovery scaling updated to n^2.15 measured (was n^2.11 simulation-only). Per-threat-model conservation sentence added (C3 outreach register). Re-convergence γ disambiguation added. RGI tech paper results incorporated: enrichment controller detail table, adversarial offline-RL question (§3.7), recurrence ladder. Standalone hero graphic (RL-SIDECAR-SUMMARY-HERO) added. Prior: v6.1.*
