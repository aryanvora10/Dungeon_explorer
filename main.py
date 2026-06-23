"""
graphics engine for 2D games
"""

import os
import numpy as np
import cv2

from sound import play_music, stop_music, victory_sound
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

    # draw dungeon tiles
    for y, row in enumerate(game.current_level.level):
        for x, tile in enumerate(row):
            if tile in SYMBOLS:
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
    return frame


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


def show_game_over_animation(last_frame):
    if last_frame is None:
        last_frame = np.zeros((SCREEN_SIZE_Y, SCREEN_SIZE_X, 3), np.uint8)

    # Step 1: Fade to black over 60 frames
    for i in range(60):
        alpha = i / 60.0
        target = np.zeros_like(last_frame)  # Solid black
        frame = cv2.addWeighted(last_frame, 1.0 - alpha, target, alpha, 0)
        cv2.imshow(GAME_TITLE, frame)
        cv2.waitKey(16)

    # Step 2: Flashing text on black background over 180 frames
    base_frame = np.zeros_like(last_frame)  # Solid black

    text = "GAME OVER"
    font = cv2.FONT_HERSHEY_TRIPLEX
    scale_factor = TILE_SIZE / 64.0
    text_scale = scale_factor * 1.6
    thickness = max(2, int(4 * text_scale))

    (text_width, text_height), _ = cv2.getTextSize(text, font, text_scale, thickness)
    text_x = (SCREEN_SIZE_X - text_width) // 2
    text_y = (SCREEN_SIZE_Y + text_height) // 2

    sub_text = "YOUR JOURNEY ENDS HERE"
    sub_font = cv2.FONT_HERSHEY_SIMPLEX
    sub_scale = scale_factor * 0.6
    sub_thickness = max(1, int(2 * sub_scale))
    (sub_w, sub_h), _ = cv2.getTextSize(sub_text, sub_font, sub_scale, sub_thickness)
    sub_x = (SCREEN_SIZE_X - sub_w) // 2
    sub_y = text_y + int(80 * scale_factor)

    for i in range(180):  # 3 seconds of flashing
        frame = base_frame.copy()

        # Flash / blink effect: visible for 20 frames, hidden for 10 frames
        is_visible = (i % 30) < 20

        if is_visible:
            # Draw shadow
            cv2.putText(
                frame,
                text,
                (text_x + 4, text_y + 4),
                font,
                text_scale,
                (0, 0, 0),
                thickness,
                cv2.LINE_AA,
            )
            # Draw main text (Red)
            cv2.putText(
                frame,
                text,
                (text_x, text_y),
                font,
                text_scale,
                (0, 0, 255),
                thickness,
                cv2.LINE_AA,
            )

            # Draw subtitle shadow
            cv2.putText(
                frame,
                sub_text,
                (sub_x + 2, sub_y + 2),
                sub_font,
                sub_scale,
                (0, 0, 0),
                sub_thickness,
                cv2.LINE_AA,
            )
            # Draw subtitle main text (White/light gray)
            cv2.putText(
                frame,
                sub_text,
                (sub_x, sub_y),
                sub_font,
                sub_scale,
                (200, 200, 200),
                sub_thickness,
                cv2.LINE_AA,
            )

        cv2.imshow(GAME_TITLE, frame)

        key = cv2.waitKey(16) & 0xFF
        if key != 255:
            break


def show_victory_animation(last_frame):
    stop_music()
    victory_sound.play()
    if last_frame is None:
        last_frame = np.zeros((SCREEN_SIZE_Y, SCREEN_SIZE_X, 3), np.uint8)

    # Step 1: Fade to black over 60 frames
    for i in range(60):
        alpha = i / 60.0
        target = np.zeros_like(last_frame)  # Solid black
        frame = cv2.addWeighted(last_frame, 1.0 - alpha, target, alpha, 0)
        cv2.imshow(GAME_TITLE, frame)
        cv2.waitKey(16)

    # Step 2: Flashing text on black background over 180 frames
    base_frame = np.zeros_like(last_frame)  # Solid black

    text = "VICTORY!"
    font = cv2.FONT_HERSHEY_TRIPLEX
    scale_factor = TILE_SIZE / 64.0
    text_scale = scale_factor * 1.6
    thickness = max(2, int(4 * text_scale))

    (text_width, text_height), _ = cv2.getTextSize(text, font, text_scale, thickness)
    text_x = (SCREEN_SIZE_X - text_width) // 2
    text_y = (SCREEN_SIZE_Y + text_height) // 2

    sub_text = "YOU CONQUERED THE DUNGEON"
    sub_font = cv2.FONT_HERSHEY_SIMPLEX
    sub_scale = scale_factor * 0.6
    sub_thickness = max(1, int(2 * sub_scale))
    (sub_w, sub_h), _ = cv2.getTextSize(sub_text, sub_font, sub_scale, sub_thickness)
    sub_x = (SCREEN_SIZE_X - sub_w) // 2
    sub_y = text_y + int(80 * scale_factor)

    for i in range(180):  # 3 seconds of flashing
        frame = base_frame.copy()

        # Flash / blink effect: visible for 20 frames, hidden for 10 frames
        is_visible = (i % 30) < 20

        if is_visible:
            # Draw shadow
            cv2.putText(
                frame,
                text,
                (text_x + 4, text_y + 4),
                font,
                text_scale,
                (0, 0, 0),
                thickness,
                cv2.LINE_AA,
            )
            # Draw main text (Gold/Yellow: BGR 0, 215, 255)
            cv2.putText(
                frame,
                text,
                (text_x, text_y),
                font,
                text_scale,
                (0, 215, 255),
                thickness,
                cv2.LINE_AA,
            )

            # Draw subtitle shadow
            cv2.putText(
                frame,
                sub_text,
                (sub_x + 2, sub_y + 2),
                sub_font,
                sub_scale,
                (0, 0, 0),
                sub_thickness,
                cv2.LINE_AA,
            )
            # Draw subtitle main text (White/light gray)
            cv2.putText(
                frame,
                sub_text,
                (sub_x, sub_y),
                sub_font,
                sub_scale,
                (200, 200, 200),
                sub_thickness,
                cv2.LINE_AA,
            )

        cv2.imshow(GAME_TITLE, frame)

        key = cv2.waitKey(16) & 0xFF
        if key != 255:
            break


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
    current_level = game.current_level
    last_frame = None
    while game.status == "running":
        # clear leftover animations from the old level on transitions
        if game.current_level is not current_level:
            moves.clear()
            current_level = game.current_level
            # reset monster/box move states so they aren't stuck mid-animation
            for m in current_level.monsters:
                m.move = None
            for b in current_level.boxes:
                b.move = None
        last_frame = draw(game, images, moves)
        update(game)
        update_effects(game)
        moves = clean_moves(game, moves)
        clean_explosions(game)
        queued_move, pulling = handle_keyboard(game)
        if not is_player_moving(moves):
            move_player(game, queued_move, pulling)

    if game.status == "game over":
        show_game_over_animation(last_frame)
    elif game.status == "finished":
        show_victory_animation(last_frame)

    cv2.destroyAllWindows()
    stop_music()


if __name__ == "__main__":
    main()
