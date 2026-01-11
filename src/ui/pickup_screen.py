"""
Pickup Screen - Select items on the ground to pick up
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import tcod
import tcod.console
import tcod.event

if TYPE_CHECKING:
    from src.items.item import Item


@dataclass
class PickupEntry:
    """Display entry for pickupable items."""
    item: "Item"
    items: list["Item"]


class PickupScreen:
    """UI screen for selecting items to pick up."""

    COLOR_TITLE = (255, 200, 50)
    COLOR_SELECTED = (100, 200, 255)
    COLOR_NORMAL = (200, 200, 200)
    COLOR_KEY_HINT = (255, 255, 100)

    def __init__(self, items: list["Item"]) -> None:
        self.entries = self._build_entries(items)
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible_items = 15
        self.selected_entries: set[int] = set()

    def _build_entries(self, items: list["Item"]) -> list[PickupEntry]:
        """Group stackable items into display entries."""
        entries: list[PickupEntry] = []
        for item in items:
            if item.stackable:
                stacked = False
                for entry in entries:
                    if entry.item.can_stack_with(item):
                        entry.item.stack_size += item.stack_size
                        entry.items.append(item)
                        stacked = True
                        break
                if stacked:
                    continue
            entries.append(PickupEntry(item.copy(), [item]))
        return entries

    def render(self, console: tcod.console.Console) -> None:
        """Render the pickup screen."""
        console.clear()
        width = console.width
        height = console.height

        title = "═══ PICK UP ITEMS ═══"
        console.print(width // 2 - len(title) // 2, 1, title, fg=self.COLOR_TITLE)

        self._render_item_list(console, 2, 4, width - 4, height - 8)
        self._render_controls(console, height - 2)

    def _render_item_list(
        self,
        console: tcod.console.Console,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        """Render the list of items to pick up."""
        console.print(x, y, f"┌─ ITEMS HERE ({len(self.entries)}) ─┐", fg=self.COLOR_TITLE)

        if not self.entries:
            console.print(x + 2, y + 2, "Nothing here.", fg=self.COLOR_NORMAL)
            return

        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.max_visible_items:
            self.scroll_offset = self.selected_index - self.max_visible_items + 1

        for i in range(self.max_visible_items):
            entry_index = self.scroll_offset + i
            if entry_index >= len(self.entries):
                break

            entry = self.entries[entry_index]
            display_y = y + 2 + i

            if entry_index == self.selected_index:
                console.draw_rect(x, display_y, width, 1, ord(" "), bg=(40, 60, 80))
                fg_color = self.COLOR_SELECTED
            else:
                fg_color = self.COLOR_NORMAL

            selected = "[x]" if entry_index in self.selected_entries else "[ ]"
            console.print(x + 1, display_y, selected, fg=self.COLOR_KEY_HINT)
            console.print(x + 5, display_y, entry.item.char, fg=entry.item.color)
            name = entry.item.get_display_name()
            max_name_len = width - 10
            if len(name) > max_name_len:
                name = name[: max_name_len - 3] + "..."
            console.print(x + 7, display_y, name, fg=fg_color)

        if self.scroll_offset > 0:
            console.print(x + width - 3, y + 1, "▲", fg=self.COLOR_KEY_HINT)
        if self.scroll_offset + self.max_visible_items < len(self.entries):
            console.print(x + width - 3, y + 2 + self.max_visible_items, "▼", fg=self.COLOR_KEY_HINT)

    def _render_controls(self, console: tcod.console.Console, y: int) -> None:
        """Render control hints."""
        controls = "[↑↓] Navigate  [Space] Toggle  [A] All  [Enter] Pick up  [Esc] Cancel"
        console.print(
            console.width // 2 - len(controls) // 2,
            y,
            controls,
            fg=self.COLOR_KEY_HINT,
        )

    def handle_input(self, event: tcod.event.Event) -> tuple[bool, list["Item"] | None]:
        """Handle input events. Returns (should_close, items_to_pick)."""
        if not isinstance(event, tcod.event.KeyDown):
            return False, None

        key = event.sym

        if key == tcod.event.KeySym.UP:
            if self.entries:
                self.selected_index = (self.selected_index - 1) % len(self.entries)
        elif key == tcod.event.KeySym.DOWN:
            if self.entries:
                self.selected_index = (self.selected_index + 1) % len(self.entries)
        elif key == tcod.event.KeySym.SPACE:
            if self.entries:
                if self.selected_index in self.selected_entries:
                    self.selected_entries.remove(self.selected_index)
                else:
                    self.selected_entries.add(self.selected_index)
        elif key == tcod.event.KeySym.a:
            if len(self.selected_entries) == len(self.entries):
                self.selected_entries.clear()
            else:
                self.selected_entries = set(range(len(self.entries)))
        elif key == tcod.event.KeySym.RETURN:
            if not self.entries:
                return True, None
            indices = (
                sorted(self.selected_entries)
                if self.selected_entries
                else [self.selected_index]
            )
            items_to_pick: list[Item] = []
            for index in indices:
                items_to_pick.extend(self.entries[index].items)
            return True, items_to_pick
        elif key == tcod.event.KeySym.ESCAPE:
            return True, None

        return False, None
