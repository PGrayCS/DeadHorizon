"""
Item system - All items in the game
"""

from __future__ import annotations

from enum import Enum, auto
from dataclasses import dataclass, field


class ItemType(Enum):
    """Categories of items."""
    WEAPON = auto()
    ARMOR = auto()
    CONSUMABLE = auto()
    AMMO = auto()
    MATERIAL = auto()
    TOOL = auto()


class EquipSlot(Enum):
    """Equipment slots on the player."""
    WEAPON = auto()
    ARMOR = auto()
    NONE = auto()


@dataclass
class ItemStats:
    """Combat stats provided by an item."""
    damage: int = 0          # Bonus damage (weapons)
    defense: int = 0         # Bonus defense (armor)
    accuracy: int = 0        # Bonus accuracy %
    crit_bonus: int = 0      # Bonus crit %
    hp_restore: int = 0      # HP restored (consumables)
    hunger_restore: int = 0  # Hunger restored (food)
    thirst_restore: int = 0  # Thirst restored (drinks)


@dataclass
class Item:
    """
    A game item that can be picked up, used, or equipped.
    """
    name: str
    char: str
    color: tuple[int, int, int]
    item_type: ItemType
    description: str = ""

    # Equipment
    equip_slot: EquipSlot = EquipSlot.NONE
    stats: ItemStats = field(default_factory=ItemStats)

    # Stacking
    stackable: bool = False
    stack_size: int = 1
    max_stack: int = 1

    # Value for trading (future)
    value: int = 1

    # Weight for inventory limits (future)
    weight: float = 1.0

    # Tile ID for graphical display
    tile_id: int | None = None

    def get_display_name(self) -> str:
        """Get name with stack count if applicable."""
        if self.stackable and self.stack_size > 1:
            return f"{self.name} x{self.stack_size}"
        return self.name

    def get_stat_string(self) -> str:
        """Get a string describing the item's stats."""
        parts = []
        if self.stats.damage > 0:
            parts.append(f"+{self.stats.damage} DMG")
        if self.stats.defense > 0:
            parts.append(f"+{self.stats.defense} DEF")
        if self.stats.accuracy > 0:
            parts.append(f"+{self.stats.accuracy}% ACC")
        if self.stats.crit_bonus > 0:
            parts.append(f"+{self.stats.crit_bonus}% CRIT")
        if self.stats.hp_restore > 0:
            parts.append(f"+{self.stats.hp_restore} HP")
        if self.stats.hunger_restore > 0:
            parts.append(f"+{self.stats.hunger_restore} Food")
        if self.stats.thirst_restore > 0:
            parts.append(f"+{self.stats.thirst_restore} Water")
        return ", ".join(parts) if parts else "No stats"

    def can_stack_with(self, other: "Item") -> bool:
        """Check if this item can stack with another."""
        return (
            self.stackable
            and other.stackable
            and self.name == other.name
            and self.stack_size + other.stack_size <= self.max_stack
        )

    def copy(self) -> "Item":
        """Create a copy of this item."""
        return Item(
            name=self.name,
            char=self.char,
            color=self.color,
            item_type=self.item_type,
            description=self.description,
            equip_slot=self.equip_slot,
            stats=ItemStats(
                damage=self.stats.damage,
                defense=self.stats.defense,
                accuracy=self.stats.accuracy,
                crit_bonus=self.stats.crit_bonus,
                hp_restore=self.stats.hp_restore,
                hunger_restore=self.stats.hunger_restore,
                thirst_restore=self.stats.thirst_restore,
            ),
            stackable=self.stackable,
            stack_size=self.stack_size,
            max_stack=self.max_stack,
            value=self.value,
            weight=self.weight,
            tile_id=self.tile_id,
        )


# ============================================================================
# ITEM DEFINITIONS - All items in the game
# ============================================================================

# --- WEAPONS ---
ITEMS = {
    # Melee Weapons
    "fists": Item(
        name="Fists",
        char=")",
        color=(200, 180, 160),
        item_type=ItemType.WEAPON,
        description="Your bare hands. Better than nothing.",
        equip_slot=EquipSlot.WEAPON,
        stats=ItemStats(damage=0),
        value=0,
    ),
    "baseball_bat": Item(
        name="Baseball Bat",
        char="/",
        color=(139, 90, 43),
        item_type=ItemType.WEAPON,
        description="A wooden baseball bat. Solid and reliable.",
        equip_slot=EquipSlot.WEAPON,
        stats=ItemStats(damage=3, accuracy=5),
        value=15,
    ),
    "pipe": Item(
        name="Lead Pipe",
        char="/",
        color=(120, 120, 130),
        item_type=ItemType.WEAPON,
        description="A heavy metal pipe. Slow but powerful.",
        equip_slot=EquipSlot.WEAPON,
        stats=ItemStats(damage=4, accuracy=-5),
        value=10,
    ),
    "knife": Item(
        name="Kitchen Knife",
        char="-",
        color=(200, 200, 210),
        item_type=ItemType.WEAPON,
        description="A sharp kitchen knife. Quick and deadly.",
        equip_slot=EquipSlot.WEAPON,
        stats=ItemStats(damage=2, crit_bonus=10, accuracy=10),
        value=12,
    ),
    "machete": Item(
        name="Machete",
        char="/",
        color=(180, 180, 190),
        item_type=ItemType.WEAPON,
        description="A large blade. Excellent for clearing zombies.",
        equip_slot=EquipSlot.WEAPON,
        stats=ItemStats(damage=5, crit_bonus=5),
        value=25,
    ),
    "fire_axe": Item(
        name="Fire Axe",
        char="P",
        color=(255, 50, 50),
        item_type=ItemType.WEAPON,
        description="A firefighter's axe. Heavy and brutal.",
        equip_slot=EquipSlot.WEAPON,
        stats=ItemStats(damage=7, accuracy=-10, crit_bonus=15),
        value=35,
    ),
    "crowbar": Item(
        name="Crowbar",
        char="/",
        color=(100, 100, 110),
        item_type=ItemType.WEAPON,
        description="A sturdy crowbar. Good for bashing and prying.",
        equip_slot=EquipSlot.WEAPON,
        stats=ItemStats(damage=3, accuracy=0),
        value=18,
    ),
    "hammer": Item(
        name="Hammer",
        char="T",
        color=(139, 90, 43),
        item_type=ItemType.WEAPON,
        description="A claw hammer. Compact but effective.",
        equip_slot=EquipSlot.WEAPON,
        stats=ItemStats(damage=2, crit_bonus=5),
        value=8,
    ),

    # --- ARMOR ---
    "leather_jacket": Item(
        name="Leather Jacket",
        char="[",
        color=(70, 40, 20),
        item_type=ItemType.ARMOR,
        description="A worn leather jacket. Some protection.",
        equip_slot=EquipSlot.ARMOR,
        stats=ItemStats(defense=1),
        value=20,
    ),
    "kevlar_vest": Item(
        name="Kevlar Vest",
        char="[",
        color=(30, 30, 40),
        item_type=ItemType.ARMOR,
        description="Military-grade body armor. Excellent protection.",
        equip_slot=EquipSlot.ARMOR,
        stats=ItemStats(defense=3),
        value=50,
    ),
    "riot_gear": Item(
        name="Riot Gear",
        char="[",
        color=(50, 50, 60),
        item_type=ItemType.ARMOR,
        description="Police riot armor. Heavy but protective.",
        equip_slot=EquipSlot.ARMOR,
        stats=ItemStats(defense=4, accuracy=-5),
        value=65,
    ),
    "hoodie": Item(
        name="Hoodie",
        char="[",
        color=(80, 80, 100),
        item_type=ItemType.ARMOR,
        description="A thick hoodie. Minimal protection.",
        equip_slot=EquipSlot.ARMOR,
        stats=ItemStats(defense=0),
        value=5,
    ),

    # --- CONSUMABLES ---
    "bandage": Item(
        name="Bandage",
        char="+",
        color=(255, 255, 255),
        item_type=ItemType.CONSUMABLE,
        description="Basic first aid bandage. Heals minor wounds.",
        stats=ItemStats(hp_restore=10),
        stackable=True,
        max_stack=10,
        value=8,
    ),
    "first_aid_kit": Item(
        name="First Aid Kit",
        char="+",
        color=(255, 100, 100),
        item_type=ItemType.CONSUMABLE,
        description="Complete first aid kit. Heals significant wounds.",
        stats=ItemStats(hp_restore=30),
        value=25,
    ),
    "painkillers": Item(
        name="Painkillers",
        char="!",
        color=(255, 200, 100),
        item_type=ItemType.CONSUMABLE,
        description="Pain medication. Restores some health.",
        stats=ItemStats(hp_restore=15),
        stackable=True,
        max_stack=5,
        value=12,
    ),
    "canned_food": Item(
        name="Canned Food",
        char="%",
        color=(200, 150, 100),
        item_type=ItemType.CONSUMABLE,
        description="Canned beans. Restores hunger.",
        stats=ItemStats(hunger_restore=30),
        stackable=True,
        max_stack=5,
        value=10,
    ),
    "mre": Item(
        name="MRE",
        char="%",
        color=(80, 100, 60),
        item_type=ItemType.CONSUMABLE,
        description="Military Meal Ready-to-Eat. Very filling.",
        stats=ItemStats(hunger_restore=50, thirst_restore=10),
        value=20,
    ),
    "water_bottle": Item(
        name="Water Bottle",
        char="!",
        color=(100, 150, 255),
        item_type=ItemType.CONSUMABLE,
        description="Clean drinking water.",
        stats=ItemStats(thirst_restore=40),
        stackable=True,
        max_stack=5,
        value=8,
    ),
    "energy_drink": Item(
        name="Energy Drink",
        char="!",
        color=(100, 255, 100),
        item_type=ItemType.CONSUMABLE,
        description="Caffeinated energy drink. Quenches thirst.",
        stats=ItemStats(thirst_restore=25, hp_restore=5),
        stackable=True,
        max_stack=5,
        value=6,
    ),
    "snack_bar": Item(
        name="Snack Bar",
        char="%",
        color=(180, 140, 80),
        item_type=ItemType.CONSUMABLE,
        description="A granola bar. Quick snack.",
        stats=ItemStats(hunger_restore=15),
        stackable=True,
        max_stack=10,
        value=4,
    ),
}


def create_item(item_id: str) -> Item:
    """Create a new instance of an item by ID."""
    if item_id not in ITEMS:
        raise ValueError(f"Unknown item ID: {item_id}")
    return ITEMS[item_id].copy()


def get_random_weapon() -> Item:
    """Get a random weapon."""
    import random
    weapons = [k for k, v in ITEMS.items() if v.item_type == ItemType.WEAPON and k != "fists"]
    return create_item(random.choice(weapons))


def get_random_armor() -> Item:
    """Get a random armor piece."""
    import random
    armors = [k for k, v in ITEMS.items() if v.item_type == ItemType.ARMOR]
    return create_item(random.choice(armors))


def get_random_consumable() -> Item:
    """Get a random consumable."""
    import random
    consumables = [k for k, v in ITEMS.items() if v.item_type == ItemType.CONSUMABLE]
    return create_item(random.choice(consumables))


def get_random_item() -> Item:
    """Get a random item with weighted distribution."""
    import random
    # Consumables are more common than equipment
    roll = random.randint(1, 100)
    if roll <= 60:
        return get_random_consumable()
    elif roll <= 85:
        return get_random_weapon()
    else:
        return get_random_armor()
