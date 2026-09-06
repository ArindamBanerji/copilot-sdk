"""Mtime-based JSON cache for purchasing fixture files.

The cache avoids reparsing unchanged fixture files for every HTTP request.
Entries are automatically refreshed when a fixture's modification time
changes, including after a preseed or fixture write.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any


_cache: dict[str, Any] = {}
_mtimes: dict[str, tuple[int, int, int]] = {}
_lock = RLock()


def load_cached_json(path: Path) -> Any:
    """Load JSON from *path*, reusing it while its mtime is unchanged."""
    key = str(path.resolve())
    with _lock:
        stat = path.stat()
        version = (stat.st_mtime_ns, stat.st_size, stat.st_ino)
        if key not in _cache or _mtimes.get(key) != version:
            # A changing file must never be labelled with a newer version than
            # the bytes we read. Writers should publish with atomic replace.
            payload = json.loads(path.read_text(encoding="utf-8"))
            after = path.stat()
            if version == (after.st_mtime_ns, after.st_size, after.st_ino):
                _cache[key] = payload
                _mtimes[key] = version
            else:
                return payload
        # Callers enrich fixture dictionaries; never expose the cached object.
        return deepcopy(_cache[key])
