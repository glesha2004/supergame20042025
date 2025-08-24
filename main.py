"""Entry point for the SpaceGrid Arena prototype.

This file sets up pygame and runs the main game loop. The implementation
is intentionally minimal and serves as a foundation for further
development following the provided technical specification.
"""

from __future__ import annotations

import pygame

from src.game import Game
from src.config import load_config


def main() -> None:
    """Load configuration and run the game stub."""
    config = load_config()
    pygame.init()
    try:
        game = Game(config)
        game.run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
