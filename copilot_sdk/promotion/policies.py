"""Default cross-copilot promotion policies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .core import PromotionStage


def _seven_stage_transitions() -> dict[PromotionStage, tuple[PromotionStage, ...]]:
    return {
        PromotionStage.DISCOVERED: (PromotionStage.SHADOWING,),
        PromotionStage.SHADOWING: (PromotionStage.PROMOTED,),
        PromotionStage.PROMOTED: (PromotionStage.MEASURING,),
        PromotionStage.MEASURING: (PromotionStage.KEPT,),
        PromotionStage.KEPT: (),
        PromotionStage.ROLLED_BACK: (PromotionStage.SHADOWING,),
        PromotionStage.TRANSFERRED: (),
    }


def _soc_transitions() -> dict[PromotionStage, tuple[PromotionStage, ...]]:
    return {
        PromotionStage.DISCOVERED: (PromotionStage.SHADOWING,),
        PromotionStage.SHADOWING: (PromotionStage.PROMOTED,),
        PromotionStage.PROMOTED: (PromotionStage.KEPT,),
        PromotionStage.KEPT: (),
        PromotionStage.ROLLED_BACK: (PromotionStage.SHADOWING,),
    }


def _trading_transitions() -> dict[PromotionStage, tuple[PromotionStage, ...]]:
    return {
        PromotionStage.DISCOVERED: (PromotionStage.SHADOWING,),
        PromotionStage.SHADOWING: (PromotionStage.PROMOTED,),
    }


@dataclass(frozen=True)
class S2PPromotionPolicy:
    stages: tuple[PromotionStage, ...] = tuple(PromotionStage)
    stage_names: tuple[str, ...] = (
        "discover",
        "shadow",
        "promote",
        "measure",
        "keep",
        "rollback",
        "transfer",
    )
    min_shadow_decisions: int = 10
    min_measurement_decisions: int = 10
    improvement_threshold: float = 0.0
    conservation_required: bool = True
    allowed_transitions: Mapping[PromotionStage, tuple[PromotionStage, ...]] = field(
        default_factory=_seven_stage_transitions
    )


@dataclass(frozen=True)
class SOCPromotionPolicy:
    """Five-rung SOC vocabulary projected onto common lifecycle stages."""

    stages: tuple[PromotionStage, ...] = (
        PromotionStage.DISCOVERED,
        PromotionStage.SHADOWING,
        PromotionStage.PROMOTED,
        PromotionStage.KEPT,
        PromotionStage.ROLLED_BACK,
    )
    stage_names: tuple[str, ...] = (
        "observed",
        "assisted",
        "shadow-qualified",
        "auto-approved",
        "circuit-broken",
    )
    rungs: tuple[str, ...] = (
        "observed",
        "assisted",
        "shadow-qualified",
        "auto-approved",
        "circuit-broken",
    )
    min_shadow_decisions: int = 10
    min_measurement_decisions: int = 10
    improvement_threshold: float = 0.0
    conservation_required: bool = True
    allowed_transitions: Mapping[PromotionStage, tuple[PromotionStage, ...]] = field(
        default_factory=_soc_transitions
    )


@dataclass(frozen=True)
class TradingPromotionPolicy:
    """Observation-only paper → small → full progression."""

    stages: tuple[PromotionStage, ...] = (
        PromotionStage.DISCOVERED,
        PromotionStage.SHADOWING,
        PromotionStage.PROMOTED,
    )
    stage_names: tuple[str, ...] = ("paper", "small", "full")
    min_shadow_decisions: int = 10
    min_measurement_decisions: int = 10
    improvement_threshold: float = 0.0
    conservation_required: bool = True
    allowed_transitions: Mapping[PromotionStage, tuple[PromotionStage, ...]] = field(
        default_factory=_trading_transitions
    )


class PurchasingPromotionPolicy(S2PPromotionPolicy):
    """Purchasing uses the full proof-before-authority lifecycle."""


class DataOpsPromotionPolicy(SOCPromotionPolicy):
    """DataOps uses the conservative five-rung authority progression."""
