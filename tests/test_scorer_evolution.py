from __future__ import annotations

from copilot_sdk.scoring.evolution import EvolutionProposal, ScorerEvolution


def decisions(
    count: int,
    *,
    correct: int | None = None,
    overrides: int = 0,
    recent_decline: bool = False,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if recent_decline:
        for index in range(count):
            rows.append({
                "is_correct": index < count - 100,
                "was_override": index < overrides,
            })
        return rows
    correct_count = count if correct is None else correct
    for index in range(count):
        rows.append({
            "is_correct": index < correct_count,
            "was_override": index < overrides,
        })
    return rows


def test_proposal_stable_accuracy() -> None:
    evo = ScorerEvolution("trading")
    proposals = evo.evaluate(
        decisions(500, correct=450),
        {"eta_confirm": 0.05, "penalty_ratio": 3.0},
        "GREEN",
    )
    eta = [p for p in proposals if p.parameter == "eta_confirm"]
    assert eta
    assert eta[0].proposed_value < eta[0].current_value


def test_proposal_declining_accuracy() -> None:
    evo = ScorerEvolution("trading")
    proposals = evo.evaluate(
        decisions(500, recent_decline=True),
        {"eta_confirm": 0.05, "penalty_ratio": 3.0},
        "GREEN",
    )
    eta = [p for p in proposals if p.parameter == "eta_confirm"]
    assert eta
    assert any(p.proposed_value > p.current_value for p in eta)


def test_proposal_high_override() -> None:
    evo = ScorerEvolution("trading")
    proposals = evo.evaluate(
        decisions(500, correct=400, overrides=180),
        {"eta_confirm": 0.05, "penalty_ratio": 10.0},
        "GREEN",
    )
    penalty = [p for p in proposals if p.parameter == "penalty_ratio"]
    assert penalty
    assert penalty[0].proposed_value < penalty[0].current_value


def test_proposal_low_override_high_accuracy() -> None:
    evo = ScorerEvolution("trading")
    proposals = evo.evaluate(
        decisions(500, correct=480, overrides=20),
        {"eta_confirm": 0.05, "penalty_ratio": 10.0},
        "GREEN",
    )
    penalty = [p for p in proposals if p.parameter == "penalty_ratio"]
    assert penalty
    assert penalty[0].proposed_value > penalty[0].current_value


def test_hard_bounds_eta_upper() -> None:
    evo = ScorerEvolution("trading")
    proposal = EvolutionProposal("eta_confirm", 0.10, 2.0, "test", "GREEN", True)
    config = {"eta_confirm": 0.10}
    assert evo.apply(proposal, config, "GREEN")
    assert config["eta_confirm"] == 0.10


def test_hard_bounds_eta_lower() -> None:
    evo = ScorerEvolution("trading")
    proposal = EvolutionProposal("eta_confirm", 0.01, 0.001, "test", "GREEN", True)
    config = {"eta_confirm": 0.01}
    assert evo.apply(proposal, config, "GREEN")
    assert config["eta_confirm"] == 0.01


def test_hard_bounds_penalty() -> None:
    evo = ScorerEvolution("trading")
    proposal = EvolutionProposal("penalty_ratio", 3.0, 0.5, "test", "GREEN", True)
    config = {"penalty_ratio": 3.0}
    assert evo.apply(proposal, config, "GREEN")
    assert config["penalty_ratio"] == 3.0


def test_conservation_gate() -> None:
    evo = ScorerEvolution("trading")
    proposals = evo.evaluate(decisions(500, correct=480), {"eta_confirm": 0.05}, "AMBER")
    assert proposals == []


def test_conservation_gate_red() -> None:
    evo = ScorerEvolution("trading")
    proposals = evo.evaluate(decisions(500, correct=480), {"eta_confirm": 0.05}, "RED")
    assert proposals == []


def test_apply_updates_config() -> None:
    evo = ScorerEvolution("trading")
    proposal = EvolutionProposal("eta_confirm", 0.05, 0.04, "test evidence", "GREEN", True)
    config = {"eta_confirm": 0.05}
    assert evo.apply(proposal, config, "GREEN")
    assert config["eta_confirm"] == 0.04


def test_apply_logs_change() -> None:
    evo = ScorerEvolution("trading")
    proposal = EvolutionProposal("eta_confirm", 0.05, 0.04, "test evidence", "GREEN", True)
    assert evo.apply(proposal, {"eta_confirm": 0.05}, "GREEN")
    assert evo.evolution_log()
    assert evo.evolution_log()[-1]["evidence"] == "test evidence"


def test_rollback_on_amber() -> None:
    evo = ScorerEvolution("trading")
    config = {"eta_confirm": 0.05}
    proposal = EvolutionProposal("eta_confirm", 0.05, 0.04, "test", "GREEN", True)
    assert evo.apply(proposal, config, "GREEN")
    rolled_back = evo.rollback_on_conservation("AMBER", config)
    assert rolled_back == ["eta_confirm"]
    assert config["eta_confirm"] == 0.05


def test_rollback_restores_original() -> None:
    evo = ScorerEvolution("trading")
    config = {"penalty_ratio": 10.0}
    proposal = EvolutionProposal("penalty_ratio", 10.0, 11.0, "test", "GREEN", True)
    assert evo.apply(proposal, config, "GREEN")
    assert evo.rollback("penalty_ratio", config)
    assert config["penalty_ratio"] == 10.0


def test_no_centroid_mutation() -> None:
    evo = ScorerEvolution("trading")
    config = {
        "eta_confirm": 0.05,
        "centroids": [[1.0, 2.0]],
        "dk": {"weights": [1.0]},
    }
    centroids = config["centroids"]
    dk = config["dk"]
    proposal = EvolutionProposal("eta_confirm", 0.05, 0.04, "test", "GREEN", True)
    assert evo.apply(proposal, config, "GREEN")
    assert config["centroids"] is centroids
    assert config["dk"] is dk


def test_apply_rejects_if_conservation_degraded_after_proposal() -> None:
    evo = ScorerEvolution("trading")
    proposal = EvolutionProposal("eta_confirm", 0.05, 0.04, "test", "GREEN", True)
    config = {"eta_confirm": 0.05}
    assert evo.apply(proposal, config, "AMBER") is False
    assert proposal.approved is False
    assert proposal.applied is False
    assert config["eta_confirm"] == 0.05


def test_find_proposal() -> None:
    evo = ScorerEvolution("trading")
    proposals = evo.evaluate(decisions(500, correct=450), {"eta_confirm": 0.05}, "GREEN")
    assert proposals
    assert evo.find_proposal(proposals[0].proposal_id) is proposals[0]
    assert evo.find_proposal("missing") is None
