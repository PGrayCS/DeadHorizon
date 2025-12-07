"""
Combat system - Handles attack and damage calculations
Enhanced with crits, dodges, knockback, and equipment support
"""

from __future__ import annotations

import random
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entities.entity import Entity
    from src.engine.game import Game


class AttackResult(Enum):
    """Result of an attack."""
    MISS = auto()
    HIT = auto()
    CRITICAL = auto()
    BLOCKED = auto()


class Combat:
    """Combat calculation utilities with tactical depth."""

    # Base chances (percentage)
    BASE_HIT_CHANCE = 85
    BASE_CRIT_CHANCE = 10
    CRIT_MULTIPLIER = 2.0

    @staticmethod
    def calculate_hit_chance(attacker: Entity, defender: Entity) -> int:
        """
        Calculate chance to hit (0-100).
        Higher attacker accuracy and lower defender defense = better chance.
        """
        base = Combat.BASE_HIT_CHANCE

        # Use total accuracy if player (includes equipment)
        if hasattr(attacker, 'get_total_accuracy'):
            attack_bonus = attacker.get_total_accuracy()
        else:
            attack_bonus = getattr(attacker, 'attack', 5) * 2

        # Penalty from defender agility/defense
        if hasattr(defender, 'get_total_defense'):
            dodge_penalty = defender.get_total_defense() * 3
        else:
            dodge_penalty = getattr(defender, 'defense', 0) * 5

        # Crawlers are harder to hit
        if hasattr(defender, 'zombie_type'):
            from src.entities.monster import ZombieType
            if defender.zombie_type == ZombieType.CRAWLER:
                dodge_penalty += 15

        hit_chance = base + attack_bonus - dodge_penalty
        return max(5, min(95, hit_chance))  # Always 5-95% chance

    @staticmethod
    def calculate_crit_chance(attacker: Entity) -> int:
        """Calculate critical hit chance (0-100)."""
        base = Combat.BASE_CRIT_CHANCE

        # Use total crit bonus if player (includes equipment)
        if hasattr(attacker, 'get_total_crit_bonus'):
            crit_bonus = attacker.get_total_crit_bonus()
        else:
            crit_bonus = getattr(attacker, 'crit_bonus', 0)

        return min(50, base + crit_bonus)  # Cap at 50%

    @staticmethod
    def roll_attack(attacker: Entity, defender: Entity) -> AttackResult:
        """
        Roll to determine attack result.
        Returns: MISS, HIT, CRITICAL, or BLOCKED
        """
        hit_chance = Combat.calculate_hit_chance(attacker, defender)
        hit_roll = random.randint(1, 100)

        if hit_roll > hit_chance:
            return AttackResult.MISS

        # Check for critical
        crit_chance = Combat.calculate_crit_chance(attacker)
        crit_roll = random.randint(1, 100)

        if crit_roll <= crit_chance:
            return AttackResult.CRITICAL

        # Check if blocked (defender has high defense)
        if hasattr(defender, 'get_total_defense'):
            defender_defense = defender.get_total_defense()
        else:
            defender_defense = getattr(defender, 'defense', 0)

        if defender_defense >= 3:
            block_chance = defender_defense * 5
            if random.randint(1, 100) <= block_chance:
                return AttackResult.BLOCKED

        return AttackResult.HIT

    @staticmethod
    def calculate_damage(
        attacker: Entity,
        defender: Entity,
        is_critical: bool = False,
    ) -> int:
        """
        Calculate damage dealt from attacker to defender.

        Formula: damage = (attacker.attack - defender.defense/2) + variance
        Critical hits multiply damage.
        """
        # Use total attack if player (includes equipment)
        if hasattr(attacker, 'get_total_attack'):
            attack_power = attacker.get_total_attack()
        else:
            attack_power = getattr(attacker, 'attack', 5)

        # Use total defense if player (includes equipment)
        if hasattr(defender, 'get_total_defense'):
            defense = defender.get_total_defense()
        else:
            defense = getattr(defender, 'defense', 0)

        # Base damage calculation
        base_damage = attack_power - (defense // 2)

        # Random variance (-1 to +2)
        variance = random.randint(-1, 2)
        damage = base_damage + variance

        # Critical hit multiplier
        if is_critical:
            damage = int(damage * Combat.CRIT_MULTIPLIER)

        return max(1, damage)  # Minimum 1 damage on hit

    @staticmethod
    def perform_attack(
        attacker: Entity,
        defender: Entity,
        game: Game,
    ) -> tuple[AttackResult, int]:
        """
        Perform a full attack with all calculations.

        Returns:
            Tuple of (result, damage_dealt)
        """
        result = Combat.roll_attack(attacker, defender)

        if result == AttackResult.MISS:
            return result, 0

        if result == AttackResult.BLOCKED:
            # Blocked attacks deal reduced damage
            damage = max(0, Combat.calculate_damage(attacker, defender) // 3)
            defender.hp -= damage
            return result, damage

        is_crit = result == AttackResult.CRITICAL
        damage = Combat.calculate_damage(attacker, defender, is_critical=is_crit)
        defender.hp -= damage

        # Knockback on critical hits or heavy attacks
        if is_crit or damage >= 6:
            Combat.apply_knockback(attacker, defender, game)

        return result, damage

    @staticmethod
    def apply_knockback(
        attacker: Entity,
        defender: Entity,
        game: Game,
    ) -> bool:
        """
        Push defender away from attacker.
        Returns True if knockback was applied.
        """
        # Calculate direction away from attacker
        dx = defender.x - attacker.x
        dy = defender.y - attacker.y

        # Normalize to -1, 0, 1
        push_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        push_y = 0 if dy == 0 else (1 if dy > 0 else -1)

        new_x = defender.x + push_x
        new_y = defender.y + push_y

        # Check if destination is valid
        if game.game_map.walkable[new_x, new_y]:
            blocking = game._get_blocking_entity_at(new_x, new_y)
            if blocking is None:
                defender.x = new_x
                defender.y = new_y
                return True

        return False

    @staticmethod
    def get_attack_message(
        attacker_name: str,
        defender_name: str,
        result: AttackResult,
        damage: int,
        is_player_attacking: bool = True,
    ) -> tuple[str, tuple[int, int, int]]:
        """
        Generate a combat message with appropriate color.

        Returns:
            Tuple of (message, color)
        """
        if is_player_attacking:
            if result == AttackResult.MISS:
                return f"You swing at the {defender_name} but miss!", (180, 180, 180)
            elif result == AttackResult.BLOCKED:
                return f"The {defender_name} blocks! ({damage} damage)", (200, 200, 100)
            elif result == AttackResult.CRITICAL:
                return f"CRITICAL HIT! You smash the {defender_name} for {damage} damage!", (255, 255, 100)
            else:
                return f"You hit the {defender_name} for {damage} damage.", (255, 200, 100)
        else:
            if result == AttackResult.MISS:
                return f"The {attacker_name} swings at you but misses!", (100, 255, 100)
            elif result == AttackResult.BLOCKED:
                return f"You block the {attacker_name}'s attack! ({damage} damage)", (100, 200, 255)
            elif result == AttackResult.CRITICAL:
                return f"The {attacker_name} lands a CRITICAL HIT for {damage} damage!", (255, 50, 50)
            else:
                return f"The {attacker_name} hits you for {damage} damage.", (255, 100, 100)
