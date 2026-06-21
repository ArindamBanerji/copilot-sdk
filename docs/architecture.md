# Architecture

## Component Flow

```text
DomainPreset -> CompoundingScorer -> GraphStore -> Conservation / Learning
```

The SDK is the public package boundary. Domain applications provide routers, factor computers, frontend views, and connector wiring. The SDK provides reusable scoring, graph persistence protocols, conservation contracts, evolution hooks, outbox primitives, and substantiation protocols.

## Repositories

| Repository | Role |
|---|---|
| `copilot-sdk` | Public package, protocols, presets, graph stores, substantiation primitives |
| `gen-ai-roi-demo-v4-v50` | SOC demo application and shared frontend/backend shell |
| `s2p-copilot` | S2P domain copilot |
| `ci-platform` | Graph, AGE, audit, platform utilities |
| `graph-attention-engine-v50` | GAE scoring and learning engine |

## Port Allocation

| Component | Backend | Frontend |
|---|---:|---:|
| SOC | 8001 | 5173 |
| S2P | 8002 | 5177 |
| Trading | 8010 | 5174 |
| Purchasing | 8020 | 5175 |
| DataOps | 8030 | 5176 |
| PostgreSQL + AGE | 5433 | N/A |

## Key Abstractions

| Abstraction | Location | Purpose |
|---|---|---|
| `GraphStore` | `copilot_sdk.graph.protocol` | Protocol for decision, outcome, centroid, and graph-memory persistence |
| `DomainPreset` shape | `copilot_sdk.scoring.config.DomainShape` | Defines categories, actions, factors, and tensor dimensions |
| `CompoundingScorer` | `copilot_sdk.scoring.scorer` | Main score/learn API around preset geometry and graph persistence |

## Tensor Shape

Every copilot has a category x action x factor tensor. In notation:

```text
C x A x D
```

Where:

- `C` = number of decision categories
- `A` = number of actions
- `D` = number of factors

## Copilot Tensor Table

These shapes are the current SDK preset shapes.

| Copilot | Shape | Values |
|---|---:|---:|
| SOC | `(6, 4, 6)` | 144 |
| Trading | `(5, 4, 10)` | 200 |
| Purchasing | `(5, 4, 7)` | 140 |
| DataOps | `(6, 5, 6)` | 180 |
| S2P | `(5, 5, 7)` | 175 |

## Preset Registry

The preset registry currently exposes:

```text
dataops, purchasing, s2p, soc, trading
```

Applications should call:

```python
CompoundingScorer.from_preset("trading", graph_store=store)
```

and pass an explicit `GraphStore` implementation.
