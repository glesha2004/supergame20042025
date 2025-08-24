"""Upgrade branches and progression logic."""

from __future__ import annotations

from dataclasses import dataclass

MAX_RANK = 10


@dataclass
class UpgradeBranch:
    name: str
    rank: int = 0

    def upgrade(self) -> None:
        """Increase the rank of this upgrade by one up to ``MAX_RANK``."""
        if self.rank < MAX_RANK:
            self.rank += 1
