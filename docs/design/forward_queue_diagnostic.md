# Forward Queue Diagnostic

**Model:** gpt-5.3  
**Mode:** read-only repository diagnostic  
**Scope:** SDK, SOC, CI Platform, S2P, and DataOps trees  
**Date:** 2026-08-08

Statuses mean:

- **DONE** — implementation and the requested surface are present.
- **PARTIAL** — a substantial implementation exists, but the stated item still has a material gap.
- **NOT STARTED** — no implementation evidence was found.

No source, test, graph, or database files were modified by the diagnostic.

## 1. C9B Formal Proof

**Status: PARTIAL**

Evidence:

- The live smoke checker still returns `READY_FOR_C9B_PROOF` when prerequisites pass, rather than declaring the formal proof complete: `gen-ai-roi-demo-v4-v50/scripts/soc_c9b_live_age_smoke.py:228-231`.
- The execution plan explicitly says conservation is proven but the DK sub-proof remains the only C9B gap: `copilot-sdk/docs/dk_runtime_execution_plan_v6_8.md:727-733`.
- The plan still lists the formal proof on fresh `soc_graph_c9b` as `NEXT`: `copilot-sdk/docs/dk_runtime_execution_plan_v6_8.md:1497-1505`.
- The proof requirements include the three SOC L5 cells and a fresh graph, not merely a diagnostic run: `copilot-sdk/docs/dk_runtime_execution_plan_v6_8.md:2751-2759`.
- The repository has F8/diagnostic artifacts and scripts, but those are prerequisites/diagnostics rather than evidence that the final fresh-graph proof was executed: `copilot-sdk/docs/dk_runtime_execution_plan_v6_8.md:2799-2803`.

**Action needed:** Execute the formal C9B proof on a clean `soc_graph_c9b`, validate `L5Centroid`, `L5DKWeight`, and `L5ConservationState`, then persist the proof JSON/Markdown report and update the execution status. Do not treat `.mypy_cache` artifacts as proof evidence.

## 2. Campaign Identity Phase 2

**Status: PARTIAL**

Evidence of shipped work:

- The original `make_campaign_id()` still hashes the sorted alert-ID set with UUID5: `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:486-488`.
- A newer tuple-stable identity function exists and uses a null-delimited SHA-256 identity over rule, entity, category, and time bucket: `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:525-542`.
- `derived_entity_key()` is implemented with type prefixes (`entity:`, `user:`, `asset:`, `loc:`): `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:495-506`.
- The seed path consumes the new identity key and preserves the derived entity key/category/bucket: `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:565-585`.
- Determinism and member-independent identity are covered by tests: `gen-ai-roi-demo-v4-v50/backend/tests/test_campaign_schema.py:34-50`.
- `check_alert()` has a non-throwing wrapper and a cache → pending seed → materialized campaign → background/inline path: `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/campaigns.py:1861-1914`.

**Why not DONE:** The named `make_campaign_id()` remains the old alert-set identity while the new Phase-1 identity is named `make_campaign_identity_key()`. The implementation has effectively moved to the new function, but the old/new API distinction is unresolved for the Phase-2 acceptance wording.

**Action needed:** Decide whether `make_campaign_id()` is legacy-only or must delegate to the tuple identity. Remove ambiguity from callers/documentation and add a migration/compatibility test proving every production campaign path uses the intended stable identity.

## 3. Hot-Path Architecture

**Status: PARTIAL**

The AGE pool itself is shipped:

- Pooling is opt-in, with `AGE_POOL_MIN_SIZE` and `AGE_POOL_MAX_SIZE` defaults: `ci-platform/ci_platform/graph/age_client.py:117-140`.
- The pool is created with the configured maximum size and autocommit connections: `ci-platform/ci_platform/graph/age_client.py:179-200`.
- Query execution selects pooled, warm-fallback, or fresh behavior: `ci-platform/ci_platform/graph/age_client.py:420-467`.

Broader architecture is also present:

- `DecisionPipeline` defines a shared four-phase hot-path skeleton with separate subject/context reads, decision/gates, persistence, and phase-4 tasks: `ci-platform/ci_platform/copilot_core/pipeline.py:96-146`.
- The pipeline records phase timings and submits phase-4 work after the core phases: `ci-platform/ci_platform/copilot_core/pipeline.py:158-205`.
- `EntityCache` is a bounded read-through LRU cache for stable entity context: `ci-platform/ci_platform/copilot_core/cache.py:93-116`.
- The cache explicitly excludes mutable counters, decisions, outcomes, and conservation/DK/L5 authority: `ci-platform/ci_platform/copilot_core/cache.py:1-8`.
- The SOC route has the entity cache enabled: `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:95-103`.

**Why not DONE:** The shared cache adapter is explicitly disabled by default unless a product route enables it: `ci-platform/ci_platform/copilot_core/context_cache.py:33-64`. The shared pipeline is currently evidenced as a SOC shadow/diagnostic comparison rather than a demonstrated production execution path for all five copilots: `gen-ai-roi-demo-v4-v50/backend/app/services/soc_domain_profile.py:420-435`. No repository evidence establishes complete five-copilot adoption of the read/write separation.

**Action needed:** Wire and verify the shared hot-path contract across all five production routes, document per-copilot cache enablement/TTL, and prove that authoritative writes remain outside the stable-context cache.

## 4. SC-14/15/16 Frontend

The demo-scenarios document is stale: it still labels the three frontend items “Pending Codex”: `copilot-sdk/docs/design/demo_scenarios_and_usecases_v2_4.md:901-903`. Current source evidence shows the components and backend surfaces exist.

| Item | Backend | Frontend | Status |
|---|---|---|---|
| SC-14 Decision Explorer | EXISTS — SDK self-decisions route: `copilot-sdk/copilot_sdk/backend/self_computation_router.py:312-336`; DataOps context route: `copilot-sdk/apps/dataops/backend/app/context_router.py:935-936` | EXISTS — DataOps panel: `copilot-sdk/apps/dataops/frontend/src/components/DecisionExplorerPanel.tsx:3-6`; mounted on Insight: `copilot-sdk/apps/dataops/frontend/src/screens/InsightScreen.tsx:8-11` | **DONE** |
| SC-15 Rule Lifecycle | EXISTS — DataOps `/rule-lifecycle`: `copilot-sdk/apps/dataops/backend/app/ae_router.py:478-481` | EXISTS — DataOps lifecycle panel: `copilot-sdk/apps/dataops/frontend/src/components/RuleLifecyclePanel.tsx:2-8`; mounted on Evidence: `copilot-sdk/apps/dataops/frontend/src/screens/EvidenceScreen.tsx:5-14` | **DONE** |
| SC-16 Audit Trail | EXISTS — SDK self audit route: `copilot-sdk/copilot_sdk/backend/self_computation_router.py:336-337`; DataOps alert audit route: `copilot-sdk/apps/dataops/backend/app/context_router.py:1425-1426` | EXISTS — DataOps audit viewer: `copilot-sdk/apps/dataops/frontend/src/components/AuditTrailViewer.tsx:2-6`; mounted on Evidence: `copilot-sdk/apps/dataops/frontend/src/screens/EvidenceScreen.tsx:5-14` | **DONE** |

Additional evidence shows S2P and Trading also have corresponding frontend surfaces, for example S2P’s Evidence screen mounts both panels: `copilot-sdk/apps/s2p/frontend/src/screens/EvidenceScreen.tsx:3-13`.

**Action needed:** Update the demo-scenarios status table and perform a live UI/API smoke check if the acceptance requires a specific copilot rather than repository-wide availability.

## 5. D-CEL Frontend

**Status: PARTIAL**

| Surface | Status | Evidence |
|---|---|---|
| SAP connector | EXISTS, but default is sample/cache-backed | `copilot-sdk/apps/dataops/backend/app/sap_connector.py:17-35` explicitly sets `provenance_tier = "sample"` and says it is not live SAP. Live mode is enabled only when credentials/configuration are supplied: `copilot-sdk/apps/dataops/backend/app/sap_connector.py:28-35`. |
| Celonis connector | EXISTS, but default is sample/cache-backed | `copilot-sdk/apps/dataops/backend/app/celonis_connector.py:17-37` explicitly sets `provenance_tier = "sample"` and says it is not live Celonis. |
| `/enterprise-health` | EXISTS | The combined endpoint calls both connector health checks: `copilot-sdk/apps/dataops/backend/app/context_router.py:725-728`. A separate router also exposes the endpoint: `copilot-sdk/apps/dataops/backend/app/enterprise_router.py:46-55`. |
| Frontend badges/cards | EXISTS | Dashboard mounts Enterprise Health, SAP, Celonis, and process timeline components: `copilot-sdk/apps/dataops/frontend/src/screens/DashboardScreen.tsx:33-39,184-209`. The badges fetch enterprise health and distinguish Fixture/Live/Offline: `copilot-sdk/apps/dataops/frontend/src/components/SAPDataBadge.tsx:20-48`; `copilot-sdk/apps/dataops/frontend/src/components/CelonisBadge.tsx:21-50`. |

**Why not DONE:** The UI and connector seams are shipped, but the default evidence path is explicitly sample/cache-backed rather than a verified live SAP/Celonis connection. This is a frontend/integration completion gap, not a missing component gap.

**Action needed:** Configure and verify live credentials/endpoints, prove the health payload reports live sources, and retain clear sample labeling when fallback fixtures are used.

## 6. Bonus Verifications

### F-26 sample refusal gate: EXISTS

- The SDK scorer rejects `Provenanced(source="sample")` factor values before scoring: `copilot-sdk/copilot_sdk/scoring/scorer.py:199-205`; implementation: `copilot-sdk/copilot_sdk/scoring/scorer.py:2261-2264`.
- DataOps has an explicit metric gate that raises on sample provenance: `copilot-sdk/apps/dataops/backend/app/data_helpers.py:4-13`.
- The gate is covered by a rejection test: `copilot-sdk/apps/dataops/backend/tests/test_dq_benchmark.py:199-207`.
- Demo preseed validation also refuses sample headline metrics under F-26: `copilot-sdk/copilot_sdk/demo/preseed.py:199-208`.

### DI-PROOF what-if surface: EXISTS

- DataOps exposes GET status, POST perturb, and POST revert endpoints: `copilot-sdk/apps/dataops/backend/app/routers/perturbation_router.py:22-50`.
- The frontend calls DI perturbation and revert endpoints: `copilot-sdk/apps/dataops/frontend/src/api.ts:295-309`.
- A separate conservation what-if API is also wired: `copilot-sdk/apps/dataops/frontend/src/api.ts:382-385`.

### Rejection Moment data: AVAILABLE

- Unified evolution telemetry includes `recent_events`: `copilot-sdk/copilot_sdk/backend/evolution_router.py:186-203`.
- Trading exposes aggregate rejection counts, reason breakdown, rejected variants, and learned provenance: `copilot-sdk/apps/trading/backend/app/routers/evolution_router.py:81-115`.
- SOC exposes a graph-backed rejection summary and recent events: `gen-ai-roi-demo-v4-v50/backend/app/routers/evolution.py:741-787`.

## Consolidated Status

| Item | Status | Immediate next action |
|---|---|---|
| C9B formal proof | **PARTIAL** | Execute and archive the fresh `soc_graph_c9b` three-cell proof. |
| Campaign identity Phase 2 | **PARTIAL** | Resolve legacy `make_campaign_id()` versus tuple-stable identity naming/callers. |
| Hot-path architecture | **PARTIAL** | Complete five-copilot production adoption and verify cache/read-write boundaries. |
| SC-14/15/16 | **DONE** | Refresh stale “Pending Codex” documentation and run live smoke checks. |
| D-CEL frontend/integration | **PARTIAL** | Verify live SAP/Celonis configuration; keep fallback provenance visible. |
| F-26 sample refusal | **EXISTS** | Continue expanding coverage to every metric surface. |
| DI-PROOF what-if | **EXISTS** | Confirm the intended demo route is included in the presenter flow. |
| Rejection Moment data | **AVAILABLE** | Bind the existing telemetry endpoints to the planned demo panel. |
