from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "verify_l5_completion.py"
spec = importlib.util.spec_from_file_location("verify_l5_completion", SCRIPT_PATH)
assert spec and spec.loader
l5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(l5)


class FakeResult:
    def __init__(self, rows: list[tuple[Any, ...]]):
        self._rows = rows

    def fetchone(self) -> tuple[Any, ...] | None:
        return self._rows[0] if self._rows else None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self._rows


class FakeConnection:
    def __init__(
        self,
        *,
        centroids: list[dict[str, Any]],
        dk_weights: list[dict[str, Any]],
        conservation: list[dict[str, Any]],
        edges: dict[str, int] | None = None,
    ):
        self._props = {
            "L5Centroid": centroids,
            "L5DKWeight": dk_weights,
            "L5ConservationState": conservation,
        }
        self._edges = edges or {"SHAPED_BY": 4, "TRIGGERED_BY": 3}
        self.closed = False

    def execute(self, query: str) -> FakeResult:
        for label, rows in self._props.items():
            if f"MATCH (n:{label})" in query and "RETURN count(n)" in query:
                return FakeResult([(len(rows),)])
            if f"MATCH (n:{label})" in query and "RETURN properties(n)" in query:
                return FakeResult([(json.dumps(row),) for row in rows])
        for rel, count in self._edges.items():
            if f"[r:{rel}]" in query:
                return FakeResult([(count,)])
        return FakeResult([])

    def close(self) -> None:
        self.closed = True


def centroid(category: str = "credential_access", values: list[float] | None = None, ts: float = 1.0):
    return {
        "category": category,
        "action": "investigate",
        "vector_json": json.dumps(values or [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]),
        "updated_at_epoch": ts,
    }


def dk_weight(category: str = "credential_access", weights: list[list[float]] | None = None, ts: float = 2.0):
    return {
        "category": category,
        "weight_json": json.dumps(weights or [[0.5, 0.6, 0.7]]),
        "mean": 0.5,
        "M2": 0.1,
        "count": 210,
        "computed_at": ts,
    }


def conservation(alpha: float = 0.5, volume: float = 100.0, ts: float = 3.0):
    return {
        "alpha": alpha,
        "V": volume,
        "status": "GREEN",
        "updated_at_epoch": ts,
    }


def make_proof(
    *,
    centroids: list[dict[str, Any]] | None = None,
    dk_weights: list[dict[str, Any]] | None = None,
    conservation_rows: list[dict[str, Any]] | None = None,
    edges: dict[str, int] | None = None,
):
    proof = l5.L5CompletionProof()
    proof._conn = FakeConnection(
        centroids=centroids if centroids is not None else [centroid(ts=float(i)) for i in range(1, 9)],
        dk_weights=dk_weights if dk_weights is not None else [dk_weight(ts=float(i)) for i in range(9, 12)],
        conservation=conservation_rows
        if conservation_rows is not None
        else [conservation(ts=float(i)) for i in range(12, 16)],
        edges=edges,
    )
    return proof


def test_verify_returns_expected_shape():
    result = make_proof().verify()

    assert {
        "total_expected",
        "l5_centroids",
        "l5_dk_weights",
        "l5_conservation",
        "l5_edges",
        "l5_welford",
        "l5_timestamps",
        "total_found",
        "complete",
        "missing_cells",
        "invalid_cells",
        "proof_status",
    } <= set(result)


def test_proof_status_complete():
    assert make_proof().verify()["proof_status"] == "COMPLETE"


def test_proof_status_incomplete():
    result = make_proof(
        centroids=[centroid() for _ in range(5)],
        dk_weights=[dk_weight() for _ in range(3)],
        conservation_rows=[conservation() for _ in range(2)],
    ).verify()

    assert result["total_found"] == 10
    assert result["proof_status"] == "INCOMPLETE"


def test_proof_status_invalid():
    result = make_proof(centroids=[centroid(values=[1.2])] + [centroid() for _ in range(7)]).verify()

    assert result["proof_status"] == "INVALID"
    assert any("L5Centroid" in item for item in result["invalid_cells"])


def test_missing_dk_weights():
    result = make_proof(
        centroids=[centroid() for _ in range(12)],
        dk_weights=[],
        conservation_rows=[conservation() for _ in range(3)],
    ).verify()

    assert any("L5DKWeight" in item for item in result["missing_cells"])


def test_invalid_conservation_alpha():
    result = make_proof(conservation_rows=[conservation(alpha=1.5)] + [conservation() for _ in range(3)]).verify()

    assert any("alpha=1.5" in item for item in result["invalid_cells"])


def test_conservation_negative_v():
    result = make_proof(conservation_rows=[conservation(volume=-1)] + [conservation() for _ in range(3)]).verify()

    assert any("V=-1" in item for item in result["invalid_cells"])


def test_edges_all_linked():
    result = make_proof(edges={"SHAPED_BY": 5, "TRIGGERED_BY": 3})._verify_edges()

    assert result["all_linked"] is True


def test_edges_missing():
    result = make_proof(edges={"SHAPED_BY": 0, "TRIGGERED_BY": 3})._verify_edges()

    assert result["all_linked"] is False


def test_welford_present():
    result = make_proof(dk_weights=[dk_weight()])._verify_welford_fields()

    assert result["all_valid"] is True


def test_welford_missing_fields():
    bad = {"category": "credential_access", "weight_json": "[[0.5]]", "mean": 0.5, "count": 10}
    result = make_proof(dk_weights=[bad])._verify_welford_fields()

    assert result["all_valid"] is False
    assert result["missing_welford"]


def test_timestamps_sequential():
    result = make_proof(
        centroids=[centroid(ts=1), centroid(ts=2), centroid(ts=3)],
        dk_weights=[],
        conservation_rows=[],
    )._verify_timestamp_ordering()

    assert result["sequential"] is True


def test_timestamps_out_of_order():
    result = make_proof(
        centroids=[centroid(ts=1), centroid(ts=3), centroid(ts=2)],
        dk_weights=[],
        conservation_rows=[],
    )._verify_timestamp_ordering()

    assert result["sequential"] is False


def test_no_age_graceful(monkeypatch, capsys):
    def fail_connect(self):
        raise RuntimeError("boom")

    monkeypatch.setattr(l5.L5CompletionProof, "connect", fail_connect)

    with pytest.raises(SystemExit) as exc:
        l5.main(["--json"])

    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["proof_status"] == "AGE_UNAVAILABLE"
    assert "boom" in payload["error"]


def test_json_output(monkeypatch, capsys):
    monkeypatch.setattr(l5.L5CompletionProof, "connect", lambda self: None)
    monkeypatch.setattr(l5.L5CompletionProof, "close", lambda self: None)
    monkeypatch.setattr(
        l5.L5CompletionProof,
        "verify",
        lambda self: {
            "proof_status": "COMPLETE",
            "total_found": 15,
            "total_expected": 15,
            "l5_centroids": {"count": 8},
            "l5_dk_weights": {"count": 3},
            "l5_conservation": {"count": 4},
            "l5_edges": {"SHAPED_BY": 1, "TRIGGERED_BY": 1},
            "l5_welford": {"all_valid": True},
            "l5_timestamps": {"sequential": True},
            "missing_cells": [],
            "invalid_cells": [],
        },
    )

    with pytest.raises(SystemExit) as exc:
        l5.main(["--json"])

    assert exc.value.code == 0
    assert json.loads(capsys.readouterr().out)["proof_status"] == "COMPLETE"


def test_cli_exit_codes(monkeypatch):
    monkeypatch.setattr(l5.L5CompletionProof, "connect", lambda self: None)
    monkeypatch.setattr(l5.L5CompletionProof, "close", lambda self: None)
    monkeypatch.setattr(
        l5.L5CompletionProof,
        "verify",
        lambda self: {
            "proof_status": "COMPLETE",
            "total_found": 15,
            "total_expected": 15,
            "l5_centroids": {"count": 8},
            "l5_dk_weights": {"count": 3},
            "l5_conservation": {"count": 4},
            "l5_edges": {"SHAPED_BY": 1, "TRIGGERED_BY": 1},
            "l5_welford": {"all_valid": True},
            "l5_timestamps": {"sequential": True},
            "missing_cells": [],
            "invalid_cells": [],
        },
    )

    with pytest.raises(SystemExit) as complete:
        l5.main([])
    assert complete.value.code == 0

    monkeypatch.setattr(l5.L5CompletionProof, "verify", lambda self: {"proof_status": "INCOMPLETE"})
    with pytest.raises(SystemExit) as incomplete:
        l5.main(["--json"])
    assert incomplete.value.code == 1
