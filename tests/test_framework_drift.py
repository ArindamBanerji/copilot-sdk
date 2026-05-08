"""
Drift detector: framework files in copilot-sdk vs SOC (canonical source),
and S2P vs SOC (secondary consumer).

SOC is the source of truth (Q3 confirmed). A mismatch means SOC was updated
and the consumer backport hasn't happened yet. Intentional divergences are
listed in KNOWN_DRIFT / S2P_KNOWN_DRIFT with a reason and backlog ticket.

Skips entirely when SOC_FRAMEWORK_DIR is absent (CI without both repos).
S2P tests skip individually when S2P_FRAMEWORK_DIR is absent.
"""
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative from repo root)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
SDK_FRAMEWORK_DIR = REPO_ROOT / "copilot_sdk" / "framework"
SOC_FRAMEWORK_DIR = (
    REPO_ROOT / ".." / "gen-ai-roi-demo-v4-v50" / "backend" / "app" / "framework"
).resolve()
S2P_FRAMEWORK_DIR = (
    REPO_ROOT / ".." / "s2p-copilot" / "backend" / "app" / "framework"
).resolve()

# ---------------------------------------------------------------------------
# Intentional drift — update this table, never suppress a test failure silently.
# Format: filename → human reason + backlog reference.
# ---------------------------------------------------------------------------
KNOWN_DRIFT = {
    "override_detector.py": "SOC-only. Not in SDK. Expected.",
    "audit.py": "app.framework.feedback_store and app.db.neo4j imports guarded with try/except ImportError. SDK standalone requirement.",
    "composite_gate.py": "Import path adapted: app.framework → copilot_sdk.framework. SDK namespace requirement.",
    "feedback_base.py": "Import path adapted: app.framework → copilot_sdk.framework. SDK namespace requirement.",
}

# ---------------------------------------------------------------------------
# Skip guard — must be module-level so collection itself is skipped.
# ---------------------------------------------------------------------------
if not SOC_FRAMEWORK_DIR.exists():
    pytest.skip(
        f"SOC framework directory not found at {SOC_FRAMEWORK_DIR} — "
        "skipping drift tests (CI environment without both repos)",
        allow_module_level=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _py_files(directory: Path) -> set[str]:
    return {
        p.name
        for p in directory.glob("*.py")
        if p.name != "__init__.py"
    }


def _read(path: Path) -> bytes:
    return path.read_bytes()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_unknown_drift():
    """Files present in both repos must be byte-identical unless listed in KNOWN_DRIFT."""
    sdk_files = _py_files(SDK_FRAMEWORK_DIR)
    soc_files = _py_files(SOC_FRAMEWORK_DIR)
    common = sdk_files & soc_files

    unknown_drifts = []
    for name in sorted(common):
        sdk_bytes = _read(SDK_FRAMEWORK_DIR / name)
        soc_bytes = _read(SOC_FRAMEWORK_DIR / name)
        if sdk_bytes != soc_bytes and name not in KNOWN_DRIFT:
            delta = abs(len(soc_bytes) - len(sdk_bytes))
            unknown_drifts.append(
                f"  {name}: byte delta={delta} "
                f"(SDK={len(sdk_bytes)}B, SOC={len(soc_bytes)}B) — "
                "not listed in KNOWN_DRIFT"
            )

    assert not unknown_drifts, (
        "Undocumented drift detected between SDK and SOC framework files.\n"
        "Either backport the SOC change or add an entry to KNOWN_DRIFT:\n"
        + "\n".join(unknown_drifts)
    )


def test_known_drift_documented():
    """Every KNOWN_DRIFT entry must actually exist and actually differ; stale entries fail."""
    sdk_files = _py_files(SDK_FRAMEWORK_DIR)
    soc_files = _py_files(SOC_FRAMEWORK_DIR)
    stale = []

    for name, reason in KNOWN_DRIFT.items():
        soc_exists = name in soc_files
        sdk_exists = name in sdk_files

        if not soc_exists:
            stale.append(f"  {name}: not found in SOC — remove from KNOWN_DRIFT")
            continue

        if sdk_exists:
            sdk_bytes = _read(SDK_FRAMEWORK_DIR / name)
            soc_bytes = _read(SOC_FRAMEWORK_DIR / name)
            if sdk_bytes == soc_bytes:
                stale.append(
                    f"  {name}: files are now identical — "
                    "drift was backported; remove from KNOWN_DRIFT"
                )

    assert not stale, (
        "Stale entries in KNOWN_DRIFT (files no longer differ or no longer exist):\n"
        + "\n".join(stale)
    )


def test_sdk_has_no_extra_files():
    """SDK framework must be a subset of SOC — no files in SDK that don't exist in SOC."""
    sdk_files = _py_files(SDK_FRAMEWORK_DIR)
    soc_files = _py_files(SOC_FRAMEWORK_DIR)
    extras = sorted(sdk_files - soc_files)

    assert not extras, (
        "SDK framework contains files not present in SOC (SDK is meant to be a subset):\n"
        + "\n".join(f"  {f}" for f in extras)
    )


# ---------------------------------------------------------------------------
# S2P ↔ SOC drift
# ---------------------------------------------------------------------------

S2P_KNOWN_DRIFT = {
    "agent.py": "Minor diff. 1 byte. Backport pending.",
    "audit.py": "SOC canonical — async, OutcomeEntry, epoch archive. -5118 bytes in S2P. Backport pending.",
    "checkpoint.py": "SOC extended with PITR backup integration. -747 bytes in S2P. Backport pending.",
    "composite_gate.py": "Same size, different content (category threshold names differ). Backport pending.",
    "decision_history.py": "Minor diff. 6 bytes. Backport pending.",
    "feedback_base.py": "Minor diff. 3 bytes. Backport pending.",
    "intervention_controls.py": "SOC extended with conservation wiring. -114 bytes in S2P. Backport pending.",
    "provenance.py": "SOC extended with W2 provenance fields. -131 bytes in S2P. Backport pending.",
    "shadow_mode.py": "SOC minor extension. -18 bytes in S2P. Backport pending.",
    "similar_cases_base.py": "Minor diff. 13 bytes. Backport pending.",
}


def test_s2p_no_unknown_drift():
    """S2P framework files must be byte-identical to SOC unless listed in S2P_KNOWN_DRIFT."""
    if not S2P_FRAMEWORK_DIR.exists():
        pytest.skip(
            f"S2P framework directory not found at {S2P_FRAMEWORK_DIR} — "
            "skipping S2P drift test"
        )

    s2p_files = _py_files(S2P_FRAMEWORK_DIR)
    soc_files = _py_files(SOC_FRAMEWORK_DIR)
    common = s2p_files & soc_files

    unknown_drifts = []
    for name in sorted(common):
        s2p_bytes = _read(S2P_FRAMEWORK_DIR / name)
        soc_bytes = _read(SOC_FRAMEWORK_DIR / name)
        if s2p_bytes != soc_bytes and name not in S2P_KNOWN_DRIFT:
            delta = abs(len(soc_bytes) - len(s2p_bytes))
            unknown_drifts.append(
                f"  {name}: byte delta={delta} "
                f"(S2P={len(s2p_bytes)}B, SOC={len(soc_bytes)}B) — "
                "not listed in S2P_KNOWN_DRIFT"
            )

    assert not unknown_drifts, (
        "Undocumented drift detected between S2P and SOC framework files.\n"
        "Either backport the SOC change or add an entry to S2P_KNOWN_DRIFT:\n"
        + "\n".join(unknown_drifts)
    )


def test_s2p_known_drift_documented():
    """Every S2P_KNOWN_DRIFT entry must actually exist and actually differ; stale entries fail."""
    if not S2P_FRAMEWORK_DIR.exists():
        pytest.skip(
            f"S2P framework directory not found at {S2P_FRAMEWORK_DIR} — "
            "skipping S2P drift test"
        )

    s2p_files = _py_files(S2P_FRAMEWORK_DIR)
    soc_files = _py_files(SOC_FRAMEWORK_DIR)
    stale = []

    for name, reason in S2P_KNOWN_DRIFT.items():
        soc_exists = name in soc_files
        s2p_exists = name in s2p_files

        if not soc_exists:
            stale.append(f"  {name}: not found in SOC — remove from S2P_KNOWN_DRIFT")
            continue

        if s2p_exists:
            s2p_bytes = _read(S2P_FRAMEWORK_DIR / name)
            soc_bytes = _read(SOC_FRAMEWORK_DIR / name)
            if s2p_bytes == soc_bytes:
                stale.append(
                    f"  {name}: files are now identical — "
                    "drift was backported; remove from S2P_KNOWN_DRIFT"
                )

    assert not stale, (
        "Stale entries in S2P_KNOWN_DRIFT (files no longer differ or no longer exist):\n"
        + "\n".join(stale)
    )
