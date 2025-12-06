"""
GameMap - The game world map
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import tcod.console
import tcod.map
from tcod import libtcodpy

from src.map import tile as tile_types

if TYPE_CHECKING:
    from src.graphics.tileset_manager import TilesetManager


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

        # Tile type tracking for graphical rendering
        # 0 = wall, 1 = floor (matches the tile type)
        self.tile_types = np.zeros((width, height), dtype=np.int32, order="F")

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

    def render(self, console: tcod.console.Console, tileset_manager: TilesetManager | None = None) -> None:
        """
        Render the map to the console using DawnLike tiles.
        """
        if tileset_manager is None:
            return

        # Get tile codepoints
        floor_tile = tileset_manager.get_terrain_tile("floor")
        wall_tile = tileset_manager.get_terrain_tile("wall")

        if floor_tile is None or wall_tile is None:
            print("ERROR: Terrain tiles not loaded!")
            return

        # Render each tile with proper lighting
        for x in range(self.width):
            for y in range(self.height):
                if not self.explored[x, y]:
                    # Unexplored - show nothing (black)
                    console.print(x, y, " ", fg=(0, 0, 0), bg=(0, 0, 0))
                elif self.visible[x, y]:
                    # Visible - show tile in full brightness
                    if self.tiles[x, y]["walkable"]:
                        console.print(x, y, chr(floor_tile), fg=(255, 255, 255), bg=(20, 20, 20))
                    else:
                        console.print(x, y, chr(wall_tile), fg=(255, 255, 255), bg=(40, 40, 40))
                else:
                    # Explored but not visible - show darker
                    if self.tiles[x, y]["walkable"]:
                        console.print(x, y, chr(floor_tile), fg=(100, 100, 100), bg=(10, 10, 10))
                    else:
                        console.print(x, y, chr(wall_tile), fg=(100, 100, 100), bg=(20, 20, 20))
