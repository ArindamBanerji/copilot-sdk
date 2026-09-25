import importlib
from pathlib import Path


FRAMEWORK = Path(__file__).parents[1] / "copilot_sdk" / "framework"


def test_audit_no_app_import() -> None:
    source = (FRAMEWORK / "audit.py").read_text(encoding="utf-8")
    assert "from app." not in source
    module = importlib.import_module("copilot_sdk.framework.audit")
    assert hasattr(module, "reconstruct_from_memory")


def test_intervention_no_app_import() -> None:
    source = (FRAMEWORK / "intervention_controls.py").read_text(encoding="utf-8")
    assert "from app." not in source
    module = importlib.import_module("copilot_sdk.framework.intervention_controls")
    assert hasattr(module, "InterventionControls")
