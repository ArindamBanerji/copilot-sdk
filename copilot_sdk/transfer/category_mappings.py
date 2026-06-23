"""Cross-copilot category mapping presets for transfer demos."""

from __future__ import annotations

from typing import Final


CROSS_COPILOT_MAPPINGS: Final[dict[tuple[str, str], dict[str, str]]] = {
    ("soc", "dataops"): {
        "credential_access": "volume_anomaly",
        "lateral_movement": "transform_drift",
        "data_exfiltration": "volume_anomaly",
        "malware_execution": "pipeline_failure",
        "insider_threat": "quality_anomaly",
        "cloud_infrastructure": "freshness_violation",
    },
    ("dataops", "purchasing"): {
        "schema_change": "dry_goods",
        "volume_anomaly": "beverages",
        "quality_anomaly": "produce",
        "freshness_violation": "produce",
        "pipeline_failure": "protein",
        "transform_drift": "dairy",
    },
    ("dataops", "trading"): {
        "schema_change": "event_driven",
        "pipeline_failure": "scalp_intraday",
        "quality_anomaly": "mean_reversion",
        "volume_anomaly": "event_driven",
        "freshness_violation": "trend_following",
        "transform_drift": "income_strategy",
    },
    ("purchasing", "dataops"): {
        "protein": "pipeline_failure",
        "produce": "quality_anomaly",
        "dairy": "transform_drift",
        "dry_goods": "schema_change",
        "beverages": "volume_anomaly",
    },
}


def _clean_domain(value: str) -> str:
    return str(value or "").strip().lower()


def get_mapping(source_domain: str, target_domain: str) -> dict[str, str] | None:
    """Return the preset mapping for a directed source-target pair."""

    mapping = CROSS_COPILOT_MAPPINGS.get((_clean_domain(source_domain), _clean_domain(target_domain)))
    return dict(mapping) if mapping is not None else None


def list_available_transfers() -> list[dict[str, int | str]]:
    """Return summary rows for all defined directed transfer mappings."""

    return [
        {"source": source, "target": target, "categories": len(mapping)}
        for (source, target), mapping in sorted(CROSS_COPILOT_MAPPINGS.items())
    ]
