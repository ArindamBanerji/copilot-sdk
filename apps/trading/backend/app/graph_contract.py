"""Trading graph contract."""

from __future__ import annotations

from copilot_sdk.graph.contract import EdgeType, GraphContract, NodeType


TRADING_GRAPH_CONTRACT = GraphContract(
    graph_name="trading_graph",
    expected_nodes=150,
    expected_edges=200,
    node_types=[
        NodeType("Decision", ["decision_id", "category", "recommended_action", "confidence", "created_at"]),
        NodeType("Instrument", ["ticker", "asset_class", "category", "sector"]),
        NodeType("Portfolio", ["portfolio_id", "name", "total_value", "cash_buffer"]),
        NodeType("Position", ["position_id", "ticker", "shares", "entry_price", "timing_quality"]),
        NodeType("TradeSignal", ["signal_id", "thesis_type", "timeframe", "position_sizing", "signal_alignment"]),
        NodeType("RiskFactor", ["factor_id", "name", "value"]),
        NodeType("MarketEvent", ["event_id", "date", "vix_at_entry", "emotional_indicator"]),
    ],
    edge_types=[
        EdgeType("DECIDED_ON", "Decision", "Instrument"),
        EdgeType("HOLDS", "Portfolio", "Position"),
        EdgeType("POSITION_IN", "Position", "Instrument"),
        EdgeType("TRIGGERED_BY", "Decision", "TradeSignal"),
        EdgeType("RISK_EXPOSURE", "Position", "RiskFactor"),
        EdgeType("EVALUATED_WITH", "Decision", "RiskFactor"),
        EdgeType("OCCURRED_DURING", "TradeSignal", "MarketEvent"),
    ],
)
