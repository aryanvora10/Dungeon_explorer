import pytest
import levels
import main
import shop

from game import start_game, move_player
from moves import Move


def test_open_door():
    # 1. prepare test data
    game = start_game()
    assert game.level[3][2] == "d"

    # 2. call the function you want to test
    move_player(game, "right")
    move_player(game, "right")
    move_player(game, "right")

    # 3. check if the result is correct
    assert game.level[3][2] == "."
    assert game.coins == 0
