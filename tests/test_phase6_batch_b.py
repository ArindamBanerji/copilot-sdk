from __future__ import annotations

import contextlib
import hashlib
import importlib
import io
import json
from types import SimpleNamespace

import numpy as np

from copilot_sdk.config.domains import ALL_COPILOT_DOMAINS
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.transfer import TransferPattern


def _scorer(domain: str) -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        domain,
        profile="test",
        graph_store=InMemoryGraphStore(domain=domain),
    )


def _pattern(
    domain: str = "soc",
    fingerprint_id: str | None = "fp-001",
    category: str | None = None,
    action: str | None = None,
    source_domain: str = "soc",
) -> TransferPattern:
    scorer = _scorer(domain)
    return TransferPattern(
        pattern_id=f"pattern-{fingerprint_id or 'missing'}-{domain}",
        source_copilot=source_domain,
        pattern_type="centroid_delta",
        category=category or scorer._preset.shape.category_names[0],
        action=action or scorer._preset.shape.action_names[0],
        win_rate=0.8,
        centroid_delta=[0.05] * scorer._preset.shape.n_factors,
        confidence=0.9,
        metadata={
            "source_domain": source_domain,
            **({"source_fingerprint_id": fingerprint_id} if fingerprint_id else {}),
            "factor_mapping": {"source_factor": "target_factor"},
        },
    )


def test_warm_start_emits_transfer_pattern() -> None:
    scorer = _scorer("trading")
    summary = scorer.warm_start([_pattern("trading")])

    rows = scorer.graph_store.get_transfer_patterns()
    assert summary["emitted"] == 1
    assert len(rows) == 1
    assert rows[0]["source_domain"] == "soc"
    assert rows[0]["target_domain"] == "trading"
    assert rows[0]["pattern_type"] == "factor_quality_transfer"
    assert rows[0]["pattern_id"].startswith("TP-")
    canonical_mapping = json.dumps(
        {"source_factor": "target_factor"},
        sort_keys=True,
        separators=(",", ":"),
    )
    expected_id = "TP-" + hashlib.sha256(
        f"soc|trading|factor_quality_transfer|fp-001||{canonical_mapping}".encode()
    ).hexdigest()[:32]
    assert rows[0]["pattern_id"] == expected_id
    assert rows[0]["source_rule"] is None
    assert rows[0]["evolution_event_id"] is None


def test_warm_start_skips_without_fingerprint_id() -> None:
    scorer = _scorer("trading")
    before = scorer.gae_scorer.centroids.copy()
    summary = scorer.warm_start([_pattern("trading", fingerprint_id=None)])

    assert summary["applied"] == 1
    assert summary["skipped"] == 1
    assert scorer.graph_store.get_transfer_patterns() == []
    assert not np.array_equal(before, scorer.gae_scorer.centroids)


def test_warm_start_partial_emission() -> None:
    scorer = _scorer("trading")
    patterns = [
        _pattern("trading", fingerprint_id="fp-1"),
        _pattern("trading", fingerprint_id="fp-2"),
        _pattern("trading", fingerprint_id=None),
    ]
    summary = scorer.warm_start(patterns)

    assert summary["applied"] == 3
    assert summary["emitted"] == 2
    assert summary["skipped"] == 1
    assert len(scorer.graph_store.get_transfer_patterns()) == 2


def test_warm_start_emission_failure_does_not_block(caplog) -> None:
    class FailingStore(InMemoryGraphStore):
        def write_transfer_pattern(self, *args, **kwargs):
            raise RuntimeError("transfer write failed")

    store = FailingStore(domain="trading")
    scorer = CompoundingScorer.from_preset("trading", profile="test", graph_store=store)
    before = scorer.gae_scorer.centroids.copy()
    with caplog.at_level("WARNING"):
        summary = scorer.warm_start([_pattern("trading")])

    assert summary["applied"] == 1
    assert summary["emission_errors"] == 1
    assert not np.array_equal(before, scorer.gae_scorer.centroids)
    assert "transfer_pattern" in caplog.text


def test_warm_start_idempotent_emission() -> None:
    scorer = _scorer("trading")
    pattern = _pattern("trading")
    scorer.warm_start([pattern])
    scorer.warm_start([pattern])

    assert len(scorer.graph_store.get_transfer_patterns()) == 1


def test_warm_start_all_five_domains() -> None:
    emitted = []
    for domain in ALL_COPILOT_DOMAINS:
        scorer = _scorer(domain)
        summary = scorer.warm_start([_pattern(domain, fingerprint_id=f"fp-{domain}")])
        emitted.append((domain, summary["emitted"], scorer.graph_store.get_transfer_patterns()))

    assert [domain for domain, count, _ in emitted if count == 1] == list(ALL_COPILOT_DOMAINS)
    assert {rows[0]["target_domain"] for _, _, rows in emitted} == set(ALL_COPILOT_DOMAINS)


def test_claim_runner_dry_run(capsys) -> None:
    runner = importlib.import_module("scripts.phase6_claim_proof")
    assert runner.main(["--age-dsn", "unused", "--dry-run"]) == 0
    output = capsys.readouterr().out
    assert "One engine, one graph" in output
    assert "MATCH (d:Decision)" in output


def test_claim_runner_structure() -> None:
    runner = importlib.import_module("scripts.phase6_claim_proof")
    assert len(runner.CLAIMS) == 8
    assert all({"id", "name", "query", "pass_condition"} <= set(claim) for claim in runner.CLAIMS)


def test_demo_status_config_line(monkeypatch) -> None:
    demo = importlib.import_module("demo")
    monkeypatch.setattr(
        demo.GraphConfig,
        "load",
        staticmethod(lambda domain, profile="production": SimpleNamespace(graph="soc_graph")),
    )
    assert "Shared judgment graph  soc_graph" in demo._shared_graph_config_line()
    assert all(domain in demo._shared_graph_config_line() for domain in ALL_COPILOT_DOMAINS)


def test_demo_status_unavailable(monkeypatch) -> None:
    demo = importlib.import_module("demo")
    monkeypatch.setattr(demo, "verify_age", lambda dsn: False)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        demo.cmd_status([])
    text = output.getvalue()
    assert "UNAVAILABLE" in text
    assert "decisions=0" not in text
