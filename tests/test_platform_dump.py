from __future__ import annotations

import json
from typing import Any, cast

import pytest

from copilot_sdk.diagnostics import platform_dump


DOMAINS = ("soc", "s2p", "trading", "purchasing", "dataops")


def _state(conservation: int = 1, transfers: int = 1) -> dict:
    rows = {domain: 1 for domain in DOMAINS}
    sections = {
        "DECISIONS PER DOMAIN": [(domain, 10) for domain in DOMAINS],
        "CONSERVATION SNAPSHOTS PER DOMAIN": [(domain, conservation) for domain in DOMAINS],
        "CHECKPOINTS PER DOMAIN": [(domain, 1) for domain in DOMAINS],
        "FINGERPRINTS PER DOMAIN": [(domain, 1) for domain in DOMAINS],
        "EVIDENCE RECEIPTS PER DOMAIN": [(domain, 1) for domain in DOMAINS],
        "DOMAIN ANCHORS": [(domain, domain) for domain in DOMAINS],
        "TRANSFER PATTERNS": [(transfers,)],
        "DOMAIN CONTEXT ENTITIES": [("sap_change", 1)],
    }
    return {"census": {"sections": sections}, "copilots": {}, "age": {}, "integrity": {}}


def _observed_verdict_state(
    *,
    soc_conservation: int = 0,
    soc_fingerprints: int = 0,
    soc_anchor: bool = False,
    dataops_receipts: int = 0,
    soc_receipts: int = 0,
    missing_non_soc_receipts: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build the observed platform census with selected readiness repairs."""
    decisions = {"soc": 211, "s2p": 303, "trading": 255, "purchasing": 345, "dataops": 200}
    conservation = {
        "soc": soc_conservation,
        "s2p": 108,
        "trading": 57,
        "purchasing": 40,
        "dataops": 1,
    }
    checkpoints = {"soc": 218, "s2p": 212, "trading": 112, "purchasing": 78, "dataops": 2}
    fingerprints = {
        "soc": soc_fingerprints,
        "s2p": 5,
        "trading": 2,
        "purchasing": 2,
        "dataops": 1,
    }
    receipts = {
        "soc": soc_receipts,
        "s2p": 206,
        "trading": 55,
        "purchasing": 38,
        "dataops": dataops_receipts,
    }
    for domain in missing_non_soc_receipts:
        receipts[domain] = 0
    anchors = [domain for domain in DOMAINS if domain != "soc" or soc_anchor]
    sections = {
        "DECISIONS PER DOMAIN": list(decisions.items()),
        "CONSERVATION SNAPSHOTS PER DOMAIN": list(conservation.items()),
        "CHECKPOINTS PER DOMAIN": list(checkpoints.items()),
        "FINGERPRINTS PER DOMAIN": list(fingerprints.items()),
        "EVIDENCE RECEIPTS PER DOMAIN": list(receipts.items()),
        "DOMAIN ANCHORS": [(domain, domain) for domain in anchors],
        "TRANSFER PATTERNS": [(0,)],
        "DOMAIN CONTEXT ENTITIES": [("invoice", 103)],
    }
    return {"census": {"sections": sections}, "copilots": {}, "age": {}, "integrity": {}}


def _compute_observed_verdict(state: dict[str, Any]) -> tuple[str, dict[str, list[str]]]:
    state["integrity"] = platform_dump._check_integrity(state)
    return platform_dump._compute_verdict(state)


def test_collect_copilot_unreachable() -> None:
    result = platform_dump._collect_copilot_state("trading", 99999)
    assert result["health"] is None
    assert any("unreachable" in error for error in result["errors"])


def test_collect_age_unreachable() -> None:
    result = platform_dump._collect_age_state(
        "host=invalid port=9999 dbname=x user=x password=x sslmode=disable", "g"
    )
    assert result["reachable"] is False
    assert "error" in result


def test_integrity_all_present() -> None:
    checks = platform_dump._check_integrity(_state())
    assert checks["all_decisions"] is True
    assert checks["all_conservation"] is True
    assert checks["all_anchors"] is True


def test_integrity_missing_conservation() -> None:
    assert platform_dump._check_integrity(_state(conservation=0))["all_conservation"] is False


def test_verdict_ready() -> None:
    state = _state()
    state["integrity"] = platform_dump._check_integrity(state)
    assert platform_dump._compute_verdict(state) == (
        "READY",
        {"blocking": [], "expected_limitations": [], "pending_operations": []},
    )


def test_verdict_not_ready_transfers() -> None:
    state = _state(transfers=0)
    state["integrity"] = platform_dump._check_integrity(state)
    verdict, categories = platform_dump._compute_verdict(state)
    assert verdict == "READY"
    assert categories["blocking"] == []
    assert categories["pending_operations"] == ["transfer_patterns"]


def test_verdict_does_not_block_on_checkpoint_coverage() -> None:
    state = _state()
    state["census"]["sections"]["CHECKPOINTS PER DOMAIN"] = []
    state["integrity"] = platform_dump._check_integrity(state)
    assert state["integrity"]["all_checkpoints"] is False
    verdict, categories = platform_dump._compute_verdict(state)
    assert verdict == "READY"
    assert categories["blocking"] == []
    assert categories["expected_limitations"] == [
        f"{domain}:checkpoints" for domain in DOMAINS
    ]


def test_verdict_classifies_soc_receipt_limitation() -> None:
    state = _state(transfers=0)
    state["census"]["sections"]["FINGERPRINTS PER DOMAIN"] = [
        ("soc", 1), ("s2p", 1), ("trading", 1), ("purchasing", 1), ("dataops", 1)
    ]
    state["census"]["sections"]["EVIDENCE RECEIPTS PER DOMAIN"] = [
        ("soc", 0), ("s2p", 1), ("trading", 1), ("purchasing", 1), ("dataops", 1)
    ]
    state["census"]["sections"]["CHECKPOINTS PER DOMAIN"] = [
        ("s2p", 1), ("dataops", 1)
    ]
    state["census"]["sections"]["DOMAIN CONTEXT ENTITIES"] = []
    state["integrity"] = platform_dump._check_integrity(state)

    verdict, categories = platform_dump._compute_verdict(state)

    assert verdict == "READY"
    assert categories["blocking"] == []
    assert categories["expected_limitations"] == [
        "soc:evidence_receipts",
        "soc:checkpoints",
        "trading:checkpoints",
        "purchasing:checkpoints",
    ]


def test_verdict_green_soc_without_receipts_is_ready() -> None:
    state = _state()
    state["census"]["sections"]["EVIDENCE RECEIPTS PER DOMAIN"] = [
        ("soc", 0), ("s2p", 1), ("trading", 1), ("purchasing", 1), ("dataops", 1)
    ]
    state["copilots"] = {"soc": {"diagnostics": {"conservation": {"conservation_status": "GREEN"}}}}
    state["integrity"] = platform_dump._check_integrity(state)

    verdict, categories = platform_dump._compute_verdict(state)

    assert verdict == "READY"
    assert categories["blocking"] == []
    assert categories["expected_limitations"] == ["soc:evidence_receipts"]


def test_verdict_red_soc_without_receipts_is_also_ready() -> None:
    state = _state()
    state["census"]["sections"]["EVIDENCE RECEIPTS PER DOMAIN"] = [
        ("soc", 0), ("s2p", 1), ("trading", 1), ("purchasing", 1), ("dataops", 1)
    ]
    state["copilots"] = {"soc": {"diagnostics": {"conservation": {"conservation_status": "RED"}}}}
    state["integrity"] = platform_dump._check_integrity(state)

    verdict, categories = platform_dump._compute_verdict(state)

    assert verdict == "READY"
    assert categories["blocking"] == []
    assert categories["expected_limitations"] == ["soc:evidence_receipts"]


def test_verdict_soc_receipts_remove_limitation() -> None:
    state = _state()
    state["copilots"] = {"soc": {"diagnostics": {"conservation": {"conservation_status": "GREEN"}}}}
    state["integrity"] = platform_dump._check_integrity(state)

    verdict, categories = platform_dump._compute_verdict(state)

    assert verdict == "READY"
    assert categories["blocking"] == []
    assert categories["expected_limitations"] == []


def test_verdict_blocks_missing_non_soc_receipts() -> None:
    state = _state()
    state["census"]["sections"]["EVIDENCE RECEIPTS PER DOMAIN"] = [
        ("soc", 0), ("s2p", 1), ("trading", 0), ("purchasing", 1), ("dataops", 1)
    ]
    state["integrity"] = platform_dump._check_integrity(state)

    verdict, categories = platform_dump._compute_verdict(state)

    assert verdict == "NOT READY"
    assert categories["blocking"] == ["all_receipts"]
    assert categories["pending_operations"] == []


def test_verdict_blocks_missing_artifact_for_green_copilot() -> None:
    state = _state()
    state["census"]["sections"]["FINGERPRINTS PER DOMAIN"] = [
        ("soc", 1), ("s2p", 1), ("trading", 0), ("purchasing", 1), ("dataops", 1)
    ]
    state["copilots"] = {
        "trading": {"diagnostics": {"conservation": {"conservation_status": "GREEN"}}}
    }
    state["integrity"] = platform_dump._check_integrity(state)

    verdict, categories = platform_dump._compute_verdict(state)

    assert verdict == "NOT READY"
    assert categories["blocking"] == ["all_fingerprints"]


def test_observed_pre_fix_census_has_all_four_blockers() -> None:
    state = _observed_verdict_state()

    verdict, categories = _compute_observed_verdict(state)

    checks = state["integrity"]
    assert checks["all_conservation"] is False
    assert checks["all_fingerprints"] is False
    assert checks["all_anchors"] is False
    assert checks["all_receipts"] is False
    assert verdict == "NOT READY"
    assert categories["blocking"] == [
        "all_conservation",
        "all_anchors",
        "all_fingerprints",
        "all_receipts",
    ]


def test_expected_post_fix_census_is_ready_with_documented_categories() -> None:
    state = _observed_verdict_state(
        soc_conservation=1,
        soc_fingerprints=1,
        soc_anchor=True,
        dataops_receipts=200,
    )

    verdict, categories = _compute_observed_verdict(state)

    checks = state["integrity"]
    assert checks["all_conservation"] is True
    assert checks["all_fingerprints"] is True
    assert checks["all_anchors"] is True
    assert checks["all_receipts"] is False
    assert verdict == "READY"
    assert categories == {
        "blocking": [],
        "expected_limitations": ["soc:evidence_receipts"],
        "pending_operations": ["transfer_patterns", "monetary_entities"],
    }


@pytest.mark.parametrize(
    ("overrides", "blocking_gate"),
    [
        ({"soc_anchor": False}, "all_anchors"),
        ({"soc_conservation": 0, "dataops_receipts": 0}, "all_conservation"),
        ({"dataops_receipts": 0}, "all_receipts"),
        ({"soc_conservation": 0, "dataops_receipts": 200}, "all_conservation"),
    ],
)
def test_partial_verdict_repairs_remain_not_ready(
    overrides: dict[str, Any],
    blocking_gate: str,
) -> None:
    settings: dict[str, Any] = {
        "soc_conservation": 1,
        "soc_fingerprints": 1,
        "soc_anchor": True,
        "dataops_receipts": 200,
    }
    settings.update(overrides)
    state = _observed_verdict_state(**settings)

    verdict, categories = _compute_observed_verdict(state)

    assert verdict == "NOT READY"
    assert blocking_gate in categories["blocking"]


def test_all_domains_with_receipts_are_ready_without_receipt_limitation() -> None:
    state = _observed_verdict_state(
        soc_conservation=1,
        soc_fingerprints=1,
        soc_anchor=True,
        dataops_receipts=200,
        soc_receipts=1,
    )

    verdict, categories = _compute_observed_verdict(state)

    assert verdict == "READY"
    assert state["integrity"]["all_receipts"] is True
    assert "soc:evidence_receipts" not in categories["expected_limitations"]


def test_two_missing_non_soc_receipt_domains_block_without_exemption() -> None:
    state = _observed_verdict_state(
        soc_conservation=1,
        soc_fingerprints=1,
        soc_anchor=True,
        dataops_receipts=200,
        missing_non_soc_receipts=("trading", "purchasing"),
    )

    verdict, categories = _compute_observed_verdict(state)

    assert verdict == "NOT READY"
    assert categories["blocking"] == ["all_receipts"]
    assert "soc:evidence_receipts" not in categories["expected_limitations"]


def test_soc_conservation_has_no_exemption() -> None:
    state = _observed_verdict_state(
        soc_conservation=0,
        soc_fingerprints=1,
        soc_anchor=True,
        dataops_receipts=200,
    )

    verdict, categories = _compute_observed_verdict(state)

    assert verdict == "NOT READY"
    assert categories["blocking"] == ["all_conservation"]
    assert categories["expected_limitations"] == ["soc:evidence_receipts"]


def test_post_fix_raw_integrity_preserves_missing_soc_receipt_truth() -> None:
    state = _observed_verdict_state(
        soc_conservation=1,
        soc_fingerprints=1,
        soc_anchor=True,
        dataops_receipts=200,
    )

    verdict, categories = _compute_observed_verdict(state)

    assert state["integrity"]["receipts"]["soc"] == 0
    assert state["integrity"]["all_receipts"] is False
    assert verdict == "READY"
    assert categories["expected_limitations"] == ["soc:evidence_receipts"]


def test_dump_creates_json(tmp_path) -> None:
    path = platform_dump.dump_to_file(_state(), tmp_path)
    assert path.exists()
    assert "platform_dump_" in path.name
    json.loads(path.read_text(encoding="utf-8"))


def test_print_summary_no_crash(capsys) -> None:
    platform_dump.print_summary(_state())
    assert "VERDICT" in capsys.readouterr().out


def test_port_map_matches_demo() -> None:
    import demo

    expected = {
        str(item["name"]).lower(): int(item["be_port"])
        for item in cast(list[dict[str, Any]], demo.COPILOTS)
    }
    assert platform_dump.COPILOT_PORTS == expected


def test_census_reuse() -> None:
    from scripts.graph_census_v2 import run_census

    assert callable(run_census)
    assert platform_dump.run_census is run_census
