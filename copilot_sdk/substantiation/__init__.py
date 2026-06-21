"""Public API for substantiation discipline."""

from .holdout import ConditionalHoldout, HoldoutAssigner, UnconditionalHoldout
from .chef_oracle import ChefOracle, ChefPipelineTest
from .cohort_day_zero import (
    ACCUMULATING,
    INSTRUMENT_VALIDATED,
    MEASURED,
    STATES,
    BaseCohortDayZeroState,
    compute_state,
    evaluate_v7_gate,
)
from .dataops_oracle import DataOpsOracle, DataOpsPipelineTest
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
from .trader_oracle import TraderOracle, TraderPipelineTest

__all__ = [
    "Tier",
    "ClaimProvenance",
    "ClaimRegistry",
    "PromotionEvent",
    "TIER_LANGUAGE",
    "DayZeroReadiness",
    "INSTRUMENT_VALIDATED",
    "ACCUMULATING",
    "MEASURED",
    "STATES",
    "BaseCohortDayZeroState",
    "compute_state",
    "evaluate_v7_gate",
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
    "TraderOracle",
    "TraderPipelineTest",
    "ChefOracle",
    "ChefPipelineTest",
    "DataOpsOracle",
    "DataOpsPipelineTest",
]
