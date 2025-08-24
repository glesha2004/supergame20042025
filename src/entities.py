"""Game entities used by SpaceGrid Arena."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

Vec2 = Tuple[float, float]


@dataclass
class Ship:
    position: Vec2
    velocity: Vec2 = (0.0, 0.0)
    hp: float = 100.0
    shield: float = 100.0
    team: int = 0


@dataclass
class Projectile:
    position: Vec2
    velocity: Vec2
    damage: float
    life: float
