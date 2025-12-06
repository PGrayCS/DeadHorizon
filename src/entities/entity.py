"""
Base Entity class - All game objects inherit from this
"""

from __future__ import annotations


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
    ) -> None:
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.render_order = render_order
    
    def move(self, dx: int, dy: int) -> None:
        """Move the entity by the given amount."""
        self.x += dx
        self.y += dy
    
    def distance_to(self, other: Entity) -> float:
        """Return the distance to another entity."""
        dx = other.x - self.x
        dy = other.y - self.y
        return (dx ** 2 + dy ** 2) ** 0.5
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.x}, {self.y}, {self.name!r})"
