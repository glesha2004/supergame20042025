import random
import pygame
from .config import Config
from .entities import Ship, BotShip, TEAM_COLORS
from .capture import CapturePoint
from .hazards import Spike


class Game:
    """High level game controller and main loop."""

    def __init__(self, config: Config):
        pygame.init()
        self.cfg = config
        self.screen = pygame.display.set_mode((config.screen_width, config.screen_height))
        pygame.display.set_caption("SpaceGrid Arena")
        self.clock = pygame.time.Clock()
        self.camera = pygame.Vector2(0, 0)

        # create capture points
        half = config.arena_size / 2
        offset = 400
        radius = 120
        self.capture_points = [
            CapturePoint((half - offset, half - offset), radius, config.capture_time),
            CapturePoint((half + offset, half - offset), radius, config.capture_time),
            CapturePoint((half - offset, half + offset), radius, config.capture_time),
            CapturePoint((half + offset, half + offset), radius, config.capture_time),
        ]

        # hazards: four corners
        hz = config.hazard_radius
        self.hazards = [
            Spike((hz, hz), hz),
            Spike((config.arena_size - hz, hz), hz),
            Spike((hz, config.arena_size - hz), hz),
            Spike((config.arena_size - hz, config.arena_size - hz), hz),
        ]

        self.ships: list[Ship] = []
        self.player = Ship(pygame.Vector2(half, half), config.teams[0], config.ship_speed, is_player=True)
        self.ships.append(self.player)

        for team in config.teams:
            for _ in range(3):
                if team == self.player.team and _ == 0:
                    continue  # skip, player already created
                pos = pygame.Vector2(
                    random.randint(100, config.arena_size - 100),
                    random.randint(100, config.arena_size - 100),
                )
                bot = BotShip(pos, team, config.ship_speed, self.capture_points)
                self.ships.append(bot)

        self.running = True

    # Input handling for player
    def _get_input(self):
        keys = pygame.key.get_pressed()
        return {
            "up": keys[pygame.K_w],
            "down": keys[pygame.K_s],
            "left": keys[pygame.K_a],
            "right": keys[pygame.K_d],
        }

    def run(self, max_frames: int | None = None):
        frame = 0
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # update
            input_state = self._get_input()
            for ship in self.ships:
                if ship.is_player:
                    ship.update(dt, input_state)
                else:
                    ship.update(dt)

            for hazard in self.hazards:
                for ship in self.ships:
                    hazard.check_collision(ship)

            for point in self.capture_points:
                point.update(dt, self.ships)

            # check victory
            for team in self.cfg.teams:
                if all(p.owner == team for p in self.capture_points):
                    print(f"Team {team} wins!")
                    self.running = False

            # draw
            self.screen.fill((10, 10, 20))
            for point in self.capture_points:
                point.draw(self.screen, self.camera, TEAM_COLORS)
            for hazard in self.hazards:
                hazard.draw(self.screen, self.camera)
            for ship in self.ships:
                ship.draw(self.screen, self.camera)
            pygame.display.flip()

            frame += 1
            if max_frames and frame >= max_frames:
                self.running = False

        pygame.quit()
