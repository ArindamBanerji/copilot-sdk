from __future__ import annotations

from typing import Any

from copilot_sdk.graph.read_diff_runner import ReadDiffRunner


class ReadStore:  # MOCK-OK: read-only GraphStore comparison boundary fixture.
    def __init__(
        self,
        decisions: list[dict[str, Any]],
        *,
        verified: int | None = None,
        correct: int | None = None,
        total: int | None = None,
    ) -> None:
        self.decisions = decisions
        self.verified = len(decisions) if verified is None else verified
        self.correct = self.verified if correct is None else correct
        self.total = self.verified if total is None else total
        self.verified_calls = 0

    def count_verified(self, domain: str) -> int:
        return self.verified

    def count_correct(self, domain: str) -> int:
        return self.correct

    def count_decisions(self, domain: str) -> int:
        return self.total

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        self.verified_calls += 1
        return list(self.decisions)


def _decision(decision_id: str, **overrides: Any) -> dict[str, Any]:
    decision: dict[str, Any] = {
        "decision_id": decision_id,
        "domain": "trading",
        "category": "equity",
        "category_index": 1,
        "recommended_action": "buy",
        "recommended_index": 0,
        "confidence": 0.85,
        "factor_vector": [0.1, 0.2],
        "probabilities": [0.85, 0.15],
        "status": "confirmed",
        "metadata": {"source": "test"},
        "created_at": 1.0,
        "is_correct": True,
        "actual_action": "buy",
    }
    decision.update(overrides)
    return decision


def _run(primary: ReadStore, secondary: ReadStore):
    return ReadDiffRunner(primary, secondary, "trading").run_diff()


def test_counts_match_passes():
    decisions = [_decision(f"d{index}") for index in range(5)]
    assert _run(ReadStore(decisions), ReadStore(decisions)).passed is True


def test_count_mismatch_fails_and_skips_level_two():
    primary = ReadStore([_decision(f"d{index}") for index in range(5)])
    secondary = ReadStore([_decision(f"d{index}") for index in range(3)])
    report = _run(primary, secondary)
    assert report.count_match is False
    assert report.passed is False
    assert primary.verified_calls == secondary.verified_calls == 0


def test_correct_count_mismatch_fails():
    decisions = [_decision("d1")]
    report = _run(ReadStore(decisions, correct=1), ReadStore(decisions, correct=0))
    assert report.correct_match is False
    assert report.passed is False


def test_total_count_mismatch_fails():
    decisions = [_decision("d1")]
    report = _run(ReadStore(decisions, total=2), ReadStore(decisions, total=1))
    assert report.total_match is False
    assert report.passed is False


def test_missing_in_secondary_is_reported_when_level_one_counts_match():
    primary = ReadStore([_decision("d1"), _decision("d2")], verified=2)
    secondary = ReadStore([_decision("d1")], verified=2)
    report = _run(primary, secondary)
    assert report.missing_in_secondary == ["d2"]
    assert report.passed is False


def test_missing_in_primary_is_reported_when_level_one_counts_match():
    primary = ReadStore([_decision("d1")], verified=2)
    secondary = ReadStore([_decision("d1"), _decision("d2")], verified=2)
    report = _run(primary, secondary)
    assert report.missing_in_primary == ["d2"]
    assert report.passed is False


def test_confidence_field_mismatch_is_captured():
    report = _run(ReadStore([_decision("d1")]), ReadStore([_decision("d1", confidence=0.7)]))
    assert report.field_mismatches == [{"decision_id": "d1", "field": "confidence", "primary": 0.85, "secondary": 0.7}]


def test_status_mismatch_is_captured():
    report = _run(ReadStore([_decision("d1")]), ReadStore([_decision("d1", status="overridden")]))
    assert any(mismatch["field"] == "status" for mismatch in report.field_mismatches)


def test_float_tolerance_treats_nearby_values_as_equal():
    report = _run(ReadStore([_decision("d1")]), ReadStore([_decision("d1", confidence=0.8500001)]))
    assert report.passed is True


def test_none_and_missing_fields_match():
    primary = _decision("d1", metadata=None)
    secondary = _decision("d1")
    secondary.pop("metadata")
    assert _run(ReadStore([primary]), ReadStore([secondary])).passed is True


def test_json_metadata_and_embedded_outcome_are_normalized():
    primary = _decision("d1", metadata={"source": "test"}, actual_action="buy", is_correct=True)
    secondary = _decision("d1", metadata='{"source":"test"}')
    secondary.pop("actual_action")
    secondary.pop("is_correct")
    secondary["outcome"] = {"actual_action": "buy", "is_correct": True}
    assert _run(ReadStore([primary]), ReadStore([secondary])).passed is True


def test_all_match_summary_contains_pass():
    decisions = [_decision(f"d{index}") for index in range(10)]
    report = _run(ReadStore(decisions), ReadStore(decisions))
    assert report.passed is True
    assert "PASS" in report.summary()


def test_empty_stores_pass():
    assert _run(ReadStore([]), ReadStore([])).passed is True
