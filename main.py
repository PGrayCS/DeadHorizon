#!/usr/bin/env python3
"""
Dead Horizon - A Zombie Apocalypse Survival Roguelike
Main entry point
"""

import os
import sys
from pathlib import Path

import tcod.tileset
import tcod.context
import tcod.console
import tcod.event

from src.engine.game import Game
from src.graphics.tileset_manager import TilesetManager
from src.ui.title_screen import TitleScreen, MenuState
from src.ui.character_creation import CharacterCreation, CreationState


def main() -> None:
    """Main entry point for Dead Horizon."""

    # Get the directory where this script is located
    script_dir = Path(__file__).parent.resolve()

    # Change to script directory so relative paths work
    os.chdir(script_dir)

    # Screen dimensions (in tiles)
    screen_width = 80
    screen_height = 50

    # Map dimensions
    map_width = 80
    map_height = 43

    # Initialize tileset manager with absolute path
    assets_path = script_dir / "assets" / "tilesets" / "dawnlike"
    tileset_manager = TilesetManager(assets_path=assets_path)
    tileset = tileset_manager.load_tileset()

    # Force tiles mode (no ASCII fallback)
    if not tileset_manager.is_tiles_mode:
        print("ERROR: Could not load DawnLike tileset!")
        print(f"Expected at: {assets_path}")
        print("Please ensure DawnLike tileset is installed.")
        sys.exit(1)

    # Create the main window
    with tcod.context.new(
        columns=screen_width,
        rows=screen_height,
        tileset=tileset,
        title="Dead Horizon",
        vsync=True,
    ) as context:

        # Create the root console
        root_console = tcod.console.Console(screen_width, screen_height, order="F")

        # Create title screen
        title_screen = TitleScreen(screen_width, screen_height)

        # Title screen / menu loop
        while title_screen.state not in (MenuState.PLAYING, MenuState.CONTINUE, MenuState.QUIT):
            root_console.clear()
            title_screen.render(root_console)
            context.present(root_console)

            for event in tcod.event.wait():
                context.convert_event(event)

                if isinstance(event, tcod.event.Quit):
                    raise SystemExit()

                title_screen.handle_event(event)

        # Check if user quit from menu
        if title_screen.state == MenuState.QUIT:
            raise SystemExit()

        # Check if continuing from save
        if title_screen.state == MenuState.CONTINUE:
            # Load saved game - skip character creation
            from src.engine.save_system import load_game

            game = Game(
                screen_width=screen_width,
                screen_height=screen_height,
                map_width=map_width,
                map_height=map_height,
                tileset_manager=tileset_manager,
            )
            if not load_game(game):
                print("ERROR: Failed to load save file!")
                raise SystemExit()
            game.add_message("Welcome back!", (100, 255, 100))
        else:
            # === NEW GAME - CHARACTER CREATION ===
            char_creation = CharacterCreation(screen_width, screen_height)

            while char_creation.state != CreationState.DONE:
                root_console.clear()
                char_creation.render(root_console)
                context.present(root_console)

                for event in tcod.event.wait():
                    context.convert_event(event)

                    if isinstance(event, tcod.event.Quit):
                        raise SystemExit()

                    char_creation.handle_event(event)

            # Get the configured character
            player_name, player_stats = char_creation.get_player_stats()

            # Create the game instance with custom character
            game = Game(
                screen_width=screen_width,
                screen_height=screen_height,
                map_width=map_width,
                map_height=map_height,
                tileset_manager=tileset_manager,
                player_name=player_name,
                player_stats=player_stats,
            )

        # Main game loop
        while True:
            # Clear the console
            root_console.clear()

            # Render the game
            game.render(root_console)

            # Present the console to the screen
            context.present(root_console)

            # Handle events
            for event in tcod.event.wait():
                context.convert_event(event)

                if isinstance(event, tcod.event.Quit):
                    raise SystemExit()

                # Handle input
                action = game.handle_event(event)

                if action == "quit":
                    raise SystemExit()


if __name__ == "__main__":
    main()
