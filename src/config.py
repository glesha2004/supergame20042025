import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

# Default configuration values used if the JSON file is missing keys.
DEFAULT_CONFIG = {
    "screen_width": 1280,
    "screen_height": 720,
    "arena_size": 3200,
    "capture_time": 10.0,
    "ship_speed": 220.0,
    "teams": ["blue", "red"],
    "hazard_radius": 35.0
}


@dataclass
class Config:
    """Runtime configuration values for the game."""
    screen_width: int
    screen_height: int
    arena_size: int
    capture_time: float
    ship_speed: float
    teams: List[str]
    hazard_radius: float


def load_config(path: str = "config/game_config.json") -> Config:
    """Load configuration from JSON file and merge with defaults."""
    data = DEFAULT_CONFIG.copy()
    cfg_path = Path(path)
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as fh:
            loaded = json.load(fh)
            data.update(loaded)
    return Config(**data)
