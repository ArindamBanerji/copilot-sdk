# math_synopsis v18 → v20: Consolidated Edit List

**Version:** 3.0 (consolidates v2.0 Phase 6 edits + Phase 7 additions)
**Date:** August 24, 2026
**Status:** Ready for application against v18 source (requires v18 upload)

## Summary

**21 edits total:**
- Edits 1–13: v2.0 list (Phase 6, unchanged — all correct)
- Edits 14–21: Phase 7 additions (August 2026, from the RL/SA/AE experimental program)

**Version bumps to v20** (not v19) because the Phase 7 additions are substantial — 12 new experiments, 3 new formalisms (JM/SA/AE), RL-scorer line closure, and the graph-native-reasoning positioning.

---

## Edits 1–13: UNCHANGED from v2.0

All 13 edits from the v2.0 list apply as-is. No corrections needed.
The application order from v2.0 is preserved.

---

## Edits 14–21: Phase 7 Additions

### Edit 14: Phase 7 Experiment Record

Location: After Phase 6 (Edit 8).

Action: ADD Phase 7:

```markdown
### Phase 7: RL-Direct, Self-Computation, SA/AE Autonomy
    (August 2026)

| # | ID | Question | Result | Key Number |
|---|---|---|---|---|
| 48 | EXP-RL-DIRECT | Category-directed η (first-order) | NEGATIVE | 1/3 seeds faster, worse AUT_ACC |
| 49 | EXP-RL-DIRECT (curvature) | Second-derivative on learning curve | MEASURED | Logistic R²≈0.88, d²q/dt²>0 for t<330 |
| 50 | EXP-RL-DIRECT-3 | σ-directed enrichment | NEGATIVE | Uniform +6.9pp > σ-directed +4.3pp |
| 51 | EXP-SELF-COMPUTE v1 | Uncalibrated structural transition | APPARATUS | Cold-start trough swamped evaluation |
| 52 | EXP-SELF-COMPUTE v2 | Calibrated structural transition | CALIBRATION VALIDATED | Distances declined 3/3, J-curve eliminated |
| 53 | EXP-SELF-COMPUTE v3 | Strong structural contrast | PRECONDITION | Conservation deadlocked below θ_min |
| 54 | EXP-RL-DIRECT-4 | Second-order rate signal | APPARATUS-LIMITED | SNR 0.37–0.60, detection lag 260-311 |
| 55 | EXP-RL-SCORER | Definitive RL-in-scorer (3 strategies) | DEFINITIVELY NEGATIVE | EMA-rate, Thompson, hybrid — none beat uniform |
| 56 | EXP-SA-ABSTAIN | Per-decision abstention | SAFETY VALIDATED | 100% detection, 4.4–5.1% FP, reduced AMBER |
| 57 | EXP-AE-GATE | Promotion gate power | DESIGN FINDING | n_min=10: 59% power, 44% FPR |
| 58 | EXP-SA-REASONING | Graph-correlated vs context-free noise | NEGATIVE (wrong operationalization) | L2 dominated by noisiest dims |
| 59 | EXP-AE-DECISION | Runtime evolution under adversarial | **VALIDATED** | Non-recovery 57%→14% (−42.5pp) |
```

### Edit 15: NEW — RL Sidecar Architecture and Scorer-RL Line Closure

Location: After §3.X (σ⊥μ) or in a new §4.X.

Action: INSERT section:

```markdown
### §X.X — The Governed Second Derivative and RL Architecture (v20)

**Measured: logistic baseline curvature.** A 2,000-decision
experiment fitted the learning curve: logistic (R²≈0.88),
d²q/dt² > 0 for t < ~330 decisions, negative by t=500.
Early positive curvature is the natural shape of centroid
convergence, not an RL effect.

**RL/evolution sidecar architecture.** The production system
separates judgment from learning with four guarantees (G1–G4).
The judgment core (centroid distance + softmax) is the
authoritative decision path (G1: action selection is not
reward-maximizing). RL/evolution operates as a procedural-
memory sidecar: five domain-specific reward functions,
ConservationBoundedThompson exploration, shadow-test →
conservation-gated promotion → rollback.

**Scorer-integrated RL: definitively closed.** Four experiments
across 6+ strategies tested whether RL-derived signals routed
into the scorer's learning rate (η) improve convergence:
  - First-order accuracy gap (DIRECT-1, 3 α variants): negative
  - σ-directed enrichment (DIRECT-3, 5 arms): negative
  - Second-order rate (DIRECT-4): apparatus SNR too low
  - EMA-rate, Thompson sampling, hybrid (RL-SCORER): negative
None beat uniform η=0.05. The sidecar IS the right architecture.

**Remaining hypothesis.** Sidecar-mediated compounding (variant
evolution → better operational context → more informative
centroid updates) is untested — pilot-arbitrated.
```

### Edit 16: NEW — Judgment Memory Fourth Cognitive Type

Location: Discussion/JM section.

Action: EXPAND any existing JM mention to include:

```markdown
### Judgment Memory as Fourth Cognitive-Architecture Type (v20)

| Memory type | Stores | Answers | Built from | Graph op |
|---|---|---|---|---|
| Episodic | What happened | "Seen before?" | Events | Read |
| Semantic | What is true | "Know about X?" | Facts | Read |
| Procedural | How to act | "Do here?" | Rules | Route |
| **Judgment** | **Decision quality + noise** | **"How reliably does A work in S?"** | **Outcome-conditioned variance** | **Reshape** |

Read and Route extend existing memory types with better graph
structure. Reshape adds a type the others cannot produce —
the one that compounds.

**σ survives DK — as diagnostic, not operational.** Per-factor
σ (outcome-conditioned variance) is a measurement, not a
scoring weight. DiagonalKernel used it as a weight (retracted).
σ-directed enrichment used it as an allocation signal (negative).
σ's value is diagnostic: signal-confidence inversion, noise
fingerprint, judgment-bias detection.
```

### Edit 17: NEW — Self-Computation Formalism

Location: After σ⊥μ and H-COALESCE sections.

Action: INSERT:

```markdown
### Self-Computation (v20)

**Formalism.** (G, Φ, C): G=centroid geometry, Φ=structural
configuration (factors, sources, processes), C=conservation.
Level 0 reshapes G; Level 1 reshapes Φ under the same C.
Convergence: monotone on finite set, bounded above.

**Calibration protocol (validated).** New factors observe/learn
without entering scoring (Phase 2a), then integrate (Phase 2b).
EXP-SELF-COMPUTE v2: distances declined 3/3 seeds.

**Conservation precondition (characterized).** Level 1 requires
current config above θ_min. Below it, conservation deadlocks
calibration (v3: zero convergence). Realistic in production
(initial configs are PILOT_GATED).

**Two pathways:** data-platform evolution (DataOps + AgentEvolver)
and process evolution (tech-process fusion).
```

### Edit 18: NEW — SA Reasoning Autonomy

Location: Architecture/SA section.

Action: INSERT or EXPAND:

```markdown
### SituationAnalyzer: Reasoning Autonomy (v20)

SA uses context graphs to consolidate semantic meaning —
traversing graph-connected entities/relations to build
situational understanding. Context-dependent factor vectors
vs heuristic dispatch (current agentic frameworks).

Evidence: V-CGA-FROZEN (+5.0pp from enrichment = graph-mediated
noise reduction). SA-REASONING (noise redistribution test)
was negative — L2 dominated by noisiest dims; SA's value is
noise REDUCTION through graph signal, not redistribution.

Per-decision abstention (SA-ABSTAIN): 100% OOD detection,
4.4–5.1% FP, reduced AMBER — safety primitive complementing
conservation.
```

### Edit 19: NEW — AE Decision Autonomy

Location: Architecture/AE section.

Action: INSERT or EXPAND:

```markdown
### AgentEvolver: Decision Autonomy (v20)

AE evolves operational context at runtime under conservation-
gated shadow-test → promote → rollback. What evolves: prompts,
scoring configs, tool limits, routing rules. What doesn't:
conservation law, L2 kernel, η asymmetry, G1 boundary.

**EXP-AE-DECISION (VALIDATED).** Under 20% adversarial
poisoning, AE's drift-triggered rollback + η damping:
  - Non-recovery: 57% → 14% (−42.5pp, 3/3 seeds)
  - Centroid drift: −60%
  - Recovery: consistently 1 decision
Conservation and AE are complementary — conservation catches
aggregate degradation; AE catches per-category poisoning.

**AE-GATE finding.** n_min=10: 59% power, 44% FPR. Strict-
inequality gate structurally capped. Production recommendation:
replace with statistical test (z-test, p<0.05, Δ̂>3pp).
```

### Edit 20: Standing Rules — Phase 7 Additions

Location: Edit 6 (standing rules).

Action: ADD:

```markdown
[NEW] Rule: RL-in-scorer CLOSED
  Four experiments, 6+ strategies: none beat uniform η=0.05.
  RL belongs in the sidecar, not in scorer η allocation.

[NEW] Rule: Logistic baseline curvature
  d²q/dt² > 0 for t < ~330 decisions (MEASURED). This is the
  natural shape of centroid convergence, not an RL effect.

[NEW] Rule: SA reasoning autonomy
  SA value = graph-mediated noise reduction (V-CGA-FROZEN +5.0pp).
  Noise redistribution does not help (SA-REASONING, negative).

[NEW] Rule: AE decision autonomy
  AE reduces adversarial non-recovery 57% → 14% (VALIDATED).
  Complements conservation.

[NEW] Rule: AE-GATE
  n_min=10 is underpowered (59% power, 44% FPR). Recommend
  statistical test. DESIGN FINDING.

[NEW] Rule: Self-computation precondition
  Level 1 requires current config above θ_min. Below it,
  conservation deadlocks calibration. CHARACTERIZED.

[NEW] Rule: Experiments lead code
  A theorem-vs-code mismatch is a discovery → roadmap item.
  Architectural value drives claims; experiments provide grounding.
```

### Edit 21: Claims Registry — Phase 7 Additions

Location: Edit 7 (claims registry).

Action: ADD:

```markdown
RL-SCORER (Scorer-Integrated RL):
  DEFINITIVELY CLOSED. Four experiments, 6+ strategies.
  Uniform η is robust. Sidecar is the right architecture.

LOGISTIC-CURVATURE:
  MEASURED. d²q/dt² > 0 for t < ~330 (logistic R²≈0.88).
  Baseline centroid convergence shape, not RL-directed.

SA-REASONING:
  NEGATIVE (wrong operationalization). Noise redistribution
  doesn't help under L2. SA value = noise reduction via graph
  (V-CGA-FROZEN +5.0pp).

AE-DECISION:
  VALIDATED. Non-recovery 57% → 14% (−42.5pp). Drift −60%.
  Recovery 1 decision. Rollback+damping 4-6× per seed.

SELF-COMPUTATION:
  Convergence: PROVED. Calibration: VALIDATED. Precondition:
  CHARACTERIZED. Dividend: production-scope pending.

SA-ABSTAIN:
  Safety primitive VALIDATED. 100% detection, <5% FP.
  Does not improve accuracy — safety gate.

AE-GATE:
  DESIGN FINDING. Strict-inequality gate underpowered.
  Recommend statistical test replacement.
```

---

## Updated Application Order

```
1-13.  Original v2.0 edits (unchanged order)
14.    Phase 7 experiment record
15.    RL sidecar + scorer-RL closure
16.    JM fourth cognitive type
17.    Self-computation formalism
18.    SA reasoning autonomy
19.    AE decision autonomy
20.    Standing rules (Phase 7)
21.    Claims registry (Phase 7)
Last:  Version history entry (bump to v20)
```

## Updated Verification After Application

```
□ Original v2.0 verification (all 12 checks from Edit 13)
□ grep "RL.*scorer.*positive\|directed.*η.*better" → 0 hits
□ grep "self-computation.*validated" → only in "calibration" context
□ grep "SA.*accuracy.*improve" → 0 hits (SA is safety, not accuracy)
□ grep "AE.*DECISION" → carries "42.5pp" and "VALIDATED"
□ grep "logistic.*curvature" → carries "MEASURED" and "t < ~330"
□ Phase 7 experiment count = 12 rows (entries 48-59)
□ Total experiment count ≈ 194 (59 primary + factorials)
```

---

*This edit list requires the math_synopsis_v18.md source file
to apply. Upload v18 to execute.*
