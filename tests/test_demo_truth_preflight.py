from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


preseed = _load("demo_preseed", "scripts/preseed_all_copilots.py")
preflight = _load("demo_truth_preflight", "scripts/demo_truth_preflight.py")


class CompleteClient:
    def __init__(self, spec: Any, bad_metric: bool = False) -> None:
        self.spec = spec
        self.bad_metric = bad_metric

    def get(self, _base_url: str, path: str) -> dict[str, Any]:
        if path in self.spec.health:
            return {"status": "ok"}
        if path in self.spec.trajectory:
            return {"iks": 0.42, "verified_count": 60, "decisions_total": 80, "phase": "GREEN"}
        if path in self.spec.twins:
            return {"status": "frozen", "snapshot_id": "day-0"}
        if path in self.spec.promotions:
            return {"records": [{"stage": "shadowing"}, {"stage": "shadowing"}]}
        if path in self.spec.claims:
            return {"claims": [{"claim_id": "demo", "evidence_tier": "T_O"}]}
        if path in self.spec.metrics:
            if self.bad_metric:
                return {"is_sample_data": True, "provenance": "sample", "accuracy": 0.9}
            return {"evidence_tier": "T_O", "evidence_label": "observed", "verified_count": 60}
        raise RuntimeError("missing path")


def test_s2p_seed_vectors_are_bounded_and_cover_categories() -> None:
    events = [preseed.s2p_event(index) for index in range(200)]
    assert len({event["category"] for event in events}) == 5
    for event in events:
        assert 0.0 <= event["duplicate_score"] <= 1.0
        assert 0.0 <= event["tax_regulatory_compliance"] <= 1.0
        assert event["amount"] > 0


def test_s2p_seed_has_confirm_and_override_schedule() -> None:
    outcomes = ["overridden" if (index + 1) % 4 == 0 else "confirmed" for index in range(200)]
    assert outcomes.count("overridden") == 50
    assert outcomes.count("confirmed") == 150


def test_preflight_passes_complete_copilot() -> None:
    spec = preflight.SPECS["trading"]
    assert preflight.check_copilot(spec, CompleteClient(spec)) == []


def test_preflight_rejects_f26_sample_metric() -> None:
    spec = preflight.SPECS["trading"]
    failures = preflight.check_copilot(spec, CompleteClient(spec, bad_metric=True))
    assert any("F-26" in failure for failure in failures)


def test_preflight_rejects_f27_synthetic_measured_label() -> None:
    spec = preflight.SPECS["trading"]

    class SyntheticMeasured(CompleteClient):
        def get(self, base_url: str, path: str) -> dict[str, Any]:
            payload = super().get(base_url, path)
            if path in self.spec.metrics:
                payload.update({"evidence_label": "measured", "source": "synthetic_preseed"})
            return payload

    failures = preflight.check_copilot(spec, SyntheticMeasured(spec))
    assert any("F-27" in failure for failure in failures)


def test_preflight_rejects_missing_twin_and_promotion() -> None:
    spec = preflight.SPECS["trading"]

    class MissingArtifacts(CompleteClient):
        def get(self, base_url: str, path: str) -> dict[str, Any]:
            if path in self.spec.twins or path in self.spec.promotions:
                raise RuntimeError("not found")
            return super().get(base_url, path)

    failures = preflight.check_copilot(spec, MissingArtifacts(spec))
    assert any("Frozen Twin" in failure for failure in failures)
    assert any("promotion records" in failure for failure in failures)


def test_preflight_dry_run_is_read_only() -> None:
    assert preflight.main(["--dry-run", "--copilots", "trading", "s2p"]) == 0


def test_launcher_exposes_preseed_and_preflight_flags() -> None:
    demo = _load("demo_launcher", "demo.py")
    args = demo.create_parser().parse_args(["--preseed", "--preflight", "--no-browser"])
    assert args.preseed is True
    assert args.preflight is True
