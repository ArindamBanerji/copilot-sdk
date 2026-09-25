"""Request-scoped demo snapshots, separate from the checked-in sample data."""

from __future__ import annotations

import asyncio
from copy import deepcopy
import hashlib
import json
import logging
from pathlib import Path
import tempfile
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


class ConnectorCache:
    """Try each request once per connector lifetime; retain validated responses.

    Keys include service URL, credential identity, endpoint and query parameters.
    Failed requests are not retried on every UI render. Restart the app to refresh.
    TLS verification belongs to the HTTP client and is never disabled here.
    """

    def __init__(self, directory: Path, identity: str):
        self.directory = directory / "connector_snapshots"
        self.identity = identity
        self._attempted: set[str] = set()
        self._memory: dict[str, Any] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def key(self, endpoint: str, params: dict[str, str] | None) -> str:
        raw = json.dumps([self.identity, endpoint, params or {}], sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def load(self, key: str) -> Any:
        try:
            return json.loads((self.directory / f"{key}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def save(self, key: str, payload: Any) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        # Unique temporary file + replace prevents partially written JSON reads.
        path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.directory,
                                             suffix=".tmp", delete=False) as stream:
                path = Path(stream.name)
                json.dump(payload, stream, allow_nan=False)
            path.replace(self.directory / f"{key}.json")
        finally:
            if path is not None:
                path.unlink(missing_ok=True)

    async def fetch(self, endpoint: str, params: dict[str, str] | None,
                    request: Callable[..., Awaitable[Any]], validate: Callable[[Any], Any]) -> tuple[Any, bool]:
        key = self.key(endpoint, params)
        async with self._locks.setdefault(key, asyncio.Lock()):
            if key not in self._attempted:
                self._attempted.add(key)
                try:
                    payload = await request(endpoint, params=params)
                    validate(payload)
                except Exception as exc:
                    # Do not log URLs, credentials, or response bodies.
                    logger.warning("Enterprise request failed (%s); using cached fallback", type(exc).__name__)
                else:
                    self._memory[key] = deepcopy(payload)
                    try:
                        self.save(key, payload)
                    except (OSError, ValueError):
                        logger.warning("Enterprise snapshot could not be saved; retaining memory cache")
                    return deepcopy(payload), True
            payload = self._memory.get(key)
            if payload is None:
                payload = self.load(key)
            if payload is None:
                raise RuntimeError("No captured response available")
            validate(payload)
            return deepcopy(payload), False
