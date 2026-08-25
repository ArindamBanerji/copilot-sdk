**Cross-Graph Attention: Distance-Kernel Scoring, Compiled Ontologies, and Super-Quadratic Discovery**

Arindam Banerji, PhD | Dakshineshwari LLC, Santa Clara, CA | banerji.arindam@gmail.com

# **Abstract**

Graph engineering — building a knowledge graph to retrieve answers and wiring a graph of agents to route work — has moved from research frontier to documented recipe. Both treat the graph as structure: something to read or to route. This paper proves that a third operation — *reshape* — crosses that line: a graph whose decision geometry reshapes from verified outcomes is safe, fast, independent of the enrichment that populates it, and produces a fourth cognitive-architecture type (judgment memory) that no read or route can derive. The formal evidence establishes graph-native reasoning as a cognitive-architecture transition beyond graph engineering, not merely a better kernel or a faster scorer.

The decision kernel matters: on identical data and identical profile centroids, L2 distance outperforms dot product by 36.89 percentage points (61.00% → 97.89%) for scoring decisions on bounded [0,1] features (Experiment C1). This magnitude confounding problem — where dot products on bounded features are dominated by high-mean dimensions regardless of discriminative value — affects any scoring system operating on pre-computed bounded features.

The architecture operates at three levels: (1) single-decision scoring as distance-kernel attention (Eq. 4-final), (2) cross-graph entity discovery as cross-attention between domain knowledge graphs (Eq. 6), and (3) multi-domain discovery with n(n−1)/2 attention heads across n domains (Eq. 9). Profile centroids are compiled ontologies — domain expert knowledge encoded as readable, auditable vectors that refine through online learning.

Key results across ~194 experiment entries (59 primary plus 1890 factorial sub-cells): L2 outperforms dot product by 36.89pp on identical centroidal data (EXP-C1) — a magnitude-confounding effect grounded in the geometry of bounded features; DiagonalKernel (per-factor 1/σ² weighting) showed up to +13.2pp over L2 on synthetic heterogeneous noise (V-MV-KERNEL-HET) and up to +10.0pp on one real dataset (Bank Marketing, min-max, 50-seed stable), but the advantage is preprocessing-dependent — it reverses sign across preprocessing conventions on most datasets, and no general predictor of when DK helps was established (best cross-dataset correlate r = −0.51, 60% leave-one-out accuracy). We report DiagonalKernel as a deployment-specific option requiring per-deployment validation, not a safe default, and retain L2 as the production kernel; 90.6% zero-learning accuracy with A=4 action space; 71.7% → 78.9% over 1,000 decisions (50-seed realistic simulation); super-quadratic discovery scaling D(n) ∝ n^{2.11} (V1A, n=2–15). Asymmetric learning rates η_override = η_confirm · (2q̄_worst − 1) = 0.01 prevent 13–27pp centroid degradation (B5B-PROXY). A conservation law α·q·V ≥ θ_min (α = cumulative category coverage) ensures learning compounds rather than decays, with q operationally defined as rolling verified accuracy over 400 decisions. Centroid means saturate at ~200 decisions per class and carry the learned scoring geometry that accumulates as the firm-specific compiled asset. The Re-Convergence Theorem (γ > 1 ⇔ ε_firm > 0.125) is analytically proven via four structural proof paths (two four-judge math polls, April 8 and 16, 2026). The theorem is confirmed for the idealized update rule (Arm B), and the production scorer logic re-converges in a calibrated apparatus (Arm A: γ > 1 across all cells, conservation fully engaged). A prior finding of γ < 1 (v8) was retracted as a calibration artifact — the original apparatus operated at chance accuracy, so conservation was trivially always-paused. Conservation does not block re-convergence when the disruption stays within the accuracy margin (§4.6). A two-engine separation result proves the expected centroid update is σ-independent, so learning (which moves centroid position μ) and graph enrichment (which reduces observation noise σ) are independent to first order, with ~1% coupling at production parameters (§3.1). We position these mechanisms — centroid geometry, per-factor noise fingerprint, and conservation law — as judgment memory, a fourth cognitive-architecture type beyond the episodic/semantic/procedural taxonomy of agent-memory systems (CoALA, Mem0, Zep, MAGMA); judgment memory measures per-factor decision quality from verified outcomes and uniquely surfaces signal-confidence inversion, where the factor practitioners trust most carries the highest outcome-conditioned variance. Most experiments use synthetic data; the DiagonalKernel de-circularization used three real datasets (finding the DK advantage is not scale-robust), and FX-1-PROXY-REAL characterized the distribution gap using 2,430 real IOC records. The production control plane is detailed in §10–§11.

**Keywords:** graph-native reasoning, distance-kernel attention, profile-based scoring, compiled ontologies, cross-graph attention, asymmetric learning, conservation law, re-convergence theorem, online learning, judgment memory, signal-confidence inversion, cognitive architectures, agent memory, characterized negative, enterprise AI

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

**From recall to judgment quality.** Cognitive architectures for language agents (CoALA) [33] define three memory types: episodic (what happened), semantic (what is true), and procedural (how to act). Every agent memory system — Mem0 [34], Zep [35], MAGMA [36] — implements variations of these three. All solve the same problem: how does a stateless agent remember things across sessions? Our framework addresses a structurally different problem: how does decision quality compound across verified outcomes? The centroid geometry, noise fingerprint (per-factor σ from outcome-conditioned variance), and conservation law constitute a fourth memory type — judgment memory — that measures not what happened or what is true, but how WELL decisions are made and WHERE they are noise. In empirical deployment, episodic, semantic, and procedural memory can all confirm a systematically incorrect decision (the trusted-source auto-approve pattern in SOC data) that only judgment memory detects, because only judgment memory decomposes decision quality by factor against verified outcomes. We term this structural pattern signal-confidence inversion: the factor practitioners report highest confidence in is the factor with highest outcome-conditioned variance (σ). This appears in our domain-informed SOC factor design (device_trust σ=0.28, weight 6%), calibrated from security-domain expertise rather than live analyst decision logs (production-log validation is pending pilot deployment), with consistent results in calibrated synthetic deployments across three additional domains.

**The economic framing.** The three advances above carry a direct financial implication. Enterprise AI that does not compound is operating expense — it delivers the same capability forever, regardless of deployment duration. Enterprise AI that does compound is capital infrastructure — it appreciates with use, and the accumulated judgment is an institutional asset that survives model transitions. The kernel choice and the learning dynamics are the architectural decisions that determine which side of that line a system falls on. This paper measures the kernel choice (36.89pp, §2.2/§5.2) and the learning dynamics (13–27pp degradation prevented, §3.1). A third candidate decision — per-factor kernel weighting — was investigated and is reported as a characterized negative (§5.2). Downstream sections measure the compounding exponent γ directly; this paper provides the analytical floor via the Re-Convergence Theorem (§4.6).

[FIGURE 1 | eq_rosetta_stone.png | NBP | The Rosetta Stone: Transformers ↔ Cross-Graph Attention — side-by-side correspondence showing Q/K/V mapping to f/W/outcomes at Level 1, E_i/E_j/V_j at Level 2, and multi-head at Level 3. | §1 | Reusable from CGA Math blog CI-05]

## **1.2 Contributions**

Our principal contributions are:

- **Empirical demonstration that the similarity kernel is the highest-leverage design decision for scoring on bounded features.** L2 achieves 97.89% where dot product achieves 61.00% on identical data — a 36.89pp gap from changing one operation (EXP-C1).

- **A three-level framework connecting enterprise decision-making to transformer attention.** The correspondence is exact at Level 2 (cross-graph discovery), structural at Levels 1 and 3.

- **The compiled ontology architecture.** Domain expert knowledge compiles into readable centroid vectors — auditable, revisable without retraining, immediately operational (97.89% on Day 1 centroidal synthetic; 90.6% on realistic data with A=4).

- **Super-quadratic discovery scaling (information-gain compounding).** D(n) ∝ n^{2.11}, 95% CI [2.09, 2.14], R² = 0.9999 across n = 2–15 domains (V1A, simulation). The near-perfect R² reflects fit to the discovery-cascade model; production validation is EXP-G1 (pending). Distinct from *operational* compounding (deployment quality×scope, a bounded onboarding effect reported in the §10–§11).

- **An original finding on frontier LLM reasoning.** Three frontier models available at the time of the original diagnosis (GPT-5, Claude Opus, Grok) correctly diagnosed the 49% accuracy failure but unanimously prescribed an intervention adding 0.01pp. The correct fix added 36.89pp. A complementary protocol — analytical derivation by LLMs, verification by independent four-judge panels — was used for the April 2026 math polls and worked cleanly.

- **A complete ~194-experiment record** — 53 primary experiments plus sub-experiments from two multi-cell factorials totaling 1890 cells — with all code and data publicly available at https://github.com/ArindamBanerji/cross-graph-experiments.

- **DiagonalKernel — preprocessing-dependent, not a safe default.** On synthetic heterogeneous data, per-factor 1/σ² weighting appeared to add up to +13.2pp over L2 (V-MV-KERNEL-HET, 390 cells) with a monotone NR curve to +7.67pp (UNI-DK-01 v5.3, 1500 cells). On five real UCI datasets under three preprocessing conventions (DK-VERIFY, 300+ cells, 50-seed confirmations), the advantage is preprocessing-dependent: some cells positive (Bank Marketing min-max: +10.0pp, stable at 50 seeds), others negative (Credit robust: −0.8pp). The mechanism: preprocessing changes which features receive high DK weight, and whether those features are informative is dataset-specific. No general predictor was established (best correlate: effective dimensionality, r = −0.51, 60% leave-one-out sign prediction). We report DiagonalKernel as a deployment-specific option requiring per-deployment validation (§5.2) and retain L2 as the safe production default.

- **Asymmetric learning with principled derivation and conservation guarantee.** η_override = 0.01 (5× attenuation) prevents 13–27pp centroid degradation. The ratio is derived from worst-case analyst quality: η_override = η_confirm · (2q̄_worst − 1) with q̄_worst = 0.60 from 24-persona stress testing — validated by the April 16, 2026 four-judge math poll (GPT-4.1 / Claude Opus 4.7 / Grok 3 / Gemini 1.5 Pro). A conservation law α·q·V ≥ θ_min (α = cumulative category coverage; θ_min = 23.53/(α·V), an empirically calibrated cold-start interlock that tightens from ≈0.357 to ≈0.118 as coverage matures) ensures the two-level learning system compounds rather than conflicts, with q = rolling verified accuracy over the last 400 decisions (SE 3.6pp at n≈100 verified samples).

- **Re-Convergence Theorem (new contribution).** γ = N_half,1 / N_half,2 > 1 if and only if ε_firm > ε_firm★ ≈ 0.125, for category-sparse disruption with warm-started centroids. Four structural proof paths confirmed across two four-judge math polls (April 8 and April 16, 2026): (1) geometric, (2) dimensional, (3) η₋ trap avoidance, (4) centroid-distance (v7 addition; Grok 3 primary). Binary simulation confirmed both directions (ε_sim = 0.05: γ = 0.714 < 1; ε_sim = 0.20: γ = 1.033 > 1). Conditions hold in every deployment studied (ε_firm ∈ [0.15, 0.40]).

- **The two-engine separation (σ ⊥ μ) (new contribution).** The expected centroid update E[Δμ] = η·(GT − μ) is exactly σ-independent under unbiased labels: the depth engine (learning moves centroid position μ toward ground truth) and the breadth engine (enrichment reduces observation noise σ) are independent to first order. The coupling runs through a boundary-mislabeling channel, ρ_eff = 2·Φ(−s / 2σ)²·(s / ε_firm), which is ~1% at production parameters (§3.1).

- **Judgment memory — a fourth cognitive architecture type.** The centroid geometry, per-factor σ (noise fingerprint), and conservation law constitute a memory type not addressed by the CoALA framework [33] or its implementations [34-36]: judgment memory stores verified decision quality decomposed by factor, compounds with use, and produces safety proofs (conservation law) that no combination of episodic, semantic, or procedural memory can derive. Signal-confidence inversion — where the factor with highest practitioner confidence has the highest outcome-conditioned variance — is detectable only through this memory type.

- **A synthetic-data identifiability guardrail (methodological contribution).** When an LLM-persona generates synthetic decisions to validate a learning claim, its competence prior dominates the decision stream — the result measures the simulator, not the system. This is an identifiability constraint, not a prompt-engineering gap; oracle separation (LLMs generate inputs, a mathematical oracle labels correctness) resolves it, and the K1–K4 taxonomy marks which validation tiers can support magnitude claims (§4.7).

| **Finding** | **Number** | **Condition** | **Experiment** |
| --- | --- | --- | --- |
| Kernel gap | +36.89pp (61.0% → 97.89%) | Identical data, identical profiles | EXP-C1 |
| Zero-learning accuracy | 97.89% | Expert profiles, no training data | EXP-C1 |
| Frozen scorer (A=4) | 90.6% | Expert prior, realistic factors | SHIFT-2 + A=4 |
| Discovery performance | 111× above random | Cross-graph entity relationships | EXP-2 |
| Scaling exponent | b = 2.11 (CI [2.09, 2.14]) | 11-point log-log fit, n = 2–15 | V1A |
| Calibration (L2) | ECE = 0.036 at τ = 0.1 | Confidence ≈ accuracy | V3B |
| Noise robustness | 0.2pp drop at 30% oracle error | Tolerates noisy feedback | EXP-B1 |
| Realistic deployment | 71.7% → 78.9% | 50-seed, noisy factors, 1K decisions | V3A |
| Asymmetric η prevents degradation | 13–27pp saved | q̄=0.60–0.70 analyst quality | B5B-PROXY |
| η_override derivation (v7) | η_confirm · (2q̄_worst − 1) = 0.01 | q̄_worst = 0.60 | Four-judge, Apr 16 |
| Conservation law | θ_min = 23.53/(α·V); α = category coverage | 0.357 (cold start, α=0.33) → 0.118 (steady, α=1.0), V=200 | Three-judge validated (form) |
| Conservation q (v7 operational) | Rolling verified accuracy / 400 decisions | SE ≈ 3.6pp | SOC-Q1 closure Apr 19 |
| Off-diagonal correlations | <1pp | Both SOC and S2P | V-HC-SHRINKAGE |
| Re-convergence theorem (v7) | γ > 1 ⇔ ε_firm > 0.125 | Four structural proof paths | Four-judge × 2 polls |
| Referral rules | 72.7% DR, 12% FPR | Policy-based VETO | EXP-REFER-LAYERED |
| Graph enrichment σ reduction | 23–46% (threat_intel, data_sensitivity) | Healthcare SOC, 90-day enrichment | V-CGA-FROZEN v3 |
| Graph enrichment accuracy gain | +5.0pp Day-1 accuracy | kernel-independent; rate-null (σ⊥μ signature) | V-CGA-FROZEN v3 |
| Centroid-mean transfer | ~2–7× warm-start acceleration, conservation-mediated; content transfer not demonstrated; K19 +28pp not reproduced | vanishes with conservation off (warm ≈ cold) | E-NEW-5 (v4.3/v5.1) |

*Table: Key results. Most experiments use synthetic data (FX-1-PROXY-REAL used 2,430 real IOC records; the DiagonalKernel de-circularization used three real datasets). The L2-vs-dot result (EXP-C1, +36.89pp) is a surviving primary finding.*

**DiagonalKernel — preprocessing-dependent on real data (§5.2).** The following DiagonalKernel measurements were obtained on synthetic data with known per-factor σ. A three-stage de-circularization (H-TRUST 180 cells + DK-VERIFY 300+ cells + DK-VERIFY-SUB 500+ cells) found the advantage is preprocessing-dependent: some dataset/convention cells positive (Bank Marketing min-max: +10.0pp), others negative (Credit robust: −0.8pp). The synthetic heterogeneity mechanism does not operate on real data (slopes flat). No general predictor was established. These synthetic measurements are retained as experimental record; the deployment recommendation is per-deployment validation, not universal application.

| Measurement (synthetic) | Value | Condition | Source |
|---|---|---|---|
| DiagonalKernel (SOC peak) | +13.2pp over L2 | Heterogeneous noise | V-MV-KERNEL-HET |
| DiagonalKernel (S2P) | +6.8pp over L2 | Heterogeneous noise | V-MV-KERNEL-HET |
| DiagonalKernel characterized | 0.00 → +7.67pp asymptotic | NR=1→5, mean-σ=0.175, 1500 cells | UNI-DK-01 v5.3 |

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

[EQUATION GRAPHIC 1 | p1_eqb_attention_mechanisms.png | Blog reuse | Three boxed equations (Eq. 1 scaled dot product, Eq. 2 cosine, Eq. 3 general kernel form) with section labels showing the progression from Vaswani through our kernel formulation. | §2.1 | Reusable from CGA Math blog §2]

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

[FIGURE 2 | eq_profilescorer.png | NBP | Level 1 Scoring Pipeline. Alert → Category Router → ProfileScorer (Eq. 4-final) → Score → Action → Outcome → Centroid Update (Eq. 4b-final) → feedback loop. | §3.1 | Reusable from paper_figures]

### **Why L2 Fixes Everything: A Concrete Example**

Consider a SOC alert with f = [0.95, 0.30, 0.10, 0.70, 0.90, 0.85] (travel_match, asset_criticality, threat_intel, time_anomaly, device_trust, pattern_history). The false_positive_close centroid for credential_access is μ = [0.90, 0.12, 0.08, 0.35, 0.88, 0.82]. Under dot product, device_trust dominates (0.90 × 0.88 = 0.792) despite carrying almost no discriminative information. Under L2, device_trust contributes (0.90 − 0.88)² = 0.0004 (near zero) while asset_criticality contributes (0.30 − 0.12)² = 0.0324 — 80× more, correctly weighted by discriminative deviation. Total L2 distance 0.1591 (nearest); P(false_positive_close) = 0.938.

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

q is operationalized as rolling verified accuracy over 400 decisions rather than per-decision confidence. AMBER auto-pause freezes learning when the invariant is breached — a state-level trigger using the same rolling accuracy signal.

**Signal-confidence inversion.** An empirical finding from the SOC deployment: the factor that analysts report highest confidence in (device_trust, mean confidence 4.2/5 in analyst surveys) has the highest outcome-conditioned variance (σ=0.28, weight 6% in the asymmetric-learning-rate-weighted fingerprint). Conversely, threat_intel — which analysts rate as routine and low-effort — has σ=0.07 (weight 100%). This inversion is structurally invisible to systems that store decision history (episodic memory) or domain knowledge (semantic memory), because it requires computing per-factor σ from verified outcomes across hundreds of decisions — a computation that only the centroid geometry and outcome-conditioned variance decomposition across verified decisions produce. Consistent patterns appear in calibrated synthetic deployments across three additional domains (trading: conviction σ=0.28/weight 12% vs research σ=0.06/weight 95%; purchasing: weather σ=0.26/weight 14% vs waste_history σ=0.08/weight 92%; data engineering: recurrence σ=0.235/weight 52% vs freshness σ=0.170/weight 100%). Universal validation requires production-verified decision data from each domain (EXP-G1 priority).

Two independent LLM-judge panels have validated this line of reasoning. A three-judge panel (GPT-4o / Claude Opus / Gemini, March 2026) validated the original conservation-law formulation. Two four-judge math polls (GPT-4.1 / Claude Opus 4.7 / Grok 3 / Gemini 1.5 Pro, April 8 and April 16, 2026) validated the Re-Convergence Theorem (§4.6) and the η_override derivation respectively. The v7 operational definition of q preserves all conservation-law guarantees (§10–§11).

[FIGURE 3 | nbp_asymmetric_eta.png | Chart | Asymmetric η trajectories: overlayed time series of centroid distance under symmetric η vs asymmetric η_override=0.01, 13–27pp degradation prevented. v7 annotation: add "η_override = η_confirm · (2q̄_worst − 1) = 0.01 (derived, four-judge Apr 16 2026)". SHARED with §10 Fig 10. | §3.1 | Existing paper_figures; needs v7 annotation]

[FIGURE 4 | nbp_conservation_timeline.png | NBP | Conservation law timeline: α·q·V signal over 180 days with GREEN/AMBER zones, θ_min floor line (lifecycle-dependent: 0.357 cold start → 0.118 steady), and AMBER auto-pause event annotation. v7.6 annotation: "α = cumulative category coverage; q = rolling verified accuracy over 400 decisions. Steady-state protector is the 0.7×-baseline relative trigger; θ_min is the cold-start interlock." SHARED with §10 Fig 11. | §3.1 | Existing; needs v7.6 annotation]

The compounding claim, formally: the accumulation of novel verified decisions improves the scorer's centroid geometry, and the switching cost deepens as the firm-specific centroid tensor accumulates verified-outcome structure that a competitor starting from generic priors does not have.

### **Deployment status: the conservation law in production**

The conservation law is deployed, not proposed. The invariant α·q·V ≥ θ_min — with AMBER auto-pause when α·q·V falls below 0.7× its rolling baseline — runs across all five production copilots (SOC, source-to-pay, trading, purchasing, and data operations) on a shared control plane (MAP v5.229, 9,826 tests passing, zero failures). Deployment is characterized, not merely live: a campaign-holdout harness assigns treatment/control at the decision-node level by deterministic SHA-256 hash and logs both arms for auditable comparison. The holdout infrastructure is deployed and validated (pipeline validation via oracle separation); real measurement awaits pilot deployment with operational analysts (PILOT_GATED). An adversarial stress test (EXP-OP2, N=100) measures 35% non-recovery under sustained poisoning (95% CI 29–48%), with a 0.15pp poisoning ceiling at A=4 (EXP-S2-REPRO). This is the highest evidence tier in the paper — a runtime safety mechanism deployed and characterized in production rather than simulated. Full control-plane detail is in §10; production characterization is in §11.

### **Calibration and Two Accuracy Regimes**

For the L2 kernel at τ = 0.25 (previous default): ECE = 0.190. At τ = 0.1: ECE = 0.036 — competitive with post-hoc temperature scaling [Guo et al., 2017] while requiring no calibration data (V3B).

Two accuracy regimes: centroidal synthetic (perfect factor computation, ground-truth-aligned centroids: 97.89%) and deployment-representative realistic (noisy factors, imperfect routing, 50-seed simulation: 71.7% → 78.9% over 1,000 decisions). The gap is the deployment noise floor.

### **Two-Engine Separation: σ ⊥ μ**

The centroid tensor carries two geometric properties that drive decision quality: its position μ (how close centroids sit to ground truth) and its observation resolution σ (the per-factor noise with which factor vectors are measured). Two mechanisms improve these independently. The *depth engine* — online learning from verified outcomes (§4.6) — moves μ toward ground truth. The *breadth engine* — graph enrichment (§5.2) — reduces σ, sharpening day-zero class separation. These engines are independent to first order: enrichment lifts the decision floor without changing the convergence rate, learning bends the convergence curve without depending on σ, and the coupling between them is bounded and characterized.

**The expected update is σ-independent.** On a correctly labeled decision for action a, the confirm-path update (Eq. 4b-final) is Δμ = η·(f − μ[c,a,:]). The factor vector is drawn from the true centroid with zero-mean noise, f = GT[c,a,:] + ε, where E[ε] = 0 and Var(ε_j) = σ². Taking the expectation over f conditional on a correct label, E[Δμ] = η·(E[f] − μ[c,a,:]) = η·(GT[c,a,:] − μ[c,a,:]), since E[ε] = 0 under unbiased labels. The expected centroid movement depends only on the mismatch (GT − μ) and the rate η — it contains no σ. Reducing σ (enrichment) does not change the direction or magnitude of the expected trajectory; it changes decision accuracy only through improved class separation.

**The coupling runs through a mislabeling channel.** The unbiased-label assumption fails near decision boundaries. A vector drawn from GT[a] but pushed by noise across the midpoint to a neighbor GT[a′] is mislabeled, and the mislabeled update pulls μ[a] toward GT[a′] — the wrong direction. For a pairwise separation s = ‖GT[a] − GT[a′]‖, the projected boundary noise has standard deviation σ, so the per-boundary mislabeling probability is p_mis = Φ(−s / 2σ). A fraction p_mis of vectors labeled a are then from the neighbor, biasing the expectation by p_mis·(GT[a′] − GT[a]), so E[Δμ[a]] = η·(GT[a] − μ[a]) + η·p_mis·(GT[a′] − GT[a]). The second term is the σ-dependent coupling. Relative to the convergence term, and weighting by the fraction of decisions that fall near a boundary (f_boundary ≈ 2·p_mis), the effective coupling is ρ_eff = 2·Φ(−s / 2σ)²·(s / ε_firm), where ε_firm = ‖GT[a] − μ[a]‖ is the initial mismatch.

**At production parameters the coupling is ~1%.** For the SOC deployment (σ = 0.08, minimum pairwise separation s ≈ 0.25, ε_firm ∈ [0.15, 0.40]), the per-boundary mislabeling rate is p_mis = Φ(−1.56) ≈ 0.059 and the effective coupling at mid-range ε_firm = 0.20 is ρ_eff ≈ 0.9% (≈1.2% at the worst-case ε_firm = 0.15). The coupling grows with σ but stays modest across the operating range:

| Per-factor σ | p_mis | ρ_eff (ε_firm = 0.20) | Status |
| --- | --- | --- | --- |
| 0.04 (enriched) | 0.001 | < 0.001% | Negligible |
| 0.08 (production) | 0.059 | ~0.9% | Production operating point |
| 0.12 (50% degraded) | 0.149 | ~5.5% | Moderate |
| 0.16 (100% degraded) | 0.217 | ~12% | High |

Coupling is ~1% at production parameters (σ = 0.08). At 50% σ degradation (σ = 0.12), coupling reaches ~5.5% — still small relative to the floor-lift effect. At σ = 0.16 (twice production noise, beyond realistic operating conditions), coupling reaches ~12% and the first-order separation begins to weaken. The two-engine claim rests on the production operating point, not the degraded regime.

**Empirical signature.** V-CGA-FROZEN v3 (§5.2) exhibits the predicted pattern directly: enrichment lifts Day-1 accuracy +5.0pp (p < 0.0001) with no change in convergence rate (d = −0.010, p = 0.873, a definitive null). Floor lifts, rate holds — the σ ⊥ μ signature. The investment implication carries a scope condition: the depth and breadth engines can be resourced independently except where operating noise approaches the decision-boundary scale, at which point the mislabeling channel couples them.

---

## **3.2 Level 2: Cross-Graph Discovery as Cross-Attention**

For each knowledge domain G_i, define an entity embedding matrix E_i ∈ ℝ^{m_i × d} [Eq. 5]. For source domain G_i and target domain G_j:

[EQUATION GRAPHIC 4 | eq6_cross_attention.png | NEW v7 | Eq. 6: CrossAttention(G_i, G_j) = softmax(E_i · E_j^T / √d) · V_j — hero equation with three boxed sections "Query E_i" (blue), "Key E_j" (green), "Value V_j" (purple); subtitle "exact instance of Eq. 1". | §3.2 | New or reuse Blog Part 1 rendering]

This is an exact instance of Eq. 1. E_i are queries, E_j are keys, V_j are values. Normalization is a structural prerequisite: without z-score + L2 normalization, cross-attention finds nothing (0× above random). With both: 111× above random (EXP-2). After discovery sweeps:

[EQUATION GRAPHIC 5 | eq12_residual_enrichment.png | Blog reuse | Eq. 12: E_i^{enriched} = Normalize(E_i + Σ_{j≠i} CrossAttention(G_i, G_j)) — rendered with explicit "residual (+)" annotation and "Normalize" gate boxed; caption "additive enrichment; original E_i preserved." | §3.2 | Reusable from Blog Part 1]

[FIGURE 5 | eq_singapore.png | NBP | The Singapore Discovery. A threat intelligence feed reports a campaign targeting Singapore authentication servers. Cross-attention discovers the connection to an 8-month auto-close pattern — the canonical worked example of cross-graph discovery. | §3.2 | Reusable from CGA Math blog CI-04]

## **3.3 Level 3: Multi-Domain Attention**

For n knowledge domains, multi-domain attention processes all domain pairs:

[EQUATION GRAPHIC 6 | eq8_multi_domain.png | NEW v7 | Eq. 8: MultiDomainAttention(G) = Aggregate({head_{i,j}}), with head_{i,j} = CrossAttention(G_i, G_j) for all i < j — two-line typeset equation; subtitle "n(n−1)/2 heads". | §3.3 | New; small equation graphic]

[EQUATION GRAPHIC 7 | eq10_combinatorial.png | NEW v7 | Eq. 10: Total = [n(n−1)/2] × m² — with annotation "15 heads at n=6, 21 at n=7". | §3.3 | New; may combine with Figure 6]

Each new domain adds n−1 new discovery categories. With 6 domains, 15 heads evaluate 3.75M pairwise scores per sweep, completing in under 2 seconds on commodity hardware.

[FIGURE 6 | eq_combinatorial.png | NBP | Combinatorial Growth: n=2 (1 pair), n=4 (6 pairs), n=6 (15 pairs) — three panels showing unique pair count growing super-linearly with n. | §3.3 | Reusable from CGA Math blog GM-02]

# **4. Architecture, Scaling, and Correspondence**

## **4.1 Compiled Ontologies**

Profile centroids are compiled from expert knowledge. The statement "for credential_access alerts, a correctly closed false positive typically has high device trust and high pattern history" compiles into:

[EQUATION GRAPHIC 8 | eq_compiled_centroid.png | NEW v7 | Worked centroid vector: μ[credential_access, false_positive_close, :] = [0.90, 0.12, 0.08, 0.35, 0.88, 0.82] with per-index factor-name annotations. Small graphic; can inline as styled code block. | §4.1 | New, optional]

The mathematical engine is domain-agnostic because domain knowledge is compiled into the centroid tensor's geometry. The same equations govern SOC alert triage, procurement approval, and financial compliance — only the centroid values change.

[FIGURE 7 | cga_levels_stack.png | NBP | **Five CGA Levels** (v7.1 rename, formerly "Five Layers"): the three mathematical levels (Level 1 ProfileScorer, Level 2 Cross-Graph Discovery, Level 3 Multi-Domain Attention) stacked above two substrate layers (UCL context substrate, FactorComputers). Caption: "Distinct from the production 4-layer architecture — UCL, Agent Engineering, ACCP, Domain Copilots — in §10.1 Fig 10; this paper's five-level decomposition groups substrate + math layers, while the four-layer decomposition (§10) groups orchestration concerns." | §4.1 | Reusable from CGA Math blog with updated caption]

## **4.2 Properties from Attention Theory**

Three structural properties transfer from transformer attention:

**Quadratic interaction space.** Discovery capacity scales as n(n−1)/2 domain pairs × m² entity interactions per pair. Empirically, D(n) ∝ n^{2.11} (V1A), with the super-quadratic exponent arising from the discovery cascade.

[FIGURE 8 | eq_scaling.png | Chart | Discovery Scaling. Log-log scatter, 11 points (n = 2–15). b = 2.11, CI [2.09, 2.14], R² = 0.9999. Scatter with fitted line and CI band. | §4.2 | Reusable from arxiv v4 paper_figures / V1A]

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
| Kernel | Dot product | L2 distance | Dot product | Dot product |
| Scaling | 1/√d_k | 1/τ, τ = 0.1 | 1/√d | 1/√d |
| Multi-head | h learned projections | n_c categories (MoE) | — | n(n−1)/2 domain pairs |
| Output | Weighted value sum | Argmax over n_a actions (v7: confidence via rolling accuracy / softmax entropy) | Enriched representations | Aggregated discoveries |
| Residual | x + Attention(x) | Centroid pull/push + clip | E_i + CrossAttn + Normalize | Preserved + Normalize |
| Correspondence | — | Partial | Exact (Eq. 6 = Eq. 1) | Structural |

*Table 1: Transformer ↔ CGA correspondence.*

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

**Two-arm calibrated characterization.** A two-arm parametric re-run tested both the bare update rule (Arm B) and the production ProfileScorer logic (Arm A) in a calibrated apparatus with production-like oracle separation. Arm B confirms the theorem (γ > 1 above ε★). Arm A also re-converges: γ > 1 across all six cells, sign-consistent and at least as fast as Arm B in every paired cell, with the conservation law fully engaged (100% engaged, 0% spuriously paused). The dimensional lower bound γ ≥ 4.6 (proof path 2) is an idealized limit not reached under production scorer dynamics due to η asymmetry, conservation gating, and centroid clipping; the realized acceleration is smaller but sign-consistent.

**A prior finding of γ < 1 was retracted as a calibration artifact.** An earlier apparatus reported that the production ProfileScorer did not re-converge (γ < 1 at ε=0.35) and that three policy variants failed to recover it. That apparatus operated at chance accuracy, which left the conservation law trivially always-paused — so the apparent gap was an artifact of the apparatus, not a property of the scorer. Under production-like separation the gap does not appear (Arm A above). Scope: conservation was engaged but never stressed — the disruption in these runs stayed within the accuracy margin, so the result supports that conservation does not block re-convergence when disruption stays within that margin; it does not test the floor-breaching regime, which remains a separate, untested safety question. Evidence tier: this is production-scorer logic re-converging in a calibrated synthetic apparatus, not a production-verified deployment result.

**Business implication — institutional memory as asset, not liability.** γ > 1 means that when the threat landscape shifts, accumulated institutional memory speeds re-calibration rather than slowing it. This inverts the intuition that "stale models need full retraining" — the theorem formalizes the specific condition (category-sparse disruption, warm-started centroids, ε_firm > 0.125) under which institutional memory is a genuine asset against environmental change rather than a liability, and the calibrated re-run supports that the production scorer logic realizes this acceleration rather than stalling. The practical implication holds: for a CISO evaluating "should we rebuild after the campaign?", the answer remains no — existing centroid calibration is an asset to preserve.

[FIGURE 9 | gamma_theorem_regions.png | NEW v7 | Re-Convergence phase diagram: x-axis ε_firm [0, 0.40]; vertical line at threshold ε_firm★ ≈ 0.125; shaded regions "γ < 1 (slower)" and "γ > 1 (faster)"; two simulation points (ε=0.05 → γ=0.714; ε=0.20 → γ=1.033); shaded band "production range ε_firm ∈ [0.15, 0.40]" within γ > 1 region. Caption: four structural proof paths; EXP-G1 pending. | §4.6 | New graphic]

## **4.7 Methodological Guardrails**

**Synthetic-data identifiability guardrail.** The experimental program identified an identifiability constraint on synthetic validation that we report as a methodological contribution. When an LLM-persona generates synthetic analyst decisions to validate a learning or behavioral claim, three independent frontier models (GPT-4.1, Claude Opus 4.7, Grok 3) diagnosed the same structural failure: the LLM's competence prior — its built-in tendency to produce reasonable decisions — dominates the synthetic decision stream, making the synthetic agent's behavior a measurement of the *simulator's* capabilities rather than the *system's* learning effect. This is an identifiability result, not a prompt-engineering gap: no amount of persona refinement resolves it, because the LLM's training distribution is the dominant data-generating mechanism regardless of the persona specification.

The resolution is oracle separation: LLMs generate factor vectors (exercising their domain knowledge of what realistic alerts look like), while a mathematical oracle assigns correctness labels (using ground-truth centroid proximity, independent of any LLM competence prior). This separates input generation, where LLMs excel at realistic scenario structure, from the correctness signal, where LLMs introduce an unresolvable confound. The K1-K4 taxonomy makes this operational:

- **K1 (oracle-behavioral):** a parametric oracle generates controlled behavioral responses — validates pipeline mechanics (e.g., the campaign-holdout AnalystOracle).
- **K2 (factor-vector oracle):** LLMs generate inputs, a mathematical oracle labels correctness — validates mechanism (e.g., the γ-theorem oracle separation).
- **K3 (demo-population):** an LLM-persona generates both inputs and decisions — validates nothing about learning effects; useful only for demo realism.
- **K4 (scraped-external):** real external data incorporated as enrichment — validates context claims.

The bright line: K1 and K2 validate mechanism and pipeline, never magnitude; K3 must not be cited as evidence for any learning or behavioral claim; and only real operational data validates magnitude claims (the EXP-G1 gate). This identifiability result applies to any AI system that claims to learn from user behavior and attempts to validate that claim with synthetic users. We report it as a methodological guardrail alongside the experimental results it motivated.

---

## **4.8 The Governed Second Derivative: When Learning Compounds**

The Re-Convergence Theorem (§4.6) proves that after a disruption, re-convergence is faster than initial convergence (γ > 1). This is a first-order acceleration result — a property of the accumulated state. A second-order question remains: does the *rate* of improvement itself improve during steady-state operation? The distinction is precise:

- **Online learning (first order):** dA/dt > 0. Decision accuracy improves with verified decisions. Proved: V3A (71.7% → 78.9% over 1,000 decisions), conservation-bounded.
- **Compounding (second order):** d²A/dt² > 0. The rate of improvement itself increases — the system learns faster *because* it has already learned.

**Measured baseline: logistic convergence with early positive curvature.** A 2,000-decision experiment (EXP-RL-DIRECT, 3 seeds, calibrated E-NEW-4 apparatus) fitted the learning curve to logistic, linear, and power-law models. The logistic fit (R² ≈ 0.88) is the best model for both uniform and directed arms, with an inflection point at ~327–361 decisions. The numerical second derivative d²q/dt² is positive at t=100 (~5.3×10⁻⁷) and t=250 (~2.0×10⁻⁷), and negative by t=500. This means:

- The centroid update rule with conservation produces an S-shaped learning curve: early acceleration (d²A/dt² > 0 for t < ~330 decisions), near-linear middle, and saturation.
- This early positive curvature is a property of the geometry of prototype convergence — early decisions move centroids rapidly because they are far from ground truth; later decisions produce smaller moves as centroids approach their targets.
- This is the baseline curvature against which any additional compounding mechanism must be measured.

**A characterized negative: scorer-integrated directed learning.** Four experiments tested whether RL-derived signals, routed into the scorer's learning rate, could improve convergence over uniform η. (1) EXP-RL-DIRECT allocated η proportionally to per-category accuracy gap (first-order, 3 α variants): negative — uniform at least as good (1/3 seeds faster, 2/3 slower). (2) EXP-RL-DIRECT-4 attempted per-category improvement rate (second-order): apparatus SNR too low to allocate reliably. (3) EXP-RL-SCORER tested three materially different RL strategies — EMA-smoothed improvement rate, Thompson sampling from verified-outcome Beta posteriors, and a hybrid gap-to-target warmup plus EMA momentum — across 3 seeds × 2,000 decisions each: none beat uniform on both decisions-to-competence and AUT_ACC in any seed. Thompson (the best directed variant) improved mean AUT_ACC by 0.4% (1,351 vs 1,357) — within noise. Curvature was not stronger for any directed arm.

We report this as a definitively characterized negative: uniform scorer learning is robust for this prototype-convergence geometry, and RL reward signals do not improve centroid learning when routed into η — not via accuracy gap, not via improvement rate, not via Thompson sampling, not via hybrid warmup. This closes the scorer-integrated RL line and confirms the sidecar as the right architecture for RL.

**The mechanism: a procedural-memory sidecar for runtime evolution.** The DIRECT-1 negative confirms that the production architecture's separation of judgment from learning is correct — the RL/evolution system operates as a procedural-memory sidecar, not as a scoring modifier. The production system separates judgment from learning with four architectural guarantees (G1–G4). The judgment core selects the live action from centroid distance and softmax — it is the authoritative decision path (G1: action selection is not reward-maximizing). RL and evolution compute reward after verified outcomes, explore variants in shadow, and gate promotion. They do not replace the centroid-selected action.

The architecture (`copilot_sdk/rl/exploration.py`, `copilot_sdk/evolution/prompt_evolver.py`):

```
verified input → scorer → centroid distance + softmax → recommended action
                        |
                        +→ learn() → reward / exploration / credit sidecar
                                        |
                                        +→ variant proposal → shadow test
                                                           → conservation gate
                                                           → promotion
```

1. **Two learning paths, one judgment core.** The centroid update rule (§3.1) learns from verified outcomes by moving prototype positions — this is the depth engine. The evolution sidecar learns from verified outcomes by proposing, shadow-testing, and promoting operational variants (prompts, scoring weights, factor configurations) — this is the breadth engine's operational complement. Both are gated by conservation; neither replaces the centroid-selected action on a live decision.

2. **Conservation-bounded evolution.** The promotion gate requires: (a) the conservation state provider returns GREEN (fail-closed: UNKNOWN, AMBER, RED, stale, missing, or provider-error states block promotion — G2); (b) the shadow variant demonstrates measurable improvement over the active variant with sufficient evidence (5pp default, 10 minimum shadow decisions, variance under cap); (c) the gate is domain-scoped (G4). ConservationBoundedThompson (`copilot_sdk/rl/exploration.py:12-44`) governs the exploration policy; AMBER/RED suppress exploration entirely.

3. **Per-copilot reward functions.** Five domain-specific reward functions (BinaryRewardFunction for SOC, GradedFinancialRewardFunction for S2P and DataOps, PnLRewardFunction for Trading, WasteReductionRewardFunction for Purchasing) compute reward from verified outcomes. Reward clips to [-1, 1] with domain-calibrated penalty ratios (SOC: 20×, S2P: 5×, Trading: 3×, Purchasing: 3×, DataOps: 10×) — asymmetric by design, penalizing false positives/negatives far more than rewarding correct decisions.

4. **G1 boundary: the decision stays nearest-centroid.** The live action is always the centroid-selected action (Eq. 4-final). Exploration proposals route to shadow/learning, never to the live decision. In the strictest configuration (SOC), production exploration is disabled entirely (`RL_EXPLORATION_ENABLED=False`) and regression tests verify no live decision carries `decision_method == "gae_scoring_explored"`. This separation is what allows the system to abstain when it is out of its depth — a property a pure reward-maximizer structurally cannot have.

**The remaining compounding hypothesis.** With scoring-integrated directed learning characterized as a negative, the pathway for d²A/dt² > 0 beyond the logistic baseline narrows to the sidecar's indirect coupling: promoted variants improve the operational context (better prompts → better factor vectors → more informative centroid updates), and this improvement compounds across successive promotions. This is architecturally plausible — each promotion raises the floor from which the next variant is shadow-tested — but it is untested. The pilot measurement (6–12 months, real operational data) remains the arbiter.

**Evidence tier (F-24).** The RL/evolution architecture is **deployed** — the procedural-memory sidecar runs across all five copilots with domain-specific reward functions, conservation-bounded promotion, and the G1–G4 guarantees verified in the test matrix (T-STARTUP through T-G1-SOC-AUDIT). The baseline logistic curvature (d²q/dt² > 0 for t < ~330 decisions) is **measured** (EXP-RL-DIRECT, 3 seeds, calibrated apparatus). Scorer-integrated directed learning is a **definitively characterized negative** (4 experiments: EXP-RL-DIRECT first-order 3 variants, EXP-RL-DIRECT-4 rate signal, EXP-RL-SCORER 3 RL strategies including Thompson sampling — none beat uniform). The sidecar-mediated compounding hypothesis (d²A/dt² > 0 beyond the logistic baseline, driven by variant-evolution coupling) is **not yet measured** — a hypothesis for the pilot.

**What this section does NOT claim.** It does not claim d²A/dt² > 0 beyond the logistic baseline is proved. It does not claim the RL/evolution sidecar is the only pathway to compounding — the Re-Convergence Theorem provides a disruption-response pathway that is independently proved. It reports a measured negative (scoring-integrated directed allocation) alongside a measured positive (logistic baseline curvature), and states precisely what remains open (sidecar-mediated compounding via variant evolution, pilot-arbitrated).

---

# **5. Experimental Validation**

We validated the framework through ~194 experiment entries — 59 primary experiments plus sub-experiments from two multi-cell factorials totaling 1890 cells — across six phases: 4 original (Phase 1, February 2026); 9 bridge (Phase 2, March 2–4) that falsified the published equation; 5 validation (Phase 3, March) responding to independent review; ~89 in Phase 4 (March 14–21) including the 390-cell kernel factorial and deployment-persona validation; Phase 5 (March 23 – April 19) including the 1500-cell UNI-DK-01 v5.3 characterization surface, the MR-COLAB-01 healthcare reproduction, and the SOC-Q1 conservation-law operational-definition adjudication; and Phase 6 (May–August 2026) adding the calibrated two-arm re-convergence re-run, the apparatus positive control, and the cross-deployment transfer decomposition; and Phase 7 (August 2026) adding category-directed learning, σ-directed enrichment, and self-computation experiments. All code publicly available [14].

## **5.1 Setup and Experimental Philosophy**

**Experiments lead the code, not the reverse.** The experimental program is designed to get AHEAD of the production codebase: a theorem-vs-code mismatch is a discovery and a roadmap item, not a mixed result. Experiments may validate mechanisms the code has not yet implemented (self-computation, per-decision abstention), characterize properties the code exhibits but doesn't formalize (logistic curvature, conservation precondition), or definitively close lines the code considered but should not pursue (directed η, σ-directed enrichment). When an experiment gets ahead of the code, the finding becomes an architectural input — the code catches up to the experiment, not the other way around.

**Architectural value drives claims; experiments provide grounding.** The claims in this paper — that graph-native reasoning is a cognitive-architecture transition beyond graph engineering (§7, §8), that judgment memory is a fourth memory type (§7), that the conservation law bounds self-improvement (§3.3), that SituationAnalyzer provides reasoning autonomy (§10.1), that AgentEvolver provides decision autonomy (§10.1) — are architectural claims. They are grounded by experiments but not DERIVED from them. The DiagonalKernel investigation illustrates this clearly: the architectural claim (the graph's decision geometry reshapes from verified outcomes) survived DK's preprocessing-dependent finding unchanged — only the kernel recommendation was refined (from DK-as-default to L2-as-default with DK as a validated-per-deployment option). The characterized negatives (directed η, σ-directed enrichment, independent content transfer) and the DK preprocessing-dependence finding each refined a mechanism without changing the architectural thesis. Experiments that produced negatives were as valuable as positives: each one sharpened what the architecture IS by establishing what it ISN'T.

Synthetic SOC data: 6 factors × 4 actions × 6 alert categories. Profile centroid tensor μ ∈ ℝ^{(6×4×6)} = 144 values. A=4 confirmed by EXP-A4-DIAGONAL: 13pp structural gap between A=4 and A=5, kernel-independent. The `refer_to_analyst` action was removed from the centroid tensor (accessed via policy-based referral rules R1–R7). Static accuracy improved from 80.4% (A=5) to 90.6% (A=4).

~194 experiment entries — 59 primary experiments plus sub-experiments from two multi-cell factorials totaling 1890 cells — across seven phases (February–August 2026), with Phase 7 (August 2026) adding the RL-scorer line closure, self-computation characterization, and SA/AE autonomy validation. All code and data publicly available at https://github.com/ArindamBanerji/cross-graph-experiments.

**Apparatus positive control.** The oracle-separation apparatus used for the re-convergence and enrichment experiments was validated with a positive control: a known all-factor floor lift (per-factor σ 0.08 → 0.04) was injected and the apparatus resolved it cleanly and monotonically — +9.167pp at the weakest tested cut, sign-consistent across three seeds, 6.35× above twice the paired standard deviation, rising monotonically to +26.25pp at deeper cuts. The lens detects broad floor lifts and is characterized for depth/rate work; this establishes that a null from the apparatus reflects absence of effect rather than blindness to it (E-NEW-4).

## **5.2 Key Experiments**

**EXP-C1: Kernel comparison (hero finding).** Dot product: 61.00%. Cosine: 96.42%. L2: 97.89%. The 36.89pp gap from one change — on identical data, identical profiles, zero learning — is the largest single-variable effect in the record.

[FIGURE 10 | eq_three_kernels.png | Chart | Three Kernels, Same Data: Dot (61.0%), Cosine (96.42%), L2 (97.89%). Bar chart with +36.89pp gap annotated between Dot and L2; small +1.47pp annotation between Cosine and L2. | §5.2 | Reusable from arxiv v4 paper_figures]

**EXP-2: Cross-graph discovery.** Security Context (100 entities) × Threat Intelligence (80 entities). With z-score + L2 normalization: F1 = 0.071, 111× above random. Without normalization: F1 = 0.000.

**V1A: Scaling validation.** b = 2.11, 95% CI [2.09, 2.14], R² = 0.9999 across n = 2–15 domains. Excess exponent (0.11) is the empirical signature of the β · R(n, t) second-order term (see §4.4 reconciliation with the n² theoretical floor).

**V3B: Calibration.** ECE = 0.036 at τ = 0.1, versus 0.190 at previous default τ = 0.25 (L2 specifically).

**EXP-B1: Noise robustness.** 0.2pp drop at 30% oracle error — expert initialization provides both accuracy and noise resistance.

**EXP-E2: Scale validation.** Warm/cold gap widens from 8pp to 27pp as the scoring problem grows from 5×5×5 to 20×10×20.

**V-MV-KERNEL-HET: DiagonalKernel factorial (synthetic; did not survive de-circularization).** 390-cell factorial on synthetic data with known σ: +13.2pp on SOC, +6.8pp on S2P, Corr(noise_ratio, advantage) = 0.990. This synthetic advantage did not survive the real-data de-circularization (H-KERNEL, below) and is reported as a characterized negative.

**UNI-DK-01 v5.3: DiagonalKernel controlled characterization (synthetic; did not survive de-circularization).** 1500-cell factorial at fixed mean-σ = 0.175 mapping the synthetic DK-over-L2 curve (0.00pp at NR=1.0 → +7.67pp at NR=5.0). Like the peak factorial, this synthetic curve did not survive the real-data de-circularization (H-KERNEL, below) and is reported as a characterized negative.

**MR-COLAB-01: Healthcare reproduction (synthetic; did not survive de-circularization).** A 50-seed synthetic reproduction at full healthcare noise profile measured a DiagonalKernel advantage over L2. Like the other DiagonalKernel measurements, it did not survive the real-data de-circularization (H-KERNEL, below) and is reported as a characterized negative.

**B5B-PROXY: Asymmetric learning validation.** η_override = 0.01 eliminates 13–27pp centroid degradation. Derived from information-theoretic principles: η_override = η_confirm · (2q̄_worst − 1) with q̄_worst = 0.60 from 24-persona validation (four-judge poll, April 16, 2026).

**V-CGA-FROZEN v3 (N=257, 90% power).** Graph enrichment reduces per-factor σ 23–46% and lifts Day-1 triage accuracy +5.0pp (p<0.0001). The effect is kernel-independent — it does not depend on DiagonalKernel (whose advantage did not survive de-circularization). Enrichment does NOT change centroid convergence rate (d = −0.010, p = 0.873, definitive null) — the floor-lifts / rate-holds signature. The remaining candidate mechanism is improved factor-vector class separation at the centroid level; this is the consistent hypothesis, not an established cause.

**H-KERNEL / DK-VERIFY: DiagonalKernel de-circularization (preprocessing-dependent, not a safe default).** The DiagonalKernel advantage over L2 (V-MV-KERNEL-HET +13.2pp; UNI-DK-01 v5.3 monotone curve to +7.67pp) was established on synthetic data with known per-factor σ. A three-stage verification (H-TRUST original 180 cells, DK-VERIFY reproduction+extension 300+ cells, DK-VERIFY-SUB 500+ cells with 50-seed confirmations) established: (1) the advantage is preprocessing-dependent — the same dataset changes sign under different conventions (Credit: +1.0pp min-max, −0.8pp robust); (2) some datasets show large, stable DK advantage (Bank Marketing min-max: +10.0pp, 50/50 seeds positive, not driven by a single feature); (3) the synthetic heterogeneity mechanism (advantage scales monotonically with NR) does not operate on real data — slopes are flat on all four admissible datasets; (4) no general predictor of DK advantage was established (best: effective dimensionality r = −0.51, conditional rule 60% leave-one-out accuracy); (5) the GAE product scorer and the fresh de-circularized scorer agree exactly. DiagonalKernel is a deployment-specific option whose benefit must be validated under the target preprocessing convention and held-out data; it is not a safe default. L2 is retained as the production kernel because its advantage over dot product (36.89pp, EXP-C1) is preprocessing-independent.

**γ-theorem simulation validation.** Oracle separation (April 2026) confirmed binary prediction in both directions. Four structural proof paths confirmed across two four-judge math polls (April 8 paths 1–3; April 16 path 4). Empirical γ measurement via EXP-G1 in progress.

**H-CURVE-CALIB: Calibrated two-arm re-convergence re-run.** A two-arm parametric re-run in a calibrated apparatus with production-like oracle separation confirmed the theorem for the bare update rule (Arm B) and showed the production ProfileScorer logic (Arm A) re-converges: γ > 1 across all six cells, sign-consistent and at least as fast as Arm B in every paired cell, with the conservation law fully engaged (100% engaged, 0% spuriously paused). A prior γ < 1 finding was retracted as a calibration artifact — the earlier apparatus operated at chance accuracy, leaving conservation trivially always-paused. Scope: conservation was engaged but not stressed (disruption stayed within the accuracy margin); the floor-breaching regime is untested. Evidence tier: calibrated synthetic apparatus, not production-verified (§4.6).

**E-NEW-5 H-COALESCE: cross-deployment transfer decomposition.** Warm-starting a new deployment with centroids from a related deployment reaches competence in 68–200 decisions versus 275–502 for a cold start (3/3 seeds) — a ~2–7× acceleration under the conservation law. A paired conservation-disabled re-run decomposed the mechanism: with conservation off, warm and cold starts reach competence at similar rates (warm 50–58 vs cold 50–71 decisions), so the acceleration is conservation-mediated rather than independent content transfer. The conservation law creates a regime boundary — starts above θ_min keep learning; starts that fall below trigger AMBER and pause — and a related warm start stays above it while a cold start is repeatedly paused during its climb from chance. Corollaries: (a) independent content transfer was not demonstrated (warm ≈ cold with conservation off); (b) an unstructured random-centroid warm start freezes under conservation (2885–3000 of 3000 decisions paused, all seeds) and is worse than a cold start, though a learned-but-unrelated start froze only on some seeds; (c) H-COALESCE and H-BOUND are coupled — the safety mechanism that bounds learning also mediates transfer. The prior +28pp cross-deployment figure (K19) is not reproduced. Evidence tier: calibrated synthetic apparatus.

## **5.3 Summary**

| **Level** | **Published Claim** | **Phase 1 Result** | **Phase 2+ Result** | **Final Status** |
| --- | --- | --- | --- | --- |
| Level 1 (Scoring) | Dot-product attention | 69.4% convergence | Falsified. **L2 centroidal: 97.89% (EXP-C1)**. DK showed +13.2pp/+7.67pp on synthetic heterogeneous noise but did NOT survive de-circularization on real data (characterized negative, §5.2). | **Corrected:** Eq. 4-final; kernel stays L2; DiagonalKernel reported as a characterized negative. |
| Level 2 (Discovery) | Cross-attention (Eq. 6) | 111× above random | Unchanged | **Validated** — exact correspondence to Eq. 1; mandatory z-score + L2 normalization prerequisite (EXP-2). |
| Level 3 (Multi-domain) | D(n) ∝ n^{2.30} | b = 2.30 (5-point) | b = 2.11, CI [2.09, 2.14] | **Validated (simulation), revised** — 11-point log-log, R²=0.9999. n^{2.11} is a simulation result (V1A); production magnitude pending EXP-G1. n² structural floor. |
| Re-Convergence | — | — | γ > 1 ⇔ ε_firm > 0.125, four proof paths | **Tier 2** — theorem confirmed (Arm B) AND production-logic re-convergence supported in calibrated apparatus (Arm A, γ > 1, all cells, conservation engaged). Prior gap retracted as calibration artifact. R-HCURVE: RETIRED. EXP-G1 pilot pending. |
| Two-Engine (σ⊥μ) | — | — | E[Δμ] exactly σ-independent | **Proved** — ~1% coupling at production parameters. Depth and breadth engines independent to first order. |
| Transfer | — | — | ~2-7× warm-start acceleration | **Conservation-mediated** — independent content transfer not demonstrated (H-COALESCE). Wrong-structure transfer actively harmful. |
| Learning Curve Shape | — | — | Logistic, d²q/dt² > 0 for t < ~330 | **Measured** — 2,000-decision experiment, R²≈0.88. Early positive curvature is baseline centroid convergence, not RL-directed. |
| Directed η Allocation | — | — | Uniform η at least as good | **Characterized negative** — category-directed learning-rate allocation does not improve convergence (EXP-RL-DIRECT, 3 seeds, 3 α variants). |
| σ-Directed Enrichment | — | — | Uniform enrichment outperforms | **Characterized negative** — σ-directed allocation +4.3pp vs uniform +6.9pp (EXP-RL-DIRECT-3, 5 arms, 3 seeds). σ's value is diagnostic, not operational. |
*Table 2: Key experimental results. v7.1 fix: Level 1 row references 97.89% (EXP-C1), not the earlier ambiguous "98.2%" (which was from V4/EXP-B1 zero-noise baseline).*

Additional experiments established: warm-start superiority at scale (EXP-E2), cross-category transfer (EXP-D1), absence of factor interactions in SOC data (EXP-D2), kernel generalization across distributions (EXP-E1), centroid clipping necessity (V2), SOC-Q1 conservation-law operational-definition closure, cross-deployment transfer decomposition (E-NEW-5 H-COALESCE), apparatus positive control (+9.167pp, E-NEW-4), calibrated re-convergence re-run (H-CURVE-CALIB), category-directed learning-rate allocation (EXP-RL-DIRECT, characterized negative), σ-directed enrichment allocation (EXP-RL-DIRECT-3, characterized negative), and self-computation calibration protocol validation (EXP-SELF-COMPUTE v2/v3). Complete record in Appendix A.

# **6. Related Work**

**Attention mechanisms and kernels.** Tsai et al. [2019] analyze attention through a kernel lens; Katharopoulos et al. [2020] use kernel approximations for linear attention; Choromanski et al. [2021] use random feature maps. Our contribution is domain-specific: the kernel choice produces a 36.89pp gap on bounded operational features. A next-order candidate — per-factor kernel weighting via inverse-variance — was investigated and did not survive de-circularization on real data (§5.2).

**Prototype networks and metric learning.** Snell et al. [2017] introduced prototypical networks for few-shot learning using Euclidean distance. Our centroid update rule extends this with asymmetric push/pull (derived from worst-case analyst quality), count-based decay, max-normalized kernel-aware gradient, and mandatory clipping. Xing et al. [2003] and Weinberger & Saul [2009] developed Mahalanobis-style distance metric learning with full covariance matrices; our tests found off-diagonal correlation terms add <1pp over the diagonal — consistent with the "naive Bayes paradox" [Domingos & Pazzani, 1997] — though the diagonal (inverse-variance) weighting itself did not survive de-circularization on real data (§5.2).

**Diagonal and Mahalanobis kernels.** Off-diagonal correlations add <1pp across two tested domains (SOC, S2P). The inverse-variance (diagonal) weighting we investigated did not survive de-circularization on real data and is reported as a characterized negative (§5.2).

**Conservation constraints in adaptive systems.** Our conservation law α·q·V ≥ θ_min is a form of regret-bounded learning [Shalev-Shwartz, 2012] applied to a two-level system. Two independent LLM-judge panels validated different aspects: a three-judge panel (GPT-4o / Claude Opus / Gemini, March 2026) validated the original formulation, and two four-judge math polls (GPT-4.1 / Claude Opus 4.7 / Grok 3 / Gemini 1.5 Pro, April 8 and April 16, 2026) validated the Re-Convergence Theorem and the η_override derivation respectively. The v7 operational definition of q decouples the conservation signal from kernel-specific calibration properties.

**Graph attention networks.** GAT [Veličković et al., 2018] applies attention within a single graph; our cross-graph attention operates between separate domain graphs with no shared topology — a structurally different setting enabling discovery of relationships between graphs that share no edges. GNN-based embeddings (Kipf & Welling, 2017; Hamilton et al., 2017) are a natural future extension for Level 2.

**Agent memory and cognitive architectures.** CoALA [33] formalized the three-type memory taxonomy (episodic, semantic, procedural) that underlies modern agent memory systems. Mem0 [34] implements episodic + semantic memory with entity linking for personalization. Zep [35] uses a temporal knowledge graph (Graphiti) with bi-temporal modeling for enterprise agent memory. MAGMA [36] represents memory across orthogonal semantic, temporal, causal, and entity graphs with policy-guided retrieval. GAM [37] separates narrative buffering from semantic consolidation via hierarchical graph structure. A comprehensive survey [38] covers mechanisms, evaluation, and frontiers.

Our centroid geometry, noise fingerprint, and conservation law address a problem none of these systems target: measuring per-factor decision quality from verified outcomes and proving when autonomous action is safe. The three CoALA memory types store WHAT (episodic), WHY (semantic), and HOW (procedural). Our judgment memory stores HOW WELL — a measurement that requires outcome-conditioned variance decomposition across verified decisions and cannot be derived from any combination of the standard three types. The distinction is analogous to the difference between a medical record (episodic: what treatments were given), a medical textbook (semantic: what is known about the condition), a clinical protocol (procedural: how to treat), and a surgical quality scorecard (judgment: how well THIS surgeon performs THIS procedure on THIS patient type). The first three can all confirm a systematically biased treatment protocol; only the fourth detects the bias.

# **7. Discussion and Limitations**

**The hierarchy of design decisions.** The experimental program identified the architectural decisions that collectively determine more of the system's accuracy than any amount of accumulated learning:

1. **Kernel function** (L2 vs dot product: 36.89pp, EXP-C1). Irreversible at deployment time.
2. **Kernel weighting** (diagonal 1/σ² vs uniform) — investigated and reported as a characterized negative: the DiagonalKernel advantage (up to +13.2pp on synthetic heterogeneous noise) did not survive de-circularization on real data (§5.2). The kernel is L2.
3. **Learning-rate asymmetry** (η_override from 2q̄_worst − 1: prevents 13–27pp degradation, B5B-PROXY). Derived, not tuned.
These decisions are architectural — made once, at configuration time. Everything else (centroid values, per-factor σ refinement, discovery thresholds) is operational and accumulates from verified decisions.

**Judgment memory: a fourth cognitive-architecture type and the formal basis for graph-native reasoning.** The results above — the kernel finding, the conservation law, the re-convergence theorem, the two-engine separation, the RL/evolution architecture — collectively produce a system that not only scores decisions but measures its own judgment quality per factor. We term this capability *judgment memory* and position it as the formal contribution that distinguishes graph-native *reasoning* from graph *engineering*.

The standard taxonomy for agent memory (CoALA [33]) names three long-term types; every agent memory system — Mem0 [34], Zep [35], MAGMA [36], GAM [37] — implements variations of these three. Judgment memory is a fourth:

| Memory type | What it stores | What it answers | How it's built | Graph operation |
|---|---|---|---|---|
| Episodic | What happened | "Did we see this before?" | Records events | **Read** |
| Semantic | What is true | "What do we know about X?" | Extracts/ingests facts | **Read** |
| Procedural | How to act | "What should I do here?" | Encodes routines/rules | **Route** |
| **Judgment** | **How well decisions are made, and where they are noise** | **"How reliably does action A work in situation S, and which factors are signal vs noise?"** | **Outcome-conditioned variance decomposition across verified decisions** | **Reshape** |

The correspondence in the rightmost column is exact: a knowledge graph that is *read* implements episodic and semantic memory (retrieves facts and events). A graph of agents that is *routed* implements procedural memory (encodes which agent does what). A graph that is *reshaped* from verified outcomes implements judgment memory — the centroid geometry stores the prototypes of good decisions, the per-factor σ stores outcome-conditioned variance (where the factors are signal vs noise), and the conservation law stores the safety proof that bounds autonomous action. None of these are derivable from any combination of the other three memory types, because none of the others compute outcome-conditioned quality decompositions from verified decisions.

This is why the Read → Route → Reshape progression is not merely an engineering ladder but a cognitive-architecture transition. Read and Route extend existing memory types with better graph structure. Reshape adds a memory type the others cannot produce — and it is the one that compounds.

**Signal-confidence inversion: the proof that judgment memory measures something new.** The per-factor σ computed from outcome-conditioned variance produces a diagnostic no other memory type can: the factor that analysts report highest confidence in (device_trust, mean confidence 4.2/5 in analyst surveys) has the highest outcome-conditioned variance (σ = 0.28), while the factor they rate as routine (threat_intel) has the lowest (σ = 0.07). This inversion is structurally invisible to episodic memory (which records what happened but not how well), semantic memory (which records what is true but not what is noise), and procedural memory (which records how to act but not how reliably). Consistent patterns appear in calibrated synthetic deployments across three additional domains (trading, purchasing, data engineering). Universal validation requires production-verified decision data from each domain (EXP-G1 priority).

**σ survives DiagonalKernel's preprocessing-dependence — as a diagnostic, not an operational lever.** The per-factor σ is a *measurement* operation on the centroid geometry — it is computed from outcome-conditioned variance across verified decisions regardless of whether σ is used in the scoring kernel. DiagonalKernel used σ as a scoring weight (W = diag(1/σ²)); that application proved preprocessing-dependent on real data — positive on some dataset/convention cells, negative on others (§5.2). A second operational application — directing enrichment budget proportionally to per-factor σ (enriching the noisiest factors most) — was tested (EXP-RL-DIRECT-3, 3 seeds, 5 arms including uniform, σ-directed, inverse-σ, concentrated, and unenriched) and also did not improve over uniform enrichment (σ-directed: +4.3pp vs uniform: +6.9pp over unenriched). The ordering σ-directed > inverse-σ confirms σ's directional signal is real (enriching noisy factors beats enriching clean ones), but uniform allocation outperforms all non-uniform strategies on this apparatus. The per-factor σ measurement itself — signal-confidence inversion, the noise fingerprint — exists under L2 scoring exactly as it does under DK scoring, and is detectable from σ under any kernel. What DK's preprocessing-dependence and the enrichment-direction negative together establish for judgment memory: σ's value is *diagnostic* — it measures where your factors are noise and surfaces systematic judgment biases — not *operational* (it does not reliably improve scoring or enrichment allocation when used as a weight or budget signal).

A full treatment of judgment memory — including the cognitive-architecture comparison, the multi-domain validation, the interpretability implications, and the formal relationship to the four-element algebra (State × Computation × Enrichment × Decisions) — is the subject of a companion paper [Banerji, 2026d].

**The default kernel is wrong for most enterprise applications.** Exporting the dot product from transformer attention to enterprise feature scoring is a category error. EXP-C1 measures the cost: 36.89 percentage points. Credit scoring, insurance risk assessment, supply chain prioritization, vendor evaluation, and HR talent matching are all vulnerable to the same magnitude confounding.

**The LLM judge finding.** Three frontier models available at the time of the original diagnosis (GPT-5, Claude Opus, Grok) correctly diagnosed magnitude confounding as the root cause of the published equation's failure but unanimously prescribed gating interventions. The best gating variant added 0.01pp. The correct fix added 36.89pp. This motivates the diagnostic protocol: run the one experiment before pursuing architectural interventions. The two four-judge math polls (April 8 and April 16, 2026; GPT-4.1 / Claude Opus 4.7 / Grok 3 / Gemini 1.5 Pro) use a complementary protocol — LLMs produce the analytical derivations, independent panels verify, and mathematical consensus gates the claim. The diagnostic lesson: LLM panels are unreliable reviewers when asked to prescribe fixes to empirical failures (where run-the-experiment beats prescribe-the-fix), but reliable when asked to verify analytical derivations against stated conditions (where mathematical consensus is the correct gate).

**Synthetic data — now characterized.** Beyond the DiagonalKernel de-circularization (three real datasets, §5.2), FX-1-PROXY-REAL quantified the distribution gap using 2,430 real IOC records from CISA KEV, NVD, and MITRE ATT&CK. All three factors show KL divergence >1.8 from the centroidal Gaussian assumption. Longitudinal validation on real SOC data over 6–12 months remains the highest-priority next step.

| **Factor** | **Real Mean** | **Synthetic Mean** | **Skewness** | **Kurtosis** | **KL Divergence** |
| --- | --- | --- | --- | --- | --- |
| Threat Intel Score | 0.467 | 0.500 | −0.60 | −1.11 | 2.578 |
| Asset Criticality | 0.646 | 0.500 | −0.60 | −1.39 | 1.880 |
| Pattern History | 0.165 | 0.300 | +2.82 | +8.05 | 2.434 |

**Convergence.** The pull/push update rule is an empirically effective heuristic without formal convergence guarantees in the most general setting. The Re-Convergence Theorem establishes formal conditions for γ > 1 (category-sparse disruption, warm-started centroids, ε_firm > 0.125) — all hold in every deployment studied (production range [0.15, 0.40]). A calibrated two-arm re-run supports that the production scorer logic re-converges (γ > 1, all cells, conservation engaged); an earlier γ < 1 finding was retracted as a calibration artifact (§4.6). The conservation law α·q·V ≥ θ_min (α = cumulative category coverage; θ_min = 23.53/(α·V), a cold-start interlock) provides a runtime safety mechanism.

**Transfer and safety are coupled (H-COALESCE × H-BOUND).** The cross-deployment transfer investigation (E-NEW-5) yielded a finding the original thesis did not predict: warm-starting's value depends on the conservation law. With conservation disabled in our apparatus, warm and cold starts converged at similar rates — the ~2–7× warm-start acceleration is present only when conservation is engaged. The mechanism is a regime boundary: the safety law lets starts above θ_min keep learning and pauses those below it, so a related warm start clears the boundary while a cold start is repeatedly paused during its climb. The safety mechanism that protects the system also rewards good initialization. A practical corollary: transferring centroids from an unrelated domain can be worse than starting cold — an unstructured start drove accuracy below the safety floor and froze learning across all seeds tested — so deployment migration should transfer within a domain (shared factor semantics), not across unrelated ones. Independent content transfer (the prior K19 +28pp) was not demonstrated in this apparatus.

**N_half scalar claim.** The scalar claim "N_half ≈ 14 verified decisions" holds for the L2 kernel. Per-factor convergence-rate variation under heterogeneous-noise weighting was characterized only under the DiagonalKernel, which is a characterized negative (§5.2); the L2 scalar claim stands.

# **10. The Control Plane: How Reshape Deploys**

The mathematical guarantees proved in §§3–5 (conservation law, re-convergence theorem, two-engine separation) are necessary but not sufficient for production deployment. This section presents the control-plane architecture that translates them into operational safety, absorbed from a companion production report [22].

## **10.1 Architecture Overview**

The production system comprises four layers: the Graph Attention Engine (GAE) substrate (profile scoring, centroid learning, conservation law — §3.1), the copilot SDK (domain-neutral RL/evolution sidecar, conservation-state contract, promotion gate — §4.8), domain copilots (SOC, S2P, Trading, Purchasing, DataOps — each with domain-specific reward functions and factor configurations), and the AgentEvolver runtime (variant proposal, shadow testing, conservation-gated promotion). The judgment core (centroid distance + softmax) is the authoritative decision path. The RL/evolution sidecar operates after verified outcomes and never replaces the centroid-selected action (G1 — §4.8).

**SituationAnalyzer — the ingress reasoning layer.** SituationAnalyzer is the architectural component that turns raw operational context into a scored decision. It is not a static mapping; it *reasons among actions*. The pipeline: (1) ingress normalization — raw inputs (an alert, an invoice, a trade signal) are transformed into a structured factor vector f ∈ [0,1]^d through LLM-mediated interpretation and context-graph enrichment; (2) situation conditioning — the factor vector is conditioned on its graph coordinate (category, deployment context) so that the same raw signal receives a different, defensible interpretation depending on *where in the graph it sits* (a 4% price variance is routine in one commodity category and a red flag in another); (3) option scoring — the conditioned factor vector is scored against the centroid geometry (Eq. 4-final) to produce a probability distribution over actions; (4) abstention — if the conservation gate (α·q·V ≥ θ_min) is not satisfied for this category, the system abstains rather than scoring. This is the *situation analysis* construct: the system reasons among actions in context, not a script firing a fixed workflow. SituationAnalyzer handles ingress normalization and routing across all copilots; domain-specific option discrimination (which actions to consider, how to weight them) is configured per copilot.

**SituationAnalyzer — reasoning autonomy (experimentally characterized).** SA's reasoning-autonomy value — the scoring-accuracy improvement from graph-mediated semantic consolidation — is evidenced by V-CGA-FROZEN: enrichment from context-graph traversal reduces per-factor σ, producing +5.0pp Day-1 accuracy (p<0.0001) with no change in convergence rate. The enrichment IS the SA mechanism: the context graph provides information (entity relationships, co-occurrence, historical context) that a context-free feature extractor cannot access, reducing the noise in the factor vectors SA constructs. A noise-redistribution test (EXP-SA-REASONING, graph-correlated vs independent noise at equal total power) was negative because L2 scoring is dominated by the noisiest dimensions — redistributing noise hurts; the value of SA is reducing TOTAL noise through graph-derived signal, not redistributing it. Per-decision abstention (EXP-SA-ABSTAIN: 100% OOD detection, 4.4–5.1% FP, reduced AMBER episodes) is a valid safety primitive complementing conservation — it catches individual anomalous inputs the aggregate gate misses.

**AgentEvolver — decision autonomy (experimentally validated).** AgentEvolver evolves the operational layer at deployment time: prompts, scoring configurations, tool limits, routing rules. What does NOT evolve: the conservation law, the L2 kernel, the update-rule asymmetry, the G1 boundary. AgentEvolver operates through the sidecar's shadow-test → promotion-gate → rollback cycle (§4.8). EXP-AE-DECISION validated the decision-autonomy claim: under adversarial poisoning (20% harmful inputs through the full learning loop), AE's drift-triggered rollback + per-category η damping reduced non-recovery from 56.9% (frozen) to 14.4% — a 42.5pp improvement, 3/3 seeds. Centroid drift reduced 60% (0.307 → 0.124 mean). Recovery time: consistently 1 decision (vs 1–9 frozen). AE triggered 4–6 rollback+damping actions per seed within ~50–100 decisions of adversarial onset, operating entirely within conservation bounds. Compared to EXP-OP2 (38% non-recovery with conservation alone): AE further reduces non-recovery to 14.4% by catching and REVERSING per-category poisoning that conservation's aggregate gate cannot detect until accuracy has already degraded. Conservation and AE are complementary — conservation catches aggregate degradation; AE catches and reverses per-category poisoning. The runtime-evolution capability also allows a deployment to change how it scores mid-incident — when the attack is novel, a frozen deployment can only do what it was configured to do; a deployment with decision autonomy adapts.

## **10.2 Binding Runtime Gates**

The adversarial results (§11.2) establish the architectural requirement for binding runtime gates — evaluation as a control plane, not an advisory layer. Seven gate types are operational:

1. **Conservation gates.** The primary mathematical safety primitive. α·q·V ≥ θ_min governs the learning system itself — AMBER auto-pause freezes learning when the product drops below the floor, preserving verified decisions for resumption (§3.1, §3.3 operational semantics).

2. **Quality gates.** Confidence thresholds for autonomous action. At ECE=0.036 (τ=0.1 on centroidal data), a threshold of 0.90 confidence is meaningful. The gate routes via kernel-independent signals: rolling verified accuracy, softmax entropy, or category-specific thresholds.

3. **Safety gates.** Operator quality verification. The P-75 paradox (§11.2) shows that even a 75%-correct operator causes more harm than no operator — 28% non-recovery versus 24%. Only verified high-quality operators pass the safety gate.

4. **Rollback gates.** The lasting-damage finding (§11.2) shows TTL is insufficient — harmful operators leave centroid damage that persists beyond TTL expiry. The system maintains μ_checkpoint, measures ‖μ(t) − μ_checkpoint‖, and triggers rollback when drift exceeds a threshold. Checkpoint + rollback is general infrastructure, not an optional safety feature.

5. **Deployment qualification gates (P28 pipeline).** A six-phase deployment pipeline: Import → Compute per-factor σ → Shadow mode → Qualify → Enable learning → Monitor. `LEARNING_ENABLED` defaults to False — enabling requires passing P28. The pipeline derives deployment-specific values: per-factor σ (for diagnostics), τ (for calibration), and deployment-specific θ_min.

6. **Promotion gates (evolution sidecar).** No variant promotes without passing: accuracy within the superiority threshold (5pp default), minimum shadow decisions (10), variance under cap, and conservation GREEN. Fail-closed: UNKNOWN, AMBER, RED, stale, missing, or provider-error states block promotion (§4.8). **Gate adequacy (experimentally characterized, EXP-AE-GATE):** at n_min=10, the strict-inequality gate (shadow > production + 5pp) has 59% power and 44% false-positive rate — little better than a coin flip. The structural cause: when the true variant improvement equals the threshold exactly, the strict inequality can never exceed 50% power asymptotically, regardless of n. At n_min=400, FPR drops to 10% but power reaches only 58%. The production recommendation: replace the strict-inequality point comparison with a statistical test (two-proportion z-test, H₀: Δ ≤ 0, require p < 0.05 AND Δ̂ > 3pp) to give the gate discriminative power near the threshold. This is a **production design finding** that changes the gate implementation.

7. **Audit chain gates.** Structural rather than behavioral. Before any learning commit, `verify_chain()` must return valid. If the DecisionEntry/OutcomeEntry chain cannot be validated (missing entries, hash mismatch, out-of-order sequence), learning is blocked. This gate is the control-plane enforcement of the safety cascade: audit chain integrity → q defensibility → conservation-law runtime guarantee.

**The distinction that matters.** Advisory gates log a warning. Binding gates prevent the action. When 38% of harmful-signal scenarios produce permanent degradation without intervention, "advisory" is an architectural failure.

## **10.3 Deployment Orchestration**

The five copilots deploy on a shared GAE substrate with independent domain configurations:

| Copilot | Factor dimensions | Action space | Reward function | Domain |
|---|---|---|---|---|
| SOC | d=6 | A=4 | BinaryReward (penalty 20×) | Security operations |
| S2P | d=8 | A=5 | GradedFinancial (penalty 5×) | Source-to-pay |
| Trading | d=6 | A=4 | PnL (penalty 3×) | Trading |
| Purchasing | d=8 | A=5 | WasteReduction (penalty 3×) | Restaurant purchasing |
| DataOps | d=6 | A=4 | GradedFinancial (penalty 10×) | Data operations |

Each copilot progresses through: shadow mode (scoring without learning) → PILOT_GATED (manual promotion by operator, requires shadow accuracy above domain threshold + conservation engaged) → production (conservation-governed learning).

Terminal actions are governed recommendations, not autonomous execution — the system advises, a human acts. Conservation gate and situation analysis are not yet coupled (C-COUPLE roadmap item).

# **11. Production Characterization**

## **11.1 Deployment Evidence**

The conservation law (§3.1) runs across all five production copilots on a shared control plane. MAP v5.229 validation: 9,826 tests passing, zero failures. Each test is a conservation-law invariant check: α·q·V ≥ θ_min held, AMBER triggered correctly, no centroid update escaped the gate. Campaign-holdout infrastructure assigns treatment/control at the decision-node level by deterministic SHA-256 hash for auditable comparison. Real measurement awaits pilot deployment with operational analysts (PILOT_GATED).

## **11.2 Adversarial Resistance**

The production question is not "does it work when everything is fine?" but "what happens when something is wrong, and can you bound the damage?" Tested with deliberately harmful inputs (operators that are 0%, 25%, 50%, 75%, 100% correct) across 100 seeds (EXP-OP2).

| Condition | NR% (N=100) | 95% CI | Mean T_recovery |
|---|---|---|---|
| B (100% correct) | 8% | [4.1%, 15.0%] | 55 ± 240 |
| A (no operator) | 24% | [16.7%, 33.2%] | 178 ± 356 |
| P-75 (75% correct) | 28% | [20.1%, 37.5%] | 228 ± 445 |
| C (0% correct, harmful) | 38% | [29.1%, 47.8%] | 425 ± 561 |

Four findings that drive the gate architecture:

1. **The 38% architecture requirement.** In 38% of harmful-operator seeds, the system does not recover within the measurement window. Without rollback, 38% of harmful-signal scenarios produce permanent degradation. This is why rollback gates (§10.2) are general infrastructure.

2. **The P-75 paradox.** A 75%-correct operator has 28% non-recovery versus 24% for no operator. Mixed-quality signals create a distribution that the learning loop must learn and then unlearn — worse than learning nothing. This is why safety gates verify operator quality, and why the η_override derivation uses worst-case q̄ (§3.1).

3. **The baseline fragility.** Condition A (no operator) has 24% non-recovery. Checkpoint + rollback is required as general infrastructure, not just for adversarial scenarios.

4. **Poisoning ceiling.** EXP-S2-REPRO extended poisoning tests to production conditions (200-decision warm-up, conservation engaged). Maximum AUAC degradation: 0.15pp at 20% poison — conservation bounds the damage even when individual centroids are permanently shifted.

## **11.3 Conservation Law in Production**

The conservation law's operational semantics (§3.3 extended):

- **q(t):** rolling verified accuracy over the last 400 decisions. Long/stable window: SE(q) ≈ 3.6pp at n ≈ 100 verified samples. Measured on argmax correctness against ground truth — kernel-independent.
- **α(t):** cumulative category coverage (c_d/C, fraction of categories with sufficient verified decisions). Captures breadth of experience.
- **V(t):** verified decisions per day. Volume multiplier.
- **θ_min = 23.53/(α·V):** self-calibrating. At SOC canonical (V=200 alerts/day, α=0.25): θ_min ≈ 0.467. Higher-volume deployments tolerate a lower conservation floor because more decisions provide more recovery signal per day.
- **AMBER auto-pause:** when α·q·V < θ_min, learning freezes until the product recovers. Protects centroids from low-quality cascades while preserving verified decisions for resumption.

Cold-start interlock progression: decisions 1→~50 (insufficient V, no learning) → decisions 50→400 (conservation-gated, AMBER fires frequently as q fluctuates) → decisions 400+ (steady-state, conservation rarely fires, reshaping proceeds).

## **11.4 Audit Chain and Compliance**

Adversarial testing extends beyond input-poisoning to structural-integrity audits. The audit chain uses a two-event-type architecture:

- **DecisionEntry** (sealed at decision time): action, confidence, factors, timestamp, prev_hash.
- **OutcomeEntry** (sealed at verification time): decision_id, outcome, analyst_override, timestamp, prev_hash.

This separates the decision event (t₁) from the outcome event (t₂) — the hash at t₁ cannot include information that doesn't exist until t₂. `verify_chain()` validates both entry types and checks prev_hash linkage.

The three-layer safety cascade: (1) audit chain integrity — every verified outcome is provably recorded, in order, without mutation; (2) q defensibility — q is a well-defined quantity only if the outcomes backing it are faithfully recorded; (3) conservation-law runtime guarantee — α·q·V ≥ θ_min is a binding gate only if q is trustworthy. A broken audit chain cascades upward: the runtime guarantee loses its grounding.

EU AI Act Article 9(2)(a)–(b) transparency obligations require tamper-evident audit trails — the DecisionEntry/OutcomeEntry architecture addresses this for regulated deployments.

---

# **8. Conclusion**

Graph engineering — building a knowledge graph to read and wiring a graph of agents to route — has moved from research frontier to documented recipe. Both are real advances; both stop at the same line: the graph is structure the model reads or routes through, and the reasoning is still the model's, still once, still transient. This paper proves that a third operation — *reshape* — crosses that line: a graph whose decision geometry reshapes from verified outcomes is safe, fast, independent of the enrichment that populates it, and produces a fourth cognitive-architecture type (judgment memory) that no read or route can derive.

The central finding: on bounded operational features, L2 distance outperforms dot product by 36.89 percentage points — the largest single-variable effect in our ~194-experiment record. A second kernel finding is reported as a negative: DiagonalKernel's per-factor 1/σ² advantage (up to +13.2pp on synthetic heterogeneous noise) did not survive de-circularization on three real datasets — it is not scale-robust and reverses sign across preprocessing conventions (§5.2). The kernel choice is L2; the DiagonalKernel investigation is retained as a characterized negative.

Together with asymmetric learning rates derived from worst-case analyst quality (η_override = 0.01 at q̄_worst = 0.60), a conservation law (α·q·V ≥ θ_min, α = cumulative category coverage, θ_min = 23.53/(α·V) an empirically calibrated cold-start interlock, with q = rolling verified accuracy over 400 decisions), and the Re-Convergence Theorem (γ > 1 ⇔ ε_firm > 0.125, four structural proof paths), the framework provides validated mechanisms for all identified failure modes. Profile centroids achieve 90.6% with zero learning (A=4, realistic data); 97.89% on centroidal synthetic. Discovery scales super-quadratically (n^{2.11}). The framework is validated across ~194 experiment entries (59 primary + 1890 factorial sub-cells).

The economic implication stated in §1.1 closes here: three architectural decisions — kernel, weighting, learning dynamics — determine whether an enterprise AI investment is operating expense or capital infrastructure. This paper quantifies all three and reports honestly when one didn't survive. The control-plane architecture (§10–§11) quantifies the runtime safeguards that make compounding operational. The judgment-memory contribution (§7) establishes why this is a cognitive-architecture transition — graph-native *reasoning* — and not merely better graph *engineering*: a graph that reshapes from verified outcomes produces a memory type the field's existing taxonomy does not contain, and it is the one that compounds.

# **9. Future Work**

## **9.1 Resolved in v7**

The v7 experimental closure retired several previously-open research items. **Kernel weighting (DiagonalKernel):** investigated and resolved as a characterized negative — the per-factor 1/σ² advantage did not survive de-circularization on three real datasets (§5.2). **Conservation law q and α operational definitions:** q = rolling verified accuracy over last 400 decisions; α = cumulative category coverage (c_d/C), not override rate [updated v7.6 under D1; the SOC-Q1 "α over last 50 verified" windowing is superseded — q definition stands]; V = verified decisions per day; SOC-Q1 closure April 19, 2026 (CLAIM-Q-DEF). **Adversarial robustness:** validated (§11.2) — 35% non-recovery (N=100, 95% CI 29–48%), 0.15pp poisoning ceiling at A=4. **Formal convergence:** partially resolved — Re-Convergence Theorem proven for category-sparse disruption with ε_firm > 0.125, four structural proof paths. **Graph enrichment as precision substrate:** validated — +5pp Day-1 accuracy (p<0.0001), kernel-independent; IKS trajectory advantage at all checkpoints (p=0.0006); convergence-speed claim retired as definitive null (d=−0.010, p=0.873). Mechanism (improved class separation) is the consistent hypothesis, not established cause.

## **9.2 Open research agenda**

Of the items below, the highest priority is **real-data longitudinal validation** on operational SOC data over 6–12 months — synthetic LLM-judge validation across 9 deployment-realistic streams provides pre-customer validation, but real data is the binding gate for deployment-scale claims. Second priority is **EXP-G1 empirical γ measurement** via 90-day pilot centroid-distance data — closes the Re-Convergence Theorem's final empirical gate. Remaining items ordered by dependency:

- **Real data validation (priority 1).** Operational SOC data over 6–12 months for V3A and V-SIM replication, and FX-1-PROXY-REAL distribution characterization extended to live streams.

- **EXP-G1 empirical γ (priority 2).** Measures γ empirically using the centroid-distance metric per proof path 4. The γ > 1 claim in Eq. 14 refers to the discovery scaling term (Term 3 of Eq. 13) — separate mechanism from centroid convergence, unaffected by V-CGA-FROZEN findings.

- **Per-factor N_half empirical validation.** EXP-G1 pilot data will measure per-factor convergence across deployment noise profiles.

- **GNN-based embeddings.** For Level 2; Experiment 4 phase transition (σ = 0.3) suggests learned embeddings would substantially improve discovery precision.

- **Multi-prototype extensions.** For categories with distinct sub-populations.

- **Kill-chain modeling.** Via sequence-aware features for multi-stage attack detection.

- **Override learning for referral routing.** Policy-based rules achieve 72.7% DR at 12% FPR (EXP-REFER-LAYERED); the 20.7% emergent fraction requires ML-based override learning, data-gated at ≥ 50 positive examples.

- **Multi-domain validation.** S2P validated (d=8); supply chain, procurement, and financial compliance remain untested in full production contexts.

- **Formal convergence — general case.** Asymptotic convergence of Eq. 4b-final for arbitrary analyst quality is open. Conservation law provides a practical runtime substitute.

- **Self-computation: graphs that reshape themselves, not just their decisions.** The architecture presented in this paper reshapes decision geometry (Level 0) from verified outcomes. A natural extension reshapes the graph's *structure* (Level 1): which factors exist, which data sources feed them, which process steps the system represents. We term this self-computation and present a formalism, a validated calibration protocol, and a characterized precondition.

  **Formalism.** Define a self-computing graph as a tuple (G, Φ, C) where G = centroid geometry (Level 0 state), Φ = structural configuration (factor space F, source configuration S, process definition P), and C = conservation law α·q·V ≥ θ_min. Level 0 reshapes G within a fixed Φ; Level 1 reshapes Φ itself by proposing a structural change Φ → Φ', shadow-testing it, and promoting through the SAME conservation gate that governs Level 0. Convergence: each promoted structural change is non-degrading (the gate requires q' > q + δ); q is bounded above; the structural change space is finite (bounded by the enterprise's actual systems) — so the sequence converges to a local optimum Φ* in finitely many steps.

  **Calibration protocol (validated).** Level 1 structural changes follow the same bootstrap as Level 0's cold-start interlock (§3.3): Phase 2a (calibration) — new factors observe and learn but do not enter the scoring equation; Phase 2b (integration) — calibrated factors enter scoring; the promotion gate evaluates HERE, after calibration, not during the cold-start trough. EXP-SELF-COMPUTE v2 validated the protocol: new-factor centroid distances declined monotonically during calibration in every seed (3/3), and the cold-start J-curve that invalidated the gate in v1 was eliminated.

  **Conservation precondition (discovered).** EXP-SELF-COMPUTE v3 revealed a structural constraint: Level 1 evolution requires the CURRENT configuration to produce accuracy above θ_min. When the degraded configuration is below the conservation floor (as in v3's d=4 weak-only, accuracy ≈ 0.23–0.31 for A=4), conservation pauses ALL learning — including the calibration updates to the new factors — and the system deadlocks (centroid distances remained at ~0.684, zero convergence across all seeds). This is the same structural pattern as the H-COALESCE transfer coupling (§5): starts above the conservation floor keep learning; starts below it freeze. The precondition is realistic in production: initial configurations are human-expert-configured and PILOT_GATED, so they clear the conservation floor before self-computation begins. Self-computation evolves incrementally from an adequate base, not from a catastrophic deficit.

  **Two concrete pathways.** (a) *Data-platform evolution (DataOps + AgentEvolver):* the DataOps copilot scores data-source quality through context graphs and situation analysis; AgentEvolver proposes changes to the data platform itself (adding a source, retiring a degraded one, re-weighting a feed) based on the decision layer's accuracy measurements, shadow-tests them, and promotes under conservation. (b) *Process evolution (tech-process fusion):* the system represents an operational process (ERP workflow, authorization policy, exception taxonomy) as machine-reasonable state; when judgment memory surfaces a gap, AgentEvolver proposes a process edit, shadow-tests it, and promotes under the conservation gate — closing the gap at the process level.

  **Evidence tier (F-24).** The convergence argument is proved (monotone on a finite set, bounded above). The calibration protocol is **validated** (EXP-SELF-COMPUTE v2, 3 seeds). The conservation precondition is a **characterized constraint** (EXP-SELF-COMPUTE v3, 3 seeds). The self-computation dividend (Level 1 produces accuracy improvements Level 0 cannot reach) is established by the structural-accuracy sweep (d=4 weak: 0.23–0.31; d=6 full: 0.25–0.98; seeds 123/777 show 65–75pp gaps) but NOT demonstrated through the calibrated promotion pathway on the current apparatus — the precondition violation prevented it. Full validation requires either (a) a production-scope test where structural evolution is incremental from an adequate base, or (b) a synthetic apparatus where the degraded configuration is above θ_min but meaningfully below the full-configuration ceiling.

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
[22] [ABSORBED] Banerji, A. (2026c). Production architecture for compounding intelligence. Now §10–§11 of this paper.
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
[33] Sumers, T.R., et al. (2023). Cognitive Architectures for Language Agents. arXiv:2309.02427.
[34] Chhikara, P., et al. (2025). Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory. ECAI 2025. arXiv:2504.19413.
[35] Rasmussen, P. (2025). Zep: A Temporal Knowledge Graph Architecture for Agent Memory. arXiv:2501.13956.
[36] Jiang, D., et al. (2026). MAGMA: A Multi-Graph based Agentic Memory Architecture for AI Agents. arXiv:2601.03236.
[37] Huang, W.-C., et al. (2026). GAM: Hierarchical Graph-based Agentic Memory for LLM Agents. arXiv:2604.12285.
[38] He, S., et al. (2026). Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers. arXiv:2603.07670.

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
| P3 | EXP-G1 | Empirical γ measurement on 90-day pilot data | PENDING | Centroid-distance convergence rate ratio (path 4). |
| P4 | V-OLS-DETECT-OLS | OLSMonitor re-validation | PENDING | Adversarial degradation detection, p90 lead time ≥ 50 decisions. P3 backlog. |

### **Phase 6: Calibrated Re-Run and Apparatus Control (May–August 2026)**

| **#** | **ID** | **Question** | **Result** | **Key Number** |
| --- | --- | --- | --- | --- |
| 44 | H-CURVE-CALIB | Calibrated two-arm re-convergence re-run | PASS | Arm A γ > 1 all 6 cells, conservation 100% engaged, 0% paused |
| 45 | H-CURVE-DIAG | Prior Arm A diagnostic (retraction) | ARTIFACT | Apparatus at chance (0.25); θ_min unreachable → conservation trivially always-paused |
| 46 | H-ENRICH-POSCONTROL | Apparatus positive control (floor-lift detection) | PASS | +9.167pp at σ→0.04, sign-consistent 3/3 seeds, 6.35× above 2·SD; monotone to +26.25pp |
| 47 | H-COALESCE | Cross-deployment transfer decomposition (v4.3 conservation-on / v5.1 conservation-off) | PARTIAL | ~2–7× warm-start acceleration, conservation-mediated; content transfer not demonstrated; unstructured transfer freezes under conservation |

Full catalog (~194 experiment entries including the 1890-cell DK factorial sub-experiments and Phase 7) available in experiment_reference_catalog_v2 [28].

### **Phase 7: RL-Direct, Enrichment-Direction, and Self-Computation (August 2026)**

| **#** | **ID** | **Question** | **Result** | **Key Number** |
| --- | --- | --- | --- | --- |
| 48 | EXP-RL-DIRECT | Category-directed learning-rate allocation (first-order) | CHARACTERIZED NEGATIVE | Directed η faster in 1/3 seeds; mean AUT_ACC worse (641 vs 599); 3 α variants tested, none consistently better |
| 49 | EXP-RL-DIRECT (curvature) | Second-derivative detection on learning curve | MEASURED | Logistic fit R²≈0.88; d²q/dt² > 0 at t=100 (~5.3×10⁻⁷), negative by t=500; inflection ~327–361 decisions |
| 50 | EXP-RL-DIRECT-3 | σ-directed enrichment allocation | CHARACTERIZED NEGATIVE | σ-directed +4.3pp vs uniform +6.9pp; σ-directed > inverse-σ (directional signal real); uniform outperforms all non-uniform |
| 51 | EXP-SELF-COMPUTE v1 | Self-computation (uncalibrated transition) | APPARATUS ISSUE | Gate passed 1/3 seeds; cold-start trough swamped evaluation |
| 52 | EXP-SELF-COMPUTE v2 | Self-computation (calibrated transition) | CALIBRATION VALIDATED | Calibration protocol works (distances declined 3/3 seeds); structural contrast too weak for gate |
| 53 | EXP-SELF-COMPUTE v3 | Self-computation (strong structural contrast) | CONSERVATION PRECONDITION | Conservation deadlocked calibration when degraded config below θ_min; precondition characterized |
| 54 | EXP-RL-DIRECT-4 | Second-order rate signal (pre-flight) | APPARATUS-LIMITED | SNR 0.37–0.60; detection lag 260-311 decisions; pre-flight characterized signal quality |
| 55 | EXP-RL-SCORER | Definitive RL-in-scorer test (3 strategies) | DEFINITIVELY NEGATIVE | EMA-rate, Thompson sampling, hybrid gap+momentum — none beat uniform on both metrics in any seed. Thompson best: AUT_ACC Δ=0.4%, within noise. Line closed. |
| 56 | EXP-SA-ABSTAIN | Per-decision abstention (SA-2 formalism) | SAFETY VALIDATED | 100% OOD detection, 4.4–5.1% FP, reduced AMBER episodes. Does NOT improve accuracy — safety primitive, not accuracy mechanism. |
| 57 | EXP-AE-GATE | Promotion gate power analysis (AE-2 formalism) | DESIGN FINDING | n_min=10: 59% power, 44% FPR. Strict-inequality gate structurally capped at 50% power when true effect = threshold. Statistical test recommended. |
| 58 | EXP-SA-REASONING | Graph-mediated vs context-free noise (SA reasoning autonomy) | NEGATIVE (wrong operationalization) | Correlated noise at equal total power worse in 3/3 seeds. L2 dominated by noisiest dims. SA value is noise REDUCTION (V-CGA-FROZEN +5.0pp), not redistribution. |
| 59 | EXP-AE-DECISION | Runtime evolution under adversarial poisoning (AE decision autonomy) | **VALIDATED** | Non-recovery: 56.9%→14.4% (−42.5pp). Drift: −60%. Recovery: 1 decision (vs 1-9). Rollback+damping 4-6× per seed. Complements conservation (38%→14.4%). |

The DiagonalKernel factorial rows in the phase tables above (V-MV-KERNEL-HET, V-HC-CONFIG, KernelSelector, UNI-DK-01 v5.3, MR-COLAB-01) are retained as the complete experimental record; the DiagonalKernel advantage they measured on synthetic data did not survive de-circularization on three real datasets and is reported as a characterized negative (§5.2).
