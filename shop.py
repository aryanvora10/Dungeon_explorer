import os
import numpy as np
import cv2
from pydantic import BaseModel
from sound import select_sound, wrong_choice_sound
from config import TILE_SIZE, read_image, SCREEN_SIZE_X, SCREEN_SIZE_Y

TILE_PATH = os.path.split(__file__)[0] + "/tiles"
SHOP_BG_PATH = os.path.split(__file__)[0] + "/images/shop_small.png"

GAME_TITLE = "Dungeon Explorer"

# Calculate the scaling factor based on dynamic TILE_SIZE (original base was 64)
SHOP_SCALE = TILE_SIZE / 64.0
SHOP_WIDTH = int(640 * SHOP_SCALE)
SHOP_HEIGHT = int(640 * SHOP_SCALE)

# Centering offsets on the fullscreen canvas
SHOP_OFFSET_X = (SCREEN_SIZE_X - SHOP_WIDTH) // 2
SHOP_OFFSET_Y = (SCREEN_SIZE_Y - SHOP_HEIGHT) // 2

# shop layout constants (scaled)
SHOP_COLS = 3
SHOP_START_X = int(80 * SHOP_SCALE)
SHOP_START_Y = int(120 * SHOP_SCALE)
SHOP_SPACING_X = int(180 * SHOP_SCALE)
SHOP_SPACING_Y = int(200 * SHOP_SCALE)
ITEM_SLOT_SIZE = TILE_SIZE + int(20 * SHOP_SCALE)  # border around each item

# colors (BGR)
COLOR_BG = (30, 20, 15)
COLOR_PANEL = (50, 40, 30)
COLOR_BORDER = (255, 180, 100)
COLOR_SELECTED = (100, 255, 255)
COLOR_GOLD = (0, 215, 255)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (160, 160, 160)
COLOR_RED = (80, 80, 255)
COLOR_GREEN = (80, 220, 80)
COLOR_TITLE = (200, 160, 255)
COLOR_DESC_BG = (60, 50, 40)


class ShopItem(BaseModel):
    name: str
    tile: str
    cost: int
    description: str


SHOP_INVENTORY = [
    ShopItem(
        name="Long Sword",
        tile="long_sword",
        cost=5,
        description="A fine blade. +3 attack damage.",
    ),
    ShopItem(
        name="Short Sword",
        tile="short_sword",
        cost=3,
        description="Quick and light. +1 attack damage.",
    ),
    ShopItem(
        name="Bow", tile="bow", cost=4, description="Strike from afar. Ranged attack."
    ),
    ShopItem(
        name="Armor",
        tile="armor",
        cost=8,
        description="Heavy plate. Reduces damage taken.",
    ),
    ShopItem(
        name="Shield",
        tile="shield",
        cost=6,
        description="Block incoming hits. +2 defense.",
    ),
    ShopItem(
        name="Potion", tile="potion", cost=2, description="Restores 3 health points."
    ),
]


class Shop(BaseModel):
    items: list[ShopItem]
    selected: int = 0
    status: str = "open"  # "open" or "closed"


def read_shop_images():
    """Read only the images needed for the shop."""
    needed = {item.tile for item in SHOP_INVENTORY}
    needed.add("coin")
    images = {}
    for name in needed:
        path = os.path.join(TILE_PATH, f"{name}.png")
        if os.path.exists(path):
            images[name] = read_image(path)
    return images


def get_item_slot_rect(index):
    """Get the (x, y) top-left pixel position of an item slot."""
    col = index % SHOP_COLS
    row = index // SHOP_COLS
    # Incorporate the screen offsets and scaled spacing
    x = SHOP_OFFSET_X + SHOP_START_X + col * SHOP_SPACING_X
    y = SHOP_OFFSET_Y + SHOP_START_Y + row * SHOP_SPACING_Y
    return x, y


def draw_shop(game, shop, images):
    """Draw the shop screen."""
    frame = np.zeros((SCREEN_SIZE_Y, SCREEN_SIZE_X, 3), np.uint8)

    # draw background image placed in the center
    bg = cv2.imread(SHOP_BG_PATH)
    if bg is not None:
        bg = cv2.resize(bg, (SHOP_WIDTH, SHOP_HEIGHT))
        frame[
            SHOP_OFFSET_Y : SHOP_OFFSET_Y + SHOP_HEIGHT,
            SHOP_OFFSET_X : SHOP_OFFSET_X + SHOP_WIDTH,
        ] = bg
    else:
        frame[
            SHOP_OFFSET_Y : SHOP_OFFSET_Y + SHOP_HEIGHT,
            SHOP_OFFSET_X : SHOP_OFFSET_X + SHOP_WIDTH,
        ] = COLOR_BG

    # draw title
    cv2.putText(
        frame,
        "~ DUNGEON SHOP ~",
        org=(
            SHOP_OFFSET_X + int(130 * SHOP_SCALE),
            SHOP_OFFSET_Y + int(60 * SHOP_SCALE),
        ),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=1.2 * SHOP_SCALE,
        color=COLOR_TITLE,
        thickness=max(1, int(3 * SHOP_SCALE)),
    )

    # draw coin count
    coin_img = images.get("coin")
    if coin_img is not None:
        coin_size = int(28 * SHOP_SCALE)
        small_coin = cv2.resize(
            coin_img[:, :, :3] if coin_img.shape[2] >= 3 else coin_img,
            (coin_size, coin_size),
        )
        y1 = SHOP_OFFSET_Y + int(72 * SHOP_SCALE)
        x1 = SHOP_OFFSET_X + int(20 * SHOP_SCALE)
        frame[y1 : y1 + coin_size, x1 : x1 + coin_size] = small_coin
    cv2.putText(
        frame,
        str(game.coins),
        org=(
            SHOP_OFFSET_X + int(55 * SHOP_SCALE),
            SHOP_OFFSET_Y + int(96 * SHOP_SCALE),
        ),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.8 * SHOP_SCALE,
        color=COLOR_GOLD,
        thickness=max(1, int(2 * SHOP_SCALE)),
    )

    # draw instruction
    cv2.putText(
        frame,
        "WASD: move  ENTER: buy  Q: leave",
        org=(
            SHOP_OFFSET_X + int(100 * SHOP_SCALE),
            SHOP_OFFSET_Y + SHOP_HEIGHT - int(20 * SHOP_SCALE),
        ),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.5 * SHOP_SCALE,
        color=COLOR_GRAY,
        thickness=max(1, int(1 * SHOP_SCALE)),
    )

    # draw each item slot
    for i, item in enumerate(shop.items):
        x, y = get_item_slot_rect(i)
        is_selected = i == shop.selected

        # draw slot background
        cv2.rectangle(
            frame,
            (x - int(10 * SHOP_SCALE), y - int(10 * SHOP_SCALE)),
            (
                x + TILE_SIZE + int(10 * SHOP_SCALE),
                y + TILE_SIZE + int(10 * SHOP_SCALE),
            ),
            COLOR_PANEL,
            -1,
        )

        # draw border (highlighted if selected)
        border_color = COLOR_SELECTED if is_selected else COLOR_BORDER
        thickness = max(1, int(3 * SHOP_SCALE)) if is_selected else 1
        cv2.rectangle(
            frame,
            (x - int(10 * SHOP_SCALE), y - int(10 * SHOP_SCALE)),
            (
                x + TILE_SIZE + int(10 * SHOP_SCALE),
                y + TILE_SIZE + int(10 * SHOP_SCALE),
            ),
            border_color,
            thickness,
        )

        # draw item tile
        tile_img = images.get(item.tile)
        if tile_img is not None:
            img = tile_img[:, :, :3] if tile_img.shape[2] >= 3 else tile_img
            if tile_img.shape[2] == 4:
                # alpha-aware draw
                mask = tile_img[:, :, 3] > 0
                roi = frame[y : y + TILE_SIZE, x : x + TILE_SIZE]
                roi[mask] = tile_img[:, :, :3][mask]
            else:
                frame[y : y + TILE_SIZE, x : x + TILE_SIZE] = img

        # draw item name below slot
        cv2.putText(
            frame,
            item.name,
            org=(x - int(8 * SHOP_SCALE), y + TILE_SIZE + int(30 * SHOP_SCALE)),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.45 * SHOP_SCALE,
            color=COLOR_WHITE,
            thickness=max(1, int(1 * SHOP_SCALE)),
        )

        # draw cost below name
        cost_color = COLOR_GREEN if game.coins >= item.cost else COLOR_RED
        cv2.putText(
            frame,
            f"{item.cost} coins",
            org=(x - int(5 * SHOP_SCALE), y + TILE_SIZE + int(50 * SHOP_SCALE)),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.4 * SHOP_SCALE,
            color=cost_color,
            thickness=max(1, int(1 * SHOP_SCALE)),
        )

        # draw "OWNED" if already in inventory
        if item.tile in game.items:
            cv2.putText(
                frame,
                "OWNED",
                org=(x + int(2 * SHOP_SCALE), y + TILE_SIZE // 2 + int(5 * SHOP_SCALE)),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.5 * SHOP_SCALE,
                color=COLOR_GREEN,
                thickness=max(1, int(2 * SHOP_SCALE)),
            )

    # draw description panel for selected item
    selected_item = shop.items[shop.selected]
    desc_y = SHOP_OFFSET_Y + SHOP_HEIGHT - int(100 * SHOP_SCALE)
    cv2.rectangle(
        frame,
        (SHOP_OFFSET_X + int(30 * SHOP_SCALE), desc_y - int(10 * SHOP_SCALE)),
        (
            SHOP_OFFSET_X + SHOP_WIDTH - int(30 * SHOP_SCALE),
            desc_y + int(55 * SHOP_SCALE),
        ),
        COLOR_DESC_BG,
        -1,
    )
    cv2.rectangle(
        frame,
        (SHOP_OFFSET_X + int(30 * SHOP_SCALE), desc_y - int(10 * SHOP_SCALE)),
        (
            SHOP_OFFSET_X + SHOP_WIDTH - int(30 * SHOP_SCALE),
            desc_y + int(55 * SHOP_SCALE),
        ),
        COLOR_BORDER,
        1,
    )

    cv2.putText(
        frame,
        selected_item.name,
        org=(SHOP_OFFSET_X + int(45 * SHOP_SCALE), desc_y + int(15 * SHOP_SCALE)),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.6 * SHOP_SCALE,
        color=COLOR_GOLD,
        thickness=max(1, int(2 * SHOP_SCALE)),
    )
    cv2.putText(
        frame,
        selected_item.description,
        org=(SHOP_OFFSET_X + int(45 * SHOP_SCALE), desc_y + int(40 * SHOP_SCALE)),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.4 * SHOP_SCALE,
        color=COLOR_GRAY,
        thickness=max(1, int(1 * SHOP_SCALE)),
    )

    cv2.imshow(GAME_TITLE, frame)
    return frame


def handle_shop_keyboard():
    """Handle keyboard input for the shop. Returns action string."""
    key = cv2.waitKey(1) & 0xFF
    if key == 255:
        return None
    char = chr(key)
    if char in ("q", "Q"):
        return "close"
    if char == "a":
        return "left"
    if char == "d":
        return "right"
    if char == "w":
        return "up"
    if char == "s":
        return "down"
    if key == 13:  # Enter key
        return "buy"
    return None


def visit_shop(game):
    """Open the shop screen. Player can browse and buy items."""
    images = read_shop_images()
    shop = Shop(items=SHOP_INVENTORY)

    while shop.status == "open":
        draw_shop(game, shop, images)
        action = handle_shop_keyboard()

        if action == "close":
            shop.status = "closed"

        elif action == "left":
            if shop.selected % SHOP_COLS > 0:
                shop.selected -= 1
                select_sound.play()

        elif action == "right":
            if shop.selected % SHOP_COLS < SHOP_COLS - 1 and shop.selected + 1 < len(
                shop.items
            ):
                shop.selected += 1
                select_sound.play()

        elif action == "up":
            if shop.selected - SHOP_COLS >= 0:
                shop.selected -= SHOP_COLS
                select_sound.play()

        elif action == "down":
            if shop.selected + SHOP_COLS < len(shop.items):
                shop.selected += SHOP_COLS
                select_sound.play()

        elif action == "buy":
            item = shop.items[shop.selected]
            if item.tile not in game.items and game.coins >= item.cost:
                game.coins -= item.cost
                game.items.append(item.tile)
                # shield gets 2 uses before it breaks
                if item.tile == "shield":
                    game.shield_hits = 2
                select_sound.play()
            else:
                wrong_choice_sound.play()

    # We do not destroy the window here because the shop runs inside the same fullscreen game window.
    # When shop closes, main game drawing automatically takes over.
    pass
