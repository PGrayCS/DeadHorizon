"""
Game engine - Main game class that orchestrates everything
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import tcod.console
import tcod.event

from src.entities.entity import Entity
from src.entities.player import Player
from src.entities.monster import Monster, ZombieType
from src.map.game_map import GameMap
from src.map.procgen import generate_dungeon
from src.engine.input_handler import handle_keys
from src.systems.combat import Combat
from src.graphics.effects import EffectsManager

if TYPE_CHECKING:
    from src.graphics.tileset_manager import TilesetManager


class Game:
    """Main game class that manages game state and orchestrates systems."""

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        map_width: int,
        map_height: int,
        tileset_manager: TilesetManager | None = None,
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.map_width = map_width
        self.map_height = map_height
        self.tileset_manager = tileset_manager

        # UI dimensions
        self.ui_height = screen_height - map_height

        # Visual effects manager
        self.effects = EffectsManager()

        # Entity list
        self.entities: list[Entity] = []

        # Generate the map and place player
        self.game_map, player_x, player_y = generate_dungeon(
            map_width=map_width,
            map_height=map_height,
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
        )

        # Create the player
        self.player = Player(x=player_x, y=player_y, tileset_manager=tileset_manager)
        self.entities.append(self.player)

        # Spawn zombies with variety
        self._spawn_zombies()

        # Message log
        self.messages: list[tuple[str, tuple[int, int, int]]] = []
        self.add_message("Welcome to Dead Horizon. Survive the apocalypse!", (255, 255, 100))
        self.add_message("Use WASD or arrow keys to move. ESC to quit.", (200, 200, 200))

        # Game state
        self.game_over = False

        # Initialize FOV
        self.recompute_fov()

    def _spawn_zombies(self, count: int = 12) -> None:
        """Spawn a variety of zombie types in random room positions."""
        rooms = getattr(self.game_map, 'rooms', [])

        # Spawn distribution: more basic zombies, fewer special types
        # Weights for each type (zombie, fast, brute, crawler, skeleton)
        zombie_weights = [
            (ZombieType.ZOMBIE, 40),    # 40% - Basic zombies
            (ZombieType.FAST, 20),      # 20% - Fast zombies
            (ZombieType.CRAWLER, 15),   # 15% - Crawlers
            (ZombieType.SKELETON, 15),  # 15% - Skeletons
            (ZombieType.BRUTE, 10),     # 10% - Brutes (rare, dangerous)
        ]
        
        types = [t for t, _ in zombie_weights]
        weights = [w for _, w in zombie_weights]

        for _ in range(count):
            if rooms:
                room = random.choice(rooms)
                x = random.randint(room.x1 + 1, room.x2 - 1)
                y = random.randint(room.y1 + 1, room.y2 - 1)
            else:
                x = random.randint(1, self.map_width - 2)
                y = random.randint(1, self.map_height - 2)

            # Don't spawn on player or walls
            if (x, y) != (self.player.x, self.player.y) and self.game_map.walkable[x, y]:
                # Don't spawn on other entities
                if not any(e.x == x and e.y == y for e in self.entities):
                    # Pick a random zombie type based on weights
                    zombie_type = random.choices(types, weights=weights, k=1)[0]
                    
                    zombie = Monster.spawn_zombie(
                        x=x,
                        y=y,
                        zombie_type=zombie_type,
                        tileset_manager=self.tileset_manager,
                    )
                    self.entities.append(zombie)

    def add_message(self, text: str, color: tuple[int, int, int] = (255, 255, 255)) -> None:
        """Add a message to the log."""
        self.messages.append((text, color))
        # Keep only the last 100 messages
        if len(self.messages) > 100:
            self.messages.pop(0)

    def recompute_fov(self) -> None:
        """Recompute the field of view based on player position."""
        self.game_map.compute_fov(self.player.x, self.player.y, radius=8)

    def handle_event(self, event: tcod.event.Event) -> str | None:
        """Handle input events and return action if any."""
        if self.game_over:
            if isinstance(event, tcod.event.KeyDown):
                if event.sym == tcod.event.KeySym.ESCAPE:
                    return "quit"
                elif event.sym == tcod.event.KeySym.r:
                    # Restart game
                    self.__init__(
                        self.screen_width,
                        self.screen_height,
                        self.map_width,
                        self.map_height,
                        self.tileset_manager,
                    )
            return None

        action = handle_keys(event)

        if action is None:
            return None

        if action == "quit":
            return "quit"

        if action == "wait":
            # Player waits, enemies take turn
            self._process_enemy_turns()
            self.effects.tick()
            return None

        if isinstance(action, tuple) and action[0] == "move":
            dx, dy = action[1], action[2]
            return self._handle_move(dx, dy)

        return None

    def _handle_move(self, dx: int, dy: int) -> str | None:
        """Handle player movement or attack."""
        dest_x = self.player.x + dx
        dest_y = self.player.y + dy

        # Clear flash states from previous turn
        self.player.is_flashing = False
        for entity in self.entities:
            entity.is_flashing = False

        # Check for collision with entities (attack)
        target = self._get_blocking_entity_at(dest_x, dest_y)
        if target:
            # Attack!
            damage = Combat.calculate_damage(self.player, target)
            target.hp -= damage

            # === DAMAGE FLASH ===
            target.is_flashing = True
            self.effects.add_damage_flash(target.x, target.y)

            if damage > 0:
                self.add_message(f"You hit the {target.name} for {damage} damage!", (255, 200, 100))
                # === BLOOD SPLATTER ===
                self.effects.add_blood(target.x, target.y, amount=min(damage // 2 + 1, 3))
            else:
                self.add_message(f"You hit the {target.name} but do no damage.", (200, 200, 200))

            if target.hp <= 0:
                self.add_message(f"The {target.name} is dead!", (255, 100, 100))
                # === DEATH BLOOD ===
                self.effects.add_death_blood(target.x, target.y)
                self.entities.remove(target)

            # Enemy turn
            self._process_enemy_turns()
            self.effects.tick()
            return None

        # Check for collision with walls
        if not self.game_map.walkable[dest_x, dest_y]:
            return None

        # Move the player
        self.player.x = dest_x
        self.player.y = dest_y

        # Recompute FOV
        self.recompute_fov()

        # Enemy turn
        self._process_enemy_turns()
        self.effects.tick()

        return None

    def _get_blocking_entity_at(self, x: int, y: int) -> Entity | None:
        """Return blocking entity at given position, if any."""
        for entity in self.entities:
            if entity.blocks and entity.x == x and entity.y == y and entity != self.player:
                return entity
        return None

    def _process_enemy_turns(self) -> None:
        """Process all enemy turns."""
        for entity in self.entities:
            if entity != self.player and hasattr(entity, 'take_turn'):
                entity.take_turn(self)

        # Check if player is dead
        if self.player.hp <= 0:
            self.game_over = True
            self.add_message("YOU DIED! Press R to restart or ESC to quit.", (255, 0, 0))

    def render(self, console: tcod.console.Console) -> None:
        """Render the game to the console."""
        # Render the map (always uses tiles mode now)
        self.game_map.render(console, self.tileset_manager)

        # Render blood splatter on floor (before entities)
        for effect in self.effects.effects:
            if hasattr(effect, 'permanent') and effect.permanent:
                if self.game_map.visible[effect.x, effect.y]:
                    if self.game_map.walkable[effect.x, effect.y]:
                        console.print(effect.x, effect.y, effect.char, fg=effect.color)

        # Render entities (in order: items, monsters, player)
        entities_sorted = sorted(self.entities, key=lambda e: e.render_order)
        for entity in entities_sorted:
            if self.game_map.visible[entity.x, entity.y]:
                # Get render character (always tile mode)
                render_char = entity.get_render_char(self.tileset_manager)
                # Use flash color if flashing, otherwise normal color
                render_color = entity.get_render_color()
                console.print(entity.x, entity.y, render_char, fg=render_color)

        # Render UI panel
        self._render_ui(console)

    def _render_ui(self, console: tcod.console.Console) -> None:
        """Render the UI panel at the bottom."""
        ui_y = self.map_height

        # Draw separator line
        console.draw_rect(0, ui_y, self.screen_width, 1, ord("-"), fg=(100, 100, 100))

        # Draw HP bar
        hp_text = f"HP: {self.player.hp}/{self.player.max_hp}"
        console.print(1, ui_y + 1, hp_text, fg=(255, 100, 100))

        # Draw HP bar visual
        bar_width = 20
        filled = int((self.player.hp / self.player.max_hp) * bar_width)
        console.draw_rect(1, ui_y + 2, bar_width, 1, ord("#"), fg=(100, 50, 50))
        if filled > 0:
            console.draw_rect(1, ui_y + 2, filled, 1, ord("#"), fg=(255, 50, 50))

        # Draw zombie count
        zombie_count = len([e for e in self.entities if isinstance(e, Monster)])
        console.print(25, ui_y + 1, f"Enemies: {zombie_count}", fg=(100, 200, 100))

        # Draw messages (last 4)
        msg_y = ui_y + 4
        for i, (text, color) in enumerate(self.messages[-4:]):
            console.print(1, msg_y + i, text, fg=color)

        # Draw game over message if applicable
        if self.game_over:
            console.print(
                self.screen_width // 2 - 10,
                self.map_height // 2,
                "  GAME OVER  ",
                fg=(255, 255, 255),
                bg=(200, 0, 0)
            )
