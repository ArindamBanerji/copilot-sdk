"""Day-0 qualification orchestration."""

from __future__ import annotations

from threading import RLock
from typing import Iterable

from .checks import QualificationCheck
from .models import QualificationReport


class QualificationGate:
    """Run all supplied checks and fail closed on check errors."""

    def __init__(self) -> None:
        self._lock = RLock()

    def run(self, copilot: str, checks: Iterable[QualificationCheck]) -> QualificationReport:
        with self._lock:
            results = []
            for check in checks:
                try:
                    result = check.check(copilot)
                except Exception as exc:
                    from .models import CheckResult

                    result = CheckResult(False, "Qualification check raised an exception", {"error": str(exc)}, getattr(check, "name", type(check).__name__))
                results.append(result)
            return QualificationReport.create(copilot, results)
