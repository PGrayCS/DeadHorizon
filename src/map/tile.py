"""
Tile definitions for the game map
"""

from __future__ import annotations

import numpy as np


# Tile graphics structured type
tile_graphic = np.dtype([
    ("ch", np.int32),      # Character code
    ("fg", "3B"),          # Foreground color (RGB)
    ("bg", "3B"),          # Background color (RGB)
])

# Tile data structured type
tile_dt = np.dtype([
    ("walkable", bool),     # Can be walked on
    ("transparent", bool),  # Allows light/vision through
    ("dark", tile_graphic), # Graphics when not in FOV
    ("light", tile_graphic), # Graphics when in FOV
])


def new_tile(
    *,
    walkable: bool,
    transparent: bool,
    dark: tuple[int, tuple[int, int, int], tuple[int, int, int]],
    light: tuple[int, tuple[int, int, int], tuple[int, int, int]],
) -> np.ndarray:
    """Helper function to create a new tile type."""
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)


# Shroud - unexplored areas
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=tile_graphic)

# Floor tile
floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("."), (50, 50, 50), (0, 0, 0)),
    light=(ord("."), (150, 150, 150), (0, 0, 0)),
)

# Wall tile
wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("#"), (50, 50, 80), (0, 0, 0)),
    light=(ord("#"), (130, 110, 90), (0, 0, 0)),
)

# Grass (outdoor)
grass = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord('"'), (20, 40, 20), (0, 0, 0)),
    light=(ord('"'), (50, 120, 50), (0, 0, 0)),
)

# Road
road = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord('.'), (40, 40, 40), (0, 0, 0)),
    light=(ord('.'), (100, 100, 100), (0, 0, 0)),
)

# Water (not walkable for now)
water = new_tile(
    walkable=False,
    transparent=True,
    dark=(ord('~'), (20, 30, 80), (0, 0, 0)),
    light=(ord('~'), (50, 80, 200), (0, 0, 0)),
)

# Door (closed)
door_closed = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord('+'), (80, 50, 30), (0, 0, 0)),
    light=(ord('+'), (180, 130, 80), (0, 0, 0)),
)

# Door (open)
door_open = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord('/'), (60, 40, 20), (0, 0, 0)),
    light=(ord('/'), (150, 110, 70), (0, 0, 0)),
)
