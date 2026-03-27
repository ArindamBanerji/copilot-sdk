"""
tests/test_framework_discipline.py — CopilotFramework extraction discipline.

Enforces the boundary rules required for clean future extraction to copilot-sdk.
These tests must pass before any new file is added to copilot_sdk/framework/.

Run from copilot-sdk/:
    pytest tests/test_framework_discipline.py -v
"""

import ast
import importlib
import pathlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ============================================================================
# Test 1 — Framework files must have zero domain or router imports
# ============================================================================

def test_framework_has_no_domain_imports():
    """
    Framework files must never import from app.domains or app.routers.
    This test enforces the copilot-sdk extraction discipline.
    Fails immediately if the boundary is violated.
    """
    framework_dir = pathlib.Path("copilot_sdk/framework")
    forbidden_prefixes = ("app.domains", "app.routers")

    violations = []
    for py_file in sorted(framework_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = getattr(node, "module", "") or ""
                for fp in forbidden_prefixes:
                    if module.startswith(fp):
                        violations.append(f"{py_file.name}: imports {module}")

    assert violations == [], f"Framework discipline violations: {violations}"


# ============================================================================
# Test 2 — All framework modules importable without error
# ============================================================================

def test_framework_modules_importable():
    """All framework modules import without error."""
    modules = [
        "copilot_sdk.framework.ols_status",
        "copilot_sdk.framework.event_bus",
        "copilot_sdk.framework.decision_history",
        "copilot_sdk.framework.checkpoint",
        "copilot_sdk.framework.economics",
        "copilot_sdk.framework.shadow_mode",
        "copilot_sdk.framework.composite_gate",
        "copilot_sdk.framework.agent",
        "copilot_sdk.framework.intervention_controls",
        "copilot_sdk.framework.convergence_math",
        "copilot_sdk.framework.feedback_store",
        "copilot_sdk.framework.audit",
        "copilot_sdk.framework.provenance",
        "copilot_sdk.framework.narrative_base",
        "copilot_sdk.framework.similar_cases_base",
        "copilot_sdk.framework.iks_base",
        "copilot_sdk.framework.learning_state",
        "copilot_sdk.framework.feedback_base",
    ]
    for m in modules:
        mod = importlib.import_module(m)
        assert mod is not None, f"Module {m} returned None"


# ============================================================================
# Test 3 — IKS formula: cold-start returns 0.0
# ============================================================================

def test_iks_cold_start_returns_zero():
    """
    compute_iks with mu == mu_zero should return IKS current = 0.0.
    No drift from cold-start centroids means zero institutional knowledge.
    """
    import numpy as np
    from copilot_sdk.framework.iks_base import compute_iks

    mu_zero = np.full((2, 3, 2), 0.5)
    mu_t    = np.full((2, 3, 2), 0.5)   # no drift
    result  = compute_iks(mu_t, mu_zero, d_max=0.20)
    assert result["current"] == 0.0, (
        f"Cold-start IKS must be 0.0, got {result['current']}"
    )
