# Judgment Memory Design Fix Plan

**Document version:** 2  
**Date:** 2026-10-05  
**Status:** PROPOSED  
**Audit:** [design_compliance_audit_v2.md](design_compliance_audit_v2.md)  
**Canonical reference:** [design_principles_v2.md](design_principles_v2.md)

This plan maps every audit violation V-01 through V-09 to an implementation-ready fix. The graph remains the sole memory authority. AGE is the durable shared graph; InMemoryGraphStore remains a test/local-development implementation. No fix adds a persistent cache or another GraphStore backend.

## Shared component: GraphStoreNamespace

F-01 uses one physical AGE graph for separately configured experiment arms. This namespace view is a stateless adapter: it retains only the shared store reference and the namespace string, creates no persistence/cache, and rewrites each supplied logical domain as `f"{namespace}::{domain}"`. Every write delegates to the same store; every domain-scoped read delegates with the rewritten domain and removes that prefix from returned top-level domain fields. Cross-domain calls rewrite both source and target domains. List methods with no domain filter query the underlying API, retain only namespaced rows, then remove the prefix. `close()` is a no-op because closing a view must not close the shared connection. Unsupported or unbounded operations must fail closed; do not silently delegate without scope.

The view must satisfy `ProtocolV2GraphStore` structurally. Implement the methods explicitly with the signatures in `copilot_sdk/graph/protocol.py`; do not rely on `__getattr__`, `Any`-typed capability probes, or a cast that hides missing methods. The following code shows the namespace invariants and exact transformation rules; the implementation prompt must provide explicit forwarding methods for every inherited `GraphStore` and added `ProtocolV2GraphStore` member from that file:

```python
from __future__ import annotations

from dataclasses import replace
from collections.abc import Mapping
from typing import Any

from copilot_sdk.graph.enrichment import (
    EnrichmentSourceSet, EntityEnrichmentReceipt, EntityEnrichmentRecord,
    ProvenancedValue,
)
from copilot_sdk.graph.protocol import ProtocolV2GraphStore


class GraphStoreNamespace(ProtocolV2GraphStore):
    """Stateless domain namespace over one shared governed graph."""

    def __init__(self, store: ProtocolV2GraphStore, namespace: str) -> None:
        normalized = namespace.strip()
        if not normalized or "::" in normalized:
            raise ValueError("namespace must be a non-empty single segment")
        self._store = store
        self._prefix = f"{normalized}::"

    def _domain(self, domain: str) -> str:
        if not domain.strip():
            raise ValueError("domain must be non-empty")
        return f"{self._prefix}{domain}"

    def _logical_domain(self, domain: str) -> str:
        if not domain.startswith(self._prefix):
            raise ValueError("graph result escaped its namespace")
        return domain[len(self._prefix):]

    def _row(self, row: Mapping[str, Any]) -> dict[str, Any]:
        result = dict(row)
        for key in ("domain", "source_domain", "target_domain"):
            value = result.get(key)
            if isinstance(value, str) and value.startswith(self._prefix):
                result[key] = self._logical_domain(value)
        return result

    def _rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self._row(row) for row in rows if self._belongs(row)]

    def _belongs(self, row: Mapping[str, Any]) -> bool:
        domains = [row.get(k) for k in ("domain", "source_domain", "target_domain")]
        return any(isinstance(value, str) and value.startswith(self._prefix)
                   for value in domains)

    # For each protocol method, preserve its declared signature and forward
    # after applying these rules:
    # * one `domain` argument -> self._domain(domain)
    # * source_domain/target_domain -> rewrite each independently
    # * returned record(s) -> self._row/_rows; scalar/opaque tensor -> unchanged
    # * domain=None inventory methods -> fetch through the protocol, filter via
    #   _belongs, and unprefix with _row
    # * close() -> return None without closing self._store
    # These rules apply to every GraphStore method and every ProtocolV2GraphStore
    # addition; the method inventory is recorded below for implementation review.
```

**Protocol method inventory to implement explicitly:** all `GraphStore` methods: `write_decision`, `write_outcome`, `get_decision`, `get_decisions`, `get_all_decisions`, `get_archived_decisions`, `get_verified_decisions`, `count_verified`, `count_verified_decisions`, `save_evolution`, `get_evolution`, `list_evolutions`, `delete_evolution`, `save_evolution_state`, `get_evolution_state`, `save_posterior`, `get_posterior`, `list_posteriors`, `delete_posterior`, `save_promotion`, `get_promotion`, `list_promotions`, `delete_promotion`, `save_ledger`, `get_ledger`, `list_ledgers`, `delete_ledger`, `save_governance`, `get_governance`, `list_governance`, `delete_governance`, `count_correct`, `count_decisions`, `save_centroids`, `load_latest_centroids`, `get_centroid_checkpoints`, `load_latest_checkpoint_for_regime`, `get_checkpoint_lineage`, `get_decision_checkpoints`, `archive_old_decisions`, `count_archived`, `close`, `write_entity_enrichment`, `read_entity_enrichment`, and `list_entity_enrichments`; plus every additional method in `ProtocolV2GraphStore`: `generate_decision_id`, `write_governed_decision`, `write_observation`, `append_evidence_receipt`, `write_conservation_status`, `write_fingerprint`, `write_centroid_checkpoint`, `write_evolution_event`, `get_evolution_events`, `write_transfer_pattern`, `get_transfer_patterns`, `decision_movement`, `contextual_judgment`, `promotion_basis`, `transfer_witness`, `list_fingerprints`, `get_latest_conservation_statuses`, `get_iks_trajectory`, `link_entity`, `archive_decisions`, and `domain_scoped_reset`.

The class declaration must include the full typed method surface below (copy exact signatures from `protocol.py`; `...` denotes the forwarding body, not an omitted capability). This signature inventory is deliberately explicit so a future protocol addition cannot be mistaken for a namespace-safe method:

```python
class GraphStoreNamespace:
    def write_decision(self, domain: str, category: str, action: str, confidence: float, factors: dict[str, Any], metadata: dict[str, Any] | None = None) -> str: ...
    def write_outcome(self, decision_id: str, actual_action: str, is_correct: bool, metadata: dict[str, Any] | None = None, *, domain: str, outcome: str | None = None, verified_at_epoch: float | None = None, quality_signal: float | None = None, override_comment: str | None = None, verified_by: str | None = None, analyst_action: str | None = None, final_action: str | None = None, recommended_action: str | None = None, was_override: bool | None = None) -> None: ...
    def get_decision(self, decision_id: str, domain: str, *, include_outcome: bool = False) -> dict[str, Any] | None: ...
    def get_decisions(self, domain: str, category: str | None = None, limit: int = 400) -> list[dict[str, Any]]: ...
    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]: ...
    def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]: ...
    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]: ...
    def count_verified(self, domain: str) -> int: ...
    def count_verified_decisions(self, domain: str) -> int: ...
    def save_evolution(self, domain: str, variant_id: str, state: dict[str, Any]) -> None: ...
    def get_evolution(self, domain: str, variant_id: str) -> dict[str, Any] | None: ...
    def list_evolutions(self, domain: str) -> list[dict[str, Any]]: ...
    def delete_evolution(self, domain: str, variant_id: str) -> None: ...
    def save_evolution_state(self, domain: str, variant_id: str, state: dict[str, Any]) -> None: ...
    def get_evolution_state(self, domain: str, variant_id: str) -> dict[str, Any] | None: ...
    def save_posterior(self, domain: str, key: str, state: dict[str, Any]) -> None: ...
    def get_posterior(self, domain: str, key: str) -> dict[str, Any] | None: ...
    def list_posteriors(self, domain: str) -> list[dict[str, Any]]: ...
    def delete_posterior(self, domain: str, key: str) -> None: ...
    def save_promotion(self, domain: str, rule_id: str, state: dict[str, Any]) -> None: ...
    def get_promotion(self, domain: str, rule_id: str) -> dict[str, Any] | None: ...
    def list_promotions(self, domain: str) -> list[dict[str, Any]]: ...
    def delete_promotion(self, domain: str, rule_id: str) -> None: ...
    def save_ledger(self, domain: str, entry_id: str, state: dict[str, Any]) -> None: ...
    def get_ledger(self, domain: str, entry_id: str) -> dict[str, Any] | None: ...
    def list_ledgers(self, domain: str) -> list[dict[str, Any]]: ...
    def delete_ledger(self, domain: str, entry_id: str) -> None: ...
    def save_governance(self, domain: str, key: str, state: dict[str, Any]) -> None: ...
    def get_governance(self, domain: str, key: str) -> dict[str, Any] | None: ...
    def list_governance(self, domain: str) -> list[dict[str, Any]]: ...
    def delete_governance(self, domain: str, key: str) -> None: ...
    def count_correct(self, domain: str) -> int: ...
    def count_decisions(self, domain: str) -> int: ...
    def save_centroids(self, domain: str, category: str, centroids: Any, metadata: dict[str, Any] | None = None, **kwargs: Any) -> None: ...
    def load_latest_centroids(self, domain: str) -> Any | None: ...
    def get_centroid_checkpoints(self, domain: str, include_v2: bool = False, **kwargs: Any) -> list[dict[str, Any]]: ...
    def load_latest_checkpoint_for_regime(self, domain: str, regime_tag: str) -> dict[str, Any] | None: ...
    def get_checkpoint_lineage(self, domain: str, checkpoint_id: str) -> dict[str, Any] | None: ...
    def get_decision_checkpoints(self, domain: str, decision_id: str) -> list[dict[str, Any]]: ...
    def archive_old_decisions(self, domain: str, keep_recent: int = 800) -> int: ...
    def count_archived(self, domain: str) -> int: ...
    def close(self) -> None: ...
    def write_entity_enrichment(self, *, domain: str, entity_type: str, entity_id: str, namespace: str, metrics: dict[str, ProvenancedValue], computed_from: EnrichmentSourceSet, dry_run: bool = False, idempotency_key: str | None = None) -> EntityEnrichmentReceipt: ...
    def read_entity_enrichment(self, *, domain: str, entity_type: str, entity_id: str, namespace: str | None = None) -> dict[str, ProvenancedValue]: ...
    def list_entity_enrichments(self, *, domain: str, entity_type: str | None = None, namespace: str | None = None, limit: int = 500) -> list[EntityEnrichmentRecord]: ...
    def generate_decision_id(self, domain: str) -> str: ...
    def write_governed_decision(self, decision_id: str, domain: str, category: str, category_index: int, recommended_action: str, recommended_index: int, confidence: float, probabilities: list[float], factor_vector: list[float], factor_names: list[str], source: str = "score", scorer_version: str = "", preset_version: str = "", factor_schema_version: str = "", metadata: dict[str, Any] | None = None) -> None: ...
    def write_observation(self, observation_id: str, domain: str, category: str, recommended_action: str, confidence: float, source_route: str, scorer_version: str, factor_schema_version: str, entity_id: str | None = None, factor_vector: list[float] | None = None, factor_names: list[str] | None = None, metadata: dict[str, Any] | None = None) -> None: ...
    def append_evidence_receipt(self, receipt_intent_id: str, domain: str, decision_id: str, canonical_payload: dict[str, Any], actor: str, source_route: str, metadata: dict[str, Any] | None = None) -> tuple[int, str]: ...
    def write_conservation_status(self, status_id: str, domain: str, V: int, q: float, alpha: float, theta_min: float, verified_count: int, correct_count: int, status: str, policy_version: str) -> None: ...
    def write_fingerprint(self, fingerprint_id: str, domain: str, factor_names: list[str], factor_stats: dict[str, Any], skipped_incompatible: int, window: int, metadata: dict[str, Any] | None = None) -> None: ...
    def write_centroid_checkpoint(self, checkpoint_id: str, domain: str, category: str, action: str, centroids: Any, decisions_count: int, verified_count: int, iks: float, shape: list[int], factor_names_hash: str, quality_window_size: int | None = None, quality_verified_count: int | None = None, quality_correct_count: int | None = None, rolling_accuracy: float | None = None, quality_window_end: str | None = None, quality_policy_version: str | None = None, metadata: dict[str, Any] | None = None, decision_id: str | None = None) -> None: ...
    def write_evolution_event(self, event_id: str, domain: str, event_type: str, rule_name: str, variant_id: str, source_copilot: str | None = None, source_rule: str | None = None, metric: float | None = None, shadow_batch_size: int | None = None, min_shadow_batches: int | None = None, metadata: dict[str, Any] | None = None, decision_id: str | None = None) -> None: ...
    def get_evolution_events(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]: ...
    def write_transfer_pattern(self, pattern_id: str, source_domain: str, target_domain: str, pattern_type: str, factor_mapping: dict[str, Any], confidence: float, validation_status: str, conservation_status: str, source_rule: str | None = None, target_rule: str | None = None, source_fingerprint_id: str | None = None, evolution_event_id: str | None = None, metadata: dict[str, Any] | None = None) -> None: ...
    def get_transfer_patterns(self, source_domain: str | None = None, target_domain: str | None = None) -> list[dict[str, Any]]: ...
    def decision_movement(self, domain: str, decision_id: str) -> list[dict[str, Any]]: ...
    def contextual_judgment(self, domain: str, entity_group: str, category: str) -> list[dict[str, Any]]: ...
    def promotion_basis(self, domain: str, rule_id: str) -> list[dict[str, Any]]: ...
    def transfer_witness(self, source_domain: str, target_domain: str, pattern_id: str) -> list[dict[str, Any]]: ...
    def list_fingerprints(self, domain: str | None = None) -> list[dict[str, Any]]: ...
    def get_latest_conservation_statuses(self, domains: list[str] | None = None) -> list[dict[str, Any]]: ...
    def get_iks_trajectory(self, domains: list[str] | None = None, start: float | None = None, end: float | None = None) -> list[dict[str, Any]]: ...
    def link_entity(self, decision_id: str, entity_id: str, entity_type: str, domain: str) -> None: ...
    def archive_decisions(self, domain: str, before: float, status_filter: str = "pending", confirm_verified: bool = False) -> int: ...
    def domain_scoped_reset(self, domain: str) -> None: ...
```

`Any` in this declaration follows the current protocol signatures; do not broaden additional methods to `Any`. The forwarding bodies must transform arguments/records as stated above.

Methods that accept `domain=None` or multiple domains must filter inventory to this prefix, including transfer patterns where both endpoints must belong to the namespace. `EntityEnrichmentReceipt` and `EntityEnrichmentRecord` results must be copied with their `domain` unprefixed. Metadata payloads remain untouched except for explicit domain fields in the protocol arguments; do not recursively rewrite arbitrary user metadata. Add a conformance test that verifies runtime protocol membership and all domain-scoped operations against two namespace views sharing one underlying store.

## F-01 — Use one AGE graph for the S2P reasoning experiment

**Maps to:** V-01  
**Target files:** `apps/s2p_differentiation/engine.py`; `copilot_sdk/scoring/scorer.py`; graph namespace composition code and S2P tests  
**Principles:** P1, P8, P9

### Current state

`_make_scorer()` constructs a new InMemoryGraphStore for each call. `run_three_arms()` calls it independently for CI and hand-specified arms and selects the offline profile. Neither graph-backed arm exercises production AGE.

### Required state

Create exactly one AGEGraphStore connection per experiment run, and pass the same underlying store to all arms. Because arms need isolated learning histories, give each arm a graph namespace within the same AGE graph; the namespace is configuration and a record filter, not a separate connection, backend, or cache. Add `graph_namespace: str | None = None` to `CompoundingScorer.from_preset()` and route all graph API calls through a protocol-only namespace view that rewrites/filters domain scope while forwarding to the same underlying AGE store.

```python
def _make_scorer(
    graph_store: GraphStore, *, graph_namespace: str, enable_rl: bool,
) -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        "s2p",
        graph_store=graph_store,
        graph_namespace=graph_namespace,
        enable_rl=enable_rl,
        evolve=False,
        profile="production",
    )


def run_three_arms(..., graph_config: GraphConfig, run_id: str) -> dict[str, Any]:
    shared_store = create_graph_store(config=graph_config)
    ci = _make_scorer(
        shared_store, graph_namespace=f"s2p:{run_id}:ci", enable_rl=True
    )
    hand = _make_scorer(
        shared_store, graph_namespace=f"s2p:{run_id}:hand", enable_rl=False
    )
    ...
```

The `GraphStoreNamespace` view specified above must contain no persistence of its own and must forward every read/write to the exact same `shared_store`; it changes only the graph's logical domain namespace. Make the run fail closed if AGE config, shared graph authorization, or connection is unavailable. Keep baseline algorithms without graph state as algorithmic baselines; do not present them as exercising graph reasoning. Record run ID, shared graph identity (redacted), arm namespace, AGE profile, and configuration in experiment output.

### Migration notes

The current scorer binds preset domain and storage domain together. Keep public domain/preset semantics (`s2p`) while applying the namespace only to graph I/O. Audit every GraphStore call in the scorer so no method reads the base `s2p` domain by accident. Ensure all arm records are filtered by namespace and no arm can learn from another arm's outcomes.

### Test changes

- Modify/create `apps/s2p_differentiation/tests/test_engine_graph_sharing.py` to assert both scorers reference one underlying AGE store identity and distinct graph namespaces.
- Add a namespace-isolation integration test: a verified outcome in `ci` is absent from `hand` reads while both records reside in the same AGE graph.
- Add an AGE-unavailable test that asserts the experiment refuses to run; it must not construct InMemoryGraphStore.
- Update any engine test expecting `profile="development"` or per-scorer memory stores.
- Delete no experiment behavior tests; replace the invalid in-memory architecture assertions.

**Expected test delta:** 0 net tests; replace per-memory assertions with shared-graph/namespace assertions.  
**Dependencies:** F-02 and F-06 should settle scorer's fresh-read/domain-scope behavior before the namespace implementation is finalized.

## F-02 — Use rolling-400 verified accuracy for conservation

**Maps to:** V-02  
**Target files:** `copilot_sdk/scoring/scorer.py`; `copilot_sdk/backend/conservation_utils.py`; related tests  
**Principle:** P4

### PRE-CHECK

Before editing, read `copilot_sdk/scoring/scorer.py` and `copilot_sdk/backend/conservation_utils.py`. Trace the exact path from `_conservation_stats()` through `_conservation_pause()` to the primary gate evaluation. Confirm whether the rolling 400-window value currently calculated for checkpoint metadata drives the primary conservation signal. If it already drives any primary gate path, record that evidence and narrow F-02 to only the paths still using lifetime accuracy; do not duplicate or change an already-correct rolling calculation.

### Current state

The primary gate computes `q = correct / verified` from all verified decisions. Status payloads do the same. A 400-decision window exists for checkpoint reporting but does not drive the main gate.

### Required state

Keep `V` as the lifetime count of confirmed/overridden decisions. Compute `q` from the last 400 verified, non-benchmark decisions, ordered by the graph's canonical decision timestamp and stable ID. Use the exact same helper for `CompoundingScorer._conservation_pause()` and `compute_conservation_status_payload()`.

```python
def _rolling_q(
    decisions: Sequence[Mapping[str, Any]],
    *,
    window_size: int = QUALITY_WINDOW_SIZE,
) -> float | None:
    verified = [
        dict(row) for row in decisions
        if _is_verified_decision(dict(row)) and not _is_benchmark_decision(dict(row))
    ]
    if not verified:
        return None
    # When fewer than window_size verified decisions exist, use all of them.
    # This is the bootstrap/warm-up case; the gate may return calibration state.
    recent = verified[-window_size:] if len(verified) > window_size else verified
    return sum(_is_correct_decision(row) for row in recent) / len(recent)
```

At the gate boundary:

```python
V = len(all_verified_decisions)
alpha = _category_coverage_from_decisions(all_verified_decisions)
q = _rolling_q(all_verified_decisions)
if q is None:
    return _conservation_unavailable_or_bootstrap()
theta_min = compute_theta_min(alpha, V)
signal = alpha * q * V
```

The status endpoint must call the same helper and report the same `q`, `V`, `alpha`, and threshold as the scorer gate. Preserve the defined warm-up/bootstrap behavior, but never silently revert to lifetime accuracy when the window is unavailable. Remove competing count-based accuracy calculations from the authoritative path.

### Migration notes

This changes the meaning of `q` after the first 400 verified decisions, as required by the paper. Keep lifetime counts in `V`; do not change historical graph records. Confirm ordering across AGE and memory conformance fixtures.

### Test changes

- Update `tests/scoring/test_conservation.py` and `tests/test_conservation_utils.py` to use rolling rather than lifetime accuracy.
- Add tests for 399, 400, and 401 verified decisions; the last 400 must be used once length exceeds 400.
- Add a recent-degradation test where lifetime accuracy is high but rolling-400 accuracy is low; the gate must close.
- Add a parity assertion that conservation status API and scorer gate report identical q/V/alpha.
- Preserve tests proving observations and unverified pending decisions are excluded from V and q.

**Expected test delta:** 0 net tests; update inaccurate assertions and add 4 focused cases.  
**Dependencies:** None; F-06 cache removal must land before the final multi-client freshness verification.

## F-03 — Retire SQLiteGraphStore and DualWriteStore without blocking data cutover

**Maps to:** V-03  
**Target files:** `copilot_sdk/graph/sqlite_store.py`; `copilot_sdk/graph/dual_write_store.py`; `copilot_sdk/migrate/__main__.py`; migration/reconciliation code; exports/tests  
**Principles:** P1, P8

### Current state

Factory selection is limited to memory and AGE, but complete SQLiteGraphStore and DualWriteStore classes remain importable. The migration CLI constructs SQLiteGraphStore as a GraphStore source. OutcomeService still describes SQLite as the canonical V store.

### Required state

Migration source reading must be a read-only migration facility, never a GraphStore backend. Add typed archived-row data and a reader with no GraphStore inheritance/protocol conformance:

```python
@dataclass(frozen=True)
class ArchivedDecision:
    decision_id: str
    domain: str
    properties: Mapping[str, Any]


class LegacySQLiteArchiveReader:
    def __init__(self, source_path: Path) -> None:
        self.source_path = source_path

    def iter_decisions(self, domain: str) -> Iterator[ArchivedDecision]:
        with sqlite3.connect(self.source_path) as connection:
            connection.row_factory = sqlite3.Row
            columns = {str(row[1]) for row in connection.execute(
                "PRAGMA table_info(decisions)"
            )}
            if not columns:
                return
            for row in connection.execute(
                "SELECT * FROM decisions WHERE domain = ? ORDER BY created_at, decision_id",
                (domain,),
            ):
                yield ArchivedDecision(
                    decision_id=str(row["decision_id"]),
                    domain=str(row["domain"]),
                    properties=dict(row),
                )
```

Change `ArchiveReconciler` to consume `Iterable[ArchivedDecision]` plus an AGE GraphStore writer. Once no code imports the old classes, delete `sqlite_store.py` and `dual_write_store.py`, remove stale export/imports, and update tests. Correct OutcomeService's docstring: canonical state is the injected GraphStore; DurableOutbox is only a pending-write buffer.

### Migration notes

Do not delete historical SQLite data or migration tooling needed for cutover. Source retirement and data cutover are separate: after the reader is decoupled, the legacy database remains a read-only source until its records are copied and live-stack verification closes the cutover gap. SQLite may remain in the migration reader and the two outbox modules only; it must not implement GraphStore or be selectable by runtime callers.

### Test changes

- Modify migration CLI and `ArchiveReconciler` tests to pass `LegacySQLiteArchiveReader` rows, not `SQLiteGraphStore`.
- Retire graph-specific SQLite and DualWrite behavior tests only after mapping any required protocol contract coverage to memory/AGE parity tests.
- Add import/factory tests proving `SQLiteGraphStore` and `DualWriteStore` are no longer exported/selectable.
- Add migration source-read parity tests for legacy JSON/SQLite source records.
- Update architecture scans and `tests/test_age_unification_invariants.py`.

**Expected test delta:** Negative delta equal to backend-specific tests retired; migration behavior tests remain and should be replaced by reader/reconciliation tests. Capture exact counts at implementation time.  
**Dependencies:** First migrate CLI and test imports; delete implementation files last. Keep historical source cutover as a later verified operation.

## F-04 — Store cross-copilot signals in the shared graph

**Maps to:** V-04  
**Target files:** `copilot_sdk/backend/signal_store.py`; `copilot_sdk/backend/cross_signal_router.py`; Trading/Purchasing/DataOps `main.py`; graph adapter tests  
**Principles:** P1, P2, P8

### Current state

All three app roots create SQLiteSignalStore and the router silently defaults to SQLiteSignalStore when no store is supplied.

### Required state

Define the route in terms of ProtocolV2GraphStore and a graph event adapter. Remove the default and require explicit graph injection:

```python
class GraphSignalStore:
    PLATFORM_DOMAIN = "platform"

    def __init__(self, graph: ProtocolV2GraphStore) -> None:
        self.graph = graph

    def publish(self, signal: Mapping[str, Any]) -> str:
        signal_id = f"sig-{uuid4().hex[:8]}"
        payload = {**dict(signal), "signal_id": signal_id}
        stamp = _validated_utc_timestamp(payload.get("timestamp"))
        payload["timestamp"] = stamp.isoformat()
        self.graph.write_evolution_event(
            event_id=f"cross-signal:{signal_id}", domain=self.PLATFORM_DOMAIN,
            event_type="cross_copilot_signal", rule_name="cross_signal",
            variant_id=str(payload.get("target_copilot") or "platform"),
            source_copilot=str(payload["source_copilot"]),
            metadata={"signal": payload, "timestamp": payload["timestamp"]},
        )
        return signal_id

    def _active_signals(self) -> list[dict[str, Any]]:
        # The app contract caps signal inventory at MAX_SIGNALS (1,000).
        events = self.graph.get_evolution_events(
            self.PLATFORM_DOMAIN,
            event_type="cross_copilot_signal",
            limit=MAX_SIGNALS,
        )
        now = datetime.now(timezone.utc)
        active: list[dict[str, Any]] = []
        for event in events:
            metadata = event.get("metadata")
            payload = metadata.get("signal") if isinstance(metadata, Mapping) else None
            if not isinstance(payload, Mapping):
                continue
            signal = dict(payload)
            try:
                stamp = _validated_utc_timestamp(signal.get("timestamp"))
            except (TypeError, ValueError):
                continue
            if now - stamp > SIGNAL_TTL:
                continue
            signal.setdefault("signal_id", str(event.get("event_id", "")).removeprefix("cross-signal:"))
            active.append(signal)
        active.sort(key=lambda item: (str(item.get("timestamp", "")), str(item.get("signal_id", ""))))
        return active

    def page(
        self,
        *,
        source: str | None = None,
        target: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        if not 1 <= limit <= MAX_SIGNALS or offset < 0:
            raise ValueError("invalid pagination")
        matching = [
            item for item in self._active_signals()
            if (source is None or item.get("source_copilot") == source)
            and (target is None or item.get("target_copilot") in (None, target))
        ]
        return matching[offset:offset + limit], len(matching)

    def get(self, signal_id: str) -> dict[str, Any] | None:
        event = self.graph.get_evolution_events(
            self.PLATFORM_DOMAIN,
            event_type="cross_copilot_signal",
            limit=MAX_SIGNALS,
        )
        for row in event:
            event_id = str(row.get("event_id") or "")
            metadata = row.get("metadata")
            payload = metadata.get("signal") if isinstance(metadata, Mapping) else None
            if event_id != f"cross-signal:{signal_id}" or not isinstance(payload, Mapping):
                continue
            signal = dict(payload)
            try:
                stamp = _validated_utc_timestamp(signal.get("timestamp"))
            except (TypeError, ValueError):
                return None
            if datetime.now(timezone.utc) - stamp > SIGNAL_TTL:
                return None
            return signal
        return None


def _validated_utc_timestamp(value: Any) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def create_cross_signal_router(store: ProtocolV2GraphStore) -> APIRouter:
    signal_store = GraphSignalStore(store)
    ...
```

The `page()` and `get()` methods above are the read path. Both call `get_evolution_events("platform", event_type="cross_copilot_signal", limit=MAX_SIGNALS)` through the protocol, decode `metadata["signal"]`, and never consult an outbox. `page()` drops expired records, applies exact `source_copilot` filtering, preserves the existing global-target behavior (`target_copilot is None` is visible to any requested target), sorts by `(timestamp, signal_id)`, computes total after filtering, then slices by offset/limit. `get()` matches `cross-signal:{signal_id}`, applies the same TTL test, and returns `None` when absent or expired. Malformed payloads are skipped rather than broadening a query. The implementation imports `datetime/timezone`, `uuid4`, `Mapping`, and existing TTL/count constants. Add a verification that the AGE adapter filters `event_type` before applying its 1,000-record bound; if not, surface the limitation and do not claim complete pagination.

The cross-signal route calls `signal_store.page(source=source_copilot, target=target_copilot, limit=limit, offset=offset)`. App roots pass their already-selected `selected_graph_store_factory(...)` object; do not call a second factory or construct a new persistence store.

### Migration notes

Map signal IDs to stable graph event IDs and preserve existing response fields. Outbox buffering may protect writes while AGE is unavailable but must never serve `/cross-signals` reads.

### Test changes

- Replace `tests/test_cross_signal_router.py` and `tests/test_signal_store.py` SQLite assertions with GraphStore API assertions.
- Add graph round-trip, source/target filtering, expiration, idempotency, and outage/no-buffer-read tests.
- Update three app wiring tests to assert same graph object is injected into scoring and signal routes.

**Expected test delta:** 0 net tests; replace implementation-specific tests with graph semantics tests.  
**Dependencies:** F-03 should keep the ProtocolV2 surface stable; F-08 uses this event shape.

## F-05 — Remove non-graph persistent authorities for outcomes and learned state

**Maps to:** V-05  
**Target files:** `copilot_sdk/outcome/ledger.py`; `copilot_sdk/promotion/core.py`; `copilot_sdk/evolution/variant_store.py`; `copilot_sdk/twin/store.py`; `apps/purchasing/backend/app/services/purchasing_control.py`; `apps/trading/backend/app/services/claim_gate.py`; package exports/tests  
**Principles:** P1, P3, P5, P8

### Current state

The code exposes SQLite outcome, promotion, and variant stores and a file-backed frozen twin store. Purchasing and Trading retain fallback branches; PromotionEngine defaults to a SQLite PromotionStore. The graph adapters already exist for outcome, proof, promotion, variant, and frozen twin records.

### Required state

Require explicit graph persistence at integrated service boundaries; remove durable fallback construction. Keep test doubles scoped to isolated unit tests and never use them as an app's authority.

```python
class PurchasingControlService:
    def __init__(
        self,
        graph_store_factory: Callable[[], ProtocolV2GraphStore],
        scorer_provider: Callable[[], Any],
        data_dir: Path,
    ) -> None:
        graph = graph_store_factory()
        self.proof = GraphProofLedger(graph, "purchasing")
        self.outcomes = GraphOutcomeLedger(graph, "purchasing")
        self.twin = FrozenTwin(GraphFrozenTwinStore(graph, "purchasing"))
        self.promotion = PromotionEngine(
            PurchasingPromotionPolicy(), GraphPromotionStore(graph, "purchasing")
        )
```

Change `PromotionEngine.__init__` to require a store implementing its persistence interface; remove `store or PromotionStore()`. `TradingPromotionGuard` must require the app's injected GraphPromotionStore (or an explicit in-memory test double in unit tests); do not silently instantiate SQLite. Remove SQLiteVariantStore from exports and production use; `create_variant_store()` remains GraphVariantStore for AGE and InMemoryVariantStore only for explicit test mode. Make FrozenTwinStore a test/local implementation; integrated apps always use GraphFrozenTwinStore and fail closed if graph persistence is unavailable.

### Migration notes

Keep record schemas and IDs when moving data into the graph. Do not silently drop existing SQLite outcome, promotion, variant, or frozen-twin data; provide read-only migration extraction and parity verification before retiring old files. Outbox modules remain untouched and hold only pending graph writes.

### Test changes

- Rewrite `tests/test_outcome_protocol.py`, `tests/test_promotion_engine.py`, and `tests/evolution/test_sqlite_variant_store.py` to verify graph adapters and explicit in-memory test doubles.
- Update Purchasing control tests to assert that unsupported graph protocols fail closed instead of selecting SQLite/file stores.
- Update Trading claim-gate tests to inject a PromotionStore test double or GraphPromotionStore.
- Add graph readback tests for outcome receipts, promotions, variant history, and frozen-twin snapshots.
- Retain migration parity tests for any existing persisted records until data cutover is verified.

**Expected test delta:** SQLite implementation-only tests removed and replaced; lifecycle tests retained. Exact net delta depends on migration tests retained.  
**Dependencies:** F-03 before deleting SQLiteGraphStore; other graph adapters already exist.

## F-06 — Remove cross-request cache of graph decisions

**Maps to:** V-06  
**Target file:** `copilot_sdk/scoring/scorer.py`  
**Principles:** P1, P4, P8

### Current state

`_verified_decisions_cache` survives between calls and is invalidated only by local writes.

### Required state

Delete the cached field, cached-return branch, and invalidation assignments. Each scoring/learning/conservation operation reads a fresh graph snapshot once and passes that snapshot within the operation. Example:

```python
def _verified_decisions(self) -> list[dict[str, Any]]:
    rows = self._graph_store.get_verified_decisions(self._domain)
    return [row for row in rows if _is_verified_decision(row)]
```

Do not cache the result on the scorer object. This snapshot may be reused only for subcalculations in the same call.

### Migration notes

Expect more GraphStore reads. If performance is a concern, optimize the AGE query/projection and indexes; do not restore an application cache that changes cross-process freshness.

### Test changes

- Replace cache-invalidation unit tests with a two-client freshness test: writer B commits outcome; scorer A's next conservation/verified read sees it.
- Retain single-operation consistency tests proving helpers share one local snapshot.

**Expected test delta:** 0 net tests.  
**Dependencies:** Implement before F-02's final stale-state tests; these two may be delivered as one prompt.

## F-07 — Remove query-serving response and context caches

**Maps to:** V-07  
**Target files:** `copilot_sdk/di/query_service.py`; `copilot_sdk/backend/scoring_router.py`; `copilot_sdk/backend/conservation_router.py`; `copilot_sdk/backend/response_materializer.py`; three app main files  
**Principles:** P1, P2, P8

### Current state

DIQueryService returns cached complete QueryResponse objects. Scoring requests may receive prior EntityCache context through EntityContextCacheAdapter.

### Required state

Remove DI response-cache configuration/state and execute the provider for every query. Remove the scoring router's cache enrichment hook and the app-level EntityCache/EntityContextCacheAdapter wiring from the scoring path. Remove graph-derived conservation responses from ResponseMaterializer and make the conservation route resolve current state for every request. Keep caller-provided request context; resolve additional graph context through the shared graph on each request.

```python
def execute(self, request: QueryRequest | Mapping[str, Any]) -> QueryResponse:
    query_request = (
        request if isinstance(request, QueryRequest)
        else QueryRequest.model_validate(request)
    )
    query_id = str(uuid4())
    started = datetime.now(timezone.utc)
    plan = self.parse(query_request.question, context=query_request.context)
    # Always route against the current provider/graph state.
    result = self.compute(plan, self.route(plan))
    return self._build_response(plan, query_id, started, result)
```

Retain memoization only for pure work scoped to one request. Do not cache a QueryResponse or graph-derived context between requests.

### Migration notes

Remove cache hit/miss fields and TTL environment setting from response contracts only if they are solely internal; if clients depend on them, keep a constant `cache="miss"` compatibility field and deprecate it. Do not keep a hidden cache for compatibility.

### Test changes

- Update `tests/test_di_query_service.py` to assert each call invokes the provider and reflects changed data.
- Update scoring-router tests to ensure current request context and graph context are used without cached substitutions.
- Update conservation-router/materializer tests to assert that status requests resolve current graph-backed state rather than returning a prior materialized payload.
- Remove app cache-stat assertions tied only to EntityCache; preserve unrelated static/config cache tests.

**Expected test delta:** 0 net tests; replace cache-specific expectations with freshness tests.  
**Dependencies:** None.

## F-08 — Share the local demo graph and persist demo signal evidence

**Maps to:** V-08  
**Target file:** `copilot_sdk/demo/preseed.py` and demo tests  
**Principles:** P1, P2

### Current state

Each `_preseed_domain()` call creates a new InMemoryGraphStore. `seed_cross_copilot_signal()` returns a dict without writing a graph artifact.

### Required state

Create one offline graph in `DemoPreseeder` and reuse it for every local demo scorer. `InMemoryGraphStore` operations are domain-multi-tenant: protocol methods receive `domain` explicitly and store/query records by that argument; its constructor `domain` does not filter those operations. The constructor domain is used only by legacy RL-state convenience methods, so keep demo scorers at `enable_rl=False` (as currently configured) and do not use those convenience methods for this shared fixture. No `GraphStoreNamespace` is needed for these domain-explicit memory calls. If the demo later needs RL state, add an explicitly domain-scoped protocol path before enabling it; do not share the legacy constructor-bound RL state across domains. Persist/read signal events in this same graph. Integrated demo mode must instead receive one AGE GraphStore from composition and must not fallback to memory.

```python
class DemoPreseeder:
    def __init__(self, seed: int = DEFAULT_SEED, fast_mode: bool = False) -> None:
        self.seed = int(seed)
        self.fast_mode = bool(fast_mode)
        self._graph_store = InMemoryGraphStore(domain="demo")
        self._scorers: dict[str, CompoundingScorer] = {}

    def _preseed_domain(self, domain: str) -> CopilotPreseedResult:
        scorer = CompoundingScorer.from_preset(
            domain, graph_store=self._graph_store, enable_rl=False, profile="offline"
        )
        ...
```

Each scorer continues to call domain-explicit GraphStore methods with its own logical domain (for example, `trading`, `purchasing`, or `dataops`). Assert that reads for each domain contain only that domain's records even though all scorers share the same `InMemoryGraphStore` object.

`seed_cross_copilot_signal()` writes a `cross_copilot_signal` graph event and reads it back by ID. The shared local graph remains explicitly offline/demo and is not used as production or reasoning-quality evidence.

### Migration notes

Verify each scorer uses domain-explicit GraphStore methods on the shared instance. The current API needs no domain-bound view for decision/outcome/centroid/event operations. If a future operation lacks an explicit domain parameter, stop and design a namespace-safe protocol path before using it; do not silently route it through the constructor-bound RL-state helpers. Do not create one memory instance per copilot.

### Test changes

- Update `tests/test_preseed.py`: assert all demo scorers share one underlying graph identity and each decision/outcome remains in its domain scope.
- Add signal event round-trip/readback and stable ID assertions.
- Keep tests confirming production profile rejects demo preseed.

**Expected test delta:** 0 net tests.  
**Dependencies:** F-04 graph signal event contract.

## F-09 — Require governed transfer artifacts; prohibit synthetic transfer fallback

**Maps to:** V-09  
**Target file:** `copilot_sdk/backend/transfer_router.py`; transfer types/adapters/tests  
**Principles:** P2, P4, P10

### Current state

When no source pattern exists, the router creates fixed synthetic `TransferPattern` values, applies them, and stores a transfer with `validation_status="validated"`. The graph artifact records only target conservation status and does not preserve the source status or source artifact IDs.

### Required state

Remove `_demo_patterns_for_mapping()` from execution. Require registered, graph-persisted source artifacts. Revalidate both source and target conservation and the factor mapping before applying. Persist source/target states, source artifact IDs, mapping, validation details, and provenance as one graph transfer artifact.

```python
patterns = _patterns_for_execute(
    scorer, source_domain, target_domain, mapping, explicit_registry
)
if not patterns:
    raise HTTPException(
        status_code=409,
        detail="No governed source transfer artifact is available",
    )

source_state = _source_conservation_state(scorer, source_domain)
target_state = _target_conservation_state(scorer, target_domain)
if source_state != "GREEN" or target_state != "GREEN":
    return _blocked_transfer(source_domain, target_domain, source_state, target_state)
```

After `warm_start` reports an applied, schema-safe transfer:

```python
store.write_transfer_pattern(
    pattern_id=transfer_id,
    source_domain=source_domain,
    target_domain=target_domain,
    pattern_type="judgment_memory_transfer",
    factor_mapping=mapping,
    confidence=summary.score,
    validation_status="validated",
    conservation_status=target_state,
    metadata={
        "source_conservation": source_state,
        "target_conservation": target_state,
        "source_artifact_ids": [pattern.pattern_id for pattern in patterns],
        "factor_mapping": mapping,
        "provenance": "governed_graph_transfer",
    },
)
```

Do not call this write for demo/synthetic patterns. If a demo UI needs a preview, label it as a non-applied preview and do not write or alter centroids.

### Migration notes

Existing transfer pattern schemas must remain readable. Historical transfers lacking source-state metadata should be labeled legacy/unverified during readback, not retroactively presented as validated.

### Test changes

- Update `tests/test_transfer_router.py` to expect no-pattern transfer blocked with no centroid mutation.
- Add tests rejecting demo provenance and validating exact source/target conservation metadata.
- Add AGE graph readback test proving factor mapping and source artifact links persist.
- Keep tests for target-domain validation and both conservation gates.

**Expected test delta:** 0 net tests.  
**Dependencies:** None; coordinate with F-04 only if a signal is proposed as source evidence.

## Implementation order

| Group | Fixes | Order/dependency |
|---|---|---|
| 1 | F-02 | First; canonical conservation math |
| 2 | F-06, F-07 | Sequential after Group 1; remove stale graph-derived reads; F-07 is P1 under P8 |
| 3 | F-01 + GraphStoreNamespace | After scorer storage namespace/API decision from Groups 1–2; build and test the shared namespace component in this group |
| 4 | F-03 | Decouple migration source reader first; delete old implementations last |
| 5 | F-04 | Independent after graph event contract is settled; can develop in parallel with Group 4 |
| 6 | F-05 | After GraphStore migration reader/backend retirement design is stable; graph adapters already exist |
| 7 | F-09 | Independent; no synthetic write path remains after fix |
| 8 | F-08 | After F-04 defines graph signal event shape; current explicit-domain demo calls do not require the namespace view |

Groups 4 and 5 can be implemented concurrently after protocol/API decisions are recorded. Groups 6 and 7 can also be implemented concurrently. Groups 1 and 2 are sequential because both affect scorer freshness and conservation. Group 3 (including GraphStoreNamespace) follows those scorer API decisions. Group 8 follows Group 5; it can reuse GraphStoreNamespace only if a future demo operation lacks explicit domain arguments. Run full regression suites after integration, not in parallel with shared source edits.

## Verification plan

Expected counts below are regression constraints, not promises that the current dirty working tree has those exact counts. At each implementation group, capture a fresh baseline and require zero new failures; only delete tests that exclusively encode a retired implementation and replace their protocol/lifecycle coverage.

| Group | Exact verification commands | Expected result |
|---|---|---|
| 1 | `python -m pytest tests/scoring/test_conservation.py tests/test_conservation_utils.py -q --timeout=120`; `python -m mypy copilot_sdk/scoring/scorer.py copilot_sdk/backend/conservation_utils.py --config-file pyproject.toml` | Focused tests pass; exact window semantics; no new SDK/app failures. |
| 2 | `python -m pytest tests/test_di_query_service.py tests/test_scoring_router.py tests/scoring/test_conservation.py -q --timeout=120`; run two-client graph freshness tests; `python -m mypy copilot_sdk/scoring/scorer.py copilot_sdk/di/query_service.py copilot_sdk/backend/scoring_router.py --config-file pyproject.toml` | Provider/store reads are fresh each request; no cache fallback; type checks pass. |
| 3 | `python -m pytest apps/s2p_differentiation/ -q --timeout=120`; `python -m pytest tests/ -q --timeout=120`; live AGE S2P integration test with namespace assertions | Same AGE store identity for graph arms, isolated arm namespaces, unavailable AGE fails closed. |
| 4 | `python -m pytest tests/ -q --timeout=120`; migration integration tests; `python -m mypy copilot_sdk/migrate/ copilot_sdk/graph/ --config-file pyproject.toml` | No imports of SQLiteGraphStore/DualWriteStore; migration remains read-only-source to AGE-target; source cutover is not claimed without live verification. |
| 5 | `python -m pytest tests/test_cross_signal_router.py tests/test_signal_store.py -q --timeout=120`; `python -m pytest apps/trading/backend/tests/ apps/purchasing/backend/tests/ apps/dataops/backend/tests/ -q --timeout=120`; live AGE signal round-trip | Each app routes signals through its selected graph; no SQLite default; outage buffer never serves reads. |
| 6 | `python -m pytest tests/test_outcome_protocol.py tests/test_promotion_engine.py tests/evolution/ -q --timeout=120`; all three app backend suites; mypy for modified adapters/apps | Outcome/promotion/variant/twin readback from graph; no durable side-store fallback. |
| 7 | `python -m pytest tests/test_transfer_router.py -q --timeout=120`; all app backend suites; live AGE transfer round-trip | No fabricated/demo transfer is applied; source/target state and artifact mapping are inspectable. |
| 8 | `python -m pytest tests/test_preseed.py -q --timeout=120`; `python -m pytest tests/ -q --timeout=120`; AGE demo smoke when configured | Offline demo scorers share one memory graph; integrated mode uses one AGE graph or fails closed. |

After all groups: run `python -m pytest tests/ -q --timeout=120`, all three app backend suites, S2P experiment integration against AGE, mypy on every changed file, and the architecture scans for SQLiteGraphStore, DualWriteStore, SQLiteSignalStore, persistent/query-serving caches, and per-arm InMemoryGraphStore use. Live-stack probes remain necessary to claim production graph closure.

## Self-review results

1. **P1 fixes specified with executable design logic:** PASS — F-01, F-02, F-03, F-04, F-05, F-06, and F-09 include signatures and key Python logic.
2. **S2P uses one shared AGE graph:** PASS — F-01 mandates one underlying AGE store, namespaces as configuration, and no memory fallback or per-arm store.
3. **No DecisionStore, SQLiteGraphStore, or persistent cache introduced:** PASS — the plan removes those authorities; the only SQLite persistence left is the explicitly exempt write-only outbox and migration-scoped read-only source extraction until cutover.
4. **Outbox exemptions preserved:** PASS — both outbox modules remain bounded write buffers and never serve reads.
5. **Implementation order respects dependencies:** PASS — scorer/window/cache work precedes experiment namespace decisions; migration reader decoupling precedes backend deletion; demo signal depends on graph signal contract.
6. **Every fix traces to principles:** PASS — every F-XX maps to a V-XX and cites its P principles.
7. **Concrete test impact provided:** PASS — each group lists test paths, cases, suite commands, and expected count change/measurement policy.
