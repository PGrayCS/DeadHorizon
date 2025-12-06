"""
Base Entity class - All game objects inherit from this
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.graphics.tileset_manager import TilesetManager


class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """

    # Render order constants
    RENDER_ORDER_CORPSE = 0
    RENDER_ORDER_ITEM = 1
    RENDER_ORDER_ACTOR = 2

    def __init__(
        self,
        x: int,
        y: int,
        char: str,
        color: tuple[int, int, int],
        name: str = "Unknown",
        blocks: bool = True,
        render_order: int = RENDER_ORDER_ACTOR,
        tile_id: int | None = None,
    ) -> None:
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.render_order = render_order
        self.tile_id = tile_id  # PUA codepoint for tile graphics

    def move(self, dx: int, dy: int) -> None:
        """Move the entity by the given amount."""
        self.x += dx
        self.y += dy

    def distance_to(self, other: Entity) -> float:
        """Return the distance to another entity."""
        dx = other.x - self.x
        dy = other.y - self.y
        return (dx ** 2 + dy ** 2) ** 0.5

    def get_render_char(self, tileset_manager: TilesetManager | None = None) -> str:
        """
        Get the character to render for this entity.
        
        If tileset_manager is provided and in TILES mode, returns the tile character.
        Otherwise returns the ASCII character.
        """
        if tileset_manager and tileset_manager.is_tiles_mode and self.tile_id is not None:
            return chr(self.tile_id)
        return self.char

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.x}, {self.y}, {self.name!r})"
