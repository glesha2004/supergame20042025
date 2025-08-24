"""Main game loop and state management."""
from __future__ import annotations

import pygame

from .config import load_config


class Game:
    """Top-level game object handling the main loop."""

    def __init__(self) -> None:
        self.config = load_config()
        window_cfg = self.config.get("window", {})
        self.screen = pygame.display.set_mode(
            (window_cfg.get("width", 1280), window_cfg.get("height", 720))
        )
        pygame.display.set_caption("SpaceGrid Arena")
        self.clock = pygame.time.Clock()
        self.running = True

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self, dt: float) -> None:
        """Update game state. Placeholder for now."""
        # TODO: implement game logic
        pass

    def render(self) -> None:
        """Render the current frame."""
        self.screen.fill((0, 0, 0))
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()
