# Step 11A: GraphStoreNamespace design

## Pre-check

Step 9 is complete by its recorded PASS result (session_state.md:7910); the entry does not literally use COMPLETE. Baseline: 4,295 SDK passes and 1 xfail. No namespace implementation/test/design files existed; prior work is complete and no conflicting work is recorded. No git commands were used. This step does not wire the engine or any app main.py.

## 1. Complete Method Inventory

GraphStore: 45 declarations. V2: 22 declarations, including one inherited redeclaration (count_verified_decisions). Total: 66 unique methods. There are no pure PASSTHROUGH or RESULT-REWRITE-only methods: all methods except close/reset take domain parameters. GraphTraversalStore, ScoringPersistenceStore and L5LearningStore are separate protocols, not inherited by V2; their additional methods are not added.

### GraphStore.write_decision — DOMAIN-REWRITE

```python
def write_decision(self, domain: str, category: str, action: str, confidence: float, factors: dict[str, Any], metadata: dict[str, Any] | None=None) -> str
```
reject explicit metadata decision_id override; prefix domain and delegate; return opaque ID.

### GraphStore.write_outcome — DOMAIN-REWRITE

```python
def write_outcome(self, decision_id: str, actual_action: str, is_correct: bool, metadata: dict[str, Any] | None=None, *, domain: str, outcome: str | None=None, verified_at_epoch: float | None=None, quality_signal: float | None=None, override_comment: str | None=None, verified_by: str | None=None, analyst_action: str | None=None, final_action: str | None=None, recommended_action: str | None=None, was_override: bool | None=None) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.get_decision — BOTH

```python
def get_decision(self, decision_id: str, domain: str, *, include_outcome: bool=False) -> dict[str, Any] | None
```
prefix domain; return None for missing/foreign result, otherwise _row(result).

### GraphStore.get_decisions — BOTH

```python
def get_decisions(self, domain: str, category: str | None=None, limit: int=400) -> list[dict[str, Any]]
```
prefix domain parameters; return _rows(delegate(...)).

### GraphStore.get_all_decisions — BOTH

```python
def get_all_decisions(self, domain: str) -> list[dict[str, Any]]
```
prefix domain parameters; return _rows(delegate(...)).

### GraphStore.get_archived_decisions — BOTH

```python
def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]
```
prefix domain parameters; return _rows(delegate(...)).

### GraphStore.get_verified_decisions — BOTH

```python
def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]
```
prefix domain parameters; return _rows(delegate(...)).

### GraphStore.count_verified — DOMAIN-REWRITE

```python
def count_verified(self, domain: str) -> int
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.count_verified_decisions — DOMAIN-REWRITE

```python
def count_verified_decisions(self, domain: str) -> int
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.save_evolution — DOMAIN-REWRITE

```python
def save_evolution(self, domain: str, variant_id: str, state: dict[str, Any]) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.get_evolution — DOMAIN-REWRITE

```python
def get_evolution(self, domain: str, variant_id: str) -> dict[str, Any] | None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.list_evolutions — DOMAIN-REWRITE

```python
def list_evolutions(self, domain: str) -> list[dict[str, Any]]
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.delete_evolution — DOMAIN-REWRITE

```python
def delete_evolution(self, domain: str, variant_id: str) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.save_evolution_state — DOMAIN-REWRITE

```python
def save_evolution_state(self, domain: str, variant_id: str, state: dict[str, Any]) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.get_evolution_state — DOMAIN-REWRITE

```python
def get_evolution_state(self, domain: str, variant_id: str) -> dict[str, Any] | None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.save_posterior — DOMAIN-REWRITE

```python
def save_posterior(self, domain: str, key: str, state: dict[str, Any]) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.get_posterior — DOMAIN-REWRITE

```python
def get_posterior(self, domain: str, key: str) -> dict[str, Any] | None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.list_posteriors — DOMAIN-REWRITE

```python
def list_posteriors(self, domain: str) -> list[dict[str, Any]]
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.delete_posterior — DOMAIN-REWRITE

```python
def delete_posterior(self, domain: str, key: str) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.save_promotion — DOMAIN-REWRITE

```python
def save_promotion(self, domain: str, rule_id: str, state: dict[str, Any]) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.get_promotion — DOMAIN-REWRITE

```python
def get_promotion(self, domain: str, rule_id: str) -> dict[str, Any] | None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.list_promotions — DOMAIN-REWRITE

```python
def list_promotions(self, domain: str) -> list[dict[str, Any]]
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.delete_promotion — DOMAIN-REWRITE

```python
def delete_promotion(self, domain: str, rule_id: str) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.save_ledger — DOMAIN-REWRITE

```python
def save_ledger(self, domain: str, entry_id: str, state: dict[str, Any]) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.get_ledger — DOMAIN-REWRITE

```python
def get_ledger(self, domain: str, entry_id: str) -> dict[str, Any] | None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.list_ledgers — DOMAIN-REWRITE

```python
def list_ledgers(self, domain: str) -> list[dict[str, Any]]
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.delete_ledger — DOMAIN-REWRITE

```python
def delete_ledger(self, domain: str, entry_id: str) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.save_governance — DOMAIN-REWRITE

```python
def save_governance(self, domain: str, key: str, state: dict[str, Any]) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.get_governance — DOMAIN-REWRITE

```python
def get_governance(self, domain: str, key: str) -> dict[str, Any] | None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.list_governance — DOMAIN-REWRITE

```python
def list_governance(self, domain: str) -> list[dict[str, Any]]
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.delete_governance — DOMAIN-REWRITE

```python
def delete_governance(self, domain: str, key: str) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.count_correct — DOMAIN-REWRITE

```python
def count_correct(self, domain: str) -> int
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.count_decisions — DOMAIN-REWRITE

```python
def count_decisions(self, domain: str) -> int
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.save_centroids — DOMAIN-REWRITE

```python
def save_centroids(self, domain: str, category: str, centroids: Any, metadata: dict[str, Any] | None=None, **kwargs: Any) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.load_latest_centroids — DOMAIN-REWRITE

```python
def load_latest_centroids(self, domain: str) -> Any | None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.get_centroid_checkpoints — BOTH

```python
def get_centroid_checkpoints(self, domain: str, include_v2: bool=False, **kwargs: Any) -> list[dict[str, Any]]
```
prefix domain parameters; return _rows(delegate(...)).

### GraphStore.load_latest_checkpoint_for_regime — BOTH

```python
def load_latest_checkpoint_for_regime(self, domain: str, regime_tag: str) -> dict[str, Any] | None
```
prefix domain; return None for missing/foreign result, otherwise _row(result).

### GraphStore.get_checkpoint_lineage — BOTH

```python
def get_checkpoint_lineage(self, domain: str, checkpoint_id: str) -> dict[str, Any] | None
```
prefix domain; return None for missing/foreign result, otherwise _row(result).

### GraphStore.get_decision_checkpoints — BOTH

```python
def get_decision_checkpoints(self, domain: str, decision_id: str) -> list[dict[str, Any]]
```
prefix domain parameters; return _rows(delegate(...)).

### GraphStore.archive_old_decisions — DOMAIN-REWRITE

```python
def archive_old_decisions(self, domain: str, keep_recent: int=800) -> int
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.count_archived — DOMAIN-REWRITE

```python
def count_archived(self, domain: str) -> int
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.close — NOOP

```python
def close(self) -> None
```
return None; never close borrowed store.

### GraphStore.write_entity_enrichment — BOTH

```python
def write_entity_enrichment(self, *, domain: str, entity_type: str, entity_id: str, namespace: str, metrics: dict[str, ProvenancedValue], computed_from: EnrichmentSourceSet, dry_run: bool=False, idempotency_key: str | None=None) -> EntityEnrichmentReceipt
```
prefix domain; delegate; validate receipt domain; dataclasses.replace(domain=_logical_domain(receipt.domain)).

### GraphStore.read_entity_enrichment — DOMAIN-REWRITE

```python
def read_entity_enrichment(self, *, domain: str, entity_type: str, entity_id: str, namespace: str | None=None) -> dict[str, ProvenancedValue]
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### GraphStore.list_entity_enrichments — BOTH

```python
def list_entity_enrichments(self, *, domain: str, entity_type: str | None=None, namespace: str | None=None, limit: int=500) -> list[EntityEnrichmentRecord]
```
prefix domain; delegate; filter foreign typed records; replace domain on detached copies.

### ProtocolV2GraphStore.generate_decision_id — DOMAIN-REWRITE

```python
def generate_decision_id(self, domain: str) -> str
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### ProtocolV2GraphStore.write_governed_decision — DOMAIN-REWRITE

```python
def write_governed_decision(self, decision_id: str, domain: str, category: str, category_index: int, recommended_action: str, recommended_index: int, confidence: float, probabilities: list[float], factor_vector: list[float], factor_names: list[str], source: str='score', scorer_version: str='', preset_version: str='', factor_schema_version: str='', metadata: dict[str, Any] | None=None) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### ProtocolV2GraphStore.write_observation — DOMAIN-REWRITE

```python
def write_observation(self, observation_id: str, domain: str, category: str, recommended_action: str, confidence: float, source_route: str, scorer_version: str, factor_schema_version: str, entity_id: str | None=None, factor_vector: list[float] | None=None, factor_names: list[str] | None=None, metadata: dict[str, Any] | None=None) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### ProtocolV2GraphStore.append_evidence_receipt — DOMAIN-REWRITE

```python
def append_evidence_receipt(self, receipt_intent_id: str, domain: str, decision_id: str, canonical_payload: dict[str, Any], actor: str, source_route: str, metadata: dict[str, Any] | None=None) -> tuple[int, str]
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### ProtocolV2GraphStore.write_conservation_status — DOMAIN-REWRITE

```python
def write_conservation_status(self, status_id: str, domain: str, V: int, q: float, alpha: float, theta_min: float, verified_count: int, correct_count: int, status: str, policy_version: str) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### ProtocolV2GraphStore.write_fingerprint — DOMAIN-REWRITE

```python
def write_fingerprint(self, fingerprint_id: str, domain: str, factor_names: list[str], factor_stats: dict[str, Any], skipped_incompatible: int, window: int, metadata: dict[str, Any] | None=None) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### ProtocolV2GraphStore.write_centroid_checkpoint — DOMAIN-REWRITE

```python
def write_centroid_checkpoint(self, checkpoint_id: str, domain: str, category: str, action: str, centroids: Any, decisions_count: int, verified_count: int, iks: float, shape: list[int], factor_names_hash: str, quality_window_size: int | None=None, quality_verified_count: int | None=None, quality_correct_count: int | None=None, rolling_accuracy: float | None=None, quality_window_end: str | None=None, quality_policy_version: str | None=None, metadata: dict[str, Any] | None=None, decision_id: str | None=None) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### ProtocolV2GraphStore.write_evolution_event — DOMAIN-REWRITE

```python
def write_evolution_event(self, event_id: str, domain: str, event_type: str, rule_name: str, variant_id: str, source_copilot: str | None=None, source_rule: str | None=None, metric: float | None=None, shadow_batch_size: int | None=None, min_shadow_batches: int | None=None, metadata: dict[str, Any] | None=None, decision_id: str | None=None) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### ProtocolV2GraphStore.get_evolution_events — BOTH

```python
def get_evolution_events(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]
```
prefix domain parameters; return _rows(delegate(...)).

### ProtocolV2GraphStore.write_transfer_pattern — DOMAIN-REWRITE

```python
def write_transfer_pattern(self, pattern_id: str, source_domain: str, target_domain: str, pattern_type: str, factor_mapping: dict[str, Any], confidence: float, validation_status: str, conservation_status: str, source_rule: str | None=None, target_rule: str | None=None, source_fingerprint_id: str | None=None, evolution_event_id: str | None=None, metadata: dict[str, Any] | None=None) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### ProtocolV2GraphStore.get_transfer_patterns — BOTH

```python
def get_transfer_patterns(self, source_domain: str | None=None, target_domain: str | None=None) -> list[dict[str, Any]]
```
require at least one filter; prefix each supplied domain; return _rows(delegate(...)).
BLOCKED when both domain filters are None; otherwise prefix supplied filters and reject results with either foreign endpoint.

### ProtocolV2GraphStore.decision_movement — BOTH

```python
def decision_movement(self, domain: str, decision_id: str) -> list[dict[str, Any]]
```
prefix domain parameters; return _rows(delegate(...)).

### ProtocolV2GraphStore.contextual_judgment — BOTH

```python
def contextual_judgment(self, domain: str, entity_group: str, category: str) -> list[dict[str, Any]]
```
prefix domain parameters; return _rows(delegate(...)).

### ProtocolV2GraphStore.promotion_basis — BOTH

```python
def promotion_basis(self, domain: str, rule_id: str) -> list[dict[str, Any]]
```
prefix domain parameters; return _rows(delegate(...)).

### ProtocolV2GraphStore.transfer_witness — BOTH

```python
def transfer_witness(self, source_domain: str, target_domain: str, pattern_id: str) -> list[dict[str, Any]]
```
prefix domain parameters; return _rows(delegate(...)).

### ProtocolV2GraphStore.list_fingerprints — BOTH

```python
def list_fingerprints(self, domain: str | None=None) -> list[dict[str, Any]]
```
require domain; return _rows(delegate(_domain(domain))).
BLOCKED when domain=None.

### ProtocolV2GraphStore.get_latest_conservation_statuses — BOTH

```python
def get_latest_conservation_statuses(self, domains: list[str] | None=None) -> list[dict[str, Any]]
```
validate domains; [] -> []; delegate with every domain prefixed; return _rows(result).
BLOCKED when domains=None; [] returns [] without calling store.

### ProtocolV2GraphStore.get_iks_trajectory — BOTH

```python
def get_iks_trajectory(self, domains: list[str] | None=None, start: float | None=None, end: float | None=None) -> list[dict[str, Any]]
```
validate domains; [] -> []; delegate with every domain prefixed; return _rows(result).
BLOCKED when domains=None; [] returns [] without calling store.

### ProtocolV2GraphStore.link_entity — DOMAIN-REWRITE

```python
def link_entity(self, decision_id: str, entity_id: str, entity_type: str, domain: str) -> None
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### ProtocolV2GraphStore.archive_decisions — DOMAIN-REWRITE

```python
def archive_decisions(self, domain: str, before: float, status_filter: str='pending', confirm_verified: bool=False) -> int
```
prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged.

### ProtocolV2GraphStore.domain_scoped_reset — BLOCKED

```python
def domain_scoped_reset(self, domain: str) -> None
```
raise RuntimeError before delegation.

## 2. Core Helpers

- `_domain(domain: str) -> str`: validate nonblank string, then concatenate namespace + "::" + domain. Never treat caller input as an already-physical domain.
- `_logical_domain(domain: str) -> str`: accept only this exact prefix and a nonempty suffix; remove one prefix. Foreign input raises ValueError.
- `_belongs(row: Mapping[str, Any]) -> bool`: require at least one structural domain field; every domain/source_domain/target_domain found in the projection must belong to this namespace. Recurse through nested projection mappings/lists. Do not inspect opaque user payload fields (metadata, outcome_metadata, context, factors, factor_stats, fingerprint, factor_mapping, canonical_payload, payload, state, metrics, computed_from, centroids).
- `_row(row: Mapping[str, Any]) -> dict[str, Any]`: require membership, recursively detach the row, rewrite structural domain/source_domain/target_domain strings, retain opaque payloads verbatim.
- `_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]`: preserve ordering and filter foreign/unscoped rows, then apply _row.
- `_optional_row`: same membership policy for optional singular records, returning None if absent/foreign.
- Generic saved platform-state payloads are opaque dictionaries, not graph record envelopes. Their getters/lists use domain-filtered direct delegation and preserve their payload domain keys. Matrices from load_latest_centroids and metric maps from read_entity_enrichment are also not graph rows.

## 3. Class Skeleton (pseudocode)

```python
class GraphStoreNamespace:
    def __init__(self, store: ProtocolV2GraphStore, namespace: str) -> None:
        require a nonblank string namespace without "::"
        require runtime structural ProtocolV2GraphStore membership
        retain only store and immutable namespace prefix; no result cache
        # Do not inherit/expose ProductionReadyStore.production_ready.

    def write_decision(self, domain: str, category: str, action: str, confidence: float, factors: dict[str, Any], metadata: dict[str, Any] | None=None) -> str:
        reject explicit metadata decision_id override; prefix domain and delegate; return opaque ID

    def write_outcome(self, decision_id: str, actual_action: str, is_correct: bool, metadata: dict[str, Any] | None=None, *, domain: str, outcome: str | None=None, verified_at_epoch: float | None=None, quality_signal: float | None=None, override_comment: str | None=None, verified_by: str | None=None, analyst_action: str | None=None, final_action: str | None=None, recommended_action: str | None=None, was_override: bool | None=None) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def get_decision(self, decision_id: str, domain: str, *, include_outcome: bool=False) -> dict[str, Any] | None:
        prefix domain; return None for missing/foreign result, otherwise _row(result)

    def get_decisions(self, domain: str, category: str | None=None, limit: int=400) -> list[dict[str, Any]]:
        prefix domain parameters; return _rows(delegate(...))

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        prefix domain parameters; return _rows(delegate(...))

    def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]:
        prefix domain parameters; return _rows(delegate(...))

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        prefix domain parameters; return _rows(delegate(...))

    def count_verified(self, domain: str) -> int:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def count_verified_decisions(self, domain: str) -> int:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def save_evolution(self, domain: str, variant_id: str, state: dict[str, Any]) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def get_evolution(self, domain: str, variant_id: str) -> dict[str, Any] | None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def list_evolutions(self, domain: str) -> list[dict[str, Any]]:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def delete_evolution(self, domain: str, variant_id: str) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def save_evolution_state(self, domain: str, variant_id: str, state: dict[str, Any]) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def get_evolution_state(self, domain: str, variant_id: str) -> dict[str, Any] | None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def save_posterior(self, domain: str, key: str, state: dict[str, Any]) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def get_posterior(self, domain: str, key: str) -> dict[str, Any] | None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def list_posteriors(self, domain: str) -> list[dict[str, Any]]:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def delete_posterior(self, domain: str, key: str) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def save_promotion(self, domain: str, rule_id: str, state: dict[str, Any]) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def get_promotion(self, domain: str, rule_id: str) -> dict[str, Any] | None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def list_promotions(self, domain: str) -> list[dict[str, Any]]:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def delete_promotion(self, domain: str, rule_id: str) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def save_ledger(self, domain: str, entry_id: str, state: dict[str, Any]) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def get_ledger(self, domain: str, entry_id: str) -> dict[str, Any] | None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def list_ledgers(self, domain: str) -> list[dict[str, Any]]:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def delete_ledger(self, domain: str, entry_id: str) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def save_governance(self, domain: str, key: str, state: dict[str, Any]) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def get_governance(self, domain: str, key: str) -> dict[str, Any] | None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def list_governance(self, domain: str) -> list[dict[str, Any]]:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def delete_governance(self, domain: str, key: str) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def count_correct(self, domain: str) -> int:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def count_decisions(self, domain: str) -> int:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def save_centroids(self, domain: str, category: str, centroids: Any, metadata: dict[str, Any] | None=None, **kwargs: Any) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def load_latest_centroids(self, domain: str) -> Any | None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def get_centroid_checkpoints(self, domain: str, include_v2: bool=False, **kwargs: Any) -> list[dict[str, Any]]:
        prefix domain parameters; return _rows(delegate(...))

    def load_latest_checkpoint_for_regime(self, domain: str, regime_tag: str) -> dict[str, Any] | None:
        prefix domain; return None for missing/foreign result, otherwise _row(result)

    def get_checkpoint_lineage(self, domain: str, checkpoint_id: str) -> dict[str, Any] | None:
        prefix domain; return None for missing/foreign result, otherwise _row(result)

    def get_decision_checkpoints(self, domain: str, decision_id: str) -> list[dict[str, Any]]:
        prefix domain parameters; return _rows(delegate(...))

    def archive_old_decisions(self, domain: str, keep_recent: int=800) -> int:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def count_archived(self, domain: str) -> int:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def close(self) -> None:
        return None; never close borrowed store

    def write_entity_enrichment(self, *, domain: str, entity_type: str, entity_id: str, namespace: str, metrics: dict[str, ProvenancedValue], computed_from: EnrichmentSourceSet, dry_run: bool=False, idempotency_key: str | None=None) -> EntityEnrichmentReceipt:
        prefix domain; delegate; validate receipt domain; dataclasses.replace(domain=_logical_domain(receipt.domain))

    def read_entity_enrichment(self, *, domain: str, entity_type: str, entity_id: str, namespace: str | None=None) -> dict[str, ProvenancedValue]:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def list_entity_enrichments(self, *, domain: str, entity_type: str | None=None, namespace: str | None=None, limit: int=500) -> list[EntityEnrichmentRecord]:
        prefix domain; delegate; filter foreign typed records; replace domain on detached copies

    def generate_decision_id(self, domain: str) -> str:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def write_governed_decision(self, decision_id: str, domain: str, category: str, category_index: int, recommended_action: str, recommended_index: int, confidence: float, probabilities: list[float], factor_vector: list[float], factor_names: list[str], source: str='score', scorer_version: str='', preset_version: str='', factor_schema_version: str='', metadata: dict[str, Any] | None=None) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def write_observation(self, observation_id: str, domain: str, category: str, recommended_action: str, confidence: float, source_route: str, scorer_version: str, factor_schema_version: str, entity_id: str | None=None, factor_vector: list[float] | None=None, factor_names: list[str] | None=None, metadata: dict[str, Any] | None=None) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def append_evidence_receipt(self, receipt_intent_id: str, domain: str, decision_id: str, canonical_payload: dict[str, Any], actor: str, source_route: str, metadata: dict[str, Any] | None=None) -> tuple[int, str]:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def write_conservation_status(self, status_id: str, domain: str, V: int, q: float, alpha: float, theta_min: float, verified_count: int, correct_count: int, status: str, policy_version: str) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def write_fingerprint(self, fingerprint_id: str, domain: str, factor_names: list[str], factor_stats: dict[str, Any], skipped_incompatible: int, window: int, metadata: dict[str, Any] | None=None) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def write_centroid_checkpoint(self, checkpoint_id: str, domain: str, category: str, action: str, centroids: Any, decisions_count: int, verified_count: int, iks: float, shape: list[int], factor_names_hash: str, quality_window_size: int | None=None, quality_verified_count: int | None=None, quality_correct_count: int | None=None, rolling_accuracy: float | None=None, quality_window_end: str | None=None, quality_policy_version: str | None=None, metadata: dict[str, Any] | None=None, decision_id: str | None=None) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def write_evolution_event(self, event_id: str, domain: str, event_type: str, rule_name: str, variant_id: str, source_copilot: str | None=None, source_rule: str | None=None, metric: float | None=None, shadow_batch_size: int | None=None, min_shadow_batches: int | None=None, metadata: dict[str, Any] | None=None, decision_id: str | None=None) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def get_evolution_events(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]:
        prefix domain parameters; return _rows(delegate(...))

    def write_transfer_pattern(self, pattern_id: str, source_domain: str, target_domain: str, pattern_type: str, factor_mapping: dict[str, Any], confidence: float, validation_status: str, conservation_status: str, source_rule: str | None=None, target_rule: str | None=None, source_fingerprint_id: str | None=None, evolution_event_id: str | None=None, metadata: dict[str, Any] | None=None) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def get_transfer_patterns(self, source_domain: str | None=None, target_domain: str | None=None) -> list[dict[str, Any]]:
        require at least one filter; prefix each supplied domain; return _rows(delegate(...))

    def decision_movement(self, domain: str, decision_id: str) -> list[dict[str, Any]]:
        prefix domain parameters; return _rows(delegate(...))

    def contextual_judgment(self, domain: str, entity_group: str, category: str) -> list[dict[str, Any]]:
        prefix domain parameters; return _rows(delegate(...))

    def promotion_basis(self, domain: str, rule_id: str) -> list[dict[str, Any]]:
        prefix domain parameters; return _rows(delegate(...))

    def transfer_witness(self, source_domain: str, target_domain: str, pattern_id: str) -> list[dict[str, Any]]:
        prefix domain parameters; return _rows(delegate(...))

    def list_fingerprints(self, domain: str | None=None) -> list[dict[str, Any]]:
        require domain; return _rows(delegate(_domain(domain)))

    def get_latest_conservation_statuses(self, domains: list[str] | None=None) -> list[dict[str, Any]]:
        validate domains; [] -> []; delegate with every domain prefixed; return _rows(result)

    def get_iks_trajectory(self, domains: list[str] | None=None, start: float | None=None, end: float | None=None) -> list[dict[str, Any]]:
        validate domains; [] -> []; delegate with every domain prefixed; return _rows(result)

    def link_entity(self, decision_id: str, entity_id: str, entity_type: str, domain: str) -> None:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def archive_decisions(self, domain: str, before: float, status_filter: str='pending', confirm_verified: bool=False) -> int:
        prefix domain/source_domain/target_domain parameters as applicable; explicitly delegate all other arguments unchanged

    def domain_scoped_reset(self, domain: str) -> None:
        raise RuntimeError before delegation

```

Signatures are copied from protocol.py, including keyword-only arguments and **kwargs. No runtime method generation, __getattr__, getattr dispatch, Any-typed capability probes, or backend-class checks. Protocol Any annotations remain only where required by payload contracts.

IDs retain the existing globally unique protocol identity contract; this class rewrites domains, not record identities. Generate IDs through the store; do not reuse explicit V2 IDs across arms. Conflicting immutable IDs retain backend errors. The unsafe legacy base write_decision metadata ID override is rejected before writing because InMemoryGraphStore can otherwise overwrite a foreign-domain record. This is not an authentication boundary against code holding the underlying store directly.

Physical colon-containing domains work in InMemoryGraphStore. Production adapter acceptance of this spelling is a separate backend-conformance prerequisite, not permission to alter separators or factory wiring. ProductionReadyStore is deliberately not exposed.

## 4. Test Plan

Use real InMemoryGraphStore fixtures shared by two adapter instances. Approximately 25 test functions; parametrization exercises all state families and blocked combinations. No graph/scorer mocks. Coverage:
1. Empty/blank namespace rejection.
2. Embedded double-colon rejection.
3. Single-colon namespace acceptance and exact physical prefix.
4. Domain validation/prefixing and strict logical-domain stripping.
5. Flat row rewriting and detached payloads.
6. Nested projection rewriting and mixed-namespace rejection.
7. _rows filtering, order preservation and missing-domain rejection.
8. Structural V2 membership, no ProductionReadyStore marker, exact signatures/method inventory.
9. Legacy decision writes and physical-domain readback.
10. Outcome forwarding, verified/correct counts and foreign outcome rejection.
11. Lists/category/limit filters, verified rows and cross-namespace invisibility.
12. Unsafe legacy decision-ID override rejection without foreign-row mutation.
13. Each evolution/posterior/promotion/ledger/governance save/get/list/delete round-trip, same logical keys across namespaces, opaque domain fields preserved.
14. Evolution-state aliases.
15. Centroid matrix writes/loads and checkpoint domain rewrites.
16. Regime/lineage/decision-checkpoint projections.
17. Governed decisions and opaque ID generation.
18. Observation writes and entity linkage scoped to the physical domain.
19. Evidence receipt chains isolated by domain.
20. Conservation status write/list with explicit domains, empty selection, foreign filtering.
21. Fingerprint writes and domain-filtered catalog.
22. Evolution events and kwargs filters.
23. Transfer writes, either/both filters, nested witness and foreign endpoints.
24. Typed entity-enrichment receipt/record domains; enrichment namespace remains unchanged.
25. Domain-bound archival/counts; destructive reset blocked.
26. Every unfiltered discovery operation blocked; [] is an empty selection, not an all-domain query.
27. close is a no-op; underlying and sibling stores remain usable.
28. Unsupported backend rejected before use; all current memory V2 methods are present, so no integration skips are needed.

Verification: mypy on module/export/tests; focused suite; requested full SDK --timeout=120. The baseline was measured with --timeout=300 and Step 6 already documented slow tests exceeding 120s; distinguish existing timeout failures from adapter regressions and record both outcomes if a diagnostic 300s rerun is needed.

## Design Review Findings

Review completed before implementation. AST comparison confirms all 66 unique methods have exact protocol signatures, including keyword-only parameters and defaults; no missing or invented methods.

Resolved findings:
- Generic state dictionaries, centroid matrices and enrichment metric maps are payloads, not domain-bearing record envelopes. They are domain-filtered delegates, not result-row rewrites.
- Fingerprint statistics (`fingerprint`) and transfer factor mappings (`factor_mapping`) are opaque user payloads too. Added them to the recursive helper exclusions to preserve user keys named domain.
- Optional domain discovery must reject None, but accept an explicit empty domain list without delegating; either transfer endpoint filter is sufficient to bound the query, followed by both-endpoint ownership filtering.
- Legacy metadata decision_id overrides can overwrite foreign records; reject this unsupported override. Explicit governed IDs remain globally unique, with conflicts surfaced by the backend.
- Enrichment results are typed dataclasses; replace their domain fields on detached copies rather than treating them as dictionaries.

No unresolved design findings. Production backend acceptance of physical names remains a documented integration prerequisite; this step does not modify or certify the AGE backend.

### Integration refinement

The first real-store transfer test exposed an additional return-shape detail: transfer rows have a catalogue `domain` set from the underlying store, despite the protocol accepting only source_domain/target_domain. Recognizable transfer records (pattern_id plus both endpoints) use both endpoints for membership and rewriting; their catalogue domain is preserved verbatim. This also applies inside transfer_witness projections. Foreign endpoints still reject the whole record. No backend is mutated and no input API is added.

AGE follow-up confirmed: ci-platform/ci_platform/graph/age_graph_store.py:42 defines `_SAFE_DOMAIN_RE = ^[a-zA-Z0-9_-]{1,200}$`; its validator at line 767 rejects namespace colons. Production integration needs an AGE-side domain-validator change and conformance tests before namespace wiring there. This SDK adapter is not production-certified.

### Separator boundary review

Namespaces ending in a single colon are permitted by the requested namespace validation. To avoid ambiguous concatenations (`arm:` + `scoring` versus `arm` + `:scoring`), logical domains beginning with a colon are unsupported and fail closed. Membership applies the same rule to the suffix. This preserves the specified namespace grammar while ensuring adjacent namespace prefixes cannot leak rows. Ordinary domains and the documented s2p:run1:ci namespace are unchanged.

Outcome readback review: `outcome_metadata` and `context` are user payloads, like `metadata`, and are excluded from structural domain traversal. Outcome integration coverage preserves their literal business-domain values.
