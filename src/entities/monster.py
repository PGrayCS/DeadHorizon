"""
Monster entity - Enemies that roam the map
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.entities.entity import Entity

if TYPE_CHECKING:
    from src.engine.game import Game


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
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks=True,
            render_order=Entity.RENDER_ORDER_ACTOR,
        )
        
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
    
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
    
    def _attack_player(self, game: Game) -> None:
        """Attack the player."""
        from src.systems.combat import Combat
        
        damage = Combat.calculate_damage(self, game.player)
        game.player.hp -= damage
        
        if damage > 0:
            game.add_message(f"The {self.name} attacks you for {damage} damage!", (255, 100, 100))
        else:
            game.add_message(f"The {self.name} attacks you but does no damage.", (200, 200, 200))
    
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
