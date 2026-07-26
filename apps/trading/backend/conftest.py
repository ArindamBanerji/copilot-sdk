"""Test-only graph configuration for isolated Trading backend tests."""

import os
import tempfile


# Backend tests exercise temporary SQLite stores unless a test explicitly opts
# into the guarded live-AGE module.  Point GraphConfig at an explicit test
# configuration whose expected backend is SQLite; this is not an implicit
# fallback and keeps module-level app construction deterministic.
_config_file = tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False, encoding="utf-8")
_config_file.write(
    "[defaults]\n"
    'dsn = ""\n'
    'graph = "test_graph"\n'
    "\n"
    "[copilot.trading]\n"
    'domain = "trading"\n'
    'backend = "sqlite"\n'
    'expected_backend = "sqlite"\n'
    'prefix = "TRD-"\n'
)
_config_file.close()
os.environ["GRAPH_CONFIG_PATH"] = _config_file.name
os.environ["TRADING_ACTIVE_GRAPH_BACKEND"] = "sqlite"
os.environ["GRAPH_BACKEND"] = "sqlite"
