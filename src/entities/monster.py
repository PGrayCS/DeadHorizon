"""
Monster entity - Enemies that roam the map
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from src.entities.entity import Entity

if TYPE_CHECKING:
    from src.engine.game import Game
    from src.graphics.tileset_manager import TilesetManager


class ZombieType(Enum):
    """Types of zombies with different behaviors and stats."""
    ZOMBIE = auto()       # Basic slow zombie
    FAST = auto()         # Fast but weak
    BRUTE = auto()        # Slow, tanky, hits hard
    CRAWLER = auto()      # Low HP, hard to hit
    SKELETON = auto()     # Undead, medium stats


# Zombie type configurations: (name, char, color, hp, attack, defense, tile_name)
ZOMBIE_CONFIGS = {
    ZombieType.ZOMBIE: ("Zombie", "Z", (100, 200, 100), 10, 3, 0, "zombie"),
    ZombieType.FAST: ("Fast Zombie", "z", (150, 255, 150), 6, 2, 0, "zombie_fast"),
    ZombieType.BRUTE: ("Zombie Brute", "B", (80, 150, 80), 20, 5, 2, "zombie_brute"),
    ZombieType.CRAWLER: ("Crawler", "c", (120, 180, 120), 5, 4, 0, "crawler"),
    ZombieType.SKELETON: ("Skeleton", "S", (220, 220, 200), 8, 3, 1, "skeleton"),
}


class Monster(Entity):
    """A hostile creature."""

    def __init__(
        self,
        x: int,
        y: int,
        name: str = "Monster",
        char: str = "M",
        color: tuple[int, int, int] = (255, 0, 0),
        hp: int = 10,
        attack: int = 3,
        defense: int = 0,
        tileset_manager: TilesetManager | None = None,
        tile_name: str | None = None,
        zombie_type: ZombieType | None = None,
    ) -> None:
        # Get tile ID from tileset manager if available
        tile_id = None
        if tileset_manager and tile_name:
            tile_id = tileset_manager.get_monster_tile(tile_name)

        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks=True,
            render_order=Entity.RENDER_ORDER_ACTOR,
            tile_id=tile_id,
        )

        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.zombie_type = zombie_type

    @classmethod
    def spawn_zombie(
        cls,
        x: int,
        y: int,
        zombie_type: ZombieType,
        tileset_manager: TilesetManager | None = None,
    ) -> "Monster":
        """Factory method to spawn a zombie of the given type."""
        name, char, color, hp, attack, defense, tile_name = ZOMBIE_CONFIGS[zombie_type]
        return cls(
            x=x,
            y=y,
            name=name,
            char=char,
            color=color,
            hp=hp,
            attack=attack,
            defense=defense,
            tileset_manager=tileset_manager,
            tile_name=tile_name,
            zombie_type=zombie_type,
        )

    def take_turn(self, game: Game) -> None:
        """Take a turn - basic AI."""
        # Only act if visible to player
        if not game.game_map.visible[self.x, self.y]:
            return

        # Get direction towards player
        dx = game.player.x - self.x
        dy = game.player.y - self.y
        distance = max(abs(dx), abs(dy))

        if distance <= 1:
            # Adjacent to player - attack!
            self._attack_player(game)
        elif distance <= 8:
            # Chase player
            self._move_towards_player(game, dx, dy)

            # Fast zombies move twice!
            if self.zombie_type == ZombieType.FAST and distance > 2:
                dx = game.player.x - self.x
                dy = game.player.y - self.y
                self._move_towards_player(game, dx, dy)

    def _attack_player(self, game: Game) -> None:
        """Attack the player using enhanced combat system."""
        from src.systems.combat import Combat, AttackResult

        result, damage = Combat.perform_attack(self, game.player, game)

        # Get and display combat message
        msg, color = Combat.get_attack_message(
            self.name, game.player.name, result, damage, is_player_attacking=False
        )
        game.add_message(msg, color)

        # Visual effects
        if result != AttackResult.MISS:
            game.player.is_flashing = True
            game.effects.add_damage_flash(game.player.x, game.player.y)

            if damage > 0:
                blood_amount = 1
                if result == AttackResult.CRITICAL:
                    blood_amount = 3
                elif damage >= 4:
                    blood_amount = 2
                game.effects.add_blood(game.player.x, game.player.y, amount=blood_amount)

    def _move_towards_player(self, game: Game, dx: int, dy: int) -> None:
        """Move one step towards the player."""
        # Normalize to -1, 0, or 1
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)

        dest_x = self.x + step_x
        dest_y = self.y + step_y

        # Check if destination is walkable and not blocked by entity
        if game.game_map.walkable[dest_x, dest_y]:
            blocking = game._get_blocking_entity_at(dest_x, dest_y)
            if blocking is None:
                self.x = dest_x
                self.y = dest_y
            elif step_x != 0 and step_y != 0:
                # Try horizontal only
                if game.game_map.walkable[self.x + step_x, self.y]:
                    if game._get_blocking_entity_at(self.x + step_x, self.y) is None:
                        self.x += step_x
                        return
                # Try vertical only
                if game.game_map.walkable[self.x, self.y + step_y]:
                    if game._get_blocking_entity_at(self.x, self.y + step_y) is None:
                        self.y += step_y
