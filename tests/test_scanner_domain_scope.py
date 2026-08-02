from pathlib import Path

from copilot_sdk.di.nl_query import _query_template
from scripts.scan_forbidden_patterns import (
    ACTIVE_SCAN_REPOSITORIES,
    WORKSPACE_ROOT,
    iter_python_files,
    load_allowlist,
    scan_read_model_mutations,
    scan_unscoped_decision_queries,
)


def _categories(source: str):
    return scan_unscoped_decision_queries(
        Path("copilot_sdk/app/query.py"), source, load_allowlist(), 8
    )


def test_multiline_query_predicate_is_scoped():
    findings = _categories('query = f"""MATCH (d:Decision)\nWHERE d.domain = {domain}\nRETURN d"""')
    assert [finding.category for finding in findings] == ["SCOPED"]


def test_domain_parameter_without_query_use_is_not_scoped():
    findings = _categories('def fetch(domain):\n    query = "MATCH (d:Decision) RETURN d"\n    return query')
    assert [finding.category for finding in findings] == ["PRODUCTION"]


def test_indirect_domain_taint_is_caller_scoped():
    source = (
        "def fetch(domain):\n"
        "    clauses = [f'd.domain = {domain}']\n"
        "    where_clause = 'WHERE ' + ' AND '.join(clauses)\n"
        "    query = f'''MATCH (d:Decision)\\n{where_clause}\\nRETURN d'''\n"
    )
    findings = _categories(source)
    assert [finding.category for finding in findings] == ["CALLER_SCOPED"]


def test_relational_domain_equality_is_scoped():
    findings = _categories(
        'query = "MATCH (d:Decision) MATCH (s:Decision) WHERE s.domain = d.domain RETURN s"'
    )
    assert [finding.category for finding in findings] == ["SCOPED"]


def test_nearby_domain_assignment_does_not_scope_query():
    source = 'domain = "soc"\nquery = "MATCH (d:Decision) RETURN d"'
    findings = _categories(source)
    assert [finding.category for finding in findings] == ["PRODUCTION"]


def test_real_unscoped_query_remains_production():
    findings = _categories('query = "MATCH (d:Decision) RETURN d"')
    assert [finding.category for finding in findings] == ["PRODUCTION"]


def test_read_model_mutation_rule_is_property_scoped_and_writer_scoped():
    source = (
        "def write_outcome():\n"
        "    updates = [f\"d.status = 'confirmed'\", f\"d.correct = true\"]\n"
        "def bad_writer():\n"
        "    query = \"MATCH (d:Decision) SET d.correct = true\"\n"
        "    d[\"status\"] = \"pending\"\n"
        "    archive = \"MATCH (d:Decision) SET d.archived = true\"\n"
    )
    path = Path("ci-platform/ci_platform/graph/age_graph_store.py")
    findings = scan_read_model_mutations(path, source, load_allowlist())

    assert sum(finding.category == "ALLOWLISTED" for finding in findings) == 1
    assert any(finding.category == "PRODUCTION" for finding in findings)
    assert not any("archived" in finding.source for finding in findings)


def test_known_template_lines_are_allowlisted():
    root = Path(__file__).resolve().parents[1]
    allowlist = load_allowlist()
    for relative, line in (
        ("copilot_sdk/di/nl_query.py", 133),
        ("copilot_sdk/graph/projection.py", 44),
    ):
        source = (root / relative).read_text(encoding="utf-8")
        findings = scan_unscoped_decision_queries(root / relative, source, allowlist, 8)
        assert any(finding.line == line and finding.category == "ALLOWLISTED" for finding in findings)


def test_nl_query_domain_injection_handles_relationship_match():
    assert "d.domain = 'soc'" in _query_template("impact", domain="soc")
    assert "d.domain = 'soc'" in _query_template("metric", domain="soc")
    assert _query_template("metric", domain=None) == "MATCH (d:Decision) RETURN d"


def test_default_scan_is_limited_to_active_repositories():
    paths = list(iter_python_files(WORKSPACE_ROOT))

    assert paths
    assert {path.relative_to(WORKSPACE_ROOT).parts[0] for path in paths} <= set(ACTIVE_SCAN_REPOSITORIES)
    assert not any("gen-ai-roi-demo-v3" in str(path) for path in paths)
