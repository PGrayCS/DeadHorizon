# Dead Horizon 

A zombie apocalypse survival roguelike built with Python and tcod.

## Description

Dead Horizon is a turn-based survival roguelike set in a post-apocalyptic world overrun by zombies. Scavenge for supplies, craft weapons, and fight to survive another day.

## Features

-  Procedurally generated dungeon maps
-  5 zombie types with unique sprites and behaviors
-  Turn-based combat with damage flash and blood effects
-  DawnLike 16x16 tileset graphics (included!)
-  Field of view with explored area memory

### Coming Soon
-  Inventory and crafting
-  Survival mechanics (hunger, thirst)
-  Save/Load system
-  Doors and more terrain

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/PGrayCS/DeadHorizon.git
cd DeadHorizon
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install tcod numpy pillow
```

4. Run the game:
```bash
python main.py
```

**That's it!** The DawnLike tileset is included in the repository.

## Controls

- **Arrow Keys / WASD**: Move and attack
- **Period (.)**: Wait a turn
- **ESC**: Quit
- **R**: Restart (after death)

## Zombie Types

| Type | HP | ATK | Special |
|------|-----|-----|---------|
| Zombie | 10 | 3 | Basic enemy |
| Fast Zombie | 6 | 2 | Moves twice per turn! |
| Zombie Brute | 20 | 5 | Tanky, high damage |
| Crawler | 5 | 4 | Low HP, high damage |
| Skeleton | 8 | 3 | Balanced stats |

## Project Structure

```
DeadHorizon/
 main.py              # Entry point
 src/
    engine/          # Core game engine
    entities/        # Player, monsters
    systems/         # Combat system
    map/             # Map generation and tiles
    graphics/        # Tileset and effects
 assets/
    tilesets/
        dawnlike/    # DawnLike tileset (included)
 data/                # JSON data files
```

## Art Credits

- **Tileset**: [DawnLike](https://opengameart.org/content/dawnlike-16x16-universal-rogue-like-tileset-v181) by DragonDePlatino (CC-BY 4.0)

## Inspired By

- [Cataclysm: Dark Days Ahead](https://github.com/CleverRaven/Cataclysm-DDA) - The ultimate zombie survival roguelike

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
