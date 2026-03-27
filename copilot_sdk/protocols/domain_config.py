"""
DomainConfig Protocol — register a new copilot domain.
Implement this protocol to build a copilot on copilot-sdk.
See examples/hello_world/config.py for a minimal implementation.
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class DomainConfig(Protocol):
    categories:    list[str]
    actions:       list[str]
    n_factors:     int
    penalty_ratio: float
    eta_confirm:   float
    eta_override:  float
    d_max:         float
    tau:           float

    def get_initial_centroids(self) -> dict: ...
    def get_sigma_profile(self) -> list[float]: ...
    def get_category_index(self, category: str) -> int: ...
    def get_action_index(self, action: str) -> int: ...
