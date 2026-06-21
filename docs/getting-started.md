# Getting Started

## What Is The Compounding Intelligence SDK?

The Compounding Intelligence SDK is a public Python package for building domain copilots that score decisions, persist the decision trail, learn from verified outcomes, and compound accuracy over time. A copilot starts from a domain preset, writes every score and outcome through a `GraphStore`, and updates its decision geometry only when the outcome path says learning is allowed.

## Requirements

- Python 3.11+
- `ci-platform`
- The SDK package on `PYTHONPATH` or installed into the active environment

## Quick Start

Pass `graph_store` explicitly when using `CompoundingScorer.from_preset()`. The in-memory store is useful for tests and demos; production copilots usually use SQLite or AGE-backed stores.

```python
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.graph.memory_store import InMemoryGraphStore

store = InMemoryGraphStore(domain="trading")
scorer = CompoundingScorer.from_preset("trading", graph_store=store)
result = scorer.score(category="trend_following", factors={
    "signal_alignment": 0.7, "market_regime": 0.4,
    "position_sizing": 0.5, "timing_quality": 0.6,
    "risk_reward_actual": 0.6, "emotional_indicator": 0.3,
    "signal_confidence": 0.7, "options_delta_exposure": 0.5,
    "options_iv_percentile": 0.4, "options_gamma_risk": 0.3,
})
print(result.action, result.confidence)
scorer.learn(result.decision_id, actual_action="strong_execution", outcome="correct")
```

## Validated Copilots

The current preset registry contains five copilots:

| Copilot | Preset key | Purpose |
|---|---:|---|
| SOC | `soc` | Security operations triage and campaign intelligence |
| Trading | `trading` | Trade execution quality and journal learning |
| Purchasing | `purchasing` | Kitchen and purchasing decision support |
| DataOps | `dataops` | Data quality and pipeline operation decisions |
| S2P | `s2p` | Source-to-pay invoice and supplier workflows |

## Notes

- Use `copilot_sdk.graph.memory_store.InMemoryGraphStore`; there is no `copilot_sdk.graph.in_memory_store` module in this SDK version.
- `ScoreResult` exposes `action`, `action_index`, `confidence`, `probabilities`, `category`, `factors`, and `decision_id`.
- `learn()` expects a decision id produced by `score()` and an actual action that belongs to the preset's action list.
