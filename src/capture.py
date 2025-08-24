"""Capture point logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class CapturePoint:
    position: tuple[float, float]
    radius: float
    progress: Dict[int, float] = field(default_factory=dict)
    owner: Optional[int] = None

    def update(self, occupants: Dict[int, int], dt: float, capture_time: float = 10.0) -> None:
        """Update capture progress based on *occupants* and elapsed *dt*.

        Parameters
        ----------
        occupants:
            Mapping of team id to number of ships currently inside the point.
        dt:
            Time delta in seconds.
        capture_time:
            Number of seconds required to fully capture a point.
        """
        if len(occupants) == 1:
            team, _ = next(iter(occupants.items()))
            self.progress[team] = self.progress.get(team, 0.0) + dt
            if self.progress[team] >= capture_time:
                self.owner = team
                self.progress = {team: capture_time}
        elif len(occupants) > 1:
            # contested: no progress change
            pass
