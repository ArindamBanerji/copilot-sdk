# GRAPH-TPC Domain Graph Contracts Implementation Plan

## 1. Executive Summary

This plan adds a domain-agnostic graph contract layer to `copilot-sdk` and per-domain contract/seed modules for Trading, Purchasing, and DataOps. The SDK currently exposes persistence protocols for decisions, outcomes, centroids, and evolution events, but it has no `GraphContract`, `NodeType`, or `EdgeType` abstraction and does not export such types from `copilot_sdk.graph` (`copilot_sdk/graph/protocol.py:8-76`, `copilot_sdk/graph/__init__.py:1-7`).

The implementation should be split into protocol, per-domain contracts/seeds, and tests. Seed functions must be deterministic and return node/edge dictionaries only; they must not write to AGE, SQLite, or app databases. Cross-domain tests must avoid importing multiple backend `app.*` packages in one Python process because current app tests add each backend root to `sys.path` and import `app.main` or `app.context_router` (`apps/trading/backend/tests/conftest.py:11-19`, `apps/purchasing/backend/tests/conftest.py:11-19`, `apps/dataops/backend/tests/conftest.py:11-18`, `apps/dataops/backend/tests/conftest.py:53-67`).

Baseline validation is currently green:

- `python -m pytest tests\ -q --timeout=120`: 306 passed, 612 warnings.
- `python -m pytest apps\trading\backend\tests\ -q --timeout=120`: 26 passed, 52 warnings.
- `python -m pytest apps\purchasing\backend\tests\ -q --timeout=120`: 33 passed, 66 warnings.
- `python -m pytest apps\dataops\backend\tests\ -q --timeout=120`: 120 passed, 240 warnings.

READY_FOR_IMPLEMENTATION: YES.

## 2. Repos and Scope

Resolved repository paths:

- Target repo: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk` exists.
- Reference-only repo: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot` exists.
- Reference-only repo: `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\ci-platform` exists.

Scope constraints from the SDK repo:

- `CLAUDE.md` requires source-backed claims and file/line citations (`CLAUDE.md:1-8`).
- The SDK is the public package and should define protocols, not domain internals (`CLAUDE.md:22-29`).
- The SDK must not import S2P/SOC app internals or `gen-ai-roi-demo-v4-v50` (`CLAUDE.md:39-47`).
- Architecture/codebase questions should first read `graphify-out/GRAPH_REPORT.md`; the report identifies `DomainConfig` as a core abstraction (`graphify-out/GRAPH_REPORT.md:49-59`).

Allowed implementation scope for follow-up prompts:

- SDK graph contract protocol in `copilot_sdk/graph/contract.py` and export in `copilot_sdk/graph/__init__.py`.
- Per-app graph contracts and deterministic seed functions under each app backend package.
- Tests under `tests/graph` and each app's existing backend test directory.

Out of scope:

- No edits to `s2p-copilot`, `ci-platform`, source AGE writers, source app routers, frontend, config, seed data, or any forbidden repo.
- No graph writes from the new seed functions.
- Do not modify `demo.py`; it is evidence for existing graph mode only, not an implementation target (`demo.py:252-255`, `demo.py:378-399`).
- Do not modify `copilot_sdk/graph/protocol.py`; `GraphStore` is a persistence protocol and GRAPH-TPC should add a separate contract model in `copilot_sdk/graph/contract.py` (`copilot_sdk/graph/protocol.py:8-76`).

## 3. Source Evidence / Current Behavior

Current SDK graph layer:

- `GraphStore` is runtime-checkable and covers decision/outcome read-write behavior (`copilot_sdk/graph/protocol.py:8-52`).
- `GraphStore` also has centroid methods and evolution-event persistence (`copilot_sdk/graph/protocol.py:54-76`).
- `copilot_sdk.graph` exports `GraphStore`, `InMemoryGraphStore`, and `SQLiteGraphStore`, but no contract types (`copilot_sdk/graph/__init__.py:1-7`).
- `InMemoryGraphStore` stores decisions, outcomes, centroid checkpoints, and evolution events in lists/dicts (`copilot_sdk/graph/memory_store.py:12-20`, `copilot_sdk/graph/memory_store.py:105-150`).
- `SQLiteGraphStore` is an open-call-close adapter over `DecisionStore` and persists centroids/evolution events through that store (`copilot_sdk/graph/sqlite_store.py:14-20`, `copilot_sdk/graph/sqlite_store.py:136-161`, `copilot_sdk/graph/sqlite_store.py:163-199`).

Current launcher graph behavior:

- The launcher knows Trading, Purchasing, DataOps, and S2P backend/frontend paths (`demo.py:38-68`).
- `--graph` only sets `GRAPH_DSN` and optionally runs the ci-platform DataOps seed script; this is not a reusable SDK/domain contract (`demo.py:252-255`, `demo.py:378-399`).

S2P reference pattern:

- `s2p-copilot/backend/app/graph_contract.py` is a dictionary contract with `graph_name`, node type definitions, and edge type definitions (`s2p-copilot/backend/app/graph_contract.py:3-89`).
- S2P includes process-oriented node types such as `ProcessModel`, `ProcessVariant`, and `Activity` (`s2p-copilot/backend/app/graph_contract.py:51-76`).
- The requested `s2p-copilot/backend/app/seed_graph.py` path is missing. The existing seed implementation is a script, `s2p-copilot/scripts/seed_s2p_graph.py`, which imports `app.graph_contract`, builds a seed plan, and can write it to AGE (`s2p-copilot/scripts/seed_s2p_graph.py:13-19`, `s2p-copilot/scripts/seed_s2p_graph.py:113-127`, `s2p-copilot/scripts/seed_s2p_graph.py:329-360`).
- For GRAPH-TPC, reuse the S2P idea of declarative labels and generated nodes/edges, but do not copy the AGE-writing script pattern. New app seed functions should return in-memory plans only.

Existing test patterns:

- SDK graph protocol tests assert `InMemoryGraphStore` and `SQLiteGraphStore` satisfy `GraphStore`, and list required protocol methods (`tests/graph/test_protocol.py:3-29`).
- In-memory and SQLite graph tests are behavior-oriented and verify stored fields/order/limits rather than only checking source strings (`tests/graph/test_memory_store.py:8-29`, `tests/graph/test_memory_store.py:87-129`, `tests/graph/test_sqlite_store.py:75-129`).

## 4. Domain Entity Discovery

### Trading

Backend and data evidence:

- Trading mounts SDK scoring/conservation/self-computation routers and uses a Trading SQLite graph store with `domain="trading"` (`apps/trading/backend/app/main.py:20-37`, `apps/trading/backend/app/main.py:102-121`).
- Trading app tests add backend and repo roots to `sys.path`, then import `app.context_router` and `app.main` (`apps/trading/backend/tests/conftest.py:11-19`).
- Trading categories are `equity_long`, `equity_short`, `crypto_spot`, `options`, and `etf`; actions are `buy`, `hold`, `sell`; factors are `conviction`, `research_depth`, `technical_signal`, `position_size`, `time_horizon`, and `market_regime` (`copilot_sdk/scoring/presets/trading.py:20-40`).
- Trading context endpoints use cached market/ticker/portfolio/similar-trade data (`apps/trading/backend/app/context_router.py:77-102`, `apps/trading/backend/app/context_router.py:113-160`).
- Trading seed rows include trade/instrument fields such as `trade_id`, `ticker`, `direction`, `category`, `thesis_type`, `timeframe`, shares/prices, PnL, and `vix_at_entry` (`apps/trading/backend/data/trading_seed_v2.json:1-38`).
- Portfolio summary has aggregate position/exposure fields (`apps/trading/backend/data/portfolio_summary.json:1-15`), and market snapshot has SPY/VIX/sector regime data (`apps/trading/backend/data/market_snapshot.json:1-18`).

Recommended Trading entities: `Decision`, `Instrument`, `Portfolio`, `Position`, `TradeSignal`, `RiskFactor`, `MarketEvent`.

### Purchasing

Backend and data evidence:

- Purchasing mounts SDK scoring/evolution/conservation/self-computation routers and uses a Purchasing SQLite graph store with `domain="purchasing"` (`apps/purchasing/backend/app/main.py:22-40`, `apps/purchasing/backend/app/main.py:158-181`).
- Purchasing app tests add backend and repo roots to `sys.path`, then import `app.context_router` and `app.main` (`apps/purchasing/backend/tests/conftest.py:11-19`).
- Purchasing categories are `protein`, `produce`, `dairy`, `dry_goods`, and `beverages`; actions are `order_as_planned`, `order_more`, `order_less`, and `skip`; factors are `expected_demand`, `day_of_week`, `weather_forecast`, `event_flag`, `historical_waste`, and `supplier_lead_time` (`copilot_sdk/scoring/presets/purchasing.py:20-45`).
- Purchasing context includes item, waste, weather, metadata, analytics, and similar-order endpoints (`apps/purchasing/backend/app/context_router.py:85-122`, `apps/purchasing/backend/app/context_router.py:125-181`).
- Purchasing seed rows include order/item/category, quantity, day/event, expected demand, weather, lead time, action taken, waste, stockout, and total cost fields (`apps/purchasing/backend/data/purchasing_seed_v2.json:1-25`).
- Waste history is keyed by item names (`apps/purchasing/backend/data/waste_history.json:1-22`), and weather cache supplies external weather context (`apps/purchasing/backend/data/weather_cache.json:1-7`).

Recommended Purchasing entities: `Decision`, `Item`, `Vendor`, `Order`, `Category`, `BudgetCenter`, `Event`.

### DataOps

Backend and data evidence:

- DataOps mounts SDK scoring/conservation/evolution/self-computation routers and uses a DataOps SQLite graph store with `domain="dataops"` (`apps/dataops/backend/app/main.py:23-43`, `apps/dataops/backend/app/main.py:121-146`).
- DataOps app tests add backend, repo, and ci-platform roots to `sys.path`, then import `app.*` modules inside fixtures (`apps/dataops/backend/tests/conftest.py:11-18`, `apps/dataops/backend/tests/conftest.py:53-67`).
- DataOps categories are `schema_change`, `volume_anomaly`, `quality_anomaly`, `freshness_violation`, `pipeline_failure`, and `transform_drift`; actions are `auto_approve`, `investigate`, `escalate_to_owner`, `pause_downstream`, and `refer_to_specialist`; factors are `impact_scope`, `source_reliability`, `recurrence_frequency`, `downstream_urgency`, `data_freshness`, and `business_criticality` (`copilot_sdk/scoring/presets/dataops.py:20-47`).
- DataOps context has fallback graph/pipeline, connector, and similarity helpers; factor and category names are duplicated locally for context routes (`apps/dataops/backend/app/context_router.py:18-45`, `apps/dataops/backend/app/context_router.py:80-107`).
- Fallback alerts include `alert_id`, `event_id`, `dataset`, `system`, category, action taken, correctness, severity, status, and factor values (`apps/dataops/backend/data/fallback/alerts.json:1-24`).
- Fallback pipelines include pipeline name/display name, SLA, criticality, reliability, owner, status, upstream/downstream links, and alert counts (`apps/dataops/backend/data/fallback/pipelines.json:1-20`, `apps/dataops/backend/data/fallback/pipelines.json:73-88`).
- Transformations include system-scoped transformation IDs, source/target datasets, schema columns, duration, and status (`apps/dataops/backend/data/transformations.json:1-52`, `apps/dataops/backend/data/transformations.json:53-78`).
- Celonis process data includes a `process_model`, `variant`, activities, bottleneck activity, cross-graph insights, recommendations, and compounding trajectory (`apps/dataops/backend/data/celonis_process_data.json:1-88`).

Recommended DataOps entities: `Decision`, `Pipeline`, `Dataset`, `QualityRule`, `Alert`, `ProcessModel`, `Activity`, `Transformation`.

## 5. Proposed Contract Schemas

### SDK contract API

Create `copilot_sdk/graph/contract.py` with:

```python
@dataclass(frozen=True)
class NodeType:
    label: str
    key: str
    properties: tuple[str, ...] = ()

@dataclass(frozen=True)
class EdgeType:
    label: str
    from_label: str
    to_label: str
    properties: tuple[str, ...] = ()

@dataclass(frozen=True)
class GraphContract:
    graph_name: str
    node_types: tuple[NodeType, ...]
    edge_types: tuple[EdgeType, ...]
```

`GraphContract` behavior:

- `node_count` returns `len(node_types)`.
- `edge_count` returns `len(edge_types)`.
- `validate() -> list[str]` returns all validation errors, not fail-fast.
- Validation messages should include the offending label/name/triple so failures are actionable.
- Validation checks:
  - `graph_name` is non-empty.
  - Duplicate node labels are rejected.
  - Duplicate exact edge triples `(label, from_label, to_label)` are rejected.
  - Every edge endpoint references an existing node label.
  - Required node label `Decision` exists.
  - Required edge label `DECIDED_ON` exists.

Export `GraphContract`, `NodeType`, and `EdgeType` from `copilot_sdk/graph/__init__.py`, alongside the existing `GraphStore` exports (`copilot_sdk/graph/__init__.py:1-7`).

### Trading contract

Create `apps/trading/backend/app/graph_contract.py`:

- `graph_name`: `trading_graph`.
- Node types:
  - `Decision`: key `decision_id`; properties include `decision_id`, `category`, `recommended_action`, `confidence`, `created_at`.
  - `Instrument`: key `ticker`; properties include `ticker`, `asset_class`, `category`, `sector`.
  - `Portfolio`: key `portfolio_id`; properties include `portfolio_id`, `name`, `total_value`, `cash_buffer`.
  - `Position`: key `position_id`; properties include `position_id`, `ticker`, `shares`, `entry_price`, `position_size`.
  - `TradeSignal`: key `signal_id`; properties include `signal_id`, `thesis_type`, `timeframe`, `technical_signal`, `conviction`.
  - `RiskFactor`: key `factor_id`; properties include `factor_id`, `name`, `value`.
  - `MarketEvent`: key `event_id`; properties include `event_id`, `date`, `vix_at_entry`, `market_regime`.
- Edge types:
  - `DECIDED_ON`: `Decision -> Instrument`.
  - `HOLDS`: `Portfolio -> Position`.
  - `POSITION_IN`: `Position -> Instrument`.
  - `TRIGGERED_BY`: `Decision -> TradeSignal`.
  - `RISK_EXPOSURE`: `Position -> RiskFactor`.
  - `EVALUATED_WITH`: `Decision -> RiskFactor`.
  - `OCCURRED_DURING`: `TradeSignal -> MarketEvent`.

### Purchasing contract

Create `apps/purchasing/backend/app/graph_contract.py`:

- `graph_name`: `purchasing_graph`.
- Node types:
  - `Decision`: key `decision_id`; properties include `decision_id`, `category`, `recommended_action`, `confidence`, `created_at`.
  - `Item`: key `item_id`; properties include `item_id`, `name`, `display_name`, `category`, `unit`.
  - `Vendor`: key `vendor_id`; properties include `vendor_id`, `name`, `lead_time`, `reliability`.
  - `Order`: key `order_id`; properties include `order_id`, `item`, `quantity_lbs`, `date`, `action_taken`.
  - `Category`: key `category_id`; properties include `category_id`, `name`.
  - `BudgetCenter`: key `budget_center_id`; properties include `budget_center_id`, `name`, `category`.
  - `Event`: key `event_id`; properties include `event_id`, `event_type`, `date`, `weather_factor`.
- Edge types:
  - `DECIDED_ON`: `Decision -> Order`.
  - `ORDERED_FROM`: `Order -> Vendor`.
  - `ORDER_FOR`: `Order -> Item`.
  - `IN_CATEGORY`: `Item -> Category`.
  - `BUDGET_FROM`: `Order -> BudgetCenter`.
  - `TRIGGERED_BY`: `Order -> Event`.
  - `SUPPLIED_BY`: `Item -> Vendor`.

### DataOps contract

Create `apps/dataops/backend/app/graph_contract.py`:

- `graph_name`: `dataops_graph`.
- Node types:
  - `Decision`: key `decision_id`; properties include `decision_id`, `category`, `recommended_action`, `confidence`, `created_at`.
  - `Pipeline`: key `pipeline_id`; properties include `pipeline_id`, `name`, `display_name`, `owner`, `status`, `sla_minutes`.
  - `Dataset`: key `dataset_id`; properties include `dataset_id`, `name`, `system`, `schema_columns`.
  - `QualityRule`: key `rule_id`; properties include `rule_id`, `name`, `category`, `severity`.
  - `Alert`: key `alert_id`; properties include `alert_id`, `event_id`, `dataset`, `system`, `category`, `severity`, `status`.
  - `ProcessModel`: key `model_id`; properties include `model_id`, `name`, `variant`, `source`.
  - `Activity`: key `activity_id`; properties include `activity_id`, `name`, `avg_duration_hours`, `case_count`, `status`, `bottleneck`.
  - `Transformation`: key `transformation_id`; properties include `transformation_id`, `name`, `type`, `source`, `target`, `status`.
- Edge types:
  - `DECIDED_ON`: `Decision -> Alert`.
  - `PRODUCES`: `Transformation -> Dataset`.
  - `CONSUMES`: `Transformation -> Dataset`.
  - `MONITORS`: `QualityRule -> Dataset`.
  - `DETECTED_IN`: `Alert -> Pipeline`.
  - `CONTAINS`: `ProcessModel -> Activity`.
  - `FOLLOWS`: `Activity -> Activity`.
  - `TRIGGERED_BY`: `Alert -> Activity`.

## 6. Seed Data Design

General seed output shape:

```python
nodes: list[dict[str, Any]]
edges: list[dict[str, Any]]

node = {"id": str, "label": str, "properties": dict[str, Any]}
edge = {"id": str, "label": str, "from_id": str, "to_id": str, "properties": dict[str, Any]}
```

All seed functions must:

- Accept `seed: int = 42`.
- Be deterministic for identical inputs and seed.
- Return `tuple[list[dict[str, Any]], list[dict[str, Any]]]`.
- Avoid writes, network calls, AGE clients, SQLite connections, and environment-variable dependencies.
- Include at least one seeded node for every contract node label and at least one seeded edge for every contract edge label.
- Include universal `Decision` nodes and `DECIDED_ON` edges.
- Avoid forbidden/SOC vocabulary in labels and seed text.
- Use a stable node ID convention, preferably `"{label}:{natural_key}"`, where `natural_key` is the node type key value. This prevents accidental edge endpoint drift.
- Build edges only from IDs returned by the node creation/deduplication helper. Do not independently reconstruct edge endpoint strings in separate code paths.
- Keep all random choices behind a local `random.Random(seed)` instance. Do not use global `random.seed()`.
- Return JSON-serializable primitives only.

Required seed helper behavior:

- `_node_id(label, natural_key) -> str` normalizes labels/keys consistently.
- `_add_node(...) -> str` returns the created or existing node ID.
- `_add_edge(...)` accepts `from_id` and `to_id` that have already been returned by `_add_node`.
- Tests must construct `node_ids = {node["id"] for node in nodes}` and assert every edge's `from_id` and `to_id` are in that set.

### Trading seed

Create `apps/trading/backend/app/seed_graph.py`:

```python
def seed_trading_graph(seed: int = 42) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ...
```

Seed source design:

- Read `apps/trading/backend/data/trading_seed_v2.json` using `Path(__file__).resolve().parents[1] / "data"`.
- Derive `Instrument` from `ticker` and `category`.
- Derive one `Portfolio` from `portfolio_summary.json`.
- Derive `Position` from trade rows using `trade_id`, `ticker`, `shares`, `entry_price`, `position_size`.
- Derive `TradeSignal` from `thesis_type`, `timeframe`, `technical_signal`, and `conviction`.
- Derive `RiskFactor` nodes from Trading factor names in the preset.
- Derive `MarketEvent` from `date`, `vix_at_entry`, and `market_regime`.
- Create synthetic `Decision` nodes from `trade_id`, `category`, and `action_taken`.

Target size: around 150 nodes and 200 edges. Do not hardcode exact counts into tests.

### Purchasing seed

Create `apps/purchasing/backend/app/seed_graph.py`:

```python
def seed_purchasing_graph(seed: int = 42) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ...
```

Seed source design:

- Read `apps/purchasing/backend/data/purchasing_seed_v2.json`.
- Derive `Order` from `order_id`.
- Derive `Item` from `item`/`display_name`/`category`.
- Derive `Category` from preset categories and row categories.
- Derive `Vendor` deterministically from item/category/lead-time context because fixture rows expose `supplier_lead_time` but no vendor IDs (`apps/purchasing/backend/data/purchasing_seed_v2.json:12-18`).
- Derive `BudgetCenter` from category.
- Derive `Event` from `is_event_day`, `event_type`, `date`, and `weather_cache.json`.
- Create synthetic `Decision` nodes from `order_id`, `category`, and `action_taken`.

Target size: around 210 nodes and 300 edges. Do not hardcode exact counts into tests.

### DataOps seed

Create `apps/dataops/backend/app/seed_graph.py`:

```python
def seed_dataops_graph(seed: int = 42) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ...
```

Seed source design:

- Read `apps/dataops/backend/data/fallback/alerts.json` for `Alert`, `Decision`, and category/action context.
- Read `apps/dataops/backend/data/fallback/pipelines.json` for `Pipeline` nodes and upstream/downstream relationships.
- Read `apps/dataops/backend/data/transformations.json` for `Transformation` and `Dataset` nodes.
- Read `apps/dataops/backend/data/celonis_process_data.json` for `ProcessModel` and `Activity` nodes. This is required; the file contains process model, variant, activity list, bottleneck activity, recommendations, and trajectory fields (`apps/dataops/backend/data/celonis_process_data.json:1-88`).
- Derive `QualityRule` nodes from alert categories and severity bands.
- Create `FOLLOWS` edges between activities in Celonis activity order.
- Do not hardcode Celonis process nodes. At minimum, the seeded `ProcessModel` name must equal `process_model` from `celonis_process_data.json`, and seeded `Activity` node IDs/names must be derived from the JSON `activities` array (`apps/dataops/backend/data/celonis_process_data.json:1-42`).

Target size: around 160 nodes and 220 edges. Do not hardcode exact counts into tests.

## 7. Import Strategy for Cross-Domain Tests

Risk:

- App backend tests currently import modules through the package name `app` after inserting a backend root into `sys.path` (`apps/trading/backend/tests/conftest.py:11-19`, `apps/purchasing/backend/tests/conftest.py:11-19`, `apps/dataops/backend/tests/conftest.py:11-18`, `apps/dataops/backend/tests/conftest.py:53-67`).
- In one process, importing `app.graph_contract` for Trading, then Purchasing, then DataOps can reuse `sys.modules["app"]` and resolve the wrong backend package.

Recommended pattern:

- Per-domain app tests should use each app's existing import style, because they run inside that app's backend test directory and fixture setup.
- Cross-domain tests under `tests/graph/test_contract_cross.py` should not import `app.graph_contract`.
- Use `importlib.util.spec_from_file_location()` with unique names such as:
  - `graph_tpc_trading_contract`
  - `graph_tpc_purchasing_contract`
  - `graph_tpc_dataops_contract`
  - `graph_tpc_trading_seed`
  - `graph_tpc_purchasing_seed`
  - `graph_tpc_dataops_seed`
- Keep seed modules self-contained enough that file-path imports work. If a seed module needs its contract, prefer importing `copilot_sdk.graph` and local constants defined in the same seed module, or structure the module so cross-domain tests can load it by path without resolving `app.*`.
- If relative app imports become necessary, run those particular cross-domain import checks in subprocesses with isolated `PYTHONPATH`/working directory instead of importing multiple `app` packages in one pytest process.
- Cross-domain tests should snapshot and restore `sys.path` and must not add app backend roots globally.
- Cross-domain tests should not leave `sys.modules["app"]` populated. If a helper detects `sys.modules["app"]` before the test, skip the in-process import path and use subprocess isolation for that domain.
- Do not require a combined same-process pytest invocation across all three app backend suites. The app suites expose separate top-level `app` packages, so validate them as separate pytest invocations and use a subprocess-isolated guard in `tests\graph\test_contract_cross.py` when `app.*` imports must be exercised.

## 8. Test Plan

### SDK protocol tests

Add `tests/graph/test_contract.py`:

- `test_graph_contract_validate_clean_contract`.
- `test_graph_contract_requires_graph_name`.
- `test_graph_contract_rejects_duplicate_node_labels`.
- `test_graph_contract_rejects_duplicate_exact_edges`.
- `test_graph_contract_rejects_unknown_edge_endpoint`.
- `test_graph_contract_requires_decision_node`.
- `test_graph_contract_requires_decided_on_edge`.
- `test_graph_contract_counts_nodes_and_edges`.
- `test_graph_contract_exports_from_graph_package`.

### Trading app tests

Add tests in `apps/trading/backend/tests/`, using the current app test import pattern:

- Contract validates cleanly.
- `Decision` node exists.
- `DECIDED_ON` edge exists.
- `graph_name == "trading_graph"`.
- Seed output is deterministic for `seed=42`.
- Seed nodes have `id`, `label`, `properties`.
- Seed edges have `id`, `label`, `from_id`, `to_id`, `properties`.
- Seed edge endpoints reference actual seeded node IDs.
- Seed includes all contract labels.
- No forbidden/SOC vocabulary in labels or seed content.
- Seed tests should assert each contract node label appears in `node["label"]` and each contract edge label appears in `edge["label"]`; do not rely on source-string scans alone.

### Purchasing app tests

Same behavior tests as Trading, with `graph_name == "purchasing_graph"` and Purchasing seed/entity expectations.

### DataOps app tests

Same behavior tests as Trading, with `graph_name == "dataops_graph"`, plus:

- Seed includes at least one `ProcessModel` node derived from `celonis_process_data.json`.
- Seed includes `Activity` nodes derived from Celonis activities.
- Seed includes at least one activity marked as bottleneck when the source data has a bottleneck.
- Seeded `ProcessModel.properties["name"]` should match the JSON `process_model`, and the set of seeded `Activity` IDs/names should cover the JSON activities. This catches hardcoded placeholder process nodes.

### Cross-domain tests

Add `tests/graph/test_contract_cross.py`:

- Load each contract module by file path with unique module names.
- Assert graph names are unique.
- Assert every contract validates cleanly.
- Assert all domains include `Decision` and `DECIDED_ON`.
- Load each seed module by file path or subprocess isolation, as described above.
- Assert deterministic seeds per domain.
- Assert no seed edge points to a missing node.
- Assert every domain seed includes all labels declared by that domain's contract.
- Assert no forbidden/SOC vocabulary across contract labels and seed text.
- Add a subprocess-isolated guard that launches one Python process per domain, inserts only that app backend root, imports `app.graph_contract` and `app.seed_graph`, validates the contract, and runs the seed. Do not add a same-process combined app-suite requirement; that is the known unsupported import pattern.

### Review step

After implementation, run a GPT-5.5 line-by-line review prompt covering:

- `copilot_sdk/graph/contract.py`
- `copilot_sdk/graph/__init__.py`
- each app `graph_contract.py`
- each app `seed_graph.py`
- `tests/graph/test_contract.py`
- `tests/graph/test_contract_cross.py`
- changed app backend tests

The review must inspect local files, cite file:line evidence, verify no source writes outside allowed files, verify no forbidden repo edits, and classify findings P1/P2/P3.

## 9. Implementation File List

SDK:

- Create `copilot_sdk/graph/contract.py`.
- Update `copilot_sdk/graph/__init__.py`.
- Create `tests/graph/test_contract.py`.
- Create `tests/graph/test_contract_cross.py`.

Trading:

- Create `apps/trading/backend/app/graph_contract.py`.
- Create `apps/trading/backend/app/seed_graph.py`.
- Add `apps/trading/backend/tests/test_graph_contract.py`.

Purchasing:

- Create `apps/purchasing/backend/app/graph_contract.py`.
- Create `apps/purchasing/backend/app/seed_graph.py`.
- Add `apps/purchasing/backend/tests/test_graph_contract.py`.

DataOps:

- Create `apps/dataops/backend/app/graph_contract.py`.
- Create `apps/dataops/backend/app/seed_graph.py`.
- Add `apps/dataops/backend/tests/test_graph_contract.py`.

No changes should be made to source routers, scoring, frontend, config, existing seed fixture files, `s2p-copilot`, `ci-platform`, or forbidden repos.

Implementation split recommendation:

- Split this into two implementation prompts rather than one large prompt.
- Prompt A: SDK-only contract model/export and `tests/graph/test_contract.py`.
- Prompt B: Trading/Purchasing/DataOps `graph_contract.py`, `seed_graph.py`, per-app tests, and `tests/graph/test_contract_cross.py`.
- Prompt C: GPT-5.5 line-by-line review.
- Rationale: the SDK contract API is small and public, while the domain seed work touches three independent app packages and has higher import-collision risk.

## 10. Validation Commands

Run from `C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk`:

```powershell
python -m pytest tests\graph\test_contract.py -v --timeout=120
python -m pytest tests\graph\test_contract_cross.py -v --timeout=120
python -m pytest tests\graph\ -v --timeout=120
python -m pytest apps\trading\backend\tests\ -q --timeout=120
python -m pytest apps\purchasing\backend\tests\ -q --timeout=120
python -m pytest apps\dataops\backend\tests\ -q --timeout=120
python -m pytest tests\graph\ apps\trading\backend\tests\ apps\purchasing\backend\tests\ apps\dataops\backend\tests\ -q --timeout=120
python -m pytest tests\ -q --timeout=120
```

Static scans:

```powershell
Select-String -Path copilot_sdk\graph\contract.py -Pattern "app\.domains|gen-ai-roi|SOC|Alert|Triage"
Select-String -Path apps\trading\backend\app\graph_contract.py,apps\trading\backend\app\seed_graph.py -Pattern "credential_access|lateral_movement|data_exfiltration|SOC"
Select-String -Path apps\purchasing\backend\app\graph_contract.py,apps\purchasing\backend\app\seed_graph.py -Pattern "credential_access|lateral_movement|data_exfiltration|SOC"
Select-String -Path apps\dataops\backend\app\graph_contract.py,apps\dataops\backend\app\seed_graph.py -Pattern "credential_access|lateral_movement|data_exfiltration|SOC"
```

Baseline results before implementation:

- SDK root tests: 306 passed, 612 warnings.
- Trading backend tests: 26 passed, 52 warnings.
- Purchasing backend tests: 33 passed, 66 warnings.
- DataOps backend tests: 120 passed, 240 warnings.

## 11. Risks / Blockers

Risks:

- Cross-domain tests can collide on `app.*` imports unless they use file-path imports with unique module names or subprocess isolation.
- S2P's requested `backend/app/seed_graph.py` reference file is missing, and the existing S2P seed script writes to AGE. The new SDK/app design must use the declarative contract idea but not the write-to-AGE behavior.
- Purchasing fixture rows expose `supplier_lead_time` but no explicit vendor fixture in the inspected files, so vendor IDs must be deterministic synthetic IDs derived from item/category context.
- DataOps seed must read Celonis data from the app-local file path, not from environment variables.
- Exact seed counts should remain flexible. Tests should assert minimum coverage and endpoint/edge integrity, not brittle exact totals.
- The SDK repo rules say class names containing `Alert` do not belong in SDK code (`CLAUDE.md:39-47`). The DataOps app may use an `Alert` node label because DataOps fixture data is alert-shaped, but `copilot_sdk/graph/contract.py` must remain domain-neutral and must not define SDK classes or constants named `Alert`.
- Full-suite failures can occur if `tests/graph/test_contract_cross.py` imports backend `app.*` modules or mutates `sys.path`; keep it file-path/subprocess isolated.

Blockers:

- None found. All referenced target paths either exist or are explicitly recorded as missing reference-only inputs.

## 12. Prompt Verification Pass Results

1. All referenced paths exist or missing paths are recorded: PASS. `s2p-copilot/backend/app/seed_graph.py` is missing; `s2p-copilot/scripts/seed_s2p_graph.py` exists as the actual seed reference.
2. The plan does not rely on environment variables: PASS. Seed functions use app-local `Path(__file__)` resolution.
3. The plan does not require `ci-platform` or `s2p-copilot` edits: PASS.
4. The plan does not touch forbidden repos: PASS.
5. Cross-domain import strategy avoids `app` module collision: PASS.
6. Test plan includes behavior tests, not only source-string tests: PASS.
7. Plan includes a GPT-5.5 post-implementation line-by-line review step: PASS.
8. Unresolved items: none. READY_FOR_IMPLEMENTATION: YES.

## 13. Reading Log

Read in `copilot-sdk`:

- `CLAUDE.md` (`CLAUDE.md:1-70`)
- `graphify-out/GRAPH_REPORT.md` (`graphify-out/GRAPH_REPORT.md:1-80`)
- `copilot_sdk/graph/protocol.py` (`copilot_sdk/graph/protocol.py:1-76`)
- `copilot_sdk/graph/__init__.py` (`copilot_sdk/graph/__init__.py:1-7`)
- `copilot_sdk/graph/memory_store.py` (`copilot_sdk/graph/memory_store.py:1-159`)
- `copilot_sdk/graph/sqlite_store.py` (`copilot_sdk/graph/sqlite_store.py:1-213`)
- `demo.py` (`demo.py:1-120`, `demo.py:245-430`)
- `tests/graph/test_protocol.py` (`tests/graph/test_protocol.py:1-40`)
- `tests/graph/test_memory_store.py` (`tests/graph/test_memory_store.py:1-155`)
- `tests/graph/test_sqlite_store.py` (`tests/graph/test_sqlite_store.py:1-185`)
- `apps/trading/backend/app/main.py` (`apps/trading/backend/app/main.py:1-134`)
- `apps/trading/backend/app/context_router.py` (`apps/trading/backend/app/context_router.py:1-178`)
- `copilot_sdk/scoring/presets/trading.py` (`copilot_sdk/scoring/presets/trading.py:1-73`)
- `apps/trading/backend/tests/conftest.py` (`apps/trading/backend/tests/conftest.py:1-46`)
- `apps/trading/backend/data/trading_seed_v2.json` (`apps/trading/backend/data/trading_seed_v2.json:1-180`)
- `apps/trading/backend/data/portfolio_summary.json` (`apps/trading/backend/data/portfolio_summary.json:1-15`)
- `apps/trading/backend/data/market_snapshot.json` (`apps/trading/backend/data/market_snapshot.json:1-18`)
- `apps/purchasing/backend/app/main.py` (`apps/purchasing/backend/app/main.py:1-194`)
- `apps/purchasing/backend/app/context_router.py` (`apps/purchasing/backend/app/context_router.py:1-181`)
- `copilot_sdk/scoring/presets/purchasing.py` (`copilot_sdk/scoring/presets/purchasing.py:1-80`)
- `apps/purchasing/backend/tests/conftest.py` (`apps/purchasing/backend/tests/conftest.py:1-53`)
- `apps/purchasing/backend/data/purchasing_seed_v2.json` (`apps/purchasing/backend/data/purchasing_seed_v2.json:1-180`)
- `apps/purchasing/backend/data/waste_history.json` (`apps/purchasing/backend/data/waste_history.json:1-22`)
- `apps/purchasing/backend/data/weather_cache.json` (`apps/purchasing/backend/data/weather_cache.json:1-7`)
- `apps/dataops/backend/app/main.py` (`apps/dataops/backend/app/main.py:1-165`)
- `apps/dataops/backend/app/context_router.py` (`apps/dataops/backend/app/context_router.py:1-180`)
- `copilot_sdk/scoring/presets/dataops.py` (`copilot_sdk/scoring/presets/dataops.py:1-80`)
- `apps/dataops/backend/tests/conftest.py` (`apps/dataops/backend/tests/conftest.py:1-68`)
- `apps/dataops/backend/data/celonis_process_data.json` (`apps/dataops/backend/data/celonis_process_data.json:1-88`)
- `apps/dataops/backend/data/fallback/alerts.json` (`apps/dataops/backend/data/fallback/alerts.json:1-25`)
- `apps/dataops/backend/data/fallback/pipelines.json` (`apps/dataops/backend/data/fallback/pipelines.json:1-158`)
- `apps/dataops/backend/data/fallback/blast_radius.json` (`apps/dataops/backend/data/fallback/blast_radius.json:1-36`)
- `apps/dataops/backend/data/transformations.json` (`apps/dataops/backend/data/transformations.json:1-156`)

Read in `s2p-copilot` reference-only:

- `backend/app/graph_contract.py` (`s2p-copilot/backend/app/graph_contract.py:1-89`)
- `backend/app/seed_graph.py` checked and missing.
- `scripts/seed_s2p_graph.py` (`s2p-copilot/scripts/seed_s2p_graph.py:1-360`)

Validated:

- `python -m pytest tests\ -q --timeout=120`
- `python -m pytest apps\trading\backend\tests\ -q --timeout=120`
- `python -m pytest apps\purchasing\backend\tests\ -q --timeout=120`
- `python -m pytest apps\dataops\backend\tests\ -q --timeout=120`
