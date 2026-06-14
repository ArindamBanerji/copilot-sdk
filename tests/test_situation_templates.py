from __future__ import annotations

import json

from copilot_sdk.situation import SafeTemplateRenderer, TemplateRenderResult


def test_missing_variable_does_not_crash() -> None:
    result = SafeTemplateRenderer().render("Hello {name}", {})

    assert result.rendered == "Hello unknown"
    assert result.missing_variables == ["name"]


def test_missing_numeric_variable_with_format_does_not_crash() -> None:
    result = SafeTemplateRenderer().render("Amount {amount:.1f}", {})

    assert result.rendered == "Amount 0.0"
    assert result.missing_variables == ["amount"]


def test_input_variables_not_mutated() -> None:
    variables = {"name": "invoice", "nested": {"value": 1}}
    original = {"name": "invoice", "nested": {"value": 1}}

    SafeTemplateRenderer().render("{name}", variables)

    assert variables == original


def test_deterministic_output() -> None:
    renderer = SafeTemplateRenderer()

    first = renderer.render("{name} {amount:.2f}", {"name": "A", "amount": 3})
    second = renderer.render("{name} {amount:.2f}", {"name": "A", "amount": 3})

    assert first.to_dict() == second.to_dict()


def test_json_safe_result() -> None:
    result = SafeTemplateRenderer().render("Items {items}", {"items": [object()]})

    json.dumps(result.to_dict())


def test_audience_preserved() -> None:
    result = SafeTemplateRenderer().render("A", {}, audience="L2")

    assert result.audience == "L2"
    assert result.to_dict()["audience"] == "L2"


def test_used_and_missing_variables_tracked() -> None:
    result = SafeTemplateRenderer().render("{known} {missing}", {"known": "ok"})

    assert result.used_variables == ["known", "missing"]
    assert result.missing_variables == ["missing"]


def test_result_is_exported_dataclass() -> None:
    result = SafeTemplateRenderer().render("A", {})

    assert isinstance(result, TemplateRenderResult)


def test_malformed_unmatched_left_brace_does_not_crash() -> None:
    result = SafeTemplateRenderer().render(
        "Invoice {invoice_id has bad syntax",
        {"invoice_id": "INV-1"},
    )

    assert result.rendered
    assert "template_parse_error" in result.missing_variables


def test_malformed_unmatched_right_brace_does_not_crash() -> None:
    result = SafeTemplateRenderer().render("Invoice } bad syntax", {})

    assert result.rendered
    assert "template_parse_error" in result.missing_variables


def test_malformed_template_does_not_mutate_input_variables() -> None:
    variables = {"invoice_id": "INV-1", "nested": {"amount": 12.5}}
    original = {"invoice_id": "INV-1", "nested": {"amount": 12.5}}

    SafeTemplateRenderer().render("Invoice {invoice_id bad", variables)

    assert variables == original


def test_valid_template_behavior_still_works() -> None:
    result = SafeTemplateRenderer().render("Invoice {invoice_id}", {"invoice_id": "INV-1"})

    assert result.rendered == "Invoice INV-1"
    assert result.missing_variables == []
