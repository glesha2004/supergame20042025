"""Configuration utilities for SpaceGrid Arena.

This module loads JSON configuration files and exposes them as dictionaries.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "game_config.json"


def load_config(path: Path | None = None) -> Dict[str, Any]:
    """Load configuration from *path* or from the default location.

    Parameters
    ----------
    path: Path | None
        Optional path to the configuration JSON file.
    """
    cfg_path = path or DEFAULT_CONFIG_PATH
    with cfg_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)
