import numpy as np
from copilot_sdk.protocols import FactorComputer


class ScoreAFactor:
    factor_name  = "score_a"
    factor_index = 0
    def compute(self, event: dict) -> float:
        return float(np.clip(event.get("score_a", 0.5), 0, 1))


class ScoreBFactor:
    factor_name  = "score_b"
    factor_index = 1
    def compute(self, event: dict) -> float:
        return float(np.clip(event.get("score_b", 0.5), 0, 1))


FACTOR_COMPUTERS = [ScoreAFactor(), ScoreBFactor()]


def compute_factor_vector(event: dict) -> list[float]:
    return [fc.compute(event) for fc in FACTOR_COMPUTERS]
