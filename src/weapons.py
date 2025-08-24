"""Weapon system stubs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Weapon:
    name: str
    rate: float
    damage: float
