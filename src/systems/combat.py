"""
Combat system - Handles attack and damage calculations
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entities.entity import Entity


class Combat:
    """Combat calculation utilities."""

    @staticmethod
    def calculate_damage(attacker: Entity, defender: Entity) -> int:
        """
        Calculate damage dealt from attacker to defender.

        Formula: damage = attacker.attack - defender.defense + random(-2, 2)
        Minimum damage is 0.
        """
        base_damage = attacker.attack - defender.defense
        variance = random.randint(-2, 2)
        damage = max(0, base_damage + variance)
        return damage

    @staticmethod
    def attack(attacker: Entity, defender: Entity) -> tuple[int, bool]:
        """
        Perform an attack.

        Returns:
            Tuple of (damage_dealt, defender_killed)
        """
        damage = Combat.calculate_damage(attacker, defender)
        defender.hp -= damage
        killed = defender.hp <= 0
        return damage, killed
