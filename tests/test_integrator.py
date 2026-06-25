from copilot_sdk.di import SourceIntegrator


class _Profiler:
    def __init__(self, qualities=None, fail=False):
        self.qualities = qualities or {}
        self.fail = fail

    def profile(self, entity_ids):
        if self.fail:
            raise RuntimeError("profile unavailable")
        name = list(entity_ids)[0]
        return type("Profile", (), {"overall_quality": self.qualities.get(name, 0.5)})()


def _quickbooks(n=3):
    return [
        {"vendor_id": f"V-{index}", "amount": 100 + index, "delivery_date": f"2026-06-{index+1:02d}"}
        for index in range(n)
    ]


def _sheet(n=3):
    return [
        {"supplier_id": f"V-{index}", "amount": 90 + index, "delivery_date": f"2026-06-{index+1:02d}"}
        for index in range(n)
    ]


def test_discover_exact_match():
    joins = SourceIntegrator().discover_joins(_quickbooks(), _sheet(), "quickbooks", "supplier_spreadsheet")
    assert joins[0]["key_a"] == "vendor_id"
    assert joins[0]["key_b"] == "supplier_id"
    assert joins[0]["confidence"] > 0.8


def test_discover_fuzzy():
    a = [{"vendor_name": "Acme Industrial"}]
    b = [{"supplier_name": "Acme Industrials"}]
    joins = SourceIntegrator().discover_joins(a, b, "a", "b")
    assert joins


def test_discover_no_match():
    joins = SourceIntegrator().discover_joins([{"a": "1"}], [{"b": "2"}], "a", "b")
    assert joins == []


def test_discover_field_name_boost():
    joins = SourceIntegrator().discover_joins(_quickbooks(1), _sheet(1), "quickbooks", "sheet")
    assert joins[0]["name_similarity"] >= 0.65


def test_discover_top_5():
    record_a = {f"id_{index}": "A" for index in range(10)}
    record_b = {f"id_{index}": "A" for index in range(10)}
    assert len(SourceIntegrator().discover_joins([record_a], [record_b], "a", "b")) == 5


def test_discover_empty_source():
    assert SourceIntegrator().discover_joins([], [], "a", "b") == []


def test_discover_single_record():
    assert SourceIntegrator().discover_joins([{"id": "1"}], [{"id": "1"}], "a", "b")


def test_discover_unicode_fields():
    joins = SourceIntegrator().discover_joins([{"vendör_id": "1"}], [{"vendor_id": "1"}], "a", "b")
    assert joins


def test_combine_basic():
    join = SourceIntegrator().discover_joins(_quickbooks(), _sheet(), "quickbooks", "sheet")[0]
    view = SourceIntegrator().combine(_quickbooks(), _sheet(), join)
    assert view["record_count"] == 3


def test_combine_trust_weighted():
    join = {"key_a": "vendor_id", "key_b": "supplier_id", "confidence": 0.9}
    view = SourceIntegrator().combine(_quickbooks(1), _sheet(1), join, trust_a=0.9, trust_b=0.4)
    assert view["records"][0]["amount"] == 100


def test_combine_quality_annotations():
    join = {"key_a": "vendor_id", "key_b": "supplier_id", "confidence": 0.9}
    view = SourceIntegrator().combine(_quickbooks(1), _sheet(1), join, trust_a=0.91, trust_b=0.67)
    assert any(item["field"] == "delivery_date" for item in view["quality_annotations"])


def test_combine_no_profiler():
    join = {"key_a": "vendor_id", "key_b": "supplier_id", "confidence": 0.9}
    view = SourceIntegrator().combine(_quickbooks(1), _sheet(1), join)
    assert view["trust_weights"]["source_a"] == 0.5


def test_trust_from_real_profiler():
    join = {"key_a": "vendor_id", "key_b": "supplier_id", "confidence": 0.9}
    profiler = _Profiler({"quickbooks": 0.91, "sheet": 0.67})
    view = SourceIntegrator(profiler=profiler).combine(
        _quickbooks(1),
        _sheet(1),
        join,
        source_a_name="quickbooks",
        source_b_name="sheet",
    )
    assert view["trust_weights"]["quickbooks"] == 0.91
    assert view["trust_weights"]["sheet"] == 0.67


def test_profiler_fallback_graceful():
    join = {"key_a": "vendor_id", "key_b": "supplier_id", "confidence": 0.9}
    view = SourceIntegrator(profiler=_Profiler(fail=True)).combine(_quickbooks(1), _sheet(1), join)
    assert view["trust_weights"]["source_a"] == 0.5
    assert view["trust_weights"]["source_b"] == 0.5


def test_trust_affects_conflict_resolution():
    join = {"key_a": "vendor_id", "key_b": "supplier_id", "confidence": 0.9}
    profiler = _Profiler({"quickbooks": 0.9, "sheet": 0.4})
    view = SourceIntegrator(profiler=profiler).combine(
        _quickbooks(1),
        _sheet(1),
        join,
        source_a_name="quickbooks",
        source_b_name="sheet",
    )
    assert view["records"][0]["amount"] == 100


def test_quality_annotations_from_profiler():
    join = {"key_a": "vendor_id", "key_b": "supplier_id", "confidence": 0.9}
    profiler = _Profiler({"quickbooks": 0.91, "sheet": 0.67})
    view = SourceIntegrator(profiler=profiler).combine(
        _quickbooks(1),
        _sheet(1),
        join,
        source_a_name="quickbooks",
        source_b_name="sheet",
    )
    delivery = [
        item for item in view["quality_annotations"]
        if item["source"] == "sheet" and item["field"] == "delivery_date"
    ][0]
    assert delivery["reliability"] == 0.71


def test_combine_large_dataset():
    join = {"key_a": "vendor_id", "key_b": "supplier_id", "confidence": 0.9}
    view = SourceIntegrator().combine(_quickbooks(550), _sheet(550), join)
    assert view["record_count"] == 550


def test_suggestions_after_100():
    join = {"key_a": "vendor_id", "key_b": "supplier_id", "confidence": 0.9}
    view = SourceIntegrator().combine(_quickbooks(1), _sheet(1), join, trust_a=0.99, trust_b=0.67)
    assert SourceIntegrator().suggest_improvements(view, usage_count=100)


def test_suggestions_before_100():
    view = {"quality_annotations": [{"field": "delivery_date", "source": "sheet", "reliability": 0.71}]}
    assert SourceIntegrator().suggest_improvements(view, usage_count=50) == []


def test_suggestions_specific():
    view = {"quality_annotations": [{"field": "delivery_date", "source": "spreadsheet", "reliability": 0.71}]}
    suggestion = SourceIntegrator().suggest_improvements(view, usage_count=100)[0]
    assert "wrong 29% of the time" in suggestion["narrative"]


def test_jaccard_empty():
    assert SourceIntegrator()._jaccard(set(), set()) == 0.0


def test_narrative_present():
    join = {"key_a": "vendor_id", "key_b": "supplier_id", "confidence": 0.87}
    view = SourceIntegrator().combine(_quickbooks(1), _sheet(1), join, source_a_name="QuickBooks", source_b_name="supplier spreadsheet")
    assert "narrative" in view
    assert "Connected QuickBooks" in view["narrative"]


def test_exports_from_init():
    from copilot_sdk.di import SourceIntegrator as Exported

    assert Exported is SourceIntegrator
