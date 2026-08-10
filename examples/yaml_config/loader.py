"""Minimal YAML -> configured real CompoundingScorer binding."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
import importlib

from copilot_sdk.scoring.scorer import CompoundingScorer, ScoreResult

_yaml = cast(Any, importlib.import_module("yaml"))

_FACTOR_ALIASES = {
    "thesis_conviction": "signal_confidence",
    "risk_reward": "risk_reward_actual",
}


def load_domain_config(yaml_path: str | Path) -> dict[str, Any]:
    """Read a Level-2 file and return its preset plus validated overrides."""
    raw = _yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict) or not isinstance(raw.get("from"), str):
        raise ValueError("YAML config must contain a string 'from' preset")
    overrides = raw.get("overrides", {})
    if not isinstance(overrides, dict):
        raise ValueError("'overrides' must be a mapping")
    factors = overrides.get("factors", {})
    if not isinstance(factors, dict):
        raise ValueError("'overrides.factors' must be a mapping")
    weights: dict[str, float] = {}
    for name, settings in factors.items():
        if not isinstance(settings, dict) or "weight" not in settings:
            raise ValueError(f"factor {name!r} needs a numeric weight")
        weights[_FACTOR_ALIASES.get(str(name), str(name))] = float(settings["weight"])
    penalty_ratio = float(overrides.get("penalty_ratio", 3.0))
    return {"from": raw["from"], "penalty_ratio": penalty_ratio, "factor_weights": weights}


class ConfiguredScorer:
    """Thin config adapter; all decisions still use CompoundingScorer.score/learn."""

    def __init__(self, scorer: CompoundingScorer, config: dict[str, Any]) -> None:
        self._scorer = scorer
        self.config = config

    def score(self, factors: dict[str, float], category: str) -> ScoreResult:
        weights = self.config["factor_weights"]
        adjusted = dict(factors)
        for name, weight in weights.items():
            if name in adjusted:
                adjusted[name] = 0.5 + (float(adjusted[name]) - 0.5) * float(weight)
        return self._scorer.score(adjusted, category)

    def learn(self, *args: Any, **kwargs: Any) -> Any:
        return self._scorer.learn(*args, **kwargs)


def build_scorer(config: dict[str, Any]) -> ConfiguredScorer:
    """Build the real SDK scorer from a loaded config mapping."""
    scorer = CompoundingScorer.from_preset(
        str(config["from"]), profile="test", enable_rl=False
    )
    return ConfiguredScorer(scorer, config)


def load_scorer(yaml_path: str | Path) -> ConfiguredScorer:
    """Load YAML and construct the configured scorer in one call."""
    return build_scorer(load_domain_config(yaml_path))
