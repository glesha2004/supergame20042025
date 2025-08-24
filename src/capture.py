"""Capture point logic for SpaceGrid Arena."""
from __future__ import annotations

from typing import Dict, Optional


class CapturePoint:
    """Represents a single capture point.

    This is a lightweight logic-only representation used by the game and tests.
    The actual rendering and collision detection are handled elsewhere.
    """

    def __init__(self, time_to_capture: float = 10.0, teams: int = 2) -> None:
        self.time_to_capture = time_to_capture
        self.progress: Dict[int, float] = {team: 0.0 for team in range(teams)}
        self.owner: Optional[int] = None

    def update(self, dt: float, inside: Dict[int, int]) -> None:
        """Update capture progress based on the teams inside the point.

        Parameters
        ----------
        dt: float
            Time delta in seconds.
        inside: Dict[int, int]
            Mapping of team id to number of ships inside the capture radius.
        """
        if self.owner is not None and inside.get(self.owner, 0) == 0:
            # Owner left the point but no other team is present.
            return

        teams_present = [team for team, count in inside.items() if count > 0]
        if len(teams_present) != 1:
            # Contested or empty: progress does not change.
            return

        team = teams_present[0]
        self.progress[team] += dt
        if self.progress[team] >= self.time_to_capture:
            self.owner = team
            # Reset other teams' progress
            for other in self.progress:
                if other != team:
                    self.progress[other] = 0.0
