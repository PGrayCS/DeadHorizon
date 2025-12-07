"""
Inventory Screen - View and manage items
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

import tcod
import tcod.console
import tcod.event

if TYPE_CHECKING:
    from src.entities.player import Player
    from src.items.item import Item


class InventoryMode(Enum):
    """What the player is doing in inventory."""
    BROWSE = auto()      # Just looking
    SELECT_ACTION = auto()  # Choosing what to do with an item


class InventoryScreen:
    """
    Full-screen inventory management.
    """

    # Colors
    COLOR_TITLE = (255, 200, 50)
    COLOR_SELECTED = (100, 200, 255)
    COLOR_NORMAL = (200, 200, 200)
    COLOR_EQUIPPED = (100, 255, 100)
    COLOR_STATS = (180, 180, 180)
    COLOR_DESCRIPTION = (150, 150, 150)
    COLOR_WEAPON = (255, 100, 100)
    COLOR_ARMOR = (100, 100, 255)
    COLOR_CONSUMABLE = (100, 255, 100)
    COLOR_KEY_HINT = (255, 255, 100)

    def __init__(self, player: Player) -> None:
        self.player = player
        self.selected_index = 0
        self.mode = InventoryMode.BROWSE
        self.action_index = 0  # For action submenu
        self.scroll_offset = 0
        self.max_visible_items = 15
        self.messages: list[tuple[str, tuple[int, int, int]]] = []

    def render(self, console: tcod.console.Console) -> None:
        """Render the inventory screen."""
        console.clear()
        
        width = console.width
        height = console.height

        # Title
        title = "═══ INVENTORY ═══"
        console.print(
            width // 2 - len(title) // 2,
            1,
            title,
            fg=self.COLOR_TITLE,
        )

        # Equipment section (top right)
        self._render_equipment(console, width - 30, 3)

        # Player stats (top left)
        self._render_player_stats(console, 2, 3)

        # Item list (center-left)
        self._render_item_list(console, 2, 12, width // 2 - 4)

        # Item details (right side)
        if self.player.inventory and self.selected_index < len(self.player.inventory):
            item = self.player.inventory[self.selected_index]
            self._render_item_details(console, width // 2 + 2, 12, item)

        # Action menu (if selecting action)
        if self.mode == InventoryMode.SELECT_ACTION:
            self._render_action_menu(console)

        # Messages at bottom
        self._render_messages(console, 2, height - 4)

        # Controls at very bottom
        self._render_controls(console, height - 2)

    def _render_equipment(self, console: tcod.console.Console, x: int, y: int) -> None:
        """Render equipped items."""
        console.print(x, y, "┌─ EQUIPMENT ─┐", fg=self.COLOR_TITLE)
        
        # Weapon
        weapon_name = self.player.equipped_weapon.name if self.player.equipped_weapon else "None"
        weapon_color = self.COLOR_WEAPON if self.player.equipped_weapon else self.COLOR_STATS
        console.print(x, y + 2, "Weapon:", fg=self.COLOR_NORMAL)
        console.print(x + 8, y + 2, weapon_name, fg=weapon_color)

        # Armor
        armor_name = self.player.equipped_armor.name if self.player.equipped_armor else "None"
        armor_color = self.COLOR_ARMOR if self.player.equipped_armor else self.COLOR_STATS
        console.print(x, y + 3, "Armor:", fg=self.COLOR_NORMAL)
        console.print(x + 8, y + 3, armor_name, fg=armor_color)

    def _render_player_stats(self, console: tcod.console.Console, x: int, y: int) -> None:
        """Render player combat stats."""
        console.print(x, y, "┌─ STATS ─┐", fg=self.COLOR_TITLE)

        stats = [
            (f"HP: {self.player.hp}/{self.player.max_hp}", (255, 100, 100)),
            (f"ATK: {self.player.get_total_attack()}", (255, 150, 100)),
            (f"DEF: {self.player.get_total_defense()}", (100, 150, 255)),
            (f"ACC: +{self.player.get_total_accuracy()}%", (200, 200, 100)),
            (f"CRIT: +{self.player.get_total_crit_bonus()}%", (255, 200, 100)),
        ]

        for i, (text, color) in enumerate(stats):
            console.print(x, y + 2 + i, text, fg=color)

    def _render_item_list(self, console: tcod.console.Console, x: int, y: int, width: int) -> None:
        """Render the list of inventory items."""
        console.print(x, y, f"┌─ ITEMS ({len(self.player.inventory)}/{self.player.max_inventory_size}) ─┐", fg=self.COLOR_TITLE)

        if not self.player.inventory:
            console.print(x + 2, y + 2, "Your inventory is empty.", fg=self.COLOR_STATS)
            return

        # Calculate scroll
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.max_visible_items:
            self.scroll_offset = self.selected_index - self.max_visible_items + 1

        # Render visible items
        for i in range(self.max_visible_items):
            item_index = self.scroll_offset + i
            if item_index >= len(self.player.inventory):
                break

            item = self.player.inventory[item_index]
            display_y = y + 2 + i

            # Selection highlight
            if item_index == self.selected_index:
                # Draw selection bar
                console.draw_rect(x, display_y, width, 1, ord(" "), bg=(40, 60, 80))
                fg_color = self.COLOR_SELECTED
            else:
                fg_color = self._get_item_color(item)

            # Item character
            console.print(x + 1, display_y, item.char, fg=item.color)

            # Item name
            name = item.get_display_name()
            if len(name) > width - 6:
                name = name[:width - 9] + "..."
            console.print(x + 3, display_y, name, fg=fg_color)

        # Scroll indicators
        if self.scroll_offset > 0:
            console.print(x + width - 3, y + 1, "▲", fg=self.COLOR_KEY_HINT)
        if self.scroll_offset + self.max_visible_items < len(self.player.inventory):
            console.print(x + width - 3, y + 2 + self.max_visible_items, "▼", fg=self.COLOR_KEY_HINT)

    def _render_item_details(self, console: tcod.console.Console, x: int, y: int, item: "Item") -> None:
        """Render details about the selected item."""
        console.print(x, y, "┌─ DETAILS ─┐", fg=self.COLOR_TITLE)

        # Item name with color
        console.print(x, y + 2, item.name, fg=self._get_item_color(item))

        # Type
        from src.items.item import ItemType, EquipSlot
        type_name = item.item_type.name.title()
        console.print(x, y + 3, f"Type: {type_name}", fg=self.COLOR_STATS)

        # Equip slot
        if item.equip_slot != EquipSlot.NONE:
            console.print(x, y + 4, f"Slot: {item.equip_slot.name.title()}", fg=self.COLOR_STATS)

        # Stats
        stat_str = item.get_stat_string()
        if stat_str != "No stats":
            console.print(x, y + 5, "Stats:", fg=self.COLOR_NORMAL)
            # Split stats across lines if needed
            stats = stat_str.split(", ")
            for i, stat in enumerate(stats[:4]):  # Max 4 stats shown
                console.print(x + 2, y + 6 + i, stat, fg=self.COLOR_EQUIPPED)

        # Description (wrapped)
        desc_y = y + 11
        console.print(x, desc_y, "Description:", fg=self.COLOR_NORMAL)
        desc_lines = self._wrap_text(item.description, 25)
        for i, line in enumerate(desc_lines[:3]):  # Max 3 lines
            console.print(x, desc_y + 1 + i, line, fg=self.COLOR_DESCRIPTION)

        # Value
        console.print(x, desc_y + 5, f"Value: {item.value}", fg=self.COLOR_STATS)

    def _render_action_menu(self, console: tcod.console.Console) -> None:
        """Render action menu for selected item."""
        if not self.player.inventory or self.selected_index >= len(self.player.inventory):
            return

        item = self.player.inventory[self.selected_index]
        from src.items.item import ItemType, EquipSlot

        # Build action list
        actions = []
        if item.item_type == ItemType.CONSUMABLE:
            actions.append(("Use", "u"))
        if item.equip_slot != EquipSlot.NONE:
            actions.append(("Equip", "e"))
        actions.append(("Drop", "d"))
        actions.append(("Cancel", "Esc"))

        # Draw menu box
        box_width = 16
        box_height = len(actions) + 4
        box_x = console.width // 2 - box_width // 2
        box_y = console.height // 2 - box_height // 2

        # Background
        console.draw_rect(box_x, box_y, box_width, box_height, ord(" "), bg=(30, 30, 40))
        
        # Border
        for bx in range(box_width):
            console.print(box_x + bx, box_y, "─", fg=self.COLOR_TITLE)
            console.print(box_x + bx, box_y + box_height - 1, "─", fg=self.COLOR_TITLE)
        for by in range(box_height):
            console.print(box_x, box_y + by, "│", fg=self.COLOR_TITLE)
            console.print(box_x + box_width - 1, box_y + by, "│", fg=self.COLOR_TITLE)
        console.print(box_x, box_y, "┌", fg=self.COLOR_TITLE)
        console.print(box_x + box_width - 1, box_y, "┐", fg=self.COLOR_TITLE)
        console.print(box_x, box_y + box_height - 1, "└", fg=self.COLOR_TITLE)
        console.print(box_x + box_width - 1, box_y + box_height - 1, "┘", fg=self.COLOR_TITLE)

        # Title
        console.print(box_x + 2, box_y + 1, "ACTION", fg=self.COLOR_TITLE)

        # Actions
        for i, (action, key) in enumerate(actions):
            action_y = box_y + 3 + i
            if i == self.action_index:
                console.draw_rect(box_x + 1, action_y, box_width - 2, 1, ord(" "), bg=(60, 80, 100))
                fg = self.COLOR_SELECTED
            else:
                fg = self.COLOR_NORMAL
            console.print(box_x + 2, action_y, f"[{key}] {action}", fg=fg)

    def _render_messages(self, console: tcod.console.Console, x: int, y: int) -> None:
        """Render recent messages."""
        for i, (msg, color) in enumerate(self.messages[-2:]):
            console.print(x, y + i, msg, fg=color)

    def _render_controls(self, console: tcod.console.Console, y: int) -> None:
        """Render control hints."""
        if self.mode == InventoryMode.BROWSE:
            controls = "[↑↓] Navigate  [Enter] Actions  [I/Esc] Close"
        else:
            controls = "[↑↓] Select  [Enter] Confirm  [Esc] Cancel"
        
        console.print(
            console.width // 2 - len(controls) // 2,
            y,
            controls,
            fg=self.COLOR_KEY_HINT,
        )

    def _get_item_color(self, item: "Item") -> tuple[int, int, int]:
        """Get display color for an item based on type."""
        from src.items.item import ItemType
        if item.item_type == ItemType.WEAPON:
            return self.COLOR_WEAPON
        elif item.item_type == ItemType.ARMOR:
            return self.COLOR_ARMOR
        elif item.item_type == ItemType.CONSUMABLE:
            return self.COLOR_CONSUMABLE
        return self.COLOR_NORMAL

    def _wrap_text(self, text: str, width: int) -> list[str]:
        """Wrap text to fit within width."""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines

    def handle_input(self, event: tcod.event.Event) -> tuple[bool, str | None]:
        """
        Handle input events.
        Returns (should_close, message).
        """
        if isinstance(event, tcod.event.KeyDown):
            return self._handle_key(event)
        return False, None

    def _handle_key(self, event: tcod.event.KeyDown) -> tuple[bool, str | None]:
        """Handle keyboard input."""
        key = event.sym

        if self.mode == InventoryMode.BROWSE:
            return self._handle_browse_input(key)
        else:
            return self._handle_action_input(key)

    def _handle_browse_input(self, key: int) -> tuple[bool, str | None]:
        """Handle input in browse mode."""
        # Navigation
        if key == tcod.event.KeySym.UP:
            if self.player.inventory:
                self.selected_index = (self.selected_index - 1) % len(self.player.inventory)
        elif key == tcod.event.KeySym.DOWN:
            if self.player.inventory:
                self.selected_index = (self.selected_index + 1) % len(self.player.inventory)
        
        # Open action menu
        elif key == tcod.event.KeySym.RETURN:
            if self.player.inventory:
                self.mode = InventoryMode.SELECT_ACTION
                self.action_index = 0

        # Quick actions
        elif key == tcod.event.KeySym.u:
            return self._try_use_item()
        elif key == tcod.event.KeySym.e:
            return self._try_equip_item()
        elif key == tcod.event.KeySym.d:
            return self._try_drop_item()

        # Close inventory
        elif key in (tcod.event.KeySym.i, tcod.event.KeySym.ESCAPE):
            return True, None

        return False, None

    def _handle_action_input(self, key: int) -> tuple[bool, str | None]:
        """Handle input in action selection mode."""
        if not self.player.inventory or self.selected_index >= len(self.player.inventory):
            self.mode = InventoryMode.BROWSE
            return False, None

        item = self.player.inventory[self.selected_index]
        from src.items.item import ItemType, EquipSlot

        # Build action list (same as render)
        actions = []
        if item.item_type == ItemType.CONSUMABLE:
            actions.append("use")
        if item.equip_slot != EquipSlot.NONE:
            actions.append("equip")
        actions.append("drop")
        actions.append("cancel")

        # Navigation
        if key == tcod.event.KeySym.UP:
            self.action_index = (self.action_index - 1) % len(actions)
        elif key == tcod.event.KeySym.DOWN:
            self.action_index = (self.action_index + 1) % len(actions)

        # Select action
        elif key == tcod.event.KeySym.RETURN:
            action = actions[self.action_index]
            self.mode = InventoryMode.BROWSE
            
            if action == "use":
                return self._try_use_item()
            elif action == "equip":
                return self._try_equip_item()
            elif action == "drop":
                return self._try_drop_item()
            # cancel does nothing

        # Quick keys
        elif key == tcod.event.KeySym.u:
            self.mode = InventoryMode.BROWSE
            return self._try_use_item()
        elif key == tcod.event.KeySym.e:
            self.mode = InventoryMode.BROWSE
            return self._try_equip_item()
        elif key == tcod.event.KeySym.d:
            self.mode = InventoryMode.BROWSE
            return self._try_drop_item()

        # Cancel
        elif key == tcod.event.KeySym.ESCAPE:
            self.mode = InventoryMode.BROWSE

        return False, None

    def _try_use_item(self) -> tuple[bool, str | None]:
        """Try to use the selected item."""
        if not self.player.inventory or self.selected_index >= len(self.player.inventory):
            return False, None

        item = self.player.inventory[self.selected_index]
        success, message = self.player.use_item(item)
        
        if success:
            self.messages.append((message, (100, 255, 100)))
            # Adjust selection if item was consumed
            if self.selected_index >= len(self.player.inventory):
                self.selected_index = max(0, len(self.player.inventory) - 1)
        else:
            self.messages.append((message, (255, 100, 100)))
        
        return False, message if success else None

    def _try_equip_item(self) -> tuple[bool, str | None]:
        """Try to equip the selected item."""
        if not self.player.inventory or self.selected_index >= len(self.player.inventory):
            return False, None

        item = self.player.inventory[self.selected_index]
        success, message = self.player.equip_item(item)
        
        if success:
            self.messages.append((message, (100, 200, 255)))
            # Adjust selection
            if self.selected_index >= len(self.player.inventory):
                self.selected_index = max(0, len(self.player.inventory) - 1)
        else:
            self.messages.append((message, (255, 100, 100)))
        
        return False, message if success else None

    def _try_drop_item(self) -> tuple[bool, str | None]:
        """Drop the selected item (returns it to be placed on map)."""
        if not self.player.inventory or self.selected_index >= len(self.player.inventory):
            return False, None

        item = self.player.inventory[self.selected_index]
        self.player.remove_from_inventory(item)
        
        message = f"Dropped {item.get_display_name()}."
        self.messages.append((message, (200, 200, 100)))

        # Adjust selection
        if self.selected_index >= len(self.player.inventory):
            self.selected_index = max(0, len(self.player.inventory) - 1)

        return False, f"DROP:{item.name}"  # Special return for game to handle
