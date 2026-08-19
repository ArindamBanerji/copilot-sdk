**Cross-Graph Attention: Distance-Kernel Scoring, Compiled Ontologies, and Super-Quadratic Discovery**

Arindam Banerji, PhD | Dakshineshwari LLC, Santa Clara, CA | banerji.arindam@gmail.com

*March 2026 (v5 — updated March 23, 2026; v7 — April 19, 2026; v7.1 — April 20, 2026: LLM-judge panel naming normalized, Table 2 experiment attribution corrected, business-implication paragraphs added; v7.2 — April 20, 2026: compacted for target length, markers preserved; v7.3 — April 29, 2026: two-phase learning formalization, James-Stein shrinkage safety, batch pipeline, Fisher-inspired asymmetry, discriminative metric learning positioning; v7.4–v7.5 — May 19, 2026: judgment memory as fourth cognitive type, signal-confidence inversion, agent-memory citation network [CoALA, Mem0, Zep, MAGMA, GAM]; v7.6 — June 1, 2026: canonical decisions D1–D4 — α = cumulative category coverage (override-rate definition retired), α_disrupt rename for re-convergence, θ_min reframed as empirically-calibrated cold-start interlock, information-gain vs operational compounding split, inversion sourcing clarified)*

# **Abstract**

We present a three-level framework for enterprise AI decision-making based on distance-kernel attention — a variant of transformer attention where L2 distance replaces the dot product as the similarity kernel. On identical data and identical profile centroids, L2 outperforms dot product by 36.89 percentage points (61.00% → 97.89%) for scoring decisions on bounded [0,1] features (Experiment C1). This magnitude confounding problem — where dot products on bounded features are dominated by high-mean dimensions regardless of discriminative value — affects any scoring system operating on pre-computed bounded features: credit scoring, insurance risk assessment, supply chain prioritization, and vendor evaluation.

The architecture operates at three levels: (1) single-decision scoring as distance-kernel attention (Eq. 4-final), (2) cross-graph entity discovery as cross-attention between domain knowledge graphs (Eq. 6), and (3) multi-domain discovery with n(n−1)/2 attention heads across n domains (Eq. 9). Profile centroids are compiled ontologies — domain expert knowledge encoded as readable, auditable vectors that refine through online learning.

Key results across ~180 experiment entries (47 primary plus 1890 factorial sub-cells): L2 outperforms dot product by 36.89pp on identical centroidal data (EXP-C1); DiagonalKernel (per-factor 1/σ² weighting) adds up to +13.2pp peak on heterogeneous noise (V-MV-KERNEL-HET, 390 cells) with characterized monotone scaling from 0.00pp at uniform noise to +7.67pp at NR=5.0 (UNI-DK-01 v5.3, 1500 cells); 90.6% zero-learning accuracy with A=4 action space; 71.7% → 78.9% over 1,000 decisions (50-seed realistic simulation); super-quadratic discovery scaling D(n) ∝ n^{2.11} (V1A, n=2–15). Asymmetric learning rates η_override = η_confirm · (2q̄_worst − 1) = 0.01 prevent 13–27pp centroid degradation (B5B-PROXY). A conservation law α·q·V ≥ θ_min (α = cumulative category coverage) ensures learning compounds rather than decays, with q operationally defined as rolling verified accuracy over 400 decisions. A two-phase learning architecture separates mean estimation (Phase 1, saturates ~200 decisions, transferable) from discriminative precision weight estimation (Phase 2, ongoing, firm-specific) via James-Stein shrinkage, with every batch update passing through a promotion gate before deployment — defense in depth with mathematical, operational, and recovery layers. The Re-Convergence Theorem (γ > 1 ⇔ ε_firm > 0.125) is analytically proven via four structural proof paths (two four-judge math polls, April 8 and 16, 2026). We position these mechanisms — centroid geometry, per-factor noise fingerprint, and conservation law — as judgment memory, a fourth cognitive-architecture type beyond the episodic/semantic/procedural taxonomy of agent-memory systems (CoALA, Mem0, Zep, MAGMA); judgment memory measures per-factor decision quality from verified outcomes and uniquely surfaces signal-confidence inversion, where the factor practitioners trust most carries the highest outcome-conditioned variance. All experiments use synthetic data; FX-1-PROXY-REAL characterized the distribution gap using 2,430 real IOC records. A companion paper [Banerji, 2026c] validates the production control plane.

**Keywords:** distance-kernel attention, profile-based scoring, compiled ontologies, cross-graph attention, diagonal kernel, noise heterogeneity, asymmetric learning, conservation law, calibration disclosure, prediction vs estimation channels, re-convergence theorem, two-phase learning, James-Stein shrinkage, discriminative metric learning, batch promotion gate, online learning, judgment memory, signal-confidence inversion, cognitive architectures, agent memory, enterprise AI

# **1. Introduction**

The dot product is the default similarity function in modern machine learning because transformers use it, and transformers dominate the current landscape. But the dot product's validity in transformer attention rests on a specific guarantee: representation learning. The training process ensures that semantically similar tokens have high dot products in the trained embedding space. That guarantee does not transfer to pre-computed feature vectors.

Enterprise AI systems routinely score items by bounded feature vectors without any such training guarantee. Credit scoring uses debt ratios and payment histories in [0,1]. Insurance risk assessment uses bounded risk factors. Supply chain prioritization uses lead-time ratios and quality scores. All operate on pre-computed, bounded, semantically-labeled features — exactly the setting where we measured a 36.89 percentage point accuracy gap from the kernel choice alone.

Our framework uses distance-kernel attention — a well-established variant in the attention literature [Tsai et al., 2019; Katharopoulos et al., 2020] — where similarity is measured by proximity in factor space rather than directional alignment. Profile centroids (ontological prototypes representing "what does this action typically look like?") serve as keys. The query asks not "which key points the same direction?" but "which key is closest?"

The framework operates at three levels that correspond structurally to components of transformer attention: Level 1 maps scoring to distance-kernel single-head attention with MoE routing, Level 2 maps cross-graph discovery to cross-attention (exact correspondence), and Level 3 maps multi-domain discovery to multi-head attention with n(n−1)/2 heads. Table 1 presents the complete correspondence.

## **1.1 Why Cross-Graph Attention Matters for Decision Intelligence**

The step forward is not a better classifier — it is a different category of reasoning. Current enterprise AI makes decisions one domain at a time. A security model scores an alert against security features. A threat intelligence model classifies indicators. An organizational risk model flags policy violations. Each operates in isolation. When a security alert coincides with a threat campaign targeting the same geography and an organizational restructuring that changed access controls, a human analyst is expected to synthesize across all three knowledge domains simultaneously — under time pressure, at scale, for every alert in the queue.

This synthesis is the hardest part of expert decision-making, and it is the part that current ML does not automate. Ensemble learning combines multiple models answering the same question. Cross-graph attention asks different questions across different knowledge domains and discovers connections that emerge only at the intersection — connections no single-domain model can surface because they require simultaneous visibility into domains that have no shared features, no shared training data, and no pre-specified relationships.

Three advances follow directly:

**From single-domain scoring to multi-domain reasoning.** Most enterprise ML is a classifier operating on one feature set from one data source. Cross-graph attention operates on n knowledge graphs simultaneously, producing n(n−1)/2 distinct discovery channels, each surfacing a qualitatively different category of insight (§3.3). At n=6, the system maintains 15 parallel cross-domain awareness streams — structurally beyond human monitoring capacity [Miller, 1956].

**From programmed queries to discovered connections.** Current systems find what you tell them to look for. Cross-graph attention finds what you did not know to ask about. The system evaluates every entity against every entity in every other domain — millions of pairwise scores per sweep — with no prior specification of what constitutes a meaningful connection. The Singapore example (§3.2) is not a better search; it is a connection that no analyst queried and no rule specified.

**From static models to compounding knowledge.** Most deployed ML systems either stay flat (no post-deployment learning) or decay (concept drift without retraining). Cross-graph attention is structurally designed to compound: each verified decision refines profile centroids via Eq. 4b-final (Term 1 of Eq. 13), each discovery enriches entity embeddings via Eq. 12 (Term 2), and each enrichment sweep creates conditions for new discoveries in subsequent sweeps (Term 3). The result is modeled to scale as O(n^{2.11} · t^γ) — what we term *information-gain compounding*: super-quadratic in domain count and super-linear in time. The n^{2.11} exponent is a simulation result (V1A); its production validation is the subject of EXP-G1 and it should be read as a modeled scaling property, not a measured production outcome.

**From recall to judgment quality.** Cognitive architectures for language agents (CoALA) [38] define three memory types: episodic (what happened), semantic (what is true), and procedural (how to act). Every agent memory system — Mem0 [39], Zep [40], MAGMA [41] — implements variations of these three. All solve the same problem: how does a stateless agent remember things across sessions? Our framework addresses a structurally different problem: how does decision quality compound across verified outcomes? The centroid geometry, noise fingerprint (per-factor σ from outcome-conditioned variance), and conservation law constitute a fourth memory type — judgment memory — that measures not what happened or what is true, but how WELL decisions are made and WHERE they are noise. In empirical deployment, episodic, semantic, and procedural memory can all confirm a systematically incorrect decision (the trusted-source auto-approve pattern in SOC data) that only judgment memory detects, because only judgment memory decomposes decision quality by factor against verified outcomes. We term this structural pattern signal-confidence inversion: the factor practitioners report highest confidence in is the factor with highest outcome-conditioned variance (σ). This appears in our domain-informed SOC factor design (device_trust σ=0.28, weight 6%), calibrated from security-domain expertise rather than live analyst decision logs (production-log validation is pending pilot deployment), with consistent results in calibrated synthetic deployments across three additional domains.

**The economic framing.** The three advances above carry a direct financial implication. Enterprise AI that does not compound is operating expense — it delivers the same capability forever, regardless of deployment duration. Enterprise AI that does compound is capital infrastructure — it appreciates with use, and the accumulated judgment is an institutional asset that survives model transitions. The kernel choice, the kernel weighting, and the learning dynamics are the three architectural decisions that determine which side of that line a system falls on. This paper measures all three: 36.89pp from the kernel (§2.2, §5.2), up to +13.2pp from the weighting (§3.1), and 13–27pp degradation prevented by the learning dynamics (§3.1). Downstream companion papers measure the compounding exponent γ directly; this paper provides the analytical floor via the Re-Convergence Theorem (§4.6).

[FIGURE 1 | eq_rosetta_stone.png | NBP | The Rosetta Stone: Transformers ↔ Cross-Graph Attention — side-by-side correspondence showing Q/K/V mapping to f/W/outcomes at Level 1, E_i/E_j/V_j at Level 2, and multi-head at Level 3. | §1 | Reusable from CGA Math blog CI-05]

## **1.2 Contributions**

Our principal contributions are:

- **Empirical demonstration that the similarity kernel is the highest-leverage design decision for scoring on bounded features.** L2 achieves 97.89% where dot product achieves 61.00% on identical data — a 36.89pp gap from changing one operation (EXP-C1). A second kernel finding: DiagonalKernel adds up to 13.2pp over L2 on heterogeneous noise (V-MV-KERNEL-HET, 390 cells) with characterized monotone scaling to +7.67pp at NR=5.0 (UNI-DK-01 v5.3, 1500 cells) — making the kernel weighting the second highest-leverage decision.

- **A three-level framework connecting enterprise decision-making to transformer attention.** The correspondence is exact at Level 2 (cross-graph discovery), structural at Levels 1 and 3.

- **The compiled ontology architecture.** Domain expert knowledge compiles into readable centroid vectors — auditable, revisable without retraining, immediately operational (97.89% on Day 1 centroidal synthetic; 90.6% on realistic data with A=4).

- **Super-quadratic discovery scaling (information-gain compounding).** D(n) ∝ n^{2.11}, 95% CI [2.09, 2.14], R² = 0.9999 across n = 2–15 domains (V1A, simulation). The near-perfect R² reflects fit to the discovery-cascade model; production validation is EXP-G1 (pending). Distinct from *operational* compounding (deployment quality×scope, a bounded onboarding effect reported in the companion control-plane work).

- **An original finding on frontier LLM reasoning.** Three frontier models available at the time of the original diagnosis (GPT-5, Claude Opus, Grok) correctly diagnosed the 49% accuracy failure but unanimously prescribed an intervention adding 0.01pp. The correct fix added 36.89pp. A complementary protocol — analytical derivation by LLMs, verification by independent four-judge panels — was used for the April 2026 math polls and worked cleanly.

- **A complete ~180-experiment record** — 47 primary experiments plus sub-experiments from two multi-cell factorials totaling 1890 cells — with all code and data publicly available at https://github.com/ArindamBanerji/cross-graph-experiments.

- **DiagonalKernel: dual-source characterization.** On heterogeneous data, per-factor 1/σ² weighting adds up to +13.2pp peak over L2 (V-MV-KERNEL-HET, 390 cells). Under controlled NR conditions, the advantage scales monotonically from 0.00pp (mathematical identity with L2) to +7.67pp asymptotic at NR=5.0 (UNI-DK-01 v5.3, 1500 cells). Noise ratio alone predicts the peak advantage (r=0.990, 4 healthcare personas). 1890 total cells; curve citable across the NR range.

- **Calibration disclosure — a novel architectural pattern (v7).** DiagonalKernel's accuracy advantage comes with a measured calibration tradeoff: Expected Calibration Error rises from 0.055 at uniform noise to 0.420 at NR=5.0, versus L2's 0.04–0.06 across the same range. This is a fundamental property of inverse-variance weighting — the same mechanism that produces the accuracy gain — addressed architecturally by separating the prediction channel (DK's argmax, accurate) from the estimation channel (DK's confidence values, unreliable). Confidence-sensitive consumers route through rolling verified accuracy (conservation law, auto-pause) or softmax entropy (triage ranking).

- **Two-phase learning with James-Stein shrinkage (v7.3).** Phase 1 estimates centroid means (Order-0 profile state) via Eq. 4b-final; saturates at ~200 decisions per class and transfers across deployments (+28pp). Phase 2 estimates deployment-specific discriminative precision weights (Order-1 profile state) via batch re-estimation; firm-specific and ongoing (+3.2pp at N=500, +5.4pp at N=4000). The deployed scorer coalesces from isotropic (Phase 1) toward weighted (Phase 2) via James-Stein shrinkage: w̃_i = α · w_DK_i + (1−α), provably dominating either extreme for total dimension p ≥ 3 (Stein, 1956; SOC p=144). Fisher-inspired asymmetry motivates Phase 2 persistence: under a Gaussian surrogate, precision parameters remain informative after means stabilize (Layer A); empirically, the deployed estimator exhibits the same pattern at 18/18 checkpoints (Layer B). The compounding claim is batch-level: individual decisions add information; batches are the unit of deployed improvement.

- **Defense in depth — three-layer safety architecture (v7.3).** James-Stein shrinkage (mathematical guardrail: interpolated scorer never below centroid baseline in 0/21 observed checkpoints at α=0.5) + promotion gate (operational guardrail: no batch of DK weights deploys without holdout non-inferiority) + instant rollback to any prior promoted state. No single mechanism is sufficient; the combination provides mathematical, operational, and recovery layers.

- **Asymmetric learning with principled derivation and conservation guarantee.** η_override = 0.01 (5× attenuation) prevents 13–27pp centroid degradation. The ratio is derived from worst-case analyst quality: η_override = η_confirm · (2q̄_worst − 1) with q̄_worst = 0.60 from 24-persona stress testing — validated by the April 16, 2026 four-judge math poll (GPT-4.1 / Claude Opus 4.7 / Grok 3 / Gemini 1.5 Pro). A conservation law α·q·V ≥ θ_min (α = cumulative category coverage; θ_min = 23.53/(α·V), an empirically calibrated cold-start interlock that tightens from ≈0.357 to ≈0.118 as coverage matures) ensures the two-level learning system compounds rather than conflicts, with q = rolling verified accuracy over the last 400 decisions (SE 3.6pp at n≈100 verified samples).

- **Re-Convergence Theorem (new contribution).** γ = N_half,1 / N_half,2 > 1 if and only if ε_firm > ε_firm★ ≈ 0.125, for category-sparse disruption with warm-started centroids. Four structural proof paths confirmed across two four-judge math polls (April 8 and April 16, 2026): (1) geometric, (2) dimensional, (3) η₋ trap avoidance, (4) centroid-distance (v7 addition; Grok 3 primary). Binary simulation confirmed both directions (ε_sim = 0.05: γ = 0.714 < 1; ε_sim = 0.20: γ = 1.033 > 1). Conditions hold in every deployment studied (ε_firm ∈ [0.15, 0.40]).

- **Judgment memory — a fourth cognitive architecture type.** The centroid geometry, per-factor σ (noise fingerprint), conservation law, and AgentEvolver rule generation constitute a memory type not addressed by the CoALA framework [38] or its implementations [39-41]: judgment memory stores verified decision quality decomposed by factor, compounds with use, and produces safety proofs (conservation law) that no combination of episodic, semantic, or procedural memory can derive. Signal-confidence inversion — where the factor with highest practitioner confidence has the highest outcome-conditioned variance — is detectable only through this memory type.

| **Finding** | **Number** | **Condition** | **Experiment** |
| --- | --- | --- | --- |
| Kernel gap | +36.89pp (61.0% → 97.89%) | Identical data, identical profiles | EXP-C1 |
| Zero-learning accuracy | 97.89% | Expert profiles, no training data | EXP-C1 |
| Frozen scorer (A=4) | 90.6% | Expert prior, realistic factors | SHIFT-2 + A=4 |
| Discovery performance | 111× above random | Cross-graph entity relationships | EXP-2 |
| Scaling exponent | b = 2.11 (CI [2.09, 2.14]) | 11-point log-log fit, n = 2–15 | V1A |
| Calibration (L2) | ECE = 0.036 at τ = 0.1 | Confidence ≈ accuracy | V3B |
| Calibration (DK, v7) | ECE 0.055 → 0.420 across NR=1→5 | Mean-σ=0.175; L2 stays 0.04–0.06 | UNI-DK-01 v5.3 |
| Noise robustness | 0.2pp drop at 30% oracle error | Tolerates noisy feedback | EXP-B1 |
| Realistic deployment | 71.7% → 78.9% | 50-seed, noisy factors, 1K decisions | V3A |
| DiagonalKernel (SOC peak) | +13.2pp over L2 | Heterogeneous noise | V-MV-KERNEL-HET |
| DiagonalKernel (S2P) | +6.8pp over L2 | Heterogeneous noise | V-MV-KERNEL-HET |
| DiagonalKernel characterized (v7) | 0.00 → +7.67pp asymptotic | NR=1→5, mean-σ=0.175, 1500 cells | UNI-DK-01 v5.3 |
| Healthcare learning rescued | +3.7pp Diag vs −7.4pp L2 | σ≈0.22, 4 personas | V-HC-CONFIG |
| Healthcare reproduction (v7) | +8.86pp at full HC noise | σ 0.07–0.35, NR=5.0, 50 seeds | MR-COLAB-01 |
| Noise ratio → advantage | r=0.990 | 4 healthcare personas (HC); r=0.991 on v5.3 | HC-scaling + v5.3 |
| Asymmetric η prevents degradation | 13–27pp saved | q̄=0.60–0.70 analyst quality | B5B-PROXY |
| η_override derivation (v7) | η_confirm · (2q̄_worst − 1) = 0.01 | q̄_worst = 0.60 | Four-judge, Apr 16 |
| Conservation law | θ_min = 23.53/(α·V); α = category coverage | 0.357 (cold start, α=0.33) → 0.118 (steady, α=1.0), V=200 | Three-judge validated (form) |
| Conservation q (v7 operational) | Rolling verified accuracy / 400 decisions | SE ≈ 3.6pp | SOC-Q1 closure Apr 19 |
| KernelSelector validation (v7) | 100% correct across 1890 cells | Rule-based: NR > 1.5 → DK | UNI-DK-01 v5.3 + V-MV-KERNEL |
| Off-diagonal correlations | <1pp | Both SOC and S2P | V-HC-SHRINKAGE |
| Re-convergence theorem (v7) | γ > 1 ⇔ ε_firm > 0.125 | Four structural proof paths | Four-judge × 2 polls |
| Referral rules | 72.7% DR, 12% FPR | Policy-based VETO | EXP-REFER-LAYERED |
| Graph enrichment σ reduction | 23–46% (threat_intel, data_sensitivity) | Healthcare SOC, 90-day enrichment | V-CGA-FROZEN v3 |
| Graph enrichment accuracy gain | +5.0pp Day-1 accuracy | DK reweighting, independent of convergence | V-CGA-FROZEN v3 |
| Phase 1 transfer (v7.3) | +28pp cross-deployment | Centroid means transferable | Framework v4 K19 |
| Phase 2 improvement (v7.3) | +3.2pp (N=500) → +5.4pp (N=4000) | DK weights, firm-specific, ongoing | Framework v4 |
| Shrinkage safety (v7.3) | 0/21 below baseline at α=0.5 | 3/21 at α=1.0 (no shrinkage) | Framework v4 RATE-9 |

*Table: Key results. All experiments use synthetic data except FX-1-PROXY-REAL (2,430 real IOC records). v7 adds UNI-DK-01 v5.3 characterization, MR-COLAB-01 reproduction, DK calibration characterization, η_override derivation, q operational definition, and the fourth γ-theorem proof path.*

# **2. Background**

## **2.1 Attention and Kernels**

Scaled dot-product attention [Vaswani et al., 2017]:

Attention(Q, K, V) = softmax(Q · K^T / √d_k) · V        [Eq. 1]

More generally, attention with kernel K: Attention_K(Q, K, V) = softmax(K(Q, K) / τ) · V. When K(q, k) = q · k^T, we recover Eq. 1. Other kernels serve different geometric purposes:

| **Kernel** | **K(q, k)** | **Measures** | **Appropriate When** |
| --- | --- | --- | --- |
| Dot product | q · k^T | Directional alignment | Learned embeddings with training guarantee |
| L2 (RBF) | −‖q − k‖² | Proximity | Bounded features; pre-computed scores |
| Cosine | cos(q, k) | Angular similarity | Pre-normalized features |
| Mahalanobis | −(q−k)^T Σ^−1 (q−k) | Scaled proximity | Mixed-scale features |
| Diagonal (1/σ²) | −(q−k)ᵀ diag(1/σ²) (q−k) | Noise-weighted proximity | Heterogeneous per-factor noise; unequal reliability |

DiagonalKernel is the diagonal of the Mahalanobis matrix — capturing per-factor noise weighting without off-diagonal correlation terms. Empirically, off-diagonal adds <1pp in both tested domains (SOC and S2P), making DiagonalKernel the optimal trade-off between expressiveness and estimation cost.

[EQUATION GRAPHIC 1 | p1_eqb_attention_mechanisms.png | Blog reuse | Four boxed equations (Eq. 1 scaled dot product, Eq. 2 cosine, Eq. 3 general kernel form, DiagonalKernel) with section labels showing the progression from Vaswani through our kernel formulation. | §2.1 | Reusable from CGA Math blog §2]

## **2.2 Why the Kernel Matters on Bounded Features**

If device_trust has mean 0.85 across all samples, then for any weight vector W, the dot product contribution from device_trust is approximately 0.85 × W_device ≈ constant — regardless of the correct action. High-mean factors dominate the dot product and suppress the discriminative signal from lower-mean factors. This is magnitude confounding.

L2 distance does not have this problem. If device_trust is consistently 0.85–0.92, the L2 contribution (0.85 − μ_device)² is near zero for centroids calibrated to the actual distribution. Deviations from the centroid — not absolute magnitudes — drive the distance.

On our data, this distinction costs 36.89 percentage points (§5.2). Magnitude confounding is not academic — a SOC processing 10,000 alerts per month at 61% versus 98% misroutes 3,700 additional alerts. At $45 per analyst-minute and 15 minutes per misrouted alert, the kernel choice alone is worth $2.5M per year in analyst productivity.

## **2.3 Notation**

v7 introduces operational definitions for three previously under-specified symbols: η_override derived from worst-case analyst quality; q(t) as rolling verified accuracy; θ_min as a self-calibrating deployment-specific floor. Full derivations in §3.1. Table below summarizes v7 notation conventions.

| **Symbol** | **Shape** | **Meaning** |
| --- | --- | --- |
| f | 1 × d | Factor vector for one alert (d = 6 for SOC) |
| μ | n_c × n_a × d | Profile centroid tensor |
| c | scalar | Category index |
| n_c, n_a, d | scalars | Number of categories, actions, factors |
| τ | scalar | Temperature parameter (τ = 0.1) |
| E_i | m_i × d | Entity embedding matrix for domain i |
| V_j | m_j × d_v | Value matrix for domain j |
| n | scalar | Number of knowledge domains |
| η_confirm | scalar | Confirm-path learning rate (0.05, clean signal) |
| η_override | scalar | Override-path rate (0.01; = η_confirm · (2q̄_worst − 1), q̄_worst = 0.60) |
| W | d × d (diagonal) | Kernel weight matrix. W = diag(1/σ²). Identity → L2. Uses max-normalized form W/W.max() in the centroid gradient. |
| noise_ratio | scalar | max(σ_factor)/min(σ_factor). > 1.5 → DiagonalKernel at Day 1. |
| θ_min | scalar | Conservation floor, deployment-specific: θ_min = 23.53/(α·V), α = category coverage. Empirically calibrated (not first-principles); ranges 0.357 (cold start) → 0.118 (steady state) at V=200. Cold-start interlock, non-binding in steady state. |
| α(t) | scalar | Conservation-law coverage: cumulative category coverage = c_d/C (fraction of categories with ≥1 verified decision to date; monotone). NOT override rate. Distinct from α_disrupt (re-convergence). |
| override_rate | scalar | Overridden / verified ≈ 1−q. Feeds a complacency advisory only; not part of the conservation gate. |
| q(t) | scalar | Rolling verified accuracy over last 400 decisions (≈100 verified samples at 25% verify rate; SE ≈ 3.6pp). Kernel-independent quality signal. |
| I(n, t) | scalar | Institutional intelligence function |
| ε_firm | scalar | Firm-specific initial mismatch ‖μ_0 − GT_1‖. Theorem holds for ε_firm > 0.125; production range [0.15, 0.40]. |
| γ | scalar | Re-convergence speed ratio N_half,1 / N_half,2. γ > 1 proven for category-sparse disruption. |

# **3. Method: Three-Level Framework**

## **3.1 Level 1: Profile Scoring as Distance-Kernel Attention**

### **The Published Equation (Falsified)**

The original system used dot-product scoring. This equation was falsified by the experimental program. Six interventions targeting the gating mechanism produced a combined +0.01pp improvement. The single intervention that replaced the kernel (dot product → L2 distance) produced +36.89pp.

[EQUATION GRAPHIC 2 | p1_eqa_published_equation.png | Blog reuse | The falsified published equation: dot-product scoring at 49% accuracy, with a red "FALSIFIED" overlay and the +36.89pp correction arrow pointing to Eq. 4-final. | §3.1 | Reusable from CGA Math blog §3.1]

### **The Corrected Formulation**

Given an alert with factor vector f ∈ [0,1]^d (d = 6 for SOC), category c from a situation classifier, and profile centroid tensor μ ∈ ℝ^{n_c × n_a × d}:

P(a | f, c) = softmax(−‖f − μ[c,a,:]‖² / τ)        [Eq. 4-final]

where τ = 0.1 (validated, ECE = 0.036 on L2). The factor vector f is the query; profile centroids μ[c,:,:] are the keys; category routing c is hard-gated MoE selection [Jacobs et al., 1991]; and the softmax produces a probability distribution over n_a actions.

[EQUATION GRAPHIC 3 | eqa_level1_hero.png | Blog reuse | Eq. 4-final as hero equation with f / μ / τ labels and colored section boxes showing distance → softmax → probability. | §3.1 | Reusable from CGA Math blog §3.1]

[FIGURE 2 | eq_profilescorer.png | NBP | Level 1 Scoring Pipeline. Alert → Category Router → ProfileScorer (Eq. 4-final) → Score → Action → Outcome → Centroid Update (Eq. 4b-final) → feedback loop. v7 optional update: add DiagonalKernel branch + "rule-based KernelSelector Day 1" label. | §3.1 | Reusable from paper_figures; optional update]

### **Why L2 Fixes Everything: A Concrete Example**

Consider a SOC alert with f = [0.95, 0.30, 0.10, 0.70, 0.90, 0.85] (travel_match, asset_criticality, threat_intel, time_anomaly, device_trust, pattern_history). The false_positive_close centroid for credential_access is μ = [0.90, 0.12, 0.08, 0.35, 0.88, 0.82]. Under dot product, device_trust dominates (0.90 × 0.88 = 0.792) despite carrying almost no discriminative information. Under L2, device_trust contributes (0.90 − 0.88)² = 0.0004 (near zero) while asset_criticality contributes (0.30 − 0.12)² = 0.0324 — 80× more, correctly weighted by discriminative deviation. Total L2 distance 0.1591 (nearest); P(false_positive_close) = 0.938.

### **DiagonalKernel: When Factor Noise Is Heterogeneous**

L2 fixes magnitude confounding but treats all factors equally. In every real deployment, factor noise is heterogeneous: device_trust might have σ=0.28 (noisy MDM data) while threat_intel has σ=0.07 (clean CISA KEV feeds). The DiagonalKernel equation:

K(f, μ) = (f − μ)ᵀ W (f − μ) = Σ_j (1/σ_j²) · (f_j − μ_j)²        [Eq. 4-dk]

When W = I or σ is uniform: reduces to L2 (mathematical identity, confirmed at NR=1.0 across 150 cells of UNI-DK-01 v5.3). When σ varies per factor: down-weights noisy dimensions, up-weights clean ones.

**Discriminative metric learning (v7.3 positioning).** DiagonalKernel's weights are estimated by coordinate descent to maximize classification accuracy — a form of discriminative metric learning restricted to the diagonal of the Mahalanobis matrix (cf. Xing et al., 2003; Weinberger & Saul, 2009). The diagonal constraint makes weights interpretable (each weight = one factor's importance) and estimation tractable (d parameters, not d²). Under a Gaussian class-conditional surrogate, w_j = 1/σ_j² (inverse variance). In the deployed scorer, the weights are discriminative precision weights — the surrogate provides the scoring FORM; the estimator provides the UTILITY.

**Kernel selection rule (v7 architecture).** Kernel selection is determined at deployment qualification time by the noise_ratio measured from the customer's initial alert stream: noise_ratio = max(σ_per_factor) / min(σ_per_factor). If noise_ratio > 1.5 → DiagonalKernel, else L2. This rule is applied at Day 1 and does not evolve with accumulated decisions. Shadow comparison of the alternative kernel runs in the background for monitoring but does not drive selection — a correction motivated by UNI-DK-01 v5.3 experiments E1/E3/E4, which showed that data-driven selection via mean confidence, agreement rate, or log-likelihood is unreliable because DiagonalKernel's sharpened probability distributions produce lower mean confidence even when accuracy is higher. This sharpening mechanism — the same one responsible for the accuracy gain — defeats confidence-based comparison metrics (see Accuracy-Calibration Tradeoff below). Validated at 100% across 1890 cells in UNI-DK-01 v5.3 (269 informative across NR ∈ {1.5, 2.0, 3.0, 5.0}) and 4/4 personas in V-MV-KERNEL-HET; per-NR breakdown in Appendix A.

**DiagonalKernel advantage — curve-based characterization (v7).** Two independent experiments jointly characterize the DiagonalKernel surface. V-MV-KERNEL-HET (390 cells, σ_level=0.30 mean, heterogeneous profiles) established the peak: +13.2pp on SOC, +6.8pp on S2P. UNI-DK-01 v5.3 (1500 cells, mean-σ=0.175 fixed, controlled NR sweep) characterized the scaling curve: asymptotic gap of 0.00pp at NR=1.0 grows monotonically to +0.72pp (NR=1.5), +1.99pp (NR=2.0), +4.43pp (NR=3.0), and +7.67pp (NR=5.0). Cold-start scoring-geometry contribution dominates at every NR (54.5%–75.5% of total gap, peak 75.5% at NR=2.0). All four pre-registered D-checks PASS (monotonicity; NR=5 ≥ 5pp; cold-start fraction ≥ 50%; q̄-SD ≤ 1pp). See Figure 4.

The two experiments together span 1890 cells. +13.2pp is the peak on heterogeneous data where individual factors can have σ as high as 0.45; +7.67pp is the asymptotic under controlled mean-σ=0.175. Neither supersedes the other — they characterize different points on the surface. The curve is citable across the NR range.

**Scale of effect.** At the SOC canonical volume of 10,000 alerts/month (§2.2), the +7.67pp asymptotic prevents approximately 770 misrouted alerts per month relative to L2; at $45 per analyst-minute × 15 minutes per misrouted alert, the DiagonalKernel weighting alone is worth approximately $520K/year. Combined with the L2-vs-dot-product kernel choice ($2.5M/year), the full distance-kernel + inverse-variance architecture delivers roughly $3M/year at this scale.

[FIGURE 3 | nbp_kernel_progression_extended.png | Chart | Kernel Progression: 5-bar chart Dot(61.0%) / Cosine(96.4%) / L2(97.9%) / L2_heterogeneous / DiagonalKernel_heterogeneous; arrows annotating +36.89pp (EXP-C1) and +13.2pp (V-MV-KERNEL-HET peak). v7 footnote: +7.67pp characterized at NR=5.0. | §3.1 | Reusable from arxiv v4 paper_figures]

[FIGURE 4 | unidk_v53_characterization_surface.png | Chart | **NEW v7.** Monotone gap curve: asymptotic DK advantage (pp) vs NR. 5 data points NR=1.0/1.5/2.0/3.0/5.0. Optional dual-y overlay showing cold-start % (75.5% → 54.5%). 1500 cells, mean-σ=0.175. UNI-DK-01 v5.3 closure April 19, 2026. | §3.1 | New graphic required]

[FIGURE 5 | nbp_diagonal_heatmap.png | Chart | 390-cell factorial heatmap: DK advantage over L2 as function of noise_ratio (x) and σ_level (y). r = 0.991. SHARED with Production Paper v9.1 Fig 2. | §3.1 | Reusable — existing paper_figures]

[FIGURE 6 | nbp_healthcare_rescue.png | Chart | Healthcare rescue: side-by-side time-series of L2 (degrades 71.3%→63.9%, −7.4pp) vs DiagonalKernel (71.3%→73.9%, +3.7pp V-HC-CONFIG floor; MR-COLAB-01 adds +8.86pp at full profile). v7 annotation: add MR-COLAB-01 floor-to-peak label. | §3.1 | Existing paper_figures; needs v7 annotation update]

### **Accuracy-Calibration Tradeoff (v7 subsection)**

DiagonalKernel is more accurate than L2 on heterogeneous noise — up to +13.2pp peak, +7.67pp characterized asymptotic. The same mechanism that produces the accuracy gain produces a second, distinct effect: the predicted probability distribution sharpens. UNI-DK-01 v5.3 characterized the calibration surface (Experiment E2): DK ECE rises monotonically from 0.055 at NR=1.0 to 0.420 at NR=5.0, versus L2's 0.04–0.06 across the same range — a 10.4× ratio at NR=5.0 (see Figure 7). L2 is well-calibrated and mildly improves with NR; DiagonalKernel is severely miscalibrated at high NR and degrades monotonically.

**Mechanism.** At NR=5.0, the per-factor σ profile [0.058, 0.105, 0.152, 0.198, 0.245, 0.292] produces normalized W ≈ [1.00, 0.31, 0.15, 0.09, 0.06, 0.04]. Four of six factors contribute less than 15% of the dominant factor's weight; the effective dimensionality of the scoring space drops from 6 toward ~3. Reduced effective dimensionality sharpens the softmax — predictions concentrate toward 0 or 1 rather than spreading across actions. When DK reports confidence 90% at high NR, actual accuracy is substantially below 90%. This is a fundamental property of inverse-variance weighting: any weighted-distance kernel with concentrated weights exhibits the same pattern. It is *not* an implementation defect.

**Architectural response — prediction vs estimation channels.** DiagonalKernel is a *good prediction channel* (its argmax is more accurate than L2's at NR > 1, up to +7.67pp at NR=5.0 and +13.2pp at V-MV-KERNEL-HET peak) but a *poor estimation channel* (its confidence values are miscalibrated as NR rises). Production consumers route through alternative signals for estimation needs: KernelSelector uses the rule-based decision (not confidence); conservation-law q reads rolling verified accuracy over 400 decisions; AMBER auto-pause triggers on rolling accuracy (state-level); analyst triage ranking uses softmax entropy or top-two probability gap (kernel-independent); per-decision auto-approve gates use raw max_p with category-specific thresholds calibrated on L2 (re-calibration under DK routing is a first-customer PROD-4b exercise); downstream ML ensembles needing calibrated soft probabilities apply Platt scaling on their own holdout (not supplied at v7).

Customer-facing accuracy claims are unaffected: +13.2pp peak and +7.67pp characterized are both argmax accuracy measurements, not confidence values. No customer-facing claim cites raw DK confidence. The honest framing: DK is a stronger prediction channel than L2, and the architecture understands that confidence from a weighted-distance kernel is an estimate to be consumed carefully, not a probability to be quoted directly.

**Generalization.** Any enterprise system deploying inverse-variance-weighted distance scoring on bounded features — and by implication, any system with strong correlation between feature reliability and feature weight — inherits this tradeoff. Deployments should measure ECE as a function of noise ratio before claiming calibrated confidence, and downstream consumers sensitive to confidence values should route through kernel-independent signals. We return to this architectural pattern in §7.

[FIGURE 7 | unidk_v53_ece_surface.png | Chart | **NEW v7.** ECE vs NR line chart — two lines (L2 flat 0.04–0.06; DK rises 0.055 → 0.420). 5 data points per line. Shaded annotation showing "prediction channel OK (argmax)" vs "estimation channel routes via rolling accuracy". | §3.1 | New graphic required]

### **Noise Ceiling and Deployment Zones**

Noise ceiling is kernel-dependent:

| **Kernel** | **GREEN** | **AMBER** | **RED** |
| --- | --- | --- | --- |
| L2 | σ_mean ≤ 0.105 | 0.105 < σ ≤ 0.157 | σ > 0.157 |
| DiagonalKernel | σ_mean ≤ 0.157 | 0.157 < σ ≤ 0.25 | σ > 0.25 |

Healthcare deployments (σ≈0.22) move from RED (L2, frozen scorer only) to AMBER (DiagonalKernel, learning with monitoring). The GREEN zone nearly doubles.

### **Kernel Compounding**

The distance metric itself improves as deployment matures. Day 1: kernel selected by rule from measured σ profile. Day 30+: centroid tensor calibrated from verified analyst decisions. W = diag(1/σ²) is firm-specific — a competitor who copies the code starts with W = I. This is a second form of compiled knowledge alongside the centroid tensor: μ encodes WHAT the firm learned; W encodes WHICH DATA TO TRUST.

A third compiled knowledge form emerges from P28 deployment qualification: Empirical Bayes bootstrap uses the measured σ profile to recompute the bootstrap prior μ₀ from enriched f-vectors, placing initial centroids closer to the operational optimum before analyst learning begins. V-CGA-FROZEN v7 + V-BOOTSTRAP-W (N=200/arm): enriched bootstrap reduces calibration time by ~11% (d=0.212, p=0.003, CI=[+2.87,+13.93] decisions) and improves Day-1 accuracy by +2.5pp.

[FIGURE 8 | fc04_decision_clock_weight_evolution.png | NBP | Decision Clock: weight evolution from Day 1 (uniform/heuristic W) to Day 30 (calibrated to firm-specific risk profile). Concrete example: travel_match weight 0.3 → 0.92 and pattern_history 0.4 → 0.95 for this firm's false_positive_close centroid after 340+ verified outcomes. | §3.1 Kernel Compounding | Reusable from CGA Math blog Graphic FC-04]

### **Online Learning**

Centroid refinement from verified outcomes (Eq. 4b-final):

CONFIRM: G ← (W / W.max()) · (f − μ[c, a_pred, :]); μ[c, a_pred, :] += η_confirm_eff · G

OVERRIDE: push μ[c, a_pred, :] away; pull μ[c, a_gt, :] toward f (kernel-aware, same (W/W.max())·(f−μ) form)

μ[c, a, :] ← clip(μ[c, a, :], 0.0, 1.0)        [Eq. 4c-final, mandatory]

where η_confirm = 0.05, η_override = 0.01, and η_eff = η / (1 + n[c,a] · decay_rate). The gradient uses max-normalized form W / W.max() for numerical stability; per-factor effective learning rate is η · w_j / w_max. Clipping is mandatory — without it, centroids escape [0,1]^d within 6–12 decisions (V2: 4,608× magnitude).

**The P0 fix — derivation of asymmetric learning rates (v7).** A 9-persona LLM-judge stress test (B5B-PROXY) found 13–27pp centroid degradation from realistic analyst override quality (q̄ = 0.60–0.70). The ratio is derived from worst-case analyst quality:

η_override = η_confirm · (2q̄_worst − 1)        [Eq. 4d, v7 derivation]

At q̄_worst = 0.60: η_override = 0.05 · 0.20 = 0.01 — the 5× attenuation observed empirically. The derivation transforms the ratio from "empirically chosen" to "information-theoretically grounded" — the override update rate is calibrated to the worst-case signal-to-noise ratio of the override channel. The April 16, 2026 four-judge math poll (GPT-4.1 / Claude Opus 4.7 / Grok 3 / Gemini 1.5 Pro) confirmed the derivation. Validated across 24 deployment personas.

**Conservation law (v7 operational definition).** The conservation invariant is:

α(t) · q(t) · V(t) ≥ θ_min        [Eq. CL]

where **α(t) is cumulative category coverage = c_d/C** — the fraction of the C alert categories with at least one verified decision to date (cumulative and monotone; a category does not lose coverage). V is verified decisions per day, and q is rolling verified accuracy over the last 400 decisions (~100 verified samples at 25% verify rate; SE ≈ 3.6pp). (α here is category coverage, *not* analyst override rate: under an override-rate reading α ≈ 1−q, which would make α·q·V ∝ q(1−q) and perversely penalize accuracy improvement. The override rate is retained only as a separate complacency advisory.) θ_min = 23.53 / (α · V) is an empirically calibrated, deployment-specific floor — the constant 23.53 was tuned from the half-convergence volume N_half ≈ 14, not derived from first principles.

Because coverage grows over the deployment lifecycle, the floor tightens as the system matures rather than resting on a single fixed threshold:

| Stage | c_d | α = c_d/C | θ_min (V=200) | α·q·V (q=0.85) |
|---|---|---|---|---|
| Cold start | 2 | 0.33 | 0.357 | 56.1 |
| Steady state | 6 | 1.00 | 0.118 | 170.0 |

The absolute floor θ_min therefore functions as a **cold-start interlock**; once coverage and volume mature, the product sits orders of magnitude above θ_min, and the binding protector is the **relative trigger** — AMBER auto-pause when α·q·V falls below 0.7× its rolling baseline. The 400-decision window applies to q, which is a windowed estimate of current quality; α is structural coverage, not a windowed estimate, and therefore carries no window. (The SOC-Q1 adjudication of April 19, 2026 resolved the q operational definition — 400-decision rolling accuracy — which stands. That adjudication's accompanying α windowing is superseded here: α is now cumulative category coverage, a structural quantity, not a responsive 50-decision override estimate.)

Operationalizing q as rolling verified accuracy (rather than per-decision confidence) decouples the conservation signal from the DiagonalKernel calibration properties above. When DK is selected, the conservation law continues to read accurate quality signal without passing through DK's miscalibrated confidence output. AMBER auto-pause freezes learning when the invariant is breached — a state-level trigger using the same rolling accuracy signal.

**Signal-confidence inversion.** An empirical finding from the SOC deployment: the factor that analysts report highest confidence in (device_trust, mean confidence 4.2/5 in analyst surveys) has the highest outcome-conditioned variance (σ=0.28, weight 6% in the asymmetric-learning-rate-weighted fingerprint). Conversely, threat_intel — which analysts rate as routine and low-effort — has σ=0.07 (weight 100%). This inversion is structurally invisible to systems that store decision history (episodic memory) or domain knowledge (semantic memory), because it requires computing per-factor σ from verified outcomes across hundreds of decisions — a computation that only the centroid geometry and inverse-variance weighting produce. Consistent patterns appear in calibrated synthetic deployments across three additional domains (trading: conviction σ=0.28/weight 12% vs research σ=0.06/weight 95%; purchasing: weather σ=0.26/weight 14% vs waste_history σ=0.08/weight 92%; data engineering: recurrence σ=0.235/weight 52% vs freshness σ=0.170/weight 100%). Universal validation requires production-verified decision data from each domain (EXP-G1 priority).

Two independent LLM-judge panels have validated this line of reasoning. A three-judge panel (GPT-4o / Claude Opus / Gemini, March 2026) validated the original conservation-law formulation. Two four-judge math polls (GPT-4.1 / Claude Opus 4.7 / Grok 3 / Gemini 1.5 Pro, April 8 and April 16, 2026) validated the Re-Convergence Theorem (§4.6) and the η_override derivation respectively. The v7 operational definition of q preserves all conservation-law guarantees (Banerji 2026c, §5).

[FIGURE 9 | nbp_asymmetric_eta.png | Chart | Asymmetric η trajectories: overlayed time series of centroid distance under symmetric η vs asymmetric η_override=0.01, 13–27pp degradation prevented. v7 annotation: add "η_override = η_confirm · (2q̄_worst − 1) = 0.01 (derived, four-judge Apr 16 2026)". SHARED with Production Paper v9.1 Fig 5. | §3.1 | Existing paper_figures; needs v7 annotation]

[FIGURE 10 | nbp_conservation_timeline.png | NBP | Conservation law timeline: α·q·V signal over 180 days with GREEN/AMBER zones, θ_min floor line (lifecycle-dependent: 0.357 cold start → 0.118 steady), and AMBER auto-pause event annotation. v7.6 annotation: "α = cumulative category coverage; q = rolling verified accuracy over 400 decisions. Steady-state protector is the 0.7×-baseline relative trigger; θ_min is the cold-start interlock." SHARED with Production Paper v9.1 Fig 6. | §3.1 | Existing; needs v7.6 annotation]

### **Two-Phase Learning Architecture (v7.3)**

The centroid update rule (Eq. 4b-final) and the DiagonalKernel weighting (Eq. 4-dk) operate on different aspects of the scoring model and have different learning dynamics. We formalize this as two-phase learning.

**Phase 1 (Mean Convergence).** Eq. 4b-final estimates centroid means μ[c,a,:] — the location of each class prototype. Phase 1 saturates at approximately 200 verified decisions per (c,a) pair, after which label-noise contamination biases the estimate. Centroids transfer across deployments (+28pp, K19) because the location of risk patterns is largely shared across firms within a domain. Phase 1 is the existing v6.0 learning architecture.

**Phase 2 (Discriminative Metric Learning).** After Phase 1 saturates, means are frozen and verified decisions buffer for periodic batch re-estimation of DK precision weights. These weights are discriminative — estimated by coordinate descent to maximize classification accuracy within the diagonal-kernel family, not by maximum likelihood under a Gaussian model. DK weights are deployment-specific and do NOT transfer across firms (−5.6pp on cross-deployment, K19) — they encode which dimensions of risk matter for THIS firm's decisions.

**James-Stein shrinkage.** The deployed scorer interpolates between Phase 1 (isotropic, all dimensions equal) and Phase 2 (discriminative, concentrated on reliable dimensions):

w̃_i = α · w_DK_i + (1 − α)        [Eq. SHRINKAGE]

At α=0: pure centroid scoring (Phase 1). At α=0.5 (default): midpoint interpolation. At α=1: full discriminative weighting. For total dimension p ≥ 3 (SOC: p=144), the interpolated estimator dominates either extreme (Stein, 1956; James & Stein, 1961). Empirically, the shrinkage scorer at α=0.5 never fell below the centroid-only baseline in 0/21 observed checkpoints; at α=1.0 (no shrinkage): 3/21 fell below.

**Batch pipeline.** Phase 2 improvements deploy through a seven-step gated pipeline: decisions accumulate → novelty triggers re-estimation → composition check verifies batch quality → estimator runs → promotion gate validates against holdout (accuracy within 1pp, no category degrades) → deploy or reject → history enables rollback. The promotion gate is the operational guardrail that catches edge cases shrinkage misses. Together with shrinkage (mathematical guardrail) and rollback (recovery), this constitutes defense in depth — three layers of safety.

**Fisher-inspired asymmetry.** Why does Phase 2 persist after Phase 1 saturates? Under a Gaussian class-conditional surrogate, the Fisher information for precision parameters (1/σ²) depends on the fourth moment, which remains informative after means (second moment) stabilize. This motivates (Layer A) why second-order metric structure is learnable. Empirically (Layer B), the Fisher-alignment metric ρ_variance ≈ +0.35 at all 18 observed checkpoints confirms the deployed estimator captures the same structure the surrogate predicts. Fisher is motivation, not proof — the deployed estimator uses coordinate descent, not MLE — but the empirical alignment justifies the two-phase architecture.

**The compounding claim (formal).** "The accumulation of novel verified decisions improves the GAE's scoring quality, realized at each promoted re-estimation." This is batch-level: individual decisions add information; batches are the unit of deployed improvement. The switching cost deepens with every promoted batch — Phase 2 weights are firm-specific and non-transferable.

### **Calibration and Two Accuracy Regimes**

For the L2 kernel at τ = 0.25 (previous default): ECE = 0.190. At τ = 0.1: ECE = 0.036 — competitive with post-hoc temperature scaling [Guo et al., 2017] while requiring no calibration data (V3B). These numbers refer to L2 specifically; DiagonalKernel calibration is characterized separately above.

Two accuracy regimes: centroidal synthetic (perfect factor computation, ground-truth-aligned centroids: 97.89%) and deployment-representative realistic (noisy factors, imperfect routing, 50-seed simulation: 71.7% → 78.9% over 1,000 decisions). The gap is the deployment noise floor.

---

## **3.2 Level 2: Cross-Graph Discovery as Cross-Attention**

For each knowledge domain G_i, define an entity embedding matrix E_i ∈ ℝ^{m_i × d} [Eq. 5]. For source domain G_i and target domain G_j:

[EQUATION GRAPHIC 4 | eq6_cross_attention.png | NEW v7 | Eq. 6: CrossAttention(G_i, G_j) = softmax(E_i · E_j^T / √d) · V_j — hero equation with three boxed sections "Query E_i" (blue), "Key E_j" (green), "Value V_j" (purple); subtitle "exact instance of Eq. 1". | §3.2 | New or reuse Blog Part 1 rendering]

This is an exact instance of Eq. 1. E_i are queries, E_j are keys, V_j are values. Normalization is a structural prerequisite: without z-score + L2 normalization, cross-attention finds nothing (0× above random). With both: 111× above random (EXP-2). After discovery sweeps:

[EQUATION GRAPHIC 5 | eq12_residual_enrichment.png | Blog reuse | Eq. 12: E_i^{enriched} = Normalize(E_i + Σ_{j≠i} CrossAttention(G_i, G_j)) — rendered with explicit "residual (+)" annotation and "Normalize" gate boxed; caption "additive enrichment; original E_i preserved." | §3.2 | Reusable from Blog Part 1]

[FIGURE 11 | eq_singapore.png | NBP | The Singapore Discovery. A threat intelligence feed reports a campaign targeting Singapore authentication servers. Cross-attention discovers the connection to an 8-month auto-close pattern — the canonical worked example of cross-graph discovery. | §3.2 | Reusable from CGA Math blog CI-04]

## **3.3 Level 3: Multi-Domain Attention**

For n knowledge domains, multi-domain attention processes all domain pairs:

[EQUATION GRAPHIC 6 | eq8_multi_domain.png | NEW v7 | Eq. 8: MultiDomainAttention(G) = Aggregate({head_{i,j}}), with head_{i,j} = CrossAttention(G_i, G_j) for all i < j — two-line typeset equation; subtitle "n(n−1)/2 heads". | §3.3 | New; small equation graphic]

[EQUATION GRAPHIC 7 | eq10_combinatorial.png | NEW v7 | Eq. 10: Total = [n(n−1)/2] × m² — with annotation "15 heads at n=6, 21 at n=7". | §3.3 | New; may combine with Figure 12]

Each new domain adds n−1 new discovery categories. With 6 domains, 15 heads evaluate 3.75M pairwise scores per sweep, completing in under 2 seconds on commodity hardware.

[FIGURE 12 | eq_combinatorial.png | NBP | Combinatorial Growth: n=2 (1 pair), n=4 (6 pairs), n=6 (15 pairs) — three panels showing unique pair count growing super-linearly with n. | §3.3 | Reusable from CGA Math blog GM-02]

# **4. Architecture, Scaling, and Correspondence**

## **4.1 Compiled Ontologies**

Profile centroids are compiled from expert knowledge. The statement "for credential_access alerts, a correctly closed false positive typically has high device trust and high pattern history" compiles into:

[EQUATION GRAPHIC 8 | eq_compiled_centroid.png | NEW v7 | Worked centroid vector: μ[credential_access, false_positive_close, :] = [0.90, 0.12, 0.08, 0.35, 0.88, 0.82] with per-index factor-name annotations. Small graphic; can inline as styled code block. | §4.1 | New, optional]

The mathematical engine is domain-agnostic because domain knowledge is compiled into the centroid tensor's geometry. The same equations govern SOC alert triage, procurement approval, and financial compliance — only the centroid values change.

DiagonalKernel adds a second form of compiled knowledge: discriminative precision weights. A healthcare deployment compiles device_trust weight = 0.04 (noisy) and threat_intel weight = 1.0 (reliable). The centroid encodes WHAT the firm learned (Phase 1, transferable). The kernel weights encode WHICH DATA TO TRUST (Phase 2, firm-specific). Both are readable, auditable, and compound — and the Phase 2 weights deepen the switching cost with every promoted batch because they are deployment-specific and do not transfer.

[FIGURE 13 | cga_levels_stack.png | NBP | **Five CGA Levels** (v7.1 rename, formerly "Five Layers"): the three mathematical levels (Level 1 ProfileScorer, Level 2 Cross-Graph Discovery, Level 3 Multi-Domain Attention) stacked above two substrate layers (UCL context substrate, FactorComputers). Caption: "Distinct from the production 4-layer architecture — UCL, Agent Engineering, ACCP, Domain Copilots — in Banerji 2026c Fig 1; the math paper's five-level decomposition groups substrate + math layers, while the production paper's four-layer decomposition groups orchestration concerns." | §4.1 | Reusable from CGA Math blog with updated caption]

## **4.2 Properties from Attention Theory**

Three structural properties transfer from transformer attention:

**Quadratic interaction space.** Discovery capacity scales as n(n−1)/2 domain pairs × m² entity interactions per pair. Empirically, D(n) ∝ n^{2.11} (V1A), with the super-quadratic exponent arising from the discovery cascade.

[FIGURE 14 | eq_scaling.png | Chart | Discovery Scaling. Log-log scatter, 11 points (n = 2–15). b = 2.11, CI [2.09, 2.14], R² = 0.9999. Scatter with fitted line and CI band. | §4.2 | Reusable from arxiv v4 paper_figures / V1A]

**Constant path length.** Any entity in domain G_i can discover a relationship with any entity in G_j in one cross-attention sweep. No traversal through intermediate graph nodes is required.

**Residual enrichment.** Cross-graph residual connections (Eq. 12) accumulate discovery information in entity embeddings. Both require normalization to prevent magnitude explosion (V1B confirmed 2.9M× explosion without it).

## **4.3 Temporal Encoding**

The architecture uses four temporal clocks: State (current snapshot), Event (historical timeline with recency weighting), Decision (confidence velocity), and Insight (discovery maturity weighting). The Decision Clock is architecturally novel: two systems at identical confidence levels but opposite velocity profiles are in fundamentally different epistemic states.

## **4.4 Scaling**

[EQUATION GRAPHIC 9 | eq13_moat_equation.png | Blog reuse | Eq. 13: I(n, t) = Σ_i W_i(t) + α · Σ_{i<j} D_{i,j}(n, t, f) + β · R(n, t) — three-term hero equation with Term 1 "within-domain calibration" (blue), Term 2 "cross-domain discoveries" (green), Term 3 "second-order discoveries" (purple). | §4.4 | Reusable from Blog Part 1]

Term 1: weight calibration from verified decisions. Term 2: discoveries from n(n−1)/2 domain pair sweeps. Term 3: discoveries from attending to previous discoveries.

[EQUATION GRAPHIC 10 | eq14_scaling_law.png | NEW v7 | Eq. 14: I(n, t) ~ O(n^{2.11} · t^γ) where γ ∈ [1, 2] — single-line scaling law with "empirical: n^{2.11} (V1A); theoretical: γ ∈ [1,2], EXP-G1 empirical pending" footnote. | §4.4 | New; small equation graphic]

**Reconciling n^{2.11} with the n² theoretical lower bound (v7.1).** Companion papers [Banerji, 2026b, CI 4.0] present institutional intelligence scaling as I(n, t) ~ O(n² · t^γ), reflecting the n(n−1)/2 unique domain pairs that is the theoretical floor. V1A's 11-point empirical measurement produced b = 2.11 — the excess exponent (0.11) arises from cross-discovery amplification captured in the β · R(n, t) term of Eq. 13, where discoveries in one domain pair enrich entity representations used in other pairs and enable additional discoveries. The two framings are consistent: n² is the structural lower bound; n^{2.11} is the empirical measurement including second-order cascade effects. Both are correct at their respective abstraction levels.

## **4.5 The Complete Correspondence**

Table 1. Transformer ↔ Cross-Graph Attention correspondence:

| **Component** | **Transformer** | **Level 1: Scoring** | **Level 2: Discovery** | **Level 3: Multi-Domain** |
| --- | --- | --- | --- | --- |
| Query | Token embed × W^Q | Factor vector f | Domain i embeddings E_i | E_i, per domain pair |
| Key | Token embed × W^K | Profile centroids μ[c,:,:] | Domain j embeddings E_j | E_j, per domain pair |
| Value | Token embed × W^V | Action labels (implicit) | Value vectors V_j | V_j, per domain pair |
| Kernel | Dot product | L2 distance (v7: DiagonalKernel when noise_ratio > 1.5, rule-based Day 1; v7.3: discriminative precision weights via two-phase learning) | Dot product | Dot product |
| Scaling | 1/√d_k | 1/τ, τ = 0.1 | 1/√d | 1/√d |
| Multi-head | h learned projections | n_c categories (MoE) | — | n(n−1)/2 domain pairs |
| Output | Weighted value sum | Argmax over n_a actions (v7: confidence via rolling accuracy / softmax entropy) | Enriched representations | Aggregated discoveries |
| Residual | x + Attention(x) | Centroid pull/push + clip | E_i + CrossAttn + Normalize | Preserved + Normalize |
| Correspondence | — | Partial | Exact (Eq. 6 = Eq. 1) | Structural |

*Table 1: Transformer ↔ CGA correspondence. v7 updates: rule-based kernel selection at Day 1; estimation-channel routing under DiagonalKernel.*

## **4.6 Re-Convergence Theorem**

The architecture's temporal re-convergence property (an operational, time-domain effect, distinct from the information-gain compounding of §4.4) states that after environmental disruption, the system re-converges to operational accuracy faster than it initially calibrated, because accumulated institutional knowledge provides a head start. We provide formal conditions under which this holds.

Let ε_firm = ‖μ_0 − GT_1‖ denote the firm-specific initial mismatch (Phase 1). Let Δ denote the disruption shift applied to c_d of C alert categories (Phase 2). Let **α_disrupt = c_d/C** (the fraction of categories disrupted by a campaign — a re-convergence quantity distinct from the conservation-law α = category coverage; the two are different measurements and must not be conflated). Then:

[EQUATION GRAPHIC 11 | eq_gamma_theorem.png | NEW v7 | Re-Convergence Theorem: γ = N_half,1 / N_half,2 > 1 ⇔ ε_firm > α_disrupt · ‖Δ‖ / (1 − α_disrupt) — theorem box with "iff" centered, numeric callout "ε_firm★ ≈ 0.125 at production values (α_disrupt = 2/6, ‖Δ‖ = 0.25, θ = 0.85)". Production range label: "ε_firm ∈ [0.15, 0.40] — all deployments clear the threshold." | §4.6 | New hero equation graphic]

**Mechanism: the rolling-window shortcut.** In Phase 2, (1 − α_disrupt) ≈ 67% of alert decisions are from undisrupted categories and immediately correct. The effective Phase 2 threshold for disrupted categories is p_d★ = (θ − (1 − α_disrupt)) / α_disrupt ≈ 0.55 — Phase 2 needs disrupted categories to reach only 55% correctness (not 85%) for the rolling operational metric to declare convergence. Phase 1 had no such shortcut.

**Four structural proof paths.** Each targets a different aspect of the mechanism. The first three were established in the April 8, 2026 four-judge math poll (GPT-4.1 / Claude Opus 4.7 / Grok 3 / Gemini 1.5 Pro); the fourth was added in the April 16 poll:

1. **Geometric.** When ε_firm > ε_firm★, Phase 1's initial mismatch exceeds Phase 2's effective challenge by construction.

2. **Dimensional.** Phase 2 reconverges only the α_disrupt fraction of categories; combining the reduced dimension with the reduced threshold yields lower bound γ ≥ (C / c_d) · (θ / p_d★) ≈ 4.6 (C=6, c_d=2, θ=0.85, p_d★=0.55).

3. **η₋ trap avoidance.** Phase 2 maintains η_eff ≈ η_confirm because 67% of decisions are immediately correct; Phase 1 with large ε_firm may fall into the η_override ≈ 0.01 regime under sustained incorrect predictions.

4. **Centroid-distance (v7).** Let D_1 = ε_firm (Phase 1 starting distance to ground truth in centroid space) and D_2 = (α_disrupt / (1 − α_disrupt)) · ‖Δ‖ (Phase 2 effective starting distance after the rolling-window shortcut). The θ threshold cancels because the inequality is stated in centroid-distance space rather than accuracy-threshold space. D_1 > D_2 is equivalent to the theorem condition and constitutes the cleanest proof for empirical validation: EXP-G1 measures γ as a centroid-distance convergence-rate ratio, not an N_half ratio. Grok 3 primary attribution; confirmed by GPT-4.1, Claude Opus 4.7, Gemini 1.5 Pro.

The four paths are independent — each proves γ > 1 under the stated conditions without depending on the others.

**Conditions.** (1) Category-sparse disruption: α_disrupt = c_d/C ≈ 0.33. (2) Warm-started centroids: Phase 1 has converged. (3) ε_firm > 0.125. All three hold in every deployment studied.

**Simulation validation.** Oracle separation experiments (April 2026) confirmed the binary prediction: ε_sim = 0.05 < 0.125 gives γ = 0.714 < 1 ✓; ε_sim = 0.20 > 0.125 gives γ = 1.033 > 1 ✓. Empirical γ measurement via EXP-G1 (90-day pilot data, centroid-distance metric) is in progress.

**Production-faithful experimental characterization (May 2026).** A 270-run parameter sweep (6 ε values × 3 kernel modes × 15 seeds) using DK-aware update gradients and conservation gating confirmed the binary prediction and characterized the effect size. L2 kernel at ε > 0.125: γ ≈ 1.2 (18% faster recovery). DiagonalKernel with correct weights: γ ≈ 1.07 (DK gradient dampens the effect). DiagonalKernel with stale pre-disruption σ estimates: γ < 1.0 (stale weights reverse the effect; see below). The dimensional lower bound γ ≥ 4.6 (proof path 2) is an idealized limit not reached under production scorer dynamics due to η asymmetry, conservation gate pausing, and centroid clipping. 100% convergence across all conditions.

**DK-STALE finding.** DiagonalKernel weights estimated pre-disruption concentrate the update gradient on pre-disruption discriminative dimensions. Post-disruption, these dimensions may no longer be discriminative, causing 1.3–1.9× convergence slowdown vs L2. Operational mitigation: reset KernelSelector to L2 during disruption recovery, re-enable DK after ~200 post-disruption decisions stabilize σ estimates.

**Business implication — institutional memory as asset, not liability.** γ > 1 means that when the threat landscape shifts, accumulated institutional memory speeds re-calibration rather than slowing it. This inverts the intuition that "stale models need full retraining" — the theorem formalizes the specific condition (category-sparse disruption, warm-started centroids, ε_firm > 0.125) under which institutional memory is a genuine asset against environmental change rather than a liability. The dimensional lower bound γ ≥ 4.6 (proof path 2) is an idealized limit; production-faithful measurement yields γ ≈ 1.2 for L2 kernel — a moderate but genuine acceleration. The practical implication holds: for a CISO evaluating "should we rebuild after the campaign?", the answer remains no — existing centroid calibration is an asset to preserve, and L2-based recovery is measurably faster than cold start.

[FIGURE 15 | gamma_theorem_regions.png | NEW v7 | Re-Convergence phase diagram: x-axis ε_firm [0, 0.40]; vertical line at threshold ε_firm★ ≈ 0.125; shaded regions "γ < 1 (slower)" and "γ > 1 (faster)"; two simulation points (ε=0.05 → γ=0.714; ε=0.20 → γ=1.033); shaded band "production range ε_firm ∈ [0.15, 0.40]" within γ > 1 region. Caption: four structural proof paths; EXP-G1 pending. | §4.6 | New graphic]

---

# **5. Experimental Validation**

We validated the framework through ~180 experiment entries — 47 primary experiments plus sub-experiments from two multi-cell factorials totaling 1890 cells — across five phases: 4 original (Phase 1, February 2026); 9 bridge (Phase 2, March 2–4) that falsified the published equation; 5 validation (Phase 3, March) responding to independent review; ~89 in Phase 4 (March 14–21) including the 390-cell kernel factorial and deployment-persona validation; and Phase 5 (March 23 – April 19) including the 1500-cell UNI-DK-01 v5.3 characterization surface, the MR-COLAB-01 healthcare reproduction, and the SOC-Q1 conservation-law operational-definition adjudication. All code publicly available [14].

## **5.1 Setup**

Synthetic SOC data: 6 factors × 4 actions × 6 alert categories. Profile centroid tensor μ ∈ ℝ^{(6×4×6)} = 144 values. A=4 confirmed by EXP-A4-DIAGONAL: 13pp structural gap between A=4 and A=5, kernel-independent. The `refer_to_analyst` action was removed from the centroid tensor (accessed via policy-based referral rules R1–R7). Static accuracy improved from 80.4% (A=5) to 90.6% (A=4).

## **5.2 Key Experiments**

**EXP-C1: Kernel comparison (hero finding).** Dot product: 61.00%. Cosine: 96.42%. L2: 97.89%. The 36.89pp gap from one change — on identical data, identical profiles, zero learning — is the largest single-variable effect in the record.

[FIGURE 16 | eq_three_kernels.png | Chart | Three Kernels, Same Data: Dot (61.0%), Cosine (96.42%), L2 (97.89%). Bar chart with +36.89pp gap annotated between Dot and L2; small +1.47pp annotation between Cosine and L2. | §5.2 | Reusable from arxiv v4 paper_figures]

**EXP-2: Cross-graph discovery.** Security Context (100 entities) × Threat Intelligence (80 entities). With z-score + L2 normalization: F1 = 0.071, 111× above random. Without normalization: F1 = 0.000.

**V1A: Scaling validation.** b = 2.11, 95% CI [2.09, 2.14], R² = 0.9999 across n = 2–15 domains. Excess exponent (0.11) is the empirical signature of the β · R(n, t) second-order term (see §4.4 reconciliation with the n² theoretical floor).

**V3B: Calibration.** ECE = 0.036 at τ = 0.1, versus 0.190 at previous default τ = 0.25 (L2 specifically).

**EXP-B1: Noise robustness.** 0.2pp drop at 30% oracle error — expert initialization provides both accuracy and noise resistance.

**EXP-E2: Scale validation.** Warm/cold gap widens from 8pp to 27pp as the scoring problem grows from 5×5×5 to 20×10×20.

**V-MV-KERNEL-HET: DiagonalKernel factorial (peak).** 390-cell factorial. +13.2pp on SOC heterogeneous noise, +6.8pp on S2P. Corr(noise_ratio, advantage) = 0.990 across 4 healthcare personas. Off-diagonal correlations <1pp in both domains (V-HC-SHRINKAGE, V-S2P-HETERO) — noise ratio alone drives the advantage.

**UNI-DK-01 v5.3: DiagonalKernel controlled characterization.** 1500-cell factorial at fixed mean-σ = 0.175 across NR ∈ {1.0, 1.5, 2.0, 3.0, 5.0} × 5 q̄-levels × 30 seeds × 2 kernels. Monotone asymptotic gap: 0.00pp at NR=1.0 → +7.67pp at NR=5.0. Cold-start contribution dominant at every NR (54.5%–75.5% of total). All four pre-registered D-checks PASS. E2 characterized the calibration surface (ECE 0.055 → 0.420 across NR=1–5 for DK; L2 0.04–0.06 flat); E1/E3/E4 confirmed that confidence-based kernel selection is unreliable — below chance at NR ≥ 3 — because the sharpening mechanism defeats confidence-based comparison metrics. Rule-based selection ships. Claims traceability: CLAIM-53 / CLAIM-DK-CAL / CLAIM-67.

**MR-COLAB-01: Healthcare reproduction.** Independent 50-seed reproduction at full healthcare noise profile (σ range 0.07–0.35, NR 5.0×). DK delivers +8.86pp over L2 — the **V-HC-CONFIG floor of +3.7pp at σ=0.22** becomes a conservative lower bound under full profile heterogeneity. Also validated the per-factor formula N_half_j = (w_max / w_j) · ln(2) / η for N_half_j ≥ 25; for smaller values, discrete measurement noise introduces up to 60% ratio error — path to unconditional per-factor claim is via EXP-G1 pilot data.

**B5B-PROXY: Asymmetric learning validation.** η_override = 0.01 eliminates 13–27pp centroid degradation. Derived from information-theoretic principles: η_override = η_confirm · (2q̄_worst − 1) with q̄_worst = 0.60 from 24-persona validation (four-judge poll, April 16, 2026).

**V-CGA-FROZEN v3 (N=257, 90% power).** Graph enrichment reduces per-factor σ 23–46%, causing DiagonalKernel to upweight reliable factors → +5.0pp Day-1 triage accuracy (p<0.0001). Graph enrichment does NOT change centroid convergence rate (d = −0.010, p = 0.873, definitive null). Precision substrate validated; convergence-speed claim retired.

**γ-theorem simulation validation.** Oracle separation (April 2026) confirmed binary prediction in both directions. Four structural proof paths confirmed across two four-judge math polls (April 8 paths 1–3; April 16 path 4). Empirical γ measurement via EXP-G1 in progress.

## **5.3 Summary**

| **Level** | **Published Claim** | **Phase 1 Result** | **Phase 2+ Result** | **Final Status** |
| --- | --- | --- | --- | --- |
| Level 1 (Scoring) | Dot-product attention | 69.4% convergence | Falsified. **L2 centroidal: 97.89% (EXP-C1)**. DK adds +13.2pp peak (V-MV-KERNEL-HET) and +7.67pp asymptotic at NR=5.0 (UNI-DK-01 v5.3). | **Corrected:** Eq. 4-final + rule-based DK selector + prediction/estimation channel separation. |
| Level 2 (Discovery) | Cross-attention (Eq. 6) | 111× above random | Unchanged | **Validated** — exact correspondence to Eq. 1; mandatory z-score + L2 normalization prerequisite (EXP-2). |
| Level 3 (Multi-domain) | D(n) ∝ n^{2.30} | b = 2.30 (5-point) | b = 2.11, CI [2.09, 2.14] | **Validated, revised** — 11-point log-log, R²=0.9999. n^{2.11} empirical; n² structural floor. |
| Re-Convergence | — | — | γ > 1 ⇔ ε_firm > 0.125, four proof paths | **Tier 2 QUALIFIED** — binary prediction confirmed (simulation + 270-run sweep). Effect size γ ≈ 1.2 (L2), not 4.6 (idealized). DK stale weights reverse effect. EXP-G1 pilot pending. |
| Two-Phase + Safety (v7.3) | — | — | Phase 1 means (transferable) → Phase 2 DK weights (firm-specific) via shrinkage + promotion gate | **Designed** — framework v4, 5-judge review, ~115 experiments. Implementation v6.5. |

*Table 2: Key experimental results. v7 additions: DK characterization at NR=5.0, MR-COLAB-01, calibration surface, Re-Convergence Theorem. v7.1 fix: Level 1 row references 97.89% (EXP-C1), not the earlier ambiguous "98.2%" (which was from V4/EXP-B1 zero-noise baseline).*

Additional experiments established: warm-start superiority at scale (EXP-E2), cross-category transfer (EXP-D1), absence of factor interactions in SOC data (EXP-D2), kernel generalization across distributions (EXP-E1), centroid clipping necessity (V2), KernelSelector rule validation across 1890 cells, SOC-Q1 conservation-law operational-definition closure. Complete record in Appendix A.

# **6. Related Work**

**Attention mechanisms and kernels.** Tsai et al. [2019] analyze attention through a kernel lens; Katharopoulos et al. [2020] use kernel approximations for linear attention; Choromanski et al. [2021] use random feature maps. Our contribution is domain-specific: the kernel choice produces a 36.89pp gap on bounded operational features, and the next-order choice (kernel weighting via inverse-variance) produces a further +7.67pp to +13.2pp gap with a characterized calibration tradeoff (§3.1) handled via prediction/estimation channel separation.

**Prototype networks and metric learning.** Snell et al. [2017] introduced prototypical networks for few-shot learning using Euclidean distance. Our centroid update rule extends this with asymmetric push/pull (derived from worst-case analyst quality), count-based decay, max-normalized kernel-aware gradient, and mandatory clipping. Xing et al. [2003] and Weinberger & Saul [2009] developed Mahalanobis-style distance metric learning with full covariance matrices; our empirical finding that the diagonal captures the full advantage is consistent with the "naive Bayes paradox" [Domingos & Pazzani, 1997].

**Diagonal and Mahalanobis kernels.** Our contribution: off-diagonal correlations add <1pp across two tested domains (SOC, S2P). The calibration characterization (ECE as a function of noise ratio) is, to our knowledge, novel: weighted-distance kernels are not typically analyzed for calibration properties distinct from their accuracy. Guo et al. [2017] characterized miscalibration in modern neural networks; our analogous characterization for inverse-variance-weighted distance kernels shows that the same mechanism driving the accuracy gain (weight concentration on reliable factors) also sharpens the softmax and degrades calibration.

**Shrinkage estimation and two-phase learning (v7.3).** James-Stein shrinkage [Stein, 1956; James & Stein, 1961; Efron & Morris, 1973] provides the mathematical guardrail for our Phase 2 metric learning: the interpolated estimator dominates either extreme for p ≥ 3. Our two-phase architecture — first estimate location (centroid means), then estimate scale (discriminative weights) with shrinkage — is related to the empirical Bayes tradition where the shrinkage target is a simpler model. The Fisher information argument motivating Phase 2 persistence [Fisher, 1925; Amari, 1985] is used as a Layer A/B framework: the Gaussian surrogate motivates why metric structure remains learnable (Layer A), and empirical alignment confirms the pattern in the deployed (non-MLE) estimator (Layer B). This separation — theoretical motivation distinct from empirical confirmation — is, to our knowledge, novel in the applied ML literature on adaptive scoring systems.

**Conservation constraints in adaptive systems.** Our conservation law α·q·V ≥ θ_min is a form of regret-bounded learning [Shalev-Shwartz, 2012] applied to a two-level system. Two independent LLM-judge panels validated different aspects: a three-judge panel (GPT-4o / Claude Opus / Gemini, March 2026) validated the original formulation, and two four-judge math polls (GPT-4.1 / Claude Opus 4.7 / Grok 3 / Gemini 1.5 Pro, April 8 and April 16, 2026) validated the Re-Convergence Theorem and the η_override derivation respectively. The v7 operational definition of q decouples the conservation signal from kernel-specific calibration properties.

**Graph attention networks.** GAT [Veličković et al., 2018] applies attention within a single graph; our cross-graph attention operates between separate domain graphs with no shared topology — a structurally different setting enabling discovery of relationships between graphs that share no edges. GNN-based embeddings (Kipf & Welling, 2017; Hamilton et al., 2017) are a natural future extension for Level 2.

**Agent memory and cognitive architectures.** CoALA [38] formalized the three-type memory taxonomy (episodic, semantic, procedural) that underlies modern agent memory systems. Mem0 [39] implements episodic + semantic memory with entity linking for personalization. Zep [40] uses a temporal knowledge graph (Graphiti) with bi-temporal modeling for enterprise agent memory. MAGMA [41] represents memory across orthogonal semantic, temporal, causal, and entity graphs with policy-guided retrieval. GAM [42] separates narrative buffering from semantic consolidation via hierarchical graph structure. A comprehensive survey [43] covers mechanisms, evaluation, and frontiers.

Our centroid geometry, noise fingerprint, and conservation law address a problem none of these systems target: measuring per-factor decision quality from verified outcomes and proving when autonomous action is safe. The three CoALA memory types store WHAT (episodic), WHY (semantic), and HOW (procedural). Our judgment memory stores HOW WELL — a measurement that requires outcome-conditioned variance decomposition across verified decisions and cannot be derived from any combination of the standard three types. The distinction is analogous to the difference between a medical record (episodic: what treatments were given), a medical textbook (semantic: what is known about the condition), a clinical protocol (procedural: how to treat), and a surgical quality scorecard (judgment: how well THIS surgeon performs THIS procedure on THIS patient type). The first three can all confirm a systematically biased treatment protocol; only the fourth detects the bias.

# **7. Discussion and Limitations**

**The hierarchy of design decisions.** The experimental program identified five architectural decisions that collectively determine more of the system's accuracy than any amount of accumulated learning:

1. **Kernel function** (L2 vs dot product: 36.89pp, EXP-C1). Irreversible at deployment time.
2. **Kernel weighting** (diagonal 1/σ² vs uniform: up to +13.2pp peak, +7.67pp asymptotic). Deployment-specific; rule-based at Day 1.
3. **Learning-rate asymmetry** (η_override from 2q̄_worst − 1: prevents 13–27pp degradation, B5B-PROXY). Derived, not tuned.
4. **Kernel-selection architecture** (rule-based Day 1 vs confidence-based, UNI-DK-01 v5.3 E1/E3/E4). Required because confidence-based comparison is below chance under DK sharpening.
5. **Two-phase separation** (freeze means at ~200 decisions, estimate precision weights via batch pipeline with shrinkage). Phase 1 saturates; Phase 2 continues improving (+3.2pp to +5.4pp). The batch promotion gate ensures no untested update deploys.

These five decisions are architectural — made once, at configuration time. Everything else (centroid values, per-factor σ refinement, discovery thresholds) is operational and accumulates from verified decisions.

**Judgment memory as architectural contribution.** The five design decisions above produce a system that not only scores decisions but measures its own judgment quality per factor — a capability we term judgment memory. This positions the framework within the agent memory literature [38-43] as addressing a fourth cognitive type: where episodic memory stores decision history, semantic memory stores domain knowledge, and procedural memory stores operational rules, judgment memory stores outcome-conditioned quality measurements that compound with verified decisions and produce safety proofs via the conservation law. The signal-confidence inversion finding (§3.1) — detectable only through judgment memory — suggests that systematic judgment biases may be a general property of expert decision-making under uncertainty, not a domain-specific artifact.

**Defense in depth.** The safety architecture uses three layers rather than relying on any single mechanism: James-Stein shrinkage provides a mathematical guardrail (the interpolated scorer provably dominates either extreme for p ≥ 3; empirically, 0/21 degradation at α=0.5), the promotion gate provides an operational guardrail (holdout non-inferiority before any batch deployment), and instant rollback provides recovery. This is stronger than "shrinkage guarantees safety" — it is layered assurance where each layer catches failures the others might miss.

**The default kernel is wrong for most enterprise applications.** Exporting the dot product from transformer attention to enterprise feature scoring is a category error. EXP-C1 measures the cost: 36.89 percentage points. Credit scoring, insurance risk assessment, supply chain prioritization, vendor evaluation, and HR talent matching are all vulnerable to the same magnitude confounding.

**Prediction vs estimation channels.** The DiagonalKernel calibration finding motivates a broader architectural pattern: weighted-distance kernels on bounded features can produce an accurate prediction channel (argmax) and an unreliable estimation channel (confidence values) simultaneously, because the same mechanism that concentrates weight on reliable factors also sharpens the output distribution. Any enterprise system deploying inverse-variance-weighted distance scoring should measure this explicitly and route confidence-sensitive consumers through kernel-independent signals — rolling verified accuracy or softmax entropy. Systems that quote raw DK confidence to humans or feed it to downstream ML ensembles without re-calibration are overstating precision.

**The LLM judge finding.** Three frontier models available at the time of the original diagnosis (GPT-5, Claude Opus, Grok) correctly diagnosed magnitude confounding as the root cause of the published equation's failure but unanimously prescribed gating interventions. The best gating variant added 0.01pp. The correct fix added 36.89pp. This motivates the diagnostic protocol: run the one experiment before pursuing architectural interventions. The two four-judge math polls (April 8 and April 16, 2026; GPT-4.1 / Claude Opus 4.7 / Grok 3 / Gemini 1.5 Pro) use a complementary protocol — LLMs produce the analytical derivations, independent panels verify, and mathematical consensus gates the claim. The diagnostic lesson: LLM panels are unreliable reviewers when asked to prescribe fixes to empirical failures (where run-the-experiment beats prescribe-the-fix), but reliable when asked to verify analytical derivations against stated conditions (where mathematical consensus is the correct gate).

**Synthetic data — now characterized.** FX-1-PROXY-REAL quantified the distribution gap using 2,430 real IOC records from CISA KEV, NVD, and MITRE ATT&CK. All three factors show KL divergence >1.8 from the centroidal Gaussian assumption. Longitudinal validation on real SOC data over 6–12 months remains the highest-priority next step.

| **Factor** | **Real Mean** | **Synthetic Mean** | **Skewness** | **Kurtosis** | **KL Divergence** |
| --- | --- | --- | --- | --- | --- |
| Threat Intel Score | 0.467 | 0.500 | −0.60 | −1.11 | 2.578 |
| Asset Criticality | 0.646 | 0.500 | −0.60 | −1.39 | 1.880 |
| Pattern History | 0.165 | 0.300 | +2.82 | +8.05 | 2.434 |

**Convergence.** The pull/push update rule is an empirically effective heuristic without formal convergence guarantees in the most general setting. The Re-Convergence Theorem establishes formal conditions for γ > 1 (category-sparse disruption, warm-started centroids, ε_firm > 0.125) — all hold in every deployment studied (production range [0.15, 0.40]). Production-faithful measurement (May 2026) characterizes the effect at γ ≈ 1.2 for L2 kernel, below the idealized dimensional bound of 4.6. DiagonalKernel with stale pre-disruption weights reverses the effect (γ < 1.0), motivating a kernel reset procedure during disruption recovery. The conservation law α·q·V ≥ θ_min (α = cumulative category coverage; θ_min = 23.53/(α·V), a cold-start interlock) provides a runtime safety mechanism.

**Per-factor N_half reclassified.** The scalar claim "N_half ≈ 14 verified decisions" holds for L2 or for the cleanest factor under DK. Under DK with heterogeneous noise, per-factor N_half_j = (w_max / w_j) · ln(2) / η varies widely — at NR=5.0, the noisiest factor's N_half_j can reach ~346 decisions. This is correct behavior (noisy factors should learn slowly), but it revises the scalar claim from unconditional to per-factor-conditional. MR-COLAB-01 validated the formula for N_half_j ≥ 25; path to unconditional is EXP-G1 pilot data.

# **8. Conclusion**

We have presented a three-level framework connecting enterprise AI decision-making to distance-kernel attention. The central finding: on bounded operational features, L2 distance outperforms dot product by 36.89 percentage points — the largest single-variable effect in our ~180-experiment record. A second kernel finding: DiagonalKernel adds up to +13.2pp peak over L2 (V-MV-KERNEL-HET, 390 cells) with characterized monotone scaling to +7.67pp asymptotic at NR=5.0 (UNI-DK-01 v5.3, 1500 cells) — 1890 total cells, curve citable across the noise-ratio range. The DK accuracy advantage comes with a characterized calibration tradeoff (ECE 0.055 → 0.420 across NR) that the architecture addresses through prediction/estimation channel separation.

Together with asymmetric learning rates derived from worst-case analyst quality (η_override = 0.01 at q̄_worst = 0.60), a conservation law (α·q·V ≥ θ_min, α = cumulative category coverage, θ_min = 23.53/(α·V) an empirically calibrated cold-start interlock, with q = rolling verified accuracy over 400 decisions), and the Re-Convergence Theorem (γ > 1 ⇔ ε_firm > 0.125, four structural proof paths), the framework provides validated mechanisms for all identified failure modes. A two-phase learning architecture separates mean estimation (Phase 1, transferable, saturates) from discriminative precision weight estimation (Phase 2, firm-specific, ongoing) via James-Stein shrinkage, with every batch update passing through a promotion gate — defense in depth with mathematical, operational, and recovery layers. Profile centroids achieve 90.6% with zero learning (A=4, realistic data); 97.89% on centroidal synthetic. Discovery scales super-quadratically (n^{2.11}). The framework is validated across ~180 experiment entries (47 primary + 1890 factorial sub-cells).

The economic implication stated in §1.1 closes here: three architectural decisions — kernel, weighting, learning dynamics — determine whether an enterprise AI investment is operating expense or capital infrastructure. This paper quantifies all three. The accompanying production control-plane paper [Banerji, 2026c] quantifies the runtime safeguards that make compounding operational.

# **9. Future Work**

## **9.1 Resolved in v7**

The v7 experimental closure retired several previously-open research items. **Mahalanobis kernel:** DiagonalKernel captures the full advantage; off-diagonal <1pp (CLAIM-53). **DiagonalKernel calibration:** characterized via UNI-DK-01 v5.3 E2; addressed via prediction/estimation channel separation — re-calibration of per-category auto-approve thresholds under DK routing is a first-customer PROD-4b exercise (CLAIM-DK-CAL). **KernelSelector architecture:** rule-based selection at Day 1, 100% across 1890 cells (CLAIM-67). **Conservation law q and α operational definitions:** q = rolling verified accuracy over last 400 decisions; α = cumulative category coverage (c_d/C), not override rate [updated v7.6 under D1; the SOC-Q1 "α over last 50 verified" windowing is superseded — q definition stands]; V = verified decisions per day; SOC-Q1 closure April 19, 2026 (CLAIM-Q-DEF). **Adversarial robustness:** validated in [Banerji, 2026c] — 38% non-recovery (N=100, 95% CI 29–48%), 0.15pp poisoning ceiling at A=4. **Formal convergence:** partially resolved — Re-Convergence Theorem proven for category-sparse disruption with ε_firm > 0.125, four structural proof paths. **Graph enrichment as precision substrate:** validated — +5pp Day-1 accuracy via DK reweighting (p<0.0001); IKS trajectory advantage at all checkpoints (p=0.0006); convergence-speed claim retired as definitive null (d=−0.010, p=0.873).

## **9.2 Open research agenda**

Of the items below, the highest priority is **real-data longitudinal validation** on operational SOC data over 6–12 months — synthetic LLM-judge validation across 9 deployment-realistic streams provides pre-customer validation, but real data is the binding gate for deployment-scale claims. Second priority is **EXP-G1 empirical γ measurement** via 90-day pilot centroid-distance data — closes the Re-Convergence Theorem's final empirical gate. Remaining items ordered by dependency:

- **Real data validation (priority 1).** Operational SOC data over 6–12 months for V3A and V-SIM replication, FX-1-PROXY-REAL distribution characterization extended to live streams, and real-customer KernelSelector rule verification.

- **EXP-G1 empirical γ (priority 2).** Measures γ empirically using the centroid-distance metric per proof path 4. The γ > 1 claim in Eq. 14 refers to the discovery scaling term (Term 3 of Eq. 13) — separate mechanism from centroid convergence, unaffected by V-CGA-FROZEN findings.

- **Two-phase learning validation (v7.3).** Phase 1 saturation timing and Phase 2 improvement curve on pilot data. Shrinkage non-inferiority with expanded seed/distribution coverage beyond the 21 checkpoints currently observed (rule of three: ≤14% upper bound at 95% CI).

- **Per-factor N_half empirical validation.** EXP-G1 pilot data will measure per-factor convergence across deployment noise profiles.

- **V-CGA-FROZEN v4 and V-KERNEL-W.** Two conditional paths from the graph enrichment resolution: (i) Empirical Bayes bootstrap reduces calibration time via starting geometry (N=100/arm, pending); (ii) lower σ increases effective per-dimension learning rate under DK via Fisher information (2 personas, pending). Gate CLAIM-62/63 and CLAIM-64.

- **GNN-based embeddings.** For Level 2; Experiment 4 phase transition (σ = 0.3) suggests learned embeddings would substantially improve discovery precision.

- **Multi-prototype extensions.** For categories with distinct sub-populations.

- **Kill-chain modeling.** Via sequence-aware features for multi-stage attack detection.

- **Override learning for referral routing.** Policy-based rules achieve 72.7% DR at 12% FPR (EXP-REFER-LAYERED); the 20.7% emergent fraction requires ML-based override learning, data-gated at ≥ 50 positive examples.

- **Multi-domain validation.** S2P validated (d=8, +6.8pp from DK); supply chain, procurement, and financial compliance remain untested in full production contexts.

- **Formal convergence — general case.** Asymptotic convergence of Eq. 4b-final for arbitrary analyst quality is open. Conservation law provides a practical runtime substitute.

# **References**

[1] Vaswani, A., et al. (2017). Attention Is All You Need. NeurIPS 30.
[2] Li, L., et al. (2010). A contextual-bandit approach to personalized news article recommendation. WWW 2010.
[3] Kipf, T.N. & Welling, M. (2017). Semi-supervised classification with GCNs. ICLR.
[4] Hamilton, W.L., et al. (2017). Inductive representation learning on large graphs. NeurIPS 30.
[5] Veličković, P., et al. (2018). Graph attention networks. ICLR.
[6] Tsai, Y.-H.H., et al. (2019). Transformer dissection via the lens of kernel. EMNLP-IJCNLP.
[7] Choromanski, K., et al. (2021). Rethinking attention with performers. ICLR.
[8] Snell, J., et al. (2017). Prototypical networks for few-shot learning. NeurIPS 30.
[9] Kulis, B. (2013). Metric learning: A survey. FTML 5(4).
[10] BRIDG-ICS (2025). Semantic knowledge graphs for cybersecurity. GitHub.
[11] Banerji, A. (2026). Cross-graph attention: Mathematical foundation. Technical Report, Dakshineshwari LLC.
[12] Banerji, A. (2026). Compounding intelligence 4.0. Technical Report, Dakshineshwari LLC.
[13] Banerji, A. (2026). Cross-graph attention: The evidence. Technical Report, Dakshineshwari LLC.
[14] Banerji, A. (2026). Code and data generators. https://github.com/ArindamBanerji/cross-graph-experiments.
[15] Katharopoulos, A., et al. (2020). Transformers are RNNs. ICML.
[16] Kohonen, T. (1990). The self-organizing map. Proc. IEEE 78(9).
[17] Jacobs, R.A., et al. (1991). Adaptive mixtures of local experts. Neural Computation 3(1).
[18] Shazeer, N., et al. (2017). Sparsely-gated MoE layer. ICLR.
[19] Miller, G.A. (1956). The magical number seven. Psych. Review 63(2).
[20] Guo, C., et al. (2017). On calibration of modern neural networks. ICML.
[21] Buchanan, B.G. & Shortliffe, E.H. (1984). Rule-Based Expert Systems. Addison-Wesley.
[22] Banerji, A. (2026c). Production architecture for compounding intelligence. Technical Report, Dakshineshwari LLC.
[23] Xing, E.P., et al. (2003). Distance metric learning. NeurIPS 15.
[24] Weinberger, K.Q. & Saul, L.K. (2009). Distance metric learning for large margin nearest neighbor. JMLR 10.
[25] Domingos, P. & Pazzani, M. (1997). On the optimality of the simple Bayesian classifier. Machine Learning 29(2-3).
[26] Shalev-Shwartz, S. (2012). Online learning and online convex optimization. FTML 4(2).
[27] Borkar, V.S. (2008). Stochastic Approximation. Cambridge University Press.
[28] Banerji, A. (2026d). SOC Copilot: Production deployment architecture. Technical Report, Dakshineshwari LLC.
[29] Banerji, A. (2026e). UNI-DK-01 v5.3 DiagonalKernel characterization. Technical Report, April 19, 2026.
[30] Banerji, A. (2026f). SOC-Q1 adjudication: Conservation-law operational definition. Technical Report, April 19, 2026.
[31] Banerji, A. (2026g). Four-judge math polls: η_override derivation and γ-theorem proof paths. Technical Report, April 8 and April 16, 2026.
[32] Banerji, A. (2026h). MR-COLAB-01: Healthcare DiagonalKernel reproduction. Technical Report, Dakshineshwari LLC.
[33] Stein, C. (1956). Inadmissibility of the usual estimator for the mean of a multivariate normal distribution. Proc. 3rd Berkeley Symposium on Mathematical Statistics and Probability.
[34] James, W. & Stein, C. (1961). Estimation with quadratic loss. Proc. 4th Berkeley Symposium.
[35] Efron, B. & Morris, C. (1973). Stein's estimation rule and its competitors. JASA 68(341).
[36] Fisher, R.A. (1925). Theory of statistical estimation. Mathematical Proceedings of the Cambridge Philosophical Society 22(5).
[37] Amari, S.-I. (1985). Differential-Geometrical Methods in Statistics. Lecture Notes in Statistics 28.
[38] Sumers, T.R., et al. (2023). Cognitive Architectures for Language Agents. arXiv:2309.02427.
[39] Chhikara, P., et al. (2025). Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory. ECAI 2025. arXiv:2504.19413.
[40] Rasmussen, P. (2025). Zep: A Temporal Knowledge Graph Architecture for Agent Memory. arXiv:2501.13956.
[41] Jiang, D., et al. (2026). MAGMA: A Multi-Graph based Agentic Memory Architecture for AI Agents. arXiv:2601.03236.
[42] Huang, W.-C., et al. (2026). GAM: Hierarchical Graph-based Agentic Memory for LLM Agents. arXiv:2604.12285.
[43] He, S., et al. (2026). Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers. arXiv:2603.07670.

# **Appendix A: Complete Experiment Record**

### **Phase 1 (February 2026) — 4 original experiments establishing baseline**

| **#** | **ID** | **Question** | **Result** | **Key Number** |
| --- | --- | --- | --- | --- |
| 1 | EXP-1 | Scoring convergence (5 methods) | PASS | Compounding 69.4%, Periodic 53.8% |
| 2 | EXP-2 | Cross-graph discovery | PASS | F1=0.071, 111× above random |
| 3 | EXP-3 | Discovery scaling (5-point) | PASS | b=2.30, R²=0.998 |
| 4 | EXP-4 | Embedding sensitivity | PASS | Phase transition σ=0.3 |

### **Phase 2 (March 2–4, 2026) — 9 bridge experiments falsifying the published equation**

| **#** | **ID** | **Question** | **Result** | **Key Number** |
| --- | --- | --- | --- | --- |
| 5 | EXP-5 | Oracle quality | PASS | 79.65% with GT oracle (dot product ceiling) |
| 6 | EXP-A1–A3 | Gating matrix (3 variants) | FAIL | +0.01pp maximum |
| 7 | EXP-B1 | Noise robustness | PASS | 0.2pp drop at 30% oracle error |
| 8 | EXP-C1 | Centroid oracle: kernel comparison (hero) | PASS | 97.89% L2, 61.0% dot (+36.89pp) |
| 9 | EXP-D1 | Cross-category transfer | PASS | Expert profiles win 2–14pp |
| 10 | EXP-D2 | Factor interactions | PASS | 0 significant (threshold 1.0 bits) |
| 11 | EXP-E1 | Kernel generalization | PASS | L2 wins [0,1]; Mahalanobis wins mixed |
| 12 | EXP-E2 | Scale validation | PASS | 27pp warm/cold gap at 20×10×20 |

### **Phase 3 (March 2026) — 5 validation experiments for independent review**

| **#** | **ID** | **Question** | **Result** | **Key Number** |
| --- | --- | --- | --- | --- |
| 13 | V1A | Scaling (11-point extension) | PASS | b=2.11, CI [2.09,2.14], R²=0.9999 |
| 14 | V1B | Norm explosion | PASS | 2.9M× without normalize |
| 15 | V2 | Push stability | PASS | 4,608× unclipped, 2.2× clipped |
| 16 | V3A | Realistic simulation (50-seed) | PASS | 71.7% static, 78.9% at 1K decisions |
| 17 | V3B | Calibration | PASS | ECE=0.036 at τ=0.1 (L2) |
| 18 | V4 | Online learning comparison | PASS | L2 centroid 94.3% vs RF 92.9% |
| 19 | V4 (ext) | Data efficiency | PASS | 5pp advantage from 200 samples |

*Note on phase counts: §5 references 4+9+5=18 Phase 1–3 experiments; table shows 19 rows because EXP-A1–A3 counts as 3 sub-experiments. The 9-bridge count in §5 is EXP-5 + (EXP-A1, A2, A3) + EXP-B1 + EXP-C1 + EXP-D1 + EXP-D2 + EXP-E1 = 9, with EXP-E2 counted in Phase 3.*

### **Phase 4: Extension, Kernel Factorial, and Deployment Persona (March 14–21, 2026)**

| **#** | **ID** | **Question** | **Result** | **Key Number** |
| --- | --- | --- | --- | --- |
| 20 | V-MV-KERNEL-HET | DK vs L2 factorial (heterogeneous) | PASS | +13.2pp SOC peak, +6.8pp S2P (390 cells) |
| 21 | V-MV-KERNEL-UNI | DK vs L2 factorial (uniform, null) | PASS-NULL | Kernels identical at uniform σ (216 cells) |
| 22 | V-HC-CONFIG | DK rescues healthcare | PASS | +3.7pp floor at σ=0.22 (4 personas) |
| 23 | V-HC-SHRINKAGE | Off-diagonal helps scoring? | NO | <1pp gap |
| 24 | V-S2P-HETERO | S2P off-diagonal confirmation | NO | <1pp gap, cross-domain confirmed |
| 25 | B5B-PROXY | Realistic analyst quality | PASS | η_override=0.01 prevents 13–27pp |
| 26 | Phase 1 sweeps | Product boundaries | PASS | σ ≤ 0.25 (DK), V ≥ 30, q̅ ≥ 0.70 |
| 27 | HC-scaling | Noise ratio predicts advantage | PASS | r=0.990 across 4 personas |
| 28 | KernelSelector | Auto-select kernel (historical) | PASS | 4/4 correct across HC personas |
| 29 | EXP-A4-DIAGONAL | A=4 vs A=5 | PASS | 13pp structural gap, kernel-independent |
| 30 | EXP-REFER-LAYERED | Referral architecture | DONE | Rules: 72.7% DR, 12% FPR, 50.7% precision |
| 31 | EXP-S2-REPRO | Poisoning at A=4 | PASS | 0.15pp max degradation |
| 32 | SHIFT-2 + A=4 | Frozen scorer baseline | PASS | 90.6% accuracy (A=4) |
| 33 | V-CGA-FROZEN v1 | Graph enrichment lifts frozen scorer? (underpowered) | DONE | M1 ✅ M2 ❌ (p=0.097) M3 ✅ +3.6pp |
| 34 | V-CGA-FROZEN v2 | Replication of v1 M2 | DONE | M2 ❌ identical null |
| 35 | V-CGA-FROZEN v3 | Definitive M2 test (90% power, N=257) | PASS/RETIRE | M1 ✅ M2 ❌ (d=−0.010, p=0.873) M3 ✅ +5.0pp. Precision substrate VALIDATED; convergence-speed RETIRED. |

### **Phase 5: Characterization and Operational-Definition Closure (March 23 – April 19, 2026)**

| **#** | **ID** | **Question** | **Result** | **Key Number** |
| --- | --- | --- | --- | --- |
| 36 | UNI-DK-01 v5.3 | DK characterization surface (1500-cell NR sweep) | PASS | 0.00 → +7.67pp asymptotic. D1–D4 all PASS. Cold-start 54.5–75.5% of total. |
| 37 | UNI-DK-01 v5.3 E2 | DK calibration surface (ECE vs NR) | CHARACTERIZED | DK ECE 0.055 → 0.420; L2 0.04–0.06. Architecturally addressed. |
| 38 | UNI-DK-01 v5.3 E1/E3/E4 | Confidence-based kernel selection viability | RETIRED | Below chance at NR ≥ 3. Rule-based ships. |
| 39 | MR-COLAB-01 | Healthcare DK reproduction at full noise | PASS | +8.86pp at σ range 0.07–0.35, NR=5.0, 50 seeds |
| 40 | γ-theorem (analytical) | Re-Convergence Theorem proof | PASS | γ > 1 ⇔ ε_firm > 0.125. Four structural proof paths confirmed (two four-judge polls, April 8 + April 16, 2026) |
| 41 | γ-theorem (binary simulation) | Oracle separation | PASS | ε=0.05 → γ=0.714<1 ✓; ε=0.20 → γ=1.033>1 ✓ |
| 42 | SOC-Q1 adjudication | Conservation-law q operational definition | RESOLVED | q = rolling verified accuracy / 400 decisions. (α redefined as cumulative category coverage under D1, v7.6; the original "α / 50 verified" windowing is superseded.) April 19, 2026. |
| 43 | η_override derivation | Information-theoretic ratio | RESOLVED | η_override = η_confirm · (2q̄_worst − 1) = 0.01 at q̄_worst = 0.60. Four-judge April 16, 2026. |

### **Phase 5 continued: Pending Experiments**

| **#** | **ID** | **Question** | **Status** | **Gate** |
| --- | --- | --- | --- | --- |
| P1 | V-CGA-FROZEN v4 | Empirical Bayes bootstrap reduces N_half via starting geometry? | PENDING | N_half(T2) < N_half(C0) × 0.80, N=100/arm. Gates CLAIM-62/63. |
| P2 | V-KERNEL-W | Lower σ increases effective per-dimension learning rate under DK? | PENDING | N_half(W1) < N_half(W0) × 0.80, 2 personas. Gates CLAIM-64. |
| P3 | EXP-G1 | Empirical γ measurement on 90-day pilot data | PENDING | Centroid-distance convergence rate ratio (path 4). |
| P4 | V-OLS-DETECT-OLS | OLSMonitor re-validation | PENDING | Adversarial degradation detection, p90 lead time ≥ 50 decisions. P3 backlog. |
| P5 | Framework v4 validation | Two-phase learning + batch pipeline on pilot | PENDING | Phase 1 saturation, Phase 2 improvement curve, shrinkage non-inferiority coverage. |

Full catalog (~180 experiment entries including the 1890-cell DK factorial sub-experiments) available in experiment_reference_catalog_v2 [28].

---

*— End of cga_arxiv_short v7.6 —*

*v7.5 → v7.6 additions (June 1, 2026): Canonical decisions D1–D4 applied. (D1) Conservation-law α redefined as cumulative category coverage = c_d/C (override-rate definition retired — under α≈1−q it made α·q·V ∝ q(1−q), penalizing accuracy); override_rate retained as a separate complacency advisory. Re-convergence quantity renamed α_cat → α_disrupt so the two α meanings no longer collide in one paper (§4.6, theorem, conclusion). (D3) θ_min = 23.53/(α·V) reframed as an empirically-calibrated cold-start interlock (lifecycle 0.357 → 0.118 at V=200); single "≈0.467" number retired everywhere; steady-state protector is the 0.7×-baseline relative trigger. SOC-Q1's q definition stands; its α windowing superseded. (D2) n^{2.11} labeled information-gain compounding (simulation, EXP-G1-gated), distinguished from operational compounding. (D4) signal-confidence inversion sourcing clarified — SOC is domain-informed factor design, not live-log observation. Body end-marker reconciled from stale "v7.3" to v7.6. All v7.5 content preserved. (Review pass, same day: judgment memory + signal-confidence inversion added to the abstract and keywords — previously present only in §1.1/§1.2/§6/§7, invisible to abstract/keyword indexing, defeating the agent-memory citation-network goal.)*

*v7.4 → v7.5 additions (May 19, 2026): Judgment memory positioned as fourth cognitive architecture type alongside episodic/semantic/procedural (CoALA framework). Signal-confidence inversion formally defined — the factor with highest practitioner confidence has highest outcome-conditioned variance. Agent memory literature referenced: CoALA, Mem0, Zep, MAGMA, GAM. Strategic: enters agent memory citation network. 5 insertion points. 6 new references [38]-[43]. ~14,300 words (was ~13,500). All v7.4 content preserved.*

*v7.2 → v7.3 additions (April 29, 2026): Two-phase learning formalization (§3.1 new subsection). James-Stein shrinkage as mathematical safety guardrail (Eq. SHRINKAGE). Batch pipeline with promotion gate (7 lifecycle steps, defense in depth). Fisher-inspired asymmetry Layer A/B motivating Phase 2 persistence. Discriminative metric learning positioning for DiagonalKernel (§3.1, §4.1). Defense in depth added to §7 Discussion (three layers). §6 Related Work: shrinkage estimation, Fisher information, empirical Bayes. §1.2: two new contribution bullets. §8: two-phase + defense in depth in conclusion. §9.2: two-phase validation added to open agenda. 5 new references [33]-[37]. Table 1 updated. ~13,500 words (was ~12,400). All v7.2 content preserved.*

*Prior: v7.1 → v7.2 compaction (14,640 → ~12,400 words). Low-risk cuts only. All v7.1 substantive improvements preserved. All 27 figure/equation markers preserved in position with v7.1 numbering.*
