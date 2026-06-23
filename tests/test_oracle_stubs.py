from __future__ import annotations

import pytest

from copilot_sdk.substantiation.oracles import (
    ChefOracle,
    DataOpsOracle,
    TraderOracle,
)


@pytest.mark.parametrize("oracle_cls", [TraderOracle, ChefOracle, DataOpsOracle])
def test_oracle_has_protocol_shape(oracle_cls) -> None:
    oracle = oracle_cls()
    outcome = oracle.synthetic_outcome(shown=True)

    assert isinstance(oracle.known_effect, float)
    assert isinstance(oracle.known_accuracy_effect, float)
    assert callable(oracle.synthetic_outcome)
    assert "action" in outcome
    assert "was_override" in outcome
    assert "quality_signal" in outcome
    assert "correct" in outcome
    assert isinstance(outcome["correct"], bool)
