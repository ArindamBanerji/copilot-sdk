from __future__ import annotations

import json
from pathlib import Path

from scripts import scan_forbidden_patterns, validate_age_unification


def _write(root: Path, relative: str, source: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def test_validation_runner_reports_thirteen_checks() -> None:
    report = validate_age_unification.build_report()
    assert report["check_count"] == 13
    assert len(report["checks"]) == 13
    json.dumps(report)


def test_validation_runner_detects_injected_neo4j_violation(tmp_path: Path) -> None:
    _write(tmp_path, "copilot_sdk/bad.py", "from neo4j import GraphDatabase\n")
    report = validate_age_unification.build_report(tmp_path)
    failed = {item["name"] for item in report["checks"] if item["result"] == "FAIL"}
    assert "no_neo4j_imports" in failed
    assert report["all_pass"] is False


def test_forbidden_scan_is_clear_for_empty_fixture_tree(tmp_path: Path) -> None:
    report = scan_forbidden_patterns.build_report(tmp_path)
    assert report["pattern_count"] == 9
    assert report["violation_count"] == 0
    assert report["all_clear"] is True
    json.dumps(report)


def test_forbidden_scan_detects_injected_patterns(tmp_path: Path) -> None:
    _write(tmp_path, "copilot_sdk/bad.py", "try:\n    pass\nexcept:\n    pass\n")
    report = scan_forbidden_patterns.build_report(tmp_path)
    assert report["all_clear"] is False
    groups = {item["pattern"] for item in report["patterns"] if item["violations"]}
    assert "bare_except" in groups


def test_forbidden_scan_detects_empty_domain(tmp_path: Path) -> None:
    _write(tmp_path, "copilot_sdk/bad.py", "domain = ''\n")
    report = scan_forbidden_patterns.build_report(tmp_path)
    groups = {item["pattern"] for item in report["patterns"] if item["violations"]}
    assert "empty_domain" in groups
