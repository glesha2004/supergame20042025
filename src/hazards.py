import pygame


class Spike:
    """A deadly hazard that destroys any ship on contact."""

    def __init__(self, pos, radius: float):
        self.pos = pygame.Vector2(pos)
        self.radius = radius

    def check_collision(self, ship) -> None:
        if not ship.alive:
            return
        if (ship.pos - self.pos).length() <= self.radius + ship.radius:
            ship.alive = False

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        pygame.draw.circle(surface, (255, 255, 0), (self.pos - camera), self.radius, 2)
