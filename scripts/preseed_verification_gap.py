#!/usr/bin/env python
"""Build a deterministic trajectory fixture with a verification gap.

The fixture keeps decisions flowing for 50 days, but only emits verified
trajectory checkpoints for days 1--14 and 36--50.  Consumers can therefore
render the 21-day interval as a period in which the copilot had no verified
outcomes from which to learn.

Run ``python scripts/preseed_verification_gap.py`` to print the fixture, or
pass ``--output PATH`` to write it as JSON for a local demo harness.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


GAP_THRESHOLD_DAYS = 7
GAP_START_DAY = 15
GAP_END_DAY = 35
TOTAL_DAYS = 50
DECISIONS_PER_DAY = 2
START = datetime(2026, 1, 1, 9, tzinfo=UTC)


def build_verification_gap_fixture() -> dict[str, Any]:
    """Return decisions and verified trajectory points for the PILOT-02 demo."""

    decisions: list[dict[str, Any]] = []
    points: list[dict[str, Any]] = []
    correct = 0
    verified = 0
    decision_count = 0

    for day in range(1, TOTAL_DAYS + 1):
        timestamp = START + timedelta(days=day - 1)
        verification_active = day < GAP_START_DAY or day > GAP_END_DAY
        for slot in range(DECISIONS_PER_DAY):
            decision_count += 1
            row: dict[str, Any] = {
                "decision_id": f"verification-gap-{decision_count:03d}",
                "created_at": (timestamp + timedelta(hours=slot * 4)).timestamp(),
                "category": "demo_verification_gap",
                "recommended_action": "monitor",
            }
            if verification_active:
                # Early confirmations establish the curve; resumed confirmations
                # continue its improvement after the deliberate verification gap.
                is_correct = day > 4 or slot == 0
                row["is_correct"] = is_correct
                verified += 1
                correct += int(is_correct)
            decisions.append(row)

        if verification_active:
            win_rate = round(correct / verified, 3)
            points.append(
                {
                    "decisions": decision_count,
                    "iks": round(20.0 + win_rate * 30.0 + verified * 0.20, 1),
                    "win_rate": win_rate,
                    "timestamp": timestamp.timestamp(),
                }
            )

    return {
        "points": points,
        "current_iks": points[-1]["iks"],
        "current_win_rate": points[-1]["win_rate"],
        "decisions_total": decision_count,
        "days_active": float(TOTAL_DAYS - 1),
        "decisions": decisions,
        "verification_gap": {
            "start_day": GAP_START_DAY,
            "end_day": GAP_END_DAY,
            "gap_days": GAP_END_DAY - GAP_START_DAY + 1,
            "threshold_days": GAP_THRESHOLD_DAYS,
            "label": "No verifications",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON destination.")
    args = parser.parse_args()
    payload = build_verification_gap_fixture()
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is None:
        print(rendered)
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(f"{rendered}\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
