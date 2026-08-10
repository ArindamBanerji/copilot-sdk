# S2P STEP 0 — Centroid Persistence Scan v1
**Date:** 2026-08-05

**Type:** Read-only code scan. No source, test, graph, or database was modified.

## Executive finding

The existing GraphStore.save_centroids(domain, category, centroids, ...) API supports wholesale replacement of the complete centroid tensor. AGEGraphStore stores one CentroidCheckpoint node containing the complete JSON tensor, domain, category, metadata, and timestamp.

The critical compatibility detail is in AGEGraphStore.load_latest_centroids(): it selects only rows where c.checkpoint_id IS NULL. The newer protocol-V2 write_centroid_checkpoint(...) always writes a non-null checkpoint_id. Therefore V2 rows are not visible to the startup loader used by CompoundingScorer.from_preset(). Calling only the V2 writer would silently leave startup on the bootstrap tensor.

The startup-compatible Commit 3 operation is:

    graph_store.save_centroids(
        domain="s2p",
        category="g2_reseed",
        centroids=np.asarray(new_centroids, dtype=np.float64),
        metadata={
            "checkpoint_id": checkpoint_id,
            "source": "s2p_g2_domain_labeled_reseed",
            "calibration_rung": "G2",
            "shape": [5, 5, 8],
            "categories": list(preset.shape.category_names),
            "actions": list(preset.shape.action_names),
            "factors": list(preset.shape.factor_names),
            "factor_names_hash": factor_names_hash,
        },
    )

This writes the entire (5,5,8) tensor and makes it visible to the next startup through load_latest_centroids("s2p"). A small additional Commit 3 change is required for identity logging and factor-order validation; persistence itself needs no new store method.

## 1. Save Methods Found

### 1.1 GraphStore protocol

File: copilot-sdk/copilot_sdk/graph/protocol.py:83-102,267-281

    def save_centroids(
        self,
        domain: str,
        category: str,
        centroids: Any,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        ...

    def load_latest_centroids(self, domain: str) -> Any | None:
        ...

    def get_centroid_checkpoints(
        self,
        domain: str,
        include_v2: bool = False,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        ...

    def write_centroid_checkpoint(
        self,
        checkpoint_id: str,
        domain: str,
        category: str,
        action: str,
        centroids: Any,
        decisions_count: int,
        verified_count: int,
        iks: float,
        shape: list[int],
        factor_names_hash: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...

save_centroids accepts an arbitrary tensor and supports wholesale replacement. write_centroid_checkpoint also accepts an arbitrary tensor, but has a different checkpoint namespace.

### 1.2 AGE SDK adapter

File: ci-platform/ci_platform/graph/age_sdk_adapter.py:219-245,427-458

Complete adapter methods:

    def write_centroid_checkpoint(
        self, checkpoint_id: str, domain: str, category: str, action: str,
        centroids: Any, decisions_count: int, verified_count: int,
        iks: float, shape: list[int], factor_names_hash: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._store.write_centroid_checkpoint(
            checkpoint_id=checkpoint_id, domain=domain, category=category,
            action=action, centroids=centroids,
            decisions_count=decisions_count, verified_count=verified_count,
            iks=iks, shape=shape, factor_names_hash=factor_names_hash,
            metadata=metadata,
        )

    def save_centroids(
        self, domain: str, category: str, centroids: Any,
        metadata: dict[str, Any] | None = None, **kwargs: Any,
    ) -> None:
        self._store.save_centroids(
            domain=domain, category=category, centroids=centroids,
            metadata=metadata, **kwargs,
        )

    def load_latest_centroids(self, domain: str) -> Any | None:
        return self._store.load_latest_centroids(domain)

    def get_centroid_checkpoints(
        self, domain: str, include_v2: bool = False, **kwargs: Any,
    ) -> list[dict[str, Any]]:
        if include_v2:
            return self._store.get_centroid_checkpoints(
                domain, include_v2=True, **kwargs,
            )
        return self._store.get_centroid_checkpoints(domain, **kwargs)

The adapter has no file persistence and performs no tensor transformation. Both operations are domain-scoped.

### 1.3 AGE legacy wholesale writer

File: ci-platform/ci_platform/graph/age_graph_store.py:2620-2659

Complete method:

    def save_centroids(
        self,
        domain: str,
        category: str,
        centroids: Any,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        decision_id = str(
            kwargs.get("decision_id") or (metadata or {}).get("decision_id") or ""
        )
        if hasattr(centroids, "tolist"):
            centroids = centroids.tolist()
        centroids_json = json.dumps(centroids, sort_keys=True)
        metadata_json = json.dumps(metadata or {}, sort_keys=True)
        created_at = datetime.now(timezone.utc).isoformat()
        props = (
            "{"
            f"decision_id: {self._S(decision_id)}, "
            f"domain: {self._S(domain)}, "
            f"category: {self._S(category)}, "
            f"centroids: {self._S(centroids_json)}, "
            f"metadata: {self._S(metadata_json)}, "
            f"created_at: {self._S(created_at)}"
            "}"
        )
        if decision_id:
            query = f"""
            MATCH (d:Decision {{decision_id: {self._S(decision_id)}}})
            WHERE d.domain = {self._S(domain)}
            WITH d LIMIT 1
            CREATE (c:CentroidCheckpoint {props})
            CREATE (d)-[:HAS_CENTROID_CHECKPOINT]->(c)
            RETURN c
            """
            rows = self._run_query(query)
            if rows:
                return
        else:
            self._run_query(f"CREATE (c:CentroidCheckpoint {props}) RETURN c")
            return
        self._run_query(f"CREATE (c:CentroidCheckpoint {props}) RETURN c")

It writes one CentroidCheckpoint vertex, with the complete tensor JSON in centroids, domain, category, metadata, and ISO created_at. It does not set checkpoint_id. If a supplied decision_id identifies a same-domain Decision, it also creates HAS_CENTROID_CHECKPOINT; otherwise the node is still created. This is wholesale, not incremental.

### 1.4 AGE protocol-V2 writer

File: ci-platform/ci_platform/graph/age_graph_store.py:1356-1426

Complete signature:

    def write_centroid_checkpoint(
        self,
        checkpoint_id: str,
        domain: str,
        category: str,
        action: str,
        centroids: Any,
        decisions_count: int,
        verified_count: int,
        iks: float,
        shape: List[int],
        factor_names_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
        decision_id: Optional[str] = None,
    ) -> None:

The complete body converts NumPy values with tolist(), builds a payload containing checkpoint_id, domain, category, action, centroids_json, counts, IKS, shape_json, factor_names_hash, and metadata_json, checks an existing checkpoint ID for idempotency/conflict, and creates a CentroidCheckpoint with schema_version='protocol_v2' and a non-null checkpoint_id. It optionally links a same-domain Decision. It supports wholesale tensor replacement, but is excluded by the current startup loader.

### 1.5 SDK checkpoint coordinator

File: copilot-sdk/copilot_sdk/scoring/scorer.py:1767-1855

Complete signature:

    def _save_centroids_checkpoint(
        self,
        *,
        decision_id: str,
        category: str,
        action: str,
        iks: float,
        boundary: str | None = None,
        decisions_in_batch: int | None = None,
        consolidation: bool = False,
        decision_time_start: str | None = None,
        decision_time_end: str | None = None,
        write_legacy: bool = False,
        checkpoint_id: str | None = None,
        capture_reason: str | None = None,
    ) -> bool:

When write_legacy=True it calls save_centroids(self._domain, category, self._scorer.centroids, ...). The normal AGE path computes the factor-name hash and calls write_centroid_checkpoint(...) with the current complete tensor. The tensor is complete, but normal learning reaches this method after incremental ProfileScorer.update(...). There is no batch corpus-to-centroid rebuild operation. write_legacy defaults to False, so normal production writes V2 only.

### 1.6 Graph Attention Engine in-memory setter

File: graph-attention-engine-v50/gae/profile_scorer.py:656-681

    @property
    def centroids(self) -> np.ndarray:
        """
        Profile centroid tensor, shape (n_categories, n_actions, n_factors).
        Alias for self.mu — use for read access and diagnostics.
        """
        return self.mu

    @centroids.setter
    def centroids(self, value: np.ndarray) -> None:
        """
        Set centroid tensor. Validates shape matches current mu.
        This is the public write API for centroids.
        """
        value = np.array(value, dtype=np.float64, copy=True)
        if not np.all(np.isfinite(value)):
            raise ValueError("centroids contain NaN or Inf values")
        if value.shape != self.mu.shape:
            raise ValueError(
                f"centroids shape {value.shape} != expected {self.mu.shape}"
            )
        self.mu = value

This is complete in-memory replacement only; it writes no graph or file.

### 1.7 Other store implementations

SQLite: copilot-sdk/copilot_sdk/graph/sqlite_store.py:2591-2637. save_centroids converts the complete array to JSON and inserts one row. load_latest_centroids selects WHERE domain = ? AND checkpoint_id IS NULL ORDER BY id DESC LIMIT 1 and returns the decoded NumPy array.

Memory: copilot-sdk/copilot_sdk/graph/memory_store.py:1346-1378. save_centroids appends a complete deep-copied tensor; load_latest_centroids filters by domain and returns the last tensor.

Both are wholesale legacy implementations, not the production AGE path.

## 2. Load + Precedence

### 2.1 AGE load_latest_centroids exact source

File: ci-platform/ci_platform/graph/age_graph_store.py:2661-2678

    def load_latest_centroids(self, domain: str) -> Any | None:
        rows = self._run_query(
            f"""
            MATCH (c:CentroidCheckpoint)
            WHERE c.domain = {self._S(domain)}
              AND c.checkpoint_id IS NULL
            RETURN c
            ORDER BY c.created_at DESC
            LIMIT 1
            """
        )
        if not rows:
            return None
        checkpoint = self._node_to_dict(rows[0].get("c", rows[0]))
        centroids = checkpoint.get("centroids")
        if centroids is None:
            return None
        return np.asarray(centroids, dtype=np.float64)

It reads the graph only. “Latest” means descending created_at, one row, restricted to the requested domain and legacy rows. It does not inspect category, shape, or factor-name hash.

### 2.2 CompoundingScorer.from_preset precedence

File: copilot-sdk/copilot_sdk/scoring/scorer.py:266-268

    centroids = graph_store.load_latest_centroids(preset.name)
    if centroids is None:
        centroids = np.array(preset.bootstrap_centroids, dtype=np.float64, copy=True)

For S2P, preset.name is "s2p". Thus checkpoint > bootstrap. There is no factor-name, category-name, action-name, shape, checkpoint-ID, or hash validation in this branch. ProfileScorer validates finite values and tensor shape relative to its current tensor, but not semantic factor order.

## 3. Write the Re-Seed

### 3.1 Exact call sequence

This is the minimal startup-compatible sequence. It was not executed in this read-only scan:

    import hashlib
    import json
    import numpy as np
    from uuid import uuid4

    domain = "s2p"
    category = "g2_reseed"
    checkpoint_id = f"S2P-G2-{uuid4().hex}"
    preset = S2PPreset()
    new_centroids = np.asarray(g2_tensor, dtype=np.float64)
    expected_shape = (
        preset.shape.n_categories,
        preset.shape.n_actions,
        preset.shape.n_factors,
    )
    if new_centroids.shape != expected_shape:
        raise ValueError(f"centroid shape {new_centroids.shape} != {expected_shape}")
    if not np.all(np.isfinite(new_centroids)):
        raise ValueError("centroids contain NaN or Inf values")
    if np.any(new_centroids < 0.0) or np.any(new_centroids > 1.0):
        raise ValueError("centroids must be in [0, 1]")

    factor_names = list(preset.shape.factor_names)
    factor_names_hash = hashlib.sha256(
        json.dumps(factor_names, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    graph_store.save_centroids(
        domain=domain,
        category=category,
        centroids=new_centroids,
        metadata={
            "checkpoint_id": checkpoint_id,
            "source": "s2p_g2_domain_labeled_reseed",
            "calibration_rung": "G2",
            "shape": list(expected_shape),
            "categories": list(preset.shape.category_names),
            "actions": list(preset.shape.action_names),
            "factors": factor_names,
            "factor_names_hash": factor_names_hash,
            "provenance": "domain-authored-exemplars",
        },
    )

The AGE writer serializes the NumPy tensor through tolist() and JSON into one CentroidCheckpoint.centroids property containing every coordinate.

### 3.2 Net-new code

No new store method is required for wholesale persistence.

Yes, small net-new deployment guard code is required if Commit 3 must meet the build-plan requirements:

- read latest legacy checkpoint metadata, for example get_centroid_checkpoints("s2p", limit=1);
- log checkpoint ID, timestamp, source, shape, and factor-name hash;
- validate shape (5,5,8) and factor-name hash before accepting the tensor.

The current loader returns only the NumPy tensor and discards metadata.

### 3.3 Post-write verification

    loaded = graph_store.load_latest_centroids("s2p")
    np.testing.assert_allclose(loaded, new_centroids, rtol=0.0, atol=0.0)
    assert loaded.shape == (5, 5, 8)

Then inspect get_centroid_checkpoints("s2p", include_v2=False, limit=1), take the newest returned row, and compare metadata checkpoint_id and factor_names_hash. Instantiate a fresh AGE-backed scorer and compare its active tensor with new_centroids. This proves startup did not fall back to S2PPreset.bootstrap_centroids.

## 4. Identity Guard

Existing logging: NO, not for the startup branch. CompoundingScorer.from_preset loads the tensor but logs no checkpoint ID, timestamp, metadata, or factor-name hash. Generic L5 restore logs only coarse source status for a separate restore path. V2 stores identity fields, but startup excludes V2 and the legacy writer has no first-class checkpoint ID/hash fields.

Proposed mechanism:

    latest = graph_store.get_centroid_checkpoints("s2p", include_v2=False, limit=1)
    if latest:
        row = latest[-1]
        metadata = row.get("metadata") or {}
        log.info(
            "S2P centroid checkpoint loaded: checkpoint_id=%s created_at=%s "
            "shape=%s factor_names_hash=%s source=%s",
            metadata.get("checkpoint_id"),
            row.get("created_at"),
            metadata.get("shape"),
            metadata.get("factor_names_hash"),
            metadata.get("source"),
        )

Reject or loudly warn when the shape, factor-order hash, or manifest is absent.

## 5. Domain Scope

Domain-isolated: YES, assuming the supplied domain is correct.

- save_centroids writes domain into CentroidCheckpoint properties.
- load_latest_centroids filters by the requested domain.
- get_centroid_checkpoints filters by the requested domain.
- from_preset("s2p") passes preset.name, "s2p".

Writing domain="s2p" does not select SOC, Trading, Purchasing, or DataOps rows. The residual risk is caller error passing the wrong domain string. category is not a domain boundary.

## 6. Active Gate

Active implementation: s2p-copilot/backend/app/domains/s2p/auto_approve.py:_should_auto_approve, imported by s2p-copilot/backend/app/routers/s2p.py and called at s2p.py:2005-2010.

Complete active gate source, auto_approve.py:28-88:

    def _should_auto_approve(
        category: str,
        confidence: float,
        conservation_status: str,
        recommended_action: str,
        spot_check_fn: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        threshold = AUTO_APPROVE_THRESHOLDS.get(category)
        if threshold is None:
            return {"auto_approved": False, "reason": "unknown_category",
                    "threshold": None, "spot_check": False, "category": category}
        if confidence < threshold:
            return {"auto_approved": False, "reason": "below_threshold",
                    "threshold": threshold, "spot_check": False, "category": category}
        if conservation_status != "GREEN":
            return {"auto_approved": False, "reason": "conservation_not_green",
                    "threshold": threshold, "spot_check": False, "category": category}
        if recommended_action != AUTO_APPROVE_ACTION:
            return {"auto_approved": False, "reason": "wrong_action",
                    "threshold": threshold, "spot_check": False, "category": category}
        spot_check = bool((spot_check_fn or _default_spot_check)())
        if spot_check:
            return {"auto_approved": False, "reason": "spot_check",
                    "threshold": threshold, "spot_check": True, "category": category}
        return {"auto_approved": True, "reason": "approved",
                "threshold": threshold, "spot_check": False, "category": category}

Thresholds, auto_approve.py:10-16:

    AUTO_APPROVE_THRESHOLDS = {
        "price_variance": 0.90,
        "quantity_mismatch": 0.85,
        "duplicate_risk": 0.92,
        "contract_gap": 0.88,
        "format_compliance": 0.80,
    }

These active thresholds are hardcoded module constants. No environment-variable or configuration-file lookup was found. Changing them requires code edit/redeployment.

The separate s2p-copilot/backend/app/services/s2p_auto_approve_gate.py is P40B shadow-only. Its AutoApproveConfig defaults to disabled, requires shadow mode when enabled, and its router explicitly states that it does not provide execution authority. It is not the active _should_auto_approve used by the main S2P scoring route.

## VERDICT

Persistence mechanism: use GraphStore/AGEGraphStoreAdapter.save_centroids(domain="s2p", category="g2_reseed", centroids=<complete np.ndarray shape (5,5,8)>, metadata=<manifest>). This creates a legacy CentroidCheckpoint with no checkpoint_id property, ordered by created_at, which load_latest_centroids("s2p") will select at next startup.

Protocol-V2 warning: do not rely on write_centroid_checkpoint(...) alone for startup loading. Its non-null checkpoint_id makes it invisible to the current load_latest_centroids() query. Using V2 instead would require changing the loader contract and adding a migration-safe precedence rule.

Net-new code for Commit 3:

1. Persist the G2 tensor through the existing legacy wholesale writer with a manifest containing checkpoint ID, shape, category/action/factor order, and canonical factor-name hash.
2. Add startup identity logging and semantic manifest validation.
3. Add a post-write readback/restart test with zero-tolerance tensor comparison.
4. Keep the write domain explicitly "s2p"; do not touch soc_graph.

READY FOR COMMIT 3: YES, conditionally — the storage API is sufficient for wholesale persistence, but Commit 3 must include the identity/hash guard and restart readback test. Without those guards, a persisted tensor can silently override bootstrap values or drift in factor order.

## Scan cleanup

- Scripts created: none.
- Graph/database writes: none.
- Production or test files modified: none.
