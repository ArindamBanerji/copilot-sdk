"""SDK-backed Trading CLI commands.

This module is intentionally separate from the existing JSON-backed offline
CLI. The public command functions return Python objects for fast tests; the
argparse hook at the bottom serializes those objects for CLI use.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from copilot_sdk.config import GraphConfig
from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer, ScoreResult


DOMAIN = "trading"


def _cli_profile() -> str:
    if os.environ.get("PYTEST_CURRENT_TEST") or "pytest" in sys.modules:
        return "test"
    age_keys = (
        "TRADING_ACTIVE_AGE_DSN",
        "GRAPH_DSN",
        "AGE_DSN",
    )
    return "production" if any(os.environ.get(key, "").strip() for key in age_keys) else "development"


def _age_configured() -> bool:
    backend = os.environ.get("TRADING_ACTIVE_GRAPH_BACKEND", "").strip().lower()
    dsn_configured = any(
        os.environ.get(key, "").strip()
        for key in ("TRADING_ACTIVE_AGE_DSN", "GRAPH_DSN", "AGE_DSN")
    )
    return backend in {"age", "dual_write"} or dsn_configured


def _load_cli_graph_config(profile: str) -> GraphConfig:
    """Load typed graph configuration, allowing local CLI SQLite development."""
    if _age_configured():
        return GraphConfig.load(DOMAIN, profile=profile)

    previous_backend = os.environ.get("TRADING_ACTIVE_GRAPH_BACKEND")
    previous_fallback = os.environ.get("CI_ALLOW_SQLITE_FALLBACK")
    os.environ["TRADING_ACTIVE_GRAPH_BACKEND"] = "sqlite"
    os.environ["CI_ALLOW_SQLITE_FALLBACK"] = "1"
    try:
        return GraphConfig.load(DOMAIN, profile="development")
    finally:
        if previous_backend is None:
            os.environ.pop("TRADING_ACTIVE_GRAPH_BACKEND", None)
        else:
            os.environ["TRADING_ACTIVE_GRAPH_BACKEND"] = previous_backend
        if previous_fallback is None:
            os.environ.pop("CI_ALLOW_SQLITE_FALLBACK", None)
        else:
            os.environ["CI_ALLOW_SQLITE_FALLBACK"] = previous_fallback
DEFAULT_DB_PATH = os.path.expanduser("~/.ci-platform/trading/trading.db")
SELF_CONFIRM_WARNING = (
    "Recorded action matches system recommendation. If this is the "
    "recommendation echoed back (not a verified real-world outcome), use "
    "'ci-trading score' instead."
)


class CLIUsageError(ValueError):
    """User-facing CLI validation error with a structured hint."""

    def __init__(self, error: str, hint: str):
        super().__init__(error)
        self.error = error
        self.hint = hint

    def to_payload(self) -> dict[str, str]:
        return {"error": self.error, "hint": self.hint}


def _preset() -> TradingPreset:
    return TradingPreset()


def _shape():
    return _preset().shape


def _valid_categories() -> list[str]:
    return list(_shape().category_names)


def _valid_actions() -> list[str]:
    return list(_shape().action_names)


def _valid_factors() -> list[str]:
    return list(_shape().factor_names)


def _format_hint(values: list[str]) -> str:
    return ", ".join(values)


def _db_path(db_path: str | None = None) -> str:
    return os.path.expanduser(db_path or DEFAULT_DB_PATH)


def _get_scorer(db_path: str | None = None) -> CompoundingScorer:
    path = _db_path(db_path)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    profile = _cli_profile()
    config = _load_cli_graph_config(profile)
    store = create_graph_store(
        backend=config.backend,
        domain=config.domain,
        db_path=path,
        dsn=config.dsn,
        graph_name=config.graph,
        env={},
        test_mode=config.active_test_mode,
        shared_graph_authorization=config.authorized,
        profile=profile,
    )
    return CompoundingScorer.from_preset(
        DOMAIN, db_path=path, graph_store=store, profile=profile
    )


def _close_scorer(scorer: CompoundingScorer) -> None:
    close = getattr(scorer.graph_store, "close", None)
    if callable(close):
        close()


def _validate_category(category: str) -> None:
    valid = _valid_categories()
    if category not in valid:
        raise CLIUsageError(
            f"Unknown category '{category}'",
            f"Valid categories: {_format_hint(valid)}",
        )


def _validate_action(action: str) -> None:
    valid = _valid_actions()
    if action not in valid:
        raise CLIUsageError(
            f"Unknown action '{action}'",
            f"Valid actions: {_format_hint(valid)}",
        )


def parse_factors(value: str | dict[str, Any]) -> dict[str, float]:
    """Parse and validate a factor JSON object."""
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise CLIUsageError(
                "Invalid JSON in --factors",
                'Expected format: {"signal_alignment": 0.8, ...}',
            ) from exc
    else:
        parsed = value

    if not isinstance(parsed, dict):
        raise CLIUsageError(
            "Invalid JSON in --factors",
            'Expected format: {"signal_alignment": 0.8, ...}',
        )

    valid = _valid_factors()
    valid_set = set(valid)
    result: dict[str, float] = {}
    for name, raw in parsed.items():
        if name not in valid_set:
            raise CLIUsageError(
                f"Unknown factor '{name}'",
                f"Valid factors: {_format_hint(valid)}",
            )
        try:
            numeric = float(raw)
        except (TypeError, ValueError) as exc:
            raise CLIUsageError(
                f"Factor '{name}' value is not numeric",
                "Factor values must be between 0.0 and 1.0",
            ) from exc
        if not math.isfinite(numeric):
            raise CLIUsageError(
                f"Factor '{name}' value is not finite",
                "Factor values must be finite numbers between 0.0 and 1.0",
            )
        if numeric < 0.0 or numeric > 1.0:
            raise CLIUsageError(
                f"Factor '{name}' value {numeric:g} out of range",
                "Factor values must be between 0.0 and 1.0",
            )
        result[name] = numeric

    return result


def _validate_factors(factors: dict[str, Any]) -> dict[str, float]:
    parsed = parse_factors(factors)
    valid = _valid_factors()
    missing = [name for name in valid if name not in parsed]
    if missing:
        raise CLIUsageError(
            f"Missing factors: {_format_hint(missing)}",
            f"Expected all factors: {_format_hint(valid)}",
        )
    return {name: parsed[name] for name in valid}


def _score_payload(result: ScoreResult, persisted: bool) -> dict[str, Any]:
    actions = _valid_actions()
    probabilities = {
        action: float(probability)
        for action, probability in zip(actions, result.probabilities)
    }
    payload: dict[str, Any] = {
        "action": result.action,
        "confidence": float(result.confidence),
        "probabilities": probabilities,
        "persisted": persisted,
    }
    if persisted:
        payload["decision_id"] = result.decision_id
    return payload


def init_sdk(db_path: str | None = None) -> dict[str, Any]:
    """Initialize the SDK-backed Trading database."""
    path = _db_path(db_path)
    existed = Path(path).exists()
    scorer = _get_scorer(path)
    try:
        shape = TradingPreset().shape
        return {
            "db_path": path,
            "created": not existed,
            "categories": list(shape.category_names),
            "actions": list(shape.action_names),
            "factors": list(shape.factor_names),
        }
    finally:
        _close_scorer(scorer)


def score_sdk(category: str, factors: str | dict[str, Any], db_path: str | None = None) -> dict[str, Any]:
    """Preview a recommendation without persisting a Decision."""
    _validate_category(category)
    clean_factors = _validate_factors(parse_factors(factors))
    scorer = _get_scorer(db_path)
    try:
        result = scorer.score_read_only(clean_factors, category)
        return _score_payload(result, persisted=False)
    finally:
        _close_scorer(scorer)


def decide_sdk(category: str, factors: str | dict[str, Any], db_path: str | None = None) -> dict[str, Any]:
    """Persist a Decision without recording an Outcome."""
    _validate_category(category)
    clean_factors = _validate_factors(parse_factors(factors))
    scorer = _get_scorer(db_path)
    try:
        result = scorer.score(clean_factors, category)
        payload = _score_payload(result, persisted=True)
        return {
            "decision_id": payload["decision_id"],
            "action": payload["action"],
            "confidence": payload["confidence"],
            "persisted": True,
        }
    finally:
        _close_scorer(scorer)


def _conservation_pause_payload(decision_id: str, action: str) -> dict[str, Any]:
    return {
        "decision_id": decision_id,
        "actual_action": action,
        "outcome_recorded": False,
        "reason": "conservation_paused",
        "hint": (
            f"Re-run 'ci-trading learn --decision {decision_id} --action {action}' "
            "after conservation resumes."
        ),
    }


# NOTE: CLI learn/record does not persist L5 conservation/DK snapshots.
# Backend scoring_router.py:143-169 does this after learn().
# CLI conservation state re-derives from decisions on next scorer construction.
# See P61 for shared L5 helper extraction.
def learn_sdk(decision: str, action: str, db_path: str | None = None) -> dict[str, Any]:
    """Record an Outcome for an existing Decision."""
    _validate_action(action)
    scorer = _get_scorer(db_path)
    try:
        stored = scorer.graph_store.get_decision(decision, domain="trading")
        if stored is None:
            raise CLIUsageError(
                f"Decision '{decision}' not found",
                "Run 'ci-trading decide' or check the decision ID.",
            )
        recommended = str(stored.get("recommended_action") or stored.get("action") or "")
        result = scorer.learn(decision, action)
        is_correct = action == recommended
        if isinstance(result, dict):
            payload = _conservation_pause_payload(decision, action)
            payload["is_correct"] = is_correct
            payload["conservation_impact"] = (
                result.get("reason") or result.get("status") or "paused"
            )
            return payload
        else:
            conservation_impact = result.outcome
        return {
            "decision_id": decision,
            "actual_action": action,
            "is_correct": is_correct,
            "outcome_recorded": True,
            "conservation_impact": conservation_impact,
        }
    finally:
        _close_scorer(scorer)


def record_sdk(category: str, factors: str | dict[str, Any], action: str, db_path: str | None = None) -> dict[str, Any]:
    """Persist a Decision and immediately record the verified Outcome."""
    _validate_category(category)
    _validate_action(action)
    clean_factors = _validate_factors(parse_factors(factors))
    scorer = _get_scorer(db_path)
    try:
        score_result = scorer.score(clean_factors, category)
        learn_result = scorer.learn(score_result.decision_id, action)
        is_correct = action == score_result.action
        if isinstance(learn_result, dict):
            payload = _conservation_pause_payload(score_result.decision_id, action)
            payload.update(
                {
                    "recommended": score_result.action,
                    "actual": action,
                    "is_correct": is_correct,
                    "warning": SELF_CONFIRM_WARNING if is_correct else None,
                    "conservation_impact": (
                        learn_result.get("reason")
                        or learn_result.get("status")
                        or "paused"
                    ),
                }
            )
            return payload
        else:
            conservation_impact = learn_result.outcome
        return {
            "decision_id": score_result.decision_id,
            "recommended": score_result.action,
            "actual": action,
            "is_correct": is_correct,
            "outcome_recorded": True,
            "conservation_impact": conservation_impact,
            "warning": SELF_CONFIRM_WARNING if is_correct else None,
        }
    finally:
        _close_scorer(scorer)


def _counts(scorer: CompoundingScorer) -> dict[str, int]:
    store = scorer.graph_store
    return {
        "total_decisions": int(store.count_decisions(DOMAIN)),
        "verified_count": int(store.count_verified(DOMAIN)),
        "correct_count": int(store.count_correct(DOMAIN)),
    }


def trust_sdk(
    category: str | None = None,
    db_path: str | None = None,
    output_format: str = "json",
) -> dict[str, Any] | str:
    """Return DK weights and fingerprint summary."""
    if category is not None:
        _validate_category(category)
    scorer = _get_scorer(db_path)
    try:
        counts = _counts(scorer)
        if counts["total_decisions"] < 200:
            payload = {
                "status": "learning",
                "decisions_needed": 200 - counts["total_decisions"],
                "message": "DK weights emerge after 200 decisions",
            }
            return _human_trust(payload) if output_format == "human" else payload

        weights = scorer.get_dk_weights()
        if weights is None:
            fingerprint = scorer.fingerprint()
            per_factor = {f.name: f.weight for f in fingerprint.factors}
            cats = [category] if category else _valid_categories()
            payload = {
                "status": "fingerprint",
                "categories": [
                    _trust_category_payload(cat, per_factor)
                    for cat in cats
                ],
            }
            return _human_trust(payload) if output_format == "human" else payload

        categories = _valid_categories()
        factors = _valid_factors()
        selected_categories = [category] if category else categories
        payload = {
            "status": "active",
            "categories": [
                _trust_category_payload(
                    cat,
                    {
                        factor: float(weights[categories.index(cat)][i])
                        for i, factor in enumerate(factors)
                    },
                )
                for cat in selected_categories
            ],
        }
        return _human_trust(payload) if output_format == "human" else payload
    finally:
        _close_scorer(scorer)


def _trust_category_payload(category: str, weights: dict[str, float]) -> dict[str, Any]:
    top_signal = max(weights, key=weights.get) if weights else None
    return {
        "category": category,
        "weights": {name: round(float(value), 4) for name, value in weights.items()},
        "noise_signals": [name for name, value in weights.items() if float(value) < 0.30],
        "top_signal": top_signal,
    }


def conservation_sdk(db_path: str | None = None) -> dict[str, Any]:
    """Return current conservation status."""
    scorer = _get_scorer(db_path)
    try:
        counts = _counts(scorer)
        state = scorer.graph_store.get_conservation_state(DOMAIN)
        phase = scorer.get_phase()
        alpha = scorer.get_alpha()
        theta_min = state.get("theta_min") if isinstance(state, dict) else None
        headroom = state.get("headroom") if isinstance(state, dict) else None
        status = state.get("status") if isinstance(state, dict) else None
        if not status:
            status = "BOOTSTRAP" if counts["verified_count"] == 0 else "GREEN"
        return {
            "phase": phase,
            "alpha": alpha,
            "verified_count": counts["verified_count"],
            "status": status,
            "theta_min": theta_min,
            "headroom": headroom,
        }
    finally:
        _close_scorer(scorer)


def status_sdk(db_path: str | None = None, output_format: str = "json") -> dict[str, Any] | str:
    """Return a one-screen Trading copilot summary."""
    path = _db_path(db_path)
    scorer = _get_scorer(path)
    try:
        counts = _counts(scorer)
        alpha = scorer.get_alpha()
        phase = scorer.get_phase()
        conservation = conservation_sdk(path)
        decisions = scorer.graph_store.get_decisions(DOMAIN, limit=10000)
        last_decision = decisions[-1]["decision_id"] if decisions else None
        trust = trust_sdk(db_path=path)
        top_factors: dict[str, float] = {}
        noise_factors: list[str] = []
        if isinstance(trust, dict) and trust.get("categories"):
            first = trust["categories"][0]
            weights = first.get("weights", {})
            top_factors = dict(sorted(weights.items(), key=lambda item: item[1], reverse=True)[:3])
            noise_factors = list(first.get("noise_signals", []))
        db_size_mb = round(Path(path).stat().st_size / (1024 * 1024), 3) if Path(path).exists() else 0.0
        payload = {
            "phase": phase,
            "alpha": alpha,
            "conservation": conservation["status"],
            "total_decisions": counts["total_decisions"],
            "verified_count": counts["verified_count"],
            "accuracy": alpha,
            "last_decision": last_decision,
            "top_factors": top_factors,
            "noise_factors": noise_factors,
            "db_path": path,
            "db_size_mb": db_size_mb,
        }
        return _human_status(payload) if output_format == "human" else payload
    finally:
        _close_scorer(scorer)


def journal_sdk(
    limit: int = 20,
    db_path: str | None = None,
    output_format: str = "json",
) -> list[dict[str, Any]] | str:
    """Return recent SDK decisions."""
    scorer = _get_scorer(db_path)
    try:
        user_limit = max(int(limit), 0)
        all_decisions = scorer.graph_store.get_decisions(DOMAIN, limit=10000)
        decisions = all_decisions[-user_limit:] if user_limit else []
        verified = {
            row["decision_id"]: row
            for row in scorer.graph_store.get_verified_decisions(DOMAIN)
        }
        rows: list[dict[str, Any]] = []
        for decision in reversed(decisions):
            outcome = verified.get(decision["decision_id"])
            rows.append(
                {
                    "decision_id": decision["decision_id"],
                    "category": decision["category"],
                    "action": decision["recommended_action"],
                    "timestamp": _format_timestamp(decision.get("created_at")),
                    "verified": outcome is not None,
                    "is_correct": bool(outcome.get("is_correct")) if outcome else False,
                }
            )
        return _human_journal(rows, limit) if output_format == "human" else rows
    finally:
        _close_scorer(scorer)


def export_sdk(
    format: str = "json",
    output_path: str | None = None,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Export all SDK decisions to JSON or CSV."""
    export_format = format.lower().strip()
    if export_format not in {"json", "csv"}:
        raise CLIUsageError("Unknown export format", "Valid formats: json, csv")

    path = _db_path(db_path)
    out_path = Path(output_path) if output_path else Path(path).parent / f"decisions.{export_format}"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    scorer = _get_scorer(db_path)
    try:
        decisions = scorer.graph_store.get_decisions(DOMAIN, limit=10000)
        verified = {
            row["decision_id"]: row
            for row in scorer.graph_store.get_verified_decisions(DOMAIN)
        }
        rows = [_export_row(decision, verified.get(decision["decision_id"])) for decision in decisions]
    finally:
        _close_scorer(scorer)

    if export_format == "json":
        out_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    else:
        fieldnames = _csv_fieldnames(rows)
        with out_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({name: _csv_value(row.get(name)) for name in fieldnames})

    return {"exported": len(rows), "format": export_format, "path": str(out_path)}


def backup_sdk(backup_path: str | None = None, db_path: str | None = None) -> dict[str, Any]:
    """Copy the SDK Trading DB to a backup file."""
    src = _db_path(db_path)
    scorer = _get_scorer(db_path)
    _close_scorer(scorer)

    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_dir = Path(src).parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = str(backup_dir / f"trading_{timestamp}.db")
    else:
        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src, backup_path)
    return {"backed_up": src, "backup_path": str(backup_path)}


def restore_sdk(
    backup_path: str,
    confirm: bool = False,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Restore the SDK Trading DB from a validated SQLite backup."""
    if not confirm:
        return {"error": "Restore is destructive. Use --confirm."}

    if not backup_path or not Path(backup_path).exists():
        return {"error": "Backup file not found"}

    conn = sqlite3.connect(backup_path)
    try:
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
    except sqlite3.DatabaseError:
        return {"error": "Invalid backup file"}
    finally:
        conn.close()

    if _load_cli_graph_config(_cli_profile()).backend != "sqlite":
        return {"error": "SQLite restore is unavailable for AGE-backed Trading"}

    dest = _db_path(db_path)
    parent = os.path.dirname(dest)
    if parent:
        os.makedirs(parent, exist_ok=True)
    shutil.copy2(backup_path, dest)
    return {"restored_from": str(backup_path), "restored_to": dest}


def import_sdk(
    source: str = "csv",
    file_path: str | None = None,
    broker: str | None = None,
    preset: str | None = None,
    days: int = 365,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Import CSV or broker trades as SDK decisions with trade metadata."""
    source_name = source.lower().strip()
    if source_name == "csv":
        if not file_path:
            return {"error": "Specify --file for CSV import"}
        trades = _load_csv_trades(file_path, preset)
    elif source_name == "broker":
        if not broker:
            return {"error": "Specify --broker for broker import"}
        trades = _load_broker_trades(broker, days)
    else:
        return {"error": "Unknown import source", "valid_sources": ["csv", "broker"]}

    scorer = _get_scorer(db_path)
    imported = 0
    skipped = 0
    try:
        existing_keys = _existing_import_keys(scorer.graph_store.get_decisions(DOMAIN, limit=10000))
        factors = {name: 0.5 for name in _valid_factors()}
        categories = _valid_categories()
        default_category = categories[0]
        for trade in trades:
            trade_data = _trade_to_dict(trade)
            trade_key = _trade_key(trade_data)
            if trade_key in existing_keys:
                skipped += 1
                continue
            category = str(trade_data.get("category") or trade_data.get("strategy_tag") or default_category)
            if category not in categories:
                category = default_category
            scorer.score(
                factors,
                category,
                metadata={
                    "source": f"import:{source_name}",
                    "import_key": trade_key,
                    "trade": trade_data,
                    "entity_id": str(trade_data.get("trade_id") or trade_key),
                },
            )
            existing_keys.add(trade_key)
            imported += 1
    finally:
        _close_scorer(scorer)

    return {"imported": imported, "skipped": skipped, "errors": 0}


def _export_row(decision: dict[str, Any], outcome: dict[str, Any] | None) -> dict[str, Any]:
    row = {
        "decision_id": decision.get("decision_id"),
        "category": decision.get("category"),
        "recommended": decision.get("recommended_action"),
        "actual": outcome.get("actual_action") if outcome else None,
        "is_correct": outcome.get("is_correct") if outcome else None,
        "confidence": decision.get("confidence"),
        "created_at": decision.get("created_at"),
    }
    factors = decision.get("factors") or {}
    if isinstance(factors, dict):
        for name in _valid_factors():
            row[f"factor_{name}"] = factors.get(name)
    return row


def _csv_fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    base = ["decision_id", "category", "recommended", "actual", "is_correct", "confidence", "created_at"]
    factor_names = [f"factor_{name}" for name in _valid_factors()]
    extras = sorted({key for row in rows for key in row if key not in base and key not in factor_names})
    return base + factor_names + extras


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return value


def _load_csv_trades(file_path: str, preset: str | None) -> list[Any]:
    from app.connectors.csv_connector import BROKER_PRESETS, CSVConnector

    if not Path(file_path).is_file():
        raise CLIUsageError(
            f"CSV file not found: {file_path}",
            "Provide a valid file path with --file",
        )
    if preset and preset.lower() not in BROKER_PRESETS:
        raise CLIUsageError(
            f"Unknown CSV preset '{preset}'",
            f"Valid presets: {_format_hint(sorted(BROKER_PRESETS))}",
        )
    connector = CSVConnector()
    return connector.import_flexible(file_path, broker_preset=preset) if preset else connector.import_from_file(file_path)


def _load_broker_trades(broker: str, days: int) -> list[Any]:
    from app.brokers import get_broker

    try:
        days_int = int(days)
    except (TypeError, ValueError) as exc:
        raise CLIUsageError("Invalid days parameter", "Days must be an integer.") from exc
    try:
        connector = get_broker(broker)
    except (ValueError, KeyError, ImportError) as exc:
        raise CLIUsageError(
            f"Unknown or unavailable broker: {broker}",
            "Valid brokers: mock, alpaca, ibkr",
        ) from exc
    import_trades = getattr(connector, "import_trades", None)
    if import_trades is None:
        raise CLIUsageError(
            f"Broker '{broker}' does not support trade import",
            "Use a broker connector with import_trades(), such as ibkr.",
        )
    return import_trades(days=days_int)


def _trade_to_dict(trade: Any) -> dict[str, Any]:
    if hasattr(trade, "to_dict"):
        return trade.to_dict()
    if isinstance(trade, dict):
        return dict(trade)
    return dict(getattr(trade, "__dict__", {}))


def _existing_import_keys(decisions: list[dict[str, Any]]) -> set[str]:
    keys: set[str] = set()
    for decision in decisions:
        metadata = decision.get("metadata") or {}
        if isinstance(metadata, dict) and metadata.get("import_key"):
            keys.add(str(metadata["import_key"]))
    return keys


def _trade_key(trade: dict[str, Any]) -> str:
    ticker = str(trade.get("ticker") or trade.get("symbol") or "").upper()
    raw_date = trade.get("entry_time") or trade.get("entry_date") or trade.get("date") or trade.get("timestamp") or ""
    date = raw_date.isoformat() if hasattr(raw_date, "isoformat") else str(raw_date)
    size = trade.get("size", trade.get("qty", trade.get("quantity", 0)))
    try:
        normalized_size = abs(float(size or 0))
    except (TypeError, ValueError):
        normalized_size = 0.0
    direction = str(trade.get("direction") or trade.get("side") or "unknown").lower()
    return "|".join([ticker, date[:19], f"{normalized_size:g}", direction])


def _format_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(value)))
    except (TypeError, ValueError, OSError):
        return str(value)


def _human_trust(payload: dict[str, Any]) -> str:
    if payload.get("status") == "learning":
        return f"{payload['message']} ({payload['decisions_needed']} decisions needed)"
    lines = ["Factor                   Weight  Bar", "-------------------------------------"]
    categories = payload.get("categories") or []
    if not categories:
        return "\n".join(lines)
    first = categories[0]
    for name, weight in first.get("weights", {}).items():
        bar = "#" * int(round(float(weight) * 20))
        lines.append(f"{name:24} {float(weight):0.2f}   {bar}")
    noise = ", ".join(first.get("noise_signals", [])) or "none"
    lines.append(f"Noise (< 0.30): {noise}")
    return "\n".join(lines)


def _human_status(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Trading Copilot Status",
            "======================================",
            f"Phase:        {payload['phase']}",
            f"Alpha:        {payload['alpha']:0.2f}",
            f"Conservation: {payload['conservation']}",
            f"Decisions:    {payload['total_decisions']} total ({payload['verified_count']} verified)",
            f"Accuracy:     {payload['accuracy'] * 100:0.0f}%",
            f"DB:           {payload['db_path']}",
            "======================================",
        ]
    )


def _human_journal(rows: list[dict[str, Any]], limit: int) -> str:
    lines = [f"Recent Decisions (last {limit})", "------------------------------------------"]
    for row in rows:
        status = "correct" if row["is_correct"] else "incorrect"
        marker = "ok" if row["verified"] and row["is_correct"] else ("x" if row["verified"] else "-")
        lines.append(
            f"{row['timestamp'] or 'unknown':16}  {row['category']:16}  "
            f"{row['action']:18}  {marker} {status if row['verified'] else 'unverified'}"
        )
    return "\n".join(lines)


def _print_payload(payload: Any, output_format: str = "json") -> int:
    if output_format == "human" and isinstance(payload, str):
        print(payload)
    else:
        print(json.dumps(payload, indent=2))
    if isinstance(payload, dict) and "error" in payload:
        return 1
    return 0


def _run_json_command(func: Callable[[], Any], output_format: str = "json") -> int:
    try:
        return _print_payload(func(), output_format)
    except CLIUsageError as exc:
        print(json.dumps(exc.to_payload(), indent=2))
        return 1
    except KeyError as exc:
        print(
            json.dumps(
                {
                    "error": f"Trading DB lookup failed for {exc}",
                    "hint": "Run 'ci-trading sdk init' first or check the decision ID.",
                },
                indent=2,
            )
        )
        return 1


def _cmd_init(args: argparse.Namespace) -> int:
    return _run_json_command(lambda: init_sdk(args.db_path))


def _cmd_score(args: argparse.Namespace) -> int:
    return _run_json_command(lambda: score_sdk(args.category, args.factors, args.db_path))


def _cmd_decide(args: argparse.Namespace) -> int:
    return _run_json_command(lambda: decide_sdk(args.category, args.factors, args.db_path))


def _cmd_learn(args: argparse.Namespace) -> int:
    return _run_json_command(lambda: learn_sdk(args.decision, args.action, args.db_path))


def _cmd_record(args: argparse.Namespace) -> int:
    return _run_json_command(lambda: record_sdk(args.category, args.factors, args.action, args.db_path))


def _cmd_trust(args: argparse.Namespace) -> int:
    return _run_json_command(
        lambda: trust_sdk(args.category, args.db_path, args.format),
        args.format,
    )


def _cmd_conservation(args: argparse.Namespace) -> int:
    return _run_json_command(lambda: conservation_sdk(args.db_path))


def _cmd_status(args: argparse.Namespace) -> int:
    return _run_json_command(
        lambda: status_sdk(args.db_path, args.format),
        args.format,
    )


def _cmd_journal(args: argparse.Namespace) -> int:
    return _run_json_command(
        lambda: journal_sdk(args.limit, args.db_path, args.format),
        args.format,
    )


def _cmd_export(args: argparse.Namespace) -> int:
    return _run_json_command(lambda: export_sdk(args.format, args.output, args.db_path))


def _cmd_backup(args: argparse.Namespace) -> int:
    return _run_json_command(lambda: backup_sdk(args.backup_path, args.db_path))


def _cmd_restore(args: argparse.Namespace) -> int:
    return _run_json_command(lambda: restore_sdk(args.backup_path, args.confirm, args.db_path))


def _cmd_import(args: argparse.Namespace) -> int:
    return _run_json_command(
        lambda: import_sdk(
            source=args.source,
            file_path=args.file_path,
            broker=args.broker,
            preset=args.preset,
            days=args.days,
            db_path=args.db_path,
        )
    )


def _add_db_path(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db-path")


def _add_top_level_subcommands(subparsers: argparse._SubParsersAction) -> None:
    init_parser = subparsers.add_parser("init", help="Initialize SDK-backed Trading DB.")
    _add_db_path(init_parser)
    init_parser.set_defaults(func=_cmd_init)

    score_parser = subparsers.add_parser("score", help="Preview a scorer decision.")
    _add_db_path(score_parser)
    score_parser.add_argument("--category", required=True)
    score_parser.add_argument("--factors", required=True)
    score_parser.set_defaults(func=_cmd_score)

    decide_parser = subparsers.add_parser("decide", help="Persist a scorer decision.")
    _add_db_path(decide_parser)
    decide_parser.add_argument("--category", required=True)
    decide_parser.add_argument("--factors", required=True)
    decide_parser.set_defaults(func=_cmd_decide)

    learn_parser = subparsers.add_parser("learn", help="Record an outcome for a decision.")
    _add_db_path(learn_parser)
    learn_parser.add_argument("--decision", required=True)
    learn_parser.add_argument("--action", required=True)
    learn_parser.set_defaults(func=_cmd_learn)

    record_parser = subparsers.add_parser("record", help="Persist a decision and outcome.")
    _add_db_path(record_parser)
    record_parser.add_argument("--category", required=True)
    record_parser.add_argument("--factors", required=True)
    record_parser.add_argument("--action", required=True)
    record_parser.set_defaults(func=_cmd_record)

    trust_parser = subparsers.add_parser("trust", help="Show DK weights and trust fingerprint.")
    _add_db_path(trust_parser)
    trust_parser.add_argument("--category")
    trust_parser.add_argument("--format", choices=["json", "human"], default="json")
    trust_parser.set_defaults(func=_cmd_trust)

    conservation_parser = subparsers.add_parser("conservation", help="Show conservation status.")
    _add_db_path(conservation_parser)
    conservation_parser.set_defaults(func=_cmd_conservation)

    status_parser = subparsers.add_parser("status", help="Show SDK-backed Trading status.")
    _add_db_path(status_parser)
    status_parser.add_argument("--format", choices=["json", "human"], default="json")
    status_parser.set_defaults(func=_cmd_status)

    journal_parser = subparsers.add_parser("journal", help="Show recent SDK decisions.")
    _add_db_path(journal_parser)
    journal_parser.add_argument("--limit", type=int, default=20)
    journal_parser.add_argument("--format", choices=["json", "human"], default="json")
    journal_parser.set_defaults(func=_cmd_journal)

    export_parser = subparsers.add_parser("export", help="Export SDK decisions.")
    _add_db_path(export_parser)
    export_parser.add_argument("--format", choices=["json", "csv"], default="json")
    export_parser.add_argument("--output", dest="output")
    export_parser.set_defaults(func=_cmd_export)

    backup_parser = subparsers.add_parser("backup", help="Back up the SDK Trading DB.")
    _add_db_path(backup_parser)
    backup_parser.add_argument("--backup-path")
    backup_parser.set_defaults(func=_cmd_backup)

    restore_parser = subparsers.add_parser("restore", help="Restore the SDK Trading DB from backup.")
    _add_db_path(restore_parser)
    restore_parser.add_argument("--backup-path", required=True)
    restore_parser.add_argument("--confirm", action="store_true")
    restore_parser.set_defaults(func=_cmd_restore)

    import_parser = subparsers.add_parser("import", help="Import CSV or broker trades.")
    _add_db_path(import_parser)
    import_parser.add_argument("--source", choices=["csv", "broker"], default="csv")
    import_parser.add_argument("--file", dest="file_path")
    import_parser.add_argument("--broker")
    import_parser.add_argument("--preset")
    import_parser.add_argument("--days", type=int, default=365)
    import_parser.set_defaults(func=_cmd_import)


def add_sdk_subcommands(subparsers: argparse._SubParsersAction) -> None:
    """Attach SDK-backed commands under `ci-trading sdk ...`."""
    sdk_parser = subparsers.add_parser("sdk", help="SDK-backed Trading scorer commands.")
    sdk_subparsers = sdk_parser.add_subparsers(dest="sdk_command")

    init_parser = sdk_subparsers.add_parser("init", help="Initialize SDK-backed Trading DB.")
    _add_db_path(init_parser)
    init_parser.set_defaults(func=_cmd_init)

    score_parser = sdk_subparsers.add_parser("score", help="Preview a scorer decision.")
    _add_db_path(score_parser)
    score_parser.add_argument("--category", required=True)
    score_parser.add_argument("--factors", required=True)
    score_parser.set_defaults(func=_cmd_score)

    decide_parser = sdk_subparsers.add_parser("decide", help="Persist a scorer decision.")
    _add_db_path(decide_parser)
    decide_parser.add_argument("--category", required=True)
    decide_parser.add_argument("--factors", required=True)
    decide_parser.set_defaults(func=_cmd_decide)

    learn_parser = sdk_subparsers.add_parser("learn", help="Record an outcome for a decision.")
    _add_db_path(learn_parser)
    learn_parser.add_argument("--decision", required=True)
    learn_parser.add_argument("--action", required=True)
    learn_parser.set_defaults(func=_cmd_learn)

    record_parser = sdk_subparsers.add_parser("record", help="Persist a decision and outcome.")
    _add_db_path(record_parser)
    record_parser.add_argument("--category", required=True)
    record_parser.add_argument("--factors", required=True)
    record_parser.add_argument("--action", required=True)
    record_parser.set_defaults(func=_cmd_record)

    trust_parser = sdk_subparsers.add_parser("trust", help="Show DK weights and trust fingerprint.")
    _add_db_path(trust_parser)
    trust_parser.add_argument("--category")
    trust_parser.add_argument("--format", choices=["json", "human"], default="json")
    trust_parser.set_defaults(func=_cmd_trust)

    conservation_parser = sdk_subparsers.add_parser("conservation", help="Show conservation status.")
    _add_db_path(conservation_parser)
    conservation_parser.set_defaults(func=_cmd_conservation)

    status_parser = sdk_subparsers.add_parser("status", help="Show SDK-backed Trading status.")
    _add_db_path(status_parser)
    status_parser.add_argument("--format", choices=["json", "human"], default="json")
    status_parser.set_defaults(func=_cmd_status)

    journal_parser = sdk_subparsers.add_parser("journal", help="Show recent SDK decisions.")
    _add_db_path(journal_parser)
    journal_parser.add_argument("--limit", type=int, default=20)
    journal_parser.add_argument("--format", choices=["json", "human"], default="json")
    journal_parser.set_defaults(func=_cmd_journal)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci-trading",
        description="Compounding Intelligence - Trading Copilot CLI",
    )
    subparsers = parser.add_subparsers(dest="command")
    _add_top_level_subcommands(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return int(args.func(args))


__all__ = [
    "CLIUsageError",
    "DEFAULT_DB_PATH",
    "SELF_CONFIRM_WARNING",
    "_get_scorer",
    "add_sdk_subcommands",
    "backup_sdk",
    "conservation_sdk",
    "decide_sdk",
    "export_sdk",
    "import_sdk",
    "init_sdk",
    "journal_sdk",
    "learn_sdk",
    "parse_factors",
    "record_sdk",
    "restore_sdk",
    "score_sdk",
    "status_sdk",
    "trust_sdk",
]
