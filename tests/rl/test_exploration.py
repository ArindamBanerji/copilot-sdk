from __future__ import annotations

import pytest

from copilot_sdk.rl import ConservationBoundedThompson


def test_green_can_select_valid_action(monkeypatch):
    policy = ConservationBoundedThompson(n_actions=3)
    monkeypatch.setattr("copilot_sdk.rl.exploration.random.random", lambda: 0.0)
    monkeypatch.setattr(
        "copilot_sdk.rl.exploration.random.gammavariate",
        lambda alpha, scale: alpha,
    )
    policy.alpha = [1.0, 4.0, 2.0]

    assert policy.select_action([0.4, 0.3, 0.3]) == 1


def test_amber_returns_best_action(monkeypatch):
    policy = ConservationBoundedThompson(n_actions=3)
    policy.set_conservation_status("AMBER")
    monkeypatch.setattr("copilot_sdk.rl.exploration.random.random", lambda: 0.0)

    assert policy.select_action([0.2, 0.7, 0.1]) == 1


def test_red_returns_best_action(monkeypatch):
    policy = ConservationBoundedThompson(n_actions=3)
    policy.set_conservation_status("RED")
    monkeypatch.setattr("copilot_sdk.rl.exploration.random.random", lambda: 0.0)

    assert policy.select_action([0.2, 0.1, 0.7]) == 2


def test_update_alpha_beta():
    policy = ConservationBoundedThompson(n_actions=2)

    policy.update(0, 0.5)
    policy.update(1, -0.25)
    policy.update(1, 0.0)

    assert policy.alpha == [1.5, 1.0]
    assert policy.beta == [1.0, 1.25]


def test_get_priors():
    policy = ConservationBoundedThompson(n_actions=2)
    policy.set_conservation_status("amber")

    assert policy.get_priors() == {
        "alpha": [1.0, 1.0],
        "beta": [1.0, 1.0],
        "conservation_status": "AMBER",
    }


def test_reset():
    policy = ConservationBoundedThompson(n_actions=2)
    policy.update(0, 1.0)
    policy.set_conservation_status("RED")

    policy.reset()

    assert policy.get_priors() == {
        "alpha": [1.0, 1.0],
        "beta": [1.0, 1.0],
        "conservation_status": "GREEN",
    }


def test_deterministic_when_confidence_max_one(monkeypatch):
    policy = ConservationBoundedThompson(n_actions=2)
    called = {"random": False}

    def random_call():
        called["random"] = True
        return 0.0

    monkeypatch.setattr("copilot_sdk.rl.exploration.random.random", random_call)

    assert policy.select_action([1.0, 0.0]) == 0
    assert called["random"] is True


def test_status_change():
    policy = ConservationBoundedThompson(n_actions=2)

    policy.set_conservation_status("red")

    assert policy.get_priors()["conservation_status"] == "RED"
    with pytest.raises(ValueError, match="status"):
        policy.set_conservation_status("BLUE")


def test_empty_probabilities_raise():
    policy = ConservationBoundedThompson(n_actions=2)

    with pytest.raises(ValueError, match="probabilities"):
        policy.select_action([])


def test_update_action_bounds_guarded():
    policy = ConservationBoundedThompson(n_actions=2)

    with pytest.raises(IndexError, match="action"):
        policy.update(3, 1.0)
