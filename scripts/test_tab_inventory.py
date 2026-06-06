#!/usr/bin/env python3
"""
test_tab_inventory.py — Tests for tab_inventory.py

Run:
  cd $CLAUDE_SDK
  python -m pytest scripts/test_tab_inventory.py -v --timeout=60

  # With live backends (for smoke tests):
  python -m pytest scripts/test_tab_inventory.py -v --timeout=60 -k "not live"
"""

import json
import os
import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test — adjust path as needed
import sys
sys.path.insert(0, str(Path(__file__).parent))
from tab_inventory import (
    _safe_name,
    _is_tab_noise,
    _prettify_id,
    _extract_tabs_from_source,
    _extract_components,
    _extract_api_calls,
    _validate_tabs,
    _substitute_smoke_ids,
    scan_frontend_static,
    generate_markdown,
    COPILOTS,
    SOC_CONFIG,
)


# =========================================================================
# P1: _safe_name — sanitized copilot names
# =========================================================================
class TestSafeName:

    def test_lowercase(self):
        assert _safe_name("Trading") == "trading"

    def test_replaces_special_chars(self):
        assert _safe_name("S2P-Preview") == "s2p_preview"

    def test_replaces_spaces(self):
        assert _safe_name("Log Trade") == "log_trade"

    def test_plain_name_unchanged(self):
        assert _safe_name("dataops") == "dataops"

    def test_backtick_removed(self):
        """P1 fix: backticks in names could break JS interpolation."""
        assert "`" not in _safe_name("test`injection")

    def test_quotes_removed(self):
        assert "'" not in _safe_name("test'injection")
        assert '"' not in _safe_name('test"injection')


# =========================================================================
# P2: Tab extraction — merged strategies
# =========================================================================
class TestTabExtraction:

    def test_shell_screen_config(self):
        """CopilotShell pattern: screens={[{ name: "Dashboard" }, ...]}"""
        source = '''
        const screens = [
            { name: "Dashboard", component: DashboardScreen },
            { name: "Analysis", component: AnalysisScreen },
            { name: "Performance", component: PerformanceScreen },
        ];
        '''
        tabs = _extract_tabs_from_source(source)
        assert "Dashboard" in tabs
        assert "Analysis" in tabs
        assert "Performance" in tabs

    def test_config_array_nav(self):
        """SOC-style: { id: 'evolution', label: 'Evolution', component: X }"""
        source = '''
        const tabs = [
            { id: 'analytics', label: 'Analytics', component: AnalyticsTab },
            { id: 'evolution', label: 'Evolution', component: EvolutionTab },
            { id: 'triage', label: 'Triage', component: TriageTab },
        ];
        '''
        tabs = _extract_tabs_from_source(source)
        assert "Analytics" in tabs
        assert "Evolution" in tabs
        assert "Triage" in tabs

    def test_strategies_merge_not_shadow(self):
        """P2 fix: config-array + shell screens should merge, not shadow."""
        source = '''
        const tabs = [
            { id: 'tab1', label: 'Alpha', component: AlphaTab },
            { id: 'tab2', label: 'Beta', component: BetaTab },
        ];
        const screens = [
            { name: "Gamma", component: GammaScreen },
        ];
        '''
        tabs = _extract_tabs_from_source(source)
        assert "Alpha" in tabs
        assert "Beta" in tabs
        assert "Gamma" in tabs

    def test_deduplication(self):
        """Same tab name from multiple strategies should appear once."""
        source = '''
        const tabs = [
            { id: 'dash', label: 'Dashboard', component: DashTab },
        ];
        const screens = [
            { name: "Dashboard", component: DashboardScreen },
        ];
        '''
        tabs = _extract_tabs_from_source(source)
        assert tabs.count("Dashboard") == 1

    def test_noise_filtered(self):
        """CSS classes and generic strings should not appear as tabs."""
        source = '''
        const x = { label: "flex", component: Foo };
        const y = { label: "mb-4", component: Bar };
        const z = { name: "Dashboard", component: DashScreen };
        '''
        tabs = _extract_tabs_from_source(source)
        assert "flex" not in tabs
        assert "mb-4" not in tabs
        assert "Dashboard" in tabs

    def test_screen_import_fallback(self):
        """When no config/shell found, fall back to screen imports."""
        source = '''
        import DashboardScreen from './screens/DashboardScreen';
        import AnalysisScreen from './screens/AnalysisScreen';
        '''
        tabs = _extract_tabs_from_source(source)
        assert "Dashboard" in tabs
        assert "Analysis" in tabs


# =========================================================================
# Tab noise filtering
# =========================================================================
class TestTabNoise:

    def test_css_class_is_noise(self):
        assert _is_tab_noise("rounded-md")
        assert _is_tab_noise("flex")

    def test_too_short(self):
        assert _is_tab_noise("X")

    def test_too_long(self):
        assert _is_tab_noise("A" * 31)

    def test_real_tab_not_noise(self):
        assert not _is_tab_noise("Dashboard")
        assert not _is_tab_noise("Log Trade")
        assert not _is_tab_noise("S2P Preview")

    def test_title_case_not_noise(self):
        """Title-case strings should not be filtered even if they look CSS-ish."""
        assert not _is_tab_noise("Evidence")


# =========================================================================
# _prettify_id
# =========================================================================
class TestPrettifyId:

    def test_camelcase(self):
        assert _prettify_id("runtimeEvolution") == "Runtime Evolution"

    def test_kebab_case(self):
        assert _prettify_id("s2p-preview") == "S2P Preview"

    def test_underscore(self):
        assert _prettify_id("log_trade") == "Log Trade"

    def test_acronym_uppercase(self):
        assert _prettify_id("soc-dashboard") == "SOC Dashboard"
        assert _prettify_id("roi-summary") == "ROI Summary"


# =========================================================================
# P3: Smoke ID substitution
# =========================================================================
class TestSmokeIdSubstitution:

    def test_no_placeholders(self):
        assert _substitute_smoke_ids("/api/health", {}) == "/api/health"

    def test_single_placeholder(self):
        result = _substitute_smoke_ids("/api/s2p/insight/{id}", {"id": "S2P-INV-0001"})
        assert result == "/api/s2p/insight/S2P-INV-0001"

    def test_multiple_placeholders(self):
        result = _substitute_smoke_ids(
            "/api/{sys}/alert/{id}",
            {"sys": "sap_s4", "id": "ALERT-001"},
        )
        assert result == "/api/sap_s4/alert/ALERT-001"

    def test_unmapped_placeholder_returns_none(self):
        result = _substitute_smoke_ids("/api/{unknown_param}", {"id": "X"})
        assert result is None

    def test_partial_mapping(self):
        """One placeholder mapped, one not → None."""
        result = _substitute_smoke_ids(
            "/api/{sys}/detail/{unknown}",
            {"sys": "sap_s4"},
        )
        assert result is None


# =========================================================================
# P5: Tab validation
# =========================================================================
class TestTabValidation:

    def test_all_match(self):
        warnings = _validate_tabs(
            ["Dashboard", "Analysis", "Performance"],
            ["Dashboard", "Analysis", "Performance"],
        )
        assert len(warnings) == 0

    def test_missing_expected(self):
        warnings = _validate_tabs(
            ["Dashboard", "Analysis"],
            ["Dashboard", "Analysis", "Performance"],
        )
        warn_msgs = [w["message"] for w in warnings]
        assert any("Performance" in m for m in warn_msgs)
        assert warnings[0]["level"] == "WARN"

    def test_extra_detected(self):
        warnings = _validate_tabs(
            ["Dashboard", "Analysis", "Journal"],
            ["Dashboard", "Analysis"],
        )
        info_msgs = [w for w in warnings if w["level"] == "INFO"]
        assert any("Journal" in w["message"] for w in info_msgs)

    def test_case_insensitive(self):
        warnings = _validate_tabs(
            ["dashboard", "ANALYSIS"],
            ["Dashboard", "Analysis"],
        )
        assert len(warnings) == 0

    def test_empty_expected(self):
        warnings = _validate_tabs(["Dashboard"], [])
        # No expected tabs → no WARN, but detected tabs produce INFO
        warn_only = [w for w in warnings if w["level"] == "WARN"]
        assert len(warn_only) == 0


# =========================================================================
# P6: API call extraction with context filtering
# =========================================================================
class TestApiExtraction:

    def test_fetch_call_extracted(self):
        source = '''const r = fetch("/api/s2p/score");'''
        apis = _extract_api_calls(source)
        assert "/api/s2p/score" in apis

    def test_axios_get_extracted(self):
        source = '''const r = axios.get("/api/conservation/status");'''
        apis = _extract_api_calls(source)
        assert "/api/conservation/status" in apis

    def test_const_assignment_extracted(self):
        source = '''const ENDPOINT = "/api/s2p/preview/queue";'''
        apis = _extract_api_calls(source)
        assert "/api/s2p/preview/queue" in apis

    def test_comment_filtered(self):
        """P6 fix: API paths in comments should be filtered out."""
        source = '''// The endpoint /api/s2p/score is used for scoring'''
        apis = _extract_api_calls(source, context_filter=True)
        assert "/api/s2p/score" not in apis

    def test_error_message_filtered(self):
        source = '''console.error("Failed to call /api/health");'''
        apis = _extract_api_calls(source, context_filter=True)
        assert "/api/health" not in apis

    def test_context_filter_disabled(self):
        """With context_filter=False, non-marker lines are included."""
        source = '''log("/api/s2p/score")'''
        # With filter ON: log() is not a context marker → filtered out
        apis_on = _extract_api_calls(source, context_filter=True)
        assert "/api/s2p/score" not in apis_on
        # With filter OFF: included regardless of context
        apis_off = _extract_api_calls(source, context_filter=False)
        assert "/api/s2p/score" in apis_off

    def test_template_literal_cleaned(self):
        source = '''fetch(`/api/s2p/insight/${invoiceId}`);'''
        apis = _extract_api_calls(source)
        assert "/api/s2p/insight/{id}" in apis


# =========================================================================
# Component extraction
# =========================================================================
class TestComponentExtraction:

    def test_destructured_import(self):
        source = '''import { ScoreResultCard, TrajectoryChart } from '../components/shared';'''
        comps = _extract_components(source)
        assert "ScoreResultCard" in comps
        assert "TrajectoryChart" in comps

    def test_default_import(self):
        source = '''import FingerprintPanel from '../components/FingerprintPanel';'''
        comps = _extract_components(source)
        assert "FingerprintPanel" in comps


# =========================================================================
# Static scan on synthetic filesystem
# =========================================================================
class TestScanFrontendStatic:

    @pytest.fixture
    def mock_frontend(self, tmp_path):
        """Create a minimal frontend directory structure."""
        src = tmp_path / "src"
        screens = src / "screens"
        components = src / "components"
        screens.mkdir(parents=True)
        components.mkdir(parents=True)

        # App.tsx with CopilotShell config
        (src / "App.tsx").write_text('''
        const screens = [
            { name: "Dashboard", component: DashboardScreen },
            { name: "Analysis", component: AnalysisScreen },
        ];
        ''')

        # Screen files
        (screens / "DashboardScreen.tsx").write_text('''
        import { ScoreCard } from '../components/ScoreCard';
        const url = "/api/health";
        fetch(url);
        export default function DashboardScreen() { return <div/>; }
        ''')

        (screens / "AnalysisScreen.tsx").write_text('''
        import { Chart } from '../components/Chart';
        const r = axios.get("/api/analytics/patterns");
        export default function AnalysisScreen() { return <div/>; }
        ''')

        # Component files
        (components / "ScoreCard.tsx").write_text("export const ScoreCard = () => <div/>;")
        (components / "Chart.tsx").write_text("export const Chart = () => <div/>;")

        return src

    def test_detects_tabs(self, mock_frontend):
        config = {
            "accent": "red", "backend_port": 8010, "frontend_port": 5174,
            "expected_tabs": ["Dashboard", "Analysis"],
        }
        result = scan_frontend_static(mock_frontend, "test", config)
        assert "Dashboard" in result["tab_names"]
        assert "Analysis" in result["tab_names"]

    def test_finds_screens(self, mock_frontend):
        config = {
            "accent": "red", "backend_port": 8010, "frontend_port": 5174,
            "expected_tabs": ["Dashboard", "Analysis"],
        }
        result = scan_frontend_static(mock_frontend, "test", config)
        screen_files = [s["file"] for s in result["screens"]]
        assert "DashboardScreen.tsx" in screen_files
        assert "AnalysisScreen.tsx" in screen_files

    def test_finds_components(self, mock_frontend):
        config = {
            "accent": "red", "backend_port": 8010, "frontend_port": 5174,
            "expected_tabs": [],
        }
        result = scan_frontend_static(mock_frontend, "test", config)
        assert len(result["components"]) >= 2

    def test_extracts_api_calls(self, mock_frontend):
        config = {
            "accent": "red", "backend_port": 8010, "frontend_port": 5174,
            "expected_tabs": [],
        }
        result = scan_frontend_static(mock_frontend, "test", config)
        assert "/api/health" in result["api_calls"] or "/api/analytics/patterns" in result["api_calls"]

    def test_validation_warnings_on_missing_tab(self, mock_frontend):
        config = {
            "accent": "red", "backend_port": 8010, "frontend_port": 5174,
            "expected_tabs": ["Dashboard", "Analysis", "Performance"],
        }
        result = scan_frontend_static(mock_frontend, "test", config)
        warn_msgs = [w["message"] for w in result["warnings"]]
        assert any("Performance" in m for m in warn_msgs)

    def test_no_warnings_when_all_match(self, mock_frontend):
        config = {
            "accent": "red", "backend_port": 8010, "frontend_port": 5174,
            "expected_tabs": ["Dashboard", "Analysis"],
        }
        result = scan_frontend_static(mock_frontend, "test", config)
        warn_only = [w for w in result["warnings"] if w["level"] == "WARN"]
        assert len(warn_only) == 0

    def test_missing_path_returns_error(self):
        config = {
            "accent": "red", "backend_port": 8010, "frontend_port": 5174,
            "expected_tabs": [],
        }
        result = scan_frontend_static(Path("/nonexistent/path"), "test", config)
        assert "error" in result


# =========================================================================
# Markdown generation
# =========================================================================
class TestMarkdownGeneration:

    def test_includes_copilot_name(self):
        inventory = {
            "generated": "2026-06-04T00:00:00",
            "mode": "static",
            "copilots": [{
                "copilot": "trading",
                "accent": "red",
                "frontend_port": 5174,
                "backend_port": 8010,
                "tsx_file_count": 10,
                "tab_names": ["Dashboard"],
                "screens": [],
                "components": ["comp/A.tsx", "comp/B.tsx"],
                "api_calls": [],
                "warnings": [],
            }],
        }
        md = generate_markdown(inventory)
        assert "TRADING" in md

    def test_verbose_shows_components(self):
        inventory = {
            "generated": "2026-06-04T00:00:00",
            "mode": "static",
            "copilots": [{
                "copilot": "test",
                "accent": "red",
                "frontend_port": 5174,
                "backend_port": 8010,
                "tsx_file_count": 5,
                "tab_names": ["Dashboard"],
                "screens": [],
                "components": ["comp/A.tsx", "comp/B.tsx", "comp/C.tsx"],
                "api_calls": [],
                "warnings": [],
            }],
        }
        md_verbose = generate_markdown(inventory, verbose=True)
        md_compact = generate_markdown(inventory, verbose=False)
        assert "comp/A.tsx" in md_verbose
        assert "comp/A.tsx" not in md_compact
        assert "3 files" in md_compact

    def test_warnings_in_markdown(self):
        inventory = {
            "generated": "2026-06-04T00:00:00",
            "mode": "static",
            "copilots": [{
                "copilot": "test",
                "accent": "red",
                "frontend_port": 5174,
                "backend_port": 8010,
                "tsx_file_count": 5,
                "tab_names": ["Dashboard"],
                "screens": [],
                "components": [],
                "api_calls": [],
                "warnings": [{"level": "WARN", "message": "Expected tab not detected: 'Analysis'"}],
            }],
        }
        md = generate_markdown(inventory)
        assert "Tab Validation" in md
        assert "Analysis" in md


# =========================================================================
# Config integrity
# =========================================================================
class TestConfigIntegrity:

    def test_all_copilots_have_smoke_ids(self):
        """P3: every copilot must have smoke_ids for parameterized path testing."""
        for name, config in COPILOTS.items():
            assert "smoke_ids" in config, f"{name} missing smoke_ids"
            assert isinstance(config["smoke_ids"], dict)
            assert len(config["smoke_ids"]) > 0

    def test_soc_has_smoke_ids(self):
        assert "smoke_ids" in SOC_CONFIG

    def test_all_copilots_have_expected_tabs(self):
        for name, config in COPILOTS.items():
            assert "expected_tabs" in config, f"{name} missing expected_tabs"
            assert len(config["expected_tabs"]) >= 3, f"{name} has too few expected_tabs"

    def test_soc_expected_tabs_no_governance(self):
        """P4: 'Governance' was removed from SOC expected_tabs."""
        assert "Governance" not in SOC_CONFIG["expected_tabs"]

    def test_port_uniqueness(self):
        """All frontend and backend ports must be unique."""
        all_ports = []
        for config in COPILOTS.values():
            all_ports.extend([config["backend_port"], config["frontend_port"]])
        all_ports.extend([SOC_CONFIG["backend_port"], SOC_CONFIG["frontend_port"]])
        assert len(all_ports) == len(set(all_ports)), "Duplicate ports found"
