"""Acceptance tests for the Level-3 build-your-own template."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

from examples.build_your_own.domains import email, reading
from examples.build_your_own.engine import run_domain


ROOT = Path(__file__).parents[1]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "examples.build_your_own.run", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_email_domain_runs(tmp_path):
    result = _run("--domain", "email", "--decisions", "50", "--output-dir", str(tmp_path))
    assert result.returncode == 0, result.stderr


def test_reading_domain_runs(tmp_path):
    result = _run("--domain", "reading", "--decisions", "50", "--output-dir", str(tmp_path))
    assert result.returncode == 0, result.stderr


def test_ungoverned_runs(tmp_path):
    result = _run("--domain", "email", "--ungoverned", "--decisions", "50", "--output-dir", str(tmp_path))
    assert result.returncode == 0, result.stderr


def test_domains_share_harness():
    from examples.build_your_own import engine

    assert callable(engine.run_domain)
    assert engine.run_domain(email, decisions=4)["domain"] != engine.run_domain(reading, decisions=4)["domain"]


def test_baseline_is_faithful():
    governed = run_domain(email, decisions=100, inject_poison=False)
    baseline = run_domain(email, decisions=100, ungoverned=True, inject_poison=False)
    assert baseline["quality_curve"][-1] >= 0.8 * governed["quality_curve"][-1]


def test_uses_real_primitives():
    source = Path(ROOT / "examples/build_your_own/run.py").read_text(encoding="utf-8")
    assert "CompoundingScorer" in source
    assert "conservation" in source.lower()


def test_oracle_separation():
    source = Path(ROOT / "examples/build_your_own/generator.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Name) and node.id == "is_correct"
        for node in ast.walk(tree)
    )


def test_metadata_only_no_content():
    content_words = {"body", "text", "content", "subject_text", "message"}
    assert not content_words.intersection(email.FACTORS + reading.FACTORS)
