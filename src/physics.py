"""Physics helpers."""

from __future__ import annotations

from typing import Tuple

Vec2 = Tuple[float, float]


def apply_velocity(position: Vec2, velocity: Vec2, dt: float) -> Vec2:
    """Return new position after applying *velocity* for time *dt*."""
    return position[0] + velocity[0] * dt, position[1] + velocity[1] * dt
