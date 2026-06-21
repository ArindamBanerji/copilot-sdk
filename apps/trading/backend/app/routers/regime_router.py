"""F10 market regime classifier endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import APIRouter

from app.services.regime import DEFAULT_ADX, DEFAULT_VIX, compute_adx
from app.services.regime_classifier import RegimeClassifier, RegimePerformanceMapper
from app.services.regime_history import RegimeHistory
from copilot_sdk.backend.conservation_router import _check_payload, _state_counts
from copilot_sdk.scoring.presets.trading import TradingPreset


GraphStoreFactory = Callable[[], Any]
ProviderFactory = Callable[[], Any]

_provider: Any | None = None
_history = RegimeHistory()


def _market_provider() -> Any:
    global _provider
    if _provider is None:
        from app.connectors.market_source import YFinanceSource
        from app.services.market_data_provider import MarketDataProvider

        _provider = MarketDataProvider(source=YFinanceSource())
    return _provider


def create_regime_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    provider_factory: ProviderFactory = _market_provider,
    history: RegimeHistory | None = None,
    classifier: RegimeClassifier | None = None,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading/regime", tags=["trading-regime-classifier"])
    regime_history = history or _history
    regime_classifier = classifier or RegimeClassifier()

    @router.get("/current")
    def current_regime() -> dict[str, Any]:
        payload = _current_market(provider_factory(), regime_classifier)
        regime_history.record(
            str(payload["regime"]),
            float(payload["vix"]),
            float(payload["adx"]),
            timestamp=str(payload["timestamp"]),
        )
        return payload

    @router.get("/history")
    def regime_history_endpoint(days: int = 90) -> list[dict[str, Any]]:
        return regime_history.history(days)

    @router.get("/performance")
    def regime_performance() -> dict[str, Any]:
        current = _current_market(provider_factory(), regime_classifier)
        conservation = _conservation_status(graph_store_factory, domain) or {}
        store = graph_store_factory() if graph_store_factory is not None else None
        if store is None:
            return {
                "per_regime_accuracy": {},
                "current_regime": current["regime"],
                "edge_categories": [],
                "recommendation": "Score more verified trades before changing regime sizing.",
            }
        mapper = RegimePerformanceMapper(store, TradingPreset(), domain=domain)
        per_regime = mapper.per_regime_accuracy()
        edges = mapper.regime_edge(str(current["regime"]))
        return {
            "per_regime_accuracy": per_regime,
            "current_regime": current["regime"],
            "edge_categories": edges,
            "recommendation": mapper.regime_recommendation(str(current["regime"]), conservation),
        }

    @router.get("/recommendation")
    def regime_recommendation() -> dict[str, Any]:
        current = _current_market(provider_factory(), regime_classifier)
        conservation = _conservation_status(graph_store_factory, domain) or {}
        store = graph_store_factory() if graph_store_factory is not None else None
        if store is None:
            edges: list[dict[str, Any]] = []
        else:
            mapper = RegimePerformanceMapper(store, TradingPreset(), domain=domain)
            edges = mapper.regime_edge(str(current["regime"]))
        return {"current_regime": current["regime"], "shifts": _shifts(str(current["regime"]), edges, conservation)}

    return router


def _current_market(provider: Any, classifier: RegimeClassifier) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    try:
        vix_result = provider.get_vix_current()
        ohlcv_result = provider.get_ohlcv("SPY", "1mo")
        vix = vix_result.value if vix_result is not None and vix_result.value is not None else DEFAULT_VIX
        rows = ohlcv_result.value if ohlcv_result is not None else None
        adx = _adx_from_rows(rows if isinstance(rows, list) else None)
        payload = classifier.classify_with_confidence(float(vix), adx)
        payload["timestamp"] = getattr(vix_result, "as_of", None) or now
        payload["source"] = getattr(vix_result, "source", "provider")
        return payload
    except Exception:
        payload = classifier.classify_with_confidence(DEFAULT_VIX, DEFAULT_ADX)
        payload["timestamp"] = now
        payload["source"] = "default"
        return payload


def _adx_from_rows(rows: list[dict[str, Any]] | None) -> float:
    if not rows:
        return DEFAULT_ADX
    highs = [row["high"] for row in rows if isinstance(row, dict) and "high" in row]
    lows = [row["low"] for row in rows if isinstance(row, dict) and "low" in row]
    closes = [row["close"] for row in rows if isinstance(row, dict) and "close" in row]
    return float(compute_adx(highs, lows, closes))


def _conservation_status(
    graph_store_factory: GraphStoreFactory | None,
    domain: str,
) -> dict[str, Any] | None:
    if graph_store_factory is None:
        return None
    store = None
    try:
        store = graph_store_factory()
        counts = _state_counts(store)
        from gae.calibration import conservation_status

        check = conservation_status(
            verified_count=counts["verified_count"],
            correct_count=counts["correct_count"],
            total_decisions=counts["total_decisions"],
            penalty_ratio=counts["penalty_ratio"],
        )
        return {**counts, **_check_payload(check)}
    except Exception:
        return None


def _shifts(
    current_regime: str,
    edges: list[dict[str, Any]],
    conservation_status: dict[str, Any],
) -> list[dict[str, Any]]:
    shifts: list[dict[str, Any]] = []
    for row in edges:
        category = str(row["category"])
        edge = float(row["edge"])
        conservation = _category_status(conservation_status, category)
        if edge > 0.05 and conservation == "GREEN":
            direction = "increase"
            reason = f"Verified edge is stronger in {current_regime} conditions."
        elif edge < -0.05:
            direction = "decrease"
            reason = f"Verified edge is weaker in {current_regime} conditions."
        else:
            direction = "hold"
            reason = "Keep sizing steady until the edge and conservation state align."
        shifts.append(
            {
                "category": category,
                "direction": direction,
                "edge": round(edge, 4),
                "conservation_status": conservation,
                "reason": reason,
            }
        )
    return shifts


def _category_status(conservation_status: dict[str, Any], category: str) -> str:
    categories = conservation_status.get("categories")
    value: Any = None
    if isinstance(categories, dict):
        value = categories.get(category)
    if value is None:
        value = conservation_status.get(category)
    if isinstance(value, dict):
        value = value.get("status") or value.get("conservation_status")
    if value is None:
        value = conservation_status.get("status") or conservation_status.get("conservation_status")
    text = str(value or "UNKNOWN").strip().upper()
    return text if text else "UNKNOWN"
