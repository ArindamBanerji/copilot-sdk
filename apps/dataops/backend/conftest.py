"""Explicit SQLite GraphConfig for isolated DataOps backend tests."""

import os
import tempfile


_config_file = tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False, encoding="utf-8")
_config_file.write(
    "[defaults]\n"
    'dsn = ""\n'
    'graph = "test_graph"\n'
    "\n"
    "[copilot.dataops]\n"
    'domain = "dataops"\n'
    'backend = "sqlite"\n'
    'expected_backend = "sqlite"\n'
    'prefix = "DOPS-"\n'
)
_config_file.close()
os.environ["GRAPH_CONFIG_PATH"] = _config_file.name
os.environ["DATAOPS_ACTIVE_GRAPH_BACKEND"] = "sqlite"
os.environ["GRAPH_BACKEND"] = "sqlite"
