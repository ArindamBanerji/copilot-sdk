from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from integrity import architecture_scan


def test_scanner_imports_and_defines_all_literal_checks() -> None:
    assert architecture_scan.SDK_ROOT.name == "copilot-sdk"
    assert [check.code for check in architecture_scan.LITERAL_CHECKS] == [
        "AGE-01",
        "AGE-02",
        "LANG-01",
    ]


def test_scanner_check_mode_passes_current_tree() -> None:
    result = subprocess.run(
        [sys.executable, "integrity/architecture_scan.py", "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ENFORCED_FAILURES=0" in result.stdout


@pytest.mark.parametrize(
    ("index", "suffix", "source"),
    [
        (0, ".py", 'query = "MERGE (n:Node {id: 1})"\n'),
        (1, ".py", "connection = sqlite3.connect('local.db')\n"),
        (2, ".tsx", 'export const label = "Customer inventory SKU";\n'),
    ],
)
def test_literal_checks_detect_violations(
    tmp_path: Path,
    index: int,
    suffix: str,
    source: str,
) -> None:
    original = architecture_scan.LITERAL_CHECKS[index]
    check = replace(original, scan_dirs=("repo",), exempt_paths=())
    target = tmp_path / "repo" / f"violation{suffix}"
    target.parent.mkdir(parents=True)
    target.write_text(source, encoding="utf-8")

    result = architecture_scan.run_literal_check(check, repos_root=tmp_path)

    assert result.passed is False
    assert len(result.evidence) == 1


def test_scan_file_skips_comments_docstrings_and_tests(tmp_path: Path) -> None:
    check = replace(
        architecture_scan.LITERAL_CHECKS[0],
        scan_dirs=("repo",),
        exempt_paths=(),
    )
    root = tmp_path / "repo"
    root.mkdir()
    source = root / "clean.py"
    source.write_text(
        '"""MERGE (n:Documented)"""\n# MERGE (n:Comment)\nquery = "MATCH (n) RETURN n"\n',
        encoding="utf-8",
    )
    test_source = root / "test_legacy.py"
    test_source.write_text('query = "MERGE (n:Test)"\n', encoding="utf-8")

    result = architecture_scan.run_literal_check(check, repos_root=tmp_path)

    assert result.passed is True


def test_missing_directory_is_skipped_cleanly(tmp_path: Path) -> None:
    check = replace(
        architecture_scan.LITERAL_CHECKS[0],
        scan_dirs=("not-cloned",),
        exempt_paths=(),
    )

    result = architecture_scan.run_literal_check(check, repos_root=tmp_path)

    assert result.passed is True
    assert "not-cloned" in result.note


def test_age02_catches_new_sqlite_in_formerly_exempt_file(tmp_path: Path) -> None:
    target = tmp_path / "copilot-sdk" / "copilot_sdk" / "backend" / "signal_store.py"
    target.parent.mkdir(parents=True)
    target.write_text(
        "extra_connection = sqlite3.connect('unexpected.db')\n",
        encoding="utf-8",
    )
    check = replace(
        architecture_scan.LITERAL_CHECKS[1],
        scan_dirs=("copilot-sdk/copilot_sdk",),
    )

    result = architecture_scan.run_literal_check(check, repos_root=tmp_path)

    assert result.passed is False
    assert len(result.evidence) == 1


def test_age02_allows_known_legitimate_uses() -> None:
    result = architecture_scan.check_raw_sqlite()
    assert result.passed is True


def test_check_exit_code_is_one_for_enforced_violation(monkeypatch: pytest.MonkeyPatch) -> None:
    failed = architecture_scan.CheckResult(
        "TEST",
        "forced violation",
        True,
        (architecture_scan.Evidence(Path("bad.py"), 1, "bad"),),
    )
    monkeypatch.setattr(architecture_scan, "run_checks", lambda: [failed])

    assert architecture_scan.main(["--check"]) == 1
    assert architecture_scan.main(["--report"]) == 0


def test_compatibility_audits_remain_available() -> None:
    assert architecture_scan.check_age_merge().code == "AGE-01"
    assert architecture_scan.check_raw_sqlite().code == "AGE-02"
    assert architecture_scan.check_purchasing_kitchen_language().code == "LANG-01"
    assert architecture_scan.check_learning_names().code == "F-25"
