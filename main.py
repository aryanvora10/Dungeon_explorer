"""
graphics engine for 2D games
"""
import os
import numpy as np
import cv2

from pygame import mixer
from cutscene import show_cutscene
from game import start_game, move_player,update, update_effects
from config import TILE_SIZE, SCREEN_SIZE_X, SCREEN_SIZE_Y, read_images
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
    "G": "closed_door"
    }

# Shift+WASD keys (uppercase) for pulling
PULL_MOVES = {
    "A": "left",
    "D": "right",
    "W": "up",
    "S": "down",
}

mixer.init()
mixer.music.load("dungeon_theme.flac")
mixer.music.play(loops=-1)


def draw_tile(frame, x, y, image, xbase=0, ybase=0) -> None:
    # calculate screen position in pixels
    xpos = int(round(xbase + x * TILE_SIZE))
    ypos = int(round(ybase + y * TILE_SIZE))
    if image.shape[2] == 4:
        # fast mask copy: only draw non-transparent pixels
        mask = image[:, :, 3] > 0
        roi = frame[ypos : ypos + TILE_SIZE, xpos : xpos + TILE_SIZE]
        roi[mask] = image[:, :, :3][mask]
    else:
        frame[ypos : ypos + TILE_SIZE, xpos : xpos + TILE_SIZE] = image


def draw_move(frame, move, images) -> None:
    draw_tile(frame, x=move.from_x, y=move.from_y, image=images[move.tile], xbase=move.progress * move.speed_x, ybase=move.progress * move.speed_y)
    move.progress += move.speed


def clean_moves(game, moves):
    result = []
    for m in moves:
        if m.progress * max(abs(m.speed_x), abs(m.speed_y)) < TILE_SIZE:
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
    tile = images["explosion_pixelfied"][framey * TILE_SIZE:(framey + 1) * TILE_SIZE, framex * TILE_SIZE:(framex + 1) * TILE_SIZE]
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
    """Draws an image of any size at exact pixel coordinates."""
    h, w = image.shape[:2]
    if image.shape[2] == 4:
        mask = image[:, :, 3] > 0
        roi = frame[ypos : ypos + h, xpos : xpos + w]
        roi[mask] = image[:, :, :3][mask]
    else:
        frame[ypos : ypos + h, xpos : xpos + w] = image


def draw(game, images, moves):
    # initialize screen
    frame = np.zeros((SCREEN_SIZE_Y, SCREEN_SIZE_X, 3), np.uint8)

    # 1. Resize the heart image to be smaller (e.g., 32x32 pixels instead of 64x64)
    small_heart = cv2.resize(images["heart"], (32, 32))

    # 2. Draw the smaller hearts using our new flexible function
    for i in range(game.health):
        # Multiply by 36 to space out the smaller 32px hearts nicely
        xpos = 1000 + (i % 3) * 36  
        ypos = 100 + (i // 3) * 36
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


    cv2.putText(frame,
        str(game.coins),
        org=(1080, 78), # Shifted from 730
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=1.5,
        color=(255, 128, 128),
        thickness=3,
        )
    draw_tile(frame, x=0, y=0, image=images["coin"], xbase=1000, ybase=30) # Shifted from 650    
    
    for i, item in enumerate(game.items):
        y = i // 2  
        x = i % 2   
        draw_tile(frame, xbase=1000, ybase=360, x=x, y=y, image=images[item])
        
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
    show_cutscene()
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
    mixer.music.stop()

if __name__ == '__main__':
    main()
