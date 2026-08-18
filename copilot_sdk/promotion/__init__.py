"""Shared Promotion & Autonomy state-machine API."""

from .core import (
    PromotionEngine,
    PromotionPolicy,
    PromotionRecord,
    PromotionResult,
    PromotionStage,
    PromotionStore,
)
from .policies import (
    DataOpsPromotionPolicy,
    PurchasingPromotionPolicy,
    S2PPromotionPolicy,
    SOCPromotionPolicy,
    TradingPromotionPolicy,
)
from .router import create_promotion_router

__all__ = [
    "PromotionStage",
    "PromotionPolicy",
    "PromotionRecord",
    "PromotionResult",
    "PromotionStore",
    "PromotionEngine",
    "S2PPromotionPolicy",
    "SOCPromotionPolicy",
    "TradingPromotionPolicy",
    "PurchasingPromotionPolicy",
    "DataOpsPromotionPolicy",
    "create_promotion_router",
]
