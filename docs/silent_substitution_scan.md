# Silent Substitution Scan — 2026-09-23

## Summary

- Files scanned: **907 production Python files** (909 inventoried; two SDK testing-support files excluded).
- Functions with graph calls: **737 direct named-call functions** after excluding 12 test/non-graph matches from 749 candidates.
- Additional helper/alias candidates read end to end: **523**; total candidate bodies reviewed: **1,272**. Supplemental candidates include confirmed graph wrappers and rejected non-graph matches; they are not all counted as graph-call functions.
- P1 findings: **150**.
- P2 findings: **53**.
- P3 findings: **17**.
- Legitimate patterns: **194**.
- Findings cover **215 distinct functions**. Counts above are table rows, grouping equivalent handler paths in a function; a function can have both a finding and a legitimate handler.

### Scope and method

The five requested scope groups resolve to seven Python roots in four repository directories (the SDK app group contains DataOps, Purchasing, and Trading). Production demo/migration helpers are included where they live in those roots. Tests, SDK testing support, caches, and third-party dependencies are excluded.

AST enumeration located named calls and exception ownership, including nested functions. Each candidate's executable body was read end to end, then helper calls, dynamically retrieved methods, caller return handling, and selected dispatch mappings were traced. Findings are semantic control-flow observations, not search matches. No application imports, tests, graph queries, fault injection, or git operations were performed. Only this requested report and the requested session-state entry were written.

“Silent” includes logging without a returned error signal. The distinction is what the immediate consumer can learn from the returned value, not whether an operator might find a log. P1 includes ordinary defaults and misleading fallback classifications, not only literal empty lists. P2 identifies unreported write/learning failures; it does not establish that data loss has occurred in a running deployment. P3 tracks narrow compatibility/data-shape catches; transport errors outside those handlers still propagate. Narrow catches that erase availability information are explicitly noted rather than declared harmless.

An outer re-raise does not repair an inner swallowed exception. Consequently, the same function may appear in both findings and legitimate patterns. Explicit unavailable/error results, reported deferred writes, and retries that ultimately raise are distinguished from ordinary empty-data results. Source line references are relative to the workspace root. Dynamic plugin/callback reachability cannot be proven exhaustively by static inspection; dormant/private APIs are identified where no production callsite was found.

| Production root | Files scanned | Direct named-call functions |
|---|---:|---:|
| `copilot-sdk/copilot_sdk/` | 294 | 154 |
| `ci-platform/ci_platform/` | 37 | 118 |
| `s2p-copilot/backend/app/` | 135 | 143 |
| `gen-ai-roi-demo-v4-v50/backend/app/` | 204 | 213 |
| `copilot-sdk/apps/dataops/backend/app/` | 41 | 34 |
| `copilot-sdk/apps/purchasing/backend/app/` | 82 | 34 |
| `copilot-sdk/apps/trading/backend/app/` | 114 | 41 |

## P1 Findings (must fix)

| File:line | Function | Caught | Returns | Caller impact |
|---|---|---|---|---|
| `ci-platform/ci_platform/graph/age_client.py:677` | `AGEClient.get_sequence_count` | Exception | 0 | Sequence read outage looks like no related decisions. |
| `ci-platform/ci_platform/graph/age_client.py:704` | `AGEClient.get_cross_category_count` | Exception | 0 | Cross-category read outage looks like no categories. |
| `ci-platform/ci_platform/graph/age_client.py:730` | `AGEClient._legacy_sequence_count` | Exception | 0 | Legacy sequence graph errors indistinguishable from no history. No production callsite found in scoped Python code; latent helper-contract defect, not a demonstrated endpoint outage. |
| `ci-platform/ci_platform/graph/age_client.py:756` | `AGEClient._legacy_cross_category_count` | Exception | 0 | Legacy category graph errors indistinguishable from no history. No production callsite found in scoped Python code; latent helper-contract defect, not a demonstrated endpoint outage. |
| `ci-platform/ci_platform/graph/age_graph_store.py:745` | `AGEGraphStore._run_query` | Exception | [] for type(exc).__name__ == PoolClosed | get_decision returns None and count methods zero on a closed pool; other exceptions propagate. Caller evidence: `ci-platform/ci_platform/graph/age_graph_store.py:141 _save_platform_state -> self._run_query`. |
| `ci-platform/ci_platform/strategy/two_phase_strategy.py:31` | `TwoPhaseStrategy.get_phase` | Exception | phase A | _counts queries GraphStore verified/correct counts; graph failure is identical to the ordinary immature/low-quality rollout phase (same file:58). get_status separately preserves an error field. |
| `copilot-sdk/apps/dataops/backend/app/ae_router.py:52` | `_events` | Exception | [] | AE event inventory returns no events when graph evolution reads fail. Caller evidence: `copilot-sdk/apps/dataops/backend/app/ae_router.py:78 _variants -> _events`. |
| `copilot-sdk/apps/dataops/backend/app/routers/dataops_status.py:109` | `_enterprise_graph_health` | Exception | connected=False; node_count=0 | Health helper cannot distinguish a failed pipeline-count query from an empty graph (both disconnected). Caller evidence: `copilot-sdk/apps/dataops/backend/app/routers/dataops_status.py:76 enterprise_health_alias -> _enterprise_graph_health`. |
| `copilot-sdk/apps/dataops/backend/app/services/cohort_status.py:149` | `DataOpsCohortStatus._read_decisions` | Exception | [] after trying alternate methods | DataOps cohort evaluation gets an empty ledger when all graph accessors fail. Caller evidence: `copilot-sdk/apps/dataops/backend/app/services/cohort_status.py:132 _records_with_provenance -> self._read_decisions`. |
| `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:352` | `_pipelines` | Exception | fixture pipeline mapping | Failed topology read falls through to fallback/pipelines.json without an outage indicator. Caller evidence: `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:136 execute -> _pipelines`. |
| `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:365` | `_blast_radius` | Exception | fixture blast-radius tree | Failed graph read falls through to fallback/blast_radius.json without an outage indicator. Caller evidence: `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:254 execute -> _blast_radius`. |
| `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:378` | `_recurrence` | Exception | fixture recurrence payload | Both missing graph capability/data and failed reads yield the same fixture response; source is labelled fixture but outage is not reported. Caller evidence: `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:219 execute -> _recurrence`. |
| `copilot-sdk/apps/purchasing/backend/app/context_router.py:82` | `_evolution_variants` | Exception | [] | Purchasing context omits evolution variants after a failed graph read. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/context_router.py:393 item_profile -> _evolution_variants`. |
| `copilot-sdk/apps/purchasing/backend/app/evidence_providers.py:84` | `_domain_context` | Exception | ({}, False) | Graph evidence context failure becomes neutral MISSING_DATA evidence in read_payload. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/evidence_providers.py:155 read_payload -> _domain_context`. |
| `copilot-sdk/apps/purchasing/backend/app/main.py:418` | `_evolution_variants` | Exception | [] | Purchasing evolution provider returns no variants after a failed graph read. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/main.py:426 _purchasing_variants_with_config -> _evolution_variants`. |
| `copilot-sdk/apps/purchasing/backend/app/main.py:674` | `create_app._alert_conservation_status` | Exception | None | Alert conservation provider hides graph failure as absent optional conservation context. |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:172` | `_all_decisions` | Exception | [] | Purchasing evidence builder treats failed decision reads as no decisions. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:27 evidence_summary -> _all_decisions`. |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:182` | `_verified_decisions` | Exception | [] | Purchasing evidence builder treats failed verified-history reads as no verified outcomes. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:28 evidence_summary -> _verified_decisions`. |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:193` | `_centroid_checkpoints` | Exception | [] | Conservation-proof endpoint shows no checkpoint trajectory after a read failure. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:102 conservation_proof -> _centroid_checkpoints`. |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:203` | `_trajectory` | Exception | None | Purchasing evidence snapshot treats failed graph-backed trajectory as absent trajectory. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:32 evidence_summary -> _trajectory`. |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:220` | `_count` | Exception | 0 | Purchasing evidence metrics treat failed graph counts as zero decisions. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:99 conservation_proof -> _count`. |
| `copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py:149` | `_verified` | Exception | [] | Proof ledger/learning beats show zero verified outcomes after graph read failure. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py:156 _stats -> _verified`. |
| `copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py:173` | `_stats` | Exception | BOOTSTRAP conservation state | Failed stored-status read leaves the ordinary BOOTSTRAP default. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py:69 hero -> _stats`. |
| `copilot-sdk/apps/purchasing/backend/app/routers/queue.py:193`<br>`copilot-sdk/apps/purchasing/backend/app/routers/queue.py:198` | `_queue_scorer` | Exception | None | Failed graph-backed scorer construction becomes unavailable scorer; queue defaults to order_as_planned at confidence 0.5. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/routers/queue.py:38 order_queue -> _queue_scorer`. |
| `copilot-sdk/apps/purchasing/backend/app/routers/scorecard_router.py:71` | `build_iks_summary` | Exception | IKS=0; verified_count=0; available=False | Failure and a valid empty/unavailable IKS summary share fields; no graph-error reason is returned. available=False limits misuse but does not identify outage. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/routers/scorecard_router.py:54 iks_summary -> build_iks_summary`. |
| `copilot-sdk/apps/purchasing/backend/app/routers/trust_router.py:156`<br>`copilot-sdk/apps/purchasing/backend/app/routers/trust_router.py:163` | `_decisions_total` | Exception | 0 | Trust response cannot distinguish failed verification counts from zero verified decisions. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/routers/trust_router.py:37 trust_weights -> _decisions_total`. |
| `copilot-sdk/apps/purchasing/backend/app/services/cohort_status.py:206` | `PurchasingCohortStatus._read_decisions` | Exception | [] after trying alternate methods | Purchasing cohort evaluation gets an empty ledger when all graph accessors fail. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/services/cohort_status.py:140 _count_structure_cohorts -> self._read_decisions`. |
| `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:71` | `PurchasingClaimRegistry.refresh` | Exception | None; has_outcomes=False | Claim refresh treats unreadable verified outcomes as no outcomes. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/main.py:612 (purchasing_claim_registry.refresh)`. |
| `copilot-sdk/apps/trading/backend/app/evidence_providers.py:83` | `_domain_context` | Exception | ({}, False) | Graph evidence context failure becomes neutral MISSING_DATA evidence in read_payload. Caller evidence: `copilot-sdk/apps/trading/backend/app/evidence_providers.py:146 read_payload -> _domain_context`. |
| `copilot-sdk/apps/trading/backend/app/routers/promotion.py:105` | `_conservation_status` | Exception | status=RED; passed=False | Fails closed, but graph outage is indistinguishable from a measured failing conservation check; no unavailable/error reason. Caller evidence: `copilot-sdk/apps/trading/backend/app/routers/promotion.py:46 evaluate_promotion -> _conservation_status`. |
| `copilot-sdk/apps/trading/backend/app/routers/regime_router.py:172` | `_conservation_status` | Exception | None | Regime endpoints replace failed conservation read with an empty mapping. Caller evidence: `copilot-sdk/apps/trading/backend/app/routers/regime_router.py:66 regime_performance -> _conservation_status`. |
| `copilot-sdk/apps/trading/backend/app/routers/regime.py:152` | `_conservation_status` | Exception | None | Conservation read failure is returned as absent optional state. Caller evidence: `copilot-sdk/apps/trading/backend/app/routers/regime.py:63 regime_detail -> _conservation_status`. |
| `copilot-sdk/apps/trading/backend/app/services/claim_gate.py:97` | `TradingClaimRegistry.refresh_from_store` | Exception | None | Claim refresh treats unreadable outcomes like an empty ledger and preserves existing claim state. Caller evidence: `copilot-sdk/apps/trading/backend/app/main.py:458 create_app -> claim_registry.refresh_from_store`. |
| `copilot-sdk/apps/trading/backend/app/services/cohort_status.py:158` | `TradingCohortStatus._read_decisions` | Exception | [] after trying alternate methods | Trading cohort evaluation gets an empty ledger when all graph accessors fail. Caller evidence: `copilot-sdk/apps/trading/backend/app/services/cohort_status.py:141 _records_with_provenance -> self._read_decisions`. |
| `copilot-sdk/apps/trading/backend/app/services/trader_profiles.py:85` | `TraderProfileService._verified_decisions` | Exception | [] | Trader profile aggregation treats failed verified-decision reads as no trader outcomes. Caller evidence: `copilot-sdk/apps/trading/backend/app/services/trader_profiles.py:73 _grouped_decisions -> self._verified_decisions`. |
| `copilot-sdk/apps/trading/backend/app/services/trust_analysis.py:173` | `TrustAnalyzer._decisions_until_dk` | Exception | None | Failed decision count is indistinguishable from no remaining decisions until DK. Caller evidence: `copilot-sdk/apps/trading/backend/app/services/trust_analysis.py:55 analyze -> self._decisions_until_dk`. |
| `copilot-sdk/apps/trading/backend/app/state/compute_helpers.py:290` | `safe_call` | Exception | caller-supplied default (IKS=0.0) | Trading registry passes graph-backed scorer._compute_iks through this wrapper; outage becomes zero IKS. Caller evidence: `copilot-sdk/apps/trading/backend/app/state/trading_registry.py:173 create_trading_tab_state_cache -> safe_call`. |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:387` | `_latest_checkpoint_info` | Exception | None | Checkpoint read failure is indistinguishable from no warm-start checkpoint. Caller evidence: `copilot-sdk/copilot_sdk/backend/transfer_router.py:376 _find_warm_start_info -> _latest_checkpoint_info`. |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:503`<br>`copilot-sdk/copilot_sdk/backend/transfer_router.py:510` | `_target_conservation_state` | Exception | fallback conservation state or UNKNOWN | Stored conservation read failures are discarded before in-process state fallback; that fallback can return an ordinary state without identifying the failed graph. The explicit UNKNOWN branch is not the finding. Caller evidence: `copilot-sdk/copilot_sdk/backend/transfer_router.py:287 transfer -> _target_conservation_state`. |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:555`<br>`copilot-sdk/copilot_sdk/backend/transfer_router.py:562` | `_source_conservation_state` | Exception | fallback source state | Stored source-state read failures can be replaced by scorer state without identifying the failed graph. This finding concerns the ordinary-state fallback, not an explicit UNKNOWN response. Caller evidence: `copilot-sdk/copilot_sdk/backend/transfer_router.py:129 transfer_execute -> _source_conservation_state`. |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:688` | `_source_store_for_domain` | Exception | None | Failed source-store provider is indistinguishable from an unconfigured source store. Caller evidence: `copilot-sdk/copilot_sdk/backend/transfer_router.py:670 _log_transfer_event -> _source_store_for_domain`. |
| `copilot-sdk/copilot_sdk/demo/bundle.py:91` | `_restore` | Exception | continues with current=0 | Failed count is treated as empty database and bypasses restore skip threshold. Caller evidence: `copilot-sdk/copilot_sdk/demo/bundle.py:40 restore_bundle_if_empty -> _restore`. |
| `copilot-sdk/copilot_sdk/framework/checkpoint.py:98` | `CheckpointService.list_checkpoints` | Exception | [] | Checkpoint listing presents graph outage as no checkpoints. |
| `copilot-sdk/copilot_sdk/framework/decision_history.py:59` | `DecisionHistoryService.get_category_stats` | Exception | zero counts; rolling_accuracy=0.5 | Same cold-start statistics returned for empty category and failed query. Caller evidence: `copilot-sdk/copilot_sdk/framework/composite_gate.py:117 (DecisionHistoryService.get_category_stats)`. |
| `copilot-sdk/copilot_sdk/framework/intervention_controls.py:268` | `InterventionControls.get_current_state` | Exception | normal state; last_intervention=None | Intervention state looks like no prior intervention during query failure. |
| `copilot-sdk/copilot_sdk/framework/intervention_controls.py:302` | `InterventionControls.get_intervention_history` | Exception | [] | Intervention-history outage is exposed as empty history. |
| `copilot-sdk/copilot_sdk/framework/provenance.py:326` | `ProvenanceService.get_provenance_from_graph` | Exception | None | Unavailable graph and missing decision provenance have identical results. |
| `copilot-sdk/copilot_sdk/framework/shadow_mode.py:106` | `ShadowModeService.get_shadow_report` | Exception | zero-count shadow report | Failed history query produces ordinary Continue shadow observation report. |
| `copilot-sdk/copilot_sdk/framework/similar_cases_base.py:99` | `SimilarCasesBase._fetch_verified_decisions` | Exception | [] | No similar verified decisions and graph outage look identical. Caller evidence: `copilot-sdk/copilot_sdk/framework/similar_cases_base.py:142 get_similar_cases -> self._fetch_verified_decisions`. |
| `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:365`<br>`copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:376` | `_category_coverage_alpha` | Exception | 0.0 | Migration shadow coverage treats failed verified/category reads as zero coverage. Log says non-authoritative; result has no failure flag. Caller evidence: `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:333 _snapshot_scorer_state -> _category_coverage_alpha`. |
| `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:395` | `_call_count` | Exception | 0 | Migration comparison treats failed count as an empty ledger. Caller evidence: `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:330 _snapshot_scorer_state -> _call_count`. |
| `copilot-sdk/copilot_sdk/reporting/weekly.py:285` | `WeeklyReportGenerator._compute_iks` | Exception | (0.0, 0.0) | Weekly report replaces an unreadable graph-backed scorer trajectory with zero IKS and zero change. Caller evidence: `copilot-sdk/copilot_sdk/reporting/weekly.py:114 generate -> self._compute_iks`. |
| `copilot-sdk/copilot_sdk/rl/exploration.py:89` | `ConservationBoundedThompson._load_from_store` | Exception | None; retains initial priors | Thompson constructor continues with default priors when persisted posterior read fails. Caller evidence: `copilot-sdk/copilot_sdk/rl/exploration.py:23 __init__ -> self._load_from_store`. |
| `copilot-sdk/copilot_sdk/scoring/gate_enforced_scorer.py:103` | `GateEnforcedScorer._conservation_state` | Exception | {} | Conservation getter failures are erased before gate evaluation. Caller evidence: `copilot-sdk/copilot_sdk/scoring/gate_enforced_scorer.py:71 _evaluate_gate -> self._conservation_state`. |
| `copilot-sdk/copilot_sdk/scoring/measurement_state.py:178` | `_current_iks` | Exception | None | Measurement snapshot treats failed graph-backed trajectory as absent IKS. Caller evidence: `copilot-sdk/copilot_sdk/scoring/measurement_state.py:83 compute_measurement_state -> _current_iks`. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py:218` | `GreyNoiseConnector.refresh.existing_observation` | Exception | None | fallback_entry replaces unreadable prior observation with hardcoded fallback. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py:223 fallback_entry -> existing_observation`. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:287` | `PulsediveConnector.refresh.existing_observation` | Exception | None | fallback_entry treats read outage as absent observation. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:293 fallback_entry -> existing_observation`. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1350` | `CampaignRepository.fetch_all_events` | Exception | [] | Campaign history outage looks like no events. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/main.py:600 startup_event -> _camp_repo.fetch_all_events`. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1387` | `CampaignRepository.fetch_recent_events` | Exception | [] | Recent campaign outage looks like no events. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2096 _materialize_alert -> self.repo.fetch_recent_events`. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1423` | `CampaignRepository.fetch_single_alert_event` | Exception | None | Alert-event read outage looks missing. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1962 _check_alert_impl -> self.repo.fetch_single_alert_event`. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1767` | `CampaignRepository.get_campaigns` | Exception | [] | Campaign listing outage appears empty. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1942 get_campaigns -> repo.get_campaigns`. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1793` | `CampaignRepository.get_campaign_detail` | Exception | None | Campaign detail outage appears not found. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2045 get_campaign_detail -> repo.get_campaign_detail`. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1804` | `CampaignRepository.campaigns_exist` | Exception | False | Campaign existence outage appears no campaigns. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/main.py:597 startup_event -> _camp_repo.campaigns_exist`. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1991` | `CampaignMatcher._check_alert_impl` | Exception | None | Campaign matching reports no campaign on materialization failure; trace records unknown only in logs. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1946 check_alert -> self._check_alert_impl`. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2040` | `CampaignMatcher._check_materialized_campaign` | Exception | None | Materialized campaign outage appears absent. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1977 _check_alert_impl -> self._check_materialized_campaign`. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2172` | `CampaignMatcher._find_matching_campaign` | Exception | None | Matching campaign outage appears no match. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/orchestrator.py:183` | `_query_rows` | Exception | [] | Orchestrator graph context helper hides outages. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/orchestrator.py:132 _threat_intel_provenance -> _query_rows`. |
| `gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:124` | `SOCEvidenceProvider._read_from_graph_client` | Exception | None | read_evidence returns no evidence on failed query. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:85 read_evidence -> self._read_from_graph_client`. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py:86` | `CheckpointService.list_checkpoints` | Exception | [] | Checkpoint route returns ordinary empty list. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:512 checkpoint_list -> CheckpointService.list_checkpoints`. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/decision_history.py:49` | `DecisionHistoryService.get_category_stats` | Exception | zero stats; accuracy 0.5 | Same payload as category without history. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/framework/composite_gate.py:117 evaluate -> DecisionHistoryService.get_category_stats`. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:268` | `InterventionControls.get_current_state` | Exception | last_intervention=None | State presents outage as no prior intervention. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:1015 intervention_state -> ctrl.get_current_state`. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:302` | `InterventionControls.get_intervention_history` | Exception | [] | History presents outage as empty. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:1025 intervention_history -> ctrl.get_intervention_history`. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/provenance.py:320` | `ProvenanceService.get_provenance_from_graph` | Exception | None | Provenance outage becomes missing provenance. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1377 get_decision_provenance -> ProvenanceService.get_provenance_from_graph`. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/shadow_mode.py:86` | `ShadowModeService.get_shadow_report` | Exception | zero-count report | Shadow outage becomes Continue shadow observation. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:477 shadow_report -> ShadowModeService.get_shadow_report`. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/similar_cases_base.py:93` | `SimilarCasesBase._fetch_verified_decisions` | Exception | [] | Similar-case outage becomes no cases. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/framework/similar_cases_base.py:135 get_similar_cases -> self._fetch_verified_decisions`. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/cohort_status_router.py:46` | `_read_decision_records` | Exception | [] | Cohort graph outage becomes zero cohort evidence. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/cohort_status_router.py:24 get_campaign_cohort_status -> _read_decision_records`. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:399` | `get_enrichment_summary` | Exception | threat_indicators zero totals/maps | Secondary summary outage looks unpopulated. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:235`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:275`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:305` | `get_compounding_metrics` | Exception | empty trend/events; omitted history | HTTP response retains projected metrics but omits query failure. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:741` | `get_board_export` | Exception | zero/partial board metrics | Outage labelled insufficient_data or live after partial reads. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:803`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:820` | `get_economics` | Exception | zero/partial decision/population metrics | Returns source=graph even when queries failed. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:592` | `query_soc_metrics` | Exception | get_metric_data fallback | Failed graph cross-context lookup returns registry data with confidence .96. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:705` | `get_detection_engineering` | Exception | noise-map count0 fp_rateNone | Outage same as insufficient category evidence. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:909` | `get_attack_tactic_breakdown` | Exception | breakdown=[] | Endpoint hides outage as no tactics. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1054`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1062` | `get_learning_state_endpoint` | Exception | last_verified_at=None; IKS0 or snapshot | No unavailable flag on returned learning-state metrics. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1242` | `explain_decision` | Exception | default threat-intelligence source label | Explanation uses default source after failed source lookup. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2164`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2261`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2286` | `get_analyst_benchmarking` | Exception | accumulating; empty archetypes/default day spread | First catch explicitly says data not loaded; later defaults may return ready. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2347 get_f9_report -> get_analyst_benchmarking`. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2393` | `get_enrichment_advisor` | Exception | advice based on IOC coverage0 | Graph outage looks like unenriched alerts. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2789`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2798`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2811`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2838` | `_tab1_content` | Exception | zero counts / empty maps | Tab content claims no pending alerts or no verified history. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3650 (tab-content dispatch mapping)`. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2905`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2917`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2935` | `_tab2_content` | Exception | zero/snapshot IKS; drift count0 | Tab claims system stable and no action required on missing graph metrics. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/governance_report.py:136 _collect_tab2_evidence -> _tab2_content`. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3144`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3205`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3263`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3275` | `_tab3_content` | Exception | node0; centroid fallback; override15%;verified0 | Normal recommendation narrative with missing graph data. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3652 (tab-content dispatch mapping)`. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3337`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3366`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3375` | `_tab4_content` | Exception | fallback counts and throughput50 | Annual ROI computed from default throughput on graph failure. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3653 (tab-content dispatch mapping)`. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3478`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3495` | `_tab5_content` | Exception | snapshot IKS; flywheel_edge_count0 | Failure labelled pre-activation instead of unavailable. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3654 (tab-content dispatch mapping)`. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3864` | `get_analyst_weights` | Exception | decision_counts={} | Precision results with missing counts treated insufficient/default weighting. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:4101` | `get_centroid_export` | Exception | iks_score=0.0 | Centroid export retains a normal zero IKS score after compute_iks_v2 graph queries fail. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:4261` | `get_centroid_support` | Exception | GREEN cold-start payload | Unreadable bootstrap centroids produce 'All centroids within data support region' with zero warnings. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:897`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1223`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1555` | `analyze_alert` | Exception | headroom0; campaign/cluster omitted | Query failures cannot be distinguished from no context; normal analyze response. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2177` | `report_decision_outcome` | Exception | analyst eta default | Graph quality read failure treated like insufficient analyst history. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3561` | `get_graph_data` | Exception | nodes=[],relationships=[] | analyze_alert embeds empty visualization after query failure. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1400 analyze_alert -> get_graph_data`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/attack_chain.py:118` | `AttackChainService._fetch_recent_alerts` | Exception | [] | Attack-chain history outage looks no alerts. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/attack_chain.py:75 scan_recent_alerts -> self._fetch_recent_alerts`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:133` | `_safe_centroid_drift` | Exception | zero drift per category | Balance sheet presents zero drift when bootstrap/export graph reads fail. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:214 generate_balance_sheet -> _safe_centroid_drift`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:150` | `_safe_auto_approve_stats` | Exception | zero coverage/counts; empty categories | Balance sheet converts auto-approve endpoint failure into ordinary zero coverage. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:216 generate_balance_sheet -> _safe_auto_approve_stats`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:158` | `_safe_timeline` | Exception | timeline=[]; ceiling_estimate=None | Balance sheet hides failed snapshot/bootstrap graph reads as absent evolution history. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:217 generate_balance_sheet -> _safe_timeline`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/benchmarking_report.py:169` | `BenchmarkingEngine._fetch_verified_decisions` | Exception | [] | Benchmark history query returns no decisions. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/benchmarking_report.py:36 generate_report -> self._fetch_verified_decisions`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cluster_history.py:155` | `get_cluster_history` | Exception | None | Analyze omits cluster history on read failure; identical to unavailable entity context. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1548 (_get_cluster_history alias)`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cohort_status.py:153` | `CohortStatusService._read_decisions` | Exception | [] | Cohort status treats callback graph-read failure as an empty cohort ledger. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/cohort_status.py:130 _real_decisions -> self._read_decisions`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:210` | `DiscoveryService._get_as_of_epoch_ms` | Exception | None | Graph-clock failure returns None, the same as no timestamps. refresh does expose a generic 'No graph timestamps available' error (same file:269); it cannot identify the swallowed database error. Impact is limited to lost failure diagnosis. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:269 refresh -> self._get_as_of_epoch_ms`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:234` | `ExecutiveNarrative._what_changed` | Exception | zero/partial change summary | Executive narrative hides failed reads. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:181 generate_weekly -> self._what_changed`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:266`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:279` | `ExecutiveNarrative._what_discovered` | Exception | zero chains/entities | Executive narrative hides failed reads. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:182 generate_weekly -> self._what_discovered`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:344` | `ExecutiveNarrative._get_metrics` | Exception | zero/partial metrics | Executive narrative hides failed reads. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:385` | `ExecutiveNarrative._generate_headline` | Exception | unpopulated or partial headline | Explicit not yet populated message on failed count lookup. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:180 generate_weekly -> self._generate_headline`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:421`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:441`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:451`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:461`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:482`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:503`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:524`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:546`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:583`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:613`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:635` | `build_executive_narrative_async` | Exception | zero/partial narrative metrics and inferred health | Digest claims not populated or derives health from IKS without graph-error flag. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1650 executive_narrative -> build_executive_narrative_async`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:190` | `GraphExplorerService.get_top_nodes` | Exception | [] | Top-nodes route exposes no nodes/count0. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:665 graph_top_nodes -> GraphExplorerService.get_top_nodes`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:216` | `GraphExplorerService.get_node_neighbors` | Exception | neighbors=[],total0 | Neighbor route looks no graph neighbors. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:678 graph_node_neighbors -> GraphExplorerService.get_node_neighbors`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:250`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:263` | `GraphExplorerService.get_graph_summary` | Exception | zero/partial counts/maps | Graph summary hides node/edge query failures. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:694 graph_summary -> GraphExplorerService.get_graph_summary`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:131`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:138` | `compute_visible_iks` | Exception | 0.0 | Visible IKS returns zero when fallback graph IKS queries fail. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2903 _tab2_content -> compute_visible_iks`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:165` | `get_iks_trend` | Exception | [] | IKS trend outage looks no snapshots. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_patterns.py:120` | `BaseInvestigationPattern._bounded_read` | Exception | [] | Investigation bounded read treats graph-query failure as no evidence. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_patterns.py:88 execute -> self._bounded_read`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:776` | `compute_volume_baseline` | Exception | zero daily baseline | Failed history read is substituted with an empty series used to compute the volume baseline. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:824 detect_volume_spike -> compute_volume_baseline`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1026`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1036`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1063`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:1081` | `compute_verification_health` | Exception | zero totals/window counts | Verification health uses zero coverage and empty time windows after failed reads. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2612 get_verification_health -> compute_verification_health`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/override_detector.py:62` | `load_from_graph` | Exception | inactive detector; empty examples | load_from_graph clears/loads the detector with no examples after a failed read. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:390` | `_get_shadow_batch_stats` | Exception | batch_count=0; batch_std=0; win_rates=[] | Promotion gate sees no shadow batches when evolution history cannot be read. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:182 evaluate_promotion -> _get_shadow_batch_stats`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:190` | `read_decision_distance_log` | Exception | [] | Distance-log read cannot distinguish empty history from query failure. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:4366 get_decision_distance_log -> read_decision_distance_log`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:208` | `fetch_category_distribution` | Exception | {} | Category distribution failure becomes an empty distribution for distance logging. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:224` | `read_reconvergence_events` | Exception | [] | Reconvergence event reader conflates failed query and no events. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2587 get_reconvergence_log -> read_reconvergence_events`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:493` | `CreditAssigner.assign_chain_credit` | Exception | [] | Credit assignment cannot distinguish failed historical query from no eligible decisions. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2898 report_decision_outcome -> get_credit_assigner().assign_chain_credit`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py:351`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py:365` | `SimulationOrchestrator.run` | Exception | alert metadata / minimal context | Simulation silently substitutes alert-pool metadata and minimal security context for failed graph reads. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:151` | `ThreatIndicatorService.get_indicators_for_alert` | Exception | [] | Alert indicator query failure is indistinguishable from no indicators. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1416 get_threat_intel_for_alert -> ThreatIndicatorService.get_indicators_for_alert`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:187` | `ThreatIndicatorService.get_all_indicators` | Exception | total=0; indicators=[] | Indicator inventory reports a normal empty inventory on failed query. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:393 get_enrichment_summary -> ThreatIndicatorService.get_all_indicators`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:178` | `_build_threat_intel_factor` | Exception | zero threat-intel factor | Graph outage produces the same 'No threat intel data' explanation as a successful empty query. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:260 get_decision_factors -> _build_threat_intel_factor`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:235` | `_get_alert_type` | Exception | empty string | Failed alert lookup loses the type exactly as a missing alert does. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:259 get_decision_factors -> _get_alert_type`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:86` | `_consult_history` | Exception | {'action':'proceed'} | Variant generator uses same proceed decision for unreadable history and no history, bypassing prior rollback/rejection checks. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:762 scan_for_opportunities -> _consult_history`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:242` | `_load_accuracy_trajectory` | Exception | trajectory built with empty live_data | Graph counts failure is hidden before the accuracy trajectory builder runs. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:613 detect -> _load_accuracy_trajectory`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:427` | `_get_per_category_accuracy_trends` | Exception | {} | Failed trend reads suppress accuracy-drift signals as if no eligible categories exist. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:461 detect -> _get_per_category_accuracy_trends`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:717` | `CoverageGapRule.detect` | Exception | None | Coverage-gap detection returns the same no-signal value after graph failure. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:755 scan_for_opportunities -> rule.detect`. |
| `s2p-copilot/backend/app/framework/checkpoint.py:86` | `CheckpointService.list_checkpoints` | Exception | [] | checkpoint_list endpoint wraps as checkpoints without error. Caller evidence: `s2p-copilot/backend/app/routers/framework_router.py:430 checkpoint_list -> CheckpointService.list_checkpoints`. |
| `s2p-copilot/backend/app/framework/intervention_controls.py:428` | `InterventionControls.get_current_state` | Exception | state with last_intervention=None | Missing intervention and unavailable graph identical. Caller evidence: `s2p-copilot/backend/app/routers/framework_router.py:699 intervention_state -> ctrl.get_current_state`. |
| `s2p-copilot/backend/app/framework/intervention_controls.py:463` | `InterventionControls.get_intervention_history` | Exception | [] | History outage returns empty history. Caller evidence: `s2p-copilot/backend/app/routers/framework_router.py:709 intervention_history -> ctrl.get_intervention_history`. |
| `s2p-copilot/backend/app/routers/framework_router.py:310` | `get_ols_status_endpoint` | Exception | warm_start_active=False | OLS endpoint treats failed LearningState read as warm-start inactive. |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:115` | `_get_iks` | Exception | {} | Audit export substitutes missing trajectory/IKS fields after failed graph-backed trajectory read. Caller evidence: `s2p-copilot/backend/app/routers/s2p_audit_export.py:292 _export_payload -> _get_iks`. |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:188` | `_factor_analysis` | Exception | fingerprint={} | Audit export omits the fingerprint when its graph-backed computation fails. Caller evidence: `s2p-copilot/backend/app/routers/s2p_audit_export.py:297 _export_payload -> _factor_analysis`. |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:166` | `_call_or_none` | Exception | None | Evidence builder uses wrapper for scorer.get_verified_count/get_category_phase; unreadable graph counts become absent evidence fields. Caller evidence: `s2p-copilot/backend/app/routers/s2p_evidence.py:113 (get_verified_count)`. |
| `s2p-copilot/backend/app/routers/s2p_situation.py:184` | `_entity_context_available` | Exception | False | Failed/timed-out entity context lookup is indistinguishable from a valid empty neighborhood. Caller evidence: `s2p-copilot/backend/app/routers/s2p_situation.py:56 get_situation -> _entity_context_available`. |
| `s2p-copilot/backend/app/routers/s2p.py:322` | `_resolve_graph_context` | Exception | None | S2P scoring uses no graph context after lookup failure, exactly as when no contextual neighbors exist. Caller evidence: `s2p-copilot/backend/app/routers/s2p.py:2291 score_procurement_event -> _resolve_graph_context`. |
| `s2p-copilot/backend/app/routers/s2p.py:1445` | `_receipt_conservation_snapshot` | Exception | state=''; verified_count=0 | Outcome receipt snapshot loses failure provenance and can record zero verification count. Caller evidence: `s2p-copilot/backend/app/routers/s2p.py:2667 learn_decision -> _receipt_conservation_snapshot`. |
| `s2p-copilot/backend/app/routers/s2p.py:2284`<br>`s2p-copilot/backend/app/routers/s2p.py:2306`<br>`s2p-copilot/backend/app/routers/s2p.py:2461` | `score_procurement_event` | Exception | active_variant/process_context=None; prior_verified_count=0 | Scoring response omits graph-backed enrichment and can label cold start after failed reads. |
| `s2p-copilot/backend/app/services/centroid_explorer.py:208` | `S2PCentroidExplorerService._p39_evidence` | Exception | {} | explain_decision receives empty P39 evidence without an error flag. Caller evidence: `s2p-copilot/backend/app/services/centroid_explorer.py:142 explain_decision -> self._p39_evidence`. |
| `s2p-copilot/backend/app/services/s2p_context_builder.py:271` | `S2PContextBuilder._supplier_enrichment` | Exception | {} | Supplier context omits enrichment indistinguishably from unseeded enrichment. Caller evidence: `s2p-copilot/backend/app/services/s2p_context_builder.py:234 build_supplier_context -> self._supplier_enrichment`. |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:217` | `S2PSupplierEnrichmentService.read_supplier` | Exception | {} | Supplier enrichment read outage appears absent. Caller evidence: `s2p-copilot/backend/app/routers/s2p_enrichment.py:79 enrichment_supplier -> service.read_supplier`. |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:228` | `S2PSupplierEnrichmentService.list_suppliers` | Exception | [] | Supplier enrichment listing outage appears empty. Caller evidence: `s2p-copilot/backend/app/services/s2p_enrichment.py:234 summary -> self.list_suppliers`. |
| `s2p-copilot/backend/app/services/s2p_situation_pattern.py:180`<br>`s2p-copilot/backend/app/services/s2p_situation_pattern.py:185` | `_receipt_context` | Exception | empty/partial receipt list | Traversal treats receipt-store read failure as no matching invoice/decision receipts. Caller evidence: `s2p-copilot/backend/app/services/s2p_situation_pattern.py:113 traverse -> _receipt_context`. |

## P2 Findings (should fix)

| File:line | Function | Caught | Returns | Caller impact |
|---|---|---|---|---|
| `ci-platform/ci_platform/graph/age_graph_store.py:383` | `AGEGraphStore._l5_upsert_current` | Exception | None unless transaction provided | Nontransactional L5 edge creation failure swallowed after prior state/edge mutations. Caller evidence: `ci-platform/ci_platform/graph/age_graph_store.py:2942 _update_centroid_impl -> self._l5_upsert_current`. |
| `copilot-sdk/apps/dataops/backend/app/main.py:498` | `_seed_from_fixtures` | Exception | partial seeded counts | Auto-seed logs skipped writes and returns counts without an error collection; startup continues. Caller evidence: `copilot-sdk/apps/dataops/backend/app/main.py:524 _auto_seed_if_needed -> _seed_from_fixtures`. |
| `copilot-sdk/apps/dataops/backend/app/main.py:535`<br>`copilot-sdk/apps/dataops/backend/app/main.py:565` | `_seed_demo_evolution_events_if_needed` | Exception | None | Demo evolution seed read/write failures are only printed; startup sees the same result as a completed/no-op seed. Caller evidence: `copilot-sdk/apps/dataops/backend/app/main.py:780 _run_startup_locked -> _seed_demo_evolution_events_if_needed`. |
| `copilot-sdk/apps/purchasing/backend/app/main.py:362` | `_seed_from_fixtures` | Exception | partial seeded counts | Auto-seed logs skipped writes and returns counts without an error collection; startup continues. Caller evidence: `copilot-sdk/apps/purchasing/backend/app/main.py:387 _auto_seed_if_needed -> _seed_from_fixtures`. |
| `copilot-sdk/apps/trading/backend/app/main.py:326` | `_seed_from_fixtures` | Exception | partial seeded counts | Auto-seed logs skipped writes and returns counts without an error collection; startup continues. Caller evidence: `copilot-sdk/apps/trading/backend/app/main.py:351 _auto_seed_if_needed -> _seed_from_fixtures`. |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:597`<br>`copilot-sdk/copilot_sdk/backend/scoring_router.py:602`<br>`copilot-sdk/copilot_sdk/backend/scoring_router.py:626` | `_persist_conservation_state_l5_locked` | Exception | None | Conservation persistence read/write failures only log; learning callers receive no failure status. Caller evidence: `copilot-sdk/copilot_sdk/backend/scoring_router.py:579 _persist_conservation_state_l5 -> _persist_conservation_state_l5_locked`. |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:701`<br>`copilot-sdk/copilot_sdk/backend/scoring_router.py:737` | `_persist_centroid_l5` | Exception | False | Phase-query or centroid persistence failure has the same return as ordinary skipped persistence; learning caller discards it. Caller evidence: `copilot-sdk/copilot_sdk/backend/scoring_router.py:333 learn -> _persist_centroid_l5`. |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:822` | `_persist_dk_state_l5` | Exception | None | Welford/runtime state may advance before graph DK persistence fails; caller sees no failure. Caller evidence: `copilot-sdk/copilot_sdk/backend/scoring_router.py:357 learn -> _persist_dk_state_l5`. |
| `copilot-sdk/copilot_sdk/demo/bundle.py:83` | `_restore` | Exception | written > 0 after skipping failed writes | Partial demo restore reports success if any decision persisted; per-row failures only logged. Caller evidence: `copilot-sdk/copilot_sdk/demo/bundle.py:40 restore_bundle_if_empty -> _restore`. |
| `copilot-sdk/copilot_sdk/demo/bundle.py:185` | `_restore` | Exception | False after rollback | Failed restore uses the same False result as ordinary skip/no-op; caller cannot identify persistence failure. Caller evidence: `copilot-sdk/copilot_sdk/demo/bundle.py:40 restore_bundle_if_empty -> _restore`. |
| `copilot-sdk/copilot_sdk/evolution/ledger.py:73`<br>`copilot-sdk/copilot_sdk/evolution/ledger.py:78` | `InMemoryEvolutionLedger.append` | Exception | None | In-memory evolution event remains appended after graph persistence fails; optional outbox failure is also log-only. |
| `copilot-sdk/copilot_sdk/framework/intervention_controls.py:360` | `InterventionControls._log_intervention` | Exception | normal intervention record | Failed audit write still returns an ID and successful-looking intervention record. Caller evidence: `copilot-sdk/copilot_sdk/framework/intervention_controls.py:56 freeze_all_learning -> self._log_intervention`. |
| `copilot-sdk/copilot_sdk/migrate/scratch_graph.py:100` | `drop_scratch_graph` | Exception | None | Scratch graph deletion failure is ignored; migration cleanup caller cannot know the graph was retained. Caller evidence: `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1324 run_migration -> drop_scratch_graph`. |
| `copilot-sdk/copilot_sdk/rl/exploration.py:117` | `ConservationBoundedThompson._persist` | Exception | None | Posterior update returns normally after save_rl_state fails; in-memory priors have advanced. Caller evidence: `copilot-sdk/copilot_sdk/rl/exploration.py:46 update -> self._persist`. |
| `copilot-sdk/copilot_sdk/scoring/dk_persistence.py:270` | `persist_dk_after_reestimate` | Exception | False | DK update failure is logged; learn-side persistence wrappers discard the boolean. Caller evidence: `copilot-sdk/copilot_sdk/backend/scoring_router.py:814 _persist_dk_state_l5 -> persist_dk_after_reestimate`. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1037`<br>`copilot-sdk/copilot_sdk/scoring/scorer.py:1068`<br>`copilot-sdk/copilot_sdk/scoring/scorer.py:1083` | `CompoundingScorer.learn` | Exception | normal conservation-pause result | Paused learning hides conservation/checkpoint/fingerprint persistence failures. Caller evidence: `copilot-sdk/copilot_sdk/backend/scorer_proxy.py:68 learn -> scorer.learn`. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1429`<br>`copilot-sdk/copilot_sdk/scoring/scorer.py:1467`<br>`copilot-sdk/copilot_sdk/scoring/scorer.py:1501` | `CompoundingScorer._persist_learning_artifacts` | Exception | None | Artifact failures logged/enqueued, but learn returns ordinary LearnResult; raise_on_error applies only checkpoint. Caller evidence: `copilot-sdk/copilot_sdk/scoring/scorer.py:1247 learn -> self._persist_learning_artifacts`. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1693`<br>`copilot-sdk/copilot_sdk/scoring/scorer.py:1706` | `CompoundingScorer._persist_evidence_receipt` | Exception | None | Receipt write and even outbox failure are hidden from learn. Caller evidence: `copilot-sdk/copilot_sdk/scoring/scorer.py:1168 learn -> self._persist_evidence_receipt`. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1768`<br>`copilot-sdk/copilot_sdk/scoring/scorer.py:1785` | `CompoundingScorer._persist_fingerprint` | Exception | False | Fingerprint persistence failure boolean discarded by learning artifact caller. Caller evidence: `copilot-sdk/copilot_sdk/scoring/scorer.py:1286 fingerprint -> self._persist_fingerprint`. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2105` | `CompoundingScorer.warm_start` | Exception | applied transfer result | Warm-start checkpoint write failure does not change returned applied count. Caller evidence: `copilot-sdk/copilot_sdk/backend/transfer_router.py:168 transfer_execute -> scorer.warm_start`. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2237` | `CompoundingScorer._refresh_dk_after_learn` | Exception | None | Learning continues after DK re-estimation fails; no DK failure status is returned. Caller evidence: `copilot-sdk/copilot_sdk/scoring/scorer.py:1175 learn -> self._refresh_dk_after_learn`. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2495`<br>`copilot-sdk/copilot_sdk/scoring/scorer.py:2528`<br>`copilot-sdk/copilot_sdk/scoring/scorer.py:2543` | `CompoundingScorer._save_centroids_checkpoint` | Exception | persisted bool | Default non-raising checkpoint writes; learn/flush ignore bool and reset batch. Caller evidence: `copilot-sdk/copilot_sdk/scoring/scorer.py:1801 flush_centroids -> self._save_centroids_checkpoint`. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2573` | `CompoundingScorer._maybe_archive` | Exception | None | Failed archive only logs. No production callsite found in the scoped Python code; latent helper-contract defect, not a demonstrated endpoint outage. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2651` | `CompoundingScorer._run_evolution` | Exception | None | Learn proceeds normally after failed history/evolution operations. Caller evidence: `copilot-sdk/copilot_sdk/scoring/scorer.py:1244 learn -> self._run_evolution`. |
| `copilot-sdk/copilot_sdk/scoring/startup_restore.py:64`<br>`copilot-sdk/copilot_sdk/scoring/startup_restore.py:79` | `_capture_existing_state` | Exception | None | Startup state-capture failure logs without adding a failure to the returned startup status. Caller evidence: `copilot-sdk/copilot_sdk/scoring/startup_restore.py:49 restore_l5_runtime_state -> _capture_existing_state`. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/crowdstrike_mock.py:146`<br>`gen-ai-roi-demo-v4-v50/backend/app/connectors/crowdstrike_mock.py:187` | `CrowdStrikeMockConnector.refresh` | Exception | ConnectorResult with counts and enrichment_summary | Writes/links fail per item; summary lists fixture items without errors. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/connectors/registry.py:88 refresh_all -> connector.refresh`. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py:317`<br>`gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py:340` | `GreyNoiseConnector.refresh` | Exception | ConnectorResult | Partial ingestion/link failure only printed; no error collection. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/connectors/registry.py:88 refresh_all -> connector.refresh`. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:403`<br>`gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:427` | `PulsediveConnector.refresh` | Exception | ConnectorResult | Failed writes/links hidden from returned summary. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/connectors/registry.py:88 refresh_all -> connector.refresh`. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1469` | `CampaignRepository.persist_campaign_seed` | Exception | None | Seed-write failure returns normally to _materialize_alert, which ignores result (same file:2113). Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2113 _materialize_alert -> self.repo.persist_campaign_seed`. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1565` | `CampaignRepository.cleanup_orphan_campaign_seeds` | Exception | 0 | Failed orphan expiry indistinguishable from zero expired. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2079` | `CampaignMatcher._materialize_in_background` | Exception | None | Background materialization failure clears pending state and returns no campaign without an error result. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2064 _schedule_materialization -> self._materialize_in_background`. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2216` | `CampaignMatcher._add_alert_to_campaign` | Exception | None | Campaign count/edge update failures discarded. |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:360` | `InterventionControls._log_intervention` | Exception | normal intervention record | Audit write failure not surfaced in mutation record. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:56 freeze_all_learning -> self._log_intervention`. |
| `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:792`<br>`gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:806`<br>`gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:820`<br>`gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:835`<br>`gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:853`<br>`gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:925` | `seed_graph` | Exception | verification report, omitting per-write error counts | Seed failures printed but not merged into returned graph verification; pre-existing counts may satisfy verification. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:997 <module> -> seed_graph`. |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:369`<br>`gen-ai-roi-demo-v4-v50/backend/app/main.py:378`<br>`gen-ai-roi-demo-v4-v50/backend/app/main.py:433`<br>`gen-ai-roi-demo-v4-v50/backend/app/main.py:459`<br>`gen-ai-roi-demo-v4-v50/backend/app/main.py:472`<br>`gen-ai-roi-demo-v4-v50/backend/app/main.py:490`<br>`gen-ai-roi-demo-v4-v50/backend/app/main.py:499`<br>`gen-ai-roi-demo-v4-v50/backend/app/main.py:588`<br>`gen-ai-roi-demo-v4-v50/backend/app/main.py:607` | `startup_event` | Exception | startup completes | Graph-backed hydration/write/recorrelation failures only printed; specific paths not startup connectivity check. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/main.py:30 lifespan -> startup_event`. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:229` | `refresh_threat_intel_endpoint` | Exception | refresh summary + partial indicators_persisted | Secondary persistence failure only printed. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1242`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1473` | `analyze_alert` | Exception | normal analysis response | Campaign flag and exploration metadata writes only warn. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2151`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2244`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2316`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2441`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2446`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2526`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2639`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2882`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2910`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2928` | `report_decision_outcome` | Exception | normal outcome response | Audit, DK, evolution/credit/reward persistence failures not represented by l5_centroid status. Also hides posterior-save and guarded/non-scorable state-capture failures. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:366` | `init_learning_state` | Exception | normal LearningState | Startup capture failure only warned, returned state has no capture error. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:626 _reset_learning_state_inner -> init_learning_state`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:687`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:725` | `_persist_l5_conservation_state` | Exception | None | Health evaluation returns computed health after failed conservation-state persistence. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:468 evaluate -> _persist_l5_conservation_state`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:178` | `log_decision_distance` | Exception | None | Background G1 logging caller discards this return; failed distance persistence only produces a log. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:244` | `_flush_shadow_batch` | Exception | None; continues other variants | Failed shadow batch write is logged without status to scheduling caller. Failed entries remain buffered for retry; immediate loss is not established. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:168 _maybe_schedule_flush -> _flush_shadow_batch`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/snapshots.py:68` | `_write_profile_snapshot` | Exception | None | Snapshot write logs and returns normally, leaving a missing persistence record. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/services/snapshots.py:34 maybe_write_profile_snapshot -> _write_profile_snapshot`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:103` | `ThreatIndicatorService.upsert_indicator` | Exception | empty string | Refresh endpoint ignores failed upsert result and increments indicators_persisted anyway (gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:219,227). Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:219,227 (unconditionally increments indicators_persisted)`. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:132` | `ThreatIndicatorService.link_to_alert` | Exception | None | Threat indicator edge failure has no status return. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:210` | `ThreatIndicatorService.cleanup_expired` | Exception | 0 | Failed deletion is reported as zero expired records removed. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:811` | `VariantGenerator.scan_for_opportunities` | Exception | partial generated list | Rule read/write failures are omitted from scan result; graph evolution-event failure skips variant registration with no returned error. Caller evidence: `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:426 admin_evolution_scan -> VariantGenerator().scan_for_opportunities`. |
| `s2p-copilot/backend/app/framework/intervention_controls.py:519` | `InterventionControls._log_intervention` | Exception | normal intervention record | rollback returns record despite failed audit insert. Caller evidence: `s2p-copilot/backend/app/framework/intervention_controls.py:172 freeze_all_learning -> self._log_intervention`. |
| `s2p-copilot/backend/app/routers/s2p.py:785`<br>`s2p-copilot/backend/app/routers/s2p.py:796`<br>`s2p-copilot/backend/app/routers/s2p.py:820` | `_persist_l5_conservation_state` | Exception | None | learn_decision and record_outcome ignore failed metrics/read/write; normal payload returned. Caller evidence: `s2p-copilot/backend/app/routers/s2p.py:2713 learn_decision -> _persist_l5_conservation_state`. |
| `s2p-copilot/backend/app/routers/s2p.py:843`<br>`s2p-copilot/backend/app/routers/s2p.py:875` | `_persist_l5_centroid_state` | Exception | False | phase graph read / centroid write failures hidden because learn endpoints discard False. Caller evidence: `s2p-copilot/backend/app/routers/s2p.py:2705 learn_decision -> _persist_l5_centroid_state`. |
| `s2p-copilot/backend/app/routers/s2p.py:924` | `_persist_l5_dk_state` | Exception | None | Welford updates before persistence; learn endpoints receive no persistence failure. Caller evidence: `s2p-copilot/backend/app/routers/s2p.py:2714 learn_decision -> _persist_l5_dk_state`. |
| `s2p-copilot/backend/app/routers/s2p.py:1017` | `_link_decision_to_invoice` | Exception | None | Non-GraphUnavailableError link failures logged; asynchronous link task does not report failure. Caller evidence: `s2p-copilot/backend/app/routers/s2p.py:2515 score_procurement_event -> _link_decision_to_invoice`. |
| `s2p-copilot/backend/app/routers/s2p.py:1913` | `_learn_with_scorer._advisory_invoice_link` | Exception | None | Advisory background invoice-link task logs the graph exception; ordinary learning response does not expose failed linkage. |

## P3 Findings (acceptable, tracked)

| File:line | Function | Caught | Returns | Note |
|---|---|---|---|---|
| `ci-platform/ci_platform/graph/age_client.py:650` | `AGEClient.get_pattern_count` | (TypeError, ValueError) | 0 | Malformed count conversion only; transport call is outside catch. |
| `ci-platform/ci_platform/graph/age_client.py:770` | `AGEClient.count_verified_decisions` | (TypeError, ValueError, KeyError) | 0 | Specific malformed count/key defaults; connection errors propagate. |
| `ci-platform/ci_platform/graph/age_client.py:785` | `AGEClient.count_correct_decisions` | (TypeError, ValueError, KeyError) | 0 | Specific malformed count/key defaults; connection errors propagate. |
| `ci-platform/ci_platform/graph/age_graph_store.py:3388` | `AGEGraphStore.load_latest_centroids` | (TypeError, ValueError) | None | Invalid centroid array after successful read treated as no usable checkpoint. |
| `ci-platform/ci_platform/graph/age_graph_store.py:4356` | `AGEGraphStore.read_entity_enrichment` | (TypeError, ValueError, json.JSONDecodeError) | partial enrichment dict | Specific malformed stored row skipped; transport error outside catch. |
| `ci-platform/ci_platform/graph/age_graph_store.py:4404` | `AGEGraphStore.list_entity_enrichments` | (TypeError, ValueError, json.JSONDecodeError) | partial enrichment list | Specific malformed stored row skipped; transport error outside catch. |
| `copilot-sdk/apps/dataops/backend/app/routers/regime_router.py:47` | `_payload` | (AttributeError, TypeError, ValueError) | verified_decisions=[] | Specific attribute/type/value compatibility catch produces observation-only conditioning without outcomes; other graph exceptions propagate. |
| `copilot-sdk/apps/purchasing/backend/app/routers/regime_router.py:47` | `_payload` | (AttributeError, TypeError, ValueError) | verified_decisions=[] | Specific attribute/type/value compatibility catch supplies empty observation-only conditioning; other graph exceptions propagate. |
| `copilot-sdk/apps/trading/backend/app/routers/analytics.py:261` | `_centroid_vectors` | (TypeError, IndexError) | omit category centroid | TypeError/IndexError skips malformed checkpoint shape; graph read itself propagates. |
| `copilot-sdk/copilot_sdk/backend/switching_cost_router.py:46`<br>`copilot-sdk/copilot_sdk/backend/switching_cost_router.py:50` | `_decision_count` | (TypeError, ValueError); (AttributeError, TypeError, ValueError) | len(records) | Narrow count/schema compatibility fallback; already-loaded records supply count. |
| `copilot-sdk/copilot_sdk/di/query_providers.py:205` | `DataOpsEnterpriseProvider._decision_invoice_ids` | ProviderUnavailableError | set() | Specific ProviderUnavailableError clears graph-linked invoice IDs; caller has no outage signal. Narrow catch, but this still loses outage information. |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2957` | `SQLiteGraphStore.load_latest_centroids` | (TypeError, ValueError) | None | Malformed stored centroid payload is treated as absent; database execution is outside catch. |
| `copilot-sdk/copilot_sdk/rl/exploration.py:105` | `ConservationBoundedThompson._load_from_store` | (TypeError, ValueError) | None; prior state retained/partially assigned | TypeError/ValueError while decoding posterior arrays; transport catch is separately P1. Partial alpha assignment is possible before beta conversion fails. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/judgment.py:199` | `explain_decision_get` | (KeyError, TypeError) | null explanation fields | Specific missing/malformed stored factor fields; graph query failure raises. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/time_machine.py:98` | `_age_payloads` | SnapshotCorruptError | omit corrupt checkpoint | SnapshotCorruptError skips an invalid stored payload; graph read itself is outside the handler. |
| `s2p-copilot/backend/app/routers/s2p_demo_beats.py:49` | `_rows` | GraphUnavailableError | [] | Demo-only fallback for GraphUnavailableError conflates outage and empty demo rows; track. |
| `s2p-copilot/backend/app/services/supplier_intelligence.py:377` | `SupplierIntelligenceComposer._read_enrichment` | (AttributeError, NotImplementedError, ValueError) | {} | Narrow optional enrichment capability/value fallback; other graph transport errors propagate. |

## Legitimate Patterns (no action)

These classifications apply to the cited paths, not every handler in the containing function. A listed caller may still discard an error-bearing result; where demonstrated, that separate caller is a finding above.

| File:line | Function | Pattern | Why legitimate |
|---|---|---|---|
| `ci-platform/ci_platform/copilot_core/cache.py:205` | `EntityCache.get_or_load` | Future/cache captures exception then propagates to waiter. | No successful default is returned to the requesting caller. |
| `ci-platform/ci_platform/graph/age_client.py:212` | `AGEClient._ensure_pool` | Failed warm-connection setup falls back to pool acquisition. | It does not invent query data; later pool/query errors propagate. |
| `ci-platform/ci_platform/graph/age_client.py:278` | `AGEClient.ensure_graph._do` | Suppresses only already-exists create race; other errors re-raise. | Idempotent graph creation handles a known race. |
| `ci-platform/ci_platform/graph/age_client.py:505` | `AGEClient._sync_execute` | Transient connection retry; terminal failures raise. | Retry does not substitute an empty result. |
| `ci-platform/ci_platform/graph/age_client.py:561` | `AGEClient._sync_transaction` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `ci-platform/ci_platform/graph/age_graph_store.py:112` | `AGEGraphStore._run._target` | Worker stores exception for _run to raise. | Thread boundary preserves failure for caller. |
| `ci-platform/ci_platform/onboarding/pipeline.py:111` | `OnboardingPipeline.run` | Onboarding returns success=False and errors. | Failure is explicit. |
| `ci-platform/ci_platform/strategy/two_phase_strategy.py:47` | `TwoPhaseStrategy.get_status` | Returns fallback phase plus error field. | Unlike get_phase, get_status exposes count failure. |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:92` | `_graph_client` | Missing factory/store raises HTTP error before query. | Pre-call availability validation is not an exception swallow. |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:121`<br>`copilot-sdk/apps/dataops/backend/app/context_router.py:123` | `_graph_decisions` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:610` | `_audit_recommendation_for_alert` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `copilot-sdk/apps/dataops/backend/app/graph_queries.py:113` | `DataOpsGraphClient.__init__` | Narrow nonproduction GraphConfigError leaves client absent. | AGE remains required; subsequent _run_graph raises 503. Production setup propagates the configuration failure. |
| `copilot-sdk/apps/dataops/backend/app/graph_queries.py:579` | `DataOpsGraphClient._run_graph` | Required AGE query failure raises 503. | Configured/live AGE sets _age_required; the None path is for deliberately absent optional topology. |
| `copilot-sdk/apps/dataops/backend/app/main.py:511` | `_auto_seed_if_needed` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/apps/dataops/backend/app/routers/query.py:43` | `create_query_router.query` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/apps/purchasing/backend/app/main.py:375` | `_auto_seed_if_needed` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/apps/purchasing/backend/app/routers/iks.py:33`<br>`copilot-sdk/apps/purchasing/backend/app/routers/iks.py:35` | `create_iks_router.iks_summary` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/apps/purchasing/backend/app/routers/iks.py:54` | `_graph_store` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/apps/purchasing/backend/app/routers/verify_router.py:121`<br>`copilot-sdk/apps/purchasing/backend/app/routers/verify_router.py:123`<br>`copilot-sdk/apps/purchasing/backend/app/routers/verify_router.py:125` | `create_verify_router.verify` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:192` | `PurchasingControlService._decisions` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/apps/trading/backend/app/main.py:339` | `_auto_seed_if_needed` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:227` | `_current_conservation_status` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `copilot-sdk/apps/trading/backend/app/routers/execution_router.py:35` | `create_execution_router._trades` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/apps/trading/backend/app/routers/journal.py:230` | `_journal_records` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/apps/trading/backend/app/routers/promotion_router.py:138` | `_conservation_status` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `copilot-sdk/apps/trading/backend/app/state/compute_helpers.py:262` | `count_decisions` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `copilot-sdk/copilot_sdk/backend/coalesced_read.py:28` | `CoalescedRead.run` | Future/cache captures exception then propagates to waiter. | No successful default is returned to the requesting caller. |
| `copilot-sdk/copilot_sdk/backend/conservation_router.py:48`<br>`copilot-sdk/copilot_sdk/backend/conservation_router.py:54`<br>`copilot-sdk/copilot_sdk/backend/conservation_router.py:99` | `create_conservation_router.status` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:112` | `_count_rows` | Count failure appends diagnostic issue. | Zero/default is accompanied by an error in the returned diagnostic structure. |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:286` | `_safe_cypher_count` | Count failure appends diagnostic issue. | Zero/default is accompanied by an error in the returned diagnostic structure. |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:332`<br>`copilot-sdk/copilot_sdk/backend/diagnostics_models.py:371`<br>`copilot-sdk/copilot_sdk/backend/diagnostics_models.py:406`<br>`copilot-sdk/copilot_sdk/backend/diagnostics_models.py:414`<br>`copilot-sdk/copilot_sdk/backend/diagnostics_models.py:466`<br>`copilot-sdk/copilot_sdk/backend/diagnostics_models.py:470`<br>`copilot-sdk/copilot_sdk/backend/diagnostics_models.py:367`<br>`copilot-sdk/copilot_sdk/backend/diagnostics_models.py:381`<br>`copilot-sdk/copilot_sdk/backend/diagnostics_models.py:362`<br>`copilot-sdk/copilot_sdk/backend/diagnostics_models.py:417` | `build_diagnostics` | Diagnostics attach errors/issues and unavailable status. | Failure remains visible in diagnostic output. |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py:60`<br>`copilot-sdk/copilot_sdk/backend/evolution_router.py:68` | `create_evolution_router._get_evolver` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py:158` | `create_evolution_router.summary` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py:359` | `_read_conservation_payload` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `copilot-sdk/copilot_sdk/backend/health_builder.py:39` | `build_graph_health` | Probe failure sets status=error, ready=False, graph unavailable. | A graph-health failure is explicit in the returned health response. |
| `copilot-sdk/copilot_sdk/backend/investigation_router.py:127`<br>`copilot-sdk/copilot_sdk/backend/investigation_router.py:129` | `create_investigation_router.investigate` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:171`<br>`copilot-sdk/copilot_sdk/backend/scoring_router.py:173` | `create_scoring_router.get_scorer` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:234`<br>`copilot-sdk/copilot_sdk/backend/scoring_router.py:236`<br>`copilot-sdk/copilot_sdk/backend/scoring_router.py:238` | `create_scoring_router.score_sync` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:287`<br>`copilot-sdk/copilot_sdk/backend/scoring_router.py:289`<br>`copilot-sdk/copilot_sdk/backend/scoring_router.py:291`<br>`copilot-sdk/copilot_sdk/backend/scoring_router.py:293` | `create_scoring_router.learn` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:408` | `create_scoring_router.diagnostics` | Diagnostic response contains error information. | Returned diagnostics do not claim successful empty graph results. |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:279` | `create_self_computation_router.counterfactual` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:219` | `_pattern_dollar_impact` | Read failure returns literal 'unknown'. | Successful empty data returns numeric 0; the failure is distinguishable. |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:644` | `_reset_conservation_state` | Atomic reset failure returns False, forwarded as conservation_reset. | Transfer response exposes reset not completed (transfer_router.py:172,198); no claim that it reset successfully. |
| `copilot-sdk/copilot_sdk/di/query_providers.py:129`<br>`copilot-sdk/copilot_sdk/di/query_providers.py:131`<br>`copilot-sdk/copilot_sdk/di/query_providers.py:118`<br>`copilot-sdk/copilot_sdk/di/query_providers.py:126` | `GraphStoreProvider._decisions` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `copilot-sdk/copilot_sdk/di/query_service.py:239` | `DIQueryService.execute` | ProviderUnavailableError becomes a query warning. | Response carries provider availability information along with any remaining data. |
| `copilot-sdk/copilot_sdk/discovery/patterns.py:226` | `_safe_phase` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `copilot-sdk/copilot_sdk/evolution/conservation_contract.py:108` | `ScorerBackedProvider.get_state` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `copilot-sdk/copilot_sdk/evolution/conservation_contract.py:153` | `CachedAsyncProvider.get_state` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:320` | `PromptVariantEvolver._resolve_conservation_state` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `copilot-sdk/copilot_sdk/evolution/shadow.py:48`<br>`copilot-sdk/copilot_sdk/evolution/shadow.py:60` | `DefaultShadowRunner.run_shadow` | Shadow evaluation accumulates errors. | Shadow output includes error count/details, rather than only ordinary empty results. |
| `copilot-sdk/copilot_sdk/framework/checkpoint.py:135` | `CheckpointService.rollback` | Rollback returns an error payload. | Query failure has a different message from checkpoint-not-found; graph error is exposed. |
| `copilot-sdk/copilot_sdk/framework/intervention_controls.py:126` | `InterventionControls.rollback` | Preview query returns {'error': ...}. | The caller receives the AGE failure rather than an empty checkpoint. |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:198` | `DualWriteStore._append_outbox_entry` | Secondary failures recorded in diagnostics/outbox; primary failure propagates. | Primary result is authoritative by DualWriteStore contract; mirror errors are observable as SECONDARY_WRITE_FAILURE/outbox health (copilot-sdk/copilot_sdk/graph/dual_write_store.py:134). This does not guarantee immediate mirror durability. |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:247` | `DualWriteStore._replay_outbox_locked` | Secondary failures recorded in diagnostics/outbox; primary failure propagates. | Primary result is authoritative by DualWriteStore contract; mirror errors are observable as SECONDARY_WRITE_FAILURE/outbox health (copilot-sdk/copilot_sdk/graph/dual_write_store.py:134). This does not guarantee immediate mirror durability. |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:300` | `DualWriteStore._write` | Secondary failures recorded in diagnostics/outbox; primary failure propagates. | Primary result is authoritative by DualWriteStore contract; mirror errors are observable as SECONDARY_WRITE_FAILURE/outbox health (copilot-sdk/copilot_sdk/graph/dual_write_store.py:134). This does not guarantee immediate mirror durability. |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:495`<br>`copilot-sdk/copilot_sdk/graph/dual_write_store.py:499` | `DualWriteStore.close` | Secondary failures recorded in diagnostics/outbox; primary failure propagates. | Primary result is authoritative by DualWriteStore contract; mirror errors are observable as SECONDARY_WRITE_FAILURE/outbox health (copilot-sdk/copilot_sdk/graph/dual_write_store.py:134). This does not guarantee immediate mirror durability. |
| `copilot-sdk/copilot_sdk/graph/factory.py:294` | `create_graph_store` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `copilot-sdk/copilot_sdk/graph/outcome_service.py:93` | `ProtocolV2OutcomeService._replay_locked` | Replay marks failed operations and reports failure count. | Deferred-write failure remains observable and retryable. |
| `copilot-sdk/copilot_sdk/graph/production.py:63` | `_probe_client_identity` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:421` | `SQLiteGraphStore.__init__` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1180`<br>`copilot-sdk/copilot_sdk/graph/sqlite_store.py:1184` | `SQLiteGraphStore._run_write` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `copilot-sdk/copilot_sdk/migrate/scratch_graph.py:85` | `create_scratch_graph` | Best-effort drop before scratch graph creation. | The subsequent create is not swallowed; an unavailable database still fails creation. |
| `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:667` | `_write_batch` | Batch errors recorded in migration report. | Failed write count/details survive to migration result. |
| `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:980`<br>`copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1271`<br>`copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:1144` | `run_migration` | Migration exception marks FAIL/errors. | Failure is explicit in report/result. |
| `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:275` | `PersistenceOutbox._drain_locked` | Outbox drain records failures and reports failed count. | Failed operations remain recoverable; caller can inspect replay failures. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:158` | `CompoundingScorer.__init__` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:331` | `CompoundingScorer.from_preset` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:454`<br>`copilot-sdk/copilot_sdk/scoring/scorer.py:475` | `CompoundingScorer.score` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:767` | `CompoundingScorer.get_conservation_state` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:953` | `CompoundingScorer.reinitialize_from_regime` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1160` | `CompoundingScorer.learn` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1375` | `CompoundingScorer._persist_conservation_snapshot` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1558`<br>`copilot-sdk/copilot_sdk/scoring/scorer.py:1568`<br>`copilot-sdk/copilot_sdk/scoring/scorer.py:1606` | `CompoundingScorer.capture_existing_state` | Capture collects persistence errors. | Returned capture result exposes failed artifacts; inspect these fields rather than assuming complete persistence. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2161` | `CompoundingScorer._compute_iks` | Catch surrounds local correctness decoding; fallback queries count_correct. | The actual fallback graph call is not swallowed and may raise. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2246` | `CompoundingScorer._conservation_pause` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2347` | `CompoundingScorer._read_conservation_inputs_with_retry` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2672` | `CompoundingScorer._evolution_conservation_state` | Conservation failure returns None and gate rejects missing state. | Successful empty history returns GREEN with zero counts; None is not accepted by evolution gate (copilot-sdk/copilot_sdk/evolution/gate.py:138). |
| `copilot-sdk/copilot_sdk/scoring/startup_restore.py:155`<br>`copilot-sdk/copilot_sdk/scoring/startup_restore.py:169` | `_restore_centroids` | Restore returns status=error and details. | Missing state and failed restore have distinct status. |
| `copilot-sdk/copilot_sdk/scoring/startup_restore.py:249` | `_restore_conservation` | Restore returns status=error and details. | Missing state and failed restore have distinct status. |
| `copilot-sdk/copilot_sdk/state/cached_static.py:66` | `cached_static.deco.async_wrapper` | Future/cache captures exception then propagates to waiter. | No successful default is returned to the requesting caller. |
| `copilot-sdk/copilot_sdk/state/cached_static.py:89` | `cached_static.deco.sync_wrapper` | Future/cache captures exception then propagates to waiter. | No successful default is returned to the requesting caller. |
| `copilot-sdk/copilot_sdk/state/tab_state_cache.py:342` | `TabStateCache._compute_and_store` | Cache marks invalidated_error/missing and stores error. | Cached payload retains explicit failure status. |
| `copilot-sdk/copilot_sdk/state/tab_state_cache.py:388` | `TabStateCache._compute_and_store_sync` | Cache marks invalidated_error/missing and stores error. | Cached payload retains explicit failure status. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/registry.py:95` | `ConnectorRegistry.refresh_all` | Connector result/health contains error information. | Outer collector exposes failures that escape individual connector helpers. |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/registry.py:116` | `ConnectorRegistry.health_check_all` | Connector result/health contains error information. | Outer collector exposes failures that escape individual connector helpers. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:232` | `TravelMatchFactor.compute` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:296` | `AssetCriticalityFactor.compute` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:356` | `ThreatIntelEnrichmentFactor.compute` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:415` | `ThreatIntelEnrichmentFactor._internal_campaign_score` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:478` | `PatternHistoryFactor.compute` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:557` | `PatternHistoryFactorComputer.compute` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:320` | `startup_event` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/audit.py:100` | `get_audit_decisions` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:107` | `get_deployments` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:461`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:463` | `process_alert` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:610`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:612` | `process_alert_blocked` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:752` | `get_recent_evolution` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:961` | `get_graph_stats` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:162` | `get_centroid_evolution` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:236`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:238`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:225` | `get_convergence_calendar` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:293`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:304`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:315` | `get_ols_status_endpoint` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:402` | `get_flywheel_comparison` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:429` | `get_iks_trend_endpoint` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:491` | `checkpoint_create` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:523` | `checkpoint_rollback` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:603` | `auto_approve_stats` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:649` | `graph_explorer_query` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:197` | `refresh_threat_intel_endpoint` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:328` | `get_enrichment_aggregate` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:368` | `get_enrichment_summary` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:448` | `get_enrichment_by_alert` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/judgment.py:166` | `explain_decision_get` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:314` | `get_compounding_metrics` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:433` | `get_evolution_events` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:479` | `get_weekly_trends` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:565`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:534` | `get_decision_economics` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:637`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:666`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:696` | `get_operational_metrics` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:37` | `_decision_counts` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:58` | `_recent_decisions` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:139` | `no_precedent_alerts` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:46`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:48` | `demo_refreeze` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:72`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:74` | `get_learning_control_room` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:101`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:103` | `get_frozen_comparison` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:126`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:128` | `initialize_frozen_comparison` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:634`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:636` | `query_soc_metrics` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:848` | `get_threat_landscape` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1166`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1222` | `explain_decision` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2089` | `get_accuracy_trajectory` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:517` | `get_alert_queue` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1692`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1696` | `analyze_alert` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1885`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1887` | `execute_action` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1940` | `reset_demo_alerts` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3006`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3010`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3014`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2622` | `report_decision_outcome` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3404`<br>`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3406` | `decision_factors` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:141` | `_safe_learning_health` | Health fallback explicitly says unavailable. | It does not masquerade as measured health. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:188`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:191` | `DiscoveryService._run_algorithm` | Returns error alongside empty discoveries. | Timeout/query error is distinguishable from no discoveries. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:270`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:327` | `DiscoveryService.refresh` | Refresh returns errors/stale information. | Outer refresh failure is observable; swallowed graph-clock reason is separately tracked. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:282` | `SOCConservationProvider.refresh` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:819` | `write_bootstrap_state` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:217`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:235`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:251`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:274` | `compute_iks_v2` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:326` | `_compute_delta_7d` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:500` | `LearningHealthMonitor._count_red_days` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:620` | `_query_soc_verified_conservation_stats` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:874` | `compute_category_baseline` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:976` | `compute_analyst_precision` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:134` | `PosteriorStore.save` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:168` | `PosteriorStore.load` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:203`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:198` | `PosteriorStore.health_check` | Health check returns healthy=False on failure. | Caller receives a health failure. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:644`<br>`gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:653` | `get_exploration_policy` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:227` | `SocAlertTraversalPattern.traverse_async` | Returns context with get_security_context failure warning. | Caller can distinguish unavailable context from an ordinary empty traversal. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:253` | `SocAlertTraversalPattern._traverse_sync` | Returns context with get_security_context failure warning. | Caller can distinguish unavailable context from an ordinary empty traversal. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:187` | `StateManager.soft_reset` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:257` | `StateManager.hard_reset` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/time_machine.py:394` | `get_evolution_timeline` | IKS catch leaves interpretation='unavailable'. | Zero estimate is explicitly labeled unavailable; earlier snapshot/bootstrap failures still propagate. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_registry.py:280` | `_query_events` | Returns ([], error_text). | The error channel distinguishes failed query from a legitimate empty event list. |
| `s2p-copilot/backend/app/framework/decision_history.py:51` | `DecisionHistoryService.get_category_stats` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/framework/provenance.py:320` | `ProvenanceService.get_provenance_from_graph` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/framework/shadow_mode.py:88` | `ShadowModeService.get_shadow_report` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:30`<br>`s2p-copilot/backend/app/graph/s2p_graph_reader.py:32` | `S2PGraphReader._read` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/migration/s2p_entity_migration.py:505` | `_ensure_invoice_index` | Only known already-existing index error is accepted. | Other database exceptions propagate. |
| `s2p-copilot/backend/app/routers/financial_router.py:367` | `_ensure_financial_snapshots` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/framework_router.py:169` | `get_centroid_evolution` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/framework_router.py:488` | `auto_approve_stats` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/framework_router.py:534` | `graph_explorer_query` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/framework_router.py:602` | `graph_run_prebuilt` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:99` | `_get_conservation_status` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:336` | `export_audit_csv` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/s2p_control_tower.py:241`<br>`s2p-copilot/backend/app/routers/s2p_control_tower.py:243`<br>`s2p-copilot/backend/app/routers/s2p_control_tower.py:248` | `queue` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/s2p_enrichment_context.py:45` | `enrich_context` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:218` | `_conservation_snapshot` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:299` | `audit_trail` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:350` | `audit_pack` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:538` | `compliance` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:195` | `_current_conservation_status` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:573` | `contribution` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/s2p_governance.py:36` | `_safe_conservation_snapshot` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p_performance.py:178`<br>`s2p-copilot/backend/app/routers/s2p_performance.py:180` | `trajectory` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p_performance.py:203` | `what_if` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p_performance.py:235` | `summary` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/s2p_preview.py:163` | `_write_preview_observation_once` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/s2p_situation.py:41`<br>`s2p-copilot/backend/app/routers/s2p_situation.py:99` | `get_situation` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p.py:98` | `S2PScoreAuditWriter.begin_outcome` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/s2p.py:105` | `S2PScoreAuditWriter.finish_outcome` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/s2p.py:152` | `S2PScoreAuditWriter.record_outcome` | Raises/re-raises or translates into an explicit failure. | Caller receives failure; retries/rollback do not replace it with an empty success. |
| `s2p-copilot/backend/app/routers/s2p.py:1015` | `_link_decision_to_invoice` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p.py:1035` | `_has_decision_invoice_link` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p.py:1126` | `_current_conservation_status` | Returns UNKNOWN/unavailable state or blocks operation. | Failure is represented as an unknown/error state rather than measured no-data success. |
| `s2p-copilot/backend/app/routers/s2p.py:1686`<br>`s2p-copilot/backend/app/routers/s2p.py:1710` | `_append_evidence_receipt_before_outcome` | Receipt append failure returns receipt_queued=True; double failure raises 503. | Durable outbox fallback is explicitly represented, unlike an unreported dropped receipt. |
| `s2p-copilot/backend/app/routers/s2p.py:1879`<br>`s2p-copilot/backend/app/routers/s2p.py:1923` | `_learn_with_scorer` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p.py:2646` | `learn_decision` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/routers/s2p.py:2811`<br>`s2p-copilot/backend/app/routers/s2p.py:2815` | `record_outcome` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/services/budget_persistence.py:159` | `PersistentBudgetPolicy.allocate` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/services/situation_traversals.py:548` | `_read_enriched_properties` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |
| `s2p-copilot/backend/app/services/situation_traversals.py:662` | `_similar_decision` | Caught exception is re-raised or translated into an exception. | No successful empty-data return on these handler paths; the immediate caller receives an error. |

## Review coverage

The following inventory records every direct named-call candidate and supplemental candidate read end to end. “No local except” means no locally owned exception handler; it is not a claim that all downstream helpers propagate. “No finding listed” includes local parsing, non-graph HTTP/file operations, explicit error responses, and redundant outer handlers whose graph callee already catches the exception. Only the finding tables assert graph-error substitution. This inventory is not a runtime call graph.

| File:line | Function | Selection | Review result |
|---|---|---|---|
| `ci-platform/ci_platform/auth/saml.py:104` | `SAMLService.validate_response` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `ci-platform/ci_platform/auth/saml.py:152` | `SAMLService._parse_xml_only` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `ci-platform/ci_platform/connectors/sap.py:330` | `SAPODataConnector.write_update` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `ci-platform/ci_platform/connectors/sentinel.py:92` | `SentinelConnector.health_check` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `ci-platform/ci_platform/connectors/splunk.py:101` | `SplunkConnector.health_check` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `ci-platform/ci_platform/copilot_core/cache.py:176` | `EntityCache.get_or_load` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `ci-platform/ci_platform/copilot_core/counters.py:218` | `AGECounterStore.read_counter` | Named-call scan | No local except |
| `ci-platform/ci_platform/copilot_core/counters.py:444` | `AGECounterStore.reconcile_counter` | Named-call scan | No local except |
| `ci-platform/ci_platform/copilot_core/counters.py:519` | `AGECounterStore.get_counter_or_graph_truth` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_client.py:191` | `AGEClient._ensure_pool` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `ci-platform/ci_platform/graph/age_client.py:230` | `AGEClient._discard_warm_connection` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `ci-platform/ci_platform/graph/age_client.py:271` | `AGEClient.ensure_graph._do` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `ci-platform/ci_platform/graph/age_client.py:342` | `AGEClient.serialize_for_age` | Named-call scan | Excluded: AGE value serialization only |
| `ci-platform/ci_platform/graph/age_client.py:369` | `AGEClient._S` | Named-call scan | Excluded: AGE value serialization only |
| `ci-platform/ci_platform/graph/age_client.py:459` | `AGEClient._sync_execute` | Named-call scan | Legitimate handler paths listed |
| `ci-platform/ci_platform/graph/age_client.py:528` | `AGEClient._execute_cypher_on_connection` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_client.py:556` | `AGEClient._sync_transaction` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `ci-platform/ci_platform/graph/age_client.py:590` | `AGEClient.get_security_context` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_client.py:625` | `AGEClient.get_alert` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_client.py:636` | `AGEClient.get_pattern_count` | Named-call scan | P3 |
| `ci-platform/ci_platform/graph/age_client.py:653` | `AGEClient.get_sequence_count` | Named-call scan | P1 |
| `ci-platform/ci_platform/graph/age_client.py:680` | `AGEClient.get_cross_category_count` | Named-call scan | P1 |
| `ci-platform/ci_platform/graph/age_client.py:707` | `AGEClient._legacy_sequence_count` | Named-call scan | P1 |
| `ci-platform/ci_platform/graph/age_client.py:733` | `AGEClient._legacy_cross_category_count` | Named-call scan | P1 |
| `ci-platform/ci_platform/graph/age_client.py:759` | `AGEClient.count_verified_decisions` | Named-call scan | P3 |
| `ci-platform/ci_platform/graph/age_client.py:773` | `AGEClient.count_correct_decisions` | Named-call scan | P3 |
| `ci-platform/ci_platform/graph/age_client.py:788` | `AGEClient.count_decisions_by_category` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_client.py:810` | `AGEClient.compute_outcome_stats` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_client.py:859` | `AGEClient.create_decision_trace` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_client.py:989` | `AGEClient.create_evolution_event` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_client.py:1098` | `AGEClient.get_recent_evolution_events` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_client.py:1125` | `AGEClient.log_decision_distance` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_client.py:1187` | `AGETransaction.run_cypher` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_client.py:1200` | `get_graph_client` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:71` | `AGEGraphStoreTransaction.write_decision` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:74` | `AGEGraphStoreTransaction.write_outcome` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:80` | `AGEGraphStoreTransaction.write_outcome_and_update_centroid` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:92` | `AGEGraphStore.__init__` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:109` | `AGEGraphStore._run._target` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `ci-platform/ci_platform/graph/age_graph_store.py:122` | `AGEGraphStore._S` | Named-call scan | Excluded: AGE value quoting only |
| `ci-platform/ci_platform/graph/age_graph_store.py:133` | `AGEGraphStore._save_platform_state` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:152` | `AGEGraphStore._get_platform_state` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:173` | `AGEGraphStore._list_platform_state` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:188` | `AGEGraphStore._delete_platform_state` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:273` | `AGEGraphStore._l5_upsert_current` | Named-call scan | P2 |
| `ci-platform/ci_platform/graph/age_graph_store.py:742` | `AGEGraphStore._run_query` | Named-call scan | P1 |
| `ci-platform/ci_platform/graph/age_graph_store.py:751` | `AGEGraphStore.run_transaction` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:772` | `AGEGraphStore.write_decision` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:803` | `AGEGraphStore._write_decision_impl` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:997` | `AGEGraphStore.write_governed_decision` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1177` | `AGEGraphStore.write_outcome` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1212` | `AGEGraphStore.write_outcome_and_update_centroid` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1245` | `AGEGraphStore._write_outcome_and_update_centroid_impl` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1278` | `AGEGraphStore._write_outcome_impl` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1380` | `AGEGraphStore._raise_write_outcome_no_row` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1476` | `AGEGraphStore.write_observation` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1518` | `AGEGraphStore._ensure_domain_anchor` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1552` | `AGEGraphStore._link_domain_summary` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1575` | `AGEGraphStore._link_checkpoint_edges` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1608` | `AGEGraphStore._link_transfer_edges` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1654` | `AGEGraphStore.write_conservation_status` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1721` | `AGEGraphStore._get_conservation_status_payload` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1751` | `AGEGraphStore.write_fingerprint` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1806` | `AGEGraphStore._get_fingerprint_payload` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1876` | `AGEGraphStore._write_centroid_checkpoint_impl` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:1976` | `AGEGraphStore._get_centroid_checkpoint_payload` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2040` | `AGEGraphStore.get_checkpoint_lineage` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2058` | `AGEGraphStore.get_decision_checkpoints` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2077` | `AGEGraphStore.ensure_snapshot_after_edges` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2166` | `AGEGraphStore.append_evidence_receipt` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2344` | `AGEGraphStore.write_evolution_event` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2410` | `AGEGraphStore._link_evolution_decision` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2439` | `AGEGraphStore.write_transfer_pattern` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2539` | `AGEGraphStore.get_transfer_patterns` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2577` | `AGEGraphStore.get_latest_conservation_statuses` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2601` | `AGEGraphStore.get_iks_trajectory` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2651` | `AGEGraphStore._get_evolution_event_payload` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2685` | `AGEGraphStore.link_entity` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2773` | `AGEGraphStore.get_decision` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2809` | `AGEGraphStore.get_decisions` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2831` | `AGEGraphStore.get_verified_decisions` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2847` | `AGEGraphStore.count_verified` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2852` | `AGEGraphStore.count_verified_decisions` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2865` | `AGEGraphStore.count_correct` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2879` | `AGEGraphStore.count_decisions` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2890` | `AGEGraphStore.count_categories_with_n` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:2965` | `AGEGraphStore.get_centroids` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3081` | `AGEGraphStore.get_dk_weights` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3222` | `AGEGraphStore.get_conservation_state` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3291` | `AGEGraphStore.get_all_decisions` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3305` | `AGEGraphStore.get_archived_decisions` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3330` | `AGEGraphStore.save_centroids` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3371` | `AGEGraphStore.load_latest_centroids` | Named-call scan | P3 |
| `ci-platform/ci_platform/graph/age_graph_store.py:3394` | `AGEGraphStore.save_evolution_event` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3416` | `AGEGraphStore.link_decision_to_entity` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3449` | `AGEGraphStore.get_decision_links` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3548` | `AGEGraphStore.get_centroid_checkpoints` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3583` | `AGEGraphStore.load_latest_checkpoint_for_regime` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3610` | `AGEGraphStore.get_evolution_events` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3706` | `AGEGraphStore.archive_old_decisions` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3766` | `AGEGraphStore.count_archived` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3777` | `AGEGraphStore.archive_decisions` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3834` | `AGEGraphStore.domain_scoped_reset` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3975` | `AGEGraphStore.query_context` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:3998` | `AGEGraphStore.decision_movement` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:4025` | `AGEGraphStore.contextual_judgment` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:4039` | `AGEGraphStore.promotion_basis` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:4052` | `AGEGraphStore.transfer_witness` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:4082` | `AGEGraphStore.list_fingerprints` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:4099` | `AGEGraphStore.query_cross_domain_context` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:4133` | `AGEGraphStore.query_similar` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:4151` | `AGEGraphStore.close` | Named-call scan | No graph-swallow finding listed |
| `ci-platform/ci_platform/graph/age_graph_store.py:4211` | `AGEGraphStore.write_entity_enrichment` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_graph_store.py:4322` | `AGEGraphStore.read_entity_enrichment` | Named-call scan | P3 |
| `ci-platform/ci_platform/graph/age_graph_store.py:4360` | `AGEGraphStore.list_entity_enrichments` | Named-call scan | P3 |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:32` | `AGEGraphStoreAdapter.write_decision` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:86` | `AGEGraphStoreAdapter.write_outcome` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:266` | `AGEGraphStoreAdapter.get_decision_checkpoints` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:316` | `AGEGraphStoreAdapter.get_decision` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:329` | `AGEGraphStoreAdapter.get_decisions` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:340` | `AGEGraphStoreAdapter.get_all_decisions` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:346` | `AGEGraphStoreAdapter.count_verified` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:349` | `AGEGraphStoreAdapter.count_verified_decisions` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:355` | `AGEGraphStoreAdapter.count_decisions` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:466` | `AGEGraphStoreAdapter.save_centroids` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:500` | `AGEGraphStoreAdapter.save_posterior` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:503` | `AGEGraphStoreAdapter.get_posterior` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:548` | `AGEGraphStoreAdapter.load_latest_centroids` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:559` | `AGEGraphStoreAdapter.get_centroid_checkpoints` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:672` | `AGEGraphStoreAdapter.get_decision_links` | Named-call scan | No local except |
| `ci-platform/ci_platform/graph/age_sdk_adapter.py:684` | `AGEGraphStoreAdapter.query_context` | Named-call scan | No local except |
| `ci-platform/ci_platform/onboarding/pipeline.py:94` | `OnboardingPipeline.run` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `ci-platform/ci_platform/redaction/pii_redactor.py:136` | `PIIRedactor._run_ner` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `ci-platform/ci_platform/strategy/two_phase_strategy.py:24` | `TwoPhaseStrategy.get_phase` | Supplemental wrapper/handler review | P1 |
| `ci-platform/ci_platform/strategy/two_phase_strategy.py:34` | `TwoPhaseStrategy.get_status` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `ci-platform/ci_platform/strategy/two_phase_strategy.py:58` | `TwoPhaseStrategy._counts` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/ae_router.py:46` | `_events` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/dataops/backend/app/ae_router.py:387` | `create_ae_router.recommendation` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/connector_cache.py:56` | `ConnectorCache.fetch` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/connectors/dq_benchmark_provider.py:143` | `DQBenchmarkProvider.schema_for_entity` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:92` | `_graph_client` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:104` | `_decision_store` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:118` | `_graph_decisions` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:607` | `_audit_recommendation_for_alert` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:788` | `pipelines` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:799` | `enterprise_health` | Named-call scan | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:865` | `_safe_connector_health` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:874` | `alerts` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:885` | `alert_groups` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1128` | `transformations` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1186` | `schema_impact` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1215` | `process_timeline` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1377` | `system_detail` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1382` | `alert_detail` | Named-call scan | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1402` | `alert_deps` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1407` | `alert_recurrence` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1412` | `alert_factors` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1502` | `_process_connector_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/context_router.py:1519` | `audit_trail` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:25` | `DataOpsGovernance.__init__` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/dataops_governance.py:128` | `DataOpsGovernance.provenance` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/enterprise_router.py:116` | `_health_with_fallback` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/enterprise_router.py:131` | `_load_process` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/enterprise_router.py:161` | `_load_sap` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/graph_queries.py:61` | `_load_age_client_class` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/graph_queries.py:80` | `DataOpsGraphClient.__init__` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/dataops/backend/app/graph_queries.py:564` | `DataOpsGraphClient._run_graph` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/dataops/backend/app/graph_status.py:111` | `DataOpsActiveGraphConfig.from_env` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/graph_status.py:291` | `create_dataops_active_graph_store` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/main.py:181` | `_graph_store` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/main.py:192` | `_snowflake_connector` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/main.py:220` | `_dbt_connector` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/main.py:242` | `_airflow_connector` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/main.py:289` | `_profile_dataops_sources` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/main.py:367` | `_selected_graph_store_factory` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/main.py:442` | `_seed_from_fixtures` | Named-call scan | P2 |
| `copilot-sdk/apps/dataops/backend/app/main.py:508` | `_auto_seed_if_needed` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/dataops/backend/app/main.py:532` | `_seed_demo_evolution_events_if_needed` | Named-call scan | P2 |
| `copilot-sdk/apps/dataops/backend/app/main.py:589` | `_evolution_variants` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/main.py:613` | `create_app` | Named-call scan | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/main.py:993` | `create_app.investigate_dataops_alert` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/routers/cohort_status_router.py:20` | `create_cohort_status_router.get_cohort_status` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/routers/dataops_status.py:69` | `enterprise_health_alias` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/routers/dataops_status.py:82` | `_enterprise_sap_health` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/routers/dataops_status.py:94` | `_enterprise_celonis_health` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/routers/dataops_status.py:106` | `_enterprise_graph_health` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/dataops/backend/app/routers/di_demo_beats.py:31` | `create_di_demo_beats_router.conservation` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/routers/di_gateway_router.py:23` | `create_di_gateway_router.verification_history` | Named-call scan | No local except |
| `copilot-sdk/apps/dataops/backend/app/routers/perturbation_router.py:34` | `create_perturbation_router.perturb` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/routers/query.py:30` | `create_query_router.query` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/dataops/backend/app/routers/regime_router.py:36` | `_payload` | Supplemental wrapper/handler review | P3 |
| `copilot-sdk/apps/dataops/backend/app/routers/trust_perturbation_router.py:100` | `create_trust_perturbation_router.perturb` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/routers/trust_perturbation_router.py:116` | `create_trust_perturbation_router.reset` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/routers/trust_perturbation_router.py:151` | `_conservation_status` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/routers/trust_router.py:23` | `create_trust_router.trust_profile` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/services/cohort_status.py:136` | `DataOpsCohortStatus._read_decisions` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/dataops/backend/app/services/graph_enrichment.py:91` | `_run_graph_query` | Named-call scan | No graph-swallow finding listed |
| `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:345` | `_pipelines` | Named-call scan | P1 |
| `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:358` | `_blast_radius` | Named-call scan | P1 |
| `copilot-sdk/apps/dataops/backend/app/services/investigation_patterns.py:372` | `_recurrence` | Named-call scan | P1 |
| `copilot-sdk/apps/purchasing/backend/app/connectors/commodity_provider.py:114` | `CommodityDataProvider.warm_cache` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/connectors/commodity_provider.py:156` | `CommodityDataProvider._fetch_with_single_flight` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/connectors/commodity_source.py:58` | `FREDCommoditySource.fetch_category_prices` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/connectors/commodity_source.py:116` | `FREDCommoditySource._frozen_prices` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/connectors/qbo_connector.py:167` | `QBOConnector._request` | Named-call scan | Excluded: QuickBooks authentication client, not graph |
| `copilot-sdk/apps/purchasing/backend/app/context_router.py:76` | `_evolution_variants` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/purchasing/backend/app/evidence_providers.py:64` | `_domain_context` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/purchasing/backend/app/evidence_providers.py:151` | `FactorEvidenceProvider.read_payload` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/graph_status.py:112` | `PurchasingActiveGraphConfig.from_env` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/graph_status.py:337` | `create_purchasing_active_graph_store` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/main.py:216` | `_graph_store` | Named-call scan | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/main.py:252` | `_fred_commodity_source` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/main.py:309` | `_seed_from_fixtures` | Named-call scan | P2 |
| `copilot-sdk/apps/purchasing/backend/app/main.py:372` | `_auto_seed_if_needed` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/purchasing/backend/app/main.py:415` | `_evolution_variants` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/purchasing/backend/app/main.py:478` | `create_app` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/main.py:517` | `create_app.selected_graph_store_factory` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/main.py:591` | `create_app._run_startup_locked` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/main.py:635` | `create_app._graph_order_rows` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/main.py:655` | `create_app._conservation_status` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/main.py:668` | `create_app._alert_conservation_status` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/purchasing/backend/app/main.py:682` | `create_app.waste_analysis` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/main.py:688` | `create_app.waste_summary` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/main.py:693` | `create_app.predictive_par` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/main.py:705` | `create_app.predictive_par_week` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/routers/auto_order_router.py:58` | `create_auto_order_router.evaluate_order` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/auto_order_router.py:147` | `_category_verified_decisions` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/routers/cohort_status_router.py:20` | `create_cohort_status_router.get_cohort_status` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:25` | `create_evidence_router.evidence_summary` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:54` | `create_evidence_router.evidence_decisions` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:71` | `create_evidence_router.audit_trail` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:97` | `create_evidence_router.conservation_proof` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:166` | `_all_decisions` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:176` | `_verified_decisions` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:186` | `_centroid_checkpoints` | Named-call scan | P1 |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:197` | `_trajectory` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:214` | `_count` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/purchasing/backend/app/routers/evidence.py:370` | `_json_safe` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/iks.py:23` | `create_iks_router.iks_summary` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/iks.py:39` | `create_iks_router.supplier_scorecard` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/routers/iks.py:49` | `_graph_store` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/iks.py:61` | `_supplier_rows_from_graph` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py:93` | `create_learning_beats_router.proof_ledger` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py:143` | `_verified` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/purchasing/backend/app/routers/learning_beats.py:154` | `_stats` | Named-call scan | P1 |
| `copilot-sdk/apps/purchasing/backend/app/routers/match.py:542` | `_write_match_decision` | Named-call scan | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/par_router.py:27` | `create_par_router._orders` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py:34` | `_default_toast_connector` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py:69` | `create_pos_router.pos_today` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/pos_router.py:100` | `create_pos_router.pos_profile` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py:17` | `_default_qbo_connector` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/qbo_router.py:78` | `create_qbo_router.get_status` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/queue.py:188` | `_queue_scorer` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/purchasing/backend/app/routers/queue.py:203` | `_score_read_only` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/queue.py:331` | `_conservation_status` | Named-call scan | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/regime_router.py:36` | `_payload` | Supplemental wrapper/handler review | P3 |
| `copilot-sdk/apps/purchasing/backend/app/routers/scorecard_router.py:59` | `build_iks_summary` | Named-call scan | P1 |
| `copilot-sdk/apps/purchasing/backend/app/routers/scorecard_router.py:120` | `_verified_decisions` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/routers/trust_router.py:149` | `_decisions_total` | Named-call scan | P1 |
| `copilot-sdk/apps/purchasing/backend/app/routers/verify_router.py:75` | `create_verify_router.verify` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/purchasing/backend/app/routers/verify_router.py:202` | `_record_paused_outcome` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/services/alert_engine.py:94` | `PurchasingAlertEngine._supplier_degradation` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/services/alert_engine.py:128` | `PurchasingAlertEngine._stockout_risk` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/services/cohort_status.py:192` | `PurchasingCohortStatus._read_decisions` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/purchasing/backend/app/services/commodity_data_provider.py:103` | `CommodityDataProvider._resolve` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/services/economic_model.py:177` | `PurchasingEconomicModel._read_cost_source` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/services/predictive_par.py:141` | `PredictivePar.base_from_optimizer` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:68` | `PurchasingClaimRegistry.refresh` | Named-call scan | P1 |
| `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:155` | `PurchasingControlService.__init__` | Named-call scan | No graph-swallow finding listed |
| `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:179` | `PurchasingControlService._store` | Named-call scan | No local except |
| `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:189` | `PurchasingControlService._decisions` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/purchasing/backend/app/services/purchasing_control.py:197` | `PurchasingControlService._verified` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/brokers/alpaca.py:85` | `AlpacaBroker._request` | Named-call scan | Excluded: Alpaca HTTP client, not graph |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py:95` | `_get_scorer` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py:120` | `_close_scorer` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py:286` | `learn_sdk` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py:361` | `_counts` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py:434` | `conservation_sdk` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py:459` | `status_sdk` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py:497` | `journal_sdk` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py:530` | `export_sdk` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py:586` | `restore_sdk` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py:617` | `import_sdk` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/cli_sdk.py:836` | `_run_json_command` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/connectors/alpaca_connector.py:30` | `AlpacaConnector.test_connection` | Named-call scan | Excluded: Alpaca client initialization, not graph |
| `copilot-sdk/apps/trading/backend/app/connectors/alpaca_connector.py:38` | `AlpacaConnector.import_trades` | Named-call scan | Excluded: Alpaca trade provider, not graph |
| `copilot-sdk/apps/trading/backend/app/connectors/ibkr_connector.py:37` | `IBKRConnector.connect` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/connectors/ibkr_connector.py:46` | `IBKRConnector.disconnect` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/connectors/ibkr_connector.py:53` | `IBKRConnector.test_connection` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/connectors/ibkr_connector.py:85` | `IBKRConnector.fetch_historical` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/connectors/ibkr_connector.py:216` | `_stock_contract` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/connectors/market_source.py:38` | `YFinanceSource.fetch_ohlcv` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/connectors/market_source.py:61` | `YFinanceSource.fetch_vix` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/connectors/market_source.py:72` | `YFinanceSource.fetch_info` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/connectors/market_source.py:81` | `YFinanceSource.fetch_batch_history` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/connectors/yfinance_provider.py:10` | `YFinanceProvider.get_ohlcv` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/context_router.py:212` | `_trading_conservation_config` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/context_router.py:302` | `market_snapshot` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/context_router.py:335` | `ticker_detail` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/context_router.py:375` | `_analytics_from_store` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/evidence_provider.py:76` | `TradingEvidenceProvider._read_from_data_source` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/evidence_providers.py:65` | `_domain_context` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/trading/backend/app/evidence_providers.py:142` | `FactorEvidenceProvider.read_payload` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/evidence.py:59` | `_load_factor_polarities` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/factors/market_regime.py:31` | `classify_regime_context` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/factors/options.py:63` | `_IVRVRatioFactorLegacy.compute` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/factors/options.py:86` | `_IVRVRatioFactorLegacy._fetch_iv_rv` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/factors/options.py:208` | `compute_options_factors` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/factors/options.py:220` | `_fetch_quant_ivrv_context` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/factors/options.py:245` | `_option_chain_payload` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/factors/registry.py:77` | `compute_factors` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/graph_status.py:109` | `TradingActiveGraphConfig.from_env` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/graph_status.py:306` | `create_trading_active_graph_store` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/main.py:175` | `_graph_store` | Named-call scan | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/main.py:272` | `_seed_from_fixtures` | Named-call scan | P2 |
| `copilot-sdk/apps/trading/backend/app/main.py:336` | `_auto_seed_if_needed` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/trading/backend/app/main.py:359` | `create_app` | Named-call scan | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/main.py:392` | `create_app.selected_graph_store_factory` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/main.py:492` | `create_app._run_startup_locked` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/main.py:625` | `create_app.query_journal` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/routers/analytics.py:113` | `_verified_decisions` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/routers/analytics.py:246` | `_centroid_vectors` | Named-call scan | P3 |
| `copilot-sdk/apps/trading/backend/app/routers/analytics.py:269` | `_coerce_category_centroid` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/broker_router.py:185` | `create_broker_router.broker_orders` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/claim_gate_router.py:21` | `create_claim_gate_router.claim_gate` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/routers/cohort_status_router.py:21` | `create_cohort_status_router.get_cohort_status` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/routers/data_import.py:119` | `create_data_import_router.import_broker` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/evidence.py:76` | `_with_saved_metadata` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:207` | `_current_conservation_status` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/trading/backend/app/routers/execution_router.py:26` | `create_execution_router._trades` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/trading/backend/app/routers/journal.py:92` | `create_journal_router.create_manual_entry` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/journal.py:129` | `create_journal_router.update_reflection` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/journal.py:145` | `create_journal_router.update_tags` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/journal.py:199` | `_journal_records` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/trading/backend/app/routers/pre_score_router.py:49` | `create_pre_score_router.pre_score` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/routers/promotion_router.py:50` | `create_promotion_engine_router._engine` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/routers/promotion_router.py:75` | `create_promotion_engine_router.promote` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/promotion_router.py:120` | `_conservation_status` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/apps/trading/backend/app/routers/promotion.py:85` | `_conservation_status` | Named-call scan | P1 |
| `copilot-sdk/apps/trading/backend/app/routers/regime_analytics.py:38` | `_read_decisions` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/routers/regime_router.py:64` | `create_regime_router.regime_performance` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/routers/regime_router.py:86` | `create_regime_router.regime_recommendation` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/routers/regime_router.py:100` | `_current_market` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/regime_router.py:151` | `_conservation_status` | Named-call scan | P1 |
| `copilot-sdk/apps/trading/backend/app/routers/regime.py:123` | `_regime_break_active` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/regime.py:132` | `_conservation_status` | Named-call scan | P1 |
| `copilot-sdk/apps/trading/backend/app/routers/social.py:71` | `create_social_router.score_as` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/social.py:100` | `_json_safe` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/webhook.py:246` | `_score_event` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/webhook.py:295` | `_current_regime_from_indicators` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/routers/webhook.py:403` | `_json_safe` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/claim_gate.py:93` | `TradingClaimRegistry.refresh_from_store` | Named-call scan | P1 |
| `copilot-sdk/apps/trading/backend/app/services/cohort_status.py:145` | `TradingCohortStatus._read_decisions` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/trading/backend/app/services/correlation.py:81` | `CorrelationService._fetch_returns` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/correlation.py:173` | `CorrelationService._quant_alert` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/market_data_provider.py:137` | `MarketDataProvider._resolve` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/pre_scorer.py:170` | `PreScorer._current_regime` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/regime_recommender.py:167` | `_historical_vix` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/regime_scoring.py:301` | `_adjusted_learning_pause` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/regime.py:44` | `_classify_regime_details` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/regime.py:70` | `compute_adx` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/regime.py:94` | `RegimeService.get_current_regime` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/regime.py:179` | `RegimeService._batch_vix_lookup` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/regime.py:224` | `RegimeService._current_regime_from_provider` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/trader_profiles.py:79` | `TraderProfileService._verified_decisions` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/trading/backend/app/services/trading_evolver.py:132` | `_VariantRule._record_shadow_read` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/apps/trading/backend/app/services/trust_analysis.py:167` | `TrustAnalyzer._decisions_until_dk` | Named-call scan | P1 |
| `copilot-sdk/apps/trading/backend/app/state/compute_helpers.py:24` | `compute_all_decisions` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/state/compute_helpers.py:41` | `compute_history_summary` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/state/compute_helpers.py:207` | `compute_promotion_dashboard` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/state/compute_helpers.py:257` | `count_decisions` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/apps/trading/backend/app/state/compute_helpers.py:287` | `safe_call` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/apps/trading/backend/app/state/trading_registry.py:47` | `create_trading_tab_state_cache` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/state/trading_registry.py:58` | `create_trading_tab_state_cache.graph_store` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/state/trading_registry.py:64` | `create_trading_tab_state_cache.centroid_history_summary` | Named-call scan | No local except |
| `copilot-sdk/apps/trading/backend/app/vld_preseed.py:59` | `seed_vld_trading_showcase` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/ae/store.py:20` | `EvolutionStore.save_variant` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/ae/store.py:23` | `EvolutionStore.get_variant` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/ae/store.py:26` | `EvolutionStore.list_variants` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/ae/store.py:29` | `EvolutionStore.delete_variant` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/ae/store.py:32` | `EvolutionStore.save_fitness` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/ae/store.py:35` | `EvolutionStore.save_promotion` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/auth/middleware.py:12` | `AuthMiddleware.__call__` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/coalesced_read.py:18` | `CoalescedRead.run` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/conservation_router.py:45` | `create_conservation_router.status` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/conservation_router.py:110` | `create_conservation_router.what_if` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/conservation_utils.py:147` | `_baseline_q` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/conservation_utils.py:315` | `state_counts` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/counterfactual_router.py:55` | `create_counterfactual_router.counterfactual` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/di_router.py:273` | `create_di_router.query` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:104` | `_count_rows` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:196` | `_unwrap_scorer` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:219` | `_artifact_count` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:276` | `_safe_cypher_count` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/diagnostics_models.py:300` | `build_diagnostics` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py:55` | `create_evolution_router._get_evolver` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py:144` | `create_evolution_router.summary` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py:222` | `_provided_variants` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py:240` | `_variant_stats` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py:351` | `_read_conservation_payload` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/evolution_router.py:364` | `_recent_evolution_events` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/health_builder.py:10` | `build_graph_health` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/investigation_router.py:58` | `create_investigation_router.investigate` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/investigation_router.py:210` | `_category_index` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/scorer_proxy.py:17` | `FreshScorerProxy.__init__` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:161` | `create_scoring_router.get_scorer` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:211` | `create_scoring_router.score` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:222` | `create_scoring_router.score_sync` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:252` | `create_scoring_router.learn` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:396` | `create_scoring_router.diagnostics` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:414` | `create_scoring_router.history` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:547` | `_get_decision` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:588` | `_persist_conservation_state_l5_locked` | Supplemental wrapper/handler review | P2 |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:678` | `_persist_centroid_l5` | Supplemental wrapper/handler review | P2 |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:744` | `_read_centroid_for_l5` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:781` | `_persist_dk_state_l5` | Supplemental wrapper/handler review | P2 |
| `copilot-sdk/copilot_sdk/backend/scoring_router.py:941` | `_score_response_payload` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:61` | `create_self_computation_router._gs` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:113` | `create_self_computation_router.centroid_history` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:248` | `create_self_computation_router.counterfactual` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:392` | `create_self_computation_router.replay_score` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:437` | `create_self_computation_router.decision_checkpoints` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:495` | `create_self_computation_router.rollback` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:505` | `create_self_computation_router.decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:549` | `create_self_computation_router.audit_trail` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:577` | `create_self_computation_router.decision_flow` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:678` | `_get_all_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:686` | `_count_verified` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:702` | `_get_centroid_checkpoints` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:711` | `_find_checkpoint` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/self_computation_router.py:930` | `_json_safe` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/backend/signal_store.py:142` | `GraphSignalStore._records` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/signal_store.py:160` | `GraphSignalStore.publish` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/switching_cost_router.py:30` | `_decision_records` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/switching_cost_router.py:41` | `_decision_count` | Named-call scan | P3 |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:58` | `create_transfer_router.transfer_opportunities` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:91` | `create_transfer_router.transfer_demo` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:207` | `_pattern_dollar_impact` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:245` | `create_self_transfer_router.list_transfers` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:273` | `create_self_transfer_router.transfer` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:379` | `_latest_checkpoint_info` | Named-call scan | P1 |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:496` | `_target_conservation_state` | Named-call scan | P1 |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:548` | `_source_conservation_state` | Named-call scan | P1 |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:638` | `_reset_conservation_state` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:680` | `_source_store_for_domain` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/copilot_sdk/backend/transfer_router.py:693` | `_save_transfer_checkpoint` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/transfer.py:25` | `save_fingerprint` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/backend/transfer.py:74` | `load_fingerprints_with_warnings` | Named-call scan | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/config/graph_config.py:242` | `GraphConfig._read_file` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/config/graph_config.py:362` | `_as_int` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/demo/bundle.py:20` | `restore_bundle_if_empty` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/demo/bundle.py:43` | `_restore` | Named-call scan | P2, P1 |
| `copilot-sdk/copilot_sdk/demo/bundle.py:197` | `_sqlite_connection` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/demo/connector_freeze.py:72` | `ConnectorFreeze._live_fred_rows` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/di/claude_parser.py:32` | `ClaudeQueryParser.parse` | Named-call scan | Excluded: Anthropic messages client, not graph |
| `copilot-sdk/copilot_sdk/di/claude_parser.py:76` | `ClaudeQueryParser._validate_plan` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/di/enrichment.py:282` | `BaseGraphEnricher._persist_entity_enrichment` | Named-call scan | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/di/enrichment.py:329` | `BaseGraphEnricher._read_verified_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/di/integrator.py:138` | `SourceIntegrator._trust_weights` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/di/nl_query.py:81` | `_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/di/perturbation.py:154` | `_fingerprint_factors` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/di/profiler.py:26` | `BaseSourceProfiler.profile` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/di/query_providers.py:112` | `GraphStoreProvider._decisions` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/di/query_providers.py:202` | `DataOpsEnterpriseProvider._decision_invoice_ids` | Supplemental wrapper/handler review | P3 |
| `copilot-sdk/copilot_sdk/di/query_service.py:74` | `DIQueryService.parse` | Named-call scan | Excluded: query_context is an input mapping helper; Claude parser only |
| `copilot-sdk/copilot_sdk/di/query_service.py:215` | `DIQueryService.execute` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/di/search_service.py:118` | `DISearchService._freshness_hours` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/diagnostics/platform_dump.py:34` | `_collect_copilot_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/diagnostics/platform_dump.py:59` | `_collect_age_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/diagnostics/platform_dump.py:174` | `collect_platform_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/discovery/engine.py:43` | `DiscoveryEngine.sweep` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/discovery/patterns.py:220` | `_safe_phase` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/evidence/gate.py:52` | `_coerce_tier` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/evolution/conservation_contract.py:90` | `ScorerBackedProvider.get_state` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/evolution/conservation_contract.py:135` | `CachedAsyncProvider.get_state` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/evolution/evolver.py:49` | `AgentEvolver.evolve` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/evolution/graph_store.py:153` | `GraphVariantStore.register_variant` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/evolution/graph_store.py:219` | `GraphVariantStore.record_outcome` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/evolution/graph_store.py:231` | `GraphVariantStore.update_variant_status` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/evolution/graph_store.py:243` | `GraphVariantStore.reset` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/evolution/graph_store.py:265` | `GraphPromotionStore.save` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/evolution/graph_store.py:270` | `GraphPromotionStore._records` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/evolution/graph_store.py:299` | `GraphOutcomeLedger.append` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/evolution/graph_store.py:342` | `GraphProofLedger.record` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/evolution/graph_store.py:350` | `GraphProofLedger.list_entries` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/evolution/ledger.py:34` | `InMemoryEvolutionLedger.append` | Supplemental wrapper/handler review | P2 |
| `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:308` | `PromptVariantEvolver._resolve_conservation_state` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/evolution/shadow.py:16` | `DefaultShadowRunner.run_shadow` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/framework/audit.py:242` | `rebuild_chain_from_graph` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/framework/audit.py:293` | `rebuild_from_age` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/framework/checkpoint.py:28` | `CheckpointService.create_checkpoint` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/framework/checkpoint.py:87` | `CheckpointService.list_checkpoints` | Named-call scan | P1 |
| `copilot-sdk/copilot_sdk/framework/checkpoint.py:113` | `CheckpointService.rollback` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/framework/composite_gate.py:62` | `CompositeDiscriminant.evaluate` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/framework/decision_history.py:22` | `DecisionHistoryService.get_category_stats` | Named-call scan | P1 |
| `copilot-sdk/copilot_sdk/framework/event_bus.py:96` | `EventBus.emit` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/framework/intervention_controls.py:107` | `InterventionControls.rollback` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/framework/intervention_controls.py:252` | `InterventionControls.get_current_state` | Named-call scan | P1 |
| `copilot-sdk/copilot_sdk/framework/intervention_controls.py:286` | `InterventionControls.get_intervention_history` | Named-call scan | P1 |
| `copilot-sdk/copilot_sdk/framework/intervention_controls.py:329` | `InterventionControls._log_intervention` | Named-call scan | P2 |
| `copilot-sdk/copilot_sdk/framework/learning_state.py:59` | `load_from_file` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/framework/learning_state.py:112` | `save_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/framework/provenance.py:287` | `ProvenanceService.get_provenance_from_graph` | Named-call scan | P1 |
| `copilot-sdk/copilot_sdk/framework/shadow_mode.py:27` | `ShadowModeService.record_shadow_decision` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/framework/shadow_mode.py:51` | `ShadowModeService.record_analyst_action` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/framework/shadow_mode.py:74` | `ShadowModeService.get_shadow_report` | Named-call scan | P1 |
| `copilot-sdk/copilot_sdk/framework/similar_cases_base.py:61` | `SimilarCasesBase._fetch_verified_decisions` | Named-call scan | P1 |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:182` | `DualWriteStore._append_outbox_entry` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:234` | `DualWriteStore._replay_outbox_locked` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:289` | `DualWriteStore._write` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:304` | `DualWriteStore.write_decision` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:388` | `DualWriteStore.save_centroids` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:413` | `DualWriteStore.get_decision` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:422` | `DualWriteStore.save_posterior` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:423` | `DualWriteStore.get_posterior` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:438` | `DualWriteStore.get_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:439` | `DualWriteStore.get_all_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:442` | `DualWriteStore.count_verified` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:444` | `DualWriteStore.count_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:445` | `DualWriteStore.load_latest_centroids` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:446` | `DualWriteStore.get_centroid_checkpoints` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:449` | `DualWriteStore.get_decision_checkpoints` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:453` | `DualWriteStore.count_verified_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/dual_write_store.py:491` | `DualWriteStore.close` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/graph/factory.py:111` | `create_graph_store` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/graph/memory_store.py:489` | `InMemoryGraphStore.write_governed_decision` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/memory_store.py:1227` | `InMemoryGraphStore.get_all_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/memory_store.py:1252` | `InMemoryGraphStore.count_verified` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/memory_store.py:1452` | `InMemoryGraphStore.save_centroids` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/memory_store.py:1630` | `InMemoryGraphStore.load_latest_checkpoint_for_regime` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/memory_store.py:1657` | `InMemoryGraphStore.get_checkpoint_lineage` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/memory_store.py:2094` | `InMemoryGraphStore.query_context` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/memory_store.py:2194` | `InMemoryGraphStore.decision_movement` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/memory_store.py:2262` | `InMemoryGraphStore.query_similar` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/outcome_service.py:81` | `ProtocolV2OutcomeService._replay_locked` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/graph/outcome_service.py:106` | `ProtocolV2OutcomeService._commit` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/production.py:35` | `_probe_client_identity` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/graph/production.py:71` | `probe_graph_identity` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/production.py:102` | `validate_production_store` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/projection.py:257` | `AGEProjection._query` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/projection.py:326` | `AGEProjection.get_profile_snapshot` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/read_diff_runner.py:219` | `ReadDiffRunner._compare_active` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:396` | `SQLiteGraphStore.__init__` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1169` | `SQLiteGraphStore._run_write` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2567` | `SQLiteGraphStore.count_verified` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2918` | `SQLiteGraphStore.save_centroids.persist` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:2944` | `SQLiteGraphStore.load_latest_centroids` | Supplemental wrapper/handler review | P3 |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:3021` | `SQLiteGraphStore.load_latest_checkpoint_for_regime` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:3048` | `SQLiteGraphStore.get_checkpoint_lineage` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:3247` | `SQLiteGraphStore.query_context` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:3354` | `SQLiteGraphStore.decision_movement` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:3360` | `SQLiteGraphStore.contextual_judgment` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/sqlite_store.py:3432` | `SQLiteGraphStore.query_similar` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/tenant_store.py:48` | `TenantScopedGraphStore.write_decision` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/tenant_store.py:51` | `TenantScopedGraphStore.write_outcome` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/tenant_store.py:54` | `TenantScopedGraphStore.get_decision` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/tenant_store.py:68` | `TenantScopedGraphStore.get_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/tenant_store.py:71` | `TenantScopedGraphStore.get_all_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/tenant_store.py:89` | `TenantScopedGraphStore.count_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/tenant_store.py:144` | `TenantScopedGraphStore.save_posterior` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/tenant_store.py:147` | `TenantScopedGraphStore.get_posterior` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/tenant_store.py:181` | `TenantScopedGraphStore.get_centroid_checkpoints` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/tenant_store.py:184` | `TenantScopedGraphStore.load_latest_centroids` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/graph/tenant_store.py:191` | `TenantScopedGraphStore.save_centroids` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:127` | `ArchiveReconciler._age_rows` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/migrate/reconcile_archive.py:144` | `ArchiveReconciler._mark_archived` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/migrate/scratch_graph.py:76` | `create_scratch_graph` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/migrate/scratch_graph.py:93` | `drop_scratch_graph` | Supplemental wrapper/handler review | P2 |
| `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:99` | `ShadowScorer.score` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:128` | `ShadowScorer.learn` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:350` | `_category_coverage_alpha` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:389` | `_call_count` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:550` | `_write_batch` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/migrate/sqlite_to_age.py:946` | `run_migration` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/migrate/verify_state.py:134` | `_ReplayGraphStore.count_verified_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/migration/rehearsal.py:56` | `_existing` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/outbox/worker.py:47` | `OutboxWorker._process_batch_locked` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/outbox/worker.py:88` | `OutboxWorker._replay_locked` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/outcome/router.py:25` | `create_outcome_router.count` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/pilot/checks.py:30` | `FrozenTwinCheck.check` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/pilot/checks.py:45` | `EvidenceGateCheck.check` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/pilot/checks.py:64` | `PromotionRecordsCheck.check` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/pilot/checks.py:81` | `ConservationHealthCheck.check` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/pilot/checks.py:99` | `VerifiedCountCheck.check` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/pilot/checks.py:114` | `TruthPreflightCheck.check` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/pilot/gate.py:18` | `QualificationGate.run` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/promotion/core.py:363` | `PromotionEngine._conservation_status` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/reporting/weekly.py:88` | `WeeklyReportGenerator.generate` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/reporting/weekly.py:189` | `WeeklyReportGenerator._compute_cost_impact` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/reporting/weekly.py:260` | `WeeklyReportGenerator._read_conservation` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/reporting/weekly.py:270` | `WeeklyReportGenerator._compute_iks` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/copilot_sdk/rl/exploration.py:83` | `ConservationBoundedThompson._load_from_store` | Supplemental wrapper/handler review | P1, P3 |
| `copilot-sdk/copilot_sdk/rl/exploration.py:111` | `ConservationBoundedThompson._persist` | Supplemental wrapper/handler review | P2 |
| `copilot-sdk/copilot_sdk/scoring/composite_gate.py:76` | `outcomes_from_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/dk_persistence.py:231` | `persist_dk_after_reestimate` | Supplemental wrapper/handler review | P2 |
| `copilot-sdk/copilot_sdk/scoring/gate_enforced_scorer.py:97` | `GateEnforcedScorer._conservation_state` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/copilot_sdk/scoring/gate_enforced_scorer.py:125` | `GateEnforcedScorer._get_recent_outcomes` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/iks_service.py:45` | `IKSService._verified_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/investigation.py:199` | `VLDInvestigator.investigate` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/measurement_state.py:111` | `_verified_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/measurement_state.py:172` | `_current_iks` | Supplemental wrapper/handler review | P1 |
| `copilot-sdk/copilot_sdk/scoring/mutation_lock.py:75` | `_resolved_signature` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:247` | `PersistenceOutbox._drain_locked` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:319` | `PersistenceOutbox._replay` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/persistence_outbox.py:399` | `PersistenceOutbox.start_periodic_drain._drain_tick` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/presets/dataops.py:99` | `_load_bootstrap` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/presets/purchasing.py:105` | `_load_bootstrap` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/presets/trading.py:123` | `_load_bootstrap` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:125` | `CompoundingScorer.__init__` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:272` | `CompoundingScorer.from_preset` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:399` | `CompoundingScorer.score` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:748` | `CompoundingScorer.get_verified_count` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:752` | `CompoundingScorer.get_conservation_state` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:837` | `CompoundingScorer.reinitialize_from_regime` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:983` | `CompoundingScorer.learn` | Named-call scan | P2; separate legitimate paths listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1289` | `CompoundingScorer._record_persistence_failure` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1310` | `CompoundingScorer._persist_conservation_snapshot` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1387` | `CompoundingScorer._persist_learning_artifacts` | Named-call scan | P2 |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1414` | `CompoundingScorer._persist_learning_artifacts.load_decision` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1510` | `CompoundingScorer.capture_existing_state` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1656` | `CompoundingScorer._persist_evidence_receipt` | Named-call scan | P2 |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1709` | `CompoundingScorer._persist_fingerprint` | Named-call scan | P2 |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1795` | `CompoundingScorer.flush_centroids` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1823` | `CompoundingScorer.trajectory` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1841` | `CompoundingScorer.rollback_to_checkpoint` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1929` | `CompoundingScorer.get_phase` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1938` | `CompoundingScorer.get_alpha` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:1946` | `CompoundingScorer.warm_start` | Named-call scan | P2 |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2122` | `CompoundingScorer.export` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2147` | `CompoundingScorer._compute_iks` | Named-call scan | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2202` | `CompoundingScorer._checkpoint_quality` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2231` | `CompoundingScorer._refresh_dk_after_learn` | Supplemental wrapper/handler review | P2 |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2240` | `CompoundingScorer._conservation_pause` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2344` | `CompoundingScorer._read_conservation_inputs_with_retry` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2433` | `CompoundingScorer._save_centroids_checkpoint` | Named-call scan | P2 |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2547` | `CompoundingScorer._maybe_archive` | Named-call scan | P2 |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2594` | `CompoundingScorer._setup_evolution` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2634` | `CompoundingScorer._run_evolution` | Named-call scan | P2 |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2654` | `CompoundingScorer._evolution_conservation_state` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2717` | `CompoundingScorer._verified_decisions` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2737` | `CompoundingScorer.close` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2753` | `_conservation_dispersion` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:2843` | `_conservation_stats` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/scoring/scorer.py:3004` | `_is_conservation_read_error` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/startup_restore.py:53` | `_capture_existing_state` | Supplemental wrapper/handler review | P2 |
| `copilot-sdk/copilot_sdk/scoring/startup_restore.py:89` | `_restore_dk` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/startup_restore.py:142` | `_restore_centroids` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/startup_restore.py:237` | `_restore_conservation` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/scoring/verification/price.py:84` | `_fetch_live_price` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/verification/weather.py:68` | `_frozen_weather` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/scoring/verification/weather.py:85` | `_fetch_live_weather` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/situation/templates.py:56` | `SafeTemplateRenderer.render` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/state/cached_static.py:50` | `cached_static.deco.async_wrapper` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/state/cached_static.py:73` | `cached_static.deco.sync_wrapper` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/state/invalidation.py:70` | `apply_cache_invalidation_event` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/state/tab_state_cache.py:320` | `TabStateCache._compute_and_store` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/state/tab_state_cache.py:366` | `TabStateCache._compute_and_store_sync` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `copilot-sdk/copilot_sdk/testing/fixtures.py:23` | `age_available` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `copilot-sdk/copilot_sdk/testing/fixtures.py:64` | `test_scorer` | Named-call scan | Excluded: SDK testing fixture, not production runtime |
| `copilot-sdk/copilot_sdk/transfer/cross_domain.py:95` | `CrossDomainTraversal.insights` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/twin/store.py:73` | `GraphFrozenTwinStore.save` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/twin/store.py:85` | `GraphFrozenTwinStore.load` | Named-call scan | No local except |
| `copilot-sdk/copilot_sdk/twin/store.py:97` | `GraphFrozenTwinStore.exists` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/celonis.py:42` | `CelonisConnector.fetch` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/crowdstrike_mock.py:96` | `CrowdStrikeMockConnector.refresh` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py:112` | `_fetch_greynoise` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py:192` | `GreyNoiseConnector.refresh` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py:208` | `GreyNoiseConnector.refresh.existing_observation` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:165` | `_fetch_pulsedive` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:261` | `PulsediveConnector.refresh` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:277` | `PulsediveConnector.refresh.existing_observation` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/registry.py:79` | `ConnectorRegistry.refresh_all` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/registry.py:107` | `ConnectorRegistry.health_check_all` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sap.py:43` | `SAPConnector.fetch` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sentinel_real.py:108` | `_normalize_sentinel_alert` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sentinel_real.py:226` | `SentinelRealConnector.get_token` | Named-call scan | Excluded: MSAL authentication client, not AGE/GraphStore |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sentinel_real.py:257` | `SentinelRealConnector.push_incident_update` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/sentinel_real.py:339` | `SentinelRealConnector.fetch_alerts` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/connectors/threat_intel_provider.py:95` | `ThreatIntelProvider._cascade` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/data/alert_pool.py:388` | `seed_simulation_alerts` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:57` | `_campaign_trace_emit` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:182` | `_campaign_trace_query` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:258` | `_coerce_alert_ids` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:516` | `get_campaign_context_for_decision` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1001` | `CampaignRepository._run_campaign_locked_transaction` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1322` | `CampaignRepository.fetch_all_events` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1354` | `CampaignRepository.fetch_recent_events` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1391` | `CampaignRepository.fetch_single_alert_event` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1427` | `CampaignRepository.persist_campaign_seed` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1473` | `CampaignRepository.mark_campaign_seed_promoted` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1502` | `CampaignRepository.materialize_seed_campaign` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1537` | `CampaignRepository.cleanup_orphan_campaign_seeds` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1569` | `CampaignRepository.write_campaign` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1747` | `CampaignRepository.get_campaigns` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1771` | `CampaignRepository.get_campaign_detail` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1797` | `CampaignRepository.campaigns_exist` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1958` | `CampaignMatcher._check_alert_impl` | Supplemental wrapper/handler review | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2014` | `CampaignMatcher._check_materialized_campaign` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2069` | `CampaignMatcher._materialize_in_background` | Supplemental wrapper/handler review | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2146` | `CampaignMatcher._find_matching_campaign` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:2176` | `CampaignMatcher._add_alert_to_campaign` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:194` | `TravelMatchFactor.compute` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:271` | `AssetCriticalityFactor.compute` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:332` | `ThreatIntelEnrichmentFactor.compute` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:371` | `ThreatIntelEnrichmentFactor._internal_campaign_score` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:451` | `PatternHistoryFactor.compute` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:517` | `PatternHistoryFactorComputer.compute` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/orchestrator.py:179` | `_query_rows` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:75` | `SOCEvidenceProvider.read_evidence` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:90` | `SOCEvidenceProvider._read_from_graph_client` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/audit.py:235` | `rebuild_chain_from_graph` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/audit.py:292` | `rebuild_from_age` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py:28` | `CheckpointService.create_checkpoint` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py:75` | `CheckpointService.list_checkpoints` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py:101` | `CheckpointService.rollback` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/composite_gate.py:62` | `CompositeDiscriminant.evaluate` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/decision_history.py:22` | `DecisionHistoryService.get_category_stats` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/event_bus.py:96` | `EventBus.emit` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:107` | `InterventionControls.rollback` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:252` | `InterventionControls.get_current_state` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:286` | `InterventionControls.get_intervention_history` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/intervention_controls.py:329` | `InterventionControls._log_intervention` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/learning_state.py:59` | `load_from_file` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/learning_state.py:112` | `save_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/provenance.py:287` | `ProvenanceService.get_provenance_from_graph` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/shadow_mode.py:27` | `ShadowModeService.record_shadow_decision` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/shadow_mode.py:45` | `ShadowModeService.record_analyst_action` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/shadow_mode.py:62` | `ShadowModeService.get_shadow_report` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/framework/similar_cases_base.py:61` | `SimilarCasesBase._fetch_verified_decisions` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:265` | `_configured_age_client` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:293` | `_configured_graph_store` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:320` | `verify_graph` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py:542` | `seed_graph` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:87` | `_safe_entity_cache_health` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:110` | `health` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:271` | `startup_event` | Named-call scan | P2; separate legitimate paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/main.py:620` | `shutdown_event` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:181` | `_write_manifest_to_graph` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:378` | `admin_ingest` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:420` | `admin_evolution_scan` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:438` | `admin_shadow_start` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:480` | `admin_promote_evaluate` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/admin.py:517` | `sentinel_health` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/audit.py:37` | `get_audit_decisions` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/audit.py:109` | `verify_audit_chain` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/cohort_status_router.py:28` | `_read_decision_records` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:37` | `fingerprint_alias` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/compat_router.py:70` | `trajectory_alias` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/discoveries_router.py:125` | `get_discoveries` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/discoveries_router.py:150` | `refresh_discoveries` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/discoveries_router.py:172` | `get_discoveries_summary` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/discoveries_router.py:195` | `cross_correlate_alerts` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/eval_router.py:30` | `upload_eval_csv` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evaluation.py:92` | `run_evaluation_endpoint` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evaluation.py:149` | `get_evaluation_summary` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:94` | `get_deployments` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:143` | `process_alert` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:472` | `process_alert_blocked` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:621` | `simulate_failure` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:719` | `get_recent_evolution` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:761` | `get_variant_history` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:777` | `get_evolution_summary` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:786` | `get_soc_rejection_summary` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:826` | `get_recent_events` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:937` | `get_graph_stats` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/explain.py:17` | `_explain_context` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/explain.py:34` | `no_precedent` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/explain.py:43` | `what_if` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:31` | `_get_age_client` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:109` | `get_centroid_evolution` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:181` | `get_convergence_calendar` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:257` | `get_ols_status_endpoint` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:330` | `get_flywheel_comparison` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:411` | `get_iks_trend_endpoint` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:462` | `shadow_analyst_action` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:474` | `shadow_report` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:485` | `checkpoint_create` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:509` | `checkpoint_list` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:517` | `checkpoint_rollback` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:543` | `scorer_freeze` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:558` | `scorer_unfreeze` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:577` | `auto_approve_stats` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:635` | `graph_explorer_query` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:655` | `graph_top_nodes` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:672` | `graph_node_neighbors` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:682` | `graph_summary` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:709` | `graph_run_prebuilt` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:727` | `learning_health` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:781` | `learning_balance_sheet` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:917` | `factor_contribution` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:944` | `_get_intervention_controls` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:1019` | `intervention_history` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:1050` | `get_triage_learning_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:1139` | `get_channel_decomposition` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:37` | `_wu_timestamp` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:50` | `gae_weights` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:79` | `gae_history` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:136` | `gae_convergence` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:187` | `gae_confidence_trajectory` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:228` | `gae_trust_curve` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:289` | `gae_before_after` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/gae.py:345` | `gae_weight_evolution` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:172` | `refresh_threat_intel_endpoint` | Named-call scan | P2; separate legitimate paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:303` | `get_enrichment_aggregate` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:351` | `get_enrichment_summary` | Named-call scan | P1; separate legitimate paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/graph.py:412` | `get_enrichment_by_alert` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/judgment.py:102` | `explain_decision_post` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/judgment.py:151` | `explain_decision_get` | Named-call scan | P3; separate legitimate paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:182` | `get_compounding_metrics` | Named-call scan | P1; separate legitimate paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:388` | `get_evolution_events` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:443` | `get_weekly_trends` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:489` | `get_decision_economics` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:609` | `get_operational_metrics` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:713` | `get_board_export` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/metrics.py:771` | `get_economics` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:40` | `_load_cross_signals` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:65` | `_load_domain_table` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:103` | `_load_warm_start_evidence` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:134` | `_load_chain_credit_demo` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:169` | `_load_rl_reward_demo` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/platform.py:204` | `_load_rl_exploration_demo` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/rl_router.py:37` | `reward_ledger_summary` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/rl_router.py:49` | `reward_ledger_entries` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/rl_router.py:61` | `posterior_summary` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/rl_router.py:128` | `chain_credit` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/rl_router.py:166` | `rl_status` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/roi.py:199` | `get_roi_defaults` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/roi.py:232` | `calculate_roi_endpoint` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/simulation.py:44` | `_load_alert_pool` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/simulation.py:126` | `_run_simulation_bg` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:28` | `_decision_counts` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:47` | `_recent_decisions` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_demo_beats.py:127` | `no_precedent_alerts` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:31` | `demo_refreeze` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:52` | `_age_client` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:59` | `get_learning_control_room` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:79` | `get_frozen_comparison` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc_learning.py:108` | `initialize_frozen_comparison` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:43` | `diagnostics` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:543` | `query_soc_metrics` | Named-call scan | P1; separate legitimate paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:646` | `get_detection_engineering` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:756` | `get_threat_landscape` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:886` | `get_attack_tactic_breakdown` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:920` | `get_soc_analytics` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1018` | `get_learning_state_endpoint` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1107` | `explain_decision` | Named-call scan | P1; separate legitimate paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1526` | `_compliance_conservation_status` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1537` | `_compliance_audit_chain_valid` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1775` | `_parse_dt` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1785` | `_format_campaign` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1826` | `_epoch_seconds` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1887` | `_format_campaign_detail` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:1929` | `get_campaigns` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2060` | `get_accuracy_trajectory` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2141` | `get_analyst_benchmarking` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2371` | `get_enrichment_advisor` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2404` | `get_enrichment_status` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2620` | `backup_centroid` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2641` | `restore_centroid` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2667` | `list_centroid_checkpoints_endpoint` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2685` | `get_gate_config` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2774` | `_tab1_content` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:2887` | `_tab2_content` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3083` | `_load_bootstrap_centroids` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3126` | `_tab3_content` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3322` | `_tab4_content` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3455` | `_tab5_content` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3752` | `get_analyst_eta_weights_endpoint` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3831` | `get_analyst_weights` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:3987` | `get_spike_cap_status_endpoint` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:4024` | `get_centroid_export` | Supplemental wrapper/handler review | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:4222` | `get_centroid_support` | Supplemental wrapper/handler review | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/soc.py:4354` | `get_decision_distance_log` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:203` | `_soc_maybe_attach_decision_pipeline_shadow` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:254` | `_soc_get_security_context_for_analyze` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:300` | `_soc_perf_safe_value` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:332` | `_soc_perf_emit_duration` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:379` | `_soc_perf_phase` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:476` | `get_alert_queue` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:532` | `investigate_alert` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:638` | `investigate_alert_oracle` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:697` | `analyze_alert` | Named-call scan | P1, P2; separate legitimate paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1722` | `execute_action` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1897` | `reset_demo_alerts` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1953` | `report_decision_outcome` | Named-call scan | P2, P1; separate legitimate paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:2563` | `report_decision_outcome._checkpoint_writer` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3043` | `get_outcome_status` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3088` | `_build_policy_context` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3140` | `check_policy_conflicts` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3187` | `get_policy_history` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3218` | `get_profile_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3337` | `rl_reward_summary` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3365` | `decision_factors` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:3418` | `get_graph_data` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/attack_chain.py:97` | `AttackChainService._fetch_recent_alerts` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:72` | `_compute_structural_ceiling_report` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:105` | `_safe_overall_iks` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:113` | `_safe_centroid_drift` | Supplemental wrapper/handler review | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:138` | `_safe_learning_health` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:145` | `_safe_auto_approve_stats` | Supplemental wrapper/handler review | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/balance_sheet.py:155` | `_safe_timeline` | Supplemental wrapper/handler review | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/benchmarking_report.py:157` | `BenchmarkingEngine._fetch_verified_decisions` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/bootstrap_neo4j.py:157` | `write_bootstrap_decisions` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/bootstrap_neo4j.py:208` | `write_bootstrap_decisions.literal` | Named-call scan | Excluded: AGE value quoting only |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cluster_history.py:126` | `get_cluster_history` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cohort_status.py:141` | `CohortStatusService._read_decisions` | Supplemental wrapper/handler review | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:181` | `DiscoveryService._run_algorithm` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:195` | `DiscoveryService._get_as_of_epoch_ms` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:259` | `DiscoveryService.refresh` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:449` | `DiscoveryService._shared_entity_discovery` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:635` | `DiscoveryService._pattern_convergence_discovery` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/cross_graph_discovery.py:740` | `DiscoveryService._temporal_velocity_discovery` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py:118` | `EvidenceRoomService._collect_audit` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py:173` | `EvidenceRoomService._collect_conservation` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evidence_room.py:247` | `EvidenceRoomService._collect_override_analysis` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:110` | `AGEVariantStore.__init__` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:119` | `AGEVariantStore._persist` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:177` | `AGEVariantStore.reset` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:273` | `SOCConservationProvider.refresh` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:321` | `_get_soc_categories` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:429` | `_soc_variant_store` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:492` | `_normalize_category` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:543` | `_legacy_prompt_variant` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:594` | `get_prompt_stats` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/evolver.py:823` | `reset_evolver_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:186` | `ExecutiveNarrative._what_changed` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:244` | `ExecutiveNarrative._what_discovered` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:289` | `ExecutiveNarrative._what_system_knows` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:318` | `ExecutiveNarrative._get_metrics` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:353` | `ExecutiveNarrative._generate_headline` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/executive_narrative.py:398` | `build_executive_narrative_async` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:226` | `_init_learning_store` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:253` | `init_learning_state` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:442` | `get_soc_centroid` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:455` | `persist_soc_centroid` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:501` | `persist_soc_outcome_and_centroid` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:512` | `persist_soc_outcome_and_centroid.operation` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:545` | `get_mu_zero` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:590` | `save_learning_state` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:610` | `_reset_learning_state_inner` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:686` | `create_centroid_checkpoint` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:716` | `list_centroid_checkpoints` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:733` | `restore_centroid_checkpoint` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:776` | `write_bootstrap_state` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:830` | `get_bootstrap_centroids` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:918` | `apply_analyst_eta_weights` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/governance_report.py:112` | `_collect_audit_evidence` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:103` | `GraphExplorerService.run_safe_query` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:141` | `GraphExplorerService.get_top_nodes` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:195` | `GraphExplorerService.get_node_neighbors` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:229` | `GraphExplorerService.get_graph_summary` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_store_adapter.py:33` | `GraphStoreAdapter._run_state_operation` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_store_adapter.py:58` | `GraphStoreAdapter.save_posterior` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/graph_store_adapter.py:61` | `GraphStoreAdapter.get_posterior` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:54` | `_load_mu_zero` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:100` | `compute_visible_iks` | Supplemental wrapper/handler review | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:144` | `get_iks_trend` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:194` | `compute_iks_v2` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/iks.py:307` | `_compute_delta_7d` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_patterns.py:114` | `BaseInvestigationPattern._bounded_read` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/investigation_patterns.py:127` | `BaseInvestigationPattern._fallback_context` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:149` | `LearningHealthMonitor._extract_components` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:288` | `LearningHealthMonitor.evaluate` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:476` | `LearningHealthMonitor._count_red_days` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:549` | `_soc_categories_total` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:558` | `_soc_category_names` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:601` | `_query_soc_verified_conservation_stats` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:665` | `_persist_l5_conservation_state` | Supplemental wrapper/handler review | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:741` | `compute_volume_baseline` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:854` | `compute_category_baseline` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:949` | `compute_analyst_precision` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/learning_health.py:996` | `compute_verification_health` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/model_swap.py:87` | `run_model_swap_trial` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/narrative.py:251` | `TemplateNarrativeProvider.generate` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/narrative.py:374` | `OllamaNarrativeProvider.generate` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/override_detector.py:42` | `load_from_graph` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/pii_redaction.py:41` | `redact_payload` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:34` | `PosteriorStore.__init__` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:96` | `PosteriorStore.save` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:137` | `PosteriorStore.load` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:175` | `PosteriorStore.clear` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/posterior_store.py:193` | `PosteriorStore.health_check` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:79` | `_get_health_components` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:248` | `_check_conservation_for_variant` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:376` | `_get_shadow_batch_stats` | Supplemental wrapper/handler review | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/promotion_gate.py:541` | `register_rollback_handler` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reasoning.py:23` | `ReasoningNarrator._ensure_init` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reasoning.py:49` | `ReasoningNarrator.generate_reasoning` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:53` | `log_reconvergence_event` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:142` | `log_decision_distance` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:183` | `read_decision_distance_log` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:195` | `fetch_category_distribution` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/reconvergence_logger.py:213` | `read_reconvergence_events` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:451` | `CreditAssigner.assign_chain_credit` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/rl_engine.py:614` | `get_exploration_policy` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/sentinel_poller.py:112` | `SentinelPoller.poll_once` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_promotion.py:95` | `_get_shadow` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_promotion.py:109` | `_sample_count` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_promotion.py:121` | `_existing_observation` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_promotion.py:169` | `promote_shadow_decision` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:48` | `compute_variant_action` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:96` | `maybe_shadow_compare` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:141` | `fill_shadow_outcome` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/shadow_runner.py:171` | `_flush_shadow_batch` | Supplemental wrapper/handler review | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py:64` | `_write_simulation_decision` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py:249` | `SimulationOrchestrator.run` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/snapshots.py:37` | `_write_profile_snapshot` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:158` | `SOCLearningControlService.comparison` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:258` | `SOCLearningControlService.measured_comparison` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_learning_control.py:302` | `build_control_room` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:147` | `_campaign_context_age_days` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:184` | `SocAlertTraversalPattern.traverse` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:206` | `SocAlertTraversalPattern.traverse_async` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/soc_situation_pattern.py:233` | `SocAlertTraversalPattern._traverse_sync` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:70` | `StateManager._verify_deletion_safety` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:101` | `StateManager.clear_session_decisions` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:119` | `StateManager.delete_session_decisions` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:139` | `StateManager.soft_reset` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:205` | `StateManager.hard_reset` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/state_manager.py:279` | `StateManager._rollback_learning_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/switching_cost.py:93` | `_normalise_milestones` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:52` | `ThreatIndicatorService.upsert_indicator` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:111` | `ThreatIndicatorService.link_to_alert` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:139` | `ThreatIndicatorService.get_indicators_for_alert` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:159` | `ThreatIndicatorService.get_all_indicators` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/threat_indicator.py:199` | `ThreatIndicatorService.cleanup_expired` | Named-call scan | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/time_machine.py:92` | `_age_payloads` | Named-call scan | P3 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/time_machine.py:103` | `_coerce_tensor` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/time_machine.py:117` | `_decision_count` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/time_machine.py:149` | `_compute_current_ceiling_estimate` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/time_machine.py:363` | `get_evolution_timeline` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/timestamp_backfill.py:18` | `backfill_decision_timestamps` | Named-call scan | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/triage_providers.py:53` | `EvidenceScopedGraphAdapter.run_query` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:163` | `_build_threat_intel_factor` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/triage.py:225` | `_get_alert_type` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:77` | `_consult_history` | Supplemental wrapper/handler review | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:215` | `_load_accuracy_trajectory` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:249` | `_live_dk_learning_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:310` | `CampaignEscalateRule.detect` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:399` | `_get_per_category_accuracy_trends` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:459` | `DriftThresholdRule.detect` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:511` | `OverridePromptRule.detect` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:662` | `CoverageGapRule.detect` | Named-call scan | P1 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_generator.py:751` | `VariantGenerator.scan_for_opportunities` | Supplemental wrapper/handler review | P2 |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_registry.py:149` | `_record_from_created` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/variant_registry.py:268` | `_query_events` | Named-call scan | Legitimate handler paths listed |
| `gen-ai-roi-demo-v4-v50/backend/app/services/whatif_service.py:129` | `_compute_current_ceiling_estimate` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `gen-ai-roi-demo-v4-v50/backend/app/state/graph_snapshot.py:61` | `GraphSnapshot.from_graph` | Named-call scan | No local except |
| `gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:72` | `seed_vld_showcase` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/connectors/supplier_intel_provider.py:120` | `SupplierIntelProvider._cascade` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/domains/s2p/factors.py:437` | `compute_all_factors` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/framework/audit.py:164` | `async_record_decision` | Named-call scan | No local except |
| `s2p-copilot/backend/app/framework/audit.py:203` | `async_record_outcome` | Named-call scan | No local except |
| `s2p-copilot/backend/app/framework/audit.py:239` | `get_decision_rows` | Named-call scan | No local except |
| `s2p-copilot/backend/app/framework/audit.py:243` | `get_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/framework/audit.py:247` | `get_audit_entries` | Named-call scan | No local except |
| `s2p-copilot/backend/app/framework/audit.py:252` | `verify_chain` | Named-call scan | No graph-swallow finding listed |
| `s2p-copilot/backend/app/framework/audit.py:296` | `async_reconstruct_from_memory` | Named-call scan | No local except |
| `s2p-copilot/backend/app/framework/audit.py:320` | `async_create_epoch_archive` | Named-call scan | No local except |
| `s2p-copilot/backend/app/framework/audit.py:335` | `get_epoch_archives` | Named-call scan | No local except |
| `s2p-copilot/backend/app/framework/audit.py:341` | `async_reset_audit_state` | Named-call scan | No local except |
| `s2p-copilot/backend/app/framework/checkpoint.py:27` | `CheckpointService.create_checkpoint` | Named-call scan | No local except |
| `s2p-copilot/backend/app/framework/checkpoint.py:74` | `CheckpointService.list_checkpoints` | Named-call scan | P1 |
| `s2p-copilot/backend/app/framework/checkpoint.py:101` | `CheckpointService.rollback` | Named-call scan | No graph-swallow finding listed |
| `s2p-copilot/backend/app/framework/composite_gate.py:61` | `CompositeDiscriminant.evaluate` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/framework/decision_history.py:23` | `DecisionHistoryService.get_category_stats` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/framework/event_bus.py:96` | `EventBus.emit` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/framework/intervention_controls.py:223` | `InterventionControls.rollback` | Named-call scan | No graph-swallow finding listed |
| `s2p-copilot/backend/app/framework/intervention_controls.py:411` | `InterventionControls.get_current_state` | Named-call scan | P1 |
| `s2p-copilot/backend/app/framework/intervention_controls.py:447` | `InterventionControls.get_intervention_history` | Named-call scan | P1 |
| `s2p-copilot/backend/app/framework/intervention_controls.py:490` | `InterventionControls._log_intervention` | Named-call scan | P2 |
| `s2p-copilot/backend/app/framework/learning_state.py:59` | `load_from_file` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/framework/learning_state.py:112` | `save_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/framework/provenance.py:287` | `ProvenanceService.get_provenance_from_graph` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/framework/shadow_mode.py:27` | `ShadowModeService.record_shadow_decision` | Named-call scan | No local except |
| `s2p-copilot/backend/app/framework/shadow_mode.py:45` | `ShadowModeService.record_analyst_action` | Named-call scan | No local except |
| `s2p-copilot/backend/app/framework/shadow_mode.py:63` | `ShadowModeService.get_shadow_report` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/framework/similar_cases_base.py:63` | `SimilarCasesBase._fetch_verified_decisions` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:27` | `S2PGraphReader._read` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:35` | `S2PGraphReader.get_decision` | Named-call scan | No local except |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:41` | `S2PGraphReader.get_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:55` | `S2PGraphReader.get_all_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:67` | `S2PGraphReader.count_verified` | Named-call scan | No local except |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:77` | `S2PGraphReader.count_verified_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:97` | `S2PGraphReader.count_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:105` | `S2PGraphReader.count_recommended_action.count` | Named-call scan | No local except |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:116` | `S2PGraphReader.get_decision_links` | Named-call scan | No local except |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:130` | `S2PGraphReader.query_context` | Named-call scan | No local except |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:183` | `S2PGraphReader.query_direct_context` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:204` | `S2PGraphReader.query_direct_context.read` | Named-call scan | No local except |
| `s2p-copilot/backend/app/graph/s2p_graph_reader.py:243` | `S2PGraphReader.query_duplicate_context.read` | Named-call scan | No local except |
| `s2p-copilot/backend/app/main.py:220` | `build_s2p_scorer` | Named-call scan | No local except |
| `s2p-copilot/backend/app/main.py:360` | `_s2p_conservation_state` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/main.py:570` | `warm_s2p_tab_state_cache` | Named-call scan | No local except |
| `s2p-copilot/backend/app/main.py:578` | `_warm_s2p_learn_store_connections` | Named-call scan | No graph-swallow finding listed |
| `s2p-copilot/backend/app/migration/s2p_entity_migration.py:425` | `_upsert_node` | Named-call scan | No local except |
| `s2p-copilot/backend/app/migration/s2p_entity_migration.py:452` | `_upsert_edge` | Named-call scan | No local except |
| `s2p-copilot/backend/app/migration/s2p_entity_migration.py:490` | `_ensure_invoice_index` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/migration/s2p_entity_migration.py:511` | `_stamp_domain_edges` | Named-call scan | No local except |
| `s2p-copilot/backend/app/migration/s2p_entity_migration.py:524` | `_reconcile_orphans` | Named-call scan | No local except |
| `s2p-copilot/backend/app/migration/s2p_entity_migration.py:612` | `write_s2p_entity_migration` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/centroid_router.py:18` | `all_centroids` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/centroid_router.py:47` | `centroid_drift` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/centroid_router.py:55` | `centroid_cell` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/cohort_status_router.py:23` | `create_cohort_status_router.get_cohort_status` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/factor_proposer_router.py:86` | `_live_factor_stats` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/financial_router.py:106` | `_all_graph_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/financial_router.py:113` | `_receipt_rows` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/financial_router.py:358` | `_ensure_financial_snapshots` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/framework_router.py:41` | `_run_graph_query` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/framework_router.py:128` | `get_centroid_evolution` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/framework_router.py:179` | `get_convergence_calendar` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/framework_router.py:250` | `get_ols_status_endpoint` | Supplemental wrapper/handler review | P1 |
| `s2p-copilot/backend/app/routers/framework_router.py:397` | `shadow_analyst_action` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/framework_router.py:409` | `shadow_report` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/framework_router.py:427` | `checkpoint_list` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/framework_router.py:462` | `auto_approve_stats` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/framework_router.py:520` | `graph_explorer_query` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/framework_router.py:590` | `graph_run_prebuilt` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/framework_router.py:703` | `intervention_history` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/optimizer_router.py:33` | `optimizer_export` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/optimizer_router.py:51` | `optimizer_validate` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:52` | `_all_graph_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:92` | `_get_conservation_status` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:112` | `_get_iks` | Supplemental wrapper/handler review | P1 |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:180` | `_factor_analysis` | Supplemental wrapper/handler review | P1 |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:216` | `_audit_verification` | Named-call scan | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:269` | `_export_payload` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_audit_export.py:333` | `export_audit_csv` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_auto_approve.py:61` | `auto_approve_status` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_auto_approve.py:124` | `evaluate_auto_approve` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_autonomy.py:40` | `create_s2p_autonomy_router.advance` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_autonomy.py:53` | `create_s2p_autonomy_router.rollback` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_autonomy.py:66` | `create_s2p_autonomy_router.transfer` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_control_tower.py:238` | `queue` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_demo_beats.py:44` | `_rows` | Named-call scan | P3 |
| `s2p-copilot/backend/app/routers/s2p_demo_beats.py:188` | `frozen_twin` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_demo_control.py:105` | `seed_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_demo_control.py:114` | `demo_refreeze` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_demo_control.py:151` | `persist_demo_learning` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_enrichment_context.py:29` | `enrich_context` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:161` | `_call_or_none` | Supplemental wrapper/handler review | P1 |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:203` | `_conservation_snapshot` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:265` | `_graph_linked_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:289` | `audit_trail` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:335` | `audit_pack` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:355` | `evidence_template` | Named-call scan | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_evidence.py:488` | `compliance` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:178` | `_current_conservation_status` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:201` | `_checkpoint_imported_centroids` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:240` | `_safe_read_dk_weights` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:276` | `_sigma_ranked_fallback` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:336` | `_find_scored_decision` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:411` | `import_centroids` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_explorer.py:567` | `contribution` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_governance.py:20` | `_safe_conservation_snapshot` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_performance.py:58` | `_json_safe` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_performance.py:76` | `_count_verified` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_performance.py:84` | `_count_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_performance.py:92` | `_current_q` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_performance.py:122` | `_build_summary` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_performance.py:172` | `trajectory` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_performance.py:192` | `what_if` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_performance.py:232` | `summary` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_preview.py:122` | `_write_preview_observation` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_preview.py:153` | `_write_preview_observation_once` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_preview.py:196` | `_pending_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_preview.py:268` | `_preview_queue_limit` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_preview.py:282` | `preview_queue` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_preview.py:351` | `preview_suppliers` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_proposals.py:29` | `create_proposal_router.create_proposal` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_situation.py:28` | `get_situation` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p_situation.py:167` | `_decision` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p_situation.py:174` | `_entity_context_available` | Supplemental wrapper/handler review | P1 |
| `s2p-copilot/backend/app/routers/s2p_situation.py:223` | `_dk_weights` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p_suppliers.py:364` | `profile` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p.py:94` | `S2PScoreAuditWriter.begin_outcome` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p.py:102` | `S2PScoreAuditWriter.finish_outcome` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p.py:108` | `S2PScoreAuditWriter.record_decision` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p.py:127` | `S2PScoreAuditWriter.record_outcome` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p.py:239` | `diagnostics` | Named-call scan | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p.py:273` | `_log_side_effect_failure` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p.py:306` | `_resolve_graph_context` | Supplemental wrapper/handler review | P1 |
| `s2p-copilot/backend/app/routers/s2p.py:353` | `_score_process_context_with_signal` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p.py:468` | `_record_score_shadow` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p.py:545` | `_record_outcome_shadow` | Named-call scan | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p.py:706` | `_learning_store_from_request` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p.py:740` | `_dk_learning_store_from_request` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p.py:757` | `_centroid_learning_store_from_request` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p.py:774` | `_persist_l5_conservation_state` | Named-call scan | P2 |
| `s2p-copilot/backend/app/routers/s2p.py:825` | `_persist_l5_centroid_state` | Named-call scan | P2 |
| `s2p-copilot/backend/app/routers/s2p.py:881` | `_persist_l5_dk_state` | Named-call scan | P2 |
| `s2p-copilot/backend/app/routers/s2p.py:945` | `_read_centroid_for_l5` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p.py:994` | `_link_decision_to_invoice` | Named-call scan | P2; separate legitimate paths listed |
| `s2p-copilot/backend/app/routers/s2p.py:1021` | `_has_decision_invoice_link` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p.py:1039` | `_graph_verified_counts` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p.py:1051` | `_read_conservation_counts` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p.py:1119` | `_current_conservation_status` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p.py:1131` | `_score_conservation_cache_key` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p.py:1186` | `_score_write_governance` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p.py:1281` | `_record_evolver_outcome_if_allowed` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p.py:1440` | `_receipt_conservation_snapshot` | Supplemental wrapper/handler review | P1 |
| `s2p-copilot/backend/app/routers/s2p.py:1505` | `_record_outcome_receipt` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p.py:1641` | `_append_evidence_receipt_before_outcome` | Supplemental wrapper/handler review | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p.py:1769` | `_record_supplier_profile` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p.py:1790` | `_json_safe` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p.py:1869` | `_learn_with_scorer` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p.py:1892` | `_learn_with_scorer._advisory_invoice_link` | Supplemental wrapper/handler review | P2 |
| `s2p-copilot/backend/app/routers/s2p.py:1942` | `_learn_with_audit` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/routers/s2p.py:1969` | `_ensure_outcome_decision` | Named-call scan | No local except |
| `s2p-copilot/backend/app/routers/s2p.py:2237` | `score_procurement_event` | Supplemental wrapper/handler review | P1 |
| `s2p-copilot/backend/app/routers/s2p.py:2620` | `learn_decision` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/routers/s2p.py:2771` | `record_outcome` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/s2p_graph_status.py:101` | `is_live_age_configured` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/s2p_graph_status.py:134` | `S2PActiveGraphConfig.from_env` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/s2p_graph_status.py:314` | `create_s2p_active_graph_store` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/s2p_shadow.py:69` | `S2PShadowConfig.from_env` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/s2p_shadow.py:143` | `create_s2p_shadow_store` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/budget_persistence.py:117` | `PersistentBudgetPolicy.allocate` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/services/centroid_explorer.py:133` | `S2PCentroidExplorerService.explain_decision` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/centroid_explorer.py:145` | `S2PCentroidExplorerService.get_centroid_drift` | Named-call scan | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/centroid_explorer.py:191` | `S2PCentroidExplorerService._get_decision` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/centroid_explorer.py:195` | `S2PCentroidExplorerService._p39_evidence` | Named-call scan | P1 |
| `s2p-copilot/backend/app/services/centroid_explorer.py:307` | `get_centroid_drift` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/centroid_explorer.py:322` | `_read_public_centroid` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/centroid_explorer.py:355` | `_factor_vector` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/centroid_explorer.py:460` | `_centroid_from_checkpoint` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/centroid_explorer.py:539` | `_call_or_none` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/centroid_explorer.py:548` | `_index_or_error` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/compounding_ledger.py:78` | `CompoundingLedger._write` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/cross_copilot_signals.py:24` | `CrossCopilotSignalConsumer.fetch_supplier_signals` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/extinction_evidence.py:11` | `active_decision_ids` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/extinction_evidence.py:19` | `record_extinction` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/optimizer_export.py:147` | `OptimizerExportService._raw_centroids` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/proposal_service.py:217` | `GraphProposalStore.save` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/proposal_service.py:229` | `GraphProposalStore.get` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/proposal_service.py:238` | `GraphProposalStore.get_by_invoice` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/proposal_service.py:249` | `GraphProposalStore.list_recent` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/proposal_service.py:259` | `GraphProposalStore.get_by_decision_id` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/proposal_service.py:291` | `GraphProposalStore.link_outcome` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/proposal_service.py:310` | `GraphProposalStore.get_outcome` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/s2p_auto_approve_gate.py:395` | `AutoApproveGate._verified_decisions` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/s2p_autonomy.py:31` | `GraphPromotionStore.save` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/s2p_autonomy.py:34` | `GraphPromotionStore.load` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/s2p_autonomy.py:44` | `GraphPromotionStore.list_all` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/s2p_autonomy.py:58` | `S2PAutonomyManager.__init__` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/s2p_autonomy.py:86` | `S2PAutonomyManager.evidence_tier` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/s2p_context_builder.py:86` | `S2PContextBuilder.build_invoice_context` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/s2p_context_builder.py:261` | `S2PContextBuilder._supplier_enrichment` | Named-call scan | P1 |
| `s2p-copilot/backend/app/services/s2p_context_builder.py:373` | `S2PContextBuilder.build_category_centroid_context` | Supplemental wrapper/handler review | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/s2p_context_builder.py:552` | `S2PContextBuilder._verified_decision` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/s2p_context_builder.py:618` | `S2PContextBuilder._decision_rows` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:207` | `S2PSupplierEnrichmentService.read_supplier` | Named-call scan | P1 |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:221` | `S2PSupplierEnrichmentService.list_suppliers` | Named-call scan | P1 |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:280` | `S2PSupplierEnrichmentService._write_metrics` | Named-call scan | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:310` | `S2PSupplierEnrichmentService._dry_run_receipt` | Named-call scan | No graph-swallow finding listed |
| `s2p-copilot/backend/app/services/s2p_enrichment.py:354` | `S2PSupplierEnrichmentService._all_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/s2p_preview_data.py:37` | `read_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/s2p_situation_pattern.py:138` | `_find_decision` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/s2p_situation_pattern.py:158` | `_linked_decisions` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/s2p_situation_pattern.py:174` | `_receipt_context` | Supplemental wrapper/handler review | P1 |
| `s2p-copilot/backend/app/services/situation_graph_enrichment.py:101` | `S2PSituationEnricher._read` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/situation_graph_enrichment.py:109` | `S2PSituationEnricher._write` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/situation_graph_enrichment.py:191` | `_decision_links` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/situation_graph_enrichment.py:196` | `_has_decision` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/situation_traversals.py:366` | `_prepare_context` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/situation_traversals.py:425` | `_query_graph_context` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/situation_traversals.py:530` | `_read_enriched_properties` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/services/situation_traversals.py:647` | `_get_decision` | Named-call scan | No local except |
| `s2p-copilot/backend/app/services/situation_traversals.py:656` | `_similar_decision` | Named-call scan | Legitimate handler paths listed |
| `s2p-copilot/backend/app/services/supplier_intelligence.py:367` | `SupplierIntelligenceComposer._read_enrichment` | Named-call scan | P3 |
| `s2p-copilot/backend/app/state/s2p_registry.py:39` | `create_s2p_tab_state_cache` | Named-call scan | No local except |

## Limits

This is a static diagnostic of the source present on 2026-09-23, not confirmation of a current graph outage. Return-value ambiguity is demonstrated from the cited code. Deployment configuration, external callers, dynamically supplied implementations, and actual outage frequency were not tested. No source fixes were made.

