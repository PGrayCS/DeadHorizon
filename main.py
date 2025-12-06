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

    # Create the game instance
    game = Game(
        screen_width=screen_width,
        screen_height=screen_height,
        map_width=map_width,
        map_height=map_height,
        tileset_manager=tileset_manager,
    )

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
