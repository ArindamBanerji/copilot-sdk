# DataOps Copilot Backend Implementation Plan

## Executive Summary

Build the DataOps Copilot backend under `apps/dataops/backend` as the enterprise-tier proof point for the SDK. The backend will mount scoring, conservation, and evolution SDK routers; expose graph-backed DataOps context; expose operational AgentEvolver endpoints under `/api/ae`; and use ci-platform AGE graph access when configured.

The implementation is graph-first through `ci-platform`'s `AGEClient`, with deterministic JSON fixture fallback when AGE is unavailable or when tests run without graph credentials. No SDK, scoring core, generic backend, frontend, ci-platform, Trading, Purchasing, GAE, SOC, or S2P files should be modified.

## Source Contracts from Prompt 0

### SDK Router Contracts

`copilot_sdk/backend/scoring_router.py` provides:

- `create_scoring_router(domain: str, db_path: str | None = None, scorer_factory: Callable[..., Any] | None = None)`.
- Endpoints mounted by the factory:
  - `POST /score`
  - `POST /learn`
  - `GET /fingerprint`
  - `GET /trajectory`
  - `GET /history`
- Score request shape: `{category, factors, context?}`.
- Learn request shape: `{decision_id, actual_action, outcome?, context?}`.
- Response engine field includes `copilot_sdk.scoring.CompoundingScorer` and `gae.profile_scorer.ProfileScorer`.

`copilot_sdk/backend/conservation_router.py` provides:

- `create_conservation_router(domain: str, state_provider: Callable[[], Any] | Any | None = None)`.
- Endpoints mounted by the factory:
  - `GET /conservation/status`
  - `POST /conservation/what-if`
- `state_provider` may be a callable, dict, store-like object, or `None`.
- Dict state should provide `verified_count`, `correct_count`, `total_decisions`, and `penalty_ratio`.
- Response engine fields use `gae.calibration`.

`copilot_sdk/backend/evolution_router.py` provides:

- `create_evolution_router(domain: str, ledger_provider: Callable[[], Any] | Any | None = None)`.
- Endpoints mounted by the factory:
  - `GET /evolution/variants`
  - `GET /evolution/patterns`
- `ledger_provider` may be a callable, object, awaitable, or `None`.
- The ledger object must work with `gae.evolution.get_recent_events` and `gae.evolution.get_evolution_summary`; fixture providers can expose `run_query` if that matches GAE's query path.
- Response engine fields use `gae.evolution`.

### DataOps Preset Contract

`copilot_sdk/scoring/presets/dataops.py` defines:

- Categories:
  - `schema_change`
  - `volume_anomaly`
  - `quality_anomaly`
  - `freshness_violation`
  - `pipeline_failure`
  - `transform_drift`
- Actions:
  - `auto_approve`
  - `investigate`
  - `escalate_to_owner`
  - `pause_downstream`
  - `refer_to_specialist`
- Factors:
  - `impact_scope`
  - `source_reliability`
  - `recurrence_frequency`
  - `downstream_urgency`
  - `data_freshness`
  - `business_criticality`
- Penalty ratio: `10.0`.

`copilot_sdk/scoring/presets/dataops_seed.json` contains 20 events with:

- `event_id`
- `dataset`
- `category`
- `action_taken`
- `is_correct`
- nested `factors`

### AGEClient Contract

The AGE client source is `ci-platform/ci_platform/graph/age_client.py`.

Contract:

- `AGEClient(dsn: str | None = None, graph_name: str | None = None)`.
- `connect()` and `close()` are async no-ops.
- `run_query(query: str, parameters: dict | None = None)` is async and returns `list[dict]`.
- `serialize_for_age(value)` exists and should be used for Cypher literal construction.
- The underlying client supports parameters internally, but DataOps backend graph queries should avoid `$params` and inline sanitized values because the DataOps prompt requires no `$params`.
- Queries must be read-only in this backend.
- Do not call live AGE in tests.

### ci-platform DataOps Schema Contract

`ci-platform/dataops/schema.py` defines:

- Node labels:
  - `PipelineSystem`
  - `DataQualityAlert`
- Edge labels:
  - `FEEDS`
  - `AFFECTS`
  - `CASCADES`
- DataOps categories/actions matching the DataOps domain, though schema category order differs from scoring preset order.
- `SYSTEMS`: 9 pipeline systems with `name`, `display_name`, `sla_minutes`, `business_criticality`, `source_reliability`, `owner`, `status`, `last_run`, and `description`.
- `FEEDS_EDGES`: 9 pipeline dependency edges.
- `DATASET_SYSTEM_MAP`: 20 dataset-to-system mappings.

Use the scoring preset for SDK tensor ordering. Use the ci-platform schema for graph fixtures and graph labels.

### Existing Backend Patterns

Trading and Purchasing backends establish these app patterns:

- Add repo root and GAE path to `sys.path`.
- Data directory constant at `Path(__file__).resolve().parents[1] / "data"`.
- `create_app(db_path: str | Path | None = None) -> FastAPI`.
- Wide-open CORS for demo/Loom usage.
- Fresh scorer proxy around `CompoundingScorer.from_preset(...)` to avoid sharing SQLite handles across FastAPI worker threads.
- SDK routers mounted under `/api`.
- Context routers mounted under `/api/context`.
- `GET /health` returns `status`, `domain`, and engine string.
- Tests use `TestClient`, temp data directories, monkeypatching, and temp SQLite DBs.

## Files to Create

- `apps/dataops/.env.example`
- `apps/dataops/backend/app/__init__.py`
- `apps/dataops/backend/app/main.py`
- `apps/dataops/backend/app/context_router.py`
- `apps/dataops/backend/app/ae_router.py`
- `apps/dataops/backend/app/graph_queries.py`
- `apps/dataops/backend/data/evolution_fixtures.json`
- `apps/dataops/backend/data/ae_impact.json`
- `apps/dataops/backend/data/incident.json`
- `apps/dataops/backend/data/conservation_history.json`
- `apps/dataops/backend/data/alert_metadata.json`
- `apps/dataops/backend/data/fallback/pipelines.json`
- `apps/dataops/backend/data/fallback/alerts.json`
- `apps/dataops/backend/data/fallback/blast_radius.json`
- `apps/dataops/backend/tests/conftest.py`
- `apps/dataops/backend/tests/test_dataops_backend.py`
- `apps/dataops/backend/tests/test_graph_queries.py`

`apps/dataops/backend/app/__init__.py` and `apps/dataops/backend/data/.gitkeep` already exist in the scaffold; update only if needed to make imports or package behavior explicit.

## Forbidden Files

Do not modify:

- `copilot_sdk/scoring/**`
- `copilot_sdk/backend/**`
- `copilot_sdk/frontend/**`
- `ci-platform/**`
- `apps/trading/**`
- `apps/purchasing/**`
- `graph-attention-engine-v50/**`
- `gen-ai-roi-demo-v4-v50/**`
- `s2p-copilot/**`
- any GAE/SOC/S2P files

Do not use git operations.

## Main App Contract

Create `apps/dataops/backend/app/main.py`.

Requirements:

- FastAPI app title: `DataOps Copilot`.
- Wide-open CORS for Loom/demo use.
- Add these paths when present:
  - repo root
  - workspace `graph-attention-engine-v50`
  - workspace `ci-platform`
- Mount all three SDK routers under `/api`:
  - `create_scoring_router("dataops", db_path=scoring_db, scorer_factory=...)`
  - `create_conservation_router("dataops", state_provider=...)`
  - `create_evolution_router("dataops", ledger_provider=...)`
- Mount context router at `/api/context`.
- Mount AE router at `/api/ae`.
- `GET /health` returns:
  - `status: "ok"`
  - `domain: "dataops"`
  - `graph_connected`
  - `graph_source`
  - `engine` containing scoring, profile scorer, calibration, evolution, and graph context references.

Implementation notes:

- Follow Trading/Purchasing `_FreshScorerProxy` and `_StoreProxy` patterns.
- Conservation provider should return a dict from fixture decisions or graph stats:
  - `verified_count`
  - `correct_count`
  - `total_decisions`
  - `penalty_ratio: 10.0`
- Evolution provider should support fixture events in the same way Purchasing does, but with DataOps event fields.
- Do not require `GRAPH_DSN` or `DATABASE_URL` for tests.

## Graph Query Contract

Create `apps/dataops/backend/app/graph_queries.py`.

Public class:

```python
class DataOpsGraphClient:
    def __init__(self, dsn: str | None = None, fallback_dir: Path | None = None): ...
```

Required behavior:

- `is_graph_connected` property.
- If `GRAPH_DSN` is absent, use fixture mode.
- If `DATABASE_URL` is present but `GRAPH_DSN` is absent, implementation may map `GRAPH_DSN` to the AGEClient `dsn` only if explicitly documented.
- If importing ci-platform AGEClient fails, use fixture mode.
- If AGE connection/query fails, fall back to fixtures and set graph state accordingly.
- Every public response includes `source: "graph"` or `source: "fixture"`.
- Only read AGE data.
- Use `AGEClient.serialize_for_age` for every string literal in Cypher.
- No `$params` in DataOps-authored Cypher strings.
- No `CREATE`, `MERGE`, `SET`, `DELETE`, `REMOVE`, `ON CREATE`, or `ON MATCH` in DataOps graph queries.

Required methods:

- `get_pipelines()`
- `get_alerts()`
- `get_system(name)`
- `get_alert(alert_id)`
- `get_blast_radius(alert_id)`
- `get_recurrence(alert_id)`
- `get_factors(alert_id)`
- `compute_impact_scope(system_name)`
- `compute_downstream_urgency(system_name)`
- `compute_recurrence(system_name, category)`

Recommended graph query shapes:

- `get_pipelines`: query `PipelineSystem` nodes with upstream/downstream counts from `FEEDS`.
- `get_alerts`: query `DataQualityAlert` nodes and their affected systems.
- `get_system`: query one `PipelineSystem` by `name`.
- `get_alert`: query one `DataQualityAlert` by `alert_id`.
- `get_blast_radius`: traverse `AFFECTS`, `FEEDS`, and `CASCADES` from alert/system.
- `get_recurrence`: count alerts by system/category over fixture-like historical records.
- `get_factors`: compute DataOps preset factors for the alert.

Fixture fallback must return the same high-level response shapes as graph mode.

## Context Router Contract

Create `apps/dataops/backend/app/context_router.py`.

Endpoints under `/api/context`:

- `GET /pipelines`
- `GET /alerts`
- `GET /system/{name}`
- `GET /alert/{id}`
- `GET /alert/{id}/deps`
- `GET /alert/{id}/recurrence`
- `GET /alert/{id}/factors`
- `POST /alert-metadata`
- `GET /alert-metadata`

Response requirements:

- Graph-backed reads delegate to `DataOpsGraphClient`.
- Missing system returns safe error object, e.g. `{"error": "System not found", "name": name}`.
- Missing alert returns safe error object, e.g. `{"error": "Alert not found", "alert_id": id}`.
- Graph-backed endpoints include `source`.
- Metadata uses `apps/dataops/backend/data/alert_metadata.json`.
- Metadata is keyed by `decision_id`.
- `decision_id` is required; missing value returns HTTP 400 with detail containing `decision_id`.
- Preserve arbitrary JSON fields in metadata records.
- Preserve existing metadata entries on write.

Route naming note:

- The prompt calls for 9 graph-backed context endpoints but lists 7 graph reads plus 2 metadata endpoints. Implement exactly the listed endpoints and treat metadata as context endpoints, not graph-backed reads.

## AE Router Contract

Create `apps/dataops/backend/app/ae_router.py`.

Endpoints under `/api/ae`:

- `GET /recommendation/{alert_id}`
- `GET /impact`
- `GET /pattern-origin`
- `GET /incident`
- `GET /conservation-history`

Rules:

- `match_ae_rule(alert, variant)` must be deterministic.
- Only promoted variants produce recommendations.
- Rejected variants can be returned as explanatory context but must not produce active recommendations.
- `impact`, `pattern-origin`, `incident`, and `conservation-history` read from JSON fixtures.
- Responses include appropriate engine labels:
  - `gae.evolution` for recommendation, impact, pattern-origin, and incident.
  - `gae.calibration` for conservation history.

Recommended recommendation response:

```json
{
  "alert_id": "DOP-001",
  "recommendations": [
    {
      "variant_id": "V-DO-RECUR-001",
      "action": "investigate",
      "reason": "Recurring pipeline issue with downstream impact",
      "confidence": 0.82
    }
  ],
  "count": 1,
  "engine": {"gae": "gae.evolution"}
}
```

## Fixture Data Contract

### `evolution_fixtures.json`

Create 3 variants:

- `V-DO-RECUR-001`
  - `event_type: "promotion_approved"`
  - match fields for recurring alerts, high recurrence, or repeated pipeline/category.
- `V-DO-FRESH-001`
  - `event_type: "promotion_approved"`
  - match fields for `freshness_violation` or low `data_freshness`.
- `V-DO-AUTO-001`
  - `event_type: "promotion_rejected"`
  - rejected auto-approval rule for risky/high-impact alerts.

Each variant should include:

- `id`
- `event_type`
- `variant_id`
- `artifact_type`
- `description`
- `impact`
- `magnitude`
- `timestamp`
- `timestamp_epoch`
- `metadata`
- `source_copilot`
- `source_rule`
- `match`

### `ae_impact.json`

Include:

- `auto_resolved_count`
- `accuracy`
- `active_rules`
- `rejected_rules`
- `breakdown`
- `rejected_example`

### `incident.json`

Include:

- `estimated_cost: 50000`
- incident narrative
- affected systems/datasets
- fingerprint insight including `source_reliability` and `recurrence_frequency`

### `conservation_history.json`

Include 3 events:

- first denied
- second denied
- third approved

Each event should include timestamp, requested action, conservation status, reason, and metrics.

### Fallback Fixtures

Create:

- `apps/dataops/backend/data/fallback/pipelines.json`
- `apps/dataops/backend/data/fallback/alerts.json`
- `apps/dataops/backend/data/fallback/blast_radius.json`

Generate from ci-platform `dataops/schema.py` and SDK `dataops_seed.json`:

- `pipelines`: 9 systems with status, alert counts, upstream counts, downstream counts, owner, SLA, reliability, and criticality.
- `alerts`: 20 alerts from seed mapped via `DATASET_SYSTEM_MAP`; severity derived from `impact_scope`; recurrence count derived from `recurrence_frequency`; system name from schema map.
- `blast_radius`: dependency trees from `FEEDS_EDGES`, keyed by alert or system.

No live graph is required to generate or test these fixtures.

## Test Plan

Create `apps/dataops/backend/tests/conftest.py`:

- Add backend root, repo root, GAE path, and ci-platform path as needed.
- Copy DataOps fixture JSON into temp data.
- Initialize temp `alert_metadata.json` as `{}`.
- Monkeypatch data dirs and graph client factory to fixture mode by default.
- Use temp SQLite DB in `create_app(db_path=...)`.
- No live AGE, network, browser, or external DB required.

Create `apps/dataops/backend/tests/test_graph_queries.py`:

- `test_fixture_fallback_pipelines`
- `test_fixture_fallback_alerts`
- `test_get_system_fixture`
- `test_get_alert_fixture`
- `test_blast_radius_tree`
- `test_compute_impact_scope_fixture`
- `test_compute_downstream_urgency_fixture`
- `test_compute_recurrence_fixture`
- `test_mocked_ageclient_compute_impact_scope`
- `test_graph_query_strings_are_read_only`

Create `apps/dataops/backend/tests/test_dataops_backend.py`:

- `test_health`
- `test_pipelines`
- `test_alerts`
- `test_alert_detail`
- `test_alert_deps`
- `test_alert_recurrence`
- `test_alert_factors`
- `test_alert_metadata_store_and_retrieve`
- `test_alert_metadata_requires_decision_id`
- `test_ae_recommendation_match`
- `test_ae_recommendation_no_match`
- `test_ae_impact`
- `test_pattern_origin`
- `test_incident`
- `test_conservation_history`
- `test_score_via_sdk_router`
- `test_learn_returns_reward`
- `test_conservation_status`
- `test_conservation_what_if`
- `test_evolution_variants`
- `test_fingerprint`

Assertions:

- Existing SDK route shapes should match SDK router contracts.
- Context endpoint responses should include `source`.
- Tests must not need `GRAPH_DSN`.
- Mocked graph tests should prove graph mode without live AGE by substituting a fake AGEClient with async `run_query`.
- Metadata tests must mutate only temp `alert_metadata.json`.

## Validation Commands

Run from repo root:

```powershell
python -m pytest apps/dataops/backend/tests/ -v --timeout=120
python -m pytest tests/ -q --timeout=120
python -c "from apps.dataops.backend.app.main import app; print(app.title)"
```

No live graph should be required for any validation command.

If `pytest-timeout` is unavailable, rerun pytest commands without `--timeout=120` and record that the plugin is unavailable.

## Prompt Verification Pass

- Prompt 0 supplied the SDK router APIs, DataOps preset shape, AGEClient API, and ci-platform schema.
- The plan does not require SDK or ci-platform edits.
- The plan includes JSON fixture fallback for all graph-backed behavior.
- The plan includes mocked graph tests and fixture-only backend tests.
- The plan is self-contained and scoped to `apps/dataops/backend/**`, `apps/dataops/.env.example`, and this implementation plan.

## Residual Risks

- The prompt says `GRAPH_DSN`, while `AGEClient` uses `DATABASE_URL`; the backend should support `GRAPH_DSN` explicitly and pass it as `dsn` to `AGEClient`, while still allowing `DATABASE_URL` if needed.
- The prompt says 9 graph-backed context endpoints, but the endpoint list contains 7 graph reads plus 2 metadata endpoints. Implement the listed endpoints exactly.
- The scoring preset category order differs from the ci-platform schema category order. Use scoring preset order for scoring factor/tensor contracts.
- AGE query strings must remain read-only and use serializer-inlined literals to honor the DataOps safety requirements.
