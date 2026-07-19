"""In-memory materialized tab-state cache."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Coroutine, Literal, cast

from pydantic import BaseModel


ComputeFn = Callable[[], Any | Awaitable[Any]]
ServiceFn = Callable[..., Any]
KeyCategory = Literal["STATIC", "DYNAMIC", "QUASI_STATIC"]
KeyTier = Literal["CRITICAL", "STANDARD", "COLD"]

WARN_BYTES = 1_000_000
REJECT_BYTES = 2_000_000
WARM_UP_BATCH_SIZE = 5
log = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    data: Any = None
    previous_data: Any = None
    error: str | None = None
    status: str = "missing"
    computed_at: float | None = None
    version: int = 0

    def envelope(self) -> dict[str, Any]:
        error = self.error
        if self.status == "missing" and self.data is None and error is None:
            error = "not materialized"
        return {
            "data": self.data,
            "error": error,
            "status": self.status,
        }


@dataclass(frozen=True)
class KeySpec:
    key: str
    url: str
    compute_fn: ComputeFn
    invalidated_by: tuple[str, ...]
    critical: bool
    category: KeyCategory
    schema: type[BaseModel]
    service_fn: ServiceFn
    tier: KeyTier = "STANDARD"
    reads_scorer: bool = False
    default_params: dict[str, str] | None = None
    wave_by_event: dict[str, int] = field(default_factory=dict)

    def wave_for(self, event: str) -> int:
        explicit = self.wave_by_event.get(event)
        if explicit in (1, 2):
            return explicit
        if event == "reset":
            return 2
        if self.tier == "CRITICAL":
            return 1
        if self.wave_by_event:
            return 2
        return 1 if self.critical else 2


class TabStateCache:
    """Per-copilot cache for materialized static tab data."""

    def __init__(
        self,
        copilot: str,
        *,
        warn_bytes: int = WARN_BYTES,
        reject_bytes: int = REJECT_BYTES,
    ) -> None:
        self.copilot = str(copilot)
        self.warn_bytes = int(warn_bytes)
        self.reject_bytes = int(reject_bytes)
        self._registrations: dict[str, KeySpec] = {}
        self._dynamic_keys: set[str] = set()
        self._entries: dict[str, CacheEntry] = {}
        self._warm = False
        self._warm_lock = asyncio.Lock()

    @property
    def registrations(self) -> dict[str, KeySpec]:
        return dict(self._registrations)

    @property
    def dynamic_keys(self) -> set[str]:
        return set(self._dynamic_keys)

    @property
    def is_warm(self) -> bool:
        return self._warm

    def register(
        self,
        key: str,
        compute_fn: ComputeFn,
        *,
        invalidated_by: list[str] | tuple[str, ...] = (),
        critical: bool = False,
        category: KeyCategory = "STATIC",
        wave_by_event: dict[str, int] | None = None,
        schema: type[BaseModel] | None = None,
        service_fn: ServiceFn | None = None,
        url: str | None = None,
        tier: KeyTier = "STANDARD",
        reads_scorer: bool = False,
        default_params: dict[str, Any] | None = None,
    ) -> None:
        normalized = _normalize_key(key)
        normalized_category = category.upper()
        if normalized_category == "DYNAMIC":
            raise ValueError("DYNAMIC keys must be registered with register_dynamic()")
        if normalized_category not in {"STATIC", "QUASI_STATIC"}:
            raise ValueError(f"unsupported tab-state category: {category}")
        if normalized in self._registrations:
            raise ValueError(f"Duplicate key registration: {normalized}")
        if not isinstance(schema, type) or not issubclass(schema, BaseModel):
            raise TypeError(f"KeySpec {normalized} requires a BaseModel schema")
        if service_fn is None:
            raise TypeError(f"KeySpec {normalized} requires a service_fn")
        if not isinstance(url, str) or not url.startswith("/api/"):
            raise TypeError(f"KeySpec {normalized} requires an /api/ url")
        normalized_tier = str(tier).upper()
        if critical and normalized_tier == "STANDARD" and not wave_by_event:
            normalized_tier = "CRITICAL"
        if normalized_tier not in {"CRITICAL", "STANDARD", "COLD"}:
            raise ValueError(f"unsupported tab-state tier: {tier}")
        normalized_default_params = _normalize_params(default_params)
        if normalized_category == "QUASI_STATIC" and not normalized_default_params:
            raise ValueError(f"QUASI_STATIC key {normalized} requires default_params")
        self._registrations[normalized] = KeySpec(
            key=normalized,
            url=url,
            compute_fn=compute_fn,
            invalidated_by=tuple(str(event) for event in invalidated_by),
            critical=bool(critical),
            category=normalized_category,  # type: ignore[arg-type]
            schema=schema,
            service_fn=service_fn,
            tier=normalized_tier,  # type: ignore[arg-type]
            reads_scorer=bool(reads_scorer),
            default_params=normalized_default_params,
            wave_by_event=dict(wave_by_event or {}),
        )
        self._entries.setdefault(self._entry_key(normalized), CacheEntry())

    def register_dynamic(self, key: str) -> None:
        self._dynamic_keys.add(_normalize_key(key))

    def get_keys_for_event(self, event: str) -> list[str]:
        event_name = str(event)
        if event_name == "reset":
            return list(self._registrations)
        return [
            key
            for key, registration in self._registrations.items()
            if registration.tier == "CRITICAL" or event_name in registration.invalidated_by
        ]

    def get_urls_for_event(self, event: str) -> list[str]:
        return [self._registrations[key].url for key in self.get_keys_for_event(event)]

    def get_entry(self, key: str, param_value: str | None = None) -> CacheEntry | None:
        """Read one cache entry without warm-up or computation."""
        normalized = _normalize_key(key)
        if normalized not in self._registrations:
            return None
        return self._entries.get(self._entry_key(normalized, param_value))

    def set_from_endpoint(
        self,
        key: str,
        data: Any,
        param_value: str | None = None,
        expected_base_version: int | None = None,
    ) -> None:
        """Store a handler result after a cache miss."""
        normalized = _normalize_key(key)
        if normalized not in self._registrations:
            return
        if expected_base_version is not None:
            base = self._entries.get(self._entry_key(normalized))
            if base is not None and base.version != expected_base_version:
                return
        entry_key = self._entry_key(normalized, param_value)
        previous = self._entries.get(entry_key, CacheEntry())
        if previous.computed_at is not None:
            return
        self._entries[entry_key] = CacheEntry(
            data=data,
            previous_data=previous.data,
            error=None,
            status="ready",
            computed_at=time.time(),
            version=previous.version + 1,
        )

    async def warm_up(self) -> None:
        async with self._warm_lock:
            if self._warm:
                return
            keys = [
                key
                for key in self._registrations
                if self._entries.setdefault(self._entry_key(key), CacheEntry()).computed_at is None
            ]
            for index in range(0, len(keys), WARM_UP_BATCH_SIZE):
                batch = keys[index : index + WARM_UP_BATCH_SIZE]
                await asyncio.gather(*(self._compute_and_store(key, invalidated=False) for key in batch))
                await asyncio.sleep(0)
            self._warm = True
            self._log_cache_size()

    async def get(self, keys: list[str] | tuple[str, ...] | str) -> dict[str, dict[str, Any]]:
        if isinstance(keys, str):
            requested = [item.strip() for item in keys.split(",")]
        else:
            requested = [str(item).strip() for item in keys]
        deduped = _dedupe([key for key in requested if key])
        if not self._warm:
            await self.warm_up()

        result: dict[str, dict[str, Any]] = {}
        for key in deduped:
            normalized = _normalize_key(key)
            if normalized in self._dynamic_keys:
                result[normalized] = {
                    "data": None,
                    "error": "dynamic_key_not_materialized",
                    "status": "dynamic",
                }
            elif normalized not in self._registrations:
                result[normalized] = {
                    "data": None,
                    "error": "unknown_key",
                    "status": "unknown_key",
                }
            else:
                result[normalized] = self._entries.get(self._entry_key(normalized), CacheEntry()).envelope()
        return result

    async def invalidate(self, event: str) -> dict[str, Any]:
        event_name = str(event)
        wave1 = self._critical_keys_for_event(event_name)
        deleted = self._standard_keys_for_event(event_name)

        versions: dict[str, int] = {}
        for key in wave1:
            self._clear_quasi_static_variants(key)
            entry = self._entries.setdefault(self._entry_key(key), CacheEntry())
            entry.version += 1
            versions[key] = entry.version

        started = time.perf_counter()
        for key in wave1:
            await self._compute_and_store(key, expected_version=versions[key], invalidated=True)
        wave1_ms = (time.perf_counter() - started) * 1000.0
        for key in deleted:
            self._delete_entry(key)
        return {
            "event": event_name,
            "wave1": wave1,
            "wave2": [],
            "deleted": deleted,
            "wave1_ms": wave1_ms,
        }

    def invalidate_sync(self, event: str) -> dict[str, Any]:
        """Invalidate inside a synchronous mutation lock scope."""
        event_name = str(event)
        started = time.perf_counter()
        wave1 = self.recompute_critical(event_name)
        wave1_ms = (time.perf_counter() - started) * 1000.0
        deleted = self.delete_standard(event_name)
        return {
            "event": event_name,
            "wave1": wave1,
            "wave2": [],
            "deleted": deleted,
            "wave1_ms": wave1_ms,
        }

    def recompute_critical(self, event: str) -> list[str]:
        keys = self._critical_keys_for_event(event)
        versions: dict[str, int] = {}
        for key in keys:
            self._clear_quasi_static_variants(key)
            entry = self._entries.setdefault(self._entry_key(key), CacheEntry())
            entry.version += 1
            versions[key] = entry.version
        for key in keys:
            self._compute_and_store_sync(key, expected_version=versions[key], invalidated=True)
        return keys

    def delete_standard(self, event: str) -> list[str]:
        keys = self._standard_keys_for_event(event)
        for key in keys:
            self._delete_entry(key)
        return keys

    def delete_critical(self, event: str) -> list[str]:
        keys = self._critical_keys_for_event(event)
        for key in keys:
            self._delete_entry(key)
        return keys

    async def _compute_and_store(
        self,
        key: str,
        *,
        expected_version: int | None = None,
        invalidated: bool,
    ) -> None:
        registration = self._registrations[key]
        entry = self._entries.setdefault(self._entry_key(key), CacheEntry())
        try:
            raw = await _run_compute(registration.compute_fn)
            data = _validate_payload(registration, raw)
            size = _json_size(data)
            if size > self.reject_bytes:
                raise ValueError(f"cache entry {key} exceeds {self.reject_bytes} bytes")
            if size > self.warn_bytes:
                log.warning(
                    "tab-state key %s.%s is %s bytes",
                    self.copilot,
                    key,
                    size,
                )
        except Exception as exc:
            if expected_version is not None and entry.version != expected_version:
                return
            if invalidated:
                entry.previous_data = entry.data
                entry.data = None
                entry.error = str(exc)
                entry.status = "invalidated_error"
                entry.computed_at = time.time()
            else:
                entry.data = None
                entry.error = str(exc)
                entry.status = "missing"
                entry.computed_at = time.time()
            return

        if expected_version is not None and entry.version != expected_version:
            return
        entry.previous_data = entry.data
        entry.data = data
        entry.error = None
        entry.status = "ready"
        entry.computed_at = time.time()

    def _compute_and_store_sync(
        self,
        key: str,
        *,
        expected_version: int | None = None,
        invalidated: bool,
    ) -> None:
        registration = self._registrations[key]
        entry = self._entries.setdefault(self._entry_key(key), CacheEntry())
        try:
            raw = _run_compute_sync(registration.compute_fn)
            data = _validate_payload(registration, raw)
            size = _json_size(data)
            if size > self.reject_bytes:
                raise ValueError(f"cache entry {key} exceeds {self.reject_bytes} bytes")
            if size > self.warn_bytes:
                log.warning(
                    "tab-state key %s.%s is %s bytes",
                    self.copilot,
                    key,
                    size,
                )
        except Exception as exc:
            if expected_version is not None and entry.version != expected_version:
                return
            if invalidated:
                entry.previous_data = entry.data
                entry.data = None
                entry.error = str(exc)
                entry.status = "invalidated_error"
                entry.computed_at = time.time()
            else:
                entry.data = None
                entry.error = str(exc)
                entry.status = "missing"
                entry.computed_at = time.time()
            return

        if expected_version is not None and entry.version != expected_version:
            return
        entry.previous_data = entry.data
        entry.data = data
        entry.error = None
        entry.status = "ready"
        entry.computed_at = time.time()

    def _log_cache_size(self) -> None:
        total = sum(_json_size(entry.data) for entry in self._entries.values() if entry.data is not None)
        log.info("tab-state cache %s warm size %s bytes", self.copilot, total)

    def _entry_key(self, key: str, param_value: str | None = None) -> str:
        registration = self._registrations.get(key)
        if registration is not None and registration.category == "QUASI_STATIC":
            return _variant_key(key, param_value or _param_value(registration.default_params or {}))
        return key

    def _clear_quasi_static_variants(self, key: str) -> None:
        registration = self._registrations.get(key)
        if registration is None or registration.category != "QUASI_STATIC":
            return
        prefix = f"{key}:"
        for entry_key in list(self._entries):
            if entry_key.startswith(prefix):
                del self._entries[entry_key]

    def _delete_entry(self, key: str) -> None:
        self._clear_quasi_static_variants(key)
        self._entries.pop(self._entry_key(key), None)

    def _critical_keys_for_event(self, event: str) -> list[str]:
        return [
            registration.key
            for registration in (self._registrations[key] for key in self.get_keys_for_event(event))
            if registration.tier == "CRITICAL"
        ]

    def _standard_keys_for_event(self, event: str) -> list[str]:
        return [
            registration.key
            for registration in (self._registrations[key] for key in self.get_keys_for_event(event))
            if registration.tier != "CRITICAL"
        ]


def _normalize_key(key: str) -> str:
    return str(key).strip()


def _normalize_params(params: dict[str, Any] | None) -> dict[str, str] | None:
    if params is None:
        return None
    return {str(key): str(value) for key, value in sorted(params.items())}


def _param_value(params: dict[str, str]) -> str:
    return "&".join(f"{key}={value}" for key, value in sorted(params.items()))


def _variant_key(key: str, param_value: str) -> str:
    return f"{key}:{param_value}"


def _dedupe(keys: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        result.append(key)
    return result


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


async def _run_compute(compute_fn: ComputeFn) -> Any:
    if inspect.iscoroutinefunction(compute_fn):
        return await compute_fn()
    value = compute_fn()
    return await _maybe_await(value)


def _run_compute_sync(compute_fn: ComputeFn) -> Any:
    value = compute_fn()
    if inspect.isawaitable(value):
        return asyncio.run(cast(Coroutine[Any, Any, Any], value))
    return value


def _json_size(value: Any) -> int:
    try:
        payload = json.dumps(value, default=str, separators=(",", ":"))
    except TypeError:
        payload = json.dumps(str(value), separators=(",", ":"))
    return len(payload.encode("utf-8"))


def _validate_payload(registration: KeySpec, value: Any) -> Any:
    if isinstance(value, BaseModel):
        model = value
    else:
        model = registration.schema.model_validate(value)
    return model.model_dump(mode="json")


KeyRegistration = KeySpec
