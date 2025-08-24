import random
import pygame
from dataclasses import dataclass
from typing import Optional

# Basic team colors used for drawing.
TEAM_COLORS = {
    "blue": (50, 150, 255),
    "red": (255, 70, 70),
    "green": (80, 255, 80),
    "purple": (200, 80, 255),
}


@dataclass
class Ship:
    """Represents a ship controlled by either the player or AI."""
    pos: pygame.Vector2
    team: str
    speed: float
    is_player: bool = False
    radius: float = 16
    alive: bool = True

    def __post_init__(self) -> None:
        self.vel = pygame.Vector2(0, 0)

    def update(self, dt: float, input_state: Optional[dict] = None) -> None:
        if not self.alive:
            return
        if self.is_player and input_state:
            move = pygame.Vector2(0, 0)
            if input_state.get("up"):
                move.y -= 1
            if input_state.get("down"):
                move.y += 1
            if input_state.get("left"):
                move.x -= 1
            if input_state.get("right"):
                move.x += 1
            if move.length_squared() > 0:
                move = move.normalize()
            self.vel = move * self.speed
        self.pos += self.vel * dt

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        if not self.alive:
            return
        color = TEAM_COLORS.get(self.team, (255, 255, 255))
        pygame.draw.circle(surface, color, (self.pos - camera), self.radius)


class BotShip(Ship):
    """Very small AI: heads towards a selected capture point."""

    def __init__(self, pos: pygame.Vector2, team: str, speed: float, capture_points):
        super().__init__(pos, team, speed, is_player=False)
        self.capture_points = capture_points
        self.target = None

    def choose_target(self):
        candidates = [p for p in self.capture_points if p.owner != self.team]
        if not candidates:
            candidates = self.capture_points
        self.target = random.choice(candidates)

    def update(self, dt: float, input_state: Optional[dict] = None) -> None:
        if not self.alive:
            return
        if not self.target or (self.target.owner == self.team and
                               self.target.progress.get(self.team, 0) >= self.target.capture_time):
            self.choose_target()
        direction = self.target.pos - self.pos
        if direction.length_squared() > 0:
            direction = direction.normalize()
        self.vel = direction * self.speed * 0.8
        super().update(dt)
