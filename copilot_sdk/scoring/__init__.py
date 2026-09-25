"""CompoundingScorer core package."""

from copilot_sdk.scoring.config import DomainPreset, DomainShape
from copilot_sdk.scoring.scorer import CompoundingScorer, LearnResult, ScoreResult
from copilot_sdk.scoring.investigation import (
    EvidenceProvider,
    InvestigationStep,
    InvestigationTrace,
    KUtilityStore,
    VLDInvestigator,
)
from copilot_sdk.scoring.situation_classifier import (
    SITUATION_BUDGETS,
    SituationAssessment,
    SituationClassifier,
    extract_features,
)

__version__ = "0.1.0"

__all__ = [
    "CompoundingScorer",
    "DomainPreset",
    "DomainShape",
    "LearnResult",
    "ScoreResult",
    "EvidenceProvider",
    "InvestigationStep",
    "InvestigationTrace",
    "KUtilityStore",
    "VLDInvestigator",
    "SITUATION_BUDGETS",
    "SituationAssessment",
    "SituationClassifier",
    "extract_features",
    "__version__",
]
