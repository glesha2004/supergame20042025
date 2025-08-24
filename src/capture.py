from __future__ import annotations
import math
import pygame


class CapturePoint:
    """Circular area that can be captured by teams."""

    def __init__(self, pos, radius: float, capture_time: float):
        self.pos = pygame.Vector2(pos)
        self.radius = radius
        self.capture_time = capture_time
        self.owner: str | None = None
        self.progress: dict[str, float] = {}

    def update(self, dt: float, ships) -> None:
        """Update capture progress based on ships present."""
        present: dict[str, int] = {}
        for ship in ships:
            if not ship.alive:
                continue
            if (ship.pos - self.pos).length() <= self.radius:
                present[ship.team] = present.get(ship.team, 0) + 1

        if len(present) == 1:
            team = next(iter(present))
            prog = self.progress.get(team, 0.0) + dt
            self.progress[team] = min(prog, self.capture_time)
            if self.progress[team] >= self.capture_time:
                self.owner = team
                # reset others
                self.progress = {team: self.capture_time}
        # contesting or empty -> no change

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2, color_map) -> None:
        color = (255, 255, 255)
        if self.owner:
            color = color_map.get(self.owner, color)
        pygame.draw.circle(surface, color, (self.pos - camera), self.radius, 3)
        # draw progress arc
        if self.owner:
            prog = self.progress.get(self.owner, 0)
            angle = (prog / self.capture_time) * 360
            rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
            rect.center = self.pos - camera
            pygame.draw.arc(
                surface,
                color,
                rect,
                math.radians(-90),
                math.radians(angle - 90),
                3,
            )
