from __future__ import annotations

from typing import cast
from dataclasses import dataclass

import numpy as np
import pytest

from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.graph import InMemoryGraphStore


@dataclass(frozen=True)
class MockPreset:
    name: str = "mock"
    shape: DomainShape = DomainShape(
        n_categories=3,
        n_actions=2,
        n_factors=3,
        category_names=("alpha", "beta", "gamma"),
        action_names=("approve", "review"),
        factor_names=("amount", "risk", "history"),
    )
    penalty_ratio: float = 5.0
    eta_confirm: float = 0.05
    eta_override: float = 0.01
    temperature: float = 0.1

    @property
    def bootstrap_centroids(self) -> np.ndarray:
        return cast(np.ndarray, np.array(
            [
                [[0.2, 0.3, 0.4], [0.7, 0.6, 0.5]],
                [[0.3, 0.4, 0.5], [0.8, 0.7, 0.6]],
                [[0.4, 0.5, 0.6], [0.9, 0.8, 0.7]],
            ],
            dtype=np.float64,
        ))


@pytest.fixture
def mock_preset() -> MockPreset:
    return MockPreset()


@pytest.fixture
def temp_db(tmp_path):
    return tmp_path / "decisions.sqlite"


@pytest.fixture
def store():
    graph_store = InMemoryGraphStore(domain="mock")
    try:
        yield graph_store
    finally:
        graph_store.close()
