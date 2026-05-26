# B1 AE-SDK — Implementation Notes
**Date:** 2026-05-25
**Baseline:** Prompt 1 SDK checks passed before this app-mount pass: `tests/evolution/` reported 195 passed, router tests reported 15 passed, focused graph evolution/consolidation checks reported 19 passed.

## Architecture Decision: Option B (Clean Separation)
- Option B was implemented because this repo has no external customer compatibility burden for the current evolution router shape.
- Option C dual-protocol compatibility was intentionally avoided so the SDK public protocols are cleaner.
- `GraphStore` is now decision/outcome/centroid persistence only.
- Evolution persistence no longer belongs to the `GraphStore` protocol.
- The removed `GraphStore` protocol methods were `save_evolution_event()` and `get_evolution_events()`.
- `EvolutionStore` is the separate protocol for evolution event persistence.
- `EvolutionStore` contains `save_evolution_event(domain, event_type, rule_name, variant_id, metadata)`.
- `EvolutionStore` contains `get_evolution_events(domain, rule_name, limit)`.
- `VariantSelector` is now a protocol for selection and reward update behavior.
- SQLite and memory stores retain their concrete evolution methods.
- Keeping concrete store methods avoids data-table churn.
- Keeping concrete store methods avoids duplicating persistence code.
- Keeping concrete store methods lets `SQLiteGraphStore` satisfy both `GraphStore` and `EvolutionStore` structurally.
- Keeping concrete store methods lets `InMemoryGraphStore` satisfy both `GraphStore` and `EvolutionStore` structurally.

## P1 Fix: Ledger Domain Mismatch
- Root cause: `InMemoryEvolutionLedger` previously persisted events through a graph-store shaped object without passing the domain.
- Root cause: the positional call could shift `event_type`, `rule_name`, and `variant_id` into the wrong slots for domain-aware stores.
- Fix applied: `InMemoryEvolutionLedger` now accepts a domain.
- Fix applied: the normal persistence path calls `save_evolution_event()` with keyword arguments.
- Fix applied: the call includes `domain`, `event_type`, `rule_name`, `variant_id`, and metadata.
- Fix applied: router-created ledgers pass the router domain into the ledger.
- Compatibility note: a narrow pre-domain adapter remains for existing scorer integration because `copilot_sdk/scoring/` was forbidden in Prompt 1.
- Test coverage: `tests/evolution/test_ledger_domain.py` verifies keyword fields, no-store behavior, and real SQLite domain persistence.

## P2 Fix: Gate Fail-Closed
- Root cause: `DefaultPromotionGate` treated missing conservation as GREEN.
- Root cause: the old check blocked only RED.
- Fix applied: missing conservation is unsafe.
- Fix applied: empty conservation dictionaries are unsafe.
- Fix applied: RED, AMBER, and unknown string states are unsafe.
- Fix applied: GREEN string is safe.
- Fix applied: `status=GREEN` is safe.
- Fix applied: `state=GREEN` is safe.
- Fix applied: `phase=green` is safe.
- Fix applied: `phase=verified` is safe.
- Fix applied: `phase=active` is safe.
- Fix applied: `overallSafe=True` is safe.
- Fix applied: `overall_safe=True` is safe.
- Fix applied: explicit `status`, `state`, or `phase` values take precedence over `overallSafe` and `overall_safe`.
- Fix applied: conflicting payloads such as `status=RED` with `overallSafe=True` fail closed.

| Conservation shape | Safe? |
|---|---|
| `None` | no |
| `{}` | no |
| `"GREEN"` | yes |
| `"AMBER"` | no |
| `"RED"` | no |
| `{"status": "GREEN"}` | yes |
| `{"status": "AMBER"}` | no |
| `{"state": "GREEN"}` | yes |
| `{"phase": "verified"}` | yes |
| `{"phase": "active"}` | yes |
| `{"overallSafe": true}` | yes |
| `{"overall_safe": true}` | yes |
| `{"status": "RED", "overallSafe": true}` | no |
| `{"state": "AMBER", "overall_safe": true}` | no |
| `{"phase": "unknown", "overallSafe": true}` | no |

- Test coverage: `tests/evolution/test_gate_fail_closed.py` covers unsafe and safe cases.
- Test coverage: existing gate/evolver/plateau tests were updated to pass explicit GREEN where promotion is expected.

## Router Changes
- Signature before: `create_evolution_router(graph_store_factory=None, domain="unknown", ledger_provider=None, variant_provider=None)`.
- Signature after: `create_evolution_router(graph_store_factory=None, domain="unknown", evolver_factory=None, variant_provider=None)`.
- `evolver_factory` is used when provided.
- `evolver_factory=None` falls back to internal `AgentEvolver` construction.
- Internal construction uses `InMemoryEvolutionLedger(evolution_store=store, domain=domain)`.
- Legacy string-domain first argument was removed.
- Legacy `ledger_provider` support was removed.
- Prefix standardization decision: the SDK router keeps the internal `/api/evolution` prefix.
- Prefix standardization decision: apps should mount it without an extra `/api` prefix.
- Prefix risk avoided: Purchasing no longer mounts the router with `prefix="/api"`.

## App Mount Updates
- Trading already used keyword arguments.
- Trading continues to pass `graph_store_factory=lambda: _graph_store(scoring_db)`.
- Trading continues to pass `domain=DOMAIN`.
- Trading continues to pass `variant_provider=lambda: []`.
- Purchasing was rewritten from legacy positional `DOMAIN` plus `ledger_provider`.
- Purchasing now passes `graph_store_factory=lambda: _graph_store(scoring_db)`.
- Purchasing now passes `domain=DOMAIN`.
- Purchasing now passes `variant_provider=_evolution_variants`.
- Purchasing no longer passes `prefix="/api"` around the evolution router.
- Purchasing no longer exposes `_FixtureEvolutionLedger`.
- Purchasing keeps fixture variant loading through `_evolution_variants()`.
- DataOps already used keyword arguments.
- DataOps continues to pass `graph_store_factory=lambda: _graph_store(scoring_db)`.
- DataOps continues to pass `domain=DOMAIN`.
- DataOps continues to pass `variant_provider=_evolution_variants`.

## SHOULD-DO Decisions
- S1 router simplification: completed for legacy string-domain and `ledger_provider` removal.
- S2 prefix consistency: completed by using router internal `/api/evolution` consistently.
- S3 ledger naming: partially complete; public constructor now prefers `evolution_store`, with narrow adapter for existing scorer integration.
- S4 shadow semantics: not changed in this pass.
- S5 gate consolidation: not consolidated with autonomous promotion; only `DefaultPromotionGate` fail-closed behavior changed.
- S6 `__init__.py` exports: completed for `EvolutionStore` and `VariantSelector`.

## Files Changed
| File | What changed |
|---|---|
| `copilot_sdk/evolution/protocol.py` | Added `EvolutionStore` and `VariantSelector`. |
| `copilot_sdk/evolution/ledger.py` | Added domain-aware evolution persistence. |
| `copilot_sdk/evolution/gate.py` | Made promotion fail closed on unsafe conservation. |
| `copilot_sdk/evolution/__init__.py` | Exported new protocols. |
| `copilot_sdk/graph/protocol.py` | Removed evolution persistence from `GraphStore`. |
| `copilot_sdk/backend/evolution_router.py` | Added `evolver_factory` and removed legacy compatibility. |
| `apps/purchasing/backend/app/main.py` | Replaced legacy evolution mount with clean keyword mount. |
| `apps/purchasing/backend/tests/test_purchasing_backend.py` | Updated clean router assertions and fixture variant tests. |
| `tests/evolution/test_ledger_domain.py` | Added ledger domain regression tests. |
| `tests/evolution/test_gate_fail_closed.py` | Added fail-closed gate tests. |
| `tests/evolution/test_evolution_store.py` | Added protocol separation tests. |
| `tests/evolution/test_gate.py` | Updated AMBER and explicit GREEN expectations. |
| `tests/evolution/test_evolver.py` | Updated promotion cases to pass explicit GREEN. |
| `tests/evolution/test_plateau.py` | Updated promotion cases to pass explicit GREEN. |
| `tests/evolution/test_protocol.py` | Added protocol runtime checks. |
| `tests/backend/test_evolution_router.py` | Updated router clean-signature tests. |
| `tests/backend/test_evolution_router_extended.py` | Added `evolver_factory` router tests. |
| `tests/graph/test_graph_store_evolution.py` | Moved protocol assertions to `EvolutionStore`. |
| `tests/graph/test_protocol.py` | Reconciled GraphStore protocol tests to Option B clean separation. |
| `docs/b1_implementation_notes.md` | Added this implementation record. |

## Files Intentionally Unchanged
- `copilot_sdk/evolution/prompt_evolver.py` was intentionally unchanged.
- `copilot_sdk/evolution/credit_attribution.py` was intentionally unchanged.
- `copilot_sdk/evolution/toy_rules.py` was intentionally unchanged.
- `copilot_sdk/evolution/variant_store.py` was intentionally unchanged.
- `copilot_sdk/graph/sqlite_store.py` was intentionally unchanged so the table and persistence behavior remain stable.
- `copilot_sdk/graph/memory_store.py` was intentionally unchanged so in-memory persistence behavior remains stable.
- Trading and DataOps app mounts were intentionally left behaviorally unchanged because they already used keyword arguments.

## Test Summary
- New tests: ledger domain tests, fail-closed gate tests, evolution store protocol tests, router factory tests.
- Updated tests: graph evolution tests, graphstore consolidation coverage, purchasing backend mount assertions, gate/evolver/plateau expectations.
- Deleted tests: none.
- Existing tests verified: `tests/evolution/` passed.
- Existing tests verified: router evolution tests passed.
- Existing tests verified: graph protocol and graphstore consolidation tests passed.
- App regressions verified: Trading backend passed.
- App regressions verified: Purchasing backend passed after updating clean-router assertions.
- App regressions verified: DataOps backend passed.
- Former failing validation resolved: `tests/graph/test_protocol.py` now asserts `EvolutionStore`, not `GraphStore`, owns evolution persistence.
- Existing tests verified: broad `tests/graph/` passed after the protocol-test reconciliation.
- Former root validation failure resolved: `copilot_sdk/scoring/scorer.py` now types evolution persistence against `EvolutionStore`.
- Former root validation failure resolved: the ledger pre-domain bridge now exposes `get_evolution_events()` and structurally satisfies `EvolutionStore`.
- Existing tests verified: broad `tests/` passed after the residual type-level coupling fixer.

## C1 Readiness Assessment
- Trading can use `evolver_factory` now because the router accepts it.
- Trading still currently uses default internal `AgentEvolver` construction.
- C1 can introduce a Trading-specific factory without changing the router signature again.
- C1 should avoid reintroducing `GraphStore` protocol coupling.
- C1 should use `EvolutionStore` for evolution event persistence.
- C1 should pass explicit conservation state to promotion paths.
- C1 should preserve the router internal `/api/evolution` prefix.

## Risks and Open Items
- The narrow ledger adapter for existing scorer integration remains transitional debt, but it now satisfies the `EvolutionStore` protocol boundary.
- Purchasing fixture variant filtering is now tested directly through `_filter_variants_by_query()` instead of the removed `_FixtureEvolutionLedger`.
- Full root suite was run after the residual type-level coupling fixer: `697 passed, 1394 warnings`.
- `copilot_sdk/scoring/scorer.py` no longer calls evolution persistence through a `GraphStore`-typed dependency.
- `copilot_sdk/evolution/ledger.py` no longer assigns a non-`EvolutionStore` bridge to the ledger persistence slot.
- GPT-5.5 review is required before treating B1 as closed.
