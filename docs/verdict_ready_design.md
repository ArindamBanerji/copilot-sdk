# Platform dump READY design

Date: 2026-10-20. Investigation and design only; no runtime code, graph data, or verdict rules changed.

## 1. Investigation findings

### Evidence and conclusion

The four blockers have two underlying defects and one already acknowledged limitation. **Do not add SOC conservation, fingerprint, or anchor exemptions.** SOC already implements those writes. Its legacy outcome vocabulary makes the SDK discard its verified rows. DataOps lacks receipts because the active direct seed writer bypasses the receipt-producing learning path. Keep the existing SOC receipt limitation, repair the two defects, and leave `_check_integrity()` and `_compute_verdict()` unchanged.

Read the SDK session log, including FIX-PRESEED-PROFILE, and the SOC implementation containing the recent PRESEED changes. Those changes fix SOC learning permission/counts; they do not fix the SDK artifact projection discussed here.

The archived `out/platform_dump_20261020_183034.json` and a fresh read-only `run_census(GraphConfig.load("soc").dsn, ...graph)` both report the following. The live census had no errors.

| Domain | Decision | ConservationStatus | CentroidCheckpoint | Fingerprint | EvidenceReceipt | Domain anchor |
|---|---:|---:|---:|---:|---:|---|
| soc | 211 | 0 | 218 | 0 | 0 | absent |
| s2p | 303 | 108 | 212 | 5 | 206 | present |
| trading | 255 | 57 | 112 | 2 | 55 | present |
| purchasing | 345 | 40 | 78 | 2 | 38 | present |
| dataops | 200 | 1 | 2 | 1 | 0 | present |

The user-facing CP=50 figures are not census totals. `print_summary()` uses backend `/api/diagnostics.graph_artifacts`, whose checkpoint list can be capped. The verdict uses census rows independently. Do not infer missing-domain identities from printed summary counts alone.

### Gate-by-gate root causes

**all_conservation — SOC only, zero snapshots: compatibility bug.**

1. SOC `backend/app/routers/triage.py:2102,2169` passes `outcome="correct"` or `"incorrect"` to its GraphStore outcome writer.
2. `ci-platform/ci_platform/graph/age_graph_store.py` assigns canonical decision `status="confirmed"`/`"overridden"` from correctness, while retaining the supplied outcome. `get_verified_decisions()` selects canonical statuses; `_merge_decision_outcome()` retains the decision's legacy outcome.
3. SDK `copilot_sdk/scoring/scorer.py:3543`, `_is_verified_decision()`, rejects any explicit outcome other than `confirmed`/`overridden`. It consults `is_correct` only when outcome is absent.
4. SOC does use `SOCCompoundingScorerAdapter`, wrapping `CompoundingScorer.from_preset("soc")`. `gae_state.init_learning_state():356` calls `capture_existing_state(capture_reason="startup_restore")`. Its conservation capture reads the SDK-filtered verified population. With zero eligible rows, `_capture_conservation_state()` returns None and writes nothing.
5. Successful SOC profile updates also call `_persist_learning_artifacts()` from `triage.py:2661`. Its conservation snapshot uses SDK metrics; an empty eligible population can produce a cold-start nonfinite threshold and the explicit skip in `_persist_conservation_snapshot()`. This path does not repair the incompatible read vocabulary.

Live confirmation: grouping `Decision` by status/outcome returned **211 `confirmed` / `correct`**. A read-only probe loaded the real Decision/Outcome properties, applied the existing AGE `_merge_decision_outcome()`, and ran the SDK predicate: **211 rows in, zero eligible**. Changing only each copied row's legacy outcome to its canonical status yielded **211 eligible**. No graph writes were made.

SOC `LearningHealthMonitor.evaluate()` is a separate conservation implementation. Its normal L5 writer calls `update_conservation_state()`, not the V2 `write_conservation_status()` counted by this census. The PRESEED early return deliberately skips L5 persistence. Neither fact justifies ignoring the broken, already implemented V2 capture.

**all_fingerprints — SOC only, zero fingerprints: same compatibility bug, with a deliberate hot-path optimization.**

Startup capture calls `fingerprint(persist=False)`, then persists only if at least five compatible decisions were analyzed (`scorer.py:2034`). All SOC rows are currently filtered out before analysis. The successful triage update passes `skip_history_scan=True`, explicitly avoiding the expensive fingerprint scan on each outcome; startup/state capture is the existing alternative. In the read-only normalization probe, `compute_fingerprint()` analyzed **211 rows, skipped 0, six factors**. The raw AGE vectors are JSON strings, but `_node_to_dict()` already decodes `factor_vector`; no new decoder is needed.

This is not an absent SOC capability: `scorer_adapter.py:126` explicitly delegates state capture, and `backend/tests/test_j6_state_capture.py` explicitly expects SOC conservation and fingerprint writes. Existing tests seed canonical outcomes and therefore miss this production legacy vocabulary.

**all_anchors — SOC only, absent: downstream effect of the missing V2 summaries.**

`ci-platform/ci_platform/graph/age_graph_store.py:1688`, `_ensure_domain_anchor()`, looks up a domain and creates it only if absent. `_link_domain_summary()` invokes it for conservation/fingerprint summaries. Governed decisions and transfer links also have anchor paths. Domain names are passed in; there is no four-domain hardcoded exclusion.

SOC's custom decision/outcome route and legacy/L5 checkpoints are not sufficient evidence that a governed decision or summary link was created. The 218 checkpoint nodes coexist with no SOC anchor. Restoring the existing SOC summary writes creates the anchor through the supported writer, including retry on an already existing summary. An independent anchor-only seed would fix one symptom while leaving both missing summaries unexplained.

**all_receipts — SOC and DataOps, both zero: two different causes.**

- **DataOps: direct-preseed artifact omission.** Active orchestration in `demo.py:953` uses `scripts/seed_all_decisions.py`, not the deprecated HTTP seed script. That writer uses stable governed Decision IDs and `write_outcome()`, but never calls `append_evidence_receipt()`. It also immediately continues past an existing outcome. Startup replay/state capture intentionally does not invent new learning receipts. Live DataOps rows have `seed-dataops-*` IDs and `source="demo_preseed"`; all 200 decisions have outcomes. The DataOps app mounts the normal SDK scoring router, so the capability exists. Fresh seeds of the other SDK domains have the same latent gap, even though later learning has supplied receipts in this snapshot.
- **SOC: existing architectural limitation.** SOC mounts custom triage routes, not SDK scoring/conservation router factories. Its successful-update bridge explicitly passes `evidence_already_persisted=True`, so SDK receipt creation is suppressed. No `append_evidence_receipt`/`EvidenceReceipt` writer exists in `backend/app`; SOC's feedback/audit and canonical Outcome records are separate contracts. `test_j6_state_capture.py` explicitly asserts state capture creates no receipts. The flag name is misleading and does not establish that a V2 receipt exists. Retaining the already documented exemption acknowledges an unfinished receipt integration; it is not a claim that SOC has equivalent V2 evidence.

The current receipt exemption activates only when **all four non-SOC domains have receipts**. DataOps's gap correctly prevents it from activating today.

### Mandatory dump/census code inventory

Read `platform_dump.py`, `graph_census_v2.py`, `conservation_router.py`, and `scoring_router.py` in full.

Every census query uses `SELECT * FROM cypher(graph, $$ ... $$)` with agtype result columns:

| Section | Cypher body |
|---|---|
| DECISIONS PER DOMAIN | `MATCH (d:Decision) RETURN d.domain AS d_domain, count(d) AS cnt` |
| CONSERVATION SNAPSHOTS PER DOMAIN | `MATCH (cs:ConservationStatus) RETURN cs.domain AS d_domain, count(cs) AS cnt` |
| CHECKPOINTS PER DOMAIN | `MATCH (cp:CentroidCheckpoint) RETURN cp.domain AS d_domain, count(cp) AS cnt` |
| TRANSFER PATTERNS | `MATCH (tp:TransferPattern) RETURN count(tp) AS cnt` |
| DOMAIN ANCHORS | `MATCH (d:Domain) RETURN d.domain_id AS d_id, d.name AS d_name` |
| DOMAIN CONTEXT ENTITIES | `MATCH (dc:DomainContext) RETURN dc.entity_type AS etype, count(dc) AS cnt` |
| FINGERPRINTS PER DOMAIN | `MATCH (f:Fingerprint) RETURN f.domain AS d_domain, count(f) AS cnt` |
| EVIDENCE RECEIPTS PER DOMAIN | `MATCH (r:EvidenceReceipt) RETURN r.domain AS d_domain, count(r) AS cnt` |
| OUTCOMES PER DOMAIN | `MATCH (o:Outcome) RETURN o.domain AS d_domain, count(o) AS cnt` |
| EVOLUTION EVENTS PER DOMAIN | `MATCH (e:EvolutionEvent) RETURN e.domain AS d_domain, count(e) AS cnt` |
| TOTAL NODE COUNT | `MATCH (n) RETURN count(n) AS total` |

`EXPECTED_DOMAINS={"soc","s2p","trading","purchasing","dataops"}`. `run_census()` returns `{graph_name, sections: {title: [tuple, ...]}, errors: [string, ...]}`. It loads AGE, sets search path and 120s statement timeout, records an empty section plus error on query failure, and continues. Connection failure escapes to the dump collector.

`_check_integrity()` requires positive counts for every expected domain for decisions, conservation, checkpoints, fingerprints and receipts; anchors require membership of every domain ID. Transfer count must be positive; monetary count sums DomainContext entity types `sap_change`, `celonis_process`, `operations_context`. It returns these checks and the underlying count maps/anchors; transfer/monetary keys ultimately contain numeric counts. Outcomes, evolution events and total nodes are informational.

`_compute_verdict()` blocks on failed decisions, conservation, anchors and fingerprints. Receipts block except the narrow SOC-only absence described above. Missing checkpoints become `<domain>:checkpoints` expected limitations, not blockers. Zero transfers/monetary entities become pending operations. READY means the blocking list is empty; it does not mean conservation is GREEN or every future capability is implemented.

`collect_platform_state()` combines timestamp/graph identity, AGE reachability/total count from one census, five health/diagnostics HTTP probes (validated with DiagnosticsResponse), a second census, integrity and verdict. Collection failures are isolated. Backend health errors themselves are not separate verdict blockers. `print_summary()` reads D/C/CP/F/R from each diagnostics payload and conservation status from diagnostics; it prints the census-derived verdict categories.

### Actual write triggers and preseed coverage

The conservation router is read/computation only: GET `/conservation/status` returns a materialized payload or `build_conservation_status()`; POST `/conservation/what-if` computes a hypothetical result. Neither writes AGE or uses a GraphStore write method.

The scoring router's POST `/score` persists a decision. POST `/learn` invokes `CompoundingScorer.learn()`, which persists evidence and then learning artifacts, including V2 conservation/fingerprint/checkpoint data. The router separately invokes L5 `update_conservation_state()`, `update_centroid()` and DK persistence. A blocked/paused learn does not have the same artifact guarantees as successful learning. GET `/fingerprint` explicitly uses `persist=False`; GET diagnostics/trajectory are not artifact backfills.

`_persist_evidence_receipt()` calls `append_evidence_receipt()` with a post-outcome payload and a UUID-bearing intent; do not call it repeatedly as an idempotent seed repair. `_persist_fingerprint()` uses a content hash ID; conservation capture uses a content hash ID; the AGE writers reject conflicting IDs and link summaries to Domain anchors. AGE receipt appends serialize by domain, return the existing receipt for identical intent/payload, and reject conflicts or a corrupt chain.

| Domain | Deprecated HTTP `preseed_all_copilots.py` phases | Active direct/lifecycle path | Artifact implication |
|---|---|---|---|
| trading | health/trajectory check; deterministic score+learn; trade metadata; verify trajectory/fingerprint; optional regime backfill, fixtures/heroes | direct 200 decisions/outcomes; app startup restore/capture; optional scenarios | successful HTTP learn can write C/F/R; direct seed has no R; capture writes C/F |
| purchasing | same score+learn cycle; order metadata; optional fixtures/heroes | same direct seed and startup capture | same latent receipt gap |
| dataops | same score+learn cycle; alert metadata; optional evolution/investigation fixtures | same direct seed and startup capture | observed seed-only population explains C=1/F=1 but R=0 |
| s2p | separate `seed_s2p_domain`: `/api/s2p/score` then `/api/learn`; health/trajectory fallbacks; optional heroes | direct deterministic invoices/decisions/outcomes; local app restore/capture and custom learning route | current R>0 does not mean direct seed writes receipts |
| soc | no live HTTP SOC section; only `--offline` delegates all five to DemoPreseed on a shared memory graph | separate SOC script: graph alert fixtures, kill-chain fixtures, AE events, twin freeze -> 30 PRE outcomes -> re-freeze -> 60 POST outcomes/comparison, then failure/checkpoint scenarios | custom analyze/outcome endpoints; no SDK receipt route; state captures encounter legacy outcome filter |

No listed HTTP phase calls a conservation GET as a persistence trigger. Fingerprint verification GET is read-only. `preseed_all_copilots.py --force` appends data, so it is not a safe idempotent repair. Its offline memory mode does not repair live AGE.

DataOps `apps/dataops/backend/app/main.py:815` calls `auto_seed_domain_if_empty()` then `restore_l5_runtime_state()`. Trading/Purchasing use the same pattern. S2P imports the shared conservation router but replaces its status GET with its local materialized view. SOC source and the ci-platform implementation were accessible; no architectural inference rests on an inaccessible file.

## 2. Options evaluated

Estimates are focused coding/test time, excluding full-suite runtime.

| Gate | Option and files/pattern | Effort | Risk and correctness |
|---|---|---|---|
| conservation | Add SOC-only exemption in `platform_dump._compute_verdict()` using receipt exemption structure | 15–25 min | Reject: masks a reproduced eligibility bug and contradicts SOC capture tests |
| conservation | Normalize legacy outcome only in SOC's verified-row projection, then existing startup capture | 35–55 min | Recommended: isolated compatibility repair, no stored outcome rewrite; affects actual SOC SDK metrics/replay and must be tested |
| conservation | Broaden SDK predicates in scorer and conservation_utils to accept legacy values globally | 40–60 min | Viable but wider five-domain semantic change; requires all eligibility implementations to agree |
| conservation | Seed a hardcoded snapshot or call status GET | 10–20 min | Reject: fabricated state or no write; does not restore computation |
| anchors | Exempt absent SOC anchor in verdict | 15 min | Reject: all-domain topology is intended; supported summary writers already create it |
| anchors | Independent idempotent anchor initialization in ci-platform/seed tooling | 30–45 min | Viable for general topology initialization, but an extra public persistence contract or backend-specific call is unnecessary here |
| anchors | Let repaired SOC C/F writers call `_link_domain_summary()` | Included above | Recommended: real summaries and links, no direct private anchor calls or new dependency |
| fingerprints | SOC-only exemption | 15–25 min | Reject: hides existing, tested SOC fingerprint capability |
| fingerprints | Repair SOC verified projection, use existing startup capture | Included above | Recommended; live probe proved enough compatible vectors |
| fingerprints | Enable fingerprint history scan on every SOC outcome or explicitly capture at end of preseed | 25–45 min | Viable refresh enhancement, but enabling scans adds latency; neither fixes vocabulary without normalization |
| receipts | Extend exemption to DataOps or all directly seeded domains | 15–25 min | Reject: normal SDK learning supports receipts; hides a seed integration omission |
| receipts | Append deterministic, truthfully labeled synthetic seed receipts in direct seed writer | 40–55 min | Recommended for all four SDK domains; handles repair/resume without learning twice |
| receipts | Restore HTTP score/learn seeding | >1 hour | Reject for this plan: changes startup performance/gate behavior, retries can duplicate decisions, deprecated path is not idempotent |
| receipts | Add SOC native receipt writes at successful outcome commit | >1 hour including transaction tests | Legitimate future work, but changes mature outcome transaction/retry semantics and the existing architectural limitation; not required for READY |

Minimal direct-seed receipts must attest synthetic seed outcome ingestion, not human verification or an SDK learner invocation. Use the protocol API, not raw receipt CREATE statements. No new dependency is necessary.

## 3. Recommended strategy

1. Add an explicit `get_verified_decisions()` compatibility method on SOC `GraphStoreAdapter`, with the underlying method's pagination/order/cursor arguments. Delegate through its existing serialized read helper, copy rows, and for domain SOC only normalize legacy `correct`/`incorrect` outcomes to the already canonical verified `status`. Require consistency with non-null boolean `is_correct`; leave canonical outcomes intact and reject or visibly exclude inconsistent/unknown records rather than promoting them. Preserve raw stored data and write_outcome behavior. No global SDK filter change.
2. Repair direct seed receipt coverage for all four SDK domains. Append after a new outcome and also for a matching existing seeded outcome before the current `continue`. Use a stable versioned intent such as `demo_preseed:v1:<domain>:<decision_id>:outcome`, a deterministic payload derived from the persisted seed decision/outcome, and explicit sample/T-sim provenance. Do not include current time/random IDs in the hashed payload. Verify seed identity/metadata before repairing an existing row; never attest an unrelated ID collision.
3. Run repair through the explicit direct seed CLI, then restart SOC using the established lifecycle so startup capture uses the normalized projection. Verify C/F/anchor creation and retained SOC receipt limitation. Repeated unchanged capture/receipt repair must not duplicate artifacts.

For automatic startup repair, the seed completion marker alone cannot prove receipts exist. Version its completion contract to include receipt completion, or introduce a separate artifact-completion marker. Allow old deterministic seed populations to repair receipts; retain `DEMO_NO_RESEED=1` and non-seed population guards. Existing mixed live populations can be repaired via explicit seed CLI, limited to validated deterministic seed IDs; do not change the automatic guard to reseed them.

Blast radius: one SOC adapter read surface; no triage response, write transaction, conservation formula, centroid update or frozen-twin code changes. SDK seed behavior changes only for explicit seed ingestion/eligible auto-seed repair. Tests must confirm persisted SOC `correct`/`incorrect` labels remain unchanged and non-SOC rows are untouched. Existing tests cannot guarantee compatibility until the added legacy fixtures pass.

No new verdict exemption is recommended. Keep `soc:evidence_receipts` as the one existing, explicit architectural limitation; this is acceptable for the diagnostic's current definition of READY, not a declaration of full SOC V2 audit compliance.

Downstream consumers found: `demo.py --dump` calls collection, writes JSON and prints it, then exits 0 even for NOT READY; `tests/test_platform_dump.py` checks category contracts. No runtime admission controller consuming the verdict was found in the searched Python/TypeScript/config sources. External JSON consumers are unknown. Preserving field names and categorization avoids a diagnostic contract change.

## 4. Implementation plan: three focused Codex prompts

### Prompt 1 — SOC verified-row compatibility (35–55 min)

**Task:** Read this design and SOC session state. Reproduce canonical status plus legacy outcome filtering with a read-only probe. Implement only the SOC adapter projection normalization described in section 3.

**Files:** SOC `backend/app/services/graph_store_adapter.py`; `backend/tests/test_j6_state_capture.py`; new focused `backend/tests/test_soc_verified_projection.py` if needed; SOC session log.

**Pre-checks:** inspect full delegated signature, active wrapper chain, and raw outcomes. Confirm the known predicate and five-row fingerprint threshold. Do not edit global SDK predicates or stored outcomes.

**Tests:** real InMemoryGraphStore wrapped in GraphStoreAdapter with faithful AGE-shaped legacy rows; correct and incorrect records, canonical outcomes, unknown/conflicting states, empty results, non-SOC passthrough, original-row immutability, pagination/cursor forwarding and exception propagation. Capture must create C/F from at least five compatible legacy rows. Run `test_scorer_adapter.py`, `test_j6_state_capture.py`, new adapter tests, and relevant L5 conservation tests; mypy changed production file. Request full SOC suite, recording any existing zero-day seed guard honestly rather than reseeding unrelated data.

**Post-check:** diff isolated; no writes during projection; no duplicate receipts introduced; both legacy and canonical rows retain correctness. Existing startup capture supplies C/F and anchor after restart. Expected verdict after applying only this prompt and capturing: NOT READY, only `all_receipts` remains.

### Prompt 2 — Deterministic direct-seed evidence receipts (40–55 min)

**Task:** In SDK read session state/design. Extend direct seed outcome ingestion and repair to append versioned synthetic evidence receipts through ProtocolV2GraphStore. Preserve public seed result fields and deterministic decisions/outcomes. Do not use the scorer's UUID receipt helper.

**Files:** `scripts/seed_all_decisions.py`, `tests/scripts/test_seed_all_decisions.py`, SDK session log.

**Pre-checks:** inspect receipt idempotency/hash contract, old completion marker fast return, existing-outcome continue, mixed-population guard, and DEMO_NO_RESEED.

**Tests:** four-domain fresh seed; second identical run has unchanged receipt chain/count; interrupted run after outcome but before receipt repairs on retry; existing old completion marker repairs; dry run writes nothing; unknown/non-V2 capability reports unsupported artifact persistence clearly; no receipt for unverified outcome or unrelated ID collision; corrupt/conflicting intent fails visibly; sample provenance remains T-sim. Validate auto-seed completion is published only after required receipts succeed. Test unchanged non-seed and no-reseed guards. Run seed tests plus existing preseed lifecycle tests and mypy.

**Post-check:** receipts derived from persisted outcomes, no arbitrary current-time fields, no duplicate learning or centroid mutation. Expected verdict with prompt 1/capture: READY. Without prompt 1, C/anchor/F still block; SOC-only receipt limitation activates.

### Prompt 3 — Acceptance regression and controlled application (20–40 min)

**Task:** Add acceptance fixtures derived from the observed census to SDK `tests/test_platform_dump.py`. Preserve both verdict and integrity implementations. Apply the two repairs through existing explicit seed/restart tooling in the authorized local demo environment, then collect a fresh dump.

**Files:** `tests/test_platform_dump.py`, session state, fresh dump artifact. No production code changes. Depends on prompts 1 and 2.

**Tests/pre-checks:** current census must yield four blockers; normalized SOC summaries/anchor plus DataOps receipts yield READY; missing any non-SOC receipt or any required C/F/anchor still yields NOT READY; SOC receipt absence alone yields the existing expected limitation; pending operations unchanged. Test raw integrity still reports `all_receipts=False`. Capture original counts before applying.

**Application/post-checks:** run explicit direct seed repair twice; confirm second pass preserves decisions/outcomes/receipt counts and chain consistency. Restart SOC through existing lifecycle and inspect capture results. Repeat unchanged capture/restart if practical to verify deduplication. Census must have no errors and must match the expected gate state; print diagnostics separately to avoid treating capped CP values as totals. Do not add transfer patterns, monetary entities, fabricated summaries or unrelated zero-day seed data.

Full-suite durations can exceed one hour (the SDK session log records a roughly 40-minute run). The estimates above cover focused implementation and targeted validation; full regression execution is an additional verification stage, not a reason to omit it or claim an unrun pass.

## 5. Expected final state and design checks

With an otherwise unchanged population:

| Domain | D | C | CP | F | R | Anchor |
|---|---:|---:|---:|---:|---:|---|
| soc | 211 | >=1 | >0 | >=1 | 0 | present |
| s2p | 303 | >0 | >0 | >0 | >0 | present |
| trading | 255 | >0 | >0 | >0 | >0 | present |
| purchasing | 345 | >0 | >0 | >0 | >0 | present |
| dataops | 200 | >0 | >0 | >0 | 200 new deterministic seed receipts | present |

Receipt counts in the other SDK domains can increase during seed repair. Exact C/F/CP totals depend on current state and capture timing; diagnostic CP may remain capped at 50. The acceptance criterion is genuine artifacts and idempotent repeat behavior, not these exact totals.

```text
VERDICT: READY
Expected Limitations: soc:evidence_receipts
Pending Operations: transfer_patterns, monetary_entities
```

The raw integrity remains `all_receipts=False`; all other required data gates are true. With only SOC missing receipts, the existing narrow receipt exemption applies. No checkpoint limitation remains for this population. Transfers and monetary entities remain zero and pending as the explicitly excluded future work (#15 SC-11–SC-16 and #8 D-CEL).

**Executed design verification:** copied the archived census in memory, added SOC C/F=1 and its anchor plus DataOps R=200, and called the unmodified `_check_integrity()` and `_compute_verdict()`. Result: `READY`, empty blocking list, exactly `["soc:evidence_receipts"]` expected limitations and the two pending operations. Negative cases restoring each C/anchor/F failure or removing DataOps receipts all returned NOT READY.

Post-checks 1–6: all four gate failures have traced causes and live supporting evidence; each has multiple evaluated options; no new exemption masks a writer bug; all relevant repositories were accessible; three bounded implementation prompts have tests/dependencies; remaining limitations/pending items are explicit. Layer 1: this documentation-only change cannot alter runtime/tests; proposed runtime changes and their coverage are identified above; schema/consumer compatibility is preserved; idempotency and failure visibility are acceptance gates. No claim is made that future implementation tests have already passed.
