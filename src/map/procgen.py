"""
Procedural map generation
"""

from __future__ import annotations

import random
import numpy as np
from typing import Iterator

import tcod

from src.map.game_map import GameMap
from src.map import tile as tile_types


class RectangularRoom:
    """A rectangular room on the map."""

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> tuple[int, int]:
        """Return the center coordinates of the room."""
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    @property
    def inner(self) -> tuple[slice, slice]:
        """Return the inner area of the room (excluding walls)."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another."""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


def tunnel_between(
    start: tuple[int, int],
    end: tuple[int, int],
) -> Iterator[tuple[int, int]]:
    """
    Return an L-shaped tunnel between two points.
    """
    x1, y1 = start
    x2, y2 = end

    if random.random() < 0.5:
        # Horizontal first, then vertical
        corner_x, corner_y = x2, y1
    else:
        # Vertical first, then horizontal
        corner_x, corner_y = x1, y2

    # Generate coordinates using Bresenham's line algorithm
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(
    map_width: int,
    map_height: int,
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
) -> tuple[GameMap, int, int]:
    """
    Generate a new dungeon map.

    Returns:
        Tuple of (game_map, player_x, player_y)
    """
    game_map = GameMap(map_width, map_height)

    rooms: list[RectangularRoom] = []

    for _ in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, map_width - room_width - 1)
        y = random.randint(0, map_height - room_height - 1)

        new_room = RectangularRoom(x, y, room_width, room_height)

        # Check for overlaps
        if any(new_room.intersects(other) for other in rooms):
            continue

        # Dig out the room
        game_map.tiles[new_room.inner] = tile_types.floor

        if rooms:
            # Tunnel to previous room
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                game_map.tiles[x, y] = tile_types.floor

        rooms.append(new_room)

    # Store rooms for spawning
    game_map.rooms = rooms

    _place_doors(game_map, rooms)

    # Player starts in the first room
    player_x, player_y = rooms[0].center

    return game_map, player_x, player_y


def _place_doors(game_map: GameMap, rooms: list[RectangularRoom]) -> None:
    """Place closed doors at room entrances leading to corridors."""

    def is_wall(x: int, y: int) -> bool:
        return np.array_equal(game_map.tiles[x, y], tile_types.wall)

    def is_floor(x: int, y: int) -> bool:
        return np.array_equal(game_map.tiles[x, y], tile_types.floor)

    def try_place_door(x: int, y: int, inside: tuple[int, int], outside: tuple[int, int]) -> None:
        if not game_map.in_bounds(*outside):
            return
        if is_wall(x, y) and is_floor(*inside) and is_floor(*outside):
            game_map.tiles[x, y] = tile_types.door_closed

    for room in rooms:
        for x in range(room.x1 + 1, room.x2 - 1):
            try_place_door(x, room.y1, (x, room.y1 + 1), (x, room.y1 - 1))
            try_place_door(x, room.y2 - 1, (x, room.y2 - 2), (x, room.y2))
        for y in range(room.y1 + 1, room.y2 - 1):
            try_place_door(room.x1, y, (room.x1 + 1, y), (room.x1 - 1, y))
            try_place_door(room.x2 - 1, y, (room.x2 - 2, y), (room.x2, y))
