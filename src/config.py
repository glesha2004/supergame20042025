"""Configuration loader for SpaceGrid Arena."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "game_config.json"
)


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Return configuration dictionary loaded from *path*.

    Parameters
    ----------
    path:
        Location of the JSON configuration file. If omitted, the default
        ``config/game_config.json`` relative to the repository root is used.
    """
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)
