"""Artificial intelligence routines for bot behavior.

Only scaffolding is provided here; detailed combat logic will be added later.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BotProfile:
    """Configuration profile for a bot's upgrade priorities."""

    role: str
