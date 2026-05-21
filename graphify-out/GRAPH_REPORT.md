# Graph Report - copilot-sdk  (2026-05-20)

## Corpus Check
- 449 files · ~233,535 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3259 nodes · 5406 edges · 111 communities detected
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 713 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 124|Community 124]]
- [[_COMMUNITY_Community 125|Community 125]]
- [[_COMMUNITY_Community 126|Community 126]]
- [[_COMMUNITY_Community 127|Community 127]]
- [[_COMMUNITY_Community 128|Community 128]]
- [[_COMMUNITY_Community 129|Community 129]]
- [[_COMMUNITY_Community 134|Community 134]]
- [[_COMMUNITY_Community 135|Community 135]]
- [[_COMMUNITY_Community 136|Community 136]]
- [[_COMMUNITY_Community 137|Community 137]]
- [[_COMMUNITY_Community 138|Community 138]]
- [[_COMMUNITY_Community 139|Community 139]]
- [[_COMMUNITY_Community 140|Community 140]]
- [[_COMMUNITY_Community 141|Community 141]]
- [[_COMMUNITY_Community 142|Community 142]]
- [[_COMMUNITY_Community 143|Community 143]]
- [[_COMMUNITY_Community 145|Community 145]]
- [[_COMMUNITY_Community 191|Community 191]]
- [[_COMMUNITY_Community 192|Community 192]]
- [[_COMMUNITY_Community 193|Community 193]]
- [[_COMMUNITY_Community 194|Community 194]]
- [[_COMMUNITY_Community 195|Community 195]]
- [[_COMMUNITY_Community 196|Community 196]]
- [[_COMMUNITY_Community 197|Community 197]]
- [[_COMMUNITY_Community 198|Community 198]]
- [[_COMMUNITY_Community 199|Community 199]]
- [[_COMMUNITY_Community 200|Community 200]]
- [[_COMMUNITY_Community 201|Community 201]]
- [[_COMMUNITY_Community 202|Community 202]]
- [[_COMMUNITY_Community 212|Community 212]]
- [[_COMMUNITY_Community 229|Community 229]]
- [[_COMMUNITY_Community 230|Community 230]]
- [[_COMMUNITY_Community 231|Community 231]]
- [[_COMMUNITY_Community 232|Community 232]]
- [[_COMMUNITY_Community 233|Community 233]]
- [[_COMMUNITY_Community 234|Community 234]]
- [[_COMMUNITY_Community 235|Community 235]]
- [[_COMMUNITY_Community 236|Community 236]]

## God Nodes (most connected - your core abstractions)
1. `DecisionStore` - 69 edges
2. `apiGet()` - 66 edges
3. `SQLiteGraphStore` - 57 edges
4. `CompoundingScorer` - 56 edges
5. `build_compounding_scorer()` - 45 edges
6. `DataOpsGraphClient` - 44 edges
7. `PromptVariantEvolver` - 44 edges
8. `expectAnyText()` - 42 edges
9. `AgentEvolver` - 40 edges
10. `sample_factors()` - 37 edges

## Surprising Connections (you probably didn't know these)
- `test_promotion_respects_conservation()` --calls--> `AutonomousPromotionGate`  [INFERRED]
  tests\evolution\test_integration.py → copilot_sdk\evolution\autonomous_promotion.py
- `plateau_config()` --calls--> `PlateauConfig`  [INFERRED]
  copilot_sdk\scoring\presets\dataops.py → copilot_sdk\evolution\evolver.py
- `plateau_config()` --calls--> `PlateauConfig`  [INFERRED]
  copilot_sdk\scoring\presets\purchasing.py → copilot_sdk\evolution\evolver.py
- `plateau_config()` --calls--> `PlateauConfig`  [INFERRED]
  copilot_sdk\scoring\presets\s2p.py → copilot_sdk\evolution\evolver.py
- `plateau_config()` --calls--> `PlateauConfig`  [INFERRED]
  copilot_sdk\scoring\presets\trading.py → copilot_sdk\evolution\evolver.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.02
Nodes (132): handleApply(), CelonisBadge(), if(), CrossGraphInsightCard(), currency(), computePositionSizing(), activityName(), isBottleneck() (+124 more)

### Community 1 - "Community 1"
Cohesion: 0.02
Nodes (94): test_action_bias_rule_deterministic_variant(), test_all_rules_handle_empty_context(), test_factor_weight_rule_works_with_dataops_action_count(), test_rules_require_at_least_two_actions(), ActionBiasRule, _bounded_index(), ConfidenceBoundaryRule, _factor_values() (+86 more)

### Community 2 - "Community 2"
Cohesion: 0.02
Nodes (65): loadProof(), ConservationMiniGauge(), duration(), ProcessContextCard(), flattenShadowResults(), formatPercent(), hasData(), numberValue() (+57 more)

### Community 3 - "Community 3"
Cohesion: 0.03
Nodes (76): AgentEvolver, PlateauConfig, _positive_improvement(), AgentEvolver orchestration primitives., InMemoryEvolutionLedger, Evolution event ledgers., Append-only event ledger with optional GraphStore persistence., EvolutionEvent (+68 more)

### Community 4 - "Community 4"
Cohesion: 0.03
Nodes (68): SQLite GraphStore adapter backed by DecisionStore., Open-call-close adapter over the existing SQLite DecisionStore., SQLiteGraphStore, test_in_memory_write_decision_preserves_metadata(), test_in_memory_write_decision_without_metadata_still_works(), test_sqlite_decision_metadata_persists_after_reopen(), test_sqlite_write_decision_preserves_metadata(), test_sqlite_write_decision_without_metadata_still_works() (+60 more)

### Community 5 - "Community 5"
Cohesion: 0.03
Nodes (82): _clean_category(), PromptEvolverConfig, PromptVariantEvolver, Prompt variant evolution foundation., Deterministic prompt variant foundation., _VariantStatsLike, _evolver(), _record() (+74 more)

### Community 6 - "Community 6"
Cohesion: 0.04
Nodes (112): accuracy_by_category(), _accuracy_for_decisions(), _alert_category_by_id(), alert_deps(), alert_detail(), alert_factors(), alert_groups(), _alert_level_for_accuracy() (+104 more)

### Community 7 - "Community 7"
Cohesion: 0.02
Nodes (20): _learn(), _parse_utc(), _score(), test_ae_fixtures_cached(), test_ae_fixtures_resettable(), test_alert_detail_has_runtime_sla_fields(), test_alert_groups_include_runtime_sla_fields(), test_alerts_have_timestamps() (+12 more)

### Community 8 - "Community 8"
Cohesion: 0.03
Nodes (42): Trading Copilot backend app., _cors_origins(), create_app(), _filter_variants_by_query(), _FixtureEvolutionLedger, _graph_store(), _ledger_provider(), FastAPI entrypoint for the Trading Copilot backend. (+34 more)

### Community 9 - "Community 9"
Cohesion: 0.04
Nodes (63): CelonisConnector, _list_from_payload(), Celonis connector with deterministic cache fallback for DataOps demos., _parse_odata_results(), SAP connector with deterministic cache fallback for DataOps demos., SAPConnector, create_narrative_provider(), get_narrative_provider() (+55 more)

### Community 10 - "Community 10"
Cohesion: 0.04
Nodes (56): cosine_similarity(), get_theta(), SimilarCaseFinder ABC for CopilotFramework. Domain implementations supply SOC/S2, Return up to k similar past Decision nodes for *category*.          Category fil, Return fraction of *similar_cases* whose action matches *current_action*., Case-based reasoning retrieval — domain subclass supplies get_theta()., Fetch up to *limit* verified Decision nodes for *category* from Neo4j,         m, SimilarCasesBase (+48 more)

### Community 11 - "Community 11"
Cohesion: 0.05
Nodes (47): create_discovery_router(), FastAPI discovery router factory., Create advisory discovery endpoints for a DiscoveryEngine., _bounded_confidence(), DiscoveryAlert, Advisory discovery alert primitives., Advisory-only cross-system discovery alert., DiscoveryEngine (+39 more)

### Community 12 - "Community 12"
Cohesion: 0.05
Nodes (20): gotoCurve(), gotoEvidence(), openFirstAlert(), gotoInsight(), openFirstTriage(), openKnownSystemTriage(), clickTab(), collectConsoleErrors() (+12 more)

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (55): BinaryRewardFunction, Return +1 for matching actions and -1 otherwise., build_compounding_scorer(), _other_action(), RecordingCreditAssigner, RecordingExplorer, RecordingRewardFunction, sample_factors() (+47 more)

### Community 14 - "Community 14"
Cohesion: 0.07
Nodes (28): _alert_factor(), _build_tree_from_edges(), _ci_platform_path(), DataOpsGraphClient, _flatten_tree_names(), _load_age_client_class(), _load_json(), DataOps graph query layer with deterministic fixture fallback. (+20 more)

### Community 15 - "Community 15"
Cohesion: 0.05
Nodes (55): check_health(), check_port(), cmd_kill_all(), cmd_start(), cmd_status(), cmd_stop(), ensure_age_available(), find_pids_on_port() (+47 more)

### Community 16 - "Community 16"
Cohesion: 0.07
Nodes (38): bootstrap_centroids(), DataOpsPreset, _load_bootstrap(), plateau_config(), DataOps domain preset., shape(), compute_fingerprint(), FactorFingerprint (+30 more)

### Community 17 - "Community 17"
Cohesion: 0.09
Nodes (41): create_self_computation_router(), mount_self_computation_router(), Self-computation endpoints backed directly by GraphStore., Mount GraphStore-backed self-computation endpoints on a FastAPI app., Mount GraphStore-backed self-computation endpoints on a FastAPI app., Create GraphStore-backed self-computation endpoints for one app instance., _client(), _seed_store() (+33 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (37): _factors(), _score_and_learn(), _scorer(), test_dataops_actions_wired_correctly(), test_evolution_triggers_after_twenty_learns(), test_evolve_false_creates_no_active_evolver(), test_evolve_true_creates_evolver(), test_evolve_true_registers_three_rules() (+29 more)

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (32): _base_score(), _category_bonus(), ContextAwareSelector, _evidence_count(), Optional context-aware variant selection helpers., Score candidate variants without mutating current evolution behavior., SelectionContext, Step-level credit attribution for multi-step evolution chains. (+24 more)

### Community 20 - "Community 20"
Cohesion: 0.08
Nodes (31): build_transfer_registry(), main(), Run a local warm-start transfer demo.  Usage:     python scripts/demo_warm_start, run_demo(), main(), Run a local cross-copilot warm-start demo., test_warm_start_checkpoint_has_null_decision_range(), from_dict() (+23 more)

### Community 21 - "Community 21"
Cohesion: 0.08
Nodes (29): create_scoring_router(), Create a domain-parametric scoring router., build_client(), FakeFingerprintFactor, FakeFingerprintResult, FakeLearnResult, FakeScorer, FakeScoreResult (+21 more)

### Community 22 - "Community 22"
Cohesion: 0.07
Nodes (33): bootstrap_centroids(), _load_bootstrap(), plateau_config(), PurchasingPreset, Purchasing domain preset., shape(), build_verified_decisions(), correct_rate() (+25 more)

### Community 23 - "Community 23"
Cohesion: 0.09
Nodes (26): _add_edge(), _add_node(), _dataset_id(), _load_json(), _node_id(), Deterministic Trading graph seed plan., seed_dataops_graph(), seed_purchasing_graph() (+18 more)

### Community 24 - "Community 24"
Cohesion: 0.05
Nodes (27): compute_iks(), interpret(), interpret_iks_v2(), _mean_centroid_drift(), IKS (Institutional Knowledge Score) algorithm for CopilotFramework. compute_iks(, Return a human-readable interpretation of the IKS (v1) score., Return a human-readable interpretation of the IKS v2 composite score., Compute mean ‖μ(t)[c,a,:] − μ₀[c,a,:]‖₂ over all (c, a) pairs.      Parameters (+19 more)

### Community 25 - "Community 25"
Cohesion: 0.08
Nodes (28): _clamp(), _clamp(), GradedFinancialRewardFunction, _number(), PnLRewardFunction, Built-in reward functions for common copilot feedback patterns., Reward recovered value, or penalize slow overrides., Scale basis-point P&L into the reward interval. (+20 more)

### Community 26 - "Community 26"
Cohesion: 0.08
Nodes (28): _check_payload(), ConservationWhatIfRequest, create_conservation_router(), _default_counts(), _finite_or_none(), _positive_float(), FastAPI conservation router factory backed by GAE calibration., Create a domain-parametric conservation router. (+20 more)

### Community 27 - "Community 27"
Cohesion: 0.07
Nodes (32): _entry_to_dict(), get_decision_rows(), get_decisions(), _outcome_to_dict(), SOC Audit Service — thin adapter over ci_platform Evidence Ledger.  Hash-chain i, Append a sealed LedgerEntry to the ci_platform ledger and return it as a SOC dic, Append a sealed LedgerEntry to the ci_platform ledger and return it as a SOC dic, Find the most-recent LedgerEntry for alert_id and update its outcome.      Mutat (+24 more)

### Community 28 - "Community 28"
Cohesion: 0.07
Nodes (17): CheckpointService, CheckpointService — centroid checkpoint and rollback (TD-033, Phase 4 §17.5).  C, Centroid checkpoint and rollback (TD-033)., Centroid checkpoint and rollback (TD-033)., InterventionControls, InterventionControls — P22 Consolidated Oversight Panel (L-12).  EU AI Act Artic, Restore centroid snapshot.          Parameters         ----------         previe, Force all decisions to human review (disabled=True) or restore. (+9 more)

### Community 29 - "Community 29"
Cohesion: 0.08
Nodes (11): InMemoryGraphStore, _matches_checkpoint_filters(), In-memory GraphStore implementation for tests and demos., Dictionary-backed decision and outcome store., Dictionary-backed decision and outcome store., _utc_iso_now(), InMemoryGraphStore, DemoGraphStore (+3 more)

### Community 30 - "Community 30"
Cohesion: 0.09
Nodes (15): Public graph persistence protocol for copilot decisions., Deprecated optional capability for stores that persist decision-entity links., Link a decision to a domain entity such as an invoice., SupportsDecisionEntityLinks, MinimalOldStore, _sqlite_events(), test_graphstore_protocol_remains_narrow_for_old_shape_stores(), test_inmemory_decision_id_prefix_applied() (+7 more)

### Community 31 - "Community 31"
Cohesion: 0.09
Nodes (13): _learn(), _load_data(), _save_proxy_decision(), _score(), _seed_verified_history(), test_analytics_consistent_with_seed_v2(), test_conservation_status_returns_live_counts(), test_fingerprint() (+5 more)

### Community 32 - "Community 32"
Cohesion: 0.13
Nodes (31): NamedTuple, actual_action(), alternate_action(), api_get(), _api_json(), api_post(), ApiError, check_already_seeded() (+23 more)

### Community 33 - "Community 33"
Cohesion: 0.16
Nodes (26): conservation_history(), _factor(), _generate_lifecycle_events(), _get_fixtures(), _graph_client(), impact(), incident(), _load_json() (+18 more)

### Community 34 - "Community 34"
Cohesion: 0.13
Nodes (9): _build_scorer(), LinkPreset, MinimalGraphStore, _score(), test_learn_with_context_invoice_creates_link(), test_learn_with_context_tolerates_graphstore_without_link_method(), test_learn_without_entity_unchanged(), test_link_decision_to_entity_sqlite() (+1 more)

### Community 35 - "Community 35"
Cohesion: 0.16
Nodes (19): AutonomousPromotionGate, _evaluate_base_gate(), PromotionDecision, Opt-in autonomous promotion checks layered over shadow promotion data., GREEN-only autonomous gate for opt-in promotion workflows., _regressions(), _win_rate(), _batches() (+11 more)

### Community 36 - "Community 36"
Cohesion: 0.13
Nodes (15): _argmax(), _beta_sample(), ConservationBoundedThompson, Conservation-bounded exploration policies., Thompson sampler that disables exploration outside GREEN conservation., test_amber_returns_best_action(), test_deterministic_when_confidence_max_one(), test_empty_probabilities_raise() (+7 more)

### Community 37 - "Community 37"
Cohesion: 0.19
Nodes (17): EdgeType, GraphContract, NodeType, Domain graph contract dataclasses., _clean_contract(), test_edge_type_fields(), test_empty_contract_invalid(), test_graph_contract_counts() (+9 more)

### Community 38 - "Community 38"
Cohesion: 0.15
Nodes (17): create_transfer_router(), _find_warm_start_info(), _latest_checkpoint_info(), _normalize_transfer_status(), _patterns_transferred(), Transfer status router for copilot applications., _source_copilot(), _string_or_none() (+9 more)

### Community 40 - "Community 40"
Cohesion: 0.1
Nodes (12): tests/test_discipline.py — SDK boundary discipline tests.  Enforces:  - No domai, FactorComputer defines compute(event) -> float as required by GAE., SourceConnector has fetch/validate; ReferralRule has evaluate., Top-level `import copilot_sdk` completes without error and is versioned., Importing copilot_sdk must not trigger torch, tensorflow,         transformers,, No domains.soc module appears in sys.modules after importing copilot_sdk., No domains.s2p module appears in sys.modules after importing copilot_sdk., AST scan of all .py files under copilot_sdk/ for forbidden import patterns. (+4 more)

### Community 41 - "Community 41"
Cohesion: 0.2
Nodes (18): Apply shared transfer patterns to the active GAE centroid tensor., Apply shared transfer patterns to the active GAE centroid tensor., _pattern(), test_blend_weight_scales_delta(), test_empty_patterns_returns_copy_and_zero_score(), test_input_centroids_are_not_mutated(), test_multiple_patterns_accumulate(), test_score_is_bounded() (+10 more)

### Community 42 - "Community 42"
Cohesion: 0.26
Nodes (16): Get-Health(), Get-PortProcessIds(), Get-SelectedCopilots(), Show-Status(), Start-Backend(), Start-Builds(), Start-Frontend(), Start-GraphMode() (+8 more)

### Community 43 - "Community 43"
Cohesion: 0.24
Nodes (13): DefaultPromotionGate, Default promotion gate for shadow results., _shadow(), test_gate_amber_conservation_passes(), test_gate_custom_thresholds(), test_gate_promotes_when_checks_pass(), test_gate_red_conservation_blocks(), test_gate_rejects_below_accuracy_floor() (+5 more)

### Community 44 - "Community 44"
Cohesion: 0.15
Nodes (7): SampleGate, SampleLedger, SampleRule, SampleShadow, test_evolution_event_defaults_metadata_and_timestamp(), test_evolution_event_validates_type(), test_protocols_are_runtime_checkable()

### Community 45 - "Community 45"
Cohesion: 0.15
Nodes (8): build_provenance(), DecisionProvenance, FactorProvenance, get_provenance_from_graph(), ProvenanceService, ProvenanceService — factor provenance and decision audit trail (Phase 6).  Provi, Builds factor provenance records for a decision., Builds factor provenance records for a decision.

### Community 46 - "Community 46"
Cohesion: 0.15
Nodes (9): DecisionResult, SOC Copilot Agent - Simple Rule-Based Decision Engine ~150 lines total. The demo, Agent decision output, Calculate faithfulness score: Does reasoning match decision and context?, Evaluate 4 deterministic eval gates.         All are deterministic checks - no L, Simple rule-based SOC decision engine.     No LLM orchestration - just determini, Determine if this decision should trigger an evolution event.          Returns:, Main decision function. Rule-based logic.          Args:             alert_type: (+1 more)

### Community 47 - "Community 47"
Cohesion: 0.13
Nodes (11): DecisionMade, EventBus, GraphMutated, OutcomeVerified, Lightweight event bus for SOC Copilot (v4.1 — replaced by ci-platform at v4.5)., Emitted after a Decision node is written to the graph.     Channel A: Decision n, Emitted after a Decision node is marked correct/incorrect.     Channel B: Outcom, Emitted for every graph write (decision or outcome).     Provides a single audit (+3 more)

### Community 48 - "Community 48"
Cohesion: 0.2
Nodes (11): CreditAssigner, Credit assignment helpers for optional RL feedback., Distribute temporally discounted reward across contributing factors., test_credit_sums_to_base(), test_dominant_contribution(), test_empty_factors_returns_empty_dict(), test_negative_reward(), test_temporal_discount() (+3 more)

### Community 49 - "Community 49"
Cohesion: 0.24
Nodes (13): _py_files(), Drift detector: framework files in copilot-sdk vs SOC (canonical source), and S2, SDK framework must be a subset of SOC — no files in SDK that don't exist in SOC., S2P framework files must be byte-identical to SOC unless listed in S2P_KNOWN_DRI, Every S2P_KNOWN_DRIFT entry must actually exist and actually differ; stale entri, Files present in both repos must be byte-identical unless listed in KNOWN_DRIFT., Every KNOWN_DRIFT entry must actually exist and actually differ; stale entries f, _read() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.29
Nodes (10): _contracts(), _load_module(), _seeds(), test_all_contract_names_unique(), test_all_contracts_have_decision_and_decided_on(), test_all_contracts_validate(), test_all_seed_edges_reference_seeded_node_ids(), test_all_seed_outputs_cover_contract_labels() (+2 more)

### Community 51 - "Community 51"
Cohesion: 0.27
Nodes (7): asRecord(), buildCurve(), exactCurve(), money(), num(), pct(), stats()

### Community 52 - "Community 52"
Cohesion: 0.2
Nodes (6): CompositeDiscriminant, CompositeDiscriminant — multi-signal auto-approve gate (Phase 5).  Uses 13 featu, Multi-signal auto-approve gate.      Uses scorer output features + graph context, DecisionHistoryService, DecisionHistoryService — per-category decision counts and rolling accuracy.  Pro, Tracks per-category decision counts and rolling accuracy.

### Community 53 - "Community 53"
Cohesion: 0.2
Nodes (9): get_all_trust_scores(), get_reward_summary(), get_trust_status(), Feedback trust/reward mechanics for CopilotFramework. Domain-agnostic — no SOC r, Return all current trust scores and the full update history.      Returns     --, Aggregate current in-memory feedback state into an RL reward summary.      Rewar, Update trust score for a situation type after a decision outcome.      Asymmetri, Get trust status for a single situation type.      Returns     -------     { (+1 more)

### Community 54 - "Community 54"
Cohesion: 0.2
Nodes (9): load_from_file(), make_state(), LearningState singleton for CopilotFramework. Domain layer (SOC/S2P) builds the, Read the metadata field from the checkpoint. Returns {} if absent., Atomically persist W matrix + WeightUpdate history to a JSON checkpoint.      Us, Create a fresh LearningState from raw parameters., Deserialize W matrix and WeightUpdate history from a JSON checkpoint.      Param, read_checkpoint_metadata() (+1 more)

### Community 55 - "Community 55"
Cohesion: 0.64
Nodes (8): _args(), _load_preseed_module(), _source_seed(), test_preseed_creates_200_decisions(), test_preseed_has_overrides(), test_preseed_idempotent(), test_preseed_nearly_complete_count_tops_up_one(), test_preseed_partial_count_tops_up_only_remaining()

### Community 56 - "Community 56"
Cohesion: 0.43
Nodes (7): _python_sources(), Guards for Pydantic v2-compatible SDK source., _source_hits(), test_sdk_source_has_no_inner_config_classes(), test_sdk_source_has_no_pydantic_v1_dict_serialization(), test_sdk_source_has_no_pydantic_v1_schema_introspection(), test_sdk_source_has_no_pydantic_v1_validator_api()

### Community 57 - "Community 57"
Cohesion: 0.29
Nodes (1): pct()

### Community 58 - "Community 58"
Cohesion: 0.29
Nodes (3): ShadowModeService — Phase 4 shadow mode (§21).  Shadow mode: system makes decisi, Shadow mode: system makes decisions but does not act on them.     Analyst action, ShadowModeService

### Community 59 - "Community 59"
Cohesion: 0.4
Nodes (2): isApprovedVariant(), isRejectedVariant()

### Community 60 - "Community 60"
Cohesion: 0.33
Nodes (1): client()

### Community 61 - "Community 61"
Cohesion: 0.33
Nodes (5): decisions_to_days(), predict_n_half(), Domain-agnostic convergence math for CopilotFramework.  CLAIM-CONV-01 (V-MV-CONV, Predict N_half (decisions to 50% convergence) from deployment params.     CLAIM-, Convert decision count to calendar days.     V IS used here — volume determines

### Community 62 - "Community 62"
Cohesion: 0.33
Nodes (3): FrozenROICalculator, Compute frozen-mode annual ROI.          Returns dict with:           time_saved, ROI for frozen scorer mode (LEARNING_ENABLED=False).      Three value drivers, a

### Community 63 - "Community 63"
Cohesion: 0.5
Nodes (2): asMetric(), RiskManagementCard()

### Community 65 - "Community 65"
Cohesion: 0.5
Nodes (1): Trading graph contract.

### Community 67 - "Community 67"
Cohesion: 0.67
Nodes (2): dayMetric(), OrderContext()

### Community 68 - "Community 68"
Cohesion: 0.67
Nodes (2): isApprovedVariant(), variantMatches()

### Community 70 - "Community 70"
Cohesion: 0.5
Nodes (3): get_ols_status(), ols_status.py — OLS (Override Lift Score) Dashboard service (L-09).  Uses GAE 0., Compute OLS dashboard status for the frontend.      Parameters     ----------

### Community 73 - "Community 73"
Cohesion: 0.5
Nodes (3): fix_file(), fix_playwright_failures.py — Fix 8 E2E test assertion issues.  Run from copilot-, Replace exact string in file. Report success or failure.

### Community 75 - "Community 75"
Cohesion: 0.67
Nodes (2): _load_demo_module(), test_warm_start_transfers_patterns()

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (2): ProfileArchetype(), topFactor()

### Community 88 - "Community 88"
Cohesion: 1.0
Nodes (2): formatPct(), Instrument()

### Community 90 - "Community 90"
Cohesion: 1.0
Nodes (2): buildSeries(), PriceSparkline()

### Community 94 - "Community 94"
Cohesion: 0.67
Nodes (1): Add create_conservation_router to Trading and Purchasing backends. Pattern copie

### Community 124 - "Community 124"
Cohesion: 1.0
Nodes (1): copilot-sdk — Build compounding intelligence copilots.  The engine is open. The

### Community 125 - "Community 125"
Cohesion: 1.0
Nodes (1): Backend router factories for copilot applications.

### Community 126 - "Community 126"
Cohesion: 1.0
Nodes (1): Cross-system advisory discovery infrastructure.

### Community 127 - "Community 127"
Cohesion: 1.0
Nodes (1): Domain-neutral agent evolution primitives.

### Community 128 - "Community 128"
Cohesion: 1.0
Nodes (1): Domain-agnostic feedback state store for CopilotFramework.  FEEDBACK_GIVEN is ex

### Community 129 - "Community 129"
Cohesion: 1.0
Nodes (1): CopilotFramework — domain-agnostic copilot infrastructure.  This package is desi

### Community 134 - "Community 134"
Cohesion: 1.0
Nodes (1): Deterministic config generators for SDK copilots.

### Community 135 - "Community 135"
Cohesion: 1.0
Nodes (1): GraphStore abstractions for SDK decision and outcome persistence.

### Community 136 - "Community 136"
Cohesion: 1.0
Nodes (1): Optional reinforcement-learning primitives for SDK copilots.

### Community 137 - "Community 137"
Cohesion: 1.0
Nodes (1): CompoundingScorer core package.

### Community 138 - "Community 138"
Cohesion: 1.0
Nodes (1): Preset registry for future domain-specific adapters.

### Community 139 - "Community 139"
Cohesion: 1.0
Nodes (1): Verification helpers.

### Community 140 - "Community 140"
Cohesion: 1.0
Nodes (1): Cross-copilot transfer primitives.

### Community 141 - "Community 141"
Cohesion: 1.0
Nodes (1): Diagnose and fix Trading conservation endpoint. Run from copilot-sdk root.

### Community 142 - "Community 142"
Cohesion: 1.0
Nodes (1): Fix copilot-fixture.ts health check to retry 3 times with 2s backoff.  Run from

### Community 143 - "Community 143"
Cohesion: 1.0
Nodes (1): Fix strict mode violations in Playwright E2E tests.

### Community 145 - "Community 145"
Cohesion: 1.0
Nodes (1): Hello World demo — score + IKS in 30 lines. Run: python examples/hello_world/dem

### Community 191 - "Community 191"
Cohesion: 1.0
Nodes (1): Snapshot current centroids to a Checkpoint node in Neo4j.          Parameters

### Community 192 - "Community 192"
Cohesion: 1.0
Nodes (1): Return all Checkpoint nodes ordered by timestamp DESC.

### Community 193 - "Community 193"
Cohesion: 1.0
Nodes (1): Restore centroids from a Checkpoint node and freeze the scorer.          Paramet

### Community 194 - "Community 194"
Cohesion: 1.0
Nodes (1): Evaluate whether a decision should be auto-approved.          Parameters

### Community 195 - "Community 195"
Cohesion: 1.0
Nodes (1): Get decision count and rolling accuracy for a category.          Uses the last 1

### Community 196 - "Community 196"
Cohesion: 1.0
Nodes (1): Build provenance for a decision.          Parameters         ----------

### Community 197 - "Community 197"
Cohesion: 1.0
Nodes (1): Retrieve a stored decision's factor vector from Neo4j and rebuild provenance.

### Community 198 - "Community 198"
Cohesion: 1.0
Nodes (1): Mark a Decision node as shadow_mode=True.

### Community 199 - "Community 199"
Cohesion: 1.0
Nodes (1): Record what the analyst actually did (the ground truth).         Also sets d.agr

### Community 200 - "Community 200"
Cohesion: 1.0
Nodes (1): Generate shadow mode report: agreement rates by category.          Returns

### Community 201 - "Community 201"
Cohesion: 1.0
Nodes (1): Return cosine similarity in [0, 1].  Returns 0.0 for zero vectors.

### Community 202 - "Community 202"
Cohesion: 1.0
Nodes (1): Return per-category cosine similarity threshold for retrieval.

### Community 212 - "Community 212"
Cohesion: 1.0
Nodes (1): The GraphStore single source of truth.

### Community 229 - "Community 229"
Cohesion: 1.0
Nodes (1): The GraphStore single source of truth.

### Community 230 - "Community 230"
Cohesion: 1.0
Nodes (1): The GraphStore single source of truth.

### Community 231 - "Community 231"
Cohesion: 1.0
Nodes (1): The GraphStore single source of truth.

### Community 232 - "Community 232"
Cohesion: 1.0
Nodes (1): Snapshot current centroids to a Checkpoint node in Neo4j.          Parameters

### Community 233 - "Community 233"
Cohesion: 1.0
Nodes (1): Return all Checkpoint nodes ordered by timestamp DESC.

### Community 234 - "Community 234"
Cohesion: 1.0
Nodes (1): Restore centroids from a Checkpoint node and freeze the scorer.          Paramet

### Community 235 - "Community 235"
Cohesion: 1.0
Nodes (1): Build provenance for a decision.          Parameters         ----------

### Community 236 - "Community 236"
Cohesion: 1.0
Nodes (1): Retrieve a stored decision's factor vector from Neo4j and rebuild provenance.

## Knowledge Gaps
- **306 isolated node(s):** `Check if a port is responding.`, `Check backend health endpoint.`, `Verify AGE/PostgreSQL is reachable.`, `Check if any WSL2 distribution is running.`, `Start PostgreSQL inside WSL2 and keep WSL2 alive.` (+301 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 57`** (7 nodes): `CounterfactualCard.tsx`, `CounterfactualCard.tsx`, `asRecord()`, `CounterfactualCard()`, `money()`, `num()`, `pct()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (6 nodes): `AEStatusBar.tsx`, `AEStatusBar()`, `isApprovedVariant()`, `isRejectedVariant()`, `money()`, `pct()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (6 nodes): `conftest.py`, `conftest.py`, `conftest.py`, `client()`, `dataops_data_dir()`, `temp_data_dir()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (5 nodes): `RiskManagementCard.tsx`, `asMetric()`, `money()`, `pct()`, `RiskManagementCard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (4 nodes): `Trading graph contract.`, `graph_contract.py`, `graph_contract.py`, `graph_contract.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (4 nodes): `OrderContext.tsx`, `dayMetric()`, `OrderContext()`, `pct()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (4 nodes): `ParLevelMonitor.tsx`, `isApprovedVariant()`, `itemRatio()`, `variantMatches()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 75`** (4 nodes): `_load_demo_module()`, `test_warm_start_demo.py`, `test_warm_start_demo_script_runs()`, `test_warm_start_transfers_patterns()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 83`** (3 nodes): `ProfileArchetype.tsx`, `ProfileArchetype()`, `topFactor()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 88`** (3 nodes): `MarketContext.tsx`, `formatPct()`, `Instrument()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 90`** (3 nodes): `PriceSparkline.tsx`, `buildSeries()`, `PriceSparkline()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 94`** (3 nodes): `fix_main()`, `fix_conservation_router.py`, `Add create_conservation_router to Trading and Purchasing backends. Pattern copie`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 124`** (2 nodes): `__init__.py`, `copilot-sdk — Build compounding intelligence copilots.  The engine is open. The`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 125`** (2 nodes): `Backend router factories for copilot applications.`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 126`** (2 nodes): `__init__.py`, `Cross-system advisory discovery infrastructure.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 127`** (2 nodes): `__init__.py`, `Domain-neutral agent evolution primitives.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 128`** (2 nodes): `feedback_store.py`, `Domain-agnostic feedback state store for CopilotFramework.  FEEDBACK_GIVEN is ex`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 129`** (2 nodes): `__init__.py`, `CopilotFramework — domain-agnostic copilot infrastructure.  This package is desi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 134`** (2 nodes): `__init__.py`, `Deterministic config generators for SDK copilots.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 135`** (2 nodes): `__init__.py`, `GraphStore abstractions for SDK decision and outcome persistence.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 136`** (2 nodes): `__init__.py`, `Optional reinforcement-learning primitives for SDK copilots.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 137`** (2 nodes): `__init__.py`, `CompoundingScorer core package.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 138`** (2 nodes): `__init__.py`, `Preset registry for future domain-specific adapters.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 139`** (2 nodes): `__init__.py`, `Verification helpers.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 140`** (2 nodes): `__init__.py`, `Cross-copilot transfer primitives.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 141`** (2 nodes): `diagnose_trading_conservation.py`, `Diagnose and fix Trading conservation endpoint. Run from copilot-sdk root.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 142`** (2 nodes): `fix_health_retry.py`, `Fix copilot-fixture.ts health check to retry 3 times with 2s backoff.  Run from`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 143`** (2 nodes): `fix_strict_mode.py`, `Fix strict mode violations in Playwright E2E tests.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 145`** (2 nodes): `demo.py`, `Hello World demo — score + IKS in 30 lines. Run: python examples/hello_world/dem`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 191`** (1 nodes): `Snapshot current centroids to a Checkpoint node in Neo4j.          Parameters`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 192`** (1 nodes): `Return all Checkpoint nodes ordered by timestamp DESC.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 193`** (1 nodes): `Restore centroids from a Checkpoint node and freeze the scorer.          Paramet`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 194`** (1 nodes): `Evaluate whether a decision should be auto-approved.          Parameters`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 195`** (1 nodes): `Get decision count and rolling accuracy for a category.          Uses the last 1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 196`** (1 nodes): `Build provenance for a decision.          Parameters         ----------`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 197`** (1 nodes): `Retrieve a stored decision's factor vector from Neo4j and rebuild provenance.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 198`** (1 nodes): `Mark a Decision node as shadow_mode=True.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 199`** (1 nodes): `Record what the analyst actually did (the ground truth).         Also sets d.agr`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 200`** (1 nodes): `Generate shadow mode report: agreement rates by category.          Returns`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 201`** (1 nodes): `Return cosine similarity in [0, 1].  Returns 0.0 for zero vectors.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 202`** (1 nodes): `Return per-category cosine similarity threshold for retrieval.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 212`** (1 nodes): `The GraphStore single source of truth.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 229`** (1 nodes): `The GraphStore single source of truth.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 230`** (1 nodes): `The GraphStore single source of truth.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 231`** (1 nodes): `The GraphStore single source of truth.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 232`** (1 nodes): `Snapshot current centroids to a Checkpoint node in Neo4j.          Parameters`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 233`** (1 nodes): `Return all Checkpoint nodes ordered by timestamp DESC.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 234`** (1 nodes): `Restore centroids from a Checkpoint node and freeze the scorer.          Paramet`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 235`** (1 nodes): `Build provenance for a decision.          Parameters         ----------`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 236`** (1 nodes): `Retrieve a stored decision's factor vector from Neo4j and rebuild provenance.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SourceConnector` connect `Community 0` to `Community 3`?**
  _High betweenness centrality (0.174) - this node is a cross-community bridge._
- **Why does `CompoundingScorer` connect `Community 1` to `Community 34`, `Community 4`, `Community 41`, `Community 10`, `Community 13`, `Community 16`, `Community 17`, `Community 20`, `Community 29`?**
  _High betweenness centrality (0.167) - this node is a cross-community bridge._
- **Why does `SQLiteGraphStore` connect `Community 4` to `Community 8`, `Community 1`, `Community 34`, `Community 30`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `DecisionStore` (e.g. with `SQLiteGraphStore` and `ScoreResult`) actually correct?**
  _`DecisionStore` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 38 inferred relationships involving `SQLiteGraphStore` (e.g. with `DecisionStore` and `ScoreResult`) actually correct?**
  _`SQLiteGraphStore` has 38 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `CompoundingScorer` (e.g. with `DomainPreset` and `JudgmentConflict`) actually correct?**
  _`CompoundingScorer` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Check if a port is responding.`, `Check backend health endpoint.`, `Verify AGE/PostgreSQL is reachable.` to the rest of the system?**
  _306 weakly-connected nodes found - possible documentation gaps or missing edges._