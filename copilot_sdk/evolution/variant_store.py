"""Prompt variant registries and durable outcome statistics."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Any, Protocol


VARIANT_STATUSES = frozenset({"active", "shadow", "promoted", "retired"})


@dataclass
class VariantSpec:
    id: str
    family: str
    version: int = 1
    template: str = ""
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("VariantSpec.id must be a non-empty string")
        if not isinstance(self.family, str) or not self.family.strip():
            raise ValueError("VariantSpec.family must be a non-empty string")
        if not isinstance(self.version, int) or self.version <= 0:
            raise ValueError("VariantSpec.version must be a positive int")
        if self.status not in VARIANT_STATUSES:
            raise ValueError(f"Unsupported variant status: {self.status}")
        self.metadata = dict(self.metadata or {})


@dataclass
class VariantStats:
    successes: int = 0
    total: int = 0
    failures: int = 0

    @property
    def success_rate(self) -> float:
        return self.successes / self.total if self.total > 0 else 0.0


@dataclass
class CategoryVariantStats:
    category: str
    variant_id: str
    successes: int = 0
    total: int = 0
    failures: int = 0

    @property
    def success_rate(self) -> float:
        return self.successes / self.total if self.total > 0 else 0.0


class VariantStore(Protocol):
    """Storage contract shared by memory and durable variant stores."""

    def register_variant(self, spec: VariantSpec) -> None: ...
    def get_variant(self, variant_id: str) -> VariantSpec | None: ...
    def get_variants_by_family(self, family: str) -> list[VariantSpec]: ...
    def get_all_variants(self) -> list[VariantSpec]: ...
    def get_active_variants(self) -> list[VariantSpec]: ...
    def get_global_stats(self, variant_id: str) -> VariantStats: ...
    def get_category_stats(self, category: str, variant_id: str) -> CategoryVariantStats: ...
    def get_all_category_stats(self, category: str) -> dict[str, CategoryVariantStats]: ...
    def record_outcome(self, variant_id: str, success: bool, category: str | None = None) -> None: ...
    def record_category_outcome(self, category: str, variant_id: str, success: bool) -> None: ...
    def update_variant_status(self, variant_id: str, new_status: str) -> None: ...
    def reset(self) -> None: ...
    def reset_stats_only(self) -> None: ...


class InMemoryVariantStore:
    """Instance-local prompt variant store."""

    def __init__(self) -> None:
        self._variants: dict[str, VariantSpec] = {}
        self._global_stats: dict[str, VariantStats] = {}
        self._category_stats: dict[str, dict[str, CategoryVariantStats]] = {}

    def register_variant(self, spec: VariantSpec) -> None:
        if not isinstance(spec, VariantSpec):
            raise TypeError("spec must be a VariantSpec")
        if spec.id in self._variants:
            raise ValueError(f"Variant already registered: {spec.id}")
        self._variants[spec.id] = _copy_spec(spec)
        self._global_stats[spec.id] = VariantStats()

    def get_variant(self, variant_id: str) -> VariantSpec | None:
        spec = self._variants.get(variant_id)
        return _copy_spec(spec) if spec is not None else None

    def get_variants_by_family(self, family: str) -> list[VariantSpec]:
        return [
            _copy_spec(spec)
            for spec in self._variants.values()
            if spec.family == family
        ]

    def get_all_variants(self) -> list[VariantSpec]:
        return [_copy_spec(spec) for spec in self._variants.values()]

    def get_active_variants(self) -> list[VariantSpec]:
        return [
            _copy_spec(spec)
            for spec in self._variants.values()
            if spec.status == "active"
        ]

    def get_global_stats(self, variant_id: str) -> VariantStats:
        stats = self._global_stats.get(variant_id)
        return _copy_global_stats(stats) if stats is not None else VariantStats()

    def get_category_stats(self, category: str, variant_id: str) -> CategoryVariantStats:
        stats = self._category_stats.get(category, {}).get(variant_id)
        if stats is None:
            return CategoryVariantStats(category=category, variant_id=variant_id)
        return _copy_category_stats(stats)

    def get_all_category_stats(self, category: str) -> dict[str, CategoryVariantStats]:
        return {
            variant_id: _copy_category_stats(stats)
            for variant_id, stats in self._category_stats.get(category, {}).items()
        }

    def record_outcome(
        self,
        variant_id: str,
        success: bool,
        category: str | None = None,
    ) -> None:
        if variant_id not in self._variants:
            raise ValueError(f"Unknown variant: {variant_id}")
        self._apply_global_outcome(variant_id, success)
        if category is not None:
            self._apply_category_outcome(str(category), variant_id, success)

    def record_category_outcome(self, category: str, variant_id: str, success: bool) -> None:
        if variant_id not in self._variants:
            raise ValueError(f"Unknown variant: {variant_id}")
        self._apply_category_outcome(str(category), variant_id, success)

    def update_variant_status(self, variant_id: str, new_status: str) -> None:
        if new_status not in VARIANT_STATUSES:
            raise ValueError(f"Unsupported variant status: {new_status}")
        spec = self._variants.get(variant_id)
        if spec is None:
            raise ValueError(f"Unknown variant: {variant_id}")
        self._variants[variant_id] = replace(spec, status=new_status)

    def reset(self) -> None:
        self._variants.clear()
        self._global_stats.clear()
        self._category_stats.clear()

    def reset_stats_only(self) -> None:
        self._global_stats.clear()
        self._category_stats.clear()
        for variant_id in self._variants:
            self._global_stats[variant_id] = VariantStats()

    def _apply_global_outcome(self, variant_id: str, success: bool) -> None:
        stats = self._global_stats.setdefault(variant_id, VariantStats())
        stats.total += 1
        if success:
            stats.successes += 1
        else:
            stats.failures += 1

    def _apply_category_outcome(self, category: str, variant_id: str, success: bool) -> None:
        category_stats = self._category_stats.setdefault(category, {})
        stats = category_stats.setdefault(
            variant_id,
            CategoryVariantStats(category=category, variant_id=variant_id),
        )
        stats.total += 1
        if success:
            stats.successes += 1
        else:
            stats.failures += 1


class SQLiteVariantStore:
    """SQLite-backed variant registry with restart-safe statistics.

    The store deliberately mirrors :class:`InMemoryVariantStore`.  A single
    connection is protected by an ``RLock`` because outcome recording can be
    called from request and background threads in the same process.  WAL and a
    busy timeout allow separate copilot workers to share a domain database
    without changing the public store contract.
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._lock = RLock()
        self._connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0,
        )
        self._connection.row_factory = sqlite3.Row
        with self._lock:
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA synchronous=NORMAL")
            self._connection.execute("PRAGMA busy_timeout=30000")
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS variants (
                    id TEXT PRIMARY KEY,
                    family TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    template TEXT NOT NULL,
                    status TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS variant_stats (
                    variant_id TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT '',
                    total INTEGER NOT NULL DEFAULT 0,
                    successes INTEGER NOT NULL DEFAULT 0,
                    failures INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (variant_id, category),
                    FOREIGN KEY (variant_id) REFERENCES variants(id) ON DELETE CASCADE
                );
                """
            )
            self._connection.commit()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def register_variant(self, spec: VariantSpec) -> None:
        if not isinstance(spec, VariantSpec):
            raise TypeError("spec must be a VariantSpec")
        now = _utc_now()
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO variants(id, family, version, template, status, config_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    family=excluded.family,
                    version=excluded.version,
                    template=excluded.template,
                    config_json=excluded.config_json
                """,
                (
                    spec.id,
                    spec.family,
                    spec.version,
                    spec.template,
                    spec.status,
                    json.dumps(spec.metadata, sort_keys=True, default=str),
                    now,
                ),
            )
            self._connection.execute(
                """
                INSERT INTO variant_stats(variant_id, category, updated_at)
                VALUES (?, '', ?)
                ON CONFLICT(variant_id, category) DO NOTHING
                """,
                (spec.id, now),
            )
            self._connection.commit()

    def get_variant(self, variant_id: str) -> VariantSpec | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT id, family, version, template, status, config_json FROM variants WHERE id=?",
                (variant_id,),
            ).fetchone()
        return _row_to_spec(row) if row is not None else None

    def get_variants_by_family(self, family: str) -> list[VariantSpec]:
        return self._get_specs("SELECT * FROM variants WHERE family=? ORDER BY rowid", (family,))

    def get_all_variants(self) -> list[VariantSpec]:
        return self._get_specs("SELECT * FROM variants ORDER BY rowid")

    def get_active_variants(self) -> list[VariantSpec]:
        return self._get_specs("SELECT * FROM variants WHERE status='active' ORDER BY rowid")

    def get_global_stats(self, variant_id: str) -> VariantStats:
        with self._lock:
            row = self._connection.execute(
                "SELECT successes, total, failures FROM variant_stats WHERE variant_id=? AND category=''",
                (variant_id,),
            ).fetchone()
        return _row_to_global_stats(row)

    def get_category_stats(self, category: str, variant_id: str) -> CategoryVariantStats:
        with self._lock:
            row = self._connection.execute(
                "SELECT successes, total, failures FROM variant_stats WHERE variant_id=? AND category=?",
                (variant_id, str(category)),
            ).fetchone()
        if row is None:
            return CategoryVariantStats(category=str(category), variant_id=variant_id)
        return CategoryVariantStats(
            category=str(category), variant_id=variant_id,
            successes=int(row["successes"]), total=int(row["total"]), failures=int(row["failures"]),
        )

    def get_all_category_stats(self, category: str) -> dict[str, CategoryVariantStats]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT variant_id, successes, total, failures FROM variant_stats WHERE category=?",
                (str(category),),
            ).fetchall()
        return {
            str(row["variant_id"]): CategoryVariantStats(
                category=str(category), variant_id=str(row["variant_id"]),
                successes=int(row["successes"]), total=int(row["total"]), failures=int(row["failures"]),
            )
            for row in rows
        }

    def record_outcome(self, variant_id: str, success: bool, category: str | None = None) -> None:
        with self._lock:
            exists = self._connection.execute(
                "SELECT 1 FROM variants WHERE id=?", (variant_id,)
            ).fetchone()
            if exists is None:
                raise ValueError(f"Unknown variant: {variant_id}")
            now = _utc_now()
            self._record_row(variant_id, "", success, now)
            if category is not None:
                self._record_row(variant_id, str(category), success, now)
            self._connection.commit()

    def record_category_outcome(self, category: str, variant_id: str, success: bool) -> None:
        with self._lock:
            exists = self._connection.execute(
                "SELECT 1 FROM variants WHERE id=?", (variant_id,)
            ).fetchone()
            if exists is None:
                raise ValueError(f"Unknown variant: {variant_id}")
            self._record_row(variant_id, str(category), success, _utc_now())
            self._connection.commit()

    def update_variant_status(self, variant_id: str, new_status: str) -> None:
        if new_status not in VARIANT_STATUSES:
            raise ValueError(f"Unsupported variant status: {new_status}")
        with self._lock:
            cursor = self._connection.execute(
                "UPDATE variants SET status=? WHERE id=?", (new_status, variant_id)
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Unknown variant: {variant_id}")
            self._connection.commit()

    def reset(self) -> None:
        with self._lock:
            self._connection.execute("DELETE FROM variant_stats")
            self._connection.execute("DELETE FROM variants")
            self._connection.commit()

    def reset_stats_only(self) -> None:
        with self._lock:
            self._connection.execute("DELETE FROM variant_stats")
            now = _utc_now()
            self._connection.executemany(
                "INSERT INTO variant_stats(variant_id, category, updated_at) VALUES (?, '', ?)",
                [(str(row["id"]), now) for row in self._connection.execute("SELECT id FROM variants")],
            )
            self._connection.commit()

    def _get_specs(self, query: str, params: tuple[Any, ...] = ()) -> list[VariantSpec]:
        with self._lock:
            rows = self._connection.execute(query, params).fetchall()
        return [_row_to_spec(row) for row in rows]

    def _record_row(self, variant_id: str, category: str, success: bool, now: str) -> None:
        self._connection.execute(
            """
            INSERT INTO variant_stats(variant_id, category, total, successes, failures, updated_at)
            VALUES (?, ?, 1, ?, ?, ?)
            ON CONFLICT(variant_id, category) DO UPDATE SET
                total=variant_stats.total + 1,
                successes=variant_stats.successes + excluded.successes,
                failures=variant_stats.failures + excluded.failures,
                updated_at=excluded.updated_at
            """,
            (variant_id, category, int(bool(success)), int(not success), now),
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_spec(row: sqlite3.Row) -> VariantSpec:
    try:
        metadata = json.loads(str(row["config_json"]))
    except (TypeError, ValueError, json.JSONDecodeError):
        metadata = {}
    return VariantSpec(
        id=str(row["id"]), family=str(row["family"]), version=int(row["version"]),
        template=str(row["template"]), status=str(row["status"]),
        metadata=metadata if isinstance(metadata, dict) else {},
    )


def _row_to_global_stats(row: sqlite3.Row | None) -> VariantStats:
    if row is None:
        return VariantStats()
    return VariantStats(
        successes=int(row["successes"]), total=int(row["total"]), failures=int(row["failures"])
    )


def _copy_spec(spec: VariantSpec) -> VariantSpec:
    return replace(spec, metadata=deepcopy(spec.metadata))


def _copy_global_stats(stats: VariantStats) -> VariantStats:
    return VariantStats(
        successes=stats.successes,
        total=stats.total,
        failures=stats.failures,
    )


def _copy_category_stats(stats: CategoryVariantStats) -> CategoryVariantStats:
    return CategoryVariantStats(
        category=stats.category,
        variant_id=stats.variant_id,
        successes=stats.successes,
        total=stats.total,
        failures=stats.failures,
    )
