"""Audio helpers for SpaceGrid Arena."""
from __future__ import annotations

import pygame


class AudioManager:
    """Simple wrapper around pygame.mixer."""

    def __init__(self) -> None:
        pygame.mixer.init()
        self.sounds: dict[str, pygame.mixer.Sound] = {}

    def load_sound(self, key: str, path: str) -> None:
        self.sounds[key] = pygame.mixer.Sound(path)

    def play(self, key: str) -> None:
        sound = self.sounds.get(key)
        if sound:
            sound.play()
