"""Data contracts for pilot qualification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class CheckResult:
    """One auditable qualification result."""

    passed: bool
    detail: str
    evidence: Mapping[str, Any] = field(default_factory=dict)
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
            "evidence": _json_safe(dict(self.evidence)),
        }


@dataclass(frozen=True)
class QualificationReport:
    """Signed-by-hash, JSON-safe qualification report."""

    copilot: str
    passed: bool
    checks: list[CheckResult]
    timestamp: str
    report_hash: str

    @classmethod
    def create(cls, copilot: str, checks: list[CheckResult]) -> "QualificationReport":
        stable = {
            "copilot": copilot,
            "checks": [result.to_dict() for result in checks],
        }
        payload = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()
        return cls(
            copilot=copilot,
            passed=all(result.passed for result in checks),
            checks=list(checks),
            timestamp=datetime.now(timezone.utc).isoformat(),
            report_hash=hashlib.sha256(payload).hexdigest(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "copilot": self.copilot,
            "passed": self.passed,
            "checks": [result.to_dict() for result in self.checks],
            "timestamp": self.timestamp,
            "report_hash": self.report_hash,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    def write_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(self.to_json() + "\n")


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)
