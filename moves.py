from typing import Callable
from pydantic import BaseModel

class Move(BaseModel):
    tile: str
    from_x: int
    from_y: int
    speed_x: int
    speed_y: int
    progress: float = 0.0
    speed: float = 1.0
    complete: bool = False
    finished: Callable = None

def player_move_finished(game):
    print(game.x, game.y)