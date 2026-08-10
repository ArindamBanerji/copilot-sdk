# Platform Factor Architecture Scan v1
**Date:** 2026-08-04  
**Type:** Static code scan. Read-only.

## Scope and evidence

The requested scan specification file, copilot-sdk/docs/design/s2p_fix_b_platform_factor_scan_v2.md, is absent from the current tree. This report uses the task requirements and docs/design/s2p_fix_b_whatif_phase_e_results_v1.md. The active code locations are gen-ai-roi-demo-v4-v50/backend (SOC), s2p-copilot/backend (S2P), and copilot-sdk/apps/{trading,purchasing,dataops}/backend. No source, test, graph, or database files were changed.

## Per-Copilot Factor Map

### SOC

The active analyze path gets the alert at gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:520-585 and invokes the ordered computers from app/domains/soc/config.py:743-751. The orchestrator calls each computer and assembles the vector at app/domains/soc/orchestrator.py:30-57.

| Factor | Source | Graph/Event | Bespoke/Generic | Properties read | Stub? | Fallback |
|---|---|---|---|---|---|---|
| privileged_identity_context | alert/security context | Event fields | no Cypher | user_risk_score, user_title, mfa_completed, device_fingerprint_match; title buckets 0.9/0.7/0.2 (factors.py:95-156) | No | 0.5 if no usable context/components |
| asset_criticality | AGE entity graph | Graph | bespoke typed Cypher | Asset.criticality and DataClass.sensitivity (factors.py:243-283) | No; low=.2, medium=.5, high=.8, critical=1.0, sensitive boost +.1 | .5 for missing id/rows/unknown value; query errors raise |
| threat_intel_enrichment | AGE entity graph | Graph | bespoke typed Cypher | ThreatIndicator.severity/source; Campaign confidence, severity, campaign_id, nl_summary, trigger_rule (factors.py:320-398) | No; severity map info=.1, low=.3, medium=.6, high=.85, critical=1.0; campaign .05/.20/.40 | 0.0 without alert id; no IOC 0.0; no campaign .50 |
| pattern_history | AGE decision/evolution history | Graph | bespoke typed Cypher | Decision category, action_index, verified_correct, factor_snapshot, decision_number (factors.py:471-557) | No; stored-history calculation | _fallback_compute() returns .40 |
| time_anomaly | alert properties | Event fields | no Cypher | weekend_login, business_hours_login (factors.py:574-610) | No | .7 when absent; 1.0 weekend; 0.0 business hours |
| device_trust | alert properties | Event fields | no Cypher | mfa_completed, device_fingerprint_match, vpn or vpn_provider (factors.py:613-650) | No | Missing flags are false, producing 1.0 |

SOC context resolution is bespoke: ci-platform/ci_platform/graph/age_client.py:551-584 issues a typed multi-OPTIONAL-MATCH query over Alert, Asset, User, Location, AttackPattern, Campaign, ThreatIndicator, and BehaviorHistory and merges returned dictionaries. Factor queries include Alert-[:DETECTED_ON]->Asset-[:STORES]->DataClass (factors.py:264-271) and Alert-[:HAS_INDICATOR]->ThreatIndicator (factors.py:329-333). It does not use the SDK generic query_context.

Silent fallback risk is YES overall: services/triage.py:257-267 still calls compute_soc_factors(), whose factors.py:877-923 selects static SOC_FACTOR_TEMPLATES by alert id/type/default. The active analyze path is different and uses the FactorComputers. Therefore the active graph path is code-backed, while the legacy factor-detail path can be template-backed.

### Trading

The active registry is copilot-sdk/apps/trading/backend/app/factors/registry.py:19-85. It has ten factors, initializes values to .5, invokes event computers, and catches exceptions to .5. No factor module contains query_context, run_query, AGE, or Neo4j calls.

| Factor | Source | Properties/fields read | Stub? | Fallback |
|---|---|---|---|---|
| signal_alignment | Event | tagged_signals.confirmed; rsi_at_entry, macd_signal, price_vs_sma, entry_direction (signal_alignment.py:11-36; technical_signal.py:10-39) | No | .5 empty/no components |
| market_regime | Event | current_regime or vix_at_entry/trend_strength; regime_accuracy[regime] (market_regime.py:56-78) | No | .5 |
| position_sizing | Event | position_size_pct, avg/max_position_size_pct, position_pct_of_max, portfolio_concentration, correlated_exposure, kelly_ratio (position_size.py:10-40) | No | .5 |
| timing_quality | Event | entry_delay_minutes, hold_time_vs_plan_pct, time_of_day_accuracy (timing_quality.py:8-35) | No | neutral numeric defaults |
| risk_reward_actual | Event | planned_risk_reward, actual_risk_reward or r_multiple (risk_reward.py:8-29) | No | .5 |
| emotional_indicator | Event | minutes_since_last_trade, last_trade_was_loss, consecutive_wins, size_vs_rolling_avg, entry_at_day_extreme (emotional_indicator.py:8-31) | No | .5 on empty context |
| signal_confidence | Event/DK context | dk_weights_by_category, tagged_signal_indices, category_index, factors_with_data, category_accuracy, similar_trade_count, novelty_distance (signal_confidence.py:10-82) | No | .5 |
| options_delta_exposure | Event/options dict | delta, options_delta, delta_exposure, net_delta (options_scored.py:14-26) | No | .5 |
| options_iv_percentile | Event/options dict | iv_percentile, iv_rank, options_iv_percentile, implied_volatility_percentile/rank (options_scored.py:30-49) | No | .5 |
| options_gamma_risk | Event/options dict | gamma, options_gamma, gamma_risk, net_gamma (options_scored.py:53-65) | No | .5 |

The separate options.py module contains explanation-only IV/RV, Greeks, and theta factors; its OPTIONS_FACTOR_NAMES are at options.py:24-37 and it is not the active ten-factor registry.

### Purchasing

The registry is copilot-sdk/apps/purchasing/backend/app/factors/__init__.py:13-44. It defines seven event/order-context callables and clamps every result. No factor module uses graph traversal.

| Factor | Source | Properties/fields read | Stub? | Fallback |
|---|---|---|---|---|
| expected_demand | Event/order | forecast_demand, par_level (expected_demand.py:19-33) | No | .5 |
| day_of_week | Event/order | day_of_week (day_of_week.py:19-27) | No | .5 |
| weather_forecast | Event/order | weather_score; category; condition/weather/forecast; precipitation, wind, temperature (weather_forecast.py:66-131) | No | .5 |
| event_flag | Event/order | event_flag or event_covers and normal_covers (event_flag.py:19-38) | No | .5 |
| historical_waste | Event/order | waste_pct (historical_waste.py:19-27) | No | .5 |
| supplier_lead_time | Event/order | lead_time_days (supplier_lead_time.py:19-26) | No | .5 |
| price_memory_index | Event/order | price_change_count, months_tracked (price_memory_index.py:19-31) | No | .5 |

### DataOps

The current tree contradicts the supplied hypothesis that DataOps is purely event-field. Factor assembly is copilot-sdk/apps/dataops/backend/app/graph_queries.py:313-378 and six names are declared at app/main.py:95-102.

| Factor | Source | Properties/fields read | Stub? | Fallback |
|---|---|---|---|---|
| impact_scope | typed graph topology | PipelineSystem name/domain and FEEDS descendants; min(downstream_count/8,1) (graph_queries.py:505-523) | No | fixture topology if optional AGE unavailable |
| source_reliability | PipelineSystem property, then alert | system.source_reliability, alert factors.source_reliability (graph_queries.py:347-350, 453-457) | No | alert/fixture |
| recurrence_frequency | typed graph history | DataQualityAlert domain/category and AFFECTS to system; min(prior_count/12,1) (graph_queries.py:546-566) | No | fixture prior count |
| downstream_urgency | typed graph topology/SLA | PipelineSystem.sla_minutes across FEEDS; (120-min_sla)/120 (graph_queries.py:525-544, 598-599) | No | fixture SLA |
| data_freshness | alert field | alert factors.data_freshness or alert field (graph_queries.py:362-365, 453-457) | No | alert/fixture |
| business_criticality | PipelineSystem property, then alert | system.business_criticality, alert factor (graph_queries.py:367-370) | No | alert/fixture |

Graph resolution is typed at graph_queries.py:380-397: DataQualityAlert with optional AFFECTS PipelineSystem and domain=dataops. _run_graph() is at :568-582. DataOps uses a bespoke graph client, not generic query_context.

### S2P (confirmation)

S2P currently has eight factors, although the requested vector names seven. ALL_FACTORS and aliases are at s2p-copilot/backend/app/domains/s2p/factors.py:330-351; compute_all_factors() catches individual failures at :354-368.

| Factor | Source | Stub? | Fallback |
|---|---|---|---|
| match_status | generic graph neighbors; PO/GR presence only (factors.py:141-159) | YES: PO+GR=.1, PO=.6, other graph=.9 | approved-category branch, otherwise .5 |
| amount_variance_ratio | PO amount and invoice amount (:165-190) | No | variance/mean, then .3 |
| duplicate_score | sibling Invoice amounts (:196-218) | No, requires sibling rows | .05 |
| supplier_exception_history | Supplier.exception_rate (:224-241) | No | vendor history/risk, then .5 |
| payment_terms_impact | Supplier.payment_terms and invoice payment_days (:247-267) | No | .5 |
| commodity_index_correlation | Commodity.volatility (:273-283) | No | .5 |
| tax_regulatory_compliance | Contract presence only (:289-302) | YES: context+Contract=.15; context without=.8 | metadata, otherwise .9 |
| environmental_risk (additional) | neighbor or invoice metadata (:305-328) | No | .5 |

S2PGraphReader.query_context() delegates to the store at s2p-copilot/backend/app/graph/s2p_graph_reader.py:118-130. The shared AGE implementation is the label-less variable-length query:
MATCH p = (e {entity_id: ...})-[*1..hops]-(n)
WHERE n.domain = ...
RETURN p
LIMIT 100
at ci-platform/ci_platform/graph/age_graph_store.py:3143-3164. _node_to_dict() is at :3190-3224. The S2P score route calls this through _resolve_graph_context() at s2p-copilot/backend/app/routers/s2p.py:138-161, and its domain-specific row check at :152-170 requires a node key. Path-shaped p results can therefore become context=None; compute_all_factors() then uses invoice-stored factors/defaults.

## Summary Table

| Copilot | Factor source | Entity-context? | Stub factors? | query_context user? | Working? |
|---|---|---|---|---|---|
| SOC | bespoke typed graph plus alert fields/history | YES for asset, threat intel, pattern history | No active topology-only factors; legacy template route exists | NO | Active analyze path is graph/property-backed in code; legacy detail path can be template-backed |
| Trading | event fields | NO | NO | NO | YES, with .5 exception fallback |
| Purchasing | event fields | NO | NO | NO | YES, with .5 missing-data fallback |
| DataOps | bespoke typed graph topology/system properties plus alert fields | YES | NO | NO | YES in graph mode; explicit fixture mode exists |
| S2P | generic graph neighbors plus invoice fallback | YES | YES, 2/7 core factors | YES, only confirmed consumer | NO for intended AGE score path |

## Synthesis

### Is the stub pattern S2P-only?

The specific topology-only presence stub is S2P-only. MatchStatus and TaxRegulatoryCompliance inspect only node-type presence and return fixed buckets (factors.py:148-159 and :295-302). The other copilots use numeric formulas, mappings, typed graph counts, or concrete graph properties. A broader fallback pattern is not S2P-only: Trading/Purchasing use neutral .5 defaults, DataOps has optional fixture mode, and SOC has a legacy static template route. Those are fallback/observability concerns, not the same topology stub.

### Is SOC a valid working reference?

Partially. The active SOC analyze path is a strong code reference: it uses typed Cypher, reads concrete properties, and emits provenance in orchestrator.py:30-57 and :72-156. Static inspection cannot establish that the live data is populated or that perturbing a property changes the response. The legacy compute_soc_factors() compatibility route is explicitly template-backed and is not a valid runtime proof.

### Generic query_context consumers

S2P is the only copilot consumer found. Its reader is s2p_graph_reader.py:118-130 and its route is s2p.py:138-161. SOC uses AGEClient typed Cypher; DataOps uses DataOpsGraphClient typed Cypher; Trading and Purchasing have no graph calls in factor code.

### Platform-level concern?

No evidence of a shared generic-query failure or broadly broken entity-context scoring. The demonstrated normalization defect and two topology-only factors are S2P-specific. There is a platform-level need for stronger provenance and perturbation tests because plausible fallback values remain possible in several products.

## Recommended Next Step

Run a disposable SOC perturbation experiment, analogous to S2P Phase B: change Asset.criticality or ThreatIndicator.severity in a sandbox and verify the active /api/alert/analyze factor vector changes, while checking factor provenance. This is not needed to identify a shared generic-query defect, but it is needed to promote SOC from a strong static reference to a runtime-proven working reference.

## Reading and scan log

- Read copilot-sdk/CLAUDE.md fully.
- Attempted to read copilot-sdk/docs/design/s2p_fix_b_platform_factor_scan_v2.md; absent.
- Read copilot-sdk/docs/design/s2p_fix_b_whatif_phase_e_results_v1.md fully.
- Read active SOC factor/config/orchestrator/triage/AGE-client sources.
- Read active Trading and Purchasing factor registries/modules.
- Read active DataOps factor assembly and graph query layer.
- Read S2P factors, reader, router normalization, and shared AGE query implementation.
- No production/test files edited; no graph/database writes performed.
