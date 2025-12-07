"""
Player entity - The survivor controlled by the user
Enhanced with RPG stats system and inventory
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.entities.entity import Entity

if TYPE_CHECKING:
    from src.graphics.tileset_manager import TilesetManager
    from src.items.item import Item, EquipSlot


@dataclass
class PlayerStats:
    """Player character stats that can be allocated during character creation."""
    strength: int = 5      # Affects melee damage
    agility: int = 5       # Affects dodge chance, hit chance, crit chance
    vitality: int = 5      # Affects max HP and HP regen
    endurance: int = 5     # Affects defense and stamina
    perception: int = 5    # Affects FOV radius and accuracy

    @property
    def total_points(self) -> int:
        return self.strength + self.agility + self.vitality + self.endurance + self.perception

    def get_max_hp(self) -> int:
        """Calculate max HP from vitality. Base 20 + 4 per vitality."""
        return 20 + (self.vitality * 4)

    def get_attack(self) -> int:
        """Calculate attack power from strength. Base 2 + strength."""
        return 2 + self.strength

    def get_defense(self) -> int:
        """Calculate defense from endurance. Base 0 + endurance/2."""
        return self.endurance // 2

    def get_crit_chance(self) -> int:
        """Calculate crit chance from agility. Base 5% + agility."""
        return 5 + self.agility

    def get_dodge_bonus(self) -> int:
        """Calculate dodge bonus from agility."""
        return self.agility * 2

    def get_accuracy_bonus(self) -> int:
        """Calculate accuracy bonus from perception."""
        return self.perception * 2

    def get_fov_radius(self) -> int:
        """Calculate FOV radius from perception. Base 6 + perception/2."""
        return 6 + (self.perception // 2)


class Player(Entity):
    """The player character."""

    def __init__(
        self,
        x: int,
        y: int,
        name: str = "Survivor",
        stats: PlayerStats | None = None,
        tileset_manager: TilesetManager | None = None,
    ) -> None:
        # Get tile ID from tileset manager if available
        tile_id = None
        if tileset_manager:
            tile_id = tileset_manager.get_player_tile("player")

        super().__init__(
            x=x,
            y=y,
            char="@",
            color=(255, 255, 255),
            name=name,
            blocks=True,
            render_order=Entity.RENDER_ORDER_ACTOR,
            tile_id=tile_id,
        )

        # Use provided stats or default
        self.stats = stats if stats else PlayerStats()

        # Derived combat stats
        self.max_hp = self.stats.get_max_hp()
        self.hp = self.max_hp
        self.attack = self.stats.get_attack()
        self.defense = self.stats.get_defense()

        # Crit bonus for combat system
        self.crit_bonus = self.stats.get_crit_chance() - 5  # Subtract base 5%

        # FOV radius
        self.fov_radius = self.stats.get_fov_radius()

        # Survival stats
        self.hunger = 100
        self.thirst = 100

        # Experience and leveling
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = 100

        # Inventory and equipment
        self.inventory: list = []
        self.max_inventory_size = 20
        self.equipped_weapon: Item | None = None
        self.equipped_armor: Item | None = None

    def heal(self, amount: int) -> int:
        """Heal the player. Returns actual amount healed."""
        old_hp = self.hp
        self.hp = min(self.hp + amount, self.max_hp)
        return self.hp - old_hp

    def take_damage(self, amount: int) -> None:
        """Take damage, reduced by defense."""
        self.hp -= amount

    def gain_xp(self, amount: int) -> bool:
        """
        Gain experience points.
        Returns True if leveled up.
        """
        self.xp += amount
        if self.xp >= self.xp_to_next_level:
            self.level_up()
            return True
        return False

    def level_up(self) -> None:
        """Level up the player."""
        self.level += 1
        self.xp -= self.xp_to_next_level
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)

        # Bonus HP on level up
        hp_bonus = 5 + self.stats.vitality // 2
        self.max_hp += hp_bonus
        self.hp = self.max_hp  # Full heal on level up

    def recalculate_stats(self) -> None:
        """Recalculate derived stats from base stats."""
        old_max_hp = self.max_hp
        self.max_hp = self.stats.get_max_hp()
        self.attack = self.stats.get_attack()
        self.defense = self.stats.get_defense()
        self.crit_bonus = self.stats.get_crit_chance() - 5
        self.fov_radius = self.stats.get_fov_radius()

        # Adjust current HP proportionally
        if old_max_hp > 0:
            hp_ratio = self.hp / old_max_hp
            self.hp = int(self.max_hp * hp_ratio)

    # =========================================================================
    # INVENTORY MANAGEMENT
    # =========================================================================

    def add_to_inventory(self, item: "Item") -> bool:
        """
        Add an item to inventory.
        Returns True if successful, False if inventory full.
        """
        # Try to stack with existing item
        if item.stackable:
            for inv_item in self.inventory:
                if inv_item.can_stack_with(item):
                    inv_item.stack_size += item.stack_size
                    return True

        # Check if inventory has space
        if len(self.inventory) >= self.max_inventory_size:
            return False

        self.inventory.append(item)
        return True

    def remove_from_inventory(self, item: "Item") -> bool:
        """Remove an item from inventory."""
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False

    def get_inventory_weight(self) -> float:
        """Get total weight of inventory."""
        return sum(item.weight * item.stack_size for item in self.inventory)

    # =========================================================================
    # EQUIPMENT
    # =========================================================================

    def equip_item(self, item: "Item") -> tuple[bool, str]:
        """
        Equip an item from inventory.
        Returns (success, message).
        """
        from src.items.item import EquipSlot

        if item.equip_slot == EquipSlot.NONE:
            return False, f"{item.name} cannot be equipped."

        # Remove from inventory first
        if item in self.inventory:
            self.inventory.remove(item)

        old_item = None

        if item.equip_slot == EquipSlot.WEAPON:
            old_item = self.equipped_weapon
            self.equipped_weapon = item
        elif item.equip_slot == EquipSlot.ARMOR:
            old_item = self.equipped_armor
            self.equipped_armor = item

        # Return old item to inventory
        if old_item:
            self.inventory.append(old_item)

        return True, f"Equipped {item.name}."

    def unequip_item(self, slot: "EquipSlot") -> tuple[bool, str]:
        """
        Unequip an item and return it to inventory.
        Returns (success, message).
        """
        from src.items.item import EquipSlot

        item = None

        if slot == EquipSlot.WEAPON:
            item = self.equipped_weapon
            self.equipped_weapon = None
        elif slot == EquipSlot.ARMOR:
            item = self.equipped_armor
            self.equipped_armor = None

        if item:
            if len(self.inventory) < self.max_inventory_size:
                self.inventory.append(item)
                return True, f"Unequipped {item.name}."
            else:
                # Re-equip if inventory full
                if slot == EquipSlot.WEAPON:
                    self.equipped_weapon = item
                else:
                    self.equipped_armor = item
                return False, "Inventory full!"
        return False, "Nothing equipped in that slot."

    def get_total_attack(self) -> int:
        """Get total attack including weapon bonus."""
        total = self.attack
        if self.equipped_weapon:
            total += self.equipped_weapon.stats.damage
        return total

    def get_total_defense(self) -> int:
        """Get total defense including armor bonus."""
        total = self.defense
        if self.equipped_armor:
            total += self.equipped_armor.stats.defense
        return total

    def get_total_accuracy(self) -> int:
        """Get total accuracy bonus from equipment."""
        total = self.stats.get_accuracy_bonus()
        if self.equipped_weapon:
            total += self.equipped_weapon.stats.accuracy
        if self.equipped_armor:
            total += self.equipped_armor.stats.accuracy
        return total

    def get_total_crit_bonus(self) -> int:
        """Get total crit bonus from stats and equipment."""
        total = self.crit_bonus
        if self.equipped_weapon:
            total += self.equipped_weapon.stats.crit_bonus
        if self.equipped_armor:
            total += self.equipped_armor.stats.crit_bonus
        return total

    # =========================================================================
    # CONSUMABLES
    # =========================================================================

    def use_item(self, item: "Item") -> tuple[bool, str]:
        """
        Use a consumable item.
        Returns (success, message).
        """
        from src.items.item import ItemType

        if item.item_type != ItemType.CONSUMABLE:
            return False, f"Cannot use {item.name}."

        messages = []

        # Apply effects
        if item.stats.hp_restore > 0:
            healed = self.heal(item.stats.hp_restore)
            if healed > 0:
                messages.append(f"Healed {healed} HP")

        if item.stats.hunger_restore > 0:
            old_hunger = self.hunger
            self.hunger = min(100, self.hunger + item.stats.hunger_restore)
            restored = self.hunger - old_hunger
            if restored > 0:
                messages.append(f"Restored {restored} hunger")

        if item.stats.thirst_restore > 0:
            old_thirst = self.thirst
            self.thirst = min(100, self.thirst + item.stats.thirst_restore)
            restored = self.thirst - old_thirst
            if restored > 0:
                messages.append(f"Restored {restored} thirst")

        if not messages:
            return False, f"{item.name} had no effect."

        # Consume the item
        if item.stackable and item.stack_size > 1:
            item.stack_size -= 1
        else:
            self.remove_from_inventory(item)

        return True, f"Used {item.name}: {', '.join(messages)}."
