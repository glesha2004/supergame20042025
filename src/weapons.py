"""Weapon systems for SpaceGrid Arena.

The full game will provide several upgradeable weapon types.
This module exposes minimal stubs used by the rest of the codebase.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Weapon:
    name: str
    damage: float
    rate_of_fire: float
