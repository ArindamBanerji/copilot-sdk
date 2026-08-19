# Production Architecture for Compounding Intelligence: Learning Loops, Adversarial Robustness, and the μ/σ Separation

**Arindam Banerji, PhD** · Dakshineshwari LLC, Santa Clara, CA · banerji.arindam@gmail.com
*April 22, 2026 (v9.2 — final polish pass from v9.1; v9.3 — April 29, 2026: two-phase learning, batch pipeline, James-Stein shrinkage, defense in depth, Fisher-inspired asymmetry, discriminative metric learning)*

---

## Abstract

Most enterprise AI systems that claim to learn do not change their policy after verified outcomes. This paper presents the production architecture required for genuine compounding intelligence — where every verified decision durably improves the system's future behavior — validated across ~180 experiment entries (47 primary experiments plus sub-experiments from two multi-cell factorials totaling 1890 cells), adversarial testing, deployment persona validation, and real-data distribution characterization. We identify six architectural primitives that together make compounding possible: inspectable distance-kernel scoring, a protected learning loop with two-phase learning (centroid means → discriminative precision weights via James-Stein shrinkage) and a conservation guarantee, the μ/σ separation (accumulated experience vs current awareness, architecturally firewalled), binding runtime gates including a batch promotion gate, adversarial robustness with defense in depth (shrinkage + promotion gate + rollback), and calibrated confidence for autonomous action.

**Key results.** The learning loop improves accuracy from 71.7% to 78.9% over 1,000 decisions in realistic simulation (V3A). Asymmetric learning rates (η_confirm=0.05, η_override=0.01, derived from η_confirm·(2q̄_worst−1) at q̄_worst=0.60) prevent 13–27pp centroid degradation from realistic analyst override quality (B5B-PROXY, 24 personas; four-judge validated April 16, 2026). A conservation law α·q·V ≥ θ_min = 23.53/(α·V) ≈ 0.467 at SOC canonical provides a runtime guarantee (three-judge validated; q and α operational definitions closed SOC-Q1 April 19, 2026). DiagonalKernel (per-factor 1/σ² weighting) delivers **+13.2pp peak over L2** on heterogeneous-noise data (V-MV-KERNEL-HET, 390-cell factorial) and **+7.67pp asymptotic** across the noise-ratio range (UNI-DK-01 v5.3, 1500 cells), with rule-based kernel selection locking at max(1000, 20·V·α) verified decisions. The gains carry a **calibration cost** — DiagonalKernel's ECE degrades monotonically with noise ratio (10.4× L2 at NR=5.0); the architecture separates prediction channel (argmax, unaffected) from estimation channel (kernel-independent signals). **Re-Convergence Theorem (CC-21 Tier 2 QUALIFIED):** γ > 1 ⇔ ε_firm > 0.125 — binary prediction confirmed. Effect size γ ≈ 1.2 for L2 kernel (production-faithful 270-run sweep, May 2026). DiagonalKernel with stale pre-disruption weights reverses the effect (CLAIM-DK-STALE: 1.3–1.9× slower). Four structural proof paths; binary simulation confirmed both directions; four-judge math polls April 8 + 16, 2026. The μ/σ firewall holds at Frobenius 0.0028 (EXP-S3). Adversarial testing: 38% of harmful-operator seeds show no autonomous recovery (EXP-OP2-N100, 95% CI 29–48%). Synthesis layer: +9.27pp at full coverage (EXP-S1), ≤0.15pp poisoning degradation at production conditions (EXP-S2-REPRO). Referral routing handled by policy rules R1–R7 (72.7% DR, 12% FPR). Graph enrichment: three validated mechanisms (+5pp triage Day 1, 54.4% faster re-convergence after unfreeze, +42.69pp enriched initialization). Audit chain integrity refined via DecisionEntry/OutcomeEntry separation (XR-BUG-1, April 21, 2026). Analyst time savings validated at 30.85 min/alert (CI [29.90, 31.81], SANS-calibrated), $523K–$2.79M/year per-industry ROI.

This is a companion paper to [Banerji, 2026a] (arxiv v7.3), which presents the full mathematical framework.

**Keywords:** compounding intelligence, production AI architecture, adversarial robustness, learning loops, runtime gates, μ/σ separation, diagonal kernel, calibration tradeoff, noise heterogeneity, asymmetric learning, conservation law, re-convergence theorem, two-phase learning, James-Stein shrinkage, discriminative metric learning, batch promotion gate, defense in depth, audit chain integrity, online learning, enterprise AI

---

## 1. Introduction

### 1.1 The Gap Between Demo AI and Production AI

Enterprise AI has a dirty secret: most systems that claim to learn do not change their behavior after verified outcomes. A RAG-augmented LLM retrieves different context but applies the same reasoning. A periodically retrained classifier improves in batch but cannot incorporate Tuesday's verified decision into Wednesday's scoring. A rule engine captures expert knowledge but cannot refine it from operational feedback. The result: organizations invest in AI systems that are exactly as good on day 1,000 as they were on day 1. Every verified decision, every analyst correction, every operational outcome is discarded — narrated in a dashboard, but never compiled into improved judgment.

The cost is concrete. A SOC handling 10,000 alerts per month with 70% accuracy routes 3,000 alerts incorrectly. At $45 per analyst-minute and 15 minutes per misrouted alert, that is $2.025M per year in wasted analyst time. A system that improves from 70% to 79% over 1,000 decisions (our V3A result) eliminates 900 misrouted alerts per month. The compounding value: the system deployed 12 months ago is measurably better than one deployed today with identical code, because the first system has accumulated 12 months of verified decisions.

This paper addresses: what does it take to build a system where every verified decision durably improves future behavior, the improvement is robust to adversarial corruption, and the accumulated advantage cannot be reproduced by a competitor who copies the algorithm?

The answer, validated across ~180 experiment entries (47 primary experiments plus sub-experiments from two multi-cell factorials totaling 1890 cells), is six architectural primitives — each experimentally motivated, each with a specific failure mode when absent.

### 1.2 Six Primitives for Compounding Intelligence

**Primitive 1 — Inspectable scoring.** The decision function must be debuggable: inputs → scoring function → action → counterfactual. Distance-kernel scoring (Eq. 4-final) provides this: every decision is a distance calculation against readable profile centroids. The kernel choice alone moved accuracy by 36.89pp.

**Primitive 2 — The learning loop.** Verified outcomes must durably change the policy. The learning loop operates in two phases: Phase 1 estimates centroid means via the pull/push rule (Eq. 4b-final, saturates ~200 decisions, transferable +28pp); Phase 2 estimates deployment-specific discriminative precision weights via batch re-estimation with James-Stein shrinkage (ongoing, firm-specific, +3.2pp to +5.4pp). Every batch update passes through a promotion gate (holdout non-inferiority) before deployment. The asymmetric learning rate (η_confirm=0.05, η_override=0.01) addresses the operational reality that analyst overrides are noisier than confirmations. Without attenuation, realistic analyst quality (q̄=0.60–0.70) produces 13–27pp centroid degradation (B5B-PROXY). A conservation law α·q·V ≥ θ_min = 23.53/(α·V) provides a runtime bound. Re-Convergence Theorem (CC-21 Tier 2 QUALIFIED): after disruption, L2-kernel re-convergence is ~18% faster than initial calibration at production ε_firm values (γ ≈ 1.2). DiagonalKernel must reset to L2 during recovery (CLAIM-DK-STALE).

**Primitive 3 — The μ/σ separation.** Accumulated experience (μ, slow, protected) and current awareness (σ, fast, bounded) must be architecturally firewalled. Frobenius divergence 0.0028 (§4).

**Primitive 4 — Calibrated confidence.** Autonomous action requires that expressed confidence match actual accuracy. ECE = 0.036 at τ = 0.1 on centroidal data; calibration regime depends on kernel choice (§6).

**Primitive 5 — Adversarial robustness with defense in depth.** Three safety layers: James-Stein shrinkage (mathematical guardrail — interpolated scorer never below centroid baseline in 0/21 observed checkpoints at α=0.5), promotion gate (operational guardrail — no batch deploys without holdout non-inferiority), and instant rollback (recovery). 38% of harmful-operator seeds show no autonomous recovery — establishing that layered defense is non-optional (§7). Audit chain integrity (XR-BUG-1 fix, April 21, 2026) closes a structural tamper-evidence issue (§7.7).

**Primitive 6 — Binding runtime gates.** Advisory gates are annotations; binding gates are architecture. The conservation law adds a fourth gate type: learning freezes automatically when α·q·V < θ_min (§8).

A note on referral routing: handled outside the six primitives by ReferralRules R1–R7, a policy-based VETO mechanism that operates after scoring and before dispatch. The referral decision is independent of and cannot contaminate the scoring decision (§3.5).

### 1.3 What Current Approaches Get Wrong

**RAG + LLM systems** retrieve updated context but do not change their reasoning. The μ/σ separation (§4) solves precisely this problem: μ accumulates verified experience (the reasoning improves), while σ injects current awareness (the context updates). The two channels are architecturally firewalled so that bad context cannot corrupt accumulated judgment.

**Periodically retrained classifiers** (XGBoost, random forests, neural networks) improve in batch retraining cycles. Between retraining, every verified decision is wasted. ProfileScorer achieves 94.3% accuracy from decision 1 with zero labeled training data; XGBoost requires 1,300 labeled samples to reach 91.5%.

**LLM-as-judge systems** use frontier models for direct decision-making. Three frontier models (GPT-5, Claude Opus, Grok — the original diagnosis panel) given the complete experimental setup prescribed the literature-standard fix (+0.01pp). The actual solution — replacing learned gating with distance-kernel scoring — produced +36.89pp. LLM-as-judge systems can narrate but cannot experiment.

**The competitive moat.** An organization that deploys this architecture accumulates verified decisions in the centroid tensor μ. A competitor who copies every line of code starts with generic expert profiles (97.89%). After 12 months of verified decisions, refined centroids encode firm-specific patterns unreproducible from the algorithm alone. The Re-Convergence Theorem (§5) formalizes this: at production ε_firm ∈ [0.15, 0.40], γ > 1 for L2 kernel — recovery from disruption is ~18% faster than cold-start. Institutional knowledge survives disruptions with guaranteed convergence.

### 1.4 Contributions

- **The μ/σ separation** — a formal architecture for combining accumulated experience with current awareness without contamination, validated by firewall test (Frobenius 0.0028) and poisoning resilience (≤0.15pp at 20% adversarial rate under production conditions).
- **Adversarial characterization** — the first systematic adversarial testing of a centroid-based online learning system: acute damage (3× in 50 decisions), recovery trajectories (bimodal, 38% non-recovery at N=100), and the P-75 paradox. Extended by April 21 audit chain integrity finding (§7.7).
- **The operative window** — principled derivation of the synthesis coupling constant from the L2 margin distribution: λ=0.5 passes GATE-OP (p=0.0008). Not a tuned hyperparameter — a geometric constraint.
- **Distribution characterization** — first empirical measurement of the gap between synthetic centroidal and real IOC factor distributions (KL divergence 1.88–2.58 across three factors from 2,430 real records).
- **A ~180-entry experiment record** (47 primary experiments + 1890 factorial cells) spanning nine experimental series plus an analytical result: Foundation, Validation, Synthesis, Operator, Extension, Kernel Factorial (V-MV-KERNEL-HET 390 cells), Deployment Persona (24 personas), DiagonalKernel Characterization (UNI-DK-01 v5.3, 1500 cells), V-CGA-FROZEN; plus CC-21 Re-Convergence Theorem (analytical, Tier 2).
- **Asymmetric learning with conservation guarantee** — the first experimentally validated safety mechanism for centroid-based online learning under realistic analyst quality. η_override=0.01 (derived from η_confirm · (2q̄_worst − 1); four-judge April 16 validated) prevents 13–27pp degradation. Conservation law α·q·V ≥ θ_min = 23.53/(α·V) provides a runtime bound with operational definitions (q = rolling 400 verified; α = rolling 50 verified, SOC-Q1 closure April 19, 2026).
- **Two-phase learning with James-Stein shrinkage (v9.3)** — Phase 1 estimates centroid means (transferable, saturates ~200 decisions). Phase 2 estimates deployment-specific discriminative precision weights via batch re-estimation with James-Stein shrinkage (w̃_i = α·w_DK_i + (1−α), provably dominating either extreme for p ≥ 3; SOC p=144). The batch pipeline (7 lifecycle steps, promotion gate) ensures no untested update deploys. Fisher-inspired asymmetry (Layer A: Gaussian surrogate motivates why metric structure remains learnable; Layer B: empirical ρ_variance ≈ +0.35 at 18/18 checkpoints confirms) justifies Phase 2 persistence.
- **Defense in depth — three-layer safety architecture (v9.3)** — James-Stein shrinkage (mathematical guardrail) + promotion gate (operational guardrail) + instant rollback (recovery). Stronger than any single mechanism: 0/21 degradation at α=0.5 (shrinkage alone) is an engineering observation, not a statistical guarantee; the promotion gate catches edge cases shrinkage misses; rollback recovers from unforeseen interactions.
- **DiagonalKernel deployment architecture with calibration disclosure** — rule-based kernel selection (noise_ratio > 1.5 → DiagonalKernel), validated in a 390-cell factorial (+13.2pp peak SOC) and characterized across a 1500-cell NR sweep (+7.67pp asymptotic at NR=5.0). The calibration cost is disclosed and architecturally addressed: DiagonalKernel degrades ECE monotonically (10.4× L2 at NR=5.0), but the architecture separates prediction channel (argmax, unaffected) from estimation channel (kernel-independent signals).
- **Re-Convergence Theorem** (CC-21 Tier 2 QUALIFIED). γ > 1 ⇔ ε_firm > 0.125. Four proof paths. Binary prediction confirmed. Effect size γ ≈ 1.2 L2 (production-faithful sweep, May 2026), not γ ≥ 4.6 (idealized). DK stale weights reverse effect. Guaranteed recovery with automated kernel safety.
- **Referral architecture** — experimental demonstration that confidence-based referral is harmful (14% precision), policy-based rules are effective (72.7% detection, 12% FPR), and the referral signal lives in organizational context rather than factor-space geometry.
- **Audit chain integrity** — structural tamper-evidence issue identified (XR-BUG-1, April 21, 2026) and resolved via DecisionEntry/OutcomeEntry separation. Closes the three-layer safety story: audit chain integrity → q defensibility → conservation-law runtime guarantee.

---

## 2. Scoring Foundation

### 2.1 Why Distance-Kernel Scoring

The production architecture requires a scoring function that is inspectable (every decision traceable to a geometric calculation), calibratable (confidence scores match actual accuracy, with disclosed regime boundaries), and learnable (verified outcomes improve future scoring). Distance-kernel scoring satisfies all three. Each alert is represented as a factor vector f ∈ [0,1]^d (d=6 for SOC). Each (category, action) pair has a learned centroid μ[c,a,:]. The full centroid tensor μ ∈ ℝ^{(6×4×6)} = 144 values. A=4 confirmed by EXP-A4-DIAGONAL: 13pp structural gap between A=4 (action space: escalate, investigate, suppress, monitor) and A=5 (with refer_to_analyst as a fifth action — the tested-and-rejected alternative).

$$P(a \mid f, c) = \text{softmax}\!\left(-\frac{\lVert f - \mu[c,a,:] \rVert^2}{\tau}\right) \qquad [\text{Eq. 4-final}]$$

where τ = 0.1 (ECE = 0.036 on centroidal data, §6). The decision is transparent: the system chose action a because the alert's factor vector was closest to centroid μ[c,a,:].

### 2.2 The Kernel Choice: Why L2, Not Dot Product

On identical data with identical centroids, L2 distance achieves 97.89% while dot product achieves 61.00% — a 36.89 percentage point gap (EXP-C1). On bounded [0,1] factors, dot product is dominated by high-magnitude dimensions regardless of discriminative value. L2 correctly measures deviation from the centroid, not absolute magnitude. Cosine similarity (96.42%) partially addresses this but still loses 1.47pp to L2.

Profile centroids are compiled from domain expert knowledge — readable, auditable, immediately operational at 97.89% with zero learning.

### 2.3 Beyond L2: DiagonalKernel for Heterogeneous Noise

L2 treats all factors equally. In production, factor noise is heterogeneous: device_trust from inconsistent MDM data (σ=0.28) and threat_intel from curated CISA KEV feeds (σ=0.07) should not receive equal weight.

$$K(f, \mu) = (f - \mu)^{\top}\, \text{diag}(1/\sigma^2)\, (f - \mu)$$

When W = I (identity), DiagonalKernel reduces to L2 — L2 is a special case. DiagonalKernel's weights are discriminative precision weights — estimated by coordinate descent to maximize classification accuracy within the diagonal-kernel family. Under a Gaussian class-conditional surrogate, w_j = 1/σ_j² (inverse variance). In the deployed scorer, the weights are discriminative: the surrogate provides the scoring FORM; the estimator provides the UTILITY. This positions DiagonalKernel within the metric learning tradition (Xing et al., 2003; Weinberger & Saul, 2009), constrained to diagonal for interpretability and tractability (d parameters, not d²). The P28 pipeline (§8) measures per-factor σ during shadow mode. KernelSelector evaluates noise_ratio = max(σ)/min(σ). If > 1.5: DiagonalKernel. Otherwise: L2. Rule-based (not learned — CLAIM-67). Locks at **max(1000, 20·V·α) verified decisions**, where V is verified decisions per day and α is the override rate (V-GATE-STABILITY-confirmed: all three baselines — volume, precision ranking, agreement variance — stabilize at N=1000; binding constraint is volume baseline ≥ 20 days). At SOC canonical (V=200, α=0.25): 20·V·α = 1000 decisions ≈ 20 days. At lower-volume deployments: max(1000, ·) floor applies. The formula is self-calibrating — it adapts to deployment volume rather than hardcoded thresholds, mirroring θ_min's architecture.

**390-cell factorial (V-MV-KERNEL-HET, peak operating point).**

| Domain | L2 (heterogeneous) | DiagonalKernel (heterogeneous) | Lift |
|---|---|---|---|
| SOC | 79.5% | 92.7% | **+13.2pp** |
| S2P | 42.2% | 49.0% | +6.8pp |
| Healthcare (σ≈0.22, V-HC-CONFIG floor) | 71.3%→63.9% (−7.4pp, degrades) | 70.3%→73.9% (+3.7pp) | +10.0pp terminal |
| Healthcare (full noise profile, MR-COLAB-01 peak) | — | — | **+8.86pp** |

Healthcare at σ=0.22 is the worst-case floor (V-HC-CONFIG). MR-COLAB-01 (50 seeds, NR=5.0, full noise profile σ range 0.07–0.35) confirms DiagonalKernel lift at **+8.86pp peak** on the realistic heterogeneity customers actually encounter. Swing: +11.1pp (floor) / **+16.26pp (peak)**.

Off-diagonal correlations (ShrinkageKernel) add <1pp in both domains (V-HC-SHRINKAGE: off-diagonal adds −0.8pp on healthcare, consistent with the "naive Bayes paradox" of Domingos & Pazzani [1997] — diagonal approximation is empirically sufficient even under correlation). Noise ratio alone drives the advantage (Corr r=0.991 across 4 healthcare personas, HC-scaling).

**[Figure 1]** DiagonalKernel deployment: L2 on healthcare (RED, degrades −7.4pp) → DiagonalKernel (AMBER, learns +3.7pp floor, +8.86pp peak). Total swing: +16.26pp peak. [SHARED with arxiv v7.2 Fig 6.]

**[Figure 2]** 390-cell factorial heatmap: noise_ratio vs accuracy lift. r=0.991 correlation. [SHARED with arxiv v7.2 Fig 5.]

### 2.3.1 DiagonalKernel Characterization Surface

The 390-cell factorial characterizes the peak operating point. UNI-DK-01 v5.3 (1500 cells, mean-σ=0.175 fixed, controlled noise-ratio sweep, April 19, 2026 closure) characterizes the asymptotic advantage curve across the noise-ratio range — 30 seeds × 5 q̄-levels × 5 NR values × 2 kernels.

| Noise Ratio (NR) | DK asymptotic advantage over L2 | Cold-start fraction of advantage |
|---|---|---|
| 1.0 | 0.00pp (identity with L2) | — |
| 1.5 | +0.72pp | 73.5% |
| 2.0 | +1.99pp | 75.5% (peak) |
| 3.0 | +4.43pp | 69.6% |
| 5.0 | **+7.67pp (asymptotic)** | 54.5% |

Four pre-registered D-checks all PASS: (D1) monotonicity — asymptotic advantage grows monotonically with NR; (D2) NR=5 asymptotic ≥ 5pp; (D3) cold-start fraction ≥ 50% at all NR; (D4) per-cell q̄ standard deviation ≤ 1pp (actual 0.285pp).

Together, V-MV-KERNEL-HET (peak: +13.2pp on SOC at σ_level=0.30 heterogeneous, 390 cells) and UNI-DK-01 v5.3 (asymptotic: +7.67pp at NR=5.0, 1500 cells) jointly characterize the DiagonalKernel surface. The curve is citable across the noise-ratio range; 1890 total cells.

**[Figure 3]** UNI-DK-01 v5.3 characterization surface: asymptotic DK advantage curve (0.00 → +7.67pp) with cold-start % overlay (75.5% peak at NR=2.0 → 54.5% at NR=5.0). All four D-checks PASS. [SHARED with arxiv v7.2 Fig 4.]

### 2.3.2 Accuracy-Calibration Tradeoff

DiagonalKernel's accuracy gains come at a calibration cost. UNI-DK-01 v5.3 Experiment E2 measured Expected Calibration Error (ECE) across the same 1500 cells:

| NR | L2 ECE | DiagonalKernel ECE | Ratio |
|---|---|---|---|
| 1.0 | 0.055 | 0.055 | 1.0× (identity) |
| 1.5 | 0.053 | 0.148 | 2.8× |
| 2.0 | 0.051 | 0.223 | 4.4× |
| 3.0 | 0.046 | 0.325 | 7.0× |
| 5.0 | 0.041 | **0.420** | **10.4×** |

L2 remains well-calibrated across the NR range (all values ≤ 0.055). DiagonalKernel degrades monotonically — at NR=5.0, its ECE is 10.4× L2's. The inverse-variance weighting that makes DK more accurate on heterogeneous data also makes its softmax temperature no longer match the effective distance scale.

The production architecture addresses this by separating two channels:

- **Prediction channel (argmax accuracy) — unaffected.** DK's argmax is more accurate than L2's across all NR > 1. Customer-facing accuracy claims are unaffected: all measured on argmax, not confidence.
- **Estimation channel (confidence, routing) — routes via kernel-independent signals.** Confidence-sensitive consumers (auto-approve gate, conservation law AMBER auto-pause, triage ranking) rely on: (i) rolling verified accuracy (conservation law input, unaffected by kernel choice); (ii) softmax entropy for triage ranking; (iii) raw max_p with category-specific thresholds re-calibrated per deployment (PROD-4b).

This is why §3.1b's conservation-law formulation uses rolling verified accuracy (measured on ground truth) rather than softmax-derived confidence: architecturally, q must be kernel-independent.

**[Figure 4]** DiagonalKernel calibration surface: ECE vs NR for L2 (flat, well-calibrated) and DK (monotone degradation). Right panel: architectural response (prediction channel unaffected; estimation channel kernel-independent). [SHARED with arxiv v7.2 Fig 7.]

**Noise ceiling is kernel-dependent.**

| Kernel | GREEN | AMBER | RED |
|---|---|---|---|
| L2 | σ_mean ≤ 0.105 | 0.105 < σ ≤ 0.157 | σ > 0.157 |
| DiagonalKernel | σ_mean ≤ 0.157 | 0.157 < σ ≤ 0.25 | σ > 0.25 |

Healthcare deployments (σ≈0.22) move from RED (L2) to AMBER (DiagonalKernel). DiagonalKernel is a second form of compiled knowledge: μ encodes WHAT the firm learned; W = diag(1/σ²) encodes WHICH DATA TO TRUST.

---

## 3. The Learning Loop: From Narration to Policy Change

**Algorithm 1: Compounding Intelligence — Decision and Learning Loop (v2)**

```
Input: alert f, category c, centroids μ, kernel weights W,
       optional synthesis bias σ, coupling λ, temperature τ

DECISION PHASE:
  score[a] ← −(f − μ[c,a,:])ᵀ W (f − μ[c,a,:])     [kernel-weighted distance]
  if σ active: score[a] ← score[a] − λ · σ[c,a]     [synthesis bias]
  P(a|f,c) ← softmax(score / τ)                      [calibrated probability]
  action ← argmax P(a|f,c)

REFERRAL CHECK (VETO — independent of scoring):
  if ReferralRules.evaluate(alert, context) triggers: route to analyst

GATE PHASE (binding, not advisory):
  if confidence(action) < quality_threshold: ESCALATE
  if α(t)·q(t)·V(t) < θ_min: FREEZE LEARNING
  if Var(q) > dispersion_threshold: ALERT
  if ‖μ(t) − μ_checkpoint‖ > drift_threshold: ROLLBACK
  if verify_chain().valid == False: BLOCK LEARNING (audit chain gate, §7.7)

LEARNING PHASE (after verified outcome, only if conservation GREEN):
  CONFIRM: G ← W · (f − μ[c,a,:]); μ[c,a,:] += η_confirm_eff · G
  OVERRIDE: push μ[c,a_pred,:] away; pull μ[c,a_gt,:] toward f
  μ[c,a,:] ← clip(μ[c,a,:], 0, 1)                    [mandatory]

Invariants:
  - σ never enters the learning phase (μ/σ firewall)
  - Learning frozen when conservation state ≠ GREEN
  - Referral VETO cannot affect scoring accuracy
  - W = I during cold-start; DiagonalKernel after P28 qualification
  - Audit chain must verify before learning commits (XR-BUG-1 fix, §7.7)
```

### 3.1 The Operational Definition of Learning

A system learns if verified outcomes durably change the policy — the function mapping inputs to actions. The centroid update rule:

```
CONFIRM:  G ← W · (f − μ[c, a_pred, :])
          μ[c, a_pred, :] += η_confirm_eff · G

OVERRIDE: push μ[c, a_pred, :] away; pull μ[c, a_gt, :] toward f  [kernel-aware]

μ[c, a, :] ← clip(μ[c, a, :], 0.0, 1.0)              [Eq. 4c-final, mandatory]
```

where η_confirm=0.05, η_override=0.01, and η_eff = η / (1 + n[c,a] · decay_rate).

#### 3.1a Asymmetric Learning Rates — The P0 Fix

B5B-PROXY (24 deployment personas, q̄=0.57–0.91) revealed that symmetric η=0.05 produces 13–27pp centroid degradation at q̄=0.60–0.70. η_override=0.01 (5× attenuation) eliminates the degradation entirely.

**Derivation (Eq. 4d, four-judge validated April 16, 2026).** The attenuation ratio is not chosen — it is derived from worst-case analyst quality:

$$\eta_{\text{override}} = \eta_{\text{confirm}} \cdot (2\bar{q}_{\text{worst}} - 1) = 0.05 \cdot (2 \cdot 0.60 - 1) = 0.05 \cdot 0.20 = 0.01 \qquad [\text{Eq. 4d}]$$

where q̄_worst = 0.60 is the worst-quality deployment persona in B5B-PROXY's 24-persona validation. Four-judge math poll April 16, 2026 (GPT-4.1 / Claude Opus 4.7 / Grok 3 / Gemini 1.5 Pro) confirmed the derivation: the 5× attenuation is the factor that makes the override path's expected update point toward ground truth rather than away, given worst-case override quality. For deployments with measured q̄_worst > 0.60, η_override is re-derived during P28 qualification.

Extended validation (Block 9.1–9.5, April 5, 2026): per-analyst η weighting confirmed (+0.86pp at q̄=0.80, r=0.975–1.000); η change-rate cap ±0.005/cadence UNCONDITIONAL (F=8.14); deployment-specific spike detector validated (not hardcoded 3σ); category freeze on volume spikes blocks 65.5% spurious events; 1.5× update cap maintains monotone learning during spikes.

| Analyst Quality (q̄) | Symmetric η=0.05 | Asymmetric η_override=0.01 | Saved |
|---|---|---|---|
| 0.91 (excellent) | +1.2pp | +1.3pp | — |
| 0.70 (average) | −4.1pp | +0.8pp | 4.9pp |
| 0.60 (B5B-PROXY worst-case) | −6.8pp | +0.6pp | 7.4pp |
| 0.57 (poor) | −9.0pp | +0.5pp | 9.5pp |

**[Figure 5]** Asymmetric η trajectories: symmetric η (degrading at q̄=0.65) vs asymmetric η (stable). Footer annotation shows the Eq. 4d derivation explicitly. [SHARED with arxiv v7.2 Fig 9.]

#### 3.1b Conservation Law — Runtime Learning Guarantee

$$\alpha(t) \cdot q(t) \cdot V(t) \geq \theta_{\min} = \frac{23.53}{\alpha \cdot V}$$

**Operational definitions (SOC-Q1 closure, April 19, 2026).** The conservation law is only enforceable if its terms are measurable at runtime. Three-judge-validated formulation (March 2026, GPT-4o / Claude Opus / Gemini) established α·q·V ≥ θ_min; operational definitions were closed April 19, 2026:

- **q(t) = rolling verified accuracy over the last 400 decisions.** Long/stable window. SE(q) ≈ 3.6pp at n ≈ 100 verified samples. Measured on argmax correctness against ground truth, not on confidence — kernel-independent per §2.3.2.
- **α(t) = override rate over the last 50 verified decisions.** Short/responsive window. Separate window from q: α captures recent trend, q captures stable average.
- **V(t) = verified decisions per day.**

Separate windows for α and q are deliberate: α must be responsive to emerging issues (50-decision window); q must be stable enough to ground the conservation floor (400-decision window).

**The θ_min formula is self-calibrating.** At SOC canonical (V=200 alerts/day, α=0.25): θ_min = 23.53 / (0.25 · 200) = 23.53/50 ≈ 0.467. The original "0.467 hardcoded" is correct only at this operating point; θ_min = 23.53/(α·V) is the deployment-specific formula. Higher-volume deployments tolerate a lower conservation floor because more decisions provide more recovery signal per day. The formula shape matches KernelSelector's max(1000, 20·V·α) locking rule (§2.3) — both are self-calibrating gates, not hardcoded constants.

When the conservation product drops below θ_min: **AMBER auto-pause** — learning freezes until the product recovers. This protects the centroid from low-quality override cascades while preserving verified decisions for resumption.

**[Figure 6]** Conservation law timeline: α·q·V product over 180 days with θ_min line. GREEN zone (learning active), AMBER auto-pause dip (learning frozen), recovery to GREEN. Annotation box with operational q/α definitions. [SHARED with arxiv v7.2 Fig 10.]

### 3.2 What Learning Produces

**[Figure 7]** Learning trajectories: centroid-only (98.0%, flat), warm-start with learning (98.2%), cold-start recovery (58.5% → 90.7% over 1,000 decisions).

The accuracy improvement is modest (97.89% → 98.2%) but the informational content is significant: refined centroids carry this firm's specific patterns — which travel anomalies are benign in their environment, which device trust thresholds matter. That firm-specific refinement is unreproducible without this firm's operational data.

**Why this matters competitively.** Two firms deploy identical code on the same day. After 6 months, Firm A has processed 60,000 verified decisions, Firm B has 20,000. Firm A's centroids encode three times more operational experience — not in a database that can be copied, but in geometric positions that have been pulled and pushed by verified outcomes. The Re-Convergence Theorem (§5) gives this a formal backing: at production ε_firm ∈ [0.15, 0.40], Phase 2 re-convergence is faster than initial calibration — Firm A's advantage compounds in accumulated decisions. Recovery from environmental shifts is guaranteed (100% convergence, all tested conditions) and ~18% faster under L2 kernel for category-sparse disruptions.

### 3.3 Two-Phase Learning Architecture (v9.3)

The centroid update rule (Eq. 4b-final) and the DiagonalKernel weighting operate on different aspects of the scoring model with different learning dynamics.

**Phase 1 (Mean Convergence).** Eq. 4b-final estimates centroid means — the location of each class prototype. Saturates at ~200 verified decisions per (c,a) pair, after which label-noise contamination biases the estimate (K33, framework v4). Centroids transfer across deployments (+28pp) because risk-pattern locations are shared within a domain.

**Phase 2 (Discriminative Metric Learning).** After Phase 1 saturates, means are frozen. Verified decisions buffer for periodic batch re-estimation of DK precision weights. These weights are firm-specific and do NOT transfer (−5.6pp on cross-deployment). Improvement: +3.2pp at N=500 → +5.4pp at N=4000.

**Shrinkage.** The deployed scorer interpolates: w̃_i = α · w_DK_i + (1−α). At α=0: pure centroid (Phase 1). At α=0.5 (default): midpoint. James-Stein guarantees the interpolated estimator dominates either extreme for p ≥ 3 (SOC: p=144). Empirically: 0/21 below centroid baseline at α=0.5; 3/21 at α=1.0.

**Batch pipeline.** Phase 2 improvements deploy through a gated pipeline: decisions accumulate → novelty triggers re-estimation → composition check → estimator runs → promotion gate validates against holdout (accuracy within 1pp, no category degrades) → deploy or reject → history enables rollback. The promotion gate is the operational guardrail; shrinkage is the mathematical guardrail; rollback is recovery. Together: defense in depth.

**Fisher-inspired asymmetry.** Why does Phase 2 persist after Phase 1 saturates? Under a Gaussian surrogate, Fisher information for precision parameters remains informative after means stabilize (Layer A: theoretical motivation). Empirically, ρ_variance ≈ +0.35 at 18/18 checkpoints confirms the deployed estimator captures the same structure (Layer B: empirical confirmation). Fisher is motivation, not proof — the deployed estimator uses coordinate descent, not MLE.

**The compounding claim.** "The accumulation of novel verified decisions improves the scoring system's quality, realized at each promoted re-estimation." Batch-level, not per-decision. The switching cost deepens with every promoted batch — Phase 2 weights are deployment-specific.

### 3.4 Noise Robustness

**[Figure 8]** Warm-start accuracy: 0% noise (98.2%), 15% (98.1%), 30% (98.1%). Cold-start reference: 90.7%.

Thirty percent of verification signals are wrong, and accuracy drops by 0.1 percentage points. The mechanism: incorrect updates are small perturbations quickly corrected by the accumulated pull from the 70% of correct verifications. Combined with asymmetric η (§3.1a), the override path's attenuation further dampens the impact of incorrect signals. **Why this matters for deployment:** real-world verification signals are imperfect. A 30% noise rate is higher than any realistic operational deployment would exhibit. The learning loop remains deployable even when the human verification process itself has known error rates — a precondition for fielding the system with real analysts rather than oracle ground truth.

### 3.5 The Realistic Deployment Trajectory

The production-representative simulation (V3A, 50 seeds) starts at 71.7% and reaches 78.9% over 1,000 decisions. The deployment trajectory includes a kernel maturation phase: Day 1 (L2 kernel) → Day 20+ (DiagonalKernel, calibrated from P28). Realistic deployment with DiagonalKernel: frozen scorer 90.6% → learning adds +2.3–3.7pp → kernel transition adds the DiagonalKernel advantage on heterogeneous factors (+3.7pp floor to +8.86pp peak in healthcare).

**[Figure 9]** ProfileScorer at 94.3% from decision 1 vs XGBoost needing 1,300 labeled samples for 91.5%.

### 3.6 Referral Routing — Context, Not Geometry

Three candidate mechanisms tested:

- **Confidence gate:** 14% precision — 86% of referrals waste analyst time (EXP-REFER-LAYERED).
- **Centroid-based (A=5 ablation):** Tested as the alternative to A=4. Result: 13pp structural accuracy gap vs A=4 — refer_to_analyst has no natural factor signature in 6D space (EXP-A4-DIAGONAL). The A=4 action set (escalate, investigate, suppress, monitor) is canonical.
- **Policy-based rules (R1–R7, VETO):** 72.7% detection rate, 12% FPR. Rules encode organizational context that cannot be captured in factor-space geometry.

| Layer | Detection Rate | FPR | Net Value |
|---|---|---|---|
| None (baseline) | — | — | $709/100 alerts |
| Rules only (R1–R7) | 72.7% | 12% | **+$611 net** |
| Rules + confidence gate | WORSE | — | $544 net |
| Rules + override learning | +1.1pp DR | — | Marginal at 1,500 decisions |

The VETO inserts after the composite scoring gate, before response build. By construction, referral cannot affect scoring accuracy (|accuracy change| = 0.0pp).

**[Figure 10]** Referral architecture: three-lane flow. Scoring (ProfileScorer, A=4) → Referral (ReferralRules R1–R7, VETO) → Dispatch.

---

## 4. The μ/σ Separation: Experience vs Awareness

### 4.1 Two Kinds of Knowledge

**Experience (μ):** pattern recognition built from thousands of verified outcomes — slow to build, durable, protected.

**Awareness (σ):** current intelligence about active threats, new vulnerabilities, policy changes — fast to update, bounded in influence, architecturally separate.

$$P(a \mid f, c, \sigma) = \text{softmax}\!\left(-\frac{\lVert f - \mu[c,a,:] \rVert^2 + \lambda \cdot \sigma[c,a]}{\tau}\right) \qquad [\text{Eq. 4-synth}]$$

**The critical architectural constraint: μ is never updated using σ.** The synthesis layer can influence decisions but cannot influence learning. The moment those channels merge, short-term awareness overwrites long-term experience.

### 4.2 The Firewall Test

**[Figure 11]** Frobenius norm of centroid difference: μ learned with σ active vs without. Divergence: 0.0028 (0.28%). Gate criterion: ≤5%. **PASS.**

EXP-S3 measured the firewall directly: 300 decisions with synthesis active (λ=0.2) vs 300 without, same alerts, same seeds, same initial centroids. Frobenius difference: 0.0028 — effectively zero. The kill switch is safe: setting λ=0 returns to accumulated experience with zero contamination.

### 4.3 Synthesis Accuracy and the Coverage Dependency

**[Figure 12]** Accuracy vs λ curve (0.0 → 0.5). +2.30pp at 60% coverage (p=0.036). +9.27pp ceiling at 100% coverage.

At realistic coverage (60%), σ adds +2.30pp (p=0.036) — below the 3pp gate criterion, borderline. At full coverage (100%), σ adds +9.27pp. The production question is not "does σ work?" but "what claim coverage is achievable?" — an intelligence collection question, not an architecture question.

### 4.4 The Coupling Constant Is Not a Hyperparameter

**[Figure 13]** AUAC delta vs λ. λ=0.5: +0.0041 (p=0.0008, PASS). λ=1.0: −0.0018 (FAIL). The sign flip is caused by Loop 2 feedback reinforcement.

EXP-OP-MARGIN revealed: p10=0.1006, p25=0.2216, p50=0.4926. At λ=0.5, σ flips 22% of decisions — the tail, where margins are thin. At λ=1.0, σ flips 42%, including cases where the original action was correct. Only λ=0.5 passes GATE-OP (p=0.0008). The operative window is derived from the margin distribution geometry, not tuned on validation data.

### 4.5 Graph Enrichment — Three Validated Mechanisms

V-CGA-FROZEN (N=257, 90% power, resolved March 23, 2026) tested three distinct graph-enrichment mechanisms:

1. **Precision substrate (Mechanism 1).** Graph enrichment reduces per-factor σ by 23–46% (p<0.0001, CLAIM-59 updated). Lower σ causes DiagonalKernel to automatically upweight reliable factors. Result: **+5pp triage accuracy from Day 1** (p<0.0001, CLAIM-60). This is the primary compounding pathway.
2. **Frozen-centroid compounding (Mechanism 2, Batch G April 6, 2026).** During periods when learning is frozen (AMBER auto-pause, extreme noise, poor analyst quality), active graph enrichment continues to accumulate state. On unfreeze, the system reaches 85% accuracy **54.4% faster** than a non-enriched baseline (p<0.0001, 26/30 seeds, CLAIM-59). The graph compounds even when the centroid cannot.
3. **Enriched initialization (Mechanism 3).** Graph-enriched μ₀ placement (Empirical Bayes bootstrap from P28 Phase 2 σ measurements) produces **+42.69pp Day-1 accuracy** versus cold-start (CLAIM-62). Fisher information analysis confirms enrichment increases effective per-dimension learning rate (r=0.9669, CLAIM-64).

Live-learning convergence-speed was a definitive null: V-CGA-FROZEN v3 measured d=−0.010, p=0.873 — graph enrichment does NOT accelerate centroid-convergence speed (N_half). This falsifies an earlier hypothesis and is published per the "publish failures" standard.

The three validated mechanisms combine: graph enrichment produces Day-1 accuracy gains (Mechanism 1), protects compounding during freezes (Mechanism 2), and starts centroids in a better geometric position (Mechanism 3). None of them depend on accelerating live-learning speed.

**Two conditional paths remain open** (Phase 5 pending experiments): V-CGA-FROZEN v4 tests whether Empirical Bayes bootstrap reduces calibration time by placing centroids closer to μ* (N=100/arm); V-KERNEL-W tests whether lower σ from enrichment increases effective per-dimension learning rate under DiagonalKernel via Fisher information path (2 personas).

---

## 5. Re-Convergence — the Compounding-Speed Guarantee

The competitive moat narrative in §3.2 — "the system deployed 12 months ago is measurably better than one deployed today" — has now been formalized as a theorem. CC-21 status: **Tier 2 QUALIFIED** (analytical proof April 2026 + production-faithful experiment May 2026). Effect size: γ ≈ 1.2 (L2 kernel). DK with stale weights reverses effect. EXP-G1 (pilot-data measurement) pending.

**Setup.** After initial deployment (Phase 1), the system converges to operational accuracy (rolling accuracy ≥ θ = 0.85) in N_half,1 verified decisions. After an environmental disruption that shifts some alert categories (Phase 2), the system re-converges in N_half,2 decisions. Re-convergence speed ratio:

$$\gamma = \frac{N_{\text{half},1}}{N_{\text{half},2}}$$

**γ > 1 means Phase 2 re-convergence is faster than Phase 1 initial calibration.** This is the temporal compounding claim.

**Two-phase parameters.**

- ε_firm = ‖μ_canonical − GT₁‖ — firm-specific deviation from canonical expert-initialized centroid
- GT₂ = GT₁ + Δ — disruption shifts c_d of C categories; α_cat = c_d/C is the fraction disrupted
- At SOC canonical: C=6, A=4, d=6, c_d=2 → α_cat = 2/6 ≈ 0.333; ‖Δ‖ ≈ 0.25; θ = 0.85

**Theorem (Re-Convergence Speed, April 8, 2026).**

$$\gamma > 1 \quad \iff \quad \varepsilon_{\text{firm}} > \varepsilon_{\text{firm}}^{\star} = \frac{\alpha_{\text{cat}} \cdot \lVert \Delta \rVert}{1 - \alpha_{\text{cat}}}$$

At SOC canonical values: ε_firm★ = (2/6 · 0.25) / (1 − 2/6) = 0.0833 / 0.6667 ≈ **0.125**.

**Central mechanism — the rolling-window shortcut.** In Phase 2, (1 − α_cat) = 4/6 ≈ 0.67 of alert decisions come from undisrupted categories (μ_T1 ≈ GT₂ for those categories), so they are immediately correct. The effective Phase 2 accuracy threshold for the disrupted subset is:

$$p_d^{\star} = \frac{\theta - (1 - \alpha_{\text{cat}})}{\alpha_{\text{cat}}} = \frac{0.85 - 0.67}{0.33} \approx 0.55$$

Phase 2 only needs disrupted categories to reach 55% correctness (not 85%) for the rolling window to declare N_half,2. Phase 1 had no such shortcut — all C categories started cold from ε_firm.

**Four independent structural proof paths.** Each proves γ > 1 under the stated conditions without depending on the others:

1. **Geometric proof (April 8, 2026).** Decomposes the factor-space reachability of Phase 2 trajectories versus Phase 1 trajectories. Shows that Phase 1 must traverse full distance from ε_firm while Phase 2 only needs to traverse ‖Δ‖ · α_cat.
2. **Dimensional proof (April 8, 2026).** Bounds γ from below by the ratio of disrupted-category degrees-of-freedom to total tensor dimensions. At SOC canonical: γ ≥ 4.6 — an idealized lower bound. Production-faithful measurement (May 2026) shows γ ≈ 1.2 for L2 kernel due to η asymmetry, conservation gate pausing, and centroid clipping. The bound comfortably clears γ > 1 but the magnitude is not reached in practice.
3. **η₋ trap avoidance (April 8, 2026).** Shows that Phase 1 cold-start with initial accuracy p < ~0.65 risks the η₋ trap (override-path learning dominated by wrong-direction updates), while Phase 2 starts with undisrupted categories already above this threshold.
4. **Centroid-distance metric proof (April 16, 2026, Grok 3 primary).** Uses dist(t) = ‖μ(t) − GT‖_F as a model-independent convergence signal (addressing the N_half measurement gap: N_half conflates centroid learning with vector separability). Proves monotone decrease per verified decision in every seed, every phase, every experiment — independent of rolling-window luck or model-specific vector quality.

**Binary simulation confirmation (OracleSeparationExperiment, April 8, 2026).** The theorem makes a binary prediction: γ < 1 below ε_firm★ and γ > 1 above. Binary simulation confirmed both directions:

- ε_sim = 0.05 (below threshold) → γ = 0.714 < 1 ✓
- ε_sim = 0.20 (above threshold) → γ = 1.033 > 1 ✓

**Production-faithful experimental characterization (May 2026).** 270-run sweep (6 ε × 3 kernel modes × 15 seeds) with DK-aware update gradients and conservation gating:

| Kernel | γ (ε > 0.125) | Interpretation |
|---|---|---|
| L2 | 1.18 ± 0.98 | Effect is real, ~18% faster |
| DK-fixed (correct σ) | 1.07 ± 0.61 | DK gradient dampens |
| DK-estimated (stale σ) | 0.94 ± 0.18 | Stale weights REVERSE |

Binary prediction confirmed: 85% of ε < 0.125 runs give γ < 1. 100% convergence all conditions.

**Production deployment range.** Enterprise deployments have ε_firm ∈ [0.15, 0.40] — the expert-initialized canonical centroid never perfectly matches firm reality. Every production value in this range exceeds ε_firm★ ≈ 0.125. **All deployments clear the threshold.** Recovery is guaranteed and ~18% faster under L2 for category-sparse disruptions. The dimensional bound (γ ≥ 4.6) is idealized; the operational effect is moderate but genuine. DiagonalKernel must reset to L2 during recovery (§5.1 DK-STALE).

**Four-judge validation.** Two math polls (April 8 and April 16, 2026) by the four-judge panel GPT-4.1 / Claude Opus 4.7 / Grok 3 / Gemini 1.5 Pro confirmed all four proof paths and both simulation predictions. Full audit trail in `synthetic_data_generation_analysis_v2.md` and `math_synopsis_v14.md` §3.2.

**[Figure 14]** Re-Convergence Theorem hero: γ > 1 ⇔ ε_firm > α_cat · ‖Δ‖ / (1 − α_cat). Production values box (α_cat = 2/6, ‖Δ‖ = 0.25, θ = 0.85, ε_firm★ ≈ 0.125, production range [0.15, 0.40], all deployments clear). Four proof paths annotated. [SHARED with arxiv v7.2 Equation Graphic 11.]

**[Figure 15]** γ-Theorem phase diagram: simulation points at (ε_sim=0.05, γ=0.714) and (ε_sim=0.20, γ=1.033). Green/red region shading around the γ=1 line. Production range band [0.15, 0.40] highlighted. [SHARED with arxiv v7.2 Fig 15.]

**Relationship to EXP-G1.** EXP-G1 v3 (May 2026) measured γ_centroid = 1.02 (L2) and DK 1.9× slower. The DK finding is consistent with DK-estimated γ = 0.94 (stale weights). The L2 gap (1.02 vs 1.18) suggests additional production mechanisms (referral, AgentEvolver) further dampen the effect. Pilot-data measurement remains the Tier 1 path. CC-21 Tier 2 QUALIFIED is the defensible claim: "γ > 1 for L2 kernel in the production regime, when disruption is category-sparse, by theorem and production-faithful experiment (γ ≈ 1.2)."

---

### 5.1 DK-STALE: Stale DiagonalKernel Weights After Disruption

DiagonalKernel weights W = diag(1/σ²) estimated pre-disruption concentrate the update gradient on pre-disruption discriminative dimensions. Post-disruption, those dimensions may no longer be discriminative. Effect: 1.3–1.9× convergence slowdown vs L2.

**Operational procedure:** After disruption detection (conservation margin decline), KernelSelector resets to L2. Re-convergence proceeds under L2 (γ ≈ 1.2). After ~200 post-disruption verified decisions stabilize σ estimates, KernelSelector re-evaluates NR and may re-enable DK. This procedure is safety-critical.

**Claim:** CLAIM-DK-STALE, Tier 2. Evidence: reconvergence_v2 experiment + EXP-G1 v3.

---

## 6. Calibrated Confidence for Autonomous Action

Autonomous action requires calibrated confidence: when the system says "92% confident," it must be correct 92% of the time. V3B measured ECE across temperature values on centroidal data:

| τ | ECE | Mean Confidence | Interpretation |
|---|---|---|---|
| 0.1 | **0.036** | 0.928 | Well-calibrated |
| 0.25 | 0.190 | 0.760 | Underconfident — 95% correct, 76% expressed |
| 0.5 | 0.378 | 0.571 | Poorly calibrated |

At τ=0.25, the system was systematically underconfident: correct 95% but expressing only 76% confidence. At τ=0.1, ECE=0.036 — competitive with XGBoost (0.015) while maintaining higher accuracy.

**On realistic synthetic alert streams (V3B follow-up, TD-034):** τ=0.08 yields ECE=0.052 — modestly better than τ=0.1 at ECE=0.036 measured on uniform centroidal data. Per-deployment τ calibration is part of the P28 deployment qualification pipeline (§8).

**The calibration tradeoff introduced by DiagonalKernel (§2.3.2) is addressed architecturally.** The prediction channel (argmax action) is unaffected by DK's ECE degradation — customer-facing accuracy claims hold at +13.2pp peak / +7.67pp asymptotic over L2. The estimation channel (confidence-sensitive consumers: auto-approve gate, conservation law, triage ranking) routes via kernel-independent signals: rolling verified accuracy (kernel-independent by construction — measured on ground truth); softmax entropy (for triage ranking, robust to absolute-scale distortion); raw max_p with category-specific thresholds re-calibrated per deployment (PROD-4b).

**Business case.** A SOC at ECE=0.036 with a 90% confidence threshold can safely auto-close approximately 6,000 alerts per month of 10,000 processed. At $45/alert, that is $3.24M/year in reclaimed analyst capacity. At ECE=0.19, the same threshold would misroute 19% of auto-approved alerts, making autonomous operation unsafe.

Independently validated analyst time savings (CL-ECON-MEASURED, March 26, 2026, UNCONDITIONAL): **30.85 minutes per alert saved** (CI [29.90, 31.81]), calibrated against SANS SOC Survey 2024 (N=422 respondents, 44 min unassisted baseline). Per-industry ROI at V=200 alerts/day: healthcare $829K/year, FinServ $2.79M/year, midmarket $523K/year. Measured claim, not estimate.

---

## 7. Adversarial Robustness: What Happens When Something Is Wrong

### 7.1 The Question That Matters

The production question about any self-improving system is not "does it work when everything is fine?" but "what happens when something is wrong, and can you bound the damage?" We tested with deliberately harmful inputs (operators that are 0%, 25%, 50% correct) across 100 seeds, measured the damage, published the failures, and derived architectural requirements from those failures. The failures are not embarrassments — they are the safety specification.

### 7.2 Acute Damage and Recovery

**[Figure 16]** Window-by-window AUAC delta for correct (B), harmful (C), and mixed (P-50) operators, decisions 0–150.

| Condition | Acute delta (0–50 decisions) | Full AUAC delta (400 decisions) |
|---|---|---|
| B (correct, 100%) | +0.0120 | +0.0041 (p=0.0008) |
| P-50 (50% correct) | +0.0010 | +0.0012 (p=0.122, n.s.) |
| C (harmful, 0% correct) | −0.0200 | −0.0029 (p=0.994, n.s.) |

### 7.3 The 38% Non-Recovery Finding

**[Figures 17–19]** Recovery time box plots (N=20). Never-recover rates (N=100 with 95% Wilson CIs). Recovery speed violin plots — bimodal in all conditions.

| Condition | Mean T_recovery | NR% (N=20) | NR% (N=100) | 95% CI |
|---|---|---|---|---|
| B (correct) | 55 ± 240 | 5% | 8% | [4.1%, 15.0%] |
| A (no operator) | 178 ± 356 | 20% | 24% | [16.7%, 33.2%] |
| P-75 (75% correct) | 228 ± 445 | 20% | **28%** | [20.1%, 37.5%] |
| C (harmful) | 425 ± 561 | 35% | **38%** | [29.1%, 47.8%] |

**Finding 1 — The 38% architecture requirement (confirmed at N=100).** In 38% of harmful-operator seeds (95% CI: 29–48%), the system does not recover within the measurement window. Without rollback, 38% of harmful-signal scenarios produce permanent degradation.

**Finding 2 — The P-75 paradox (strengthened at N=100).** A 75%-correct operator has 28% non-recovery vs 24% for no operator. Mixed σ signals create a distribution that Loop 2 must learn and then unlearn.

**Finding 3 — The baseline itself is fragile.** Condition A (no operator) has 24% non-recovery (95% CI: 17–33%). Checkpoint+rollback is required as general infrastructure.

**Finding 4 — B-exp bimodality confirmed.** The indirect path produces a bimodal recovery distribution (std/mean = 3.64). TTL design must account for this binary outcome.

### 7.4 Lasting Damage Beyond TTL

The most safety-critical finding: harmful operators leave centroid damage that persists beyond TTL expiry.

| Condition | Post-expiry AUAC delta |
|---|---|
| B-exp (correct, expired) | +0.0128 ± 0.0190 — bimodal, unreliable |
| C-exp (harmful, expired) | −0.0124 ± 0.0187 — did not recover |

**TTL alone is not a sufficient safety mechanism.** The damage is in the centroids — TTL expiry removes the σ signal but not the centroid displacement it caused. Checkpoint + rollback is required.

### 7.5 Poisoning Resilience Under Production Conditions

**[Figures 20–22]** EXP-S2-REPRO: replication at λ=0.2 (Arm 0), AUAC vs poison at λ=0.5 Loop 2 running (Arm A), realistic vs synthetic AUAC (Arm B).

EXP-S2-REPRO extended poisoning tests to production conditions (λ=0.5, Loop 2 running, 200-decision warm-up). Maximum AUAC degradation: **0.15pp at 20% poison** — the safety mechanisms hold. Arm B confirmed negligible effect on realistic alert distributions. The caveat from v5 (EXP-S2 ran at cold-start λ=0.2) is resolved.

### 7.6 Asymmetric η as Adversarial Defense

Under symmetric η, a compromised analyst who systematically overrides correct decisions causes rapid centroid degradation (13–27pp at q̄=0.60–0.70). Under asymmetric η, the override path is attenuated 5× — the 5× is not an engineering choice but a derived constant: η_override = η_confirm · (2q̄_worst − 1) = 0.01 at q̄_worst=0.60 (§3.1a, Eq. 4d, four-judge validated April 16, 2026).

Combined with the conservation law (§3.1b), the system detects degradation via the α·q·V product and freezes learning before damage becomes irreversible. The complete safety architecture is defense in depth — three layers:

1. **James-Stein shrinkage** (mathematical guardrail): the interpolated scorer w̃ = α·w_DK + (1−α) provably dominates either extreme for p ≥ 3. At α=0.5: never below centroid baseline in 0/21 checkpoints. Catches gradual weight drift.
2. **Promotion gate** (operational guardrail): no batch of DK weights deploys without holdout non-inferiority (accuracy within 1pp, no category degrades). Catches edge cases shrinkage misses.
3. **Rollback + conservation law** (recovery and monitoring): instant revert to any prior state; α·q·V monitoring detects degradation; AMBER auto-pause freezes learning.

Asymmetric η operates within Layer 1 (reduces the damage rate of individual updates). The conservation law operates across Layers 2-3 (detects cumulative degradation and triggers system-level response). The three layers compose: even if shrinkage misses an edge case, the promotion gate catches it before deployment; even if both miss, the conservation law detects it and rollback recovers.

### 7.7 Audit Chain Integrity (XR-BUG-1, April 21, 2026)

Adversarial testing must extend beyond input-poisoning attacks to include structural-integrity audits of the system itself. On April 21, 2026, a Codex cross-repo adversarial audit found a structural defect in the tamper-evidence chain.

**The problem.** The shared library `ci-platform` computes `entry_hash` for each `LedgerEntry` by hashing all fields — including `outcome` and `analyst_override`. However, the SOC consumer intentionally mutates these fields *after* the entry is sealed (when a decision's outcome becomes known minutes to hours later). The docstring acknowledges the mutation: *"the entry_hash is NOT recomputed."* Consequence: `verify_chain()` fails on any entry where the outcome was recorded post-decision — which is every entry with a verified outcome.

The modeling error is treating a decision event and its outcome event as a single sealed record. They are not. At t₁, the analyst makes a decision (action, confidence, factors) — this should be sealed. At t₂, the system verifies whether the decision was correct — this should be a separate sealed event. The hash at t₁ cannot include information that doesn't exist until t₂.

**The fix (Alternative C — agreed April 21, 2026).** Separate decision events from outcome events. Each is a tamper-evident entry on the same chain:

```
Chain: D₁ → D₂ → O₁ → D₃ → O₂ → D₄ → O₃ → ...
  D_n = DecisionEntry (action, confidence, factors, timestamp)
  O_n = OutcomeEntry (decision_id, outcome, analyst_override, timestamp)
```

- `DecisionEntry.compute_hash()` hashes only immutable decision-time fields.
- `OutcomeEntry` is a new entry type with its own hash over (decision_id, outcome, analyst_override, timestamp, prev_hash).
- `verify_chain()` validates both entry types and checks prev_hash linkage.
- SOC stops mutating sealed entries; instead calls `record_outcome()` which appends an OutcomeEntry.

Two alternatives were rejected: (A) removing mutable fields from the hash only — weakens the guarantee because outcomes would no longer be tamper-evident; (B) recomputing the hash on mutation — breaks the chain because the next entry's `prev_hash` points to the old hash, and rehashing the entire chain tail defeats the purpose.

**The three-layer safety story.** Audit chain integrity is not an engineering footnote — it is the foundation of the conservation-law runtime guarantee:

1. **Audit chain integrity** (this section): DecisionEntry/OutcomeEntry separation ensures every verified outcome is provably recorded, in order, without mutation.
2. **q defensibility** (§3.1b): q(t) = rolling verified accuracy over 400 decisions. q is a well-defined quantity only if the outcomes backing it are faithfully recorded. Without audit chain integrity, q is an assertion; with it, q is a measurement.
3. **Conservation-law runtime guarantee** (§3.1b, §8): α·q·V ≥ θ_min is a binding gate only if q is trustworthy. A broken audit chain cascades upward: the runtime guarantee loses its grounding.

The fix restores the cascade. Implementation effort: ~4–5 days (ci-platform hash change, OutcomeEntry class, verify_chain update, SOC record_outcome wiring, migration path, Codex adversarial re-audit). Status as of April 22, 2026: architectural fix agreed; implementation plan addresses six identified refinements (type tagging symmetry, JSON canonicalization, sequence numbering for rebuild, multi-outcome policy, legacy ledger migration, and referential integrity warnings).

**The compliance implication.** The EU AI Act Article 9(2)(a)–(b) transparency obligations require tamper-evident audit trails — ship-blocker for regulated deployments. The DecisionEntry/OutcomeEntry refinement (April 2026) restores the tamper-evidence guarantee under Alternative C.

---

## 8. Binding Runtime Gates

The adversarial results establish the architectural requirement for binding runtime gates — evaluation as a control plane, not an advisory layer. Six gate types are operational:

**Quality gates.** Confidence thresholds for autonomous action. At ECE=0.036 (τ=0.1 on centroidal data), a threshold of 0.90 confidence is meaningful. Under DiagonalKernel with ECE degradation (§2.3.2), the gate routes via kernel-independent signals: rolling verified accuracy, softmax entropy, or category-specific re-calibrated raw max_p thresholds.

**Safety gates.** Operator quality verification. The P-75 paradox shows that even a 75%-correct operator causes harm. Only 100%-correct operators pass GATE-OP.

**Rollback gates.** The lasting-damage finding shows TTL is insufficient. Maintain μ_checkpoint, measure ‖μ(t) − μ_checkpoint‖, trigger rollback when drift exceeds threshold.

**Conservation gates.** The fourth binding gate type. Unlike the others (which operate per-decision), the conservation gate operates on the learning system itself — it freezes the learning mechanism when α(t)·q(t)·V(t) < θ_min = 23.53/(α·V). AMBER auto-pause preserves verified decisions for resumption without centroid-corruption cascades.

**Deployment qualification gates.** The P28 pipeline adds a fifth gate type that operates at deployment time. `LEARNING_ENABLED` defaults to False — enabling requires passing P28. The pipeline also derives deployment-specific values: per-factor σ (for KernelSelector and η_override derivation), τ (for calibration), and locks the KernelSelector at max(1000, 20·V·α) verified decisions (§2.3).

**Batch promotion gates (v9.3).** The sixth binding gate type — operates at the batch boundary between Phase 2 re-estimation and deployment. No DK weights deploy without passing the PromotionGate: overall accuracy within ε=1.0pp of baseline, no single category degrades >δ=2.0pp, minimum sample per active (c,a) cell ≥ N_min=20. Holdout = 20% of accumulated decisions, stratified by category. Combined with shrinkage (mathematical guardrail) and rollback (recovery), this constitutes defense in depth.

**Audit chain gates (per §7.7).** The seventh binding gate type — structural rather than behavioral. Before any learning commit, `verify_chain()` must return valid. If the DecisionEntry/OutcomeEntry chain cannot be validated (missing entries, hash mismatch, out-of-order sequence), learning is blocked at the commit phase. This gate is the control-plane enforcement of the three-layer safety story (§7.7): audit chain integrity → q defensibility → conservation-law runtime guarantee.

**[Figure 23]** P28 deployment qualification pipeline: 6-phase flow. Import → Compute per-factor σ → Shadow mode → Qualify → Enable learning → Monitor. Gates listed at each phase boundary.

**The distinction that matters.** Advisory gates log a warning. Binding gates prevent the action. When 38% of harmful-signal scenarios produce permanent degradation without intervention, "advisory" is an architectural failure.

---

## 9. Related Work

**Online learning theory.** The centroid update rule relates to LinUCB [Li et al., 2010], LVQ [Kohonen, 1990], and online convex optimization [Shalev-Shwartz, 2012]. Our contribution is asymmetric η with derived attenuation (Eq. 4d, §3.1a), the μ/σ separation, and the Re-Convergence Theorem as a compounding-speed guarantee (§5). The adversarial characterization shows 38% permanent degradation under harmful signals — a failure mode that standard regret bounds do not capture.

**Diagonal and weighted distance metrics.** Xing et al. [2003] and Weinberger & Saul [2009] established metric learning as a principled approach. Our DiagonalKernel uses the diagonal of the inverse covariance matrix derived from deployment-measured per-factor noise. Off-diagonal adds <1pp, consistent with the "naive Bayes paradox" [Domingos & Pazzani, 1997]. Our novel contribution is the calibration-cost disclosure (§2.3.2): DiagonalKernel degrades ECE monotonically with noise ratio, and the architecture addresses this by channel separation rather than kernel suppression.

**Calibration.** Guo et al. [2017] showed modern neural networks are miscalibrated. Our approach is simpler: L2 distance scoring with a single temperature parameter (τ=0.1) achieves ECE=0.036 without post-hoc adjustment, because the geometry of well-placed centroids naturally produces calibrated softmax outputs. The DiagonalKernel extension carries a calibration cost that architecture addresses explicitly (§2.3.2).

**Adversarial ML and data poisoning.** Beyond the standard test-time and training-time threat models, we test a third: poisoning the feedback signal that drives online learning in a deployed system. The lasting-damage finding (§7.4) is specific to centroid-based systems where the model state (μ) is directly modified by each verified outcome. EXP-S2-REPRO extends this to production conditions. The structural-integrity finding (§7.7, XR-BUG-1) opens a fourth threat class: adversarial audit of the system's own safety claims.

**Safe deployment.** The runtime gate architecture connects to the safe RL literature [Amodei et al., 2016]. Our contribution is quantitative: the 38% non-recovery rate, the P-75 paradox, and the seven-gate architecture (§8) provide specific architectural requirements grounded in experimental measurement and adversarial audit, not design principles alone.

**Shrinkage estimation and two-phase learning (v9.3).** James-Stein shrinkage [Stein, 1956; James & Stein, 1961; Efron & Morris, 1973] provides the mathematical guardrail for Phase 2 metric learning. Our two-phase architecture — first estimate location, then estimate scale with shrinkage — is related to the empirical Bayes tradition. The Fisher information argument motivating Phase 2 persistence [Fisher, 1925; Amari, 1985] uses a Layer A/B framework: the Gaussian surrogate motivates (Layer A), empirical alignment confirms (Layer B). This separation is novel in the applied ML literature on adaptive scoring.

**Re-convergence and concept drift.** The Re-Convergence Theorem (§5) extends the concept-drift literature by proving a speed advantage rather than just a recovery possibility. Gama et al. [2014] surveyed concept drift detection and adaptation; our contribution is the analytical result that under category-sparse disruption with ε_firm > 0.125, re-convergence is strictly faster than initial calibration, with a dimensional lower bound γ ≥ 4.6 at SOC canonical. Four independent structural proof paths; binary simulation confirmed.

---

## 10. Discussion, Limitations, and Future Work

### 10.1 Limitations

**Synthetic data — now characterized.** FX-1-PROXY-REAL quantified the distribution gap using 2,430 real IOC records (KL divergence 1.88–2.58). Real threat data is not Gaussian around a centroid: threat intelligence scores are bimodal (kurtosis −1.1), asset criticality skews high, and pattern recurrence is extremely right-skewed (skewness 2.8). Full real-SOC longitudinal validation remains the highest-priority post-deployment step.

**[Figures 24–25]** FX-1-PROXY-REAL: real vs synthetic factor distributions. KL divergence from synthetic — all three factors show KL > 1.8.

**EXP-S2-REPRO complete — caveat closed.** Poisoning resilience holds at production λ, with Loop 2 running: maximum 0.15pp AUAC degradation at 20% poison. EXP-S1 borderline: +2.30pp at 60% coverage (p=0.036) is below the 3pp gate.

**Convergence under adversarial conditions — partially addressed.** The ~180-entry experiment record (47 primary + 1890 factorial cells) provides statistically conclusive results for the tested conditions. Formal convergence under non-stationary distributions with adversarial feedback remains open; the conservation law α·q·V ≥ θ_min and the Re-Convergence Theorem provide practical substitutes.

**DiagonalKernel calibration tradeoff — disclosed.** DiagonalKernel's ECE degrades monotonically with noise ratio (§2.3.2). The architectural response (prediction/estimation channel separation) is specified, but production deployments must confirm that confidence-sensitive downstream consumers (auto-approve, conservation gate, triage ranking) have been routed to kernel-independent signals during P28 qualification.

**Audit chain fix — in implementation.** XR-BUG-1 (§7.7) architectural fix agreed; implementation underway. Six identified gaps (asymmetric type tagging, JSON canonicalization, rebuild-by-timestamp fragility, multi-outcome policy, migration of existing ledgers, referential integrity) are tracked. Production ledgers will require either grandfathering or rebuild-from-graph migration.

**Two-phase learning — designed, not shipped (v9.3).** The two-phase architecture, batch pipeline, and promotion gate are formalized in framework v4 (5-judge review, ~115 experiments) but implementation is v6.5 roadmap (~550 lines code + ~200 tests, ~2 weeks). Phase 1 is the existing v6.0 learning loop; Phase 2 adds batch re-estimation with shrinkage. The shrinkage safety result (0/21 at α=0.5) is from the framework v4 experiment record; production-scale validation is pending.

**Re-Convergence Theorem — CC-21 Tier 2, EXP-G1 pending.** Analytically proven; binary simulation confirmed. Empirical magnitude measurement (γ value from real pilot data) awaits EXP-G1. The defensible claim is the Tier 2 analytical result; magnitude is not.

### 10.2 Future Work

**EXP-OP3: Residual tracker diagnostic.** R(t) = μ(t) − μ_checkpoint as early-warning signal: correct operators produce bounded R_norm; harmful operators produce monotonically growing R_norm. Goal: distinguish correct from harmful within 50 decisions, before damage is irreversible.

**Two-phase learning validation (v9.3).** Phase 1 saturation timing and Phase 2 improvement curve on pilot data. Shrinkage non-inferiority with expanded seed/distribution coverage beyond the 21 checkpoints currently observed (rule of three: ≤14% upper bound at 95% CI). 2³ factorial channel composition validation (scorer × graph × labels, 8 conditions) as pilot milestone.

**EXP-G1: Empirical γ measurement.** Measures γ from pilot deployment Day 1+ using centroid_distance_to_canonical as the model-independent convergence signal (Re-Convergence Theorem proof path 4). CC-21 Tier 1 validation path. See `math_synopsis_v14.md` §3.2 for the full experimental design.

**V-CGA-FROZEN v4 and V-KERNEL-W (pending).** Two conditional paths: (i) V-CGA-FROZEN v4 tests whether Empirical Bayes bootstrap from P28 Phase 2 σ measurements reduces calibration time by placing centroids closer to μ* (N=100/arm, gates CLAIM-62/63); (ii) V-KERNEL-W tests whether lower σ from enrichment increases effective per-dimension learning rate under DiagonalKernel via Fisher information path (2 personas, gates CLAIM-64). Both use the V-CGA-FROZEN SVM methodology (Colab Pro, LLM-judge personas).

**Multi-prototype extensions.** FX-1-PROXY-REAL revealed bimodal threat intelligence scores (kurtosis −1.1) and extreme right-skew in pattern recurrence (skewness 2.8). A single centroid per (category, action) pair cannot capture bimodal structure. Multi-prototype (k=2–3) would recover the bimodal mass without breaking the μ/σ separation.

**Mahalanobis / ShrinkageKernel — RESOLVED.** DiagonalKernel captures the full advantage on tested domains. Off-diagonal correlations add <1pp. ShrinkageKernel deprioritized to v7.0 roadmap. Domains with ρ>0.80 remain untested.

**Penalty ratio sensitivity — partially addressed.** S2P uses penalty_ratio=5.0 (vs SOC 20:1). The penalty ratio now interacts with η_override — the two must be co-calibrated during P28 qualification.

**Real-data longitudinal validation.** V-SIM (9 deployment-realistic LLM-judge-generated streams) provides pre-customer synthetic validation. Real SOC data validation remains the highest-priority post-deployment step.

**Override learning for referral.** ReferralRules R1–R7 catch 72.7%. The 20.7% emergent fraction requires ML-based override learning, data-gated at ≥50 positive examples (~8 days at V=200).

**Cross-tenant meta-intelligence.** Anonymized threat pattern sharing across tenant graphs creates a network effect. The formal protocol requires differential privacy guarantees for regulated industries (HIPAA, DORA, CMMC).

**Full XR-BUG-1 implementation and migration.** Complete the DecisionEntry/OutcomeEntry refactor, address the six identified implementation gaps (§7.7), and migrate production ledgers. Scheduled for completion within 4–5 engineering days plus Codex adversarial re-audit.

---

## 11. Conclusion

Compounding intelligence is not a capability of the scoring equation — it is a property of the complete production architecture. The scoring equation (Eq. 4-final) provides the foundation. The learning loop (Eq. 4b-final) provides the mechanism. The μ/σ separation provides the safety (Frobenius 0.0028). The adversarial testing provides the honesty: 38% non-recovery under harmful conditions (95% CI: 29–48%, confirmed at N=100).

**Six primitives, each experimentally motivated, all now with significantly stronger evidence:**

1. **Inspectable distance-kernel scoring** — +36.89pp kernel gap (EXP-C1). +13.2pp peak DK over L2 (V-MV-KERNEL-HET). +7.67pp asymptotic (UNI-DK-01 v5.3, 1500 cells). Calibration cost disclosed and architecturally addressed.
2. **Protected learning loop with two-phase architecture and conservation guarantee** — Phase 1 estimates means (transferable, saturates); Phase 2 estimates discriminative precision weights via batch pipeline with James-Stein shrinkage (firm-specific, ongoing). η_override=0.01 derived (Eq. 4d) from worst-case q̄=0.60; prevents 13–27pp degradation. Promotion gate ensures no untested update deploys. Conservation law α·q·V ≥ θ_min = 23.53/(α·V) with operational q/α definitions (SOC-Q1, April 19, 2026).
3. **μ/σ separation with firewall at Frobenius 0.0028** — and graph enrichment as a second compounding pathway (3 validated mechanisms: +5pp Day-1, 54.4% faster re-convergence, +42.69pp enriched init).
4. **Calibrated confidence for autonomous action** — ECE=0.036 on centroidal data; DiagonalKernel calibration tradeoff handled via prediction/estimation channel separation; 30.85 min/alert analyst savings UNCONDITIONAL (CL-ECON-MEASURED).
5. **Adversarial robustness with defense in depth** — 38% non-recovery bounded; three safety layers: James-Stein shrinkage (mathematical, 0/21 at α=0.5) + promotion gate (operational, holdout non-inferiority) + rollback + conservation law monitoring + audit chain integrity (XR-BUG-1 fix, April 21, 2026).
6. **Binding runtime gates** — seven gate types including batch promotion gate and audit chain gate (§8).

**Plus three architectural results that resolve long-open questions:**

- **Re-Convergence Theorem** (CC-21 Tier 2, four proof paths, four-judge polls April 8 + April 16, 2026): γ > 1 ⇔ ε_firm > 0.125. Every production deployment clears the threshold. The compounding-speed claim is now a theorem, not a narrative.
- **Two-phase learning with batch pipeline and defense in depth** (v9.3): Phase 1 → Phase 2 via James-Stein shrinkage, 7-step gated pipeline, promotion gate. Fisher-inspired asymmetry (Layer A/B) justifies Phase 2 persistence. The switching cost deepens with every promoted batch.
- **DiagonalKernel deployment architecture** with rule-based KernelSelector (max(1000, 20·V·α), self-calibrating), two-surface characterization (peak + asymptotic), calibration-cost disclosure, and discriminative metric learning positioning.
- **ReferralRules R1–R7** as policy-based VETO (72.7% DR, 12% FPR), architecturally separated from scoring.

The ~180-entry experiment record (47 primary experiments + 1890 factorial cells: V-MV-KERNEL-HET 390 + UNI-DK-01 v5.3 1500) extends the evidence to a statistically conclusive experimental program.

**The competitive position.** Most enterprise AI systems are stateless between retraining cycles. The architecture presented here compounds — every verified decision durably improves future behavior, the improvement resists adversarial corruption (input-level and structural-integrity), and the accumulated advantage is unreproducible without this organization's operational history. A competitor who copies the algorithm starts at 97.89%. The system that has been running for 12 months has refined centroids and kernel weights encoding tens of thousands of verified decisions, and — by theorem — re-converges faster after each environmental shift. The moat is not in the code. It is in the centroids, the discriminative precision weights (deployment-specific, non-transferable), the conservation history, the referral rules, and now the re-convergence speed advantage that compounds against any competitor without this firm's operational trajectory. The two-phase architecture deepens this: Phase 1 centroids transfer (+28pp), but Phase 2 DK weights do not (−5.6pp) — the firm-specific advantage grows with every promoted batch.

**The standard we hold:** every claim has an experiment ID, every failure is published, every adversarial finding is acknowledged (including structural audits like XR-BUG-1), and the system is tested under conditions designed to break it.

---

## References

[1] Banerji, A. (2026a). *Cross-graph attention: Distance-kernel scoring, compiled ontologies, and super-quadratic discovery.* Arxiv v7.2, Dakshineshwari LLC. [Companion mathematical paper — full framework.]

[2] Banerji, A. (2026b). Experimental code and data. https://github.com/ArindamBanerji/cross-graph-experiments

[3] Banerji, A. (2026c). Compounding Intelligence 4.0 blog. https://www.dakshineshwari.net/post/compounding-intelligence-4-0-how-enterprise-ai-develops-self-improving-judgment

[4] Banerji, A. (2026d). *SOC Copilot: DiagonalKernel, asymmetric learning, and conservation guarantees.* Technical Report, Dakshineshwari LLC.

[5] Vaswani, A., et al. (2017). Attention Is All You Need. NeurIPS 30.

[6] Snell, J., et al. (2017). Prototypical networks for few-shot learning. NeurIPS 30.

[7] Kohonen, T. (1990). The self-organizing map. Proc. IEEE 78(9).

[8] Li, L., et al. (2010). A contextual-bandit approach to personalized news article recommendation. WWW 2010.

[9] Goodfellow, I.J., et al. (2015). Explaining and harnessing adversarial examples. ICLR.

[10] Amodei, D., et al. (2016). Concrete problems in AI safety. arXiv:1606.06565.

[11] NIST (2023). AI Risk Management Framework (AI RMF 1.0).

[12] Guo, C., et al. (2017). On calibration of modern neural networks. ICML.

[13] Jacobs, R.A., et al. (1991). Adaptive mixtures of local experts. Neural Computation 3(1).

[14] Miller, G.A. (1956). The magical number seven. Psych. Review 63(2).

[15] Shalev-Shwartz, S. (2012). Online learning and online convex optimization. FTML 4(2).

[16] Platt, J.C. (1999). Probabilistic outputs for support vector machines. Advances in Large Margin Classifiers.

[17] Kull, M., et al. (2019). Beyond temperature scaling. NeurIPS 32.

[18] Biggio, B., et al. (2012). Poisoning attacks against support vector machines. ICML.

[19] Steinhardt, J., et al. (2017). Certified defenses for data poisoning attacks. NeurIPS 30.

[20] Xing, E.P., et al. (2003). Distance metric learning. NeurIPS 15.

[21] Weinberger, K.Q. & Saul, L.K. (2009). Distance metric learning for large margin nearest neighbor. JMLR 10.

[22] Domingos, P. & Pazzani, M. (1997). On the optimality of the simple Bayesian classifier. Machine Learning 29(2-3).

[23] Borkar, V.S. (2008). Stochastic Approximation. Cambridge University Press.

[24] Gama, J., et al. (2014). A survey on concept drift adaptation. ACM Computing Surveys 46(4).

[25] Experiment reference catalog v2, Dakshineshwari LLC.
[27] Stein, C. (1956). Inadmissibility of the usual estimator for the mean of a multivariate normal distribution. Proc. 3rd Berkeley Symposium.
[28] James, W. & Stein, C. (1961). Estimation with quadratic loss. Proc. 4th Berkeley Symposium.
[29] Efron, B. & Morris, C. (1973). Stein's estimation rule and its competitors. JASA 68(341).
[30] Fisher, R.A. (1925). Theory of statistical estimation. Mathematical Proceedings of the Cambridge Philosophical Society 22(5).
[31] Amari, S.-I. (1985). Differential-Geometrical Methods in Statistics. Lecture Notes in Statistics 28.

[26] Claims registry v5, Dakshineshwari LLC. [Individual CLAIM-IDs cited in body text refer to entries in this registry. See registry for scope conditions, gates, and status.]

---

## Appendix A: Complete ~180-Entry Experiment Record

**Total:** 47 primary experiments + 1890 factorial cells (V-MV-KERNEL-HET 390 + UNI-DK-01 v5.3 1500) = ~180 entries.

**Series timeline.** Foundation: Feb 2026. Validation: Mar 1–4, 2026. Synthesis: Mar 5–8, 2026. Operator: Mar 8–12, 2026. Extension: Mar 14, 2026. Kernel Factorial: Mar 21, 2026. Deployment Persona: Mar 21, 2026. V-CGA-FROZEN v1–v3: Mar 23, 2026. Re-Convergence Theorem analytical: Apr 8, 2026. UNI-DK-01 v5.3 / SOC-Q1 closure: Apr 19, 2026. XR-BUG-1 audit chain fix: Apr 21, 2026.

### Foundation Series (13 experiments)

| # | ID | Question | Result | Key Number |
|---|---|---|---|---|
| 1 | EXP-5 | Oracle validation | PASS | 79.65% with GT oracle |
| 2 | EXP-A (MI) | Gating — static MI | FALSIFIED | 48.88% (−0.38pp) |
| 3 | EXP-A (Hebbian) | Gating — learned | FALSIFIED | 49.27% (+0.01pp) |
| 4 | EXP-A (aug) | Gating — augmentation | FALSIFIED | 51.03% (+1.77pp) |
| 5 | EXP-A2 | Per-category W | FAIL | 51.61% (+2.35pp) |
| 6 | EXP-C1 (L2) | Centroid oracle — L2 | PASS | 97.89% |
| 7 | EXP-C1 (cosine) | Centroid oracle — cosine | PASS | 96.42% |
| 8 | EXP-C1 (dot) | Centroid oracle — dot | FAIL | 61.00% |
| 9 | EXP-B1 | Profile scoring + learning | PASS | 98.2% warm, 90.7% cold |
| 10 | EXP-D1 | Cross-category transfer | Marginal | Config wins 2–14pp |
| 11 | EXP-D2 | Factor interactions | None | 0 significant / 75 pairs |
| 12 | EXP-E1 | Kernel generalization | L2 wins 2/3 | Mahalanobis wins mixed |
| 13 | EXP-E2 | Scale validation | PASS | 99.9% at 20×10×20 |

### Validation Series (5 experiments)

| # | ID | Question | Result | Key Number |
|---|---|---|---|---|
| 14 | V1A | Scaling exponent | PASS | b=2.11, CI [2.09, 2.14] |
| 15 | V1B | Norm explosion | PASS | 2.9M× without normalize |
| 16 | V2 | Push stability | PASS | 4,608× unclipped |
| 17 | V3A | Baseline comparison | PASS | L2 94.78% vs XGBoost 92.24% |
| 18 | V3B | Calibration | PASS | ECE=0.036 at τ=0.1 (centroidal) |

### Synthesis Series (4 experiments)

| # | ID | Question | Result | Key Number |
|---|---|---|---|---|
| 19 | EXP-S1 | Synthesis accuracy | Borderline | +2.30pp @ 60% cov (p=0.036) |
| 20 | EXP-S2 | Poisoning resilience | PASS | ≤2pp at 20% poison |
| 21 | EXP-S3 | Loop 2 independence (firewall) | PASS | Frobenius 0.0028 (0.28%) |
| 22 | EXP-S4 | λ sensitivity | PASS | Plateau width 0.300 |

### Operator Series (3 experiments + infrastructure)

| # | ID | Question | Result | Key Number |
|---|---|---|---|---|
| 23 | EXP-OP1 (3 var.) | Scalar σ + Loop 2 | FAIL × 3 | Near-ceiling; ε recovered |
| 24 | OP-MARGIN / OP1-FINAL | Margin diagnostic + GATE-OP | PASS | δ=+0.0041, p=0.0008 |
| 25 | EXP-OP2 | Harmful resilience | KEY | 35% non-recovery; lasting damage |
| 26 | SYNTH-EXP-0 | Infrastructure build | COMPLETE | synthesis.py, rule_projector.py |

### Extension Experiments (3 experiments, March 14, 2026)

| # | ID | Question | Result | Key Number |
|---|---|---|---|---|
| 27 | EXP-S2-REPRO | Poisoning at production λ=0.5 | PASS | 0.15pp max degradation |
| 28 | EXP-OP2-N100 | Harmful resilience at N=100 | Confirmed | 38% NR, CI [29%, 48%] |
| 29 | FX-1-PROXY-REAL | Real IOC distribution gap | GAP DETECTED | KL 1.88–2.58 |

### Kernel Factorial Series (March 21, 2026)

| # | ID | Question | Result | Key Number |
|---|---|---|---|---|
| 30 | **V-MV-KERNEL-HET** | **DiagonalKernel factorial (390 cells)** | **PASS** | **+13.2pp peak SOC, +6.8pp S2P** |
| 31 | V-HC-CONFIG | Healthcare diagonal (floor) | PASS | +3.7pp at σ=0.22 |
| 32 | V-HC-SHRINKAGE | Off-diagonal scoring | NO HELP | <1pp (naive Bayes paradox) |
| 33 | HC-scaling | Noise ratio correlation | PASS | r=0.991, 4 personas |
| 34 | KernelSelector | Kernel auto-selection (rule-based) | PASS | 4/4 correct, locks max(1000, 20·V·α) |
| 35 | MR-COLAB-01 | Healthcare reproduction (full profile, 50 seeds) | PASS | **+8.86pp peak** (NR=5.0) |

### DiagonalKernel Characterization Series (UNI-DK-01 v5.3, April 19, 2026)

| # | ID | Question | Result | Key Number |
|---|---|---|---|---|
| 36 | **UNI-DK-01 v5.3 E1** | **DK asymptotic advantage across NR (1500 cells)** | **PASS** | **+7.67pp at NR=5.0; monotone** |
| 37 | UNI-DK-01 v5.3 E2 | DK calibration (ECE) across NR | CONFIRMED | 10.4× L2 ECE at NR=5.0 |

All four D-checks PASS: D1 monotonicity, D2 NR=5 asymptotic ≥ 5pp, D3 cold-start fraction ≥ 50%, D4 q̄-SD ≤ 1pp (actual 0.285pp).

### Deployment Persona Series (March 21, 2026, 24 personas)

| # | ID | Question | Result | Key Number |
|---|---|---|---|---|
| 38 | B5B-PROXY | Realistic analyst quality | PASS | η_override=0.01 prevents 13–27pp |
| 39 | Phase 1 sweeps | Product boundaries | PASS | σ≤0.25 (Diag), V≥30, q̅≥0.70 |
| 40 | EXP-A4-DIAGONAL | A=4 vs A=5 | PASS | 13pp structural gap |
| 41 | EXP-REFER-COVERAGE | Referral taxonomy | DONE | 72.7% rule-expressible |
| 42 | EXP-REFER-LAYERED | Referral architecture | DONE | Rules: 72.7% DR, 12% FPR |

### V-CGA-FROZEN Series (March 23 – April 6, 2026)

| # | ID | Question | Result | Key Number |
|---|---|---|---|---|
| 43 | V-CGA-FROZEN v1 | Graph enrichment lifts frozen scorer? (N=50) | DONE | M1 ✅ M2 ❌ (underpowered) M3 ✅ +3.6pp |
| 44 | V-CGA-FROZEN v2 | Replication of v1 M2 (N=50) | DONE | M2 ❌ identical null |
| 45 | **V-CGA-FROZEN v3** | **Definitive M2 test (N=257, 90% power)** | **RESOLVED** | **M2 null d=−0.010, p=0.873; Precision substrate VALIDATED +5pp (p<0.0001)** |
| 46 | **Batch G (April 6, 2026)** | **Frozen-centroid compounding** | **PASS** | **54.4% faster re-convergence (p<0.0001, 26/30 seeds, CLAIM-59)** |

### Analytical Results (April 2026)

| # | ID | Question | Result | Key Number |
|---|---|---|---|---|
| 47 | **CC-21 / Re-Convergence** | **γ > 1 ⇔ ε_firm > 0.125?** | **Tier 2 PROVEN** | **Four proof paths; binary sim both directions; four-judge Apr 8 + Apr 16** |

### Phase 5: Pending Experiments

| # | ID | Question | Status | Gate |
|---|---|---|---|---|
| P1 | V-CGA-FROZEN v4 | Empirical Bayes bootstrap reduces N_half? | PENDING | N_half(T2) < N_half(C0) × 0.80. N=100/arm. Gates CLAIM-62/63. |
| P2 | V-KERNEL-W | Lower σ → higher effective η under DK (Fisher path)? | PENDING | N_half(W1) < N_half(W0) × 0.80 per dim. 2 personas. Gates CLAIM-64. |
| P3 | EXP-G1 | Empirical γ measurement (pilot Day 1+) | PENDING | Tier 1 path for CC-21. Centroid-distance metric per proof path 4. |
| P4 | XR-BUG-1 audit chain fix | DecisionEntry/OutcomeEntry migration | IN IMPLEMENTATION | 4–5 engineering days + Codex adversarial re-audit. |
| P5 | Framework v4 validation | Two-phase learning + batch pipeline on pilot | PENDING | Phase 1 saturation, Phase 2 curve, shrinkage coverage. |

**Plus factorial and persona sub-experiments (V-MV-KERNEL-HET 390 cells + UNI-DK-01 v5.3 1500 cells = 1890 additional cells).** Full catalog: experiment reference catalog v2 [25].

---

*Production Paper v9.3 · April 29, 2026 · Companion to cga_arxiv_short v7.3 [Banerji 2026a].*

*v9.2 → v9.3 additions (April 29, 2026): Two-phase learning architecture (§3.3). James-Stein shrinkage as mathematical safety guardrail. Batch pipeline with promotion gate (7 lifecycle steps). Fisher-inspired asymmetry Layer A/B. Discriminative metric learning positioning for DiagonalKernel (§2.3). Defense in depth — three safety layers (§7.6). Batch promotion gate as seventh binding gate (§8). §9 Related Work: shrinkage, Fisher. §11: updated primitives 2 and 5, added two-phase to architectural results. 5 new references [27]-[31]. All v9.2 content preserved.*
