# J6 Write-on-Exist Design

Status: architecture investigation only. No implementation is included in this
document. This design is based on the current source tree; the older description
that every state artifact is unreachable on pause is not fully true in the
current code and is called out below.

## 1. Executive Summary

J6 has two different kinds of persistence:

* State-capture artifacts describe the state that currently exists. They should
  be capturable after startup restoration, after a pause, and after a successful
  learn. A state change is not a prerequisite for recording an accurate
  snapshot.
* Evidence receipts describe an auditable decision/outcome event. They require
  an event payload and must not be fabricated merely because a scorer was
  constructed or paused. JM defines the receipt as a hash-chain audit trail
  (`judgment_memory_v2_7.md:307-314`).

The current implementation already captures conservation on the shared scorer
pause path (`scorer.py:579-602`) and writes a V2 checkpoint on that same path
when finite centroids exist (`scorer.py:603-628`). It does not capture a
fingerprint on pause because the branch returns before `_compute_iks()` and the
artifact coordinator (`scorer.py:629`, `:687-690`, `:748-758`). SOC's
non-scorable route currently captures only conservation
(`gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1914-1928`).

The unambiguous write-on-exist gap affects all five copilots at startup:
`restore_l5_runtime_state()` restores DK, centroids, and conservation state but
has no J6 capture call (`copilot_sdk/scoring/startup_restore.py:14-49`), and
the four SDK application startup paths invoke that restore after constructing
their scorers (`apps/trading/backend/app/main.py:357-377`,
`apps/purchasing/backend/app/main.py:455-475`,
`apps/dataops/backend/app/main.py:564-583`,
`s2p-copilot/backend/app/main.py:189-195`). SOC constructs its compound
scorer and graph store during learning-state initialization, but does not run a
J6 state capture there (`gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:204-221`,
`:296-302`).

Design decision: add an explicit, public state-capture operation to the shared
compound scorer, invoke it after startup restoration for all five copilots, and
invoke its state portion on pause/non-scorable paths. Preserve the existing
successful-learn writes. Do not create an evidence receipt without a real
receipt event.

## 2. Artifact Classification

| Artifact | Type | Justification | Multiple writes safe? |
|---|---|---|---|
| `ConservationStatus` | Type A: state snapshot | JM defines `V`, `q`, `alpha`, `theta_min`, status, and `computed_at` as the current conservation state (`judgment_memory_v2_7.md:332-340`). The shared writer accepts those state values directly (`copilot-sdk/copilot_sdk/graph/protocol.py:228-241`). | Yes, when each capture has a distinct capture identity or is idempotent for identical content. |
| `Fingerprint` | Type A: derived quality snapshot | It summarizes factor names/statistics and the analyzed window (`judgment_memory_v2_7.md:327-330`). The scorer derives it from verified decisions, not from the current learn event (`scorer.py:772-784`). | Yes, with the existing content signature deduplication (`scorer.py:1071-1084`). A changed verified population creates a new content identity. |
| `CentroidCheckpoint` | Type A: centroid/IKS snapshot | JM explicitly stores serialized centroids, counts, IKS, shape, and timestamp (`judgment_memory_v2_7.md:320-325`). The V2 writer persists those fields (`scorer.py:1603-1620`). | Yes for distinct snapshots; startup captures need a deterministic identity and explicit capture reason because the current writer uses a random UUID (`scorer.py:1607-1618`). |
| `EvidenceReceipt` | Type B: event record | It is a tamper-evident receipt chain tied to a decision, actor, route, and payload (`judgment_memory_v2_7.md:307-314`; `protocol.py:216-226`). | No arbitrary duplicates. A receipt is valid only for a real intent/outcome event and must preserve chain ordering. |

The current fingerprint implementation has a useful startup constraint: it
returns a deterministic “insufficient data” result below five compatible
decisions (`copilot_sdk/copilot_sdk/scoring/fingerprint.py:21-45`). The proposed
startup writer must therefore record a fingerprint only when the verified graph
population is usable for the transfer contract, or record an explicit
`insufficient_data` state rather than advertise it as a learned transfer.

## 3. Lifecycle × Artifact × Copilot Matrix

Legend: `YES` means the current path writes the artifact; `PROPOSED` means the
write is part of this design; `NO` means the artifact is not valid for that
phase; `conditional` means the required state or event must exist.

### 3.1 Current write locations

| Artifact | SOC | S2P | Trading | Purchasing | DataOps |
|---|---|---|---|---|---|
| Conservation | on SOC non-scorable; on SOC guarded-update pause/success | on shared learn success and pause | on shared learn success and pause | on shared learn success and pause | on shared learn success and pause |
| Fingerprint | on SOC scorable bridge only; not non-scorable | on successful shared learn or explicit fingerprint call | on successful shared learn or explicit fingerprint call | on successful shared learn or explicit fingerprint call | on successful shared learn or explicit fingerprint call |
| Evidence receipt | on SOC scorable bridge only | pre-outcome route plus successful shared learn | successful shared learn | successful shared learn | successful shared learn |
| Checkpoint | on SOC scorable bridge only | shared learn success and pause | shared learn success and pause | shared learn success and pause | shared learn success and pause |

Evidence for the shared paths: successful `learn()` writes an outcome and
receipt (`scorer.py:663-677`), computes IKS/fingerprint persistence
(`scorer.py:687-690`), performs the direct checkpoint path when configured
(`scorer.py:697-727`), and calls the coordinator (`scorer.py:748-758`). The
coordinator itself writes conservation, fingerprint, optional receipt, and
optional checkpoint (`scorer.py:914-993`).

Evidence for S2P's special receipt path: S2P appends a pre-outcome receipt
through the shared store (`s2p-copilot/backend/app/routers/s2p.py:1335-1405`)
before both `/api/learn` and `/api/s2p/outcome` call the scorer
(`s2p.py:2068-2121`, `:2169-2250`).

Evidence for SOC: the non-scorable branch explicitly skips learning and writes
only conservation (`triage.py:1914-1928`); the scorable bridge invokes the
shared artifact coordinator only after `_guarded_update()` returns a result
(`triage.py:2143-2172`).

### 3.2 Lifecycle matrix

| Lifecycle phase | Conservation | Fingerprint | Checkpoint | Evidence receipt |
|---|---|---|---|---|
| Construction/startup, all domains | NO today; **PROPOSED** after restore | NO today; **PROPOSED conditional on usable verified data** | NO today; **PROPOSED** after restore when centroids exist | NO: no decision/outcome event |
| Score | NO | NO | NO | NO |
| Successful shared learn | YES | YES | YES | YES |
| Shared learn paused | YES | NO today; **PROPOSED conditional on usable verified data** | YES today when finite centroids exist | NO in the shared scorer because no successful outcome is written |
| S2P paused learn route | YES | NO today; **PROPOSED conditional** | YES through shared `learn()` | YES for the S2P pre-outcome intent receipt |
| SOC non-scorable outcome | YES today | NO today; **PROPOSED conditional on usable verified data** | NO today; **PROPOSED** | NO |
| SOC guarded-update pause | YES today | NO today; **PROPOSED conditional** | NO in the SOC bridge; **PROPOSED** | NO |
| First request after startup, before learn | NO today; **PROPOSED startup capture already completed** | NO today; **PROPOSED startup capture already completed** | NO today; **PROPOSED startup capture already completed** | NO |

“Score” is deliberately empty: the scoring router calls `scorer.score()` and
returns its result; the J6 learn coordinator is not called by that route
(`copilot_sdk/backend/scoring_router.py:101-120`, `:122-200`).

### 3.3 Per-copilot startup state

| Copilot | Centroid source | DK loaded? | Conservation loaded? | State available to capture? |
|---|---|---|---|---|
| SOC | Compound scorer loads graph centroids or preset state; SOC also initializes its profile scorer (`scorer.py:238-278`; `gae_state.py:204-221`) | SOC L5/bootstrap state is initialized in `gae_state.py:228-300` | Compound scorer can compute shared conservation from the graph; current SOC non-scorable bridge proves the method is available (`triage.py:1920-1928`) | YES, conditional on a Protocol V2 graph store and usable verified decisions |
| S2P | `CompoundingScorer.from_preset()` loads latest centroids or uses preset bootstrap (`scorer.py:238-278`) | Startup restore calls `_restore_dk()` (`startup_restore.py:43-48`, `:58-108`) | Startup restore calls `_restore_conservation()` (`startup_restore.py:206-226`) | YES |
| Trading | Fresh proxy constructs the compound scorer against its active store (`scorer_proxy.py:31-41`; `trading/main.py:323-340`) | Startup restore is run against the inner scorer (`trading/main.py:368-377`) | Same restore path | YES |
| Purchasing | Fresh proxy constructs the compound scorer (`scorer_proxy.py:31-41`; `purchasing/main.py:441-443`) | Startup restore runs against the inner scorer (`purchasing/main.py:466-475`) | Same restore path | YES |
| DataOps | Fresh proxy constructs the compound scorer (`scorer_proxy.py:31-41`; `dataops/main.py:550-552`) | Startup restore runs against the inner scorer (`dataops/main.py:574-583`) | Same restore path | YES |

Trading's regime wrapper preserves the shared path: it delegates unknown
attributes to `FreshScorerProxy` (`apps/trading/backend/app/services/regime_scoring.py:20-31`),
and the router receives that wrapper (`trading/main.py:338-390`). Purchasing and
DataOps use `FreshScorerProxy` directly. S2P constructs `CompoundingScorer`
directly (`s2p-copilot/backend/app/main.py:134-141`).

## 4. Gap Analysis

### 4.1 Artifact-level result

| Artifact | Write-on-exist gap? | Exact gap |
|---|---|---|
| Conservation | YES, startup only | Pause and non-scorable writes exist, but no startup capture is called after L5/graph state is restored (`startup_restore.py:14-49`). |
| Fingerprint | YES | No pause, SOC non-scorable, or startup capture. Successful learn and explicit fingerprint calls are the only current routes (`scorer.py:670-690`, `:772-784`, `:914-924`). |
| Checkpoint | YES, startup and SOC-specific pause paths | Shared `learn()` covers success and pause, but startup has no capture and the SOC bridge does not call `_save_centroids_checkpoint()` on non-scorable or guarded-update pause (`triage.py:2143-2172`). Warm-start writes only legacy centroids, not the V2 checkpoint (`scorer.py:1320-1335`). |
| Evidence receipt | NO | It is an event artifact. The shared receipt requires decision/outcome data (`scorer.py:995-1046`), so creating one at startup or for a non-scorable route would be false provenance. S2P's pre-outcome receipt is valid because it records a real submitted intent (`s2p.py:1335-1405`). |

Therefore `GAP_COUNT = 3` Type A artifacts. All five copilots are affected by
the startup gap. SOC has additional pause/non-scorable fingerprint and
checkpoint gaps. Trading, Purchasing, and DataOps have fingerprint gaps on
shared pause; S2P has the same fingerprint gap, while its pre-outcome receipt
path is intentionally separate.

### 4.2 The design premise versus the code

The statement “all artifacts are only written after centroid change” is stale
for the shared scorer. Conservation is explicitly called before the pause
return (`scorer.py:579-602`), and checkpoint persistence is explicitly called
before that return (`scorer.py:603-621`). The implementation work must not
remove either behavior. The actual unimplemented requirement is state capture
after restoration and the missing fingerprint/state checkpoint capture on
special paths.

## 5. Design Decision

### 5.1 Public state-capture operation

Add a public method to `CompoundingScorer`, for example:

```python
capture_existing_state(
    *,
    capture_reason: Literal["startup_restore", "conservation_pause", "non_scorable"],
    decision_id: str | None = None,
) -> dict[str, int | str]
```

The method must:

1. Require a Protocol V2 store before attempting J6 writes, matching the
   existing guards (`scorer.py:819-820`, `:900-901`).
2. Compute conservation from the same verified population used by
   `_conservation_pause()` (`scorer.py:1428-1470`) and preserve JM's
   `alpha * q * V` semantics (`judgment_memory_v2_7.md:429-465`).
3. Persist a conservation snapshot even when no centroid update occurred.
4. Compute and persist a fingerprint only when the verified decisions contain
   enough compatible factor data to be meaningful. Reuse the current canonical
   fingerprint serialization and signature (`scorer.py:1056-1084`); do not
   manufacture learned weights.
5. Persist a V2 centroid checkpoint when a finite centroid tensor exists. Add
   metadata such as `capture_reason`, `state_source`, and `decision_id` when a
   real decision caused the capture. Startup/non-scorable captures must not
   create a fabricated `DERIVED_FROM` Decision edge.
6. Never persist an evidence receipt. Return per-artifact counts and error
   information so a partial capture is visible.

The existing `_persist_learning_artifacts()` remains the successful-learn
coordinator. It should call the state portion only where that does not duplicate
the existing event ordering; the current direct learn-path flags must be
preserved (`scorer.py:748-758`, `:890-899`).

### 5.2 Placement

* **Startup:** invoke the method immediately after
  `restore_l5_runtime_state()` returns for S2P, Trading, Purchasing, and
  DataOps. This is the first point where L5 DK/centroid/conservation restore
  has completed (`startup_restore.py:43-49`). For SOC, invoke it after the
  compound scorer and graph store are initialized in `gae_state.py`; expose a
  named adapter method rather than relying on the adapter's raw-profile
  `__getattr__` (`scorer_adapter.py:20-32`, `gae_state.py:204-221`, `:296-302`).
* **Shared pause:** retain the existing conservation and checkpoint calls, then
  add only the conditional fingerprint capture. Do not call the full
  successful-event coordinator because it would imply an outcome.
* **SOC non-scorable:** retain the current conservation call and add the
  conditional fingerprint and checkpoint state capture in the same guarded
  block (`triage.py:1916-1933`). No receipt.
* **SOC guarded-update pause:** add the same state-only capture where `_cu is
  None` (`triage.py:2143-2157`).
* **Successful learn:** preserve current writes and deduplication. No extra
  startup-style capture is needed at this point.

### 5.3 Identity and duplicate guards

* Conservation: keep decision-scoped IDs for decision-caused captures. For
  startup captures, use a deterministic `domain + capture_reason + state
  digest` identity, so restart retries are idempotent and changed state is a
  new snapshot. Do not use a random UUID for a state snapshot.
* Fingerprint: retain the content hash and in-process signature dedup already
  implemented (`scorer.py:1071-1084`). The graph writer must reject conflicting
  content under one fingerprint ID rather than overwrite it.
* Checkpoint: add a deterministic startup/non-event identity derived from
  domain, capture reason, centroid digest, verified count, and IKS. Keep the
  existing per-decision UUID behavior for learn checkpoints until a compatible
  immutable revision identity is approved. Mark startup captures with
  `metadata.capture_reason="startup_restore"` and do not attach them to a
  nonexistent Decision.
* Receipt: preserve append/hash-chain ordering. The only duplicate guard is the
  existing receipt intent/idempotency contract; no “write on startup” shortcut.

### 5.4 Coordinator decision

Do not invoke `_persist_learning_artifacts()` wholesale on pause or SOC
non-scorable paths. Its contract says it runs after a successful update
(`scorer.py:881-899`) and its evidence/checkpoint branches can resolve event
fields from a Decision (`scorer.py:926-993`). Create a state-only helper that
shares the three Type A writers, while keeping evidence receipt under the
event-specific path.

## 6. Per-Copilot Post-Fix State

| Copilot | Phase | Conservation | Fingerprint | Checkpoint | Receipt |
|---|---|---:|---:|---:|---:|
| SOC | startup with usable verified graph data | YES | YES, conditional on compatible factor vectors | YES if finite centroids | NO |
| SOC | non-scorable | YES | YES, conditional | YES if finite centroids | NO |
| SOC | scorable learn | YES | YES | YES | YES |
| S2P | startup with restored state | YES, conditional on finite conservation metrics | YES, conditional on usable verified data | YES if centroids exist | NO |
| S2P | successful learn | YES | YES | YES | YES, including the existing pre-outcome intent path |
| S2P | paused learn | YES | YES, conditional | YES | YES only for the existing real pre-outcome intent; no synthetic post-outcome receipt |
| Trading | startup with restored state | YES, conditional | YES, conditional | YES | NO |
| Trading | successful learn | YES | YES | YES | YES |
| Trading | paused learn | YES | YES, conditional | YES | NO |
| Purchasing | startup with restored state | YES, conditional | YES, conditional | YES | NO |
| Purchasing | successful learn | YES | YES | YES | YES |
| Purchasing | paused learn | YES | YES, conditional | YES | NO |
| DataOps | startup with restored state | YES, conditional | YES, conditional | YES | NO |
| DataOps | successful learn | YES | YES | YES | YES |
| DataOps | paused learn | YES | YES, conditional | YES | NO |

“Conditional” is intentional: a fingerprint needs compatible verified factor
vectors, and a checkpoint needs a finite centroid tensor. The scorer's current
fingerprint fallback explicitly reports insufficient data rather than learned
statistics (`fingerprint.py:21-45`).

## 7. Warm-Start Validation

### 7.1 Fingerprint equivalence

A fingerprint captured at startup from the same AGE verified-decision set will
contain the same factor names and factor statistics as one captured after
learn. Both use `compute_fingerprint(get_verified_decisions(...), factor_names)`
(`scorer.py:772-780`) and serialize factor sigma/weight, win rate, category
precision, analyzed window, and skipped count (`scorer.py:1056-1077`). The
centroid tensor itself is not fingerprint content; it is represented by a
checkpoint. The implementation must record the capture reason so operators can
distinguish “startup snapshot” from “post-learn snapshot.”

### 7.2 Sufficiency for transfer

The existing detector uses source and target factor sigma maps and emits a
factor opportunity when the source is sufficiently low-noise and the target is
high-noise (`copilot_sdk/backend/transfer.py:101-138`, `:150-165`). Therefore a
startup fingerprint is sufficient for factor-quality transfer if its factor
vectors are compatible and its statistics are not the insufficient-data
fallback. The warm-start graph audit still requires a real source fingerprint
ID and target application; the scorer emits a TransferPattern only after a
pattern is applied (`scorer.py:1222-1238`, `:1272-1307`).

### 7.3 SOC claim-4 consequence

After this design is implemented, SOC can produce a usable fingerprint without
a scorable outcome in the current process **if** the shared AGE graph contains
enough verified SOC decisions with compatible factor vectors. The non-scorable
route alone does not create an evidence receipt or a learn update, but it also
does not invalidate pre-existing verified graph data (`triage.py:1914-1955`). If
SOC's verified rows are missing compatible vectors, the writer must return
`insufficient_data`; SOC→S2P and SOC→DataOps remain `NOT_PROVEN`, not fabricated.

## 8. Implementation Plan

### 8.1 Files and changes

| File | Location | Planned change | Preserve |
|---|---|---|---|
| `copilot-sdk/copilot_sdk/scoring/scorer.py` | Around `_persist_learning_artifacts()`, pause branch, and checkpoint writer (`:579-629`, `:881-993`, `:1558-1635`) | Add state-only capture helper; add conditional fingerprint capture on shared pause; add deterministic non-event snapshot identity/metadata; expose a public method for adapters. | Existing pause conservation, pause checkpoint, successful outcome/receipt/fingerprint/checkpoint order, outbox behavior. |
| `copilot-sdk/copilot_sdk/scoring/startup_restore.py` | `restore_l5_runtime_state()` after restore (`:43-49`) | Invoke the public state-capture method after restore, with `capture_reason="startup_restore"`; return capture status in startup diagnostics. | Existing restore source/error reporting and L5 data transformations. |
| `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py` | Adapter public methods (`:20-32`) | Add an explicit state-capture delegation to the compound scorer. Do not depend on the current `__getattr__`, which delegates to the raw profile scorer. | Existing SOC scoring/update API and profile-scorer delegation. |
| `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py` | End of `init_learning_state()` (`:296-302`) | Invoke compound state capture after the SOC graph store and compound scorer are available. | Bootstrap state, raw SOC persistence, and store selection. |
| `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py` | Non-scorable and `_cu is None` branches (`:1916-1933`, `:2143-2172`) | Invoke state-only capture for fingerprint/checkpoint when state is usable; retain conservation call and no receipt. | Routing skip semantics and no learning for `refer_to_analyst`. |

No changes are proposed to Trading, Purchasing, DataOps, or S2P main files if
`startup_restore.py` owns the common hook. Their current startup calls already
pass the inner `CompoundingScorer` and graph store (`trading/main.py:370-375`,
`purchasing/main.py:468-473`, `dataops/main.py:576-581`,
`s2p/main.py:189-193`). If the common helper cannot safely own the hook, the
fallback is to add one explicit call at each of those four call sites; that is
a design implementation choice, not permission to silently omit a domain.

### 8.2 Execution order

1. Add unit-level state-capture contract and deterministic identity helpers in
   the shared scorer; run SDK mypy and scorer persistence tests.
2. Add the startup-restore hook; run SDK startup/diagnostics tests and verify
   all four SDK application paths receive the capture status.
3. Add explicit SOC adapter delegation and the SOC startup call; run SOC tests.
4. Add SOC non-scorable and guarded-pause state capture; run SOC triage tests.
5. Run S2P, Trading, Purchasing, DataOps, SOC, CI, and SDK suites.
6. Run live AGE census and verify one state snapshot per domain before and
   after a restart. Then test a paused path and a SOC non-scorable path.

### 8.3 What must not change

Do not:

* write an EvidenceReceipt at construction or for a skipped routing action;
* call the successful-event coordinator when no outcome exists;
* replace the verified population with L5 decision counts;
* turn an insufficient-data fingerprint into a validated transfer;
* attach startup snapshots to fabricated Decision or EvolutionEvent nodes;
* remove the shared pause conservation/checkpoint behavior already present;
* change the existing successful-learn artifact ordering.

## 9. Test Plan

### Shared SDK tests

1. Startup capture with a restored centroid and verified graph population writes
   conservation, fingerprint, and V2 checkpoint, but no receipt.
2. Repeating startup capture with identical state is idempotent; changing the
   centroid or verified population creates a new immutable snapshot.
3. Shared paused learn writes conservation and checkpoint, conditionally writes
   fingerprint, and does not write outcome or receipt.
4. Fingerprint with fewer than five compatible vectors remains explicitly
   insufficient and cannot be marked validated.
5. All writes use Protocol V2 stores and record outbox failures without
   blocking score/learn responses.

### Per-copilot tests

* SOC non-scorable outcome: conservation plus conditional fingerprint/checkpoint;
  no receipt and no centroid update.
* SOC guarded-update pause: same state-only behavior.
* S2P pre-outcome receipt remains present for both learn routes, while a paused
  scorer does not receive a fabricated post-outcome receipt.
* Trading regime proxy delegates startup capture and learn persistence to the
  inner compound scorer.
* Purchasing and DataOps FreshScorerProxy paths write the same artifacts as the
  underlying compound scorer.
* Each copilot has a restart test proving the startup capture does not depend on
  a new learn cycle.

### Live AGE gates

For each of `soc`, `s2p`, `trading`, `purchasing`, and `dataops`, record:

* one `ConservationStatus` with verified-only scope and finite metrics;
* one usable `Fingerprint` when the domain has compatible verified vectors;
* one V2 `CentroidCheckpoint` when centroids exist;
* zero synthetic receipts for startup/non-scorable capture;
* unchanged successful-learn receipt chains.

The graph topology must continue to use JM's canonical labels and edges,
including `SUMMARIZES_DOMAIN` for conservation/fingerprint and the checkpoint
schema in `judgment_memory_v2_7.md:343-374`.

## 10. Blast Radius

| File/change | Consumers | Test impact |
|---|---|---|
| Shared `CompoundingScorer` capture helper | `FreshScorerProxy.learn/fingerprint` and every caller of `CompoundingScorer.from_preset()` (`scorer_proxy.py:31-41`, `:56-92`) | SDK scoring, persistence, startup, diagnostics, and all three SDK app suites |
| Startup restore hook | Trading, Purchasing, DataOps, S2P startup call sites listed in §8.1 | Four app startup/health suites plus SDK startup tests |
| SOC adapter method | `gae_state.init_learning_state()` and triage's compound bridge (`scorer_adapter.py:20-32`; `triage.py:1920-1928`, `:2143-2167`) | SOC backend suite and shared J6 persistence tests |
| SOC triage state-only capture | Non-scorable and guarded-update branches (`triage.py:1916-1955`, `:2069-2172`) | SOC triage/outcome tests; no change to routing action semantics |
| Graph schema/writer identity metadata | AGE/SQLite/InMemory Protocol V2 implementations (`protocol.py:216-303`) | Store conformance, idempotency, outbox, and graph integration tests |

Cross-repo verification order: SDK targeted tests, SOC tests, S2P tests,
Trading tests, Purchasing tests, DataOps tests, CI tests, then the SDK full
suite. A new failure in a downstream proxy or adapter is a release blocker.

## 11. Open Questions

1. Should startup centroid snapshots use the existing `CentroidCheckpoint`
   label with `metadata.capture_reason`, or should JM add a separate
   `StateSnapshot` label? The existing schema requires category/action fields
   (`judgment_memory_v2_7.md:320-325`), while startup has no decision event.
2. Should conservation startup captures add an explicit `capture_reason` field
   to the protocol, or is a deterministic `status_id` plus policy-version
   suffix sufficient? The current protocol has no metadata argument
   (`protocol.py:228-241`).
3. What minimum compatible verified-vector count makes a fingerprint eligible
   for validated warm-start? The current calculator uses five as its
   insufficient-data cutoff (`fingerprint.py:21-45`), but transfer validation
   may require a stronger domain policy.
4. Does the SOC graph contain enough compatible factor vectors in its verified
   decisions to make a startup fingerprint useful? This requires a live graph
   read; source inspection alone cannot prove it.
5. Should warm-start's legacy `save_centroids()` call also emit a V2 checkpoint,
   or should warm-start remain a separate event class? Current warm-start writes
   only the legacy method (`scorer.py:1320-1335`).
6. How should startup state captures be retained and displayed in global IKS
   trajectories without confusing them with decision-caused learning events?

## Read Log / Evidence Index

* Shared scorer lifecycle and all J6 writers: `copilot-sdk/copilot_sdk/scoring/scorer.py:548-770`, `:772-1128`, `:1200-1349`, `:1428-1488`, `:1558-1635`.
* Protocol V2 artifact contract: `copilot-sdk/copilot_sdk/graph/protocol.py:165-350`.
* Fingerprint calculation and transfer sufficiency: `copilot-sdk/copilot_sdk/scoring/fingerprint.py:21-95`; `copilot-sdk/copilot_sdk/backend/transfer.py:101-165`.
* Startup restore: `copilot-sdk/copilot_sdk/scoring/startup_restore.py:14-49`, `:58-140`, `:206-226`.
* SDK startup callers: `copilot-sdk/apps/trading/backend/app/main.py:303-390`; `copilot-sdk/apps/purchasing/backend/app/main.py:433-480`; `copilot-sdk/apps/dataops/backend/app/main.py:534-583`; `s2p-copilot/backend/app/main.py:134-195`.
* Proxy delegation: `copilot-sdk/copilot_sdk/backend/scorer_proxy.py:16-76`, `:86-132`; `copilot-sdk/apps/trading/backend/app/services/regime_scoring.py:20-31`.
* S2P receipt and learn paths: `s2p-copilot/backend/app/routers/s2p.py:76-94`, `:1335-1405`, `:2068-2166`, `:2169-2290`.
* SOC initialization, adapter, and non-scorable/scorable paths: `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py:186-302`; `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py:15-115`; `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py:1912-1955`, `:1995-2172`.
* JM schema, edge labels, and conservation semantics: `copilot-sdk/docs/design/judgment_memory_v2_7.md:296-340`, `:343-375`, `:425-465`, `:905-919`.

READY_FOR_IMPLEMENTATION: YES
GAP_COUNT: 3 Type A artifacts (conservation, fingerprint, checkpoint); all five have the startup gap, with additional fingerprint/checkpoint gaps on SOC special paths and fingerprint gaps on shared pause.
AFFECTED_COPILOTS: SOC, S2P, Trading, Purchasing, DataOps
FILES_TO_CHANGE: `copilot-sdk/copilot_sdk/scoring/scorer.py`; `copilot-sdk/copilot_sdk/scoring/startup_restore.py`; `gen-ai-roi-demo-v4-v50/backend/app/domains/soc/scorer_adapter.py`; `gen-ai-roi-demo-v4-v50/backend/app/services/gae_state.py`; `gen-ai-roi-demo-v4-v50/backend/app/routers/triage.py`; corresponding SDK/SOC/S2P/Trading/Purchasing/DataOps/CI tests
