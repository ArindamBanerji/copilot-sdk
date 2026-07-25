# AGE Unification Gaps v1.1

Status: authoritative implementation contract
Date: 2026-07-25
Scope: JM v2.7 shared AGE graph delivery
Supersedes: `docs/design/age_unification_gaps_v1.md` and individual AGE-unification audit outputs

## 1. Executive summary

JM v2.7 requires one engine and one shared graph: all five copilots must read
and write Decision data in `soc_graph`, with domain partitioning and
cross-copilot traversal. The consolidated audit found 501 application and
infrastructure files, 37 unified access paths, and 47 non-unified paths: 20
P1 blockers and 27 P2 gaps.

The configuration-consolidation foundation is already complete: the TOML,
typed GraphConfig loader, its 16 tests, and wiring into all five
`graph_status.py` modules, `demo.py`, and `phase_config.py` are done. The
remaining shared-infrastructure work is factory/scorer/AGE-client/projection
integration, covered by A1-A4.

Three systemic blockers must be resolved first:

* **A - SOC scorer isolation.** The SOC scorer defaults to
  `InMemoryGraphStore`, so scorer conservation and writes are not AGE-backed.
* **B - S2P dual graph systems.** S2P has both governed GraphStore code and a
  separate ungoverned Neo4j system, preventing one-graph traversal.
* **C - SQLite defaults and substitution.** Factory/scorer defaults and
  dual-write fallback can silently route production work to SQLite.

Seven of the nine JM goals are directly blocked by these findings and the
remaining non-unified paths. The implementation below closes all 20 P1 and 27
P2 items in dependency order. The path denominator is explained in the
counting-methodology note in Section 12.

## 2. JM goals to blockers map

| JM v2.7 goal | JM section | Requirement | Blocking audit finding |
|---|---|---|---|
| One engine, one graph | Section 2 | All Decision data in shared AGE | SOC scorer uses memory; factory defaults SQLite; S2P uses separate Neo4j |
| Cross-graph attention | Sections 2, 4.2 | Transfer edges traversable in one query | SOC memory, S2P separate Neo4j, six unscoped S2P reads |
| $604K cross-graph finding | Section 2 | SAP x Celonis x operations traversal is real | DataOps context and graph-query fixture fallbacks |
| Pattern transfer SOC to S2P to DataOps | Section 2, Phase 6 | Shared graph reads/writes and transfer edges | SOC memory and S2P parallel graph system |
| Conservation across copilots | Section 6, Phase 6 | Shared-graph V for all five | SOC scorer V differs from AGE/router V; SQLite scorer defaults |
| One traversal, one answer | Sections 2, 4.3 | Cross-domain query in one operation | 47 non-unified paths select different stores |
| Domain partitioning | Section 4.3 | Domain predicate on every Decision query | S2P unscoped reads; Trading fallback without domain |
| SQLite local/test only | Section 12 | No production SQLite Decision data | Factory defaults, CLI SQLite, dual-write fallback, four main downgrades |
| Audit chain as graph traversal | Sections 4.1, 4.2 | Decision to Outcome to receipt to checkpoint | Requires every writer to use shared AGE |

The first seven rows are the explicitly blocked JM claims. The last two are
the required safety and topology constraints that make the claims testable.

## 3. Design goals

1. Every Decision read and write uses the GraphStore protocol backed by AGE;
   no direct Neo4j, psycopg, or production SQLite Decision path.
2. Every graph access path resolves DSN and graph through GraphConfig.
3. AGE failures raise; they never substitute SQLite, memory, fixtures, or
   default data.
4. Every Decision query is domain-scoped unless it is an explicitly reviewed
   cross-domain traversal.
5. Every Decision write includes an explicit domain property.
6. All five copilots use the same `soc_graph` and can traverse one graph.
7. Close all 47 non-unified paths, prioritizing the 20 P1s and then the 27
   P2s.

## 4. Systemic blockers

### 4.1 Blocker A - SOC scorer uses memory

**Evidence.** `services/gae_state.py:189` initializes the SOC scorer adapter
without a graph store, and `domains/soc/scorer_adapter.py:19` defaults to
`InMemoryGraphStore(domain="soc")`.

**Prevents.** SOC score/learn writes, scorer-side V, and conservation state do
not observe the AGE tenant. Router queries may report AGE counts while scorer
logic operates on process-local state. Cross-copilot transfer edges cannot be
consumed by the scorer.

**Pre-B1 investigation gate (B0).** Before injecting AGE, record two values
from the current running process: scorer-side V from the in-memory SOC scorer
and census V from the direct AGE query. Reconcile the delta explicitly and
retain both values in the validation artifact. If they differ, SOC has been
conserving against the wrong population; this is a migration finding that
must be resolved before B1, not a post-B1 pass criterion. B1 cannot proceed
until the SOC domain-scoping prerequisite is also confirmed complete.

**Fix.** Inject the GraphConfig-resolved, AGE-backed GraphStore into
`init_learning_state`; remove the production memory default from the SOC
adapter. Preserve an in-memory store only in explicitly isolated tests.

### 4.2 Blocker B - S2P has two graph systems

**Evidence.** `backend/app/db/neo4j.py:14-51` creates an independent Aura
client; `backend/app/db/neo4j.py:147-210` creates Decision and
DecisionContext nodes without domain; `backend/app/domains/s2p/graph.py:52-111`
and `:114-176` write/read a caller-supplied Neo4j driver; and raw route writes
are at `backend/app/routers/s2p.py:1963-1984` and `:2221-2227`.

**Prevents.** S2P decisions are not guaranteed to be in `soc_graph`; raw
reads, writes, outcomes, evolution edges, and counts cannot participate in
one shared traversal.

**Fix.** Route all Decision, Outcome, evolution, and framework operations
through the governed GraphStore. Retire the direct Decision operations in
`db/neo4j.py`; retain only explicitly non-Decision infrastructure that is
approved by the implementation gate. Scope framework queries to `s2p` and
restrict the arbitrary Cypher explorer.

### 4.3 Blocker C - SQLite and silent substitution

**Evidence.** The factory defaults to SQLite at `copilot_sdk/graph/factory.py:26,143`;
missing dual-write DSN returns the SQLite primary at
`copilot_sdk/graph/factory.py:171`; and `CompoundingScorer.from_preset()`
creates SQLite when no store is injected at `copilot_sdk/scoring/scorer.py:208`.

**Prevents.** A configuration mistake can look healthy while writes land in a
local database, memory, or fixture. This violates SQLite-local/test-only and
invalidates parity evidence.

**Fix.** Require an injected store in production scorer construction, make an
expected AGE backend fail closed, make dual-write DSN absence raise, and route
the AGE client through GraphConfig. Development SQLite must be explicit.

## 5. Complete audit inventory

The following inventory includes every P1 and P2 from the consolidated audit.
Unified paths are listed after each copilot for completeness.

### 5.0 SOC domain-scoping prerequisite

The SOC domain-scoping retrofit is **complete**, not deferred: the retrofit
design records the 86-query scope and exact `soc_decision_where()` contract,
and `backend/tests/test_soc_domain_isolation.py` contains the 10 isolation
tests, including foreign-domain exclusion, domain-stamped writes, archive
scope, mutation safety, and snapshot scope. The evidence is the retrofit
document and test file itself; B1 is blocked if either artifact is absent or
fails. This prerequisite must remain ahead of SOC AGE scorer injection so that
connecting the scorer cannot expose foreign-domain rows.

### 5.1 Trading - 6 unified, 9 non-unified

#### P1

* **P1-TRD-1:** `app/main.py:109-117` silently converts AGE to SQLite. This
  causes fixture seeding at `:337-347`.
* **P1-TRD-2:** `app/graph_status.py:153-158` rejects dual-write and the
  active-store constructor returns `None` unless backend is AGE at
  `:314-315`.
* **P1-TRD-3:** `app/cli_sdk.py:76-81` always builds a local SQLite scorer;
  restore copies directly to SQLite at `:564-577`.
* **P1-TRD-4:** `app/services/regime_classifier.py:143-147` retries a
  domain-aware read without a domain.

#### P2

* **P2-TRD-1:** `app/routers/execution_router.py:30-42` and
  `journal.py:224-235` swallow graph errors and return local records.
* **P2-TRD-2:** `app/context_router.py:310-336,339-354,440-477` serves
  fixture market, analytics, and similarity data when providers fail.

#### Unified paths

The unified six groups are `analytics.py:117-127`,
`regime_analytics.py:41-53`, `compute_helpers.py:24-45,245-252`,
`trust_analysis.py:167-170`, `trader_profiles.py:79-86`, and the
promotion/regime/prescore/vix-timing/cohort-status routers. They use the
selected factory or an explicitly domain-qualified store method.

### 5.2 Purchasing - 9 unified, 5 non-unified

#### P1

* **P1-PUR-1:** `app/main.py:128-137` reads raw `GRAPH_BACKEND` outside
  GraphConfig.
* **P1-PUR-2:** `copilot_sdk/graph/factory.py:171-177` silently returns the
  SQLite primary when dual-write DSN is missing.

#### P2

* **P2-PUR-1:** `app/graph_status.py:395-414` reports dual-write as
  SQLite-authoritative.
* **P2-PUR-2:** `app/routers/discovery_router.py:14-28` always returns demo
  decisions.
* **P2-PUR-3:** `app/routers/pos_router.py:50-72`,
  `spend_router.py:18-34,102-128`, and
  `services/commodity_data_provider.py:101-122` use mock/sample fallbacks.
* **P2-PUR-4:** `app/main.py:664-674,:752` wires demo routes with in-memory
  fixture data.
* **P2-PUR-5:** `app/main.py:145-163` resolves `CI_DATA_DIR` directly.

#### Unified paths

The nine unified groups are `evidence.py:166-220`,
`scorecard_router.py:120-128`, `queue.py:331-356`,
`auto_order_router.py:142-168`, `verify_router.py:91,160-170,217-230`,
`match.py:543-598`, `iks.py:45-60`, `cohort_status.py:192-205`, and
`trust_router.py:158-164`.

### 5.3 DataOps - 7 unified, 9 non-unified

#### P1

* **P1-DOPS-1:** `app/context_router.py:388-396,853-903,939-1042` serves
  Decision metadata and seed Decisions from local JSON without domain
  enforcement.
* **P1-DOPS-2:** `app/graph_queries.py:510-531` substitutes fixtures on AGE
  exceptions; `:70-107` uses generic DSN/default graph values when
  DataOps-specific variables are absent.

#### P2

* **P2-DOPS-1:** `app/main.py:91-116` reads raw backend and converts AGE to
  SQLite.
* **P2-DOPS-2:** `app/main.py:515-562` starts the scorer from seed fixtures
  with SQLite dependence.
* **P2-DOPS-3:** `app/main.py:639-646` reports health while graph source is
  fixture.
* **P2-DOPS-4:** `app/context_router.py:1579-1586` writes Decision-shaped
  local JSON without domain validation.
* **P2-DOPS-5:** `app/services/graph_enrichment.py:50-115` calls `run_query`
  without a domain predicate.

#### Unified paths

The seven unified groups are `graph_status.py:80-109`,
`graph_status.py:232-293`, `graph_status.py:306-337`, and the topology reads
at `graph_queries.py:110-175,187-233,325-342,450-508`.

Non-Decision fixtures remain P3 at `seed_graph.py:76-306`,
`celonis_connector.py:1-88`, `sap_connector.py:1-69`,
`connectors/dq_benchmark_provider.py:59-270`, and
`routers/dataops_status.py:134-200`.

### 5.4 S2P - 4 unified, 15 non-unified

#### P1

* **P1-S2P-1:** `backend/app/db/neo4j.py:14-51` uses an independent Aura
  client and `NEO4J_URI`.
* **P1-S2P-2:** `backend/app/db/neo4j.py:147-210` creates Decision and
  DecisionContext without domain.
* **P1-S2P-3:** `backend/app/routers/s2p.py:1963-1984` writes score traces
  through direct Neo4j and ignores exceptions; `:2221-2227` does the same for
  outcome traces.
* **P1-S2P-4:** `backend/app/db/neo4j.py:298-353` performs unscoped sequence
  and category counts and returns zero on failure.
* **P1-S2P-5:** `backend/app/domains/s2p/graph.py:52-111` writes using a
  caller-supplied driver; `:114-176` reads/outcomes without domain.
* **P1-S2P-6:** Unscoped framework paths are
  `backend/app/framework/similar_cases_base.py:61-115`,
  `backend/app/routers/framework_router.py:74-117,148-170,223-260,287-318,519-529`.
* **P1-S2P-7:** `backend/app/routers/framework_router.py:559-637` exposes
  arbitrary global Cypher, even though it is read-only.

#### P2

* **P2-S2P-1:** `backend/app/main.py:89-114` constructs the scorer from raw
  backend configuration.
* **P2-S2P-2:** `backend/app/main.py:133-151` sends enrichment to SQLite,
  not the AGE-authoritative path.
* **P2-S2P-3:** `backend/app/s2p_shadow.py:63-227` maintains a separate AGE
  DSN/factory.
* **P2-S2P-4:** `backend/app/db/neo4j.py:216-276` writes evolution events and
  Decision links without domain.
* **P2-S2P-5:** `backend/app/framework/similar_cases_base.py:92-115` and
  `backend/app/routers/framework_router.py:115-117,166-170` turn graph errors
  into empty/default output.
* **P2-S2P-6:** `backend/app/routers/s2p_situation.py:109-143` and
  `backend/app/services/situation_traversals.py:636-676` mix store and local
  metadata without a universal domain assertion.
* **P2-S2P-7:** `backend/app/seed_graph.py` seeds Decision-shaped JSON data.
* **P2-S2P-8:** `backend/app/services/supplier_profile_accumulator.py:118-138,388-399`
  uses local event/fixture files.

#### Unified paths

The four unified groups are `s2p_graph_status.py:80-109`,
`s2p_graph_status.py:257-365`, and governed S2P writes using the S2P prefix.

### 5.5 SOC - approximately 8 unified, 5 non-unified

#### P1

* **P1-SOC-1:** `services/gae_state.py:189` creates a SOC scorer without a
  graph store; `domains/soc/scorer_adapter.py:19` defaults to memory.
* **P1-SOC-2:** `services/gae_state.py:150` builds the AGE adapter from raw
  `GRAPH_DSN`/`AGE_GRAPH_NAME` and returns `None` when DSN is missing.

#### P2

* **P2-SOC-1:** `services/posterior_store.py:36` uses `POSTERIOR_DSN` with a
  localhost fallback and direct psycopg; `:70` suppresses RL posterior
  delete/insert errors.
* **P2-SOC-2:** `services/rl_engine.py:569` uses in-memory priors when the
  posterior store is unavailable.
* **P2-SOC-3:** `db/neo4j.py:54` retains a legacy Neo4j Aura driver when
  `GRAPH_BACKEND=neo4j`.
* **P2-SOC-4:** `graph_schema.py:218` constructs an AGE factory directly and
  mutates environment for synthetic graph seeding.

#### Unified paths

The unified paths are `db/neo4j.py:30`, `db/neo4j.py:517`, and
`main.py:176`, where the module-level client routes SOC graph access.

### 5.6 Shared infrastructure - 3 unified, 4 non-unified

#### P1

* **P1-INFRA-1:** `copilot_sdk/graph/factory.py:26,143` defaults to SQLite.
* **P1-INFRA-2:** `copilot_sdk/graph/factory.py:171` returns SQLite on missing
  dual-write DSN.
* **P1-INFRA-3:** `copilot_sdk/scoring/scorer.py:208` creates SQLite when no
  store is injected.

#### P2

* **P2-INFRA-1:** `ci_platform/graph/age_client.py:57` resolves DSN from raw
  environment and localhost fallback.
* **P2-INFRA-2:** `ci_platform/graph/age_client.py:1105` uses a raw optional
  DSN/graph singleton factory.
* **P2-INFRA-3:** `copilot_sdk/graph/projection.py:204` constructs a read-only
  AGE client directly from DSN/graph.

#### Unified paths

`age_graph_store.py:34` and `age_sdk_adapter.py:14` are the unified shared
store/adapter layer.

## 6. Implementation plan

Every item below names the source file, change, test, blast radius, and
dependency. The grouped items A1-A4, B0-B7/B'1-B'2, C1-C12, D1-D14, and
E1-E4 close the 47 non-unified paths.

### Phase A - Shared infrastructure

**Already done:** GraphConfig/TOML and the 16-loader tests exist; GraphConfig
is wired into all five copilot graph-status modules, `demo.py`, and
`phase_config.py`. Those completed steps are not reimplemented here.

**Remaining:** A1-A4 below are specifically the factory, scorer, AGE client,
and projection consumers that still bypass GraphConfig.

#### A1. Fail-closed factory backend resolution

* **Files:** `copilot_sdk/graph/factory.py`; factory tests.
* **Change:** Require explicit production backend/expected-backend agreement;
  raise instead of defaulting to SQLite or returning the primary when dual-
  write DSN is absent.
* **Tests:** AGE declaration with missing DSN, wrong backend, and dual-write
  missing DSN all raise before store construction; explicit development SQLite
  still works.
* **Blast radius:** All five copilots and factory callers; startup failures
  become visible instead of silently local.
* **Dependency:** GraphConfig loader contract.

#### A2. Require injected production scorer store

* **Files:** `copilot_sdk/scoring/scorer.py`; scorer tests and callers.
* **Change:** Make `from_preset()` require a GraphStore for production; permit
  memory only through an explicit isolated-test profile.
* **Tests:** no-store production construction raises; injected AGE store is
  used; explicit test profile remains isolated.
* **Blast radius:** Every scorer construction, especially SOC and CLI.
* **Dependency:** A1 and each copilot's GraphConfig wiring.

#### A3. GraphConfig in AGE client

* **Files:** `ci_platform/graph/age_client.py`; AGE client tests.
* **Change:** Replace raw DSN/graph and localhost fallback with typed config.
  Preserve caller-provided disposable graph support for tests.
* **Tests:** missing DSN, redaction, graph selection, and no-CWD fallback.
* **Blast radius:** Shared AGE adapters, projection, and singleton callers.
* **Dependency:** A1 and loader availability in ci-platform.

#### A4. Projection factory compliance

* **Files:** `copilot_sdk/graph/projection.py`; projection tests.
* **Change:** Construct read-only AGE through the common factory/config path.
* **Tests:** projection reads use configured graph; missing configuration raises.
* **Blast radius:** Read-only projection consumers.
* **Dependency:** A3.

### Phase B - SOC scorer

#### B0. Pre-injection V reconciliation gate

* **Files:** SOC validation runner and the existing SOC census/scorer entry
  points.
* **Change:** On the current in-memory path, record scorer-side V; on the
  current AGE path, record census V; reconcile the difference in a signed
  artifact before changing the scorer store.
* **Tests:** A pre-B1 test fails on an unexplained delta and records both
  values; it must not treat equality as an assumption.
* **Blast radius:** SOC conservation pause behavior and flagship demo safety.
* **Dependency:** SOC domain-scoping completion; A1-A3.

#### B1. Inject AGE store into SOC learning state

* **Files:** `gen-ai-roi-demo-v4-v50/backend/services/gae_state.py`.
* **Change:** Resolve SOC GraphConfig/factory and inject the store into
  `init_learning_state` at the existing scorer construction.
* **Tests:** scorer store type is AGE; scorer V equals AGE census V; score/learn
  Decision and Outcome appear in `soc_graph`.
* **Blast radius:** SOC startup, learning, and conservation.
* **Dependency:** B0, SOC domain-scoping completion, and A1-A3.

#### B2. Remove SOC production memory default

* **Files:** `gen-ai-roi-demo-v4-v50/backend/domains/soc/scorer_adapter.py`.
* **Change:** Remove the `InMemoryGraphStore` production default; require an
  injected store.
* **Tests:** missing store fails; explicit isolated test store works.
* **Blast radius:** SOC adapter callers.
* **Dependency:** B1.

#### B3. SOC AGE adapter fail-closed behavior

* **Files:** `gen-ai-roi-demo-v4-v50/backend/services/gae_state.py`.
* **Change:** Missing DSN/configuration raises rather than returning `None`.
* **Tests:** startup negative matrix and no silent memory fallback.
* **Blast radius:** SOC startup failures become explicit.
* **Dependency:** A3, B1.

### Phase B' - SOC non-Decision RL state (P2)

Posterior state is relational RL state, not Decision graph data. These items
are deliberately lower priority than AGE Decision unification. Removing the
fallback changes exploration behavior: production tests must assert that the
failure is loud, not that a degraded recommendation is returned.

#### B'1. SOC posterior configuration

* **Files:** `gen-ai-roi-demo-v4-v50/backend/services/posterior_store.py`.
* **Change:** Resolve `POSTERIOR_DSN` through approved config, remove localhost
  fallback, and surface mutation failures.
* **Tests:** missing DSN and failed delete/insert are visible.
* **Blast radius:** RL posterior persistence.
* **Dependency:** A3.

#### B'2. SOC RL fallback policy

* **Files:** `gen-ai-roi-demo-v4-v50/backend/services/rl_engine.py`.
* **Change:** Do not substitute in-memory priors in production; require an
  explicit offline/test profile.
* **Tests:** production failure is surfaced; test profile is labeled.
* **Blast radius:** RL recommendations.
* **Dependency:** B'1.

### Phase B - SOC scorer (continued)

#### B6. SOC legacy driver retirement

* **Files:** `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py`.
* **Change:** Disable the legacy `GRAPH_BACKEND=neo4j` Aura branch for Decision
  operations; route through configured AGE.
* **Tests:** legacy selection fails closed; AGE path remains domain-scoped.
* **Blast radius:** SOC query layer.
* **Dependency:** A3 and existing domain-scoping contract.

#### B7. SOC synthetic seed isolation

* **Files:** `gen-ai-roi-demo-v4-v50/backend/app/graph_schema.py`.
* **Change:** Route synthetic graph seeding only to disposable graphs and stop
  mutating production environment state.
* **Tests:** `soc_graph` refusal and disposable cleanup.
* **Blast radius:** schema/seed tooling only.
* **Dependency:** A1-A3.

### Phase C - S2P Decision path

#### C1. Retire direct Aura client for Decisions

* **Files:** `s2p-copilot/backend/app/db/neo4j.py`.
* **Change:** Remove direct Decision/Outcome client operations and delegate to
  GraphStore; retain only approved non-Decision infrastructure.
* **Tests:** no direct client construction in Decision paths; shared AGE IDs.
* **Blast radius:** S2P score, learn, counts, and framework features.
* **Dependency:** A1-A4.

#### C2. Stamp domain on S2P Decision writes

* **Files:** `s2p-copilot/backend/app/db/neo4j.py`.
* **Change:** Any retained topology write must include `domain="s2p"`; reject
  missing domain.
* **Tests:** zero NULL-domain writes and exact S2P domain.
* **Blast radius:** S2P migration compatibility.
* **Dependency:** C1.

#### C3. Govern S2P score/outcome routes

* **Files:** `s2p-copilot/backend/app/routers/s2p.py`.
* **Change:** Replace direct trace writes and swallowed exceptions with
  governed GraphStore Decision/Outcome calls.
* **Tests:** score and learn produce shared AGE nodes; failures are returned.
* **Blast radius:** S2P API behavior and error handling.
* **Dependency:** C1-C2.

#### C4. Govern S2P domain graph writes

* **Files:** `s2p-copilot/backend/app/domains/s2p/graph.py`.
* **Change:** Replace caller-supplied driver writes/reads with GraphStore and
  domain-qualified methods.
* **Tests:** Decision, Outcome, and read parity in `s2p`.
* **Blast radius:** S2P domain graph features.
* **Dependency:** C1.

#### C5. Scope S2P count queries

* **Files:** `s2p-copilot/backend/app/db/neo4j.py`.
* **Change:** Domain-scope sequence/category counts and stop returning zero on
  graph exceptions.
* **Tests:** cross-domain data cannot alter S2P counts; failures surface.
* **Blast radius:** S2P metrics and conservation.
* **Dependency:** C1-C2.

#### C6. Scope S2P framework reads

* **Files:** `s2p-copilot/backend/app/framework/similar_cases_base.py` and
  `backend/app/routers/framework_router.py`.
* **Change:** Add `domain="s2p"` to verified, centroid, factor, learning,
  evolution, and auto-approve reads.
* **Tests:** six cross-domain negative tests and domain ID-set checks.
* **Blast radius:** framework tabs and similar-case behavior.
* **Dependency:** C1-C5.

#### C7. Restrict arbitrary Cypher explorer

* **Files:** `s2p-copilot/backend/app/routers/framework_router.py`.
* **Change:** Remove arbitrary global Cypher or enforce a closed query registry
  that injects S2P domain predicates.
* **Tests:** global labels/graphs rejected; approved queries remain readable.
* **Blast radius:** explorer endpoint.
* **Dependency:** C6.

#### C8. Unify S2P main and enrichment

* **Files:** `s2p-copilot/backend/app/main.py`.
* **Change:** Resolve scorer through GraphConfig/factory. Enrichment is
  non-Decision data; under JM Section 12, keeping it on the SQLite primary is
  architecturally correct. The implementation must preserve this conscious
  split while ensuring enrichment never substitutes for AGE Decision data.
* **Tests:** startup store type, DSN/graph, and enrichment failure behavior.
* **Blast radius:** startup and enrichment consumers.
* **Dependency:** A1-A4, C1.

#### C9. Unify S2P shadow state

* **Files:** `s2p-copilot/backend/app/s2p_shadow.py`.
* **Change:** Remove separate AGE DSN/factory and derive shadow configuration
  from the shared typed config.
* **Tests:** shadow opt-in and graph name use one config.
* **Blast radius:** shadow validation only.
* **Dependency:** C8.

#### C10. Remove S2P substitution fallbacks

* **Files:** `s2p-copilot/backend/app/framework/similar_cases_base.py`,
  `backend/app/routers/framework_router.py`,
  `backend/app/routers/s2p_situation.py`,
  `backend/app/services/situation_traversals.py`.
* **Change:** Surface AGE errors instead of empty/default results and assert
  domain on mixed store/local traversals.
* **Tests:** forced AGE failure returns an explicit error; no hidden empty pass.
* **Blast radius:** framework and situation endpoints.
* **Dependency:** C6-C9.

#### C11. Remove S2P Decision-shaped seed substitution

* **Files:** `s2p-copilot/backend/app/seed_graph.py`.
* **Change:** Restrict seed data to disposable test graphs and stamp domain;
  prohibit production fixture substitution.
* **Tests:** production graph refusal and disposable seed topology.
* **Blast radius:** seed tooling.
* **Dependency:** C1-C2.

#### C12. Isolate supplier profile local files

* **Files:** `s2p-copilot/backend/app/services/supplier_profile_accumulator.py`.
* **Change:** Keep local events separate from Decision graph data and reject
  use as a graph substitute.
* **Tests:** no local event appears as a Decision.
* **Blast radius:** supplier profile UI.
* **Dependency:** C1.

### Phase D - Trading, Purchasing, and DataOps

This phase is split deliberately. D-DECISION closes shared-graph Decision
paths and is part of JM v2.7. D-NON-DECISION governs external operational
data and demo fixtures; it is lower priority and does not substitute for
Decision unification.

#### D-DECISION

#### D1. Trading main backend resolution

* **Files:** `copilot-sdk/apps/trading/backend/app/main.py`.
* **Change:** Remove AGE-to-SQLite conversion and resolve the selected store
  through GraphConfig/factory.
* **Tests:** AGE startup is AGE; missing DSN fails; no fixture seed on failure.
* **Blast radius:** Trading startup and every router.
* **Dependency:** A1.

#### D2. Trading active status/dual-write support

* **Files:** `copilot-sdk/apps/trading/backend/app/graph_status.py`.
* **Change:** Accept dual-write, construct it through the approved factory, and
  report the actual active backend.
* **Tests:** dual-write store/status and derived authorization.
* **Blast radius:** Trading cutover status and writes.
* **Dependency:** D1.

#### D3. Trading CLI factory compliance

* **Files:** `copilot-sdk/apps/trading/backend/app/cli_sdk.py`.
* **Change:** Load GraphConfig and use the selected GraphStore for score,
  learn, history, export, and import; remove direct SQLite restore for
  production mode.
* **Tests:** CLI uses AGE and refuses unconfigured production.
* **Blast radius:** CLI users and backups.
* **Dependency:** A1-A2, D1.

#### D4. Trading domain-safe fallback

* **Files:** `copilot-sdk/apps/trading/backend/app/services/regime_classifier.py`.
* **Change:** Remove the no-argument retry; protocol mismatch is an error.
* **Tests:** missing domain signature fails rather than reading globally.
* **Blast radius:** regime analytics.
* **Dependency:** A2.

#### D5. Trading graph error policy

* **Files:** `copilot-sdk/apps/trading/backend/app/routers/execution_router.py`,
  `journal.py`.
* **Change:** Do not silently return local records when AGE fails; return a
  graph-unavailable response or explicit error.
* **Tests:** forced graph failure never produces an apparently authoritative
  local result.
* **Blast radius:** execution and journal endpoints.
* **Dependency:** D1.

#### D-NON-DECISION

D6, D9, and D10 are non-Decision provider/demo policy items. They must not be
used to claim Decision-path closure. They remain required for product
integrity but are sequenced after the Decision gates.

#### D6. Trading non-Decision provider fallback policy

* **Files:** `copilot-sdk/apps/trading/backend/app/context_router.py`.
* **Change:** Keep external-provider fixtures only behind explicit demo/test
  mode and label them; never use them for Decision metrics.
* **Tests:** production AGE failure is not presented as authoritative data.
* **Blast radius:** market/context tabs.
* **Dependency:** D1.

#### D-DECISION

#### D7. Purchasing main GraphConfig resolution

* **Files:** `copilot-sdk/apps/purchasing/backend/app/main.py`.
* **Change:** Replace raw `GRAPH_BACKEND` and direct `CI_DATA_DIR` resolution
  with the typed config while retaining explicit test path injection.
* **Tests:** config collision, AGE startup, and path resolution.
* **Blast radius:** Purchasing startup and seed path.
* **Dependency:** A1 and loader.

#### D8. Purchasing dual-write status and active selection

* **Files:** `copilot-sdk/apps/purchasing/backend/app/graph_status.py` and
  `app/main.py`.
* **Change:** Represent dual-write as dual-write, not SQLite-authoritative;
  ensure selected and seed stores are the intended factory result.
* **Tests:** store/status consistency and outbox behavior.
* **Blast radius:** Purchasing cutover reporting.
* **Dependency:** D7, A1.

#### D-NON-DECISION

#### D9. Purchasing demo substitution policy

* **Files:** `app/routers/discovery_router.py`, `app/routers/pos_router.py`,
  `app/routers/spend_router.py`, `app/services/commodity_data_provider.py`.
* **Change:** Put demo/sample fallbacks behind explicit demo mode and preserve
  provenance; production provider failure must not masquerade as live data.
* **Tests:** production failure response and explicit demo response.
* **Blast radius:** non-Decision purchasing dashboards.
* **Dependency:** D7.

#### D10. Purchasing demo route isolation

* **Files:** `app/main.py:664-674,:752` and referenced demo services.
* **Change:** Do not register demo in-memory routes in production mode.
* **Tests:** route absent or explicitly labeled in production; demo mode works.
* **Blast radius:** demo-only endpoints.
* **Dependency:** D7.

#### D-DECISION

#### D11. DataOps backend and path configuration

* **Files:** `copilot-sdk/apps/dataops/backend/app/main.py`.
* **Change:** Replace raw backend and AGE-to-SQLite conversion with GraphConfig
  and fail-closed factory selection.
* **Tests:** AGE positive/negative startup and no fixture seed on failure.
* **Blast radius:** DataOps startup.
* **Dependency:** A1 and loader.

#### D12. DataOps context Decision reads

* **Files:** `copilot-sdk/apps/dataops/backend/app/context_router.py`.
* **Change:** Replace local JSON Decision metadata/seed responses with
  domain-scoped GraphStore reads; retain JSON only as explicit demo data.
* **Tests:** AGE Decision IDs/domain and no JSON substitution.
* **Blast radius:** context endpoints.
* **Dependency:** D11.

#### D13. DataOps graph-query failure policy

* **Files:** `copilot-sdk/apps/dataops/backend/app/graph_queries.py`.
* **Change:** Remove fixture fallback on AGE exceptions and resolve DSN/graph
  only from GraphConfig.
  The topology client queries `PipelineSystem` and `DataQualityAlert`, not
  Decision nodes; it is intentionally separate from the Decision-focused
  GraphStore protocol. It still must use GraphConfig for DSN/graph resolution
  and must not fall back to fixtures when AGE is authoritative.
* **Tests:** missing DataOps-specific variables do not select generic defaults;
  AGE exceptions surface.
* **Blast radius:** topology queries.
* **Dependency:** D11.

#### D14. DataOps enrichment scope and health

* **Files:** `copilot-sdk/apps/dataops/backend/app/services/graph_enrichment.py`,
  `app/context_router.py`, and `app/main.py`.
* **Change:** Add DataOps domain predicates to enrichment, stamp writes, and
  make health fail/flag when graph source is fixture.
* **Tests:** domain isolation, no fixture health, and enrichment failure.
* **Blast radius:** graph enrichment and health endpoints.
* **Dependency:** D12-D13.

### Phase E - validation and release gates

#### E1. Comprehensive runner

* **Files:** `copilot-sdk/scripts/validate_age_migration.py` and the existing
  AGE-gated test entry points.
* **Change:** Implement comprehensive validation from the validation plan:
  health, census, parity, five-domain cycles, contention, configuration
  negatives, destructive safety, indexes, rollback, and output equivalence.
  It must also run all 73 existing AGE-gated SDK tests. The seven explicitly
  feature-gated tests are reported separately; unexpected skips are failures.
* **Tests:** runner unit tests, all 73 AGE-gated tests, and disposable AGE
  integration.
* **Blast radius:** release automation only.
* **Dependency:** A-D complete.

#### E2. Cross-copilot traversal proof

* **Files:** validation tests/scripts and existing transfer-edge suites.
* **Change:** Assert one query can read all five domains' Decision data with
  domain-scoped counts and no foreign-domain leakage. TransferPattern edges
  do not yet exist; true edge traversal is a Phase 6 dependency and is not
  claimed by this plan.
* **Tests:** cross-domain read/count and domain-ID-set assertions. Transfer
  edge traversal is a separate Phase 6 gate.
* **Blast radius:** JM Phase 6 evidence.
* **Dependency:** all Decision paths unified.

#### E3. Production no-substitution gate

* **Files:** CI configuration, validation runner, and
  `docs/design/age_unification_forbidden_patterns_allowlist.toml`.
* **Change:** Fail the build on the following forbidden patterns outside the
  approved adapter/config/test allowlists:
  `GraphDatabase.driver(`, `psycopg.connect(`, `SQLiteGraphStore(` outside
  tests, `InMemoryGraphStore(` outside tests, `os.environ["GRAPH_*"]` or
  `os.environ.get("GRAPH_*")` outside GraphConfig, and
  `MATCH (d:Decision)` without a domain predicate outside the reviewed
  cross-domain allowlist. The repo-local allowlist is
  `docs/design/age_unification_forbidden_patterns_allowlist.toml`.
* **Tests:** static scan against the enumerated patterns plus the negative
  runtime matrix.
* **Blast radius:** all repositories.
* **Dependency:** E1.

#### E4. Migration and rollback evidence

* **Files:** migration/validation artifacts and operator runbooks.
* **Change:** Capture source hashes/counts, active/archive parity, V deltas,
  score equivalence, and forced AGE-to-SQLite flip-back evidence.
* **Tests:** disposable migration and forced-outage drill.
* **Blast radius:** release and incident response.
* **Dependency:** E1-E3.

The implementation inventory contains 47 non-unified paths: four Trading P1,
two Trading P2, two Purchasing P1, five Purchasing P2, two DataOps P1, five
DataOps P2, seven S2P P1, eight S2P P2, two SOC P1, four SOC P2, and three
shared-infrastructure P1 plus three shared-infrastructure P2. Some shared
fixes intentionally close multiple copilot paths.

## 7. Risk assessment

* **Fail-closed factory/scorer:** Existing deployments that relied on silent
  SQLite or memory will fail at startup. This is intentional; operators must
  provide DSN, graph, and explicit development fallback.
* **SOC injection:** SOC learning behavior changes from process-local state to
  persisted AGE state. Validate V and conservation before enabling writes.
* **S2P retirement:** Direct Neo4j endpoints may change response timing and
  error behavior. Preserve response schemas while replacing the backing path.
* **Fixture removal:** Demo dashboards may become empty when external sources
  are unavailable. Keep explicit demo mode and provenance rather than silently
  presenting sample data.
* **Domain predicates:** Counts may decrease when foreign rows are excluded.
  Every decrease must be reconciled against a named foreign-row count and
  preserved ID evidence. An unreconciled decrease is NO-GO; it cannot be
  dismissed as filtering.
* **CLI changes:** Backup/restore commands that assumed SQLite need an
  explicit local/test mode or a graph-aware export path.

## 8. Test requirements

### Phase A

* Loader tests: all domains, source provenance, redaction, expected backend,
  missing DSN/graph, and collision warnings.
* Factory tests: no implicit SQLite, no dual-write primary fallback, and
  explicit development profile.
* Scorer tests: injected store required in production.
* AGE client/projection tests: typed DSN/graph and disposable test graph.

### Phase B

* SOC startup store-type assertion.
* Score/learn writes visible in AGE with `domain="soc"`.
* V equality between scorer and census.
* Posterior failure and no in-memory production fallback.

### Phase C

* S2P score/outcome/evolution topology in `soc_graph`.
* No direct Neo4j Decision writes.
* Six framework domain-isolation tests.
* Arbitrary explorer rejection.
* No empty/default success on AGE exceptions.

### Phase D

* Trading dual-write and CLI AGE tests.
* Trading no-domain fallback regression test.
* Purchasing backend/status consistency tests.
* DataOps JSON-substitution, fixture-health, and enrichment-domain tests.

### Phase E

* Comprehensive runner refusal/redaction tests.
* Five-domain concurrent score/learn and contention tests.
* Active/archive parity and orphan/duplicate checks.
* Fixed SQLite/AGE score output corpus.
* Forced outage/read rollback drill.

All tests must use disposable AGE graphs for mutating checks. No mutating test
may target `soc_graph`.

## 9. Dependency map

```text
GraphConfig + fail-closed factory (A1-A4)
          |
          +--> SOC domain-scoping retrofit (complete prerequisite)
                         |
                         +--> B0 V investigation
                                      |
                                      +--> SOC AGE scorer (B1-B7)
          |
          +--> S2P governed graph (C1-C12)
          |
          +--> SDK copilot wiring (D1-D14)
                         |
                         +--> comprehensive runner (E1-E4)
```

The ordering is mandatory:

1. Configuration and factory guarantees precede any copilot cutover.
2. The completed SOC domain-scoping retrofit (86 queries, exact helper, and
   10 isolation tests) is verified before B0/B1.
3. B0 V reconciliation precedes SOC scorer injection; S2P retirement
   precedes cross-domain traversal.
4. Trading/Purchasing/DataOps fixes can proceed in parallel after Phase A,
   but validation must wait for all three.
5. Comprehensive validation and rollback evidence precede JM v2.7 release.

## 10. Success criteria

JM v2.7 is achieved only when all of the following are evidenced:

1. Every five-copilot Decision and Outcome read/write reaches the same AGE
   graph through GraphStore; no direct Neo4j/psycopg/production SQLite path
   remains.
2. Every service resolves backend, DSN, graph, domain, and authorization from
   GraphConfig; no raw env or localhost fallback controls production.
3. AGE declaration failures stop startup; no SQLite, memory, fixture, or empty
   substitution is reported as success.
4. All Decision reads are domain-scoped and all writes stamp domain.
5. V_soc satisfies the canonical Section 11 gate: it is at least the live
   census baseline, every increment is event-traceable, and scorer/store/census
   values reconcile after B1.
6. One query reads all five domains' Decision data with exact domain-scoped
   counts and no foreign rows. TransferPattern edge traversal is a separate
   Phase 6 dependency because those edges do not yet exist.
 7. The shared graph substrate required for the $604K cross-graph finding is
    in place: all five domains' Decisions are in soc_graph with domain
    partitioning and governed writes. The finding's entity edges (OD-1) and
    cross-domain traversal queries are Phase 6 deliverables and are not claimed by this plan.
8. Active/archive IDs, Outcomes, EvidenceReceipts, CentroidCheckpoints,
   entities, and evolution edges have exact parity and zero orphans.
9. Comprehensive validation passes, including contention, performance,
   output equivalence, browser isolation, and rollback evidence.

Any unexplained fallback, unscoped read, domainless write, store/census V
disagreement, or missing evidence is a NO-GO for JM v2.7.

## 11. Canonical V_soc reconciliation

This is the single canonical V_soc note for this document and the AGE
validation plan. Do not re-derive a permanent constant elsewhere.

The parent PF-1 snapshot reported:

```text
V_soc = 4,899 = 4,862 NULL-domain verified + 37 already-tagged verified
```

The live July 25, 2026 census reported zero NULL-domain rows and 4,862
verified rows with `domain='soc'`. The two values describe different graph
snapshots; the graph evolved between them. Therefore the authoritative value
for a validation run is the live census value captured at run start, not a
hardcoded 4,899 or 4,862.

The release gate is:

```text
V_soc(t) >= census_baseline
every increment is traceable to a recorded SOC verification event
scorer-side V == census V after B1, or the reconciled delta is documented
```

B0 records scorer-side and census V before AGE injection. B1 then proves the
post-injection scorer reads the same population. Any unexplained delta or
count decrease is NO-GO. The validation plan's Section 1.1 is the companion
reference and must cite this canonical note rather than introduce another
number.

## 12. Counting methodology

The audit denominator is a count of grouped graph-access paths, not source
files and not individual Cypher tokens. A path is one independently callable
reader, writer, fallback, configuration branch, or test-facing graph access
group. The audit found 501 files, 37 unified path groups, and 47 non-unified
path groups. Thus `37 + 47 = 84` access-path groups; the remaining files were
audited but contained no graph access hit. This definition is binding for the
next audit and prevents denominator drift.

## 13. Review dispositions

* R1 is addressed by B0: scorer-side V and census V are measured before B1.
* R2 is addressed by Section 11: live census is authoritative and every
  increment is event-traceable.
* R3 is addressed by Section 5.0 and the dependency map: SOC scoping is
  complete and precedes B0/B1.
* F1 is addressed in Phase A's completed/remaining split.
* F2 is addressed by Phase B': posterior/RL state is P2 and loud failure is
  required.
* F3 is addressed by C8: enrichment is non-Decision SQLite data by design.
* F4 is addressed by the D-DECISION/D-NON-DECISION split.
* F5 is addressed by E3's explicit forbidden-pattern list and repo-local
  allowlist.
* F6 is addressed by E1's 73-test requirement and skip classification.
* F7 is addressed by D13's PipelineSystem/DataQualityAlert distinction.
* F8 is addressed by E2's five-domain read proof; TransferPattern traversal
  remains a Phase 6 dependency.
* F9 is addressed by the Section 7 foreign-row reconciliation gate.
* F10 is addressed by Section 12's grouped-path definition.

## 14. Execution Synopsis

Prerequisites (already complete):
- GraphConfig + TOML + 16 tests [done]
- All 5 graph_status.py wired [done]
- demo.py + phase_config.py wired [done]
- SOC domain-scoping (86 queries, 10 isolation tests) [done]

Phase A - Shared infrastructure:
A1. factory.py fail-closed (no SQLite default) -> all copilots
A2. scorer.py from_preset() requires injected store -> SOC, CLI
A3. AGE client uses GraphConfig (no localhost fallback) -> adapters
A4. projection.py uses factory -> read-only consumers
Gate: all 5 domains load, no implicit SQLite, tests pass

Phase B - SOC scorer:
B0. Measure scorer V vs census V BEFORE injection -> reconcile delta
B1. Inject AGE store into gae_state.py -> scorer writes to soc_graph
B2. Remove InMemoryGraphStore default from scorer_adapter.py
B3. gae_state.py fail-closed (no None on missing DSN)
B6. Retire legacy GRAPH_BACKEND=neo4j branch
B7. Seed tooling uses disposable graphs only
Gate: scorer V == census V, SOC 2,174 tests pass

Phase B' - SOC RL state (P2, non-Decision):
B'1. PosteriorStore uses GraphConfig, no localhost fallback
B'2. RL engine fails loud, no in-memory priors in production

Phase C - S2P Decision path (15 items -> 12 grouped):
C1. Retire direct Aura client for Decision operations
C2. Stamp domain="s2p" on all retained writes
C3. Govern score/outcome routes through GraphStore
C4. Govern domain graph writes (domains/s2p/graph.py)
C5. Scope count queries to domain="s2p"
C6. Scope 6 framework reads to domain="s2p"
C7. Restrict/retire arbitrary Cypher explorer
C8. Main uses GraphConfig; enrichment stays SQLite (by design)
C9. Shadow uses shared config (not separate DSN)
C10. Remove empty/default substitution on AGE errors
C11. Seed uses disposable graphs with domain stamp
C12. Supplier profile isolated from Decision data
Gate: zero direct Neo4j Decision writes, S2P 1,627 tests pass

Phase D - SDK copilots:
D-DECISION:
D1. Trading main: remove AGE->SQLite downgrade
D2. Trading graph_status: accept dual_write
D3. Trading CLI: use GraphConfig/factory
D4. Trading regime_classifier: remove unscoped retry
D5. Trading execution/journal: fail-closed on graph error
D7. Purchasing main: use GraphConfig
D8. Purchasing status: report dual_write correctly
D11. DataOps main: use GraphConfig, no AGE->SQLite
D12. DataOps context_router: read from AGE, not JSON
D13. DataOps graph_queries: no fixture fallback, use GraphConfig for DSN
D14. DataOps enrichment: domain predicates + health accuracy

D-NON-DECISION (lower priority):
D6. Trading context fixture policy
D9. Purchasing demo substitution policy
D10. Purchasing demo route isolation
Gate: all SDK copilot tests pass, no silent SQLite

Phase E - Validation + release:
E1. Comprehensive runner (all 13 areas + 73 AGE-gated tests)
E2. 5-domain read proof (not edge traversal - that's Phase 6)
E3. Forbidden-pattern static scan + allowlist
E4. Migration/rollback evidence capture
Gate: comprehensive validation PASS, 0 failures, 0 unexpected skips

-> Phase 6 (separate, after this plan): TransferPattern edges,
   cross-domain traversal queries, $604K proof, global conservation
