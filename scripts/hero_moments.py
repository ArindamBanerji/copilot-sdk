"""Run the four B31 demo hero moments against live copilot APIs.

The runner is deliberately stdlib-only and truth-preserving.  It captures
before/after payloads, labels evidence, and reports ``unsupported`` or
``unavailable`` when a backend does not expose the required contract.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable
from urllib import error, request


COPILOTS = {
    "soc": 8001,
    "s2p": 8002,
    "trading": 8010,
    "purchasing": 8020,
    "dataops": 8030,
}

BEATS = ("c2", "c3", "c4", "c5")
TIMEOUT_SECONDS = 10


class HeroApiError(RuntimeError):
    """A live API call failed and the beat cannot be claimed."""


@dataclass
class HeroResult:
    beat: str
    copilot: str
    status: str
    message: str
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ApiClient:
    def __init__(self, base_url: str, timeout: int = TIMEOUT_SECONDS) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self._request("POST", path, payload)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = request.Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise HeroApiError(f"{method} {path}: {exc}") from exc

    def first(self, paths: Iterable[str]) -> tuple[str, Any] | None:
        for path in paths:
            try:
                return path, self.get(path)
            except HeroApiError:
                continue
        return None

    def first_post(self, calls: Iterable[tuple[str, dict[str, Any] | None]]) -> tuple[str, Any] | None:
        for path, payload in calls:
            try:
                return path, self.post(path, payload)
            except HeroApiError:
                continue
        return None


class HeroRunner:
    def __init__(self, copilot: str, port: int) -> None:
        self.copilot = copilot
        self.port = port
        self.client = ApiClient(os.environ.get(f"{copilot.upper()}_URL", f"http://127.0.0.1:{port}"))
        self._reachable: bool | None = None

    def backend_available(self) -> bool:
        if self._reachable is None:
            try:
                self.client.get("/health")
                self._reachable = True
            except HeroApiError:
                self._reachable = False
        return self._reachable

    def state(self) -> dict[str, Any]:
        if not self.backend_available():
            return {}
        state: dict[str, Any] = {}
        for key, paths in {
            "trajectory": ("/api/trajectory", "/api/s2p/trajectory", "/api/soc/learning-health"),
            "conservation": ("/api/conservation/status", "/api/soc/learning-health", "/api/trajectory"),
            "twin": ("/api/twin/status", "/api/frozen-twin/status", "/api/soc/learning/frozen-comparison"),
            "promotion": (
                "/api/trading/promotion/dashboard",
                "/api/promotion",
                "/api/purchasing/promotion",
                "/api/dataops/promotion",
            ),
        }.items():
            result = self.client.first(paths)
            if result is not None:
                state[key] = {"path": result[0], "payload": result[1]}
        return state

    def c2_score_learn(self) -> HeroResult:
        before = self.state()
        if not self.backend_available():
            return _result("c2", self.copilot, "unavailable", "Backend health endpoint is unavailable.", before, before)
        score_payload = _score_payload(self.client, self.copilot)
        score_paths = ("/api/s2p/score", "/api/score") if self.copilot == "s2p" else ("/api/score",)
        score_call = self.client.first_post((path, score_payload) for path in score_paths)
        if score_call is None:
            return _result("c2", self.copilot, "unsupported", "No score endpoint accepted the hero request.", before, before)
        score_path, score = score_call
        decision_id = score.get("decision_id") if isinstance(score, dict) else None
        if not decision_id:
            return _result("c2", self.copilot, "blocked", "Score response did not expose a decision identity.", before, before, [{"path": score_path, "payload": score}])
        action = _action_for_score(score, self.copilot)
        learn = self.client.first_post(
            (path, {"decision_id": decision_id, "actual_action": action, "outcome": "confirmed", "context": {"hero_moment": "B31-C2"}})
            for path in ("/api/learn", "/api/outcome")
        )
        if learn is None:
            return _result("c2", self.copilot, "unsupported", "Score succeeded, but no compatible learn/outcome endpoint was available.", before, self.state(), [{"path": score_path, "payload": score}])
        after = self.state()
        before_iks = _find_number(before, ("current_iks", "iks", "intelligence_knowledge_score"))
        after_iks = _find_number(after, ("current_iks", "iks", "intelligence_knowledge_score"))
        delta = None if before_iks is None or after_iks is None else after_iks - before_iks
        status = "measured" if delta is not None and delta > 0 else "completed"
        message = "Verified score→learn completed; IKS increased." if status == "measured" else "Verified score→learn completed; the backend did not expose a positive IKS delta."
        return _result("c2", self.copilot, status, message, before, after, [{"path": score_path, "payload": score}, {"path": learn[0], "payload": learn[1]}], {"iks_before": before_iks, "iks_after": after_iks, "iks_delta": delta})

    def c3_twin_improvement(self) -> HeroResult:
        before = self.state()
        if not self.backend_available():
            return _result("c3", self.copilot, "unavailable", "Backend health endpoint is unavailable.", before, before)
        twin = before.get("twin")
        if twin is None:
            return _result("c3", self.copilot, "unsupported", "No Frozen Twin status endpoint is available.", before, before)
        after = self.state()
        before_drift = _find_number(before, ("centroid_drift", "iks_delta", "delta", "improvement"))
        after_drift = _find_number(after, ("centroid_drift", "iks_delta", "delta", "improvement"))
        delta = None if before_drift is None or after_drift is None else after_drift - before_drift
        status = "measured" if delta is not None and delta > 0 else "available"
        message = "Frozen Twin comparison is available; measured live-vs-frozen improvement is visible." if status == "measured" else "Frozen Twin is available, but a non-zero improvement delta was not exposed by the read-only API."
        return _result("c3", self.copilot, status, message, before, after, [{"path": twin["path"], "payload": twin["payload"]}], {"twin_delta_before": before_drift, "twin_delta_after": after_drift, "twin_delta": delta})

    def c4_promotion_earned(self) -> HeroResult:
        before = self.state()
        if not self.backend_available():
            return _result("c4", self.copilot, "unavailable", "Backend health endpoint is unavailable.", before, before)
        call = self.client.first_post(
            (path, {"category": "demo", "hero_moment": "B31-C4"})
            for path in ("/api/evolution/check-promotion", "/api/promotion/check", "/api/trading/promotion/check")
        )
        after = self.state()
        if call is None:
            return _result("c4", self.copilot, "unsupported", "No promotion-check endpoint is available for this copilot.", before, after)
        promoted = _has_truth(call[1], ("promoted", "advanced", "promotion_earned"))
        status = "measured" if promoted else "blocked"
        message = "Promotion advancement was reported by the live gate." if promoted else "Promotion gate responded, but did not report advancement."
        return _result("c4", self.copilot, status, message, before, after, [{"path": call[0], "payload": call[1]}])

    def c5_conservation_constraint(self) -> HeroResult:
        before = self.state()
        if not self.backend_available():
            return _result("c5", self.copilot, "unavailable", "Backend health endpoint is unavailable.", before, before)
        conservation = before.get("conservation")
        status = str(_find_value(conservation, ("status", "phase", "conservation_status")) or "UNKNOWN").upper()
        promotion = self.client.first_post(
            (path, {"category": "demo", "hero_moment": "B31-C5"})
            for path in ("/api/evolution/check-promotion", "/api/promotion/check", "/api/trading/promotion/check")
        )
        after = self.state()
        blocked = status == "RED" and (promotion is None or not _has_truth(promotion[1], ("promoted", "advanced")))
        if blocked:
            message = "Conservation is RED and the promotion path reports no advancement: not yet."
            result_status = "measured"
        elif status == "RED":
            message = "Conservation is RED, but the promotion response did not expose a safe blocked result."
            result_status = "inconclusive"
        else:
            message = f"Conservation is {status}; a RED-veto moment cannot be claimed without a live RED state."
            result_status = "unavailable"
        events = [] if promotion is None else [{"path": promotion[0], "payload": promotion[1]}]
        return _result("c5", self.copilot, result_status, message, before, after, events, {"conservation_status": status})


def hero_c2_score_learn(copilot: str, port: int) -> HeroResult:
    return HeroRunner(copilot, port).c2_score_learn()


def hero_c3_twin_improvement(copilot: str, port: int) -> HeroResult:
    return HeroRunner(copilot, port).c3_twin_improvement()


def hero_c4_promotion_earned(copilot: str, port: int) -> HeroResult:
    return HeroRunner(copilot, port).c4_promotion_earned()


def hero_c5_conservation_constraint(copilot: str, port: int) -> HeroResult:
    return HeroRunner(copilot, port).c5_conservation_constraint()


def run(copilot: str, port: int, beat: str) -> HeroResult:
    try:
        return {
            "c2": hero_c2_score_learn,
            "c3": hero_c3_twin_improvement,
            "c4": hero_c4_promotion_earned,
            "c5": hero_c5_conservation_constraint,
        }[beat](copilot, port)
    except HeroApiError as exc:
        return _result(beat, copilot, "unavailable", str(exc), {}, {})


def _result(
    beat: str,
    copilot: str,
    status: str,
    message: str,
    before: dict[str, Any],
    after: dict[str, Any],
    evidence: list[dict[str, Any]] | None = None,
    events: dict[str, Any] | None = None,
) -> HeroResult:
    return HeroResult(beat, copilot, status, message, before, after, evidence or [], [] if events is None else [events])


def _score_payload(client: ApiClient, copilot: str) -> dict[str, Any]:
    if copilot == "s2p":
        return {
            "event_id": "hero-c2-s2p",
            "category": "invoice_matching",
            "amount": 1250.0,
            "supplier_id": "hero-supplier",
            "supplier_name": "Hero Supplier",
            "contract_id": "hero-contract",
            "supplier_risk_rating": 0.25,
            "historical_spend_mean": 1200.0,
            "historical_spend_std": 240.0,
            "vendor_decisions": 24,
            "vendor_approvals": 20,
            "match_status": "match",
            "amount_variance_ratio": 0.02,
            "duplicate_score": 0.08,
            "supplier_exception_history": 0.1,
            "payment_terms_impact": 0.2,
            "commodity_index_correlation": 0.7,
            "tax_regulatory_compliance": 0.9,
            "environmental_risk": 0.2,
        }
    fingerprint = client.first(("/api/fingerprint", "/api/trading/fingerprint"))
    names: list[str] = []
    if fingerprint is not None:
        for row in _walk(fingerprint[1]):
            if isinstance(row, dict) and row.get("name") and ("weight" in row or "factor" in row):
                names.append(str(row["name"]))
    factors = {name: 0.5 for name in dict.fromkeys(names)} or {"signal_alignment": 0.5}
    category = {"trading": "trend_following", "purchasing": "strategic_sourcing", "dataops": "data_quality"}.get(copilot, "trend_following")
    return {"category": category, "factors": factors, "context": {"hero_moment": "B31-C2"}}


def _action_for_score(score: Any, copilot: str) -> str:
    if isinstance(score, dict) and score.get("action"):
        return str(score["action"])
    return {"trading": "strong_execution", "purchasing": "order_as_planned", "dataops": "investigate", "s2p": "approve"}.get(copilot, "confirmed")


def _walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _find_value(value: Any, keys: tuple[str, ...]) -> Any:
    for item in _walk(value):
        if isinstance(item, dict):
            for key in keys:
                if key in item:
                    return item[key]
    return None


def _find_number(value: Any, keys: tuple[str, ...]) -> float | None:
    raw = _find_value(value, keys)
    try:
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _has_truth(value: Any, keys: tuple[str, ...]) -> bool:
    raw = _find_value(value, keys)
    return raw is True or str(raw).lower() in {"true", "promoted", "advanced"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run B31 Loom hero moments against live copilot APIs")
    parser.add_argument("--copilot", choices=sorted(COPILOTS))
    parser.add_argument("--port", type=int)
    parser.add_argument("--beat", choices=BEATS)
    parser.add_argument("--all", action="store_true", help="Run all four beats for every configured copilot")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args(argv)
    if not args.all and (args.copilot is None or args.beat is None):
        parser.error("--copilot and --beat are required unless --all is used")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    jobs = (
        [(name, args.port or port, beat) for name, port in COPILOTS.items() for beat in BEATS]
        if args.all
        else [(args.copilot, args.port or COPILOTS[args.copilot], args.beat)]
    )
    results = [run(name, port, beat) for name, port, beat in jobs]
    if args.json:
        print(json.dumps([result.to_dict() for result in results], indent=2, sort_keys=True, allow_nan=False))
    else:
        for result in results:
            print(f"{result.copilot}/{result.beat}: {result.status} — {result.message}")
    return 0 if all(result.status not in {"unavailable", "inconclusive"} for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
