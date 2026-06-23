"""
the Dungeon Explorer game logic
"""

from pydantic import BaseModel
from effects import Effect, RandomBlur, FadeIn, Flash
from typing import Callable, Literal
from moves import Move, player_move_finished
import time
from sound import (
    rock_slide_sound,
    door_open_sound,
    coin_sound,
    damage_sound,
    teleport_sound,
)

Position = tuple[int, int]
Direction = Literal["up", "down", "left", "right"]


def get_next_position(from_pos: Position, direction: Direction) -> Position:
    x, y = from_pos
    offsets = {"right": (1, 0), "left": (-1, 0), "up": (0, -1), "down": (0, 1)}
    dx, dy = offsets.get(direction, (0, 0))
    return x + dx, y + dy


class Monster(BaseModel):
    x: int
    y: int
    move: Move = None
    direction: Direction
    tile: str = "monster"
    explodes: bool = False
    speed: float = 0.5


class Teleporter(BaseModel):
    x: int
    y: int
    target_x: int
    target_y: int


class Fireball(Monster):
    tile: str = "fireball"
    explodes: bool = True


class Skeleton(Monster):
    tile: str = "skeleton"


class Explosion(BaseModel):
    x: int
    y: int
    max_frame: int = 16
    max_delay: int = 5
    delay: int = 0
    frame: int = 0
    complete: bool = False


class Box(BaseModel):
    x: int
    y: int
    move: Move = None


class PressurePlate(BaseModel):
    x: int
    y: int
    gate_x: int
    gate_y: int
    original_gate_tile: str = None


class Level(BaseModel):
    level: list[list[str]]
    teleporters: list[Teleporter] = []
    monsters: list[Monster] = []
    boxes: list[Box] = []
    pressure_plates: list[PressurePlate] = []
    has_secret_door: bool = False


class DungeonGame(BaseModel):
    status: str = "running"
    x: int
    y: int
    moves: list[Move] = []
    coins: int = 0
    health: int = 10
    items: list[str] = []
    current_level: Level
    last_damage_time: float = 0.0
    level_number: int = 0
    return_level_number: int = -1  # -1 means not in a secret level
    return_x: int = 1
    return_y: int = 1
    explosions: list[Explosion] = []
    effects: list[Effect] = []
    shield_hits: int = 0  # remaining shield uses (set to 2 when shield is bought)


def parse_level(level: list[str]) -> list[list[str]]:
    return [list(row) for row in level]


def check_collision(game: DungeonGame) -> None:
    has_sword = "long_sword" in game.items or "short_sword" in game.items
    for m in list(game.current_level.monsters):
        if m.x == game.x and m.y == game.y:
            if has_sword and isinstance(m, Skeleton):
                # kill the skeleton
                game.current_level.monsters.remove(m)
                game.explosions.append(Explosion(x=m.x, y=m.y))
            else:
                take_damage(game)
            return  # one interaction per frame is enough


def update_effects(game: DungeonGame) -> None:
    new_effects = []
    for e in game.effects:
        e.countdown -= 5
        if e.countdown > 0:
            new_effects.append(e)
    game.effects = new_effects


def update(game: DungeonGame) -> None:
    for m in game.current_level.monsters:
        if not m.move or m.move.complete:
            move_monster(game, m)
    check_collision(game)


def move_monster(game: DungeonGame, monster: Monster) -> None:
    new_x, new_y = get_next_position([monster.x, monster.y], monster.direction)
    is_teleporter = any(
        t.x == new_x and t.y == new_y for t in game.current_level.teleporters
    )
    # Changed ".€k" to [".", "$", "K", "^"] to correctly match floors, coins, keys, and traps
    if (
        game.current_level.level[new_y][new_x] in [".", "$", "K", "^"]
        and get_box_at(game, new_x, new_y) is None
        and not is_teleporter
    ):
        monster.move = Move(
            tile=monster.tile,
            from_x=monster.x,
            from_y=monster.y,
            speed_x=new_x - monster.x,
            speed_y=new_y - monster.y,
            speed=monster.speed,
        )
        game.moves.append(monster.move)
        monster.x = new_x
        monster.y = new_y
    else:
        if monster.explodes:
            game.explosions.append(Explosion(x=new_x, y=new_y))
        opposite_directions = {
            "right": "left",
            "left": "right",
            "up": "down",
            "down": "up",
        }
        monster.direction = opposite_directions[monster.direction]


def check_teleporters(game: DungeonGame) -> None:
    for t in game.current_level.teleporters:
        if game.x == t.x and game.y == t.y:
            game.x = t.target_x
            game.y = t.target_y
            game.effects.append(RandomBlur(x=game.x, y=game.y, countdown=80))
            teleport_sound.play()


def get_box_at(game: DungeonGame, x: int, y: int):
    """Return the box at position (x, y) or None."""
    for box in game.current_level.boxes:
        if box.x == x and box.y == y:
            return box
    return None


def is_tile_free_for_box(game: DungeonGame, x: int, y: int) -> bool:
    """Check if a tile is free for a box to move into."""
    tile = game.current_level.level[y][x]
    if tile not in [".", "P"]:
        return False
    # Also check no other box is there
    if get_box_at(game, x, y) is not None:
        return False
    return True


def is_gate_closing(game: DungeonGame, x: int, y: int) -> bool:
    for m in game.moves:
        if m.tile == "wall" and m.from_x == x and m.from_y == y - 1 and m.speed_y == 2:
            return True
    return False


def close_gate(
    game: DungeonGame, x: int, y: int, tile: str, plate: PressurePlate
) -> None:
    # If a box is on the plate, or the player is on the gate tile, do NOT close the door!
    if get_box_at(game, plate.x, plate.y) is not None or (game.x == x and game.y == y):
        return
    game.current_level.level[y][x] = tile


def make_close_callback(gx, gy, ot, plate):
    return lambda g: close_gate(g, gx, gy, ot, plate)


def check_pressure_plates(game: DungeonGame) -> None:
    """Check if any box is on a pressure plate and open/close the corresponding gate."""
    for plate in game.current_level.pressure_plates:
        box_on_plate = get_box_at(game, plate.x, plate.y)
        gate_tile = game.current_level.level[plate.gate_y][plate.gate_x]

        if plate.original_gate_tile is None:
            plate.original_gate_tile = gate_tile

        if box_on_plate is not None:
            if gate_tile in ["G", "D"]:
                # Open the gate/door with animation
                game.current_level.level[plate.gate_y][plate.gate_x] = "d"
                move = Move(
                    tile="wall",
                    from_x=plate.gate_x,
                    from_y=plate.gate_y,
                    speed_x=0,
                    speed_y=-2,
                )
                game.moves.append(move)
                door_open_sound.play()
            elif gate_tile == "#":
                # Open a Secret Door!
                game.current_level.level[plate.gate_y][plate.gate_x] = "S"
                move = Move(
                    tile="wall",
                    from_x=plate.gate_x,
                    from_y=plate.gate_y,
                    speed_x=0,
                    speed_y=-2,
                )
                game.moves.append(move)
                door_open_sound.play()
        else:
            if gate_tile == "d" and plate.original_gate_tile in ["G", "D"]:
                if not is_gate_closing(game, plate.gate_x, plate.gate_y):
                    # Close the gate/door with animation
                    move = Move(
                        tile="wall",
                        from_x=plate.gate_x,
                        from_y=plate.gate_y - 1,
                        speed_x=0,
                        speed_y=2,
                    )
                    move.finished = make_close_callback(
                        plate.gate_x, plate.gate_y, plate.original_gate_tile, plate
                    )
                    game.moves.append(move)
            elif gate_tile == "S" and plate.original_gate_tile == "#":
                if not is_gate_closing(game, plate.gate_x, plate.gate_y):
                    # Hide the secret door again
                    move = Move(
                        tile="wall",
                        from_x=plate.gate_x,
                        from_y=plate.gate_y - 1,
                        speed_x=0,
                        speed_y=2,
                    )
                    move.finished = make_close_callback(
                        plate.gate_x, plate.gate_y, "#", plate
                    )
                    game.moves.append(move)


def push_box(game: DungeonGame, box: Box, direction: str) -> bool:
    """Try to push a box in the given direction. Returns True if successful."""
    new_bx, new_by = get_next_position((box.x, box.y), direction)
    if is_tile_free_for_box(game, new_bx, new_by):
        # Animate the box moving
        speed = 1.5
        box.move = Move(
            tile="statue_orb",
            from_x=box.x,
            from_y=box.y,
            speed_x=new_bx - box.x,
            speed_y=new_by - box.y,
            speed=speed,
        )
        game.moves.append(box.move)
        box.x = new_bx
        box.y = new_by
        rock_slide_sound.play()
        return True
    return False


def move_player(game: DungeonGame, direction: str, pulling: bool = False) -> None:
    target_x, target_y = get_next_position([game.x, game.y], direction)

    allowed = [".", "x", "u", "$", "^", "K", "d", "h", "S", "P"]
    if "key" in game.items:
        allowed.append("D")

    # Check if there's a box at the target position (pushing)
    target_box = get_box_at(game, target_x, target_y)

    new_x, new_y = game.x, game.y
    if target_box is not None and not pulling:
        # Try to push the box
        if push_box(game, target_box, direction):
            # Box moved, player can step into its old position
            speed_x = target_x - game.x
            speed_y = target_y - game.y
            speed = 1.5
            move = Move(
                tile="player",
                from_x=game.x,
                from_y=game.y,
                speed_x=speed_x,
                speed_y=speed_y,
                speed=speed,
            )
            game.moves.append(move)
            new_x, new_y = target_x, target_y
        # If push failed (wall behind box), player doesn't move
    elif game.current_level.level[target_y][target_x] in allowed and (
        target_x != game.x or target_y != game.y
    ):
        speed_x = target_x - game.x
        speed_y = target_y - game.y
        speed = 2.0
        move = Move(
            tile="player",
            from_x=game.x,
            from_y=game.y,
            speed_x=speed_x,
            speed_y=speed_y,
            speed=speed,
        )
        game.moves.append(move)
        new_x, new_y = target_x, target_y

    # Handle pulling: pull a box from behind the player
    if pulling and (new_x != game.x or new_y != game.y):
        opposite = {"right": "left", "left": "right", "up": "down", "down": "up"}
        behind_dir = opposite.get(direction)
        if behind_dir:
            behind_x, behind_y = get_next_position((game.x, game.y), behind_dir)
            pull_box = get_box_at(game, behind_x, behind_y)
            if pull_box is not None:
                # Pull the box to the player's old position
                speed = 1.5
                pull_box.move = Move(
                    tile="statue_orb",
                    from_x=pull_box.x,
                    from_y=pull_box.y,
                    speed_x=game.x - pull_box.x,
                    speed_y=game.y - pull_box.y,
                    speed=speed,
                )
                game.moves.append(pull_box.move)
                pull_box.x = game.x
                pull_box.y = game.y
                rock_slide_sound.play()

    tile = game.current_level.level[new_y][new_x]
    if tile in ["$", "h", "K"]:
        game.current_level.level[new_y][new_x] = "."
        collect_funcs = {"$": collect_coin, "h": collect_potion, "K": collect_key}
        func = collect_funcs[tile]
        if game.moves:
            game.moves[-1].finished = func
        else:
            func(game)

    if game.current_level.level[new_y][new_x] == "D" and "key" in game.items:
        game.items.remove("key")
        game.current_level.level[new_y][new_x] = "d"
        door_open_sound.play()
        for plate in game.current_level.pressure_plates:
            if plate.gate_x == new_x and plate.gate_y == new_y:
                plate.original_gate_tile = "d"

    if game.current_level.level[new_y][new_x] in [".", "^", "x", "u", "d", "S", "P"]:
        game.x = new_x
        game.y = new_y

    if game.current_level.level[new_y][new_x] == "x":
        game.level_number += 1
        if game.level_number < len(LEVELS):
            # move to next level
            game.current_level = LEVELS[game.level_number]
            game.x = 1
            game.y = 1
            game.moves.clear()
        else:
            # no more levels left
            game.status = "finished"

    # enter secret level through the secret door
    if game.current_level.level[new_y][new_x] == "S":
        game.return_level_number = game.level_number
        game.return_x = 1
        game.return_y = 1
        game.current_level = SECRET_LEVEL
        game.x = 1
        game.y = 1
        game.moves.clear()

    # return from secret level via stairs up
    if game.current_level.level[new_y][new_x] == "u":
        game.level_number = game.return_level_number
        game.current_level = LEVELS[game.level_number]
        game.x = game.return_x
        game.y = game.return_y
        game.return_level_number = -1
        game.moves.clear()

    if game.current_level.level[new_y][new_x] == "^":
        game.effects.append(Flash(x=new_x, y=new_y, countdown=255))
        game.current_level.level[new_y][new_x] = "."
        if game.moves:
            game.moves[-1].finished = lambda g: take_damage(g, ignore_shield=True)
        else:
            take_damage(game, ignore_shield=True)

    check_teleporters(game)
    check_collision(game)
    check_pressure_plates(game)


def take_damage(game: DungeonGame, ignore_shield: bool = False) -> None:
    # enforce cooldown first so rapid hits don't stack
    current_time = time.time()
    if current_time - game.last_damage_time < 2.0:
        return
    game.last_damage_time = current_time

    # shield blocks damage but breaks after 2 hits
    if not ignore_shield and "shield" in game.items and game.shield_hits > 0:
        game.shield_hits -= 1
        if game.shield_hits <= 0:
            game.items.remove("shield")
        return

    game.health -= 1
    damage_sound.play()
    if game.health <= 0:
        game.status = "game over"


def collect_coin(game: DungeonGame) -> None:
    game.coins += 1
    coin_sound.play()


def collect_key(game: DungeonGame) -> None:
    game.items.append("key")


def collect_potion(game: DungeonGame) -> None:
    game.health = min(10, game.health + 3)


def close_secret_door(game: DungeonGame) -> None:
    game.current_level.level[1][0] = "#"


def parse_skeletons(level_map: list[list[str]]) -> list[Skeleton]:
    skeletons = []
    for y in range(len(level_map)):
        for x in range(len(level_map[y])):
            if level_map[y][x] == "s":
                skeletons.append(Skeleton(x=x, y=y))
                level_map[y][x] = "."
    return skeletons


LEVELS = []
SECRET_LEVEL = None


def start_game() -> DungeonGame:
    global LEVELS, SECRET_LEVEL
    from levels import create_levels

    LEVELS, SECRET_LEVEL = create_levels()

    game = DungeonGame(x=1, y=1, current_level=LEVELS[0])
    game.effects.append(FadeIn(x=game.x, y=game.y, countdown=255))
    return game
