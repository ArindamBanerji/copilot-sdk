"""Purchasing graph contract."""

from __future__ import annotations

from copilot_sdk.graph.contract import EdgeType, GraphContract, NodeType


PURCHASING_GRAPH_CONTRACT = GraphContract(
    graph_name="purchasing_graph",
    expected_nodes=210,
    expected_edges=300,
    node_types=[
        NodeType("Decision", ["decision_id", "category", "recommended_action", "confidence", "created_at"]),
        NodeType("Item", ["item_id", "name", "display_name", "category", "unit"]),
        NodeType("Vendor", ["vendor_id", "name", "lead_time", "reliability"]),
        NodeType("Order", ["order_id", "item", "quantity_lbs", "date", "action_taken"]),
        NodeType("Category", ["category_id", "name"]),
        NodeType("BudgetCenter", ["budget_center_id", "name", "category"]),
        NodeType("Event", ["event_id", "event_type", "date", "weather_factor"]),
    ],
    edge_types=[
        EdgeType("DECIDED_ON", "Decision", "Order"),
        EdgeType("ORDERED_FROM", "Order", "Vendor"),
        EdgeType("ORDER_FOR", "Order", "Item"),
        EdgeType("IN_CATEGORY", "Item", "Category"),
        EdgeType("BUDGET_FROM", "Order", "BudgetCenter"),
        EdgeType("TRIGGERED_BY", "Order", "Event"),
        EdgeType("SUPPLIED_BY", "Item", "Vendor"),
    ],
)
