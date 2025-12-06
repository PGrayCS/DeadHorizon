"""
Game engine - Main game class that orchestrates everything
"""

from __future__ import annotations

import tcod.event

from src.entities.entity import Entity
from src.entities.player import Player
from src.entities.monster import Monster
from src.map.game_map import GameMap
from src.map.procgen import generate_dungeon
from src.engine.input_handler import handle_keys
from src.systems.combat import Combat


class Game:
    """Main game class that manages game state and orchestrates systems."""
    
    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        map_width: int,
        map_height: int,
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.map_width = map_width
        self.map_height = map_height
        
        # UI dimensions
        self.ui_height = screen_height - map_height
        
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
        self.player = Player(x=player_x, y=player_y)
        self.entities.append(self.player)
        
        # Spawn some zombies
        self._spawn_zombies()
        
        # Message log
        self.messages: list[tuple[str, tuple[int, int, int]]] = []
        self.add_message("Welcome to Dead Horizon. Survive the apocalypse!", (255, 255, 100))
        self.add_message("Use arrow keys or WASD to move. Bump into zombies to attack.", (200, 200, 200))
        
        # Game state
        self.game_over = False
        
        # Initialize FOV
        self.recompute_fov()
    
    def _spawn_zombies(self, count: int = 10) -> None:
        """Spawn zombies in random room positions."""
        import random
        
        rooms = getattr(self.game_map, 'rooms', [])
        
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
                    zombie = Monster(x=x, y=y, name="Zombie", char="Z", color=(100, 200, 100), hp=10, attack=3, defense=1)
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
            return None
        
        if isinstance(action, tuple) and action[0] == "move":
            dx, dy = action[1], action[2]
            return self._handle_move(dx, dy)
        
        return None
    
    def _handle_move(self, dx: int, dy: int) -> str | None:
        """Handle player movement or attack."""
        dest_x = self.player.x + dx
        dest_y = self.player.y + dy
        
        # Check for collision with entities (attack)
        target = self._get_blocking_entity_at(dest_x, dest_y)
        if target:
            # Attack!
            damage = Combat.calculate_damage(self.player, target)
            target.hp -= damage
            
            if damage > 0:
                self.add_message(f"You hit the {target.name} for {damage} damage!", (255, 200, 100))
            else:
                self.add_message(f"You hit the {target.name} but do no damage.", (200, 200, 200))
            
            if target.hp <= 0:
                self.add_message(f"The {target.name} is dead!", (255, 100, 100))
                self.entities.remove(target)
            
            # Enemy turn
            self._process_enemy_turns()
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
        # Render the map
        self.game_map.render(console)
        
        # Render entities (in order: items, monsters, player)
        entities_sorted = sorted(self.entities, key=lambda e: e.render_order)
        for entity in entities_sorted:
            if self.game_map.visible[entity.x, entity.y]:
                console.print(entity.x, entity.y, entity.char, fg=entity.color)
        
        # Render UI panel
        self._render_ui(console)
    
    def _render_ui(self, console: tcod.console.Console) -> None:
        """Render the UI panel at the bottom."""
        ui_y = self.map_height
        
        # Draw separator line
        console.draw_rect(0, ui_y, self.screen_width, 1, ord("─"), fg=(100, 100, 100))
        
        # Draw HP bar
        hp_text = f"HP: {self.player.hp}/{self.player.max_hp}"
        console.print(1, ui_y + 1, hp_text, fg=(255, 100, 100))
        
        # Draw HP bar visual
        bar_width = 20
        filled = int((self.player.hp / self.player.max_hp) * bar_width)
        console.draw_rect(1, ui_y + 2, bar_width, 1, ord("█"), fg=(100, 50, 50))
        if filled > 0:
            console.draw_rect(1, ui_y + 2, filled, 1, ord("█"), fg=(255, 50, 50))
        
        # Draw zombie count
        zombie_count = len([e for e in self.entities if isinstance(e, Monster)])
        console.print(25, ui_y + 1, f"Zombies: {zombie_count}", fg=(100, 200, 100))
        
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
