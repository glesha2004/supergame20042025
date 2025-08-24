"""User interface components for SpaceGrid Arena."""
from __future__ import annotations

import pygame


class HUD:
    """Placeholder HUD renderer."""

    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface

    def draw(self) -> None:
        # TODO: draw health/shield bars etc.
        pass
