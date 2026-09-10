# VLD Implementation Review and Consolidated Design v3

Date: 2026-09-08

This document preserves the review of `vld_implementation_design_v2.md`, the exact proposed replacements, and a consolidated implementation design v3 assembled from those replacements. The original v2 document is unchanged. The consolidated design is a reviewed proposal, not a claim that its planned implementation has shipped.

## Review outcome

**Implementation design v2 is INSUFFICIENT for Phase 1b.** The main blockers are substantive: the real factor-provider path fails, the patterns do not perform distinct retrievals, the first dispatch is content-forced, and the experiments would conflate category classification with investigation value.

There is also an input-version problem: **the supplied `vld_implementation_design_v2.md` labels itself v1 and has no §3B.** Its §9 does not contain the simulation-derived architectural decisions described in the review request. All six v4 experiments were verified separately; their output cannot be compared against absent tables.

The underlying review created or changed no files and used no git or AGE connection. This companion report was subsequently created at the user's request.

## Review references

All paths are relative to:

`C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\`

| Alias | File |
|---|---|
| `D` | `copilot-sdk/docs/design/vld_implementation_design_v2.md` |
| `Arch` | `copilot-sdk/docs/design/vld_graph_reasoning_architecture_v3.md` |
| `Audit` | `copilot-sdk/docs/design/soc_rho_structural_feasibility_audit_2026-09-08.md` |
| `Demo` | `copilot-sdk/docs/design/demo_scenarios_and_usecases_v2_8.md` |
| `Sim4` | `copilot-sdk/scripts/vld_validation_sims_v4.py` |
| `Sim1` | `copilot-sdk/scripts/vld_validation_sims.py` |
| `Loop` | `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_loop.py` |
| `Router` | `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_router.py` |
| `Patterns` | `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_patterns.py` |
| `Models` | `gen-ai-roi-demo-v4-v50/backend/app/models/investigation.py` |
| `Tests` | `gen-ai-roi-demo-v4-v50/backend/tests/test_investigation_loop.py` |
| `Triage` | `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py` |
| `SOC/` | `gen-ai-roi-demo-v4-v50/backend/` |
| `SDK/` | `copilot-sdk/` |
| `S2P/` | `s2p-copilot/backend/` |

The audited design has **490 lines** and SHA-256:

```text
f378ea0a24cf44680c177f428eb90a37fd90c5d49c1ed43f39dc5a6b8da02800
```

Part G supplies the complete replacement text. References such as **G03** identify those replacements. The final appendix assembles them into a continuous design document.

## PART A: Accuracy corrections

| # | Doc says—exact text | Code shows, with evidence | Replacement text |
|---|---|---|---|
| A1 | `**Version:** v1 · **Date:** Sep 8, 2026` (`D:2`) | The named v2 file contains this header. §3.5 ends at `D:202`; §4 begins at `D:206`; no §3B exists. The v4 simulation is present and contains six experiments (`Sim4:236`, `301`, `368`, `425`, `487`, `544`). | **G01, G12:** correct document identity and insert the reproduced simulation review. |
| A2 | `ProfileScorer.score(v) → (action, confidence, category)` (`D:27`) | SOC requires a supplied category index: `score(..., category_index=...)`; missing category raises `TypeError` (`SOC/app/domains/soc/scorer_adapter.py:50–66`). The investigation loop separately chooses categories (`Loop:45`, `79`, `120`). | **G02:** “The scorer selects an action within a supplied category; investigation category selection is a separate policy.” |
| A3 | “The alert's explicit category label is NOT used.” (`D:91`) | `preferred = initial_category if step_index == 0 else None` (`Loop:55`). The router puts that category first (`Router:63–64`). `_resolve_category()` reads `category`, then `alert_type`, then defaults to category zero (`Loop:138–143`). | **G03:** “The current loop uses a content-forced first dispatch and geometry-ranked subsequent dispatches.” |
| A4 | `L_max = 3 (initial + 2 investigation reads)` (`D:97`) | `range(self.L_max)` allows **three pattern executions after initial extraction** (`Loop:43`, `54`). Endpoint and router both receive three (`Triage:514–520`). | **G03:** “L_max=3 caps pattern dispatches, excluding initial extraction and endpoint context reads.” |
| A5 | `RESIDUAL_THRESHOLD = 0.05` and “halt after 2 action changes” (`D:99–100`) | Threshold is `1.0e-3` (`Loop:14`). Oscillation stops when `flip_count > max_flips`, therefore after the **third** change with default two (`Loop:27`, `89`). | **G03/G05:** document the actual defaults and distinguish target residual from damped movement. |
| A6 | “Each pattern follows the SA interface (supports/execute)” (`D:104`) | Local protocol uses `supports(dict)` and asynchronous `execute(...)` (`Patterns:22–46`). SDK SA uses `supports(TypedIntent)` and `traverse(...) -> SituationContext` (`SDK/copilot_sdk/situation/patterns.py:11–27`). | **G04:** “These implement a SOC-local protocol; an SDK SA adapter remains [ASPIRATIONAL].” |
| A7 | `CredentialInvestigation`, `MalwareInvestigation`, `LateralMovementInvestigation`, etc. (`D:109–114`) | Actual classes are `CredentialInvestigationPattern`, `MalwareInvestigationPattern`, `LateralMovementPattern`, `ExfiltrationPattern`, `InsiderPattern`, `CloudInfraPattern` (`Patterns:109`, `126`, `142`, `158`, `175`, `191`). | **G04:** replacement table uses exact class names. |
| A8 | “queries ONLY existing graph schema nodes” and traversal table (`D:104–118`) | Every pattern calls the same `get_security_context(alert_id)` (`Patterns:69–82`). `graph_query` is placed in returned metadata, never executed (`Patterns:92`). Advertised IAM changes, connected assets and cloud-resource traversal are not implemented by these methods. | **G04:** distinguish executable retrieval from descriptive query metadata. |
| A9 | `factor_provider.compute({**alert, **evidence})` (`D:136`) | Actual call is `compute(alert_context, enriched_context)` (`Loop:72`). The real provider forwards the second argument as the graph object; pattern-history extraction calls `graph.run_query` (`SOC/app/services/triage_providers.py:28–34`; `SOC/app/domains/soc/factors.py:551`). | **G05:** specify an admitted-evidence adapter implementing the real provider’s graph contract. |
| A10 | “Scorer and centroids are FROZEN during investigation” (`D:154`) | The loop retains the live scorer reference (`Loop:33`) and awaits reads without acquiring the existing scorer lock. Endpoint calls the global getter (`Triage:468`). Lock exists at `SOC/app/services/gae_state.py:50–68`. | **G05:** “[ASPIRATIONAL] Capture an immutable episode model snapshot under the scorer lock.” |
| A11 | “Conservation is checked at EMIT” (`D:156`) | Model default is `conservation_emit_gate = "not_evaluated_read_only"` (`Models:43`); endpoint returns that value (`Triage:535`). No conservation evaluation occurs in this path. | **G02/G05:** distinguish diagnostic response from action authorization. |
| A12 | Trace schema at `D:174–201` | Existing model additionally contains `selected_edge` and `conservation_emit_gate`, plus serializers (`Models:19`, `27`, `43–48`). Logged propensity is `1 / len(candidates)` despite deterministic selection (`Router:84`). | **G07:** preserve actual fields, correct probability semantics, add missing episode/evidence references. |
| A13 | File sizes approximately 60/200/80/120/30 (`D:54–58`) | Actual files: models **48**, patterns **216**, router **89**, loop **162** lines. Endpoint function spans `Triage:453–536`, approximately **84**, not 30. | **G02:** corrected inventory. |
| A14 | “POST /api/soc/investigate … Endpoint test” (`D:369`) | The nine tests invoke the loop directly. None calls the endpoint (`Tests:82–233`). Their helper sets `eps=1.0` (`Tests:67`), unlike endpoint `eps=0.3` (`Triage:520`). | **G09:** “Nine direct loop tests; no endpoint or real-provider integration test in this file.” |
| A15 | Shared SDK components marked ✅ (`D:401–406`) | Loop/router/models are SOC-local, import SOC category constants, and have no corresponding shared implementation established by this design (`Loop:10–12`; `Router:10–11`; `Models:1`). | **G14:** mark SDK extraction and generic endpoint template **[ASPIRATIONAL]**. |

The suspected SOC naming errors are **not present** in this document: `insider_threat` and `privileged_identity_context` already match configuration. No replacement is needed for them.

Evidence: `D:109`, `113`; `SOC/app/domains/soc/config.py:92–98`, `120–126`.

### Executed checks supporting the corrections

All nine test functions were invoked directly in a bytecode-disabled Python process: **9 passed**. This was not a full pytest/backend-suite run.

The real factor provider was then exercised with an offline graph stub. The first re-extraction failed:

```text
RuntimeError: AGE query failed for pattern computation
Cause: AttributeError("'dict' object has no attribute 'run_query'")
```

Evidence: `Loop:72`; `SOC/app/domains/soc/factors.py:551–554`.

A separate no-read control produced:

```text
steps: 0
initial category: credential_access
final category: data_exfiltration
single-pass action: monitor
final action: investigate
agreement: false
```

The vector did not change. This follows from initial scoring in the supplied category and final scoring in the geometrically closest category (`Loop:45–46`, `119–133`). Consequently, **`agreement=false` does not establish evidence-driven depth value**.

## PART B: Completeness gaps

| # | Gap | What is needed—exact addition in Part G | Priority |
|---|---|---|---|
| B1 | Real-provider integration does not work. | **G03/G05:** admitted-evidence adapter, consistent alert normalization, real-provider verification. Evidence: `Loop:72`; factor graph calls cited above. | **P1** |
| B2 | Six pattern names conceal one common bulk read. | **G04:** distinct, bounded, parameterized retrievals; explicit returned node/edge IDs and evidence scope. Evidence: `Patterns:69–106`. | **P1** |
| B3 | No clean surface boundary. Endpoint loads full security context before investigation. | **G02/G05:** explicit S₀, shared first read and cumulative admitted-evidence snapshots; count initial reads. Evidence: `Triage:486`, `507–522`. | **P1** |
| B4 | E-ρ assumes fixture labels identify correct investigation branches. | **G08:** retain category recovery only as a diagnostic; require independently labelled branches for R1. Evidence: `SOC/app/seed/decisions.py:36–55`, `99–104`; `Audit:31–40`. | **P1** |
| B5 | E-ρsk proposes label stripping instead of conditional-case generation. | **G08:** latent-cause generator, ambiguous observable indicators, branch-specific evidence, independent labels, train/holdout split. Evidence: `D:240–245`; `Loop:138–143`. | **P1** |
| B6 | Trace fields exist but do not support replay or causal attribution. | **G07:** episode/model/evidence identifiers, actual selection probability, errors, outcome linkage, result-level stop reason. Evidence: `Models:10–43`; `Router:84`. | **P1** |
| B7 | Budget 0–6 experiment does not match endpoint configuration. | **G03/G05/G08:** explicit zero-read arm and configurable matched budgets. Current loop rejects `L_max=0`; endpoint fixes three (`Loop:29–30`; `Triage:514–520`). | **P1** |
| B8 | API contract is not documented beyond a table entry. | **G02:** request fields, response shape, errors, fixed configuration and diagnostic conservation status. Evidence: `Triage:453–536`; `SOC/app/models/schemas.py:33–37`. | **P1** |
| B9 | DataOps/S2P extension assumes incompatible category and graph names. | **G14:** actual taxonomies, schema adapters, temporal history and planted branch fixtures. Sources detailed below. | **P2** |
| B10 | Execution-plan dependency is unresolved. | **G01/G15:** mark `vld_execution_plan_v2.md` missing and use explicitly cited architecture gates pending reconciliation. | **P1** |

The R1 audit remains applicable to **data sufficiency**, even though the new Phase 1a files supersede its earlier “no controller” implementation inventory. New scaffolding does not create historical first-read observations or correct-branch labels.

Evidence: `Audit:418–432`; `Tests:30–42`, `218–228`.

## PART C: Consistency issues

| # | Design section | Companion section | Issue | Exact fix |
|---|---|---|---|---|
| C1 | §3.1 | `Arch` §2.2; `Demo` §4.17 | Design describes cross-category routing; SOC demo explicitly claims **branch selection within a supplied category**. Current first dispatch is content-forced. | **G03**, supported by `Loop:55`; `Demo:1025–1027`. |
| C2 | §3.3 | `Arch` §2.3 | Code halts on damped movement, whereas architecture specifies **update-target residual**. | **G05**; compare `Loop:76–89` with `Arch:88–93`. |
| C3 | §3.3 | `Arch` §2.3 | Emit gate is described as existing but is unevaluated in shadow output. | **G05**; `Models:43`; `Arch:81–86`. |
| C4 | §3.5 | `Arch` §2.4 | Deterministic selection is assigned a fictitious uniform propensity; no outcome reference or concrete evidence identity. | **G07**; `Router:84`; `Models:10–43`; `Arch:97–109`. |
| C5 | §4.1–4.2 | `Arch` §5.1; R1 | v₀ category matching and a fixed 0.5 gate replace post-first-read branch accuracy against the best comparator. | **G08**; `Arch:230–234`, `350–363`; `Loop:55`. |
| C6 | §4.3–4.6 | `Arch` §5.2 | Disagreement accuracy omits population coverage, conditional fraction, comparator utility and acquisition cost. | **G08**; `Arch:245–255`; `Loop:119–133`. |
| C7 | §5 | `Demo` §4.17 and §5 | Beat names are shortened, the mappings miss branch-specific content, and readiness upgrades conflict with demo gates. | **G13**; `Demo:73`, `908–916`, `1019–1067`. |
| C8 | §7/§9 | `Arch` R6 and roadmap | Multi-copilot extension is scheduled after synthetic gates, before required R4/R5 evidence. | **G11/G14**; `Arch:447–450`, `514–517`. |
| C9 | Claimed §3B | v4 simulation | §3B does not exist in the supplied artifact. | Insert **G12** using reproduced output, not reconstructed quotations. |
| C10 | §8 damping risk | `Arch` §5.3 | “Damping over-weights first read” is inaccurate for sequential exponential averaging: later reads receive more weight. | **G10/G12**; `Sim4:155`; `Arch:284–289`. |

The architecture’s assertion that μ mismatch necessarily biases ρ downward is itself stronger than the evidence permits. The design should retain the **measurement question**, not inherit a guaranteed direction.

Evidence: `Arch:113–121`; `Audit:590–603`; `Sim4:149–155`.

## PART D: Risks not adequately addressed

| # | Risk | Current mitigation | Recommended addition |
|---|---|---|---|
| D1 | Empty reads halt before a productive second branch. | Residual halt after each step; no explicit selector/negative-evidence continuation (`Loop:86–117`). Pattern results contain metadata even when no substantive evidence exists (`Patterns:82–97`). | **G05/G10:** distinguish empty, exhausted, failed and informative reads; zero vector movement alone cannot exhaust all branches. |
| D2 | Real provider fails or ignores enrichment. | Tests substitute `_FactorProvider`, keyed on `investigation_category` (`Tests:36–42`). Time/device factors read the first argument, while the loop keeps passing the original alert (`Loop:72`; `SOC/app/domains/soc/factors.py:606`, `647`). | **G05:** normalize enriched alert fields and preserve the graph interface through a scoped adapter. |
| D3 | Concurrent learning/reset changes episode geometry. | Existing scorer lock is not used by this path (`Triage:468`; `Loop:33`, `69`; `SOC/app/services/gae_state.py:50–78`). | **G05/G10:** immutable snapshot captured under lock; pin policy and conservation inputs. |
| D4 | “Read-only” endpoint initializes/persists state when scorer is absent. | Calls `_init_ls()` (`Triage:469–472`). Initialization can save state and capture provenance (`SOC/app/services/gae_state.py:360–368`). | **G02/G05:** require ready scorer; return 503 rather than initialize inside investigation. |
| D5 | Unbounded latency relative to investigation SLA. | No episode/step deadline. AGE has a 120-second statement timeout, not an investigation deadline (`Loop:69–72`; `ci-platform/ci_platform/graph/age_client.py:184`). | **G05/G10:** per-query cancellation and total deadline; charge failed/timed-out reads. |
| D6 | Trace count is bounded, evidence payload size is not. | Default three dispatches; registry has six patterns (`Loop:54`; `Patterns:207–216`). No result-size cap or measured byte budget. | **G07/G10:** bounded evidence payloads and trace references; explicit byte/query/node limits. |
| D7 | Exceptions abort without a complete terminal trace. | Bulk-context errors are converted into metadata (`Patterns:78–80`), but provider/custom-pattern exceptions propagate (`Loop:69–73`). | **G05/G07:** typed error outcomes and result-level halt reason, including zero-step results. |
| D8 | Category reassignment creates apparent value without new evidence. | No control; initial and final category policies differ (`Loop:45–46`, `119–133`). Reproduced above. | **G06/G08:** fixed scoring-category control and no-new-evidence arm. |
| D9 | Centroid initialization is mistaken for learned routing capability. | Tests use configured priors (`Tests:45–50`). S2P config repeats identical action centroids across categories (`S2P/app/domains/s2p/config.py:139–143`). | **G10/G14:** record model provenance; distinguish ties/initialization from measured routing skill. |
| D10 | Simulation interior-category failures are transferred to SOC. | No evidence supporting that transfer. Simulation category centers lie on one axis (`Sim4:95–100`); SOC tensor varies across factors (`SOC/app/domains/soc/config.py:153`). | **G12:** do not reduce real branches to improve simulated accuracy; derive available branches from evidence topology. |
| D11 | “70% neutral” is treated as measured reality. | It is a generator parameter; no SOC measurement supplies it (`Sim4:37–45`, `499–501`). | **G10/G12:** label hypothetical and measure missing/neutral/refuting evidence separately. |

## PART E: Experiment validity

| Experiment | Valid as specified? | Issue | Recommended fix |
|---|---|---|---|
| **E-ρ** | **No, as a ρ measurement.** | It measures v₀ category recovery. Current loop’s first dispatch already uses the category. R1 requires the next branch after first-read evidence. | **G08:** retain category recovery as `E-category`; measure branch correctness at S₁ against independently adjudicated labels. |
| **E-ρsk** | **No.** | Removing `category` leaves `alert_type`; removing both triggers category-zero fallback. Label removal also changes pattern-history extraction inputs. It does not create conditional structure. | **G08:** generate genuine ambiguous cases with controlled evidence reveal and a common extraction path. Sources: `Loop:138–143`; `SOC/app/domains/soc/factors.py:522`. |
| **E-Δ** | **No, as causal depth attribution.** | Action differences can occur with zero reads. Seed incorrect outcomes do not identify the correct alternative action. Selecting only disagreements hides population coverage. | **G06/G08:** matched evidence-budget policies, no-evidence control, valid terminal labels, whole-cohort utility plus disagreement diagnostics. Sources: `Loop:119–133`; `SOC/app/graph_schema.py:855–862`. |
| **E-budget** | **Partially.** | Dispatch count is genuinely enforced in router and loop, but node/query cost is only metadata; endpoint is fixed at three. The v4 breadth and re-extraction arms use different aggregators. | **G05/G06/G08:** separate dispatch/node/time budgets, support zero, use a routing × aggregation factorial. Sources: `Router:58`; `Loop:54`; `Patterns:94`; `Sim4:180–184`. |
| **E-μskew** | **No, as a degradation measurement.** | ‖vL−v₀‖ alone does not establish degraded routing. Current real-provider loop cannot produce a valid vL; surface-trained and full-evidence-trained models are not supplied. | **G08:** treat vector displacement as diagnostic; compare independently trained representations on the same held-out intermediate states. |

**Sample size:** the 432 campaign-linked seed rows represent **48 alerts in four campaigns**, not 432 independent investigations. No score-keyed hard-tail sample larger than 30 has been established. Even a P25 hard-tail slice would not automatically leave 30 independent qualifying alerts. Report the actual selected count and campaign dependence; do not manufacture power through nine synthetic repetitions.

Sources: `Audit:54–60`, `534–544`; `SOC/app/seed/decisions.py:67–78`.

Giving VLD additional evidence is appropriate for measuring **total investigation benefit**. It is insufficient for attributing that benefit specifically to **adaptive routing**. That attribution requires non-adaptive policies with the same available evidence, extraction, model and budget.

## PART F: Simulation review

The six experiment functions were executed with their default **5,000 cases**, without invoking `plot_results()`, which writes a PNG (`Sim4:682–703`). Both copies of the v4 script—the one under `scripts` and the one under `docs/design`—are byte-identical.

### Reproduced results

Because §3B is absent, the “reported finding” column refers to the finding requested in the review prompt, not an invented quotation from the document.

| Requested §3B section | Finding to verify | Code/output confirms? | Discrepancy or limitation |
|---|---|---|---|
| §3B.1 / Exp 1 | Neutral-fraction crossover | Raw Δ: **−0.0166 at 0.0; 0 at 0.1; +0.0144 at 0.2**. At 0.7: VLD **0.726**, single **0.636**. | Script prints crossover **≈0.0**, because it reports the lower endpoint of a negative-to-nonnegative interval (`Sim4:282–287`). A strict positive crossover is not established at 0.0. |
| §3B.2 / Exp 2 | ρ calibration | At parameter 0.60: VLD **0.706 [0.693, 0.719]**, content **0.794**, majority **0.634**, random **0.635**, single **0.632**. Correlation **0.926**; VLD beats single at **17/18** settings. | Parameter `rho_target` controls signal amplitude, not measured routing probability (`Sim4:60–62`). Content-rule accuracy exceeds VLD across this sweep; populations mix labelled/unlabelled cases. |
| §3B.3 / Exp 3 | Re-extraction versus damping at budget 3 | Neutral: **0.931 vs 0.913**. Mixed: **0.874 vs 0.815**. Misleading: **0.715 vs 0.548**. | Supports testing accumulated evidence. Does not support universal replacement: mixed budget 1 is **0.680 reext vs 0.717 damp**; misleading budget 6 is **0.001 vs 0.020**. |
| §3B.4 / Exp 4 | Always investigate at 70% neutral | Best tested gate **0.40**, accuracy **0.726**, investigates **100%**. Single **0.636**. | Accuracy-only, one hypothetical world, no acquisition cost and no held-out threshold selection (`Sim4:442–477`). |
| §3B.5 / Exp 5 | SOC optimal abstention threshold | SOC **0.35**, utility **−0.966**, commits **106/5,000**, committed accuracy **0.981**. | **97.88% abstention**. The threshold is an uncalibrated geometric margin, not confidence. |
| §3B.5 / Exp 5 | S2P/Trading thresholds | S2P **0.20**, utility **−0.368**; Trading **0.05**, utility **−0.086**. | Review costs are assumed, and thresholds are optimized/evaluated on the same sample (`Sim4:503–537`). |
| §3B.6 / Exp 6 | Routing breakdown | Overall **0.3762 = 1,881/5,000**. Categories 0–5: **0.805, 0.167, 0.149, 0.163, 0.144, 0.806**. | This is initial-surface category/branch matching at parameter `rho=0.6`, not post-first-read R1 ρ (`Sim4:566–573`). |
| §3B.6 / Exp 6 | Routing/action relationship | Correct-route action accuracy **0.961**; wrong-route **0.584**; single-pass **0.636**. Hardest quartile routing **0.298**; easiest **0.553**. | Useful synthetic decomposition, not proof of learned SOC routing quality. |
| §3B.8 | Scope limitations | No such section exists. | Add **G12**, including generator, comparator, margin, cost, sampling and platform-transfer limitations. |

### Re-extraction implementation

The code correctly implements this particular arithmetic operation:

```text
v_t = (s + sum(e_b for b in admitted)) / (1 + len(admitted))
```

It resets from the surface copy, adds each admitted branch once, and divides by the number of vectors (`Sim4:149–153`).

It does **not** execute SOC factor extraction from a cumulative graph snapshot. Consequently:

- Calling it “re-extraction” is a simulation analogy.
- Setting production `eps=1` is equivalent only if the candidate vector is actually extracted from the **entire admitted evidence set**.
- At budget three, damping weights are surface **0.343**, first evidence **0.147**, second **0.21**, third **0.30**. Averaging gives each **0.25**. The change affects both weighting and future routing.
- The breadth arm uses sequential damping rather than the same average (`Sim4:180–184`). A fair aggregation comparison must also run fixed-order and random routing with averaging.

### Penalty ratios

The base ratios do match platform presets:

| Copilot | Simulation | Platform evidence |
|---|---:|---|
| SOC | 20 | `SDK/copilot_sdk/scoring/presets/soc.py:60–61` |
| S2P | 5 | `SDK/copilot_sdk/scoring/presets/s2p.py:62–63` |
| Trading | 3 | `SDK/copilot_sdk/scoring/presets/trading.py:67–69` |

But the simulation’s abstention costs **1.0, 0.5, 0.3** are hardcoded assumptions (`Sim4:503–506`), not established platform review costs. Trading can also adjust its base ratio by regime (`SDK/apps/trading/backend/app/services/regime_scoring.py:292–294`).

The margin is the distance gap between the closest **two category-action centroids**, potentially representing the same action (`Sim4:102–114`). It is neither calibrated correctness probability nor necessarily an action margin.

### Additional validity limitations

- Neutral evidence is zero-mean noise, not an empty result or logical refutation (`Sim4:66–74`).
- The productive branch is planted as `correct_branch = true_cat`; its evidence directly encodes the correct action (`Sim4:54`, `68`).
- Resetting the RNG per neutral-fraction setting does not preserve identical cases: taking the neutral branch consumes an additional random draw (`Sim4:70–72`, `256`).
- Majority routing is selected using the evaluation world (`Sim4:261–262`, `326–327`).
- Bootstrap intervals cover VLD accuracy, not paired policy differences or parameter-selection uncertainty (`Sim4:329–331`).
- Category centers are arranged on one line in the toy model (`Sim4:95–100`). SOC’s configured category-center geometry is not that layout; an offline calculation found affine rank five.
- No simulation measures actual SOC neutral fraction, conditional-case prevalence, latency, or trained-model generalization.

The original two-branch script also remains only a scoped diagnostic. Its default budget sweep reproduced **0.871 VLD versus 0.686 breadth at budget 1**, but **0.840 versus 0.884 at budget 2**, and prints **“NEEDS INVESTIGATION”** under its own convergence test (`Sim1:339–374`).

**Architectural conclusions:** accumulated-evidence extraction deserves a controlled experiment; universal re-extraction, production always-investigate at “70% neutral,” transferable abstention thresholds, and reducing SOC branch count are **not established**.

## PART G: Recommended changes—mechanically applicable replacement text

The following replacements apply to the **hash-pinned 490-line input above**. Line intervals are inclusive and identify the exact old text; quoted boundary lines make the target explicit. Apply replacements against the original line numbering, from bottom to top. Inserts have an empty old span.

This avoids inventing quotations for the missing §3B.

### G01 — P1: Correct document identity and dependencies

**Old:** `D:2–7`, beginning:

```text
**Version:** v1 · **Date:** Sep 8, 2026
```

and ending:

```text
- Simulation: `vld_validation_sims.py`
```

**New:**

```markdown
**Version:** v3 · **Date:** Sep 8, 2026
**Status:** Phase 1a scaffold reviewed; Phase 1b measurement prerequisites remain open.

**Companion documents:**
- Architecture: `vld_graph_reasoning_architecture_v3.md`
- Data feasibility: `soc_rho_structural_feasibility_audit_2026-09-08.md`
- Demo authority: `demo_scenarios_and_usecases_v2_8.md`
- Execution gates: Architecture §8 and §10. `vld_execution_plan_v2.md`
  was not present in the audited checkout; its gates are not assumed.
- Simulations: `../../scripts/vld_validation_sims.py` and
  `../../scripts/vld_validation_sims_v4.py`

This revision distinguishes current implementation, [ASPIRATIONAL] work,
synthetic diagnostics, and empirical product evidence. The reviewed file
named v2 contained a v1 header and no §3B; §3B below records a fresh,
read-only reproduction of v4.
```

### G02 — P1: Replace the platform and built-component inventory

**Old:** `D:22–71`, from `### 2.1 Current platform (unchanged by VLD)` through the S2P patterns row.

**New:**

```markdown
### 2.1 Current SOC scoring and shadow endpoint

SOC factor extraction requires both an alert and a graph/context adapter.
The scorer selects an action within a supplied category; it does not
independently return an inferred category.

The current investigation endpoint is a diagnostic shadow path, not a
conservation-authorized action path. It loads alert and security context
before initial extraction, so its initial vector is not surface-only.

`POST /api/soc/investigate` accepts `ProcessAlertRequest`:
`alert_id`, optional `deployment_version="v3.1"`, and
`simulate_failure=False`. Investigation does not currently expose budget
or policy selection in this request.

The response contains `status`, `mode="vld_read_only_shadow"`, `alert_id`,
`single_pass`, `vld`, `investigation_trace`, and
`conservation_emit_gate="not_evaluated_read_only"`. Explicit errors include
503 for an unavailable scorer, 404 for missing alert/context, and 422 for
an unmapped alert type. A returned diagnostic action is not authorization
to execute it.

### 2.2 What Phase 1a actually built

| File | Current implementation | Audited lines |
|---|---|---:|
| `app/models/investigation.py` | Step/result dataclasses and serializers | 48 |
| `app/services/investigation_patterns.py` | Six named wrappers around the same bulk-context read | 216 |
| `app/services/investigation_router.py` | Raw Euclidean category ranking, preferred-category override, dispatch cap | 89 |
| `app/services/investigation_loop.py` | Initial comparison, damping, movement halt, trace assembly | 162 |
| `app/routers/triage.py:453–536` | Diagnostic investigate endpoint | 84 |

Nine direct loop tests exist. They use a fake factor provider and
`eps=1.0`; they do not establish endpoint or real-provider integration.

Current blockers: the first dispatch is content-forced; pattern queries
are metadata rather than distinct executed reads; re-extraction passes
a dictionary where graph methods are required; the live scorer is not
snapshotted; conservation is not evaluated; category reassignment can
change the action without any evidence read.

### 2.3 [ASPIRATIONAL] Phase 1b prerequisites

| Component | Required behavior |
|---|---|
| Admitted-evidence adapter | Support real factor computers while exposing only evidence already admitted |
| Distinct retrieval patterns | Execute bounded, parameterized reads with concrete evidence identities |
| Episode snapshot | Pin model, scoring configuration, policy and evidence time boundary |
| Branch policy | Separate supplied scoring category from investigation branch selection |
| Episode fixtures | S0, first read, candidate branches, branch evidence, independent ground truth and provenance |
| Comparator framework | Matched budgets/extraction/models; fixed-order, rule, majority, random and no-evidence controls |
| Measurement scripts | Separate category diagnostics, synthetic routing tests and empirical R1 |
| Trace contract | Accurate probabilities, costs, evidence references, errors, stopping reason and outcome linkage |
| Endpoint integration tests | Exercise the real provider with an offline graph implementation |
| SDK extraction | Generalize SOC-local classes only after their contracts are validated |

Persistent trajectory storage is required before persisted-trace demos
and longitudinal replay claims. DataOps/S2P extensions remain separate,
gated work.
```

### G03 — P1: Correct router semantics and define the intended policy

**Old:** `D:77–100`, from `### 3.1 InvestigationRouter — the VLD Ψ policy` through the flip-count configuration line.

**New:**

```markdown
### 3.1 InvestigationRouter — current policy and target contract

Current API:
`route_decision(v_t, scorer, investigated, *,
alert_context=None, preferred_category=None) -> RouteDecision`.
`route(v_t, scorer, investigated)` is a convenience wrapper.

`category_distances()` computes the minimum raw Euclidean distance to
each category's action centroids. It does not apply the scorer's
phase-dependent DK weighting or factor mask.

The loop passes its resolved alert category as `preferred_category` for
the first dispatch. Subsequent dispatches use geometry among eligible,
unvisited categories. Therefore the current loop is hybrid:
content-forced first read, geometry-ranked later reads. It is not
label-independent routing.

Current defaults: L_max=3 pattern dispatches after initial extraction;
eps=0.3; residual_threshold=0.001; max_flips=2 with halt when the count
exceeds two. L_max does not count endpoint context reads, factor queries,
or evidence nodes. The router also enforces its own dispatch cap.

[ASPIRATIONAL] The measured policy operates over available investigation
branch IDs, not interchangeable names for scoring categories. For the
SOC demo, keep the supplied scoring category fixed and choose among
within-category branches. Treat cross-category reclassification as a
separate experiment with the same policy in every comparison arm.

Freeze the first-read protocol before measuring R1. Measure the next
branch selected from S1/v1. A content-selected first read is permitted
but must not be counted as successful score-keyed routing.

The distance metric, tie-breaking, eligibility rules, unknown-category
handling and any learned policy parameters must be versioned. Unknown
categories must not silently become `credential_access`.
```

### G04 — P1: Replace the pattern table and schema claim

**Old:** `D:102–118`, from `### 3.2 Investigation Patterns — category-specific evidence retrieval` through the sentence ending `nodes (don't exist).`

**New:**

```markdown
### 3.2 Investigation patterns — current wrappers and required retrievals

Current patterns implement the SOC-local
`supports(alert_context)` / `execute(alert_context, graph_store)`
protocol. They do not implement the SDK SA `TypedIntent` /
`traverse(...) -> SituationContext` protocol.

All six currently call `get_security_context(alert_id)` and merge the
same bulk context. Their `graph_query`, `traversal`, `selected_edge` and
`enriched_factors` fields describe intended reads; they do not execute
or enforce those reads.

| Class | Category | Edges named in its descriptive query |
|---|---|---|
| CredentialInvestigationPattern | credential_access | INVOLVES, CLASSIFIED_AS, HAS_INDICATOR |
| MalwareInvestigationPattern | malware_execution | HAS_INDICATOR, CLASSIFIED_AS |
| LateralMovementPattern | lateral_movement | DETECTED_ON, MEMBER_OF |
| ExfiltrationPattern | data_exfiltration | DETECTED_ON, HAS_INDICATOR, MEMBER_OF |
| InsiderPattern | insider_threat | INVOLVES, MEMBER_OF |
| CloudInfraPattern | cloud_infrastructure | DETECTED_ON, CLASSIFIED_AS |

The SOC seed writer creates Alert→User INVOLVES, Alert→Asset DETECTED_ON,
Alert→AttackPattern CLASSIFIED_AS, Alert→ThreatIndicator HAS_INDICATOR,
and Alert→Campaign MEMBER_OF. These edges do not establish User→IAM,
Asset→Asset, Process, Session or CloudResource traversal.

[ASPIRATIONAL] Implement distinct, alert/domain/time-scoped retrievals
and an explicit SDK SA adapter. Return concrete node/edge IDs, evidence
values, observation timestamps, read status and measured cost. Do not
treat query-description strings or metadata keys as admitted evidence.
Tests must prove that selecting different branches can expose different
information and cannot silently fetch all branches.
```

### G05 — P1: Replace loop algorithm and invariants

**Old:** `D:120–157`, from `### 3.3 Investigation Loop — the VLD executor` through `- Trace is complete and auditable`.

**New:**

```markdown
### 3.3 Investigation loop — current behavior and target contract

Current API:
`await InvestigationLoop(scorer, router, factor_provider,
L_max=3, eps=0.3, residual_threshold=0.001, max_flips=2)
.investigate(alert_context, graph_store)`.

Current code computes the initial vector with a graph object, then calls
`factor_provider.compute(alert_context, enriched_context)` with a dict.
This fails for real factor computers requiring `run_query`; Phase 1b
must correct that integration before producing measurements.

Current updates are clipped damped updates:
`v_next = clip((1-eps)*v + eps*v_candidate, 0, 1)`.
The implemented residual measures the damped movement, not the
architecture's update-target residual.

[ASPIRATIONAL] Target episode:

1. Require an initialized scorer. Capture immutable model and policy
   snapshots under the scorer lock; release the lock before I/O.
   Do not initialize, learn, reset or persist scoring state in this path.
2. Construct an explicit initial observation S0. Supply the real factor
   provider with an evidence-scoped adapter implementing its graph
   methods. Initial and subsequent extraction must share one schema.
3. Enforce both dispatch and acquisition budgets, including initial
   reads and factor/provenance queries. Budget zero returns the initial
   comparison result unchanged.
4. Select an eligible branch using the frozen policy. Before dispatch,
   enforce the remaining budget and deadline. Record its true selection
   probability, not a uniform probability for deterministic selection.
5. Execute the bounded read. Record empty, exhausted, failed, timed-out
   and informative reads distinctly. Charge attempted reads.
6. Add new evidence to a deduplicated, versioned admitted set. Normalize
   enriched alert fields and expose graph evidence through the adapter.
   Compute the candidate vector from that cumulative set.
7. Apply the preregistered aggregation policy. Compare cumulative
   extraction and damping as experimental arms; eps=1 alone is not
   cumulative extraction.
8. Compute target residual
   `norm(v_candidate-v)/max(norm(v), floor)`.
   Halt using budget, deadline, oscillation and justified convergence.
   Zero movement from an empty/selector read does not alone prove that
   no productive eligible branch remains.
9. Final scoring uses the same scoring-category policy as the comparison
   arm. Always return a result-level stopping reason, including failures
   and zero-step episodes.
10. Return diagnostics without action authorization. A future actionable
    path must apply the authoritative conservation emit gate separately;
    it must not use conservation as a per-step stopping test.

No learning is permitted within an episode. Model/policy/evidence
versions must remain pinned. Trace construction must survive read or
extraction failures. Episode and per-query timeouts require cancellation;
the database statement timeout is not the episode latency budget.
```

### G06 — P1: Replace comparator definitions

**Old:** `D:159–168`, the entire `### 3.4 Comparison Policies (for experiments)` section.

**New:**

```markdown
### 3.4 Comparison policies

All routing comparisons share the same S0, first-read protocol,
available evidence, factor extraction, frozen model, scoring-category
policy, aggregation arm, conservation treatment and acquisition budget.

| Policy | Definition |
|---|---|
| VLD | Preregistered state-conditioned next-branch policy |
| Content-rule | Strongest available diagnostic rule using the same visible evidence |
| Majority-branch | Branch frequencies estimated from training cases, conditioned on relevant category/entity context |
| Random | Uniform selection among currently eligible branches, with a recorded RNG seed |
| Fixed-order/breadth | Non-adaptive ordering truncated to the same budget |
| Exhaustive | All eligible evidence with the same aggregation; report full cost |
| Single-pass | Current production comparison plus a separately identified surface-only ablation |
| No-new-evidence | Identical rescoring/category logic with no newly admitted evidence |

Breadth is not an accuracy upper bound when irrelevant evidence can
harm aggregation. Single-pass is not an accuracy lower bound.

Run routing × aggregation comparisons: every routing policy must be
tested with the same cumulative-extraction and damping choices.
Disagreement produced solely by category reassignment is not depth value.
```

### G07 — P1: Replace trace specification

**Old:** `D:170–202`, the complete trace-model section.

**New:**

```markdown
### 3.5 Investigation trace contract

Current `InvestigationStep` fields are:
step, pattern, v_before, v_after, cat_distances_before,
cat_distances_after, evidence_keys, candidate_reads, selected_edge,
propensity, cost, timestamp, policy_version, residual, halt_reason.
`halt_reason` defaults to None; `to_dict()` serializes the dataclass.

Current `InvestigationResult` fields are:
action, confidence, category, trace, v_final, steps,
single_pass_action, single_pass_confidence, agreement, fixture_source,
conservation_emit_gate. The gate defaults to
`not_evaluated_read_only`; the result has a serializer.

Current `selected_edge` is an edge-type string, not a concrete traversed
edge. Current cost is context metadata, not measured acquisition cost.
Current propensity is incorrect: deterministic first-choice selection
logs 1/N.

[ASPIRATIONAL] Extend the episode record with:
- episode_id, alert_id, decision/outcome references and provenance;
- model/checkpoint, feature-schema, policy and evidence-snapshot versions;
- S0 and cumulative evidence references with as-of timestamps;
- eligible candidate IDs, selected branch and concrete node/edge IDs;
- selection_mode and actual conditional selection probability:
  deterministic selection has probability 1 and no exploration support;
- action/category/confidence/margin before and after each read;
- read status, error, new-evidence count, elapsed time and budget usage;
- target residual and movement residual as separate quantities;
- result-level stop_reason, including zero-step and failed episodes;
- conservation snapshot/status and whether actionable emission occurred.

Record true empty reads separately from metadata-only responses.
Keep evidence payloads bounded and store references to larger snapshots.
Attach outcomes later without rewriting the original trajectory.
Deterministic traces do not identify counterfactual step-level credit.
```

### G08 — P1: Replace experiment specification and gates

**Old:** `D:206–327`, from `## 4. Experiments — Quantified Value Targets` through the final E-μskew summary row.

**New:**

```markdown
## 4. Experiments and evidence gates

### 4.0 Data feasibility and shared protocol

The R1 audit found 4,862 synthetic outcome-labelled seed decisions,
including 432 campaign-linked rows representing 48 alerts in four
campaigns. It did not establish an evaluable score-keyed investigation
sample. Nine synthetic decisions per alert are not independent episodes.

Seed correctness is not an observed branch label. Incorrect seed rows
do not necessarily identify the correct alternative action. Do not
derive ground truth from the same centroids used by the evaluated policy.

Every routing episode requires S0, an ordered first read, S1, available
next branches, independently adjudicated productive branches, evidence
timestamps, frozen model/policy versions and a valid outcome where
terminal utility is evaluated. Without these, report NOT MEASURABLE.

Use campaign/entity/time-disjoint training, validation and test sets.
Fit majority policies and thresholds only on training/validation data.
Report the hard-tail selection rule, independent case count, campaign
count, exclusions and uncertainty. n>30 is not a sufficient power
criterion; plan power for the paired improvement of interest.

### 4.1 E-ρ: Empirical next-branch routing accuracy

ρ is the probability that the policy selects a productive next branch
from the scorer state after the common first evidence read, S1/v1.

Category recovery from labelled S0 fixtures is a separate E-category
diagnostic. It is not empirical ρ and cannot establish the content-keyed
fraction of conditional investigation.

Success requires positive held-out improvement over the best
budget-appropriate rule, majority, fixed-order or other strong adaptive
comparator, with paired uncertainty. Random routing is a sanity check;
its expected accuracy depends on the eligible and acceptable branch sets.

### 4.2 E-ρsk: Synthetic conditional investigation

Build a planted, versioned generator with latent causes, ambiguous
observable indicators, multiple available branches, branch-specific
evidence, and independent productive-branch labels. Include empty,
refuting and misleading reads and useful second reads after a neutral
first read. Do not use evaluated-centroid proximity as the label oracle.

Removing category or alert_type fields is a leakage ablation, not a
method for creating score-keyed cases. Preserve the same extraction
schema and prevent labels, IDs or aliases from exposing the answer.

Run the E-ρ comparator protocol on held-out planted cases. Report
synthetic results as instrument validation, not customer ρ or market
prevalence. No universal 0.5 threshold is used.

### 4.3 E-Δ: Incremental investigation utility

Evaluate all preregistered eligible episodes, not only disagreements.
Use valid terminal-action labels and domain-specific action/review costs.

Report:
- whole-cohort paired accuracy and net utility differences;
- disagreement rate and conditional disagreement accuracy;
- read cost, latency, abstention, coverage and harmful-action rate;
- no-new-evidence and fixed-category controls;
- matched-budget adaptive versus non-adaptive comparisons.

Total benefit from extra evidence and benefit specifically attributable
to adaptive routing are separate estimands.

The value claim is:
`htail * m_cond * E[g(ρ)] - acquisition_cost > 0`,
where g is measured against the best budget-appropriate comparator.
Synthetic results alone do not establish population htail or m_cond.

### 4.4 E-budget: Cost-constrained policy comparison

Support an explicit zero-read arm and sweep available dispatch, node/
query and time budgets. Count all evidence acquisition, including initial
context and factor/provenance queries. Enforce limits before dispatch.

Cross every routing policy with the same aggregation choices. Exhaustive
arms use the same admitted set and order-independent extraction when
testing whether routing differences disappear at full coverage.

Report policy utility, accuracy, coverage, actual cost and latency at
each budget. Do not require a preselected advantage peak at budget 1–2.
Full-budget equality is a control under identical evidence and
aggregation, not a universal theorem about noisy evidence.

### 4.5 E-μskew: Representation ablation

First report paired v0/v1/vL displacement on valid evidence snapshots.
Vector displacement alone does not establish degraded routing.

To measure skew, train surface/intermediate and full-evidence centroid
models on the same training episodes under controlled label, kernel and
learning settings. Evaluate both on identical held-out intermediate
states and branch policies. Report routing and utility differences.

If paired states or independently trained models are absent, report
the skew effect as NOT MEASURABLE. Do not assume its sign.

### 4.6 Progression gates

1. Integration gate: real-provider replay, distinct admitted evidence,
   immutable episode state, correct trace and enforced budgets.
2. Synthetic gate: valid conditional generator and fair, held-out
   comparator tests; permits further research, not a product claim.
3. Empirical R1/R2 gate: score-keyed conditional cases exist and routing
   exceeds the best comparator with adequate evidence.
4. R4 gate: positive net depth value against rule-based investigation.
5. R5/R6 gate: measured workflow benefit before product extension to
   other copilots. Insufficient data is inconclusive, not a negative
   result about VLD's addressable market.
```

### G09 — P1: Replace verification claims

**Old:** `D:360–391`, the complete §6 verification section.

**New:**

```markdown
## 6. Verification plan

### 6.1 Current evidence

`test_investigation_loop.py` contains nine direct loop tests. They passed
when invoked directly during this review. They use a fake factor
provider and eps=1.0. No endpoint test exists in that file. This review
did not run or certify the full SOC backend suite.

The existing centroid-immutability test shows that the isolated loop
does not update its test scorer. It does not prove snapshot isolation
against concurrent learning/reset or absence of startup persistence.

### 6.2 Required before measurement

- Real provider plus offline graph adapter completes multiple reads.
- Branches expose distinct evidence and cannot read future/unselected data.
- Endpoint exercises request/response and 404/422/503/error paths.
- Production eps=0.3 and cumulative-extraction arms are both tested.
- Label-independent branch mode cannot use category aliases as answers.
- No-evidence and zero-budget episodes preserve the comparison result.
- Empty first read can continue when another eligible branch is useful.
- Target residual, flip limit and acquisition budgets enforce their contracts.
- Query/episode deadlines and failures produce complete terminal traces.
- Deterministic probabilities and actual read costs are logged correctly.
- Concurrent learning/reset cannot alter the episode snapshot.
- Investigation performs no model initialization, learning or persistence.
- Diagnostic output cannot be mistaken for conservation-authorized action.

### 6.3 Experiment verification

Validate episode labels independently, split by campaign/entity/time,
fit comparators without test leakage, use identical evidence and
aggregation controls, and report paired uncertainty and coverage.
Pin script, dataset, model and policy versions with every result.
```

### G10 — P1: Replace risk register

**Old:** `D:441–450`, the complete risk register.

**New:**

```markdown
## 8. Risk register

| Risk | Required mitigation |
|---|---|
| Synthetic labels mistaken for observed branch truth | Separate planted instrument tests from empirical R1 |
| Empty read causes premature convergence | Track exhaustion and selector information; permit justified continuation |
| Graph object replaced with evidence dict | Use a real-provider-compatible admitted-evidence adapter |
| Different names return identical bulk evidence | Verify distinct branch retrieval and concrete evidence identities |
| Category reassignment creates action disagreement | Fixed-category and no-new-evidence controls |
| Concurrent model changes | Immutable snapshot captured under the scorer lock |
| Initialization writes during a diagnostic request | Require ready state; return 503 |
| Slow queries or oversized evidence | Cancellation, total deadline and bounded payload/query/node budgets |
| Exceptions erase the trajectory | Typed read/extraction errors and result-level stop reason |
| Untrained, tied or stale centroids | Record model provenance; report ties and measured routing rather than assuming chance |
| Uniform averaging or damping amplifies misleading evidence | Matched routing × aggregation experiments |
| Assumed 70% neutral fraction | Label hypothetical; measure real empty/neutral/refuting evidence distributions |
| In-sample abstention tuning | Held-out calibration, measured review cost, coverage and harmful-action reporting |
| No outcome or insufficient independent cases | Report NOT MEASURABLE/inconclusive; do not manufacture sample size |
```

### G11 — P1: Replace implementation sequence

**Old:** `D:454–477`, the complete §9 sequence.

**New:**

```markdown
## 9. Implementation sequence

CURRENT:
- SOC-local loop/router/pattern/model/endpoint scaffolding exists.
- Nine fake-provider loop tests pass.
- Real-provider integration, distinct retrieval, episode isolation and
  empirical measurement prerequisites are not complete.
- v4 simulations are synthetic diagnostics; see §3B limitations.

PHASE 1b-A — repair the measurement substrate:
- Implement the admitted-evidence adapter and distinct bounded reads.
- Separate scoring category, branch policy and first-read protocol.
- Add immutable model/policy snapshots, correct trace semantics,
  zero-read controls, acquisition budgets and deadlines.
- Complete real-provider and endpoint verification.
- Design trajectory/outcome linkage before replay or persisted demos.

PHASE 1b-B — validate the instrument:
- Build independently labelled planted conditional episodes.
- Implement matched-budget comparator and aggregation arms.
- Run E-category, synthetic E-ρsk, E-Δ, E-budget and representation
  diagnostics. Do not label these empirical R1.
- Retain both damping and cumulative extraction until controlled
  experiments justify selection; no universal always-investigate
  or simulation-derived abstention threshold is adopted.

EMPIRICAL VALIDATION:
- Acquire as-of episode data and independent branch labels for R1/R2.
- Run R4 shadow comparisons without executing VLD recommendations.
- Measure R5 workflow benefit and apply R6 extension gates.

MULTI-COPILOT:
- DataOps/S2P planted architecture previews may be researched separately.
- Product extension follows the architecture's R4/R5/R6 gates.
- Neural controllers and production claims remain contingent.

Do not promise a one-slot empirical result: data acquisition, annotation
and adequate independent sample size are prerequisites.
```

### G12 — P1: Insert the missing simulation section

**Old:** empty span. **Insert after original `D:204`, before §4.**

**New:**

```markdown
## 3B. Simulation v4: reproduced results and scope

Defaults: 5,000 synthetic cases, eight dimensions and six branches.
The six experiment functions were reproduced without plot-file writes.
`rho_target` is a signal-amplitude parameter, not measured routing ρ.

### 3B.1 Neutral-fraction sweep

At neutral fractions 0.0, 0.1 and 0.2, VLD-minus-single accuracy is
-0.0166, 0.0000 and +0.0144 respectively. At 0.7, VLD is 0.726 and
single-pass is 0.636.

The script prints crossover ≈0.0 because it reports the lower endpoint
of the negative-to-nonnegative interval. Report the raw grid values:
tie at 0.1; first tested strict improvement at 0.2. This is not an
estimated production threshold. The neutral fraction is hypothetical.

### 3B.2 Signal-parameter sweep

At parameter 0.60:
VLD=0.706 [0.693, 0.719], content-rule=0.794, majority=0.634,
random=0.635, single=0.632. Correlation between parameter and
VLD-minus-single gain is 0.926; VLD beats single at 17/18 settings.

The content comparator exceeds VLD across this sweep, which mixes
labelled and unlabelled cases. Report those populations separately.
The parameter must not be substituted for empirical routing accuracy.

### 3B.3 Aggregation and budget

| Evidence regime | Budget | VLD damping | VLD accumulated average |
|---|---:|---:|---:|
| All neutral | 3 | 0.913 | 0.931 |
| Mixed 70/30 | 3 | 0.815 | 0.874 |
| All misleading | 3 | 0.548 | 0.715 |
| Mixed 70/30 | 1 | 0.717 | 0.680 |
| All misleading | 6 | 0.020 | 0.001 |

The implementation called re-extraction averages the initial surface
vector and all admitted evidence vectors. It correctly implements that
arithmetic operation; it does not run production graph factor extraction.

Damping gives later evidence greater weight. At three reads with eps=.3,
weights are .343 for surface and .147/.21/.30 for successive reads.
The accumulated average gives each vector .25.

The breadth arm uses fixed-order damping. Therefore comparing it with
VLD accumulated averaging changes both routing and aggregation. Run the
same aggregation under every routing policy before selecting a default.
These results do not establish that cumulative extraction always wins.

### 3B.4 Selective investigation

At the hypothetical 70% neutral setting and one-read budget, the best
tested margin gate is 0.40: all cases are investigated, accuracy 0.726,
versus 0.636 single-pass. This is an accuracy-only, in-sample result
without acquisition cost. It does not authorize always-investigate in SOC.

### 3B.5 Abstention utility

| Scenario | Error penalty | Assumed abstention cost | Best tested margin | Utility |
|---|---:|---:|---:|---:|
| SOC | 20 | 1.0 | 0.35 | -0.966 |
| S2P | 5 | 0.5 | 0.20 | -0.368 |
| Trading | 3 | 0.3 | 0.05 | -0.086 |

Base penalty ratios match SDK presets. Abstention costs are assumptions,
not measured platform costs. SOC commits 106/5,000 cases at its selected
threshold: 97.88% abstention and 0.981 accuracy among committed cases.

The margin is a gap between two category-action centroid distances,
not calibrated correctness probability. Thresholds are selected and
evaluated on the same sample. Do not transfer them to platform confidence
gates; calibrate on held-out domain data with measured costs and coverage.

### 3B.6 Routing breakdown

At signal parameter 0.6, actual initial routing accuracy is
1,881/5,000 = 0.3762.

Per-category accuracy, categories 0–5:
0.805, 0.167, 0.149, 0.163, 0.144, 0.806.
Hardest margin quartile: 0.298; easiest: 0.553.
Action accuracy conditional on correct routing: 0.961;
conditional on incorrect routing: 0.584.

The toy category centers lie on one axis, giving edge categories different
decision regions from interior categories. This does not establish the
same failure pattern in SOC or justify reducing its branch count.
Available branches must follow the investigation problem.

### 3B.7 Architectural decisions

Retain cumulative extraction as an experimental candidate alongside
damping. Do not adopt universal always-investigate, fixed simulation
abstention thresholds, or a smaller branch registry from these results.
Require matched aggregation, cost-sensitive evaluation and held-out
evidence before choosing a production policy.

### 3B.8 What these simulations do not establish

- Empirical post-first-read R1 ρ, hard-tail prevalence or conditional density.
- Real SOC neutral/empty/refuting evidence frequencies.
- Production factor-provider integration or trained-centroid quality.
- Fair adaptive-versus-breadth attribution when aggregation differs.
- Held-out abstention calibration, measured review cost or latency.
- Counterfactual credit from deterministic trajectories.
- A universal crossover, aggregation winner or optimal branch count.

Correct branches and action-revealing evidence are planted. Neutral
evidence is noise, not an empty result. RNG consumption changes across
neutral regimes; cases are not strictly paired across the sweep.
Majority choice uses the evaluation world. Bootstrap intervals cover
VLD accuracy, not paired policy gains or threshold-selection uncertainty.

The original two-branch script remains a separate diagnostic. Its
default budget sweep reproduced VLD/breadth 0.871/0.686 at budget 1 and
0.840/0.884 at budget 2, with its own verdict NEEDS INVESTIGATION.
Neither simulation version establishes customer value.
```

### G13 — P2: Replace demo integration

**Old:** `D:331–356`, the complete §5 section.

**New:**

```markdown
## 5. Demo integration

Use `demo_scenarios_and_usecases_v2_8.md` §4.17 as the storyboard authority.

| Beat | Exact name | Demonstration and evidence requirement |
|---|---|---|
| VLD-SOC-1 | The Investigation Trace | Mixed indicators; score-keyed branch choice within a supplied category; persisted evidence/order trace |
| VLD-SOC-2 | The Wrong-First-Step Recovery | Empty auth read followed by productive alternative; explicit two-branch budget; no superiority claim over exhaustive retrieval |
| VLD-DO-1 | Three Systems, One Root Cause | Schema-versus-upstream choice; subsequent lineage walk labelled CONTENT-KEYED / PREREQUISITE |
| VLD-DO-2 | Known Pattern, New Twist | Preregistered follow-known versus read-wide policy; both branches exercised |
| VLD-S2P-1 | The Supplier It Knew | Dual mismatch; receipt-first versus contract-first ordering; supplier ratio computed from time-filtered planted history |

Synthetic E-ρsk and trajectory verification support architecture previews.
Empirical E-ρ/E-Δ and matched-budget tests support routing/value claims.
No per-category agreement statistic substitutes for supplier-specific
or within-category branch correctness.

All five remain ARCH on planted fixtures until their implementation and
data prerequisites are met. Follow Demo's explicit readiness gates:
prototype plus trajectory store for NEAR; demonstrated R4 value against
rule-based routing for LIVE. R5 is required for time-savings claims.
A positive synthetic disagreement result does not automatically upgrade
all beats.

Always show PLANTED FIXTURE and ROUTING ACCURACY: not yet measured
where applicable. Compute contrast strips from the same episode.
Do not display hardcoded nodes_consulted as measured cost.

`resource_quota`, `partial_delivery` and `accept-with-adjustment` are
scenario concepts, not established current preset category/action names.
Map concepts explicitly to real schemas without silently adding tensor
axes. Distinguish confidence from margin in threshold captions.
```

### G14 — P2: Replace multi-copilot extension

**Old:** `D:395–437`, the complete §7 section.

**New:**

```markdown
## 7. [ASPIRATIONAL] Multi-copilot extension

### 7.1 Shared versus current implementation

Loop, router and trace models are currently SOC-local.
SDK generalization, shared endpoint templates and cross-copilot
measurement tooling remain planned. Remove direct SOC imports before
claiming a shared implementation.

### 7.2 DataOps

Actual preset shape: 6 categories × 5 actions × 6 factors.
Categories: schema_change, volume_anomaly, quality_anomaly,
freshness_violation, pipeline_failure, transform_drift.

The local graph contract/seed includes:
Decision-DECIDED_ON->Alert-DETECTED_IN->Pipeline;
Transformation-CONSUMES/PRODUCES->Dataset;
QualityRule-MONITORS->Dataset;
ProcessModel-CONTAINS->Activity-FOLLOWS->Activity;
Alert-TRIGGERED_BY->Activity.

The context graph client separately queries DataQualityAlert-AFFECTS->
PipelineSystem and PipelineSystem-FEEDS->PipelineSystem. These are
different representations; specify the chosen store and adapter rather
than composing an unverified path across them.

Schema changes such as MATKL_V2 exist in JSON evidence. The inspected
local contract/seed does not create a SchemaChange node. Upstream,
schema-history, quality, blast-radius and known-resolution patterns
require explicit evidence contracts and entity/time joins.

Current fixtures include labelled actions and root-cause descriptions,
not a complete independently labelled sequential-routing dataset.

### 7.3 S2P

Actual shape: 5 categories × 5 actions × 8 factors.
Categories: price_variance, quantity_mismatch, duplicate_risk,
contract_gap, format_compliance.

The inspected seed contract supports:
Decision-DECIDED_ON->Invoice;
Invoice-SUPPLIED_BY->Supplier;
Invoice-MATCHED_TO->PurchaseOrder;
Invoice-RECEIVED_AS->GoodsReceipt;
Invoice-GOVERNED_BY->ContractClause.

Receipt, pricing, supplier-history and delivery checks are branch IDs,
not additional category names. Contract amendments and shipment tracking
require new evidence contracts; their availability is not established
by the existing seed. The seed adds demonstration receipt/clause nodes
to the first invoice, not complete branch evidence for every invoice.

Reconcile the local seed contract with the live reader/migration schema.
The supplier prior-decision matcher requires an as-of cutoff. Do not
assume that current synthetic invoice vectors encode observed histories.

The configuration's initial action centroids repeat across categories;
category-distance ties must be detected. Record the actual runtime model
rather than assuming learned category separation.

### 7.4 Extension gate

Build copilot-specific planted episodes before measurement. Use the same
independent-label, matched-budget and held-out comparator requirements
as SOC; do not impose unexplained 0.5/0.4 routing thresholds or target
content-keyed fractions.

Product extension follows Architecture R4/R5/R6. Planted previews remain
separately labelled architecture work.
```

Evidence for this replacement: `SDK/copilot_sdk/scoring/presets/dataops.py:31–58`; `SDK/apps/dataops/backend/app/graph_contract.py:12–30`; `SDK/apps/dataops/backend/app/seed_graph.py:307–310`; `SDK/apps/dataops/backend/app/graph_queries.py:150–179`; `SDK/apps/dataops/backend/data/schema_changes.json:5–22`; `S2P/app/domains/s2p/config.py:20–46`, `139–143`; `S2P/app/graph_contract.py:128–140`; `S2P/app/seed_graph.py:273–310`; `S2P/app/services/s2p_context_builder.py:150–174`.

### G15 — P3: Replace relationship table

**Old:** `D:481–490`, the complete §10 section.

**New:**

```markdown
## 10. Relationship to companion documents

| Document | Authority and limitation |
|---|---|
| Architecture v3 | Controller placement, frozen episode state, C4, value model and R1–R6 gates |
| R1 structural feasibility audit | Offline data limitations; Phase 1a scaffolding does not supply missing historical branch labels |
| Demo scenarios v2.8 | Exact beat names, planted-data requirements, captions and readiness gates |
| Execution plan v2 | Not present in the audited checkout; reconcile before treating it as an additional authority |
| Original simulation | Two-branch synthetic instrument and budget diagnostic |
| Simulation v4 | Six-branch synthetic sensitivity/aggregation/abstention diagnostics, scoped in §3B |
| Phase 1b implementation prompt | Must implement the prerequisites and tests in this revision before reporting empirical measurements |
```

## PART H: Completeness verdict

**Implementation design v2 is INSUFFICIENT for Phase 1b.**

The P1 prerequisites are:

1. Correct the missing/version-mismatched simulation documentation.
2. Repair real-provider extraction and implement genuinely distinct evidence reads.
3. Separate scoring category, first-read policy and score-keyed investigation branches.
4. Pin episode state and enforce acquisition budgets, deadlines and valid stopping rules.
5. Correct trace probabilities, evidence identity, error handling and outcome linkage.
6. Keep diagnostic output separate from conservation-authorized action.
7. Replace fixture-category and label-stripping experiments with valid data and comparator specifications.
8. Add no-evidence/category controls and real-provider/endpoint verification.
9. Remove unsupported production conclusions from the simulation results.
10. Align progression with R1–R6 rather than synthetic accuracy thresholds.

**Simulation findings are INCORRECTLY reported in the supplied artifact in the sense that the claimed §3B report is missing.** Numerical agreement with its alleged tables cannot be assessed. The independently reproduced results are listed above; they support narrower conclusions than universal re-extraction, always-investigate, or transferable abstention thresholds.

---

# Consolidated Implementation Design v3

The following design incorporates G01–G15. The original v2 file remains unchanged. File/line evidence for the design decisions appears in Parts A–G above. Planned implementation remains marked [ASPIRATIONAL].

**Version:** v3 · **Date:** Sep 8, 2026
**Status:** Phase 1a scaffold reviewed; Phase 1b measurement prerequisites remain open.

**Companion documents:**
- Architecture: `vld_graph_reasoning_architecture_v3.md`
- Data feasibility: `soc_rho_structural_feasibility_audit_2026-09-08.md`
- Demo authority: `demo_scenarios_and_usecases_v2_8.md`
- Execution gates: Architecture §8 and §10. `vld_execution_plan_v2.md`
  was not present in the audited checkout; its gates are not assumed.
- Simulations: `../../scripts/vld_validation_sims.py` and
  `../../scripts/vld_validation_sims_v4.py`

This revision distinguishes current implementation, [ASPIRATIONAL] work,
synthetic diagnostics, and empirical product evidence. The reviewed file
named v2 contained a v1 header and no §3B; §3B below records a fresh,
read-only reproduction of v4.

---

## 1. Purpose

This document defines WHAT to build, HOW to verify it works, and
WHAT NUMBERS constitute success. Every component maps to an experiment
that produces a quantified result. No component exists without a
measurement plan.

---

## 2. System Architecture — What Exists and What's New

### 2.1 Current SOC scoring and shadow endpoint

SOC factor extraction requires both an alert and a graph/context adapter.
The scorer selects an action within a supplied category; it does not
independently return an inferred category.

The current investigation endpoint is a diagnostic shadow path, not a
conservation-authorized action path. It loads alert and security context
before initial extraction, so its initial vector is not surface-only.

`POST /api/soc/investigate` accepts `ProcessAlertRequest`:
`alert_id`, optional `deployment_version="v3.1"`, and
`simulate_failure=False`. Investigation does not currently expose budget
or policy selection in this request.

The response contains `status`, `mode="vld_read_only_shadow"`, `alert_id`,
`single_pass`, `vld`, `investigation_trace`, and
`conservation_emit_gate="not_evaluated_read_only"`. Explicit errors include
503 for an unavailable scorer, 404 for missing alert/context, and 422 for
an unmapped alert type. A returned diagnostic action is not authorization
to execute it.

### 2.2 What Phase 1a actually built

| File | Current implementation | Audited lines |
|---|---|---:|
| `app/models/investigation.py` | Step/result dataclasses and serializers | 48 |
| `app/services/investigation_patterns.py` | Six named wrappers around the same bulk-context read | 216 |
| `app/services/investigation_router.py` | Raw Euclidean category ranking, preferred-category override, dispatch cap | 89 |
| `app/services/investigation_loop.py` | Initial comparison, damping, movement halt, trace assembly | 162 |
| `app/routers/triage.py:453–536` | Diagnostic investigate endpoint | 84 |

Nine direct loop tests exist. They use a fake factor provider and
`eps=1.0`; they do not establish endpoint or real-provider integration.

Current blockers: the first dispatch is content-forced; pattern queries
are metadata rather than distinct executed reads; re-extraction passes
a dictionary where graph methods are required; the live scorer is not
snapshotted; conservation is not evaluated; category reassignment can
change the action without any evidence read.

### 2.3 [ASPIRATIONAL] Phase 1b prerequisites

| Component | Required behavior |
|---|---|
| Admitted-evidence adapter | Support real factor computers while exposing only evidence already admitted |
| Distinct retrieval patterns | Execute bounded, parameterized reads with concrete evidence identities |
| Episode snapshot | Pin model, scoring configuration, policy and evidence time boundary |
| Branch policy | Separate supplied scoring category from investigation branch selection |
| Episode fixtures | S0, first read, candidate branches, branch evidence, independent ground truth and provenance |
| Comparator framework | Matched budgets/extraction/models; fixed-order, rule, majority, random and no-evidence controls |
| Measurement scripts | Separate category diagnostics, synthetic routing tests and empirical R1 |
| Trace contract | Accurate probabilities, costs, evidence references, errors, stopping reason and outcome linkage |
| Endpoint integration tests | Exercise the real provider with an offline graph implementation |
| SDK extraction | Generalize SOC-local classes only after their contracts are validated |

Persistent trajectory storage is required before persisted-trace demos
and longitudinal replay claims. DataOps/S2P extensions remain separate,
gated work.

---

## 3. Component Design

### 3.1 InvestigationRouter — current policy and target contract

Current API:
`route_decision(v_t, scorer, investigated, *,
alert_context=None, preferred_category=None) -> RouteDecision`.
`route(v_t, scorer, investigated)` is a convenience wrapper.

`category_distances()` computes the minimum raw Euclidean distance to
each category's action centroids. It does not apply the scorer's
phase-dependent DK weighting or factor mask.

The loop passes its resolved alert category as `preferred_category` for
the first dispatch. Subsequent dispatches use geometry among eligible,
unvisited categories. Therefore the current loop is hybrid:
content-forced first read, geometry-ranked later reads. It is not
label-independent routing.

Current defaults: L_max=3 pattern dispatches after initial extraction;
eps=0.3; residual_threshold=0.001; max_flips=2 with halt when the count
exceeds two. L_max does not count endpoint context reads, factor queries,
or evidence nodes. The router also enforces its own dispatch cap.

[ASPIRATIONAL] The measured policy operates over available investigation
branch IDs, not interchangeable names for scoring categories. For the
SOC demo, keep the supplied scoring category fixed and choose among
within-category branches. Treat cross-category reclassification as a
separate experiment with the same policy in every comparison arm.

Freeze the first-read protocol before measuring R1. Measure the next
branch selected from S1/v1. A content-selected first read is permitted
but must not be counted as successful score-keyed routing.

The distance metric, tie-breaking, eligibility rules, unknown-category
handling and any learned policy parameters must be versioned. Unknown
categories must not silently become `credential_access`.

### 3.2 Investigation patterns — current wrappers and required retrievals

Current patterns implement the SOC-local
`supports(alert_context)` / `execute(alert_context, graph_store)`
protocol. They do not implement the SDK SA `TypedIntent` /
`traverse(...) -> SituationContext` protocol.

All six currently call `get_security_context(alert_id)` and merge the
same bulk context. Their `graph_query`, `traversal`, `selected_edge` and
`enriched_factors` fields describe intended reads; they do not execute
or enforce those reads.

| Class | Category | Edges named in its descriptive query |
|---|---|---|
| CredentialInvestigationPattern | credential_access | INVOLVES, CLASSIFIED_AS, HAS_INDICATOR |
| MalwareInvestigationPattern | malware_execution | HAS_INDICATOR, CLASSIFIED_AS |
| LateralMovementPattern | lateral_movement | DETECTED_ON, MEMBER_OF |
| ExfiltrationPattern | data_exfiltration | DETECTED_ON, HAS_INDICATOR, MEMBER_OF |
| InsiderPattern | insider_threat | INVOLVES, MEMBER_OF |
| CloudInfraPattern | cloud_infrastructure | DETECTED_ON, CLASSIFIED_AS |

The SOC seed writer creates Alert→User INVOLVES, Alert→Asset DETECTED_ON,
Alert→AttackPattern CLASSIFIED_AS, Alert→ThreatIndicator HAS_INDICATOR,
and Alert→Campaign MEMBER_OF. These edges do not establish User→IAM,
Asset→Asset, Process, Session or CloudResource traversal.

[ASPIRATIONAL] Implement distinct, alert/domain/time-scoped retrievals
and an explicit SDK SA adapter. Return concrete node/edge IDs, evidence
values, observation timestamps, read status and measured cost. Do not
treat query-description strings or metadata keys as admitted evidence.
Tests must prove that selecting different branches can expose different
information and cannot silently fetch all branches.

### 3.3 Investigation loop — current behavior and target contract

Current API:
`await InvestigationLoop(scorer, router, factor_provider,
L_max=3, eps=0.3, residual_threshold=0.001, max_flips=2)
.investigate(alert_context, graph_store)`.

Current code computes the initial vector with a graph object, then calls
`factor_provider.compute(alert_context, enriched_context)` with a dict.
This fails for real factor computers requiring `run_query`; Phase 1b
must correct that integration before producing measurements.

Current updates are clipped damped updates:
`v_next = clip((1-eps)*v + eps*v_candidate, 0, 1)`.
The implemented residual measures the damped movement, not the
architecture's update-target residual.

[ASPIRATIONAL] Target episode:

1. Require an initialized scorer. Capture immutable model and policy
   snapshots under the scorer lock; release the lock before I/O.
   Do not initialize, learn, reset or persist scoring state in this path.
2. Construct an explicit initial observation S0. Supply the real factor
   provider with an evidence-scoped adapter implementing its graph
   methods. Initial and subsequent extraction must share one schema.
3. Enforce both dispatch and acquisition budgets, including initial
   reads and factor/provenance queries. Budget zero returns the initial
   comparison result unchanged.
4. Select an eligible branch using the frozen policy. Before dispatch,
   enforce the remaining budget and deadline. Record its true selection
   probability, not a uniform probability for deterministic selection.
5. Execute the bounded read. Record empty, exhausted, failed, timed-out
   and informative reads distinctly. Charge attempted reads.
6. Add new evidence to a deduplicated, versioned admitted set. Normalize
   enriched alert fields and expose graph evidence through the adapter.
   Compute the candidate vector from that cumulative set.
7. Apply the preregistered aggregation policy. Compare cumulative
   extraction and damping as experimental arms; eps=1 alone is not
   cumulative extraction.
8. Compute target residual
   `norm(v_candidate-v)/max(norm(v), floor)`.
   Halt using budget, deadline, oscillation and justified convergence.
   Zero movement from an empty/selector read does not alone prove that
   no productive eligible branch remains.
9. Final scoring uses the same scoring-category policy as the comparison
   arm. Always return a result-level stopping reason, including failures
   and zero-step episodes.
10. Return diagnostics without action authorization. A future actionable
    path must apply the authoritative conservation emit gate separately;
    it must not use conservation as a per-step stopping test.

No learning is permitted within an episode. Model/policy/evidence
versions must remain pinned. Trace construction must survive read or
extraction failures. Episode and per-query timeouts require cancellation;
the database statement timeout is not the episode latency budget.

### 3.4 Comparison policies

All routing comparisons share the same S0, first-read protocol,
available evidence, factor extraction, frozen model, scoring-category
policy, aggregation arm, conservation treatment and acquisition budget.

| Policy | Definition |
|---|---|
| VLD | Preregistered state-conditioned next-branch policy |
| Content-rule | Strongest available diagnostic rule using the same visible evidence |
| Majority-branch | Branch frequencies estimated from training cases, conditioned on relevant category/entity context |
| Random | Uniform selection among currently eligible branches, with a recorded RNG seed |
| Fixed-order/breadth | Non-adaptive ordering truncated to the same budget |
| Exhaustive | All eligible evidence with the same aggregation; report full cost |
| Single-pass | Current production comparison plus a separately identified surface-only ablation |
| No-new-evidence | Identical rescoring/category logic with no newly admitted evidence |

Breadth is not an accuracy upper bound when irrelevant evidence can
harm aggregation. Single-pass is not an accuracy lower bound.

Run routing × aggregation comparisons: every routing policy must be
tested with the same cumulative-extraction and damping choices.
Disagreement produced solely by category reassignment is not depth value.

### 3.5 Investigation trace contract

Current `InvestigationStep` fields are:
step, pattern, v_before, v_after, cat_distances_before,
cat_distances_after, evidence_keys, candidate_reads, selected_edge,
propensity, cost, timestamp, policy_version, residual, halt_reason.
`halt_reason` defaults to None; `to_dict()` serializes the dataclass.

Current `InvestigationResult` fields are:
action, confidence, category, trace, v_final, steps,
single_pass_action, single_pass_confidence, agreement, fixture_source,
conservation_emit_gate. The gate defaults to
`not_evaluated_read_only`; the result has a serializer.

Current `selected_edge` is an edge-type string, not a concrete traversed
edge. Current cost is context metadata, not measured acquisition cost.
Current propensity is incorrect: deterministic first-choice selection
logs 1/N.

[ASPIRATIONAL] Extend the episode record with:

- episode_id, alert_id, decision/outcome references and provenance;
- model/checkpoint, feature-schema, policy and evidence-snapshot versions;
- S0 and cumulative evidence references with as-of timestamps;
- eligible candidate IDs, selected branch and concrete node/edge IDs;
- selection_mode and actual conditional selection probability:
  deterministic selection has probability 1 and no exploration support;
- action/category/confidence/margin before and after each read;
- read status, error, new-evidence count, elapsed time and budget usage;
- target residual and movement residual as separate quantities;
- result-level stop_reason, including zero-step and failed episodes;
- conservation snapshot/status and whether actionable emission occurred.

Record true empty reads separately from metadata-only responses.
Keep evidence payloads bounded and store references to larger snapshots.
Attach outcomes later without rewriting the original trajectory.
Deterministic traces do not identify counterfactual step-level credit.

---

## 3B. Simulation v4: reproduced results and scope

Defaults: 5,000 synthetic cases, eight dimensions and six branches.
The six experiment functions were reproduced without plot-file writes.
`rho_target` is a signal-amplitude parameter, not measured routing ρ.

### 3B.1 Neutral-fraction sweep

At neutral fractions 0.0, 0.1 and 0.2, VLD-minus-single accuracy is
-0.0166, 0.0000 and +0.0144 respectively. At 0.7, VLD is 0.726 and
single-pass is 0.636.

The script prints crossover ≈0.0 because it reports the lower endpoint
of the negative-to-nonnegative interval. Report the raw grid values:
tie at 0.1; first tested strict improvement at 0.2. This is not an
estimated production threshold. The neutral fraction is hypothetical.

### 3B.2 Signal-parameter sweep

At parameter 0.60:
VLD=0.706 [0.693, 0.719], content-rule=0.794, majority=0.634,
random=0.635, single=0.632. Correlation between parameter and
VLD-minus-single gain is 0.926; VLD beats single at 17/18 settings.

The content comparator exceeds VLD across this sweep, which mixes
labelled and unlabelled cases. Report those populations separately.
The parameter must not be substituted for empirical routing accuracy.

### 3B.3 Aggregation and budget

| Evidence regime | Budget | VLD damping | VLD accumulated average |
|---|---:|---:|---:|
| All neutral | 3 | 0.913 | 0.931 |
| Mixed 70/30 | 3 | 0.815 | 0.874 |
| All misleading | 3 | 0.548 | 0.715 |
| Mixed 70/30 | 1 | 0.717 | 0.680 |
| All misleading | 6 | 0.020 | 0.001 |

The implementation called re-extraction averages the initial surface
vector and all admitted evidence vectors. It correctly implements that
arithmetic operation; it does not run production graph factor extraction.

Damping gives later evidence greater weight. At three reads with eps=.3,
weights are .343 for surface and .147/.21/.30 for successive reads.
The accumulated average gives each vector .25.

The breadth arm uses fixed-order damping. Therefore comparing it with
VLD accumulated averaging changes both routing and aggregation. Run the
same aggregation under every routing policy before selecting a default.
These results do not establish that cumulative extraction always wins.

### 3B.4 Selective investigation

At the hypothetical 70% neutral setting and one-read budget, the best
tested margin gate is 0.40: all cases are investigated, accuracy 0.726,
versus 0.636 single-pass. This is an accuracy-only, in-sample result
without acquisition cost. It does not authorize always-investigate in SOC.

### 3B.5 Abstention utility

| Scenario | Error penalty | Assumed abstention cost | Best tested margin | Utility |
|---|---:|---:|---:|---:|
| SOC | 20 | 1.0 | 0.35 | -0.966 |
| S2P | 5 | 0.5 | 0.20 | -0.368 |
| Trading | 3 | 0.3 | 0.05 | -0.086 |

Base penalty ratios match SDK presets. Abstention costs are assumptions,
not measured platform costs. SOC commits 106/5,000 cases at its selected
threshold: 97.88% abstention and 0.981 accuracy among committed cases.

The margin is a gap between two category-action centroid distances,
not calibrated correctness probability. Thresholds are selected and
evaluated on the same sample. Do not transfer them to platform confidence
gates; calibrate on held-out domain data with measured costs and coverage.

### 3B.6 Routing breakdown

At signal parameter 0.6, actual initial routing accuracy is
1,881/5,000 = 0.3762.

Per-category accuracy, categories 0–5:
0.805, 0.167, 0.149, 0.163, 0.144, 0.806.
Hardest margin quartile: 0.298; easiest: 0.553.
Action accuracy conditional on correct routing: 0.961;
conditional on incorrect routing: 0.584.

The toy category centers lie on one axis, giving edge categories different
decision regions from interior categories. This does not establish the
same failure pattern in SOC or justify reducing its branch count.
Available branches must follow the investigation problem.

### 3B.7 Architectural decisions

Retain cumulative extraction as an experimental candidate alongside
damping. Do not adopt universal always-investigate, fixed simulation
abstention thresholds, or a smaller branch registry from these results.
Require matched aggregation, cost-sensitive evaluation and held-out
evidence before choosing a production policy.

### 3B.8 What these simulations do not establish

- Empirical post-first-read R1 ρ, hard-tail prevalence or conditional density.
- Real SOC neutral/empty/refuting evidence frequencies.
- Production factor-provider integration or trained-centroid quality.
- Fair adaptive-versus-breadth attribution when aggregation differs.
- Held-out abstention calibration, measured review cost or latency.
- Counterfactual credit from deterministic trajectories.
- A universal crossover, aggregation winner or optimal branch count.

Correct branches and action-revealing evidence are planted. Neutral
evidence is noise, not an empty result. RNG consumption changes across
neutral regimes; cases are not strictly paired across the sweep.
Majority choice uses the evaluation world. Bootstrap intervals cover
VLD accuracy, not paired policy gains or threshold-selection uncertainty.

The original two-branch script remains a separate diagnostic. Its
default budget sweep reproduced VLD/breadth 0.871/0.686 at budget 1 and
0.840/0.884 at budget 2, with its own verdict NEEDS INVESTIGATION.
Neither simulation version establishes customer value.


## 4. Experiments and evidence gates

### 4.0 Data feasibility and shared protocol

The R1 audit found 4,862 synthetic outcome-labelled seed decisions,
including 432 campaign-linked rows representing 48 alerts in four
campaigns. It did not establish an evaluable score-keyed investigation
sample. Nine synthetic decisions per alert are not independent episodes.

Seed correctness is not an observed branch label. Incorrect seed rows
do not necessarily identify the correct alternative action. Do not
derive ground truth from the same centroids used by the evaluated policy.

Every routing episode requires S0, an ordered first read, S1, available
next branches, independently adjudicated productive branches, evidence
timestamps, frozen model/policy versions and a valid outcome where
terminal utility is evaluated. Without these, report NOT MEASURABLE.

Use campaign/entity/time-disjoint training, validation and test sets.
Fit majority policies and thresholds only on training/validation data.
Report the hard-tail selection rule, independent case count, campaign
count, exclusions and uncertainty. n>30 is not a sufficient power
criterion; plan power for the paired improvement of interest.

### 4.1 E-ρ: Empirical next-branch routing accuracy

ρ is the probability that the policy selects a productive next branch
from the scorer state after the common first evidence read, S1/v1.

Category recovery from labelled S0 fixtures is a separate E-category
diagnostic. It is not empirical ρ and cannot establish the content-keyed
fraction of conditional investigation.

Success requires positive held-out improvement over the best
budget-appropriate rule, majority, fixed-order or other strong adaptive
comparator, with paired uncertainty. Random routing is a sanity check;
its expected accuracy depends on the eligible and acceptable branch sets.

### 4.2 E-ρsk: Synthetic conditional investigation

Build a planted, versioned generator with latent causes, ambiguous
observable indicators, multiple available branches, branch-specific
evidence, and independent productive-branch labels. Include empty,
refuting and misleading reads and useful second reads after a neutral
first read. Do not use evaluated-centroid proximity as the label oracle.

Removing category or alert_type fields is a leakage ablation, not a
method for creating score-keyed cases. Preserve the same extraction
schema and prevent labels, IDs or aliases from exposing the answer.

Run the E-ρ comparator protocol on held-out planted cases. Report
synthetic results as instrument validation, not customer ρ or market
prevalence. No universal 0.5 threshold is used.

### 4.3 E-Δ: Incremental investigation utility

Evaluate all preregistered eligible episodes, not only disagreements.
Use valid terminal-action labels and domain-specific action/review costs.

Report:

- whole-cohort paired accuracy and net utility differences;
- disagreement rate and conditional disagreement accuracy;
- read cost, latency, abstention, coverage and harmful-action rate;
- no-new-evidence and fixed-category controls;
- matched-budget adaptive versus non-adaptive comparisons.

Total benefit from extra evidence and benefit specifically attributable
to adaptive routing are separate estimands.

The value claim is:
`htail * m_cond * E[g(ρ)] - acquisition_cost > 0`,
where g is measured against the best budget-appropriate comparator.
Synthetic results alone do not establish population htail or m_cond.

### 4.4 E-budget: Cost-constrained policy comparison

Support an explicit zero-read arm and sweep available dispatch, node/
query and time budgets. Count all evidence acquisition, including initial
context and factor/provenance queries. Enforce limits before dispatch.

Cross every routing policy with the same aggregation choices. Exhaustive
arms use the same admitted set and order-independent extraction when
testing whether routing differences disappear at full coverage.

Report policy utility, accuracy, coverage, actual cost and latency at
each budget. Do not require a preselected advantage peak at budget 1–2.
Full-budget equality is a control under identical evidence and
aggregation, not a universal theorem about noisy evidence.

### 4.5 E-μskew: Representation ablation

First report paired v0/v1/vL displacement on valid evidence snapshots.
Vector displacement alone does not establish degraded routing.

To measure skew, train surface/intermediate and full-evidence centroid
models on the same training episodes under controlled label, kernel and
learning settings. Evaluate both on identical held-out intermediate
states and branch policies. Report routing and utility differences.

If paired states or independently trained models are absent, report
the skew effect as NOT MEASURABLE. Do not assume its sign.

### 4.6 Progression gates

1. Integration gate: real-provider replay, distinct admitted evidence,
   immutable episode state, correct trace and enforced budgets.
2. Synthetic gate: valid conditional generator and fair, held-out
   comparator tests; permits further research, not a product claim.
3. Empirical R1/R2 gate: score-keyed conditional cases exist and routing
   exceeds the best comparator with adequate evidence.
4. R4 gate: positive net depth value against rule-based investigation.
5. R5/R6 gate: measured workflow benefit before product extension to
   other copilots. Insufficient data is inconclusive, not a negative
   result about VLD's addressable market.

---

## 5. Demo integration

Use `demo_scenarios_and_usecases_v2_8.md` §4.17 as the storyboard authority.

| Beat | Exact name | Demonstration and evidence requirement |
|---|---|---|
| VLD-SOC-1 | The Investigation Trace | Mixed indicators; score-keyed branch choice within a supplied category; persisted evidence/order trace |
| VLD-SOC-2 | The Wrong-First-Step Recovery | Empty auth read followed by productive alternative; explicit two-branch budget; no superiority claim over exhaustive retrieval |
| VLD-DO-1 | Three Systems, One Root Cause | Schema-versus-upstream choice; subsequent lineage walk labelled CONTENT-KEYED / PREREQUISITE |
| VLD-DO-2 | Known Pattern, New Twist | Preregistered follow-known versus read-wide policy; both branches exercised |
| VLD-S2P-1 | The Supplier It Knew | Dual mismatch; receipt-first versus contract-first ordering; supplier ratio computed from time-filtered planted history |

Synthetic E-ρsk and trajectory verification support architecture previews.
Empirical E-ρ/E-Δ and matched-budget tests support routing/value claims.
No per-category agreement statistic substitutes for supplier-specific
or within-category branch correctness.

All five remain ARCH on planted fixtures until their implementation and
data prerequisites are met. Follow Demo's explicit readiness gates:
prototype plus trajectory store for NEAR; demonstrated R4 value against
rule-based routing for LIVE. R5 is required for time-savings claims.
A positive synthetic disagreement result does not automatically upgrade
all beats.

Always show PLANTED FIXTURE and ROUTING ACCURACY: not yet measured
where applicable. Compute contrast strips from the same episode.
Do not display hardcoded nodes_consulted as measured cost.

`resource_quota`, `partial_delivery` and `accept-with-adjustment` are
scenario concepts, not established current preset category/action names.
Map concepts explicitly to real schemas without silently adding tensor
axes. Distinguish confidence from margin in threshold captions.

---

## 6. Verification plan

### 6.1 Current evidence

`test_investigation_loop.py` contains nine direct loop tests. They passed
when invoked directly during this review. They use a fake factor
provider and eps=1.0. No endpoint test exists in that file. This review
did not run or certify the full SOC backend suite.

The existing centroid-immutability test shows that the isolated loop
does not update its test scorer. It does not prove snapshot isolation
against concurrent learning/reset or absence of startup persistence.

### 6.2 Required before measurement

- Real provider plus offline graph adapter completes multiple reads.
- Branches expose distinct evidence and cannot read future/unselected data.
- Endpoint exercises request/response and 404/422/503/error paths.
- Production eps=0.3 and cumulative-extraction arms are both tested.
- Label-independent branch mode cannot use category aliases as answers.
- No-evidence and zero-budget episodes preserve the comparison result.
- Empty first read can continue when another eligible branch is useful.
- Target residual, flip limit and acquisition budgets enforce their contracts.
- Query/episode deadlines and failures produce complete terminal traces.
- Deterministic probabilities and actual read costs are logged correctly.
- Concurrent learning/reset cannot alter the episode snapshot.
- Investigation performs no model initialization, learning or persistence.
- Diagnostic output cannot be mistaken for conservation-authorized action.

### 6.3 Experiment verification

Validate episode labels independently, split by campaign/entity/time,
fit comparators without test leakage, use identical evidence and
aggregation controls, and report paired uncertainty and coverage.
Pin script, dataset, model and policy versions with every result.

---

## 7. [ASPIRATIONAL] Multi-copilot extension

### 7.1 Shared versus current implementation

Loop, router and trace models are currently SOC-local.
SDK generalization, shared endpoint templates and cross-copilot
measurement tooling remain planned. Remove direct SOC imports before
claiming a shared implementation.

### 7.2 DataOps

Actual preset shape: 6 categories × 5 actions × 6 factors.
Categories: schema_change, volume_anomaly, quality_anomaly,
freshness_violation, pipeline_failure, transform_drift.

The local graph contract/seed includes:
Decision-DECIDED_ON->Alert-DETECTED_IN->Pipeline;
Transformation-CONSUMES/PRODUCES->Dataset;
QualityRule-MONITORS->Dataset;
ProcessModel-CONTAINS->Activity-FOLLOWS->Activity;
Alert-TRIGGERED_BY->Activity.

The context graph client separately queries DataQualityAlert-AFFECTS->
PipelineSystem and PipelineSystem-FEEDS->PipelineSystem. These are
different representations; specify the chosen store and adapter rather
than composing an unverified path across them.

Schema changes such as MATKL_V2 exist in JSON evidence. The inspected
local contract/seed does not create a SchemaChange node. Upstream,
schema-history, quality, blast-radius and known-resolution patterns
require explicit evidence contracts and entity/time joins.

Current fixtures include labelled actions and root-cause descriptions,
not a complete independently labelled sequential-routing dataset.

### 7.3 S2P

Actual shape: 5 categories × 5 actions × 8 factors.
Categories: price_variance, quantity_mismatch, duplicate_risk,
contract_gap, format_compliance.

The inspected seed contract supports:
Decision-DECIDED_ON->Invoice;
Invoice-SUPPLIED_BY->Supplier;
Invoice-MATCHED_TO->PurchaseOrder;
Invoice-RECEIVED_AS->GoodsReceipt;
Invoice-GOVERNED_BY->ContractClause.

Receipt, pricing, supplier-history and delivery checks are branch IDs,
not additional category names. Contract amendments and shipment tracking
require new evidence contracts; their availability is not established
by the existing seed. The seed adds demonstration receipt/clause nodes
to the first invoice, not complete branch evidence for every invoice.

Reconcile the local seed contract with the live reader/migration schema.
The supplier prior-decision matcher requires an as-of cutoff. Do not
assume that current synthetic invoice vectors encode observed histories.

The configuration's initial action centroids repeat across categories;
category-distance ties must be detected. Record the actual runtime model
rather than assuming learned category separation.

### 7.4 Extension gate

Build copilot-specific planted episodes before measurement. Use the same
independent-label, matched-budget and held-out comparator requirements
as SOC; do not impose unexplained 0.5/0.4 routing thresholds or target
content-keyed fractions.

Product extension follows Architecture R4/R5/R6. Planted previews remain
separately labelled architecture work.

---

## 8. Risk register

| Risk | Required mitigation |
|---|---|
| Synthetic labels mistaken for observed branch truth | Separate planted instrument tests from empirical R1 |
| Empty read causes premature convergence | Track exhaustion and selector information; permit justified continuation |
| Graph object replaced with evidence dict | Use a real-provider-compatible admitted-evidence adapter |
| Different names return identical bulk evidence | Verify distinct branch retrieval and concrete evidence identities |
| Category reassignment creates action disagreement | Fixed-category and no-new-evidence controls |
| Concurrent model changes | Immutable snapshot captured under the scorer lock |
| Initialization writes during a diagnostic request | Require ready state; return 503 |
| Slow queries or oversized evidence | Cancellation, total deadline and bounded payload/query/node budgets |
| Exceptions erase the trajectory | Typed read/extraction errors and result-level stop reason |
| Untrained, tied or stale centroids | Record model provenance; report ties and measured routing rather than assuming chance |
| Uniform averaging or damping amplifies misleading evidence | Matched routing × aggregation experiments |
| Assumed 70% neutral fraction | Label hypothetical; measure real empty/neutral/refuting evidence distributions |
| In-sample abstention tuning | Held-out calibration, measured review cost, coverage and harmful-action reporting |
| No outcome or insufficient independent cases | Report NOT MEASURABLE/inconclusive; do not manufacture sample size |

---

## 9. Implementation sequence

CURRENT:

- SOC-local loop/router/pattern/model/endpoint scaffolding exists.
- Nine fake-provider loop tests pass.
- Real-provider integration, distinct retrieval, episode isolation and
  empirical measurement prerequisites are not complete.
- v4 simulations are synthetic diagnostics; see §3B limitations.

PHASE 1b-A — repair the measurement substrate:

- Implement the admitted-evidence adapter and distinct bounded reads.
- Separate scoring category, branch policy and first-read protocol.
- Add immutable model/policy snapshots, correct trace semantics,
  zero-read controls, acquisition budgets and deadlines.
- Complete real-provider and endpoint verification.
- Design trajectory/outcome linkage before replay or persisted demos.

PHASE 1b-B — validate the instrument:

- Build independently labelled planted conditional episodes.
- Implement matched-budget comparator and aggregation arms.
- Run E-category, synthetic E-ρsk, E-Δ, E-budget and representation
  diagnostics. Do not label these empirical R1.
- Retain both damping and cumulative extraction until controlled
  experiments justify selection; no universal always-investigate
  or simulation-derived abstention threshold is adopted.

EMPIRICAL VALIDATION:

- Acquire as-of episode data and independent branch labels for R1/R2.
- Run R4 shadow comparisons without executing VLD recommendations.
- Measure R5 workflow benefit and apply R6 extension gates.

MULTI-COPILOT:

- DataOps/S2P planted architecture previews may be researched separately.
- Product extension follows the architecture's R4/R5/R6 gates.
- Neural controllers and production claims remain contingent.

Do not promise a one-slot empirical result: data acquisition, annotation
and adequate independent sample size are prerequisites.

---

## 10. Relationship to companion documents

| Document | Authority and limitation |
|---|---|
| Architecture v3 | Controller placement, frozen episode state, C4, value model and R1–R6 gates |
| R1 structural feasibility audit | Offline data limitations; Phase 1a scaffolding does not supply missing historical branch labels |
| Demo scenarios v2.8 | Exact beat names, planted-data requirements, captions and readiness gates |
| Execution plan v2 | Not present in the audited checkout; reconcile before treating it as an additional authority |
| Original simulation | Two-branch synthetic instrument and budget diagnostic |
| Simulation v4 | Six-branch synthetic sensitivity/aggregation/abstention diagnostics, scoped in §3B |
| Phase 1b implementation prompt | Must implement the prerequisites and tests in this revision before reporting empirical measurements |
