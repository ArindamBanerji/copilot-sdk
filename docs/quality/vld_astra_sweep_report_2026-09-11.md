# VLD-ASTRA-SWEEP — offline real-component validation

Generated: 2026-09-11T21:15:30.032255+00:00

Scope: real CompoundingScorer and EvidenceProvider code with local checkpoint snapshots and real showcase seed functions. No live AGE or running-app state is certified. Ground truth below means the preseed's claimed action, not an independently verified outcome. All scenario matrix runs request budget=2; omitted-budget router behavior is shown separately.

Authority note: MAP VLD Addendum v12 was not found. The supplied sweep prompt defines the gate; the historical mock audit is `copilot-sdk/docs/quality/frontend_wiring_and_mock_audit.md:21`.

## 1 — Per-copilot scenario matrix

### soc

Centroids: **real preset bootstrap prior**, shape [6, 4, 6]; 0 checkpoints, 0 decisions, 0 verified. Sigma: router unit-vector fallback (not learned sigma); tau=0.1. Sources: `copilot-sdk/copilot_sdk/scoring/scorer.py:320`, `copilot-sdk/copilot_sdk/backend/investigation_router.py:178`.

Database: `None`; latest checkpoint: `None`. Construction: CompoundingScorer.from_preset(profile='test', enable_rl=False); no app startup/bootstrap calibration.

Evidence scope: real registered showcase evidence; no backing graph/data client; unregistered reads are offline-unavailable. Identical action centroids by category: `{"credential_access": false, "malware_execution": false, "lateral_movement": false, "data_exfiltration": false, "insider_threat": false, "cloud_infrastructure": false}`. Identical action centroids force tied probabilities and zero margins; changing evidence alone cannot separate those actions.

| Scenario | Surface act | Surf margin | VLD act | VLD margin | Flip? | Claimed | MATCH | Steps taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-SOC-1 | investigate | 0.40832728 | investigate | 0.89766652 | False | monitor -> escalate | False | privileged_identity_context(0.6000->0.8944) |
| VLD-SOC-2 | investigate | 0.40854915 | investigate | 0.40854915 | False | monitor -> escalate | False | none |
| VLD-SOC-S1 | escalate | 0.14886927 | escalate | 0.14886927 | False | escalate -> escalate | True | none |

**VLD-SOC-1** — seed `gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:10`; provider `gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:75`.

Real reads by dimension (including None): `{"0": {"confidence": 0.92, "source": "identity_graph", "value": 0.92}, "1": null, "2": null, "3": null, "4": null, "5": null}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 2, "empty": true}]`. Narrative dimensions: [0]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=None, budget=2, attempts=2, final=investigate. Fragile at <=0.05: False; below 0.02: False.

**P0 PRESEED MISMATCH:** claimed monitor -> escalate; actual investigate -> investigate.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

**VLD-SOC-2** — seed `gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:30`; provider `gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:75`.

Real reads by dimension (including None): `{"0": null, "1": null, "2": null, "3": {"confidence": 0.85, "source": "historical_db", "value": 0.9}, "4": null, "5": null}`

Attempted order: `[{"dim": 0, "empty": true}, {"dim": 5, "empty": true}]`. Narrative dimensions: [2, 3]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=None, budget=2, attempts=2, final=investigate. Fragile at <=0.05: False; below 0.02: False.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**P0 PRESEED MISMATCH:** claimed monitor -> escalate; actual investigate -> investigate.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

**VLD-SOC-S1** — seed `gen-ai-roi-demo-v4-v50/backend/app/vld_preseed.py:48`; provider `gen-ai-roi-demo-v4-v50/backend/app/evidence_provider.py:75`.

Real reads by dimension (including None): `{"0": null, "1": null, "2": null, "3": null, "4": null, "5": null}`

Attempted order: `[{"dim": 5, "empty": true}, {"dim": 1, "empty": true}]`. Narrative dimensions: []; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=None, budget=2, attempts=2, final=escalate. Fragile at <=0.05: False; below 0.02: False.

**P0 S1 CONTRACT:** surface margin=0.14886927; omitted-budget allocation=2, situation=None. Claimed high-margin/no-investigation behavior is not satisfied.

### trading

Centroids: **local SQLite checkpoint**, shape [5, 4, 10]; 5 checkpoints, 800 decisions, 223 verified. Sigma: router unit-vector fallback (not learned sigma); tau=0.1. Sources: `copilot-sdk/copilot_sdk/scoring/scorer.py:320`, `copilot-sdk/copilot_sdk/backend/investigation_router.py:178`.

Database: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\trading\backend\data\trading.db`; latest checkpoint: `{'id': 5, 'created_at': 1700720000.0, 'factor_names_hash': ''}`. Construction: CompoundingScorer.from_preset(profile='test', enable_rl=False); no app startup/bootstrap calibration.

Evidence scope: real registered showcase evidence; no backing graph/data client; unregistered reads are offline-unavailable. Identical action centroids by category: `{"trend_following": true, "mean_reversion": true, "event_driven": true, "income_strategy": true, "scalp_intraday": true}`. Identical action centroids force tied probabilities and zero margins; changing evidence alone cannot separate those actions.

| Scenario | Surface act | Surf margin | VLD act | VLD margin | Flip? | Claimed | MATCH | Steps taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-TRD-1 | strong_execution | 0.00000000 | strong_execution | 0.00000000 | False | strong_execution -> poor_execution | False | market_regime(0.3500->0.8270) |
| VLD-TRD-2 | strong_execution | 0.00000000 | strong_execution | 0.00000000 | False | strong_execution -> skip_recommended | False | market_regime(0.4000->0.7344) |
| VLD-TRD-S1 | strong_execution | 0.00000000 | strong_execution | 0.00000000 | False | skip_recommended -> skip_recommended | False | none |

**VLD-TRD-1** — seed `copilot-sdk/apps/trading/backend/app/vld_preseed.py:10`; provider `copilot-sdk/apps/trading/backend/app/evidence_provider.py:63`.

Real reads by dimension (including None): `{"0": null, "1": {"confidence": 0.9, "source": "correlation_engine", "value": 0.88}, "2": null, "3": {"confidence": 0.85, "source": "momentum_tracker", "value": 0.25}, "4": null, "5": null, "6": null, "7": null, "8": null, "9": null}`

Attempted order: `[{"dim": 0, "empty": true}, {"dim": 1, "empty": false}]`. Narrative dimensions: [1, 3]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=None, budget=2, attempts=2, final=strong_execution. Fragile at <=0.05: True; below 0.02: True.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**P0 PRESEED MISMATCH:** claimed strong_execution -> poor_execution; actual strong_execution -> strong_execution.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

**VLD-TRD-2** — seed `copilot-sdk/apps/trading/backend/app/vld_preseed.py:22`; provider `copilot-sdk/apps/trading/backend/app/evidence_provider.py:63`.

Real reads by dimension (including None): `{"0": null, "1": {"confidence": 0.88, "source": "correlation_engine", "value": 0.78}, "2": {"confidence": 0.92, "source": "portfolio_engine", "value": 0.85}, "3": null, "4": null, "5": null, "6": null, "7": null, "8": null, "9": null}`

Attempted order: `[{"dim": 0, "empty": true}, {"dim": 1, "empty": false}]`. Narrative dimensions: [2, 1]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=None, budget=2, attempts=2, final=strong_execution. Fragile at <=0.05: True; below 0.02: True.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**P0 PRESEED MISMATCH:** claimed strong_execution -> skip_recommended; actual strong_execution -> strong_execution.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

**VLD-TRD-S1** — seed `copilot-sdk/apps/trading/backend/app/vld_preseed.py:34`; provider `copilot-sdk/apps/trading/backend/app/evidence_provider.py:63`.

Real reads by dimension (including None): `{"0": null, "1": null, "2": null, "3": null, "4": null, "5": null, "6": null, "7": null, "8": null, "9": null}`

Attempted order: `[{"dim": 0, "empty": true}, {"dim": 1, "empty": true}]`. Narrative dimensions: []; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=None, budget=2, attempts=2, final=strong_execution. Fragile at <=0.05: False; below 0.02: False.

**P0 S1 CONTRACT:** surface margin=0.00000000; omitted-budget allocation=2, situation=None. Claimed high-margin/no-investigation behavior is not satisfied.

**P0 PRESEED MISMATCH:** claimed skip_recommended -> skip_recommended; actual strong_execution -> strong_execution.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

### purchasing

Centroids: **local SQLite checkpoint**, shape [5, 4, 7]; 5 checkpoints, 801 decisions, 457 verified. Sigma: router unit-vector fallback (not learned sigma); tau=0.1. Sources: `copilot-sdk/copilot_sdk/scoring/scorer.py:320`, `copilot-sdk/copilot_sdk/backend/investigation_router.py:178`.

Database: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\purchasing\backend\data\purchasing.db`; latest checkpoint: `{'id': 5, 'created_at': 1700720000.0, 'factor_names_hash': ''}`. Construction: CompoundingScorer.from_preset(profile='test', enable_rl=False); no app startup/bootstrap calibration.

Evidence scope: real in-memory showcase seed; same source type supplied by application startup. Identical action centroids by category: `{"protein": true, "produce": true, "dairy": true, "dry_goods": true, "beverages": true}`. Identical action centroids force tied probabilities and zero margins; changing evidence alone cannot separate those actions.

| Scenario | Surface act | Surf margin | VLD act | VLD margin | Flip? | Claimed | MATCH | Steps taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-PUR-DEMAND-SPIKE | order_as_planned | 0.00000000 | order_as_planned | 0.00000000 | False | order_more -> order_less | False | expected_demand(0.8000->0.8000); day_of_week(0.5000->0.5000) |
| VLD-PUR-VENDOR-CASCADE | order_as_planned | 0.00000000 | order_as_planned | 0.00000000 | False | order_as_planned -> skip | False | expected_demand(0.4000->0.4000); day_of_week(0.5000->0.5000) |
| VLD-PUR-S1-STANDARD | order_as_planned | 0.00000000 | order_as_planned | 0.00000000 | False | order_as_planned -> order_as_planned | True | expected_demand(0.5800->0.5800); day_of_week(0.5000->0.5000) |

**VLD-PUR-DEMAND-SPIKE** — seed `copilot-sdk/apps/purchasing/backend/app/vld_preseed.py:63`; provider `copilot-sdk/apps/purchasing/backend/app/evidence_provider.py:25`.

Real reads by dimension (including None): `{"0": {"confidence": 0.86, "forecast_units": 320, "inventory_units": 38, "safety_stock_units": 90, "source": "demand_forecast", "value": 0.8}, "1": {"confidence": 0.65, "source": "calendar", "value": 0.5}, "2": {"confidence": 0.65, "source": "weather_service", "value": 0.5}, "3": {"confidence": 0.65, "source": "event_calendar", "value": 0.5}, "4": {"confidence": 0.65, "source": "vendor_tracker", "value": 0.5}, "5": {"backlog_days": 21, "baseline_days": 5, "confidence": 0.9, "current_days": 21, "source": "lead_time_tracker", "stretch_pct": null, "value": 0.25}, "6": {"alternate_lead_days": 2, "alternate_vendor": "Rapid Components", "confidence": 0.8, "premium_pct": 0.08, "source": "vendor_catalog", "value": 0.82}}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 1, "empty": false}]`. Narrative dimensions: [5, 6]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S6, budget=4, attempts=4, final=order_as_planned. Fragile at <=0.05: True; below 0.02: True.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**P0 PRESEED MISMATCH:** claimed order_more -> order_less; actual order_as_planned -> order_as_planned.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

**VLD-PUR-VENDOR-CASCADE** — seed `copilot-sdk/apps/purchasing/backend/app/vld_preseed.py:108`; provider `copilot-sdk/apps/purchasing/backend/app/evidence_provider.py:25`.

Real reads by dimension (including None): `{"0": {"confidence": 0.7, "source": "demand_forecast", "value": 0.4}, "1": {"confidence": 0.65, "source": "calendar", "value": 0.5}, "2": {"confidence": 0.65, "source": "weather_service", "value": 0.5}, "3": {"confidence": 0.65, "source": "event_calendar", "value": 0.5}, "4": {"confidence": 0.88, "notes": "Two seal-failure incidents in the last 30 days.", "quality_incidents_30d": 2, "reliability_score": 0.28, "source": "vendor_tracker", "value": 0.72}, "5": {"backlog_days": null, "baseline_days": 7.0, "confidence": 0.85, "current_days": 9.8, "source": "lead_time_tracker", "stretch_pct": 0.4, "value": 0.72}, "6": {"confidence": 0.65, "source": "cost_benchmark", "value": 0.55}}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 1, "empty": false}]`. Narrative dimensions: [4, 5]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S6, budget=4, attempts=4, final=order_as_planned. Fragile at <=0.05: True; below 0.02: True.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**P0 PRESEED MISMATCH:** claimed order_as_planned -> skip; actual order_as_planned -> order_as_planned.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

**VLD-PUR-S1-STANDARD** — seed `copilot-sdk/apps/purchasing/backend/app/vld_preseed.py:140`; provider `copilot-sdk/apps/purchasing/backend/app/evidence_provider.py:25`.

Real reads by dimension (including None): `{"0": {"confidence": 0.7, "source": "demand_forecast", "value": 0.58}, "1": {"confidence": 0.65, "source": "calendar", "value": 0.5}, "2": {"confidence": 0.65, "source": "weather_service", "value": 0.5}, "3": {"confidence": 0.65, "source": "event_calendar", "value": 0.5}, "4": {"confidence": 0.65, "source": "vendor_tracker", "value": 0.2}, "5": {"confidence": 0.65, "source": "lead_time_tracker", "value": 0.2}, "6": {"confidence": 0.65, "source": "cost_benchmark", "value": 0.84}}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 1, "empty": false}]`. Narrative dimensions: []; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S6, budget=4, attempts=4, final=order_as_planned. Fragile at <=0.05: False; below 0.02: False.

**P0 S1 CONTRACT:** surface margin=0.00000000; omitted-budget allocation=4, situation=S6. Claimed high-margin/no-investigation behavior is not satisfied.

### dataops

Centroids: **local SQLite checkpoint**, shape [6, 5, 6]; 219 checkpoints, 720 decisions, 388 verified. Sigma: router unit-vector fallback (not learned sigma); tau=0.1. Sources: `copilot-sdk/copilot_sdk/scoring/scorer.py:320`, `copilot-sdk/copilot_sdk/backend/investigation_router.py:178`.

Database: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\dataops\backend\data\dataops.db`; latest checkpoint: `{'id': 219, 'created_at': 1779171270.8414052, 'factor_names_hash': ''}`. Construction: CompoundingScorer.from_preset(profile='test', enable_rl=False); no app startup/bootstrap calibration.

Evidence scope: real fixture loader plus in-memory showcase seed. Identical action centroids by category: `{"schema_change": false, "volume_anomaly": false, "quality_anomaly": false, "freshness_violation": false, "pipeline_failure": false, "transform_drift": false}`. Identical action centroids force tied probabilities and zero margins; changing evidence alone cannot separate those actions.

| Scenario | Surface act | Surf margin | VLD act | VLD margin | Flip? | Claimed | MATCH | Steps taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-DO-1 | escalate_to_owner | 0.29536041 | escalate_to_owner | 0.86376876 | False | investigate -> escalate_to_owner | False | source_reliability(0.5500->0.4500); business_criticality(0.7000->0.8400) |
| VLD-DO-2 | refer_to_specialist | 0.61737901 | escalate_to_owner | 0.80140743 | True | refer_to_specialist -> escalate_to_owner | True | downstream_urgency(0.2000->0.7576); source_reliability(0.3500->0.4500) |
| VLD-DO-S1 | auto_approve | 0.99855883 | auto_approve | 0.99855883 | False | auto_approve -> auto_approve | True | none |

**VLD-DO-1** — seed `copilot-sdk/apps/dataops/backend/app/vld_preseed.py:11`; provider `copilot-sdk/apps/dataops/backend/app/evidence_provider.py:38`.

Real reads by dimension (including None): `{"0": {"change_type": "schema_expansion", "column": "MATKL_V2", "confidence": 0.92, "impacted_systems": ["pricing_engine", "inventory_sync", "billing_api"], "join_fanout_factor": 9.0, "source": "schema_registry", "value": 0.9}, "1": {"confidence": 0.86, "source": "pipeline_monitor", "status": "degraded", "system": "order_ingestion", "value": 0.45}, "2": {"confidence": 0.85, "known_resolution": null, "pattern": null, "prior_count": 2, "source": "historical_alerts", "value": 0.3}, "3": {"confidence": 0.88, "downstream_systems": ["pricing_engine", "inventory_sync", "billing_api"], "new_upstream_dependencies": [], "source": "dependency_graph", "upstream_systems": [], "value": 0.85}, "4": {"confidence": 0.82, "correlated_alerts": ["pricing_engine_latency", "inventory_sync_retries", "billing_api_errors"], "source": "alert_correlator", "value": 0.72}, "5": {"affected_systems": ["pricing_engine", "inventory_sync", "billing_api"], "affected_systems_count": 3, "confidence": 0.8, "source": "impact_analysis", "value": 0.84}}`

Attempted order: `[{"dim": 1, "empty": false}, {"dim": 5, "empty": false}]`. Narrative dimensions: [0, 3]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S3, budget=1, attempts=1, final=escalate_to_owner. Fragile at <=0.05: False; below 0.02: False.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**P0 PRESEED MISMATCH:** claimed investigate -> escalate_to_owner; actual escalate_to_owner -> escalate_to_owner.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

**VLD-DO-2** — seed `copilot-sdk/apps/dataops/backend/app/vld_preseed.py:12`; provider `copilot-sdk/apps/dataops/backend/app/evidence_provider.py:38`.

Real reads by dimension (including None): `{"0": null, "1": {"confidence": 0.86, "source": "pipeline_monitor", "status": "degraded", "system": "billing_api", "value": 0.45}, "2": {"confidence": 0.55, "known_resolution": "Rebuild billing validation cache", "pattern": "billing_quality_drop", "prior_count": 8, "source": "historical_alerts", "value": 0.65}, "3": {"confidence": 0.82, "downstream_systems": ["revenue_mart", "customer_invoices"], "new_upstream_dependencies": ["data_lake_v2"], "source": "dependency_graph", "upstream_systems": ["payments_hourly"], "value": 0.88}, "4": {"confidence": 0.74, "correlated_alerts": ["revenue_mart_missing_rows", "invoice_export_retries"], "source": "alert_correlator", "value": 0.64}, "5": null}`

Attempted order: `[{"dim": 3, "empty": false}, {"dim": 1, "empty": false}]`. Narrative dimensions: [2, 3]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S3, budget=1, attempts=1, final=escalate_to_owner. Fragile at <=0.05: False; below 0.02: False.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**VLD-DO-S1** — seed `copilot-sdk/apps/dataops/backend/app/vld_preseed.py:13`; provider `copilot-sdk/apps/dataops/backend/app/evidence_provider.py:38`.

Real reads by dimension (including None): `{"0": null, "1": {"confidence": 0.86, "source": "pipeline_monitor", "status": "ok", "system": "staging_etl", "value": 0.92}, "2": {"confidence": 0.85, "known_resolution": null, "pattern": null, "prior_count": 0, "source": "historical_alerts", "value": 0.05}, "3": null, "4": null, "5": null}`

Attempted order: `[{"dim": 0, "empty": true}, {"dim": 4, "empty": true}]`. Narrative dimensions: []; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S3, budget=1, attempts=1, final=auto_approve. Fragile at <=0.05: False; below 0.02: False.

**P0 S1 CONTRACT:** surface margin=0.99855883; omitted-budget allocation=1, situation=S3. Claimed high-margin/no-investigation behavior is not satisfied.

### s2p

Centroids: **local SQLite checkpoint**, shape [5, 5, 8]; 174 checkpoints, 871 decisions, 160 verified. Sigma: router unit-vector fallback (not learned sigma); tau=0.1. Sources: `copilot-sdk/copilot_sdk/scoring/scorer.py:320`, `copilot-sdk/copilot_sdk/backend/investigation_router.py:178`.

Database: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot\backend\app\data\s2p.db`; latest checkpoint: `{'id': 174, 'created_at': 1785586175.2645347, 'factor_names_hash': '7a56aae292b46ee04a0bb1d71aed2f6b4966478a3d3a4b5b143c80373fc49aa2'}`. Construction: CompoundingScorer.from_preset(profile='test', enable_rl=False); no app startup/bootstrap calibration.

Evidence scope: real in-memory showcase seed; same source type supplied by application startup. Identical action centroids by category: `{"price_variance": false, "quantity_mismatch": false, "duplicate_risk": false, "contract_gap": false, "format_compliance": false}`. Identical action centroids force tied probabilities and zero margins; changing evidence alone cannot separate those actions.

| Scenario | Surface act | Surf margin | VLD act | VLD margin | Flip? | Claimed | MATCH | Steps taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VLD-S2P-1 | hold_for_review | 0.55262529 | hold_for_review | 0.22103431 | False | hold_for_review -> auto_approve | False | match_status(0.7800->0.9500) |
| VLD-S2P-2 | flag_leakage | 0.25905874 | flag_leakage | 0.39555448 | False | flag_leakage -> auto_approve | False | match_status(0.8000->0.9300); supplier_exception_history(0.2000->0.0732) |
| VLD-S2P-S1 | auto_approve | 0.87438733 | auto_approve | 0.89154808 | False | auto_approve -> auto_approve | True | match_status(0.9500->0.9800) |

**VLD-S2P-1** — seed `s2p-copilot/backend/app/vld_preseed.py:65`; provider `s2p-copilot/backend/app/evidence_provider.py:28`.

Real reads by dimension (including None): `{"0": {"clause": "Partial delivery may auto-approve when verified supplier history is clean.", "confidence": 0.9, "contract_ref": "CTR-ASTER-PARTIAL", "coverage_score": 0.95, "dimension": 0, "factor_name": "match_status", "invoice_id": "VLD-S2P-1", "source": "contract_db", "value": 0.95}, "1": {"confidence": 0.75, "dimension": 1, "factor_name": "amount_variance_ratio", "invoice_id": "VLD-S2P-1", "source": "pricing_benchmark", "value": 0.22}, "2": {"confidence": 0.82, "dimension": 2, "factor_name": "duplicate_score", "invoice_id": "VLD-S2P-1", "source": "invoice_history", "value": 0.08}, "3": {"confidence": 0.8214285714285714, "dimension": 3, "factor_name": "supplier_exception_history", "invoice_id": "VLD-S2P-1", "partial_delivery_pricing_error_ratio": 3.1, "source": "supplier_history", "trust_score": 0.82, "value": 0.03, "verified_priors": 23}, "4": {"confidence": 0.8, "dimension": 4, "factor_name": "payment_terms_impact", "invoice_id": "VLD-S2P-1", "payment_terms": "Net 45", "source": "payment_terms", "value": 0.82}, "5": null, "6": {"confidence": 0.8, "dimension": 6, "factor_name": "tax_regulatory_compliance", "flags": [], "invoice_id": "VLD-S2P-1", "source": "compliance_db", "value": 0.8}, "7": {"confidence": 0.65, "dimension": 7, "factor_name": "environmental_risk", "invoice_id": "VLD-S2P-1", "source": "compliance_db", "value": 0.5}}`

Attempted order: `[{"dim": 5, "empty": true}, {"dim": 0, "empty": false}]`. Narrative dimensions: [3, 0]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S1, budget=0, attempts=0, final=hold_for_review. Fragile at <=0.05: False; below 0.02: False.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**P0 PRESEED MISMATCH:** claimed hold_for_review -> auto_approve; actual hold_for_review -> hold_for_review.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[{"dimension": 5, "factor_name": "commodity_index_correlation", "current_final_factor": 0.58, "nearest_grid_factor": 0.68, "absolute_change": 0.10000000000000009}, {"dimension": 1, "factor_name": "amount_variance_ratio", "current_final_factor": 0.22, "nearest_grid_factor": 0.1, "absolute_change": 0.12}, {"dimension": 3, "factor_name": "supplier_exception_history", "current_final_factor": 0.25, "nearest_grid_factor": 0.03, "absolute_change": 0.22}, {"dimension": 4, "factor_name": "payment_terms_impact", "current_final_factor": 0.45, "nearest_grid_factor": 0.78, "absolute_change": 0.33}]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

**VLD-S2P-2** — seed `s2p-copilot/backend/app/vld_preseed.py:96`; provider `s2p-copilot/backend/app/evidence_provider.py:28`.

Real reads by dimension (including None): `{"0": {"clause": "Bulk pricing pass-through activates above 2x forecast volume.", "confidence": 0.9, "contract_ref": "CTR-MERIDIAN-BULK", "coverage_score": 0.93, "dimension": 0, "factor_name": "match_status", "invoice_id": "VLD-S2P-2", "source": "contract_db", "value": 0.93}, "1": {"benchmark_delta_pct": 18.0, "confidence": 0.82, "dimension": 1, "factor_name": "amount_variance_ratio", "invoice_id": "VLD-S2P-2", "sample_size": 41, "source": "pricing_benchmark", "value": 0.05}, "2": {"confidence": 0.82, "dimension": 2, "factor_name": "duplicate_score", "invoice_id": "VLD-S2P-2", "source": "invoice_history", "value": 0.1}, "3": {"confidence": 1.0, "dimension": 3, "factor_name": "supplier_exception_history", "invoice_id": "VLD-S2P-2", "source": "supplier_history", "trust_score": 0.926829268292683, "value": 0.07317073170731707, "verified_priors": 41}, "4": {"confidence": 0.8, "dimension": 4, "factor_name": "payment_terms_impact", "invoice_id": "VLD-S2P-2", "payment_terms": "Net 60", "source": "payment_terms", "value": 0.82}, "5": {"confidence": 0.78, "dimension": 5, "explanation": "Rush order exceeds the 2x bulk-pricing threshold.", "factor_name": "commodity_index_correlation", "invoice_id": "VLD-S2P-2", "source": "demand_forecast", "value": 0.82, "volume_multiplier": 3.0}, "6": {"confidence": 0.8, "dimension": 6, "factor_name": "tax_regulatory_compliance", "flags": [], "invoice_id": "VLD-S2P-2", "source": "compliance_db", "value": 0.8}, "7": {"confidence": 0.65, "dimension": 7, "factor_name": "environmental_risk", "invoice_id": "VLD-S2P-2", "source": "compliance_db", "value": 0.5}}`

Attempted order: `[{"dim": 0, "empty": false}, {"dim": 3, "empty": false}]`. Narrative dimensions: [1, 5]; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S3, budget=1, attempts=1, final=flag_leakage. Fragile at <=0.05: False; below 0.02: False.

**P0 NARRATIVE ROUTING MISMATCH:** the actual attempted dimensions do not follow the claimed investigation branch. An action match alone does not validate the demo's evidence story.

**P0 PRESEED MISMATCH:** claimed flag_leakage -> auto_approve; actual flag_leakage -> flag_leakage.

One-dimension final-factor sensitivity (0.01 grid; other final factors held fixed; NOT real evidence, NOT a routed replay or proposed seed fix): `[{"dimension": 5, "factor_name": "commodity_index_correlation", "current_final_factor": 0.2, "nearest_grid_factor": 0.85, "absolute_change": 0.6499999999999999}]`. An empty list means no single-factor grid candidate reaches the claimed action at margin >0.05. Surface mismatches cannot be repaired by evidence read after surface scoring.

**VLD-S2P-S1** — seed `s2p-copilot/backend/app/vld_preseed.py:132`; provider `s2p-copilot/backend/app/evidence_provider.py:28`.

Real reads by dimension (including None): `{"0": {"clause": "Standard matched invoice auto-approval.", "confidence": 0.95, "contract_ref": "CTR-NORTHSTAR-STANDARD", "dimension": 0, "factor_name": "match_status", "invoice_id": "VLD-S2P-S1", "source": "contract_db", "value": 0.98}, "1": {"confidence": 0.75, "dimension": 1, "factor_name": "amount_variance_ratio", "invoice_id": "VLD-S2P-S1", "source": "pricing_benchmark", "value": 0.05}, "2": {"confidence": 0.82, "dimension": 2, "factor_name": "duplicate_score", "invoice_id": "VLD-S2P-S1", "source": "invoice_history", "value": 0.02}, "3": {"confidence": 1.0, "dimension": 3, "factor_name": "supplier_exception_history", "invoice_id": "VLD-S2P-S1", "source": "supplier_history", "trust_score": 0.9875, "value": 0.0125, "verified_priors": 80}, "4": {"confidence": 0.8, "dimension": 4, "factor_name": "payment_terms_impact", "invoice_id": "VLD-S2P-S1", "payment_terms": "Net 45", "source": "payment_terms", "value": 0.82}, "5": null, "6": {"confidence": 0.8, "dimension": 6, "factor_name": "tax_regulatory_compliance", "flags": [], "invoice_id": "VLD-S2P-S1", "source": "compliance_db", "value": 0.8}, "7": {"confidence": 0.65, "dimension": 7, "factor_name": "environmental_risk", "invoice_id": "VLD-S2P-S1", "source": "compliance_db", "value": 0.5}}`

Attempted order: `[{"dim": 5, "empty": true}, {"dim": 0, "empty": false}]`. Narrative dimensions: []; missing required evidence: []. Empty reads consume budget but are omitted from core trace steps (`copilot-sdk/copilot_sdk/scoring/investigation.py:138`).

Omitted-budget router: situation=S1, budget=0, attempts=0, final=auto_approve. Fragile at <=0.05: False; below 0.02: False.

## 2 — Summary

| Copilot | Scenarios | Flips claimed | Flips actual | Match | Mismatch | Fragile |
| --- | --- | --- | --- | --- | --- | --- |
| soc | 3 | 2 | 0 | 1 | 2 | 0 |
| trading | 3 | 2 | 0 | 0 | 3 | 2 |
| purchasing | 3 | 2 | 0 | 1 | 2 | 2 |
| dataops | 3 | 2 | 1 | 2 | 1 | 0 |
| s2p | 3 | 2 | 0 | 1 | 2 | 0 |
| TOTAL | 15 | 10 | 1 | 5 | 10 | 4 |

## 3 — K store and classifier status

| Copilot | K store wired | K has data (local) | Classifier wired | Model loaded | Fallback | Source |
| --- | --- | --- | --- | --- | --- | --- |
| soc | False | False | False | False | fixed default budget; no classifier | gen-ai-roi-demo-v4-v50/backend/app/main.py:224 |
| trading | False | False | False | False | fixed default budget; no classifier | copilot-sdk/apps/trading/backend/app/main.py:541 |
| purchasing | False | False | True | False | heuristic d_min classifier | copilot-sdk/apps/purchasing/backend/app/main.py:826 |
| dataops | False | False | True | False | heuristic d_min classifier | copilot-sdk/apps/dataops/backend/app/main.py:934 |
| s2p | False | False | True | False | heuristic d_min classifier | s2p-copilot/backend/app/main.py:324 |

Classifier heuristic: `copilot-sdk/copilot_sdk/scoring/situation_classifier.py:122`; model load: line 95. SOC/Trading have no classifier; high margin alone does not suppress their default budget. K updates require a connected SQL store (`copilot-sdk/copilot_sdk/scoring/investigation.py:194`).

## 4 — Mock divergence inventory

The only MockEvidenceProvider call sites found in SDK/app/SOC/S2P test directories use synthetic SDK d1/cat inputs. Those inputs have no real scenario join, so a numerical delta or substituted-test pass claim would be fabricated. All call sites are listed below, including the client fixture used by router tests.

| Copilot | Test/source | Dim/mock payload | Real value | Delta | Flag |
| --- | --- | --- | --- | --- | --- |
| SDK generic | test_investigate_reads_highest_Q_first (copilot-sdk/tests/test_investigation.py:142) | {expected: {'value': 0.9, 'confidence': 1.0, 'source': 'raw'}} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_stops_at_budget (copilot-sdk/tests/test_investigation.py:148) | {i: {'value': 0.9, 'confidence': 1.0, 'source': 'raw'} for i in range(6)} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_skips_none_evidence (copilot-sdk/tests/test_investigation.py:154) | {1: {'value': 0.9, 'confidence': 1.0, 'source': 'raw'}} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_records_flips (copilot-sdk/tests/test_investigation.py:162) | {0: {'value': 0.95, 'confidence': 1.0, 'source': 'raw'}, 1: {'value': 0.95, 'confidence': 1.0, 'source': 'raw'}} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_recomputes_Q_each_step (copilot-sdk/tests/test_investigation.py:189) | {i: {'value': 0.9, 'confidence': 1.0, 'source': 'raw'} for i in range(6)} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_evidence_provider_protocol_runtime (copilot-sdk/tests/test_investigation.py:81) | {} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | Protocol assertion passes for all five real classes; numeric comparison N/A |
| SDK generic | test_investigate_returns_trace (copilot-sdk/tests/test_investigation.py:133) | {} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_contrast_strip (copilot-sdk/tests/test_investigation.py:169) | {} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_gated_vs_raw_update (copilot-sdk/tests/test_investigation.py:182) | evidence | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_investigate_gated_vs_raw_update (copilot-sdk/tests/test_investigation.py:183) | evidence | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | evidence_factory; fixture consumers: test_router_health:294, test_router_investigate:300, test_router_contrast_fields:308, test_router_with_budget:322, test_router_action_changed_flag:328 (copilot-sdk/tests/test_investigation.py:287) | {0: {'value': 0.95, 'confidence': 1.0, 'source': 'raw'}, 1: {'value': 0.95, 'confidence': 1.0, 'source': 'raw'}} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |
| SDK generic | test_router_no_evidence (copilot-sdk/tests/test_investigation.py:316) | {} | N/A: generic d1/cat and synthetic factor names; no real scenario key | N/A | UNMAPPED; substitution pass/fail not established |

The five domain evidence suites already use real provider classes. Their significant substitutions concern geometry, sigma, K weights, or S1 vectors; replacing a provider alone would leave those substitutions intact.

| Copilot | Test | Actual substitution | Source |
| --- | --- | --- | --- |
| soc | test_vld_soc1_scenario_flips_monitor_to_escalate | hand-built mu and sigma=0.1 | gen-ai-roi-demo-v4-v50/backend/tests/test_soc_evidence.py:128 |
| soc | test_vld_soc2_empty_branch_then_recompute_flips | hand-built mu/sigma; budget=3 | gen-ai-roi-demo-v4-v50/backend/tests/test_soc_evidence.py:146 |
| soc | test_s1_no_investigation_budget_zero | replaces showcase vector with centroid; classifier absent in app | gen-ai-roi-demo-v4-v50/backend/tests/test_soc_evidence.py:164 |
| soc | test_router_investigate_alert | monkeypatches real scorer with FakeScorer | gen-ai-roi-demo-v4-v50/backend/tests/test_soc_evidence.py:185 |
| trading | test_thesis_reversal_flips_enter_to_reduce_or_hedge | hand-built mu and sigma | copilot-sdk/apps/trading/backend/tests/test_trading_evidence.py:114 |
| trading | test_concentration_risk_flips_add_to_hold | hand-built mu and dimension-specific sigma | copilot-sdk/apps/trading/backend/tests/test_trading_evidence.py:129 |
| trading | test_thesis_reversal_trace_order | hand-built mu and sigma | copilot-sdk/apps/trading/backend/tests/test_trading_evidence.py:157 |
| trading | test_s1_conservation_no_investigation | centroid replaces showcase vector; classifier absent in app | copilot-sdk/apps/trading/backend/tests/test_trading_evidence.py:144 |
| trading | test_investigation_endpoint | monkeypatches scorer with FakeScorer | copilot-sdk/apps/trading/backend/tests/test_trading_evidence.py:174 |
| purchasing | test_demand_spike | hand-built mu/sigma/tau and injected K weights | copilot-sdk/apps/purchasing/backend/tests/test_purchasing_evidence.py:77 |
| purchasing | test_vendor_cascade | hand-built mu/sigma/tau and injected K weights | copilot-sdk/apps/purchasing/backend/tests/test_purchasing_evidence.py:86 |
| purchasing | test_demand_spike_trace_order | hand-built mu/sigma/tau and injected K weights | copilot-sdk/apps/purchasing/backend/tests/test_purchasing_evidence.py:126 |
| purchasing | test_s1_conservation | hand-built geometry | copilot-sdk/apps/purchasing/backend/tests/test_purchasing_evidence.py:105 |
| dataops | test_vld_do1_three_systems | preset mu, injected K weights and preset tau | copilot-sdk/apps/dataops/backend/tests/test_dataops_evidence.py:133 |
| dataops | test_vld_do2_known_pattern_new_twist | preset mu, injected K weights and preset tau | copilot-sdk/apps/dataops/backend/tests/test_dataops_evidence.py:155 |
| dataops | test_s1_conservation_skip | centroid replaces showcase vector | copilot-sdk/apps/dataops/backend/tests/test_dataops_evidence.py:180 |
| s2p | test_vld_s2p1_supplier_it_knew | domain-config mu/tau and injected K weights | s2p-copilot/backend/tests/test_s2p_evidence.py:66 |
| s2p | test_vld_s2p2_price_spike_context | domain-config mu/tau and injected K weights | s2p-copilot/backend/tests/test_s2p_evidence.py:80 |
| s2p | test_investigation_endpoint | custom Scorer wrapper over config; asserts response structure | s2p-copilot/backend/tests/test_s2p_evidence.py:114 |

Provider-value comparison: SOC/Trading seeded values equal their registered real-provider values; Purchasing/DataOps/S2P tests read the same real seeded source. No comparable numeric mock-provider divergence >0.1 was established. UNMAPPED entries remain unmeasured, not zero-distance observations.

## 5 — Gate verdict

- **ALL_FLIPS_MATCH:** False
- **ALL_MARGINS_STABLE:** False
- **MOCK_DIVERGENCE_COUNT:** 0
- **MOCK_COMPARISON_STATUS:** generic mock cases unmapped; numeric count is not a clean bill
- **K_STORE_EXERCISED:** False
- **CLASSIFIER_MODEL_LOADED:** False
- **HURTS:** 0
- **COMPLETE:** True
- **ALL_NARRATIVE_READS_MATCH:** False
- **ALL_S1_BUDGETS_ZERO:** False
- **PAPER_READY:** False
- **DEMO_READY:** False
- **LIVE_AGE_VALIDATED:** False

PAPER_READY/DEMO_READY apply only to the prompt's 15 showcase contracts. They do not establish empirical routing accuracy, independent ground truth, or live AGE fidelity. Missing domains fail completeness.

Baseline at implementation gate: SDK 3402 passed; VLD core 30, DataOps 14, Trading 13, Purchasing 13 passed. These are recorded pre-sweep results, not tests rerun by this report.

- Current SHA-256 `copilot_sdk/scoring/investigation.py`: `a1531aea56125475f29cebec64b197a500a7a82bdf56fa1caa1c567ca9c8672a`
- Current SHA-256 `copilot_sdk/backend/investigation_router.py`: `f30767bc7080196a358569a16b34ac8159c6250aca3d3fc6244368067bfc8e90`

## Recorded sweep execution results

The five sections above were regenerated from the existing report generator when this Markdown document was saved. The test results below record the completed VLD-ASTRA-SWEEP session; saving this document did not rerun pytest.

| Check | Result |
| --- | --- |
| PRE-1: original SDK root baseline | 3,402 passed |
| PRE-2: SDK VLD core | 30 passed |
| PRE-2: DataOps evidence suite | 14 passed |
| PRE-2: Trading evidence suite | 13 passed |
| PRE-2: Purchasing evidence suite | 13 passed |
| POST-1: new integration suite (31 tests, all 15 scenarios exercised) | 14 passed, 17 diagnostic failures |
| POST-2: standalone report generator | All five sections generated successfully |
| POST-3: centroid JSON export | Valid JSON; 5 copilots, all category tensors, 15 scenarios |
| POST-4: existing VLD tests across SDK and all five copilots | 94 passed: SDK 30, SOC 12, Trading 13, Purchasing 13, DataOps 14, S2P 12 |
| POST-5: full SDK root including new diagnostics | 3,416 passed, 17 failed |
| POST-6: production Python integrity | 876 files matched the pre-sweep aggregate hashes; both VLD core hashes matched |

All 17 failures in the full SDK post-check belonged to the new diagnostic suite. The original 3,402 SDK tests remained green. No production fixes, evidence-provider tuning, or preseed changes were made.

### Recorded findings

- Only 1 of the 10 claimed surface-to-final flip pairs matched exactly: DataOps VLD-DO-2. Its evidence-read sequence still differed from the narrative.
- Across all 15 scenarios, 5 action pairs matched and 10 did not. Action-pair matching does not establish the S1 budget or narrative-routing contracts.
- Four claimed-flip scenarios had final margins at or below 0.05, all with zero margin in the local Trading/Purchasing snapshots.
- No scenario moved from the seed's claimed correct action to an incorrect action: HURTS=0. These labels are preseed claims, not independently verified outcomes.
- No application investigation router supplied a K store. No classifier model was loaded. Purchasing, DataOps, and S2P used the heuristic classifier; SOC and Trading used a fixed default budget.
- Twelve generic SDK mock constructor sites were inventoried, including five router tests using a shared fixture. Their synthetic identifiers do not provide a valid real-scenario join; numeric mock divergences remain unmeasured.
- PAPER_READY=False and DEMO_READY=False.

### Scope and centroid provenance

This is an offline validation of real Python scorer/provider components. Trading, Purchasing, DataOps, and S2P use read-only copies of local SQLite checkpoints. SOC uses the real preset bootstrap prior because no local SOC checkpoint was available. Every exported category is labelled.

The real investigation-router readers supply unit sigma vectors when the scorer exposes no sigma vector. These fallback values are not learned sigma estimates. SOC/Trading provider runs use registered showcase evidence without a backing graph/data client; unregistered evidence remains offline-unavailable.

The local Trading and Purchasing snapshots have identical action centroids, forcing tied probabilities and zero margins. Evidence-value tuning alone cannot separate identical action centroids.

**Live AGE state and running-application fidelity were not validated.** The paper/demo flags apply to the specified showcase contracts, not empirical routing accuracy or a production-readiness certification.

### Core hash verification

The pre-sweep hashes below were recorded during the completed sweep. Current hashes were read again when this document was saved. The 876-file aggregate check above is the recorded sweep check, not a fresh all-repository comparison.

| File | Pre-sweep SHA-256 | At document save SHA-256 | Match |
| --- | --- | --- | --- |
| `copilot_sdk/scoring/investigation.py` | `a1531aea56125475f29cebec64b197a500a7a82bdf56fa1caa1c567ca9c8672a` | `a1531aea56125475f29cebec64b197a500a7a82bdf56fa1caa1c567ca9c8672a` | True |
| `copilot_sdk/backend/investigation_router.py` | `f30767bc7080196a358569a16b34ac8159c6250aca3d3fc6244368067bfc8e90` | `f30767bc7080196a358569a16b34ac8159c6250aca3d3fc6244368067bfc8e90` | True |

### Artifacts and reproduction

Run these commands from the `copilot-sdk` repository root with the project's Python environment.

- [Integration tests](../../tests/test_vld_integration.py)
- [Markdown report generator](../../tests/vld_validation_report.py)
- [Centroid exporter](../../tests/extract_real_centroids.py)
- [Exported centroid JSON](../../real_centroids_v1.json)

```powershell
python tests/vld_validation_report.py
python -m pytest tests/test_vld_integration.py -v --timeout=180
python tests/extract_real_centroids.py
```

The integration suite intentionally fails on unresolved showcase mismatches. The exporter prints JSON to stdout. No pytest rerun is required merely to read this saved report.
