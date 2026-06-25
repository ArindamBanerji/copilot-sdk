from copilot_sdk.di import AcquisitionAdvisor, ExternalDataSource
from copilot_sdk.di.acquisition import EXTERNAL_CATALOG


def test_recommend_for_purchasing():
    response = AcquisitionAdvisor().recommend("purchasing", [], decisions_per_year=10000)
    names = {item["source"] for item in response["recommendations"]}
    assert "OpenMeteo Weather" in names
    assert "Bureau of Labor Statistics" in names


def test_recommend_excludes_connected():
    response = AcquisitionAdvisor().recommend("purchasing", ["OpenMeteo Weather"], decisions_per_year=10000)
    assert "OpenMeteo Weather" not in {item["source"] for item in response["recommendations"]}


def test_roi_computation():
    catalog = [ExternalDataSource("Paid", "vendor", "signal", 5000.0, ["dataops"], "Paid signal.", 10.989010989)]
    response = AcquisitionAdvisor(catalog=catalog).recommend("dataops", [], decisions_per_year=12000)
    assert round(float(response["recommendations"][0]["roi"]), 2) == 12.0


def test_free_infinite_roi():
    response = AcquisitionAdvisor().recommend("purchasing", [], decisions_per_year=10000)
    first = response["recommendations"][0]
    assert first["cost"] == 0
    assert first["roi"] == "infinite"
    assert first["priority"] == "high"


def test_priority_high():
    assert AcquisitionAdvisor().recommend("dataops", [], decisions_per_year=12000)["recommendations"][0]["priority"] == "high"


def test_priority_low():
    catalog = [ExternalDataSource("Low", "vendor", "signal", 100000.0, ["dataops"], "Low ROI.", 1.0)]
    response = AcquisitionAdvisor(catalog=catalog).recommend("dataops", [], decisions_per_year=1000)
    assert response["recommendations"][0]["priority"] == "low"


def test_sort_by_roi():
    catalog = [
        ExternalDataSource("Low", "vendor", "low", 10000.0, ["dataops"], "Low.", 2.0),
        ExternalDataSource("High", "vendor", "high", 10000.0, ["dataops"], "High.", 20.0),
    ]
    response = AcquisitionAdvisor(catalog=catalog).recommend("dataops", [], decisions_per_year=1000)
    assert response["recommendations"][0]["source"] == "High"


def test_free_first():
    catalog = [
        ExternalDataSource("Paid High", "vendor", "paid", 1000.0, ["dataops"], "Paid.", 50.0),
        ExternalDataSource("Free Lower", "vendor", "free", 0.0, ["dataops"], "Free.", 1.0),
    ]
    response = AcquisitionAdvisor(catalog=catalog).recommend("dataops", [], decisions_per_year=1000)
    assert response["recommendations"][0]["source"] == "Free Lower"


def test_monetization_1000():
    response = AcquisitionAdvisor().discover_monetization(1000, ["s2p"])
    assert response["opportunities"]


def test_monetization_below():
    assert AcquisitionAdvisor().discover_monetization(500, ["s2p"])["opportunities"] == []


def test_monetization_narrative():
    narrative = AcquisitionAdvisor().discover_monetization(5000, ["s2p"])["opportunities"][0]["narrative"]
    assert "outperform D&B" in narrative


def test_empty_catalog():
    response = AcquisitionAdvisor(catalog=[]).recommend("dataops", [], decisions_per_year=1000)
    assert response["recommendations"] == []


def test_narrative_present():
    response = AcquisitionAdvisor().recommend("purchasing", [], decisions_per_year=10000)
    assert response["narrative"]
    assert all(item["narrative"] for item in response["recommendations"])


def test_catalog_all_real():
    assert all(not source.provider.endswith(".example") for source in EXTERNAL_CATALOG)
    assert any(source.provider == "project44.com" for source in EXTERNAL_CATALOG)


def test_no_decisions_provenance_demo():
    response = AcquisitionAdvisor().recommend("purchasing", [])
    assert response["provenance"] == "demo"


def test_no_decisions_provenance_note():
    response = AcquisitionAdvisor().recommend("purchasing", [])
    assert "12,000" in response["provenance_note"]
    assert "actual rate" in response["provenance_note"]
