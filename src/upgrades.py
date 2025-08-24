"""Upgrade system for ships and weapons."""
from __future__ import annotations

from dataclasses import dataclass


MAX_RANK = 10


@dataclass
class Upgrade:
    """Represents a single upgrade path."""

    name: str
    rank: int = 0

    def cost_for_next(self) -> int:
        """Return the sphere cost for the next rank."""
        return 5 + 2 * self.rank
