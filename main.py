"""
graphics engine for 2D games
"""

import os
import numpy as np
import cv2

from sound import play_music, stop_music
from cutscene import show_cutscene
from game import start_game, move_player, update, update_effects
from config import (
    TILE_SIZE,
    SCREEN_SIZE_X,
    SCREEN_SIZE_Y,
    read_images,
    OFFSET_X,
    OFFSET_Y,
)
from shop import visit_shop

# title of the game window
GAME_TITLE = "Dungeon Explorer"

# map keyboard keys to move commands
MOVES = {
    "a": "left",
    "d": "right",
    "w": "up",
    "s": "down",
}

SYMBOLS = {
    ".": "floor",
    "#": "wall",
    "x": "stairs_down",
    "u": "stairs_up",
    "$": "coin",
    "^": "trap",
    "S": "secret_door",
    "K": "key",
    "D": "closed_door",
    "d": "open_door",
    "h": "potion",
    "P": "slot",
    "G": "closed_door",
}

# Shift+WASD keys (uppercase) for pulling
PULL_MOVES = {
    "A": "left",
    "D": "right",
    "W": "up",
    "S": "down",
}

play_music()


def draw_tile(frame, x, y, image, xbase=0, ybase=0) -> None:
    # calculate screen position in pixels relative to centering offsets
    xpos = int(round(OFFSET_X + xbase + x * TILE_SIZE))
    ypos = int(round(OFFSET_Y + ybase + y * TILE_SIZE))

    h, w = image.shape[:2]

    # Target rect coordinates on frame
    x1, y1 = xpos, ypos
    x2, y2 = xpos + w, ypos + h

    # Clip target rect to frame boundaries
    tx1 = max(0, x1)
    ty1 = max(0, y1)
    tx2 = min(SCREEN_SIZE_X, x2)
    ty2 = min(SCREEN_SIZE_Y, y2)

    if tx1 >= tx2 or ty1 >= ty2:
        return  # Completely off-screen
        
    # Source rect coordinates in image
    ix1 = tx1 - x1
    iy1 = ty1 - y1
    ix2 = tx2 - x1
    iy2 = ty2 - y1

    tile_slice = image[iy1:iy2, ix1:ix2]
    roi = frame[ty1:ty2, tx1:tx2]

    if image.shape[2] == 4:
        mask = tile_slice[:, :, 3] > 0
        roi[mask] = tile_slice[:, :, :3][mask]
    else:
        roi[:] = tile_slice


def draw_move(frame, move, images) -> None:
    # move.progress is a float in [0.0, 1.0] representing tile progress fraction.
    if move.tile == "wall":
        # For doors/walls, the original speed_x/y was 2 or -2 (representing 1 tile displacement)
        tile_offset_x = move.speed_x / 2.0
        tile_offset_y = move.speed_y / 2.0
        speed_multiplier = 2.0
    else:
        tile_offset_x = move.speed_x
        tile_offset_y = move.speed_y
        speed_multiplier = 1.0

    draw_tile(
        frame,
        x=move.from_x,
        y=move.from_y,
        image=images[move.tile],
        xbase=move.progress * tile_offset_x * TILE_SIZE,
        ybase=move.progress * tile_offset_y * TILE_SIZE,
    )
    # move.speed is originally pixels per frame (assuming 64px TILE_SIZE).
    # We divide by 32.0 to double the animation speed and make movement feel responsive.
    move.progress += (move.speed * speed_multiplier) / 32.0


def clean_moves(game, moves):
    result = []
    for m in moves:
        if m.progress < 1.0:
            result.append(m)
        else:
            m.complete = True
            if m.finished is not None:
                m.finished(game)
    return result


def is_player_moving(moves):
    return any([m for m in moves if m.tile == "player"])


def draw_explosion(frame, explosion, images):
    framex = explosion.frame % 4
    framey = explosion.frame // 4
    tile = images["explosion_pixelfied"][
        framey * TILE_SIZE : (framey + 1) * TILE_SIZE,
        framex * TILE_SIZE : (framex + 1) * TILE_SIZE,
    ]
    draw_tile(frame, x=explosion.x, y=explosion.y, image=tile)
    # increase the frame here and set the explosion to complete if necessary
    # also handle delays here
    explosion.delay += 1
    if explosion.delay >= explosion.max_delay:
        explosion.delay = 0
        explosion.frame += 1
        if explosion.frame >= explosion.max_frame:
            explosion.complete = True


def clean_explosions(game):
    """updates each explosion in the game"""
    result = []
    for e in game.explosions:
        if not e.complete:
            result.append(e)
    game.explosions = result


def draw_ui_element(frame, xpos, ypos, image) -> None:
    """Draws an image of any size at exact pixel coordinates with robust screen clipping."""
    h, w = image.shape[:2]

    x1, y1 = xpos, ypos
    x2, y2 = xpos + w, ypos + h

    tx1 = max(0, x1)
    ty1 = max(0, y1)
    tx2 = min(SCREEN_SIZE_X, x2)
    ty2 = min(SCREEN_SIZE_Y, y2)

    if tx1 >= tx2 or ty1 >= ty2:
        return

    ix1 = tx1 - x1
    iy1 = ty1 - y1
    ix2 = tx2 - x1
    iy2 = ty2 - y1

    img_slice = image[iy1:iy2, ix1:ix2]
    roi = frame[ty1:ty2, tx1:tx2]

    if image.shape[2] == 4:
        mask = img_slice[:, :, 3] > 0
        roi[mask] = img_slice[:, :, :3][mask]
    else:
        roi[:] = img_slice


_FRAME_BUFFER = None


def draw(game, images, moves):
    global _FRAME_BUFFER
    # Initialize or reuse frame buffer to avoid expensive allocations
    if _FRAME_BUFFER is None or _FRAME_BUFFER.shape[:2] != (
        SCREEN_SIZE_Y,
        SCREEN_SIZE_X,
    ):
        _FRAME_BUFFER = np.zeros((SCREEN_SIZE_Y, SCREEN_SIZE_X, 3), np.uint8)
    else:
        _FRAME_BUFFER.fill(0)
    frame = _FRAME_BUFFER

    scale_factor = TILE_SIZE / 64.0
    UI_PANEL_START_X = 15 * TILE_SIZE

    # Resize the image proportionally
    heart_size = int(32 * scale_factor)
    small_heart = cv2.resize(images["heart"], (heart_size, heart_size))

    # Draw the smaller hearts
    for i in range(game.health):
        xpos = int(
            OFFSET_X
            + UI_PANEL_START_X
            + int(40 * scale_factor)
            + (i % 3) * int(36 * scale_factor)
        )
        ypos = int(
            OFFSET_Y + int(100 * scale_factor) + (i // 3) * int(36 * scale_factor)
        )
        draw_ui_element(frame, xpos, ypos, small_heart)

    # tiles that are items on top of a floor
    FLOOR_ITEMS = {"$", "^", "K", "h"}

    # draw dungeon tiles
    for y, row in enumerate(game.current_level.level):
        for x, tile in enumerate(row):
            if tile in SYMBOLS:
                if tile in FLOOR_ITEMS:
                    draw_tile(frame, x=x, y=y, image=images["floor"])
                draw_tile(frame, x=x, y=y, image=images[SYMBOLS[tile]])

    # draw teleporters
    for t in game.current_level.teleporters:
        draw_tile(frame, x=t.x, y=t.y, image=images["teleporter"])

    # draw enemies
    # draw boxes
    for box in game.current_level.boxes:
        if box.move is None or box.move.complete:
            draw_tile(frame, x=box.x, y=box.y, image=images["statue_orb"])

    for m in game.current_level.monsters:
        if m.move is None or m.move.complete:
            draw_tile(frame, x=m.x, y=m.y, image=images[m.tile])

    # Draw coin count text
    cv2.putText(
        frame,
        str(game.coins),
        org=(
            int(OFFSET_X + UI_PANEL_START_X + int(120 * scale_factor)),
            int(OFFSET_Y + int(78 * scale_factor)),
        ),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=1.5 * scale_factor,
        color=(255, 128, 128),
        thickness=max(1, int(3 * scale_factor)),
    )
    # Draw coin icon
    draw_tile(
        frame,
        x=0,
        y=0,
        image=images["coin"],
        xbase=UI_PANEL_START_X + int(40 * scale_factor),
        ybase=int(30 * scale_factor),
    )

    # Draw inventory items
    for i, item in enumerate(game.items):
        y = i // 2
        x = i % 2
        draw_tile(
            frame,
            xbase=UI_PANEL_START_X + int(40 * scale_factor),
            ybase=int(360 * scale_factor),
            x=x,
            y=y,
            image=images[item],
        )

    # draw player
    while game.moves:
        moves.append(game.moves.pop())
    if not is_player_moving(moves):
        draw_tile(frame=frame, x=game.x, y=game.y, image=images["player"])

    # draw everything that moves
    for m in moves:
        draw_move(frame=frame, move=m, images=images)

    # draw explosions
    for explosion in game.explosions:
        draw_explosion(frame, explosion, images)

    # draw special effects
    for e in game.effects:
        e.draw(frame)

    # display complete image
    cv2.imshow(GAME_TITLE, frame)


def handle_keyboard(game):
    """keys are mapped to move commands. Shift+WASD returns pulling mode."""
    key = chr(cv2.waitKey(1) & 0xFF)
    if key in ("q", "Q"):
        game.status = "exited"
    if key == "b":
        visit_shop(game)
        return None, False

    # Check for pull (Shift+WASD = uppercase)
    if key in PULL_MOVES:
        return PULL_MOVES[key], True
    if key in MOVES:
        return MOVES[key], False
    return None, False


def main():
    if not show_cutscene():
        cv2.destroyAllWindows()
        stop_music()
        return

    # Create and configure the window to be fullscreen
    cv2.namedWindow(GAME_TITLE, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(GAME_TITLE, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    images = read_images()
    game = start_game()
    queued_move = None
    moves = []
    while game.status == "running":
        draw(game, images, moves)
        update(game)
        update_effects(game)
        moves = clean_moves(game, moves)
        clean_explosions(game)
        queued_move, pulling = handle_keyboard(game)
        if not is_player_moving(moves):
            move_player(game, queued_move, pulling)

    cv2.destroyAllWindows()
    stop_music()


if __name__ == "__main__":
    main()
