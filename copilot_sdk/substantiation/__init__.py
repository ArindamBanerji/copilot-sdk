"""Public API for substantiation discipline."""

from .holdout import ConditionalHoldout, HoldoutAssigner, UnconditionalHoldout
from .instrument import AnalyticClaim, RealInstrument, ScrapedContextProvider
from .oracle import (
    AccuracyResult,
    BaseOracle,
    ExperimentResult,
    LiftResult,
    Oracle,
    compute_accuracy,
    compute_lift,
    floor_power,
)
from .populate_readiness import populate_default_readiness
from .populate_registry import populate_default_registry
from .readiness import DayZeroReadiness
from .registry import ClaimRegistry, PromotionEvent, TIER_LANGUAGE
from .tiers import ClaimProvenance, Tier

__all__ = [
    "Tier",
    "ClaimProvenance",
    "ClaimRegistry",
    "PromotionEvent",
    "TIER_LANGUAGE",
    "DayZeroReadiness",
    "populate_default_registry",
    "populate_default_readiness",
    "Oracle",
    "BaseOracle",
    "LiftResult",
    "AccuracyResult",
    "ExperimentResult",
    "compute_lift",
    "compute_accuracy",
    "floor_power",
    "HoldoutAssigner",
    "UnconditionalHoldout",
    "ConditionalHoldout",
    "RealInstrument",
    "ScrapedContextProvider",
    "AnalyticClaim",
]
