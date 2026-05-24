from __future__ import annotations

import ast
import re
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (PACKAGE_ROOT / path).read_text(encoding="utf-8")


def _project_version() -> str:
    match = re.search(r'^version\s*=\s*"([^"]+)"', _read("pyproject.toml"), re.MULTILINE)
    assert match is not None
    return match.group(1)


def test_version_importable_or_file_contains_version():
    source = _read("ci_trading/__init__.py")
    tree = ast.parse(source)
    versions = [
        node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
        and target.id == "__version__"
        and isinstance(node.value, ast.Constant)
    ]
    assert versions == ["0.1.0"]


def test_pyproject_exists():
    assert (PACKAGE_ROOT / "pyproject.toml").exists()


def test_readme_exists():
    assert (PACKAGE_ROOT / "README.md").exists()


def test_license_exists():
    text = _read("LICENSE")
    assert "Apache License" in text
    assert "Version 2.0, January 2004" in text
    assert "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION" in text


def test_pyproject_has_entry_point():
    text = _read("pyproject.toml")
    assert 'name = "ci-trading"' in text
    assert 'version = "0.1.0"' in text
    assert 'ci-trading = "ci_trading.cli:main"' in text


def test_version_matches_pyproject():
    init_source = _read("ci_trading/__init__.py")
    assert f'__version__ = "{_project_version()}"' in init_source


def test_readme_mentions_editable_install():
    text = _read("README.md").lower()
    assert "pip install -e ." in text
    assert "editable" in text


def test_readme_says_standalone_pypi_is_v020():
    text = _read("README.md").lower()
    assert "standalone `pip install ci-trading`" in text
    assert "v0.2.0" in text


def test_disclaimer_in_readme():
    text = _read("README.md").lower()
    assert "does not provide investment advice" in text
    assert "does not provide trading signals or recommendations" in text
    assert "past performance does not predict future results" in text
    assert "qualified financial advisor" in text


def test_cli_wrapper_file_exists():
    assert (PACKAGE_ROOT / "ci_trading" / "cli.py").exists()


def test_cli_wrapper_does_not_import_app_directly():
    source = _read("ci_trading/cli.py")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name != "app" and not alias.name.startswith("app.") for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "app"
            assert node.module is None or not node.module.startswith("app.")
