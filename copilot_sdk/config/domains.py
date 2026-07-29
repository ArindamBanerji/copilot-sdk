"""Canonical copilot identities for test and validation tooling.

Graph queries deliberately discover domains from persisted graph data rather
than filtering against this product-level inventory.
"""

from __future__ import annotations

from typing import Final


ALL_COPILOT_DOMAINS: Final[tuple[str, ...]] = (
    "soc",
    "s2p",
    "trading",
    "purchasing",
    "dataops",
)

COPILOT_PORTS: Final[dict[str, int]] = {
    "soc": 8001,
    "s2p": 8002,
    "trading": 8010,
    "purchasing": 8020,
    "dataops": 8030,
}
