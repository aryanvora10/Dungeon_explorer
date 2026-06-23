# 🗝️ Dungeon Explorer

A premium, feature-rich 2D Dungeon Crawler built in Python, rendering dynamic pixel-art graphics using **OpenCV** and managing rich audio with **Pygame Mixer**. Navigate treacherous dungeons, push statues to trigger pressure plates, avoid deadly traps, buy upgrades from the shop, and locate the hidden secret level to conquer the dungeon!

---

## 🎮 Key Features

* **Dynamic Rendering Engine**: Custom grid-based rendering engine using OpenCV with DPI awareness, responsive fullscreen sizing, and smooth frame-based interpolation for movement animations.
* **Complex Game Mechanics**:
  * **Pressure Plates & Gates**: Push statues/orbs onto pressure plates to open/close gates and reveal hidden paths.
  * **Pulling Mechanics**: Hold `Shift` while moving to pull statues/boxes behind you to solve complex puzzles.
  * **Key & Door System**: Collect keys to unlock doors, with animations.
  * **Teleporters**: Instantly warp across the map with visual distortion effects.
  * **Secret Levels**: Discover secret doors to travel to high-risk, high-reward secret levels and return via stairs.
* **Interactive Dungeon Shop**: Press `B` to open the shop screen. Buy equipment like swords, bows, shields, armor, and potions using collected coins.
* **Immersive Visual Effects**: Flash overlays on damage/traps, fade-in transitions, and dynamic pixel-blur teleporter visuals.
* **Audio Atmosphere**: Full looping dungeon soundtrack and contextual sound effects (rock sliding, teleporting, door opening, taking damage, and victory sounds).
* **Fully Unit Tested**: Covered by automated tests ensuring correctness of doors, plates, shield blocks, and monster pathfinding.

---

## 🕹️ Controls Reference

| Context | Action | Keys |
| :--- | :--- | :--- |
| **Title Screen** | Navigate Menu | `A` / `D` or `Left` / `Right` Arrow |
| | Confirm Selection | `Enter` or `Space` |
| **Gameplay** | Move Player | `W` (Up), `A` (Left), `S` (Down), `D` (Right) |
| | Pull Statue / Box | `Shift + W / A / S / D` |
| | Open Shop | `B` |
| | Quit Game | `Q` |
| **Dungeon Shop** | Browse Items | `W`, `A`, `S`, `D` |
| | Buy Item | `Enter` |
| | Exit Shop | `Q` |

---

## 🗺️ Symbol Legend

Explore the dungeon and identify these tiles:

* `#` — **Wall**: Solid obstacle.
* `.` — **Floor**: Walkable path.
* `$` — **Coin**: Currency used in the Dungeon Shop.
* `^` — **Trap**: Inflicts immediate damage when stepped on (ignores shields).
* `K` — **Key**: Consumed to unlock doors.
* `D` / `d` — **Closed / Open Door**: Blocks paths until unlocked by a key or plate.
* `h` — **Health Potion**: Restores 3 health points when collected.
* `P` — **Pressure Plate**: Triggered by placing a Box/Statue on it.
* `S` — **Secret Door**: Steps into the secret level when opened.
* `x` — **Stairs Down**: Progresses to the next level.
* `u` — **Stairs Up**: Returns from the secret level to the main dungeon.

---

## 🛒 Dungeon Shop Inventory

Spend your coins wisely to survive:

| Item | Cost | Tile | Description |
| :--- | :--- | :--- | :--- |
| **Long Sword** | 5 Coins | `long_sword` | A fine blade. Allows you to defeat Skeleton enemies (+3 attack). |
| **Short Sword** | 3 Coins | `short_sword` | Quick and light. Allows you to defeat Skeleton enemies (+1 attack). |
| **Bow** | 4 Coins | `bow` | Strike from afar. Ranged attack. |
| **Armor** | 8 Coins | `armor` | Heavy plate. Reduces damage taken. |
| **Shield** | 6 Coins | `shield` | Blocks the next 2 incoming hits from monsters (broken afterwards). |
| **Potion** | 2 Coins | `potion` | Instantly restores 3 health points. |

---

## 📁 Codebase Architecture

The project is structured into modular Python components:

* [main.py](file:///d:/summer_school/Dungeon_explorer/main.py): The main entry point, game loop, keyboard input handling, and screen render pipeline.
* [game.py](file:///d:/summer_school/Dungeon_explorer/game.py): Core game state model, collision detection, player/monster movement logic, and event callbacks.
* [levels.py](file:///d:/summer_school/Dungeon_explorer/levels.py): Procedural creation and layouts for Level 1, Level 2, and the Secret Level.
* [shop.py](file:///d:/summer_school/Dungeon_explorer/shop.py): Full UI drawing and purchase handling for the Dungeon Shop.
* [config.py](file:///d:/summer_school/Dungeon_explorer/config.py): DPI-aware screen resolution detection, tile scaling calculations, and optimized asset loading.
* [effects.py](file:///d:/summer_school/Dungeon_explorer/effects.py): Visual effect rendering classes (e.g., `FadeIn`, `Flash`, `RandomBlur`, and `ColorText`).
* [moves.py](file:///d:/summer_school/Dungeon_explorer/moves.py): Core movement classes tracking linear interpolation progress.
* [sound.py](file:///d:/summer_school/Dungeon_explorer/sound.py): Sound loader and Pygame audio mixer wrapper.
* [test_dungeon_game.py](file:///d:/summer_school/Dungeon_explorer/test_dungeon_game.py): Test suite verifying core logic behaviors.

---

## 🚀 Setup & Execution

### Prerequisites
* Python 3.10+
* System audio output enabled (for sound effects/soundtrack)

### 1. Install Dependencies
Initialize your virtual environment and install the required libraries:
```bash
pip install -r requirements.txt
```

### 2. Run the Game
Execute the main entry script to start playing:
```bash
python main.py
```

### 3. Run the Test Suite
Run tests using `pytest` to verify game logic:
```bash
pytest
```
