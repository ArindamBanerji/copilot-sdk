from __future__ import annotations

from pathlib import Path

from integrity.correctness_scanner import scan, scan_file


ROOT = Path(__file__).resolve().parents[2]


def test_scanner_finds_no_violations_in_current_code() -> None:
    assert scan(ROOT) == []


def test_scanner_detects_raw_set_correct(tmp_path: Path) -> None:
    source = tmp_path / "bad_write.py"
    source.write_text(
        "def bad_write():\n"
        "    query = \"MATCH (d:Decision) SET d.correct = true\"\n",
        encoding="utf-8",
    )

    violations = scan_file(source)

    assert len(violations) == 1
    assert violations[0].rule == "C2"


def test_scanner_detects_has_outcome_in_count(tmp_path: Path) -> None:
    source = tmp_path / "bad_count.py"
    source.write_text(
        "def count_correct():\n"
        "    return \"MATCH (d)-[:HAS_OUTCOME]->(o)\"\n",
        encoding="utf-8",
    )

    violations = scan_file(source)

    assert len(violations) == 1
    assert violations[0].rule == "C3"


def test_scanner_allows_write_outcome_implementations() -> None:
    age_store = (
        Path(__file__).resolve().parents[2]
        / "ci-platform"
        / "ci_platform"
        / "graph"
        / "age_graph_store.py"
    )

    assert scan_file(age_store) == []

