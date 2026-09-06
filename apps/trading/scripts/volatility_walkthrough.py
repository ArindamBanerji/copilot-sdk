"""Walk through a live Trading volatility decision from regime to gate.

Run from ``apps/trading`` while the Trading backend is listening on port 8010:

    python scripts/volatility_walkthrough.py
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BACKEND = f"http://{os.environ.get('COPILOT_HOST', '127.0.0.1')}:8010"
DEFAULT_REPORT = Path(__file__).with_name("volatility_walkthrough_report.json")
HIGH_VOLATILITY_VIX = 42.0
HIGH_VOLATILITY_ADX = 35.0
TRADE_CATEGORY = "income_strategy"
TRADE_FACTORS = {
    "signal_alignment": 0.72,
    "market_regime": 0.92,
    "position_sizing": 0.32,
    "timing_quality": 0.38,
    "risk_reward_actual": 0.68,
    "emotional_indicator": 0.18,
    "signal_confidence": 0.78,
    "options_delta_exposure": 0.56,
    "options_iv_percentile": 0.86,
    "options_gamma_risk": 0.74,
}


class LiveBackendError(RuntimeError):
    """Raised when the live Trading backend cannot complete the walkthrough."""


def _request(
    backend: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{backend.rstrip('/')}{path}",
        data=body,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as exc:
        detail = ""
        if isinstance(exc, HTTPError):
            try:
                detail = exc.read().decode("utf-8")[:500]
            except OSError:
                detail = ""
        raise LiveBackendError(f"{method} {path} failed: {exc} {detail}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LiveBackendError(f"{method} {path} returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise LiveBackendError(f"{method} {path} returned a non-object JSON payload")
    return value


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _narrate(report: dict[str, Any]) -> None:
    regime = report["regime"]
    score = report["score"]
    parameters = score.get("regime_parameters", {})
    iv = report["iv_analysis"]
    gate = report["conservation"]
    print("\nTRADING VOLATILITY WALKTHROUGH (live backend)")
    print("=" * 52)
    print(
        f"1. Regime: {regime.get('regime', 'unknown')} "
        f"(VIX {regime.get('vix', 'n/a')}, ADX {regime.get('adx', 'n/a')})"
    )
    print(
        f"2. Trade score: {score.get('action', 'unknown')} "
        f"with confidence {_number(score.get('confidence')):.3f} "
        f"for {score.get('category', TRADE_CATEGORY)}"
    )
    print(
        "3. Regime conditioning: "
        f"{parameters.get('regime', 'unknown')} regime, "
        f"penalty ratio {parameters.get('penalty_ratio', 'n/a')}, "
        f"eta {parameters.get('eta', 'n/a')}"
    )
    weights = report["factor_weights"]
    if weights.get("status") == "available":
        print(f"   Factor weights returned by backend: {weights.get('factor_weights')}")
    else:
        print(f"   Factor weights: {weights.get('reason', 'not available from live backend')}")
    print(
        f"4. IV: percentile={iv.get('iv_percentile', 'n/a')}, "
        f"classification={iv.get('band', iv.get('classification', 'unknown'))}; "
        f"VRP={report['vrp'].get('vrp_edge', report['vrp'].get('vrp_spread_current', 'n/a'))}"
    )
    print(
        f"5. Conservation gate: {gate.get('status', gate.get('conservation_status', 'unknown'))} "
        f"(headroom={gate.get('headroom', 'n/a')})"
    )
    print(
        f"6. Decision: {score.get('action', 'unknown')}; "
        "the live scorer and conservation response are authoritative."
    )


def run_walkthrough(backend: str) -> dict[str, Any]:
    regime = _request(backend, "GET", "/api/trading/regime/current")
    score = _request(
        backend,
        "POST",
        "/api/trading/score-as",
        {
            "category": TRADE_CATEGORY,
            "factors": TRADE_FACTORS,
            "trader_id": "volatility-walkthrough",
            "context": {
                "vix_at_entry": HIGH_VOLATILITY_VIX,
                "trend_strength": HIGH_VOLATILITY_ADX,
                "implied_volatility": 0.42,
                "realized_volatility": 0.22,
                "regime_scenario": "volatile",
            },
        },
    )
    detail = _request(backend, "GET", "/api/trading/regime/detail")
    iv_analysis = _request(backend, "GET", "/api/trading/volatility/rich-cheap?regime=volatile")
    vrp = _request(backend, "GET", "/api/trading/volatility/vrp")
    conservation = _request(backend, "GET", "/api/conservation/status")
    return {
        "scenario": {
            "name": "high_volatility_income_trade",
            "requested_regime": "volatile",
            "vix_at_entry": HIGH_VOLATILITY_VIX,
            "trend_strength_at_entry": HIGH_VOLATILITY_ADX,
            "category": TRADE_CATEGORY,
        },
        "regime": regime,
        "score": score,
        "factor_weights": detail.get("regime_factor_weights", {}),
        "iv_analysis": iv_analysis,
        "vrp": vrp,
        "conservation": conservation,
        "decision": {
            "action": score.get("action"),
            "confidence": score.get("confidence"),
            "decision_id": score.get("decision_id"),
            "observation_only": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", default=DEFAULT_BACKEND)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    report = run_walkthrough(args.backend)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _narrate(report)
    print(f"\nJSON report: {args.report}")


if __name__ == "__main__":
    main()
