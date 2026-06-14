"""Minimal provenance wrapper for evidence rendering surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Provenanced(Generic[T]):
    """A value tagged with a display-safe provenance source."""

    value: T
    source: str
    label: str | None = None
