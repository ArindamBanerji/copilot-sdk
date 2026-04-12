"""
tests/test_discipline.py — SDK boundary discipline tests.

Enforces:
 - No domain-specific imports (domains.soc, domains.s2p)
 - Protocol API contracts match GAE Tier 1 expectations
 - SDK imports clean with no heavy ML dependencies

Run from copilot-sdk/:
    pytest tests/test_discipline.py -v
"""
import ast
import pathlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

SDK_ROOT = pathlib.Path(__file__).parent.parent / "copilot_sdk"

FORBIDDEN_IMPORT_PREFIXES = (
    "app.domains.soc",
    "app.domains.s2p",
)

# Packages with hyphens cannot appear in normal import statements;
# they could only be loaded via importlib — scan source text for these.
FORBIDDEN_STRINGS = ("gen-ai-roi-demo",)

HEAVY_DEPS = ("torch", "tensorflow", "transformers", "sklearn")


# ============================================================================
# TestNoDomainImports — SDK must never pull in domain-specific modules
# ============================================================================

class TestNoDomainImports:

    def test_no_soc_modules_in_sys_modules(self):
        """No domains.soc module appears in sys.modules after importing copilot_sdk."""
        import copilot_sdk  # noqa: F401
        violations = [k for k in sys.modules if "domains.soc" in k]
        assert violations == [], f"Forbidden SOC modules loaded: {violations}"

    def test_no_s2p_modules_in_sys_modules(self):
        """No domains.s2p module appears in sys.modules after importing copilot_sdk."""
        import copilot_sdk  # noqa: F401
        violations = [k for k in sys.modules if "domains.s2p" in k]
        assert violations == [], f"Forbidden S2P modules loaded: {violations}"

    def test_sdk_source_has_no_forbidden_imports(self):
        """
        AST scan of all .py files under copilot_sdk/ for forbidden import patterns.
        Also scans source text for importlib-style references to forbidden packages.
        """
        violations = []
        for py_file in sorted(SDK_ROOT.rglob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                # from <module> import ...
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for fp in FORBIDDEN_IMPORT_PREFIXES:
                        if module.startswith(fp):
                            violations.append(
                                f"{py_file.name}: 'from {module} import ...'"
                            )
                # import <name>
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        for fp in FORBIDDEN_IMPORT_PREFIXES:
                            if alias.name.startswith(fp):
                                violations.append(
                                    f"{py_file.name}: 'import {alias.name}'"
                                )

            # Text scan for hyphenated package names unreachable by AST
            for fs in FORBIDDEN_STRINGS:
                if fs in source:
                    violations.append(
                        f"{py_file.name}: contains reference to '{fs}'"
                    )

        assert violations == [], f"Discipline violations found:\n" + "\n".join(violations)


# ============================================================================
# TestProtocolsMatchGAE — Protocol API contracts
# ============================================================================

class TestProtocolsMatchGAE:

    def test_domain_config_has_required_methods(self):
        """DomainConfig defines all four lifecycle methods required by GAE Tier 1."""
        from copilot_sdk.protocols import DomainConfig
        required = [
            "get_initial_centroids",
            "get_sigma_profile",
            "get_category_index",
            "get_action_index",
        ]
        missing = [m for m in required if not hasattr(DomainConfig, m)]
        assert missing == [], f"DomainConfig missing required methods: {missing}"

    def test_factor_computer_has_compute_method(self):
        """FactorComputer defines compute(event) -> float as required by GAE."""
        from copilot_sdk.protocols import FactorComputer
        assert hasattr(FactorComputer, "compute"), (
            "FactorComputer must define compute(event) -> float in [0.0, 1.0]"
        )

    def test_source_connector_and_referral_rule_api(self):
        """SourceConnector has fetch/validate; ReferralRule has evaluate."""
        from copilot_sdk.protocols import SourceConnector, ReferralRule
        assert hasattr(SourceConnector, "fetch"), (
            "SourceConnector must define fetch(entity_id) -> list[dict]"
        )
        assert hasattr(SourceConnector, "validate"), (
            "SourceConnector must define validate(record) -> bool"
        )
        assert hasattr(ReferralRule, "evaluate"), (
            "ReferralRule must define evaluate(context) -> dict"
        )


# ============================================================================
# TestSDKImportClean — Import hygiene
# ============================================================================

class TestSDKImportClean:

    def test_copilot_sdk_import_succeeds(self):
        """Top-level `import copilot_sdk` completes without error and is versioned."""
        import copilot_sdk
        assert copilot_sdk is not None
        assert hasattr(copilot_sdk, "__version__"), (
            "copilot_sdk must expose __version__"
        )

    def test_no_heavy_ml_deps_on_import(self):
        """
        Importing copilot_sdk must not trigger torch, tensorflow,
        transformers, or sklearn. Heavy deps make the SDK unusable in
        lightweight environments.
        """
        import copilot_sdk  # noqa: F401
        loaded = [dep for dep in HEAVY_DEPS if dep in sys.modules]
        assert loaded == [], (
            f"Heavy ML dependencies must not be loaded on import: {loaded}"
        )
