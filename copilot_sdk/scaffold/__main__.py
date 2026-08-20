from __future__ import annotations

import argparse
from pathlib import Path

from .generator import CopilotScaffold


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an open-source copilot scaffold")
    parser.add_argument("--config", type=Path, required=True, help="Path to copilot.yaml")
    parser.add_argument("--output", type=Path, default=Path("my-copilot"))
    args = parser.parse_args()
    scaffold = CopilotScaffold.from_yaml(args.config)
    paths = scaffold.generate(args.output)
    print(f"Generated {scaffold.config.name!r} in {args.output}")
    print(f"Created {len(paths)} files. Run: cd {args.output} && python -m pytest backend/tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

