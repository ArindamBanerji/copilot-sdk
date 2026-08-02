# JM v2.7 Post-Fix Review S2

Review type: adversarial, review-only. Evidence below is from the inspected source and tests; no live AGE claim is made unless a cited test or script establishes it. The requested `correctness_unification_architecture_v1.md` was not present; the available substitute, `docs/design/correctness_architecture.md`, was read and is identified in the reading log.

## §1 EXECUTIVE SUMMARY

| Area | Result |
|---|---|
| Non-negotiable properties | 2 conformant / 4 partial / 0 fully closed gaps out of 6 |
| Conservation | PARTIAL |
| AGE failure policy | 2 conformant / 2 partial / 3 gap out of 7 operations |
| SQLite role | PARTIAL (runtime source is guarded, but defaults/documentation remain permissive or stale) |
| Standing rules | 1 enforced / 3 partial / 1 gap out of 5 |

Overall status: **PARTIAL**. The fail-closed AGE checks and domain predicates are materially improved, but the audit does not support an unconditional JM v2.7 architecture claim: SOC does not use the SDK factory, verified-count semantics differ between stores, and the §12b outbox policy is incomplete.

## §2 NON-NEGOTIABLE PROPERTIES (Part A)

| # | Property | Status | Evidence | Gap |
|---|---|---|---|---|
| 1 | One physical AGE graph, domain-partitioned | PARTIAL | Trading, Purchasing, and DataOps load config, require the shared graph, then call the factory (`apps/trading/backend/app/main.py:117-148`; `apps/purchasing/backend/app/main.py:166-197`; `apps/dataops/backend/app/main.py:109-138`). S2P does the same (`s2p-copilot/backend/app/main.py:115-133`). `require_shared_graph` rejects production AGE graphs other than `soc_graph` (`copilot_sdk/config/graph_config.py:26-49`). | SOC instead uses `app.db.neo4j.get_graph_client`, not `create_graph_store` (`gen-ai-roi-demo-v4-v50/backend/app/main.py:163-221`; `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:28-61`). The graph invariant is configured, but the one-factory architecture is not universal. |
| 2 | SQLite is local-adapter only | PARTIAL | Production expected AGE plus SQLite is rejected (`copilot_sdk/config/graph_config.py:248-265`; `copilot_sdk/graph/factory.py:145-164`). The four SDK/S2P app paths only select SQLite in test handling or through explicit factory selection (`apps/trading/backend/app/main.py:125-148`; `s2p-copilot/backend/app/main.py:111-133`). | The package defaults are SQLite (`copilot-sdk/graph_config.toml:1-5`), and the factory has an explicit SQLite branch (`copilot_sdk/graph/factory.py:171-192`). This is appropriate for local/test use but requires configuration discipline; stale architecture prose still describes old SQLite app deployment (`docs/storage_architecture.md:204-214`). |
| 3 | Both adapters implement the same Protocol v2 | PARTIAL | Protocol v2 declares the shared surface (`copilot_sdk/graph/protocol.py:176-360`). Protocol tests include SQLite and an AGE fixture (`tests/graph/test_protocol_v2_conformance.py:35-65`). | Correctness and domain conformance fixtures cover only memory and SQLite (`tests/graph/test_correctness_conformance.py:14-23`; `tests/graph/test_domain_required_conformance.py:11-15`). There is no dedicated identical-output AGE/SQLite conformance test. |
| 4 | Cross-copilot queries are graph traversals | CONFORMANT | Phase 6 claims 2, 3, 4, and 7 are single-store Cypher traversals, not API calls (`scripts/phase6_claim_proof.py:84-117`). AGE store loading also verifies one DSN and `soc_graph` for all configs (`scripts/phase6_claim_proof.py:176-198`). | The cited proof script is the evidence for the claim; it does not establish that every application helper is scoped, which is assessed under rule #41. |
| 5 | Conservation operates on the shared graph | PARTIAL | Scorer conservation reads V and q from its injected graph store (`copilot_sdk/scoring/scorer.py:2025-2032`); alpha is derived from verified decisions and configured categories (`copilot_sdk/scoring/scorer.py:1919-1929`). | Store implementations do not agree on verified semantics: memory and AGE allow an outcome fallback, while SQLite has a status-only method but scorer uses `count_verified` (`copilot_sdk/graph/memory_store.py:1117-1133`; `ci-platform/ci_platform/graph/age_graph_store.py:2122-2155`; `copilot_sdk/graph/sqlite_store.py:2219-2254`). |
| 6 | Audit chain is a graph traversal | PARTIAL | AGE writes Outcome/HAS_OUTCOME and domain-scoped EvidenceReceipt and checkpoint relationships (`ci-platform/ci_platform/graph/age_graph_store.py:952-968`; `:1103-1125`; `:1627-1651`). | The SDK edges are Decision→Outcome, Decision→Receipt, and Decision→Checkpoint; the source does not show one literal Outcome→Receipt→Checkpoint chain. SOC uses a separate hash-chain/raw-outcome model documented as distinct (`docs/design/correctness_architecture.md:17-39`). |

## §3 CONSERVATION (Part B)

| Check | Result | Evidence |
|---|---|---|
| V, InMemory | NO | `count_verified_decisions` accepts confirmed/overridden **or** an outcome entry (`copilot_sdk/graph/memory_store.py:1117-1126`). |
| V, SQLite | YES for its named method; NO for uniform scorer semantics | The method uses status only (`copilot_sdk/graph/sqlite_store.py:2231-2243`), but scorer calls `count_verified` (`copilot_sdk/scoring/scorer.py:2025-2028`), whose SQLite implementation joins outcomes (`copilot_sdk/graph/sqlite_store.py:2219-2229`). |
| V, AGE | NO, strictly | AGE also accepts `(status IS NULL AND outcome IS NOT NULL)` (`ci-platform/ci_platform/graph/age_graph_store.py:2127-2142`). |
| q | YES per store | All three `count_correct` implementations read the Decision `correct` property and do not traverse HAS_OUTCOME (`copilot_sdk/graph/memory_store.py:1128-1133`; `copilot_sdk/graph/sqlite_store.py:2245-2254`; `ci-platform/ci_platform/graph/age_graph_store.py:2144-2155`). |
| α | PARTIAL | Category coverage is computed from verified decisions (`copilot_sdk/scoring/scorer.py:1919-1929`), but `_is_verified_decision` accepts any non-None `is_correct` (`copilot_sdk/scoring/scorer.py:2115-2119`). |
| Snapshot persistence | YES per store | Payloads include V, q, alpha, theta_min, status and scope fields in memory (`copilot_sdk/graph/memory_store.py:704-743`), SQLite (`copilot_sdk/graph/sqlite_store.py:1405-1465`), and AGE (`ci-platform/ci_platform/graph/age_graph_store.py:1176-1235`). |
| Identical SQLite/AGE output conformance | NO | The correctness fixture is memory/SQLite and the AGE check is static source inspection (`tests/graph/test_correctness_conformance.py:14-23`; `:80-94`), not identical-data runtime comparison. |

## §4 AGE FAILURE POLICY (Part C)

| Operation | Required | Implemented? | Test? | Gap |
|---|---|---|---|---|
| Read/preview | Cached/computed degradation | PARTIAL | SDK `score_read_only` is pure computation (`copilot_sdk/scoring/scorer.py:383-406`); DataOps tests assert 503 on required AGE (`apps/dataops/backend/tests/test_dataops_fixture_closure.py:31-69`). | DataOps required reads fail 503 rather than degrade read-only (`apps/dataops/backend/app/graph_queries.py:143-145`; `:568-582`). |
| Score | Continue and queue Decision | GAP | No outage test. | `score` writes directly and propagates failure (`copilot_sdk/scoring/scorer.py:312-371`); outbox replay supports no Decision operation (`copilot_sdk/scoring/persistence_outbox.py:176-192`). |
| Learn/outcome | Fail closed and retry | PARTIAL | Normal conservation tests exist (`tests/scoring/test_conservation.py:54-80`). | Canonical outcome write is direct and fail-closed, but there is no outcome outbox/replay operation (`copilot_sdk/scoring/scorer.py:680-686`; `copilot_sdk/scoring/persistence_outbox.py:176-192`). |
| Evidence/audit | Queue/retry | YES | Failure is recorded and replay supports evidence receipts (`copilot_sdk/scoring/scorer.py:1167-1189`; `copilot_sdk/scoring/persistence_outbox.py:176-190`; `tests/scoring/test_persistence_outbox.py:30-49`). | No live AGE outage test. |
| Observation | Best effort/drop | GAP | No production caller or outage test was found. | Protocol/store write exists (`copilot_sdk/graph/protocol.py:218-220`), but outbox has no observation operation (`copilot_sdk/scoring/persistence_outbox.py:176-192`). |
| Conservation snapshot | Queue/retry | YES | Catch-and-record path and replay are implemented (`copilot_sdk/scoring/scorer.py:876-899`; `copilot_sdk/scoring/persistence_outbox.py:176-184`; `tests/scoring/test_conservation.py:100-113`). | No live AGE outage test. |
| Evolution event | Queue/retry | GAP | No dedicated failure/retry test. | Outbox replay has no evolution operation (`copilot_sdk/scoring/persistence_outbox.py:176-192`); evolution handling logs/returns from the scorer path rather than recording an evolution retry (`copilot_sdk/scoring/scorer.py:1870-1886`). |

## §5 SQLITE ROLE (Part D)

| Requirement | Status | Evidence |
|---|---|---|
| D1 no production AGE→SQLite rewrite | CONFORMANT in current app source | Production config is checked before factory construction in the SDK apps (`apps/trading/backend/app/main.py:117-148`; `apps/purchasing/backend/app/main.py:166-197`; `apps/dataops/backend/app/main.py:109-138`). SOC rejects non-AGE (`gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:46-50`). |
| D2 no silent SQLite when AGE expected | PARTIAL | Expected AGE plus SQLite is rejected (`copilot_sdk/graph/factory.py:145-164`), but default config is SQLite (`copilot-sdk/graph_config.toml:1-5`) and explicit factory SQLite construction remains available (`copilot_sdk/graph/factory.py:171-192`). |
| D3 same Protocol v2 methods | PARTIAL | Shared declarations and broad tests exist (`copilot_sdk/graph/protocol.py:176-360`; `tests/graph/test_protocol_v2_conformance.py:35-65`), but the named correctness/domain suites omit AGE (`tests/graph/test_correctness_conformance.py:14-23`; `tests/graph/test_domain_required_conformance.py:11-15`). |
| D4 protocol tests are not SQLite-specific | CONFORMANT for the named suites | Assertions are written against the generic store fixture (`tests/graph/test_correctness_conformance.py:26-78`; `tests/graph/test_domain_required_conformance.py:33-134`). |

## §6 STANDING RULES (Part E)

| Rule | Status | Evidence | Finding |
|---|---|---|---|
| #37 V is verified only | PARTIAL | SQLite’s status-only method is correct (`copilot_sdk/graph/sqlite_store.py:2231-2243`), but memory and AGE accept outcome fallback (`copilot_sdk/graph/memory_store.py:1117-1126`; `ci-platform/ci_platform/graph/age_graph_store.py:2127-2142`). | Not uniformly enforced. |
| #38 main uses create_graph_store | GAP | Four SDK/S2P paths call the factory (`apps/dataops/backend/app/main.py:129-138`; `s2p-copilot/backend/app/main.py:123-133`). | SOC main uses the separate AGE client path (`gen-ai-roi-demo-v4-v50/backend/app/main.py:163-221`; `gen-ai-roi-demo-v4-v50/backend/app/db/neo4j.py:52-61`). |
| #39 preview/read creates Observation, not Decision | PARTIAL | SDK preview is read-only (`copilot_sdk/scoring/scorer.py:383-406`), and the SOC triage path scores then writes a Decision (`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:604-609`; `:848-887`). | No evidence of an Observation write for a preview/read operation; the required behavior is therefore not proven. |
| #40 SQLite is never called product graph | CONFORMANT in inspected source | SQLite is named as a SQLite-backed GraphStore, not a product graph (`copilot_sdk/graph/sqlite_store.py:1`; `:376-377`). | Older storage documentation still describes SQLite app deployment (`docs/storage_architecture.md:204-214`), so documentation cleanup remains advisable. |
| #41 cross-domain reads have explicit filters | PARTIAL | Core store reads require domain (`copilot_sdk/graph/protocol.py:50-68`), and phase6 cross-domain claims explicitly express intentional cross-domain predicates (`scripts/phase6_claim_proof.py:84-117`). | Framework helpers make domain optional and omit the predicate when absent (`framework/decision_history.py:21-50`; `framework/similar_cases_base.py:61-88`). |

## §7 TEST GAPS (Part F)

| Gap | Has test? | Test needed |
|---|---|---|
| Strict status-only V across memory, SQLite, AGE | Partial | Parameterize identical data including pending decisions with outcomes; assert all stores exclude them. |
| Identical SQLite/AGE conservation counts and snapshots | No | Runtime AGE/SQLite fixture with equal V, q, alpha, theta_min, and status. |
| Score queues Decision during AGE outage | No | AGE-required store failure; assert score returns and Decision intent is durable in outbox. |
| Learn queues outcome while remaining fail-closed | No | Assert no false verification and an outcome retry record. |
| Observation best-effort/drop | No | Unavailable AGE observation write; assert request behavior and no Decision substitution. |
| Evolution retry | No | Failed evolution write, drain, and idempotent replay test. |
| Read/preview §12b degradation | Partial/opposite | Test cached/computed response under AGE outage; current DataOps closure test asserts 503 (`apps/dataops/backend/tests/test_dataops_fixture_closure.py:31-69`). |
| All five mains use one factory | No | Import/start each app and inspect construction path; SOC currently fails the rule by source evidence. |
| Preview Observation contract | No | Scan/integration test covering SDK and SOC preview/read endpoints. |
| Optional-domain helper enforcement | No | Require domain or explicitly mark intentional cross-domain in `decision_history` and `similar_cases_base`. |
| Audit chain shape and SOC equivalence | No | AGE traversal test for the actual edge topology plus a documented SOC hash-chain equivalence check. |

## §8 READING LOG

Fully read: `docs/design/judgment_memory_v2_7.md`; `docs/design/correctness_architecture.md` (substitute because the requested `correctness_unification_architecture_v1.md` is missing); `copilot_sdk/config/graph_config.py`; `copilot_sdk/graph/factory.py`; `copilot_sdk/graph/protocol.py`; `copilot_sdk/graph/memory_store.py`; `copilot_sdk/graph/sqlite_store.py`; `ci-platform/ci_platform/graph/age_graph_store.py`; `copilot_sdk/scoring/scorer.py`; `copilot_sdk/scoring/persistence_outbox.py`; all five copilot `main.py` files; SOC `app/db/neo4j.py`; `scripts/phase6_claim_proof.py`; the named conformance, conservation, outbox, and DataOps closure tests; and the SOC triage path cited above.

The requested `copilot_sdk/config/graph_config.py` is present; the package graph configuration used by the review is `copilot-sdk/graph_config.toml`. No source or test file was modified.

**READY: NO** — review evidence identifies unresolved PARTIAL/GAP items and missing permanent tests.
