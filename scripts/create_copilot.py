"""CLI for the L-CDK open-source developer cut."""

from __future__ import annotations

import argparse
from pathlib import Path

from copilot_sdk.scaffold import CopilotScaffold


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a new copilot from copilot.yaml")
    parser.add_argument("--config", type=Path, required=True, help="YAML configuration path")
    parser.add_argument("--output", type=Path, required=True, help="Output project directory")
    args = parser.parse_args(argv)
    scaffold = CopilotScaffold.from_yaml(args.config)
    files = scaffold.generate(args.output)
    print(f"Created {scaffold.config.name} ({len(files)} files) at {args.output}")
    print("Next steps:")
    print(f"  cd {args.output}")
    print("  python -m pytest backend/tests")
    print("  uvicorn backend.app.main:app --reload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

