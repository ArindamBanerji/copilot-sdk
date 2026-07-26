"""Offline CLI for Purchasing Copilot."""

from __future__ import annotations

import json
import math
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click


BACKEND_ROOT = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from copilot_sdk.graph.sqlite_store import SQLiteGraphStore  # noqa: E402
from copilot_sdk.scoring import CompoundingScorer  # noqa: E402
from copilot_sdk.scoring.presets import PurchasingPreset  # noqa: E402
from gae.calibration import conservation_status  # noqa: E402


DOMAIN = "purchasing"


def _cli_profile() -> str:
    if "pytest" in sys.modules:
        return "test"
    return "development"
DEFAULT_DB_PATH = BACKEND_ROOT / "data" / "purchasing.db"
BACKUP_VERSION = 1

PRESET = PurchasingPreset()
SHAPE = PRESET.shape
CATEGORY_NAMES = tuple(SHAPE.category_names)
ACTION_NAMES = tuple(SHAPE.action_names)
FACTOR_NAMES = tuple(SHAPE.factor_names)


def _store(db_path: Path) -> SQLiteGraphStore:
    db_path = db_path.expanduser()
    if str(db_path) != ":memory:":
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return SQLiteGraphStore(str(db_path), domain=DOMAIN)


def _scorer(db_path: Path) -> CompoundingScorer:
    resolved = str(db_path.expanduser())
    store = SQLiteGraphStore(resolved, domain=DOMAIN)
    return CompoundingScorer.from_preset(
        DOMAIN, db_path=resolved, graph_store=store, profile=_cli_profile()
    )


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "tolist"):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _json_dump(value: Any) -> str:
    return json.dumps(_json_safe(value), default=_json_default, indent=2, sort_keys=True)


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def _parse_factors(factors_json: str | None, factor_items: tuple[str, ...]) -> dict[str, float]:
    if factors_json and factor_items:
        raise click.ClickException("Use either --factors JSON or repeated --factor name=value, not both.")
    if factors_json:
        try:
            raw = json.loads(factors_json)
        except json.JSONDecodeError as exc:
            raise click.ClickException(f"Invalid factors JSON: {exc.msg}") from exc
        if not isinstance(raw, dict):
            raise click.ClickException("--factors must be a JSON object.")
        factors = raw
    else:
        factors = {}
        for item in factor_items:
            if "=" not in item:
                raise click.ClickException("--factor values must use name=value.")
            name, value = item.split("=", 1)
            factors[name.strip()] = value.strip()

    expected = set(FACTOR_NAMES)
    provided = set(factors)
    missing = sorted(expected - provided)
    unknown = sorted(provided - expected)
    if missing or unknown:
        details = []
        if missing:
            details.append(f"missing factors: {', '.join(missing)}")
        if unknown:
            details.append(f"unknown factors: {', '.join(unknown)}")
        details.append(f"valid factors: {', '.join(FACTOR_NAMES)}")
        raise click.ClickException("; ".join(details))

    parsed: dict[str, float] = {}
    for name in FACTOR_NAMES:
        try:
            value = float(factors[name])
        except (TypeError, ValueError) as exc:
            raise click.ClickException(f"Factor {name} must be numeric.") from exc
        if not math.isfinite(value):
            raise click.ClickException(f"Factor {name} must be finite.")
        parsed[name] = value
    return parsed


def _validate_category(category: str) -> None:
    if category not in CATEGORY_NAMES:
        raise click.ClickException(
            f"Unknown category {category!r}. Valid categories: {', '.join(CATEGORY_NAMES)}"
        )


def _validate_action(action: str) -> None:
    if action not in ACTION_NAMES:
        raise click.ClickException(
            f"Unknown action {action!r}. Valid actions: {', '.join(ACTION_NAMES)}"
        )


def _shape_payload() -> dict[str, Any]:
    return {
        "n_categories": SHAPE.n_categories,
        "n_actions": SHAPE.n_actions,
        "n_factors": SHAPE.n_factors,
        "categories": list(CATEGORY_NAMES),
        "actions": list(ACTION_NAMES),
        "factors": list(FACTOR_NAMES),
    }


def _validate_backup_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise click.ClickException("Backup must be a JSON object.")
    if payload.get("domain") != DOMAIN:
        raise click.ClickException("Backup domain does not match purchasing.")
    shape = payload.get("shape")
    if shape != _shape_payload():
        raise click.ClickException("Backup shape does not match live Purchasing shape.")
    decisions = payload.get("decisions")
    verified = payload.get("verified_decisions", [])
    if not isinstance(decisions, list) or not isinstance(verified, list):
        raise click.ClickException("Backup decisions must be lists.")
    decision_ids: set[str] = set()
    for decision in decisions:
        decision_id = _validate_decision_payload(decision)
        if decision_id in decision_ids:
            raise click.ClickException(f"Duplicate decision_id in backup: {decision_id}")
        decision_ids.add(decision_id)
    for decision in verified:
        decision_id = _validate_decision_payload(decision)
        if decision_id not in decision_ids:
            raise click.ClickException(f"Verified decision references unknown decision_id: {decision_id}")
        action = str(decision.get("actual_action", ""))
        _validate_action(action)
        actual_index = _int_in_range(decision.get("actual_index", 0), "actual_index", len(ACTION_NAMES))
        if ACTION_NAMES[actual_index] != action:
            raise click.ClickException("Verified decision actual_index does not match actual_action.")
        if not isinstance(decision.get("is_correct"), bool):
            raise click.ClickException("Verified decision is_correct must be a boolean.")
        _finite_float(decision.get("verified_at"), "verified_at")
        context = decision.get("context", {})
        if context is not None and not isinstance(context, dict):
            raise click.ClickException("Verified decision context must be an object.")
    checkpoints = payload.get("centroid_checkpoints", [])
    if not isinstance(checkpoints, list):
        raise click.ClickException("Backup centroid_checkpoints must be a list.")
    for checkpoint in checkpoints:
        _validate_checkpoint_payload(checkpoint, decision_ids)
    return payload


def _validate_decision_payload(decision: Any) -> str:
    if not isinstance(decision, dict):
        raise click.ClickException("Backup decision rows must be objects.")
    decision_id = _nonempty_str(decision.get("decision_id"), "decision_id")
    _validate_category(str(decision.get("category", "")))
    _validate_action(str(decision.get("recommended_action", "")))
    _int_in_range(decision.get("category_index"), "category_index", len(CATEGORY_NAMES))
    _int_in_range(decision.get("recommended_index"), "recommended_index", len(ACTION_NAMES))
    _finite_float(decision.get("confidence"), "confidence")
    _finite_float(decision.get("created_at"), "created_at")
    probabilities = decision.get("probabilities")
    if not isinstance(probabilities, list) or len(probabilities) != len(ACTION_NAMES):
        raise click.ClickException("Backup decision probabilities must match live Purchasing actions.")
    for index, value in enumerate(probabilities):
        _finite_float(value, f"probabilities[{index}]")
    factor_vector = decision.get("factor_vector")
    if not isinstance(factor_vector, list) or len(factor_vector) != len(FACTOR_NAMES):
        raise click.ClickException("Backup decision factor_vector must match live Purchasing factors.")
    for index, value in enumerate(factor_vector):
        _finite_float(value, f"factor_vector[{index}]")
    factors = decision.get("factors")
    if not isinstance(factors, dict):
        raise click.ClickException("Backup decision factors must be objects.")
    _parse_factors(json.dumps({name: factors.get(name) for name in FACTOR_NAMES}), ())
    return decision_id


def _validate_checkpoint_payload(checkpoint: Any, decision_ids: set[str]) -> None:
    if not isinstance(checkpoint, dict):
        raise click.ClickException("Backup checkpoint rows must be objects.")
    _validate_category(str(checkpoint.get("category", "")))
    decision_id = checkpoint.get("decision_id")
    if decision_id is not None and str(decision_id) not in decision_ids:
        raise click.ClickException(f"Checkpoint references unknown decision_id: {decision_id}")
    metadata = checkpoint.get("metadata", {})
    if not isinstance(metadata, dict):
        raise click.ClickException("Backup checkpoint metadata must be an object.")
    for field in ("decision_time_start", "decision_time_end", "checkpoint_time"):
        value = checkpoint.get(field)
        if value is not None and not isinstance(value, str):
            raise click.ClickException(f"Backup checkpoint {field} must be a string.")
    centroids = checkpoint.get("centroids")
    if not isinstance(centroids, list) or len(centroids) != SHAPE.n_categories:
        raise click.ClickException("Backup checkpoint centroids do not match live Purchasing shape.")
    for category_index, category_rows in enumerate(centroids):
        if not isinstance(category_rows, list) or len(category_rows) != SHAPE.n_actions:
            raise click.ClickException("Backup checkpoint centroids do not match live Purchasing shape.")
        for action_index, action_rows in enumerate(category_rows):
            if not isinstance(action_rows, list) or len(action_rows) != SHAPE.n_factors:
                raise click.ClickException("Backup checkpoint centroids do not match live Purchasing shape.")
            for factor_index, value in enumerate(action_rows):
                _finite_float(value, f"centroids[{category_index}][{action_index}][{factor_index}]")


def _nonempty_str(value: Any, field: str) -> str:
    if value is None:
        raise click.ClickException(f"Backup {field} is required.")
    text = str(value)
    if not text:
        raise click.ClickException(f"Backup {field} must not be empty.")
    return text


def _finite_float(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise click.ClickException(f"Backup {field} must be numeric.") from exc
    if not math.isfinite(number):
        raise click.ClickException(f"Backup {field} must be finite.")
    return number


def _int_in_range(value: Any, field: str, upper_bound: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise click.ClickException(f"Backup {field} must be an integer.") from exc
    if number < 0 or number >= upper_bound:
        raise click.ClickException(f"Backup {field} is out of range.")
    return number


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--db-path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_DB_PATH,
    show_default=True,
    help="SQLite scorer state path.",
)
@click.pass_context
def cli(ctx: click.Context, db_path: Path) -> None:
    """Purchasing Copilot offline commands."""

    ctx.obj = {"db_path": db_path.expanduser()}


@cli.command()
@click.option("--category", required=True, help="Purchasing category to score.")
@click.option("--factors", help="JSON object containing all Purchasing factors.")
@click.option(
    "--factor",
    "factor_items",
    multiple=True,
    help="Purchasing factor as name=value. Repeat for all factors.",
)
@click.pass_context
def score(ctx: click.Context, category: str, factors: str | None, factor_items: tuple[str, ...]) -> None:
    """Score one purchasing decision."""

    _validate_category(category)
    parsed_factors = _parse_factors(factors, factor_items)
    result = _scorer(ctx.obj["db_path"]).score(
        parsed_factors,
        category,
        metadata={"source": "purchasing-cli"},
    )
    probabilities = {
        action: float(probability)
        for action, probability in zip(ACTION_NAMES, result.probabilities, strict=True)
    }
    click.echo(f"decision_id: {result.decision_id}")
    click.echo(f"category: {result.category}")
    click.echo(f"action: {result.action}")
    click.echo(f"confidence: {result.confidence:.6f}")
    click.echo(f"factor_count: {len(result.factors)}")
    click.echo(f"actions: {', '.join(ACTION_NAMES)}")
    click.echo(f"probabilities: {json.dumps(probabilities, sort_keys=True)}")


@cli.command()
@click.option("--decision-id", required=True, help="Decision ID returned by score.")
@click.option("--actual-action", required=True, help="Actual Purchasing action.")
@click.option("--outcome", default="confirmed", show_default=True)
@click.pass_context
def learn(ctx: click.Context, decision_id: str, actual_action: str, outcome: str) -> None:
    """Record the actual action for a previous decision."""

    _validate_action(actual_action)
    try:
        result = _scorer(ctx.obj["db_path"]).learn(decision_id, actual_action, outcome=outcome)
    except KeyError as exc:
        raise click.ClickException(f"Decision ID not found: {decision_id}") from exc

    click.echo(f"decision_id: {result.decision_id}")
    click.echo(f"actual_action: {actual_action}")
    click.echo(f"outcome: {result.outcome}")
    click.echo(f"reward: {result.reward}")
    click.echo(f"iks_before: {result.iks_before}")
    click.echo(f"iks_after: {result.iks_after}")


@cli.command()
@click.pass_context
def conservation(ctx: click.Context) -> None:
    """Display conservation-law status for the Purchasing store."""

    store = _store(ctx.obj["db_path"])
    try:
        total = store.count_decisions(DOMAIN)
        verified = store.count_verified(DOMAIN)
        correct = store.count_correct(DOMAIN)
        check = conservation_status(
            verified_count=verified,
            correct_count=correct,
            total_decisions=total,
            penalty_ratio=PRESET.penalty_ratio,
        )
    finally:
        store.close()

    click.echo(f"domain: {DOMAIN}")
    click.echo(f"total_decisions: {total}")
    click.echo(f"verified_count: {verified}")
    click.echo(f"correct_count: {correct}")
    click.echo(f"penalty_ratio: {PRESET.penalty_ratio}")
    click.echo(f"q: {_json_safe(float(check.signal))}")
    click.echo(f"theta_min: {_json_safe(float(check.theta_min))}")
    click.echo(f"status: {check.status}")


@cli.command()
@click.pass_context
def trajectory(ctx: click.Context) -> None:
    """Display IKS checkpoint trajectory."""

    payload = asdict(_scorer(ctx.obj["db_path"]).trajectory())
    payload["label"] = "IKS trajectory"
    click.echo(_json_dump(payload))


@cli.command()
@click.pass_context
def fingerprint(ctx: click.Context) -> None:
    """Display per-factor fingerprint values."""

    payload = asdict(_scorer(ctx.obj["db_path"]).fingerprint())
    click.echo(_json_dump(payload))


@cli.command()
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Backup JSON file path.",
)
@click.pass_context
def backup(ctx: click.Context, output: Path | None) -> None:
    """Back up Purchasing scorer state to JSON."""

    db_path = ctx.obj["db_path"]
    if output is None:
        backup_dir = db_path.expanduser().parent / "backup"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = backup_dir / f"purchasing-backup-{timestamp}.json"
    output = output.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)

    store = _store(db_path)
    try:
        decisions = store.get_all_decisions(DOMAIN)
        verified = store.get_verified_decisions(DOMAIN)
        checkpoints = store.get_centroid_checkpoints(DOMAIN, limit=None)
    finally:
        store.close()

    payload = {
        "version": BACKUP_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "domain": DOMAIN,
        "shape": _shape_payload(),
        "decision_count": len(decisions),
        "verified_count": len(verified),
        "decisions": decisions,
        "verified_decisions": verified,
        "centroid_checkpoints": checkpoints,
    }
    output.write_text(_json_dump(payload), encoding="utf-8")
    click.echo(f"Backup written: {output}")
    click.echo(f"Decision count: {len(decisions)}")
    click.echo(f"Verified count: {len(verified)}")


@cli.command()
@click.option("from_file", "--from", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_context
def restore(ctx: click.Context, from_file: Path) -> None:
    """Restore Purchasing scorer state from JSON."""

    try:
        payload = json.loads(from_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid backup JSON: {exc.msg}") from exc
    payload = _validate_backup_payload(payload)

    store = _store(ctx.obj["db_path"])
    restored = 0
    verified_restored = 0
    checkpoints_restored = 0
    try:
        for decision in payload["decisions"]:
            store.write_decision(
                DOMAIN,
                category=str(decision["category"]),
                action=str(decision["recommended_action"]),
                confidence=float(decision["confidence"]),
                factors={name: float(decision["factors"][name]) for name in FACTOR_NAMES},
                metadata={
                    "decision_id": str(decision["decision_id"]),
                    "category_index": int(decision["category_index"]),
                    "recommended_index": int(decision["recommended_index"]),
                    "probabilities": list(decision.get("probabilities") or []),
                    "factor_vector": list(decision.get("factor_vector") or []),
                    "created_at": float(decision.get("created_at") or 0.0),
                },
            )
            restored += 1
        for decision in payload["verified_decisions"]:
            store.write_outcome(
                str(decision["decision_id"]),
                str(decision["actual_action"]),
                bool(decision["is_correct"]),
                domain=DOMAIN,
                metadata={
                    "actual_index": int(decision.get("actual_index", 0)),
                    "verified_at": float(decision.get("verified_at") or 0.0),
                    "context": decision.get("context") or {},
                },
            )
            verified_restored += 1
        for checkpoint in payload.get("centroid_checkpoints", []):
            store.save_centroids(
                DOMAIN,
                category=str(checkpoint["category"]),
                centroids=checkpoint["centroids"],
                metadata=dict(checkpoint.get("metadata") or {}),
                decision_id=checkpoint.get("decision_id"),
                decision_time_start=checkpoint.get("decision_time_start"),
                decision_time_end=checkpoint.get("decision_time_end"),
                checkpoint_time=checkpoint.get("checkpoint_time"),
            )
            checkpoints_restored += 1
    finally:
        store.close()

    click.echo(f"Restored decisions: {restored}")
    click.echo(f"Restored verified decisions: {verified_restored}")
    click.echo(f"Restored centroid checkpoints: {checkpoints_restored}")


def main(args: list[str] | None = None) -> int:
    try:
        cli.main(args=args, standalone_mode=False)
    except click.ClickException as exc:
        exc.show()
        return exc.exit_code
    except click.Abort:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
