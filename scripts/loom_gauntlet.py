"""Automated B32 Loom recording gauntlet.

Runs the existing preseed/preflight scripts, exercises B31 hero moments for
the configured copilots, and writes a timestamped, presenter-ready storyboard.
No application code is imported or changed; all backend interaction remains
behind ``scripts.hero_moments``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import hero_moments
except ImportError:  # Package mode: python -m scripts.loom_gauntlet
    from scripts import hero_moments


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "docs" / "loom_gauntlet_report.json"
DEFAULT_STORYBOARD = ROOT / "docs" / "loom_storyboard_v1.md"
ACTS = (
    ("Act 1 — Establish the baseline", "Show the preseed and truth preflight state. The system starts with evidence, not a claim."),
    ("Act 2 — Score and learn", "Run C2 for each available copilot. Show a real decision, a verified outcome, and the measured before/after state."),
    ("Act 3 — Prove the twin delta", "Run C3. Put the immutable day-zero comparison beside the live state and call out only an exposed delta."),
    ("Act 4 — Earn authority", "Run C4. Show promotion evidence and the gate response; unsupported means the beat is not record-ready."),
    ("Act 5 — The system says not yet", "Run C5. Show conservation state and whether RED actually blocks advancement. Close on the constraint."),
)


@dataclass
class StageResult:
    name: str
    status: str
    duration_s: float
    return_code: int | None = None
    output: str = ""


@dataclass
class BeatResult:
    copilot: str
    beat: str
    status: str
    duration_s: float
    message: str
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    timestamp_s: float = 0.0


@dataclass
class GauntletReport:
    generated_at: str
    duration_s: float
    stages: list[StageResult]
    beats: list[BeatResult]
    storyboard_path: str
    report_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GauntletRunner:
    def __init__(
        self,
        copilots: Iterable[str] = hero_moments.COPILOTS.keys(),
        *,
        report_path: Path = DEFAULT_REPORT,
        storyboard_path: Path = DEFAULT_STORYBOARD,
        skip_preseed: bool = False,
        skip_preflight: bool = False,
    ) -> None:
        self.copilots = tuple(copilots)
        self.report_path = report_path
        self.storyboard_path = storyboard_path
        self.skip_preseed = skip_preseed
        self.skip_preflight = skip_preflight

    def run(self) -> GauntletReport:
        started = time.monotonic()
        stages: list[StageResult] = []
        if not self.skip_preseed:
            stages.append(self._command_stage("preseed", [sys.executable, "scripts/preseed_all_copilots.py"]))
        else:
            stages.append(StageResult("preseed", "skipped", 0.0))
        if not self.skip_preflight:
            stages.append(self._command_stage("truth_preflight", [sys.executable, "scripts/demo_truth_preflight.py"]))
        else:
            stages.append(StageResult("truth_preflight", "skipped", 0.0))

        beats: list[BeatResult] = []
        for copilot in self.copilots:
            port = hero_moments.COPILOTS[copilot]
            for beat in hero_moments.BEATS:
                beat_started = time.monotonic()
                result = hero_moments.run(copilot, port, beat)
                beats.append(
                    BeatResult(
                        copilot=copilot,
                        beat=beat,
                        status=result.status,
                        duration_s=round(time.monotonic() - beat_started, 3),
                        message=result.message,
                        before=result.before,
                        after=result.after,
                        evidence=result.evidence,
                        events=result.events,
                        timestamp_s=round(time.monotonic() - started, 3),
                    )
                )

        duration = round(time.monotonic() - started, 3)
        report = GauntletReport(
            generated_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            duration_s=duration,
            stages=stages,
            beats=beats,
            storyboard_path=str(self.storyboard_path),
            report_path=str(self.report_path),
        )
        self._write_report(report)
        self._write_storyboard(report)
        return report

    def _command_stage(self, name: str, command: list[str]) -> StageResult:
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            status = "passed" if completed.returncode == 0 else "failed"
            output = (completed.stdout + completed.stderr).strip()[-4000:]
            return StageResult(name, status, round(time.monotonic() - started, 3), completed.returncode, output)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return StageResult(name, "unavailable", round(time.monotonic() - started, 3), None, str(exc))

    def _write_report(self, report: GauntletReport) -> None:
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")

    def _write_storyboard(self, report: GauntletReport) -> None:
        self.storyboard_path.parent.mkdir(parents=True, exist_ok=True)
        self.storyboard_path.write_text(render_storyboard(report), encoding="utf-8")


def render_storyboard(report: GauntletReport) -> str:
    """Render a stable five-act presenter script from one gauntlet run."""
    lines = [
        "# Loom Storyboard — B32 Gauntlet",
        "",
        f"Generated: {report.generated_at}",
        f"Total measured runner time: {_stamp(report.duration_s)}",
        "",
        "> Recording rule: describe only values present in the report. `unsupported`, `blocked`, and `unavailable` are valid truth states, not successes to narrate around.",
        "",
    ]
    for index, (title, talking_point) in enumerate(ACTS, start=1):
        lines.extend([f"## {title}", "", f"**Talking point:** {talking_point}", ""])
        if index == 1:
            for stage in report.stages:
                lines.append(f"- **{stage.name}** at `{_stamp(stage.duration_s)}` — **{stage.status}**.")
            lines.extend(["", "**Show:** the preseed/preflight terminal output and the initial evidence/conservation surfaces.", ""])
            continue
        beat_name = f"c{index}"
        selected = [beat for beat in report.beats if beat.beat == beat_name]
        lines.append(f"### Beat {beat_name.upper()} — {len(selected)} copilot run(s)")
        lines.append("")
        if not selected:
            lines.append("No beat result was produced.")
        for beat in selected:
            lines.extend(_beat_lines(beat))
        lines.append("")
    lines.extend([
        "## Recording checklist",
        "",
        "- Capture the terminal/report timestamp before changing tabs.",
        "- Keep the evidence tier and provenance visible whenever a metric is shown.",
        "- Do not narrate an unavailable or blocked beat as if it succeeded.",
        "- Re-run the gauntlet after a deterministic reset when byte-stable recording is required.",
        "",
        "## Raw artifacts",
        "",
        f"- Structured report: `{report.report_path}`",
        f"- This storyboard: `{report.storyboard_path}`",
    ])
    return "\n".join(lines) + "\n"


def _beat_lines(beat: BeatResult) -> list[str]:
    before_iks = _find_number(beat.before, ("current_iks", "iks", "intelligence_knowledge_score"))
    after_iks = _find_number(beat.after, ("current_iks", "iks", "intelligence_knowledge_score"))
    evidence = ", ".join(str(item.get("path")) for item in beat.evidence if isinstance(item, dict) and item.get("path")) or "none exposed"
    return [
        f"- **{beat.copilot}** — `{beat.status}` at `{_stamp(beat.timestamp_s)}` (step {beat.duration_s:.3f}s).",
        f"  - **Say:** {beat.message}",
        f"  - **Show:** evidence `{evidence}`; IKS before `{_display(before_iks)}`, after `{_display(after_iks)}`; conservation before/after captured in the raw report.",
        f"  - **Expected output:** structured status `{beat.status}` with before/after state and no unsupported claim.",
    ]


def _find_number(value: Any, keys: tuple[str, ...]) -> float | None:
    if isinstance(value, dict):
        for key in keys:
            raw = value.get(key)
            if isinstance(raw, (int, float)):
                return float(raw)
        for child in value.values():
            found = _find_number(child, keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_number(child, keys)
            if found is not None:
                return found
    return None


def _display(value: float | None) -> str:
    return "not exposed" if value is None else f"{value:.3f}"


def _stamp(seconds: float) -> str:
    total = max(0, int(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the B32 Loom recording gauntlet")
    parser.add_argument("--copilots", nargs="+", choices=sorted(hero_moments.COPILOTS), default=sorted(hero_moments.COPILOTS))
    parser.add_argument("--skip-preseed", action="store_true")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--storyboard", type=Path, default=DEFAULT_STORYBOARD)
    parser.add_argument("--json", action="store_true", help="Print the structured report after writing artifacts")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = GauntletRunner(
        args.copilots,
        report_path=args.report,
        storyboard_path=args.storyboard,
        skip_preseed=args.skip_preseed,
        skip_preflight=args.skip_preflight,
    ).run()
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True, allow_nan=False))
    else:
        passed = sum(beat.status in {"measured", "completed", "available", "blocked"} for beat in report.beats)
        print(f"Loom gauntlet: {passed}/{len(report.beats)} beats produced a structured result")
        print(f"Report: {report.report_path}")
        print(f"Storyboard: {report.storyboard_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
