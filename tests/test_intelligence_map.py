from copilot_sdk.di import DataValuationEngine, IntelligenceMapBuilder


def _sources():
    return [
        {"name": "Customer Orders", "domain": "Customer-360", "source_reliability": 0.91, "record_count": 2000, "quality_score": 0.88},
        {"name": "Weather API", "domain": "Customer-360", "source_reliability": 0.82, "record_count": 500, "quality_score": 0.79},
        {"name": "Supplier Quality", "domain": "ESG", "source_reliability": 0.62, "record_count": 150},
    ]


def _valuation():
    return DataValuationEngine("dataops").valuate_single(
        15,
        decisions_per_year=26373,
        factor_a="Customer Orders",
        factor_b="Weather API",
        description="Connect weather API to demand prediction",
    )


def test_build_basic():
    data = IntelligenceMapBuilder().build(_sources())
    assert len(data.nodes) == 3


def test_nodes_have_trust():
    data = IntelligenceMapBuilder().build(_sources())
    assert data.nodes[0].brightness == 0.91


def test_edges_from_correlations():
    data = IntelligenceMapBuilder().build(_sources(), correlations=[{"source": "a", "target": "b", "correlation": 0.75}])
    assert data.edges[0].thickness > 1


def test_gold_lines_from_valuations():
    data = IntelligenceMapBuilder().build(_sources(), valuations=[_valuation()])
    assert data.gold_lines[0].color == "gold"
    assert data.gold_lines[0].style == "dotted"


def test_gold_line_dollar_label():
    data = IntelligenceMapBuilder().build(_sources(), valuations=[_valuation()])
    assert data.gold_lines[0].label.startswith("$")
    assert data.gold_lines[0].label.endswith("/year")


def test_iks_badges():
    data = IntelligenceMapBuilder().build(_sources(), iks_by_domain={"Customer-360": 72, "ESG": 8})
    assert {badge.domain: badge.status for badge in data.iks_badges} == {"Customer-360": "mature", "ESG": "learning"}


def test_domain_clusters():
    data = IntelligenceMapBuilder().build(_sources())
    assert len(data.domain_clusters["Customer-360"]) == 2


def test_backward_compatible():
    data = IntelligenceMapBuilder().build([{"name": "Legacy Source"}])
    assert data.nodes[0].label == "Legacy Source"
    assert data.gold_lines == []


def test_empty_valuations():
    data = IntelligenceMapBuilder().build(_sources(), valuations=[])
    assert data.gold_lines == []


def test_narrative_present():
    data = IntelligenceMapBuilder().build(_sources(), valuations=[_valuation()])
    assert "narrative" in data.to_dict()
    assert "suggested data connections" in data.narrative


def test_gold_lines_from_api_payload():
    data = IntelligenceMapBuilder().build(_sources(), valuations=[{
        "factor_a": "Customer Orders",
        "factor_b": "Weather API",
        "annual_value": 180000,
        "confidence": 0.87,
        "narrative": "Connect weather API to demand prediction.",
    }])
    assert data.gold_lines[0].source == "Customer Orders"
    assert data.gold_lines[0].target == "Weather API"
    assert data.gold_lines[0].label == "$180K/year"


def test_gold_lines_empty_when_no_valuations():
    data = IntelligenceMapBuilder().build(_sources())
    assert data.gold_lines == []


def test_iks_from_payload():
    data = IntelligenceMapBuilder().build(_sources(), iks_by_domain={"Customer-360": 72})
    assert data.iks_badges[0].domain == "Customer-360"
    assert data.iks_badges[0].score == 72
    assert data.iks_badges[0].status == "mature"
