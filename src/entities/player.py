"""
Player entity - The survivor controlled by the user
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.entities.entity import Entity

if TYPE_CHECKING:
    from src.graphics.tileset_manager import TilesetManager


class Player(Entity):
    """The player character."""

    def __init__(
        self,
        x: int,
        y: int,
        name: str = "Survivor",
        hp: int = 30,
        max_hp: int = 30,
        attack: int = 5,
        defense: int = 2,
        tileset_manager: TilesetManager | None = None,
    ) -> None:
        # Get tile ID from tileset manager if available
        tile_id = None
        if tileset_manager:
            tile_id = tileset_manager.get_player_tile("player")
        
        super().__init__(
            x=x,
            y=y,
            char="@",
            color=(255, 255, 255),
            name=name,
            blocks=True,
            render_order=Entity.RENDER_ORDER_ACTOR,
            tile_id=tile_id,
        )

        self.hp = hp
        self.max_hp = max_hp
        self.attack = attack
        self.defense = defense

        # Survival stats
        self.hunger = 100  # 100 = full, 0 = starving
        self.thirst = 100  # 100 = hydrated, 0 = dehydrated

        # Inventory (to be implemented)
        self.inventory: list = []

    def heal(self, amount: int) -> int:
        """Heal the player. Returns actual amount healed."""
        old_hp = self.hp
        self.hp = min(self.hp + amount, self.max_hp)
        return self.hp - old_hp

    def take_damage(self, amount: int) -> None:
        """Take damage."""
        self.hp -= amount
