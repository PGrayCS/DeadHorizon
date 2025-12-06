"""
TilesetManager - Handles loading and managing tilesets
"""

from __future__ import annotations

from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import tcod.tileset

if TYPE_CHECKING:
    from numpy.typing import NDArray


class GraphicsMode(Enum):
    """Graphics rendering mode."""
    ASCII = auto()
    TILES = auto()


class TilesetManager:
    """
    Manages tileset loading, sprite extraction, and tile mapping.
    
    Uses Unicode Private Use Area (PUA) starting at 0xE000 for custom tiles.
    """
    
    # PUA starting codepoints for different categories
    PUA_TERRAIN_START = 0xE000    # 0xE000 - 0xE0FF (256 terrain tiles)
    PUA_PLAYER_START = 0xE100     # 0xE100 - 0xE10F (16 player sprites)
    PUA_MONSTER_START = 0xE110    # 0xE110 - 0xE1FF (240 monster sprites)
    PUA_ITEM_START = 0xE200       # 0xE200 - 0xE2FF (256 item sprites)
    PUA_UI_START = 0xE300         # 0xE300 - 0xE3FF (256 UI elements)
    
    TILE_SIZE = 16  # DawnLike uses 16x16 tiles
    
    def __init__(self, assets_path: str | Path = "assets/tilesets/dawnlike") -> None:
        self.assets_path = Path(assets_path)
        self.tileset: tcod.tileset.Tileset | None = None
        self.mode = GraphicsMode.ASCII
        
        # Track assigned codepoints
        self._terrain_codepoints: dict[str, int] = {}
        self._player_codepoints: dict[str, int] = {}
        self._monster_codepoints: dict[str, int] = {}
        self._item_codepoints: dict[str, int] = {}
        
        # Counters for next available codepoint
        self._next_terrain = self.PUA_TERRAIN_START
        self._next_player = self.PUA_PLAYER_START
        self._next_monster = self.PUA_MONSTER_START
        self._next_item = self.PUA_ITEM_START
    
    def load_tileset(self) -> tcod.tileset.Tileset:
        """
        Load the DawnLike tileset and create mappings.
        
        Returns the configured tileset ready for use with tcod.context.
        """
        # Create a tileset with 16x16 tile size
        self.tileset = tcod.tileset.Tileset(self.TILE_SIZE, self.TILE_SIZE)
        
        # Load base ASCII font first (for fallback characters)
        self._load_ascii_base()
        
        # Check if DawnLike assets exist
        if self.assets_path.exists():
            try:
                self._load_terrain_tiles()
                self._load_character_tiles()
                self._load_item_tiles()
                self.mode = GraphicsMode.TILES
                print(f"Loaded DawnLike tileset from {self.assets_path}")
            except Exception as e:
                print(f"Warning: Could not load DawnLike tileset: {e}")
                print("Falling back to ASCII mode")
                self.mode = GraphicsMode.ASCII
        else:
            print(f"DawnLike assets not found at {self.assets_path}")
            print("Using ASCII mode. Download DawnLike for graphics.")
            self.mode = GraphicsMode.ASCII
        
        return self.tileset
    
    def _load_ascii_base(self) -> None:
        """Load a base font for ASCII characters."""
        # Use Windows Consolas for ASCII fallback
        try:
            base_tileset = tcod.tileset.load_truetype_font(
                "C:/Windows/Fonts/consola.ttf",
                tile_width=self.TILE_SIZE,
                tile_height=self.TILE_SIZE,
            )
            # Copy ASCII characters to our tileset
            for codepoint in range(32, 127):  # Printable ASCII
                try:
                    tile = base_tileset.get_tile(codepoint)
                    if tile is not None:
                        self.tileset.set_tile(codepoint, tile)
                except Exception:
                    pass
        except Exception as e:
            print(f"Warning: Could not load base font: {e}")
    
    def _load_terrain_tiles(self) -> None:
        """Load terrain tiles (floor, wall, etc.)."""
        objects_path = self.assets_path / "Objects"
        
        # Load floor tiles
        floor_path = objects_path / "Floor.png"
        if floor_path.exists():
            sheet = self._load_sheet(floor_path)
            # Floor.png is 336x624 - 21 tiles wide, 39 tiles tall
            # First row has various floor types
            self._assign_terrain_tile("floor", sheet, 1, 1)
            self._assign_terrain_tile("floor_alt", sheet, 2, 1)
        
        # Load wall tiles
        wall_path = objects_path / "Wall.png"
        if wall_path.exists():
            sheet = self._load_sheet(wall_path)
            # Wall.png is 320x816 - 20 tiles wide
            # Use a solid wall tile
            self._assign_terrain_tile("wall", sheet, 0, 1)
            self._assign_terrain_tile("wall_alt", sheet, 1, 1)
        
        # Load door tiles
        door_path = objects_path / "Door0.png"
        if door_path.exists():
            sheet = self._load_sheet(door_path)
            # Door0.png is 128x80 - 8 tiles wide, 5 tiles tall
            self._assign_terrain_tile("door_closed", sheet, 0, 0)
            self._assign_terrain_tile("door_open", sheet, 3, 0)
    
    def _load_character_tiles(self) -> None:
        """Load character sprites (player, monsters)."""
        chars_path = self.assets_path / "Characters"
        
        # Load player sprite
        player_path = chars_path / "Player0.png"
        if player_path.exists():
            sheet = self._load_sheet(player_path)
            # Player0.png has various player sprites
            self._assign_player_tile("player", sheet, 0, 0)
            self._assign_player_tile("player_alt", sheet, 1, 0)
        
        # Load undead/zombie sprites
        undead_path = chars_path / "Undead0.png"
        if undead_path.exists():
            sheet = self._load_sheet(undead_path)
            # Undead0.png has zombie/skeleton sprites
            self._assign_monster_tile("zombie", sheet, 0, 0)
            self._assign_monster_tile("zombie_fast", sheet, 1, 0)
            self._assign_monster_tile("zombie_brute", sheet, 2, 0)
            self._assign_monster_tile("skeleton", sheet, 4, 0)
            self._assign_monster_tile("crawler", sheet, 3, 0)
    
    def _load_item_tiles(self) -> None:
        """Load item sprites (weapons, food, etc.)."""
        items_path = self.assets_path / "Items"
        
        # Load weapon sprites - try different weapon files
        for weapon_file in ["MedWep.png", "ShortWep.png", "LongWep.png"]:
            weapon_path = items_path / weapon_file
            if weapon_path.exists():
                sheet = self._load_sheet(weapon_path)
                self._assign_item_tile("weapon", sheet, 0, 0)
                break
        
        # Load food sprites
        food_path = items_path / "Food.png"
        if food_path.exists():
            sheet = self._load_sheet(food_path)
            self._assign_item_tile("food", sheet, 0, 0)
    
    def _load_sheet(self, path: Path) -> NDArray[np.uint8]:
        """Load a PNG spritesheet as a numpy array."""
        import PIL.Image
        
        with PIL.Image.open(path) as img:
            # Convert to RGBA if needed (handles palette mode 'P')
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            return np.array(img)
    
    def _extract_tile(self, sheet: NDArray[np.uint8], tile_x: int, tile_y: int) -> NDArray[np.uint8]:
        """Extract a single 16x16 tile from a spritesheet."""
        x = tile_x * self.TILE_SIZE
        y = tile_y * self.TILE_SIZE
        
        # Check bounds
        sheet_h, sheet_w = sheet.shape[:2]
        if x + self.TILE_SIZE > sheet_w or y + self.TILE_SIZE > sheet_h:
            # Out of bounds - return a default colored tile
            print(f"Warning: Tile ({tile_x}, {tile_y}) out of bounds for sheet {sheet_w}x{sheet_h}")
            default = np.zeros((self.TILE_SIZE, self.TILE_SIZE, 4), dtype=np.uint8)
            default[:, :, 3] = 255  # Opaque
            return default
        
        return sheet[y:y + self.TILE_SIZE, x:x + self.TILE_SIZE].copy()
    
    def _assign_terrain_tile(self, name: str, sheet: NDArray[np.uint8], tile_x: int, tile_y: int) -> int:
        """Assign a terrain tile to a PUA codepoint."""
        codepoint = self._next_terrain
        self._next_terrain += 1
        
        tile = self._extract_tile(sheet, tile_x, tile_y)
        self.tileset.set_tile(codepoint, tile)
        self._terrain_codepoints[name] = codepoint
        
        return codepoint
    
    def _assign_player_tile(self, name: str, sheet: NDArray[np.uint8], tile_x: int, tile_y: int) -> int:
        """Assign a player tile to a PUA codepoint."""
        codepoint = self._next_player
        self._next_player += 1
        
        tile = self._extract_tile(sheet, tile_x, tile_y)
        self.tileset.set_tile(codepoint, tile)
        self._player_codepoints[name] = codepoint
        
        return codepoint
    
    def _assign_monster_tile(self, name: str, sheet: NDArray[np.uint8], tile_x: int, tile_y: int) -> int:
        """Assign a monster tile to a PUA codepoint."""
        codepoint = self._next_monster
        self._next_monster += 1
        
        tile = self._extract_tile(sheet, tile_x, tile_y)
        self.tileset.set_tile(codepoint, tile)
        self._monster_codepoints[name] = codepoint
        
        return codepoint
    
    def _assign_item_tile(self, name: str, sheet: NDArray[np.uint8], tile_x: int, tile_y: int) -> int:
        """Assign an item tile to a PUA codepoint."""
        codepoint = self._next_item
        self._next_item += 1
        
        tile = self._extract_tile(sheet, tile_x, tile_y)
        self.tileset.set_tile(codepoint, tile)
        self._item_codepoints[name] = codepoint
        
        return codepoint
    
    # Public API for getting tile codepoints
    
    def get_terrain_tile(self, name: str) -> int | None:
        """Get codepoint for a terrain tile by name."""
        return self._terrain_codepoints.get(name)
    
    def get_player_tile(self, name: str = "player") -> int | None:
        """Get codepoint for a player tile by name."""
        return self._player_codepoints.get(name)
    
    def get_monster_tile(self, name: str) -> int | None:
        """Get codepoint for a monster tile by name."""
        return self._monster_codepoints.get(name)
    
    def get_item_tile(self, name: str) -> int | None:
        """Get codepoint for an item tile by name."""
        return self._item_codepoints.get(name)
    
    def toggle_mode(self) -> GraphicsMode:
        """Toggle between ASCII and TILES mode."""
        if self.mode == GraphicsMode.ASCII:
            # Only switch to tiles if we have tiles loaded
            if self._terrain_codepoints:
                self.mode = GraphicsMode.TILES
        else:
            self.mode = GraphicsMode.ASCII
        return self.mode
    
    @property
    def is_tiles_mode(self) -> bool:
        """Return True if currently in tiles mode."""
        return self.mode == GraphicsMode.TILES
