# Dead Horizon 🧟

A zombie apocalypse survival roguelike built with Python and tcod.

## Description

Dead Horizon is a turn-based survival roguelike set in a post-apocalyptic world overrun by zombies. Scavenge for supplies, craft weapons, and fight to survive another day.

## Features (Planned)

- 🗺️ Procedurally generated maps
- 🧟 Various zombie types with different behaviors
- ⚔️ Turn-based combat system
- 🎒 Inventory and crafting
- 🍖 Survival mechanics (hunger, thirst, health)
- 💾 Save/Load system
- 🎨 DawnLike 16x16 tileset graphics

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DeadHorizon.git
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
pip install -r requirements.txt
```

4. Download the DawnLike tileset:
   - Go to: https://opengameart.org/content/dawnlike-16x16-universal-rogue-like-tileset-v181
   - Download and extract to `assets/tilesets/DawnLike/`

5. Run the game:
```bash
python main.py
```

## Controls

- **Arrow Keys / WASD / Numpad**: Move
- **G**: Pick up item
- **I**: Open inventory
- **ESC**: Menu / Quit

## Project Structure

```
DeadHorizon/
├── main.py              # Entry point
├── requirements.txt     # Python dependencies
├── src/
│   ├── engine/          # Core game engine
│   ├── entities/        # Player, monsters, items
│   ├── components/      # Entity components
│   ├── systems/         # Game systems (combat, survival)
│   ├── map/             # Map generation and tiles
│   ├── ui/              # User interface
│   └── data/            # Data loaders
├── data/
│   ├── items/           # Item definitions (JSON)
│   ├── monsters/        # Monster definitions (JSON)
│   └── terrain/         # Terrain definitions (JSON)
├── assets/
│   └── tilesets/        # Graphics (DawnLike)
├── saves/               # Save files
└── tests/               # Unit tests
```

## Art Credits

- **Tileset**: DawnLike by DragonDePlatino (CC-BY 4.0)
  - https://opengameart.org/content/dawnlike-16x16-universal-rogue-like-tileset-v181

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
