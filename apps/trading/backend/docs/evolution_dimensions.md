# Trading Evolution Dimensions

## Domain Rule

Trading evolution is limited to presentation and routing behavior.
The Trading copilot scores execution quality, not directional buy, hold, or sell advice.
The score actions remain `strong_execution`, `partial_execution`, `poor_execution`, and `skip_recommended`.
This feature does not change the scorer, RL behavior, tensor shape, action semantics, or generic evolution router.

## Level 2 Scope

Level 2 evolution learns how analysis is presented to the trader.
It does not learn what trade to place.
It does not alter order side, position direction, or execution-quality scoring.
Variants are safe presentation candidates that can be shown, shadow-tested, and eventually promoted only after conservation is verified.

## Dimensions

| Dimension | Values | Default | Rationale |
|---|---|---|---|
| `evidence_ordering` | `factor_first`, `regime_first`, `pattern_first` | `factor_first` | Tests whether traders respond better when factor, regime, or pattern evidence appears first. |
| `risk_framing` | `numerical`, `categorical`, `comparative` | `numerical` | Tests whether risk is clearer as numbers, labels, or comparisons to prior behavior. |
| `strategy_weight` | `balanced`, `strategy_heavy`, `general_heavy` | `balanced` | Tests whether strategy-specific or general execution context should receive more emphasis. |

## Default Variants

`DEFAULT_VARIANTS` contains three stable initial variants.
Each variant explores one dimension while keeping the other dimensions at their defaults.

| Variant | Name | Status | Purpose |
|---|---|---|---|
| `trd-ev-001` | Regime-first evidence | `active` | Move regime context ahead of factor evidence. |
| `trd-ev-002` | Comparative risk framing | `shadow` | Present risk against prior comparable trades. |
| `trd-ev-003` | Strategy-heavy weighting | `shadow` | Give strategy-specific execution history more weight. |

## Router Integration

The Trading app exposes these variants through the generic SDK evolution router.
The app passes `get_trading_variants` as `variant_provider` to the existing `create_evolution_router(...)` mount.
The generic router keeps its existing `/api/evolution/variants`, `/api/evolution/history`, and `/api/evolution/promoted` endpoints.
No new backend router is added.

## Promotion Workflow

Promotion must be fail-closed.
A candidate variant should first run in shadow mode and collect evidence.
Before promotion, conservation must be verified as GREEN or an equivalent safe phase.
The Trading backend exposes `/api/conservation/status`, but the offline CLI does not operate against a running backend session.
Therefore `ci-trading evolution promote <variant_id>` validates the variant and then blocks promotion unless verified GREEN conservation can be checked by a future backend-backed workflow.
The command does not invent a local conservation formula.
The command does not persist a promotion without backend support.

## CLI Examples

```powershell
ci-trading evolution variants
ci-trading evolution status
ci-trading evolution promote trd-ev-001
```

`variants` lists all presentation variants.
`status` summarizes active and shadow variant counts.
`promote` is validation-only today and fails closed when conservation cannot be verified.

## T1 and T13-T20 Mapping

T1 needs a stable analysis surface that helps traders understand execution quality.
T13-T20 style experiences can vary evidence order, risk framing, and strategy emphasis without changing scoring actions.
These dimensions are intentionally presentation-side because they can improve comprehension without creating trade advice.

## Intentionally Unchanged

- Trading scorer
- Trading RL behavior
- Trading tensor shape
- Trading action semantics
- Broker execution code
- Import connectors
- Generic SDK evolution router
- SDK evolution protocols
- Purchasing, DataOps, S2P, and SOC code

## Safety Notes

Variant IDs are stable.
Variant dictionaries are returned as defensive copies.
No variant contains directional trade recommendations.
No variant changes execution-quality actions.
Manual promotion remains blocked until conservation and promotion persistence are explicitly wired.
