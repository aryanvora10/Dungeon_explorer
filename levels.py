"""
Level definitions for Dungeon Explorer
"""
from game import parse_level, Level, Teleporter, Fireball, Skeleton, Box, PressurePlate


def create_levels():
    """Create and return all game levels."""

    # Level 1: Compact Labyrinth (15x11)
    level_map_1 = parse_level([
        "###############",
        "#.K...#...$...#",
        "#.###.#.###.###",
        "#.#...#.#^#...#",
        "#.###.###.###.#",
        "#.#h..#.......#",
        "#.###.#####.###",
        "#.#.......#...#",
        "#.#######.###.#",
        "#.$.....#D..x.#",
        "###############"
    ])

    # Level 2: Chaos vs Order (15x11)
    level_map_2 = parse_level([
        "###############",
        "#.......#.....#",
        "#.............#",
        "#.#...#.#.#K#.#",
        "#.............#",
        "#.....#...P...#",
        "#.............#",
        "#...#...#.G.#.#",
        "###.#.###.###.#",
        "#h..$....$.D.x#",
        "###############"
    ])

    # Secret Level: Clustered Rewards (15x11)
    level_map_secret = parse_level([
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
        "###############"
    ])

    level_1 = Level(
        level=level_map_1,
        has_secret_door=True,
        teleporters=[
            Teleporter(x=1, y=9, target_x=13, target_y=1)
        ],
        monsters=[
            Fireball(x=9, y=1, direction="left"),
            Fireball(x=13, y=7, direction="up"),
            Skeleton(x=3, y=3, direction="right"),
            Skeleton(x=7, y=7, direction="left")
        ]
    )

    level_2 = Level(
        level=level_map_2,
        has_secret_door=False,
        monsters=[
            Fireball(x=3, y=1, direction="down"),
            Fireball(x=11, y=5, direction="down"),
            Skeleton(x=5, y=5, direction="left"),
            Skeleton(x=9, y=7, direction="right")
        ],
        boxes=[
            Box(x=3, y=5)
        ],
        pressure_plates=[
            PressurePlate(x=10, y=5, gate_x=10, gate_y=7)
        ]
    )

    secret_level = Level(
        level=level_map_secret,
        monsters=[
            Fireball(x=7, y=1, direction="down"),
            Fireball(x=7, y=9, direction="up"),
            Skeleton(x=1, y=4, direction="right"),
            Skeleton(x=13, y=7, direction="left")
        ]
    )

    levels = [level_1, level_2]
    return levels, secret_level
