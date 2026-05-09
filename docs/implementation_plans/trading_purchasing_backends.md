# Trading + Purchasing Backend Apps Implementation Plan

## 1. Executive Summary

Implement two FastAPI app backends under `apps/`:

- Trading backend mounts the SDK scoring router for domain `trading` and adds trading-specific context and trade metadata endpoints.
- Purchasing backend mounts the SDK scoring router for domain `purchasing`, mounts the SDK evolution router with an app-local fixture ledger provider, and adds purchasing-specific context and order metadata endpoints.

This block must not modify `copilot_sdk/backend`, `copilot_sdk/scoring`, root tests, or frontend code. Backend apps must be importable by tests and must not hardcode ports in Python code. Frontend implementation remains out of scope.

## 2. Source Contracts from Prompt 0

### SDK Scoring Router

Actual factory:

```python
create_scoring_router(
    domain: str,
    db_path: str | None = None,
    scorer_factory: Callable[..., Any] | None = None,
) -> APIRouter
```

The returned router exposes:

- `POST /score`
- `POST /learn`
- `GET /fingerprint`
- `GET /trajectory`
- `GET /history`

The router constructs `CompoundingScorer.from_preset(domain, db_path=db_path)` when no `scorer_factory` is supplied. Score responses include the scoring result fields plus `engine`. Learn responses include the learn result fields plus `reward`, `previous_reward`, `reward_multiplier`, and `engine`.

### SDK Evolution Router

Actual factory:

```python
create_evolution_router(
    domain: str,
    ledger_provider: Callable[[], Any] | Any | None = None,
) -> APIRouter
```

The returned router exposes:

- `GET /evolution/variants`
- `GET /evolution/patterns`

`ledger_provider` may be a callable, awaitable, object, or `None`. With no usable ledger it returns safe empty responses. For purchasing, implement an app-local fixture provider matching the GAE evolution helper expectations used by the SDK router tests.

### Trading Preset Contract

Domain: `trading`

Categories:

- `equity_long`
- `equity_short`
- `crypto_spot`
- `options`
- `etf`

Actions:

- `buy`
- `hold`
- `sell`

Factors:

- `conviction`
- `research_depth`
- `technical_signal`
- `position_size`
- `time_horizon`
- `market_regime`

Penalty ratio: `2.0`.

### Purchasing Preset Contract

Domain: `purchasing`

Categories:

- `protein`
- `produce`
- `dairy`
- `dry_goods`
- `beverages`

Actions:

- `order_as_planned`
- `order_more`
- `order_less`
- `skip`

Factors:

- `expected_demand`
- `day_of_week`
- `weather_forecast`
- `event_flag`
- `historical_waste`
- `supplier_lead_time`

Penalty ratio: `3.0`.

### Weather Adapter Contract

Actual callable:

```python
get_weather_factor(zip_code: str = "10001", date=None, use_live: bool = False) -> WeatherForecast
```

Default `use_live=False` returns cached data and performs no network call. Returned fields are:

- `temperature_f`
- `precipitation_prob`
- `wind_mph`
- `weather_factor`
- `source`

## 3. Files to Create

### Trading

- `apps/trading/backend/app/__init__.py`
- `apps/trading/backend/app/main.py`
- `apps/trading/backend/app/context_router.py`
- `apps/trading/backend/data/market_snapshot.json`
- `apps/trading/backend/data/ticker_cache.json`
- `apps/trading/backend/data/portfolio_summary.json`
- `apps/trading/backend/data/trade_metadata.json`
- `apps/trading/backend/tests/conftest.py`
- `apps/trading/backend/tests/test_trading_backend.py`
- `apps/trading/.env.example`

`trade_metadata.json` should start as `{}` when using the JSON store.

### Purchasing

- `apps/purchasing/backend/app/__init__.py`
- `apps/purchasing/backend/app/main.py`
- `apps/purchasing/backend/app/context_router.py`
- `apps/purchasing/backend/app/items.json`
- `apps/purchasing/backend/data/waste_history.json`
- `apps/purchasing/backend/data/weather_cache.json`
- `apps/purchasing/backend/data/evolution_fixtures.json`
- `apps/purchasing/backend/data/order_metadata.json`
- `apps/purchasing/backend/tests/conftest.py`
- `apps/purchasing/backend/tests/test_purchasing_backend.py`
- `apps/purchasing/.env.example`

`order_metadata.json` should start as `{}` when using the JSON store.

## 4. Forbidden Files

Do not modify:

- `copilot_sdk/scoring/**`
- `copilot_sdk/backend/**`
- root `tests/**`
- `copilot_sdk/frontend/**`
- `apps/*/frontend/**`
- `graph-attention-engine-v50/**`
- `gen-ai-roi-demo-v4-v50/**`
- `s2p-copilot/**`
- `ci-platform/**`
- package/build/config files

Do not use git.

## 5. Trading Backend Contract

### `main.py`

Implement an importable FastAPI app module with:

- `create_app() -> FastAPI`
- module-level `app = create_app()` if consistent with tests
- title `Trading Copilot`
- wide-open CORS for Loom
- robust `sys.path` setup for repo root and GAE path only if needed by local imports
- `app.include_router(create_scoring_router("trading", db_path=<app data db>), prefix="/api")`
- `app.include_router(context_router, prefix="/api/context")`
- `GET /health`

`/health` should return:

```json
{
  "status": "ok",
  "domain": "trading",
  "engine": "copilot_sdk.backend.scoring_router + gae.profile_scorer"
}
```

No Python code should hardcode a port. Keep ports in `.env.example` only.

### `context_router.py`

Expose:

- `GET /market-snapshot`
- `GET /ticker/{ticker}`
- `GET /portfolio-summary`
- `POST /trade-metadata`
- `GET /trade-metadata`

Metadata behavior:

- Use `apps/trading/backend/data/trade_metadata.json`.
- Store records keyed by `decision_id`.
- `POST /trade-metadata` validates that `decision_id` exists in the payload.
- Return HTTP 201 for create/update.
- Do not persist outside the app data file.
- Unknown tickers should return a clear 404.

## 6. Trading Fixture Contract

### `market_snapshot.json`

Include cached market context:

- `spy`
- `vix`
- `sector`
- `source`: `cached`

### `ticker_cache.json`

Include entries for every ticker used in `trading_seed.json`:

- `AAPL`
- `BTC`
- `COIN`
- `ETH`
- `IWM`
- `META`
- `MSFT`
- `NVDA`
- `QQQ`
- `SPY`
- `TLT`
- `TSLA`

Each ticker entry should include enough context for the UI and tests, such as `ticker`, `price`, `change_pct`, `source`, and optional `category_hint`.

### `portfolio_summary.json`

Include:

- `total_trades`
- `win_rate`
- `best_category`
- `worst_category`
- optional exposure or cash fields

Keep fixture data deterministic and cached.

## 7. Purchasing Backend Contract

### `main.py`

Implement an importable FastAPI app module with:

- `create_app() -> FastAPI`
- module-level `app = create_app()` if consistent with tests
- title `Purchasing Copilot`
- wide-open CORS for Loom
- `app.include_router(create_scoring_router("purchasing", db_path=<app data db>), prefix="/api")`
- `app.include_router(create_evolution_router("purchasing", ledger_provider=<fixture provider>), prefix="/api")`
- `app.include_router(context_router, prefix="/api/context")`
- `GET /health`

`/health` should return:

```json
{
  "status": "ok",
  "domain": "purchasing",
  "engine": "copilot_sdk.backend.scoring_router + gae.profile_scorer + gae.evolution"
}
```

No Python code should hardcode a port. Keep ports in `.env.example` only.

### `context_router.py`

Expose:

- `GET /today-summary`
- `GET /items`
- `GET /waste-history/{item}`
- `GET /weather`
- `POST /order-metadata`
- `GET /order-metadata`

Metadata behavior:

- Use `apps/purchasing/backend/data/order_metadata.json`.
- Store records keyed by `decision_id`.
- `POST /order-metadata` validates that `decision_id` exists in the payload.
- Return HTTP 201 for create/update.
- Do not persist outside the app data file.
- Unknown waste-history items should return a clear 404.

Weather behavior:

- Use the cached SDK weather adapter by default.
- Do not use live network in tests.
- Include returned `WeatherForecast` fields in the response.

### Evolution fixtures

If `create_evolution_router` accepts `ledger_provider`, pass an app-local provider. The provider should expose data compatible with `gae.evolution.get_recent_events` and `gae.evolution.get_evolution_summary`, or the app tests should monkeypatch the SDK router evolution helpers around this fixture.

If fixture integration with the GAE helper shape proves incompatible, keep the SDK evolution router mounted with no provider and add no app-local duplicate evolution endpoints. Do not modify `copilot_sdk/backend/evolution_router.py`.

Responses from SDK evolution routes must preserve engine metadata containing `gae.evolution`.

## 8. Purchasing Fixture Contract

### `items.json`

Exactly 20 items across the 5 purchasing categories:

- `protein`
- `produce`
- `dairy`
- `dry_goods`
- `beverages`

Each item should include a stable item id/name, category, unit, par level or typical quantity, and supplier/lead-time hints if useful.

### `waste_history.json`

- Every item key from `items.json` lowercased with spaces replaced by underscores.
- Each value is a list of length 5.
- Values should be deterministic numeric history points.

### `weather_cache.json`

Cached weather object with:

- `temperature_f`
- `precipitation_prob`
- `wind_mph`
- `weather_factor`
- `source`

### `evolution_fixtures.json`

Exactly 3 variants:

- 2 promoted
- 1 rejected

Include fields compatible with the SDK evolution payload where possible:

- `id`
- `variant_id`
- `event_type`
- `artifact_type`
- `description`
- `impact`
- `magnitude`
- `timestamp`
- `timestamp_epoch`
- `metadata`
- optional `source_copilot`, `source_rule`, or `warm_start_prior` for patterns

## 9. Tests

Tests must live under app-local test folders, not root `tests/`.

### Trading tests

`apps/trading/backend/tests/test_trading_backend.py` should cover:

- `/health`
- `GET /api/context/market-snapshot`
- `GET /api/context/ticker/{ticker}` for a known ticker
- `GET /api/context/ticker/{ticker}` for an unknown ticker
- `POST /api/context/trade-metadata`
- `GET /api/context/trade-metadata`
- `POST /api/score` through the SDK router
- `POST /api/learn` returns reward fields
- fingerprint after at least 3 score/learn cycles

Use `TestClient`. Use temporary copied metadata files or monkeypatch app data paths so tests do not mutate committed fixture JSON unexpectedly.

### Purchasing tests

`apps/purchasing/backend/tests/test_purchasing_backend.py` should cover:

- `/health`
- `GET /api/context/today-summary`
- `GET /api/context/items` and category coverage
- `GET /api/context/waste-history/{item}` for a known item
- `GET /api/context/waste-history/{item}` for an unknown item
- `GET /api/context/weather`
- `POST /api/context/order-metadata`
- `GET /api/context/order-metadata`
- `POST /api/score` through the SDK router
- `POST /api/learn` returns reward fields
- `GET /api/evolution/variants`
- fingerprint after at least 3 score/learn cycles

Use `TestClient`. Keep tests network-free and app-local.

## 10. Validation Commands

From the target repo:

```powershell
python -m pytest apps/trading/backend/tests/ -v --timeout=120
python -m pytest apps/purchasing/backend/tests/ -v --timeout=120
python -m pytest tests/ -q --timeout=120
```

Import smoke:

```powershell
python -c "from apps.trading.backend.app.main import create_app; print('trading app OK')"
python -c "from apps.purchasing.backend.app.main import create_app; print('purchasing app OK')"
```

Optional user-run server smoke:

```powershell
uvicorn apps.trading.backend.app.main:app --reload
uvicorn apps.purchasing.backend.app.main:app --reload
```

Do not hardcode those ports in Python code.

## 11. Implementation Sequence

### Prompt 2: Trading backend

Create trading backend app, context router, fixtures, metadata JSON store, and app-local tests. Do not touch purchasing or SDK core.

### Prompt 3: Purchasing backend

Create purchasing backend app, context router, fixtures, metadata JSON store, evolution fixture provider, and app-local tests. Do not touch trading except if a shared test helper in its own app folder requires no changes.

### Prompt 4: Review

Mandatory line-by-line review of both app backend implementations and tests.

## 12. Prompt Verification Pass

Before implementation:

1. Confirm `create_scoring_router` still has `domain`, optional `db_path`, and optional `scorer_factory`.
2. Confirm `create_evolution_router` still has `domain` and optional `ledger_provider`.
3. Confirm no SDK backend/scoring file is needed.
4. Confirm `.env.example` contains port hints only; Python app code contains no port constants.
5. Confirm tests are app-local under `apps/{domain}/backend/tests`.
6. Confirm fixture data is deterministic and network-free.

## 13. Residual Risks

- Evolution fixture compatibility depends on the current `gae.evolution` helper expectations. Keep the fixture provider small and covered by tests.
- SDK scoring routes create SQLite DB files through `db_path`; app tests should isolate those paths under temporary directories.
- The existing `CLAUDE.md` says the SDK package should not contain domain logic. Keep all domain-specific backend behavior under `apps/`.
