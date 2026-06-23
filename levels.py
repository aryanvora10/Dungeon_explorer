"""
Level definitions for Dungeon Explorer
"""

from game import parse_level, Level, Teleporter, Fireball, Skeleton, Box, PressurePlate


def create_levels():
    """Create and return all game levels."""

    # Level 1: Compact Labyrinth (15x11)
    level_map_1 = parse_level(
        [
            "###############",
            "#.....#...$..K.",
            "#.###.#.###.###",
            "#$#...#.#^#...#",
            "#$###...^^###.#",
            "#$#h..#.......#",
            "#$##.######^..#",  
            "#$#.......#^^.#",
            "#$#...P.#.###.#",
            ".$#.....#D..x##",
            "###############",
        ]
    )

    # Level 2: The Gauntlet (15x11)
    level_map_2 = parse_level(
        [
            "###############",
            "#..$..#.^.#.K.#",
            "#..#..#.#.#...#",
            "#.#..$..#...#.#",
            "#.###.###.###.#",
            "#h..P.#...P.^.#",
            "#.###.#.###.###",
            "#.#.^.#.$D#.$.#",
            "#.#.###.#.###h#",
            "#.$.....#..Dx##",
            "###############",
        ]
    )

    # Secret Level: Clustered Rewards (15x11)
    level_map_secret = parse_level(
        [
            "###############",
            "#.............#",
            "#.$$.$$$.$$.$u#",
            "#.$$.$$$.$$.$.#",
            "#.............#",
            "#.$$.$$$.$$.$.#",
            "#.$$.$$$.$$.$.#",
            "#.............#",
            "#.$$.$$$.$$.$.#",
            "#h............#",
            "###############",
        ]
    )

    level_1 = Level(
        level=level_map_1,
        has_secret_door=True,
        teleporters=[
            Teleporter(x=0, y=9, target_x=13, target_y=1), 
            Teleporter(x=14, y=1, target_x=1, target_y=1)
        ],
        monsters=[
            Fireball(x=9, y=1, direction="left"),
            Fireball(x=13, y=7, direction="up"),
            Skeleton(x=3, y=3, direction="right"),
            Skeleton(x=7, y=7, direction="left"),
        ],
        boxes=[Box(x=3, y=7)],
        pressure_plates=[PressurePlate(x=6, y=8, gate_x=6, gate_y=6)],
    )

    level_2 = Level(
        level=level_map_2,
        has_secret_door=False,
        teleporters=[
            Teleporter(x=1, y=1, target_x=13, target_y=2),
            Teleporter(x=13, y=1, target_x=1, target_y=2),
        ],
        monsters=[
            Fireball(x=7, y=1, direction="down"),
            Fireball(x=5, y=9, direction="left"),
            Skeleton(x=3, y=3, direction="right"),
            Skeleton(x=11, y=5, direction="left"),
            Skeleton(x=9, y=7, direction="left"),
            Skeleton(x=9, y=9, direction="left"),
        ],
        boxes=[Box(x=3, y=5), Box(x=9, y=5)],
        pressure_plates=[
            PressurePlate(x=4, y=5, gate_x=4, gate_y=4),
            PressurePlate(x=10, y=5, gate_x=9, gate_y=7),
        ],
    )

    secret_level = Level(
        level=level_map_secret,
        monsters=[
            Fireball(x=7, y=1, direction="down", speed=1),
            Fireball(x=7, y=9, direction="up", speed=1),
            Skeleton(x=1, y=4, direction="right", speed=1),
            Skeleton(x=13, y=7, direction="left", speed=1),
        ],
    )

    levels = [level_1, level_2]
    return levels, secret_level
