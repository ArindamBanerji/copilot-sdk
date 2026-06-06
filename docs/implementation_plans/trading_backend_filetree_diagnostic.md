# Trading Backend Filetree Diagnostic

Date: 2026-06-05
Model: gpt-5.3
Task Type: Diagnostic document creation only; no source code changes.
Repo: copilot-sdk
Target App: apps/trading/backend/app
Diagnostic Purpose: Discover the actual Trading backend app file tree, TODO/stub/mock signals, router registrations, router cross-checks, and path hints for Trading MAP prompts P48-P85 so future implementation/review prompts do not guess backend paths.

## Executive Summary

- Can future Trading prompts stop guessing paths? PARTIAL
- Biggest findings:
  - The Trading backend app path exists under the known workspace repo path.
  - The app contains 56 Python files under `apps/trading/backend/app`, excluding `__pycache__`.
  - `main.py` registers all obvious app-local APIRouter modules found by the router-definition scan.
  - Concrete connector, factor, router, service, broker, evidence, graph, and evolution paths are visible for many MAP prompts.
- Biggest ambiguity:
  - CLI-related MAP prompts and feature names such as TRD-IKS-WIRE, TRD-TRUST-RADAR, and TRD-REALTIME-SCORE are not directly named in the target app tree.
- Recommended next diagnostic, if any:
  - Scan `apps/trading/backend` outside `app` plus repo-wide exact feature-label references for CLI and ambiguous MAP names, without git or tests.

## Path Resolution

- CLAUDE_SDK value: `C:\Users\baner\CopyFolder\IOT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
- Repo path used: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`
- Trading backend app path used: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk\apps\trading\backend\app`
- CLAUDE.md found: True
- main.py found: True
- docs/implementation_plans found or created: Found

## CLAUDE.md Relevant Notes

- Do not use git directly.
- Docs are aspirational until proven in code; check actual source files.
- Cite file and line for behavioral claims.
- Code and tests beat docs; report drift when source and docs disagree.
- Make surgical changes only.
- Before architecture/codebase answers, read `graphify-out/GRAPH_REPORT.md` when applicable.
- The repo guidance says to run tests after changes, but this diagnostic is explicitly document-only and the user instructed not to run tests.

## Full Trading Backend App File Tree

```text
__init__.py  (0.1KB)
brokers\__init__.py  (0.7KB)
brokers\alpaca.py  (6.7KB)
brokers\mock.py  (4.1KB)
brokers\protocol.py  (1.8KB)
connectors\__init__.py  (0.3KB)
connectors\alpaca_connector.py  (3.5KB)
connectors\csv_connector.py  (10KB)
connectors\ibkr_connector.py  (5.1KB)
connectors\yfinance_provider.py  (2KB)
context_router.py  (14.3KB)
evidence.py  (9.8KB)
evolution\__init__.py  (0.6KB)
evolution\dimensions.py  (0.8KB)
evolution\evolver_config.py  (3.5KB)
evolution\variant_provider.py  (0.3KB)
factors\__init__.py  (0.4KB)
factors\base.py  (0.6KB)
factors\conviction.py  (1.4KB)
factors\market_regime.py  (1.2KB)
factors\options_scored.py  (2.4KB)
factors\options.py  (7.6KB)
factors\position_size.py  (2KB)
factors\registry.py  (2.8KB)
factors\research_depth.py  (1.5KB)
factors\signal_confidence.py  (1.4KB)
factors\technical_signal.py  (2.4KB)
factors\time_horizon.py  (2.4KB)
graph_contract.py  (1.4KB)
graph_status.py  (12.7KB)
main.py  (12.9KB)
models\__init__.py  (0.1KB)
models\trade.py  (4.2KB)
routers\analytics.py  (12.3KB)
routers\broker_router.py  (9.4KB)
routers\correlation.py  (0.8KB)
routers\data_import.py  (2.4KB)
routers\evidence.py  (7.4KB)
routers\journal.py  (11KB)
routers\prescore.py  (11.3KB)
routers\promotion.py  (3.5KB)
routers\regime.py  (3.5KB)
routers\social.py  (4.2KB)
routers\vix_timing.py  (0.8KB)
routers\webhook.py  (10.8KB)
seed_graph.py  (6.7KB)
services\__init__.py  (0KB)
services\correlation.py  (7.2KB)
services\pattern_detector.py  (10.3KB)
services\promotion.py  (8.8KB)
services\regime_recommender.py  (5.9KB)
services\regime.py  (7.3KB)
services\subcategory.py  (2.3KB)
services\trader_profiles.py  (10.5KB)
services\verification.py  (3KB)
services\vix_timing.py  (7.1KB)
```

## Files With TODO / Stub / Mock / Fixture Signals

| File | Lines | TODO_STUB | MOCK_FIXTURE | Notes |
|---|---:|---:|---:|---|
| brokers\__init__.py | 30 | 0 | 4 | Signal scan matched mock/fixture/fake/hardcod/sample/demo data/synthetic terms. |
| brokers\mock.py | 104 | 0 | 2 | Signal scan matched mock/fixture/fake/hardcod/sample/demo data/synthetic terms. |
| connectors\ibkr_connector.py | 159 | 2 | 0 | Signal scan matched TODO/FIXME/XXX/NotImplementedError/standalone pass/stub terms. |
| connectors\yfinance_provider.py | 57 | 0 | 1 | Signal scan matched mock/fixture/fake/hardcod/sample/demo data/synthetic terms. |
| context_router.py | 435 | 0 | 7 | Signal scan matched mock/fixture/fake/hardcod/sample/demo data/synthetic terms. |
| evolution\evolver_config.py | 123 | 0 | 1 | Signal scan matched mock/fixture/fake/hardcod/sample/demo data/synthetic terms. |
| main.py | 344 | 0 | 7 | Signal scan matched mock/fixture/fake/hardcod/sample/demo data/synthetic terms. |
| routers\journal.py | 314 | 1 | 0 | Signal scan matched TODO/FIXME/XXX/NotImplementedError/standalone pass/stub terms. |
| routers\social.py | 117 | 2 | 0 | Signal scan matched TODO/FIXME/XXX/NotImplementedError/standalone pass/stub terms. |
| routers\webhook.py | 339 | 1 | 2 | Signal scan matched both TODO/stub and mock/fixture categories. |

## main.py Router Registrations

```text
  20: for path in (BACKEND_ROOT, REPO_ROOT, GAE_PATH):
  21:     if path.exists() and str(path) not in sys.path:
  22:         sys.path.insert(0, str(path))
  23: 
  24: from .context_router import router as context_router  # noqa: E402
  25: from .graph_status import (  # noqa: E402
  26:     create_trading_active_graph_store,
  27:     initialize_trading_active_graph_config,
  28:     router as trading_graph_status_router,
  29: )
  30: from .routers.broker_router import create_broker_router  # noqa: E402
  31: from .routers.analytics import create_analytics_router  # noqa: E402
  32: from .routers.correlation import create_correlation_router  # noqa: E402
  33: from .routers.data_import import router as data_import_router  # noqa: E402
  34: from .routers.evidence import create_evidence_router  # noqa: E402
  35: from .evolution import get_trading_variants  # noqa: E402
  36: from .routers.journal import create_journal_router  # noqa: E402
  37: from .routers.prescore import create_prescore_router  # noqa: E402
  38: from .routers.promotion import create_promotion_router  # noqa: E402
  39: from .routers.regime import create_regime_router  # noqa: E402
  40: from .routers.social import create_social_router  # noqa: E402
  41: from .routers.vix_timing import create_vix_timing_router  # noqa: E402
  42: from .routers.webhook import create_webhook_router  # noqa: E402
  43: from copilot_sdk.backend.transfer_router import create_transfer_router  # noqa: E402
  44: from copilot_sdk.backend import (  # noqa: E402
  45:     create_conservation_router,
  46:     create_evolution_router,
  47:     create_scoring_router,
  48:     mount_self_computation_router,
  49: )
  50: from copilot_sdk.backend.scorer_proxy import FreshScorerProxy  # noqa: E402
  51: from copilot_sdk.demo.bundle import restore_bundle_if_empty as _restore_demo_bundle  # noqa: E402
  52: from copilot_sdk.graph import SQLiteGraphStore  # noqa: E402
  53: from copilot_sdk.scoring.scorer import CompoundingScorer  # noqa: E402
  54: from copilot_sdk.scoring.presets.trading import TradingPreset  # noqa: E402
  55: 
 265:     app.include_router(
 266:         create_scoring_router(
 267:             DOMAIN,
 268:             db_path=scoring_db,
 269:             scorer_factory=lambda: scorer_proxy,
 270:         ),
 271:         prefix="/api",
 272:     )
 273:     app.include_router(create_transfer_router(scorer_proxy))
 274:     app.include_router(
 275:         create_evolution_router(
 276:             graph_store_factory=lambda: selected_graph_store_factory(scoring_db),
 277:             domain=DOMAIN,
 278:             variant_provider=get_trading_variants,
 279:         )
 280:     )
 281: 
 282:     # Conservation router
 283:     app.include_router(
 284:         create_conservation_router(
 285:             DOMAIN,
 286:             state_provider=scorer_proxy,
 287:         ),
 288:         prefix="/api",
 289:     )
 290:     mount_self_computation_router(app, selected_graph_store_factory(scoring_db))
 291:     app.include_router(context_router, prefix="/api/context")
 292:     app.include_router(create_evidence_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
 293:     app.include_router(create_journal_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
 294:     app.include_router(create_analytics_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
 295:     app.include_router(create_correlation_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
 296:     app.include_router(create_prescore_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
 297:     app.include_router(
 298:         create_promotion_router(
 299:             lambda: selected_graph_store_factory(scoring_db),
 300:             config_dir=_promotion_config_dir(scoring_db),
 301:             domain=DOMAIN,
 302:         )
 303:     )
 304:     app.include_router(create_regime_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
 305:     app.include_router(create_social_router(scorer_proxy))
 306:     app.include_router(create_vix_timing_router(lambda: selected_graph_store_factory(scoring_db), domain=DOMAIN))
 307:     app.include_router(create_webhook_router(scorer_proxy))
 308:     app.include_router(create_broker_router(), prefix="/api/broker", tags=["broker"])
 309:     app.include_router(data_import_router)
 310:     app.include_router(trading_graph_status_router)
```

## Router Cross-Check

### Registered Routers Found

- `context_router` from `context_router.py`; router definition observed at `context_router.py` L18.
- `trading_graph_status_router` from `graph_status.py`; router definition observed at `graph_status.py` L29.
- `create_broker_router` from `routers\broker_router.py`; APIRouter factory observed at `routers\broker_router.py` L125-L126.
- `create_analytics_router` from `routers\analytics.py`; APIRouter factory/router observed at `routers\analytics.py` L27-L28.
- `create_correlation_router` from `routers\correlation.py`; APIRouter factory/router observed at `routers\correlation.py` L20-L21.
- `data_import_router` from `routers\data_import.py`; APIRouter factory/router observed at `routers\data_import.py` L14-L15.
- `create_evidence_router` from `routers\evidence.py`; APIRouter factory/router observed at `routers\evidence.py` L24-L25.
- `create_journal_router` from `routers\journal.py`; APIRouter factory/router observed at `routers\journal.py` L23-L24.
- `create_prescore_router` from `routers\prescore.py`; APIRouter factory/router observed at `routers\prescore.py` L37-L38.
- `create_promotion_router` from `routers\promotion.py`; APIRouter factory/router observed at `routers\promotion.py` L23-L24.
- `create_regime_router` from `routers\regime.py`; APIRouter factory/router observed at `routers\regime.py` L24-L25.
- `create_social_router` from `routers\social.py`; APIRouter factory/router observed at `routers\social.py` L22-L23.
- `create_vix_timing_router` from `routers\vix_timing.py`; APIRouter factory/router observed at `routers\vix_timing.py` L21-L22.
- `create_webhook_router` from `routers\webhook.py`; APIRouter factory/router observed at `routers\webhook.py` L76-L77.
- External `copilot_sdk.backend` routers are registered from outside the target app: `create_scoring_router`, `create_transfer_router`, `create_evolution_router`, `create_conservation_router`, and `mount_self_computation_router`.

### Registered Routers Missing

- None observed for app-local router imports in the target app tree.
- External `copilot_sdk.backend` router modules were not cross-checked inside the target app tree because they are outside `apps/trading/backend/app`.

### Router Files Present But Not Registered

- None obvious. Every app-local file with an APIRouter/router definition found by the scan appears to be included from `main.py`.

## Trading MAP Path Hints

| MAP Prompt | Feature | Likely Actual File(s) | Status | Evidence / Notes |
|---|---|---|---|---|
| P48 | TRD-DOMAIN-CONFIG | `main.py`, `graph_status.py`, `graph_contract.py`, `seed_graph.py` | FOUND_PATH | `main.py` imports active graph config at L25-L28 and defines domain/config constants near L57-L62 in prior scan context. |
| P49 | TRD-ALPACA-CONNECTOR | `connectors\alpaca_connector.py`, `brokers\alpaca.py`, `routers\broker_router.py` | FOUND_PATH | Tree contains Alpaca connector and broker adapter; broker router is imported in `main.py` L30 and included L308. |
| P50 | TRD-YFINANCE | `connectors\yfinance_provider.py`, `services\regime.py`, `services\correlation.py`, `factors\options.py`, `routers\data_import.py` | FOUND_PATH | Tree contains yfinance provider and yfinance-related services/factors; data import router is imported L33 and included L309. |
| P51 | TRD-SIGNAL-FACTORS | `factors\registry.py`, `factors\conviction.py`, `factors\technical_signal.py`, `factors\signal_confidence.py` | FOUND_PATH | Factor registry and signal-related factor files are present in the file tree. |
| P52 | TRD-CLI-CORE | No app-path CLI file visible | NO_OBVIOUS_PATH | No CLI file appears under `apps/trading/backend/app`; `routers\broker_router.py` references `apps/trading/backend/cli.py`, outside this target app scan. |
| P53 | TRD-TRUST-RADAR | `routers\social.py`, `services\trader_profiles.py`, possibly `context_router.py` | UNCLEAR | Trader profile/social paths are visible, but the exact phrase `trust radar` was not observed in the target app tree scan. |
| P54 | TRD-REMAINING-FACTORS | `factors\research_depth.py`, `factors\position_size.py`, `factors\time_horizon.py`, `factors\market_regime.py`, `factors\options_scored.py`, `factors\registry.py` | FOUND_PATH | Remaining factor modules are present in the file tree. |
| P55 | TRD-PATTERN-DETECTOR | `services\pattern_detector.py`, `context_router.py` | FOUND_PATH | Pattern detector service exists; prior focused scan observed `context_router.py` importing `detect_patterns`. |
| P56 | TRD-CONSERVATION-STRAT | `main.py`, external `copilot_sdk.backend.create_conservation_router`, `routers\promotion.py`, `services\regime_recommender.py` | UNCLEAR | `main.py` imports `create_conservation_router` L45 and includes it L283-L289, but the conservation router itself is external to the target app. |
| P57 | TRD-JOURNAL | `routers\journal.py` | FOUND_PATH | `main.py` imports `create_journal_router` L36 and includes it L293. |
| P58 | TRD-IKS-WIRE | No obvious app-path file visible | NO_OBVIOUS_PATH | No IKS-named file/module was observed in the target app file tree. |
| P59 | TRD-IBKR | `connectors\ibkr_connector.py` | FOUND_PATH | IBKR connector file is present in the file tree; no direct router registration was observed in `main.py`. |
| P60 | TRD-CSV-IMPORT | `connectors\csv_connector.py`, `routers\data_import.py`, `models\trade.py` | FOUND_PATH | CSV connector and data import router are present; data import router is imported L33 and included L309. |
| P61 | TRD-CLI-FULL | No app-path CLI file visible | NO_OBVIOUS_PATH | No CLI file appears under target app path. |
| P63 | TRD-EVIDENCE-NL | `evidence.py`, `routers\evidence.py`, `routers\prescore.py` | FOUND_PATH | Evidence module/router are present; evidence router is imported L34 and included L292. |
| P81 | TRD-REGIME-CLASSIFIER | `services\regime.py`, `factors\market_regime.py`, `routers\regime.py` | FOUND_PATH | Regime service/factor/router files are present; regime router is imported L39 and included L304. |
| P82 | TRD-REALTIME-SCORE | `routers\webhook.py`, `routers\prescore.py`, `main.py` | UNCLEAR | Webhook and prescore paths are visible and registered, but no explicit realtime-score module name was observed. |
| P83 | TRD-PROMOTION-ENGINE | `services\promotion.py`, `routers\promotion.py`, `evolution\evolver_config.py` | FOUND_PATH | Promotion service/router/evolver config are present; promotion router is imported L38 and included L297-L303. |
| P84 | TRD-AGENT-EVOLVER-FULL | `evolution\evolver_config.py`, `evolution\dimensions.py`, `evolution\variant_provider.py`, `main.py` | FOUND_PATH | `main.py` imports `get_trading_variants` L35 and wires it into `create_evolution_router` L274-L280. |
| P85 | TRD-REGIME-RECOMMEND | `services\regime_recommender.py`, `routers\regime.py`, `services\vix_timing.py`, `routers\vix_timing.py` | FOUND_PATH | Regime recommender and VIX timing modules are present; regime and VIX timing routers are included L304 and L306. |

## Diagnostic Limitations

- This diagnostic does not prove implementation completeness.
- This diagnostic does not validate endpoint behavior or service behavior.
- No tests were run.
- No source files were changed.
- The MAP table is path discovery only.
- External `copilot_sdk.backend` routers were noted from `main.py` imports and registrations but were not inspected as part of the target app tree.

## Recommended Next Step

Run the smallest follow-up diagnostic that scans `apps/trading/backend` outside `app` and searches for exact MAP labels or feature names, especially CLI, IKS, trust radar, and realtime score references. Keep it read-only unless a later implementation prompt explicitly requests code changes.
