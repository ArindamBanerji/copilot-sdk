# Bounded consumer contracts — P3 (amended P3-FIX)

Date: 2026-10-15. Scope: design only. Authority: `design_fix_bounded_projections_v3.md`, shipped `graph/query.py` and `graph/protocol.py`, canonical `design_principles_v2.md`, and the inspected consumer implementations. This document supplements v3 §§2.2, 4.2 and Appendix A; it does not change the four generic methods.

## §1 Purpose and relationship to BoundedProjectionStore

### 1.1 Shipped state and limits of this review

BP-P1 and REV-P1 record implementation and PASS review. The actual source contains **six**, not seven, frozen slotted dataclasses: DecisionFilter, DecisionCursor, DecisionPageRequest, DecisionPageResult, DecisionAggregate, DecisionChangePage. There are four Literal aliases, two exceptions, and the optional BoundedProjectionStore protocol: 13 new package re-exports. Do not invent DecisionChange or restore obsolete fields from the abandoned IMPL-STORE-TYPES prompt.

The retained full-suite evidence is **4,545 passed, 1 xfailed, 0 failed**; the P1 review separately passed 62 contract cases and its mypy gate. These are recorded results, not tests rerun by P3. Earlier baseline arithmetic differs in session state; it must not replace the retained measured count. P2 implementation is not assumed shipped.

P1 defaults are page limit100, created_at descending, offset0; result items are tuples, without total_estimate. Filters use tuples and names confidence_min/max, created_from/to, verified_from/to, decision_ids/exclude_decision_ids. DecisionAggregate has dimensions and values. Changes use after_generation, not since_generation. as_of_generation is a current-generation fence, not an historical snapshot. All subsequent prompts use these real signatures.

### 1.2 Comprehension gate: architecture

**Scoring core.** Scorer owns replay, checkpoints, fingerprint, IKS, trajectory, conservation and evolution. Its verified helper and module helper have different callers and both occur in ledger49. Measurement counts actual-action arms; trust uses rank halves and category concentration; composite and enforced gates use different correctness normalizers and populations. Recent-window, full-history and benchmark-excluded populations are not interchangeable. Replay and arbitrary evolution callbacks cannot generally be replaced with finite moments.

**SDK backend.** Health and several counters already use scalars. History needs complete row fields and a separate count. Self-computation combines raw and verified records, sometimes filtering after a limited fetch; replacing that with global filtering changes results. Conservation baseline order differs from chronological conservation order. Switching cost examines three timestamp fields. Transfer APIs use two different monetary precedence policies. Response materialization/coalescing currently shares graph-derived data across requests and must be replaced atomically with request-local reads.

**Trading.** Decision analytics, pre-score similarity, stage-rank promotion, trader profiles and volatility statistics consume different subsets of factors, outcomes and nested metadata. Journal is a separate union of imported trades, manual records and Decisions, followed by annotations, normalization and source-precedence deduplication. Imported/process-memory and JSON writers are part of the migration, as are indirect journal consumers outside the ledger. Journal P&L and entry dates are not Decision confidence or creation dates.

**Purchasing.** Readiness uses counts, but auto-order excludes sample data and resolves nested categories. Evidence recomputes missing factors and selects valid recent records; proof curves use every prefix. Supplier IKS and scorecards have different supplier resolution and price windows. PAR requires real item/date quantities across history, sample rejection and population mean/standard deviation; a count of decisions is not an order history. QBO/vendor facts retain their own provenance.

**DataOps.** Context projections normalize system/action/correctness differently from generic Decision fields. Accuracy includes pending decisions, with per-category rank halves. Pipeline/schema/transformation queries need exact domain predicates. Source trust counts per-factor and per-source observations and compares a specific prior fingerprint; DK tensor weights are not fingerprint weights. RSI reads several graph fact types plus a labeled curated timeline. The current 60-second graph-result cache is in scope for removal.

**Other SDK.** Projection category/profile methods mix a capped category cohort with all-history scalars. Weekly reports anchor to the latest active creation timestamp and allow arbitrary cost callbacks. DI allows arbitrary grouping/metric callbacks and source-ID sets; those need registered bounded reducers or explicit offline work. Read-diff, backups, export and migration need complete active and archived evidence. Demo restore and outcome counts already have bounded point/scalar paths.

### 1.3 Access inventory and categories

The complete 122-row gate inventory is §5, including existing methods and the generic-versus-supplemental decision. Additional discovered caller sites are §5.2. Categories are: coherent counts; ordered windows/rank statistics; fingerprint moments; actual-action arms; prefix curves; monetary/domain reductions; bounded domain rows and point lookups; journal facts/annotations; and complete offline traversal.

Do not extend GraphStore or ProtocolV2GraphStore. Supplemental capabilities are optional structural protocols, implemented completely by a store before its selected wrapper variant advertises them. No NotImplementedError membership stubs, __getattr__ capability leakage, or catch-and-fallback full scans. Tenant → legacy → adapter → primary and bounded namespace composition apply to every new method, including tombstones, journal facts and exports. Production graph identity checks remain intact.

### 1.4 Governing invariants

All platform records and read execution stay on the same governed graph primary. Manual trades, imports, annotations, supplier observations and market observations are graph facts, not fabricated verified Decisions. No SQLite, secondary query store, graph-serving cache, outbox reader, or shadow reasoning substrate is introduced. Memory is a contract reference only. External market/QBO adapters may supply observations with provenance; persisted observations go through GraphStore before reuse. User-visible fixture data remains labeled fixture data.

Conservation alpha*q*V, scorer geometry, learning, trust thresholds and rounding are frozen. Existing formula-only modules remain untouched. An adapter supplies sufficient statistics to an access-layer evaluator; it must not fabricate Decision rows to trick a list-based function. Reference functions remain parity oracles. Changes to legacy population/order are separately versioned as specified below, never hidden in a storage optimization.

## §2 Read-model sufficient statistics

### 2.1 Common typed contracts, consistency and bounds

The following blocks form one normative Python specification in future `copilot_sdk/graph/domain_queries.py`. All data classes are frozen with slots. Optional fields are optional only where explicitly shown. No untyped metric bag or executable callback crosses the graph boundary. Profile names and field schemas are closed registries in §2.3; an unknown name/parameter/result field is an error.

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Protocol, TypeAlias, runtime_checkable
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.graph.query import DecisionFilter, DecisionProjection

Scalar: TypeAlias = str | int | float | bool | None
StatisticsProfile: TypeAlias = Literal[
    "counts_v1",
    "baseline_v1",
    "conservation_v1",
    "checkpoint_quality_v1",
    "fingerprint_v1",
    "scorer_iks_v1",
    "measurement_v1",
    "trust_v1",
    "composite_v1",
    "gate_v1",
    "profile_v1",
    "profile_v2",
    "switching_age_v1",
    "transfer_router_v1",
    "cross_domain_v1",
    "shadow_coverage_v1",
    "trading_context_v1",
    "claim_gate_v1",
    "trading_analytics_v1",
    "vol_sharpe_v1",
    "vrp_v1",
    "regime_vrp_v1",
    "dispersion_v1",
    "prescore_regime_v1",
    "regime_classifier_v1",
    "trading_regime_v1",
    "conditioner_v1",
    "promotion_v1",
    "trader_profiles_v1",
    "purchasing_auto_v1",
    "purchasing_evidence_v1",
    "supplier_iks_v1",
    "supplier_scorecard_v1",
    "purchasing_orders_v1",
    "par_v1",
    "dataops_accuracy_v1",
    "dataops_pipelines_v1",
    "schema_impact_v1",
    "transformations_v1",
    "rsi_v1",
    "source_trust_v1",
    "di_sources_v1",
    "weekly_v1",
    "decision_flow_v1",
]
RowsProfile: TypeAlias = Literal[
    "conservation_tail_v1",
    "gate_tail_v1",
    "self_legacy_v1",
    "self_rows_v2",
    "active_legacy_v1",
    "cli_journal_v1",
    "prescore_topk_v1",
    "valid_evidence_v1",
    "control_proof_v1",
    "twin_v1",
    "dataops_rows_v1",
    "dataops_timeline_v1",
    "di_recent_v1",
    "di_rows_v1",
    "transfer_evidence_v1",
    "checkpoint_lookup_v1",
    "fingerprint_predecessor_v1",
    "evolution_rows_v1",
    "invoice_membership_v1",
    "trading_evidence_v1",
    "history_legacy_v1",
    "decision_flow_rows_v1",
    "counterfactual_rows_v1",
    "fact_history_v1",
    "evidence_similar_v1",
    "weekly_supplier_changes_v1",
]
JournalStatisticsProfile: TypeAlias = Literal[
    "group_totals_v1",
    "execution_v1",
    "journal_correlation_v1",
    "journal_prescore_v1",
    "journal_vix_v1",
    "journal_regime_v1",
]
LegacyOrder: TypeAlias = Literal["memory_recent", "memory_chronological",
                                "age_recent", "age_all", "age_verified",
                                "projection_created"]

@dataclass(frozen=True, slots=True)
class ReadStamp:
    graph_id: str
    domain: str
    scope_digest: str
    epoch: int
    schema_version: str

@dataclass(frozen=True, slots=True)
class ReadCursor:
    token: str

@dataclass(frozen=True, slots=True)
class BoundPage:
    limit: int = 100
    after: ReadCursor | None = None

@dataclass(frozen=True, slots=True)
class Cell:
    name: str
    value: Scalar

@dataclass(frozen=True, slots=True)
class StatisticGroup:
    key: tuple[Cell, ...]
    values: tuple[Cell, ...]

@dataclass(frozen=True, slots=True)
class StatisticsRequest:
    profile: StatisticsProfile
    legacy_order: LegacyOrder = "age_verified"
    filters: DecisionFilter = DecisionFilter()
    category: str | None = None
    action: str | None = None
    system: str | None = None
    supplier: str | None = None
    item: str | None = None
    factor_names: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    rank_start: int = 0
    window: int = 400
    threshold: int = 30
    start: float | None = None
    end: float | None = None
    source_domain: str | None = None
    target_domain: str | None = None
    evidence_ids: tuple[str, ...] = ()
    population: Literal["active", "verified", "scorer_verified",
                        "conservation", "journal", "execution"] = "active"

@dataclass(frozen=True, slots=True)
class StatisticsResult:
    stamp: ReadStamp
    profile: StatisticsProfile | JournalStatisticsProfile
    population_count: int
    totals: tuple[Cell, ...]
    groups: tuple[StatisticGroup, ...]
    next_cursor: ReadCursor | None
    has_more: bool

@dataclass(frozen=True, slots=True)
class CurveRequest:
    profile: Literal["trajectory_v1", "iks_category_v1",
                     "purchasing_competence_v1"]
    category: str | None = None
    legacy_order: LegacyOrder = "age_verified"
    at_or_before: float | None = None

@dataclass(frozen=True, slots=True)
class PrefixPoint:
    rank: int
    decision_id: str | None
    timestamp: float
    outcome_count: int
    correct_count: int
    win_rate: float
    iks: float | None

@dataclass(frozen=True, slots=True)
class CurvePage:
    stamp: ReadStamp
    profile: str
    population_count: int
    point_count: int
    days_active: float
    final_point: PrefixPoint
    prior_point: PrefixPoint | None
    points: tuple[PrefixPoint, ...]
    next_cursor: ReadCursor | None
    has_more: bool

@dataclass(frozen=True, slots=True)
class RowsRequest:
    profile: RowsProfile
    legacy_order: LegacyOrder = "age_all"
    filters: DecisionFilter = DecisionFilter()
    projection: DecisionProjection = "full"
    category: str | None = None
    system: str | None = None
    supplier: str | None = None
    identifiers: tuple[str, ...] = ()
    reference_vector: tuple[float, ...] = ()
    factor_names: tuple[str, ...] = ()
    rank_start: int = 0
    window: int = 400
    before_count: int | None = None
    action: str | None = None
    outcome: str | None = None
    verified_only: bool = False
    start: float | None = None
    end: float | None = None
    source_domain: str | None = None
    target_domain: str | None = None
    policy: Literal["default", "composite_v1", "gate_v1"] = "default"

@dataclass(frozen=True, slots=True)
class EvidenceRow:
    record_id: str
    rank: int
    # Canonical, lossless typed JSON envelope, NOT an arbitrary query.
    payload_json: str

@dataclass(frozen=True, slots=True)
class RowsPage:
    stamp: ReadStamp
    matched_count: int
    items: tuple[EvidenceRow, ...]
    next_cursor: ReadCursor | None
    has_more: bool

@runtime_checkable
class ConsumerReadCapability(GraphStore, Protocol):
    def consumer_snapshot(self, domain: str) -> ReadStamp: ...

@runtime_checkable
class ConsumerStatisticsStore(ConsumerReadCapability, Protocol):
    def consumer_statistics(self, domain: str, *, request: StatisticsRequest,
                            page: BoundPage = BoundPage(),
                            stamp: ReadStamp | None = None) -> StatisticsResult: ...
    def supplier_details(self, domain: str, *, request: SupplierDetailRequest,
                         page: BoundPage = BoundPage(),
                         stamp: ReadStamp | None = None) -> SupplierDetailPage: ...
    def trading_context_summary(self, domain: str, *, legacy_order: LegacyOrder,
                                stamp: ReadStamp | None = None) -> TradingContextSummary: ...
    def estimate_graph_dk(self, domain: str, *, request: DKRequest,
                          stamp: ReadStamp) -> DKResult: ...

@runtime_checkable
class PrefixCurveStore(ConsumerReadCapability, Protocol):
    def query_prefix_curve(self, domain: str, *, request: CurveRequest,
                           page: BoundPage = BoundPage(),
                           stamp: ReadStamp | None = None) -> CurvePage: ...
    def iks_summary_page(self, domain: str, *, categories: tuple[str, ...],
                         legacy_order: LegacyOrder, page: BoundPage = BoundPage(),
                         stamp: ReadStamp | None = None) -> IKSSummaryPage: ...

@runtime_checkable
class ConsumerRowsStore(ConsumerReadCapability, Protocol):
    def query_consumer_rows(self, domain: str, *, request: RowsRequest,
                            page: BoundPage = BoundPage(),
                            stamp: ReadStamp | None = None) -> RowsPage: ...
```

**Validation and binding.** BoundPage limit1..1000. JournalQuery alone supports offset0..10000 (§3.4); other supplemental pages use cursors, apart from explicitly specified legacy rank_start adapters. Strings/IDs max1024 UTF-8 bytes except lossless evidence payloads. Tuple selectors max1000 unique entries; shape factor/category/action tuples max1000 each. A Cartesian product may exceed1000: measurement reduces it on the primary and pages detail, never rejects it merely because the product exceeds a page. Reject an indivisible online result exceeding its byte budget before activation rather than truncate. rank_start>=0, threshold>=1, finite numeric parameters, start<=end. window is a positive integer: conservation and gate populations have NO400/1000 semantic ceiling; other profiles retain their explicit individual bounds, with1..1000 the default where none is specified. Reject irrelevant nondefault parameters per profile. Cursor binds graph identity, domain, effective tenant/legacy policy, profile/schema, all normalized selection parameters, sort/direction, epoch and last complete key (the global H rank for conservation/gate evidence, as defined in §2.2). Opaque authenticated token max4096 bytes; callers only echo it. Cross-scope/profile reuse is an error. Page-after requires the same stamp, embedded in cursor if omitted.

**Consistency.** `epoch` is a supplemental graph revision, incremented atomically on EVERY fact mutation relevant to these capabilities, including archive/delete, journal annotations, imports, checkpoint/fingerprint/evolution/transfer changes and migration activation. It is not a replacement for P2's Decision change-feed generation and must not reset/reuse values; graph replacement changes graph_id. Each query checks epoch and reads under one consistent transaction, returning the epoch it actually read. A later request at a different epoch raises a typed `ConsumerReadChanged(expected: ReadStamp, actual: ReadStamp)`; discard all pages and restart, with at most one automatic restart per HTTP request. No claim of historical MVCC across independent requests. Offline long exports can instead pin a read transaction (§4). Request-local reuse uses the same stamp and dies with the request.

**Transport bounds.** Online statistics/curves/rows/journal pages are <=2 MiB of decoded canonical UTF-8 JSON, including framing and cursor; totals<=128 cells, groups<=1000, cells/group<=128, key dimensions<=8. Reduce page size on byte boundary, never drop fields or split a logical row. A single oversized row raises `ConsumerRecordTooLarge(record_id: str, bytes: int, limit: int)`; route it to explicit offline chunk traversal, not silent omission. At most limit+1 logical candidates cross the DB-driver boundary for paged rows/groups; aggregates transmit only aggregate state, not all inputs. Exact full-population totals are independent of page length. Group cursors use normalized key tuple ascending (null first, then type tag and UTF-8 value); no hash-map iteration order.

These are output/network bounds, not a claim of constant-time exact scans. Primary-side scans, ordered windows and temp sort spill inside the same database are allowed. They are not persisted query-serving tables. P5 deadlines and P12 physical statement/byte accounting still apply. Statistics group paging cannot be implemented by fetching every group and slicing in Python.

### 2.2 Order, numeric fidelity and eligibility policies

Define C=(normalized created_at, decision_id) ASC, V=(coalesce(verified_at,created_at), decision_id) ASC, and L=the explicitly requested legacy order. L is never assumed equal to C. The inspected providers differ: memory_store.py:2577 defaults to created DESC with decision_id ASC and null dates last; its chronological verified read uses created,_sequence,id ASC. AGE get_decisions at age_graph_store.py:2897 defaults created DESC,id ASC; AGE get_all_decisions:3428 and non-cursor get_verified_decisions:2927 use created,id ASC. Verified AGE cursor reads alone use the coalesced verification key. AGEProjection:291 orders only created ASC, with previously unspecified ties.

LegacyOrder names select those exact orders: memory_recent=(null flag,-normalized created,id); memory_chronological=(created,recorded sequence,id); age_recent=(created DESC,id ASC); age_all and age_verified=(created ASC,id ASC); projection_created=(created ASC,stable projection ordinal). Request adapters choose age_verified for raw verified AGE calls, age_all for get_all_decisions, age_recent for get_decisions, and the corresponding memory order for old memory callers. Both concrete supplemental implementations support all named orders so parity fixtures compare the SAME request. This is an explicit request field, never an implementation-type-dependent hidden sort. The trusted composition factory supplies the legacy order mapping to consumer_access; wrappers preserve it and cursor binding includes it.

AGEProjection's historical equal-created tie order is not recoverable from its query. P4 captures a migration ordinal for existing ties and labels the deterministic projection_v1 tie policy in schema_version; it cannot claim to reproduce a previously unspecified order. Projection profile_v2 instead uses created,id ASC and all-history category population. Existing memory sequence provenance is retained where needed; no invented historical sequence for AGE. P2 generic cursors remain strictly timestamp/id, both components in the same direction. In particular age_recent is NOT representable by generic descending=True on tied timestamps: legacy-compatible history must use the supplemental recent-row profile or explicitly version the tie change.

**Reference chronological order H (conservation, trust and gates).** This is distinct from C. Scorer _read_conservation_inputs_once calls _sort_decisions_chronological, which delegates through backend/conservation_utils.py to composite_gate.chronological_decisions. Its exact ascending key is (normalize_timestamp(row["created_at"]), str(row.get("decision_id") or "")) for a dict whose created_at is non-null; otherwise the key is (0.0, ""). A missing/null timestamp therefore ignores the actual decision ID. A present epoch-zero timestamp retains its ID component; negative timestamps precede zero. Do not replace missing dates by zero while retaining their IDs, substitute verified_at, or add an unconditional ID tiebreaker. Non-null malformed timestamps retain the reference normalization error.

Python's sort is stable: identical complete keys retain the sequence's original input order, including all missing/null timestamps. Let input_ordinal be the position in the complete effective legacy provider sequence L supplied to the helper, before sorting or page slicing. Preserve this ordinal through eligibility filtering. It is not universally insertion order, a newly assigned ID order, or page-local position. For ordinary finite keys the equivalent native total key is (reference_timestamp, reference_id, input_ordinal) ASC. Present equal timestamps still compare IDs first; only equal complete keys use input_ordinal. Capture/preserve existing provider sequence provenance at a ReadStamp; do not invent historical provenance or use a database's unspecified tie order. The same L mapping must be used by the reference and bounded paths. If exact provider order/reference comparison behavior cannot be reproduced, capability activation fails its parity gate. Nonfinite inputs retain the reference's actual stable-sort comparison behavior under §2.2's numerical fidelity requirement; no new SQL NULL/NaN order is substituted.

Define H as the resulting reference-ordered eligible sequence, with unique zero-based global ranks assigned AFTER that stable sort and BEFORE tail selection. Conservation totals, configured-window membership and conservation_tail_v1 evidence all use this identical H. Trust and composite/gate profiles use the same ordering rule with their own eligibility/correctness policies. Helpers such as _recent_quality and _rolling_q only slice their supplied sequence; they do not themselves sort. Their scorer path receives H. Raw-provider baseline/checkpoint profiles and any explicitly supplied unsorted-input helper parity cases preserve their separate input-order contracts; this amendment does not silently sort those populations.

**Cursor/window identity.** For conservation_tail_v1 and gate_tail_v1 the existing opaque ReadCursor carries the last emitted global H rank, bound to ReadStamp, profile/policy, L, selectors, configured W and ascending H order. Select the eligible complete H and its tail ranks [max(0,N-W), N) first; page predicates then select ranks greater than the cursor's last rank, ORDER BY that same rank ASC. No offset, C/V timestamp predicate, real-ID tie substitution, or re-ranking of individual pages is permitted. Recompute identical ranks on the primary at the same epoch; an epoch change raises ConsumerReadChanged and restarts the read, never resumes against shifted ranks. This is bounded output from the same primary, not a persisted alternate rank store. Page concatenation must equal the scalar reducer's T_W row for row, including null and equal-key ties. All normal byte/cardinality limits still apply.

This rank is internal to the existing supplemental cursor; no generic DecisionCursor field or P1 dataclass changes are required. Other profiles retain their own stated orders: group pages use group keys, trajectory uses prefix rank, journal uses entry/P&L order, and replay uses its verification boundary (§4.3). Their cursor predicates must match their respective orders; none is reused for H windows. This rule makes conservation reduction and evidence pagination consistent without changing unrelated consumer semantics.

Correctness policies are separate:
- canonical: P2 normalized verified/correct fields; correct=False excludes pending.
- scorer: non-null outcome string confirmed/overridden determines verification, otherwise non-null is_correct; correct is confirmed OR truthy is_correct.
- fingerprint: AFTER scorer eligibility and compatible-vector selection, correct is ONLY bool(row.get("is_correct", False)); outcome/status/correct aliases never override this class mask. See frozen policies in §2.5.
- strict: is_correct is True OR the explicitly named strict legacy alternative; do not convert a string "false" into canonical correctness.
- trajectory: count outcome when key is_correct EXISTS, including None; truthiness determines numerator.
- trust: key is_correct, then outcome_correct, then outcome string confirmed/correct/success.
- composite: discard None is_correct; remaining values use bool.
- gate: key is_correct, then correct, then outcome in true/1/correct/confirmed/success/passed.
- journal: monetary win pnl>0; missing P&L is not a win and remains in trade-count denominator.

Scorer field lookup honors key presence before metadata then factors.metadata. Conservation benchmark exclusion is context.benchmark is True OR outcome_metadata.context.benchmark is True. No source/sample shortcut is equivalent.

**Equivalence obligation.** Counts are sums of the identical indicator; means use the identical numerator, denominator and missing-value policy; rank windows select the identical ordered subsequence; prefix sums include ranks1..n, never only the page. These identities prove sufficient-input equivalence over exact arithmetic. They do NOT prove floating-point bit equivalence for SQL SUM/stddev.

For frozen numerical outputs P4 must implement ordered reducers on the primary with the reference arithmetic/reduction order, rounding mode and pinned dependency semantics. Fingerprint variance requires the same two-pass NumPy ddof=0 reduction, not cancellation-prone sum(x*x)-sum(x)^2/n; statistics.mean/pstdev and Python ordered sum are distinct reducers. Bootstrap profiles preserve random generator, seed, block sampling and percentile interpolation. Use native same-primary reduction functions in the P4 SQL migration; stream ordered values inside the server, bounded reducer state/sort spill, no all-row driver materialization or persistent read cache. The migration and installed function version are part of capability activation. If exact reference behavior cannot be implemented on the supported primary, P4 FAILS its acceptance gate; it may not loosen tolerances, switch algorithms, or replace history with400 rows. Reference arithmetic modules remain unchanged; no new remote numerical service.

Tests include adversarial cancellation, rounding boundaries, nonfinite/invalid values, ties, small-class defaults, and threshold boundaries. Preserve existing errors where the reference errors; do not silently coerce malformed historical vectors. Serialization of legacy nonfinite evidence uses tagged values in lossless payloads, not invalid JSON numbers. HTTP metrics retain their existing finite/null/error contract.

### 2.3 Closed statistics registry and formula contracts

Each row defines all allowed result keys. Counts below are int; rates/sums/moments float; nullable values are explicitly marked ?. `n,c` always refer to the row's named policy, not implicitly canonical. Empty groups are emitted only where configured zero groups are required. Selectors not mentioned are rejected. Unless a row specifies otherwise: all-history active population, no time filter, totals on the entire population, group keys ascending, BoundPage(100), stamp required for composition.

| Profile / callers | Exact totals and group fields | Population, ordering, equivalence |
|---|---|---|
| counts_v1 / 26,30,31,36,48,53–55,58,78,91,97 | totals total:int, verified:int, correct:int, overrides:int; groups category:str → n:int,c:int | Canonical active/V/C, explicit conservation variant request.population; alpha=round(C/V,4), phase unchanged. Count pair from one transaction. |
| baseline_v1 /24 | totals population:int, selected:int, correct:int; no groups | Raw verified L order; if N>=200 choose [max(0,N-400):max(0,N-400)+200], bool(is_correct fallback correct). Otherwise caller's existing state/preset/.5 fallback. No benchmark exclusion. |
| conservation_v1 /25,45,69,97 | totals n:int,c:int,overrides:int,category_support:int,window_size:int,window_n:int,window_c:int; groups category:str → n:int,c:int; optional ordered evidence via conservation_tail_v1 | Scorer verification, benchmark exclusion, H order (§2.2); request.window equals the actual caller-configured W (§2.7), no400 cap. Core q defaults400, preset recent window defaults100, threshold.75. Bootstrap400 block20 n_boot200 remains fixed. Raw-count branch retains raw V/C denominator with eligible overrides; supplied-row branch uses eligible denominator. |
| checkpoint_quality_v1 /43 | totals n:int,c:int,end_timestamp:float? | Last400 from existing get_recent_verified semantics or L[-400:]; strict-True correctness; caller-supplied end wins, else last created/verified fallback. |
| fingerprint_v1 /44,50,108 | totals n:int,c:int,skipped:int; groups (kind:str,category:str?,factor:str?) → n:int,c:int,sigma_correct:float?,sigma_incorrect:float? | Scorer verified ELIGIBILITY, compatible vector width only; correctness/class split ONLY bool(is_correct), FINGERPRINT_POLICY (§2.5), never OR-confirmed. Per-factor class std ddof0. If total<5 defaults sigma.5 weight0 overall0 no category precision. Class<3 sigma.5; combined max((sC+sI)/2,.01), weights inverse-square/max, round3; interpretations from unrounded sigma .1/.2; accuracy round3, category precision only n>=3. Counts and the two class sigmas reproduce every output. |
| scorer_iks_v1 /44 | totals n:int,c:int,categories_ge10:int; groups none | All scorer verified accuracy; nonbenchmark category>=10 support. Combine fingerprint rounded sigmas: clip((1-mean_sigma/.5)*25,0,25); min(V/500,1)*25 + accuracy*25 + FP + support/configured_categories*25, round1. Preserve skip_historical/checkpoint centroid-drift branches separately. |
| measurement_v1 /42 | totals n:int,c:int,arm_group_count:int,arms_measured:int,min_arm_count:int,decisions_needed:int; groups (category:str,action:str) → n:int | Raw verified, bool(is_correct), actual_action OR recommended_action OR action. Configured Cartesian zero arms plus unknown observed arms, skip empty category/action. ALL-arm reductions are independent of group pagination (§2.5); threshold default30. Caller preserves configured arms_total from shape, which need not equal arm_group_count. |
| trust_v1 /57 | totals n:int,c:int,first_n:int,first_c:int,last_n:int,last_c:int,tail50_n:int,tail50_c:int,tail200_n:int,tail200_c:int; groups category:str → n:int,c:int,first_n:int,first_c:int,last_n:int,last_c:int | H order (§2.2), including missing/null (0,empty-id) and original input-order ties. First floor(N/2), rest; trust correctness. Gini on all category counts; half delta>.02, percat n>=4 and drops>.10/.20; N>=50 tail50 vs200>.15; easy>=.8/hard<.6 and easy volume>=3*hard preserved. |
| composite_v1 /39; gate_v1 /40 | totals n:int,c:int,window_size:int,window_n:int,window_c:int; no groups; optional paged gate_tail_v1 | H order (§2.2), each policy above; composite drops null, gate full-history C/N despite method name "recent". Request actual configured w_short/w_long separately at one stamp;20/400 defaults, no400 semantic cap (§2.7). Baseline fallback unchanged. |
| profile_v1 /15,16 | totals verified:int,correct:int; groups category:str → n:int,c:int | Preserve existing oldest first10000 verified category cohort, skip empty category, strict correctness; V/C remains all-history. profile_v2 uses all verified for categories, explicitly different population/version. |
| switching_age_v1 /37 | totals n:int,earliest:float? | Min of every parsable created_at/timestamp/createdAt candidate, not only created_at. Clock-now stays caller input; round days3 unchanged. |
| transfer_router_v1 /38 | totals n:int,amount:float | Pattern override first; else source+target Decisions first numeric top-level dollar_impact/financial_impact/impact/value. Legacy bool-as-number and error/nonfinite semantics preserved. |
| cross_domain_v1 /116 | totals n:int,amount:float; groups domain:str → n:int,amount:float | Separate financial_impact/dollar_impact/impact/value and nested metadata precedence; optional evidence IDs, independent authorized domain scopes. IDs paged by transfer_evidence_v1, never an unbounded totals field. |
| shadow_coverage_v1 /117 | totals supported:int; groups category_index:int → n:int | Non-null integer category_index wins even unknown/out-of-range, otherwise configured category mapping. Existing fraction may exceed1; do not clamp. |
| trading_context_v1 /61 | totals n:int,closed:int,correct:int,monetary_count:int,monetary_sum:float; groups (kind:str,key:str) → n:int,c:int,confidence_n:int,confidence_sum:float; REQUIRED companion TradingContextSummary (§2.5) | Existing merged-row correctness and closed predicate; calendar=str(created)[:10] or unknown; thesis/concentration/category groups. Companion supplies exact rolling10 items and latest metadata regime. Monetary first finite top/outcome_metadata/metadata dollars_saved,monetary_impact,pnl_dollars,dollar_impact,pnl, over ALL Boolean-is_correct rows in verification DESC order. Evidence IDs use R. |
| claim_gate_v1 /66 | totals tested:int,powered:int,survived:int,impact:float | All active tested, canonical V/C; first-not-None top/meta pnl,pnl_dollars,dollar_impact, numeric else0; max(0,round(sum,2)). Not finite-first monetary selector. |
| trading_analytics_v1 /65 | totals n:int,c:int; groups (kind:str,category:str?,action:str?,factor:str?) → n:int,c:int,sum:float | Actual-or-recommended action counts, strong/poor factor means and category means; checkpoint vectors are exact R lookups, not Decision groups. |
| vol_sharpe_v1 /65 | totals n:int,mean:float?,stdev:float?,iid_se:float?,block_se:float?,inflation:float?; groups cluster_id:str → n:int,mean:float,stdev:float | Quality first finite quality/outcome_quality/decision_quality, then key is_correct binary, actual-action mapping strong1/partial.5/poor0, then pnl clipping. Full ordered population; block bootstrap50 seed0 block20; metadata.analytics.cluster_id grouping preserved. Return exact bootstrap diagnostics, not only replica means; clusters use sample stdev (0 for n<2), measured threshold10, mean/stdev round6 and ratio round3. Overall measured threshold30, EPS1e-12, adjusted=naive*min(1,iid_se/max(block_se,EPS)) with existing zero/nonfinite branches. |
| vrp_v1 /65 | totals total:int,eligible:int,vrp_sum:float,iv_sum:float,rv_sum:float,current:float?,tail_n:int,low_tail_n:int,high_tail_n:int,positive_capture:float,low_capture:float,high_loss:float,high_gain:float | Native per-record current helpers, metadata.analytics iv/rv; tail flags incl vrp_harvest; threshold.35; ordered sum and last; eligible and tail populations are distinct, excluded=total-eligible; measured>=30, spread classification at +/-.01. |
| regime_vrp_v1 /65 | totals n:int; groups regime:str → n:int,current:float?,percentile:float? | Existing option-chain/implied/vol-proxy/RV selectors; percentile of last252 with min_periods=min(5,N), same pandas rank semantics. |
| dispersion_v1 /65 | totals fired:int,followed:int,skipped_value:float | Existing explicit fired override or gap>=.05, native same quant gap derivation from graph arrays; ordered sum. |
| prescore_regime_v1 /73 | totals n:int,c:int; groups (category:str,regime:str?) → n:int,c:int | Existing prescore nested selectors; unknown candidate may be rejected then later candidate tried. Null regime (explicit None) retains rows for category-wide n/c, not regime-specific accuracy. See exact caller fields and classifier distinction in §2.5. |
| regime_classifier_v1 /75; trading_regime_v1 /70; conditioner_v1 /89,107 | totals n:int,verified:int,correct:int,rejected:int; groups (category:str?,regime:str) → n:int,verified:int,correct:int | Separate versioned selector profiles; regime_classifier_v1 requires category key and configured categories, emits buckets n>=10 at the presentation layer (unfiltered native counts preserve category baseline). Other profiles use null category key. Trading analytics uses nested regime_context/regime_metadata, verification flags/timestamps/status, outcome_correct before is_correct; conditioner normalizes choppy/range to ranging and applies its existing abstention thresholds. Unknown buckets retained where reference emits them. |
| promotion_v1 /74 | totals population:int,stage_n:int,stage_c:int; groups none | Category, ordered float(created OR verified OR0),id; ranks>=rank_start=stage_start_count. Demotion n>=20 and accuracy<.5 over whole stage, not last20. |
| trader_profiles_v1 /76 | totals n:int; groups (trader:str,category:str,action:str,factor:str?) → n:int,c:int,sum:float | Valid configured category/recommended/actual terms; trader entity top/meta entity/trader/default; strict correct True; strong-action means factors/scored/vector precedence; configured zero categories, accuracy ties by name. |
| purchasing_auto_v1 /83 | totals n:int,c:int; groups category:str → n:int,c:int | top/meta/context category, status/outcome confirmed/overridden or non-null correct, exclude is_sample_data. Do not map sample exclusion to legacy-signal flag. |
| purchasing_evidence_v1 /85,86 | totals active:int,verified:int,correct:int; groups factor:str → n:int,sum:float | Strict correct True; factors from verified, or all if verified empty; exact full-context factor recomputation for missing values, not vector-only. Top-factor evaluator unchanged. |
| supplier_iks_v1 /87 | totals n:int,otif:int,exceptions:int,seasons:int; groups category:str → price_n:int,price_sum:float | Supplier top/meta/factors.metadata; OTIF defaultTrue/exceptionFalse with key-presence semantics and outcome context. Price count/sum describe last5 numeric prices by L PER category but cannot reconstruct the response. REQUIRED companion supplier_details returns individual SupplierPriceDetail or SupplierSeasonDetail pages (§2.5), with all-history distinct seasons. |
| supplier_scorecard_v1 /90 | totals n:int,exceptions:int; groups supplier:str → n:int,exceptions:int | Supplier top/meta/context/outcomecontext, NOT factors.metadata; exception is is_correct is False OR actual!=recommended. QBO order/vendor counts separate; min5orders and weights .45/.25/.20/.10 unchanged. |
| purchasing_orders_v1 /80 | totals n:int; groups item:str → orders:int | Existing graph item metadata/top/category grouping; no invented consumption quantity. |
| par_v1 /81,82 | totals matching:int,sample_present:bool,usage_n:int,usage_mean:float?,usage_pstdev:float?,first_date:str?,last_date:str?,data_days:int | Reject sample anywhere in input BEFORE item filter; item casefold, sum quantities by date, nonnegative daily sums only in mean/pstdev; extent uses valid dates including excluded negative sums. NormalDist z, low-history<30 factor1.5, summer-produce1.2/winter-protein1.15, lead2,current40,unit8 unchanged. Missing orders => existing40/unavailable, not fabricated rows. |
| dataops_accuracy_v1 /99 | totals n:int; groups category:str → n:int,c:int,first_n:int,first_c:int,last_n:int,last_c:int | All active incl pending; skip missing/unknown category, actual normalization policy; per-category L halves; .10 trend threshold. |
| dataops_pipelines_v1 /100 | totals n:int; groups system:str → n:int,c:int | top system/system_name/source/default dataops; no metadata substitution. |
| schema_impact_v1 /103 | totals impacts:int; groups column:str → impacts:int | category-column normalization, 1 per matching Decision; no inferred structural edges or extra system predicate. |
| transformations_v1 /104 | totals n:int,rows:int,avg_duration:float | Existing requested-system fallback means missing system matches; source rows have duration_minutes while reducer reads avg_duration_minutes, so preserve0 rather than "fix" arithmetic here. |
| rsi_v1 /102 | totals total:int,verified:int,correct:int,evolution_count:int,accepted_transfer_count:int; groups variant_id:str → first_event_id:str | Latest500 evolution cohort, planted excluded, first per variant; accepted cross-domain patterns metadata.patterns_applied>=1 distinct; trajectory final point via P; curated7-point data remains fixture. |
| source_trust_v1 /108 | totals n:int; groups (kind:str,name:str) → present:int | Factor vector length/names checks, top/meta/context system aliases set per row (no double count); DK-normalized tensor and current/prior fingerprint kept separate. |
| di_sources_v1 /112 | totals n:int,unmatched:int,latest_datetime:str?; groups source_id:str → uses:int | verified if ANY else all active; source_ids duplicates count, fallback source graph; latest only datetime-typed values, match_status unmatched/mismatch. Canonical payload preserves datetime tags. |
| weekly_v1 /114,115 | totals start:float?,end:float?,active:int,verified_rows:int,verified_ids:int,correct:int,waste_sum:float,variance_sum:float; groups (category:str,action:str?) → n:int,verified:int,c:int,first_rank:int | End=max active created, start=end-days, created>=start inclusive; verified window also CREATED, no now/verified_at substitution. Top action ties by first L encounter. Built-in purchasing cost exact waste/stockout/order_less/skip/price-memory rules; arbitrary callback offline E. Supplier changes are row evidence (one per qualifying Decision, not one per supplier) via weekly_supplier_changes_v1; sort rounded pct DESC then L rank. No cost_extractor means provider-waste only. With extractor, external waste_provider replaces the row waste sum but not variance sum. dollars_found=net_found_period=waste+variance; retain provider error/default behavior. |

The totals/group schemas above are mandatory discriminated runtime schemas keyed by request.profile. P4 generates typed profile constructors and validates Cell names/types, rejects duplicates and unknown fields; None is allowed only at '?' fields. Scalar is a serialization union, not permission to change a profile's schema. This table is the exact field contract; adding a profile or field is an explicit contract version amendment.

### 2.4 Curves, bounded rows and non-reducible algorithms

**Trajectory.** Existing compute_trajectory sorts normalized C and emits ranks0,10,20,...,N (last N only if not already emitted). Each prefix retains the same values: O=number of rows with is_correct key; C=truthy such values; win_rate=round(C/O,3) or .50. IKS=round(min(n/500,1)*25+win_rate*25+min(n/200,1)*15+min(n/100,1)*10,1). Empty population yields the existing zero point IKS0; nonempty rank0 yields12.5. Timestamp at0 is first creation; at n>0 is nth creation. days_active=round((last-first)/86400,1). Curve pages use increasing global prefix rank; final_point and population_count describe the complete population even on page1. Checkpoints/shape and currently ignored trajectory filter arguments are not newly applied. iks_category_v1 first performs IKSService category/normalization rules, including fallback decision-index/created-index, then the same prefix computation. purchasing_competence_v1 emits every rank1..N, correctness strict existing policy, accuracy round4; iks=None. No latest400 replacement.

**Rows registry.** Payload JSON is a lossless tagged representation of the exact existing row type after the indicated projection/normalizer, with no hidden internal fields. Dates/ndarrays/tuples/nonfinite floats need explicit type tags for offline/reference parity. Decode at the access boundary; tags never leak into old HTTP row models.

| Rows profile | Filters / projection / exact order and bound |
|---|---|
| conservation_tail_v1 | conservation population, full policy normalization, last min(N,window) in H then return global H rank ASC across bounded pages, using the §2.2 rank cursor; window is the actual configured positive W, not capped400. Payload id,timestamp,outcome,override,category only; native window totals in §2.7 serve online verdicts without page accumulation. |
| gate_tail_v1 | composite_v1 or gate_v1 selected by request.policy; last min(N,window) in H, across bounded pages using the same §2.2 global-rank cursor; id,timestamp,outcome only. Native window_n/window_c serve configured w_short/w_long with no400 cap (§2.7). |
| self_legacy_v1 | Existing self-router prelimit/filter/join semantics, full; identifiers carry requested decision IDs, category/action encoded via DecisionFilter only where identical. Actual-or-recommended matching uses self_rows_v2 below. |
| self_rows_v2 | Full, explicit category/status filters; actions match recommended OR actual OR action; C DESC, default50/max1000; filtered total matched_count. |
| active_legacy_v1; cli_journal_v1 | Full L ASC, then requested rank/window. CLI legacy cohort first10000, last n reversed, pending bool False; label legacy prefix, not newest all-history. |
| prescore_topk_v1 | Category, reference_vector + factor_names, all active; cosine round6 BEFORE sort score DESC, tie L; top5 exactly. No 400-prefix candidate restriction. |
| valid_evidence_v1 | Purchasing valid configured category/action terms filtered BEFORE last25 L; full context projection. |
| control_proof_v1 | Existing stored proof entries and reversed verified then reversed active, dedup(kind,id), max100; exact source precedence. |
| twin_v1 | Last200 sorted str(created_at), then existing validity filters; full scoring context; no date parser substitution. |
| dataops_rows_v1 | Existing _normalize_live_decision; system/category/actual action/correct predicates; limit1..100, L order. Unknown correct text means no predicate in v1 adapter. |
| dataops_timeline_v1 | Same all active population, id/name/created-or-timestamp projection, L then ID; cursor pages100. |
| di_recent_v1 | Last5 raw verified by L, full metadata/source IDs. |
| di_rows_v1 | Raw verified if nonempty else all active; preserve DIQueryService's time predicate before first max_records (default1000). request.start/end are computed once; timestamp is created_at OR timestamp OR verified_at. Full context, explicit legacy order. Current QueryPlan typed filters/dimensions are not applied by compute(); do not silently activate them. Unknown callbacks are offline-only. |
| transfer_evidence_v1 | Scoped source+target domains, IDs selected by pattern, identity=(domain,id), full or ID-only, domain/id ASC. |
| checkpoint_lookup_v1 | Exact identifiers or latest checkpoint prior to bound; no capped-prefix search; full checkpoint fields. |
| fingerprint_predecessor_v1 | Maximum decisions_analyzed < before_count AND >=5, ties timestamp/id; one full fingerprint. |
| evolution_rows_v1 | Explicit event filters, timestamp/id ASC, max1000; replay/export may page to exhaustion offline. |
| invoice_membership_v1 | identifiers<=1000, exact top/meta invoice aliases; outputs only requested IDs with found bool; missing IDs retained as found=False. |
| trading_evidence_v1 | Matched analytics group, identity only, C ASC; no unbounded inline contrast/source ID list. |

R requests reject unsupported filters; no "best effort" dropping predicates. Existing bounded point get_decision remains preferred for exact Decision IDs. Generic Q summary suffices for verified existence; generic scoring suffices only when its explicit learning_metadata allowlist supplies every requested field. Generic full is required for legacy history/context metadata compatibility; it is still page/byte bounded.

**Stateful work.** Replay consumes the COMPLETE fenced active-only stream after the restored checkpoint boundary (§4.3), updating its opaque cursor after each page; never advance only page_offset with a fixed replay_cursor. Startup replay finishes before readiness; a failed/resumed run publishes no partial scorer state. Arbitrary evolution callbacks, arbitrary DI group_fn/metric_fn and arbitrary weekly cost_fn have no universal finite sufficient statistic: a callback may return its entire input or query any rank. These remain explicit offline operations using E with complete outputs/manifest, subject to the evolution activation constraint in §8.5. DK is expressly excluded from that offline rule: the existing local-buffer estimator stays synchronous, and the graph fallback has the exact synchronous native contract in §2.6. No learn call reports completion while a required DK update is queued for later.

**Additional journal analytics.** Correlation needs exact total trades and first20 distinct tickers in journal order, not all rows; prescore needs category count/accuracy, mean size, latest trade, consecutive win-run length and last20 category factor nondefaults. VIX timing needs 4x3 hold/VIX count/win cells, date extent and explicit market-observation provenance; durations <8/<72/<336 hours, VIX<20/<30, P&L>0, local calendar date lookup. Regime accuracy is category/regime P&L wins/count; explicit regime wins over historical VIX-derived regime. Native profiles journal_correlation_v1, journal_prescore_v1, journal_vix_v1 and journal_regime_v1 use the JournalStats schema in §3. No graph rows are passed to a market adapter as an unbounded list. New market history fetched in bounded date chunks is ingested as Observation facts before primary-side joins. Dynamic arbitrary pattern/trust/recommender computations not expressible by these profiles run as E offline analyses until separately registered; no fabricated online approximation.

### 2.5 P3-FIX A/D: lossless detail and complete reductions

Source correction: there is no `copilot_sdk/scoring/projection.py`. Fingerprint arithmetic lives in `scoring/fingerprint.py:30–122`; `graph/projection.py:313–335` instead supplies the distinct strict-True, first10000 category/profile view. Both were read. The following additive frozen types belong to the same normative domain_queries specification, and the methods declared on ConsumerStatisticsStore above use them.

```python
@dataclass(frozen=True, slots=True)
class CorrectnessPolicy:
    name: Literal["fingerprint_v1", "scorer_v1", "trajectory_v1"]
    population: Literal["scorer_verified_compatible", "scorer_verified", "raw_verified"]
    numerator: Literal["bool_is_correct", "confirmed_or_bool_is_correct"]
    denominator: Literal["rows", "is_correct_key_present"]

FINGERPRINT_POLICY = CorrectnessPolicy(
    "fingerprint_v1", "scorer_verified_compatible", "bool_is_correct", "rows")
SCORER_POLICY = CorrectnessPolicy(
    "scorer_v1", "scorer_verified", "confirmed_or_bool_is_correct", "rows")
TRAJECTORY_POLICY = CorrectnessPolicy(
    "trajectory_v1", "raw_verified", "bool_is_correct", "is_correct_key_present")

@dataclass(frozen=True, slots=True)
class SupplierPriceDetail:
    category: str
    price: float
    decision_id: str
    legacy_rank: int

@dataclass(frozen=True, slots=True)
class SupplierSeasonDetail:
    season: str
    source_value: Scalar

@dataclass(frozen=True, slots=True)
class SupplierDetailRequest:
    supplier_id: str
    kind: Literal["prices", "seasons"]
    legacy_order: LegacyOrder = "age_verified"

@dataclass(frozen=True, slots=True)
class SupplierDetailPage:
    stamp: ReadStamp
    supplier_id: str
    kind: Literal["prices", "seasons"]
    matched_count: int
    items: tuple[SupplierPriceDetail | SupplierSeasonDetail, ...]
    next_cursor: ReadCursor | None
    has_more: bool

@dataclass(frozen=True, slots=True)
class TradingRollingOutcome:
    decision_id: str
    correct: bool
    verified_sort_value: float
    legacy_rank: int

@dataclass(frozen=True, slots=True)
class TradingContextSummary:
    stamp: ReadStamp
    rolling_10: tuple[TradingRollingOutcome, ...]
    latest_regime: str | None
    latest_regime_decision_id: str | None
    latest_regime_created_sort_value: float | None

@dataclass(frozen=True, slots=True)
class DKRequest:
    centroids_shape: tuple[int, ...]
    centroids_values: tuple[float, ...]
    n_categories: int
    n_dims: int
    legacy_order: LegacyOrder = "age_verified"
    algorithm: Literal["scorer_graph_fallback_v1"] = "scorer_graph_fallback_v1"

@dataclass(frozen=True, slots=True)
class DKResult:
    stamp: ReadStamp
    correct_support: int
    sampled_per_category: tuple[int, ...]
    weights: tuple[tuple[float, ...], ...] | None
    dispersion_fallback: bool
```

**Supplier detail (A-i).** `routers/iks.py:_supplier_rows_from_graph/_last_prices_by_category/_seasonal_patterns` is the reference for ledger87. Filter the complete raw verified population using its exact supplier resolver, BEFORE choosing prices. Select category=top-level category OR metadata.category OR "unknown"; price=float(top-level invoice_price if key exists, otherwise metadata.invoice_price); TypeError/ValueError means omit that price. This helper does not actually reject NaN/Infinity despite its name: preserve reference error/serialization behavior, using the already specified tagged nonfinite evidence representation where necessary, never silently filter them out. Price items are the final five valid-price rows PER category in L, returned category ASC then original L rank ASC. Keep repeated equal prices as separate records. matched_count is the number of selected detail records across ALL categories, not source Decisions; a page can cut a category's five records without losing its continuation. No aggregate sum is substituted for these records.

Seasons are the complete set of truthy metadata.season values from ALL supplier rows, not just price rows or the last five. Deduplicate and sort the original values with the reference Python semantics, then stringify for the legacy response; source_value preserves identity so distinct typed values that stringify alike are not accidentally merged. Unsupported/unhashable or mutually unsortable historical values retain the reference error instead of silently acquiring a new order. For valid values the cursor binds the exact original-value order plus its stable ordinal. The request kind discriminates items: prices returns ONLY SupplierPriceDetail, seasons ONLY SupplierSeasonDetail. Both are <=page.limit and2MiB, with a common stamp for statistics and both detail streams.

For a supplier whose complete arrays fit one bounded response, `price_memory=[{"category":x.category,"price":x.price}]` and `seasonal_patterns=[{"season":x.season}]` reproduce the current response exactly; OTIF/exception rates are round(count/n,4),0 when n=0. Larger arrays use explicit v2 independently cursor-paged price and season subresources under `/api/v2/purchasing/suppliers/{supplier_id}/scorecard/{prices|seasons}`, plus a scalar summary; do not loop through all pages inside the old endpoint. V1 retirement follows §6.1, not silent truncation. Counterexample: same supplier/category with prices [1,3], season winter versus [2,2], season summer has identical price_n=2/price_sum=4/season_count=1 but different price detail AND season detail; both legacy responses are reconstructible and distinguishable.

**Trading outputs (A-ii).** `context_router.py:523–705` is the exact reference for trading_context_summary. Use the same all-active/verified merge and original active-list L ordinal as trading_context_v1, at the SAME stamp. rolling_10 selects only rows where isinstance(is_correct,bool), sorts by _analytics_verified_time DESC with stable L ties, and returns at most10 items. The timestamp helper tries verified_at, verified_at_epoch, then created_at; each accepts the existing numeric/ISO conversion, default0. Legacy HTTP emits only decision_id/correct; the extra sort fields are capability provenance. If a caller needs rolling accuracy it is sum(correct)/len(rolling_10), with its existing empty handling; do not return the all-history accuracy in its place.

Latest regime is the first truthy metadata.regime_tag OR metadata.regime_metadata.regime in _analytics_decision_time DESC, stable L ties; it is NOT the regime of the newest verified row and is not restricted to canonical regime names. Missing candidate returns all three latest-regime fields None. The presentation adapter reproduces regime_analysis: selected metadata -> source=decision_metadata,available=True; otherwise the EXISTING monitor.current_regime fallback -> source=regime_monitor; otherwise source/status=unavailable,regime=None,available=False. No current-time market classification is invented by the graph query. Monetary count/sum in trading_context_v1 use ALL Boolean-is_correct candidates in that same verification-descending order, not merely the ten returned and not every closed row.

These meanings differ from `routers/regime_router.py`: /current returns market-derived regime,confidence,vix,adx,near_boundary,hurst,vol_state,vix_percentile,timestamp,source; /performance returns per_regime_accuracy,current_regime,edge_categories,observation; /recommendation returns current_regime,shifts. Preserve the market classifier/provider inputs. Use regime_classifier_v1 ALL category/regime n/c for performance/edges, including sub-threshold buckets in baseline; only presentation hides n<10. `services/pre_scorer.py:PreScoreResult` preserves recommended_action,confidence,probabilities,category,factor_values,similar_trades,category_accuracy,current_regime,regime_accuracy,warning. Its current_regime comes from the injected classifier, NOT latest Decision metadata. prescore_regime_v1 returns category-wide n/c even for rows without a recognized regime (null regime bucket encoded by regime=None), plus recognized-regime n/c; category_accuracy=round(c/n,4) or0; requested category/regime accuracy=round(c/n,4) orNone. Its unknown-candidate resolver continues trying later candidates, while RegimePerformanceMapper normalizes its first nonempty unknown candidate to ranging. These are separate profiles. Generic regime filtering cannot replace either. Shapes are fixed or paged; TradingContextSummary<=10 rows and2MiB, never truncated strings.

**Measurement global reduction (A-iii).** Let U be the union of configured Cartesian arm keys and all observed nonempty (category,actual_action OR recommended_action OR action) keys. At the primary, first form COMPLETE counts n[u], with configured absent arms zero; then compute arm_group_count=|U|, arms_measured=sum(1[n[u]>=threshold]), min_arm_count=min(n[u], default=N), decisions_needed=max(threshold-min_arm_count,0). Return those scalar totals on EVERY statistics page unchanged, together with N and bool(is_correct) correct count over all raw verified rows. Do not sum copies of totals across pages. arms_total remains the caller's _arms_total(shape) result (including its declared-size fallback), not |U| or page length; unknown observed arms can make arms_measured exceed arms_total, exactly as today.

The group page contains complete arm counts for selected keys. If native execution partitions group keys, merge (group_count,measured_count,minimum) by (sum,sum,min), applying the empty-U default N once at the end. If execution partitions source rows instead, first SUM partial counts by key and only THEN threshold/min: threshold counts are not additive across row partitions. No weighted average of per-page accuracies. N and correct counts yield the identical all-row accuracy C/N, while global minimum yields the identical state branch and decisions_needed. Thus >1000 groups, including a zero arm outside page1, cannot incorrectly mark a domain measured. Online measurement needs one totals result, not all detail pages. Existing empty/degraded/IKS branches in measurement_state.py are unchanged.

**Frozen correctness (D).** CorrectnessPolicy instances above are fixed definitions, not caller-overridable policies. fingerprint_v1 uses scorer verification only for ELIGIBILITY; all its n/c, class sigmas, overall accuracy and per-category precision use FINGERPRINT_POLICY after _compatible_decisions. For five compatible rows with outcome="confirmed" and is_correct=False: fingerprint correct count=0 and win rate0; scorer _is_correct_decision counts5; trajectory numerator0 with denominator5. Absence/None/string truthiness and minimum5/3 behavior are preserved. Scorer trajectory itself calls compute_trajectory, so it does NOT use the scorer OR-confirmed rule; that rule belongs to scorer IKS, DK fallback and specified conservation helpers. The graph/projection.py profile remains its separate strict-True policy. Canonical P1 projections must not overwrite conflicting historical values before these native reducers evaluate their named policies.

### 2.6 P3-FIX E: synchronous DK with exact graph fallback

`scorer.py:946–1004,1523–1644,2733–2752,3382–3413` defines the sequence. Persist Outcome and centroid first; invalidate the pre-write read context; evaluate the existing min_verified gate (default400, NOT a history cap) and captured conservation permission. Run the existing ProfileScorer.reestimate_dk() local-buffer path synchronously and unchanged. It uses its configured strategy and buffered correct decisions, which can differ from graph history. Call estimate_graph_dk ONLY if _dk_weights is still None afterwards. Neither existing weights nor a local-buffer estimator result may be overwritten by an unconditional graph estimate.

estimate_graph_dk is an optional GraphStore capability method on ConsumerStatisticsStore, not an addition to P1's four methods. It executes on the same primary, returns only a bounded tensor, and does not persist or publish model state. Its full input population is exactly _dk_decisions_from_store: raw active verified L, scorer eligibility and scorer correctness, key-presence vector/index lookup, float64 conversion, width check, integer conversion skip rules; benchmark rows are NOT excluded. Preserve conversion exceptions and invalid-index behavior, including category indices ignored by the estimator but counted in correct_support and dispersion fallback. Domain is the already bound scorer/store domain, preserved through namespaces.

For graph fallback algorithm scorer_graph_fallback_v1, pin `gae/dk_estimator.py:CoordinateDescentEstimator`: n_rounds5, max_per_cat400, candidates(.1,.3,.5,.7,1,1.5,2,3,5), tau.1, seed=None. Per category it chooses the FIRST400 eligible correct tuples in L (all when fewer); seed=None does not randomly subsample. It initializes unit weights, visits dimensions/candidates in reference order, accepts strictly better accuracy, stops when no improvement, and uses the same weighted-distance/softmax/argmax/float64 arithmetic. This is an exact native execution of the existing estimator, NOT replacement by means or a global tail. Primary-side ordered scans/temp spill are allowed; no full Decision vectors cross the driver boundary. Pin reference source/dependency versions in the P4 migration and parity fixture; a changed estimator version requires a reviewed algorithm version.

correct_support counts ALL graph tuples BEFORE per-category sampling. If <2 return weights=None, dispersion_fallback=False. Otherwise perform the estimator, then preserve the SDK's exact fallback: if np.var(weights)<1e-12 AND correct_support<200, run _dk_factor_dispersion_weights on ALL those tuples; NumPy axis0 variance, mean variance, unit weights when mean<=0, otherwise clip(var/mean,.25,4) tiled across categories. At N>=200 uniform output remains uniform. sampled_per_category contains estimator sample counts, not total support. This proves equivalence: identical selected tuples and live centroid tensor feed the identical deterministic estimator; support count selects the identical fallback, whose full population and reduction order are also identical.

DKRequest is row-major flattened live centroid tensor, shape(C,A,D) or(A,D) matching the reference accepted shapes, C=n_categories and D=n_dims. Request and result each<=2MiB; C,D and A each1..1000 and total centroid cells<=65536, output C*D<=65536; validate the complete configured model before enabling bounded mode, never silently truncate or disable DK. Historical malformed graph vectors retain reference behavior. The local-buffer path is not moved into GraphStore or substituted with graph rows, and no GAE estimator/formula source changes are authorized.

**Visibility and failure.** Capture the new read stamp after the committed outcome (and any receipt written before refresh). The native query sees that outcome in one consistent transaction and binds the supplied live centroid tensor. P5's existing mutation admission serializes learn/model publication and subsequent score on that scorer; keep ownership through synchronous DK completion and checkpoint capture. Apply the returned tensor before computing subsequent artifacts and before _save_centroids_checkpoint captures _checkpoint_dk_weights(). A score admitted after a successful learn sees the updated tensor; persist_artifacts=False still refreshes DK, just as today. No staleness window or deferred job exists. This is read-your-write/model-publication ordering, not a claim that the existing Outcome, receipt and checkpoint writes form one ACID transaction. Independent scorers still follow their explicit refresh/restore lifecycle; no distributed cache-coherence guarantee is invented.

A failed native read/estimate follows the existing _refresh_dk_after_learn failure path: logs, dk_refresh="failed", LearnResult.status="partial" with failure metadata; the committed Outcome remains committed, no background retry is reported as success. Preserve the existing effective tensor/checkpoint behavior of that failure branch. Epoch conflicts cannot apply a tensor computed over mixed pages; bounded retry reacquires a fresh post-write stamp within the remaining deadline. Tests compare first next-score probabilities, tensor, checkpoint metadata and failure status, not merely final accuracy. P4 activation requires exact native support; P6 cannot reinterpret ordinary learning as offline_required.

### 2.7 P3-FIX F: configured windows are population bounds, not page limits

For conservation_v1 add exact totals window_size:int,window_n:int,window_c:int to its existing totals; request.window=W selects that window under the identical conservation eligibility/order policy. Set W=max(int(preset.conservation_recent_window),1) for the recent gate, per domain; the current default is100. For the rolling-q helper use its passed window_size (default QUALITY_WINDOW_SIZE=400). Do not conflate the two settings. The bootstrap diagnostic and checkpoint quality remain their actual fixed400 reference cohorts; baseline remains first200 of tail400. Window positivity is validated, with no400 or1000 ceiling for conservation/gate profiles.

Let H be the reference-ordered eligible sequence defined in §2.2 (including missing/null keys and stable input-order ties), N=len(H), T_W=H[max(0,N-W):]. Native ordered rank selection uses the FULL H, then returns window_n=min(N,W), window_c=sum(reference_correct(d) for d in T_W). The caller evaluates the unchanged division, minimum-sample check and conservation thresholds. Full-history n/c/coverage/override totals remain full-history. If a caller explicitly requests row evidence, conservation_tail_v1 selects EXACTLY T_W and pages it by the same global H rank cursor (§2.2) with at most1000 records/2MiB per page; W600 returns600 when N>=600, W1600 returns1600 across pages, not1000. Online verdicts use native scalar reductions, not a loop accumulating that tail.

For composite_v1/gate_v1 likewise add window_size:int,window_n:int,window_c:int, leaving existing n/c all-history. Request each configured w_short/w_long at a common stamp. Means and short-window activation checks use each true configured cohort and correctness/null policy;400/20 are defaults, not hidden ceilings. This avoids transferring an arbitrarily large configurable gate tail during a score.

Counterexample resolved: H=200 losses followed by400 wins, W=600 yields window_n600,window_c400,recent_q=2/3. With threshold.75, count>=600 and q<.75, so learning pauses. Core q400 can simultaneously be1; the recent gate still pauses first, exactly as _conservation_pause does. A truncated400 input would yield count400 and skip that guard; this contract forbids it. Test W=1,400,600,1600,N<W and missing/tied timestamps, plus fixed400 bootstrap parity. No theta_min, alpha*q*V, learning-rate or penalty formula changes.

**Mixed null/epoch-zero counterexample (REV-P3-FIX).** Take the complete memory_recent input sequence: IDs0001..0200 are200 losses with created_at=0.0; IDs0201..0800 are600 wins with created_at=None (omitting the field has the same effect). The provider supplies losses then wins. Reference keys for every null win are (0.0,""), so stable H is wins0201..0800 followed by losses0001..0200. At W600, select global ranks200..799: wins0401..0800 (400) followed by losses0001..0200 (200). Thus window_n=600,window_c=400,q=400/600=2/3<.75; the recent-window guard pauses, exactly as the reference does. Using null-to-zero with the real ID would instead select600 wins and incorrectly yield q=1. The §2.2 cursor must visit this exact selected sequence once across pages (including pages crossing rank599/600), and its concatenated counts must equal the native totals. Also test shuffled provider IDs for missing/null keys, tied present timestamps, absent/empty IDs at epoch zero, negative timestamps, N<W and epoch invalidation; ordinal stability must not be inferred from monotonic fixture IDs.

## §3 Journal capability

### 3.1 Typed request, response and write contracts

Journal data is a view over governed Decision facts and distinct JournalEntry, ImportedTradeReference, Annotation and MarketObservation facts in the SAME graph. Their identities never increment verified Decision counts. JournalWriteCapability inherits GraphStore through ConsumerReadCapability; it is not a second database client.

```python
@dataclass(frozen=True, slots=True)
class FactIdentity:
    domain: str
    tenant_id: str
    kind: Literal["decision", "manual_entry", "imported_trade",
                  "annotation", "market_observation"]
    record_id: str

@dataclass(frozen=True, slots=True)
class Provenance:
    source: str
    source_record_id: str | None
    imported_at: float | None
    actor: str | None
    sample: bool
    source_digest: str | None

@dataclass(frozen=True, slots=True)
class FactorValue:
    name: str
    value: float

@dataclass(frozen=True, slots=True)
class FactorPredicate:
    name: str
    operator: Literal["lt", "le", "eq", "ge", "gt"]
    value: float

@dataclass(frozen=True, slots=True)
class JournalQuery:
    offset: int = 0
    ticker: str | None = None
    category: str | None = None
    strategy_tag: str | None = None
    regime: str | None = None
    actions: tuple[str, ...] = ()
    pnl_outcome: Literal["win", "loss"] | None = None
    entry_from: str | None = None
    entry_through: str | None = None
    date_basis: Literal["utc_instant", "record_calendar_date"] = "utc_instant"
    tags: tuple[str, ...] = ()
    text: str | None = None
    factors: tuple[FactorPredicate, ...] = ()
    confidence_min: float | None = None
    order_by: Literal["entry_time", "pnl", "legacy_rank"] = "entry_time"
    descending: bool = True
    pnl_nulls: Literal["last", "as_zero"] = "last"
    include_kinds: tuple[str, ...] = ("decision", "manual_entry", "imported_trade")

@dataclass(frozen=True, slots=True)
class JournalRecord:
    identity: FactIdentity
    revision: int
    provenance: Provenance
    decision_id: str | None
    trade_id: str | None
    entry_id: str | None
    ticker: str | None
    category: str | None
    action: str | None
    direction: str | None
    strategy_tag: str | None
    regime: str | None
    entry_time: str | None
    exit_time: str | None
    entry_price: float | None
    exit_price: float | None
    size: float | None
    pnl: float | None
    confidence: float | None
    tags: tuple[str, ...]
    reflection: str
    notes: str
    factors: tuple[FactorValue, ...]
    options_factors: tuple[FactorValue, ...]
    evidence_json: str

@dataclass(frozen=True, slots=True)
class JournalTotals:
    trades: int
    pnl_observations: int
    wins: int
    total_pnl: float
    avg_pnl: float
    win_rate: float
    confidence_observations: int
    avg_confidence: float

@dataclass(frozen=True, slots=True)
class JournalPage:
    stamp: ReadStamp
    items: tuple[JournalRecord, ...]
    totals: JournalTotals
    next_cursor: ReadCursor | None
    has_more: bool

@dataclass(frozen=True, slots=True)
class JournalStatsRequest:
    query: JournalQuery = JournalQuery()
    profile: Literal["group_totals_v1", "execution_v1", "journal_correlation_v1",
                     "journal_prescore_v1", "journal_vix_v1",
                     "journal_regime_v1"] = "group_totals_v1"
    group_by: Literal["category", "ticker", "strategy_tag", "regime",
                      "month", "subcategory"] = "category"
    category: str | None = None

@dataclass(frozen=True, slots=True)
class JournalWrite:
    identity: FactIdentity
    idempotency_key: str
    expected_revision: int | None
    provenance: Provenance
    record: JournalRecord

@dataclass(frozen=True, slots=True)
class AnnotationWrite:
    target: FactIdentity
    idempotency_key: str
    expected_revision: int
    tags: tuple[str, ...] | None = None
    reflection: str | None = None
    notes: str | None = None
    metadata_json: str | None = None

@dataclass(frozen=True, slots=True)
class FactReceipt:
    identity: FactIdentity
    revision: int
    epoch: int
    created: bool

@dataclass(frozen=True, slots=True)
class ImportBatch:
    source: Literal["csv", "broker", "manual_json", "reflection_json",
                    "metadata_json", "process_memory", "market_observation"]
    batch_id: str
    source_sha256: str
    records: tuple[JournalWrite, ...]
    policy: Literal["preserve_rows", "broker_deduplicate"] = "preserve_rows"

@dataclass(frozen=True, slots=True)
class ImportReceipt:
    batch_id: str
    read_count: int
    created_count: int
    linked_count: int
    duplicate_count: int
    rejected_count: int
    epoch: int
    receipts: tuple[FactReceipt, ...]

@dataclass(frozen=True, slots=True)
class LegacyAliasKey:
    namespace: Literal["trade_detail", "entry_overlay", "trade_metadata"]
    value: str

@dataclass(frozen=True, slots=True)
class LegacyAliasMapping:
    alias: LegacyAliasKey
    target: FactIdentity
    source_id: str
    source_ordinal: int
    precedence_rank: int

@dataclass(frozen=True, slots=True)
class LegacyAliasResolution:
    stamp: ReadStamp
    alias: LegacyAliasKey
    selected: FactIdentity | None
    match_count: int
    annotation_revision: int
    mappings: tuple[LegacyAliasMapping, ...]
    next_cursor: ReadCursor | None
    has_more: bool

@dataclass(frozen=True, slots=True)
class LegacyAnnotationWrite:
    alias: LegacyAliasKey
    idempotency_key: str
    expected_revision: int
    tags: tuple[str, ...] | None = None
    reflection: str | None = None
    notes: str | None = None
    metadata_json: str | None = None

@dataclass(frozen=True, slots=True)
class HistoricalAnnotation:
    annotation_id: str
    target: FactIdentity | None
    legacy_alias: LegacyAliasKey
    source_id: str
    source_ordinal: int
    history_ordinal: int
    kind: Literal["history_event", "current_snapshot"]
    original_updated_at: str | None
    normalized_updated_at: float | None
    payload_json: str
    provenance: Provenance

@dataclass(frozen=True, slots=True)
class AnnotationHistoryPage:
    stamp: ReadStamp
    items: tuple[HistoricalAnnotation, ...]
    matched_count: int
    next_cursor: ReadCursor | None
    has_more: bool

@dataclass(frozen=True, slots=True)
class JournalMigrationSource:
    source_id: str
    kind: Literal["manual_json", "reflection_json", "metadata_json",
                  "process_memory", "csv", "broker", "graph_inventory"]
    source_sha256: str
    expected_operations: int
    next_ordinal: int = 0

@dataclass(frozen=True, slots=True)
class JournalMigrationState:
    migration_id: str
    revision: int
    phase: Literal["staging", "reconciled", "active", "blocked"]
    sources: tuple[JournalMigrationSource, ...]
    committed_operations: int
    unresolved_aliases: int
    rejected_operations: int
    normalized_view_sha256: str | None
    epoch: int

@dataclass(frozen=True, slots=True)
class JournalMigrationBatch:
    migration_id: str
    expected_revision: int
    source_id: str
    source_sha256: str
    first_ordinal: int
    batch_id: str
    payload_sha256: str
    operations: tuple[JournalWrite | LegacyAliasMapping | HistoricalAnnotation, ...]

@dataclass(frozen=True, slots=True)
class JournalMigrationReconciliation:
    migration_id: str
    expected_revision: int
    normalized_view_sha256: str
    raw_fact_count: int
    annotation_event_count: int
    alias_mapping_count: int
    journal_totals: JournalTotals

@runtime_checkable
class JournalQueryCapability(ConsumerReadCapability, Protocol):
    def query_journal(self, domain: str, *, query: JournalQuery = JournalQuery(),
                      page: BoundPage = BoundPage(),
                      stamp: ReadStamp | None = None) -> JournalPage: ...
    def journal_totals(self, domain: str, *, query: JournalQuery = JournalQuery(),
                       stamp: ReadStamp | None = None) -> JournalTotals: ...
    def journal_statistics(self, domain: str, *, request: JournalStatsRequest,
                           page: BoundPage = BoundPage(),
                           stamp: ReadStamp | None = None) -> StatisticsResult: ...
    def get_journal_record(self, domain: str, *, identity: FactIdentity,
                           stamp: ReadStamp | None = None) -> JournalRecord | None: ...
    def resolve_journal_alias(self, domain: str, *, alias: LegacyAliasKey,
                              policy: Literal["legacy", "strict"] = "strict",
                              page: BoundPage = BoundPage(),
                              stamp: ReadStamp | None = None) -> LegacyAliasResolution: ...
    def journal_annotation_history(self, domain: str, *, identity: FactIdentity,
                                    page: BoundPage = BoundPage(),
                                    stamp: ReadStamp | None = None) -> AnnotationHistoryPage: ...

@runtime_checkable
class JournalWriteCapability(ConsumerReadCapability, Protocol):
    def write_journal_fact(self, domain: str, *, request: JournalWrite) -> FactReceipt: ...
    def annotate_journal_fact(self, domain: str, *, request: AnnotationWrite) -> FactReceipt: ...
    def import_journal_batch(self, domain: str, *, request: ImportBatch) -> ImportReceipt: ...
    def annotate_journal_alias(self, domain: str, *, request: LegacyAnnotationWrite) -> FactReceipt: ...
    def begin_journal_migration(self, domain: str, *, migration_id: str,
                                sources: tuple[JournalMigrationSource, ...]) -> JournalMigrationState: ...
    def get_journal_migration(self, domain: str, *, migration_id: str) -> JournalMigrationState | None: ...
    def import_journal_migration_batch(self, domain: str, *, request: JournalMigrationBatch) -> JournalMigrationState: ...
    def reconcile_journal_migration(self, domain: str, *, request: JournalMigrationReconciliation) -> JournalMigrationState: ...
    def activate_journal_migration(self, domain: str, *, migration_id: str,
                                   expected_revision: int) -> JournalMigrationState: ...
```

JournalWrite may create manual/import/market facts only, never a Decision or annotation by impersonating its kind. AnnotationWrite updates an annotation fact linked to target; Decision metadata/outcome is not silently rewritten. A Decision is created only by the existing governed scoring/write path. identity/domain/tenant/provenance fields are server-authorized; legacy absent/empty tenant normalizes to the existing literal default tenant 'default', not a new sentinel; conflicting ownership blocks migration; client-provided tenant cannot escape wrapper scope. expected_revision is required for updates; mismatch raises a conflict, not last-write-wins. Idempotency keys are tenant/domain scoped, payload digest bound; identical retry returns same receipt, different payload with same key errors. Import max100 records and2MiB per atomic batch; partial rejection is not a commit policy: validate first, reject entire batch with per-index typed errors, rejected_count=0 on successful receipt. Migration splits offline and retains rejected evidence for repair; does not skip it while declaring completion.

All requests/returned schemas frozen; include_kinds is validated against the three readable journal kinds. tags max100, text/reflection/notes max64KiB each, factors/options<=1000, finite normalized numeric values. Oversized legacy evidence remains lossless via E; online oversized record raises explicit error. New writes that exceed bounds are rejected, not truncated. Fact IDs max1024 bytes, timestamp strings preserve original representation and local calendar date alongside normalized query keys.

### 3.2 Normalization, predicates and exact totals

Compatibility normalizer is the current journal router:
1. Merge factors.metadata then raw metadata (raw wins). trade_id is raw trade_id, metadata trade_id, decision_id, metadata decision_id; entry_id raw/meta then trade_id. ticker uppercase.
2. action raw action/recommended_action/meta action; direction raw/meta/action. entry_time raw/meta entry_time/meta date, **not created_at**. pnl raw then metadata.pnl then metadata.pnl_dollars. regime raw/meta regime then raw/meta market_regime.
3. reflection raw reflection/notes/meta reflection/notes; notes raw/meta/reflection. size uses current non-null/raw then metadata size-or-shares rule. Normalize numeric factors and options without changing missing defaults. evidence_json retains omitted source fields for evidence/execution.
4. Tags strip strings and deduplicate case-sensitively; filter matching case-insensitive. Text is lowercased substring across ticker/category/strategy/reflection/notes/tags. Reflection PUT sets both reflection and notes and appends timestamped history; tag PUT replaces tags and appends history.
5. Legacy union precedence imported → manual → graph; dedup only nonempty trade_id, FIRST wins. Null-ID records all survive. Explicit collision links preserve this view while retaining every underlying fact for export. Physical identity always (tenant,domain,kind,id), never trade_id alone.

All predicates run BEFORE pagination. Entry date bounds are inclusive at both ends. utc_instant normalizes to UTC-naive equivalent instants; date-only end means midnight of that date, preserving existing behavior. record_calendar_date compares original timestamp local date, used by NL query. Invalid v1 date strings are ignored by compatibility adapter as today; v2 rejects with422. Default order entry_time DESC, invalid/null dates last; ties use preserved union/source ordinal then fact identity. P&L order uses pnl then entry-time legacy tie order then identity; normal API nulls last, NL best/worst uses null as0. Both cursor key and ORDER BY must contain the exact same normalized components/direction.

Totals cover every filtered logical journal record, independent of page or offset: trades=N, wins=count(pnl>0), win_rate=wins/N (including missing pnl in denominator), pnl_observations=count numeric pnl, total_pnl=reference ordered sum, avg_pnl=reference mean of present pnl, confidence analogously. Empty totals0. No capped prefix, no Decimal substitution for legacy binary-float outputs. Group totals use the same formulas; missing labels "unknown"; month follows existing entry parser; subcategory only event_driven. Group keys ASC and paged. Scalar totals method exists to preserve limit=0 without constructing an illegal generic page.

JournalStats schemas:
- group_totals_v1: totals JournalTotals fields encoded as Cells; group key is requested label; group values all JournalTotals fields.
- execution_v1: totals trades:int, fills:int, slippage_n:int, slippage_sum:float, slippage_median:float?, quantity_n:int, quantity_sum:float, cost_sum:float, fill_time_n:int, fill_time_sum:float; groups broker:str with same fields. Population is imported+active Decisions **without journal dedup**, matching execution_router. Slippage abs(fill-ref), quantity default1, annual delta*meanqty*max(N,1)*12. Exact median requires primary ordered rank selection, not mean.
- journal_correlation_v1: totals trades:int; groups rank:int → ticker:str, ranks0..19 first distinct tickers in full journal order. Correlation service retains external market-return math and30-trade measurement threshold.
- journal_prescore_v1: totals trades:int,size_n:int,size_sum:float,latest_entry:float?,latest_loss:bool,consecutive_wins:int,category_n:int,category_verified:int,category_correct:int,factor_rows:int,nondefault_factor_sum:int; no groups. Category input required. All-history mean size; category verified is verified flag OR P&L present; correct key correct then is_correct then pnl>0. Last20 category rows by existing journal list direction, not an assumed newest20. Consecutive wins computed over whole ordered run, not capped20.
- journal_vix_v1: totals analyzed:int,skipped:int; groups (hold:str,vix:str) → n:int,wins:int, all12 cells including zeros. Same-primary MarketObservation date lookup, external observation has precedence over row vix_at_entry then metadata. Historical local dates, exact thresholds in §2.4.
- journal_regime_v1: totals trades:int; groups (category:str,regime:str) → n:int,wins:int; nonemptycategory only, explicit row/meta regime else historical-VIX classifier with existing ADX default. Primary uses the version-pinned classifier, no approximate new threshold.

### 3.3 Every current writer and migration/cutover

| Source/writer | Graph migration and continuing write |
|---|---|
| journal.py manual POST, manual JSON loader/writer | ManualEntry with stable imported UUID or digest+source ordinal; write_journal_fact. Do not score a manual fact merely to persist it. |
| journal.py reflection PUT / tags PUT, reflection history JSON | Annotation linked to governed target identity; preserve notes+reflection alias and every historical change, timestamps and order. |
| context_router.py POST /trade-metadata and GET mapping; trade_metadata.json | Metadata Annotation; preserve whole payload and camelCase compatibility selectors. Point GET instead of loading whole mapping; v2 pages for list. |
| data_import.py CSV extend and broker import | ImportedTradeReference. CSV preserves duplicate rows with source ordinal; broker dedup by uppercase ticker, LOCAL entry date, abs(size), lowercase direction, across committed history and current batch. Server-atomic key uniqueness; no prefix scan. |
| data_import.py _trade_store_ref and process lifetime data | Quiesce imports, capture complete list with ordinal/digest, import as graph facts before reader switch. Do not lose rows on process restart during migration. |
| cli_sdk.py import (CSV/broker/scorer writes), export/journal | Existing governed Decisions remain Decisions with linked source references. New raw imported trades use fact API; scoring remains explicit. Version CLI command behavior, no silent removal of existing scored history. |
| main.py startup/scoring/seed paths | Existing governed Decision writes continue, preserving metadata linkage; pre-seed migration and sample provenance. No direct journal file writes after activation. |
| evidence_providers.py and routers/evidence.py metadata enrichment reads | Read graph annotation by identity. Explicit fixture_data remains a labeled test/demo input; filesystem fallback cannot serve live annotations. |
| context/registry/materialization and journal leaf routes | Replace process-list/JSON reads atomically with J/S/R or explicit offline analysis references; see §5.2 and P11 manifest. |

Migration is offline, resumable, graph-governed and idempotent. Create a migration manifest fact containing source digest, record count, ordinal range, normalized-view digest and rejected/collision counts. Import batches through GraphStore; retain original source bytes as lossless evidence chunks in the same graph where required for full export. Resolve collisions with explicit alias links and legacy precedence, never delete the losing evidence. Tenant conflict/missing ownership is quarantined and blocks activation; do not guess a tenant. Reconcile raw fact counts, annotation history, union count, ordered IDs, total P&L and normalized field digests against the frozen source snapshot. Record no unexplained rejects.

Install code additively in P4. P11 stages a quiesced source snapshot, migrates/reconciles, then atomically activates all writers and readers for that tenant/domain. Migration state lives in the graph, not an alternate query store. Installing code never automatically deletes files or migrates live data. On failure before activation, old readers/writers remain selected; after activation, rollback is to a graph-capable release, never to stale JSON. Resume via committed batch receipts; re-read only unchanged source digests. Historical JSON can remain archival evidence but cannot be a serving fallback. Source-scoped locks/maintenance admission prevent writes between final snapshot and activation.

### 3.4 P3-FIX B/C: offsets, aliases and historical migration

**Bounded offset decision (B, option a).** JournalQuery.offset is an integer0..10000; bool is invalid. query_journal applies all predicates and exact totals first, then ordered offset, then page.limit. page.after with offset!=0 raises ValueError (HTTP422); it never silently ignores either. Offset is a positioning instruction, not a selection predicate: the returned cursor binds the selection/order/stamp and final logical key, not the initial offset. To continue a page started at offset75, echo its cursor with the SAME filters/order and offset0. Next page follows that final key without skipping75 again. journal_totals and journal_statistics validate but IGNORE offset: totals describe the complete filtered population. BoundPage remains unchanged and limit>=1; limit0 HTTP requests call journal_totals and return an empty array.

Ledger68 covers BOTH /api/trading/journal/trades and its /api/trading/trades alias: v1 limit/offset map directly to JournalQuery(offset=offset) plus BoundPage(limit), preserving fields, pre-pagination filtering and inclusive date ends. Frontend api.ts fetchTrades/journalQuery passes its optional offset unchanged. The JournalQueryBar natural-language path does not currently pass an offset; start at0, return cursor in v2. Ledger60 CLI keeps its documented first10000 legacy cohort in P8; after its explicit P11 journal version switch it starts at0 and uses a cursor, not an implicit reinterpretation of that cohort. Execution ledger67, analytics ledger61/65, and metadata/evidence point routes are totals/point operations, not journal offset consumers. No other Appendix A entry requires a journal offset. P11 tests both HTTP aliases and api.ts parameter serialization. New v2 journal routes also tolerate offset<=10000 for migration but prefer cursors; this exception to the supplemental cursor-only default is explicit.

Existing uncapped offsets/limits cannot be promised under bounded operation. During the announced legacy migration window the old release keeps their old behavior. At coordinated P11 activation, v1 offset>10000 or limit>1000 returns422 with code legacy_page_bound, successor v2 URL and cursor/export instructions; no clipping and no hidden scan-through-pages helper. Values within bounds preserve v1 behavior, including limit0. V2 rejects out-of-bounds with422. This explicit validation tightening is documented alongside the deprecation/cutover mechanism of §6.1.

**Alias semantics (C).** Alias keys are opaque case-sensitive legacy strings within the effective authenticated tenant/domain and an operation namespace; strip/lowercase transformations are forbidden. Physical FactIdentity remains kind-qualified. Migration and every continuing write register aliases atomically with the fact/annotation:
- trade_detail: preserve GET /trades/{id}'s direct Decision ID lookup FIRST (with Outcome), then the first matching normalized trade_id in the legacy union. It differs deliberately from journal list dedup precedence.
- entry_overlay: preserve _entry_exists/_apply_overlay's str(trade_id OR entry_id), not an unconditional OR match on both fields. An entry_id hidden by a nonempty trade_id does not become a new v1 alias. The winning visible union record follows imported, manual, graph precedence plus source ordinal.
- trade_metadata: exact existing metadata-file key and its authorized target links; preserve overlays on every historically linked target, including a direct Decision detail view and a different journal-union winner. One alias may link multiple facts without discarding losing source evidence.

LegacyAliasMapping records EVERY candidate with original ordinal and deterministic precedence_rank. resolve_journal_alias(policy="legacy") returns the namespace's selected target regardless of which mappings page is requested, match_count for the full candidate set, and paged evidence. policy="strict" returns selected only when exactly one distinct target exists; otherwise selected=None and the v2 caller returns409 alias_ambiguous (404 when no target). No post-limit collision resolution. Mappings are <=1000/page and2MiB; IDs/source IDs follow1024-byte limits. Legacy reads retain the above winner; v2 clients can use the returned kind-qualified identity. Unknown aliases never fall back to a raw unscoped primary.

**Continuing alias writes.** Legacy reflection/tags and trade-metadata routes use annotate_journal_alias with LegacyAnnotationWrite. expected_revision is the alias annotation revision from resolve_journal_alias (0 before its first annotation); CAS and payload-bound idempotency apply. The primary writes ONE alias-linked Annotation fact and applies its overlay to ALL authorized linked targets under the original namespace rules, without fetching all alias candidates into the caller. This preserves the case where a metadata key affects both a direct Decision detail and an imported union winner. FactReceipt identifies that Annotation, not a fabricated Decision. Existing aliases are required; unknown returns404, ownership conflict fails. Kind-qualified v2 updates use ordinary annotate_journal_fact and deliberately affect only their explicit target. Both write paths append governed history atomically. For new live history rows, journal_annotation_history supplies source_id="live", the durable append ordinal and original commit timestamp through HistoricalAnnotation's same lossless representation.

**Historical annotations.** Ordinary AnnotationWrite continues to assign commit time for a new user edit. HistoricalAnnotation is a SEPARATE migration operation, authorized only during staging for a quiesced tenant/domain. Each imported history item retains original_updated_at exactly, parsed normalized_updated_at if valid (elseNone), payload key presence, original history_ordinal and source_ordinal. payload_json is a lossless canonical encoding of the original history dictionary (updated_at/reflection/tags plus any retained legacy fields) or original current overlay dictionary for kind=current_snapshot; the discriminator fixes the interpretation, it is not executable query text. Reflection updates set notes too exactly as _update_overlay; absence differs from explicit empty/null. The current_snapshot stores the original overlay's actual final fields even where incomplete history cannot reconstruct them. It is not fabricated as another user history event.

History presentation/order is original history_ordinal within the original alias/source, NOT normalized timestamp sort: equal, missing or backwards clocks must not reorder edits. If several sources target one fact, use the recorded migration source order and source_ordinal, then history_ordinal, then annotation_id; retain source boundaries. New edits follow all imported history at a monotonically increasing per-target append ordinal. Their timestamps remain separately recorded. journal_annotation_history returns only history_event entries in that append order, cursor-paged; current snapshots remain lossless export facts and provide the reconciled overlay baseline. Oversized evidence uses §4 chunks or an explicit oversized-record error; no history item is dropped.

**Migration state and atomic resume.** All ten new migration/alias data structures above are frozen, with typed method signatures. JournalMigrationSource.source_sha256 binds a frozen source snapshot AND the versioned deterministic operation stream. Each source compiles to a zero-based stream of JournalWrite, alias mappings and HistoricalAnnotation operations; ordinals are durable and stable across retry. Sources<=1000 and state<=2MiB; every batch<=100 operations/2MiB; counters nonnegative, SHA-256 strings64hex. Begin requires next_ordinal=0, unique source IDs, immutable counts/digests; graph_inventory describes preexisting governed records without cloning Decisions. begin/get are idempotent and tenant/domain scoped. Missing provenance/tenant conflicts and unresolved targets are retained as migration evidence but block reconciliation/activation.

import_journal_migration_batch validates source digest, expected_revision, first_ordinal==next_ordinal and payload digest, then commits ALL operations, deterministic annotation IDs/aliases, source progress, counters and batch receipt in one graph transaction. Importing a HistoricalAnnotation with target=None may preserve an orphan, but unresolved_aliases remains nonzero until an explicit resolved operation links the same annotation ID with matching payload. It can never activate as a silently lost overlay. Batch retry checks its durable (migration_id,batch_id,payload_sha256) receipt BEFORE revision comparison: identical retry returns the originally committed JournalMigrationState receipt; changed payload errors. To continue after such a retry call get_journal_migration for current progress. Out-of-order or partially accepted batches are rejected without moving next_ordinal. A crash before commit retries the same batch; after commit resumes at the stored ordinal. Source changed => block that attempt and stage a new migration ID/snapshot, never splice histories.

Reconciliation is native on the primary over all staged evidence: compare expected raw fact/history/alias counts, complete normalized-view SHA-256 (including ordered identities, all normalized fields and annotations), and exact JournalTotals with the frozen-source reference. It additionally checks every source next_ordinal==expected_operations, ownership, source provenance, alias precedence and zero unexplained rejection/unresolved counts. A caller-supplied digest alone is not proof. Only a successful server comparison transitions staging→reconciled and increments revision; failures produce a typed conflict and preserve non-active state. activate requires that exact reconciled revision and continued write quiescence, then atomically selects the graph-backed source and phase=active for the tenant/domain. A mutation of staged facts invalidates reconciliation. New writes and readers consult the same activation fact; no mixed JSON/graph serving interval.

Manual JSON, reflection history/current overlay, trade_metadata JSON, CSV duplicates, broker dedup, process-memory imported trades and existing governed CLI/scoring identities all use these operations; §3.3 writer coverage still applies. No separate migration database, process-only progress or fake Decision is introduced. P11 installs/migrates/activates only after P4 supplies these methods completely. Source snapshots remain offline evidence; after activation they cannot serve reads. This preserves both the visible historical overlay and the audit history rather than retimestamping imports as new edits.

## §4 Archive/export capability

### 4.1 Exact types and protocol

```python
@dataclass(frozen=True, slots=True)
class ReplayBoundary:
    checkpoint_id: str | None = None
    through_verified_at: float | None = None
    through_decision_id: str | None = None

@dataclass(frozen=True, slots=True)
class ExportRequest:
    mode: Literal["full_evidence", "active_comparison", "verified_replay"]
    order: Literal["identity", "created", "verified"] = "identity"
    consistency: Literal["transaction", "epoch"] = "transaction"
    include_archived: bool = False
    format_version: int = 2
    replay: ReplayBoundary | None = None

@dataclass(frozen=True, slots=True)
class ExportHandle:
    token: str
    stamp: ReadStamp
    request: ExportRequest
    expires_at: float

@dataclass(frozen=True, slots=True)
class EvidenceChunk:
    kind: str
    record_id: str
    archived: bool
    archive_id: str | None
    record_revision: int
    chunk_index: int
    final_chunk: bool
    canonical_utf8: bytes
    record_sha256: str

@dataclass(frozen=True, slots=True)
class ExportPage:
    chunks: tuple[EvidenceChunk, ...]
    next_cursor: ReadCursor | None
    has_more: bool
    page_sha256: str

@dataclass(frozen=True, slots=True)
class KindCount:
    kind: str
    active: int
    archived: int

@dataclass(frozen=True, slots=True)
class CompletenessManifest:
    format_version: int
    stamp: ReadStamp
    request: ExportRequest
    counts: tuple[KindCount, ...]
    logical_records: int
    chunks: int
    canonical_bytes: int
    ordered_sha256: str
    complete: bool

@runtime_checkable
class ArchiveExportCapability(ConsumerReadCapability, Protocol):
    def begin_export(self, domain: str, *, request: ExportRequest) -> ExportHandle: ...
    def export_page(self, domain: str, *, handle: ExportHandle,
                    page: BoundPage = BoundPage()) -> ExportPage: ...
    def complete_export(self, domain: str, *, handle: ExportHandle,
                        last_cursor: ReadCursor | None) -> CompletenessManifest: ...
    def close_export(self, domain: str, *, handle: ExportHandle) -> None: ...
```

Seven supplemental protocols total including shared ConsumerReadCapability; six functional capability families. Full evidence means active AND archived Decisions and their Outcomes, linked evidence and factor-schema/provenance, checkpoints/centroids, fingerprints, evolution/governance/transfer records, journal facts/annotations, and applicable domain observations. Include referenced shared schema/preset facts through authorized links, not another tenant's private data. No outbox consumer. mode full_evidence requires include_archived=True and identity order. Other modes label their narrower scope in the manifest; replay is not a backup. archived duplicates are distinguished by kind/id/revision/archive identity and every relationship endpoint must be resolvable or explicitly external with provenance.

Sort identity=(kind,record_id,revision,archive identity), then chunk_index ASC. Replay sorts EXACT normalized verification timestamp/id; created mode uses exact creation key/id. A chunk cursor binds handle and entire query plus record/chunk position. max1000 chunks/page, max8MiB decoded payload, max64KiB chunk; one large record is chunked losslessly, never omitted. Logical record checksum is over reassembled canonical representation; page checksum over length-prefixed chunks; stream checksum over ordered length-prefixed (identity,revision,record bytes). Manifest includes exact kind counts and bytes; complete=True only after terminal page and count/digest reconciliation. Empty export has a terminal empty page and valid empty-stream digest. complete_export cannot turn an arbitrary cursor into a proof; server verifies traversal/terminal position, and importer independently recomputes.

Transaction mode pins a read-only consistent transaction on the SAME primary for at most30minutes, max2 exports per tenant and8 per process, renewable only by beginning a new handle after expiry. This connection registry is a resource registry, not a graph-result cache; no snapshot rows live there. Memory reference uses a protected consistent view for the duration, without pretending to be production. Epoch mode checks stamp inside each page read and before manifest; any relevant mutation invalidates the WHOLE stream. A changing graph may starve epoch mode; select transaction mode for complete backups. No filtered last-mutation-generation approximation is a snapshot.

### 4.2 Failure, resume and publication

Write offline output to an unadvertised temporary artifact with header, ordered chunks, page checksums and a durable local checkpoint of handle/cursor/digest/count. Only publish/rename after the server terminal manifest and local digest/count checks agree. This output is an export artifact, never a query-serving substrate or scorer's alternate graph.

Retry the SAME cursor safely; append only if that page digest is not already committed. Handle still valid => resume. Transaction lost/expired or epoch changed => mark attempt incomplete, retain for diagnostics, begin new export and restart from zero; never splice two snapshots. Explicit close/finalization/failure releases connection, with expiry cleanup. No "resume by offset" over a new dataset. The manifest prevents a partial prefix being called a full export.

Scorer export and Purchasing/Trading backup get version2 envelopes with manifest and full evidence. Existing legacy export/load formats remain explicitly named legacy; current scorer load restores centroids only and must not be advertised as full graph restoration. Full restore is an offline governed import with idempotency, reference validation, version checks and complete-or-fail activation. Read-diff uses complete streams and existing float tolerance, retaining sample selection order; a missing page or archive is a comparison failure, not equality.

### 4.3 P3-FIX G: replay scope and checkpoint boundary

verified_replay defaults to active-only (include_archived=False), order="verified", and requires ReplayBoundary (empty means bootstrap through the captured snapshot). full_evidence callers MUST explicitly set include_archived=True; active_comparison must leave itFalse. ReplayBoundary is invalid in other modes. An optional through timestamp/ID pair is inclusive, finite/nonempty, supplied together and cursor-bound. A checkpoint ID is an exact lookup, never a last1000-prefix search. These selectors define the export range; page cursors remain opaque and returned by the store.

Replay ordering uses EXACTLY _replay_verified_decisions's key: normalize_timestamp(_decision_field(row,"verified_at",_decision_field(row,"created_at",0.0))), str(_decision_field(row,"decision_id","")). Key presence matters: explicit null verification is passed to normalize_timestamp, not automatically replaced with creation. P4's replay predicate and ORDER BY must share this expression; do not assume SQL coalesce is identical for historical nulls. P1's generic verified ordering remains unchanged. Preserve replay's bool(is_correct), validity skips and eta/override/penalty/phase logic.

When checkpoint_id is present, begin_export reads that checkpoint, its corresponding centroid tensor and metadata in the SAME pinned view as the replay range. The first logical export record is its full replay-checkpoint envelope; it is included in manifest counts/checksum. Validate factor hash, centroid shape and usable replay_state/cursor before applying anything to a private fresh scorer. Restore centroids and _restore_checkpoint_replay_state (counts, decision_count, category phases/freeze points, buffer and gated/applied counts) FIRST. Preserve from_preset's existing constructor/local-DK/temperature initialization semantics; this query change does not silently add a new restore policy for DK or temperature. The separate rollback/model-state APIs retain their existing restoration rules and evidence.

Let B=(checkpoint replay_cursor_verified_at,replay_cursor_decision_id). Return/apply ONLY Decision tuples K>B, through the optional inclusive upper key and captured snapshot. The checkpoint already accounts for prefix K<=B, including rows since archived; do not replay that prefix again or subtract its historical counters. If a broad diagnostic input contains both sides of B, prefix records may be audited but MUST NOT be fed to update(). Never apply a checkpoint halfway through a stream that was already replayed from bootstrap. An upper bound below B is invalid for that checkpoint; choose an earlier checkpoint or bootstrap. Once begun, newly created checkpoints do not replace the selected one between pages.

No usable cursor/state/hash means the existing explicit rebuild branch: discard the partially restored private state, start from preset bootstrap and replay the COMPLETE active verified population, including its prefix, once. Preserve the current no-active-row/restored-centroid behavior rather than manufacturing replay data. Do not infer a replay boundary from verified_count, page offset or creation time. Active-only rebuild cannot promise to reconstruct removed archived evidence; that scope is explicit and is not relabeled all-history.

Archive-inclusive replay is an explicit offline diagnostic: include_archived=True, checkpoint_id=None, and an explicit through pair. It starts at bootstrap, uses active+archived normalized verified Decisions and Outcomes once per governed decision identity, with canonical archive revision at the pinned snapshot; conflicting revisions cause an explicit ambiguity error rather than duplicate learning. It never silently becomes the normal startup path and never publishes into the live scorer without a separately governed restore. Full evidence exports continue to retain every archived revision, independently of replay's canonical-event view.

Advance after the final COMPLETE logical Decision record, not a partial EvidenceChunk and not the last successfully learned row (invalid skipped rows must still advance). Retry/resume reassembles and validates chunks, consumes each decision once in private state, and publishes only after terminal manifest validation. If the snapshot/handle expires, discard private replay state and restart from the same validated checkpoint or rebuild; never splice streams. Startup readiness waits for completion. P4/P6 tests cover reversed created/verified order, explicit-null verification, tied timestamps, archived prefix, unusable checkpoint, a page straddling B, skips, page retry and new checkpoints appearing during traversal.

## §5 Per-entry consumer manifest and comprehension inventory

This table preserves every Appendix A ID. Line numbers identify the inspected working tree, not future patch offsets. `S/P/R/J/E` refer to the exact capabilities in §§2–4; recipes below specify parameters. `G0`, `EXISTS`, v2 `HISTORY`, and eligible `VERIFY` use the generic API or existing scalar/point methods; `KEEP` requires no migration. Other entries need supplemental semantics or explicitly offline traversal. Empty filters mean `DecisionFilter()`; tenant/legacy/namespace policy is always injected before selection. Rows marked `POL` are P2 prerequisites, not permission for P3 to edit them.

| # | File:line / symbol | Existing read / pattern | Contract / exact migration recipe | Stage |
|---:|---|---|---|---|
| 1 | `copilot_sdk/graph/legacy_signal_filter.py:226` — `_count` | legacy visible count incl archive; currently scans both; is_legacy_signal_decision; self._store.get_all_decisions; self._store.get_archived_decisions | **POL**: Policy-native scalar; preserve archive flag, tenant/default and legacy key-presence rules. | P2 |
| 2 | `copilot_sdk/graph/legacy_signal_filter.py:74` — `get_all_decisions` | all active visible rows; is_legacy_signal_decision; self._store.get_all_decisions | **OFF**: Legacy API unchanged; migrated callers use Q or E, never implement all-history by one page. | P2 |
| 3 | `copilot_sdk/graph/legacy_signal_filter.py:217` — `save_centroids` | count persisted with centroid; self.count_decisions | **G0**: Existing scalar delegation; no query. | P2 |
| 4 | `copilot_sdk/graph/memory_store.py:2445` — `_contextual_judgment_with_view` | context traversal over in-memory view; decision.get; view.get_all_decisions | **KEEP**: In-memory reference traversal unchanged, not production query fallback. | P2 parity; preserve traversal/checkpoint behavior |
| 5 | `copilot_sdk/graph/memory_store.py:2515` — `_query_similar_with_view` | similarity traversal plus point lookup; _decision_supplier; view.get_all_decisions; view.get_decision | **KEEP**: Preserve reference geometry; native top-k contract for migrated production callers. | P2 parity; preserve traversal/checkpoint behavior |
| 6 | `copilot_sdk/graph/memory_store.py:1475` — `count_verified` | verified scalar; self.count_verified_decisions | **G0**: Keep alias to count_verified_decisions. | P2 parity; preserve traversal/checkpoint behavior |
| 7 | `copilot_sdk/graph/memory_store.py:1675` — `save_centroids` | checkpoint decision scalar; self.count_decisions | **G0**: Keep count_decisions. | P2 parity; preserve traversal/checkpoint behavior |
| 8 | `copilot_sdk/graph/namespace.py:148` — `get_decisions` | legacy bounded rows; self._store.get_decisions | **POL**: Preserve old delegate; bounded namespace variant forwards Q and rewrites domain. | P2 |
| 9 | `copilot_sdk/graph/namespace.py:170` — `get_verified_decisions` | legacy verified rows; self._store.get_verified_decisions | **POL**: Preserve old delegate; new scoped capabilities must be explicitly advertised. | P2 |
| 10 | `copilot_sdk/graph/namespace.py:158` — `get_all_decisions` | legacy full collection; self._store.get_all_decisions | **POL**: Keep compatibility; no migrated online caller may use it. | P2 |
| 11 | `copilot_sdk/graph/namespace.py:342` — `count_decisions` | total scalar; self._store.count_decisions | **G0**: Forward scoped count. | P2 |
| 12 | `copilot_sdk/graph/namespace.py:180` — `count_verified` | verified scalar; self._store.count_verified | **G0**: Forward scoped count. | P2 |
| 13 | `copilot_sdk/graph/namespace.py:336` — `count_correct` | correct scalar; self._store.count_correct | **G0**: Forward scoped count. | P2 |
| 14 | `copilot_sdk/graph/outcome_service.py:56` — `_commit` | post-commit verified scalar; self.store.count_verified_decisions | **G0**: No change; regression test transaction visibility. | Unchanged; scalar-count regression P2/P6 |
| 15 | `copilot_sdk/graph/projection.py:313` — `get_category_breakdown` | category verified counts/correct counts; decision.get; self.get_verified_decisions | **PROFILE**: Native profile_v1: historical first-10000 cohort, not all-history; v2 all-history explicitly versioned. | P3/P4 constructor and query contract |
| 16 | `copilot_sdk/graph/projection.py:326` — `get_profile_snapshot` | V/C and category profile; self.count_correct; self.count_verified | **PROFILE**: Atomic profile_v1 mixed-cohort semantics retained; never label capped breakdown complete. | P3/P4 constructor and query contract |
| 17 | `copilot_sdk/graph/read_diff_runner.py:213` — `_compare_active` | active/verified/archive equality evidence; self._decision_map; self._is_verified; self._merge_verified_fields | **E**: Complete fenced streams on both stores, merge by identity; no truncated comparison. | P6 |
| 18 | `copilot_sdk/graph/tenant_store.py:132` — `count_correct` | tenant correct count; self.get_verified_decisions | **POL**: Native tenant+legacy visibility before aggregate. | P2 |
| 19 | `copilot_sdk/graph/tenant_store.py:135` — `count_decisions` | tenant total count; self.get_all_decisions | **POL**: Native tenant predicate. | P2 |
| 20 | `copilot_sdk/graph/tenant_store.py:126` — `count_verified` | tenant verified count; self.get_verified_decisions | **POL**: Native verified count. | P2 |
| 21 | `copilot_sdk/graph/tenant_store.py:129` — `count_verified_decisions` | tenant verified alias; self.get_verified_decisions | **POL**: Preserve alias. | P2 |
| 22 | `copilot_sdk/graph/tenant_store.py:78` — `get_all_decisions` | tenant full collection; self._store.get_all_decisions | **POL**: Compatibility unchanged; migrated readers Q/E. | P2 |
| 23 | `copilot_sdk/graph/tenant_store.py:84` — `get_verified_decisions` | tenant verified collection; self._store.get_verified_decisions | **POL**: Compatibility unchanged; migrated readers S. | P2 |
| 24 | `copilot_sdk/backend/conservation_utils.py:278` — `_baseline_q` | baseline first200 of tail400; indirect/helper access | **BASE**: S baseline_v1, raw verified provider order; no benchmark exclusion. | P6 |
| 25 | `copilot_sdk/backend/conservation_utils.py:129` — `_state_verified_decisions` | chronological verified conservation; _sort_decisions_chronological; store.get_verified_decisions | **CONS**: S conservation_v1; exact eligibility and caller-configured W, default q400; §2.7. | P6 |
| 26 | `copilot_sdk/backend/conservation_utils.py:477` — `state_counts` | total/V/C and override/category scalars; store.count_correct; store.count_verified; store.count_verified_decisions | **COUNTS**: One coherent S counts; keep different supplied-row versus raw-count policy. | P6 |
| 27 | `copilot_sdk/backend/health_builder.py:66` — `build_graph_health` | graph health total; store.count_decisions | **G0**: Scalar count_decisions; no rows. | P6 |
| 28 | `copilot_sdk/backend/response_materializer.py:104` — `refresh` | all+verified response cache; store.get_all_decisions; store.get_verified_decisions | **DISPLAY**: P7 request-scoped composed S/Q; no cross-request graph cache. | P7 |
| 29 | `copilot_sdk/backend/scoring_router.py:361` — `history` | history full rows plus total; indirect/helper access | **HISTORY**: R history_legacy_v1 full, limit50 (1..100), offset0 (<=10000), legacy mixed-direction order and exact count; v2 Q has versioned ties. | P6 |
| 30 | `copilot_sdk/backend/self_computation_router.py:697` — `_count_correct` | correct count; store.count_correct | **G0**: Scalar canonical verified/correct. | P6 |
| 31 | `copilot_sdk/backend/self_computation_router.py:689` — `_count_verified` | verified count; store.count_verified | **G0**: Scalar canonical verified. | P6 |
| 32 | `copilot_sdk/backend/self_computation_router.py:681` — `_get_all_decisions` | all active convenience helper; store.get_all_decisions | **E**: Eliminate online helper via caller-specific S/Q; E offline only. | P6 |
| 33 | `copilot_sdk/backend/self_computation_router.py:685` — `_get_verified_decisions` | all verified convenience helper; store.get_verified_decisions | **S**: Caller-specific profiles, not universal capped list. | P6 |
| 34 | `copilot_sdk/backend/self_computation_router.py:67` — `_verified` | coalesced verified snapshot; store.get_verified_decisions; verified_reads.run | **S**: Request-local S at common fence; P7 removes cross-request coalescing. | P6 |
| 35 | `copilot_sdk/backend/self_computation_router.py:504` — `decisions` | filtered active/verified decision listing; _matches_decision; _merge_verified_fields; _verified | **SELF**: R self_legacy preserves prelimit filtering; v2 Q/R global-filter semantics. | P6 |
| 36 | `copilot_sdk/backend/switching_cost_router.py:41` — `_decision_count` | switching total; scorer.get_decision_count; store.count_decisions | **G0**: Scalar count. | P6 |
| 37 | `copilot_sdk/backend/switching_cost_router.py:30` — `_decision_records` | earliest created_at/timestamp/createdAt; store.get_all_decisions | **AGE**: S switching_age_v1 min of all parsable candidate fields. | P6 |
| 38 | `copilot_sdk/backend/transfer_router.py:213` — `_pattern_dollar_impact` | pattern dollar impact; store.get_all_decisions | **MONEY**: S transfer_router_v1 first numeric field per row in source+target, unless pattern override. | P6 |
| 39 | `copilot_sdk/scoring/composite_gate.py:78` — `outcomes_from_state` | non-null outcomes sorted chronological; chronological_decisions | **GATE**: S composite_v1 with actual configured w_long/w_short, defaults400/20; native window totals, null excluded (§2.7). | P6 |
| 40 | `copilot_sdk/scoring/gate_enforced_scorer.py:122` — `_get_recent_outcomes` | all verified accuracy plus tail gate; chronological_decisions | **GATE**: S gate_v1 full-history C/N plus actual configured window totals (§2.7); no tail-mean substitution. | P6 |
| 41 | `copilot_sdk/scoring/iks_service.py:45` — `_verified_decisions` | per-category verified prefix IKS; _normalize_decision; self._graph_store.get_verified_decisions | **CURVE**: P iks_category_v1; normalized fallback IDs/timestamps preserve provider rank. | P6 |
| 42 | `copilot_sdk/scoring/measurement_state.py:141` — `_verified_decisions` | actual-action measurement coverage; get_verified_count; store.get_verified_decisions | **ARMS**: S measurement_v1 global measured/minimum/needed totals over all configured+unknown arms, independent of pages; actual-first action (§2.5). | P6 |
| 43 | `copilot_sdk/scoring/scorer.py:2704` — `_checkpoint_quality` | checkpoint quality last400; decision.get; self._graph_store.get_verified_decisions | **QUALITY**: S checkpoint_quality_v1 raw provider window and strict-True correctness. | P6 |
| 44 | `copilot_sdk/scoring/scorer.py:2642` — `_compute_iks` | scorer IKS / fingerprint / category coverage; _count_categories_with_n; _is_correct_decision; self._conservation_verified_decisions | **IKS**: S scorer_iks_v1 and fingerprint_v1; preserve synthetic/checkpoint branches. | P6 |
| 45 | `copilot_sdk/scoring/scorer.py:3433` — `_conservation_stats` | conservation raw counts or supplied rows; _conservation_verified_decisions; _is_correct_decision; _is_override_decision | **CONS**: S conservation_v1 with explicit population; no denominator conflation. | P6 |
| 46 | `copilot_sdk/scoring/scorer.py:3110` — `_maybe_archive` | archive beyond keep_recent800; self._graph_store.archive_old_decisions; self._graph_store.count_decisions | **ARCH**: Existing governed archive mutation, E for traversal; do not compute candidates client-side. | P6 |
| 47 | `copilot_sdk/scoring/scorer.py:3197` — `_run_evolution` | evolution arbitrary rule input; decisions[-1].get; self._graph_store.get_verified_decisions | **OFF**: E complete verified stream to explicit offline evaluator; fixed registered rules may use S only with exact adapter. | P6 |
| 48 | `copilot_sdk/scoring/scorer.py:2974` — `_save_centroids_checkpoint` | checkpoint verified count within transaction; self.get_verified_count; transaction.count_verified | **G0**: Keep transaction count; no independent unfenced read. | P6 |
| 49 | `copilot_sdk/scoring/scorer.py:3452,3304` — `_verified_decisions` | method+module all verified snapshots; _is_verified_decision; self._graph_store.get_verified_decisions; self._verified_snapshot_active.get | **S**: Both definitions migrate to named S/P/R or E; remove generic online list dependency. | P6 |
| 50 | `copilot_sdk/scoring/scorer.py:1981` — `capture_existing_state` | capture fingerprint/count/checkpoint identity; self._graph_store.count_verified; self._persist_fingerprint; self.fingerprint | **LOOK**: S fingerprint + counts, R checkpoint lookup exact; no 1000-prefix search. | P6 |
| 51 | `copilot_sdk/scoring/scorer.py:2616` — `export` | scorer JSON export active rows + centroids; self._graph_store.get_all_decisions | **E**: Version2 complete evidence stream including archive, outcomes and manifest. | P6 |
| 52 | `copilot_sdk/scoring/scorer.py:493` — `from_preset` | checkpoint replay verified rows; _replay_verified_decisions; _sort_decisions_chronological; graph_store.get_verified_decisions | **REPLAY**: E active-only verified replay, restore checkpoint first and exclude its prefix (§4.3); advance returned cursor, no offset. | P6 |
| 53 | `copilot_sdk/scoring/scorer.py:2420` — `get_alpha` | alpha C/V rounded4; self._graph_store.count_correct; self._graph_store.count_verified | **G0**: Coherent count pair; unchanged formula. | P6 |
| 54 | `copilot_sdk/scoring/scorer.py:2411` — `get_phase` | phase V<10 or accuracy>=.5; self._graph_store.count_correct; self._graph_store.count_verified | **G0**: Coherent count pair; unchanged thresholds. | P6 |
| 55 | `copilot_sdk/scoring/scorer.py:1121` — `get_verified_count` | verified scalar; self._graph_store.count_verified_decisions | **G0**: Keep canonical count. | P6 |
| 56 | `copilot_sdk/scoring/scorer.py:2306` — `trajectory` | global trajectory verified prefix points; compute_trajectory; self._graph_store.get_verified_decisions | **CURVE**: P trajectory_v1 limit100, rank ASC, full history; preserve point0 and final remainder. | P6 |
| 57 | `copilot_sdk/scoring/trust_traps.py:143` — `_verified_decisions` | chronological trust populations/halves/windows; chronological_decisions | **TRUST**: S trust_v1 rank halves/category counts + tails50/200. | P6 |
| 58 | `apps/trading/backend/app/cli_sdk.py:351` — `_counts` | CLI total/V/C; store.count_correct; store.count_decisions; store.count_verified | **G0**: Scalars. | P8 |
| 59 | `apps/trading/backend/app/cli_sdk.py:519` — `export_sdk` | CLI capped export+verified join; scorer.graph_store.get_decisions; scorer.graph_store.get_verified_decisions; verified.get | **E**: Offline E full version2 JSON/CSV; legacy cap is labeled, not full export. | P8 |
| 60 | `apps/trading/backend/app/cli_sdk.py:486` — `journal_sdk` | CLI last n from first10000 active; decision.get; scorer.graph_store.get_decisions; scorer.graph_store.get_verified_decisions | **CLI**: R cli_journal_v1 legacy cohort; v2 journal capability after P11. | P8 |
| 61 | `apps/trading/backend/app/context_router.py:513` — `_analytics_from_store` | merged all active analytics; _analytics_from_decisions; store.get_all_decisions; store.get_verified_decisions | **TRADE**: S trading_context_v1 + trading_context_summary rolling10/latest regime at one stamp (§2.5), plus paged evidence IDs. | P8 |
| 62 | `apps/trading/backend/app/main.py:316` — `_auto_seed_if_needed` | seed existence; graph_store.count_decisions | **G0**: count or Q summary limit1; no scan. | P8 |
| 63 | `apps/trading/backend/app/main.py:465` — `_run_startup_locked` | startup regime monitor restore all decisions; scorer_proxy.graph_store.get_all_decisions | **OFF**: E complete ordered restore before ready; not an HTTP read. | P8 |
| 64 | `apps/trading/backend/app/main.py:729` — `clone_fingerprint` | clone empty memory fingerprint; compute_fingerprint; store.get_verified_decisions | **EMPTY**: Pure empty-input reference result, no alternate production graph query. | P7/P8 |
| 65 | `apps/trading/backend/app/routers/analytics.py:131` — `_verified_decisions` | verified analytics fields/factors/quality; get_verified | **TRADE**: S trading_analytics_v1, vol_sharpe_v1, vrp_v1, regime_vrp_v1, dispersion_v1. | P8 |
| 66 | `apps/trading/backend/app/routers/claim_gate_router.py:21` — `claim_gate` | tested/powered/survived/impact; store.count_correct; store.count_verified; store.get_all_decisions | **MONEY**: S claim_gate_v1 distinct first-not-None monetary coercion. | P8 |
| 67 | `apps/trading/backend/app/routers/execution_router.py:26` — `_trades` | imported trades plus active decisions; store.get_all_decisions | **JEXEC**: Move to P11; S execution_v1 over governed union WITHOUT journal dedup. | P11 (moved from P8) |
| 68 | `apps/trading/backend/app/routers/journal.py:217` — `_journal_records` | import/manual/Decision journal plus overlays; store.get_all_decisions | **J**: J graph union, native offset0..10000, cursor, exact filters/totals/order, alias/history migration (§3.4). | P11 |
| 69 | `apps/trading/backend/app/routers/promotion.py:86` — `_conservation_status` | promotion conservation + journal reads; count_correct; count_total; count_verified | **CONS**: Scalar/category counts P8; journal-dependent route cutover P11. | P8 |
| 70 | `apps/trading/backend/app/routers/regime_analytics.py:38` — `_read_decisions` | all active + verified regime analytics; decision.get; get_decisions; get_verified | **REG**: S trading_regime_v1 nested context rules, not generic regime. | P8 |
| 71 | `apps/trading/backend/app/services/claim_gate.py:92` — `refresh_from_store` | claim registry verified existence; graph_store.get_verified_decisions | **EXISTS**: Q summary verified=True limit1. | P8 |
| 72 | `apps/trading/backend/app/services/pre_scorer.py:223` — `_all_decisions` | all active candidate cosine matches; indirect/helper access | **SIM**: R prescore_topk_v1 category filter top5, rounded6 score DESC, legacy-rank tie. | P8 |
| 73 | `apps/trading/backend/app/services/pre_scorer.py:230` — `_verified_decisions` | prescore category/regime accuracy; indirect/helper access | **REG**: S prescore_regime_v1; distinct unknown-regime policy. | P8 |
| 74 | `apps/trading/backend/app/services/promotion_engine.py:196` — `_category_decisions` | category stage-rank verified outcomes; decision.get | **PROM**: S promotion_v1 rank_start=stage_start_count; all stage count/accuracy. | P8 |
| 75 | `apps/trading/backend/app/services/regime_classifier.py:154` — `_verified_decisions` | regime classifier verified counts; indirect/helper access | **REG**: S regime_classifier_v1; named resolver/defaults. | P8 |
| 76 | `apps/trading/backend/app/services/trader_profiles.py:82` — `_verified_decisions` | trader/category/actual-action profiles; get_verified | **TRADER**: S trader_profiles_v1 paged groups, strict correctness and valid action terms. | P8 |
| 77 | `apps/trading/backend/app/state/compute_helpers.py:26` — `compute_all_decisions` | active rows first configured limit; get_decisions | **ROWS**: Q full only if provider cohort matches; otherwise R active_legacy limit50. | P8 |
| 78 | `apps/trading/backend/app/state/compute_helpers.py:259` — `count_decisions` | display total; count | **G0**: Scalar. | P8 |
| 79 | `apps/purchasing/backend/app/main.py:408` — `_auto_seed_if_needed` | seed existence; graph_store.count_decisions | **G0**: Count or Q summary1. | P9 |
| 80 | `apps/purchasing/backend/app/main.py:747` — `_graph_order_rows` | all graph order rows by item; app.state.purchasing_selected_graph_store.get_all_decisions | **PAR**: S purchasing_orders_v1; actual item quantities/date population, no invented orders. | P9 |
| 81 | `apps/purchasing/backend/app/main.py:807` — `predictive_par` | item predictive PAR full-history usage; request.app.state.graph_store.get_all_decisions | **PAR**: S par_v1 sufficient statistics plus sample guard. | P9 |
| 82 | `apps/purchasing/backend/app/main.py:821` — `predictive_par_week` | week7 by item predictive PAR; request.app.state.graph_store.get_all_decisions | **PAR**: S par_v1 batched item/date requests; preserve availability. | P9 |
| 83 | `apps/purchasing/backend/app/routers/auto_order_router.py:148` — `_category_verified_decisions` | category verified, excluding sample data; _decision_allowed_for_metric; _decision_category; _is_verified_decision | **AUTO**: S purchasing_auto_v1 nested category and verification policy. | P9 |
| 84 | `apps/purchasing/backend/app/routers/auto_order_router.py:140` — `_store_for_state` | find GraphStore object; indirect/helper access | **KEEP**: No data read; preserve factory and capability selection. | P9 |
| 85 | `apps/purchasing/backend/app/routers/evidence.py:235` — `_all_decisions` | evidence all rows fallback and top factors; indirect/helper access | **PUR**: S purchasing_evidence_v1 + R valid last25; raw metadata needed for factor recomputation. | P9 |
| 86 | `apps/purchasing/backend/app/routers/evidence.py:246` — `_verified_decisions` | verified evidence rows; get_verified | **PUR**: Same profile, strict correctness and valid terms. | P9 |
| 87 | `apps/purchasing/backend/app/routers/iks.py:61` — `_supplier_rows_from_graph` | supplier OTIF/exceptions/invoice prices/seasons; store.get_verified_decisions | **SUP**: S supplier_iks_v1 + supplier_details prices/seasons (§2.5); last5 each category, lossless values and names. | P9 |
| 88 | `apps/purchasing/backend/app/routers/learning_beats.py:186` — `_verified` | proof ledger every verified prefix; indirect/helper access | **PCURVE**: P purchasing_competence_v1 stride1 plus R proof last25; HTTP v2. | P9 |
| 89 | `apps/purchasing/backend/app/routers/regime_router.py:36` — `_payload` | regime conditioner payload; indirect/helper access | **REG**: S conditioner_v1, normalized verified/correct/rejection counts. | P9 |
| 90 | `apps/purchasing/backend/app/routers/scorecard_router.py:123` — `_verified_decisions` | supplier scorecard Decision exceptions; indirect/helper access | **SUP**: S supplier_scorecard_v1; external QBO inputs remain separately provenanced. | P9 |
| 91 | `apps/purchasing/backend/app/routers/trust_router.py:161` — `_decisions_total` | trust decisions_total is verified count; count_verified | **G0**: Keep semantic V, do not substitute active total. | P9 |
| 92 | `apps/purchasing/backend/app/routers/verify_router.py:160` — `_already_verified` | already verified ID; decision.get; get_verified; str(decision.get('status') or '').lower | **EXISTS**: Existing point get or Q summary decision_ids=(id,), verified=True, limit1; atomic write check retained. | P9 |
| 93 | `apps/purchasing/backend/app/services/purchasing_control.py:198` — `_decisions` | control all active / proof / twin; self._store().get_all_decisions | **CTRL**: R control_proof_v1 last100 dedup; twin_v1 last200 lexicographic-created cohort. | P9 |
| 94 | `apps/purchasing/backend/app/services/purchasing_control.py:206` — `_verified` | control verified rows; self._store().get_verified_decisions | **CTRL**: Same R + S counts; no all verified materialization. | P9 |
| 95 | `apps/purchasing/backend/app/services/purchasing_control.py:67` — `refresh` | control registry verified existence; graph_store.get_verified_decisions | **EXISTS**: Q summary verified=True limit1. | P9 |
| 96 | `apps/purchasing/backend/cli.py:430` — `backup` | CLI full backup active+verified; _backup_decision; store.get_all_decisions; store.get_verified_decisions | **E**: E version2 complete active+archived+outcomes evidence. | P9 |
| 97 | `apps/purchasing/backend/cli.py:375` — `conservation` | CLI conservation counts/category support; store.count_categories_with_n; store.count_correct; store.count_decisions | **CONS**: S counts/categories; formulas unchanged. | P9 |
| 98 | `apps/dataops/backend/app/context_router.py:119` — `_graph_decisions` | DataOps normalized decisions; _decision_store; _normalize_live_decision | **DOR**: R dataops_rows_v1, actual-action/system/correct predicates; limit1..100. | P10 |
| 99 | `apps/dataops/backend/app/context_router.py:1207` — `accuracy_by_category` | per-category correctness/trend on all active; indirect/helper access | **DOACC**: S dataops_accuracy_v1, pending included, per-category provider-rank halves. | P10 |
| 100 | `apps/dataops/backend/app/context_router.py:856` — `pipelines` | pipeline groups; _pipelines_from_decisions | **DOG**: S dataops_pipelines_v1 top-level system aliases, exact counts. | P10 |
| 101 | `apps/dataops/backend/app/context_router.py:1341` — `process_timeline` | all process timeline activities; decision.get | **DOR**: R dataops_timeline_v1 cursor pages; v2 response. | P10 |
| 102 | `apps/dataops/backend/app/context_router.py:904` — `rsi_summary` | trajectory/epoch/transfer-pattern summary; _rsi_pattern_counts; _trajectory_iks; scorer.trajectory | **RSI**: S rsi_v1 + P curve summary; remove60sec graph cache; curated timeline labeled fixture. | P10 |
| 103 | `apps/dataops/backend/app/context_router.py:1312` — `schema_impact` | column/schema impact; _schema_impact_count; decision.get | **DOG**: S schema_impact_v1 normalized category-column match, no invented system filter. | P10 |
| 104 | `apps/dataops/backend/app/context_router.py:1254` — `transformations` | transformations per system; decision.get | **DOG**: S transformations_v1 preserves missing-system fallback and existing duration-key result. | P10 |
| 105 | `apps/dataops/backend/app/main.py:551` — `_auto_seed_if_needed` | seed existence; graph_store.count_decisions | **G0**: Count or Q summary1. | P10 |
| 106 | `apps/dataops/backend/app/routers/di_gateway_router.py:23` — `verification_history` | recent category verification history; decision.get; store.get_decisions; store.get_verified_decisions | **VERIFY**: Q scoring category, limit100<=400, created DESC; no all-verified join; page-only summary. | P10 |
| 107 | `apps/dataops/backend/app/routers/regime_router.py:36` — `_payload` | regime payload; indirect/helper access | **REG**: S conditioner_v1. | P10 |
| 108 | `apps/dataops/backend/app/services/source_trust.py:40` — `compute_source_trust` | factor/source trust plus fingerprint delta; _decision_factors; _decision_sources; graph_store.get_verified_decisions | **SOURCE**: S source_trust_v1 and R previous-fingerprint exact predecessor; DK weights distinct. | P10 |
| 109 | `copilot_sdk/demo/bundle.py:173` — `_restore` | demo restore counts and point gets; _decision_payload; counts.values; decision.get | **KEEP**: Already bounded reads; evolution event scan uses explicit complete traversal if >1000. | P6 |
| 110 | `copilot_sdk/di/enrichment.py:329` — `_read_verified_decisions` | DI arbitrary group/metric callbacks; graph_store.get_verified_decisions | **OFF**: E complete offline evaluation; built-in registered profiles S; unknown callbacks never online fallback. | P6 |
| 111 | `copilot_sdk/di/nl_query.py:81` — `_decisions` | NL latest5 or registered plan; graph_store.get_verified_decisions | **DI**: R di_recent_v1 verified provider last5 full; typed plan for built-ins; offline unknown callbacks. | P6 |
| 112 | `copilot_sdk/di/query_providers.py:112` — `_decisions` | verified else all, source usage, invoice IDs; indirect/helper access | **DI**: S di_sources_v1 + R di_rows_v1; batched exact membership<=1000. | P6 |
| 113 | `copilot_sdk/outcome/router.py:25` — `count` | outcome processor count; processor.count_verified | **G0**: Keep scalar, no query. | P6 |
| 114 | `copilot_sdk/reporting/weekly.py:91` — `generate` | weekly category/cost/price/prefix summary; decision.get; self._store.get_all_decisions; self._verified_by_id | **WEEK**: S weekly_v1 built-in cost rules; custom cost callback E offline; paged price groups. | P6 |
| 115 | `copilot_sdk/reporting/weekly.py:160` — `_window_verified` | verified created-window for report; decision.get; self._store.get_verified_decisions | **WEEK**: S weekly_v1: created>=max(active.created)-days, not verified time. | P6 |
| 116 | `copilot_sdk/transfer/cross_domain.py:95` — `insights` | pattern impact plus source/target evidence IDs; self.store.get_all_decisions | **TRANSFER**: S cross_domain_v1 + R transfer_evidence_v1 paged IDs; field precedence differs from router. | P6 |
| 117 | `copilot_sdk/migrate/shadow_scorer.py:350` — `_category_coverage_alpha` | shadow actual category-index support; count_categories_with_n; get_verified | **COVER**: S shadow_coverage_v1; non-null unknown indices count, no clamping. | P6 |
| 118 | `copilot_sdk/migrate/verify_state.py:150` — `count_correct` | offline mirror correct count; self.get_verified_decisions | **KEEP**: Leave offline local-map implementation; do not advertise bounded production capability. | P6 |
| 119 | `copilot_sdk/migrate/verify_state.py:133` — `count_verified` | offline mirror verified count; self.get_verified_decisions | **KEEP**: Unchanged. | P6 |
| 120 | `copilot_sdk/migrate/verify_state.py:136` — `count_verified_decisions` | offline mirror verified alias; self.count_verified | **KEEP**: Unchanged. | P6 |
| 121 | `copilot_sdk/migrate/verify_state.py:259` — `replay_decisions` | migration full replay; _normalise_decision; store.add_decision; store.get_verified_decisions | **REPLAY**: E complete offline, pinned creation order; no bounded prefix substitution. | P6 |
| 122 | `copilot_sdk/migration/rehearsal.py:56` — `_existing` | rehearsal existing IDs; store.get_all_decisions | **EXISTS**: Point/batch membership<=1000; E if total full audit requested. | P6 |


### 5.1 Generic recipes and projection allowlist decisions

- **G0**: retain existing truly native count/point methods; when filter needed use count_decisions(domain, filters=DecisionFilter(...)). For verified count use verified=True; correct count verified=True,correct=True. Multiple related counts need one read stamp/transaction, not four independent moving snapshots.
- **EXISTS**: query_decisions(domain, filters=DecisionFilter(verified=True[, decision_ids=(id,)]), projection="summary", page=DecisionPageRequest(limit=1,order_by="created_at",descending=True)). Any item means exists. Seed checks omit verified. No total query needed.
- **HISTORY**: legacy-compatible history_legacy_v1, full, no filters, requested limit/offset with legacy mixed-direction timestamp/ID ties and exact count. Offset<=10000. V2 Q uses after and offset0 with the P1 total order; tied-timestamp changes are versioned.
- **VERIFY**: scoring projection, categories=(requested_category,), page limit=min(requested,400), created_at DESC, verified filter ONLY when the existing endpoint selects exclusively verified rows. Verification-history currently includes pending candidate rows and merges any Outcome; preserve that cohort and page-only metrics.
- **Q for ordinary recent rows**: select explicit limit, order_by and descending; never rely on P1 default direction for a legacy L-ordered caller. Do not apply application filtering after LIMIT unless the legacy-cohort profile explicitly requires it.
- **S/P/R/J**: use the exact named request profile and selectors described in §§2–3, BoundPage(100), stamp from the same scoped consumer_snapshot; final pages may be shorter due to bytes. Full group traversals are offline except configured finite group outputs<=1000. UI group lists page instead of accumulating silently.
- **E/OFF/REPLAY**: no HTTP loop over all pages; explicit offline work, complete manifest, no serving cache. Full backups explicitly set include_archived=True; startup replay selects active-only with ReplayBoundary (§4.3). DK refresh is synchronous, not an E/OFF operation (§2.6).
- **POL/KEEP**: infrastructure/unchanged entries remain ledger evidence, not newly migrated endpoints.

Projection allowlists from v3 are **not widened**. summary is identity/category/action/confidence/status/timestamps/correctness. scoring adds the frozen factor/vector/probability/index/action/outcome/version/source fields and only learning_metadata reward/verifier/override_reason/variant_id/regime_tag. journal adds named trade fields/factors/tags/text, but NOT arbitrary metadata/entity_id. full is complete Decision+Outcome evidence without internal fields. Supplier, source, monetary and contextual-regime selectors frequently need nested metadata not in scoring; use the typed native profile, not hidden metadata expansion. JournalQueryCapability is a separate fact-union view; generic projection="journal" does not suddenly include manual/imported facts.

### 5.2 Additional sites discovered beyond the planning122

These are part of the amended file manifests, not renumbered substitutions for Appendix A.

| Site | Exact migration |
|---|---|
| namespace.count_verified_decisions:186 | P2 alias/scoping regression; scalar unchanged. |
| scorer.from_preset replay loop, coordinate-estimation and checkpoint lookup callers | P6 complete active-only replay after checkpoint (§4.3); synchronous local DK plus estimate_graph_dk fallback (§2.6); R exact checkpoint lookup; never fixed cursor plus changing offset. |
| self_computation_router decision-flow, counterfactual, audit/lineage/replay helpers | P6 recent rows<=200, full-population native counts/reward/override totals; counterfactual window<=400; exact checkpoint/Decision lookup; page fact histories. |
| di/query_providers source usage and enterprise invoice membership | P6 di_sources_v1 and invoice_membership_v1; avoid fetching all invoice IDs. |
| Trading main.py:604, routers/correlation.py:36 | P11 J correlation profile, count + first20 tickers; external return math unchanged. |
| Trading routers/prescore.py:49 | P11 J prescore profile plus regime accuracy; no whole journal list. |
| Trading routers/regime.py:44,67; routers/vix_timing.py:38 | P11 J regime/VIX profiles, governed market observations; external fetch bounded by date chunks. |
| Trading routers/evidence.py:98,218; evidence_providers.py:95 | P11 exact governed identity/annotation lookup. Existing similar-trades cohort remains category400 then top5; distinct from pre_scorer all-history top5. |
| Trading context_router.py:774,786,809,910–919 | P11 replace import-list analytics and JSON metadata read/write. Non-reducible pattern/trust analysis uses explicit offline operation, not capped online input. |
| Trading state/trading_registry.py:111,122,138; compute_helpers.py:221,238; trading_materialization.py:87 | P7 removes cross-request serving; P11 migrates remaining journal population to graph contracts in one release. No _StaticDecisionRows surrogate graph after cutover. |
| Trading duplicate data_import /trades routes | P11 one route owner; journal router currently wins mounting order. Preserve aliases deliberately, test route resolution. |
| Trading CLI status first10000[-1] and import dedup | P8 preserve labeled legacy status cohort or explicitly version latest; P11 exact broker membership without prefix cap. |
| Purchasing proof/control/frozen-twin dependent reads | P9 P curve stride1, proof100 precedence/dedup, twin200 lexicographic-created before validity. |
| DataOps context system history/pipeline decisions/RSI cache | P10 R normalization policies, preserve limit0 behavior per endpoint, remove graph-derived60sec cache; fixed fixture labels remain. |
| weekly supplier price changes and arbitrary cost callbacks | P6 paged groups; callback jobs offline with complete E input. |

Additional profiles needed by these direct callers:
- history_legacy_v1: full active rows, legacy_order=age_recent (memory_recent for old memory callers), window=limit1..100, rank_start=offset0..10000; total before offset. Cursor and nonzero offset are mutually exclusive. Generic-created v2 may use Q; v1 preserves legacy ties.
- decision_flow_v1 statistics: totals total:int,verified:int,correct:int,overrides:int,confidence_n:int,confidence_sum:float,reward_n:int,reward_sum:float; category groups n:int,c:int. Reward first top/context/outcome_metadata/metadata reward,signed_reward,score_reward; finite confidence only, round6 after mean. Override actual not in (None,recommended,action). Recent R decision_flow_rows_v1 uses numeric created else verified else0,id DESC, full, limit50<=200.
- counterfactual_rows_v1: full raw verified L[-window:], window20 default<=400, return L order; caller rescoring unchanged.
- fact_history_v1: exact target identifiers, full governance/audit/checkpoint relationship facts, timestamp/id ASC; only whitelisted relationship kinds from existing reader, never arbitrary Cypher.
- evidence_similar_v1: category earliest/current legacy400 cohort, exclude target, common named factors, round6 cosine DESC stable L, top5; outcome already joined, no N+1 point calls.
These schemas belong to the same closed registries; no new protocol required.

Self-row requests use explicit action/outcome/verified_only fields. For self_legacy_v1, verified_only=True selects all raw verified before filtering, then takes limit (default50,max500); False takes first limit recent active, joins its Outcome, then filters. action matches recommended OR actual OR action, outcome is exact equality to the existing outcome field. matched_count reproduces the old total rule: all active only for completely unfiltered non-verified query, otherwise filtered cohort count. self_rows_v2 filters globally with exact global matched_count on its separate versioned endpoint.

DIQueryService.compute filters time then takes first max_records and then aggregates. P6 changes query_service.py and query_providers.py together: a bounded provider entry point receives the parsed plan, fixed reference time and max_records, returning the di_rows_v1 cohort; compute must not evaluate a different second clock boundary. Preserve the current parser: numeric token defaults30; a string ending singular month means30 days, singular week7 days, otherwise the numeric token is days (plural tokens are not silently fixed). requested_sources affects attribution, not row selection. At-most1000 rows can feed the unchanged metric computation; label this existing cohort, not all-history. Enterprise invoices retain snapshot reference time and exact batched graph membership. Custom NL QueryPattern/enrichment callbacks remain complete offline work.

## §6 HTTP compatibility plan

### 6.1 Version boundary and bounded envelope

Introduce explicit **/api/v2/** routes, retaining the remainder of the existing mounted path (for example /api/v2/trajectory, /api/v2/trading/journal/trades). Never change an existing list into a page while leaving the same response model/name. New models in SDK backend/models.py: BoundedPageMeta(schema_version:str, cursor:str|None, has_more:bool, population_count:int, read_epoch:int), TrajectoryPageResponse(points:list[TrajectoryPointResponse], final_point:TrajectoryPointResponse, days_active:float, page:BoundedPageMeta), DecisionPageResponse(decisions:list[dict[str,object]], page:BoundedPageMeta), GroupPageResponse(groups:list[dict[str,object]], totals:dict[str,object], page:BoundedPageMeta), OfflineAnalysisResponse(status:Literal["offline_required"], export_url:str, reason:str). App models reuse envelope and their existing row models; serializers enforce profile schema rather than accepting arbitrary fields.

These HTTP models are transport views of frozen capability dataclasses; they do not replace those dataclasses. Time uses existing JSON number/string conventions per row, cursor is opaque, read_epoch is not an historical-time selector. New pages default100, max1000 and2MiB; new generic offset remains0..10000 and exclusive with cursor; supplemental routes expose cursor only except journal, whose bounded offset contract is §3.4. Invalid cursor/filter422, scope denial403, changed snapshot409 with code read_changed, too-large-record413 with offline export route, graph unavailable503, deadline504, no results200 with empty page and exact zeros. No stale success on graph outage.

P6 adds v2 shared SDK routes without switching existing clients. P7 ships all three bundled clients and shared tab projection changes together; P9/P10/P11 do their domain route/model/client switches atomically. V1 bounded responses remain compatible where §6.2 says preserve. Unbounded v1 routes cannot be honestly supported by returning a capped prefix: advertise deprecation in the introducing release, retain until the coordinated versioned client cutover, then return documented410 with successor URL and offline-export option. This is an explicit API retirement in that release, not a silent payload change. Tests cover old bounded contracts and the deliberate410 contract. External users must have a release note/migration window before activation; code installation alone does not activate retirement.

A v2 frontend fetches page1 plus exact summary/final_point; "load more" follows the cursor, never infers completion from page length. It labels partial curves as partial history and displays all-history final summary separately. It discards prior pages on409 and restarts once; it does not merge two epochs or load every page in a render loop. Versioned request-coalescing keys include route/version, tenant, domain and normalized filters; no graph-result cache survives request boundaries on the server.

### 6.2 Endpoint/model compatibility matrix

Paths below are router suffixes under their existing mount; v2 prefix rule above is exact. Non-Decision connector/fixture endpoints not fed by these consumer sites retain their explicit external/fixture provenance.

| Owner / endpoint(s) | Current shape/behavior | Proposed response and compatibility |
|---|---|---|
| SDK /history | ScoringHistoryResponse: engine,decisions,total,limit,offset;50,1..100,offset<=10000 | Preserve v1 full row keys and counts. Add v2 DecisionPageResponse cursor. |
| SDK /trajectory | TrajectoryResponse includes whole points array, totals/summary | v2 TrajectoryPageResponse BEFORE client change; unchanged existing prefix values. Unbounded v1 retires at P7 activation, never newest400 as full. |
| SDK /fingerprint,/measurement-state and /{copilot}/measurement-state,/health,/diagnostics | Named FingerprintResponse,MeasurementStateResponse,ScoringHealthResponse,DiagnosticsResponse | Scalar/fixed-shape responses preserved. Oversized dynamic group lists use v2 paged group subresources, with all-history scalar summary. |
| SDK /score,/learn | ScoreResponse/LearnResponse with embedded display data | Preserve mutation receipt and frozen score fields; v2 embedded curve field becomes summary+page URL, not whole curve. Existing bounded embedded fields unchanged. |
| Self /decisions | SelfDecisionsResponse, prelimit/filter asymmetry and merged verified fields | v1 legacy profile only within existing bound; v2 global predicate + exact matched_count, actual/recommended OR explicitly supported. No silent total semantic change. |
| Self /decision-flow | DecisionFlowResponse recent list<=200 + all-history aggregates | Preserve bounded recent shape and totals; native aggregates. v2 only if arbitrary categories exceed group bound. |
| Self /centroid-history,/centroid-timeline | CentroidHistoryResponse lists | v2 page checkpoint rows; preserve existing bounded v1 limit. |
| Self /centroid-history/{id}/counterfactual | CounterfactualResponse window<=400 | Preserve window and output; exact checkpoint lookup and R raw verified window. |
| Self /centroid-history/{id}/lineage,/replay; /decisions/{id}/checkpoints; /audit-trail | FlexibleResponse/history rows | Exact point/relationship query; v2 bounded fact page, complete offline replay via offline-required response where stateful work unbounded. |
| Self /accuracy-by-category,/accuracy-alerts,/trust-traps | AccuracyByCategoryResponse/FlexibleResponse category metrics | Same formulas; paged dynamic group v2; no prefix means. |
| Self /evolution/summary,/rule-genealogy,/rule-lifecycle/{id} | Summary or graph histories | Keep bounded summary, v2 fact pages for histories; arbitrary evolution offline. |
| Transfer /opportunities,/transfers and transfer result evidence | FlexibleResponse/TransferListResponse, pattern/provenance ID arrays | Preserve scalar counts/impact; v2 paged pattern/evidence arrays. /execute,/transfer remain governed writes. |
| Trading /journal/trades,/trades | trades,count(paged),total,filters,aggregate; special unfiltered-empty only trades/count | v1 bounded adapter preserves special shape, inclusive end-date and offset. v2 JournalPage includes exact totals and cursor, explicit kind-qualified identity. |
| Trading /trades/{id}, /evidence/{id} | Single normalized trade / evidence with camel+snake aliases | Preserve aliases and field precedence; identity lookup plus annotations. v2 kind-qualified selector resolves ambiguous aliases,409 if unresolved collision. |
| Trading /journal/entry, reflection/tags PUT, /trade-metadata POST | Written record/status, JSON side effects | Receipt-backed graph writes; v1 response adapter keeps fields, v2 adds revision/idempotency identity. |
| Trading /trade-metadata GET | Entire id→metadata mapping | v2 annotation page; retire unbounded v1 at P11 activation; exact ID GET remains bounded. |
| Trading /analytics (journal and context mounts) | AnalyticsResponse grouped stats or context analytics | Preserve exact population of winning registered route; test duplicate mount resolution. v2 grouped page plus exact totals. |
| Trading /import/csv,/import/broker | imported,total,trades (unbounded batch echo) | v2 bounded batch receipt + result-page cursor; version upload max100 rows/batch and duplicates policy; v1 bulk workflow becomes offline import job. |
| Trading POST /trading/journal/query | All matching trade rows, best/worst and explanation | v2 JournalPage + normalized query/explanation, no capped residual filter; local-calendar date basis and pnl-null-as0 preserved. |
| Trading /similar,/prescore,/claim-gate,/promotion,/regime-analytics,/trader profiles | Bounded matches or group metrics | Preserve fixed outputs; top-k native selection. Dynamic profiles use v2 group pages. |
| Trading /correlation,/regime,/regime/detail,/vix-timing | Fixed matrices/metrics or dynamic category recommendations | J summaries + external observation provenance, matrices unchanged; dynamic groups page; non-reducible recommender detail uses explicit offline operation when needed. |
| Trading /execution analytics,/trust-analysis,/patterns,/conservation-breakdown | Imported/Decision analyses | Exact execution stats. Unregistered arbitrary/full-history analyses v2 offline operation, explicit behavior change; no claimed synchronous bounded equivalence. |
| Purchasing /evidence/decisions,/evidence/audit-trail | Last25 valid evidence rows / audit | Preserve shapes and validity-before-limit; no all-history requirement. |
| Purchasing /evidence/summary,/evidence/conservation-proof,/health,/status,/learning/hero,/learning/self-pause,/diagnostics/signal-gate,/diagnostics/ramp,/competence/ramp | Fixed metrics/diagnostics | Preserve formulas and correct population. |
| Purchasing /evidence/proof-ledger and control proof-ledger alias | ProofLedgerResponse entries + complete competence_curve | v2 entries page + stride1 CurvePage metadata/final point. Update both aliases and PurchasingBeatPanels together; v1 curve retires at P9 activation. |
| Purchasing /api/purchasing/iks | IKSService summary INCLUDING full trajectory | Version2 IKSSummaryPage transport, explicit /api/v2/purchasing/iks or api_version=2; §6.4. Never classify this as scalar. |
| Purchasing supplier scorecard/trust/regime/PAR endpoints | Scalar or per-supplier/item reports,7-day forecast; scorecard includes price/season arrays | Same values/availability; supplier_details preserves individual prices/seasons, v2 pages if dynamic arrays exceed bound (§2.5); no synthetic orders. External QBO provenance unchanged. |
| DataOps /decisions,/pipeline/{system_id}/decisions,/system/{name}/history | decisions/count/accuracy/breakdown, variable limit handling | v1 same bounded cohort and shape; v2 normalized actual-action/system/correct predicates with cursor and exact totals. |
| DataOps /trust/verify | Recent category rows + page-local summary | Preserve latest100<=400 cohort and page-local denominator, scoring fields plus outcome; no all-verified join. |
| DataOps /accuracy-by-category,/pipelines,/schema-impact/{system},/transformations/{system},/bottleneck/{system} | Group/summary structures | Exact native reductions; paged v2 variable groups/steps, totals unchanged. No new structural schema semantics. |
| DataOps /process-timeline | ProcessTimelineResponse activities all-history | v2 activities page with cursor, separate summary; ProcessTimelinePanel and WhatIfReordering may act only on loaded labeled window, complete analysis offline. |
| DataOps /rsi-summary | Counts/scalars plus curated timeline, cached60sec | Fresh graph S/P every request; labeled curated timeline unchanged; no graph cache. |
| SDK DI queries, weekly report, cross-domain insight, CLI exports | Arbitrary/full result collections | Registered bounded plans return page+totals; arbitrary callbacks/report jobs explicit offline, version2 complete manifests. |

### 6.3 Limit and offset compatibility

Journal v1 limit=0 returns no trades but complete totals; route uses journal_totals, not illegal BoundPage(0). JournalQuery.offset now provides the actual native contract:0..10000 in both versions, mutually exclusive with page.after (§3.4). Both v1 aliases and api.ts callers map directly to it; cursor continuation sets offset0. Formerly uncapped v1 offsets>10000 or limits>1000 receive the explicit422 legacy_page_bound contract at announced P11 activation; no silent clipping or client scan. Journal unfiltered-empty special response remains v1-only.

DataOps /decisions clamps limit to1..100 (including0→1); /system/{name}/history uses max(0,limit), so0 is empty. CLI journal max(0,n) remains0-empty; no generic constructor error should change it. SDK history rejects0 and >100 with existing FastAPI validation. Other explicitly bounded endpoint windows retain their existing limits. New routes reject out-of-range values instead of silently clamping, documented as v2. A supplied cursor and offset are mutually exclusive in generic P1; do not copy the historical AGE precedence rule into P1 requests.

### 6.4 P3-FIX H: Purchasing IKS includes a full trajectory

The current `apps/purchasing/backend/app/routers/iks.py:21–32` GET **/api/purchasing/iks** returns IKSService.summary(): `{iks, per_category, trajectory, verified_count, available, source}`; trajectory is the WHOLE list of `{decisions,iks,win_rate,timestamp}`. It is not a scalar endpoint. This is distinct from the frontend's current **/api/purchasing/iks/summary** request in api.ts:584; do not rename or accidentally remount that unrelated route.

Add these immutable capability outputs to domain_queries.py, implemented by PrefixCurveStore. No new protocol is required.

```python
@dataclass(frozen=True, slots=True)
class IKSCategoryValue:
    category: str
    iks: float

@dataclass(frozen=True, slots=True)
class IKSSummaryPage:
    stamp: ReadStamp
    iks: float
    per_category: tuple[IKSCategoryValue, ...]
    trajectory: CurvePage
    verified_count: int
    available: bool
    source: Literal["graphstore"] = "graphstore"
```

iks_summary_page composes the normalized global curve and final category points in ONE consistent read. Categories are the same configured ordered category tuple supplied to IKSService, max1000 unique names; no Decision row cap. Normalize fallback decision ID and creation index against the FULL raw provider stream before category filtering, exactly as IKSService._verified_decisions. Global iks=global final_point.iks, verified_count=full normalized row count, available=bool(count), per_category contains every configured category including0 for empty history. Compute each category's final trajectory value natively with the same prefix rounding; do not accumulate category curve pages. Per-category array plus curve page together<=2MiB; reduce point page size for bytes, never drop categories or final totals. Reject an indivisible oversized configured summary at activation. trajectory uses iks_category_v1 with category=None, full-history ranks0,10,...,N, preserving the nonempty rank0 and final remainder rules. Empty curve still has its single zero point.

**Version selection.** Canonical new route **GET /api/v2/purchasing/iks?limit=100&cursor=...**. Also accept **/api/purchasing/iks?api_version=2** with identical bounded schema during migration; this explicit integer query parameter is the compatibility opt-in (only1/2 accepted, otherwise422). No content guessing or automatic version selection based on history length. V2 path with api_version=1 is422. Cursor defaultNone; limit1..1000, default100, no offset. Version2 JSON keeps iks/per_category/verified_count/available/source semantics, replaces the trajectory array with only the returned page's ORIGINAL four-field points, and adds:

- trajectory_page: BoundedPageMeta plus point_count:int (population_count is full verified rows, not number of points);
- trajectory_final: original four-field all-history final point;
- days_active: unchanged full-history value.

per_category is the same category→float mapping for the configured Purchasing shape. Every page repeats unchanged scalar summaries at its epoch. Client labels the visible curve partial until has_more=False; it does not fetch to exhaustion in the initial render. Cursor/epoch errors follow §6.1.

P6 adds IKSService's explicit bounded entry point using this capability while leaving legacy summary operational for pre-cutover callers. P9 adds the route/serializer and api.ts/types.ts helper for the version2 endpoint (separate from the existing /iks/summary helper). Existing consumers of the latter keep their schema. Unversioned/api_version=1 /api/purchasing/iks retains its exact whole-trajectory response during the announced compatibility window; after coordinated P9 activation it returns410 with successor/export links. It NEVER returns a capped array as though it were the old full history. Backend compatibility fixtures deliberately distinguish pre-activation200, opted-in v2 pages and post-activation410.

**Exact P9 tests.** Extend existing `apps/purchasing/backend/tests/test_iks_trust.py` and add `test_iks_http_v2.py`: >1000 derived points; concatenate pages offline and compare every original point and scalar to IKSService.summary; verify category normalization before filtering, missing fallback fields, empty population and last nonmultiple10 point. Check unchanged global/per-category final values on each page, no duplicate ranks,2MiB bound, cross-tenant cursor rejection,409 restart, limit0/1001 and offset rejection, both version-selection URLs, legacy window/retirement and the unrelated /iks/summary route untouched. SDK `tests/test_iks_service.py` tests the new bounded summary composition at one stamp; P4 memory/native curve tests verify that no full row list crosses the driver boundary.

## §7 Blast-radius manifest amendments

These lists replace v3 §4.2 for P4–P12. Paths are relative to copilot-sdk unless prefixed ../ci-platform. A file absent today is a planned new file; capabilities.py is the P2 prerequisite, not a second P4 creation. All other files remain unchanged by that stage, including production.py, existing GraphStore/ProtocolV2GraphStore member sets, P1 query.py and formula-only compounding/learning/conservation/trajectory/fingerprint modules. The lists are write allowances, not a requirement to edit every file if its existing contract already fits. Existing tests remain enabled. Documentation/session updates are additional and serialized.

**Production-file count:** 131 distinct production files across P4–P12, 170 stage/file assignments (shared files counted per owning stage). Original v3 manifests had 85 distinct production files. Counts include frontend TypeScript/TSX and the same-primary SQL migration, exclude tests/docs. The increase is explained by complete cache-decorator closure, atomic frontend/model versioning, journal indirect readers, and native numerical/migration support. The 122 ledger count is a site count, not a file estimate.

| Stage | Production files | Test files |
|---|---:|---:|
| P4 | 15 | 10 |
| P5 | 7 | 3 |
| P6 | 27 | 16 |
| P7 | 46 | 9 |
| P8 | 16 | 9 |
| P9 | 15 | 9 |
| P10 | 10 | 5 |
| P11 | 26 | 24 |
| P12 | 8 | 5 |

### P4 exact file set

Production:

- `copilot_sdk/graph/domain_queries.py` (new)
- `copilot_sdk/graph/memory_store.py`
- `copilot_sdk/graph/legacy_signal_filter.py`
- `copilot_sdk/graph/tenant_store.py`
- `copilot_sdk/graph/namespace.py`
- `copilot_sdk/graph/capabilities.py` (P2 prerequisite)
- `copilot_sdk/graph/factory.py`
- `copilot_sdk/graph/projection.py`
- `copilot_sdk/graph/__init__.py`
- `../ci-platform/ci_platform/graph/age_sdk_adapter.py`
- `../ci-platform/ci_platform/graph/age_graph_store.py`
- `../ci-platform/ci_platform/graph/domain_queries.py` (new)
- `copilot_sdk/graph/consumer_reducers.py` (new)
- `../ci-platform/ci_platform/graph/domain_query_migration.py` (new)
- `../ci-platform/ci_platform/graph/sql/consumer_reductions_v1.sql` (new)

Tests:

- `tests/test_domain_query_contract.py` (new)
- `tests/test_domain_query_wrappers.py` (new)
- `../ci-platform/tests/test_domain_queries_age.py` (new)
- `tests/test_consumer_numeric_parity.py` (new)
- `tests/test_consumer_curve_contract.py` (new)
- `tests/test_journal_fact_contract.py` (new)
- `tests/test_archive_export_contract.py` (new)
- `../ci-platform/tests/test_consumer_numeric_age.py` (new)
- `../ci-platform/tests/test_journal_facts_age.py` (new)
- `../ci-platform/tests/test_archive_export_age.py` (new)

### P5 exact file set

Production:

- `copilot_sdk/scoring/mutation_lock.py`
- `copilot_sdk/backend/scoring_router.py`
- `copilot_sdk/backend/scorer_proxy.py`
- `copilot_sdk/graph/deadline.py` (new)
- `../ci-platform/ci_platform/graph/age_client.py`
- `../ci-platform/ci_platform/graph/age_graph_store.py`
- `../ci-platform/ci_platform/graph/age_sdk_adapter.py`

Tests:

- `tests/test_mutation_lock.py`
- `tests/backend/test_score_deadlines.py` (new)
- `../ci-platform/tests/test_age_deadlines.py` (new)

### P6 exact file set

Production:

- `copilot_sdk/backend/scoring_router.py`
- `copilot_sdk/backend/conservation_utils.py`
- `copilot_sdk/backend/health_builder.py`
- `copilot_sdk/backend/self_computation_router.py`
- `copilot_sdk/backend/switching_cost_router.py`
- `copilot_sdk/backend/transfer_router.py`
- `copilot_sdk/scoring/composite_gate.py`
- `copilot_sdk/scoring/gate_enforced_scorer.py`
- `copilot_sdk/scoring/iks_service.py`
- `copilot_sdk/scoring/measurement_state.py`
- `copilot_sdk/scoring/scorer.py`
- `copilot_sdk/scoring/trust_traps.py`
- `copilot_sdk/demo/bundle.py`
- `copilot_sdk/di/enrichment.py`
- `copilot_sdk/di/nl_query.py`
- `copilot_sdk/di/query_providers.py`
- `copilot_sdk/outcome/router.py`
- `copilot_sdk/reporting/weekly.py`
- `copilot_sdk/transfer/cross_domain.py`
- `copilot_sdk/graph/read_diff_runner.py`
- `copilot_sdk/migrate/shadow_scorer.py`
- `copilot_sdk/migrate/verify_state.py`
- `copilot_sdk/migration/rehearsal.py`
- `copilot_sdk/backend/models.py`
- `copilot_sdk/backend/consumer_access.py` (new)
- `copilot_sdk/di/query_models.py`
- `copilot_sdk/di/query_service.py`

Tests:

- `tests/test_bounded_sdk_consumers.py` (new)
- `tests/test_bounded_replay_export.py` (new)
- `tests/test_bounded_dk_refresh.py` (new)
- `tests/backend/test_self_computation_router.py`
- `tests/backend/test_self_computation_panels.py`
- `tests/test_iks_service.py`
- `tests/test_measurement_state.py`
- `tests/test_weekly_report.py`
- `tests/test_di_query.py`
- `tests/test_nl_query_extended.py`
- `tests/test_transfer_router.py`
- `tests/test_conservation_utils.py`
- `tests/scoring/test_trajectory.py`
- `tests/scoring/test_fingerprint.py`
- `tests/scoring/test_trust_traps.py`
- `tests/test_consumer_http_v2.py` (new)

### P7 exact file set

Production:

- `copilot_sdk/backend/request_graph_projection.py` (new)
- `copilot_sdk/backend/response_materializer.py`
- `copilot_sdk/backend/scoring_router.py`
- `copilot_sdk/backend/conservation_router.py`
- `copilot_sdk/state/tab_state_cache.py`
- `copilot_sdk/state/tab_state_router.py`
- `copilot_sdk/state/cached_static.py`
- `copilot_sdk/state/cached_quasi_static.py`
- `copilot_sdk/state/invalidation.py`
- `copilot_sdk/state/__init__.py`
- `apps/trading/backend/app/main.py`
- `apps/trading/backend/app/services/trading_materialization.py`
- `apps/trading/backend/app/state/trading_registry.py`
- `apps/trading/backend/app/state/compute_helpers.py`
- `apps/purchasing/backend/app/main.py`
- `apps/dataops/backend/app/main.py`
- `copilot_sdk/backend/transfer_router.py`
- `copilot_sdk/backend/evolution_router.py`
- `apps/trading/backend/app/state/__init__.py`
- `apps/trading/backend/app/context_router.py`
- `apps/trading/backend/app/routers/analytics.py`
- `apps/trading/backend/app/routers/cohort_status_router.py`
- `apps/trading/backend/app/routers/promotion_router.py`
- `apps/trading/backend/app/routers/execution_router.py`
- `apps/trading/backend/app/routers/regime_router.py`
- `apps/trading/backend/app/routers/regime_analytics.py`
- `apps/trading/backend/app/routers/evolution_router.py`
- `apps/trading/backend/app/routers/regime.py`
- `apps/trading/backend/app/routers/regime_status.py`
- `apps/trading/backend/app/routers/webhook.py`
- `apps/trading/backend/app/routers/vix_timing.py`
- `apps/trading/frontend/src/api.ts`
- `apps/trading/frontend/src/types.ts`
- `apps/trading/frontend/src/App.tsx`
- `apps/purchasing/frontend/src/api.ts`
- `apps/purchasing/frontend/src/types.ts`
- `apps/purchasing/frontend/src/App.tsx`
- `apps/dataops/frontend/src/api.ts`
- `apps/dataops/frontend/src/types.ts`
- `apps/dataops/frontend/src/App.tsx`
- `apps/trading/frontend/src/screens/PerformanceScreen.tsx`
- `apps/purchasing/frontend/src/screens/PerformanceScreen.tsx`
- `apps/dataops/frontend/src/screens/CurveScreen.tsx`
- `apps/dataops/frontend/src/components/CompoundingCurveOverlay.tsx`
- `apps/dataops/frontend/src/components/ConservationProjection.tsx`
- `apps/trading/frontend/src/state/tradingKeys.ts`

Tests:

- `tests/test_response_materializer.py`
- `tests/test_request_graph_projection.py` (new)
- `apps/trading/backend/tests/test_materializer_invalidation.py`
- `apps/purchasing/backend/tests/test_materializer_invalidation.py`
- `apps/dataops/backend/tests/test_materializer_invalidation.py`
- `tests/test_cache_caller_closure.py` (new)
- `apps/trading/backend/tests/test_trajectory_http_v2.py` (new)
- `apps/purchasing/backend/tests/test_trajectory_http_v2.py` (new)
- `apps/dataops/backend/tests/test_trajectory_http_v2.py` (new)

### P8 exact file set

Production:

- `apps/trading/backend/app/cli_sdk.py`
- `apps/trading/backend/app/context_router.py`
- `apps/trading/backend/app/main.py`
- `apps/trading/backend/app/routers/analytics.py`
- `apps/trading/backend/app/routers/claim_gate_router.py`
- `apps/trading/backend/app/routers/promotion.py`
- `apps/trading/backend/app/routers/regime_analytics.py`
- `apps/trading/backend/app/routers/regime_router.py`
- `apps/trading/backend/app/services/claim_gate.py`
- `apps/trading/backend/app/services/pre_scorer.py`
- `apps/trading/backend/app/services/promotion_engine.py`
- `apps/trading/backend/app/services/regime_classifier.py`
- `apps/trading/backend/app/services/trader_profiles.py`
- `apps/trading/backend/app/state/compute_helpers.py`
- `apps/trading/frontend/src/api.ts`
- `apps/trading/frontend/src/types.ts`

Tests:

- `apps/trading/backend/tests/test_bounded_read_consumers.py` (new)
- `apps/trading/backend/tests/test_pre_scorer.py`
- `apps/trading/backend/tests/test_regime_classifier.py`
- `apps/trading/backend/tests/test_analytics.py`
- `apps/trading/backend/tests/test_analytics_verified_merge.py`
- `apps/trading/backend/tests/test_regime_analytics.py`
- `apps/trading/backend/tests/test_clone_fingerprint.py`
- `apps/trading/backend/tests/test_vol_analytics.py`
- `apps/trading/backend/tests/test_measurement_state.py`

### P9 exact file set

Production:

- `apps/purchasing/backend/app/main.py`
- `apps/purchasing/backend/app/routers/auto_order_router.py`
- `apps/purchasing/backend/app/routers/evidence.py`
- `apps/purchasing/backend/app/routers/iks.py`
- `apps/purchasing/backend/app/routers/learning_beats.py`
- `apps/purchasing/backend/app/routers/regime_router.py`
- `apps/purchasing/backend/app/routers/scorecard_router.py`
- `apps/purchasing/backend/app/routers/trust_router.py`
- `apps/purchasing/backend/app/routers/verify_router.py`
- `apps/purchasing/backend/app/services/purchasing_control.py`
- `apps/purchasing/backend/cli.py`
- `apps/purchasing/backend/app/services/bounded_purchasing.py` (new)
- `apps/purchasing/frontend/src/api.ts`
- `apps/purchasing/frontend/src/types.ts`
- `apps/purchasing/frontend/src/components/PurchasingBeatPanels.tsx`

Tests:

- `apps/purchasing/backend/tests/test_bounded_read_consumers.py` (new)
- `apps/purchasing/backend/tests/test_trajectory_regression.py`
- `apps/purchasing/backend/tests/test_iks_trust.py`
- `apps/purchasing/backend/tests/test_predictive_par.py`
- `apps/purchasing/backend/tests/test_par_optimizer.py`
- `apps/purchasing/backend/tests/test_evidence.py`
- `apps/purchasing/backend/tests/test_purchasing_evidence.py`
- `apps/purchasing/backend/tests/test_proof_ledger_v2.py` (new)
- `apps/purchasing/backend/tests/test_iks_http_v2.py` (new)

### P10 exact file set

Production:

- `apps/dataops/backend/app/context_router.py`
- `apps/dataops/backend/app/main.py`
- `apps/dataops/backend/app/routers/di_gateway_router.py`
- `apps/dataops/backend/app/routers/regime_router.py`
- `apps/dataops/backend/app/services/source_trust.py`
- `apps/dataops/frontend/src/api.ts`
- `apps/dataops/frontend/src/types.ts`
- `apps/dataops/frontend/src/screens/DashboardScreen.tsx`
- `apps/dataops/frontend/src/components/ProcessTimelinePanel.tsx`
- `apps/dataops/frontend/src/components/WhatIfReordering.tsx`

Tests:

- `apps/dataops/backend/tests/test_bounded_read_consumers.py` (new)
- `apps/dataops/backend/tests/test_source_trust.py`
- `apps/dataops/backend/tests/test_di_enterprise_query.py`
- `apps/dataops/backend/tests/test_dataops_evidence.py`
- `apps/dataops/backend/tests/test_process_timeline_v2.py` (new)

### P11 exact file set

Production:

- `apps/trading/backend/app/services/journal_query.py`
- `apps/trading/backend/app/services/journal_graph_migration.py` (new)
- `apps/trading/backend/app/routers/journal.py`
- `apps/trading/backend/app/routers/data_import.py`
- `apps/trading/backend/app/context_router.py`
- `apps/trading/backend/app/main.py`
- `apps/trading/backend/app/cli_sdk.py`
- `apps/trading/backend/app/routers/execution_router.py`
- `apps/trading/backend/app/routers/correlation.py`
- `apps/trading/backend/app/routers/prescore.py`
- `apps/trading/backend/app/routers/regime.py`
- `apps/trading/backend/app/routers/vix_timing.py`
- `apps/trading/backend/app/routers/evidence.py`
- `apps/trading/backend/app/routers/promotion.py`
- `apps/trading/backend/app/evidence_providers.py`
- `apps/trading/backend/app/services/correlation.py`
- `apps/trading/backend/app/services/regime.py`
- `apps/trading/backend/app/services/vix_timing.py`
- `apps/trading/backend/app/services/execution_analysis.py`
- `apps/trading/backend/app/state/compute_helpers.py`
- `apps/trading/backend/app/state/trading_registry.py`
- `apps/trading/backend/app/services/trading_materialization.py`
- `apps/trading/frontend/src/api.ts`
- `apps/trading/frontend/src/types.ts`
- `apps/trading/frontend/src/App.tsx`
- `apps/trading/frontend/src/components/JournalQueryBar.tsx`

Tests:

- `apps/trading/backend/tests/test_journal.py`
- `apps/trading/backend/tests/test_journal_query.py`
- `apps/trading/backend/tests/test_journal_graph_migration.py` (new)
- `apps/trading/backend/tests/conftest.py`
- `apps/trading/backend/tests/test_broker.py`
- `apps/trading/backend/tests/test_conservation_breakdown.py`
- `apps/trading/backend/tests/test_correlation.py`
- `apps/trading/backend/tests/test_evidence.py`
- `apps/trading/backend/tests/test_data_endpoints.py`
- `apps/trading/backend/tests/test_csv_connector.py`
- `apps/trading/backend/tests/test_multi_trader.py`
- `apps/trading/backend/tests/test_options_factors.py`
- `apps/trading/backend/tests/test_p50_smoke.py`
- `apps/trading/backend/tests/test_pattern_detector.py`
- `apps/trading/backend/tests/test_prescore.py`
- `apps/trading/backend/tests/test_regime.py`
- `apps/trading/backend/tests/test_regime_recommender.py`
- `apps/trading/backend/tests/test_regime_recommender_p49.py`
- `apps/trading/backend/tests/test_subcategory.py`
- `apps/trading/backend/tests/test_trust_analysis.py`
- `apps/trading/backend/tests/test_vix_timing.py`
- `apps/trading/backend/tests/test_evidence_providers.py`
- `apps/trading/backend/tests/test_trading_backend.py`
- `apps/trading/backend/tests/test_real_providers.py`

### P12 exact file set

Production:

- `copilot_sdk/graph/query_budget.py` (new)
- `copilot_sdk/graph/memory_store.py`
- `../ci-platform/ci_platform/graph/age_client.py`
- `../ci-platform/ci_platform/graph/age_graph_store.py`
- `../ci-platform/ci_platform/graph/age_sdk_adapter.py`
- `apps/trading/backend/app/main.py`
- `apps/purchasing/backend/app/main.py`
- `apps/dataops/backend/app/main.py`

Tests:

- `tests/test_query_budget.py` (new)
- `../ci-platform/tests/test_age_query_budget.py` (new)
- `apps/trading/backend/tests/test_query_budgets.py` (new)
- `apps/purchasing/backend/tests/test_query_budgets.py` (new)
- `apps/dataops/backend/tests/test_query_budgets.py` (new)

### 7.1 Ownership changes and implementation constraints

P4 owns all supplemental type/validator/schema definitions, reference reducers, same-primary native implementations and the idempotent numeric/order/fact-epoch migration. Install exact numeric functions through domain_query_migration.py; capabilities activate only after schema/function versions and parity probes succeed. No endpoint cutover in P4. consumer_reducers.py is the reference/access adapter, not a production fallback that fetches all rows.

P6 owns SDK models.py additions and consumer_access.py adapters, plus the atomic DI service/provider bounded-cohort handoff. Formula modules are reference oracles, not edit targets. DI query_models.py receives the closed bounded-plan representation; arbitrary callable APIs retain explicit offline use only. P6 introduces shared v2 endpoints before P7 bundled-client activation.

P7's expanded manifest includes every direct cached_static/cached_quasi_static/tab-state/ResponseMaterializer importer found in the SDK and three named apps. It replaces graph-serving behavior and registry callbacks together. Market connector caches are not relabeled graph caches; graph-derived regime accuracy still cannot be cached. P7 may leave not-yet-migrated journal source reads request-local until P11, with explicit remaining debt; it must not claim journal graph cutover. P7 tests verify no graph-serving cache remains on migrated paths and all old decorators/import names either have a bounded request-local contract or their callers are removed.

P8 execution_router's data migration moves to P11 because its population includes imported trades. Its cache decorator is still handled in P7. Promotion's scalar/category work remains P8; journal-dependent routes change in P11. P8 leaves journal source semantics operational before P11.

P9 bounded_purchasing.py adapts sufficient statistics to existing PAR/evidence/scorecard result schemas, without constructing fake orders or modifying par_optimizer/predictive_par arithmetic. New field/model changes for proof curves belong to learning_beats.py and Purchasing frontend together.

P11 includes service access signatures for correlation/regime/VIX/execution as well as every _journal_records and _trade_store_ref caller. Numerical formulas remain identical. Journal tests that seed process lists/JSON must instead seed governed facts after activation; separate migration fixtures retain legacy inputs. Do not delete tests to make the source switch pass.

P12 does not redesign contracts: it counts physical queries, retries, decoded bytes, groups and response bytes against these contracts. Multi-page offline operations are separately labeled and accounted; they cannot evade an online budget by moving loops into a helper.

## §8 Acceptance criteria for P4–P12

### 8.1 Release sequence, dependencies and green gates

The dependency chain remains P1 → P2 → P4 → P5 → P6 → P7 → P8 → P11 → P12 → P13, with **this P3 contract required before P4**. P9 and P10 branch after P7 and join before P12. P8/P9/P10 can run in parallel: their final manifests are app-disjoint and P7 has already completed shared frontend changes. P11 waits for P8; P4/P5/P12 share AGE files and are serialized. P5/P6/P7 share scoring_router. Session-log integration is serialized. P2 and P3 can be developed independently, but P4 starts only with both accepted. No claim of elapsed-time estimates; P9/P10 can become the critical branch.

Every source-changing stage first records its actual baseline, then runs changed-file mypy with repository configuration and no ignore-errors masking, full relevant SDK/app/ci-platform suites in separate app import environments, and import/startup composition tests. Existing failures must be reported and resolved/triaged before a green claim. Run frontend type-check/build for changed clients and contract tests for their consumed JSON. Multi-repository capability work is one tested dependency set. Release only with zero introduced failures and complete capability activation; never leave a protocol advertised pending a later implementation.

| Stage | Must be true BEFORE start | Required evidence BEFORE shipping / next stage |
|---|---|---|
| P4 | P1+P2 accepted, P3 schemas reviewed, same-primary migration can run under production policy | Native and memory parity for every registered profile; numeric/order boundary cases; typed schema validation; tenant/legacy/namespace composition and negative capability membership; epoch conflicts across all fact kinds; all-history >10000, dynamic >1000 groups; no all-row driver transport; journal fact writes/alias collisions; full export manifests and rollback. Old constructors/consumers still work. |
| P5 | P4 complete capability selected without consumer cutover | Absolute deadline and lock admission, cancellation/rollback/no late write, pool checkout/close behavior, score/learn regression; no schema changes. |
| P6 | P5 gates; exact profile result schemas proven | Frozen scorer outputs including trajectory every prefix, fingerprint tiny classes, benchmark/actual-arm differences; replay cursor advances under reverse created/verified order; no fixed-cursor offset bug; full exports/archives; DI/weekly arbitrary callbacks explicit offline; v2 route schemas before client change. |
| P7 | P6 v2 routes installed and P4 native reads available | All cache import/registry callers migrated atomically; no cross-request graph result reuse; graph outage503; multi-tenant request isolation; direct/tab response parity; all three client builds and epoch restart/partial-curve UX tests; v1 retirement only coordinated version activation. |
| P8 | P7 shared access and display stable | Trading top-k/rounding, native whole-history analytics, stage-rank promotion, profile zero groups, CLI/versioned complete export, startup full replay; journal source remains operational until P11. |
| P9 | P7 stable | Sample rejection before item filter; supplier selector distinctions; per-category last5 prices; PAR missing/negative/date/season parity; evidence validity-before25; proof every-prefix pagination; complete archive backup; Purchasing client build. |
| P10 | P7 stable | Pending included in accuracy denominator; L-rank halves; missing-system behavior; source factor presence dedup; correct prior fingerprint; RSI fresh graph and fixture labeling; timeline cursor/client semantics. |
| P11 | P8 and all P4 journal capabilities accepted; source snapshot/reconciliation dry run; no unresolved identity/tenant conflicts | Every writer and reader switched together; CSV duplicates/broker dedup, inclusive end instant/local date distinction, entry!=created, pnl-null/ties, predicates matching only beyond first2000, limit0 totals, annotations history, exact provenance, no JSON/process serving fallback, all journal dependent fixtures and client build. |
| P12 | P9,P10,P11 green; no unversioned full-history HTTP response remains | Physical execution telemetry incl retries/transaction statements, decoded UTF-8 bytes, threadpool context isolation, single oversize record behavior; measured per-endpoint bounded rows/groups/bytes; no deadline/budget suppression. |
| P13 | All implementation gates and deployed schema/package set accepted | Real shared AGE through production wrappers, fresh-write/outage/multi-tenant/legacy/namespace probes, frozen reasoning baselines and full completeness checks. Only this live evidence can close gaps under Rule85. |

### 8.2 Required fixtures and formula verification matrix

P4 shared contract tests enumerate the profile registry and fail if a profile lacks a schema, memory implementation, native implementation, policy wrapper delegation or parity fixture. Test every empty population, pending/confirmed/overridden conflict, missing versus explicit None field, top/meta/factors.metadata disagreement, default tenant, legacy markers with null values, benchmark and sample distinctions, unknown category/action, tied timestamps and >10000 records.

Reference-computation matrix:
- trajectory/IKSService: all prefix points, point0 empty/nonempty, non-multiple10 remainder, category normalization, days_active;
- fingerprint/scorer IKS: class std, compatible vector filtering, minimum5/3 cases, round3, interpret boundaries, FP rounding input and category>=10;
- conservation/baseline/checkpoint quality: distinct populations/orders, configured W1/400/600/1600 and N<W (not a400 cap), fixed first200-of-tail400, overrides, bootstrap and timestamp boundary;
- measurement/trust/composite/enforced gate: actual arms incl unknown/zeros, Gini/half ranks, tail50/200, null exclusions, all-history gate mean;
- Trading: monetary selector variants, cosine rounding before rank, stage rank, typed trader groups, volatility bootstrap/RNG, VRP/dispersion and exact execution median;
- Purchasing: supplier selector variants, strict correctness, sample guard, daily quantity sums, population std, seasonal factors, ordered invoice windows and every-prefix proof;
- DataOps: all-active category denominator, provider order halves, source-set dedup, named factor presence, DK tensor vs fingerprint and predecessor selection;
- SDK projection/reporting/transfer: profile_v1 capped cohort label, max-created report anchor, action tie order, built-in cost arithmetic, both monetary precedence rules, complete provenance traversal;
- journal: source union/dedup precedence, missing P&L denominators, inclusive instant vs local dates, annotations and broker key;
- offline replay/export/evolution/DI: same full inputs, stateful order, no partial publication, complete manifest.

No golden expected values may be changed solely to accommodate truncation, normalization drift or another floating-point reducer. A failed equivalence test blocks its owning stage; it is not a new formula feature.

### 8.3 P3 validation and limits

The documentation validation checks the Appendix A IDs1..122 exactly once, resolves their path/symbol anchors (including BOTH ledger49 definitions), parses all Python specification blocks, verifies all specified dataclasses frozen, checks exact manifest paths/planned-new paths and counts unique production files. The edit audit records this task's docs-only writes. The whole-tree source/test/config checksum changed concurrently, so it cannot be used to claim that the entire shared workspace remained unchanged; the concurrent edits are recorded below. P3 does not rerun the long production suite or claim P4 implementations are tested.

This document makes explicit two deliberate compatibility decisions beyond the original estimate: arbitrary full-history callable work is offline, and unbounded HTTP collections receive v2 pagination with a coordinated v1 retirement. These are not mathematical approximations. Same-primary ordered numeric reducers are a deployment prerequisite, not assumed capabilities of existing AGE. A deployment that cannot satisfy this prerequisite must not activate those profiles. No platform gap is closed by this design session.

### 8.4 Offline HTTP decision (normative clarification)

No background-job store or scheduler is introduced by this design. References above to offline operations mean explicit CLI/admin processing of a complete ExportHandle. A synchronous v2 route that cannot be expressed by a registered exact native profile returns409 `offline_required` with OfflineAnalysisResponse and the authorized export instructions; it does not return202 or an invented job ID. Old synchronous unbounded behavior is explicitly retired at the relevant version activation. This restriction covers arbitrary callable evolution/DI/reporting and unregistered journal pattern/trust/recommender analyses. Offline result artifacts are user-delivered reports, never a serving fallback. Existing finite registered analyses remain synchronous.


### 8.5 Final contract clarifications and documentation evidence

**Curve predecessor.** CurveRequest.at_or_before is an optional finite timestamp used by weekly reporting. CurvePage.prior_point is the last EXISTING global prefix point whose timestamp<=at_or_before, or None. It does not filter/rebase the curve population and does not change final_point. The primary finds the predecessor by rank/timestamp without fetching all curve pages. Weekly IKS delta is final_point.iks minus prior_point.iks (or0); empty/unavailable branches stay as in weekly.py.

**Weekly row output.** weekly_supplier_changes_v1 is a RowsRequest profile with start=period_start, population raw verified and L order before sorting rounded percentage DESC; full evidence row payload has supplier_id:str,supplier:str,metric:"unit_price",issue:"price_increase",previous_value:float,current_value:float,pct:float,direction:"up",decision_id:str. Exactly one row per qualifying source Decision; do not collapse identical supplier IDs. previous/current aliases, previous>0, pct>=8, round prices4/pct2 match _compute_supplier_changes. StatisticsRequest.window is period_days for weekly_v1 (default adapter7, positive<=1000), not a number of Decisions. The access adapter combines returned row waste/variance sums with the independently governed waste-provider result, preserving replacement versus addition semantics.

**Bounded DI provider handoff.** The additive local provider method is execute_bounded(plan: QueryPlan, *, max_records: int, reference_epoch_seconds: float) -> RawQueryResult. It is implemented by GraphStoreProvider and DataOpsEnterpriseProvider and called by DIQueryService only for these explicitly selected bounded providers; legacy provider.execute remains valid for offline/test providers. It translates to RowsRequest(di_rows_v1,window=max_records,start=resolved_start,end=reference_epoch_seconds) and returns that exact bounded cohort. It must not re-fetch all rows through execute. QueryPlan remains an existing HTTP/service model; the graph boundary is the frozen RowsRequest, never raw SQL/Cypher or an executable callback. Existing unsupported plan behavior remains explicit, not a fallback all-history query. max_records>1000 is an explicit offline request, not silently clipped.

**Journal predicate composition.** All distinct supplied fields combine with AND. actions and include_kinds use IN. Tags require every requested normalized tag; a single-tag legacy request is unchanged. Factor predicates all apply. Text matches the normalized concatenated search fields. Journal-only predicates never get pushed down as an approximate generic DecisionFilter. Generic journal projection remains Decision-only.

**Result schema typing.** Cell is the common immutable wire scalar representation; each profile's closed field table is its schema, not arbitrary user-selected names. Implement profile-name Literal aliases enumerating exactly the names in §§2.3–2.4 and §5.2 (including weekly_supplier_changes_v1 here), plus literal result-field unions generated from those tables. Validators must reject malformed types including bool where an int count is required. Public typed constructors bind a profile to its allowed arguments; no dynamically supplied profile code or callbacks. This does not add aliases or fields to P1 query.py.

**Shared-workspace evidence.** Inspection began at HEAD fca9497979d9f1d276b80da0101383871d3584d0 with existing unrelated changes. The initial tracked source/test/config digest was 7278715918dc5ccd9e83b652125f8f811f224e7dbbc366cfadc20b1286009bea (2871 files); later it was c5a6bf4d74b0b8e248eeb161254585f5aaf17f95029fefbbbcf27855b46f7017. During P3, concurrent changes appeared in Trading routers/regime_router.py, services/pre_scorer.py, services/regime_classifier.py and tests/test_pre_scorer.py,test_regime_classifier.py. Those production services were reread; the changes reuse raw rows/buckets within a request and do not supply native bounded statistics. Ledger72/73/75 anchors were refreshed to223/230/154. Existing source/test edits were neither made nor reverted by P3. The aggregate digest mismatch is reported rather than presented as a passing unchanged-tree check. P3's write operations targeted only this document and the required session-state append. No production/test file was edited by this task; no implementation test or mypy success is claimed for future P4–P12 code.

**Evolution activation constraint.** _run_evolution executes registered rules synchronously on its full verified input and its final legacy-order decision ID. Moving that work to a later job can change subsequent learning even if formulas are identical. P6 must NOT silently defer or disable configured evolution. Its online activation preflight rejects an enabled arbitrary/custom evolver without a registered exact native rule contract BEFORE admitting score/learn writes; existing unsupported configurations remain on the pre-cutover release until explicitly moved to offline mode or given a separately reviewed exact rule profile. Offline evaluation uses the same full input, trigger and conservation state, and publishes governed results in the original order. This is an explicit compatibility/activation restriction, not a claim that a universal bounded evolution reducer exists. Tests must verify no score is committed and then unexpectedly loses required evolution work.

**Original P3 documentation validation result (before P3-FIX).** All 51 requested files were read in order before design. All122 Appendix A IDs occur exactly once; AST resolution confirms every file/symbol anchor, including both scorer helpers. Three Python specification blocks parse; all33 dataclasses have frozen=True; seven supplemental protocols are defined. Manifests contained131 distinct production files and169 stage/file assignments before P3-FIX; planned-new paths were marked. Scorer formulas are specified as preservation obligations, not claimed empirically verified by this docs-only session. Journal writer coverage includes manual entries, reflections/tags, metadata overlays, CSV/broker/process-memory imports and CLI governed writes. Trajectory prefixes and journal inclusive end-date semantics are explicit. Only docs/design_bounded_consumer_contracts.md and the required docs/session_state.md append were written by P3.

### 8.6 P3-FIX amendment gates and validation

P3-FIX addresses REV-P3 A–F (P1) and G–H (P2). The original33 dataclass names remain; JournalQuery and ExportRequest are amended,22 dataclasses are added, yielding55 frozen specifications in five parseable Python blocks. All seven existing optional protocols remain; their new signatures live on the supplemental capabilities, never on GraphStore/V2/P1. The122 Appendix A IDs remain exactly once. The revised manifests contain131 distinct production files/170 stage assignments: P8 adds regime_router.py already owned by P7, so distinct production count does not grow. P6 adds one DK test file, P8 adds two existing Trading regression files, P9 adds one IKS HTTP test file. Other stage file lists/dependencies and disjoint P8/P9/P10 parallelism remain unchanged.

These are additional mandatory stage gates, not claims that implementations exist:

| Finding | Owner and exact verification targets | Required evidence |
|---|---|---|
| A supplier | P4 test_domain_query_contract.py, test_consumer_numeric_parity.py, ci-platform test_domain_queries_age.py; P9 test_iks_trust.py/test_bounded_read_consumers.py | [1,3]/winter versus [2,2]/summer retain distinct detail despite identical sums; last5 per category across >1000 categories; all season names; nested supplier and key-presence/null/nonfinite policies; scalar summary and paged detail share stamp. |
| A Trading | P4 numeric/native parity; P8 test_analytics_verified_merge.py, test_pre_scorer.py, test_regime_classifier.py | Boolean-only rolling10 with verification/creation reversal and stable ties; latest metadata regime independent of latest verification; monitor fallback; classifier-current versus historical regime separation; exact response field/rounding parity. |
| A measurement | P4 numeric/native parity; P6 test_measurement_state.py/test_bounded_sdk_consumers.py | >1000 keys, a zero arm only beyond page1, unknown arms, empty Cartesian shape and threshold-split row partitions; global min/measured/needed equal full _arm_counts, no page-count substitute. |
| B offsets | P4 test_journal_fact_contract.py and ci-platform test_journal_facts_age.py; P11 test_journal.py/test_journal_query.py | Both legacy aliases, offset0/75/10000, first offset page followed by offset0 cursor, cursor+offset rejection, total independent of offset, limit0, >bounds explicit validation, inclusive end-date unchanged. |
| C migration | Same P4 journal files; P11 test_journal_graph_migration.py/test_journal.py/test_evidence_providers.py | Direct-Decision-versus-union alias precedence; multiple linked targets and tenant isolation; original history ordinal despite tied/reversed/missing clocks; final snapshot versus incomplete history; crash before/after commit, identical retry, digest mismatch, orphan/collision blocking, atomic activation and no JSON fallback. |
| D correctness | P4 test_consumer_numeric_parity.py/ci-platform test_consumer_numeric_age.py; P6 tests/scoring/test_fingerprint.py | Five compatible confirmed/is_correct=False records yield fingerprint0 versus scorer correct5; missing/None/string booleans; trajectory key-presence denominator; strict AGE profile stays distinct. |
| E DK | P4 numeric/native parity and wrappers; P6 test_bounded_dk_refresh.py | Local-buffer estimator wins; graph fallback only when weights None; exact first400/category with >400 each; full-support <2/<200/>=200 branches, uniform/dispersion, invalid vectors/indices; learn→next score/checkpoint observes synchronous weights; failures return existing partial status; no offline-required ordinary learn. |
| F windows | P4 numeric/native parity; P6 test_conservation_utils.py/test_bounded_sdk_consumers.py | W600/200L+400W pauses exactly; mixed null/epoch-zero fixture (§2.7) gives q=2/3 and pauses, with identical H-rank cursor traversal and stable provider ties; W1600 spans pages but online verdict uses native totals; N<W minimum sample; per-domain configuration, benchmark/order policy; fixed400 bootstrap/checkpoint unaffected. |
| G replay | P4 test_archive_export_contract.py/ci-platform test_archive_export_age.py; P6 test_bounded_replay_export.py | Active-only default versus explicit archived diagnostic; restore prefix once then K>B; no usable checkpoint rebuild; explicit-null timestamp preserves error; reversed times/ties, skipped invalid records, complete chunks, retry/expiry and no partial publication. |
| H IKS | P4 test_consumer_curve_contract.py; P6 test_iks_service.py; P9 test_iks_http_v2.py/test_iks_trust.py | Version-selection and retirement contracts in §6.4; every prefix equals reference offline concatenation, final/global/category values independent of page, >1000 points, empty and fallback indices, unchanged /iks/summary. |

Read-only Python checks in this amendment parsed/compiled all specification blocks together, resolved every class/method type annotation, verified frozen=True and all original class names, counted protocols/ledger/manifests, and executed actual source functions without modifying them. Supplier counterexample produced different [1,3] versus[2,2] rows and winter versus summer. _recent_quality gave (600,0.6666666666666666) for both full input and the exact W600 tail, versus the forbidden truncated (400,1.0). A1001-arm fixture retained its zero minimum beyond page1. Fingerprint's conflict fixture returned win rate0 while scorer correctness counted5. The current DK estimator returned equal weights for full1100 rows and its exact first400 per category selection. These are contract/reference checks, not tests of future native implementations.

No scorer formulas or production/test files were changed by this amendment. The six P1 and two P2 design findings have concrete amendments and stage gates; REV-P3-FIX must review them before P4 starts. No full-suite/mypy/native-performance/live-stack success is claimed here, and no gap is closed under Rule85.


### 8.7 P3-FIX-2: reference timestamp ordering

REV-P3-FIX's remaining P1 is addressed by the H definition in §2.2, its shared rank cursor, the conservation/trust/gate registry amendments and the explicit mixed null/epoch-zero proof in §2.7. P4 numeric/native parity and P6 conservation consumer gates must verify the exact reference sequence and each evidence page, not just finite distinct-date fixtures or a final count. Scalar totals and paged evidence must select the same W-sized cohort. Existing baseline, replay, journal and trajectory orders are unchanged.

No types or consumer entries are added or removed: all55 frozen dataclasses, seven supplemental protocols and122 manifest entries remain. No scorer formula changes are proposed; this is an ordering-contract correction only. Reference probes verify both W600 counterexamples and stable pagination, not future native implementation or live-stack closure. P4 remains subject to re-review and its implementation acceptance gates.
