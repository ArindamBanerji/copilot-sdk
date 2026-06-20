"""Day-zero readiness contract for measurement-gated features."""

from dataclasses import dataclass


@dataclass
class DayZeroReadiness:
    """Gate for every measurement-gated intelligence feature."""

    feature: str
    copilot: str
    populated: bool
    proven: bool
    instrumented: bool
    real_path_committed: bool
    labels_honest: bool

    def gate(self) -> tuple[bool, list[str]]:
        """Returns (pass, missing_layers)."""
        missing = [
            key
            for key in (
                "populated",
                "proven",
                "instrumented",
                "real_path_committed",
                "labels_honest",
            )
            if not getattr(self, key)
        ]
        return not missing, missing
