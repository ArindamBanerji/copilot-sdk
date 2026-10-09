"""Retired secondary-write queue module, retained for import compatibility.

Canonical outcome writes use the graph store directly. The supported scoring
resilience buffer lives in ``copilot_sdk.scoring.persistence_outbox``; this
module provides no separate persistence or replay implementation.
"""
