"""Core game loop and high level orchestration."""

from __future__ import annotations

import pygame
from typing import Dict, Any

from .capture import CapturePoint


class Game:
    """Simple pygame loop as a placeholder for the real game."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("SpaceGrid Arena")
        self.clock = pygame.time.Clock()
        self.running = True

        size = config.get("arena_size", 3200)
        cp_radius = 120
        self.capture_points = [
            CapturePoint((size * 0.25, size * 0.25), cp_radius),
            CapturePoint((size * 0.75, size * 0.25), cp_radius),
            CapturePoint((size * 0.25, size * 0.75), cp_radius),
            CapturePoint((size * 0.75, size * 0.75), cp_radius),
        ]

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self, dt: float) -> None:
        # Placeholder for updating game state.
        pass

    def render(self) -> None:
        self.screen.fill((0, 0, 0))
        for cp in self.capture_points:
            color = (255, 255, 255)
            pygame.draw.circle(self.screen, color, (int(cp.position[0] % 1280), int(cp.position[1] % 720)), int(cp.radius), 1)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()
