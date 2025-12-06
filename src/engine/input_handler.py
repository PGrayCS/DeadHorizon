"""
Input handler - Processes keyboard input and returns actions
"""

from __future__ import annotations

import tcod.event


def handle_keys(event: tcod.event.Event) -> str | tuple | None:
    """
    Handle keyboard input and return an action.
    
    Returns:
        None: No action
        "quit": Quit the game
        "wait": Wait a turn
        ("move", dx, dy): Move in direction
    """
    if not isinstance(event, tcod.event.KeyDown):
        return None
    
    key = event.sym
    
    # Movement keys
    move_keys = {
        # Arrow keys
        tcod.event.KeySym.UP: (0, -1),
        tcod.event.KeySym.DOWN: (0, 1),
        tcod.event.KeySym.LEFT: (-1, 0),
        tcod.event.KeySym.RIGHT: (1, 0),
        
        # WASD
        tcod.event.KeySym.w: (0, -1),
        tcod.event.KeySym.s: (0, 1),
        tcod.event.KeySym.a: (-1, 0),
        tcod.event.KeySym.d: (1, 0),
        
        # Numpad
        tcod.event.KeySym.KP_8: (0, -1),
        tcod.event.KeySym.KP_2: (0, 1),
        tcod.event.KeySym.KP_4: (-1, 0),
        tcod.event.KeySym.KP_6: (1, 0),
        tcod.event.KeySym.KP_7: (-1, -1),
        tcod.event.KeySym.KP_9: (1, -1),
        tcod.event.KeySym.KP_1: (-1, 1),
        tcod.event.KeySym.KP_3: (1, 1),
        
        # Diagonal with QEZC
        tcod.event.KeySym.q: (-1, -1),
        tcod.event.KeySym.e: (1, -1),
        tcod.event.KeySym.z: (-1, 1),
        tcod.event.KeySym.c: (1, 1),
    }
    
    if key in move_keys:
        dx, dy = move_keys[key]
        return ("move", dx, dy)
    
    # Wait
    if key in (tcod.event.KeySym.PERIOD, tcod.event.KeySym.KP_5):
        return "wait"
    
    # Quit
    if key == tcod.event.KeySym.ESCAPE:
        return "quit"
    
    return None
