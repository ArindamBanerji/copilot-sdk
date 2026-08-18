# SOC Copilot v5.11 — Feature Gap Analysis

Date: 2026-08-17  
PD: `soc_copilot_design_v5_11.md` (§30 feature manifest + Part II product)  
Prior work: `soc_structural_diagnosis.md`  
Repositories: `gen-ai-roi-demo-v4-v50` (primary), `copilot-sdk` (shared SDK), `graph-attention-engine`, `ci-platform`

## Summary

- Shipped requirements R1–R13: **10 substantially implemented, 3 partial**. R5b is included as a separately assessed requirement.
- Features F1–F22: **10 LIVE, 9 PARTIAL, 3 GAP**.
- v5.9 additions F16–F22: **0 LIVE, 5 PARTIAL, 2 GAP**.
- Referral rules R1–R7: **7 implemented as pure rules and factory-wired; triage VETO integration is present in the designed path, but live route-wide enforcement requires targeted runtime verification**.
- Three-Signal Monitoring: **Circuit Breaker LIVE; Flywheel Health Monitor PARTIAL; Analyst Contribution Monitor data-gated/NEAR**.
- Factor-0: live scoring is canonical `privileged_identity_context`; fixtures, provenance, aliases, and legacy explanatory content remain mixed (`84` legacy versus `33` canonical backend occurrences).
- C-COUPLE: conservation is coupled to evolution and triage health/gate data, but a universal RED decision-path veto is **not proven**.
- Frozen Twin: **GAP confirmed**. Frozen-scorer percentages are controlled/experimental results, not live infrastructure.
- Inventory: **1,896 backend test definitions across 236 files; 444 E2E call sites across 64 files**.
- Main P0 blockers: **F18 Frozen Twin, F17 Earned Autonomy Ladder, F16 Learning Control Room, and full C-COUPLE decision-path enforcement**.

The report uses strict status labels: LIVE requires mounted backend behavior, backend tests, frontend surface, and E2E coverage. PARTIAL identifies a concrete acceptance gap. Related infrastructure is not counted as a complete feature.

## Shipped Requirements (R1–R13)

R1–R13 here are the v5.5 shipped-requirement namespace. They are distinct from referral rules R1–R7 in §22.6.

| R-item | Description | Backend evidence | Test evidence | Status |
|---|---|---|---|---|
| R1 | Category-specific auto-approve thresholds | `backend/app/domains/soc/config.py` threshold methods; `framework/composite_gate.py`; triage threshold path | category threshold/composite/triage tests and E2E | LIVE for threshold computation; production coverage claim remains calibration-dependent |
| R2 | Factor provenance nodes | `domains/soc/factors.py`, `framework/provenance.py`, provenance models and response fields | factor provenance, receipt and API tests | LIVE |
| R3 | Centroid drift metric / Chart A fix | scorer/update state, `centroid_delta_norm`, SOC analytics and learning-state endpoints | checkpoint/centroid/learning tests and chart/E2E coverage | LIVE for metric plumbing; route/UI aggregation should be verified with real learned state |
| R4 | Institutional Knowledge Score (IKS) | `backend/app/services/iks.py`, `framework/iks_base.py`, SOC/profile/Tab-2 endpoints | IKS and tab-content tests | LIVE |
| R5 | NL Template Engine | `backend/app/services/nl_templates.py` and triage/evidence integration | NL/evidence/receipt tests and UI/E2E | LIVE |
| R5b | Tab-2 two-mechanism redesign | Compounding/runtime evolution tabs, IKS, evolver, drift and conservation APIs | tab-content and evolution/learning tests, E2E surfaces | PARTIAL — ingredients exist, but the PD’s single institutional-intelligence panel, four-section navigator, anchored Tab-3 bridge, and seeded-versus-session data distinction are not verified as one contract |
| R6 | Alert type → category mapping completion | `SOCDomainConfig.get_alert_category_mapping()` and SOC config mapping | mapping/category/triage tests | LIVE |
| R7 | Threat-intelligence persistence | `threat_intel.py`, `threat_indicator.py`, Pulsedive/GreyNoise/CISA/NVD connector paths | threat-indicator/connector/persistence tests | LIVE/connector-dependent — external connector availability is deployment-specific |
| R8 | Shadow Mode | `routers/shadow.py`, shadow config, evolver/shadow services | shadow router/config and E2E tests | LIVE |
| R9 | Docker Compose VPS deployment | deployment artifacts/scripts exist in the SOC repository | deployment checks are present, but no live hosted deployment was verified in this session | PARTIAL — packaging/config exists; deployed-host acceptance is not evidenced |
| R10 | Tab-1 Graph Explorer / Ask the Graph | graph/query router, query catalog and SOC graph services | graph/query contract tests and frontend/E2E | LIVE for current query surface |
| R11 | Graduated human review tiers | referral/triage policy and confidence routing fields | referral/triage tests and E2E | LIVE for routing primitives; threshold values are explicitly design estimates until empirical calibration |
| R12 | Centroid drift alerts | drift bounds, checkpoint/alert services and SOC routes | drift/checkpoint/diagnostic tests | LIVE for alert plumbing; no automatic revert by design |
| R13 | Evidence export in compliance format | audit/evidence routers, NL Layer 3, export paths | evidence export/receipt/audit tests and E2E | LIVE/PARTIAL — export exists; full EU AI Act deployment package remains a compliance/documentation obligation |

## Feature Status Table (F1–F22)

The v5.11 §30 table skips F11. This report preserves that document anomaly and does not renumber it.

| Feature | Target ver. | Status | Backend evidence | Frontend evidence | Test evidence | Gap |
|---|---|---|---|---|---|---|
| F1 Shadow Mode | v5.5 | LIVE | `routers/shadow.py`, shadow config/evolver paths | Runtime Evolution/shadow surfaces | shadow backend and E2E tests | No identified feature-surface gap; deployment measurement remains separate |
| F2 Detection Engineering Feedback | v5.0 | LIVE | centroid drift/update and factor analysis services | SOC Analytics/Compounding learning views | factor contribution, drift and learning tests/E2E | No identified surface gap |
| F3 EU AI Act Compliance Evidence | v5.5/v6.0 | PARTIAL | audit, governance, evidence export and provenance | Governance/audit panels | compliance/evidence/receipt tests | Article 9/12/13/14/15 deployment package and risk-log completion are not the same as an export endpoint |
| F4 Operational Outcome Metrics | v5.0 | LIVE | metrics/ROI/triage outcome services | Compounding and analytics tabs | metrics/tab/E2E coverage | Current values must retain evidence tier; modelled ROI is not realized outcome |
| F5 Multi-SIEM Abstraction | v6.0 | GAP | No SOC multi-SIEM abstraction matching the PD was found | No matching SOC surface | No matching SOC contract test | Splunk/threat connectors are not a complete provider-neutral SIEM protocol |
| F6 Attack Chain Correlation | v6.0 | PARTIAL | cross-graph discovery, campaign/situation and graph routes | analytics/discovery surfaces | discovery/graph tests | No confirmed end-to-end multi-stage ATT&CK campaign object with chain-level UI and acceptance contract |
| F7 NHI Behavioral Baseline | v6.5 | GAP | Factor-0 handles identity context, but no named NHI baseline subsystem was found | No dedicated NHI surface | No NHI contract test | Service accounts/API keys/AI agents are not a persisted behavioral-baseline product feature |
| F8 Cross-Tenant Meta-Intelligence | v7.0 | GAP | Tenant isolation/provenance primitives exist; no cross-tenant meta-intelligence implementation found | No customer-facing cross-tenant surface | No matching contract test | Privacy-safe aggregate-prior product is not present |
| F9 Analyst Benchmarking Report | v5.6 | LIVE | `/api/soc/f9-report` and shadow/analyst comparison services | analytics/report surfaces | report and API/E2E evidence | The report is present; the evidence tier remains data-dependent |
| F10 A2A/MCP Protocol | v7.0+ | GAP | No SOC-specific A2A/MCP interoperability surface found | No SOC surface | No SOC contract test | Generic connector/HTTP support is not this feature |
| F12 INTSUM-Quality Threat Briefing | v5.5 proposal | PARTIAL | threat-intel and NL template inputs exist | narrative/analytics surfaces | threat/NL tests | No confirmed gated, inspectable INTSUM artifact with GATE-M/GATE-D semantics and bias audit |
| F13 ContextConnectors | v6.0 proposal | GAP | Individual connectors exist, not Slack/email/docs context ingestion | No matching surface | No matching contract test | No unified context-connector pipeline |
| F14 Ask the Graph | v5.5 | LIVE/PARTIAL | query/graph routers and catalog | Graph Explorer/analytics UI | graph query tests/E2E | Current structured query surface is present; full 20+ template/NL executive scope needs route-by-route confirmation |
| F15 SynthesisNode Artifact | v6.0 proposal | GAP | No SOC SynthesisNode artifact found | No surface | No matching test | Discovery/narrative results are not inspectable SynthesisNode artifacts |
| F16 Learning Control Room | v5.9 | PARTIAL | centroid history, DK/learning state, conservation, IKS, evolver APIs | Compounding and Runtime Evolution tabs | tab/evolution/learning tests | No named unified `LearningControlRoom`; the PD’s summary panel, left rail, anchored Tab-3 bridge, and single learning-state contract are not evidenced as complete |
| F17 Earned Autonomy Ladder | v5.9 | PARTIAL | shadow, conservation, referral, promotion/intervention primitives | Runtime Evolution/Compounding and governance surfaces | shadow/conservation/evolution tests | No named persisted five-rung per-alert-class ladder: Observed → Assisted → Shadow-qualified → Auto-approved → Circuit-broken |
| F18 Frozen Twin | v5.9 | GAP | No `FrozenTwin`, `frozen_twin`, `frozen_scorer`, `frozen_baseline`, or immutable parallel scorer | No matching UI | No matching test | Checkpoints/rollback primitives are not a day-0 immutable twin or live-vs-frozen comparison |
| F19 No-Precedent Surface | v5.9 | GAP | No `no_precedent`/`NoPrecedent` implementation found; novelty exists separately | No dedicated “no precedent” surface | No matching contract test | Novelty status is not the explicit “I have no precedent; here is what I know” evidence-linked state |
| F20 Counterfactual Inspector | v5.9 | PARTIAL | shared `self_computation_router.py` and `counterfactual_router.py` | No confirmed SOC-specific per-factor inspector panel | shared counterfactual tests, but no complete SOC acceptance contract | Existing replay/score counterfactuals do not prove per-factor boundary direction/magnitude and evidence-linked “what would flip this” UI |
| F21 Day-0 Readiness Assessment | v5.9 | PARTIAL | SOC cohort/readiness and ci-platform qualification primitives | No confirmed dedicated SOC Day-0 assessment surface | readiness/qualification tests exist outside a complete SOC onboarding contract | Coverage, connector health, graph state, and trusted-versus-enrichment-required report is not assembled for SOC |
| F22 Cold-Start / Transfer Measurement | v5.9 | PARTIAL | reconvergence logger, accuracy trajectory, promotion/flywheel services and framework routes | Runtime Evolution/Analytics views | instrumentation and trajectory tests | No explicit per-category/new-team crossover measurement contract proving “category 6 in 40 vs category 1 in 120” |

## v5.9 new features detail (F16–F22)

### F16 — Learning Control Room: PARTIAL

The backend exposes the ingredients the PD names: centroid history/checkpoints, learning state, IKS, conservation, drift, and AgentEvolver session data. The frontend has Compounding and Runtime Evolution tabs. Search found no `LearningControlRoom` or `learning_control` component. The current product is multiple adjacent surfaces rather than the specified unified view with:

- one institutional-intelligence summary;
- situational-understanding versus deployment-adaptation split;
- convergence/adaptation/cold counts;
- active variant/promotions;
- verified-decision and IKS summary;
- four-section left rail; and
- a decision-anchored Tab-3 → Tab-2 Learning Impact bridge.

### F17 — Earned Autonomy Ladder: PARTIAL

Shadow mode, conservation, referrals, promotion gates, and intervention controls are real. The product-level ladder is not. Search found no `EarnedAutonomy`, `autonomy_ladder`, or persisted `autonomy_level`. GREEN/AMBER/RED conservation is a health signal, not the required per-alert-class authority state. The auto-approve implementation remains shadow-only, so the Auto-approved rung cannot honestly be presented as live authority.

### F18 — Frozen Twin: GAP

No matching implementation or UI/test was found. Profile checkpoints and rollback afford repair/recovery, but they do not satisfy immutable day-0 snapshot, parallel same-stream scoring, restart persistence, frozen/live/outcome comparison, or drift reporting. The frozen-scorer percentages in the design are experimental evidence, not a shipped feature.

### F19 — No-Precedent Surface: GAP

The Stryker/Handala narrative and novelty tracker exist, but no dedicated no-precedent object or UI was found. “Novelty” and “no similar cases” are not interchangeable: the PD requires an explicit epistemic disclosure of what the system does not know, linked to the decision’s evidence and confidence.

### F20 — Counterfactual Inspector: PARTIAL

The shared SDK exposes self-computation/counterfactual routes and replay-oriented infrastructure. The missing piece is the SOC product contract: per-factor boundary search, direction/magnitude explanation, action transition, evidence linkage, and a visible SOC frontend inspector. A generic counterfactual score is not enough to mark F20 LIVE.

### F21 — Day-0 Readiness Assessment: PARTIAL

ci-platform onboarding/qualification and SDK readiness/substantiation components can provide the substrate. SOC has cohort/readiness-related services and governance endpoints, but no confirmed SOC-mounted onboarding report combining source coverage, connector health, graph/AGE state, identity resolution, and safe-mode capability boundaries.

### F22 — Cold-Start / Transfer Measurement: PARTIAL

`reconvergence_logger.py`, accuracy trajectories, flywheel/promotion services, and runtime evolution views are measurement primitives. There is no verified canonical metric/report for category-specific decision-to-competence, new-team transfer, or crossover against the claimed 120→40 example. This is instrumentation, not a complete customer-facing measurement feature.

## Referral routing (R1–R7)

The referral namespace is separate from v5.5 R1–R13. Referral is post-score VETO routing and does not modify ProfileScorer geometry.

| Rule | Description | Implementation evidence | Status |
|---|---|---|---|
| R1 | Confidence-band referral / low margin | `referral_rules.py` implements `ExecutiveAccountRule`; the design explicitly rejects confidence as the primary referral mechanism because of poor precision | PARTIAL/DRIFT — the rule name in the implementation is Executive Account, not confidence-band referral; confidence routing is handled separately |
| R2 | Geometric competitiveness / close centroids | `referral_rules.py` implements `RapidSuccessionRule`; no dedicated close-centroid referral rule found | PARTIAL/DRIFT — implementation namespace differs from the prose label |
| R3 | Red-flag override patterns | `ComplianceMandateRule` and `HighValueDataRule` cover compliance/high-value patterns | LIVE for these rule classes |
| R4 | High-value data / sensitive category override | `HighValueDataRule` in `referral_rules.py` | LIVE |
| R5 | Active incident override | `ActiveIncidentRule` | LIVE |
| R6 | New asset override | `NewAssetRule` | LIVE |
| R7 | Cross-category activity | `CrossCategoryRule` | LIVE |

Important drift: the executable factory returns seven concrete rules—Executive Account, Rapid Succession, Compliance Mandate, High Value Data, Active Incident, New Asset, and Cross Category. The v5.11 prose’s R1/R2 “confidence-band/geometric” descriptions do not match the executable rule class names. The implementation is the source of truth; this must be resolved before calling the referral specification fully reconciled.

## Three-Signal Monitoring

| Signal | Specification | Implementation | Status |
|---|---|---|---|
| Circuit Breaker | `α·q·V ≥ θ_min=0.467`; relative AMBER/RED bands; AMBER pauses learning | SOC/shared conservation services and health/gate paths; `THETA_MIN` and GREEN/AMBER/RED logic are present | LIVE for conservation monitoring/evolution gating |
| Flywheel Health Monitor | OLS CUSUM `h=5.0`, plateau baseline, early degradation detection | GAE OLS/convergence primitives and SOC `reconvergence_logger`/flywheel-related services exist; no confirmed complete SOC `/api/soc/ols-status` + Tab-2 chart contract | PARTIAL |
| Analyst Contribution Monitor | per-analyst OLS variance, activates at ≥20 overrides/analyst | Design specifies a query over DecisionRecord; source scan did not establish a fully mounted, always-available SOC product endpoint/panel; design calls it a production milestone | NEAR/data-gated |

The design explicitly forbids replacing per-analyst OLS variance with pooled binary variance. Any implementation of that shortcut would be a correctness violation.

## Cross-cutting findings

### Factor-0 naming migration

The live scoring path is canonical:

```text
SOCDomainConfig / SOC preset
  → privileged_identity_context factor name
  → PrivilegedIdentityContextFactor in domains/soc/factors.py
  → scorer adapter / ProfileScorer
```

The remaining `travel_match` references are concentrated in:

- `app/data/soc_eval_scenarios.json` legacy/quarantined fixture keys;
- provenance and compatibility mappings;
- evaluation/judgment router aliases;
- legacy explanatory/design text;
- residual factor/provenance fields.

The NL template layer must be treated carefully: the v5.11 engineering body still contains user-facing examples such as `travel_match: 0.87`, while the current service has canonical identity-context templates. Removing every legacy string blindly would break legacy fixture loading, compatibility aliases, and historical-document provenance. The safe migration unit is: canonicalize live output and new fixtures, retain explicitly labelled legacy input aliases/fixtures until downstream consumers are audited.

### Conservation coupling (C-COUPLE)

`triage.py` reads conservation health and carries conservation status/headroom/reason fields into the decision path. It updates the SOC conservation provider from health and has an effective-conservation helper. Evolution/promotion routes consume conservation gates.

What is not proven by source presence alone is the universal behavior required by C-COUPLE: when conservation is RED, every auto-approve-capable triage route must refuse authority or force referral. The correct status is:

- evolution/promotion conservation gate: **LIVE**;
- triage conservation observability and gate inputs: **PRESENT**;
- route-wide RED veto/referral behavior: **NOT PROVEN / PARTIAL**.

This requires an integration test that drives a real alert through scoring and triage under RED, asserts no autonomous action, and verifies referral/audit output.

### Frozen Twin / Frozen Scorer

No implementation was found for `FrozenTwin`, `frozen_twin`, `frozen_scorer`, or `frozen_baseline`. The blog/design values `80.4%`, `92.9%@85%`, and `DISC-1 70.4%@85%` are stored/repeated in design and controlled-evaluation artifacts, not computed by a live parallel scorer.

Part II §P0.4 explicitly labels the figures—including 71.7%, 78.9%, frozen-scorer values, IKS 43→82, and `$523K–$2.8M` ROI—as measured-synthetic/controlled evaluation, not realized customer outcomes. The codebase does not have the Frozen Twin mechanism needed to convert those claims into measured pilot evidence.

### Acceleration / second derivative

The source scan found no `second_derivative`, `dA_dt`, or `meta_learn` live loop. `reconvergence_logger.py` is mounted/referenced by SOC routes/services and logs reconvergence/trajectory-related observability. Acceleration mentions in transparency/instrumentation do not establish a production update loop. No confirmed customer-facing acceleration metric was found beyond trajectory/learning views.

Status: **instrumentation exists; second-derivative/meta-learning production loop does not.**

### `reward` / `reward_raw`

The SOC backend does not show a dominant SOC-specific reward contract in its canonical triage/factor path. Shared SDK and cross-domain scorer/evolution code do contain reward-related fields, and S2P production code consumes them. This is a cross-copilot protocol concern, not a justification for deleting fields from shared interfaces.

### Canonical numbers audit

| Number/claim | Code finding | Evidence status |
|---|---|---|
| 71.7% static/realistic accuracy | Appears in `app/data/gae_learning_state.json` and design/experiment material; no live computation endpoint establishing this as current production accuracy was found | Controlled/synthetic or seeded state, not measured customer outcome |
| 78.9% at 1,000 decisions / 50-seed realistic | Present in learning-state/experiment artifacts and design material; no current live recomputation found | Controlled evaluation |
| IKS 43→82 | IKS service computes live trajectory values, but the specific headline is not a fixed current endpoint result | Historical/controlled claim unless tied to a dated live run |
| Frozen-ROI `$523K–$2.8M` | No production formula/result path establishing realized dollars was found; ROI/economics services are present | Modelled/controlled, not realized customer ROI |
| 97.89% centroidal synthetic versus 78.9% realistic | Design and learning-state artifacts preserve the distinction; code-level enforcement of “never customer-facing” was not proven by the source scan | The design is honest; enforcement depends on UI/API evidence labels and should be tested |

The two-regime rule is documented strongly, but a future gap analysis must inspect every product response for evidence/substantiation labels rather than rely on documentation alone.

## Scenario / demo coverage

| Scenario/beat | Features needed | Can demo? | Missing/qualification |
|---|---|---|---|
| Stryker/Intune living-off-the-land hero | factor-0 identity context, F2 situation, threat intel, NL evidence, F19 | PARTIAL | Live scoring/factor path and threat connectors exist; explicit no-precedent surface is GAP and graph-backed evidence depends on deployed graph state |
| Five CISO Questions Q1–Q5 | F4 metrics, F9 IKS, conservation, referral/counterfactual | PARTIAL | Several tab/API answers exist; F20 is incomplete, Flywheel/Analyst monitoring is not fully surfaced, and synthetic figures must remain labelled |
| Shadow mode → earned autonomy | F1, F17, conservation | PARTIAL | Shadow and conservation are live; named persisted five-rung autonomy ladder and live authority transition are missing |
| Cross-graph discovery | discovery service, graph routes, advisory-only posture | Yes, advisory | Discovery path exists; real shared-graph population and customer-specific evidence require runtime verification |
| Analyst departure / knowledge transfer | IKS, centroid export, F22 | PARTIAL | IKS/export primitives exist; F22 has no complete transfer-measurement report and there is no Frozen Twin baseline |

## MAP coverage

The MAP is `copilot-sdk/docs/design/master_action_plan_v5.228 (1).md`. Its SOC coverage is not a clean one-to-one F1–F22 register. It contains historical platform/prompt items, SOC v5.5 requirements, and later continuation records.

| Feature/requirement | MAP coverage | Reality check |
|---|---|---|
| R1–R5/R5b | Historical SOC v5.5 scope/continuation material | Broadly tracked; R5b’s unified control-room acceptance remains partial |
| R6–R13 | SOC v5.5 scope, referral/evidence/drift/shadow items | Tracked as shipped/closed in MAP language; deployment/calibration qualifications remain |
| F1 Shadow Mode | SOC shadow/production items | Covered and substantially live |
| F2/F4 detection/outcome metrics | v5.5 SOC/compounding work | Covered and substantially live |
| F3 compliance evidence | evidence/compliance items | Covered but partially complete for full regulatory package |
| F5–F8, F10, F13, F15 | target v6/v7 roadmap | Tracked as future roadmap, not current product |
| F9 benchmarking | report/benchmark work | Tracked and implementation evidence exists |
| F12/F14 | v5.5 proposal/Ask the Graph items | Tracked; implementation is partial-to-live by scope |
| F16 Learning Control Room | v5.9 continuation/design references | MAP/design tracked, but no complete named implementation |
| F17 Earned Autonomy Ladder | v5.9 continuation/design references | MAP/design tracked, implementation partial |
| F18 Frozen Twin | v5.9 continuation/design references | MAP/design tracked, implementation GAP |
| F19 No-Precedent | v5.9 continuation/design references | MAP/design tracked, implementation GAP |
| F20 Counterfactual Inspector | v5.9 continuation/shared self-computation references | Partially tracked; product contract incomplete |
| F21 Day-0 Readiness | v5.9/qualification references | Partially tracked; no SOC product assessment |
| F22 Cold-Start/Transfer | v5.9/reconvergence/roadmap references | Partially tracked; no complete measurement contract |

The MAP therefore does not prove implementation. It has entries for the v5.9 additions, but the status language is ahead of the current strict LIVE definition for F16–F22. A future MAP reconciliation should add explicit acceptance items for the unified control room, autonomy ladder state persistence, Frozen Twin, no-precedent response, per-factor counterfactuals, Day-0 report, and cold-start transfer metric.

## Recommendations

### Demo-blocking

1. Use `soc_copilot_design_v5_11.md` as the sole SOC authority and label the duplicate/out-of-place files.
2. Keep Stryker/Handala claims explicitly at the documented evidence tier; do not present Frozen Twin or no-precedent as live features.
3. Verify the actual seven-tab frontend map in all demo scripts; the five-tab assumption is stale.
4. Add a visible runtime indicator for graph/evidence availability and shadow versus authority mode.

### Pilot-blocking

1. Implement F18 Frozen Twin first: immutable day-0 state, parallel scorer, restart persistence, outcome comparison, and drift report.
2. Implement F17 as a persisted per-alert-class authority ladder, not a relabelled conservation color.
3. Complete F16’s unified Learning Control Room and R5b’s decision-anchored bridge.
4. Close C-COUPLE with RED-state triage integration tests and enforced referral/no-authority behavior.
5. Complete F20 per-factor counterfactuals, F19 explicit no-precedent, and F22 transfer measurement before using those stories in pilot material.

### Roadmap / hygiene

1. Resolve the §30 F11 numbering hole without silently renumbering existing features.
2. Reconcile v5.11 prose’s legacy `travel_match` examples with canonical factor-0 output while preserving explicitly labelled fixture/alias compatibility.
3. Separate the v5.5 R1–R13 and referral R1–R7 namespaces in MAP and test names.
4. Add evidence/substantiation labels to every canonical-number response and UI surface.
5. Replace “shipped” documentation statements with dated runtime/test evidence where strict LIVE status is required.

## Final assessment

SOC has a substantial working operational surface: six-factor scoring, triage, provenance, NL evidence, IKS, conservation, shadow mode, referral rules, threat-intelligence paths, analytics, graph exploration, and audit/export. The v5.9 “proof of compounding” surface is not complete under the strict product contract. The missing Frozen Twin and Earned Autonomy state are architectural gaps, not missing polish; they determine whether synthetic improvements can become measured and whether authority expansion is explainable and reversible.

## Discovery boundary

This report did not execute the complete SOC, SDK, GAE, ci-platform, or Playwright suites and did not connect to a live AGE DSN. Test counts are source inventories. Live claims about graph population, external threat-intel availability, deployment packaging, and route-wide conservation enforcement require a separate verification ladder.
