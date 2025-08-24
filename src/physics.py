"""Basic physics helpers for SpaceGrid Arena."""
from __future__ import annotations


def calculate_collision_damage(relative_velocity: float) -> int:
    """Compute collision damage based on relative velocity.

    The damage follows the quadratic rule from the specification::

        damage = clamp(round((v_rel / 250)**2 * 30), 1, 60)

    Parameters
    ----------
    relative_velocity: float
        Magnitude of the relative velocity in pixels per second.
    """
    scaled = (relative_velocity / 250) ** 2 * 30
    damage = round(scaled)
    return max(1, min(damage, 60))
