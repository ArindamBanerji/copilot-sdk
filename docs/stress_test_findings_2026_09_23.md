# STRESS-TEST-FIX investigation — September 23, 2026

## Decision visibility and conservation (Phase 10)

The reported Trading discrepancy is exactly the archived population. The first
direct AGE inspection in this investigation returned:

| Domain | Active Decisions | Archived Decisions | Retained total | Active verified Decisions |
| --- | ---: | ---: | ---: | ---: |
| trading | 880 | 2,531 | 3,411 | 510 |
| purchasing | 852 | 1,744 | 2,596 | 416 |
| dataops | 1,037 | 1,419 | 2,456 | 401 |
| s2p | 801 | 26,945 | 27,746 | 488 |

`AGEGraphStore.get_all_decisions(domain)` filters only by domain and
`archived IS NULL OR archived <> true`. It has no creator, source, timestamp,
ID-prefix, verification-status or row-limit filter. The SDK adapter delegates
without adding a filter. Hexadecimal IDs do not identify a SOC writer; the SDK
also returned hexadecimal IDs during these live scoring requests.

The intended contract remains **all active Decisions in the requested domain,
across writers**. Archived history is retained and exposed by
`get_archived_decisions()`. Shared storage does not mean cross-domain read access
or automatic inclusion of archived history. A future "my decisions" view needs
an explicit authenticated creator field/filter, not an inferred ID prefix.

This is consistent with paper v13 §3.4 (shared graph enables linked evidence)
and §4.1–4.2 (verified active Decisions contribute to V; pending, archived and
preview Observations do not). The previously quoted Purchasing/DataOps/S2P API
counts were verified counts, not complete active inventories.

The protocol and AGE method docstrings now state the active-inventory contract.
Phase 10 compares active Trading inventory and each domain's verified count
against equivalent direct AGE predicates. Before/after reads bracket concurrent
changes rather than allowing an arbitrary five-percent mismatch. Preview queue
rows are verified by Decision ID; response dictionary keys are not row counts.

## Transfer traversal (Phase 7)

The original phase passed before changes on today's live stack. The earlier
typed `FROM_DOMAIN`/`TO_DOMAIN` product fix was already loaded. Six persisted
directed transfers exist: soc→s2p, soc→dataops, trading→purchasing,
s2p→trading, purchasing→dataops, dataops→s2p. Trading→s2p has no direct
transfer; its empty response is correct. No transfer was fabricated.

The old test covered only three of those six transfers, could retain `passed`
despite HTTP failures on other pairs, and used a nonexistent hardcoded Decision
ID. It now discovers all persisted pairs, compares exact pattern IDs, checks
specific-pattern queries and pair isolation, and exercises decision_movement
with an actual linked Decision. A broad untyped diagnostic edge lookup proved
slow and was replaced with a typed HAS_OUTCOME lookup.

## Concurrent scoring (Phase 8)

Initially all 40 requests returned validation rejections, yet the phase passed.
All three SDK payloads lacked category and used incorrect factor names. S2P
requires event_id, category, amount and supplier_id, with eight named factors
at the top level. The test now uses those public contracts. The learning probe
also now supplies actual_action, using the returned recommended action.

Rejections are reported, never counted as successful load. Each of 40 returned
IDs must be unique within its domain and present in that exact domain in AGE;
unrelated traffic cannot satisfy a persistence ratio. Any recorded failure
fails its phase. Conservation gates remain enforced: Trading learning was
blocked with HTTP 423, so this run does not demonstrate a successful update.

## Health identity (Phase 9)

The reported inconsistency did not reproduce before changes. All five live
copilots reported ready=true, graph_backend=age, graph_connected=true,
graph_name=soc_graph and identity `268fc3c2a353ab6b28a2e1be`. The historic
discrepant field cannot be identified without the failed run's responses.
The verifier now rejects missing/sentinel identities and wrong graph names;
five missing identities could previously count as agreement. Health identity
agreement is not proof of tenant authorization or semantic schema compatibility.

## Additional finding: centroid persistence (Phase 3)

The full run queried the nonexistent Centroid storage representation. Product
persistence uses CentroidCheckpoint. The verifier now counts checkpoints with
tensors and validates the latest tensor's domain-specific shape and finite
values, accommodating legacy ISO and numeric timestamps. Metadata-only
checkpoints cannot satisfy this test.

## Verification limits

The test writes tagged synthetic pending Decisions to the live graph. It does
not delete these records or relax conservation. Restart survival is explicitly
excluded by --skip-restart. These checks verify the listed contracts, not the
entire JM architecture. Nine unit regressions exercise false-pass prevention,
domain-specific persistence, archived inventory and missing health identities.

During sandboxed full runs, the S2P queue intermittently timed out at the
unchanged ten-second deadline; a separate probe also saw a connection reset.
Other probes returned in 0.3–0.6 seconds, and an instrumented full run passed.
The server logged HTTP 200 and no active database query was seen during an
observed wait. This does not establish a product root cause; verification
outside the sandbox is used to distinguish execution-environment interference.

Final verification: `python -u -X utf8 scripts/jm_stress_test.py --skip-restart`
completed outside the sandbox with **9/9 passed**, including 40/40 exact
concurrent score IDs persisted and all six directed transfer patterns matched.
The S2P queue returned five graph-verified rows within the existing deadline.
The passing run does not prove the cause of the earlier sandboxed timeouts.
Mypy passed for the script, regression tests, SDK protocol and AGE store;
the nine focused regression tests passed. No product runtime changes or service
restart were necessary; product changes only clarify enumeration docstrings.
