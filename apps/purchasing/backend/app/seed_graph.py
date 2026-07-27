"""Deterministic Purchasing graph seed plan."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CATEGORIES = ("protein", "produce", "dairy", "dry_goods", "beverages")


def _load_json(filename: str, default: Any) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _slug(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    return "_".join("".join(ch if ch.isalnum() else "_" for ch in text).split("_")) or "unknown"


def _node_id(label: str, natural_key: Any) -> str:
    return f"{label}:{_slug(natural_key)}"


def _add_node(
    nodes: list[dict[str, Any]],
    seen: dict[str, dict[str, Any]],
    label: str,
    natural_key: Any,
    properties: dict[str, Any],
) -> str:
    node_id = _node_id(label, natural_key)
    if node_id not in seen:
        node = {"id": node_id, "label": label, "properties": dict(properties)}
        nodes.append(node)
        seen[node_id] = node
    return node_id


def _add_edge(
    edges: list[dict[str, Any]],
    seen: set[tuple[str, str, str]],
    label: str,
    from_id: str,
    to_id: str,
    properties: dict[str, Any] | None = None,
) -> None:
    token = (label, from_id, to_id)
    if token in seen:
        return
    seen.add(token)
    edges.append(
        {
            "id": f"{label}:{len(edges) + 1}",
            "label": label,
            "from_id": from_id,
            "to_id": to_id,
            "properties": properties or {},
        }
    )


def seed_purchasing_graph(seed: int = 42) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    orders = _load_json("purchasing_seed_v2.json", [])
    if not isinstance(orders, list):
        orders = []
    weather = _load_json("weather_cache.json", {})
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes: dict[str, dict[str, Any]] = {}
    seen_edges: set[tuple[str, str, str]] = set()

    category_ids = {
        category: _add_node(
            nodes,
            seen_nodes,
            "Category",
            category,
            {"category_id": category, "name": category},
        )
        for category in CATEGORIES
    }
    budget_ids = {
        category: _add_node(
            nodes,
            seen_nodes,
            "BudgetCenter",
            category,
            {
                "budget_center_id": f"budget-{category}",
                "name": f"{category}_budget",
                "category": category,
            },
        )
        for category in CATEGORIES
    }

    for index, order in enumerate(orders):
        if not isinstance(order, dict):
            continue
        order_id_value = str(order.get("order_id") or f"order-{index}")
        item_key = str(order.get("item") or order_id_value)
        category = str(order.get("category") or "unknown")
        vendor_key = f"{category}-{item_key}"
        event_key = str(order.get("event_type") or order.get("date") or "standard_day")

        item_id = _add_node(
            nodes,
            seen_nodes,
            "Item",
            item_key,
            {
                "item_id": item_key,
                "name": item_key,
                "display_name": order.get("display_name"),
                "category": category,
                "unit": "lb",
            },
        )
        vendor_id = _add_node(
            nodes,
            seen_nodes,
            "Vendor",
            vendor_key,
            {
                "vendor_id": f"vendor-{_slug(vendor_key)}",
                "name": f"{category}_vendor",
                "lead_time": order.get("supplier_lead_time"),
                "reliability": round(0.7 + rng.random() * 0.25, 4),
            },
        )
        order_id = _add_node(
            nodes,
            seen_nodes,
            "Order",
            order_id_value,
            {
                "order_id": order_id_value,
                "item": item_key,
                "quantity_lbs": order.get("quantity_lbs"),
                "date": order.get("date"),
                "action_taken": order.get("action_taken"),
            },
        )
        event_id = _add_node(
            nodes,
            seen_nodes,
            "Event",
            event_key,
            {
                "event_id": event_key,
                "event_type": order.get("event_type") or "standard_day",
                "date": order.get("date"),
                "weather_factor": weather.get("weather_factor"),
            },
        )
        decision_id = _add_node(
            nodes,
            seen_nodes,
            "Decision",
            order_id_value,
            {
                "decision_id": f"decision-{order_id_value}",
                "domain": "purchasing",
                "category": category,
                "recommended_action": order.get("action_taken"),
                "confidence": round(0.55 + rng.random() * 0.4, 4),
                "created_at": order.get("date"),
            },
        )

        category_id = category_ids.get(category) or _add_node(
            nodes,
            seen_nodes,
            "Category",
            category,
            {"category_id": category, "name": category},
        )
        budget_id = budget_ids.get(category) or _add_node(
            nodes,
            seen_nodes,
            "BudgetCenter",
            category,
            {"budget_center_id": f"budget-{category}", "name": f"{category}_budget", "category": category},
        )

        _add_edge(edges, seen_edges, "DECIDED_ON", decision_id, order_id)
        _add_edge(edges, seen_edges, "ORDERED_FROM", order_id, vendor_id)
        _add_edge(edges, seen_edges, "ORDER_FOR", order_id, item_id)
        _add_edge(edges, seen_edges, "IN_CATEGORY", item_id, category_id)
        _add_edge(edges, seen_edges, "BUDGET_FROM", order_id, budget_id)
        _add_edge(edges, seen_edges, "TRIGGERED_BY", order_id, event_id)
        _add_edge(edges, seen_edges, "SUPPLIED_BY", item_id, vendor_id)

    return nodes, edges
