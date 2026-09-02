"""Conservation-bounded exploration policies."""

from __future__ import annotations

import random
from collections.abc import Iterable
from typing import Any

from copilot_sdk.rl.types import ExplorationDecision


class ConservationBoundedThompson:
    """Compatibility Thompson policy used by the SDK compounding scorer."""

    def __init__(self, n_actions: int, graph_store: Any | None = None) -> None:
        if int(n_actions) <= 0:
            raise ValueError("n_actions must be positive")
        self.n_actions = int(n_actions)
        self._graph_store = graph_store
        self.alpha = [1.0] * self.n_actions
        self.beta = [1.0] * self.n_actions
        self._conservation_status = "GREEN"
        self._load_from_store()

    def select_action(self, probabilities: Iterable[float]) -> int:
        values = [float(value) for value in probabilities]
        if not values:
            raise ValueError("probabilities must not be empty")
        if len(values) != self.n_actions:
            raise ValueError("probabilities length must match n_actions")
        best = _argmax(values)
        if self._conservation_status != "GREEN":
            return best
        explore_probability = max(0.0, min(1.0, 1.0 - max(values)))
        if random.random() >= explore_probability:
            return best
        samples = [self._beta_sample(a, b) for a, b in zip(self.alpha, self.beta)]
        return _argmax(samples)

    def update(self, action: int, reward: float) -> None:
        index = self._safe_action(action)
        if float(reward) >= 0.0:
            self.alpha[index] += float(reward)
        else:
            self.beta[index] += abs(float(reward))
        self._persist()

    def set_conservation_status(self, status: str) -> None:
        normalized = str(status).strip().upper()
        if normalized not in {"GREEN", "AMBER", "RED"}:
            raise ValueError("status must be GREEN, AMBER, or RED")
        self._conservation_status = normalized

    @property
    def conservation_status(self) -> str:
        return self._conservation_status

    def get_priors(self) -> dict[str, Any]:
        return {
            "alpha": list(self.alpha),
            "beta": list(self.beta),
            "conservation_status": self._conservation_status,
        }

    def reset(self) -> None:
        self.alpha = [1.0] * self.n_actions
        self.beta = [1.0] * self.n_actions
        self._conservation_status = "GREEN"
        self._persist()

    def _safe_action(self, action: int) -> int:
        index = int(action)
        if not 0 <= index < self.n_actions:
            raise IndexError("action must be within n_actions")
        return index

    @staticmethod
    def _beta_sample(alpha: float, beta: float) -> float:
        left = random.gammavariate(alpha, 1.0)
        right = random.gammavariate(beta, 1.0)
        return left / (left + right) if left + right else 0.5

    def _load_from_store(self) -> None:
        loader = getattr(self._graph_store, "load_rl_state", None)
        if not callable(loader):
            return
        try:
            state = loader("thompson_posteriors")
        except Exception:
            return
        if not isinstance(state, dict):
            return
        alpha = state.get("alpha")
        beta = state.get("beta")
        if (
            not isinstance(alpha, list)
            or not isinstance(beta, list)
            or len(alpha) != self.n_actions
            or len(beta) != self.n_actions
        ):
            return
        try:
            self.alpha = [float(value) for value in alpha]
            self.beta = [float(value) for value in beta]
        except (TypeError, ValueError):
            return
        status = state.get("conservation_status")
        if isinstance(status, str) and status.upper() in {"GREEN", "AMBER", "RED"}:
            self._conservation_status = status.upper()

    def _persist(self) -> None:
        saver = getattr(self._graph_store, "save_rl_state", None)
        if not callable(saver):
            return
        try:
            saver("thompson_posteriors", self.get_priors())
        except Exception:
            return


class ExplorationPolicy:
    """Epsilon-greedy exploration bounded by the conservation safety floor."""

    EPSILON_FIRM_STAR = 0.125

    def __init__(
        self,
        n_actions: int,
        epsilon: float = EPSILON_FIRM_STAR,
        graph_store: Any | None = None,
        penalty_ratio: float = 1.0,
    ) -> None:
        if int(n_actions) <= 0:
            raise ValueError("n_actions must be positive")
        if not 0.0 <= float(epsilon) <= self.EPSILON_FIRM_STAR:
            raise ValueError("epsilon must be between 0 and epsilon_firm_star")
        if float(penalty_ratio) <= 0.0:
            raise ValueError("penalty_ratio must be positive")
        self.n_actions = int(n_actions)
        self.epsilon = float(epsilon)
        self.graph_store = graph_store
        self._graph_store = graph_store
        self.penalty_ratio = float(penalty_ratio)
        self._conservation_status = "GREEN"

    def select_action(
        self, values: Iterable[float], conservation_fraction: float = 0.0
    ) -> ExplorationDecision:
        scores = [float(value) for value in values]
        if len(scores) != self.n_actions:
            raise ValueError("values length must match n_actions")
        best = _argmax(scores)
        fraction = max(0.0, min(1.0, float(conservation_fraction)))
        effective_epsilon = min(
            self.epsilon, self.EPSILON_FIRM_STAR * (1.0 - fraction)
        )
        if self._conservation_status != "GREEN":
            effective_epsilon = 0.0
        explored = effective_epsilon > 0.0 and random.random() < effective_epsilon
        action = random.randrange(self.n_actions) if explored else best
        return ExplorationDecision(action, explored, effective_epsilon, self._conservation_status)

    def set_conservation_status(self, status: str) -> None:
        normalized = str(status).strip().upper()
        if normalized not in {"GREEN", "AMBER", "RED"}:
            raise ValueError("status must be GREEN, AMBER, or RED")
        self._conservation_status = normalized

    @property
    def conservation_status(self) -> str:
        return self._conservation_status


def _argmax(values: list[float]) -> int:
    return max(range(len(values)), key=values.__getitem__)
