"""Purchasing VLD binding and read-only campaign topology (Tier 5C).

Links describe actual attempted reads; they are returned in memory, never
persisted by investigation. Historical filtering and richer entity traversals
remain Tier 5D work. Demo prose uses legacy indices: canonical names win here.
"""
from __future__ import annotations

from typing import Any

from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from .evidence_providers import PROVIDER_REGISTRY, POLICY_VERSION, PurchasingEvidenceProvider

_SHAPE = PurchasingPreset().shape


def decision_attachment(decision: dict[str, Any]) -> dict[str, Any]:
    """Resolve an existing decision's entity without parsing IDs or inventing it."""
    metadata = decision.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    fields = {**metadata, **{key: value for key, value in decision.items() if value is not None}}
    decision_id = str(fields.get("decision_id") or fields.get("order_id") or fields.get("id") or "")
    lookup_id = str(fields.get("order_id") or fields.get("entity_id") or decision_id)
    entity_id = next((str(fields[key]) for key in ["order_id","entity_id","sku","supplier_id"] if fields.get(key)), lookup_id)
    if not decision_id or not entity_id:
        raise ValueError("A decision or entity identifier is required")
    return {**{key: fields[key] for key in ["order_id","entity_id","sku","supplier_id"] if fields.get(key)},
            "decision_id": decision_id, "lookup_id": lookup_id, "entity_id": entity_id,
            "entity_type": "order",
            "resolved": any(bool(fields.get(key)) for key in ["order_id","entity_id","sku","supplier_id"])}


INVESTIGATION_CONFIG: dict[str, Any] = {
    "copilot_name": "purchasing",
    "factor_names": list(_SHAPE.factor_names),
    "category_names": list(_SHAPE.category_names),
    "action_names": list(_SHAPE.action_names),
    "provider_registry": PROVIDER_REGISTRY,
    "campaign_topology": {
        "DECIDED_ON": "order decision → factor read",
        "MEMBER_OF": "factor read → investigation episode",
        "CONTINUES": "episode → next episode (same order)",
    },
    "decision_attachment": decision_attachment,
    "policy_version": POLICY_VERSION,
    # Preserve confidence blending when provenance is visible in the SDK source field.
    "gated_sources": {
        prefix + source
        for source in ["vendor_tracker","lead_time_tracker"]
        for prefix in ("", "SYNTHETIC:fixture:", "SYNTHETIC:PLACEHOLDER:Tier5D:")
    },
}


def create_evidence_provider(data_source: Any, decision_id: str, *,
                             fixture_data: dict | None = None) -> PurchasingEvidenceProvider:
    getter = getattr(data_source, "get_decision", None)
    decision = getter(str(decision_id), "purchasing") if callable(getter) else None
    if not isinstance(decision, dict):
        decision = {"decision_id": str(decision_id)}
    else:
        decision = {**decision, "decision_id": str(decision_id)}
    if fixture_data is not None:
        orders = fixture_data.get("orders", {})
        order_id = decision_attachment(decision)["lookup_id"]
        order = orders.get(order_id) if isinstance(orders, dict) else None
        if isinstance(order, dict):
            decision = {**order, **decision}
    attachment = decision_attachment(decision)
    return PurchasingEvidenceProvider(data_source, decision_id, attachment=attachment,
        fixture_data=fixture_data, provider_registry=INVESTIGATION_CONFIG["provider_registry"])


def build_trace_links(attachment: dict[str, Any], episode_id: str, steps: list[dict],
                      *, previous_episode: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Link actual SDK steps, including empty/error attempts, without graph writes."""
    if not episode_id:
        raise ValueError("episode_id is required")
    links = []
    for ordinal, step in enumerate(steps):
        dimension = int(step["dimension"])
        if dimension < 0 or dimension >= len(_SHAPE.factor_names):
            raise ValueError("Trace dimension outside canonical factor schema")
        factor_name = _SHAPE.factor_names[dimension]
        if step.get("factor_name", factor_name) != factor_name:
            raise ValueError("Trace factor name and dimension mismatch")
        read_id = f"{episode_id}:read:{ordinal}"
        links.extend([
            {"edge": "DECIDED_ON", "from": attachment["decision_id"], "to": read_id,
             "entity_id": attachment["entity_id"], "factor_name": factor_name,
             "dimension": dimension, "status": step.get("status")},
            {"edge": "MEMBER_OF", "from": read_id, "to": episode_id},
        ])
    if previous_episode is not None:
        if previous_episode["entity_id"] != attachment["entity_id"]:
            raise ValueError("CONTINUES must stay on the same entity")
        if previous_episode["episode_id"] == episode_id:
            raise ValueError("CONTINUES requires distinct episodes")
        links.append({"edge": "CONTINUES", "from": previous_episode["episode_id"], "to": episode_id})
    return links
