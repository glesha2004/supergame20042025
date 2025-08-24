"""Entity definitions for SpaceGrid Arena.

Currently only contains placeholders for future implementation.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Ship:
    """Base ship entity shared by players and bots."""

    hp: int = 100
    shield: int = 100
    x: float = 0.0
    y: float = 0.0
