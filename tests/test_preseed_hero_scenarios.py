"""Synthetic hero patterns and fail-closed HTTP orchestration, without live APIs."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import demo
from copilot_sdk.scoring.fingerprint import compute_fingerprint
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.trust_traps import TrustTrapDetector
from scripts import hero_moments, loom_gauntlet
from scripts import preseed_all_copilots as base_preseed
from scripts import preseed_hero_scenarios as heroes


@pytest.mark.parametrize("domain,count", [("trading", 40), ("purchasing", 30), ("dataops", 20), ("s2p", 30)])
def test_patterns_use_actual_presets(domain: str, count: int) -> None:
    rows = heroes.hero_decisions(domain)
    shape = PRESET_REGISTRY[domain]().shape
    assert len(rows) == count <= 40
    assert len({row["metadata"]["hero_id"] for row in rows}) == count
    for row in rows:
        assert row["category"] in shape.category_names
        assert set(row["factors"]) == set(shape.factor_names)
        assert all(0 <= value <= 1 for value in row["factors"].values())
        assert row["metadata"]["planted"] is True
        assert row["metadata"]["evidence_tier"] == "T-sim"


def test_determinism_and_fresh_decisions() -> None:
    for domain in heroes.DOMAINS:
        first, second = heroes.hero_decisions(domain), heroes.hero_decisions(domain)
        assert first == second
        first[0]["factors"].clear()
        assert second == heroes.hero_decisions(domain)


@pytest.mark.parametrize("domain,trusted,useful", [
    ("trading", "signal_alignment", "timing_quality"),
    ("purchasing", "supplier_lead_time", "historical_waste"),
])
def test_trust_pattern_has_precision_accuracy_divergence(domain: str, trusted: str, useful: str) -> None:
    rows = heroes.hero_decisions(domain)
    names = list(PRESET_REGISTRY[domain]().shape.factor_names)
    decisions = [{"category": row["category"], "is_correct": row["correct"],
                  "factor_vector": [row["factors"][name] for name in names]} for row in rows]
    fingerprint = compute_fingerprint(decisions, names)
    weights = {factor.name: factor.weight for factor in fingerprint.factors}
    assert weights[trusted] > weights[useful]
    assert weights[trusted] == max(weights.values())
    useful_accuracy = sum((row["factors"][useful] > 0.5) == row["correct"] for row in rows) / len(rows)
    center = 0.5 if domain == "trading" else 0.85
    trusted_accuracy = sum((row["factors"][trusted] > center) == row["correct"] for row in rows) / len(rows)
    assert useful_accuracy == 1.0
    assert useful_accuracy - trusted_accuracy > 0.2
    if domain == "purchasing":
        assert all(row["factors"][trusted] > 0.8 for row in rows if not row["correct"])
    check = heroes._trading_weights if domain == "trading" else heroes._purchasing_weights
    assert check(asdict(fingerprint))


@pytest.mark.parametrize("domain", ["trading", "purchasing"])
def test_actual_detector_finds_category_divergence(domain: str) -> None:
    rows = [{"category": row["category"], "is_correct": row["correct"]}
            for row in heroes.hero_decisions(domain)]
    store = SimpleNamespace(get_verified_decisions=lambda _domain: rows)
    assert "CATEGORY_DIVERGENCE" in {trap.trap_type for trap in TrustTrapDetector(None, store, domain).scan()}


def test_s2p_triage_ratios_and_supplier_clustering() -> None:
    rows = heroes.hero_decisions("s2p")
    for category, approves in (("price_variance", 8), ("duplicate_risk", 3), ("contract_gap", 5)):
        selected = [row for row in rows if row["category"] == category]
        assert len(selected) == 10
        assert sum(row["actual_action"] == "auto_approve" for row in selected) == approves
    for row in rows:
        supplier = int(row["metadata"]["supplier_id"].split("-")[1])
        assert (supplier <= 3) == (row["actual_action"] == "auto_approve")


def _transport(monkeypatch: pytest.MonkeyPatch, *, status: str = "GREEN") -> list[tuple[str, dict[str, Any]]]:
    calls: list[tuple[str, dict[str, Any]]] = []

    def get(_url: str, path: str) -> dict[str, Any]:
        if path == "/api/conservation/status":
            return {"status": status, "passed": status == "GREEN"}
        if path == "/api/trajectory":
            return {"decisions_total": 200, "current_iks": 30}
        if path == "/api/context/bottleneck/warehouse_etl":
            return {"bottleneck": {"system": "warehouse_etl"}, "all_steps_ranked": [{"step": "load"}]}
        return {}

    def post(_url: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        calls.append((path, body))
        if path == "/api/learn":
            return {"outcome": "applied", "status": "complete", "decision_id": body["decision_id"]}
        return {"decision_id": f"decision-{len(calls)}", "action": "auto_approve"}

    monkeypatch.setattr(heroes, "api_get", get)
    monkeypatch.setattr(heroes, "api_post", post)
    return calls


def test_conservation_blocks_before_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _transport(monkeypatch, status="AMBER")
    report = heroes.seed_hero("trading", "http://test", journal_dir=tmp_path)
    assert report["status"] == "not_ready"
    assert "AMBER" in report["errors"][0]
    assert report["checks"]
    assert calls == []


def test_journal_prevents_second_batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _transport(monkeypatch)
    first = heroes.seed_hero("dataops", "http://test", journal_dir=tmp_path)
    second = heroes.seed_hero("dataops", "http://test", journal_dir=tmp_path)
    assert first["seeded"] == 20
    assert second["seeded"] == 0 and second["skipped"] == 20
    assert len(calls) == 40
    assert first["checks"]["bottleneck_prerequisite"]["passed"] is True
    assert first["status"] == second["status"] == "not_ready"


@pytest.mark.parametrize("payload", [{}, {"bottleneck": None}, {"bottleneck": {}, "all_steps_ranked": []}])
def test_dataops_prerequisite_prevents_all_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any],
) -> None:
    calls = _transport(monkeypatch)
    get = heroes.api_get

    def missing(url: str, path: str) -> Any:
        return payload if path == "/api/context/bottleneck/warehouse_etl" else get(url, path)

    monkeypatch.setattr(heroes, "api_get", missing)
    result = heroes.seed_hero("dataops", "http://test", journal_dir=tmp_path)
    assert result["status"] == "prerequisite_not_met"
    assert result["seeded"] == 0
    assert result["errors"] == []
    assert result["prerequisites"] == ["DataOps bottleneck prerequisite is not met; no seed writes sent"]
    assert calls == []
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("error", ["HTTP 423 Conservation locked", "timed out after possible commit"])
def test_failed_write_is_not_retried(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: str) -> None:
    _transport(monkeypatch)
    calls: list[str] = []

    def post(_url: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        calls.append(path)
        if path == "/api/score":
            return {"decision_id": "one", "action": "investigate"}
        raise heroes.ApiError(error)

    monkeypatch.setattr(heroes, "api_post", post)
    first = heroes.seed_hero("dataops", "http://test", journal_dir=tmp_path)
    second = heroes.seed_hero("dataops", "http://test", journal_dir=tmp_path)
    assert error in first["errors"][0]
    assert "Unfinished write" in second["errors"][0]
    assert calls == ["/api/score", "/api/learn"]


def test_already_ready_state_skips_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _transport(monkeypatch)
    monkeypatch.setattr(heroes, "verify_hero_state", lambda *_args: {"existing": {"passed": True}})
    assert heroes.seed_hero("trading", "http://test", journal_dir=tmp_path)["status"] == "already_ready"
    assert calls == []


def test_verification_pass_fail_and_transport_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def get(_url: str, path: str) -> dict[str, Any]:
        if path == "/error":
            raise heroes.ApiError("HTTP 503")
        return {"status": "GREEN" if path == "/pass" else "AMBER", "passed": path == "/pass"}

    monkeypatch.setattr(heroes, "api_get", get)
    checks = [(name, path, heroes._green) for name, path in (("yes", "/pass"), ("no", "/fail"), ("error", "/error"))]
    result = heroes.verify_hero_state("trading", "http://test", checks)
    assert result["yes"]["passed"] is True
    assert result["no"]["passed"] is False
    assert result["error"]["passed"] is False
    assert "503" in result["error"]["error"]


def test_s2p_final_cohort_remains_pending(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _transport(monkeypatch)
    get = heroes.api_get

    def get_s2p(url: str, path: str) -> dict[str, Any]:
        assert path != "/api/trajectory", "S2P does not expose generic trajectory"
        return dict(get(url, path))

    monkeypatch.setattr(heroes, "api_get", get_s2p)
    report = heroes.seed_hero("s2p", "http://test", journal_dir=tmp_path)
    assert report["seeded"] == 30
    assert all(path == "/api/s2p/score" for path, _body in calls)
    assert all(body["context"]["planted"] for _path, body in calls)


def test_cli_integration_is_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    assert demo.create_parser().parse_args(["--preseed", "--heroes"]).heroes
    assert not demo.create_parser().parse_args(["--preseed"]).heroes
    assert hero_moments.parse_args(["--all", "--heroes"]).heroes
    assert loom_gauntlet.parse_args(["--heroes"]).heroes
    assert base_preseed.parse_args(["--heroes"]).heroes
    with pytest.raises(SystemExit):
        base_preseed.parse_args(["--heroes", "--demo-fixtures"])
    events: list[str] = []

    def seed(_selected: set[str]) -> int:
        events.append("seed")
        return 0

    def beat(name: str, _port: int, phase: str) -> hero_moments.HeroResult:
        events.append(phase)
        return hero_moments.HeroResult(phase, name, "completed", "done")

    def verify(_domain: str, _url: str) -> dict[str, Any]:
        events.append("verify")
        return {"check": {"passed": True}}

    monkeypatch.setattr(heroes, "run_heroes", seed)
    monkeypatch.setattr(heroes, "verify_hero_state", verify)
    monkeypatch.setattr(hero_moments, "run", beat)
    assert hero_moments.main(["--copilot", "trading", "--beat", "c2", "--heroes"]) == 0
    assert events == ["seed", "c2", "verify"]
    selected_domains: list[set[str]] = []

    def seed_selected(selected: set[str]) -> int:
        selected_domains.append(selected)
        return 0

    monkeypatch.setattr(heroes, "run_heroes", seed_selected)
    monkeypatch.setattr(base_preseed, "seed_s2p_domain", lambda _args: base_preseed.DomainResult("s2p", 0, 0, 0, 0, True, False, 0.0))
    assert base_preseed.main(["--s2p-only", "--heroes", "--dry-run"]) == 0
    assert selected_domains == []
    assert base_preseed.main(["--s2p-only", "--heroes"]) == 0
    assert selected_domains == [{"s2p"}]


def test_verify_only_cli_never_posts(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _transport(monkeypatch)
    assert heroes.main(["--domains", "dataops", "--verify-only"]) == 1
    assert calls == []


def test_queue_verifies_own_cohort_not_unrelated_actions() -> None:
    assert not heroes._queue({"exceptions": [{"recommended_action": action} for action in ("auto_approve", "hold_for_review")]})
    rows = [{"invoice_id": row["metadata"]["hero_id"], "supplier_id": row["metadata"]["supplier_id"],
             "recommended_action": row["actual_action"]} for row in heroes.hero_decisions("s2p")]
    assert heroes._queue({"exceptions": rows})
    rows[0]["recommended_action"] = "hold_for_review"
    assert not heroes._queue({"exceptions": rows})


def test_http_200_pause_is_not_counted_as_learning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _transport(monkeypatch)
    post = heroes.api_post

    def paused(url: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        response = post(url, path, body)
        if path == "/api/learn":
            response["paused"] = True
        return dict(response)

    monkeypatch.setattr(heroes, "api_post", paused)
    result = heroes.seed_hero("dataops", "http://test", journal_dir=tmp_path)
    assert result["seeded"] == 0
    assert result["status"] == "not_ready"
    assert len(calls) == 2


@pytest.mark.parametrize("domain", ["trading", "purchasing"])
def test_hero_sequence_learns_under_real_conservation(domain: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COPILOT_PRESEED_MODE", raising=False)
    monkeypatch.setenv("CI_PERSISTENCE_OUTBOX_PATH", str(tmp_path / "outbox.db"))
    scorer = CompoundingScorer.from_preset(domain, profile="test")
    shape = PRESET_REGISTRY[domain]().shape
    for index in range(200):
        score = scorer.score({name: 0.3 + (index % 7) * 0.08 for name in shape.factor_names},
                             shape.category_names[index % shape.n_categories])
        # Keep this integration sequence above the 0.75 recent-quality boundary.
        # Windows can assign equal timestamps to adjacent decisions, whose stable-ID
        # tie-breaker legitimately changes which boundary record enters the window.
        correct = index % 5 != 4
        action = score.action if correct else next(value for value in shape.action_names if value != score.action)
        assert not isinstance(scorer.learn(score.decision_id, action, "confirmed" if correct else "overridden"), dict)

    def post(_url: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if path == "/api/score":
            return dict(asdict(scorer.score(body["factors"], body["category"], metadata=body["metadata"])))
        assert path == "/api/learn"
        result = scorer.learn(body["decision_id"], body["actual_action"], body["outcome"], context=body["context"])
        return result if isinstance(result, dict) else dict(asdict(result))

    def get(_url: str, path: str) -> dict[str, Any]:
        if path == "/api/conservation/status":
            return dict(scorer.get_conservation_state())
        if path == "/api/trajectory":
            return {"decisions_total": scorer.get_verified_count()}
        return {}

    monkeypatch.setattr(heroes, "api_get", get)
    monkeypatch.setattr(heroes, "api_post", post)
    result = heroes.seed_hero(domain, "http://in-memory", journal_dir=tmp_path)
    count = len(heroes.hero_decisions(domain))
    assert result["errors"] == []
    assert result["seeded"] == count
    assert scorer.get_verified_count() == 200 + count
