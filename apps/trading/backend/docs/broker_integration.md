# Broker Integration — Design Decisions
**Date:** 2026-05-25 · **Repo:** copilot-sdk/apps/trading

## Architecture
- `BrokerProtocol` is the CLI execution boundary.
- `AlpacaBroker` implements live or paper order execution with `httpx`.
- `MockBroker` implements deterministic local execution for tests.
- `connectors/` remains historical fill import.
- `brokers/` is live or paper execution and order state.
- No FastAPI routers are changed for this feature.
- No frontend contract is introduced.
- Broker commands are intentionally CLI-only.

## CLI Commands Added
| Command | Args | Behavior |
|---|---|---|
| `order` | `ticker side qty --type --limit-price --broker` | Places one broker order. |
| `orders` | `--status --limit --broker` | Lists broker orders. |
| `positions` | `--broker` | Lists open positions. |
| `account` | `--broker` | Shows account cash, equity, and buying power. |
| `sync` | `--dry-run --limit --broker` | Syncs filled broker orders to local `trades.json`. |

## Broker Flag Scope
- `--broker` is scoped to broker subcommands.
- Non-broker commands do not parse broker options.
- Non-broker commands do not instantiate broker classes.
- This avoids credential checks during `journal`, `score`, `regime`, and other offline commands.
- The existing `import --broker` option remains historical import source selection.

## Sync Design
- `sync` requests filled orders from the selected broker.
- Synced trades use `trade_id = "{broker}_{order_id}"`.
- Alpaca synced trades therefore use `alpaca_{order_id}`.
- Existing trades are loaded through the CLI `_load_trades()` helper.
- New trades are written through the CLI `_save_trades()` helper.
- `--dry-run` prints candidate rows and does not write.
- Existing `trade_id` values are skipped to keep sync idempotent.
- Synced rows use the journal-compatible local trade shape.
- Missing category data is stored as `uncategorized`.
- Users should run `retag` before using category-level scoring or promotion analysis.

## Journal Entry Format
- `trade_id`
- `ticker`
- `direction`
- `entry_price`
- `entry_time`
- `exit_price`
- `exit_time`
- `pnl`
- `category`
- `strategy_tag`
- `regime`
- `metadata.source`
- `metadata.broker_order_id`
- `metadata.qty`
- `metadata.order_type`
- `metadata.synced_at`

## Domain Context
- Trading scoring evaluates execution quality.
- It does not provide buy, hold, or sell advice.
- Broker fills are verified execution records for later journaling and scoring.
- `direction` records the fill side as long or short journal context.
- Execution-quality scoring remains separate from order placement.

## Security
- Alpaca credentials come from environment variables only.
- Use `APCA_API_KEY_ID` for the API key.
- Use `APCA_API_SECRET_KEY` for the API secret.
- Use `APCA_API_BASE_URL` to override the paper base URL when needed.
- The default Alpaca base URL is the paper endpoint.
- Missing Alpaca credentials fail explicitly.
- There is no fallback from Alpaca to mock.
- Tests use `MockBroker` or injected clients and do not call real broker APIs.
- Secrets are not logged.

## Error Handling
- Broker validation and HTTP failures raise `BrokerError`.
- CLI broker commands catch broker errors and return exit code 1.
- Missing credentials raise an environment configuration error.
- Alpaca HTTP 403 is reported as a forbidden broker rejection.
- Alpaca HTTP 422 is reported as an invalid order.
- Network and timeout failures are reported without credential values.

## Test Summary
- Broker protocol tests cover mock order behavior and factory behavior.
- CLI tests cover order, orders, positions, account, and sync.
- Sync tests cover dry-run and duplicate prevention.
- Credential tests cover missing Alpaca key and secret.
- Regression tests should include the existing Trading CLI suite.

## Future
- Add an `IBKRBroker` execution adapter.
- Add broker webhook sync.
- Add close-tracking for realized P&L.
- Add richer order metadata if broker APIs expose strategy tags.
- Add live/paper safety prompts for production accounts.
