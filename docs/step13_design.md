# Step 13: F-08 shared demo infrastructure

## 1. Current state

Pre-check: Steps 10 and 11A are COMPLETE. Latest completed entry is Step 11B, with 4,367 SDK passes / 1 xfail. Step 12 owns transfer_router.py and transfer/registry.py in parallel; this step will not edit either. No existing shared-demo implementation or conflicting edit in the target files was observed.

- `copilot_sdk/demo/preseed.py:220-233`: DemoPreseed._preseed_domain creates a new InMemoryGraphStore for each of trading, purchasing, dataops, s2p and soc. There is no build_demo_scorers function currently.
- `preseed.py:115-137`: preseed_all orchestrates these domains, caches its result and verifies live scorer conservation. Full run: 200 rows per domain except DataOps 150; fast mode: Trading/Purchasing 20 each. Score and private preseed learn paths create decisions/outcomes, centroids and fingerprints; Trading also saves its rejection summary through graph evolution state. Existing display fixtures remain unchanged.
- `preseed.py:175-195`: cross-copilot supplier signal is currently an unpersisted dictionary. It is a deterministic demo fixture, not conservation evidence.
- `scripts/preseed_all_copilots.py:1-7,680-762`: an HTTP orchestrator, not an in-process store factory. It seeds separately running backends, preserves score/learn verification and supports selection/hero options. A Python object cannot be injected across those HTTP process boundaries.
- `demo.py:947-1017,1020-1250`: launcher starts backend subprocesses with AGE configuration and runs HTTP preseed scripts. Its local deterministic helper (`1491-1493`) delegates to DemoPreseed. Therefore sharing belongs in DemoPreseed; no launcher change is needed. The helper's pre-existing print_summary import is absent from preseed.py and is an independent launcher defect, not introduced here.
- No build_demo_scorers or _demo_patterns_for_mapping references occur in the preseed module or orchestration script. No transfer fixture replacement is needed; do not add a dependency on the Step 12 files.
- `copilot_sdk/graph/in_memory.py` does not exist. Actual implementation: `copilot_sdk/graph/memory_store.py:399`: `InMemoryGraphStore(domain: str = "test", decision_id_prefix: str = "") -> None`.
- Governance methods, memory_store.py:1701-1705 and GraphStore in protocol.py: `save_governance(self, domain: str, key: str, state: dict[str, Any]) -> None`, `get_governance(self, domain: str, key: str) -> dict[str, Any] | None`. ProtocolV2GraphStore inherits them unchanged.
- Root cause needed for safe sharing: scorer.py:176 derives persistence domain from the store's default domain, whereas from_preset loads centroids by preset.name (:349). A store named demo would otherwise mix different copilot schemas in one decision domain.

## 2. Proposed changes

### Change 1: shared offline graph factory

Add `create_demo_graph() -> InMemoryGraphStore` in preseed.py, returning `InMemoryGraphStore(domain="demo")`. Each invocation returns a new instance. No module singleton or implicit persistent fallback.

### Change 2: graph-backed cross-copilot signal

Add `seed_cross_copilot_signal(graph_store: GraphStore) -> str`. Use a stable demo-only governance key under domain `demo:cross_copilot`. Preserve the existing signal payload and add explicit synthetic fixture metadata. Save, read the exact key, compare the complete state, and raise RuntimeError on absent/mismatched readback. Return the key. No static JSON or fabricated conservation counters.

Move existing payload construction into a private module helper. DemoPreseed.seed_cross_copilot_signal delegates to the new function and returns the graph-read payload, preserving the existing result shape and deterministic output. Signal writes are idempotent for the same fixture key.

### Change 3: scorer graph injection

Add `build_demo_scorers(graph_store: GraphStore | None = None, *, profile: str | None = None) -> dict[str, CompoundingScorer]`. No supplied store means explicitly offline construction using one create_demo_graph call. An injected store is borrowed, passed verbatim to every scorer and never replaced/closed; its normal profile/production validation remains active (profile can be supplied for explicit test/offline injection). All five domains use enable_rl=False, as existing preseed does.

Add a backward-compatible optional `storage_domain: str | None = None` construction argument to CompoundingScorer.__init__/from_preset. Default retains legacy behavior. An explicit value selects that domain for writes, conservation, outbox and checkpoint loading; reject blank values. Production may not override the preset domain. The demo builder supplies each preset's own domain so every scorer has the SAME store identity but distinct domain-scoped histories. This is the minimal prerequisite for safe sharing; do not mutate store.domain or rebind private fields after initialization.

Extend DemoPreseed(seed, fast_mode, *, graph_store=None, profile=None). Build one scorer dictionary using build_demo_scorers; retain its shared graph for governance. _preseed_domain reuses the dictionary. Existing calls and per-instance idempotency remain supported. No scorer mocking or conservation replacement.

### Change 4: preseed script composition

Preserve default HTTP behavior. Add `preseed_offline(graph_store=None, *, seed=DEFAULT_SEED, fast_mode=False, profile=None)` as an in-process composition entry point. It explicitly creates one graph when absent and passes it to DemoPreseed (which calls build_demo_scorers and seeds the governance signal). Add opt-in --offline CLI mode invoking this path. Offline --dry-run reports a plan without writes; reject HTTP-only selection/hero/fixture/force flags in offline mode rather than silently ignoring them. Keep heavy SDK imports lazy for the default standard-library HTTP path.

### Change 5: demo.py

No change. Backend processes manage AGE at startup; local DemoPreseed calls inherit the fixed shared graph. No new in-memory store is constructed by the launcher.

## 3. Test plan

Use real InMemoryGraphStore and real scorers, with explicit test/offline profiles. The requested readback failure test may monkeypatch only get_governance (explicit user exception), annotated MOCK-OK; writes still hit the real store.

1. Factory returns memory store domain demo.
2. Factory calls produce separate objects.
3. Signal persists in exact governance domain/key and has fixture provenance.
4. Repeat signal seed/readback is stable and non-cumulative.
5. Missing readback raises RuntimeError; complete payload equality also rejects corrupt readback.
6. Default builder creates all five scorers sharing one memory object.
7. Provided store is the exact object used by all scorers; no replacement.
8. Scorer write visible through another scorer's graph API, with explicit source domain.
9. All five scorer domains remain distinct; verified counts/conservation use their own live rows.
10. Checkpoints reload from the explicit persistence domain, not the store default.
11. Omitted storage_domain preserves existing scorer domain behavior; blank override rejected.
12. DemoPreseed fast run writes 40 verified rows into supplied graph and preserves foreign data and domain counts.
13. Offline script helper uses supplied graph and persists the cross-copilot signal.
14. CLI dry-run and incompatible flag validation preserve no-write semantics.
15. Production construction without an injected production store fails; explicit production domain override is rejected.

Existing demo/preseed tests remain unchanged unless an actual shared-store regression requires an update. Existing tests reviewed include deterministic preseed, launcher lifecycle/AGE operations, preseed HTTP transport/schedules, hero contracts, truth checks, warm-start/discovery/transfer demos and bundle restoration.

Verification: mypy after each changed file and combined; focused shared-demo and existing preseed/scorer tests; full SDK --timeout=120; graphify refresh and package smoke checks. Preserve concurrent Step 12 edits and report final SDK counts accurately.

## Design review findings (resolved before implementation)

- Actual constructor is in memory_store.py; use domain="demo" and no nonexistent in_memory import.
- Governance key argument is named key, not ID; use exact positional domain/key/state contract and verify full readback.
- There is no existing build_demo_scorers function or caller signature to preserve. Preserve DemoPreseed positional seed/fast_mode arguments and HTTP seed_domain/main behavior.
- Sharing storage without a scorer domain override would mix decisions and checkpoint schemas. Add the optional storage_domain argument with unchanged defaults, validate production scope, and cover per-domain counts and checkpoint reload.
- Offline composition is an explicit mode. Injected stores retain normal profile resolution; they are never silently replaced by memory and production guards remain active.
- HTTP preseed cannot share an in-process memory object with remote backend processes. Add an opt-in offline path and helper instead of breaking the live HTTP workflow.
- Existing deterministic signal return shape stays intact; governance persistence is added and readback becomes authoritative. Synthetic provenance is explicit, and conservation still reads actual rows.
- demo.py needs no sharing edit; its existing local calls delegate to DemoPreseed. The unrelated stale print_summary import is documented, not expanded into this change.
- No _demo_patterns_for_mapping dependency exists in either target preseed file. No transfer-router imports or edits are needed.
- Missing-readback monkeypatch is explicitly requested by the user and limited to that fault-injection test; all normal tests use live stores/scorers.

## Implementation verification notes

- New shared-demo suite: 25 cases pass. Existing preseed/HTTP/scorer/Step 11B regression selection: 39 pass, no existing tests modified.
- The same GraphStore instance is used directly by all five scorers. Explicit storage_domain selects each copilot's existing domain before outbox, conservation and checkpoint initialization. Omitted storage_domain retains existing constructor and checkpoint behavior, including subclass compatibility.
- Existing production composition limitation discovered during review: production.py:98-109 requires each AGE adapter's bound domain to equal the scorer domain. A single currently domain-bound AGE adapter cannot serve all five production-profile scorers without a separately reviewed multi-domain composition contract. The injection API supports external stores and never creates a replacement; explicit offline/test profiles are verified. Production validation is preserved, not weakened or bypassed, and live multi-domain AGE production use is not claimed verified here.
- No _demo_patterns_for_mapping import/call was introduced. Step 12's transfer files remain outside this step's edits.

## Scope confirmation (2026-10-07)

The user confirmed that the shared offline InMemoryGraphStore path is the Step 13 deliverable. Do not extend the production validation contract. Record the multi-domain AGE shared-composition gap under Step 13 findings in session_state.md for a separate task. Existing production validation remains unchanged.
