"""
Visual effects system - damage flash, blood splatter, etc.
"""

from __future__ import annotations

from enum import Enum, auto
import random


class EffectType(Enum):
    DAMAGE_FLASH = auto()
    BLOOD_SPLATTER = auto()


class VisualEffect:
    """A temporary visual effect."""
    
    def __init__(
        self,
        x: int,
        y: int,
        effect_type: EffectType,
        duration: int = 1,
        color: tuple[int, int, int] = (255, 0, 0),
        char: str = "*",
    ) -> None:
        self.x = x
        self.y = y
        self.effect_type = effect_type
        self.duration = duration  # Turns remaining
        self.color = color
        self.char = char
        self.permanent = False  # Blood stays forever
    
    def tick(self) -> bool:
        """
        Advance the effect by one turn.
        Returns True if effect should be removed.
        """
        if self.permanent:
            return False
        self.duration -= 1
        return self.duration <= 0


class BloodSplatter(VisualEffect):
    """Blood on the ground - permanent until cleaned."""
    
    BLOOD_CHARS = [".", ",", "'", "`", "~", "*"]
    BLOOD_COLORS = [
        (139, 0, 0),    # Dark red
        (178, 34, 34),  # Firebrick
        (165, 42, 42),  # Brown red
        (128, 0, 0),    # Maroon
        (120, 20, 20),  # Darker
    ]
    
    def __init__(self, x: int, y: int) -> None:
        char = random.choice(self.BLOOD_CHARS)
        color = random.choice(self.BLOOD_COLORS)
        super().__init__(x, y, EffectType.BLOOD_SPLATTER, duration=0, color=color, char=char)
        self.permanent = True


class DamageFlash(VisualEffect):
    """Brief red flash when entity takes damage."""
    
    def __init__(self, x: int, y: int) -> None:
        super().__init__(
            x, y,
            EffectType.DAMAGE_FLASH,
            duration=1,
            color=(255, 50, 50),
            char="*"
        )


class EffectsManager:
    """Manages all visual effects in the game."""
    
    def __init__(self) -> None:
        self.effects: list[VisualEffect] = []
        self.flash_positions: set[tuple[int, int]] = set()  # Positions flashing this frame
    
    def add_damage_flash(self, x: int, y: int) -> None:
        """Add a damage flash at position."""
        self.flash_positions.add((x, y))
        self.effects.append(DamageFlash(x, y))
    
    def add_blood(self, x: int, y: int, amount: int = 1) -> None:
        """Add blood splatter at and around position."""
        # Blood at impact point
        self.effects.append(BloodSplatter(x, y))
        
        # Splatter around (random nearby tiles)
        for _ in range(amount - 1):
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            self.effects.append(BloodSplatter(x + dx, y + dy))
    
    def add_death_blood(self, x: int, y: int) -> None:
        """Add extra blood when something dies."""
        self.add_blood(x, y, amount=random.randint(3, 5))
    
    def tick(self) -> None:
        """Advance all effects and remove expired ones."""
        self.flash_positions.clear()
        self.effects = [e for e in self.effects if not e.tick()]
    
    def is_flashing(self, x: int, y: int) -> bool:
        """Check if position has active damage flash."""
        return (x, y) in self.flash_positions
    
    def get_blood_at(self, x: int, y: int) -> BloodSplatter | None:
        """Get blood splatter at position (for rendering under entities)."""
        for effect in self.effects:
            if effect.effect_type == EffectType.BLOOD_SPLATTER and effect.x == x and effect.y == y:
                return effect
        return None
    
    def get_effects_at(self, x: int, y: int) -> list[VisualEffect]:
        """Get all effects at a position."""
        return [e for e in self.effects if e.x == x and e.y == y]
