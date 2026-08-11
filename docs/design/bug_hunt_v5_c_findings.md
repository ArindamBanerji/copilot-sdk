# Bug Hunt v5-C Findings — Dimensions 12–16

Read-only review performed against the SDK, ci-platform, S2P, and SOC source trees. No source or test files were modified. The only artifact written is this report.

## Summary — sorted by severity

### P1 BUGS (fix before demo)

1. **`copilot-sdk/copilot_sdk/scoring/scorer.py:1024-1147` — score/learn persistence is not one transaction.** The in-memory centroid update occurs before `write_outcome`, receipt, DK refresh, checkpoint, and learning-artifact writes. A later exception can leave the scorer and graph at different states. This is a silent consistency failure affecting every SDK copilot using `CompoundingScorer.learn()`.

### P2 BUGS (fix before pilot)

1. **`copilot-sdk/copilot_sdk/evolution/gate.py:31-41` — promotion gate does not enforce a minimum batch count.** With one batch, variance is forced to `0.0`; `sufficient_data` checks total decisions only. A one-batch result can pass if the other checks pass.
2. **`copilot-sdk/copilot_sdk/scoring/measurement_state.py:53-94` — measurement state is derived without transition monotonicity.** If verified/arm counts later fall below the threshold, a previously measured cohort can report `ACCUMULATING` again. This is a derived-state regression rather than an invalid persisted enum transition.
3. **`copilot-sdk/apps/trading/frontend/src/components/ProvenanceBadge.tsx:16-33` and `MarketContext.tsx:23-35` — provenance badges have no subscription or refresh mechanism.** They update when a parent supplies new props, but a K3→K4 backend flip is not reflected until the parent refetches or the page rerenders with new data.
4. **SOC endpoint parity — `/api/conservation/status` is missing on port 8001.** Live probe returned 404; SOC exposes `/api/soc/learning-health` at `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:720-735` instead. This breaks a shared endpoint contract for clients that require the common conservation route.

### P3 ISSUES (backlog)

1. **`copilot-sdk/copilot_sdk/evolution/variant_store.py:62-72` — in-memory variant storage has no capacity bound or retirement cleanup.** Variant IDs and statistics can grow for the process lifetime.

### Findings not classified as bugs

- Transfer centroid deltas are shape-filtered before assignment; no silent truncation was found.
- Transfer payloads do not carry DK weights, temperature, or effective weights.
- Transfer execution resets target conservation state when patterns are applied.
- Shadow scorer construction enforces distinct primary and shadow stores.
- Evolution parameter application clamps values to `EvolutionBounds`.
- Holdout assignment is deterministic by SHA-256.
- Claim promotion rejects a REAL-tier promotion without `evidence_ref`.
- No active MERGE query was found in the targeted SDK/ci-platform graph implementation; AGEClient rejects MERGE text at `ci-platform/ci_platform/graph/age_client.py:86-99`.
- Oracle modules generate synthetic outcomes in memory and do not write oracle data to a graph.

The stop condition was not reached: one P1 finding was confirmed, fewer than five.

## Detailed findings per dimension

### 12a — Transfer centroids shape mismatch

**LOCATE:** `warm_start_centroids()` — `copilot-sdk/copilot_sdk/transfer/warm_start.py:10-16`.

**READ:** Full body `warm_start.py:10-39`; filtering helper `applied_patterns()` is `warm_start.py:42-66`. The production scorer calls the filter before applying at `copilot-sdk/copilot_sdk/scoring/scorer.py:1845-1861`. The chain-transfer validator also checks complete tensor shape at `copilot-sdk/copilot_sdk/transfer/chain_transfer.py:49-54`.

**TRACE for source `(5,4,10)` and target `(5,4,7)`:**

- `warm_start.py:19`: copies the target tensor; target shape remains `(5,4,7)`.
- `warm_start.py:27`: iterates only `applied_patterns(...)`.
- `warm_start.py:53`: reads `factor_count = 7` from the target.
- `warm_start.py:60`: converts the incoming delta.
- `warm_start.py:61`: requires `delta.shape == (7,)`.
- `warm_start.py:62`: a 10-element source delta fails the check and is skipped.
- `warm_start.py:32`: is therefore never reached for the mismatched pattern; no broadcasting or truncation occurs.
- For `ChainTransfer`, `chain_transfer.py:51-52` rejects the mismatched source/target before pattern construction.

**VERDICT:** `if delta.shape != (factor_count,): continue` — `warm_start.py:61-62`.

**CLASSIFY:** OK — `copilot-sdk/copilot_sdk/transfer/warm_start.py:53-65`.

**BLAST RADIUS:** A mismatched transfer is safely ignored or rejected; it does not mutate target centroids.

### 12b — Transfer DK-weight leak

**LOCATE:** Transfer payload definition — `copilot-sdk/copilot_sdk/transfer/registry.py:14-24`; transfer persistence — `copilot-sdk/copilot_sdk/scoring/scorer.py:1916-1929`.

**READ:** `TransferPattern` contains pattern identity, category/action, win rate, centroid delta, confidence, and metadata only (`registry.py:14-24`). The persistence call writes factor mapping, confidence, validation, conservation, source fingerprint, and event IDs (`scorer.py:1916-1929`).

**TRACE:**

- `registry.py:21`: payload field is `centroid_delta`; there is no `dk_weights` field.
- `registry.py:24`: metadata is arbitrary, so callers could technically insert arbitrary metadata, but the production construction path does not add DK/tau.
- `scorer.py:1916-1929`: persisted transfer fields omit DK weights, temperature, and effective weights.
- `chain_transfer.py:99`: response explicitly reports `"dk_transferred": False`.

**VERDICT:** `"dk_transferred": False` — `copilot-sdk/copilot_sdk/transfer/chain_transfer.py:99`.

**CLASSIFY:** OK — `copilot-sdk/copilot_sdk/transfer/registry.py:14-24`.

**BLAST RADIUS:** No DK/tau authority crosses the transfer boundary in the reviewed production paths.

### 12c — Transfer conservation reset

**LOCATE:** Transfer execution — `copilot-sdk/copilot_sdk/backend/transfer_router.py:139-170`; reset helper — `transfer_router.py:582-606`.

**READ:** Full execution branch `transfer_router.py:139-173` and reset helper `582-606`.

**TRACE:**

- `transfer_router.py:139`: invokes `scorer.warm_start(patterns)`.
- `transfer_router.py:140`: reads applied-pattern count.
- `transfer_router.py:142-143`: when `applied > 0`, calls `_reset_conservation_state`.
- `transfer_router.py:588-601`: writes target status `GREEN`, `alpha=0.0`, `q=0.0`, `V=0`, and zero category coverage.
- `transfer_router.py:604`: returns `True` only if the write succeeds.
- `transfer_router.py:170`: exposes whether the reset was persisted.
- Chain transfer independently sets `target.conservation_v = 0.0` at `chain_transfer.py:82-99`.

**VERDICT:** `conservation_reset = _reset_conservation_state(scorer, target_domain)` — `transfer_router.py:141-143`.

**CLASSIFY:** OK — `copilot-sdk/copilot_sdk/backend/transfer_router.py:582-606`.

**BLAST RADIUS:** Applied transfers reset target conservation rather than carrying source V/q/alpha into the target. A failed reset is surfaced as `conservation_reset=False`.

### 12d — Cross-domain graph query isolation

**LOCATE:** Canonical domain predicate — `copilot-sdk/copilot_sdk/graph/projection.py:90-99`; AGE store domain filtering — `ci-platform/ci_platform/graph/age_graph_store.py:2463-2517`.

**READ:** `AGEProjection` injects the constructor domain through `_d2_where()` at `projection.py:268-272`; all public decision reads use it at `projection.py:276-299`. AGE store methods build a domain clause at `age_graph_store.py:2467-2473` and apply it after `MATCH` at `2466-2483`, `2485-2499`, and `2506-2517`.

**TRACE:**

- Static projection templates at `projection.py:39`, `44`, and `49` display bare `MATCH (d:Decision)` strings.
- `ProjectionRegistry.render()` receives a domain and replaces the predicate placeholder or inserts one at `projection.py:71-86`.
- An `AGEProjection` cannot be constructed without a validated domain at `projection.py:238-255`.
- Runtime decision reads then use `self.domain` through `_d2_where()` at `projection.py:268-299`.
- AGE store `get_decisions`, verified counts, correct counts, category counts, and archive reads all add their domain clause before returning data (`age_graph_store.py:2467-2558`, `2945-2970`, `3282-3340`).

**VERDICT:** `WHERE {domain_clause}` — `ci-platform/ci_platform/graph/age_graph_store.py:2473-2478`; the bare registry strings are templates, not executed without rendering.

**CLASSIFY:** OK for the reviewed executable SDK/ci-platform graph paths — `projection.py:71-86`, `age_graph_store.py:2467-2478`.

**BLAST RADIUS:** No cross-domain read was demonstrated in the canonical store/projection paths. The static template strings remain a maintenance hazard if a caller bypasses `render(domain)`.

### 13a — Promotion gate with insufficient batches

**LOCATE:** `DefaultPromotionGate.evaluate()` — `copilot-sdk/copilot_sdk/evolution/gate.py:22-54`.

**READ:** Full method `gate.py:22-54`; configuration declares `shadow_min_batches=3` at `copilot-sdk/copilot_sdk/evolution/prompt_evolver.py:28-37`.

**TRACE for one batch:**

- `gate.py:27`: reads total decisions.
- `gate.py:31`: reads one batch accuracy.
- `gate.py:32`: `len(batches) == 1`, so `variance = 0.0` without measuring between-batch stability.
- `gate.py:35`: sufficient data checks the caller’s `sufficient` flag and total decisions only.
- `gate.py:36-39`: superiority, accuracy floor, conservation, and zero variance checks run.
- `gate.py:41`: promotion occurs if all five checks pass.
- No expression checks `len(batches) >= shadow_min_batches`.

**VERDICT:** `"variance": variance <= 0.10` — `gate.py:39`; this treats one batch as zero variance.

**CLASSIFY:** P2 — `copilot-sdk/copilot_sdk/evolution/gate.py:31-41`.

**BLAST RADIUS:** A candidate supported by one batch can be promoted before the configured multi-batch stability requirement is honored.

### 13b — Shadow scorer isolation

**LOCATE:** `ShadowScorer.from_preset()` — `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:67-97`.

**READ:** Full constructor guard and factory `shadow_scorer.py:46-97`; score/learn forwarding `99-150`.

**TRACE:**

- `shadow_scorer.py:76`: compares store object identity.
- `shadow_scorer.py:77-79`: raises if primary and shadow stores are the same object.
- `shadow_scorer.py:81-84`: primary scorer receives `primary_store`.
- `shadow_scorer.py:86-89`: shadow scorer receives `shadow_store`.
- `shadow_scorer.py:101-126`: both are scored, but primary result is returned.
- `shadow_scorer.py:128-150`: both learn paths run with mapped decision IDs.

**VERDICT:** `if primary_store is shadow_store: raise ValueError(...)` — `shadow_scorer.py:76-79`.

**CLASSIFY:** OK — `copilot-sdk/copilot_sdk/migrate/shadow_scorer.py:67-97`.

**BLAST RADIUS:** The factory prevents shadow writes from entering the primary store. Callers that bypass the factory remain responsible for supplying separate stores.

### 13c — Agent/evolver variant cleanup

**LOCATE:** `InMemoryVariantStore.register_variant()` — `copilot-sdk/copilot_sdk/evolution/variant_store.py:58-72`; evolver proposal log — `copilot-sdk/copilot_sdk/scoring/evolution.py:47-60`, `128-129`, `240-243`.

**READ:** Store initialization and registration `variant_store.py:58-72`; no cap/eviction method exists in the full 178-line module. Scorer evolution appends proposals at `scoring/evolution.py:128-129` and remembers them at `240-243`.

**TRACE:**

- `variant_store.py:62-64`: dictionaries are initialized without a maximum.
- `variant_store.py:66-71`: every new ID is inserted into `_variants` and `_global_stats`.
- No branch removes old variants during registration.
- `scoring/evolution.py:128`: every evaluation extends `_log` with proposals.
- `scoring/evolution.py:240-243`: `_remember` appends when the object is not already present.

**VERDICT:** `self._variants[spec.id] = _copy_spec(spec)` — `variant_store.py:71`.

**CLASSIFY:** P3 — `copilot-sdk/copilot_sdk/evolution/variant_store.py:62-72`.

**BLAST RADIUS:** Long-lived processes can accumulate variant metadata and proposal history; this is capacity pressure, not immediate correctness failure.

### 13d — Scorer evolution hard bounds

**LOCATE:** `EvolutionBounds` — `copilot-sdk/copilot_sdk/scoring/evolution_config.py:8-16`; clamp/apply — `copilot-sdk/copilot_sdk/scoring/evolution.py:131-155`, `230-254`.

**READ:** Full bounds dataclass and `_bounds_for_parameter`; full `apply()` and `_clamp()`.

**TRACE:**

- `evolution_config.py:13`: `eta_override` is bounded to `(0.005, 0.05)`.
- `evolution_config.py:15`: temperature is bounded to `(0.05, 0.20)`.
- `evolution.py:143-145`: unsupported parameters are rejected and every supported proposed value is passed to `_clamp`.
- `evolution.py:230-232`: `_clamp` applies `max(low, min(value, high))`.
- A proposal of `eta_override=1.0` becomes `0.05`; `-0.5` becomes `0.005`.
- A temperature of `0` becomes `0.05`.
- No direct scorer-internal mutation occurs in this evolution class; `apply()` writes only the supplied config dict at `evolution.py:152`.

**VERDICT:** `bounded_value = self._clamp(proposal.parameter, float(proposal.proposed_value))` — `evolution.py:145-146`.

**CLASSIFY:** OK — `copilot-sdk/copilot_sdk/scoring/evolution.py:131-155`.

**BLAST RADIUS:** The reviewed proposal path cannot set values outside the configured bounds. External callers can still mutate their own config dict after `apply()`; that is outside this enforcement path.

### 14a — Cohort state machine invalid transitions

**LOCATE:** `compute_measurement_state()` — `copilot-sdk/copilot_sdk/scoring/measurement_state.py:37-94`.

**READ:** Full state computation `measurement_state.py:37-94`; enum values `13-16`.

**TRACE:**

- `measurement_state.py:44-51`: recomputes threshold, verified count, arm counts, and missing decisions on every call.
- `measurement_state.py:53-64`: zero verified decisions returns `INSTRUMENT_VALIDATED`.
- `measurement_state.py:66-80`: any positive `decisions_needed` returns `ACCUMULATING`.
- `measurement_state.py:82-94`: only zero `decisions_needed` returns `MEASURED`.
- There is no prior-state argument, persisted state comparison, or transition table. If archival/reset changes counts below threshold after a measured response, the next call returns `ACCUMULATING`.

**VERDICT:** `if decisions_needed > 0:` — `measurement_state.py:66`; it permits a derived measured→accumulating regression when inputs regress.

**CLASSIFY:** P2 — `copilot-sdk/copilot_sdk/scoring/measurement_state.py:44-94`.

**BLAST RADIUS:** UI and gates may see a cohort move backward after archival, reset, or threshold changes; no invalid enum value is produced.

### 14b — Oracle experiment synthetic data in production graph

**LOCATE:** `BaseOracle.synthetic_outcome()` — `copilot-sdk/copilot_sdk/substantiation/oracle.py:33-73`; experiment runners call it in `substantiation/chef_oracle.py:133-144`, `dataops_oracle.py:135-144`, and `trader_oracle.py:128-137`.

**READ:** The oracle methods construct dictionaries in memory. The experiment helpers collect lists; no graph/store import or write call appears in those bodies. The package-level oracle scan found no `write_decision`, `write_outcome`, graph store, or save operation in the oracle implementations.

**TRACE:**

- `oracle.py:59`: returns a synthetic outcome dictionary.
- `chef_oracle.py:134`: appends returned dictionaries to a local `treatment` list.
- `chef_oracle.py:142`: appends returned dictionaries to a local `control` list.
- The same pattern is used by DataOps and Trader oracle helpers.
- No graph handle is constructed and no write method is called.

**VERDICT:** `return { ... }` from the synthetic outcome path — `copilot-sdk/copilot_sdk/substantiation/oracle.py:59-72`.

**CLASSIFY:** OK — `copilot-sdk/copilot_sdk/substantiation/oracle.py:33-73`.

**BLAST RADIUS:** Oracle outputs stay in the experiment process and cannot contaminate the production AGE graph through these paths. This satisfies the F-27 separation requirement.

### 14c — Holdout assignment determinism

**LOCATE:** `_bucket()` — `copilot-sdk/copilot_sdk/substantiation/holdout.py:46-48`; assigners call it at `holdout.py:22-43`.

**READ:** Full holdout module `holdout.py:1-48`.

**TRACE:**

- `UnconditionalHoldout.suppressed()` passes the same entity ID and configured seed to `_bucket()` at line 30.
- `ConditionalHoldout.suppressed()` returns false only when enrichment is absent; otherwise it uses the same `_bucket()` at line 43.
- `_bucket()` hashes the exact string `f"{entity_id}:{seed}"` with SHA-256 at line 47.
- It converts the first eight hex digits to an integer and applies `% 100` at line 48.
- There is no random module, clock, process ID, or mutable assignment state.

**VERDICT:** `return int(digest[:8], 16) % 100` — `holdout.py:48`.

**CLASSIFY:** OK — `copilot-sdk/copilot_sdk/substantiation/holdout.py:22-48`.

**BLAST RADIUS:** The same decision/entity ID and seed receive the same assignment across calls and processes.

### 14d — Claim registry promotion without evidence

**LOCATE:** `ClaimRegistry.promote()` — `copilot-sdk/copilot_sdk/substantiation/registry.py:56-66`.

**READ:** Full method `registry.py:56-66`; `PromotionEvent.evidence_ref` is required by the dataclass at `registry.py:25-33`.

**TRACE:**

- `registry.py:57`: loads the existing claim.
- `registry.py:58`: checks specifically for a REAL-tier promotion with a falsey evidence reference.
- `registry.py:59-62`: raises `ValueError` when that condition is met.
- `registry.py:63-66`: only then updates tier/evidence and appends history.

**VERDICT:** `if ev.to_tier == Tier.REAL and not ev.evidence_ref:` — `registry.py:58`.

**CLASSIFY:** OK — `copilot-sdk/copilot_sdk/substantiation/registry.py:56-66`.

**BLAST RADIUS:** REAL claims cannot silently promote without an evidence reference through this registry.

### 14e — Provenance badge stale after K4 flip

**LOCATE:** `ProvenanceBadge` — `copilot-sdk/apps/trading/frontend/src/components/ProvenanceBadge.tsx:16-68`; representative parent `MarketContext` — `copilot-sdk/apps/trading/frontend/src/components/MarketContext.tsx:23-35`.

**READ:** Badge is a pure function of `source`, `asOf`, and `market` (`ProvenanceBadge.tsx:16-33`). The parent reads `snapshot.provenance` and passes it to the badge (`MarketContext.tsx:23-35`). No timer, websocket, subscription, or fetch appears in either component.

**TRACE:**

- Parent receives a snapshot at `MarketContext.tsx:23`.
- `MarketContext.tsx:25-26` derives the current provenance source and timestamp.
- `MarketContext.tsx:33` passes the source to the badge.
- `ProvenanceBadge.tsx:17-33` computes the label from the current prop.
- A K3→K4 backend change is invisible until the parent obtains a new snapshot; the badge has no independent refresh path.

**VERDICT:** `{provenance?.source ? <ProvenanceBadge ... /> : null}` — `MarketContext.tsx:33`.

**CLASSIFY:** P2 — `copilot-sdk/apps/trading/frontend/src/components/MarketContext.tsx:23-35`.

**BLAST RADIUS:** A long-lived page can display stale provenance after the backend flips source tier, potentially mislabeling displayed context until refetch/navigation.

### 15a — Score+learn atomicity

**LOCATE:** `CompoundingScorer.learn()` — `copilot-sdk/copilot_sdk/scoring/scorer.py:903-1158`.

**READ:** Full method read in chunks `scorer.py:903-1008`, `1009-1079`, and `1080-1158`.

**TRACE:**

- `scorer.py:913`: reads the decision.
- `scorer.py:1024-1031`: mutates the in-memory scorer centroids through `_scorer.update()`.
- `scorer.py:1045-1051`: writes the graph outcome in a separate store call.
- `scorer.py:1055-1061`: writes an evidence receipt separately.
- `scorer.py:1062`: refreshes DK state.
- `scorer.py:1065-1070`: may write an entity link separately.
- `scorer.py:1087-1098` or `1105-1113`: may write a centroid checkpoint separately.
- `scorer.py:1136-1146`: persists additional learning artifacts separately.
- The only `finally` at `scorer.py:1032-1034` restores temporary eta fields; it does not roll back centroids or graph writes.
- No `run_transaction` or transaction object wraps the full method.

**VERDICT:** `self._graph_store.write_outcome(...)` — `scorer.py:1045-1051`, after the centroid mutation at `1024-1031` and before later writes.

**CLASSIFY:** P1 — `copilot-sdk/copilot_sdk/scoring/scorer.py:1024-1147`.

**BLAST RADIUS:** Any failure after the in-memory update can produce a centroid/outcome/checkpoint mismatch. The affected domain’s subsequent scores may use learned state that has no durable verified outcome, or durable outcomes may lack matching learned artifacts.

### 15b — Concurrent domain writes and decision ID prefixes

**LOCATE:** `SQLiteGraphStore.generate_decision_id()` — `copilot-sdk/copilot_sdk/graph/sqlite_store.py:1105-1111`; store constructor prefix — `sqlite_store.py:393-396`; production prefixes — `copilot-sdk/apps/trading/backend/app/main.py:153`, `apps/purchasing/backend/app/main.py:202`, `apps/dataops/backend/app/main.py:166`.

**READ:** The generator creates a UUID suffix and prepends the configured prefix. In-memory store has the equivalent prefix policy at `copilot_sdk/graph/memory_store.py:330-332`, `483-486`.

**TRACE:**

- `sqlite_store.py:1108`: creates a fresh UUID-based 12-character raw ID.
- `sqlite_store.py:1109-1110`: prepends `_decision_id_prefix` when configured.
- Trading, Purchasing, and DataOps production stores configure distinct prefixes.
- Even without a prefix, the UUID suffix makes accidental equality highly unlikely; domain is also stored and used in graph reads.

**VERDICT:** `return f"{self._decision_id_prefix}{raw_id}"` — `sqlite_store.py:1109-1111`.

**CLASSIFY:** OK for configured SDK production stores — `apps/*/backend/app/main.py` cited above.

**BLAST RADIUS:** No same-process collision mechanism was found for the configured production prefixes. Bare in-memory/test stores intentionally omit a semantic prefix but still use UUID IDs.

### 15c — Advisory-lock and MERGE policy

**LOCATE:** AGE safety check — `ci-platform/ci_platform/graph/age_client.py:86-99`; graph store write pattern — `ci-platform/ci_platform/graph/age_graph_store.py:1025-1053`.

**READ:** The targeted `ci-platform/ci_platform/graph` and `copilot-sdk/copilot_sdk/graph` scan found no active non-comment MERGE query. AGE writes use MATCH/SET/CREATE, as shown in `age_graph_store.py:1025-1053`.

**TRACE:**

- `age_client.py:86`: documents the forbidden syntax.
- `age_client.py:96-99`: rejects a `MERGE (` token before execution.
- `age_graph_store.py:1026-1052`: matches the domain decision, sets fields, creates the outcome, and creates the edge without MERGE.

**VERDICT:** `raise ValueError("Forbidden: MERGE is not supported...")` — `age_client.py:96-99`.

**CLASSIFY:** OK — `ci-platform/ci_platform/graph/age_client.py:86-99`.

**BLAST RADIUS:** The targeted shared graph layer rejects MERGE rather than executing it. This probe did not find a Rule #50 violation in the inspected graph implementation.

### 16a–16d — Endpoint parity

**LOCATE:** Shared SDK routes are mounted by `copilot-sdk/copilot_sdk/backend/self_computation_router.py`; SOC’s alternate learning-health route is `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:720-735`.

**READ:** Live parity was checked for `/health`, `/api/self/diagnostics`, `/api/conservation/status`, `/api/self/evolution/summary`, and `/api/self/centroid-history?limit=1` across ports 8001, 8002, 8010, 8020, and 8030.

**TRACE:**

- **16a `/health`:** all five returned 200. Response shapes are intentionally domain-specific: SOC returns `components,status`; S2P returns `service,status,version`; the other copilots include cache/domain/engine fields.
- **16b `/api/self/diagnostics`:** all five returned the common keys `centroid_distance_to_canonical`, `domain`, `epsilon_firm`, `iks`, and `measurement_state` on the stable retry.
- **16c `/api/conservation/status`:** S2P, Trading, Purchasing, and DataOps returned 200 with the common explainability fields. SOC port 8001 returned 404.
- **16d `/api/self/evolution/summary` and centroid history:** all five returned 200; evolution responses shared `schema_version`, `evolution_enabled`, `conservation_state`, inventory, recent events, and variant fields; centroid history shared `checkpoints,total`.
- SOC instead exposes `GET /api/soc/learning-health` at `framework_router.py:723`, whose documented response starts at `framework_router.py:724-735`.

**VERDICT:** SOC has no common conservation route; the live response was `404 {"detail":"Not Found"}` for `http://127.0.0.1:8001/api/conservation/status`.

**CLASSIFY:** P2 — `gen-ai-roi-demo-v4-v50/backend/app/routers/framework_router.py:720-735`.

**BLAST RADIUS:** Shared clients, parity tests, and cross-copilot dashboards that call the common conservation endpoint fail only for SOC. The alternate SOC route remains available.

## Blast radius matrix

| Finding | Trigger | Copilots affected | Data at risk |
|---|---|---|---|
| P1 non-atomic learn | Exception in outcome/receipt/checkpoint/artifact persistence after centroid update | Trading, Purchasing, DataOps, S2P, and any SDK scorer | In-memory centroids and durable outcome/checkpoint state can diverge |
| P2 one-batch promotion | `batch_accuracies` has one element while total/superiority checks pass | Any SDK evolution gate user | Premature variant promotion |
| P2 measurement regression | Counts fall below threshold after archive/reset or threshold change | Any SDK measurement consumer | State label can move from measured back to accumulating |
| P2 provenance refresh | Backend K3/K4 source changes without parent refetch | Trading and analogous badge consumers | Stale provenance label only |
| P2 SOC parity | Client calls `/api/conservation/status` on port 8001 | SOC clients and shared parity checks | Endpoint availability, not graph data |
| P3 variant growth | Repeated unique variant registration/proposal | Long-lived SDK processes | Process memory / metadata growth |

## Verification notes

- Read-only source analysis completed; no production or test source was modified.
- Live endpoint parity probe used Node `fetch` after the shell’s Python URL reader showed intermittent connection-drain behavior on unrelated large responses.
- Stable live results: all five `/health`, diagnostics, evolution, and centroid-history families returned 200; only SOC `/api/conservation/status` returned 404.
- No P1 threshold stop was triggered.
