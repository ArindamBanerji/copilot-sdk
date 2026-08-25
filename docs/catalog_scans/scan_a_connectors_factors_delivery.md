PART 1 - CONNECTOR / INTEGRATION CATALOG
COMPONENT | CONNECTOR | EXTERNAL SYSTEM | DIRECTION | LIVE-OR-FIXTURE | AUTH MODEL | EVIDENCE | STATUS
GAE | GraphStore protocol | graph store | read-write | live-with-fixture-fallback | unknown | graph-attention-engine-v50/gae/graph.py:GraphStore | BUILT
copilot-sdk | SnowflakeMetaConnector | Snowflake | read | live-with-fixture-fallback | env-var | copilot-sdk/copilot_sdk/connectors/snowflake_meta.py:SnowflakeMetaConnector | BUILT
copilot-sdk | DBTConnector | dbt Cloud/artifacts | read | live-with-fixture-fallback | api-key | copilot-sdk/copilot_sdk/connectors/dbt_connector.py:DBTConnector | BUILT
copilot-sdk | AirflowConnector | Apache Airflow | read | live-with-fixture-fallback | env-var | copilot-sdk/copilot_sdk/connectors/airflow_connector.py:AirflowConnector | BUILT
SOC | SentinelRealConnector | Microsoft Sentinel / Graph Security API | read | live-with-fixture-fallback | oauth2 | gen-ai-roi-demo-v4-v50/backend/app/connectors/sentinel_real.py:SentinelRealConnector | BUILT
SOC | NVDClient | NIST NVD API | read | live | api-key | gen-ai-roi-demo-v4-v50/backend/app/connectors/nvd_client.py:NVDClient | BUILT
SOC | MITREClient | MITRE ATT&CK | read | live | none | gen-ai-roi-demo-v4-v50/backend/app/connectors/mitre_client.py:MITREClient | BUILT
SOC | GreyNoiseClient | GreyNoise | read | live | api-key | gen-ai-roi-demo-v4-v50/backend/app/connectors/greynoise.py:GreyNoiseClient | BUILT
SOC | PulsediveClient | Pulsedive | read | live | api-key | gen-ai-roi-demo-v4-v50/backend/app/connectors/pulsedive.py:PulsediveClient | BUILT
SOC | CrowdStrikeMockConnector | CrowdStrike | read | fixture-only | none | gen-ai-roi-demo-v4-v50/backend/app/connectors/crowdstrike_mock.py:CrowdStrikeMockConnector | PARTIAL
Trading | AlpacaConnector | Alpaca market/trading API | read | live | api-key | copilot-sdk/apps/trading/backend/app/connectors/alpaca_connector.py:AlpacaConnector | BUILT
Trading | AlpacaBroker | Alpaca order API | write | live | api-key | copilot-sdk/apps/trading/backend/app/brokers/alpaca.py:AlpacaBroker | BUILT
Trading | IBKRConnector | Interactive Brokers TWS/Gateway | read-write | live-with-fixture-fallback | none | copilot-sdk/apps/trading/backend/app/connectors/ibkr_connector.py:IBKRConnector | BUILT
Trading | YFinanceProvider | Yahoo Finance | read | live-with-fixture-fallback | none | copilot-sdk/apps/trading/backend/app/connectors/yfinance_provider.py:YFinanceProvider | PARTIAL
Trading | CSVConnector | local CSV files | read | fixture-only | none | copilot-sdk/apps/trading/backend/app/connectors/csv_connector.py:CSVConnector | BUILT
Trading | TradingView webhook | TradingView webhook sender | read | live | none | copilot-sdk/apps/trading/backend/app/routers/webhook.py:tradingview_webhook | BUILT
Purchasing | QBOConnector | QuickBooks Online | read | live-with-fixture-fallback | oauth2 | copilot-sdk/apps/purchasing/backend/app/connectors/qbo_connector.py:QBOConnector | BUILT
Purchasing | ToastConnector | Toast POS | read | live-with-fixture-fallback | api-key | copilot-sdk/apps/purchasing/backend/app/connectors/toast.py:ToastConnector | BUILT
Purchasing | FREDCommoditySource | FRED commodity series API | read | live-with-fixture-fallback | api-key | copilot-sdk/apps/purchasing/backend/app/connectors/commodity_source.py:FREDCommoditySource | BUILT
Purchasing | MockWeatherProvider | weather fixture | read | fixture-only | none | copilot-sdk/copilot_sdk/connectors/mock_weather.py:MockWeatherProvider | PARTIAL
Purchasing | OpenMeteo | Open-Meteo weather API | read | mock | none | not found | UNVERIFIED
DataOps | SAPConnector | SAP S/4HANA OData API | read | live-with-fixture-fallback | api-key | copilot-sdk/apps/dataops/backend/app/sap_connector.py:SAPConnector | BUILT
DataOps | CelonisConnector | Celonis process/KPI API | read | live-with-fixture-fallback | env-var | copilot-sdk/apps/dataops/backend/app/celonis_connector.py:CelonisConnector | BUILT
DataOps | SAPODataConnector | SAP S/4HANA OData API | read | live-with-fixture-fallback | env-var | copilot-sdk/apps/dataops/backend/app/enterprise_router.py:_sap_connector | BUILT
DataOps | CelonisProcessConnector | Celonis EMS | read | live-with-fixture-fallback | env-var | copilot-sdk/apps/dataops/backend/app/enterprise_router.py:_celonis_connector | BUILT
DataOps | DQBenchmarkProvider | Schema.org JSON-LD | read | live-with-fixture-fallback | none | copilot-sdk/apps/dataops/backend/app/connectors/dq_benchmark_provider.py:SchemaOrgSource | PARTIAL
DataOps | Snowflake connector factory | Snowflake | read | live-with-fixture-fallback | env-var | copilot-sdk/apps/dataops/backend/app/main.py:_snowflake_connector | BUILT
DataOps | dbt connector factory | dbt | read | live-with-fixture-fallback | api-key | copilot-sdk/apps/dataops/backend/app/main.py:_dbt_connector | BUILT
DataOps | Airflow connector factory | Apache Airflow | read | live-with-fixture-fallback | env-var | copilot-sdk/apps/dataops/backend/app/main.py:_airflow_connector | BUILT
S2P | FDAClient | openFDA enforcement API | read | live | none | s2p-copilot/backend/app/connectors/fda_client.py:FDAClient | BUILT
S2P | SECClient | SEC EDGAR API | read | live | none | s2p-copilot/backend/app/connectors/sec_client.py:SECClient | BUILT
S2P | SupplierIntelProvider | SEC and FDA supplier intelligence | read | live-with-fixture-fallback | none | s2p-copilot/backend/app/connectors/supplier_intel_provider.py:SupplierIntelProvider | BUILT

PART 2 - FACTOR LINEAGE
COPILOT | FACTOR | HOW COMPUTED | INPUT SOURCE | EVIDENCE | STATUS
SOC | privileged_identity_context | weighted normalization of risk, title, MFA, and device context | graph-store | gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:PrivilegedIdentityContextFactor.compute | BUILT
SOC | asset_criticality | graph query resolves asset criticality and clamps the result | graph-store | gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:AssetCriticalityFactor.compute | BUILT
SOC | threat_intel_enrichment | threat-intel provider result normalized to a score | connector:GreyNoise | gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:ThreatIntelEnrichmentFactor.compute | PARTIAL (fixture-backed)
SOC | pattern_history | extracts pattern-history slot from prior decision factor snapshot, with neutral fallback | decision-history | gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:PatternHistoryFactorComputer.compute | PARTIAL (fixture-backed)
SOC | time_anomaly | compares event time with temporal baseline and clamps anomaly score | graph-store | gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:TimeAnomalyFactor.compute | BUILT
SOC | device_trust | weighted device trust and authentication context, neutral when absent | graph-store | gen-ai-roi-demo-v4-v50/backend/app/domains/soc/factors.py:DeviceTrustFactor.compute | PARTIAL (fixture-backed)
Trading | signal_alignment | mean of confirmed tagged-signal fraction and technical-signal alignment | derived-from-factors | copilot-sdk/apps/trading/backend/app/factors/signal_alignment.py:SignalAlignmentFactor.compute | PARTIAL (fixture-backed)
Trading | market_regime | regime classifier uses VIX, trend, and optional price history | connector:yfinance | copilot-sdk/apps/trading/backend/app/factors/market_regime.py:MarketRegimeFactor.compute | PARTIAL (fixture-backed)
Trading | position_sizing | mean of size-vs-average, max-size, concentration, correlated exposure, and Kelly scores | derived-from-factors | copilot-sdk/apps/trading/backend/app/factors/position_size.py:PositionSizeFactor.compute | PARTIAL (fixture-backed)
Trading | timing_quality | combines entry delay, hold-time adherence, and time-of-day accuracy | decision-history | copilot-sdk/apps/trading/backend/app/factors/timing_quality.py:TimingQualityFactor.compute | PARTIAL (fixture-backed)
Trading | risk_reward_actual | normalizes actual risk/reward or actual-to-planned ratio | decision-history | copilot-sdk/apps/trading/backend/app/factors/risk_reward.py:RiskRewardActualFactor.compute | PARTIAL (fixture-backed)
Trading | emotional_indicator | rule score from recent loss, recency, consecutive wins, sizing, and entry extreme | decision-history | copilot-sdk/apps/trading/backend/app/factors/emotional_indicator.py:EmotionalIndicatorFactor.compute | PARTIAL (fixture-backed)
Trading | signal_confidence | mean of data coverage, category accuracy, similar-trade count, novelty, or supplied DK weights | decision-history | copilot-sdk/apps/trading/backend/app/factors/signal_confidence.py:SignalConfidenceFactor.compute | PARTIAL (fixture-backed)
Trading | options_delta_exposure | absolute delta normalized by configured exposure cap | decision-history | copilot-sdk/apps/trading/backend/app/factors/options_scored.py:OptionsDeltaExposureFactor.compute | PARTIAL (fixture-backed)
Trading | options_iv_percentile | clamps supplied implied-volatility percentile | decision-history | copilot-sdk/apps/trading/backend/app/factors/options_scored.py:OptionsIVPercentileFactor.compute | PARTIAL (fixture-backed)
Trading | options_gamma_risk | absolute gamma normalized by configured gamma cap | decision-history | copilot-sdk/apps/trading/backend/app/factors/options_scored.py:OptionsGammaRiskFactor.compute | PARTIAL (fixture-backed)
Purchasing | expected_demand | forecast demand divided by par level and clamped | fixture | copilot-sdk/apps/purchasing/backend/app/factors/expected_demand.py:compute | PARTIAL (fixture-backed)
Purchasing | day_of_week | lookup from day-of-week score table | fixture | copilot-sdk/apps/purchasing/backend/app/factors/day_of_week.py:compute | PARTIAL (fixture-backed)
Purchasing | weather_forecast | maps weather condition or normalized weather measurements to category score | connector:OpenMeteo | copilot-sdk/apps/purchasing/backend/app/factors/weather_forecast.py:compute | PARTIAL (fixture-backed)
Purchasing | event_flag | event coverage divided by normal coverage, or explicit flag | fixture | copilot-sdk/apps/purchasing/backend/app/factors/event_flag.py:compute | PARTIAL (fixture-backed)
Purchasing | historical_waste | waste percentage normalized by a 20 percent reference | decision-history | copilot-sdk/apps/purchasing/backend/app/factors/historical_waste.py:compute | PARTIAL (fixture-backed)
Purchasing | supplier_lead_time | one minus lead-time days divided by seven, clamped | connector:QBO | copilot-sdk/apps/purchasing/backend/app/factors/supplier_lead_time.py:compute | PARTIAL (fixture-backed)
Purchasing | price_memory_index | one minus observed price-change count divided by tracked months | connector:FRED | copilot-sdk/apps/purchasing/backend/app/factors/price_memory_index.py:compute | PARTIAL (fixture-backed)
DataOps | impact_scope | graph traversal aggregates affected systems and impact scope | graph-store | copilot-sdk/apps/dataops/backend/app/di_config.py:DEFAULT_FACTOR_TO_SOURCE_MAP | PARTIAL (fixture-backed)
DataOps | source_reliability | source reliability value from SAP source mapping or seed data | connector:SAP | copilot-sdk/apps/dataops/backend/app/di_config.py:DEFAULT_FACTOR_TO_SOURCE_MAP | PARTIAL (fixture-backed)
DataOps | recurrence_frequency | alert-history recurrence count mapped to a factor | decision-history | copilot-sdk/apps/dataops/backend/app/di_config.py:DEFAULT_FACTOR_TO_SOURCE_MAP | PARTIAL (fixture-backed)
DataOps | downstream_urgency | pipeline graph downstream criticality mapping | graph-store | copilot-sdk/apps/dataops/backend/app/di_config.py:DEFAULT_FACTOR_TO_SOURCE_MAP | PARTIAL (fixture-backed)
DataOps | data_freshness | Airflow metadata freshness value | connector:Airflow | copilot-sdk/apps/dataops/backend/app/di_config.py:DEFAULT_FACTOR_TO_SOURCE_MAP | PARTIAL (fixture-backed)
DataOps | business_criticality | configured business criticality value | fixture | copilot-sdk/apps/dataops/backend/app/di_config.py:DEFAULT_FACTOR_TO_SOURCE_MAP | PARTIAL (fixture-backed)
S2P | match_status | compares invoice amount/quantity with PO and goods receipt, or uses approval/category fallback | graph-store | s2p-copilot/backend/app/domains/s2p/factors.py:MatchStatus.compute | PARTIAL (fixture-backed)
S2P | amount_variance_ratio | absolute invoice-to-PO or invoice-to-history variance ratio | graph-store | s2p-copilot/backend/app/domains/s2p/factors.py:AmountVarianceRatio.compute | PARTIAL (fixture-backed)
S2P | duplicate_score | maximum amount similarity among neighboring invoices | graph-store | s2p-copilot/backend/app/domains/s2p/factors.py:DuplicateScore.compute | PARTIAL (fixture-backed)
S2P | supplier_exception_history | supplier exception rate or inverse supplier risk rating | graph-store | s2p-copilot/backend/app/domains/s2p/factors.py:SupplierExceptionHistory.compute | PARTIAL (fixture-backed)
S2P | payment_terms_impact | normalized deviation of actual payment days from standard terms | graph-store | s2p-copilot/backend/app/domains/s2p/factors.py:PaymentTermsImpact.compute | PARTIAL (fixture-backed)
S2P | commodity_index_correlation | reads commodity volatility from neighboring commodity node | graph-store | s2p-copilot/backend/app/domains/s2p/factors.py:CommodityIndexCorrelation.compute | PARTIAL (fixture-backed)
S2P | tax_regulatory_compliance | proportion of tax/compliance checks passed, with metadata fallback | graph-store | s2p-copilot/backend/app/domains/s2p/factors.py:TaxRegulatoryCompliance.compute | PARTIAL (fixture-backed)
S2P | environmental_risk | reads environmental risk, footprint, or route-weather risk | graph-store | s2p-copilot/backend/app/domains/s2p/factors.py:EnvironmentalRisk.compute | PARTIAL (fixture-backed)

PART 3 - OUTBOUND DELIVERY / NOTIFICATION
COMPONENT | DELIVERY SURFACE | CHANNEL | EVIDENCE | STATUS
GAE | NONE | - | - | ABSENT
copilot-sdk | NONE | - | - | ABSENT
SOC | NONE | - | - | ABSENT
Trading | Alpaca order execution | HTTPS API write | copilot-sdk/apps/trading/backend/app/brokers/alpaca.py:AlpacaBroker.submit_order | BUILT
Trading | SDK decision export | local JSON or CSV file | copilot-sdk/apps/trading/backend/app/cli_sdk.py:export_sdk | BUILT
Purchasing | Audit export | downloadable JSON or CSV response | copilot-sdk/apps/purchasing/backend/app/services/audit_export.py:AuditExportService | BUILT
DataOps | NONE | - | - | ABSENT
S2P | Centroid export | JSON or CSV HTTP response | s2p-copilot/backend/app/routers/s2p_explorer.py:export_centroids_csv | BUILT
S2P | Optimizer export | JSON export for optimizer consumers | s2p-copilot/backend/app/services/optimizer_export.py:OptimizerExportService.export | BUILT

CONNECTORS FOUND=31, FACTORS COVERED=37, COMPONENTS WITH OUTBOUND DELIVERY=3
