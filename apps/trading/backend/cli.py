"""Offline Phase 0 CLI for Trading Copilot."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import types
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Avoid executing app/__init__.py, which imports FastAPI app.main. The CLI only
# needs specific offline modules under app/.
if "app" not in sys.modules:
    app_package = types.ModuleType("app")
    app_package.__path__ = [str(BACKEND_ROOT / "app")]  # type: ignore[attr-defined]
    sys.modules["app"] = app_package

from app.connectors.csv_connector import CSVConnector  # noqa: E402
from app.factors.options import OPTIONS_FACTOR_NAMES, compute_options_factors  # noqa: E402
from app.factors.registry import (  # noqa: E402
    ALL_FACTOR_NAMES,
    TRADING_FACTOR_COMPUTERS,
    compute_factors,
)
from app.cli_sdk import (  # noqa: E402
    _cmd_conservation as _sdk_cmd_conservation,
    _cmd_decide as _sdk_cmd_decide,
    _cmd_init as _sdk_cmd_init,
    _cmd_journal as _sdk_cmd_journal,
    _cmd_learn as _sdk_cmd_learn,
    _cmd_record as _sdk_cmd_record,
    _cmd_score as _sdk_cmd_score,
    _cmd_status as _sdk_cmd_status,
    _cmd_trust as _sdk_cmd_trust,
    add_sdk_subcommands,
)
from app.services.subcategory import get_subcategory  # noqa: E402


DEFAULT_CONFIG_DIR = os.path.expanduser("~/.ci-trading")
CONFIG_FILENAME = "config.json"
TRADES_FILENAME = "trades.json"


def _config_path(config_dir: str | os.PathLike[str]) -> Path:
    return Path(config_dir).expanduser() / CONFIG_FILENAME


def _trades_path(config_dir: str | os.PathLike[str]) -> Path:
    return Path(config_dir).expanduser() / TRADES_FILENAME


def _ensure_config_dir(config_dir: str | os.PathLike[str]) -> Path:
    path = Path(config_dir).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_config(config_dir: str | os.PathLike[str]) -> dict[str, Any] | None:
    path = _config_path(config_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save_config(config: dict[str, Any], config_dir: str | os.PathLike[str]) -> None:
    _ensure_config_dir(config_dir)
    _config_path(config_dir).write_text(json.dumps(config, indent=2), encoding="utf-8")


def _load_trades(config_dir: str | os.PathLike[str]) -> list[dict[str, Any]]:
    path = _trades_path(config_dir)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _save_trades(trades: list[dict[str, Any]], config_dir: str | os.PathLike[str]) -> None:
    _ensure_config_dir(config_dir)
    _trades_path(config_dir).write_text(json.dumps(trades, indent=2), encoding="utf-8")


def _initialized(config_dir: str | os.PathLike[str]) -> bool:
    return _load_config(config_dir) is not None


def _print_factor_table(factors: dict[str, float]) -> None:
    print("Factor scores")
    for name in ALL_FACTOR_NAMES:
        value = float(factors.get(name, 0.5))
        bar = "#" * int(round(value * 20))
        print(f"{name:20} {value:0.3f} {bar}")


def _print_options_factor_table(context: dict[str, Any]) -> bool:
    if not _is_options_like_trade(context):
        return False
    options_factors = compute_options_factors(context)
    print("Options Factors (analytics-only):")
    for name in OPTIONS_FACTOR_NAMES:
        value = float(options_factors.get(name, 0.5))
        bar = "#" * int(round(value * 20))
        print(f"{name:20} {value:0.3f} {bar}")
    return True


def _save_imported_trades(
    parsed: list[Any],
    config_dir: str | os.PathLike[str],
) -> tuple[int, int, int]:
    existing = _load_trades(config_dir)
    seen = {str(trade.get("trade_id")) for trade in existing}
    imported: list[dict[str, Any]] = []
    duplicates = 0
    for trade in parsed:
        row = trade.to_dict() if hasattr(trade, "to_dict") else dict(trade)
        trade_id = str(row["trade_id"])
        if trade_id in seen:
            duplicates += 1
            continue
        seen.add(trade_id)
        imported.append(row)

    all_trades = [*existing, *imported]
    _save_trades(all_trades, config_dir)
    return len(imported), duplicates, len(all_trades)


def _get_broker(broker_name: str):
    from app.brokers import get_broker

    return get_broker(broker_name)


def _broker_error_types() -> tuple[type[BaseException], ...]:
    from app.brokers import BrokerError

    return (BrokerError, EnvironmentError, ValueError)


def _broker_name(args: argparse.Namespace) -> str:
    return str(getattr(args, "broker", None) or "alpaca").lower()


def _format_money(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "-"


def _format_order_row(order: Any) -> str:
    status = getattr(order, "status", "")
    status_text = getattr(status, "value", status)
    side = getattr(order, "side", "")
    side_text = getattr(side, "value", side)
    price = getattr(order, "avg_fill_price", None) or getattr(order, "limit_price", None)
    return (
        f"{str(getattr(order, 'order_id', '-'))[:18]:18} "
        f"{str(getattr(order, 'ticker', '-'))[:8]:8} "
        f"{str(side_text)[:5]:5} "
        f"{float(getattr(order, 'qty', 0.0) or 0.0):10.4g} "
        f"{str(status_text)[:10]:10} "
        f"{_format_money(price):>10}"
    )


def _synced_trade_id(broker_name: str, order_id: str) -> str:
    source = broker_name.lower().strip() or "broker"
    return f"{source}_{order_id}"


def _trade_from_order(order: Any, broker_name: str, synced_at: str) -> dict[str, Any]:
    side = getattr(order, "side", "")
    side_text = str(getattr(side, "value", side)).lower()
    qty = float(getattr(order, "filled_qty", None) or getattr(order, "qty", 0.0) or 0.0)
    order_id = str(getattr(order, "order_id", ""))
    metadata = dict(getattr(order, "metadata", {}) or {})
    metadata.update(
        {
            "source": broker_name,
            "broker_order_id": order_id,
            "qty": qty,
            "order_type": getattr(order, "order_type", None),
            "synced_at": synced_at,
        }
    )
    return {
        "trade_id": _synced_trade_id(broker_name, order_id),
        "ticker": str(getattr(order, "ticker", "")).upper(),
        "direction": "short" if side_text == "sell" else "long",
        "entry_price": getattr(order, "avg_fill_price", None) or getattr(order, "limit_price", None),
        "entry_time": getattr(order, "filled_at", None) or getattr(order, "submitted_at", None),
        "exit_price": None,
        "exit_time": None,
        "pnl": None,
        "category": "uncategorized",
        "strategy_tag": None,
        "regime": None,
        "metadata": metadata,
    }


def cmd_init(args: argparse.Namespace) -> int:
    config_dir = _ensure_config_dir(args.config_dir)
    config_path = _config_path(config_dir)
    trades_path = _trades_path(config_dir)

    if not config_path.exists():
        config = {
            "created": datetime.now(timezone.utc).isoformat(),
            "version": "0.1.0",
            "broker": None,
            "data_dir": str(config_dir),
        }
        _save_config(config, config_dir)
        print(f"Created config: {config_path}")
    else:
        print(f"Config already exists: {config_path}")

    if not trades_path.exists():
        _save_trades([], config_dir)
        print(f"Created trades store: {trades_path}")
    else:
        print(f"Trades store already exists: {trades_path}")
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    if args.disable_pattern_detection and args.enable_pattern_detection:
        print("Choose only one pattern-detection toggle.", file=sys.stderr)
        return 1

    config_dir = Path(args.config_dir).expanduser()
    config = _load_config(config_dir) or {
        "version": "0.1.0",
        "broker": None,
        "data_dir": str(config_dir),
        "pattern_detection_enabled": True,
    }

    changed = False
    if args.disable_pattern_detection:
        config["pattern_detection_enabled"] = False
        changed = True
    elif args.enable_pattern_detection:
        config["pattern_detection_enabled"] = True
        changed = True

    if changed:
        _save_config(config, config_dir)

    print(json.dumps(config, indent=2))
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    if not _initialized(args.config_dir):
        print("Trading CLI is not initialized. Run init first.", file=sys.stderr)
        return 1

    broker = str(args.broker or "csv").lower()
    if broker == "csv":
        csv_path = Path(args.file).expanduser() if args.file else None
        if csv_path is None or not csv_path.exists():
            print(f"CSV file not found: {csv_path}", file=sys.stderr)
            return 1
        connector = CSVConnector()
        parsed = (
            connector.import_flexible(str(csv_path), broker_preset=args.preset)
            if args.preset
            else connector.import_from_file(str(csv_path))
        )
    elif broker == "ibkr":
        try:
            from app.connectors.ibkr_connector import IBKRConnector

            parsed = IBKRConnector().import_trades(days=int(args.days))
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    else:
        print(f"Unsupported broker: {args.broker}", file=sys.stderr)
        return 1

    if not parsed:
        print("No trades parsed from import source.", file=sys.stderr)
        return 1

    imported, duplicates, total = _save_imported_trades(parsed, args.config_dir)
    print(f"Imported: {imported}")
    print(f"Duplicates: {duplicates}")
    print(f"Total trades: {total}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    trades = _load_trades(args.config_dir)
    if not trades:
        print("No trades available. Import trades first.", file=sys.stderr)
        return 1

    if args.trade_id:
        trade = next((row for row in trades if row.get("trade_id") == args.trade_id), None)
        if trade is None:
            print(f"Trade not found: {args.trade_id}", file=sys.stderr)
            return 1
        print(f"Trade: {args.trade_id}")
        _print_factor_table(compute_factors(trade))
        _print_options_factor_table(trade)
        print("Offline factor scoring only; no decision recorded.")
        return 0

    rows = [compute_factors(trade) for trade in trades]
    print(f"Trades scored: {len(rows)}")
    print("Factor summary")
    for name in ALL_FACTOR_NAMES:
        values = [float(row.get(name, 0.5)) for row in rows]
        print(
            f"{name:20} avg={mean(values):0.3f} "
            f"min={min(values):0.3f} max={max(values):0.3f}"
        )
    option_rows = [compute_options_factors(trade) for trade in trades if _is_options_like_trade(trade)]
    if option_rows:
        print("Options Factors (analytics-only):")
        for name in OPTIONS_FACTOR_NAMES:
            values = [float(row.get(name, 0.5)) for row in option_rows]
            print(
                f"{name:20} avg={mean(values):0.3f} "
                f"min={min(values):0.3f} max={max(values):0.3f}"
            )
    print("Offline factor scoring only; no decision recorded.")
    return 0


def cmd_trust(args: argparse.Namespace) -> int:
    trades = _load_trades(args.config_dir)
    if not trades:
        print("No trades available. Import trades first.", file=sys.stderr)
        return 1

    implemented = set(TRADING_FACTOR_COMPUTERS)
    neutral = [name for name in ALL_FACTOR_NAMES if name not in implemented]
    print("Implemented factors:")
    for name in sorted(implemented):
        print(f"- {name}")
    print("Neutral factors:")
    for name in neutral:
        print(f"- {name}")
    print(f"Neutral factor count: {len(neutral)}")

    sample = trades[:100]
    print("Implemented factor variance:")
    for name in sorted(implemented):
        values = [float(compute_factors(trade).get(name, 0.5)) for trade in sample]
        avg = mean(values)
        variance = mean([(value - avg) ** 2 for value in values])
        print(f"{name:20} variance={variance:0.6f}")
    return 0


def cmd_conservation(args: argparse.Namespace) -> int:
    trades = _load_trades(args.config_dir)
    if not trades:
        print("No trades available. Import trades first.", file=sys.stderr)
        return 1

    groups: dict[str, int] = {}
    for trade in trades:
        key = str(trade.get("category") or trade.get("strategy_tag") or "unknown")
        groups[key] = groups.get(key, 0) + 1

    print("Offline conservation proxy")
    for key in sorted(groups):
        count = groups[key]
        state = "GREEN" if count >= 50 else "AMBER" if count >= 20 else "RED"
        print(f"{key:20} {count:4d} {state}")
    print("Full conservation requires the scoring server.")
    return 0


def cmd_journal(args: argparse.Namespace) -> int:
    trades = _load_trades(args.config_dir)
    if not trades:
        print("No trades available. Import trades first.", file=sys.stderr)
        return 1

    filtered = _filter_journal_trades(
        trades,
        ticker=args.ticker,
        category=args.category,
        strategy=args.strategy,
        wins_only=args.wins_only,
        losses_only=args.losses_only,
    )
    if not filtered:
        print("No trades match filters.")
        return 0

    limit = max(int(args.limit), 0)
    visible = filtered[:limit] if limit else []
    pnls = [_trade_pnl(trade) for trade in filtered if _trade_pnl(trade) is not None]
    wins = sum(1 for trade in filtered if (_trade_pnl(trade) or 0.0) > 0)
    win_rate = wins / len(filtered) if filtered else 0.0
    avg_pnl = mean(pnls) if pnls else 0.0
    total_pnl = sum(pnls) if pnls else 0.0

    print(f"Trades: {len(filtered)}")
    print(f"Win rate: {win_rate:.1%}")
    print(f"Avg P&L: {avg_pnl:.2f}")
    print(f"Total P&L: {total_pnl:.2f}")
    print(f"{'ID':12} {'Ticker':8} {'Dir':6} {'P&L':>10} {'Category':18} {'Strategy':18}")
    for trade in visible:
        print(
            f"{str(trade.get('trade_id', '-'))[:12]:12} "
            f"{str(trade.get('ticker', '-'))[:8]:8} "
            f"{str(trade.get('direction', '-'))[:6]:6} "
            f"{(_trade_pnl(trade) or 0.0):10.2f} "
            f"{str(trade.get('category') or '-')[:18]:18} "
            f"{str(trade.get('strategy_tag') or trade.get('thesis_type') or '-')[:18]:18}"
        )
    _print_event_subcategory_summary(filtered, args.category)
    _print_options_journal_summary(filtered)
    return 0


def _print_event_subcategory_summary(trades: list[dict[str, Any]], category_filter: str | None) -> None:
    if category_filter not in {None, "", "event_driven"}:
        return
    event_trades = [trade for trade in trades if trade.get("category") == "event_driven"]
    if not event_trades:
        return
    print("Event-Driven Subcategories")
    for subcategory in ("directional", "volatility"):
        rows = [trade for trade in event_trades if get_subcategory(trade) == subcategory]
        wins = sum(1 for trade in rows if (_trade_pnl(trade) or 0.0) > 0)
        win_rate = wins / len(rows) if rows else 0.0
        print(f"- {subcategory}: {len(rows)} trades, win rate {win_rate:.1%}")


def _print_options_journal_summary(trades: list[dict[str, Any]]) -> None:
    option_trades = [trade for trade in trades if _is_options_like_trade(trade)]
    if not option_trades:
        return
    rows = [compute_options_factors(trade) for trade in option_trades]
    print("Options Factors (analytics-only):")
    for name in OPTIONS_FACTOR_NAMES:
        values = [float(row.get(name, 0.5)) for row in rows]
        print(f"- {name}: avg {mean(values):.3f} across {len(values)} trades")


def cmd_regime(args: argparse.Namespace) -> int:
    from app.services.regime import RegimeService

    service = RegimeService()
    current = service.get_current_regime()
    print(f"Current regime: {current.get('regime', 'ranging')}")
    print(f"VIX: {float(current.get('vix', 20.0) or 0.0):0.2f}")
    print(f"ADX: {float(current.get('adx', 20.0) or 0.0):0.2f}")
    print(f"Source: {current.get('source', 'default')}")

    trades = _load_trades(args.config_dir)
    accuracy = service.get_regime_accuracy(trades) if trades else {}
    if args.detail:
        from app.services.regime_recommender import RegimeRecommender

        detail = RegimeRecommender().recommend(
            str(current.get("regime") or "ranging"),
            accuracy,
            conservation_status=None,
        )
        print("Regime Allocation Context")
        print(str(detail["summary"]))
        if detail["conservation_safe"] is False:
            print("Conservation not confirmed; recommendations are informational.")
        recommendations = detail.get("recommendations") or []
        if recommendations:
            print(f"{'Category':20} {'Action':10} {'Shift':>8} {'Neutral':>8}")
            for item in recommendations:
                print(
                    f"{str(item.get('category', '-'))[:20]:20} "
                    f"{str(item.get('action', '-'))[:10]:10} "
                    f"{int(item.get('shift_pct', 0)):>7}% "
                    f"{str(bool(item.get('regime_neutral'))):>8}"
                )
        else:
            print("No regime recommendations available.")
        transitions = detail.get("regime_transitions") or []
        if transitions:
            print("Regime transitions")
            for transition in transitions:
                print(
                    f"{transition['from_regime']} -> {transition['to_regime']}: "
                    f"{transition['avg_accuracy_delta_pp']:+.1f}pp "
                    f"({transition['count']} categories)"
                )
        return 0

    if not trades:
        print("No local trades available for regime accuracy.")
        return 0

    if not accuracy:
        print("No regime accuracy available.")
        return 0

    print(f"{'Category':20} {'Trending':>10} {'Ranging':>10} {'Volatile':>10}")
    for category, regimes in sorted(accuracy.items()):
        print(
            f"{category[:20]:20} "
            f"{_format_rate(regimes.get('trending')):>10} "
            f"{_format_rate(regimes.get('ranging')):>10} "
            f"{_format_rate(regimes.get('volatile')):>10}"
        )
    return 0


def cmd_correlation(args: argparse.Namespace) -> int:
    from app.services.correlation import CorrelationService

    trades = _load_trades(args.config_dir)
    if not trades:
        print("No trades. Import trades first.", file=sys.stderr)
        return 1
    result = CorrelationService(window_days=args.window).compute(trades)
    if result.get("source") == "insufficient_data":
        print(str(result.get("reason") or "Insufficient data for correlation monitoring."))
        return 0

    print(f"Correlation monitor ({result['window_days']} days)")
    print(f"Tickers: {', '.join(result.get('tickers') or [])}")
    print(f"Average correlation: {float(result.get('avg_correlation') or 0.0):.2f}")
    max_pair = result.get("max_pair")
    if isinstance(max_pair, dict):
        print(
            "Max pair: "
            f"{max_pair.get('ticker_a')} / {max_pair.get('ticker_b')} "
            f"({float(max_pair.get('correlation') or 0.0):.2f})"
        )
    alerts = result.get("alerts") or []
    if alerts:
        print("Alerts:")
        for alert in alerts:
            print(f"- {alert.get('level')}: {alert.get('message')}")
    else:
        print("Alerts: none")
    print(f"{'Pair':18} {'Correlation':>12}")
    for pair in (result.get("pairs") or [])[:10]:
        print(
            f"{str(pair.get('ticker_a')) + '/' + str(pair.get('ticker_b')):18} "
            f"{float(pair.get('correlation') or 0.0):12.2f}"
        )
    return 0


def cmd_vix_timing(args: argparse.Namespace) -> int:
    from app.services.regime import RegimeService
    from app.services.vix_timing import HOLD_BUCKETS, HOLD_DISPLAY, VIX_BUCKETS, VIX_DISPLAY, VIXTimingService

    trades = _load_trades(args.config_dir)
    if not trades:
        print("No trades. Import trades first.", file=sys.stderr)
        return 1

    vix_data = RegimeService().get_historical_vix(trades)
    result = VIXTimingService().analyze(trades, vix_data)
    print("VIX timing analysis")
    print(f"Analyzed: {int(result.get('total_analyzed') or 0)}")
    print(f"Skipped: {int(result.get('total_skipped') or 0)}")
    print(f"{'Hold period':16} {'Low VIX':>12} {'Medium VIX':>12} {'High VIX':>12}")
    matrix = result.get("matrix") if isinstance(result.get("matrix"), dict) else {}
    for hold_bucket in HOLD_BUCKETS:
        row = matrix.get(hold_bucket, {}) if isinstance(matrix, dict) else {}
        values = []
        for vix_bucket in VIX_BUCKETS:
            cell = row.get(vix_bucket, {}) if isinstance(row, dict) else {}
            if cell.get("count"):
                values.append(f"{float(cell.get('accuracy') or 0.0):.0%}/{int(cell.get('count') or 0)}")
            else:
                values.append("-")
        print(f"{HOLD_DISPLAY[hold_bucket]:16} {values[0]:>12} {values[1]:>12} {values[2]:>12}")

    best = result.get("best_bucket")
    if isinstance(best, dict):
        print(
            "Best: "
            f"{HOLD_DISPLAY.get(str(best.get('hold_bucket')), str(best.get('hold_bucket')))} / "
            f"{VIX_DISPLAY.get(str(best.get('vix_bucket')), str(best.get('vix_bucket')))} "
            f"({float(best.get('accuracy') or 0.0):.0%}, {int(best.get('count') or 0)} trades)"
        )
    worst = result.get("worst_bucket")
    if isinstance(worst, dict):
        print(
            "Worst: "
            f"{HOLD_DISPLAY.get(str(worst.get('hold_bucket')), str(worst.get('hold_bucket')))} / "
            f"{VIX_DISPLAY.get(str(worst.get('vix_bucket')), str(worst.get('vix_bucket')))} "
            f"({float(worst.get('accuracy') or 0.0):.0%}, {int(worst.get('count') or 0)} trades)"
        )

    print("Performance observations")
    for recommendation in result.get("recommendations") or []:
        print(f"- {recommendation}")
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    from app.services.promotion import PromotionService, _metrics, strategy_key

    trades = _load_trades(args.config_dir)
    service = PromotionService(config_dir=args.config_dir)
    if args.evaluate:
        events = service.evaluate(trades, conservation_status={"phase": "unknown", "source": "cli"})
        if not events:
            print("No tier changes. Conservation status is unknown in CLI mode; promotions require GREEN conservation.")
            return 0
        print("Promotion events")
        for event in events:
            print(
                f"{event['strategy_key']}: {event['action']} "
                f"{event['from_tier']} -> {event['to_tier']} "
                f"({event['reason']})"
            )
        return 0

    groups: dict[str, list[dict[str, Any]]] = {}
    for trade in trades:
        category = trade.get("category")
        if not category:
            continue
        key = strategy_key(str(category), trade.get("strategy_tag") or trade.get("thesis_type"))
        groups.setdefault(key, []).append(trade)
    if not groups:
        print("No strategies tracked yet. Score trades to begin.")
        return 0

    print(f"{'Strategy':28} {'Tier':12} {'Verified':>8} {'Win rate':>8}")
    for key, rows in sorted(groups.items()):
        metrics = _metrics(rows)
        print(
            f"{key[:28]:28} "
            f"{service.get_tier(key):12} "
            f"{metrics['verified_count']:8d} "
            f"{metrics['win_rate']:8.0%}"
        )
    return 0


def _format_rate(value: float | None) -> str:
    return "-" if value is None else f"{value:.0%}"


def _filter_journal_trades(
    trades: list[dict[str, Any]],
    *,
    ticker: str | None,
    category: str | None,
    strategy: str | None,
    wins_only: bool,
    losses_only: bool,
) -> list[dict[str, Any]]:
    output = list(trades)
    if ticker:
        output = [trade for trade in output if str(trade.get("ticker") or "").upper() == ticker.upper()]
    if category:
        output = [trade for trade in output if str(trade.get("category") or "") == category]
    if strategy:
        output = [
            trade for trade in output
            if str(trade.get("strategy_tag") or trade.get("thesis_type") or "") == strategy
        ]
    if wins_only:
        output = [trade for trade in output if (_trade_pnl(trade) or 0.0) > 0]
    if losses_only:
        output = [trade for trade in output if _trade_pnl(trade) is not None and (_trade_pnl(trade) or 0.0) <= 0]
    return output


def _is_options_like_trade(trade: dict[str, Any]) -> bool:
    if str(trade.get("category") or "") == "income_strategy":
        return True
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    text = " ".join(
        str(value or "")
        for value in (
            trade.get("strategy_tag"),
            trade.get("thesis_type"),
            trade.get("category"),
            trade.get("subcategory"),
            trade.get("notes"),
            trade.get("direction"),
            metadata.get("strategy_tag"),
            metadata.get("notes"),
        )
    ).lower().replace("-", "_").replace(" ", "_")
    return any(
        token in text
        for token in (
            "option",
            "straddle",
            "strangle",
            "iron_condor",
            "credit",
            "debit",
            "covered",
            "wheel",
            "calendar",
            "butterfly",
            "premium",
            "iv",
        )
    )


def _trade_pnl(trade: dict[str, Any]) -> float | None:
    value = trade.get("pnl")
    if value is None:
        value = trade.get("pnl_dollars")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def cmd_export(args: argparse.Namespace) -> int:
    trades = _load_trades(args.config_dir)
    if not trades:
        print("No trades to export.", file=sys.stderr)
        return 1
    export_format = str(args.format).lower()
    output = Path(args.output).expanduser() if args.output else Path(args.config_dir).expanduser() / f"export.{export_format}"
    output.parent.mkdir(parents=True, exist_ok=True)
    if export_format == "json":
        output.write_text(json.dumps(trades, indent=2, default=str), encoding="utf-8")
    elif export_format == "csv":
        fieldnames = sorted({key for trade in trades for key in trade})
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(trades)
    else:
        print(f"Unsupported export format: {args.format}", file=sys.stderr)
        return 1
    print(f"Exported {len(trades)} trades to {output}")
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    _ensure_config_dir(args.config_dir)
    trades = _load_trades(args.config_dir)
    config = _load_config(args.config_dir) or {}
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = {
        "version": "0.1.0",
        "timestamp": timestamp,
        "config": config,
        "trades": trades,
        "trade_count": len(trades),
    }
    backup_dir = Path(args.config_dir).expanduser() / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    output = backup_dir / f"trading-backup-{timestamp}.json"
    output.write_text(json.dumps(backup, indent=2, default=str), encoding="utf-8")
    print(f"Backup written: {output}")
    print(f"Trade count: {len(trades)}")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    backup_path = Path(getattr(args, "from_file")).expanduser()
    if not backup_path.exists():
        print(f"Backup file not found: {backup_path}", file=sys.stderr)
        return 1
    payload = json.loads(backup_path.read_text(encoding="utf-8"))
    trades = payload.get("trades") if isinstance(payload, dict) else None
    if not isinstance(trades, list):
        print("Backup file does not contain trades.", file=sys.stderr)
        return 1
    config = payload.get("config") if isinstance(payload.get("config"), dict) else None
    if config is not None:
        _save_config(config, args.config_dir)
    else:
        _ensure_config_dir(args.config_dir)
    _save_trades(trades, args.config_dir)
    print(f"Restored {len(trades)} trades from {backup_path}")
    return 0


def cmd_retag(args: argparse.Namespace) -> int:
    trades = _load_trades(args.config_dir)
    for trade in trades:
        if str(trade.get("trade_id")) == str(args.trade_id):
            old = trade.get("category")
            trade["category"] = args.category
            _save_trades(trades, args.config_dir)
            print(f"Retagged {args.trade_id}: {old or '-'} -> {args.category}")
            return 0
    print(f"Trade not found: {args.trade_id}", file=sys.stderr)
    return 1


def cmd_order(args: argparse.Namespace) -> int:
    from app.brokers import OrderRequest, OrderSide

    try:
        qty = float(args.qty)
        if qty <= 0:
            raise ValueError("quantity must be positive")
        order_type = str(args.type).lower()
        limit_price = float(args.limit_price) if args.limit_price is not None else None
        if order_type == "limit" and limit_price is None:
            print("Limit orders require --limit-price.", file=sys.stderr)
            return 1
        broker = _get_broker(_broker_name(args))
        result = broker.place_order(
            OrderRequest(
                ticker=args.ticker,
                side=OrderSide(str(args.side).lower()),
                qty=qty,
                order_type=order_type,
                limit_price=limit_price,
            )
        )
    except _broker_error_types() as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("Order submitted")
    print(_format_order_row(result))
    return 0


def cmd_orders(args: argparse.Namespace) -> int:
    try:
        orders = _get_broker(_broker_name(args)).get_orders(status=args.status, limit=int(args.limit))
    except _broker_error_types() as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not orders:
        print("No orders.")
        return 0
    print(f"{'Order ID':18} {'Ticker':8} {'Side':5} {'Qty':>10} {'Status':10} {'Price':>10}")
    for order in orders:
        print(_format_order_row(order))
    return 0


def cmd_positions(args: argparse.Namespace) -> int:
    try:
        positions = _get_broker(_broker_name(args)).get_positions()
    except _broker_error_types() as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not positions:
        print("No positions.")
        return 0
    print(f"{'Ticker':8} {'Qty':>10} {'Avg Entry':>12} {'Current':>12} {'Unreal P&L':>12}")
    for position in positions:
        print(
            f"{str(position.ticker)[:8]:8} "
            f"{float(position.qty):10.4g} "
            f"{float(position.avg_entry_price):12.2f} "
            f"{float(position.current_price):12.2f} "
            f"{float(position.unrealized_pnl):12.2f}"
        )
    return 0


def cmd_account(args: argparse.Namespace) -> int:
    try:
        account = _get_broker(_broker_name(args)).get_account()
    except _broker_error_types() as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Cash: {_format_money(account.get('cash'))}")
    print(f"Equity: {_format_money(account.get('equity'))}")
    print(f"Buying power: {_format_money(account.get('buying_power'))}")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    if not _initialized(args.config_dir):
        print("Trading CLI is not initialized. Run init first.", file=sys.stderr)
        return 1
    broker_name = _broker_name(args)
    try:
        orders = _get_broker(broker_name).get_orders(status="filled", limit=int(args.limit))
    except _broker_error_types() as exc:
        print(str(exc), file=sys.stderr)
        return 1

    trades = _load_trades(args.config_dir)
    existing_ids = {str(trade.get("trade_id")) for trade in trades}
    synced_at = datetime.now(timezone.utc).isoformat()
    new_trades: list[dict[str, Any]] = []
    for order in orders:
        order_id = str(getattr(order, "order_id", ""))
        if not order_id:
            continue
        trade_id = _synced_trade_id(broker_name, order_id)
        if trade_id in existing_ids:
            continue
        new_trades.append(_trade_from_order(order, broker_name, synced_at))
        existing_ids.add(trade_id)

    if args.dry_run:
        print(f"Would sync: {len(new_trades)}")
        for trade in new_trades:
            print(f"- {trade['trade_id']} {trade['ticker']} {trade['direction']} {trade['entry_price']}")
        return 0

    if new_trades:
        _save_trades([*trades, *new_trades], args.config_dir)
    print(f"Synced: {len(new_trades)}")
    print(f"Total trades: {len(trades) + len(new_trades)}")
    return 0


def cmd_evolution_variants(args: argparse.Namespace) -> int:
    from app.evolution import get_trading_variants

    variants = get_trading_variants()
    if not variants:
        print("No Trading evolution variants configured.")
        return 0
    print(f"{'Variant ID':12} {'Status':10} {'Name':28} Dimensions")
    for variant in variants:
        dimensions = variant.get("dimensions") if isinstance(variant.get("dimensions"), dict) else {}
        dim_text = ", ".join(f"{key}={value}" for key, value in sorted(dimensions.items()))
        print(
            f"{str(variant.get('variant_id', '-'))[:12]:12} "
            f"{str(variant.get('status', '-'))[:10]:10} "
            f"{str(variant.get('name', '-'))[:28]:28} "
            f"{dim_text}"
        )
    return 0


def cmd_evolution_status(args: argparse.Namespace) -> int:
    from app.evolution import get_trading_variants

    counts: dict[str, int] = {}
    variants = get_trading_variants()
    for variant in variants:
        status = str(variant.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    print("Trading evolution status")
    print(f"variants: {len(variants)}")
    for status in sorted(counts):
        print(f"{status}: {counts[status]}")
    print("last promotion: unavailable")
    print("manual promotion requires verified GREEN conservation from /api/conservation/status")
    return 0


def cmd_evolution_promote(args: argparse.Namespace) -> int:
    from app.evolution import get_trading_variant

    variant = get_trading_variant(args.variant_id)
    if variant is None:
        print(f"Unknown Trading evolution variant: {args.variant_id}", file=sys.stderr)
        return 1
    print(f"Variant found: {variant['variant_id']} ({variant['name']})")
    print(
        "Promotion blocked: offline CLI cannot verify GREEN conservation from "
        "/api/conservation/status, and no backend promotion endpoint is available.",
        file=sys.stderr,
    )
    return 1


def _sdk_missing_args(*names: str) -> int:
    print(
        json.dumps(
            {
                "error": f"Missing required SDK argument(s): {', '.join(names)}",
                "hint": "Use --category and --factors for SDK-backed scoring commands.",
            },
            indent=2,
        )
    )
    return 1


def cmd_init_dispatch(args: argparse.Namespace) -> int:
    if getattr(args, "db_path", None):
        return _sdk_cmd_init(args)
    return cmd_init(args)


def cmd_score_dispatch(args: argparse.Namespace) -> int:
    sdk_requested = any(
        getattr(args, name, None)
        for name in ("db_path", "category", "factors")
    )
    if not sdk_requested:
        return cmd_score(args)
    missing = [name for name in ("category", "factors") if not getattr(args, name, None)]
    if missing:
        return _sdk_missing_args(*missing)
    return _sdk_cmd_score(args)


def cmd_trust_dispatch(args: argparse.Namespace) -> int:
    if getattr(args, "db_path", None) or getattr(args, "category", None) or getattr(args, "format", None):
        return _sdk_cmd_trust(args)
    return cmd_trust(args)


def cmd_conservation_dispatch(args: argparse.Namespace) -> int:
    if getattr(args, "db_path", None):
        return _sdk_cmd_conservation(args)
    return cmd_conservation(args)


def cmd_journal_dispatch(args: argparse.Namespace) -> int:
    if getattr(args, "db_path", None) or getattr(args, "format", None):
        return _sdk_cmd_journal(args)
    return cmd_journal(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ci-trading")
    parser.add_argument("--config-dir", default=DEFAULT_CONFIG_DIR)

    subparsers = parser.add_subparsers(dest="command")
    add_sdk_subcommands(subparsers)

    init_parser = subparsers.add_parser("init", help="Initialize local Trading CLI storage.")
    init_parser.add_argument("--db-path")
    init_parser.set_defaults(func=cmd_init_dispatch)

    config_parser = subparsers.add_parser("config", help="Show or update local Trading CLI config.")
    config_parser.add_argument("--disable-pattern-detection", action="store_true")
    config_parser.add_argument("--enable-pattern-detection", action="store_true")
    config_parser.set_defaults(func=cmd_config)

    import_parser = subparsers.add_parser("import", help="Import trades from CSV.")
    import_parser.add_argument("--file")
    import_parser.add_argument("--broker", choices=["csv", "ibkr"], default="csv")
    import_parser.add_argument("--preset", choices=["thinkorswim", "webull", "robinhood"])
    import_parser.add_argument("--days", type=int, default=365)
    import_parser.set_defaults(func=cmd_import)

    score_parser = subparsers.add_parser("score", help="Compute offline factor scores.")
    score_parser.add_argument("--trade-id")
    score_parser.add_argument("--category")
    score_parser.add_argument("--factors")
    score_parser.add_argument("--db-path")
    score_parser.set_defaults(func=cmd_score_dispatch)

    decide_parser = subparsers.add_parser("decide", help="Persist an SDK scorer decision.")
    decide_parser.add_argument("--category", required=True)
    decide_parser.add_argument("--factors", required=True)
    decide_parser.add_argument("--db-path")
    decide_parser.set_defaults(func=_sdk_cmd_decide)

    learn_parser = subparsers.add_parser("learn", help="Record an SDK outcome for a decision.")
    learn_parser.add_argument("--decision", required=True)
    learn_parser.add_argument("--action", required=True)
    learn_parser.add_argument("--db-path")
    learn_parser.set_defaults(func=_sdk_cmd_learn)

    record_parser = subparsers.add_parser("record", help="Persist an SDK decision and outcome.")
    record_parser.add_argument("--category", required=True)
    record_parser.add_argument("--factors", required=True)
    record_parser.add_argument("--action", required=True)
    record_parser.add_argument("--db-path")
    record_parser.set_defaults(func=_sdk_cmd_record)

    trust_parser = subparsers.add_parser("trust", help="Summarize factor computer coverage.")
    trust_parser.add_argument("--category")
    trust_parser.add_argument("--db-path")
    trust_parser.add_argument("--format", choices=["json", "human"])
    trust_parser.set_defaults(func=cmd_trust_dispatch)

    conservation_parser = subparsers.add_parser(
        "conservation",
        help="Show an offline conservation proxy.",
    )
    conservation_parser.add_argument("--db-path")
    conservation_parser.set_defaults(func=cmd_conservation_dispatch)

    status_parser = subparsers.add_parser("status", help="Show SDK-backed Trading status.")
    status_parser.add_argument("--db-path")
    status_parser.add_argument("--format", choices=["json", "human"], default="json")
    status_parser.set_defaults(func=_sdk_cmd_status)

    journal_parser = subparsers.add_parser("journal", help="Show local imported trade journal.")
    journal_parser.add_argument("--ticker")
    journal_parser.add_argument("--category")
    journal_parser.add_argument("--strategy")
    journal_parser.add_argument("--wins-only", action="store_true")
    journal_parser.add_argument("--losses-only", action="store_true")
    journal_parser.add_argument("--limit", type=int, default=20)
    journal_parser.add_argument("--db-path")
    journal_parser.add_argument("--format", choices=["json", "human"])
    journal_parser.set_defaults(func=cmd_journal_dispatch)

    regime_parser = subparsers.add_parser("regime", help="Show current market regime and local regime accuracy.")
    regime_parser.add_argument("--detail", action="store_true")
    regime_parser.set_defaults(func=cmd_regime)

    correlation_parser = subparsers.add_parser("correlation", help="Monitor cross-position correlation concentration.")
    correlation_parser.add_argument("--window", type=int, default=20)
    correlation_parser.set_defaults(func=cmd_correlation)

    vix_timing_parser = subparsers.add_parser("vix-timing", help="Analyze hold periods across VIX conditions.")
    vix_timing_parser.set_defaults(func=cmd_vix_timing)

    promote_parser = subparsers.add_parser("promote", help="Show or evaluate strategy promotion tiers.")
    promote_parser.add_argument("--evaluate", action="store_true")
    promote_parser.set_defaults(func=cmd_promote)

    export_parser = subparsers.add_parser("export", help="Export local trades.")
    export_parser.add_argument("--format", choices=["json", "csv"], default="json")
    export_parser.add_argument("--output")
    export_parser.set_defaults(func=cmd_export)

    backup_parser = subparsers.add_parser("backup", help="Back up local CLI state.")
    backup_parser.set_defaults(func=cmd_backup)

    restore_parser = subparsers.add_parser("restore", help="Restore local CLI state from backup.")
    restore_parser.add_argument("--from", dest="from_file", required=True)
    restore_parser.set_defaults(func=cmd_restore)

    retag_parser = subparsers.add_parser("retag", help="Update a trade category.")
    retag_parser.add_argument("--trade-id", required=True)
    retag_parser.add_argument("--category", required=True)
    retag_parser.set_defaults(func=cmd_retag)

    order_parser = subparsers.add_parser("order", help="Place a broker order.")
    order_parser.add_argument("ticker")
    order_parser.add_argument("side", choices=["buy", "sell"])
    order_parser.add_argument("qty", type=float)
    order_parser.add_argument("--type", choices=["market", "limit"], default="market")
    order_parser.add_argument("--limit-price", type=float)
    order_parser.add_argument("--broker", choices=["alpaca", "mock"], default="alpaca")
    order_parser.set_defaults(func=cmd_order)

    orders_parser = subparsers.add_parser("orders", help="List broker orders.")
    orders_parser.add_argument("--status", choices=["filled", "pending", "all"], default="all")
    orders_parser.add_argument("--limit", type=int, default=50)
    orders_parser.add_argument("--broker", choices=["alpaca", "mock"], default="alpaca")
    orders_parser.set_defaults(func=cmd_orders)

    positions_parser = subparsers.add_parser("positions", help="List broker positions.")
    positions_parser.add_argument("--broker", choices=["alpaca", "mock"], default="alpaca")
    positions_parser.set_defaults(func=cmd_positions)

    account_parser = subparsers.add_parser("account", help="Show broker account summary.")
    account_parser.add_argument("--broker", choices=["alpaca", "mock"], default="alpaca")
    account_parser.set_defaults(func=cmd_account)

    sync_parser = subparsers.add_parser("sync", help="Sync filled broker orders to the local journal.")
    sync_parser.add_argument("--dry-run", action="store_true")
    sync_parser.add_argument("--limit", type=int, default=50)
    sync_parser.add_argument("--broker", choices=["alpaca", "mock"], default="alpaca")
    sync_parser.set_defaults(func=cmd_sync)

    evolution_parser = subparsers.add_parser("evolution", help="Inspect Trading evolution variants.")
    evolution_subparsers = evolution_parser.add_subparsers(dest="evolution_command")

    evolution_variants = evolution_subparsers.add_parser("variants", help="List Trading evolution variants.")
    evolution_variants.set_defaults(func=cmd_evolution_variants)

    evolution_status = evolution_subparsers.add_parser("status", help="Summarize Trading evolution status.")
    evolution_status.set_defaults(func=cmd_evolution_status)

    evolution_promote = evolution_subparsers.add_parser("promote", help="Validate a Trading variant promotion request.")
    evolution_promote.add_argument("variant_id")
    evolution_promote.set_defaults(func=cmd_evolution_promote)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        if code != 0:
            print(json.dumps({"error": "Invalid arguments", "hint": "Run 'ci-trading --help'"}))
        raise
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
