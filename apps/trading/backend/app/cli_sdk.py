"""SDK-backed Trading CLI commands.

This module is intentionally separate from the existing JSON-backed offline
CLI. The public command functions return Python objects for fast tests; the
argparse hook at the bottom serializes those objects for CLI use.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer, ScoreResult


DOMAIN = "trading"
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
    return CompoundingScorer.from_preset(DOMAIN, db_path=path)


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
        stored = scorer.graph_store.get_decision(decision)
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


def _add_db_path(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db-path")


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
    parser = argparse.ArgumentParser(prog="ci-trading-sdk")
    subparsers = parser.add_subparsers(dest="command")
    add_sdk_subcommands(subparsers)
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
    "conservation_sdk",
    "decide_sdk",
    "init_sdk",
    "journal_sdk",
    "learn_sdk",
    "parse_factors",
    "record_sdk",
    "score_sdk",
    "status_sdk",
    "trust_sdk",
]
