"""
Game engine - Main game class that orchestrates everything
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import tcod.console
import tcod.event

from src.entities.entity import Entity
from src.entities.player import Player, PlayerStats
from src.entities.monster import Monster, ZombieType
from src.map.game_map import GameMap
from src.map.procgen import generate_dungeon
from src.engine.input_handler import handle_keys
from src.systems.combat import Combat, AttackResult
from src.graphics.effects import EffectsManager
from src.items.item import Item, get_random_item, create_item
from src.ui.inventory_screen import InventoryScreen

if TYPE_CHECKING:
    from src.graphics.tileset_manager import TilesetManager


class GameState:
    """Game state enum."""
    PLAYING = "playing"
    INVENTORY = "inventory"
    PAUSED = "paused"
    GAME_OVER = "game_over"


class Game:
    """Main game class that manages game state and orchestrates systems."""

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        map_width: int,
        map_height: int,
        tileset_manager: TilesetManager | None = None,
        player_name: str = "Survivor",
        player_stats: PlayerStats | None = None,
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.map_width = map_width
        self.map_height = map_height
        self.tileset_manager = tileset_manager
        self.player_name = player_name
        self.player_stats = player_stats

        # UI dimensions
        self.ui_height = screen_height - map_height

        # Visual effects manager
        self.effects = EffectsManager()

        # Entity list
        self.entities: list[Entity] = []

        # Items on the ground
        self.ground_items: dict[tuple[int, int], list[Item]] = {}

        # Generate the map and place player
        self.game_map, player_x, player_y = generate_dungeon(
            map_width=map_width,
            map_height=map_height,
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
        )

        # Create the player with custom stats
        self.player = Player(
            x=player_x,
            y=player_y,
            name=player_name,
            stats=player_stats,
            tileset_manager=tileset_manager,
        )
        self.entities.append(self.player)

        # Spawn zombies with variety
        self._spawn_zombies()

        # Spawn items in rooms
        self._spawn_items()

        # Message log
        self.messages: list[tuple[str, tuple[int, int, int]]] = []
        self.add_message(f"Welcome, {player_name}. Survive the apocalypse!", (255, 255, 100))
        self.add_message("WASD/Arrows to move. I=Inventory, G=Pickup", (200, 200, 200))

        # Kill counter
        self.kills = 0

        # Game state
        self.state = GameState.PLAYING
        self.game_over = False
        self.pause_selection = 0  # For pause menu

        # Inventory screen (created when opened)
        self.inventory_screen: InventoryScreen | None = None

        # Initialize FOV with player's perception-based radius
        self.recompute_fov()

    def _spawn_zombies(self, count: int = 12) -> None:
        """Spawn a variety of zombie types in random room positions."""
        rooms = getattr(self.game_map, 'rooms', [])

        # Spawn distribution: more basic zombies, fewer special types
        zombie_weights = [
            (ZombieType.ZOMBIE, 40),
            (ZombieType.FAST, 20),
            (ZombieType.CRAWLER, 15),
            (ZombieType.SKELETON, 15),
            (ZombieType.BRUTE, 10),
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

            if (x, y) != (self.player.x, self.player.y) and self.game_map.walkable[x, y]:
                if not any(e.x == x and e.y == y for e in self.entities):
                    zombie_type = random.choices(types, weights=weights, k=1)[0]
                    zombie = Monster.spawn_zombie(
                        x=x,
                        y=y,
                        zombie_type=zombie_type,
                        tileset_manager=self.tileset_manager,
                    )
                    self.entities.append(zombie)

    def _spawn_items(self) -> None:
        """Spawn items in dungeon rooms."""
        rooms = getattr(self.game_map, 'rooms', [])

        # Skip the first room (player spawn)
        for room in rooms[1:]:
            # 60% chance to spawn 1-3 items in each room
            if random.random() < 0.6:
                num_items = random.randint(1, 3)
                for _ in range(num_items):
                    x = random.randint(room.x1 + 1, room.x2 - 1)
                    y = random.randint(room.y1 + 1, room.y2 - 1)

                    if self.game_map.walkable[x, y]:
                        item = get_random_item()
                        self._add_ground_item(x, y, item)

    def _add_ground_item(self, x: int, y: int, item: Item) -> None:
        """Add an item to the ground at position."""
        key = (x, y)
        if key not in self.ground_items:
            self.ground_items[key] = []
        self.ground_items[key].append(item)

    def _get_ground_items(self, x: int, y: int) -> list[Item]:
        """Get items on the ground at position."""
        return self.ground_items.get((x, y), [])

    def _remove_ground_item(self, x: int, y: int, item: Item) -> bool:
        """Remove an item from the ground."""
        key = (x, y)
        if key in self.ground_items and item in self.ground_items[key]:
            self.ground_items[key].remove(item)
            if not self.ground_items[key]:
                del self.ground_items[key]
            return True
        return False

    def add_message(self, text: str, color: tuple[int, int, int] = (255, 255, 255)) -> None:
        """Add a message to the log."""
        self.messages.append((text, color))
        if len(self.messages) > 100:
            self.messages.pop(0)

    def recompute_fov(self) -> None:
        """Recompute the field of view based on player position and perception."""
        radius = getattr(self.player, 'fov_radius', 8)
        self.game_map.compute_fov(self.player.x, self.player.y, radius=radius)

    def handle_event(self, event: tcod.event.Event) -> str | None:
        """Handle input events and return action if any."""
        # Handle inventory state
        if self.state == GameState.INVENTORY:
            return self._handle_inventory_event(event)

        # Handle paused state
        if self.state == GameState.PAUSED:
            return self._handle_pause_event(event)

        # Handle game over state
        if self.game_over:
            if isinstance(event, tcod.event.KeyDown):
                if event.sym == tcod.event.KeySym.ESCAPE:
                    return "quit"
                elif event.sym == tcod.event.KeySym.r:
                    self.__init__(
                        self.screen_width,
                        self.screen_height,
                        self.map_width,
                        self.map_height,
                        self.tileset_manager,
                        self.player_name,
                        self.player_stats,
                    )
            return None

        action = handle_keys(event)

        if action is None:
            return None

        if action == "quit":
            return "quit"

        if action == "wait":
            self.add_message("You wait...", (150, 150, 150))
            self._process_enemy_turns()
            self.effects.tick()
            return None

        if action == "inventory":
            self.state = GameState.INVENTORY
            self.inventory_screen = InventoryScreen(self.player)
            return None

        if action == "pickup":
            return self._handle_pickup()

        if action == "pause":
            self.state = GameState.PAUSED
            self.pause_selection = 0  # 0=Resume, 1=Save, 2=Quit
            return None

        if action == "save":
            return self._handle_save()

        if action == "load":
            return self._handle_load()

        if isinstance(action, tuple) and action[0] == "move":
            dx, dy = action[1], action[2]
            return self._handle_move(dx, dy)

        return None

    def _handle_inventory_event(self, event: tcod.event.Event) -> str | None:
        """Handle events while inventory is open."""
        if self.inventory_screen is None:
            self.state = GameState.PLAYING
            return None

        should_close, result = self.inventory_screen.handle_input(event)

        if should_close:
            self.state = GameState.PLAYING
            self.inventory_screen = None
            return None

        # Handle special results
        if result and result.startswith("DROP:"):
            item_name = result[5:]
            # Create a copy of the dropped item to place on ground
            for item_id, item_def in __import__('src.items.item', fromlist=['ITEMS']).ITEMS.items():
                if item_def.name == item_name:
                    dropped_item = create_item(item_id)
                    self._add_ground_item(self.player.x, self.player.y, dropped_item)
                    self.add_message(f"Dropped {item_name}.", (200, 200, 100))
                    break

        return None

    def _handle_pause_event(self, event: tcod.event.Event) -> str | None:
        """Handle events while pause menu is open."""
        if not isinstance(event, tcod.event.KeyDown):
            return None

        key = event.sym

        # Navigation
        if key in (tcod.event.KeySym.UP, tcod.event.KeySym.w):
            self.pause_selection = (self.pause_selection - 1) % 3
        elif key in (tcod.event.KeySym.DOWN, tcod.event.KeySym.s):
            self.pause_selection = (self.pause_selection + 1) % 3
        elif key == tcod.event.KeySym.ESCAPE:
            # ESC closes pause menu
            self.state = GameState.PLAYING
        elif key in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER, tcod.event.KeySym.SPACE):
            if self.pause_selection == 0:  # Resume
                self.state = GameState.PLAYING
            elif self.pause_selection == 1:  # Save & Continue
                self._handle_save()
                self.state = GameState.PLAYING
            elif self.pause_selection == 2:  # Quit to Desktop
                return "quit"

        return None

    def _handle_pickup(self) -> str | None:
        """Handle picking up items."""
        items = self._get_ground_items(self.player.x, self.player.y)

        if not items:
            self.add_message("Nothing here to pick up.", (150, 150, 150))
            return None

        # Pick up the first item
        item = items[0]
        if self.player.add_to_inventory(item):
            self._remove_ground_item(self.player.x, self.player.y, item)
            self.add_message(f"Picked up {item.get_display_name()}.", (100, 255, 100))
        else:
            self.add_message("Inventory full!", (255, 100, 100))

        return None

    def _handle_save(self) -> None:
        """Handle saving the game."""
        from src.engine.save_system import save_game
        if save_game(self):
            self.add_message("Game saved!", (100, 255, 100))
        else:
            self.add_message("Failed to save game!", (255, 100, 100))

    def _handle_load(self) -> None:
        """Handle loading the game."""
        from src.engine.save_system import load_game
        if load_game(self):
            self.add_message("Game loaded!", (100, 255, 100))
            self.recompute_fov()
        else:
            self.add_message("No save file found!", (255, 100, 100))

    def _handle_move(self, dx: int, dy: int) -> str | None:
        """Handle player movement or attack."""
        dest_x = self.player.x + dx
        dest_y = self.player.y + dy

        self.player.is_flashing = False
        for entity in self.entities:
            entity.is_flashing = False

        target = self._get_blocking_entity_at(dest_x, dest_y)
        if target:
            result, damage = Combat.perform_attack(self.player, target, self)

            msg, color = Combat.get_attack_message(
                self.player.name, target.name, result, damage, is_player_attacking=True
            )
            self.add_message(msg, color)

            if result != AttackResult.MISS:
                target.is_flashing = True
                self.effects.add_damage_flash(target.x, target.y)

                if damage > 0:
                    blood_amount = 1
                    if result == AttackResult.CRITICAL:
                        blood_amount = 4
                    elif damage >= 5:
                        blood_amount = 3
                    elif damage >= 3:
                        blood_amount = 2
                    self.effects.add_blood(target.x, target.y, amount=blood_amount)

            if target.hp <= 0:
                self.kills += 1
                # XP based on enemy type
                xp_gained = 10 + getattr(target, 'max_hp', 10)
                if self.player.gain_xp(xp_gained):
                    self.add_message(f"LEVEL UP! You are now level {self.player.level}!", (255, 255, 100))
                self.add_message(f"The {target.name} is dead! (+{xp_gained} XP)", (255, 100, 100))
                self.effects.add_death_blood(target.x, target.y)
                self.entities.remove(target)

                # Chance to drop item on death
                if random.random() < 0.3:
                    drop = get_random_item()
                    self._add_ground_item(target.x, target.y, drop)
                    self.add_message(f"The {target.name} dropped {drop.name}!", (200, 200, 100))

            self._process_enemy_turns()
            self.effects.tick()
            return None

        if not self.game_map.walkable[dest_x, dest_y]:
            return None

        self.player.x = dest_x
        self.player.y = dest_y
        self.recompute_fov()

        # Notify if there are items here
        items = self._get_ground_items(dest_x, dest_y)
        if items:
            if len(items) == 1:
                self.add_message(f"You see {items[0].get_display_name()} here. (G to pick up)", (100, 200, 255))
            else:
                self.add_message(f"You see {len(items)} items here. (G to pick up)", (100, 200, 255))

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

        if self.player.hp <= 0:
            self.game_over = True
            self.add_message(f"YOU DIED! Kills: {self.kills}. Press R to restart.", (255, 0, 0))

    def render(self, console: tcod.console.Console) -> None:
        """Render the game to the console."""
        # If inventory is open, render that instead
        if self.state == GameState.INVENTORY and self.inventory_screen:
            self.inventory_screen.render(console)
            return

        # If paused, render pause menu overlay
        if self.state == GameState.PAUSED:
            self._render_pause_menu(console)
            return

        self.game_map.render(console, self.tileset_manager)

        # Render blood effects
        for effect in self.effects.effects:
            if hasattr(effect, 'permanent') and effect.permanent:
                if self.game_map.visible[effect.x, effect.y]:
                    if self.game_map.walkable[effect.x, effect.y]:
                        console.print(effect.x, effect.y, effect.char, fg=effect.color)

        # Render ground items
        for (x, y), items in self.ground_items.items():
            if self.game_map.visible[x, y] and items:
                # Show the top item
                item = items[0]
                console.print(x, y, item.char, fg=item.color)

        # Render entities
        entities_sorted = sorted(self.entities, key=lambda e: e.render_order)
        for entity in entities_sorted:
            if self.game_map.visible[entity.x, entity.y]:
                render_char = entity.get_render_char(self.tileset_manager)
                render_color = entity.get_render_color()
                console.print(entity.x, entity.y, render_char, fg=render_color)

        self._render_ui(console)

    def _render_ui(self, console: tcod.console.Console) -> None:
        """Render the UI panel at the bottom."""
        ui_y = self.map_height

        console.draw_rect(0, ui_y, self.screen_width, 1, ord("-"), fg=(100, 100, 100))

        # Player name and level
        name_text = f"{self.player.name} Lv.{self.player.level}"
        console.print(1, ui_y + 1, name_text, fg=(255, 255, 255))

        # HP bar
        hp_text = f"HP: {self.player.hp}/{self.player.max_hp}"
        console.print(1, ui_y + 2, hp_text, fg=(255, 100, 100))

        bar_width = 20
        filled = int((self.player.hp / self.player.max_hp) * bar_width)
        console.draw_rect(1, ui_y + 3, bar_width, 1, ord("#"), fg=(100, 50, 50))
        if filled > 0:
            console.draw_rect(1, ui_y + 3, filled, 1, ord("#"), fg=(255, 50, 50))

        # XP bar
        xp_text = f"XP: {self.player.xp}/{self.player.xp_to_next_level}"
        console.print(25, ui_y + 1, xp_text, fg=(100, 200, 255))
        xp_filled = int((self.player.xp / self.player.xp_to_next_level) * 15)
        console.draw_rect(25, ui_y + 2, 15, 1, ord("-"), fg=(30, 60, 80))
        if xp_filled > 0:
            console.draw_rect(25, ui_y + 2, xp_filled, 1, ord("="), fg=(100, 200, 255))

        # Stats - show total stats from equipment
        console.print(45, ui_y + 1, f"ATK:{self.player.get_total_attack()}", fg=(255, 180, 100))
        console.print(55, ui_y + 1, f"DEF:{self.player.get_total_defense()}", fg=(100, 180, 255))
        console.print(45, ui_y + 2, f"CRIT:{self.player.get_total_crit_bonus() + 10}%", fg=(255, 255, 100))
        console.print(55, ui_y + 2, f"Kills:{self.kills}", fg=(255, 100, 100))

        # Enemy count
        zombie_count = len([e for e in self.entities if isinstance(e, Monster)])
        console.print(68, ui_y + 1, f"Enemies:{zombie_count}", fg=(100, 200, 100))

        # Inventory count
        inv_count = len(self.player.inventory)
        console.print(68, ui_y + 2, f"Items:{inv_count}/{self.player.max_inventory_size}", fg=(200, 200, 100))

        # Messages (last 3)
        msg_y = ui_y + 4
        for i, (text, color) in enumerate(self.messages[-3:]):
            console.print(1, msg_y + i, text[:self.screen_width - 2], fg=color)

        if self.game_over:
            console.print(
                self.screen_width // 2 - 10,
                self.map_height // 2,
                "  GAME OVER  ",
                fg=(255, 255, 255),
                bg=(200, 0, 0)
            )

    def _render_pause_menu(self, console: tcod.console.Console) -> None:
        """Render the pause menu overlay."""
        # Dark overlay
        console.draw_rect(0, 0, self.screen_width, self.screen_height, ord(" "), bg=(10, 10, 15))

        # Box dimensions
        box_width = 30
        box_height = 12
        box_x = (self.screen_width - box_width) // 2
        box_y = (self.screen_height - box_height) // 2

        # Draw box background
        console.draw_rect(box_x, box_y, box_width, box_height, ord(" "), bg=(20, 20, 30))

        # Draw border
        for x in range(box_x, box_x + box_width):
            console.print(x, box_y, "-", fg=(80, 80, 100))
            console.print(x, box_y + box_height - 1, "-", fg=(80, 80, 100))
        for y in range(box_y, box_y + box_height):
            console.print(box_x, y, "|", fg=(80, 80, 100))
            console.print(box_x + box_width - 1, y, "|", fg=(80, 80, 100))
        console.print(box_x, box_y, "+", fg=(80, 80, 100))
        console.print(box_x + box_width - 1, box_y, "+", fg=(80, 80, 100))
        console.print(box_x, box_y + box_height - 1, "+", fg=(80, 80, 100))
        console.print(box_x + box_width - 1, box_y + box_height - 1, "+", fg=(80, 80, 100))

        # Title
        title = " PAUSED "
        console.print((self.screen_width - len(title)) // 2, box_y, title, fg=(255, 200, 100))

        # Menu options
        options = ["Resume Game", "Save & Continue", "Quit to Desktop"]
        option_y = box_y + 3

        for i, option in enumerate(options):
            y = option_y + i * 2
            if i == self.pause_selection:
                # Selected
                console.print(box_x + 2, y, ">>", fg=(255, 255, 100))
                console.print(box_x + 5, y, option, fg=(255, 255, 100))
            else:
                console.print(box_x + 5, y, option, fg=(140, 140, 150))

        # Controls hint
        hint = "[W/S] Select  [Enter] Confirm  [ESC] Resume"
        console.print((self.screen_width - len(hint)) // 2, box_y + box_height + 1, hint, fg=(80, 80, 100))
