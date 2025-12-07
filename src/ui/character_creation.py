"""
Character Creation Screen
Allows players to allocate stat points before starting a run
"""

from __future__ import annotations

from enum import Enum, auto
from dataclasses import dataclass

import tcod.console
import tcod.event

from src.entities.player import PlayerStats


class CreationState(Enum):
    """Current state of character creation."""
    NAMING = auto()
    STATS = auto()
    CONFIRM = auto()
    DONE = auto()


@dataclass
class StatInfo:
    """Information about a stat for display."""
    name: str
    short: str
    description: str
    color: tuple[int, int, int]


STAT_INFO = {
    "strength": StatInfo(
        "Strength", "STR",
        "Melee damage. +1 ATK per point.",
        (255, 100, 100)
    ),
    "agility": StatInfo(
        "Agility", "AGI",
        "Dodge & crit chance. +1% crit, +2% dodge per point.",
        (100, 255, 100)
    ),
    "vitality": StatInfo(
        "Vitality", "VIT",
        "Health pool. +4 HP per point.",
        (255, 100, 255)
    ),
    "endurance": StatInfo(
        "Endurance", "END",
        "Defense & stamina. +0.5 DEF per point.",
        (100, 200, 255)
    ),
    "perception": StatInfo(
        "Perception", "PER",
        "Vision & accuracy. +2% accuracy, +0.5 FOV per point.",
        (255, 255, 100)
    ),
}

STAT_ORDER = ["strength", "agility", "vitality", "endurance", "perception"]


class CharacterCreation:
    """
    Character creation screen with stat allocation.
    """

    # Starting points to allocate
    STARTING_POINTS = 25
    MIN_STAT = 1
    MAX_STAT = 10

    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state = CreationState.NAMING

        # Character name
        self.name = ""
        self.max_name_length = 20

        # Stats - start with 5 in each
        self.stats = PlayerStats(
            strength=5,
            agility=5,
            vitality=5,
            endurance=5,
            perception=5,
        )

        # Current selection
        self.selected_stat_index = 0

        # Points remaining
        self.points_remaining = self.STARTING_POINTS - self.stats.total_points

        # Animation
        self.frame_count = 0

    def get_player_stats(self) -> tuple[str, PlayerStats]:
        """Return the configured name and stats."""
        return self.name if self.name else "Survivor", self.stats

    def handle_event(self, event: tcod.event.Event) -> CreationState:
        """Handle input events."""
        if isinstance(event, tcod.event.KeyDown):
            if self.state == CreationState.NAMING:
                return self._handle_naming(event)
            elif self.state == CreationState.STATS:
                return self._handle_stats(event)
            elif self.state == CreationState.CONFIRM:
                return self._handle_confirm(event)

        return self.state

    def _handle_naming(self, event: tcod.event.KeyDown) -> CreationState:
        """Handle name input."""
        if event.sym == tcod.event.KeySym.RETURN:
            if not self.name:
                self.name = "Survivor"
            self.state = CreationState.STATS
        elif event.sym == tcod.event.KeySym.BACKSPACE:
            self.name = self.name[:-1]
        elif event.sym == tcod.event.KeySym.ESCAPE:
            # Skip to default
            self.name = "Survivor"
            self.state = CreationState.STATS
        else:
            # Add character if printable
            char = event.sym.name if len(event.sym.name) == 1 else ""
            if char and len(self.name) < self.max_name_length:
                # Handle shift for uppercase
                if event.mod & tcod.event.KMOD_SHIFT:
                    char = char.upper()
                else:
                    char = char.lower()
                self.name += char

        return self.state

    def _handle_stats(self, event: tcod.event.KeyDown) -> CreationState:
        """Handle stat allocation."""
        if event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.w):
            self.selected_stat_index = (self.selected_stat_index - 1) % len(STAT_ORDER)

        elif event.sym in (tcod.event.KeySym.DOWN, tcod.event.KeySym.s):
            self.selected_stat_index = (self.selected_stat_index + 1) % len(STAT_ORDER)

        elif event.sym in (tcod.event.KeySym.RIGHT, tcod.event.KeySym.d, tcod.event.KeySym.PLUS, tcod.event.KeySym.KP_PLUS):
            self._adjust_stat(1)

        elif event.sym in (tcod.event.KeySym.LEFT, tcod.event.KeySym.a, tcod.event.KeySym.MINUS, tcod.event.KeySym.KP_MINUS):
            self._adjust_stat(-1)

        elif event.sym == tcod.event.KeySym.RETURN:
            self.state = CreationState.CONFIRM

        elif event.sym == tcod.event.KeySym.r:
            # Reset to default
            self.stats = PlayerStats(5, 5, 5, 5, 5)
            self.points_remaining = self.STARTING_POINTS - self.stats.total_points

        elif event.sym == tcod.event.KeySym.ESCAPE:
            self.state = CreationState.NAMING

        return self.state

    def _handle_confirm(self, event: tcod.event.KeyDown) -> CreationState:
        """Handle confirmation screen."""
        if event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.y):
            self.state = CreationState.DONE
        elif event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.n):
            self.state = CreationState.STATS

        return self.state

    def _adjust_stat(self, delta: int) -> None:
        """Adjust the selected stat by delta."""
        stat_name = STAT_ORDER[self.selected_stat_index]
        current_value = getattr(self.stats, stat_name)
        new_value = current_value + delta

        # Check bounds
        if new_value < self.MIN_STAT or new_value > self.MAX_STAT:
            return

        # Check points
        if delta > 0 and self.points_remaining <= 0:
            return

        # Apply change
        setattr(self.stats, stat_name, new_value)
        self.points_remaining = self.STARTING_POINTS - self.stats.total_points

    def render(self, console: tcod.console.Console) -> None:
        """Render the character creation screen."""
        console.clear()
        self.frame_count += 1

        # Dark background
        console.draw_rect(0, 0, self.screen_width, self.screen_height, ord(" "), bg=(5, 5, 10))

        if self.state == CreationState.NAMING:
            self._render_naming(console)
        elif self.state == CreationState.STATS:
            self._render_stats(console)
        elif self.state == CreationState.CONFIRM:
            self._render_confirm(console)

    def _render_naming(self, console: tcod.console.Console) -> None:
        """Render the name input screen."""
        # Title
        title = "CREATE YOUR SURVIVOR"
        console.print((self.screen_width - len(title)) // 2, 8, title, fg=(255, 200, 100))

        # Decorative line
        line = "~" * 30
        console.print((self.screen_width - len(line)) // 2, 10, line, fg=(80, 80, 100))

        # Name prompt
        prompt = "Enter your name:"
        console.print((self.screen_width - len(prompt)) // 2, 15, prompt, fg=(200, 200, 200))

        # Name input box
        box_width = self.max_name_length + 4
        box_x = (self.screen_width - box_width) // 2
        self._draw_box(console, box_x, 17, box_width, 3)

        # Name text with cursor
        display_name = self.name
        if (self.frame_count // 15) % 2 == 0:
            display_name += "_"
        console.print(box_x + 2, 18, display_name, fg=(255, 255, 255))

        # Instructions
        inst = "[ENTER] Continue   [ESC] Use default name"
        console.print((self.screen_width - len(inst)) // 2, 25, inst, fg=(100, 100, 120))

    def _render_stats(self, console: tcod.console.Console) -> None:
        """Render the stat allocation screen."""
        # Title
        title = f"CHARACTER: {self.name.upper()}"
        console.print((self.screen_width - len(title)) // 2, 3, title, fg=(255, 200, 100))

        # Points remaining
        points_color = (100, 255, 100) if self.points_remaining > 0 else (255, 100, 100)
        if self.points_remaining == 0:
            points_color = (200, 200, 200)
        points_text = f"Points Remaining: {self.points_remaining}"
        console.print((self.screen_width - len(points_text)) // 2, 5, points_text, fg=points_color)

        # Stats box
        box_x = 15
        box_y = 8
        box_width = 50
        box_height = 17
        self._draw_box(console, box_x, box_y, box_width, box_height)

        # Column headers
        console.print(box_x + 3, box_y + 2, "STAT", fg=(150, 150, 150))
        console.print(box_x + 20, box_y + 2, "VALUE", fg=(150, 150, 150))
        console.print(box_x + 30, box_y + 2, "EFFECT", fg=(150, 150, 150))

        # Render each stat
        for i, stat_name in enumerate(STAT_ORDER):
            y = box_y + 4 + i * 2
            info = STAT_INFO[stat_name]
            value = getattr(self.stats, stat_name)

            # Highlight selected
            is_selected = i == self.selected_stat_index
            if is_selected:
                # Draw selection bar
                pulse = abs((self.frame_count // 3) % 16 - 8)
                console.draw_rect(box_x + 1, y, box_width - 2, 1, ord(" "), bg=(30 + pulse, 20, 20))

            # Stat name
            name_color = info.color if is_selected else (info.color[0] // 2, info.color[1] // 2, info.color[2] // 2)
            console.print(box_x + 3, y, info.name, fg=name_color)

            # Value with arrows if selected
            if is_selected:
                # Left arrow (if can decrease)
                if value > self.MIN_STAT:
                    console.print(box_x + 18, y, "<", fg=(200, 200, 200))
                # Right arrow (if can increase)
                if value < self.MAX_STAT and self.points_remaining > 0:
                    console.print(box_x + 26, y, ">", fg=(200, 200, 200))

            # Value bar
            bar_color = info.color
            for j in range(self.MAX_STAT):
                char = "#" if j < value else "-"
                color = bar_color if j < value else (40, 40, 40)
                console.print(box_x + 20 + j, y, char, fg=color)

            # Derived stat preview
            effect_text = self._get_effect_preview(stat_name, value)
            console.print(box_x + 32, y, effect_text, fg=(150, 150, 150))

        # Selected stat description
        selected_info = STAT_INFO[STAT_ORDER[self.selected_stat_index]]
        desc_y = box_y + box_height + 1
        console.print(box_x, desc_y, selected_info.description, fg=selected_info.color)

        # Final stats preview
        preview_y = desc_y + 3
        console.print(box_x, preview_y, "CALCULATED STATS:", fg=(200, 200, 100))
        console.print(box_x, preview_y + 1, f"HP: {self.stats.get_max_hp()}", fg=(255, 100, 100))
        console.print(box_x + 12, preview_y + 1, f"ATK: {self.stats.get_attack()}", fg=(255, 180, 100))
        console.print(box_x + 24, preview_y + 1, f"DEF: {self.stats.get_defense()}", fg=(100, 180, 255))
        console.print(box_x + 36, preview_y + 1, f"CRIT: {self.stats.get_crit_chance()}%", fg=(255, 255, 100))

        # Instructions
        inst1 = "[W/S] Select   [A/D] Adjust   [R] Reset"
        inst2 = "[ENTER] Confirm   [ESC] Back"
        console.print((self.screen_width - len(inst1)) // 2, self.screen_height - 5, inst1, fg=(100, 100, 120))
        console.print((self.screen_width - len(inst2)) // 2, self.screen_height - 4, inst2, fg=(100, 100, 120))

    def _render_confirm(self, console: tcod.console.Console) -> None:
        """Render the confirmation screen."""
        # Title
        title = "CONFIRM CHARACTER"
        console.print((self.screen_width - len(title)) // 2, 8, title, fg=(255, 200, 100))

        # Character summary box
        box_x = 20
        box_y = 12
        box_width = 40
        box_height = 16
        self._draw_box(console, box_x, box_y, box_width, box_height)

        # Name
        console.print(box_x + 3, box_y + 2, f"Name: {self.name}", fg=(255, 255, 255))

        # Stats
        y = box_y + 4
        for stat_name in STAT_ORDER:
            info = STAT_INFO[stat_name]
            value = getattr(self.stats, stat_name)
            console.print(box_x + 3, y, f"{info.short}: {value}", fg=info.color)
            y += 1

        # Derived stats
        y += 1
        console.print(box_x + 3, y, "---", fg=(80, 80, 80))
        y += 1
        console.print(box_x + 3, y, f"Max HP: {self.stats.get_max_hp()}", fg=(255, 100, 100))
        console.print(box_x + 20, y, f"Attack: {self.stats.get_attack()}", fg=(255, 180, 100))
        y += 1
        console.print(box_x + 3, y, f"Defense: {self.stats.get_defense()}", fg=(100, 180, 255))
        console.print(box_x + 20, y, f"Crit: {self.stats.get_crit_chance()}%", fg=(255, 255, 100))
        y += 1
        console.print(box_x + 3, y, f"FOV: {self.stats.get_fov_radius()}", fg=(200, 200, 100))

        # Confirmation prompt
        prompt = "Begin your survival?"
        console.print((self.screen_width - len(prompt)) // 2, box_y + box_height + 2, prompt, fg=(200, 200, 200))

        inst = "[ENTER/Y] Start   [ESC/N] Go Back"
        if (self.frame_count // 20) % 2 == 0:
            console.print((self.screen_width - len(inst)) // 2, box_y + box_height + 4, inst, fg=(200, 200, 100))

    def _get_effect_preview(self, stat_name: str, value: int) -> str:
        """Get a preview of what a stat does at current value."""
        if stat_name == "strength":
            return f"+{value} ATK"
        elif stat_name == "agility":
            return f"+{value}% crit"
        elif stat_name == "vitality":
            return f"+{value * 4} HP"
        elif stat_name == "endurance":
            return f"+{value // 2} DEF"
        elif stat_name == "perception":
            return f"+{value // 2} FOV"
        return ""

    def _draw_box(self, console: tcod.console.Console, x: int, y: int, width: int, height: int) -> None:
        """Draw a decorative box."""
        fg = (80, 80, 100)

        # Corners
        console.print(x, y, "+", fg=fg)
        console.print(x + width - 1, y, "+", fg=fg)
        console.print(x, y + height - 1, "+", fg=fg)
        console.print(x + width - 1, y + height - 1, "+", fg=fg)

        # Horizontal lines
        for i in range(1, width - 1):
            console.print(x + i, y, "-", fg=fg)
            console.print(x + i, y + height - 1, "-", fg=fg)

        # Vertical lines
        for i in range(1, height - 1):
            console.print(x, y + i, "|", fg=fg)
            console.print(x + width - 1, y + i, "|", fg=fg)
