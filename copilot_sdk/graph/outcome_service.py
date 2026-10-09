"""Protocol-V2 canonical outcome commits and conservation accounting."""

from __future__ import annotations

from typing import Any, Callable, Protocol, cast

from copilot_sdk.graph.protocol import L5LearningStore, ProtocolV2GraphStore


OutcomeWriter = Callable[..., None]


class ProtocolV2OutcomeStore(ProtocolV2GraphStore, L5LearningStore, Protocol):
    """Protocol V2 graph API plus optional legacy L5 state compatibility."""


class ProtocolV2OutcomeService:
    """Commit verified outcomes and account for V after canonical persistence.

    The optional writer selects the canonical persistence endpoint. Persistence
    and validation failures propagate to the caller; this service does not queue
    secondary writes or report a failed commit as pending synchronization.
    """

    def __init__(
        self,
        store: ProtocolV2OutcomeStore,
        *,
        domain: str,
        canonical_writer: OutcomeWriter | None = None,
    ) -> None:
        self.store = store
        self.domain = str(domain)
        self._canonical_writer = canonical_writer or store.write_outcome

    def set_canonical_writer(self, writer: OutcomeWriter) -> None:
        """Install the canonical endpoint used by subsequent commit attempts."""
        self._canonical_writer = writer

    def learn(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self._payload(decision_id, actual_action, is_correct, metadata)
        V = self._commit(payload)
        return {
            "status": "committed",
            "canonical_committed": True,
            "decision_id": decision_id,
            "V": V,
        }

    def _commit(self, payload: dict[str, Any]) -> int:
        before = self.store.count_verified_decisions(self.domain)
        self._canonical_writer(*payload["args"], **payload["kwargs"])
        after = self.store.count_verified_decisions(self.domain)
        if after <= before:
            return self._current_v()
        state = self._state()
        next_V = cast(int, int(state["V"]) + (after - before))
        self.store.write_conservation_status(
            f"{self.domain}:{payload['args'][0]}:{next_V}",
            self.domain,
            next_V,
            float(state["q"]),
            float(state["alpha"]),
            float(state["theta_min"]),
            int(state.get("verified_count", 0)) + (after - before),
            int(state.get("correct_count", 0)),
            str(state["status"]),
            str(state.get("policy_version", "protocol-v2")),
        )
        self.store.update_conservation_state(
            self.domain,
            str(state["status"]),
            float(state.get("alpha", 0.0)),
            float(state["q"]),
            next_V,
            float(state["theta_min"]),
            float(state.get("product", 0.0)),
            int(state.get("categories_total", 0)),
            int(state.get("categories_with_data", 0)),
            float(state.get("baseline_product", 0.0)),
            float(state.get("relative_threshold", 0.0)),
            str(state.get("complacency_flag", "false")),
            caused_by_decision_id=str(payload["args"][0]),
            old_status=str(state["status"]),
        )
        return next_V

    def _current_v(self) -> int:
        return cast(int, int(self._state()["V"]))

    def _state(self) -> dict[str, Any]:
        legacy_state = self.store.get_conservation_state(self.domain)
        if legacy_state is not None:
            return dict(legacy_state)
        states = self.store.get_latest_conservation_statuses([self.domain])
        if not states:
            raise RuntimeError(f"missing conservation state for {self.domain}")
        state = dict(states[0])
        state.setdefault("verified_count", 0)
        state.setdefault("correct_count", 0)
        state.setdefault("policy_version", "protocol-v2")
        return state

    def _payload(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "args": (str(decision_id), str(actual_action), bool(is_correct)),
            "kwargs": {"metadata": dict(metadata or {}), "domain": self.domain},
        }
