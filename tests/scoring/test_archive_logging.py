from __future__ import annotations

import logging

from gae.profile_scorer import ProfileScorer

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


def test_maybe_archive_uses_logger_not_print(mock_preset, caplog, capsys) -> None:
    store = InMemoryGraphStore(domain="test")
    scorer = CompoundingScorer(
        mock_preset,
        ProfileScorer(
            mu=mock_preset.bootstrap_centroids.copy(),
            actions=list(mock_preset.shape.action_names),
            categories=list(mock_preset.shape.category_names),
        ),
        graph_store=store,
    )
    category = mock_preset.shape.category_names[0]
    for index in range(801):
        store.write_decision(
            "test",
            category=category,
            action=mock_preset.shape.action_names[0],
            confidence=0.7,
            factors={name: 0.5 for name in mock_preset.shape.factor_names},
            metadata={"decision_id": f"archive-{index}"},
        )

    with caplog.at_level(logging.INFO, logger="copilot_sdk.scoring.scorer"):
        scorer._maybe_archive()

    assert "Archived" in caplog.text
    assert capsys.readouterr().out == ""
