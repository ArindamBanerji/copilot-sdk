from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_MAIN_FILES = [
    REPO_ROOT / "apps" / "trading" / "backend" / "app" / "main.py",
    REPO_ROOT / "apps" / "purchasing" / "backend" / "app" / "main.py",
    REPO_ROOT / "apps" / "dataops" / "backend" / "app" / "main.py",
]
DEV_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
]


def test_sdk_apps_do_not_allow_wildcard_cors() -> None:
    for path in APP_MAIN_FILES:
        source = path.read_text(encoding="utf-8")
        assert 'allow_origins=["*"]' not in source
        assert "allow_origins=['*']" not in source


def test_sdk_apps_use_cors_origins_env() -> None:
    for path in APP_MAIN_FILES:
        source = path.read_text(encoding="utf-8")
        assert "CORS_ORIGINS" in source
        assert "os.environ.get" in source
        assert '.split(",")' in source
        assert "origin.strip()" in source
        assert "if origin.strip()" in source


def test_sdk_apps_keep_default_dev_origins() -> None:
    for path in APP_MAIN_FILES:
        source = path.read_text(encoding="utf-8")
        for origin in DEV_ORIGINS:
            assert origin in source


def test_sdk_apps_preserve_cors_flags() -> None:
    for path in APP_MAIN_FILES:
        source = path.read_text(encoding="utf-8")
        assert "allow_credentials=True" in source
        assert 'allow_methods=["*"]' in source
        assert 'allow_headers=["*"]' in source
