from __future__ import annotations

from copilot_sdk.transfer import SharedPatternRegistry, TransferPattern


def _pattern(
    pattern_id: str = "p1",
    source_copilot: str = "dataops",
    category: str = "source_category",
    action: str = "auto_approve",
    confidence: float = 0.8,
    win_rate: float = 0.7,
) -> TransferPattern:
    return TransferPattern(
        pattern_id=pattern_id,
        source_copilot=source_copilot,
        pattern_type="centroid_delta",
        category=category,
        action=action,
        win_rate=win_rate,
        centroid_delta=[0.1, 0.2],
        confidence=confidence,
    )


def test_register_and_count() -> None:
    registry = SharedPatternRegistry()

    registry.register(_pattern())

    assert registry.count == 1


def test_register_assigns_auto_id() -> None:
    registry = SharedPatternRegistry()

    stored = registry.register(_pattern(pattern_id=""))

    assert stored.pattern_id.startswith("XC-DATAOPS-")
    assert registry.count == 1


def test_filter_by_source_confidence_and_win_rate() -> None:
    registry = SharedPatternRegistry()
    registry.register(_pattern("p1", source_copilot="dataops", confidence=0.9, win_rate=0.8))
    registry.register(_pattern("p2", source_copilot="trading", confidence=0.9, win_rate=0.8))
    registry.register(_pattern("p3", source_copilot="dataops", confidence=0.4, win_rate=0.8))
    registry.register(_pattern("p4", source_copilot="dataops", confidence=0.9, win_rate=0.5))

    patterns = registry.get_patterns(source_copilot="dataops")

    assert [pattern.pattern_id for pattern in patterns] == ["p1"]


def test_patterns_are_sorted_by_confidence() -> None:
    registry = SharedPatternRegistry()
    registry.register(_pattern("low", confidence=0.6))
    registry.register(_pattern("high", confidence=0.95))

    patterns = registry.get_patterns()

    assert [pattern.pattern_id for pattern in patterns] == ["high", "low"]


def test_warm_start_excludes_same_source() -> None:
    registry = SharedPatternRegistry()
    registry.register(_pattern("same", source_copilot="s2p"))
    registry.register(_pattern("other", source_copilot="dataops"))

    patterns = registry.get_patterns_for_warm_start("s2p")

    assert [pattern.pattern_id for pattern in patterns] == ["other"]


def test_category_mapping_returns_discounted_copy_without_mutating_original() -> None:
    registry = SharedPatternRegistry()
    original = registry.register(_pattern(category="freshness_violation", confidence=0.8))

    patterns = registry.get_patterns_for_warm_start(
        "s2p",
        category_mapping={"freshness_violation": "price_variance"},
    )

    assert patterns[0].category == "price_variance"
    assert patterns[0].confidence == 0.6400000000000001
    assert original.category == "freshness_violation"
    assert registry.get_patterns()[0].category == "freshness_violation"


def test_json_persistence_round_trip(tmp_path) -> None:
    path = tmp_path / "patterns.json"
    registry = SharedPatternRegistry(path)
    registry.register(_pattern())

    loaded = SharedPatternRegistry(path)

    assert loaded.count == 1
    assert loaded.get_patterns()[0].pattern_id == "p1"


def test_invalid_json_does_not_crash(tmp_path) -> None:
    path = tmp_path / "patterns.json"
    path.write_text("{not json", encoding="utf-8")

    registry = SharedPatternRegistry(path)

    assert registry.count == 0
