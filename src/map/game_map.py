"""
GameMap - The game world map
"""

from __future__ import annotations

import numpy as np
import tcod.console
import tcod.map
from tcod import libtcodpy

from src.map import tile as tile_types


class GameMap:
    """
    Represents the game map with tiles, FOV, and explored areas.
    """

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

        # Initialize all tiles as walls
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        # Visible and explored arrays
        self.visible = np.full((width, height), fill_value=False, order="F")
        self.explored = np.full((width, height), fill_value=False, order="F")

        # Rooms list (for spawning)
        self.rooms: list = []

    @property
    def walkable(self) -> np.ndarray:
        """Return walkable mask."""
        return self.tiles["walkable"]

    @property
    def transparent(self) -> np.ndarray:
        """Return transparent mask."""
        return self.tiles["transparent"]

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x, y are inside the map bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def compute_fov(self, x: int, y: int, radius: int = 8) -> None:
        """Compute the field of view from position (x, y)."""
        self.visible[:] = tcod.map.compute_fov(
            self.transparent,
            (x, y),
            radius=radius,
            algorithm=libtcodpy.FOV_SYMMETRIC_SHADOWCAST,
        )
        # Mark visible tiles as explored
        self.explored |= self.visible

    def render(self, console: tcod.console.Console) -> None:
        """
        Render the map to the console.

        Shows:
        - Visible tiles in full color
        - Explored but not visible tiles in dark color
        - Unexplored tiles as shroud
        """
        # Create the display array
        console.rgb[0:self.width, 0:self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD,
        )
