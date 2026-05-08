"""CompoundingScorer core package."""

from copilot_sdk.scoring.config import DomainPreset, DomainShape
from copilot_sdk.scoring.scorer import CompoundingScorer, LearnResult, ScoreResult

__version__ = "0.1.0"

__all__ = [
    "CompoundingScorer",
    "DomainPreset",
    "DomainShape",
    "LearnResult",
    "ScoreResult",
    "__version__",
]
