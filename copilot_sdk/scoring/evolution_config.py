"""Configuration bounds for scorer parameter evolution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvolutionBounds:
    """Hard bounds for evolvable scoring parameters."""

    eta_confirm: tuple[float, float] = (0.01, 0.10)
    eta_override: tuple[float, float] = (0.005, 0.05)
    penalty_ratio_range: tuple[float, float] = (3.0, 40.0)
    temperature: tuple[float, float] = (0.05, 0.20)


BOUNDS_BY_DOMAIN: dict[str, EvolutionBounds] = {
    "trading": EvolutionBounds(),
    "purchasing": EvolutionBounds(penalty_ratio_range=(5.0, 40.0)),
    "dataops": EvolutionBounds(penalty_ratio_range=(4.0, 40.0)),
    "s2p": EvolutionBounds(penalty_ratio_range=(5.0, 40.0)),
}


def bounds_for_domain(domain_preset: str) -> EvolutionBounds:
    """Return hard scorer evolution bounds for a domain preset."""

    return BOUNDS_BY_DOMAIN.get(str(domain_preset).lower(), EvolutionBounds())
