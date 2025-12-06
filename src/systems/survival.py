"""
Survival system - Handles hunger, thirst, health regeneration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entities.player import Player


class Survival:
    """Survival mechanics handler."""
    
    # How often survival ticks occur (in turns)
    TICK_RATE = 100
    
    # Hunger/thirst decrease per tick
    HUNGER_DECAY = 1
    THIRST_DECAY = 2
    
    # Damage when starving/dehydrated
    STARVATION_DAMAGE = 1
    DEHYDRATION_DAMAGE = 1
    
    @staticmethod
    def tick(player: Player, turns: int) -> list[str]:
        """
        Process survival mechanics for the given number of turns.
        
        Returns:
            List of messages to display
        """
        messages = []
        
        # Only tick every TICK_RATE turns
        if turns % Survival.TICK_RATE != 0:
            return messages
        
        # Decrease hunger
        player.hunger = max(0, player.hunger - Survival.HUNGER_DECAY)
        if player.hunger <= 0:
            player.hp -= Survival.STARVATION_DAMAGE
            messages.append("You are starving!")
        elif player.hunger <= 20:
            messages.append("You are getting hungry.")
        
        # Decrease thirst
        player.thirst = max(0, player.thirst - Survival.THIRST_DECAY)
        if player.thirst <= 0:
            player.hp -= Survival.DEHYDRATION_DAMAGE
            messages.append("You are dying of thirst!")
        elif player.thirst <= 20:
            messages.append("You are getting thirsty.")
        
        return messages
    
    @staticmethod
    def eat(player: Player, nutrition: int) -> str:
        """Player eats food."""
        old_hunger = player.hunger
        player.hunger = min(100, player.hunger + nutrition)
        gained = player.hunger - old_hunger
        return f"You eat and restore {gained} hunger."
    
    @staticmethod
    def drink(player: Player, hydration: int) -> str:
        """Player drinks."""
        old_thirst = player.thirst
        player.thirst = min(100, player.thirst + hydration)
        gained = player.thirst - old_thirst
        return f"You drink and restore {gained} thirst."
