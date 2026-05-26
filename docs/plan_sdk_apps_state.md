# SDK Apps State Assessment
**Date:** 2026-05-25 · **Baseline:** Trading 574 passed, Purchasing 98 passed, DataOps 161 passed, Root 654 passed

## Trading Copilot
### Routers (9 files, 26 endpoints)
| File | Endpoints | Functionality |
|---|---|---|
| `apps/trading/backend/app/routers/correlation.py` | `GET /api/trading/correlation` at line 24 | Cross-position correlation monitor backed by `CorrelationService`. |
| `apps/trading/backend/app/routers/data_import.py` | `POST /api/trading/import/csv` line 20; `GET /api/trading/trades` line 31; `GET /api/trading/trades/{trade_id}` line 39; `GET /api/trading/market/ohlcv` line 46; `GET /api/trading/market/vix` line 55 | CSV import and market-data helper endpoints. |
| `apps/trading/backend/app/routers/evidence.py` | `GET /api/trading/evidence/{trade_id}` line 29 | Trade evidence text and factor breakdown. |
| `apps/trading/backend/app/routers/journal.py` | `GET /api/trading/trades` line 30; `GET /api/trading/trades/{trade_id}` line 68; `GET /api/trading/analytics` line 75 | Journal records, trade detail, and analytics. |
| `apps/trading/backend/app/routers/prescore.py` | `POST /api/trading/prescore` line 42 | Pre-trade classification and core/options factor scoring. |
| `apps/trading/backend/app/routers/promotion.py` | `GET /api/trading/promotion` line 33; `POST /api/trading/promotion/evaluate` line 42 | Tier promotion state and evaluation. |
| `apps/trading/backend/app/routers/regime.py` | `GET /api/trading/regime` line 28; `GET /api/trading/regime/detail` line 40 | VIX/regime summary plus detailed allocation context. |
| `apps/trading/backend/app/routers/vix_timing.py` | `GET /api/trading/vix-timing` line 25 | VIX-aware hold timing analysis. |
| `apps/trading/backend/app/context_router.py` | `GET /api/context/market-snapshot` line 249; `/ticker/{ticker}` line 254; `/portfolio-summary` line 269; `/analytics` line 277; `/trust-analysis` line 285; `/patterns` line 299; `/conservation-breakdown` line 320; `/similar` line 358; `POST /trade-metadata` line 410; `GET /trade-metadata` line 423 | Trading context, trust, pattern, and metadata APIs under `/api/context`. |

Trading router mounts in `apps/trading/backend/app/main.py` include scoring at lines 234-241, transfer at line 242, evolution at lines 243-249, conservation at lines 252-258, self-computation at line 259, context at line 260, and trading routers at lines 261-274.

### Services (8 files)
| File | Classes/functions | Purpose |
|---|---|---|
| `apps/trading/backend/app/services/correlation.py` | `CorrelationService`, `_extract_tickers`, `_pairs`, `_alerts`, `_pct_change` | Computes batch-yfinance correlation matrix, pairs, and alerts. |
| `apps/trading/backend/app/services/pattern_detector.py` | `detect_patterns` plus detector helpers | Behavioral pattern detection for revenge trading, overconfidence, FOMO, tilt, and drawdown-chasing. |
| `apps/trading/backend/app/services/promotion.py` | `PromotionService` plus conservation and strategy metric helpers | Tier promotion/demotion evaluation with conservation gate. |
| `apps/trading/backend/app/services/regime.py` | `classify_regime`, `compute_adx`, `RegimeService`, `_trade_date`, `_is_win` | Current/historical VIX regime and regime accuracy. |
| `apps/trading/backend/app/services/regime_recommender.py` | `RegimeRecommender` | Detailed regime-aware allocation context. |
| `apps/trading/backend/app/services/subcategory.py` | `classify_event_subcategory`, `get_subcategory`, `_normalize` | Event-driven directional/volatility metadata classifier. |
| `apps/trading/backend/app/services/vix_timing.py` | `_bucket_hold_period`, `_bucket_vix`, `VIXTimingService` | VIX bucket by hold-period cross-tabulation. |
| `apps/trading/backend/app/services/__init__.py` | no exported service definitions | Package marker. |

### Factor Computers
| File | Purpose |
|---|---|
| `apps/trading/backend/app/factors/registry.py` | Core `compute_factors` registry for the 7 Trading factors. |
| `apps/trading/backend/app/factors/options.py` | Auxiliary options analytics factors: IV/RV, Greeks exposure, theta efficiency. |
| `apps/trading/backend/app/factors/conviction.py` | Conviction factor. |
| `apps/trading/backend/app/factors/market_regime.py` | Market regime factor and regime classifier. |
| `apps/trading/backend/app/factors/position_size.py` | Position sizing factor. |
| `apps/trading/backend/app/factors/research_depth.py` | Research depth factor. |
| `apps/trading/backend/app/factors/signal_confidence.py` | Signal confidence factor. |
| `apps/trading/backend/app/factors/technical_signal.py` | Technical signal factor. |
| `apps/trading/backend/app/factors/time_horizon.py` | Time horizon/timing factor. |
| `apps/trading/backend/app/factors/base.py` | Factor utility helpers such as clamp/neutral mean. |
| `apps/trading/backend/app/factors/__init__.py` | Factor package exports. |

### CLI Commands (14)
- `init`: creates config; default broker field is present but set to `None`.
- `import`: imports CSV or IBKR fills; `--broker csv|ibkr` is local to import at `apps/trading/backend/cli.py:711`.
- `score`: scores a saved or ad hoc trade.
- `trust`: prints trust analysis from local trades.
- `conservation`: prints conservation status.
- `journal`: prints journal/table analytics.
- `regime`: prints current regime; supports `--detail`.
- `correlation`: prints cross-position correlation; supports `--window`.
- `vix-timing`: prints VIX-aware hold timing.
- `promote`: prints tier promotion state; supports `--evaluate`.
- `export`: exports trades.
- `backup`: backs up config/trades.
- `restore`: restores backup.
- `retag`: retags a trade category.

No Trading CLI command named `order`, `orders`, `positions`, `account`, or `sync` is registered. Current broker code is import-oriented: `apps/trading/backend/cli.py:161-182` handles CSV/IBKR import, not live execution.

### Evolution/AE State
- Evolution is mounted in `apps/trading/backend/app/main.py:243-249` with `create_evolution_router(graph_store_factory=lambda: _graph_store(scoring_db), domain=DOMAIN, variant_provider=lambda: [])`.
- The mount is generic SDK evolution; `variant_provider=lambda: []` means no Trading-specific variant dimensions are currently exposed through that provider.
- Smoke result: `GET /api/evolution/variants`, `/api/evolution/history`, and `/api/evolution/promoted` all returned 200.
- No evidence was found that AE variant selection is injected into the Trading scoring path; scoring is mounted through `create_scoring_router` in `apps/trading/backend/app/main.py:234-241`.
- `apps/trading/backend/tests/test_evolution_mount.py` has 3 tests and covers the generic mount surface.

### Broker/Execution State
- `apps/trading/backend/app/brokers/` is absent.
- Existing broker-related files are connectors: `apps/trading/backend/app/connectors/alpaca_connector.py`, `csv_connector.py`, and `ibkr_connector.py`.
- `alpaca_connector.py` uses `alpaca-py` imports such as `TradingClient`, not a C3 execution broker using `httpx`.
- `ibkr_connector.py` has guarded `ib_insync` optional dependency handling.
- CLI execution commands are absent: no `order`, `orders`, `positions`, `account`, or `sync`.
- Smoke result: `GET /api/trading/broker/positions` returned 404, consistent with no backend broker execution API.
- Existing tests cover connectors/imports, including `apps/trading/backend/tests/test_csv_connector.py` and `test_cli_complete.py`; there are no broker execution command tests.

### Multi-Trader/Social State
- Search for `social`, `multi_trader`, `collaboration`, `shared`, and `trader profile` found no dedicated Trading social router or endpoint.
- Smoke result: `GET /api/trading/social/traders` returned 404.
- Remaining C2 work appears genuinely absent in backend.

### Cross-Copilot/Webhook State
- A generic transfer router is mounted in `apps/trading/backend/app/main.py:242`, but Trading-specific `/api/trading/cross-insights` returned 404.
- Search found no TradingView webhook router or status endpoint.
- Smoke results: `/api/trading/webhook/status`, `/api/trading/cross-insights`, and `/api/trading/execution/analysis` returned 404.
- Context-level trust/pattern routes exist under `/api/context/trust-analysis` and `/api/context/patterns`, but `/api/trading/trust-analysis` and `/api/trading/pattern-detection` returned 404.

### Data/Fixture Inventory
- `apps/trading/backend/data/` contains `.gitkeep`, `analytics_cache.json`, `market_snapshot.json`, `portfolio_summary.json`, `ticker_cache.json`, `trade_metadata.json`, `trading_seed_v2.json`, and `trading.db`.
- `apps/trading/backend/app/data/` is absent.
- `apps/trading/backend/seed_graph.py` exists for graph seeding.
- Fixtures/data support journal, context, market, and scoring flows, but not broker execution or social/webhook features.

### Test Inventory (574 tests)
| File | Count | Coverage |
|---|---:|---|
| `test_cli.py` | 30 | Core CLI commands and config behavior. |
| `test_cli_complete.py` | 34 | CLI completeness, CSV/IBKR import behavior, connector edge cases. |
| `test_conservation_breakdown.py` | 15 | Conservation context breakdown. |
| `test_conviction.py` | 11 | Conviction factor. |
| `test_correlation.py` | 26 | Correlation service, endpoint, CLI. |
| `test_csv_connector.py` | 16 | CSV and Alpaca normalization helpers. |
| `test_data_endpoints.py` | 10 | Data import and market endpoints. |
| `test_evidence.py` | 26 | Evidence renderer and endpoint. |
| `test_evolution_mount.py` | 3 | Generic evolution mount. |
| `test_journal.py` | 20 | Journal records and analytics. |
| `test_market_regime.py` | 19 | Market regime factor. |
| `test_options_factors.py` | 36 | Auxiliary options factor separation. |
| `test_pattern_detector.py` | 23 | Behavioral pattern detection. |
| `test_position_size.py` | 13 | Position sizing. |
| `test_prescore.py` | 23 | Pre-score endpoint/factors. |
| `test_promotion.py` | 32 | Promotion engine and conservation gate. |
| `test_regime.py` | 27 | Regime service/router. |
| `test_regime_recommender.py` | 25 | Detailed regime recommendations. |
| `test_research_depth.py` | 13 | Research depth factor. |
| `test_signal_confidence.py` | 19 | Signal confidence. |
| `test_subcategory.py` | 24 | Event-driven subcategory metadata. |
| `test_technical_signal.py` | 11 | Technical signal factor. |
| `test_time_horizon.py` | 15 | Time horizon/timing factor. |
| `test_trade_model.py` | 7 | Normalized trade model. |
| `test_trading_backend.py` | 31 | Integrated Trading backend flow. |
| `test_trading_config_migration.py` | 21 | Config migration. |
| `test_trading_graph.py` | 7 | Trading graph seed/contract. |
| `test_trust_analysis.py` | 9 | Trust analysis. |
| `test_vix_timing.py` | 28 | VIX timing service, endpoint, CLI. |

### Endpoint Smoke Results
| Result | Path |
|---|---|
| ERR `AssertionError: mu.shape[1]=3 must equal len(actions)=4` | `GET /api/health` |
| 404 | `GET /api/trading/health` |
| 200 | `GET /api/conservation/status` |
| 404 | `GET /api/trading/conservation/status` |
| 200 | `GET /api/evolution/variants` |
| 200 | `GET /api/evolution/history` |
| 200 | `GET /api/evolution/promoted` |
| 200 | `GET /api/self/accuracy-by-category` |
| 200 | `GET /api/self/centroid-history` |
| 200 | `GET /api/self/decisions` |
| 404 | `GET /api/self/decision-flow` |
| 200 | `GET /api/trading/regime` |
| 200 | `GET /api/trading/regime/detail` |
| 404 | `GET /api/trading/journal` |
| 200 | `GET /api/trading/correlation` |
| 200 | `GET /api/trading/vix-timing` |
| 200 | `GET /api/trading/promotion` |
| 404 | `GET /api/trading/trust-analysis` |
| 404 | `GET /api/trading/pattern-detection` |
| 404 | `GET /api/trading/variants` |
| 404 | `GET /api/trading/broker/positions` |
| 404 | `GET /api/trading/social/traders` |
| 404 | `GET /api/trading/cross-insights` |
| 404 | `GET /api/trading/execution/analysis` |
| 404 | `GET /api/trading/webhook/status` |
| EXISTS | `POST /api/score` |
| MISSING | `POST /api/trading/score` |
| EXISTS | `POST /api/trading/prescore` |

The Trading smoke test triggered yfinance SSL/fallback warnings from regime endpoints; that does not affect endpoint availability but should be avoided in deterministic tests.

### Gap Table (C1-C6)
| MAP Item | ID | Exists? | What's There | Remaining Gap |
|---|---|---|---|---|
| AE mount + variant dims | C1 | Partial | Generic `/api/evolution/*` mount exists at `main.py:243-249`; provider returns empty list. | Trading-specific variant dimensions and scoring-path selection are absent. |
| Multi-trader social | C2 | No | No matching router/files; smoke `/api/trading/social/traders` 404. | Create backend model/router/service/tests if still desired. |
| Broker execution | C3 | No | CSV/IBKR/Alpaca import connectors exist; no `app/brokers` package or execution CLI. | Create CLI-only broker execution package and docs; no backend endpoint needed. |
| Cross-copilot insights | C4 | Partial | Generic transfer router mounted at `main.py:242`. | Trading-specific `/api/trading/cross-insights` absent. |
| Execution analysis | C5 | No | Pattern/trust context exists under `/api/context`; `/api/trading/execution/analysis` 404. | Define whether context patterns satisfy C5 or create dedicated route. |
| TradingView webhook | C6 | No | No webhook route; `/api/trading/webhook/status` 404. | Create webhook intake/status if required. |
| CLI completeness | CLI | Partial | 14 commands; correlation, vix timing, regime, promotion present. | Broker execution commands and evolution/variant CLI absent. |
| Evidence/reasoning | Evidence | Yes | `GET /api/trading/evidence/{trade_id}` and `evidence.py` present. | No immediate create work. |

### Assessment
- C1: Enhance. Generic evolution exists, but Trading-specific variant dimensions/selection are missing.
- C2: Create. Social/multi-trader backend is absent.
- C3: Create. Broker execution is absent; existing connectors are import-only.
- C4: Enhance. Generic transfer exists, but Trading-specific cross-insights endpoint is absent.
- C5: Investigate/Enhance. Pattern/trust logic exists under `/api/context`; dedicated execution analysis route is absent.
- C6: Create. TradingView webhook is absent.

## Purchasing Copilot
### Routers
| File | Endpoints | Functionality |
|---|---|---|
| `apps/purchasing/backend/app/context_router.py` | `GET /api/context/today-summary` line 107; `/items` line 117; `/waste-history/{item}` line 134; `/weather` line 142; `POST /order-metadata` line 147; `GET /order-metadata` line 161; `GET /analytics` line 166; `GET /similar` line 184; `GET /item/{name}/profile` line 238 | Purchasing domain context and analytics under `/api/context`. |

No `apps/purchasing/backend/app/routers/` directory exists. The main app mounts scoring at `apps/purchasing/backend/app/main.py:272-279`, transfer at line 280, evolution at lines 281-284, conservation at lines 287-293, self-computation at line 294, and context at line 295.

### Services + Factors + Data
| Area | State |
|---|---|
| Services directory | Absent. No `apps/purchasing/backend/app/services/`. |
| Factors directory | Absent. Purchasing uses SDK scoring preset/router plus context data rather than app-local factor computer modules. |
| Connectors directory | Absent. |
| Data files | `apps/purchasing/backend/data/` contains analytics cache, evolution fixtures, order metadata, orders, seed data, suppliers, waste history, weather cache, and `purchasing.db`. |
| App-level data | `apps/purchasing/backend/app/items.json`, `graph_contract.py`, and `seed_graph.py` exist. |
| App-level fixture helpers | `apps/purchasing/backend/app/data_helpers.py` is a 66-line helper module for deterministic Purchasing fixture loading. It defines `DATA_DIR`, `SUPPLIERS_PATH`, and `ORDERS_PATH` at lines 10-12, loads JSON via `_load_json()` at lines 18-19, exposes `load_purchasing_suppliers()` at lines 22-26 and `load_purchasing_orders()` at lines 29-33, and adds lookup helpers for supplier/category order filtering at lines 42-66. This does not change the "no services/factors dirs" statement; it is fixture/data plumbing rather than a service package. |

### CLI
No backend CLI exists: `apps/purchasing/backend/cli.py` was absent in the read-only check.

### Evolution/AE State
- Evolution is mounted at `apps/purchasing/backend/app/main.py:281-284` with `create_evolution_router(DOMAIN, ledger_provider=_ledger_provider)`.
- Purchasing evolution fixtures exist in `apps/purchasing/backend/data/evolution_fixtures.json`.
- Main contains provider helpers around line 249 for variant status mapping.
- Smoke result: `GET /api/evolution/variants` and `GET /api/evolution/history` returned 200.
- Evidence of Purchasing-specific AE variant selection in the scoring path was not found; scoring remains the generic `create_scoring_router` mount.

### Self-Computation + Conservation
- Conservation is mounted under `/api` at `apps/purchasing/backend/app/main.py:287-293`; smoke `GET /api/conservation/status` returned 200.
- Self-computation is mounted at line 294; smoke returned 200 for `/api/self/accuracy-by-category`, `/api/self/centroid-history`, and `/api/self/decisions`.
- `/api/self/decision-flow` returned 404.
- Context endpoints are fixture/data-backed through `context_router.py`; direct `/api/purchasing/*` endpoints were absent in smoke.

### Test Inventory
| File | Count | Coverage |
|---|---:|---|
| `test_purchasing_backend.py` | 40 | Main backend scoring, context, conservation, evolution smoke. |
| `test_purchasing_config_migration.py` | 19 | Config migration and preset compatibility. |
| `test_purchasing_fixtures.py` | 32 | Purchasing fixtures/data quality. |
| `test_purchasing_graph.py` | 7 | Purchasing graph contract/seed coverage. |

### Endpoint Smoke Results
| Result | Path |
|---|---|
| 200 | `GET /api/health` |
| 404 | `GET /api/purchasing/health` |
| 200 | `GET /api/conservation/status` |
| 200 | `GET /api/evolution/variants` |
| 200 | `GET /api/evolution/history` |
| 200 | `GET /api/self/accuracy-by-category` |
| 200 | `GET /api/self/centroid-history` |
| 200 | `GET /api/self/decisions` |
| 404 | `GET /api/self/decision-flow` |
| 404 | `GET /api/purchasing/items` |
| 404 | `GET /api/purchasing/categories` |
| 404 | `GET /api/purchasing/analytics` |
| 404 | `GET /api/purchasing/evidence` |
| 404 | `GET /api/purchasing/preview/queue` |
| 404 | `GET /api/purchasing/preview/suppliers` |
| EXISTS | `POST /api/score` |
| MISSING | `POST /api/purchasing/score` |

### Gap Table
| Feature | Exists? | What's There | Remaining Gap |
|---|---|---|---|
| Core scoring | Yes | Generic SDK scoring router at `main.py:272-279`; `POST /api/score` exists. | No `/api/purchasing/score` alias. |
| Conservation | Yes | `create_conservation_router` mounted at `main.py:287-293`; smoke 200. | None for generic status; domain-specific route alias absent. |
| Evolution/AE | Partial | Generic evolution mounted; fixtures exist; smoke 200. | Purchasing-specific selection/dimensions not evident. |
| Self-computation 6 endpoints | Partial | Accuracy, centroid history, decisions exist; decision-flow 404. | Complete intended SC endpoint set if MAP requires six. |
| Purchasing-specific analytics | Partial | `/api/context/analytics` exists at `context_router.py:166`; `/api/purchasing/analytics` 404. | Decide whether context route is canonical or add aliases. |
| Evidence/reasoning | Partial/No | No `/api/purchasing/evidence`; no evidence router found. | Create if still in scope. |
| Factor computers | Partial | Generic scorer uses SDK preset; no app-local factor computer directory. | Add only if MAP needs app-level explainable factor computers. |
| CLI | No | No `cli.py`. | Create if command surface is required. |
| Fixtures/data | Yes | Orders, suppliers, waste history, weather, metadata, evolution fixtures, and `data_helpers.py` supplier/order loaders. | No immediate data creation gap. |

### Assessment
- Core features built: generic scoring, conservation, self-computation subset, evolution mount, context analytics, graph/data fixtures.
- Missing features: domain-prefixed purchasing endpoints, CLI, evidence route, and full SC endpoint set if required by MAP.
- Estimated effort to complete: small-to-medium, mostly aliases/evidence/CLI unless Purchasing-specific AE selection is required.

## DataOps Copilot
### Routers
| File | Endpoints | Functionality |
|---|---|---|
| `apps/dataops/backend/app/context_router.py` | `GET /api/context/pipelines` line 663; `/enterprise-health` line 668; `/sap/purchase-orders` line 684; `/celonis/process-data` line 694; `/alerts` line 723; `/alert-groups` line 732; `/system/{name}/history` line 815; `/decisions` line 901; `/accuracy-by-category` line 931; `/centroid-history` line 973; `/transformations/{system}` line 1007; `/bottleneck/{system}` line 1018; `/schema-impact/{system}` line 1051; `/process-timeline` line 1071; `/cross-graph-insight/{alert_id}` line 1179; `POST /apply-fix` line 1265; `/system/{name}` line 1291; `/alert/{id}` line 1296; `/alert/{id}/deps` line 1305; `/alert/{id}/recurrence` line 1310; `/alert/{id}/factors` line 1315; `/similar` line 1320; `/process-signals/{system}` line 1369; `/audit-trail/{alert_id}` line 1417; `POST /alert-metadata` line 1536; `GET /alert-metadata` line 1548 | DataOps context, graph, enterprise, and metadata APIs under `/api/context`. |
| `apps/dataops/backend/app/ae_router.py` | `GET /api/ae/recommendation/{alert_id}` line 292; `/impact` line 334; `/pattern-origin` line 367; `/rule-lifecycle` line 420; `/operational-rules` line 445; `/incident` line 462; `/conservation-history` line 469; `/transfer-status` line 476 | AE/operational-excellence views under `/api/ae`. |

No `apps/dataops/backend/app/routers/` directory exists. The main app mounts scoring at `apps/dataops/backend/app/main.py:241-248`, transfer at line 249, conservation at lines 250-256, evolution at lines 257-263, self-computation at line 264, context at line 265, and AE at line 266.

### Services + Connectors
| File | Classes/functions | Fixture vs live |
|---|---|---|
| `apps/dataops/backend/app/celonis_connector.py` | `CelonisConnector` with `get_knowledge_models`, `get_kpis`, `get_process_data`, `health`, `_request_json`, cache helpers | Live when `CELONIS_URL` and `CELONIS_TOKEN` are present; otherwise fixture/cache backed. |
| `apps/dataops/backend/app/sap_connector.py` | `SAPConnector` with `get_purchase_orders`, `get_supplier_invoices`, `get_suppliers`, `health`, `_get_collection`, `_request_json` | Live when SAP env vars are present; otherwise fixture/cache backed. |
| `apps/dataops/backend/app/graph_queries.py` | `DataOpsGraphClient` and graph/query helper functions | Uses SQLite/fallback fixtures and optional AGE/Cypher style client hooks. |
| `apps/dataops/backend/app/graph_contract.py` | `DATAOPS_GRAPH_CONTRACT` | Declares graph nodes, edges, expected counts, and validation rules. |
| Directories | `services/` and `connectors/` directories absent | Connectors live as top-level app modules. |

### Enterprise Connectors
- `CelonisConnector` exists in `apps/dataops/backend/app/celonis_connector.py:17`; env-based setup is at lines 25-32, and HTTP fallback/error handling is in `_request_json` around lines 94-103.
- `SAPConnector` exists in `apps/dataops/backend/app/sap_connector.py:17`; env-based setup is at lines 25-32, cache fallback at lines 89-93, and HTTP handling at lines 95-106.
- Smoke showed `/api/context/enterprise-health`, `/api/context/sap/purchase-orders`, and `/api/context/celonis/process-data` exist indirectly through endpoint inventory; the user-requested `/api/dataops/*` aliases returned 404.
- Connectors are fixture-backed unless environment credentials are supplied.

### DI-1 SOURCE-PROFILER
- Search for `source_profiler`, `source-profiler`, `DI-1`, and `profiler` found no source-profiler implementation or route.
- Smoke result: `GET /api/dataops/source-profiler` returned 404.
- Data quality categories exist as alert data such as `quality_anomaly`, but that is not a source profiler.
- DI-1 appears absent and should be treated as a genuine create item.

### Graph Contract
- `apps/dataops/backend/app/graph_contract.py` defines `DATAOPS_GRAPH_CONTRACT` at line 8 with graph name `dataops_graph` and expected 160 nodes/220 edges at lines 9-11.
- Node types include Decision, Pipeline, Dataset, QualityRule, Alert, ProcessModel, Activity, and Transformation at lines 13-20.
- Edge types include DECIDED_ON, PRODUCES, CONSUMES, MONITORS, DETECTED_IN, CONTAINS, FOLLOWS, and TRIGGERED_BY at lines 23-30.
- `apps/dataops/backend/app/graph_queries.py` defines `DataOpsGraphClient` at line 56 and AGE/client handling around lines 38-84.

### Test Inventory
| File | Count | Coverage |
|---|---:|---|
| `test_dataops_backend.py` | 103 | DataOps scoring, context, AE, conservation, enterprise/context routes. |
| `test_dataops_graph.py` | 9 | DataOps graph contract and seed state. |
| `test_enterprise_connectors.py` | 26 | SAP/Celonis connector health, cache, env/live fallback behavior. |
| `test_graph_queries.py` | 16 | DataOps graph query client behavior. |
| `test_transfer_status.py` | 7 | AE transfer-status fixture and endpoint behavior. |

### Endpoint Smoke Results
| Result | Path |
|---|---|
| 200 | `GET /api/health` |
| 404 | `GET /api/dataops/health` |
| 200 | `GET /api/conservation/status` |
| 200 | `GET /api/evolution/variants` |
| 200 | `GET /api/evolution/history` |
| 200 | `GET /api/self/accuracy-by-category` |
| 200 | `GET /api/self/centroid-history` |
| 200 | `GET /api/context/pipelines` |
| 200 | `GET /api/context/alert-groups` |
| 200 | `GET /api/context/bottleneck/sap_po` |
| 200 | `GET /api/context/schema-impact/sap_po` |
| 200 | `GET /api/ae/operational-rules` |
| 200 | `GET /api/ae/impact` |
| 404 | `GET /api/ae/variants` |
| 404 | `GET /api/dataops/enterprise-health` |
| 404 | `GET /api/dataops/celonis/status` |
| 404 | `GET /api/dataops/sap/status` |
| 404 | `GET /api/dataops/source-profiler` |
| 404 | `GET /api/dataops/transfer/status` |
| EXISTS | `POST /api/score` |
| MISSING | `POST /api/dataops/score` |

### Gap Table
| Feature | Exists? | What's There | Remaining Gap |
|---|---|---|---|
| Core scoring + triage | Yes | `POST /api/score`; context alert/system endpoints. | No `/api/dataops/score` alias. |
| Conservation | Yes | `create_conservation_router` mounted at `main.py:250-256`; smoke 200. | Domain-prefixed alias absent. |
| Evolution/AE | Partial | Generic evolution mounted at `main.py:257-263`; AE router mounted at line 266. | `/api/ae/variants` absent; variant selection integration unclear. |
| Self-computation | Partial | `/api/self/accuracy-by-category` and `/api/self/centroid-history` 200. | Other SC endpoints need separate verification if MAP requires them. |
| Pipeline context D-1 to D-6 | Mostly Yes | `/api/context/pipelines`, alert groups, bottleneck, schema impact, process timeline, cross-graph insight. | Domain-prefixed aliases absent. |
| OE panels OE-1 to OE-5 | Partial/Yes | `/api/ae/impact`, operational rules, incident, conservation history, transfer status endpoint exists at `/api/ae/transfer-status`. | `/api/ae/variants` absent. |
| Enterprise connectors | Yes | SAP/Celonis top-level connectors with fixture fallback and tests. | `/api/dataops/celonis/status` and `/api/dataops/sap/status` aliases absent. |
| DI-1 SOURCE-PROFILER | No | No source-profiler implementation found; smoke 404. | Create service/router/tests if still required. |
| Graph contract | Yes | `graph_contract.py` and `graph_queries.py` present. | None obvious. |
| Transfer/cross-copilot | Partial | Generic transfer router mounted; AE transfer status endpoint exists under `/api/ae`. | `/api/dataops/transfer/status` alias absent. |

### Assessment
- DI-1: Create. Source-profiler is absent.
- Enterprise connectors: Enhance only for route aliases/status paths; connector modules and tests already exist.
- Missing features: DataOps-domain aliases, source-profiler, and `/api/ae/variants` if still required.

## Cross-App Summary
| Component | Trading | Purchasing | DataOps |
|---|---|---|---|
| CompoundingScorer | `create_scoring_router` mounted in `main.py:234-241` | `create_scoring_router` mounted in `main.py:272-279` | `create_scoring_router` mounted in `main.py:241-248` |
| GraphStore impl | `_graph_store(scoring_db)` used for evolution/self/conservation | `_graph_store(scoring_db)` plus ledger provider | `_graph_store(scoring_db)` used for evolution/self/conservation |
| Scoring router | Yes, `/api/score` | Yes, `/api/score` | Yes, `/api/score` |
| Conservation router | Yes, `/api/conservation/status` | Yes, `/api/conservation/status` | Yes, `/api/conservation/status` |
| Evolution router | Yes, `/api/evolution/*`, empty variant provider | Yes, `/api/evolution/*`, ledger provider | Yes, `/api/evolution/*`, `_evolution_variants` provider |
| SC router | Yes, partial smoke coverage | Yes, partial smoke coverage | Yes, partial smoke coverage |
| Port | not found in `main.py` scan | not found in `main.py` scan | not found in `main.py` scan |
| Tensor shape | `(5,4,7)` | `(5,4,7)` | `(6,5,6)` |
| Frontend .tsx count | 46 | 35 | 50 |

## Queue Recommendations
### Items to DROP (already done)
- Trading regime detail, correlation, VIX timing, promotion, options factors, event-driven subcategories: all have service/router/test coverage.
- Trading evidence/reasoning: `GET /api/trading/evidence/{trade_id}` exists.
- Purchasing core scoring, conservation, evolution mount, self-computation subset, context analytics/data fixtures: already present.
- DataOps enterprise connectors, graph contract, graph queries, context pipeline endpoints, AE impact/operational rule endpoints: already present.

### Items to ENHANCE (partially done)
- Trading C1 AE: add Trading-specific variants/selection if required; do not recreate generic evolution router.
- Trading C4 cross-copilot: generic transfer exists, but Trading-specific route is missing.
- Trading C5 execution analysis: context patterns/trust exist; dedicated Trading execution-analysis route is absent.
- Purchasing domain aliases/evidence/CLI: generic core exists; domain-specific endpoints and CLI are missing.
- DataOps enterprise/status aliases: connectors exist, but `/api/dataops/*` status aliases are missing.
- DataOps AE variants: generic evolution exists but `/api/ae/variants` is absent.

### Items to CREATE (genuinely new)
- Trading C2 multi-trader/social backend.
- Trading C3 CLI-only broker execution package and broker integration doc.
- Trading C6 TradingView webhook/status flow.
- DataOps DI-1 SOURCE-PROFILER.
- Purchasing backend CLI if MAP requires a command surface.

### Items to INVESTIGATE (need separate code analysis)
- Trading `/api/health` smoke assertion caused by persisted scorer shape mismatch.
- Whether MAP expects `/api/self/decision-flow` across all apps or accepts existing SC subset.
- Whether domain-prefixed aliases are required or `/api/context`/`/api/ae` paths are canonical.
- Whether AE variant selection should affect score-time behavior or remain advisory.

## Revised Effort Estimates
| Item | Old Estimate | Revised | Rationale |
|---|---|---|---|
| Trading C1 AE | create from scratch | small/medium enhance | Generic evolution exists; need Trading-specific variant dimensions/integration only. |
| Trading C2 social | unknown | medium create | No backend route/service found. |
| Trading C3 broker execution | create | medium create | Import connectors exist, but execution broker package/CLI absent. |
| Trading C4 cross-copilot | create | small/medium enhance | Generic transfer router exists; Trading-specific insight route absent. |
| Trading C5 execution analysis | create | small/medium investigate/enhance | Trust/pattern context exists, dedicated route absent. |
| Trading C6 webhook | create | medium create | No webhook/status route found. |
| Purchasing core | create | drop/enhance | Generic scoring/conservation/evolution/context already built. |
| Purchasing CLI/evidence | create | small/medium create | No CLI or domain evidence route found. |
| DataOps enterprise connectors | create | drop/enhance | SAP/Celonis connectors and tests exist; only alias/status gaps remain. |
| DataOps DI-1 | create | medium create | Source-profiler absent. |

## Blockers
- Trading `/api/health` smoke raised `AssertionError: mu.shape[1]=3 must equal len(actions)=4`; investigate persisted scorer DB before treating health as stable.
- Separate app import processes must continue for smoke tests because all apps expose `app.main` and module names collide.
- Several route gaps may be aliases rather than feature gaps; next implementation prompts should declare canonical API path expectations before writing code.
