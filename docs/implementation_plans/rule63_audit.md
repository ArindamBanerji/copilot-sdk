# Rule #63 GraphStore Test-Double Audit

Audit date: 2026-07-29. The inventory covers test patches that replace a
GraphStore/Protocol method. Rule #63 requires complete stateful doubles for
those methods rather than runtime monkeypatching.

## Violations

1. `copilot-sdk/tests/scoring/test_scorer.py:542` — patches
   `scorer.graph_store.count_decisions` — **VIOLATION**.
2. `copilot-sdk/tests/scoring/test_scorer.py:547` — patches
   `scorer.graph_store.archive_old_decisions` — **VIOLATION**.
3. `copilot-sdk/tests/scoring/test_scorer.py:589` — patches
   `graph_store.count_verified` — **VIOLATION**.
4. `copilot-sdk/tests/scoring/test_scorer.py:679` — patches
   `scorer._graph_store.count_verified` — **VIOLATION**.
5. `copilot-sdk/tests/scoring/test_scorer.py:697` — patches
   `store.count_verified` — **VIOLATION**.
6. `s2p-copilot/backend/tests/test_graph_links.py:124` — patches
   `app.state.graph_store.link_decision_to_entity` — **VIOLATION**.
7. `s2p-copilot/backend/tests/test_graph_links.py:139` — patches
   `app.state.graph_store.link_decision_to_entity` — **VIOLATION**.

## Allowed non-method patches reviewed

These hits replace application wiring or external test dependencies, not a
GraphStore method:

1. `s2p-copilot/backend/tests/test_l5_dk_s2p_hook.py:150` — replaces
   `app.state.graph_store` with a complete store double — **ALLOWED**.
2. `s2p-copilot/backend/tests/test_l5_full_flow_s2p.py:79` — replaces
   `app.state.graph_store` with a complete store double — **ALLOWED**.
3. `s2p-copilot/backend/tests/test_s2p_enrichment.py:470,489,503,513,525,538,549`
   — replaces application graph-store wiring — **ALLOWED**.
4. `s2p-copilot/backend/tests/test_s2p_score_endpoint.py:123` — restores the
   application graph-store reference to the scorer store — **ALLOWED**.
5. `s2p-copilot/backend/tests/test_graphstore_consolidation.py:127,145` —
   patches the test data directory — **ALLOWED**.
6. `copilot-sdk/tests/graph/test_graphstore_factory.py:220,252-254` — patches
   import loading and `sys.modules` to test factory behavior — **ALLOWED**.

No `mock.patch` call targeting a GraphStore method was found in either test
tree. The seven violations remain remediation work; this audit does not alter
those tests.
