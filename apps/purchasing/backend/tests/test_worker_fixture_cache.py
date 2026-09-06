from __future__ import annotations

import os
from pathlib import Path

from app.data_cache import load_cached_json
from app.data_helpers import write_purchasing_fixture


def test_fixture_return_values_do_not_mutate_another_request(tmp_path: Path) -> None:
    path = tmp_path / "fixture.json"
    write_purchasing_fixture(path, {"item": {"provenance": "sample", "count": 1}})
    first = load_cached_json(path)
    first["item"]["count"] = 99
    assert load_cached_json(path)["item"]["count"] == 1


def test_atomic_replacement_invalidates_even_with_preserved_mtime(tmp_path: Path) -> None:
    path = tmp_path / "fixture.json"
    write_purchasing_fixture(path, {"item": {"provenance": "sample", "count": 1}})
    assert load_cached_json(path)["item"]["count"] == 1
    before = path.stat()
    write_purchasing_fixture(path, {"item": {"provenance": "sample", "count": 2}})
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert load_cached_json(path)["item"]["count"] == 2
