"""Built-in, dependency-injected pilot qualification checks."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Protocol

from .models import CheckResult


class QualificationCheck(Protocol):
    name: str

    def check(self, copilot: str) -> CheckResult: ...


def _result(name: str, passed: bool, detail: str, evidence: Mapping[str, Any] | None = None) -> CheckResult:
    return CheckResult(passed=passed, detail=detail, evidence=dict(evidence or {}), name=name)


class FrozenTwinCheck:
    name = "frozen_twin"

    def __init__(self, twin: Any) -> None:
        self.twin = twin

    def check(self, copilot: str) -> CheckResult:
        try:
            frozen = bool(self.twin.is_frozen())
        except Exception as exc:
            return _result(self.name, False, "Frozen Twin check unavailable", {"error": str(exc)})
        return _result(self.name, frozen, "Frozen Twin exists" if frozen else "Frozen Twin is missing", {"frozen": frozen})


class EvidenceGateCheck:
    name = "evidence_gate"

    def __init__(self, gate: Any, context: str = "pilot") -> None:
        self.gate = gate
        self.context = context

    def check(self, copilot: str) -> CheckResult:
        try:
            failures = list(self.gate.scan_all(self.context))
            claims = getattr(self.gate, "_claims", None)
            claim_count = len(claims) if isinstance(claims, Mapping) else None
        except Exception as exc:
            return _result(self.name, False, "Evidence Gate check unavailable", {"error": str(exc)})
        failures_data = [item.to_dict() if hasattr(item, "to_dict") else str(item) for item in failures]
        passed = not failures and claim_count != 0
        detail = "All registered claims meet pilot evidence minimum" if passed else "Claims are missing or fail pilot evidence minimum"
        return _result(self.name, passed, detail, {"context": self.context, "claim_count": claim_count, "failures": failures_data})


class PromotionRecordsCheck:
    name = "promotion_records"

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def check(self, copilot: str) -> CheckResult:
        try:
            records = list(self.engine.get_all(copilot))
        except Exception as exc:
            return _result(self.name, False, "Promotion records unavailable", {"error": str(exc)})
        discovered = sum(1 for record in records if _stage_value(record) == "discovered")
        passed = bool(records) and discovered == len(records)
        detail = "Promotion records are at DISCOVERED" if passed else "Promotion records missing or already advanced"
        return _result(self.name, passed, detail, {"record_count": len(records), "discovered_count": discovered})


class ConservationHealthCheck:
    name = "conservation_health"

    def __init__(self, provider: Any) -> None:
        self.provider = provider

    def check(self, copilot: str) -> CheckResult:
        try:
            raw = self.provider() if callable(self.provider) else self.provider
            if hasattr(raw, "get_state") and callable(raw.get_state):
                raw = raw.get_state()
            status = _status_value(raw)
        except Exception as exc:
            return _result(self.name, False, "Conservation health unavailable", {"error": str(exc)})
        return _result(self.name, status == "GREEN", "Conservation is GREEN" if status == "GREEN" else "Conservation is not GREEN", {"phase": status})


class VerifiedCountCheck:
    name = "verified_count"

    def __init__(self, source: Any, minimum: int = 1) -> None:
        self.source = source
        self.minimum = minimum

    def check(self, copilot: str) -> CheckResult:
        try:
            count = _verified_count(self.source, copilot)
        except Exception as exc:
            return _result(self.name, False, "Verified decision count unavailable", {"error": str(exc), "minimum": self.minimum})
        return _result(self.name, count >= self.minimum, "Verified decision floor met" if count >= self.minimum else "Verified decision floor not met", {"verified_count": count, "minimum": self.minimum})


class TruthPreflightCheck:
    name = "truth_preflight"

    def __init__(self, checker: Callable[[str], Any] | None = None, script: str | Path | None = None) -> None:
        self.checker = checker
        self.script = Path(script) if script is not None else Path(__file__).resolve().parents[2] / "scripts" / "demo_truth_preflight.py"

    def check(self, copilot: str) -> CheckResult:
        try:
            if self.checker is not None:
                outcome = self.checker(copilot)
                failures = _preflight_failures(outcome)
                return _result(self.name, not failures, "Truth preflight is clean" if not failures else "Truth preflight found violations", {"failures": failures})
            completed = subprocess.run([sys.executable, str(self.script), "--copilots", copilot], capture_output=True, text=True, check=False)
            passed = completed.returncode == 0
            return _result(self.name, passed, "Truth preflight is clean" if passed else "Truth preflight failed", {"returncode": completed.returncode, "output": (completed.stdout + completed.stderr).strip()})
        except Exception as exc:
            return _result(self.name, False, "Truth preflight unavailable", {"error": str(exc)})


def _stage_value(record: Any) -> str:
    stage = getattr(record, "current_stage", record)
    return str(getattr(stage, "value", stage)).lower()


def _status_value(raw: Any) -> str:
    if isinstance(raw, Mapping):
        raw = raw.get("phase", raw.get("status", raw.get("state", raw.get("conservation_status", "UNKNOWN"))))
    else:
        raw = getattr(raw, "phase", getattr(raw, "status", raw))
    return str(raw or "UNKNOWN").upper()


def _verified_count(source: Any, copilot: str) -> int:
    if isinstance(source, int):
        return source
    if callable(source):
        try:
            return int(source(copilot))
        except TypeError:
            return int(source())
    for method_name in ("count_verified", "count_verified_decisions"):
        method = getattr(source, method_name, None)
        if callable(method):
            try:
                return int(method(copilot))
            except TypeError:
                return int(method())
    raise AttributeError("verified count source has no supported count method")


def _preflight_failures(outcome: Any) -> list[str]:
    if outcome is None or outcome is True:
        return []
    if outcome is False:
        return ["checker returned false"]
    if outcome == 0:
        return []
    if isinstance(outcome, str):
        return [] if not outcome.strip() else [outcome]
    if isinstance(outcome, (list, tuple, set)):
        return [str(item) for item in outcome]
    return [str(outcome)]
