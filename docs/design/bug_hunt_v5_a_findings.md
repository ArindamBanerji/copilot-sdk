# Bug Hunt v5-A Findings — Dimensions 1–6

**Date:** 2026-08-10  
**Scope:** Read-only source audit of the SOC, SDK, GAE, and CI paths  
**Method:** For each completed probe: locate exact source lines, read the full relevant function, trace the values through the branch, quote the decisive line, and classify severity.  
**Modification policy:** No application code, configuration, or tests were changed. This findings document is the sole deliverable.

## Executive result

The audit is **STOPPED** after five confirmed P1 findings, as required by the task. The five findings are production-impacting:

| ID | Finding | Severity | Primary location |
|---|---|---:|---|
| P1-1 | Simulation learning updates the production scorer instead of the simulation copy | P1 | `gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py:473-484` |
| P1-2 | Evaluation CSV upload reads the complete unbounded body into memory | P1 | `gen-ai-roi-demo-v4-v50/backend/app/routers/eval_router.py:31` |
| P1-3 | Graph explorer allows arbitrary `CALL` through the read-only query gate | P1 | `gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py:92-141` |
| P1-4 | Checkpoint rollback does not restore the live decision counter or complete model state | P1 | `gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py:145-173` |
| P1-5 | SOC graph-store provider dereferences a possibly uninitialized scorer | P1 | `gen-ai-roi-demo-v4-v50/backend/app/main.py:169`; `copilot-sdk/copilot_sdk/backend/self_computation_router.py:52,87-106` |

Because the threshold was met, dimensions 4–6 were not completed as a full mandatory probe set. Opportunistic reads made before the stop are separated from completed findings below; they must not be treated as a clean bill of health.

## Stop decision

The fifth P1 was confirmed while tracing the null/missing-data path (`1d`), after four earlier P1s had already been confirmed in dimensions 2 and 3. Per the instruction to stop immediately at five P1 findings, no further exhaustive line-by-line probes were run.

## P1-1 — Simulation mutates the production scorer

### STEP A — Locate

`gen-ai-roi-demo-v4-v50/backend/app/services/simulation.py:248` defines `SimulationOrchestrator.run`. The simulation clone is created at approximately line 309. The production scorer is reacquired at lines 473–484.

### STEP B — Function body read

The function creates a local cloned learning state, runs simulated decisions, optionally updates that local state, and then handles the ground-truth action path. The relevant branch is:

```python
_sim_scorer = get_profile_scorer()
if _sim_scorer is not None:
    _cu_sim = _guarded_update_sim(
        _sim_scorer,
        ...,
    )
```

The surrounding comments state that simulation updates are intended to be local and not affect the production singleton. The actual branch does not use the local clone.

### STEP C — Trace

1. `run()` receives a simulation request.
2. It creates `sim_ls = _clone_learning_state_for_simulation(get_learning_state())` at approximately line 309.
3. Simulated scoring proceeds against the local simulation state.
4. When learning is enabled and the ground-truth action is present, the code calls `get_profile_scorer()` again.
5. That function returns the process-wide production `ProfileScorer`, not `sim_ls`.
6. `_guarded_update_sim` therefore mutates live centroids, counts, and decision state.
7. The following snapshot path can also persist the resulting live mutation.

### STEP D — Verdict

The decisive source quote is:

> `_sim_scorer = get_profile_scorer()` — `simulation.py:473`

This contradicts the function’s local-copy design: the simulation branch obtains the production singleton rather than the simulation scorer/state.

### STEP E — Classification

**P1 — `simulation.py:473-484`.** A simulation request can alter shared production model geometry and persistence state. Concurrent real decisions can observe the mutation; all SOC scoring and later checkpoints are in blast radius.

## P1-2 — Evaluation CSV upload has no size limit

### STEP A — Locate

`gen-ai-roi-demo-v4-v50/backend/app/routers/eval_router.py:27` defines `upload_eval_csv`; the complete file body is read at line 31.

### STEP B — Function body read

The handler checks the filename extension, reads the upload, rejects empty content, decodes UTF-8, constructs a CSV reader, and materializes all rows with `list(enumerate(...))`. There is no byte limit, content-length guard, streaming parser, row limit, or multipart cap in this handler.

### STEP C — Trace

1. A request supplies a file whose name ends in `.csv`.
2. The extension check passes.
3. `raw = await file.read()` loads the entire request body.
4. Decoding creates a second in-memory representation.
5. `list(enumerate(reader, start=2))` materializes every parsed row.
6. A large upload therefore creates multiple large allocations; concurrent uploads multiply the cost.
7. A non-CSV file renamed with `.csv` is also not rejected by the extension check alone.

### STEP D — Verdict

The decisive source quote is:

> `raw = await file.read()` — `eval_router.py:31`

### STEP E — Classification

**P1 — `eval_router.py:31,54`.** An unauthenticated or otherwise reachable large upload can exhaust worker memory and take down the evaluation service. The extension-only validation is an additional P2 input-validation weakness at `eval_router.py:28`.

## P1-3 — Graph explorer permits arbitrary `CALL`

### STEP A — Locate

`gen-ai-roi-demo-v4-v50/backend/app/services/graph_explorer.py` contains the query gate:

- `SAFE_PREFIXES` at line 92 includes `CALL`.
- `BLOCKED_KEYWORDS` at line 95 includes mutation terms such as `CREATE`, `SET`, `DELETE`, `MERGE`, and `DROP`, but not `CALL`.
- `validate_query` starts at line 98.
- `run_safe_query` starts at line 117 and executes the query around line 141.

### STEP B — Function body read

`validate_query` uppercases and strips the query, requires one of the safe prefixes, then rejects only words in `BLOCKED_KEYWORDS`. `run_safe_query` calls the validator, appends a limit when absent, and forwards the resulting Cypher to the graph service.

### STEP C — Trace

1. Input begins with `CALL`.
2. The safe-prefix test passes because `CALL` is explicitly allowed.
3. The blocked-word loop does not reject `CALL` because it is absent from `BLOCKED_KEYWORDS`.
4. Validation returns true.
5. `run_safe_query` appends a limit if needed.
6. The graph service executes the caller-controlled `CALL` statement.
7. AGE procedures can have side effects or invoke operations beyond a read-only graph query; the prefix gate does not establish read-only semantics.

### STEP D — Verdict

The decisive source quote is:

> `"CALL",` — `graph_explorer.py:92`

The matching blocked-keyword list at line 95 does not contain `CALL`.

### STEP E — Classification

**P1 — `graph_explorer.py:92,95,98-113,117-141`.** The read-only graph explorer boundary is bypassable. A caller can execute arbitrary procedures through a path represented as safe; graph data and potentially graph state are in blast radius.

## P1-4 — Checkpoint rollback restores incomplete state

### STEP A — Locate

`gen-ai-roi-demo-v4-v50/backend/app/framework/checkpoint.py:101` defines `CheckpointService.rollback`; its complete body was read through line 177.

### STEP B — Function body read

The function queries a checkpoint, restores `mu_snapshot` into `scorer.centroids`, optionally restores counts, freezes the scorer, reads the checkpoint’s decision count into a local variable, and returns a response containing that count.

### STEP C — Trace

1. The checkpoint query returns a row and `cp` is extracted at line 128.
2. `mu_snapshot` is deserialized and assigned to `scorer.centroids` at line 145.
3. If counts exist, `scorer.counts[:]` is restored at line 156.
4. `scorer.freeze()` changes the current live scorer state at line 162.
5. The checkpoint decision count is read into `restored_dc` at line 163.
6. `restored_dc` is returned in the response, but no assignment updates `scorer.decision_count`.
7. No restoration was found for W/kernel weights, DK weights, temperature, covariance/uncertainty state, conservation state, or the other mutable model controls used by current scoring.
8. The API therefore reports a historical counter while the live scorer continues with its future counter and incomplete state.

### STEP D — Verdict

The decisive source quote is:

> `restored_dc = cp.get("decision_count")` — `checkpoint.py:163`

The subsequent code returns that local value; it does not assign `scorer.decision_count`.

### STEP E — Classification

**P1 — `checkpoint.py:145-173`.** Rollback silently leaves shared model state partly in the future. Subsequent learning, conservation, snapshots, and audit/reporting can diverge from the supposedly restored checkpoint. The rollback endpoint and all consumers of the live scorer are in blast radius.

## P1-5 — Null scorer dereference in the SOC graph-store provider

### STEP A — Locate

- `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:480-486` defines `get_profile_scorer()` and explicitly returns `None` before initialization.
- `gen-ai-roi-demo-v4-v50/backend/app/main.py:169` defines `_soc_store_provider`.
- `copilot-sdk/copilot_sdk/backend/self_computation_router.py:52` defines `_gs()`.
- `self_computation_router.py:87` defines the centroid-history route; it calls `_gs().get_centroid_checkpoints(...)` at line 106.

### STEP B — Function body read

The state accessor is:

```python
def get_profile_scorer():
    """Return global ProfileScorer instance, or None if not yet initialized."""
    try:
        return get_learning_state().profile_scorer
    except RuntimeError:
        return None
```

The SOC provider is:

```python
def _soc_store_provider():
    from app.services.gae_state import get_profile_scorer
    return get_profile_scorer().graph_store
```

The shared router’s `_gs()` simply calls the provider and returns its result; it does not translate an uninitialized provider into a 503.

### STEP C — Trace

1. A request arrives during the initialization window, or a startup failure leaves the learning state absent.
2. `get_profile_scorer()` catches the `RuntimeError` and returns `None`.
3. `_soc_store_provider` evaluates `None.graph_store`.
4. Attribute access raises before a valid `GraphStore` is returned.
5. `_gs()` propagates that failure.
6. The centroid-history route reaches `_gs().get_centroid_checkpoints(...)` at line 106, so the endpoint fails instead of returning a controlled unavailable response.

### STEP D — Verdict

The decisive source quote is:

> `return get_profile_scorer().graph_store` — `main.py:169`

This directly dereferences the nullable accessor documented at `gae_state.py:480-486`.

### STEP E — Classification

**P1 — `main.py:169`; `self_computation_router.py:52,87-106`.** A normal early request can produce an uncaught server failure on the shared self-computation surface. SOC graph-history and other routes using the same provider are in blast radius.

## Dimension 1 — Null / missing data paths

The following probes were traced before the stop condition.

| Probe | Trace result | Classification |
|---|---|---:|
| 1a — missing decision node | `get_decision(..., domain="soc")` returns `None`; handler raises an explicit 404 before the graph query result is consumed | OK — `triage.py:1806-1815` |
| 1b — orphan decision without `DECIDED_ON` | `OPTIONAL MATCH` yields null alert/category; fallback uses `unknown`/unclassified behavior and outcome can still be written | P2 — `triage.py:1830-1855` |
| 1c — null factor vector | parser produces `None`; routing path skips learning, while scorable path reaches factor-vector validation and can become a 500 | P2 — `triage.py:1935` and downstream validation |
| 1d — null profile scorer | most callers return 503 or use guarded fallbacks; the SOC graph-store provider dereferences `None` and is P1-5 above | P1 — `main.py:169` |
| 1e — null `mu_zero` | `compute_iks` returns estimated IKS 50 with `estimated=True`; shape mismatch follows the same safe fallback | OK/P2 informational — `iks_base.py:57-82` |
| 1f — unguarded graph result indexing | guarded `result[0]` uses were observed in the traced handlers; a complete all-repository inventory was not completed after the stop threshold | Not completed |

### 1a trace detail

`_decision_before` is loaded; when it is `None`, the handler raises a 404 and returns through the explicit HTTP error path. No `result[0]` is reached for that missing-node case.

### 1b trace detail

The graph query uses `OPTIONAL MATCH (d)-[:DECIDED_ON]->(a:Alert)`. With no edge, the decision row still exists, but `category` and alert type are null. The handler’s fallback selects an unknown/unclassified path. This avoids a null dereference but can record an outcome without the intended alert semantics.

### 1c trace detail

A null or unparsable factor vector becomes `None`. The routing-action branch logs that learning is skipped and continues to outcome persistence. The normal scorable branch validates the vector; the invalid value is rejected and the outer generic exception path can return HTTP 500. This is a controlled failure boundary but not a graceful response contract.

### 1e trace detail

`compute_visible_iks` obtains `mu_zero`; null is passed to `compute_iks`. `iks_base.py` explicitly returns the estimated payload rather than performing a subtraction or division against null. The result is degraded/estimated, not a crash.

## Dimension 2 — Concurrency / async safety

The stop threshold was reached while this dimension was being traced. The completed observations are recorded here; this is not a complete six-probe clearance.

| Probe | Evidence | Classification |
|---|---|---:|
| 2a — mutable singleton inventory | SOC/S2P audit ledgers and learning state are process-level mutable objects; audit has a lock; snapshot counter does not | P2 where unlocked — `gae_state.py:652-684` |
| 2b — `ProfileScorer.update()` lock | GAE `ProfileScorer.update` is synchronous and has no internal lock; some SOC callers serialize externally, but the library method itself is not thread-safe | P2 — `profile_scorer.py:780-1010` |
| 2c — simulation scorer copy | local learning state is cloned, but the ground-truth update reacquires the production scorer | P1-1 — `simulation.py:309,473-484` |
| 2d — snapshot counter | module counter increments and tests its interval without a lock | P2 — `gae_state.py:652-684` |
| 2e — audit hash/append lock | SOC and S2P audit append and chain updates occur under `asyncio.Lock` | OK — respective `framework/audit.py` ledgers |
| 2f — AGE pool | configured max defaults to 5 and connect timeout to 10 seconds; pool wait timeout is not explicitly configured in the inspected code | P2 operational gap — `ci-platform/ci_platform/graph/age_client.py:122-208,429-470` |

### 2a singleton notes

The relevant shared objects include the SOC/S2P audit ledger, learning-state/profile-scorer singleton, graph snapshot state, and the snapshot decision counter. Audit locking is present, while snapshot-counter locking is not. Provider caches were observed as mutable instance state; a complete lock inventory across every provider was not completed after the stop.

### 2f pool trace

The AGE client reads pool enablement and sizes, constructs a pool with `max_size=5`, and uses `pool.connection()` for pooled execution. Fresh connections use `connect_timeout=10`. The inspected constructor does not set an explicit pool acquisition timeout, so exhaustion behavior depends on the underlying pool defaults and should be made explicit in a follow-up.

## Dimension 3 — Error-state corruption

| Probe | Evidence | Classification |
|---|---|---:|
| 3a — ETA override restoration | original ETA fields are saved and restored in `finally` | OK — `triage.py` outcome handler, approximately `2225+` |
| 3b — partial scorer mutation | input shape/finite checks precede mutation; centroid mutation and clipping are separate operations, so an unexpected post-mutation exception could leave partial state | P2 — `profile_scorer.py:820-1010` |
| 3c — outcome transaction | AGE path uses `store.run_transaction` for outcome, centroid persistence, and checkpoint; audit/other surrounding effects are not all in that transaction | P2 — `gae_state.py` persistence helper |
| 3c-ext — K4 connectors | timeout/cache/error handling exists in inspected market, commodity, QBO, ThreatIntel, and SupplierIntel paths; no credential string was found in inspected exception messages; QBO exceptions are not explicitly redacted | P2 follow-up — connector paths |
| 3d — checkpoint rollback | centroids/counts/freeze are restored, but live decision counter and multiple model-state fields are not | P1-4 — `checkpoint.py:145-173` |
| 3e — startup order | graph setup and learning-state initialization precede normal route serving in the inspected startup sequence; provider race remains possible for early requests | P1-5 / P2 sequencing concern — `main.py:188+` |

### 3a trace detail

The outcome handler saves output ETA, negative ETA, and override values, enters the guarded update, and restores all three in `finally`, including the case where update or persistence raises. No stale override path was found in this probe.

### 3c trace detail

The AGE transaction callback writes the outcome, persists the centroid, and writes the checkpoint through the transaction object. However, audit-chain work and other pre/post effects are outside that closure. A later failure can therefore leave cross-system evidence at different commit points even though the core AGE writes are grouped.

### 3c-ext trace detail

Trading market data and SOC/S2P intelligence providers catch network failures and use cached/fallback data. Purchasing commodity loading uses a single-flight path and records a failed result. QBO uses a 15-second request timeout and passes credentials through the auth client/header path rather than the URL; no literal credential was observed in the inspected exception handling, but exception propagation without explicit redaction is a risk.

## Dimensions 4–6 — Stop boundary

The required immediate-stop rule prevents claiming a complete diagnostic for the remaining dimensions. Some source reads occurred opportunistically before the report was prepared, but the mandatory A–E procedure was not completed for every numbered probe after P1-5.

### Dimension 4 partial observations

- Conservation paths guard `V <= 0` and `alpha <= 0`; the inspected code returns a conservative threshold rather than dividing by zero.
- Scoring paths validate vector shape and finite values before update.
- IKS explicitly handles `mu_zero is None` and shape mismatch with an estimated result.
- Counts use `numpy.int64` in the inspected GAE scorer; `decision_count` is a Python integer.
- Several exact `== 0.0` checks were found in learning/reporting paths. They are potential P3 numerical-hygiene issues and were not exhaustively classified.

**Status:** probes 4a–4f not fully completed under the stop rule.

### Dimension 5 partial observations

- `ProfileScorer._decision_buffer` appends decisions and no cap/trim was observed in the traced update path.
- Centroid snapshot files are written with context-safe `pathlib` methods, but the snapshot directory has no observed retention cap.
- Snapshot listing loads all backup files, so disk growth and listing memory grow with snapshot count.
- AGE pool lifecycle is context-managed for pooled/fresh query connections in the inspected client.
- Hot-path logging and every mutable collection were not exhaustively inventoried.

**Status:** probes 5a–5f not fully completed under the stop rule.

### Dimension 6 partial observations

- The inspected AGE serializer escapes strings and serializes typed values; `_sync_execute` substitutes parameters through the serializer rather than concatenating raw values.
- Dynamic administrative graph labels/keys in migration code require separate validation review.
- Full POST endpoint inventory, upload type/size validation across all upload routes, graph-explorer mutation permutations, and `analyst_action` validation were not completed.

**Status:** probes 6a–6e not fully completed under the stop rule.

## Severity and blast-radius summary

| Severity | Count | Impact |
|---|---:|---|
| P1 | 5 | Shared production scorer corruption, process memory exhaustion, graph mutation/security bypass, incomplete rollback state, and uncaught early-request failure |
| P2 | Several | Semantic degradation, race windows, unbounded buffers/snapshots, transaction consistency, and connector redaction/pool configuration concerns |
| P3 | Several candidates | Float equality and other hygiene items not fully classified after stop |
| OK | Several | Explicit 404s, null IKS fallback, ETA `finally`, audit lock, shape/finite guards |

## Recommended remediation order

1. Make simulation use an isolated scorer/state for every learning update and prevent simulation checkpoint writes from reaching production storage.
2. Enforce upload byte, row, and parsed-field limits before materialization; validate content type/schema.
3. Remove `CALL` from the safe prefix list or replace it with a strict procedure allowlist whose procedures are provably read-only.
4. Define a complete rollback state contract and restore every mutable field, especially `decision_count`, W/DK/temperature, conservation, covariance, and freeze/pause state, atomically.
5. Make nullable scorer/store providers return a controlled 503 during initialization instead of dereferencing `None`.
6. Then resume the interrupted full probe matrix, beginning with dimensions 4–6 and the uncompleted 1f/2a/3c-ext inventories.

## Verification record

- Five repository `CLAUDE.md` files read: SOC, SDK, GAE, CI, and S2P.
- Prior Bug Hunt v5 probe document read through dimensions 1–6.
- Relevant function bodies read for all five P1 findings.
- No application code, test code, or configuration changed.
- No test suite was run because this was a read-only diagnostic.
- Audit intentionally stopped at the fifth confirmed P1 finding.
