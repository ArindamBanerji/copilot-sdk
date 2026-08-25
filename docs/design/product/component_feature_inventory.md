gpt-5.3

COMPONENT: GAE
CODE ROOT: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\graph-attention-engine-v50
PD DOC(S): gae_design_v10_10.md; math_synopsis_v18.md; factor0_reconciliation_summary_v2.md
PURPOSE: Graph-attention scoring, centroid learning, kernel weighting, conservation monitoring, and evaluation primitives.

FEATURE | FUNCTIONALITY | EVIDENCE | STATUS
Scoring kernel protocol | Defines scoring against profile state. | gae/kernels.py:ScoringKernel | BUILT
L2 kernel | Scores with Euclidean distance. | gae/kernels.py:L2Kernel | BUILT
Diagonal kernel | Scores with per-factor diagonal weights. | gae/kernels.py:DiagonalKernel | BUILT
Profile scorer | Scores factor vectors against centroids. | gae/profile_scorer.py:ProfileScorer | BUILT
Profile scorer factory | Builds configured profile scorers. | gae/profile_scorer.py:build_profile_scorer | BUILT
Factor computer protocol | Defines domain factor computation. | gae/factors.py:FactorComputer | BUILT
Factor vector assembly | Combines factor outputs into vectors. | gae/factors.py:assemble_factor_vector | BUILT
DK estimator | Estimates diagonal kernel weights. | gae/dk_estimator.py:DKEstimator | BUILT
Coordinate descent estimator | Estimates weights by coordinate descent. | gae/dk_estimator.py:CoordinateDescentEstimator | BUILT
Covariance estimator | Computes covariance state. | gae/covariance.py:CovarianceEstimator | BUILT
Novelty tracker | Tracks novelty of factor vectors. | gae/novelty.py:NoveltyTracker | BUILT
Nearest-neighbor novelty | Computes nearest-neighbor novelty. | gae/novelty.py:NearestNeighborNovelty | BUILT
Shrinkage schedules | Computes fixed and ramped learning shrinkage. | gae/shrinkage.py:ShrinkageSchedule; FixedAlpha; LinearRampAlpha; compute_effective_weights | BUILT
Judgment computation | Converts score state into judgment results. | gae/judgment.py:compute_judgment | BUILT
Referral engine | Routes decisions to referral rules. | gae/referral.py:ReferralEngine | BUILT
Override detector | Detects override behavior. | gae/referral.py:OverrideDetector | BUILT
Theta-min computation | Computes conservation thresholds. | gae/calibration.py:compute_theta_min | BUILT
Conservation check | Checks conservation constraints. | gae/calibration.py:check_conservation | BUILT
Conservation status | Computes conservation phase status. | gae/calibration.py:conservation_status | BUILT
Breach window | Computes breach windows. | gae/calibration.py:compute_breach_window | BUILT
Optimal tau | Computes decision threshold tau. | gae/calibration.py:compute_optimal_tau | BUILT
Transfer prior | Computes transfer priors. | gae/calibration.py:compute_transfer_prior | BUILT
Conservation state machine | Tracks conservation phase transitions. | gae/convergence.py:ConservationStateMachine | BUILT
Conservation monitor | Monitors conservation state. | gae/convergence.py:ConservationMonitor | BUILT
OLS monitor | Monitors override lift. | gae/convergence.py:OLSMonitor | BUILT
Var-Q monitor | Monitors Q variance. | gae/convergence.py:VarQMonitor | BUILT
Convergence metrics | Computes half-life, MSE, asymptotic error, and reconvergence. | gae/convergence.py:compute_n_half; compute_steady_state_mse; compute_reconvergence_ratio | BUILT
Convergence predictions | Predicts decisions and weeks to convergence. | gae/convergence.py:predict_convergence_decisions; predict_category_convergence_weeks | BUILT
Evaluation runner | Runs evaluation scenarios and reports ECE. | gae/evaluation.py:run_evaluation; compute_ece | BUILT
SNR reporting | Computes category signal-to-noise reports. | gae/snr.py:compute_snr_report | BUILT
Kernel selector | Recommends scoring kernels. | gae/kernel_selector.py:KernelSelector | BUILT
Ablation runner | Runs component ablations. | gae/ablation.py:run_ablation | BUILT
Bootstrap calibration | Creates calibration and enriched priors. | gae/bootstrap.py:bootstrap_calibration; bootstrap_enriched_prior | BUILT
Batch promotion gate | Validates batch composition and promotion. | gae/batch_pipeline.py:DefaultPromotionGate | BUILT
State persistence | Saves and loads scorer state. | gae/store.py:save_state; load_state | BUILT
Evolution ledger | Records and summarizes evolution events. | gae/evolution.py:record_evolution_event; get_evolution_summary | BUILT
Two-phase policies | Defines decision-count, manual, and rolling-accuracy phase policies. | gae/two_phase.py | BUILT
DomainConfig and presets | Defines tensor, learning, and domain configuration. | gae/domain_config.py:DomainConfig | BUILT
CLI | Exposes packaged command-line operations. | gae/cli.py; pyproject.toml | BUILT
Packaged examples | Provides example scorer/configuration material. | graph-attention-engine-v50/examples | PARTIAL
GAE design validation scenarios | Specifies validation requirements without a directly mapped implementation. | gae_design_v10_10.md:validation sections | DESIGNED-ONLY
BUILT=36, PARTIAL=1, DESIGNED-ONLY=1, UNVERIFIED=0

COMPONENT: copilot-sdk
CODE ROOT: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk
PD DOC(S): rl_architecture.md; rl_consolidated_verification_and_design.md; judgment_memory_v2_9.md; math_synopsis_v18.md; demo_scenarios_and_usecases_v2_7.md; factor0_reconciliation_summary_v2.md
PURPOSE: Shared copilot runtime, learning, graph, evidence, evolution, transfer, pilot, and frontend infrastructure.

FEATURE | FUNCTIONALITY | EVIDENCE | STATUS
DomainShape | Represents category, action, and factor dimensions. | copilot_sdk/scoring/config.py:DomainShape | BUILT
DomainPreset | Stores domain scoring configuration. | copilot_sdk/scoring/config.py:DomainPreset | BUILT
CompoundingScorer | Scores and learns from decisions. | copilot_sdk/scoring/scorer.py:CompoundingScorer | BUILT
Scorer proxy | Exposes score, learn, state, and diagnostics operations. | copilot_sdk/backend/scorer_proxy.py:ScorerProxy | BUILT
Scoring router factory | Mounts score and scorer inspection endpoints. | copilot_sdk/backend/scoring_router.py:create_scoring_router | BUILT
Scoring endpoints | Mounts POST /score, POST /learn, GET /fingerprint, GET /trajectory, GET /health, GET /diagnostics, GET /history, and GET /measurement-state. | copilot_sdk/backend/scoring_router.py | BUILT
Measurement-state router | Returns named copilot measurement state. | copilot_sdk/backend/scoring_router.py:create_measurement_state_router; GET /{copilot}/measurement-state | BUILT
Conservation router | Mounts GET /conservation/status and POST /conservation/what-if. | copilot_sdk/backend/conservation_router.py:create_conservation_router | BUILT
Counterfactual router | Mounts POST /counterfactual. | copilot_sdk/backend/counterfactual_router.py:create_counterfactual_router | BUILT
Self-computation router | Mounts centroid history, replay, lineage, diagnostics, trust traps, rollback, decisions, audit trail, and decision flow endpoints. | copilot_sdk/backend/self_computation_router.py:create_self_computation_router | BUILT
Archetype router | Mounts GET /, GET /current, GET /{name}, and POST /apply/{name}. | copilot_sdk/backend/archetype_router.py:create_archetype_router | BUILT
Discovery router | Mounts POST /sweep, GET /digest, GET /alerts, and GET /cross-system. | copilot_sdk/backend/discovery_router.py:create_discovery_router | BUILT
Data intelligence router | Mounts profile, source, combination, acquisition, valuation, intelligence-map, query, search, and catalog endpoints. | copilot_sdk/backend/di_router.py:create_di_router | BUILT
Evolution router | Mounts GET /variants, GET /history, GET /promoted, GET /summary, POST /record-outcome, and POST /check-promotion. | copilot_sdk/backend/evolution_router.py:create_evolution_router | BUILT
Report router | Mounts GET /report/weekly. | copilot_sdk/backend/report_router.py:create_report_router | BUILT
Transfer router | Mounts GET /status, GET /opportunities, GET /demo, and POST /execute. | copilot_sdk/backend/transfer_router.py:create_transfer_router | BUILT
Self-transfer router | Mounts GET /transfers and POST /transfer. | copilot_sdk/backend/transfer_router.py:create_self_transfer_router | BUILT
Variant store | Stores variant definitions and statistics. | copilot_sdk/evolution/variant_store.py:VariantStore; InMemoryVariantStore; SQLiteVariantStore | BUILT
Evolution ledger | Stores evolution events. | copilot_sdk/evolution/ledger.py:InMemoryEvolutionLedger | BUILT
Evolution protocols | Defines event, rule, ledger, store, selector, shadow, and promotion interfaces. | copilot_sdk/evolution/protocol.py | BUILT
Shadow runner | Executes variants in shadow mode. | copilot_sdk/evolution/shadow.py:DefaultShadowRunner | BUILT
Prompt variant evolver | Generates and manages prompt variants. | copilot_sdk/evolution/prompt_evolver.py:PromptVariantEvolver | BUILT
Agent evolver | Coordinates agent evolution. | copilot_sdk/evolution/evolver.py:AgentEvolver | BUILT
Promotion engine | Manages promotion stages and records. | copilot_sdk/promotion/core.py:PromotionEngine | BUILT
Promotion policies | Provides S2P, SOC, Trading, Purchasing, and DataOps policies. | copilot_sdk/promotion/policies.py | BUILT
Verified outcome | Represents a human-verified decision receipt. | copilot_sdk/outcome/models.py:VerifiedOutcome | BUILT
Outcome processor | Idempotently processes verified outcomes. | copilot_sdk/outcome/processor.py:OutcomeProcessor | BUILT
Outcome ledger | Persists verified outcomes. | copilot_sdk/outcome/ledger.py:OutcomeLedger | BUILT
Outcome router | Mounts POST /api/outcome/process, GET /api/outcome/{receipt_id}, and GET /api/outcome/count. | copilot_sdk/outcome/router.py:create_outcome_router | BUILT
Outcome adapters | Bridges legacy reward-shaped records to verified outcomes. | copilot_sdk/outcome/adapters.py:reward_to_outcome; outcome_to_reward | PARTIAL
Reward compatibility layer | Provides legacy reward functions while migration remains in progress. | copilot_sdk/rl/reward.py; copilot_sdk/rl/reward_functions.py | PARTIAL
Frozen Snapshot | Stores immutable scorer, kernel, conservation, IKS, and checksum state. | copilot_sdk/twin/models.py:FrozenSnapshot | BUILT
Frozen Twin | Compares immutable day-zero and live scoring. | copilot_sdk/twin/service.py:FrozenTwin | BUILT
Frozen Twin store | Persists snapshots across restarts. | copilot_sdk/twin/store.py:FrozenTwinStore | BUILT
Frozen Twin router | Mounts GET /api/twin/status, GET /api/twin/drift, GET /api/twin/parallel-score, and POST /api/twin/freeze. | copilot_sdk/twin/router.py:create_frozen_twin_router | BUILT
Evidence gate | Assigns evidence maturity tiers. | copilot_sdk/evidence/gate.py:EvidenceGate | BUILT
Pilot qualification | Provides pilot readiness and transfer qualification. | copilot_sdk/pilot | BUILT
Situation analyzer | Builds situation context. | copilot_sdk/situation/analyzer.py:SituationAnalyzer | BUILT
Regime detector | Detects regime state. | copilot_sdk/regime/detector.py:RegimeDetector | BUILT
Regime conditioner | Applies regime-specific context. | copilot_sdk/regime/conditioner.py:RegimeConditioner | BUILT
Per-regime centroids | Tracks centroids by regime. | copilot_sdk/regime/conditioning.py:PerRegimeCentroidTracker | BUILT
Transfer registry | Stores reusable transfer patterns. | copilot_sdk/transfer/registry.py:SharedPatternRegistry | BUILT
Cross-domain traversal | Traverses cross-copilot relationships. | copilot_sdk/transfer/cross_domain.py:CrossDomainTraversal | BUILT
Warm start | Applies transferred centroids. | copilot_sdk/transfer/warm_start.py:warm_start_centroids | BUILT
GraphStore protocol | Defines shared graph operations. | copilot_sdk/graph/protocol.py:GraphStore | BUILT
In-memory graph store | Provides isolated graph state. | copilot_sdk/graph/in_memory.py:InMemoryGraphStore | BUILT
SQLite graph store | Provides durable graph state. | copilot_sdk/graph/sqlite.py:SQLiteGraphStore | BUILT
AGE graph store | Provides AGE graph access. | copilot_sdk/graph/age.py:AGEGraphStore | BUILT
Protocol V2 graph store | Provides protocol-v2 graph operations. | copilot_sdk/graph/protocol_v2.py:ProtocolV2GraphStore | BUILT
Dual-write store | Writes to canonical and secondary stores. | copilot_sdk/graph/dual_write.py:DualWriteStore | BUILT
Outbox | Persists pending writes for replay. | copilot_sdk/outbox | BUILT
Scaffold generator | Generates a new copilot from YAML. | copilot_sdk/scaffold/generator.py:CopilotScaffold | BUILT
Enterprise ROI | Aggregates financial impact across copilots. | copilot_sdk/enterprise/calculator.py:SunkInvestmentCalculator | BUILT
Demo runner | Runs product demonstration flows. | demo.py | BUILT
Preseed tool | Seeds all copilot demo state. | scripts/preseed_all_copilots.py | BUILT
Truth preflight | Checks demo provenance and readiness. | scripts/demo_truth_preflight.py | BUILT
Hero moments | Runs C2, C3, C4, and C5 sequences. | scripts/hero_moments.py | BUILT
Loom gauntlet | Runs heroes and produces storyboard output. | scripts/loom_gauntlet.py | BUILT
Scaffold CLI | Generates a copilot from a YAML file. | scripts/create_copilot.py | BUILT
Shared frontend components | Provides reusable frontend TSX components. | copilot_sdk/frontend; no shared TSX implementation located | UNVERIFIED
Framework router extraction | Provides one domain-parameterized framework router for SOC and S2P. | Requested SDK file copilot_sdk/backend/framework_router.py not located; local consumer copies exist | DESIGNED-ONLY
BUILT=45, PARTIAL=2, DESIGNED-ONLY=1, UNVERIFIED=1

COMPONENT: SOC
CODE ROOT: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50
PD DOC(S): soc_copilot_design_v5_11.md; soc_campaign_v6_context_injection_v2_2.md; demo_scenarios_and_usecases_v2_7.md; factor0_reconciliation_summary_v2.md
PURPOSE: Security operations triage, threat enrichment, analyst referral, learning, and governed autonomy.

FEATURE | FUNCTIONALITY | EVIDENCE | STATUS
SOC tensor | Uses code shape C=6, A=4, d=6. | copilot_sdk/scoring/presets/soc.py:SocPreset | BUILT
SOC penalty ratio | Uses penalty ratio 20.0. | copilot_sdk/scoring/presets/soc.py:SocPreset | BUILT
Factor: privileged_identity_context | Computes privileged identity context. | copilot_sdk/scoring/presets/soc.py:factors[0] | BUILT
Factor: asset_criticality | Computes asset criticality. | soc.py:factors[1] | BUILT
Factor: threat_intel_enrichment | Computes threat intelligence enrichment. | soc.py:factors[2] | BUILT
Factor: pattern_history | Computes pattern history. | soc.py:factors[3] | BUILT
Factor: time_anomaly | Computes time anomaly. | soc.py:factors[4] | BUILT
Factor: device_trust | Computes device trust. | soc.py:factors[5] | BUILT
PD category: malware_delivery | Defines malware delivery. | soc_copilot_design_v5_11.md:§5.1 | DESIGNED-ONLY
PD category: phishing | Defines phishing. | soc_copilot_design_v5_11.md:§5.1 | DESIGNED-ONLY
Code category: credential_access | Represents credential access. | soc.py:categories[0] | BUILT
Code category: malware_execution | Represents malware execution. | soc.py:categories[1] | BUILT
Code category: lateral_movement | Represents lateral movement. | soc.py:categories[2] | BUILT
Code category: data_exfiltration | Represents data exfiltration. | soc.py:categories[3] | BUILT
Code category: insider_threat | Represents insider threat. | soc.py:categories[4] | BUILT
Code category: cloud_infrastructure | Represents cloud infrastructure. | soc.py:categories[5] | BUILT
Factor orchestrator | Runs factor computers and preserves provenance. | backend/app/domains/soc/orchestrator.py:FactorOrchestrator | BUILT
Pattern history factor | Accumulates historical alert evidence. | backend/app/domains/soc/factors.py:PatternHistoryFactorComputer | BUILT
Threat intelligence factor | Enriches alerts from threat intelligence. | backend/app/domains/soc/factors.py:ThreatIntelEnrichment | BUILT
Triage router | Scores alerts and records triage decisions. | backend/app/routers/triage.py:POST /api/triage/analyze; POST /api/triage/decide; GET /api/triage/health | BUILT
Alert router | Lists and retrieves alerts. | backend/app/routers/alerts.py:GET /api/alerts; GET /api/alerts/{alert_id} | BUILT
Learning control | Controls shadow and learning state. | backend/app/services/soc_learning_control.py:SOCLearningControl | BUILT
Framework router | Exposes graph, scorer, shadow, checkpoint, and intervention controls. | backend/app/routers/framework_router.py | BUILT
Conservation service | Computes conservation state and veto status. | backend/app/services/conservation.py:ConservationService | BUILT
Learning service | Applies verified learning. | backend/app/services/learning.py:LearningService | BUILT
Shadow service | Runs parallel shadow decisions. | backend/app/services/shadow.py:ShadowModeService | BUILT
IKS service | Computes institutional knowledge. | backend/app/services/iks.py:compute_iks | BUILT
NL template engine | Renders evidence explanations. | backend/app/services/nl_templates.py:NLTemplateEngine | BUILT
Referral service | Routes decisions to review. | backend/app/services/referral.py:ReferralService | BUILT
Authority ladder | Persists per-class authority and applies conservation vetoes. | backend/app/services/authority_ladder.py:AuthorityLadder | BUILT
No-precedent detector | Identifies novel alerts. | backend/app/services/no_precedent.py:NoPrecedentDetector | BUILT
What-if inspector | Computes per-factor decision boundaries. | backend/app/services/what_if.py:WhatIfInspector | BUILT
Campaign context injection | Injects campaign context into decisions. | soc_campaign_v6_context_injection_v2_2.md; backend campaign context services | PARTIAL
SOC frontend screens | Provides Triage, Intelligence, Learning, and Settings screens. | frontend/src/screens | BUILT
Control Room | Displays learning controls and authority state. | frontend/src/components/LearningControlRoom.tsx | BUILT
Authority ladder panel | Displays per-class authority. | frontend/src/components/AuthorityLadder.tsx | BUILT
No-precedent sidebar | Displays insufficient evidence. | frontend/src/components/NoPrecedentSidebar.tsx | BUILT
What-if panel | Displays factor changes. | frontend/src/components/WhatIfPanel.tsx | BUILT
SOC-LADDER | Demonstrates earned authority and conservation veto. | authority_ladder.py; demo_scenarios_and_usecases_v2_7.md | BUILT
SOC-TWIN | Demonstrates frozen versus live scoring. | framework_router.py; twin integration | PARTIAL
SOC-FRONTIER | Demonstrates no-precedent evidence. | no_precedent.py | PARTIAL
BUILT=27, PARTIAL=4, DESIGNED-ONLY=2, UNVERIFIED=0

COMPONENT: Trading
CODE ROOT: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\trading
PD DOC(S): trading_copilot_product_definition_v1_1_corrected.md; demo_scenarios_and_usecases_v2_7.md; factor0_reconciliation_summary_v2.md
PURPOSE: Observation-only trading analysis, regime-conditioned judgment, volatility analytics, and evidence-gated learning.

FEATURE | FUNCTIONALITY | EVIDENCE | STATUS
Trading tensor | Uses code shape C=5, A=4, d=10. | apps/trading/backend/app/domain_config.py; copilot_sdk/scoring/presets/trading.py | BUILT
PD core tensor | Specifies 5x4x7 before the v1.1 option extension. | trading_copilot_product_definition_v1_1_corrected.md:§7.2 | PARTIAL
Tensor discrepancy | Code=(5,4,10); PD core=(5,4,7); v1.1 extension=(5,4,10). | code and PD references above | PARTIAL
Trading penalty ratio | Uses penalty ratio 3.0. | copilot_sdk/scoring/presets/trading.py:TradingPreset | BUILT
Category: trend_following | Represents trend-following. | trading.py:categories[0] | BUILT
Category: mean_reversion | Represents mean-reversion. | trading.py:categories[1] | BUILT
Category: event_driven | Represents event-driven. | trading.py:categories[2] | BUILT
Category: income_strategy | Represents income strategy. | trading.py:categories[3] | BUILT
Category: scalp_intraday | Represents scalp and intraday. | trading.py:categories[4] | BUILT
Factor: signal_alignment | Represents signal alignment. | trading.py:factors[0] | BUILT
Factor: market_regime | Represents market regime. | trading.py:factors[1] | BUILT
Factor: position_sizing | Represents position sizing. | trading.py:factors[2] | BUILT
Factor: timing_quality | Represents timing. | trading.py:factors[3] | BUILT
Factor: risk_reward_actual | Represents realized risk/reward. | trading.py:factors[4] | BUILT
Factor: emotional_indicator | Represents emotional indicators. | trading.py:factors[5] | BUILT
Factor: signal_confidence | Represents signal confidence. | trading.py:factors[6] | BUILT
Factor: options_delta_exposure | Represents options delta. | trading.py:factors[7] | BUILT
Factor: options_iv_percentile | Represents options IV percentile. | trading.py:factors[8] | BUILT
Factor: options_gamma_risk | Represents options gamma risk. | trading.py:factors[9] | BUILT
Trade import | Imports CSV and broker trades. | backend/app/routers/data_import.py:POST /api/trading/import/csv; POST /api/trading/import/broker | BUILT
Trade journal | Stores entries, reflections, tags, and queries. | backend/app/routers/journal.py; services/journal_query.py:JournalQueryService | BUILT
Signal trust dashboard | Displays signal trust. | frontend/src/components/TrustRadarPanel.tsx | BUILT
Decision quality scorer | Scores trade quality. | backend/app/services/decision_quality.py:DecisionQualityScorer | BUILT
Pattern detector | Detects trade patterns. | backend/app/services/pattern_detector.py:PatternDetector | BUILT
Conservation dashboard | Displays strategy safety state. | backend/app/routers/conservation.py; frontend/src/components/ConservationPanel.tsx | BUILT
IKS | Computes institutional knowledge. | backend/app/services/iks.py | BUILT
Claim gate | Gates selection-adjusted claims. | backend/app/services/claim_gate.py:TradingClaimRegistry; TradingPromotionGuard | BUILT
Regime classifier | Classifies market regimes. | backend/app/services/regime_classifier.py:RegimeClassifier | BUILT
Regime mirror | Shows behavior by regime. | backend/app/routers/regime_beats.py:GET /api/trading/regime/mirror | BUILT
Situational abstention | Shows abstention under uncertainty. | regime_beats.py:GET /api/trading/regime/abstention | BUILT
Autonomy throttle | Shows authority reduction after regime break. | regime_beats.py:GET /api/trading/regime/throttle | BUILT
Regime rejection | Shows regime-scoped rejections. | regime_beats.py:GET /api/trading/regime/rejection | BUILT
Promotion engine | Generates, shadows, promotes, applies, and rolls back variants. | backend/app/routers/evolution_router.py | BUILT
Volatility analytics | Computes Sharpe, VRP, rich/cheap, dispersion, and tail-bet observations. | backend/app/services/volatility_analytics.py:VolatilityAnalytics | BUILT
Volatility endpoints | Mounts GET /api/trading/volatility/sharpe, /vrp, /rich-cheap, /dispersion, and /tail-bets. | backend/app/routers/volatility_router.py | BUILT
Correlation monitor | Computes correlation and concentration. | backend/app/services/correlation.py:CorrelationService | BUILT
Broker router | Mounts GET /status, /account, /positions, /orders, GET /orders/{order_id}, POST /orders, and POST /sync. | backend/app/routers/broker_router.py | PARTIAL
Observation-only execution gate | Blocks live order execution by default. | broker router and trading settings | PARTIAL
Execution analyzer | Compares broker execution outcomes. | backend/app/services/execution_analysis.py:ExecutionAnalyzer | BUILT
TradingView webhook | Receives and inspects TradingView events. | backend/app/routers/webhook.py | BUILT
Social trader surfaces | Lists traders, compares profiles, and scores-as another trader. | backend/app/routers/social.py | BUILT
Frontend screens | Provides Analysis, Dashboard, Journal, Log Trade, Performance, and Trade Detail screens. | apps/trading/frontend/src/screens | BUILT
Demo panels | Provides regime, volatility, claim, certificate, dividend, and rejection panels. | apps/trading/frontend/src/components/DemoBeatPanels.tsx | BUILT
Scenarios T1-T20 | Defines signal, scaling, self-knowledge, governance, preservation, and volatility scenarios. | trading_copilot_product_definition_v1_1_corrected.md:§3 | PARTIAL
BUILT=35, PARTIAL=5, DESIGNED-ONLY=0, UNVERIFIED=0

COMPONENT: Purchasing
CODE ROOT: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\purchasing
PD DOC(S): purchasing_copilot_pd_v1_4.md; demo_scenarios_and_usecases_v2_7.md; factor0_reconciliation_summary_v2.md
PURPOSE: Food-service purchasing analysis, supplier intelligence, order decisions, proof-ledger governance, and kitchen continuity.

FEATURE | FUNCTIONALITY | EVIDENCE | STATUS
Purchasing tensor | Uses shape C=5, A=4, d=7. | copilot_sdk/scoring/presets/purchasing.py:PurchasingPreset | BUILT
Purchasing penalty ratio | Uses penalty ratio 3.0. | purchasing.py:PurchasingPreset | BUILT
Category: protein | Represents protein purchasing. | purchasing.py:categories[0] | BUILT
Category: produce | Represents produce purchasing. | purchasing.py:categories[1] | BUILT
Category: dairy | Represents dairy purchasing. | purchasing.py:categories[2] | BUILT
Category: dry_goods | Represents dry goods purchasing. | purchasing.py:categories[3] | BUILT
Category: beverages | Represents beverage purchasing. | purchasing.py:categories[4] | BUILT
Factor: expected_demand | Represents expected demand. | purchasing.py:factors[0] | BUILT
Factor: day_of_week | Represents day-of-week effects. | purchasing.py:factors[1] | BUILT
Factor: weather_forecast | Represents weather. | purchasing.py:factors[2] | BUILT
Factor: event_flag | Represents events. | purchasing.py:factors[3] | BUILT
Factor: historical_waste | Represents historical waste. | purchasing.py:factors[4] | BUILT
Factor: supplier_lead_time | Represents supplier lead time. | purchasing.py:factors[5] | BUILT
Factor: price_memory_index | Represents price memory. | purchasing.py:factors[6] | BUILT
Core routers | Mount alerts, auto-order, chain, commodity, delivery, discovery, economic, event, evidence, IKS, match, menu, multi-unit, PAR, POS, queue, regime, scorecard, signal, spend, trust, trust weights, and verification endpoints. | apps/purchasing/backend/app/routers/*.py | BUILT
Purchasing control router | Mounts proof ledger, handoff pack, day-zero, legal exposure, frozen twin, promotion, discovery gate, and yield quote audit endpoints. | backend/app/routers/purchasing_control.py | BUILT
Compounding ledger | Stores purchasing proof and competence state. | backend/app/services/compounding_ledger.py:CompoundingLedger | BUILT
Supplier intelligence | Composes supplier profiles and behavioral metrics. | backend/app/services/supplier_intelligence.py:SupplierIntelligenceComposer | BUILT
Supplier profile accumulator | Accumulates supplier events. | backend/app/services/supplier_profile_accumulator.py:SupplierProfileAccumulator | BUILT
Synthetic invoice generator | Generates invoice and supplier fixtures. | backend/app/services/synthetic_invoices.py:SyntheticInvoiceGenerator | BUILT
Regime service | Computes purchasing situation. | backend/app/services/regime_service.py:RegimeService | BUILT
Evidence service | Computes evidence and proof states. | backend/app/services/evidence_service.py:EvidenceService | BUILT
Frozen Twin service | Compares current and day-zero scoring. | backend/app/services/frozen_twin_service.py:FrozenTwinService | BUILT
Promotion service | Advances purchasing decision classes. | backend/app/services/promotion_service.py:PromotionService | BUILT
Signal gate | Gates supplier signals by evidence. | backend/app/services/signal_gate.py:SignalGate | BUILT
QBO connector | Reads QuickBooks Online purchasing data. | backend/app/connectors/qbo.py:QBOConnector | PARTIAL
Frontend screens | Provides Analysis, Dashboard, Inventory, Order, and Performance screens. | apps/purchasing/frontend/src/screens | BUILT
Purchasing beat panels | Provides MirrorOpen, GatedSignalReliability, ProofLedger, SelfPause, TimeToCompetence, NotYet, and ContinuityClose panels. | apps/purchasing/frontend/src/components/PurchasingBeatPanels.tsx | BUILT
PUR-HERO | Shows mirror open and continuity close. | PurchasingBeatPanels.tsx | BUILT
PUR-GATE | Shows gated signal reliability. | PurchasingBeatPanels.tsx | BUILT
PUR-PROOF-LEDGER | Shows proof and competence curves. | PurchasingBeatPanels.tsx | BUILT
PUR-REFUSAL | Shows self-pause after drift. | PurchasingBeatPanels.tsx | BUILT
PUR-RAMP | Shows time-to-competence ramp. | PurchasingBeatPanels.tsx | BUILT
PUR-NOT-YET | Shows day-zero or quiet-week state. | PurchasingBeatPanels.tsx | BUILT
PD scenarios P1-P10 | Defines purchasing foundation, supplier, cross-system, and disruption scenarios. | purchasing_copilot_pd_v1_4.md:§3 | PARTIAL
PD scenarios S1-S16 | Defines exception, autonomy, supplier, discovery, disruption, and continuity scenarios. | purchasing_copilot_pd_v1_4.md:§PD2 | PARTIAL
BUILT=28, PARTIAL=4, DESIGNED-ONLY=0, UNVERIFIED=0

COMPONENT: DataOps
CODE ROOT: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\dataops
PD DOC(S): dataops_copilot_design_v1_9.md; demo_scenarios_and_usecases_v2_7.md; factor0_reconciliation_summary_v2.md
PURPOSE: Data-system monitoring, root-cause analysis, self-computation, discovery, governance, and data-product intelligence.

FEATURE | FUNCTIONALITY | EVIDENCE | STATUS
DataOps tensor | Uses shape C=6, A=5, d=6. | copilot_sdk/scoring/presets/dataops.py:DataOpsPreset | BUILT
DataOps penalty ratio | Uses penalty ratio 10.0. | dataops.py:DataOpsPreset | BUILT
Category: schema_change | Represents schema changes. | dataops.py:categories[0] | BUILT
Category: volume_anomaly | Represents volume anomalies. | dataops.py:categories[1] | BUILT
Category: quality_anomaly | Represents quality anomalies. | dataops.py:categories[2] | BUILT
Category: freshness_violation | Represents freshness violations. | dataops.py:categories[3] | BUILT
Category: pipeline_failure | Represents pipeline failures. | dataops.py:categories[4] | BUILT
Category: transform_drift | Represents transform drift. | dataops.py:categories[5] | BUILT
Factor: impact_scope | Represents affected impact scope. | dataops.py:factors[0] | BUILT
Factor: source_reliability | Represents source reliability. | dataops.py:factors[1] | BUILT
Factor: recurrence_frequency | Represents recurrence. | dataops.py:factors[2] | BUILT
Factor: downstream_urgency | Represents downstream urgency. | dataops.py:factors[3] | BUILT
Factor: data_freshness | Represents freshness. | dataops.py:factors[4] | BUILT
Factor: business_criticality | Represents business criticality. | dataops.py:factors[5] | BUILT
Context router | Provides pipeline, alert, system, decision, and process context. | backend/app/context_router.py | BUILT
AE router | Provides recommendation, impact, pattern, rule, incident, conservation, and transfer endpoints. | backend/app/ae_router.py | BUILT
DI router | Provides profiles, acquisitions, and intelligence-map endpoints. | backend/app/main.py; backend/app/routers/di_router.py | BUILT
DI enrichment router | Returns source consumers, trust, and products. | backend/app/routers/di_enrichment_router.py | BUILT
DI gateway | Verifies external-agent trust. | backend/app/routers/di_gateway.py:GET /trust/verify | BUILT
Governance router | Provides claims, abstention, holdouts, provenance, promotion, and frozen-twin endpoints. | backend/app/routers/governance_router.py | BUILT
Enterprise router | Returns enterprise health and process data. | backend/app/routers/enterprise_router.py | BUILT
DI demo beats | Provides earned-trust, acquisition, abstention, gateway, source-compounding, and frozen-twin endpoints. | backend/app/routers/di_demo_beats.py | BUILT
Graph configuration | Loads centralized graph configuration. | backend/app/graph_status.py:DataOpsActiveGraphConfig | BUILT
AGE graph store | Provides AGE graph access and status. | backend/app/graph_status.py:DataOpsActiveAGEGraphStore | BUILT
Graph client | Reads pipelines, alerts, systems, dependencies, recurrence, and factors. | backend/app/graph_queries.py:DataOpsGraphClient | BUILT
Graph enricher | Writes domain-scoped enrichment. | backend/app/graph_enrichment.py:DataOpsGraphEnricher | BUILT
Governance service | Tracks claims, holdouts, abstention, provenance, promotion, and twin state. | backend/app/dataops_governance.py:DataOpsGovernance | BUILT
Celonis connector | Reads knowledge models, KPIs, and process data. | backend/app/celonis_connector.py:CelonisConnector | PARTIAL
SAP connector | Reads purchase orders, invoices, and suppliers. | backend/app/sap_connector.py:SAPConnector | PARTIAL
Frontend screens | Provides Curve, Dashboard, Evidence, Insight, and Triage screens. | apps/dataops/frontend/src/screens | BUILT
Source trust card | Displays source trust. | frontend/src/components/SourceTrustCard.tsx | BUILT
Intelligence map | Displays source and relationship maps. | frontend/src/components/IntelligenceMapPanel.tsx | BUILT
Frozen twin panel | Displays frozen state. | frontend/src/components/FrozenTwinControlPanel.tsx | BUILT
Agent trust gateway | Displays agent trust state. | frontend/src/components/AgentTrustGatewayPanel.tsx | BUILT
Acquisition advisor | Displays acquisition advice. | frontend/src/components/AcquisitionAdvisorPanel.tsx | BUILT
Source compounding | Displays source compounding. | frontend/src/components/SourceCompoundingPanel.tsx | BUILT
Governance panel | Displays claims and governance. | frontend/src/components/DataOpsGovernancePanel.tsx | BUILT
H1 self-aware data | Provides fingerprints and source trust. | dataops_copilot_design_v1_9.md:§36 H1 | BUILT
H2 self-combining data | Discovers cross-source combinations. | dataops_copilot_design_v1_9.md:§36 H2 | BUILT
H3 self-correcting data | Provides self-correction and enrichment. | dataops_copilot_design_v1_9.md:§36 H3 | PARTIAL
H4 self-governing data | Provides conservation and abstention governance. | dataops_copilot_design_v1_9.md:§36 H4 | BUILT
H5 self-valuating data | Provides valuation and acquisition advice. | dataops_copilot_design_v1_9.md:§36 H5 | BUILT
H6 agent-ready trust | Provides trust verification to agents. | dataops_copilot_design_v1_9.md:§36 H6 | BUILT
DI-TWIN | Demonstrates DataOps frozen twin comparison. | di_demo_beats.py:frozen-twin | BUILT
BUILT=34, PARTIAL=3, DESIGNED-ONLY=0, UNVERIFIED=0

COMPONENT: S2P
CODE ROOT: C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot
PD DOC(S): s2p_copilot_unified_v1_4.md; demo_scenarios_and_usecases_v2_7.md; factor0_reconciliation_summary_v2.md
PURPOSE: Source-to-pay invoice and procurement decision triage, supplier intelligence, learning, governance, and earned automation.

FEATURE | FUNCTIONALITY | EVIDENCE | STATUS
S2P tensor | Uses shape C=5, A=5, d=8. | backend/app/domains/s2p/config.py; copilot_sdk/scoring/presets/s2p.py | BUILT
Legacy tensor text | Some later PD text refers to the older 5x5x7 shape. | s2p_copilot_unified_v1_4.md:legacy roadmap sections | PARTIAL
Tensor discrepancy | Code and primary engineering section use 5x5x8; stale PD text uses 5x5x7. | code=(5,5,8); PD primary=(5,5,8); PD stale=(5,5,7) | PARTIAL
S2P penalty ratio | Uses penalty ratio 5.0. | copilot_sdk/scoring/presets/s2p.py:S2PPreset | BUILT
Category: price_variance | Represents price variance. | s2p.py:categories[0] | BUILT
Category: quantity_mismatch | Represents quantity mismatch. | s2p.py:categories[1] | BUILT
Category: duplicate_risk | Represents duplicate risk. | s2p.py:categories[2] | BUILT
Category: contract_gap | Represents contract gaps. | s2p.py:categories[3] | BUILT
Category: format_compliance | Represents format compliance. | s2p.py:categories[4] | BUILT
PD category: routine_purchase | Represents routine purchases in the engineering design. | s2p_copilot_unified_v1_4.md:§7.2 | PARTIAL
PD category: high_value_contract | Represents high-value contracts. | s2p_copilot_unified_v1_4.md:§7.3 | PARTIAL
PD category: compliance_sensitive | Represents compliance-sensitive purchases. | s2p_copilot_unified_v1_4.md:§7.4 | PARTIAL
PD category: sole_source | Represents sole-source purchases. | s2p_copilot_unified_v1_4.md:§7.5 | PARTIAL
PD category: emergency_procurement | Represents emergency procurement. | s2p_copilot_unified_v1_4.md:§7.6 | PARTIAL
Factor: match_status | Represents match status. | s2p.py:factors[0] | BUILT
Factor: amount_variance_ratio | Represents amount variance. | s2p.py:factors[1] | BUILT
Factor: duplicate_score | Represents duplicate likelihood. | s2p.py:factors[2] | BUILT
Factor: supplier_exception_history | Represents supplier exception history. | s2p.py:factors[3] | BUILT
Factor: payment_terms_impact | Represents payment terms. | s2p.py:factors[4] | BUILT
Factor: commodity_index_correlation | Represents commodity correlation. | s2p.py:factors[5] | BUILT
Factor: tax_regulatory_compliance | Represents tax and regulatory compliance. | s2p.py:factors[6] | BUILT
Factor: environmental_risk | Represents environmental risk. | s2p.py:factors[7] | BUILT
S2P score router | Mounts POST /api/s2p/score, POST /api/s2p/learn, POST /api/s2p/outcome, GET /api/s2p/diagnostics, GET /api/s2p/iks, and GET /api/s2p/learning-gate. | backend/app/routers/s2p.py | BUILT
Auto-approve router | Mounts GET /status, POST /enable, POST /disable, GET /audit, and POST /evaluate. | backend/app/routers/s2p_auto_approve.py | BUILT
Autonomy router | Mounts promotion and twin status, advance, rollback, transfer, drift, and freeze endpoints. | backend/app/routers/s2p_autonomy.py | BUILT
Demo beats router | Mounts extinction, frozen twin, what-if, day-zero, confidence, and rule-vs-reasoning endpoints. | backend/app/routers/s2p_demo_beats.py | BUILT
Evolution router | Mounts rules, variants, dimensions, proposal, promotion-check, reset, shadow-results, and promoted endpoints. | backend/app/routers/s2p_evolution.py | BUILT
Evidence router | Mounts receipts, audit trail, chain integrity, audit pack, template, rules, and compliance endpoints. | backend/app/routers/s2p_evidence.py | BUILT
Discovery router | Mounts alerts, disruptions, extended discoveries, supplier discoveries, and propagation. | backend/app/routers/s2p_discovery.py | BUILT
Early warning router | Mounts early-warning patterns, early warnings, trends, and trend signals. | backend/app/routers/s2p_early_warning.py | BUILT
Enrichment router | Mounts enrichment execution, summary, alerts, and supplier endpoints. | backend/app/routers/s2p_enrichment.py | BUILT
Centroid explorer | Mounts centroid export, import, inspection, drift, DK weights, ranking, and contribution endpoints. | backend/app/routers/s2p_explorer.py | BUILT
Insight router | Mounts fingerprint, similarity, process context, cross-graph, and process signals. | backend/app/routers/s2p_insight.py | BUILT
Ledger router | Mounts timeline, summary, IKS trajectory, and conservation history. | backend/app/routers/s2p_ledger.py | BUILT
Novelty router | Mounts novelty status, history, rate, auto-pause, and triggered-decisions. | backend/app/routers/s2p_novelty.py | BUILT
Proposals router | Mounts proposal creation, retrieval, confirmation, override, and audit. | backend/app/routers/s2p_proposals.py | BUILT
Simulation router | Mounts scenarios, what-if, impact summary, simulation, and batch simulation. | backend/app/routers/s2p_simulation.py | BUILT
Situation router | Returns situation context for a decision. | backend/app/routers/s2p_situation.py:GET /situation/{decision_id} | BUILT
Supplier router | Mounts supplier profiles, history, clustering, declining suppliers, heatmaps, and correlations. | backend/app/routers/s2p_suppliers.py | BUILT
Performance router | Mounts trajectory, what-if, and summary. | backend/app/routers/s2p_performance.py | BUILT
Preview router | Mounts isolated preview queue, conservation, compounding, suppliers, and config. | backend/app/routers/s2p_preview.py | BUILT
Process fusion | Combines procurement and process signals. | backend/app/routers/s2p_process_fusion.py:POST /process-fusion | BUILT
Payment router | Provides payment strategy, portfolio, and behavior. | backend/app/routers/s2p_payment.py | BUILT
PVG router | Provides variant, impact, leakage, and cycle-time views. | backend/app/routers/s2p_pvg.py | BUILT
Control tower | Classifies intents and manages queues. | backend/app/routers/s2p_control_tower.py | BUILT
Clustering router | Provides clusters and similarity. | backend/app/routers/s2p_clustering.py | BUILT
Financial router | Provides financial impact and trend views. | backend/app/routers/financial_router.py | BUILT
Compliance router | Screens compliance and returns reports. | backend/app/routers/compliance_router.py | BUILT
Factor proposer | Analyzes and proposes factors. | backend/app/routers/factor_proposer_router.py | BUILT
Lead-time router | Provides lead-time summaries, suppliers, and alerts. | backend/app/routers/lead_time_router.py | BUILT
Optimizer router | Exports and validates optimizer state. | backend/app/routers/optimizer_router.py | BUILT
Graph reader | Reads domain-scoped graph state. | backend/app/graph/s2p_graph_reader.py:S2PGraphReader | BUILT
Supplier intelligence | Builds supplier profiles and risk tiers. | backend/app/services/supplier_intelligence.py:SupplierIntelligenceComposer | BUILT
Supplier profile accumulator | Accumulates supplier events. | backend/app/services/supplier_profile_accumulator.py:SupplierProfileAccumulator | BUILT
Synthetic invoice generator | Generates procurement demo invoices. | backend/app/services/synthetic_invoices.py:SyntheticInvoiceGenerator | BUILT
Situation traversal | Builds graph-backed decision context. | backend/app/services/situation_traversals.py | BUILT
Frontend screens | Provides Dashboard, Evidence, Insight, Performance, Suppliers, and Triage screens. | apps/s2p/frontend/src/screens | BUILT
Frozen Twin comparison panel | Displays current versus day-one scoring. | apps/s2p/frontend/src/components/FrozenTwinComparisonPanel.tsx | BUILT
What-if inspector panel | Displays factor sensitivity and boundaries. | apps/s2p/frontend/src/components/WhatIfInspectorPanel.tsx | BUILT
Day-zero readiness panel | Displays missing evidence and readiness. | apps/s2p/frontend/src/components/DayZeroReadinessPanel.tsx | BUILT
Exception extinction timeline | Displays Discover, Shadow, and Promote progression. | apps/s2p/frontend/src/components/ExceptionExtinctionTimeline.tsx | BUILT
Confidence band panel | Displays confidence and novelty. | apps/s2p/frontend/src/components/ConfidenceBandPanel.tsx | BUILT
Scenario S2P-ROUTINE-01 | Scores a routine approval. | s2p_copilot_unified_v1_4.md:§15 | BUILT
Scenario S2P-SOLE-SOURCE-01 | Handles sole-source escalation. | s2p_copilot_unified_v1_4.md:§15 | BUILT
Scenario S2P-PRICE-SPIKE-01 | Handles a financial-risk hold. | s2p_copilot_unified_v1_4.md:§15 | BUILT
Scenario S2P-LEARN-01 | Exercises learning prerequisites. | s2p_copilot_unified_v1_4.md:§15 | BUILT
Scenario S2P-SANCTIONS-01 | Handles compliance escalation. | s2p_copilot_unified_v1_4.md:§15 | BUILT
Scenario S2P-COMPOUND-01 | Handles a multi-domain compound shock. | s2p_copilot_unified_v1_4.md:§15 | BUILT
S2P-EXTINCT | Demonstrates exception extinction. | backend/app/routers/s2p_demo_beats.py:GET /evolution/extinction | BUILT
S2P-TWIN | Demonstrates frozen scorer comparison. | s2p_demo_beats.py:GET /learning/frozen-twin | BUILT
S2P-WHATIF | Demonstrates counterfactual factor sensitivity. | s2p_demo_beats.py:GET /context/what-if/{invoice_id} | BUILT
S2P-DAY0 | Demonstrates readiness and missing evidence. | s2p_demo_beats.py:GET /diagnostics/day-zero | BUILT
S2P-CONFIDENCE | Demonstrates confidence bands and novelty. | s2p_demo_beats.py:GET /diagnostics/confidence | BUILT
S2P CLI | Provides invoice generation, scoring, learning, and reporting commands. | backend scripts and project entry points | PARTIAL
BUILT=54, PARTIAL=8, DESIGNED-ONLY=0, UNVERIFIED=0
