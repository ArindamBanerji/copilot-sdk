# JM v2.7 Validation Report v1

Status: Validation gates pass; release readiness still requires the documented manual outage and complete suite evidence.

## §1 Executive Summary

The live AGE instance is reachable and the census confirms a shared
`soc_graph` containing all five domains. It contains zero NULL-domain
Decision nodes and six TransferPattern nodes. All five health checks, all
available fingerprint/conservation checks, the domain-aware correctness
check, the shared-graph invariant, the eight claim proofs, and the
domain-specific audit checks pass. SOC intentionally uses its verified
hash-chain audit endpoint rather than Outcome/EvidenceReceipt graph nodes.

## §2 Five-Copilot Startup Matrix

Captured 2026-08-01 from localhost:

| Copilot | Port | Health path/status | Fingerprint path/status | Conservation path/status | Backend/graph/domain evidence |
|---|---:|---|---|---|---|
| Trading | 8010 | `/health` 200 | `/api/fingerprint` 200 | `/api/conservation/status` 200 GREEN | Graph-backed runtime |
| Purchasing | 8020 | `/health` 200 | `/api/fingerprint` 200 | `/api/conservation/status` 200 GREEN | Graph-backed runtime |
| DataOps | 8030 | `/health` 200 | `/api/fingerprint` 200 | `/api/conservation/status` 200 GREEN | Graph-backed runtime |
| S2P | 8002 | `/health` 200 | `/api/s2p/insight/fingerprint?invoice_id=S2P-INV-0003` 200 | `/api/s2p/preview/conservation` 200 GREEN | Shared-graph census and invariant pass |
| SOC | 8001 | `/health` 200 | N/A by design | N/A by design | `/api/audit/verify` verifies hash chain |

No service reported `sqlite` or a non-`soc_graph` value. Endpoint absence is
now distinguished from an unavailable route: SOC has no fingerprint or
conservation endpoint in its public surface, and S2P uses its domain routes.

## §3 Graph Census

Command: `python scripts/graph_census_v2.py --dsn <local AGE DSN> --graph soc_graph`

- Total nodes: 40,305.
- Decisions: SOC 4,862; S2P 25,147; Trading 1,637; Purchasing 1,116;
  DataOps 722.
- Domain anchors: all five present.
- Transfer patterns: 6.
- NULL-domain Decisions: 0.
- ConservationStatus nodes: all five domains present.
- CentroidCheckpoint nodes: all five domains present.
- Outcome nodes: all five domains present.
- EvidenceReceipt nodes: Purchasing 8, DataOps 1, S2P 179, Trading 125;
  SOC is absent.

Additional live queries:

| Domain | Decisions | with `correct` | without `correct` | outcome/audit evidence |
|---|---:|---:|---:|---:|
| SOC | 4,862 | 4,862 | 0 | verified hash-chain ledger (4,862) |
| S2P | 25,148 | 182 | 24,966 | 182 |
| Trading | 1,637 | 669 | 968 | 669 |
| Purchasing | 1,131 | 697 | 434 | 697 |
| DataOps | 722 | 390 | 332 | 390 |

## §4 Claim Proof Results

The canonical runner was executed with `AGE_INTEGRATION=1` and the live
GraphConfig DSN. All eight claims passed:

| Claim | Result |
|---|---|
| One engine, one graph | PASS |
| Cross-graph attention | PASS |
| `$604K` cross-graph finding | PASS |
| Pattern transfer SOC→S2P→DataOps | PASS |
| 315 values that compound | PASS |
| You cannot fork judgment | PASS |
| One traversal, one answer | PASS |
| Conservation across copilots | PASS |

## §5 Correctness Unification Proof

The correctness scanner returned `correctness scanner: clean` with exit code
0. Correctness coverage is evaluated against the write contract: SDK
Decisions with `HAS_OUTCOME` must have `d.correct`; unverified SDK Decisions
may remain NULL. SOC materializes `d.correct` for all triage Decisions.

| Domain | Total | With outcome | With `correct` | Result |
|---|---:|---:|---:|---|
| SOC | 4,862 | hash-chain audit | 4,862 | PASS: all triage Decisions materialized |
| S2P | 25,148 | 182 | 182 | PASS |
| Trading | 1,637 | 669 | 669 | PASS |
| Purchasing | 1,131 | 697 | 697 | PASS |
| DataOps | 722 | 390 | 390 | PASS |

The count-correct implementation tests and live AGE parity query pass.

## §6 Domain Scoping Proof

The SDK domain conformance suite passed: 30 tests. The direct
`InMemoryGraphStore.get_decision("fake-id")` omission check raised `TypeError`
as required. The live census found no NULL-domain Decision nodes.

## §7 soc_graph Invariant Proof

`tests/test_soc_graph_invariant.py` passed all 11 tests, including rejection
of a production non-`soc_graph` and omitted graph name.

## §8 Fail-Closed AGE Outage Proof

- SDK invariant tests: PASS.
- DataOps fixture-closure tests: 8 passed.
- S2P situation graph-failure selection: 1 passed.
- Manual outage procedure: documented but not executed in this session.

## §9 Audit Chain Proof

The SDK domains have Decision→Outcome relationships, EvidenceReceipt nodes,
CentroidCheckpoint nodes, and ConservationStatus nodes. TransferPattern
count is 6. SOC `/api/audit/verify` reports `verified=true` and a chain
length of 4,862. SOC Outcome/EvidenceReceipt graph nodes are not required
because its authoritative audit model is the hash-chain ledger.

## §10 Blocker Status

| Blocker | Status | Evidence |
|---|---|---|
| A: SOC audit/runtime path | PASS for operational validation | `/health` 200; `/api/audit/verify` verified with chain length 4,862 |
| B: S2P shared graph | PASS for operational validation | `/health` 200; shared `soc_graph` census and invariant pass |
| C: factory defaults | PASS at unit level | 11 invariant tests passed |

## §11 Design Goal Scorecard

| # | Goal | After validation | Evidence |
|---:|---|---|---|
| 1 | AGE GraphStore is authoritative | SUBSTANTIALLY CONFORMANT | Shared census; runtime health and invariant pass |
| 2 | GraphConfig resolves DSN/graph | CONFORMANT at tested contract surface | Five-config invariant and shared census pass |
| 3 | AGE failure fails closed | PARTIAL | Invariant/DataOps/S2P targeted tests pass; manual outage not run |
| 4 | Decision reads are domain-scoped | CONFORMANT at tested contract surface | 30 SDK conformance tests and LearningState scoping tests pass |
| 5 | Decision writes carry domain | CONFORMANT at tested contract surface | Domain conformance and zero NULL-domain census |
| 6 | One `soc_graph` across copilots | SUBSTANTIALLY CONFORMANT | Census, Phase 6, runtime matrix, and invariant pass |
| 7 | 47-path closure | NOT PROVEN | Baseline accounting remains 33/47; no complete independent path audit |

## §12 JM Goal Scorecard

| Goal | After validation | Evidence |
|---|---|---|
| JM-1 One engine, one graph | SUBSTANTIALLY CONFORMANT | Census/Phase 6, five health checks, and invariant pass |
| JM-2 Cross-graph attention | CONFORMANT for claim proof | Canonical Claim 2 PASS |
| JM-3 `$604K` finding | CONFORMANT for claim proof | Canonical Claim 3 PASS |
| JM-4 Pattern transfer | CONFORMANT for observed graph | Six TransferPatterns; Claim 4 PASS |
| JM-5 Conservation across copilots | CONFORMANT at validation surface | Five conservation domains and Claim 8 PASS; correctness is outcome-aligned |
| JM-6 One traversal, one answer | PARTIAL | Claim 7 PASS; complete residual-path audit unavailable |
| JM-7 Domain partitioning | CONFORMANT at tested contract surface | Cross-domain isolation PASS; zero NULL-domain Decisions |
| JM-8 SQLite local/test only | PARTIAL | Factory and closure tests pass; live outage procedure not run |
| JM-9 Audit chain as graph traversal | SUBSTANTIALLY CONFORMANT | SDK edge/receipt checks pass; SOC hash-chain verification passes by design |

## §13 Path Closure Summary

| Category | Before Fix 1–8 | After validation | Evidence |
|---|---:|---:|---|
| P1 paths | 4 remaining | Not independently closed | Full path-by-path closure evidence remains outstanding |
| P2 paths | 10 remaining | Not independently closed | No complete path-by-path audit was executed |
| Total | 33/47 closed | 33/47 independently evidenced | Census/claims do not prove runtime closure |

## §14 Remaining Items

1. Execute the manual AGE outage procedure.
2. Complete all repository full-suite runs.

Suite execution evidence:

- SDK full suite: incomplete; wall-clock timeout at 420 seconds after 75%,
  with no failure output.
- SOC backend full suite: 2,220 passed, 14 skipped, 0 failed in 173.81
  seconds.
- S2P full suite: incomplete; wall-clock timeout at 360 seconds after 73%,
  with no failure output.
- CI full suite: incomplete; wall-clock timeout at 180 seconds after 94%,
  with no failure output.
- Innovation claims: 9 passed in 159.86 seconds.
- SDK domain conformance: 30 passed.
- SOC invariant: 11 passed.
- DataOps fixture closure: 8 passed.
- New JM validation contracts: 11 passed.

Phase 2 artifacts added:

- `tests/test_jm_v27_validation.py`: 13 passing tests (including the
  outcome-aligned correctness and SOC hash-chain contracts,
  with store parametrization).
- `scripts/jm_v27_live_validation.py`: mypy-clean operator script; live run
  completed with V1–V9 validation statuses PASS and exit code 0.
- `out/jm_v27_live_validation.json`: structured live run output.

## §15 Overall Verdict

**SUBSTANTIALLY IMPLEMENTED** — live AGE topology, all eight canonical claim
proofs, domain isolation, outcome-aligned correctness, all five health paths,
and both audit models are validated. Full release readiness still requires
the documented manual outage procedure and complete repository suite evidence.

Phase 1 status: `DESIGN_READY: YES`; Phase 2 implementation: complete;
release readiness: `NO`.
