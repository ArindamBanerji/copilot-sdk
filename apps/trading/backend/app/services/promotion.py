"""Deterministic strategy promotion tiers for Trading."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TIERS = ["paper", "small_live", "full_live"]
PROMOTION_THRESHOLDS = {
    ("paper", "small_live"): {"win_rate": 0.55, "verified_count": 50},
    ("small_live", "full_live"): {"win_rate": 0.58, "verified_count": 100},
}
DEMOTION_WINDOW = 20
DEMOTION_FLOOR = 0.50


def strategy_key(category: str | None, strategy_tag: str | None = None) -> str:
    category_name = str(category or "uncategorized")
    tag = str(strategy_tag or "default")
    return f"{category_name}:{tag}"


class PromotionService:
    def __init__(self, config_dir: str | Path | None = None) -> None:
        self.config_dir = Path(config_dir).expanduser() if config_dir is not None else None
        self._state = self._load()

    def _tier_file(self) -> Path | None:
        if self.config_dir is None:
            return None
        return self.config_dir / "promotion_tiers.json"

    def _load(self) -> dict[str, Any]:
        path = self._tier_file()
        if path is None or not path.exists():
            return {"tiers": {}, "history": []}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"tiers": {}, "history": []}
        tiers = payload.get("tiers") if isinstance(payload, dict) else None
        history = payload.get("history") if isinstance(payload, dict) else None
        return {
            "tiers": tiers if isinstance(tiers, dict) else {},
            "history": history if isinstance(history, list) else [],
        }

    def _save(self) -> None:
        path = self._tier_file()
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8")

    def get_tier(self, key: str) -> str:
        tier = str(self._state.get("tiers", {}).get(key) or "paper")
        return tier if tier in TIERS else "paper"

    def get_all_tiers(self) -> dict[str, str]:
        tiers = {
            str(key): str(value)
            for key, value in self._state.get("tiers", {}).items()
            if str(value) in TIERS
        }
        return dict(sorted(tiers.items()))

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._state.get("history", []))

    def evaluate(
        self,
        trades: list[dict[str, Any]],
        conservation_status: Any = None,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        grouped = _group_trades(trades)
        conservation_green = _is_conservation_green(conservation_status)

        for key in sorted(grouped):
            rows = grouped[key]
            category, tag = _split_key(key)
            metrics = _metrics(rows)
            current = self.get_tier(key)
            target = current
            action = None
            reason = None

            demotion_target = _demotion_target(current, rows)
            if demotion_target:
                target = demotion_target
                action = "demote"
                reason = f"last {DEMOTION_WINDOW} win rate below {DEMOTION_FLOOR:.0%}"
            elif conservation_green:
                promotion_target = _promotion_target(current, metrics)
                if promotion_target:
                    target = promotion_target
                    action = "promote"
                    reason = _promotion_reason(current, promotion_target)
            elif current != "full_live":
                reason = "conservation not GREEN"

            if action is None or target == current:
                continue

            event = {
                "strategy_key": key,
                "category": category,
                "strategy_tag": None if tag == "default" else tag,
                "action": action,
                "from_tier": current,
                "to_tier": target,
                "win_rate": metrics["win_rate"],
                "verified_count": metrics["verified_count"],
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._state.setdefault("tiers", {})[key] = target
            self._state.setdefault("history", []).append(event)
            events.append(event)

        if events:
            self._save()
        return events


def _is_conservation_green(status: Any) -> bool:
    if status is None:
        return False
    if isinstance(status, str):
        return status.strip().upper() == "GREEN"
    if not isinstance(status, dict):
        return False
    status_value = status.get("status")
    if isinstance(status_value, str) and status_value.strip().upper() == "GREEN":
        return True
    state_value = status.get("state")
    if isinstance(state_value, str) and state_value.strip().upper() == "GREEN":
        return True
    phase_value = status.get("phase")
    if isinstance(phase_value, str) and phase_value.strip().lower() in {"green", "verified", "active"}:
        return True
    if status.get("overall_safe") is True or status.get("overallSafe") is True:
        return True
    return False


def _group_trades(trades: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for trade in trades:
        category = trade.get("category")
        if not category:
            continue
        key = strategy_key(str(category), _strategy_tag(trade))
        grouped.setdefault(key, []).append(trade)
    return grouped


def _metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    verified = [trade for trade in trades if _is_verified(trade)]
    wins = sum(1 for trade in verified if (_trade_pnl(trade) or 0.0) > 0)
    total = len(verified)
    return {
        "verified_count": total,
        "win_rate": round(wins / total, 4) if total else 0.0,
        "wins": wins,
    }


def _promotion_target(current: str, metrics: dict[str, Any]) -> str | None:
    if current == "paper":
        threshold = PROMOTION_THRESHOLDS[("paper", "small_live")]
        if metrics["win_rate"] >= threshold["win_rate"] and metrics["verified_count"] >= threshold["verified_count"]:
            return "small_live"
    if current == "small_live":
        threshold = PROMOTION_THRESHOLDS[("small_live", "full_live")]
        # v1 has no per-tier baseline; total verified count is the evidence window.
        if metrics["win_rate"] >= threshold["win_rate"] and metrics["verified_count"] >= threshold["verified_count"]:
            return "full_live"
    return None


def _promotion_reason(current: str, target: str) -> str:
    threshold = PROMOTION_THRESHOLDS[(current, target)]
    return (
        f"win rate >= {threshold['win_rate']:.0%} and "
        f"verified trades >= {threshold['verified_count']}"
    )


def _demotion_target(current: str, trades: list[dict[str, Any]]) -> str | None:
    if current == "paper":
        return None
    recent = _recent_verified(trades, DEMOTION_WINDOW)
    if len(recent) < DEMOTION_WINDOW:
        return None
    wins = sum(1 for trade in recent if (_trade_pnl(trade) or 0.0) > 0)
    if wins / len(recent) >= DEMOTION_FLOOR:
        return None
    index = TIERS.index(current)
    return TIERS[max(0, index - 1)]


def _recent_verified(trades: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    verified = [trade for trade in trades if _is_verified(trade)]
    return sorted(verified, key=_trade_sort_key, reverse=True)[:limit]


def _is_verified(trade: dict[str, Any]) -> bool:
    if bool(trade.get("verified")) or bool(trade.get("is_correct")):
        return True
    return _trade_pnl(trade) is not None


def _strategy_tag(trade: dict[str, Any]) -> str | None:
    value = trade.get("strategy_tag") or trade.get("thesis_type")
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    value = value or metadata.get("strategy_tag") or metadata.get("thesis_type")
    return str(value) if value not in {None, ""} else None


def _trade_pnl(trade: dict[str, Any]) -> float | None:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    for key in ("pnl", "pnl_dollars"):
        value = trade.get(key) if key in trade else metadata.get(key)
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _trade_sort_key(trade: dict[str, Any]) -> str:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    return str(trade.get("entry_time") or metadata.get("entry_time") or trade.get("date") or metadata.get("date") or "")


def _split_key(key: str) -> tuple[str, str]:
    if ":" not in key:
        return key, "default"
    category, tag = key.split(":", 1)
    return category, tag or "default"
