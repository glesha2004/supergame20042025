"""Entry point for SpaceGrid Arena."""
from __future__ import annotations

import os

# Use a dummy video driver when running in headless environments
if os.environ.get("SDL_VIDEODRIVER") is None:
    os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame

from src.game import Game


def main() -> None:
    pygame.init()
    try:
        Game().run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
