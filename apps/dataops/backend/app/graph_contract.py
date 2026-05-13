"""DataOps graph contract."""

from __future__ import annotations

from copilot_sdk.graph.contract import EdgeType, GraphContract, NodeType


DATAOPS_GRAPH_CONTRACT = GraphContract(
    graph_name="dataops_graph",
    expected_nodes=160,
    expected_edges=220,
    node_types=[
        NodeType("Decision", ["decision_id", "category", "recommended_action", "confidence", "created_at"]),
        NodeType("Pipeline", ["pipeline_id", "name", "display_name", "owner", "status", "sla_minutes"]),
        NodeType("Dataset", ["dataset_id", "name", "system", "schema_columns"]),
        NodeType("QualityRule", ["rule_id", "name", "category", "severity"]),
        NodeType("Alert", ["alert_id", "event_id", "dataset", "system", "category", "severity", "status"]),
        NodeType("ProcessModel", ["model_id", "name", "variant", "source"]),
        NodeType("Activity", ["activity_id", "name", "avg_duration_hours", "case_count", "status", "bottleneck"]),
        NodeType("Transformation", ["transformation_id", "name", "type", "source", "target", "status"]),
    ],
    edge_types=[
        EdgeType("DECIDED_ON", "Decision", "Alert"),
        EdgeType("PRODUCES", "Transformation", "Dataset"),
        EdgeType("CONSUMES", "Transformation", "Dataset"),
        EdgeType("MONITORS", "QualityRule", "Dataset"),
        EdgeType("DETECTED_IN", "Alert", "Pipeline"),
        EdgeType("CONTAINS", "ProcessModel", "Activity"),
        EdgeType("FOLLOWS", "Activity", "Activity"),
        EdgeType("TRIGGERED_BY", "Alert", "Activity"),
    ],
)
