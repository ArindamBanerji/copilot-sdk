"""Fetch conservation telemetry for the standalone conservation visualization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import URLError
from typing import cast
from urllib.request import urlopen


def _get_json(base_url: str, path: str) -> object | None:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    try:
        with urlopen(url, timeout=5) as response:
            return cast(object, json.load(response))
    except (OSError, URLError, ValueError):
        return None


def collect(base_url: str) -> dict[str, object]:
    """Collect the conservation status, trajectory, and category breakdown."""
    status = _get_json(base_url, "/api/conservation/status")
    trajectory = _get_json(base_url, "/api/trajectory")
    categories = _get_json(base_url, "/api/accuracy-by-category")
    if not isinstance(status, dict):
        status = {}
    if not isinstance(trajectory, dict):
        trajectory = {}
    if not isinstance(categories, dict):
        categories = {}
    return {
        "status": status,
        "trajectory": trajectory,
        "categories": categories,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8010")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("conservation_demo_data.json"),
    )
    args = parser.parse_args()
    payload = collect(args.base_url)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote conservation telemetry to {args.output}")


if __name__ == "__main__":
    main()
