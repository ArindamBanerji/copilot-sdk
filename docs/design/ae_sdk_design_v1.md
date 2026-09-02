# AE-SDK Design v1

**Status:** design-only extraction proposal  
**Scope:** AgentEvolver (AE) platform contracts for all five copilots  
**Dependency:** the existing GraphStore/AGE protocol and the RL-SDK contract

## 1. Purpose

AgentEvolver is the platform capability that manages candidate behavior,
shadow evaluation, promotion, rollback, and evolution telemetry. The current
SOC implementation combines these concerns with SOC-specific alert and
triage logic. The SDK extraction makes the lifecycle domain-neutral: each
copilot supplies its candidate generator, evidence adapter, and reward
function, while the SDK owns lifecycle state, gates, and audit identity.

AE is an evolution sidecar. It must not replace centroid judgment, bypass the
conservation gate, or select a live action in a high-stakes domain. Candidate
evaluation is shadow-first; promotion is an explicit governed transition.

## 2. Existing implementation to extract

The SOC services currently demonstrate the relevant seams:

- `evolver.py` contains an AGE-backed variant store, conservation-state
  provider, variant registration, outcome recording, and status changes.
- The SOC promotion service persists promotion records and evaluates candidate
  accuracy against a baseline.
- Evolution routes expose candidate registration, shadow evaluation, and
  promotion decisions to the application layer.
- Learning-health and conservation services provide the evidence needed by a
  promotion gate.

These are reference behaviors, not SDK imports. The SDK must remain free of
SOC and S2P modules and receive all domain semantics through protocols.

## 3. SDK contracts

### 3.1 Candidate and variant

```python
class VariantSpec(Protocol):
    id: str
    family: str
    version: int
    template: str
    metadata: Mapping[str, Any]

class VariantStore(Protocol):
    def register(self, variant: VariantSpec) -> None: ...
    def get(self, variant_id: str) -> VariantSpec | None: ...
    def list_active(self) -> Sequence[VariantSpec]: ...
```

The store is domain-scoped and AGE-backed in production. Variant identity is
stable across restarts, and registration is idempotent for the same version.

### 3.2 Shadow evaluation

```python
class ShadowEvaluator(Protocol):
    def evaluate(self, variant: VariantSpec, batch: Sequence[Decision]) -> ShadowBatch: ...
```

`ShadowBatch` records total decisions, correct decisions, accuracy,
baseline accuracy, batch identifier, evidence references, and the reward
breakdown. Missing or unverifiable evidence is an unsuccessful evaluation,
never an implicit pass.

### 3.3 Conservation-aware promotion gate

The gate requires all of the following:

1. minimum shadow volume and minimum batch count;
2. candidate accuracy at or above the configured floor;
3. configured superiority over baseline;
4. bounded batch variance;
5. a live conservation state positively established as GREEN.

UNKNOWN, stale, CALIBRATING, AMBER, RED, provider errors, and absent state
all fail closed. The gate may return a structured rejection, but it must not
manufacture GREEN. `theta_min` remains owned by the conservation provider;
AE consumes it as evidence and does not recompute a competing law.

### 3.4 Promotion persistence

Promotion records are append-only governed state in GraphStore. The state
machine is:

`REGISTERED → SHADOW → ELIGIBLE → PROMOTED`

with `REJECTED`, `ROLLED_BACK`, and `PAUSED` terminal or supervisory states.
Every transition includes actor, source route, prior state, evidence IDs,
conservation snapshot, and a monotonic event ID. A rollback creates a new
event; it does not delete history.

### 3.5 Evolution telemetry

The SDK emits domain-neutral events for registration, shadow batch completion,
gate evaluation, promotion, rollback, and pause. Domain and candidate IDs are
mandatory. Metrics are descriptive and provenance-bearing; generated demo
fixtures must not be presented as customer evidence.

## 4. GraphStore mapping

Production AE uses the existing GraphStore protocol:

| AE state | GraphStore operation | AGE node/event kind |
|---|---|---|
| variant definition | `save_evolution` / `get_evolution` | Evolution |
| shadow posterior | `save_posterior` / `get_posterior` | Posterior |
| promotion record | `save_promotion` / `get_promotion` | Promotion |
| gate and reward evidence | `save_ledger` / `get_ledger` | Ledger |
| governance transition | `save_governance` / `get_governance` | Governance |
| lifecycle telemetry | `write_evolution_event` | EvolutionEvent |

All reads and writes carry the domain. InMemoryGraphStore is a complete
contract test implementation only; it is not a production fallback. AGE
connection failures surface to health and promotion responses rather than
becoming empty candidate lists or safe defaults.

## 5. Domain injection boundary

Each copilot supplies:

- a candidate generator or prompt/template builder;
- a `DomainRewardFunction` from RL-SDK;
- an evidence adapter that converts verified outcomes into `ShadowBatch`;
- a domain conservation provider;
- optional domain-specific eligibility metadata.

The SDK supplies variant lifecycle, temporal ordering, persistence, gate
evaluation, audit records, and rollback semantics. No SDK module imports a
copilot application package.

## 6. Security and safety invariants

- Live scoring remains centroid-authoritative unless a separately governed
  domain policy explicitly permits another authority.
- Promotion cannot proceed without a positive live GREEN conservation state.
- A failed AGE read/write raises or becomes an explicit unavailable health
  state; it is never represented by `None`, `[]`, or `False` as success.
- Domain isolation applies to every GraphStore operation.
- Candidate, evidence, actor, and decision identities are preserved across
  shadow evaluation, promotion, and rollback.
- All state transitions are replayable from append-only AGE events.

## 7. Rollout and verification

1. Add SDK protocols and AGE adapters without changing copilot behavior.
2. Add conformance tests for InMemoryGraphStore and the AGE adapter.
3. Wire one copilot in shadow-only mode and compare telemetry with its current
   implementation.
4. Roll out the remaining copilots with domain reward/evidence adapters.
5. Enable promotion only after conservation, isolation, replay, and rollback
   tests pass for all five domains.

The extraction is complete when all five copilots use the same variant,
promotion, event, and gate contracts, and every promotion can be explained by
its persisted evidence and conservation snapshot.
