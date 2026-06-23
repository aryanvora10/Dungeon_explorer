import pytest
import levels
import main
import shop
import time

from game import start_game, move_player, check_collision, take_damage, Skeleton
from moves import Move


def test_open_door():
    # 1. prepare test data
    game = start_game()
    # Place a closed door at (2, 1) and give the player a key
    game.current_level.level[1][2] = "D"
    game.items.append("key")

    # 2. call the function you want to test
    move_player(game, "right")

    # 3. check if the result is correct
    assert game.current_level.level[1][2] == "d"
    assert "key" not in game.items


def test_shield_blocks_monster_but_not_trap():
    game = start_game()
    initial_health = game.health

    # Give player shield with 2 hits
    game.items.append("shield")
    game.shield_hits = 2

    # 1. Monster damage should be blocked by shield
    skeleton = Skeleton(x=game.x, y=game.y, direction="left")
    game.current_level.monsters.append(skeleton)

    # Ensure no sword is equipped
    if "short_sword" in game.items:
        game.items.remove("short_sword")
    if "long_sword" in game.items:
        game.items.remove("long_sword")

    check_collision(game)

    # Health should not change, shield hits should decrease
    assert game.health == initial_health
    assert game.shield_hits == 1
    assert "shield" in game.items

    # Reset last_damage_time so cooldown doesn't prevent damage
    game.last_damage_time = 0.0

    # 2. Trap damage should NOT be blocked by shield
    # Direct call simulating trap damage (ignore_shield=True)
    take_damage(game, ignore_shield=True)

    # Health should decrease, shield hits should remain 1
    assert game.health == initial_health - 1
    assert game.shield_hits == 1
    assert "shield" in game.items


def test_pressure_plate_gates():
    from game import PressurePlate, Box, check_pressure_plates
    from main import clean_moves
    game = start_game()

    # Let's set up a custom pressure plate at (3, 3) targeting a closed door D at (4, 3)
    game.current_level.level[3][4] = "D"
    plate = PressurePlate(x=3, y=3, gate_x=4, gate_y=3)
    game.current_level.pressure_plates = [plate]
    game.current_level.boxes = []

    # 1. No box on the plate, door is closed "D"
    check_pressure_plates(game)
    assert game.current_level.level[3][4] == "D"

    # 2. Place box on the plate, door should open to "d"
    box = Box(x=3, y=3)
    game.current_level.boxes.append(box)
    check_pressure_plates(game)
    assert game.current_level.level[3][4] == "d"
    game.moves.clear()

    # 3. Remove box from the plate, door should close back to "D" AFTER the animation finishes
    game.current_level.boxes.remove(box)
    check_pressure_plates(game)
    # The tile is still "d" immediately after checking, because animation just started
    assert game.current_level.level[3][4] == "d"

    # Complete the closing animation
    assert len(game.moves) == 1
    game.moves[0].progress = 1.0
    clean_moves(game, game.moves)
    # The tile is now updated to "D"
    assert game.current_level.level[3][4] == "D"
    game.moves.clear()

    # 4. Set up pressure plate targeting a secret wall '#' at (5, 3)
    game.current_level.level[3][5] = "#"
    plate_secret = PressurePlate(x=3, y=3, gate_x=5, gate_y=3)
    game.current_level.pressure_plates = [plate_secret]

    # Place box on plate -> secret gate S revealed
    game.current_level.boxes.append(box)
    check_pressure_plates(game)
    assert game.current_level.level[3][5] == "S"
    game.moves.clear()

    # Remove box -> secret gate S turns back to "#" AFTER animation finishes
    game.current_level.boxes.remove(box)
    check_pressure_plates(game)
    assert game.current_level.level[3][5] == "S"

    # Complete the closing animation
    assert len(game.moves) == 1
    game.moves[0].progress = 1.0
    clean_moves(game, game.moves)
    # The tile is now updated to "#"
    assert game.current_level.level[3][5] == "#"
    game.moves.clear()

    # 5. Key override test: if a plate targets a door D, but the door is opened with key
    plate_key = PressurePlate(x=3, y=3, gate_x=4, gate_y=3)
    game.current_level.pressure_plates = [plate_key]
    game.current_level.level[3][4] = "D"
    game.items.append("key")

    # Move player onto the door to unlock it
    game.x = 3
    game.y = 3
    move_player(game, "right")

    # Door should be open "d" and key should be consumed
    assert game.current_level.level[3][4] == "d"
    assert "key" not in game.items

    check_pressure_plates(game)
    assert game.current_level.level[3][4] == "d"


def test_monster_cant_step_on_teleporters():
    from game import Teleporter, Skeleton, move_monster
    game = start_game()
    # Add a teleporter at (2, 1) which is adjacent to player start (1, 1)
    teleporter = Teleporter(x=2, y=1, target_x=13, target_y=1)
    game.current_level.teleporters = [teleporter]

    # Place a skeleton at (1, 1) and make it face right (towards the teleporter at 2, 1)
    skeleton = Skeleton(x=1, y=1, direction="right")
    game.current_level.monsters = [skeleton]

    # Try to move the skeleton
    move_monster(game, skeleton)

    # The skeleton should NOT move to (2, 1) and its direction should turn around (since movement is blocked)
    assert skeleton.x == 1
    assert skeleton.y == 1
    assert skeleton.direction == "left"


