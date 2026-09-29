# P2 Diagnostic Report — SDK (copilot-sdk)
Date: 2026-09-28
Scanner: P2-DIAG-SDK (terra/high)
Baseline: 3,777 passed, 0 failed, 0 skipped

## Scan Scope

Files scanned: 320

Directories:

- `copilot_sdk/scoring/` — 31 files
- `copilot_sdk/backend/` — 32 files
- `copilot_sdk/evolution/` — 14 files
- `copilot_sdk/demo/` — 5 files
- `apps/trading/backend/app/` — 115 files
- `apps/purchasing/backend/app/` — 82 files
- `apps/dataops/backend/app/` — 41 files
- `apps/s2p/backend/app/` — not present

Known findings excluded: 17 (R01 through R17)

The scan parsed every Python file in scope and inventoried 696 exception handlers, 219 `or []` / `or {}` expressions, and 30 availability/degraded flag assignments. Each candidate below was then traced through its caller and, where present, its HTTP or frontend consumer. Routine input normalization, explicitly labelled fixture fallbacks, fail-closed guards, and the known R01–R17 findings were excluded.

## New Findings

### P2 — User-Visible Data Quality

| ID | File | Line | Function | Pattern | Copilot | Description |
|----|------|------|----------|---------|---------|-------------|
| SDK-P2-N01 | `copilot_sdk/backend/platform_router.py` | 27 | `_verified_decisions` / `_compounding_gain_pp` | 1, 2 | all | Missing, malformed, or failed metric reads become `0` decisions and `0.0` gain in `/platform/domain-applicability`, with no availability flag; consumers cannot distinguish unavailable metrics from real zero performance. |
| SDK-P2-N02 | `copilot_sdk/scoring/verification/price.py` | 37 | `verify_trade` / `_fetch_live_price` | 1, 5 | Trading | A failed live Yahoo read falls back to a seed price, but `verify_trade` labels any positive fallback as `source="live"` and computes correctness from it, so stale seed data is presented as a live verification. |
| SDK-P2-N03 | `copilot_sdk/scoring/presets/trading.py` | 123 | `_load_bootstrap` | 1, 2 | Trading | Any missing, corrupt, or wrong-shaped bootstrap silently becomes an all-`0.5` centroid tensor; scoring continues with fabricated neutral priors and no degraded signal. |
| SDK-P2-N04 | `copilot_sdk/scoring/presets/purchasing.py` | 105 | `_load_bootstrap` | 1, 2 | Purchasing | Any missing, corrupt, or wrong-shaped bootstrap silently becomes an all-`0.5` centroid tensor; purchasing scores therefore look valid although configured priors were unavailable. |
| SDK-P2-N05 | `copilot_sdk/scoring/presets/dataops.py` | 99 | `_load_bootstrap` | 1, 2 | DataOps | Any missing, corrupt, or wrong-shaped bootstrap silently becomes an all-`0.5` centroid tensor, with no availability state carried into DataOps scoring. |
| SDK-P2-N06 | `apps/trading/backend/app/routers/data_import.py` | 171 | `get_ohlcv` / `get_vix` | 2, 4 | Trading | Both market endpoints discard the provider's provenance and collapse `Provenanced.value=None` to empty rows; an unavailable provider is indistinguishable from a valid empty market result. |
| SDK-P2-N07 | `apps/trading/backend/app/factors/registry.py` | 77 | `compute_factors` | 1, 2 | Trading | Every factor-computation exception is replaced with the legitimate neutral score `0.5`; the score response has no per-factor availability state, so a broken factor looks neutrally measured. |
| SDK-P2-N08 | `apps/trading/backend/app/factors/options.py` | 86 | `_fetch_iv_rv` / `compute_options_factors` | 1, 2 | Trading | Missing options dependencies, market-data failures, and factor exceptions converge on neutral `0.5` option factors without provenance or availability, even when the rest of the factor registry succeeds. |
| SDK-P2-N09 | `apps/purchasing/backend/app/routers/par_router.py` | 27 | `_orders` / `_recommendations` / `get_status` | 1, 2, 5 | Purchasing | A QBO read failure becomes an empty recommendation list; `/status` still identifies QuickBooks Online as the source, so an outage appears to be a healthy account with no PAR items. |
| SDK-P2-N10 | `apps/purchasing/backend/app/routers/queue.py` | 34 | `order_queue` / `order_queue_detail` / `_orders` | 1, 2, 5 | Purchasing | QBO file or I/O failure becomes an empty queue labelled `source="quickbooks_online"`; detail requests then return a misleading 404 instead of reporting source unavailability. |
| SDK-P2-N11 | `apps/purchasing/backend/app/services/alert_engine.py` | 59 | `evaluate` / `_supplier_degradation` / `_stockout_risk` | 1, 2 | Purchasing | Scorecard or PAR optimizer failures silently remove two alert classes from the aggregate. The API has no degraded fields, and an empty result makes the frontend display “All clear. No active alerts.” |
| SDK-P2-N12 | `apps/purchasing/backend/app/services/economic_model.py` | 155 | `_service_impacts` / `_read_cost_source` | 1, 3 | Purchasing | A failed cost-impact source is erased as `{}`; if another source succeeds, the aggregate is still labelled `provenance="live"` even though savings are incomplete. |
| SDK-P2-N13 | `apps/purchasing/backend/app/services/predictive_par.py` | 141 | `base_from_optimizer` | 1, 2 | Purchasing | Optimizer failure becomes a plausible 40-unit base PAR. Prediction endpoints use that value as measured input and expose no availability flag, so forecasts can be based on fabricated inventory levels. |
| SDK-P2-N14 | `apps/purchasing/backend/app/services/waste_tracker.py` | 132 | `_waste_pct` / `_quantity` / `_unit_cost` | 1, 2 | Purchasing | Malformed waste, quantity, and cost inputs become legitimate-looking `0.0`, `1.0`, and `4.0` values; waste and savings outputs can therefore look measured while using invented defaults. |
| SDK-P2-N15 | `apps/dataops/backend/app/routers/di_gateway_router.py` | 129 | `_timestamp` | 1 | DataOps | A missing verification timestamp is replaced with the current time, making an undated graph decision appear freshly verified rather than unavailable. |
| SDK-P2-N16 | `apps/dataops/backend/app/ae_router.py` | 237 | `_persisted_rule_lifecycles.event_time` | 1 | DataOps | An unparseable persisted event timestamp becomes epoch zero for sorting; this can reorder lifecycle history and cause `history[-1]` to expose the wrong event as the current rule state. |

### P3 — Internal Observability / Type Contract

| ID | File | Line | Function | Pattern | Copilot | Description |
|----|------|------|----------|---------|---------|-------------|
| SDK-P3-N01 | `copilot_sdk/backend/models.py` | 231 | `EvolutionVariantsResponse` | 2 | all | `data_available` and `degraded` are `bool | None` and are omitted on healthy responses; failure remains observable, but the response contract does not provide concrete booleans on every path. |
| SDK-P3-N02 | `copilot_sdk/scoring/verification/weather.py` | 68 | `_frozen_weather` | 1 | Purchasing | A configured freeze file that is missing or malformed is silently ignored and execution proceeds to another source. Returned source metadata describes the replacement, but no diagnostic records that the requested frozen source failed. |
| SDK-P3-N03 | `apps/dataops/backend/app/routers/dataops_status.py` | 82 | `_enterprise_sap_health` / `_enterprise_celonis_health` / `_enterprise_graph_health` | 1, 2 | DataOps | Health read exceptions become disconnected/zero values without component error or availability detail. The top-level response is still degraded, so users are not told the system is healthy, but operators lose the failure reason. |
| SDK-P3-N04 | `apps/purchasing/backend/app/routers/evidence.py` | 26 | evidence read endpoints | 6 | Purchasing | The backend sets `data_available`, `verified_available`, `trajectory_available`, and related flags, but the purchasing frontend has no readers for them; the flags currently provide API-only observability. |
| SDK-P3-N05 | `apps/purchasing/backend/app/services/delivery_coordinator.py` | 109 | `_to_date` | 1, 5 | Purchasing | Invalid internal schedule dates silently become today. Current HTTP callers pass a valid date, so there is no present UI misstatement, but future or direct callers cannot observe the parse failure. |
| SDK-P3-N06 | `apps/trading/backend/app/connectors/ibkr_connector.py` | 46 | `disconnect` | 1 | Trading | Disconnect exceptions are swallowed without logging or connector state, hiding cleanup failures from operators; current response data is already complete before cleanup runs. |

### P4 — Cosmetic / Style

| ID | File | Line | Function | Pattern | Copilot | Description |
|----|------|------|----------|---------|---------|-------------|
| SDK-P4-N01 | `copilot_sdk/scoring/mutation_lock.py` | 75 | `_resolved_signature` | 1 | all | Failure to resolve runtime type hints falls back to the callable's existing signature without a diagnostic; routing behavior remains intact and no data-quality state is changed. |

## Totals

| Severity | Count |
|----------|-------|
| P2       | 16 |
| P3       | 6 |
| P4       | 1 |
| **Total**| 23 |

## Findings by Copilot

The `SDK-core` row includes findings marked `all`; domain-specific SDK preset and verification findings are counted under the copilot they affect.

| Copilot | P2 | P3 | P4 |
|---------|----|----|-----|
| SDK-core | 1 | 1 | 1 |
| Trading  | 5 | 1 | 0 |
| Purchasing | 7 | 3 | 0 |
| DataOps  | 3 | 1 | 0 |
| S2P (not present) | 0 | 0 | 0 |
