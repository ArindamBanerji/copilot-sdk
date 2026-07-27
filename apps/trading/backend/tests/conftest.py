from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from copilot_sdk.config import GraphConfig
from copilot_sdk.testing import age_available


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app import context_router  # noqa: E402
from app.main import create_app  # noqa: E402
from apps.trading.backend.app.connectors.market_source import MockMarketSource  # noqa: E402
from apps.trading.backend.app.services.market_data_provider import MarketDataProvider  # noqa: E402


@pytest.fixture
def trading_live_age_graph():
    """Run live AGE tests against an isolated disposable graph."""
    if not age_available():
        yield
        return

    import psycopg

    config = GraphConfig.load("trading")
    if not config.dsn:
        pytest.skip("Trading AGE DSN is not configured")
    graph_name = f"protocol_v2_test_{uuid.uuid4().hex[:12]}"
    keys = {
        "TRADING_ACTIVE_GRAPH_BACKEND": "age",
        "TRADING_ACTIVE_AGE_DSN": config.dsn,
        "TRADING_ACTIVE_AGE_GRAPH": graph_name,
        "TRADING_ACTIVE_AGE_DOMAIN": "trading",
        "TRADING_ACTIVE_AGE_TEST_MODE": "1",
    }
    previous = {key: os.environ.get(key) for key in keys}
    conn = psycopg.connect(config.dsn, connect_timeout=3, autocommit=True)
    try:
        conn.execute("LOAD 'age'")
        conn.execute('SET search_path = ag_catalog, "$user", public')
        conn.execute("SELECT create_graph(%s)", (graph_name,))
        os.environ.update(keys)
        yield graph_name
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        try:
            conn.execute("LOAD 'age'")
            conn.execute('SET search_path = ag_catalog, "$user", public')
            conn.execute("SELECT drop_graph(%s, true)", (graph_name,))
        finally:
            conn.close()


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    source_data = BACKEND_ROOT / "data"
    temp_data = tmp_path / "data"
    temp_data.mkdir()
    for filename in (
        "market_snapshot.json",
        "ticker_cache.json",
        "portfolio_summary.json",
        "trading_seed_v2.json",
        "analytics_cache.json",
    ):
        (temp_data / filename).write_text(
            (source_data / filename).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    (temp_data / "trade_metadata.json").write_text(
        json.dumps({}, indent=2),
        encoding="utf-8",
    )

    monkeypatch.setattr(context_router, "_DATA_DIR", temp_data)
    app = create_app(db_path=tmp_path / "trading_test.db", demo_bundle_path=False)
    app.state.trading_data_dir = temp_data
    return TestClient(app)


@pytest.fixture
def mock_market_source():
    """Shared mock market source for all trading tests."""
    return MockMarketSource()


@pytest.fixture
def market_provider(mock_market_source):
    """Shared market data provider with mock source."""
    return MarketDataProvider(source=mock_market_source)
