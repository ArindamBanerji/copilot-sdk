# No-Amend Outcome Policy v1

## §1 POLICY STATEMENT

- Outcomes are write-once.
- `write_outcome()` is the sole writer of `d.correct` and `d.status`.
- It fires only when the Decision has `status = 'pending'`; the contract is already enforced.
- No `amend_outcome()` method exists or will be created.

## §2 CORRECTION MECHANIC

A correction is a re-triage: create a new Decision, score it, and write its outcome.
The superseded Decision is archived with `archived = true` and
`superseded_by = <new_decision_id>`. The superseded Decision therefore leaves V
through the existing archival guard. `count_verified` is unchanged as a total:
the old Decision drops out and the new Decision adds its replacement. The audit
chain shows the original and correction as separate events.

## §3 WHY NO-AMEND

The platform uses an append-only hash-chain audit. A hash-chain entry cannot be
amended; a correction is appended as a new event. An `amend_outcome()` method
would put the read model in tension with the audit chain. Immutability is the
correct trade for audit integrity. Product framing: corrections are appended
and traceable.

## §4 E3 SCANNER ENFORCEMENT

- The scanner bans `SET d.correct` and `SET d.status` mutations outside
  `write_outcome`.
- The ban is property-scoped to `d.correct` and `d.status`; it is not a blanket
  Decision-mutation ban.
- Re-triage archival mutations such as `SET d.archived` and
  `SET d.superseded_by` are legitimate and pass.
- The sole allowlist exception is `age_graph_store.write_outcome`, because
  `write_outcome` is the sole CQRS contract writer for `d.correct`/`d.status`
  per this policy.
- The SOC triage raw-Cypher path is retired; the scanner prevents regression.

## §5 REQUIRED TEST

`test_retriage_correction_preserves_counts` proves that a correction is a new
Decision and that archiving the superseded Decision preserves the verified and
correct-count invariants.

## §6 D5 REVERSAL NOTE

SOC now routes outcomes through `write_outcome` (the CQRS contract). This creates
Outcome nodes and `HAS_OUTCOME` edges for SOC, reversing the earlier D5 decision
that SOC audit was projection-based permanently.

The reversal is intentional and correct: routing SOC through the shared contract
is what made `count_correct` work uniformly. SOC's hash-chain audit
(`framework/audit.py` `record_outcome`) is preserved as a supplementary audit
mechanism called alongside `write_outcome`, not replaced by it.

Historical SOC Decisions (approximately 4,862 at the time of the CQRS change)
had `d.correct` set by the triage path but `d.status` was NULL. A one-time
status backfill (`scripts/backfill_soc_status.py`) sets `d.status` from
`d.correct` using the JM §5 lifecycle mapping:

- `d.correct = true` → `d.status = 'confirmed'`
- `d.correct = false` → `d.status = 'overridden'`

After the backfill, all SOC decisions have both `d.correct` and `d.status`.
The status-guarded count handles all rows uniformly; no mixed counting
topology exists.

New SOC decisions use `write_outcome`, which sets both `d.correct` and
`d.status` atomically. `count_correct` uses `d.correct` with a status guard,
so both historical (backfilled) and new rows are counted by the same predicate.
