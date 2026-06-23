"""F-27 enforcement checks for user-facing routers."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent


def _router_dirs() -> list[tuple[str, Path]]:
    return [
        ("trading", ROOT / "apps" / "trading" / "backend" / "app" / "routers"),
        ("purchasing", ROOT / "apps" / "purchasing" / "backend" / "app" / "routers"),
        ("dataops", ROOT / "apps" / "dataops" / "backend" / "app" / "routers"),
        (
            "soc",
            WORKSPACE / "gen-ai-roi-demo-v4-v50" / "backend" / "app" / "routers",
        ),
        ("s2p", WORKSPACE / "s2p-copilot" / "backend" / "app" / "routers"),
    ]


def test_no_router_returns_oracle_synthetic_outcome() -> None:
    """F-27: K1/K2 oracle outputs must not surface through API routers."""

    scanned = 0
    for copilot, router_dir in _router_dirs():
        assert router_dir.is_dir(), f"Missing router directory for {copilot}: {router_dir}"
        for path in router_dir.glob("*.py"):
            scanned += 1
            src = path.read_text(encoding="utf-8")
            assert "synthetic_outcome" not in src, (
                f"F-27: {copilot}/{path.name} references synthetic_outcome"
            )
            if "oracle" in src.lower() and "cohort" not in path.stem.lower():
                assert "synthetic_outcome" not in src, (
                    f"F-27: {copilot}/{path.name} may expose oracle output"
                )
    assert scanned > 0
