"""
Save/Load system - Persist game state to disk
Uses JSON for human-readable save files
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.engine.game import Game
    from src.entities.player import Player, PlayerStats
    from src.items.item import Item


# Default save directory
SAVE_DIR = Path.home() / ".deadhorizon" / "saves"


def get_save_path(slot: int = 0) -> Path:
    """Get the path for a save file."""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    return SAVE_DIR / f"save_{slot}.json"


def save_exists(slot: int = 0) -> bool:
    """Check if a save file exists."""
    return get_save_path(slot).exists()


def get_save_info(slot: int = 0) -> dict | None:
    """Get basic info about a save file without loading the full game."""
    path = get_save_path(slot)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "player_name": data.get("player", {}).get("name", "Unknown"),
                "level": data.get("player", {}).get("level", 1),
                "kills": data.get("kills", 0),
                "save_date": data.get("save_date", "Unknown"),
                "dungeon_level": data.get("dungeon_level", 1),
            }
    except (json.JSONDecodeError, KeyError):
        return None


def delete_save(slot: int = 0) -> bool:
    """Delete a save file."""
    path = get_save_path(slot)
    if path.exists():
        os.remove(path)
        return True
    return False


# =============================================================================
# SERIALIZATION - Convert game objects to JSON-compatible dicts
# =============================================================================

def serialize_item(item: "Item") -> dict:
    """Convert an Item to a JSON-serializable dict."""
    return {
        "name": item.name,
        "char": item.char,
        "color": list(item.color),
        "item_type": item.item_type.name,
        "description": item.description,
        "equip_slot": item.equip_slot.name,
        "stats": {
            "damage": item.stats.damage,
            "defense": item.stats.defense,
            "accuracy": item.stats.accuracy,
            "crit_bonus": item.stats.crit_bonus,
            "hp_restore": item.stats.hp_restore,
            "hunger_restore": item.stats.hunger_restore,
            "thirst_restore": item.stats.thirst_restore,
        },
        "stackable": item.stackable,
        "stack_size": item.stack_size,
        "max_stack": item.max_stack,
        "value": item.value,
        "weight": item.weight,
    }


def deserialize_item(data: dict) -> "Item":
    """Create an Item from a JSON dict."""
    from src.items.item import Item, ItemType, ItemStats, EquipSlot

    return Item(
        name=data["name"],
        char=data["char"],
        color=tuple(data["color"]),
        item_type=ItemType[data["item_type"]],
        description=data.get("description", ""),
        equip_slot=EquipSlot[data["equip_slot"]],
        stats=ItemStats(
            damage=data["stats"].get("damage", 0),
            defense=data["stats"].get("defense", 0),
            accuracy=data["stats"].get("accuracy", 0),
            crit_bonus=data["stats"].get("crit_bonus", 0),
            hp_restore=data["stats"].get("hp_restore", 0),
            hunger_restore=data["stats"].get("hunger_restore", 0),
            thirst_restore=data["stats"].get("thirst_restore", 0),
        ),
        stackable=data.get("stackable", False),
        stack_size=data.get("stack_size", 1),
        max_stack=data.get("max_stack", 1),
        value=data.get("value", 1),
        weight=data.get("weight", 1.0),
    )


def serialize_player(player: "Player") -> dict:
    """Convert Player to JSON-serializable dict."""
    return {
        "x": player.x,
        "y": player.y,
        "name": player.name,
        "hp": player.hp,
        "max_hp": player.max_hp,
        "hunger": player.hunger,
        "thirst": player.thirst,
        "level": player.level,
        "xp": player.xp,
        "xp_to_next_level": player.xp_to_next_level,
        "stats": {
            "strength": player.stats.strength,
            "agility": player.stats.agility,
            "vitality": player.stats.vitality,
            "endurance": player.stats.endurance,
            "perception": player.stats.perception,
        },
        "inventory": [serialize_item(item) for item in player.inventory],
        "equipped_weapon": serialize_item(player.equipped_weapon) if player.equipped_weapon else None,
        "equipped_armor": serialize_item(player.equipped_armor) if player.equipped_armor else None,
    }


def serialize_monster(monster) -> dict:
    """Convert Monster to JSON-serializable dict."""
    return {
        "x": monster.x,
        "y": monster.y,
        "zombie_type": monster.zombie_type.name,
        "hp": monster.hp,
        "max_hp": monster.max_hp,
    }


def serialize_ground_items(ground_items: dict) -> list:
    """Convert ground items dict to JSON-serializable list."""
    result = []
    for (x, y), items in ground_items.items():
        for item in items:
            result.append({
                "x": x,
                "y": y,
                "item": serialize_item(item),
            })
    return result


def serialize_map(game_map) -> dict:
    """Convert GameMap to JSON-serializable dict."""
    # Store walkable as a simple 2D list of bools
    walkable = [[bool(game_map.tiles[x, y]["walkable"]) for y in range(game_map.height)]
                for x in range(game_map.width)]
    explored = game_map.explored.tolist()

    return {
        "width": game_map.width,
        "height": game_map.height,
        "walkable": walkable,
        "explored": explored,
        "rooms": [
            {"x1": r.x1, "y1": r.y1, "x2": r.x2, "y2": r.y2}
            for r in getattr(game_map, "rooms", [])
        ],
    }


# =============================================================================
# SAVE GAME
# =============================================================================

def save_game(game: "Game", slot: int = 0) -> bool:
    """
    Save the current game state to a file.
    Returns True if successful.
    """
    try:
        # Collect monsters (non-player entities)
        monsters = [
            serialize_monster(e)
            for e in game.entities
            if e != game.player and hasattr(e, "zombie_type")
        ]

        save_data = {
            "version": "1.0",
            "save_date": datetime.now().isoformat(),
            "player": serialize_player(game.player),
            "monsters": monsters,
            "ground_items": serialize_ground_items(game.ground_items),
            "map": serialize_map(game.game_map),
            "kills": game.kills,
            "messages": game.messages[-20:],  # Keep last 20 messages
            "dungeon_level": getattr(game, "dungeon_level", 1),
        }

        path = get_save_path(slot)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2)

        return True
    except Exception as e:
        print(f"Save failed: {e}")
        return False


# =============================================================================
# LOAD GAME
# =============================================================================

def load_game(game: "Game", slot: int = 0) -> bool:  # pylint: disable=too-many-statements,too-many-locals
    """
    Load a saved game state from a file.
    Returns True if successful.
    """
    from src.entities.player import Player, PlayerStats
    from src.entities.monster import Monster, ZombieType
    from src.map.game_map import GameMap
    from src.map.procgen import RectangularRoom
    from src.map import tile as tile_types
    import numpy as np

    path = get_save_path(slot)
    if not path.exists():
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Restore player stats
        stats_data = data["player"]["stats"]
        player_stats = PlayerStats(
            strength=stats_data["strength"],
            agility=stats_data["agility"],
            vitality=stats_data["vitality"],
            endurance=stats_data["endurance"],
            perception=stats_data["perception"],
        )

        # Restore map
        map_data = data["map"]
        game.game_map = GameMap(map_data["width"], map_data["height"])

        # Rebuild tiles from walkable data
        walkable = map_data["walkable"]
        for x in range(map_data["width"]):
            for y in range(map_data["height"]):
                if walkable[x][y]:
                    game.game_map.tiles[x, y] = tile_types.floor
                else:
                    game.game_map.tiles[x, y] = tile_types.wall

        # Restore explored
        game.game_map.explored = np.array(map_data["explored"], dtype=bool)

        # Restore rooms
        game.game_map.rooms = [
            RectangularRoom(r["x1"], r["y1"], r["x2"] - r["x1"], r["y2"] - r["y1"])
            for r in map_data.get("rooms", [])
        ]

        # Restore player
        player_data = data["player"]
        game.player = Player(
            x=player_data["x"],
            y=player_data["y"],
            name=player_data["name"],
            stats=player_stats,
            tileset_manager=game.tileset_manager,
        )
        game.player.hp = player_data["hp"]
        game.player.max_hp = player_data["max_hp"]
        game.player.hunger = player_data["hunger"]
        game.player.thirst = player_data["thirst"]
        game.player.level = player_data["level"]
        game.player.xp = player_data["xp"]
        game.player.xp_to_next_level = player_data["xp_to_next_level"]

        # Restore inventory
        game.player.inventory = [
            deserialize_item(item_data)
            for item_data in player_data.get("inventory", [])
        ]

        # Restore equipment
        if player_data.get("equipped_weapon"):
            game.player.equipped_weapon = deserialize_item(player_data["equipped_weapon"])
        if player_data.get("equipped_armor"):
            game.player.equipped_armor = deserialize_item(player_data["equipped_armor"])

        # Restore entities
        game.entities = [game.player]

        for monster_data in data.get("monsters", []):
            zombie_type = ZombieType[monster_data["zombie_type"]]
            monster = Monster.spawn_zombie(
                x=monster_data["x"],
                y=monster_data["y"],
                zombie_type=zombie_type,
                tileset_manager=game.tileset_manager,
            )
            monster.hp = monster_data["hp"]
            monster.max_hp = monster_data["max_hp"]
            game.entities.append(monster)

        # Restore ground items
        game.ground_items = {}
        for item_entry in data.get("ground_items", []):
            x, y = item_entry["x"], item_entry["y"]
            item = deserialize_item(item_entry["item"])
            if (x, y) not in game.ground_items:
                game.ground_items[(x, y)] = []
            game.ground_items[(x, y)].append(item)

        # Restore game state
        game.kills = data.get("kills", 0)
        game.messages = data.get("messages", [])
        game.dungeon_level = data.get("dungeon_level", 1)

        # Recompute FOV
        game.recompute_fov()

        # Reset game state
        game.game_over = False
        from src.engine.game import GameState
        game.state = GameState.PLAYING

        return True

    except Exception as e:
        print(f"Load failed: {e}")
        import traceback
        traceback.print_exc()
        return False
