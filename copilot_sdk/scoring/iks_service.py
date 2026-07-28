"""Service wrapper for SDK Institutional Knowledge Score computation."""

from __future__ import annotations

from typing import Any, Iterable

from copilot_sdk.scoring.trajectory import TrajectoryPoint, compute_trajectory


class IKSService:
    """Compute IKS summaries from verified decisions using canonical SDK trajectory logic."""

    def __init__(
        self,
        graph_store: Any,
        *,
        domain: str,
        shape: Any,
        categories: Iterable[str],
    ) -> None:
        self._graph_store = graph_store
        self._domain = str(domain)
        self._shape = shape
        self._categories = tuple(str(category) for category in categories)

    def summary(self) -> dict[str, Any]:
        decisions = self._verified_decisions()
        trajectory = compute_trajectory([], decisions, self._shape)
        return {
            "iks": float(trajectory.current_iks),
            "per_category": self._per_category(decisions),
            "trajectory": [_point_payload(point) for point in trajectory.points],
            "verified_count": len(decisions),
            "available": bool(decisions),
            "source": "graphstore",
        }

    def _per_category(self, decisions: list[dict[str, Any]]) -> dict[str, float]:
        output: dict[str, float] = {}
        for category in self._categories:
            scoped = [decision for decision in decisions if _decision_category(decision) == category]
            output[category] = float(compute_trajectory([], scoped, self._shape).current_iks)
        return output

    def _verified_decisions(self) -> list[dict[str, Any]]:
        rows = self._graph_store.get_verified_decisions(self._domain)
        return [
            _normalize_decision(row, index)
            for index, row in enumerate(rows)
            if isinstance(row, dict)
        ]


def _normalize_decision(decision: dict[str, Any], index: int) -> dict[str, Any]:
    output = dict(decision)
    output.setdefault("decision_id", f"decision-{index}")
    output.setdefault("created_at", float(index))
    return output


def _decision_category(decision: dict[str, Any]) -> str:
    raw_metadata = decision.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
    return str(decision.get("category") or metadata.get("category") or "")


def _point_payload(point: TrajectoryPoint) -> dict[str, float | int]:
    return {
        "decisions": point.decisions,
        "iks": point.iks,
        "win_rate": point.win_rate,
        "timestamp": point.timestamp,
    }
