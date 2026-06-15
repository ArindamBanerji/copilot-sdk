from apps.purchasing.backend.app.connectors.mock_toast import MockToastConnector
from apps.purchasing.backend.app.connectors.toast import ToastConnector


def test_protocol_compliance():
    """ToastConnector has all 5 SourceConnector members."""
    connector = ToastConnector()
    assert hasattr(connector, "source_name")
    assert hasattr(connector, "entity_type")
    assert hasattr(connector, "trust_tier")
    assert callable(getattr(connector, "fetch", None))
    assert callable(getattr(connector, "validate", None))


def test_mock_protocol_compliance():
    """MockToastConnector has all 5 SourceConnector members."""
    connector = MockToastConnector()
    assert hasattr(connector, "source_name")
    assert hasattr(connector, "entity_type")
    assert hasattr(connector, "trust_tier")
    assert callable(getattr(connector, "fetch", None))
    assert callable(getattr(connector, "validate", None))


def test_mock_fetch_returns_records():
    """Fixture data returned for known date."""
    connector = MockToastConnector()
    records = connector.fetch("2024-06-10")
    assert len(records) == 1
    assert "covers" in records[0]
    assert "items" in records[0]


def test_mock_fetch_missing_date():
    """Unknown date returns empty list, not error."""
    connector = MockToastConnector()
    assert connector.fetch("2099-01-01") == []


def test_validate_valid_record():
    connector = MockToastConnector()
    records = connector.fetch("2024-06-10")
    assert connector.validate(records[0]) is True


def test_validate_missing_field():
    connector = MockToastConnector()
    assert connector.validate({"timestamp": 1.0, "covers": 10}) is False


def test_validate_negative_revenue():
    connector = MockToastConnector()
    record = connector.fetch("2024-06-10")[0].copy()
    record["total_revenue"] = -100.0
    assert connector.validate(record) is False


def test_validate_non_integer_covers():
    connector = MockToastConnector()
    record = connector.fetch("2024-06-10")[0].copy()
    record["covers"] = 95.5
    assert connector.validate(record) is False


def test_default_fixtures_7_days():
    connector = MockToastConnector()
    assert len(connector._data) == 7


def test_covers_range():
    """80-150 covers per day in fixtures."""
    connector = MockToastConnector()
    for date, records in connector._data.items():
        covers = records[0]["covers"]
        assert 80 <= covers <= 150, f"{date}: covers={covers}"


def test_revenue_positive():
    """All days have positive revenue."""
    connector = MockToastConnector()
    for records in connector._data.values():
        assert records[0]["total_revenue"] > 0


def test_daypart_distribution():
    """lunch + dinner + late_night sums to total covers."""
    connector = MockToastConnector()
    for records in connector._data.values():
        dayparts = records[0]["dayparts"]
        total = dayparts["lunch"] + dayparts["dinner"] + dayparts["late_night"]
        assert total == records[0]["covers"]


def test_items_have_categories():
    """Every item has a category matching Purchasing categories."""
    valid = {"protein", "produce", "dairy", "dry_goods", "beverages"}
    connector = MockToastConnector()
    for records in connector._data.values():
        for item in records[0]["items"]:
            assert item["category"] in valid


def test_records_have_timestamp():
    """Every record has timestamp field for BaseSourceProfiler freshness."""
    connector = MockToastConnector()
    for records in connector._data.values():
        assert "timestamp" in records[0]
        assert isinstance(records[0]["timestamp"], (int, float))


def test_profiler_integration():
    """BaseSourceProfiler accepts MockToastConnector and profiles."""
    from copilot_sdk.di.profiler import BaseSourceProfiler

    connector = MockToastConnector()
    profiler = BaseSourceProfiler(connector)
    result = profiler.profile(["2024-06-10", "2024-06-11"])
    assert result is not None
