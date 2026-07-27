"""Stable identity for deterministic SOC/demo seed output."""

import hashlib


SEED_VERSION = "v1"


def compute_seed_hash(decisions: list) -> str:
    """Return a compact hash of the deterministic decision identity set."""
    content = str(sorted(d.get("decision_id", "") for d in decisions))
    return hashlib.sha256(content.encode()).hexdigest()[:16]
