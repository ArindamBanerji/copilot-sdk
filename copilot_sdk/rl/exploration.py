"""Conservation-bounded exploration policies."""

from __future__ import annotations

import random
from typing import Any, Iterable


_THOMPSON_STATE_KEY = "thompson_posteriors"


class ConservationBoundedThompson:
    """Thompson sampler that disables exploration outside GREEN conservation."""

    def __init__(self, n_actions: int, graph_store: Any | None = None) -> None:
        if int(n_actions) <= 0:
            raise ValueError("n_actions must be positive")
        self.n_actions = int(n_actions)
        self._graph_store = graph_store
        self.alpha = [1.0 for _ in range(self.n_actions)]
        self.beta = [1.0 for _ in range(self.n_actions)]
        self._conservation_status = "GREEN"
        self._load_from_store()

    def select_action(self, probabilities: Iterable[float]) -> int:
        values = [float(value) for value in probabilities]
        if not values:
            raise ValueError("probabilities must not be empty")
        if len(values) != self.n_actions:
            raise ValueError("probabilities length must match n_actions")

        best_action = _argmax(values)
        if self._conservation_status in {"AMBER", "RED"}:
            return best_action

        explore_probability = max(0.0, min(1.0, 1.0 - max(values)))
        if random.random() >= explore_probability:
            return best_action

        samples = [
            _beta_sample(self.alpha[index], self.beta[index])
            for index in range(self.n_actions)
        ]
        return _argmax(samples)

    def update(self, action: int, reward: float) -> None:
        action_index = self._safe_action(action)
        value = float(reward)
        if value > 0.0:
            self.alpha[action_index] += value
        elif value < 0.0:
            self.beta[action_index] += abs(value)
        self._persist()

    def set_conservation_status(self, status: str) -> None:
        normalized = str(status).strip().upper()
        if normalized not in {"GREEN", "AMBER", "RED"}:
            raise ValueError("status must be GREEN, AMBER, or RED")
        self._conservation_status = normalized

    def get_priors(self) -> dict[str, list[float] | str]:
        return {
            "alpha": list(self.alpha),
            "beta": list(self.beta),
            "conservation_status": self._conservation_status,
        }

    def reset(self) -> None:
        self.alpha = [1.0 for _ in range(self.n_actions)]
        self.beta = [1.0 for _ in range(self.n_actions)]
        self._conservation_status = "GREEN"

    def _safe_action(self, action: int) -> int:
        action_index = int(action)
        if not 0 <= action_index < self.n_actions:
            raise IndexError("action out of range")
        return action_index

    def _load_from_store(self) -> None:
        loader = getattr(self._graph_store, "load_rl_state", None)
        if not callable(loader):
            return
        try:
            data = loader(_THOMPSON_STATE_KEY)
            if not isinstance(data, dict):
                return
            alpha = _state_vector(data.get("alpha"), self.n_actions)
            beta = _state_vector(data.get("beta"), self.n_actions)
            if alpha is None or beta is None:
                return
            self.alpha = alpha
            self.beta = beta
            status = str(data.get("conservation_status", "GREEN")).strip().upper()
            if status in {"GREEN", "AMBER", "RED"}:
                self._conservation_status = status
        except Exception:
            return

    def _persist(self) -> None:
        saver = getattr(self._graph_store, "save_rl_state", None)
        if not callable(saver):
            return
        try:
            saver(_THOMPSON_STATE_KEY, self.get_priors())
        except Exception:
            return


def _state_vector(value: Any, expected_length: int) -> list[float] | None:
    if not isinstance(value, list | tuple) or len(value) != expected_length:
        return None
    try:
        return [float(item) for item in value]
    except (TypeError, ValueError):
        return None


def _beta_sample(alpha: float, beta: float) -> float:
    x = random.gammavariate(max(float(alpha), 0.0001), 1.0)
    y = random.gammavariate(max(float(beta), 0.0001), 1.0)
    total = x + y
    return x / total if total > 0.0 else 0.0


def _argmax(values: list[float]) -> int:
    best_index = 0
    best_value = values[0]
    for index, value in enumerate(values[1:], start=1):
        if value > best_value:
            best_index = index
            best_value = value
    return best_index
