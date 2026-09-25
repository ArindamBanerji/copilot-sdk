from __future__ import annotations

import json

import k14_validation_tier as k14


def test_astra_scenarios_load() -> None:
    audit = k14.inspect_inputs()
    assert all(audit[c]["accessible"] for c in k14.COPILOTS)
    assert all(audit[c]["scenario_count"] == 50 for c in k14.COPILOTS)


def test_anchor_labels_exist() -> None:
    audit = k14.inspect_inputs()
    assert all(audit[c]["anchor_field_count"] == 50 for c in k14.COPILOTS)


def test_k2_labels_loaded() -> None:
    labels = k14.load_labels()
    assert all(len(labels[c]) >= 40 for c in k14.COPILOTS)
    assert all(row.get("k2_label") is not None for c in k14.COPILOTS for row in labels[c])


def test_k2_has_confidence() -> None:
    labels = k14.load_labels()
    assert all(0.0 <= float(row["k2_confidence"]) <= 1.0 for c in k14.COPILOTS for row in labels[c])


def test_three_arms_run() -> None:
    result = json.loads((k14.ROOT / "experiments/vld/results/k14_validation_tier.json").read_text(encoding="utf-8"))
    assert result["status"] == "measured"
    for copilot in k14.COPILOTS:
        row = result["per_copilot"][copilot]
        assert "k2_compounding_gain" in row
        assert "k3_compounding_gain" in row
        assert "anchor_compounding_gain" in row


def test_gains_and_agreements_bounded() -> None:
    result = json.loads((k14.ROOT / "experiments/vld/results/k14_validation_tier.json").read_text(encoding="utf-8"))
    for row in result["per_copilot"].values():
        assert 0.0 <= row["k2_anchor_agreement"] <= 1.0
        assert 0.0 <= row["k3_anchor_agreement"] <= 1.0
        for key in ("k2_compounding_gain", "k3_compounding_gain", "anchor_compounding_gain"):
            assert -1.0 <= float(row[key]["mean"]) <= 1.0


def test_deterministic_payload() -> None:
    assert json.dumps(k14.build_payload(), sort_keys=True, allow_nan=False) == json.dumps(k14.build_payload(), sort_keys=True, allow_nan=False)


def test_deterministic_compounding() -> None:
    labels = k14.load_labels()
    geometry = k14.load_geometry()
    scenarios = k14.find_scenarios(k14.load_object(k14.SAMPLES / k14.SCENARIO_FILES["soc"]))
    rows = k14.label_rows("soc", labels, scenarios, geometry["soc"])
    assert k14.run_arm(rows, geometry["soc"], 42, "k2") == k14.run_arm(rows, geometry["soc"], 42, "k2")
