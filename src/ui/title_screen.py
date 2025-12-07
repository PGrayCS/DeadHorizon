"""
Title Screen and Menu System
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Callable

import tcod.console
import tcod.event


class MenuState(Enum):
    """Current menu state."""
    TITLE = auto()
    MAIN_MENU = auto()
    OPTIONS = auto()
    CREDITS = auto()
    PLAYING = auto()
    QUIT = auto()


class MenuItem:
    """A selectable menu item."""

    def __init__(
        self,
        text: str,
        action: Callable[[], MenuState] | MenuState,
        enabled: bool = True,
    ) -> None:
        self.text = text
        self.action = action
        self.enabled = enabled


class TitleScreen:
    """
    Professional title screen with animated effects.
    """

    # Epic ASCII art logo
    LOGO = [
        " ____  _____    _    ____    _   _  ___  ____  ___ _____  ___  _   _ ",
        "|  _ \\| ____|  / \\  |  _ \\  | | | |/ _ \\|  _ \\|_ _|__  / / _ \\| \\ | |",
        "| | | |  _|   / _ \\ | | | | | |_| | | | | |_) || |  / / | | | |  \\| |",
        "| |_| | |___ / ___ \\| |_| | |  _  | |_| |  _ < | | / /_ | |_| | |\\  |",
        "|____/|_____/_/   \\_\\____/  |_| |_|\\___/|_| \\_\\___/____| \\___/|_| \\_|",
    ]

    SUBTITLE = "A Zombie Apocalypse Survival Roguelike"

    VERSION = "v0.2.0"

    # Atmospheric zombie silhouettes
    ZOMBIE_LEFT = [
        "    .--.",
        "   |o_o |",
        "   |:_/ |",
        "  //   \\ \\",
        " (|     | )",
        "/'\\_   _/`\\",
        "\\___)=(___/",
    ]

    ZOMBIE_RIGHT = [
        "    .--.",
        "   | o_o|",
        "   | \\_:|",
        "  / /   \\\\",
        " ( |     |)",
        "/`\\_   _/'\\",
        "\\___=(___/",
    ]

    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state = MenuState.TITLE
        self.selected_index = 0
        self.frame_count = 0

        # Main menu items
        self.main_menu_items = [
            MenuItem("NEW GAME", MenuState.PLAYING),
            MenuItem("CONTINUE", MenuState.PLAYING, enabled=False),
            MenuItem("OPTIONS", MenuState.OPTIONS),
            MenuItem("CREDITS", MenuState.CREDITS),
            MenuItem("QUIT", MenuState.QUIT),
        ]

        # Credits text
        self.credits_lines = [
            "",
            "========================================",
            "               CREDITS                 ",
            "========================================",
            "",
            "GAME DESIGN & PROGRAMMING",
            "PGrayCS",
            "",
            "TILESET",
            "DawnLike by DragonDePlatino",
            "(CC-BY 4.0)",
            "",
            "INSPIRED BY",
            "Cataclysm: Dark Days Ahead",
            "",
            "BUILT WITH",
            "Python + tcod",
            "",
            "========================================",
            "",
            "Press ESC to return",
        ]

    def handle_event(self, event: tcod.event.Event) -> MenuState:
        """Handle input events and return new state."""
        if isinstance(event, tcod.event.KeyDown):
            if self.state == MenuState.TITLE:
                # Any key advances from title to main menu
                self.state = MenuState.MAIN_MENU
                return self.state

            elif self.state == MenuState.MAIN_MENU:
                return self._handle_main_menu(event)

            elif self.state == MenuState.CREDITS:
                if event.sym == tcod.event.KeySym.ESCAPE:
                    self.state = MenuState.MAIN_MENU
                return self.state

            elif self.state == MenuState.OPTIONS:
                if event.sym == tcod.event.KeySym.ESCAPE:
                    self.state = MenuState.MAIN_MENU
                return self.state

        return self.state

    def _handle_main_menu(self, event: tcod.event.KeyDown) -> MenuState:
        """Handle main menu navigation."""
        if event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.w):
            # Move selection up
            self.selected_index -= 1
            if self.selected_index < 0:
                self.selected_index = len(self.main_menu_items) - 1
            # Skip disabled items
            while not self.main_menu_items[self.selected_index].enabled:
                self.selected_index -= 1
                if self.selected_index < 0:
                    self.selected_index = len(self.main_menu_items) - 1

        elif event.sym in (tcod.event.KeySym.DOWN, tcod.event.KeySym.s):
            # Move selection down
            self.selected_index += 1
            if self.selected_index >= len(self.main_menu_items):
                self.selected_index = 0
            # Skip disabled items
            while not self.main_menu_items[self.selected_index].enabled:
                self.selected_index += 1
                if self.selected_index >= len(self.main_menu_items):
                    self.selected_index = 0

        elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER, tcod.event.KeySym.SPACE):
            # Select current item
            item = self.main_menu_items[self.selected_index]
            if item.enabled:
                if isinstance(item.action, MenuState):
                    self.state = item.action
                else:
                    self.state = item.action()

        elif event.sym == tcod.event.KeySym.ESCAPE:
            self.state = MenuState.QUIT

        return self.state

    def render(self, console: tcod.console.Console) -> None:
        """Render the current menu state."""
        console.clear()
        self.frame_count += 1

        if self.state == MenuState.TITLE:
            self._render_title_screen(console)
        elif self.state == MenuState.MAIN_MENU:
            self._render_main_menu(console)
        elif self.state == MenuState.CREDITS:
            self._render_credits(console)
        elif self.state == MenuState.OPTIONS:
            self._render_options(console)

    def _render_title_screen(self, console: tcod.console.Console) -> None:
        """Render the animated title screen."""
        # Dark atmospheric background
        console.draw_rect(0, 0, self.screen_width, self.screen_height, ord(" "), bg=(5, 5, 10))

        # Draw zombie silhouettes on sides (subtle pulsing)
        zombie_y = self.screen_height - len(self.ZOMBIE_LEFT) - 3
        pulse = abs((self.frame_count // 8) % 30 - 15) + 25

        for i, line in enumerate(self.ZOMBIE_LEFT):
            console.print(3, zombie_y + i, line, fg=(pulse, pulse + 5, pulse))

        for i, line in enumerate(self.ZOMBIE_RIGHT):
            console.print(self.screen_width - len(line) - 3, zombie_y + i, line, fg=(pulse, pulse + 5, pulse))

        # Draw the main logo with color gradient and pulse
        logo_y = 10
        for i, line in enumerate(self.LOGO):
            x = (self.screen_width - len(line)) // 2

            # Red to orange gradient based on line
            base_r = 255 - i * 20
            base_g = 60 + i * 25
            base_b = 40

            # Pulsing glow effect
            glow = abs((self.frame_count // 4) % 20 - 10)
            r = min(255, base_r + glow * 2)
            g = min(255, base_g + glow)

            console.print(x, logo_y + i, line, fg=(r, g, base_b))

        # Decorative line under logo
        line_y = logo_y + len(self.LOGO) + 1
        deco_line = "~" * 50
        console.print((self.screen_width - len(deco_line)) // 2, line_y, deco_line, fg=(80, 40, 40))

        # Subtitle
        subtitle_y = line_y + 2
        console.print(
            (self.screen_width - len(self.SUBTITLE)) // 2,
            subtitle_y,
            self.SUBTITLE,
            fg=(180, 180, 190)
        )

        # Blinking "Press any key" text
        press_text = "[ Press any key to start ]"
        if (self.frame_count // 25) % 2 == 0:
            fg = (220, 200, 100)
        else:
            fg = (150, 130, 60)
        console.print(
            (self.screen_width - len(press_text)) // 2,
            subtitle_y + 5,
            press_text,
            fg=fg
        )

        # Version in corner
        console.print(self.screen_width - len(self.VERSION) - 2, self.screen_height - 2, self.VERSION, fg=(60, 60, 70))

        # Copyright
        copyright_text = "(c) 2025 PGrayCS"
        console.print(2, self.screen_height - 2, copyright_text, fg=(60, 60, 70))

        # Decorative corners
        console.print(1, 1, "+", fg=(60, 40, 40))
        console.print(self.screen_width - 2, 1, "+", fg=(60, 40, 40))
        console.print(1, self.screen_height - 1, "+", fg=(60, 40, 40))
        console.print(self.screen_width - 2, self.screen_height - 1, "+", fg=(60, 40, 40))

    def _render_main_menu(self, console: tcod.console.Console) -> None:
        """Render the main menu."""
        # Dark background
        console.draw_rect(0, 0, self.screen_width, self.screen_height, ord(" "), bg=(5, 5, 10))

        # Smaller logo at top
        logo_y = 5
        for i, line in enumerate(self.LOGO):
            x = (self.screen_width - len(line)) // 2
            r = 180 - i * 15
            g = 50 + i * 15
            console.print(x, logo_y + i, line, fg=(r, g, 40))

        # Menu box
        menu_y = logo_y + len(self.LOGO) + 4
        box_width = 36
        box_height = len(self.main_menu_items) * 2 + 3
        box_x = (self.screen_width - box_width) // 2

        # Draw box border
        self._draw_box(console, box_x, menu_y, box_width, box_height)

        # Menu title
        title = " MAIN MENU "
        console.print((self.screen_width - len(title)) // 2, menu_y, title, fg=(200, 180, 100))

        # Menu items
        item_y = menu_y + 2
        for i, item in enumerate(self.main_menu_items):
            y = item_y + i * 2

            if i == self.selected_index:
                # Selected item - highlighted with animation
                pulse = abs((self.frame_count // 3) % 16 - 8)
                bg_color = (50 + pulse * 2, 25, 25)
                fg_color = (255, 230, 120)

                # Draw highlight bar
                console.draw_rect(box_x + 1, y, box_width - 2, 1, ord(" "), bg=bg_color)

                # Draw selection indicators
                arrow = ">>" if (self.frame_count // 8) % 2 == 0 else "> "
                console.print(box_x + 3, y, arrow, fg=fg_color, bg=bg_color)
                console.print(box_x + box_width - 5, y, arrow[::-1], fg=fg_color, bg=bg_color)

                # Draw text centered
                text_x = (self.screen_width - len(item.text)) // 2
                console.print(text_x, y, item.text, fg=fg_color, bg=bg_color)
            else:
                # Unselected item
                if item.enabled:
                    fg_color = (140, 140, 150)
                else:
                    fg_color = (50, 50, 60)  # Disabled - grayed out

                text_x = (self.screen_width - len(item.text)) // 2
                console.print(text_x, y, item.text, fg=fg_color)

        # Controls hint at bottom
        hint = "[W/S or UP/DOWN] Navigate   [ENTER] Select   [ESC] Quit"
        console.print((self.screen_width - len(hint)) // 2, self.screen_height - 4, hint, fg=(70, 70, 90))

        # Version
        console.print(self.screen_width - len(self.VERSION) - 2, self.screen_height - 2, self.VERSION, fg=(50, 50, 60))

    def _render_credits(self, console: tcod.console.Console) -> None:
        """Render the credits screen."""
        console.draw_rect(0, 0, self.screen_width, self.screen_height, ord(" "), bg=(5, 5, 10))

        start_y = 6
        for i, line in enumerate(self.credits_lines):
            x = (self.screen_width - len(line)) // 2

            # Color coding
            if "=" in line:
                fg = (80, 80, 100)
            elif line in ("GAME DESIGN & PROGRAMMING", "TILESET", "INSPIRED BY", "BUILT WITH"):
                fg = (200, 160, 100)
            elif line == "Press ESC to return":
                if (self.frame_count // 25) % 2 == 0:
                    fg = (200, 200, 100)
                else:
                    fg = (100, 100, 60)
            elif line in ("PGrayCS", "DawnLike by DragonDePlatino", "Cataclysm: Dark Days Ahead", "Python + tcod"):
                fg = (180, 200, 220)
            else:
                fg = (150, 150, 160)

            console.print(x, start_y + i, line, fg=fg)

    def _render_options(self, console: tcod.console.Console) -> None:
        """Render the options screen (placeholder)."""
        console.draw_rect(0, 0, self.screen_width, self.screen_height, ord(" "), bg=(5, 5, 10))

        # Box
        box_x = (self.screen_width - 40) // 2
        box_y = 12
        self._draw_box(console, box_x, box_y, 40, 10)

        title = " OPTIONS "
        console.print((self.screen_width - len(title)) // 2, box_y, title, fg=(200, 160, 100))

        msg = "Coming soon..."
        console.print((self.screen_width - len(msg)) // 2, box_y + 4, msg, fg=(140, 140, 150))

        hint = "Press ESC to return"
        if (self.frame_count // 25) % 2 == 0:
            console.print((self.screen_width - len(hint)) // 2, box_y + 7, hint, fg=(200, 200, 100))

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
