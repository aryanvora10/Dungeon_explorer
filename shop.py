import os
import numpy as np
import cv2
from pydantic import BaseModel

from config import TILE_SIZE, read_image

TILE_PATH = os.path.split(__file__)[0] + '/tiles'
SHOP_BG_PATH = os.path.split(__file__)[0] + '/shop_small.png'

GAME_TITLE = "Shop"

SCREEN_SIZE_X, SCREEN_SIZE_Y = 640, 640

# shop layout constants
SHOP_COLS = 3
SHOP_START_X = 80
SHOP_START_Y = 120
SHOP_SPACING_X = 180
SHOP_SPACING_Y = 200
ITEM_SLOT_SIZE = TILE_SIZE + 20  # border around each item

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
    ShopItem(name="Long Sword", tile="long_sword", cost=5, description="A fine blade. +3 attack damage."),
    ShopItem(name="Short Sword", tile="short_sword", cost=3, description="Quick and light. +1 attack damage."),
    ShopItem(name="Bow", tile="bow", cost=4, description="Strike from afar. Ranged attack."),
    ShopItem(name="Armor", tile="armor", cost=8, description="Heavy plate. Reduces damage taken."),
    ShopItem(name="Shield", tile="shield", cost=6, description="Block incoming hits. +2 defense."),
    ShopItem(name="Potion", tile="potion", cost=2, description="Restores 3 health points."),
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
    x = SHOP_START_X + col * SHOP_SPACING_X
    y = SHOP_START_Y + row * SHOP_SPACING_Y
    return x, y


def draw_shop(game, shop, images):
    """Draw the shop screen."""
    frame = np.zeros((SCREEN_SIZE_Y, SCREEN_SIZE_X, 3), np.uint8)

    # draw background image
    bg = cv2.imread(SHOP_BG_PATH)
    if bg is not None:
        bg = cv2.resize(bg, (SCREEN_SIZE_X, SCREEN_SIZE_Y))
        frame[:] = bg
    else:
        frame[:] = COLOR_BG

    # draw title
    cv2.putText(frame, "~ DUNGEON SHOP ~",
                org=(130, 60),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=1.2, color=COLOR_TITLE, thickness=3)

    # draw coin count
    coin_img = images.get("coin")
    if coin_img is not None:
        small_coin = cv2.resize(coin_img[:, :, :3] if coin_img.shape[2] >= 3 else coin_img, (28, 28))
        frame[72:100, 20:48] = small_coin
    cv2.putText(frame, str(game.coins),
                org=(55, 96),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.8, color=COLOR_GOLD, thickness=2)

    # draw instruction
    cv2.putText(frame, "WASD: move  ENTER: buy  Q: leave",
                org=(100, SCREEN_SIZE_Y - 20),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.5, color=COLOR_GRAY, thickness=1)

    # draw each item slot
    for i, item in enumerate(shop.items):
        x, y = get_item_slot_rect(i)
        is_selected = (i == shop.selected)

        # draw slot background
        cv2.rectangle(frame, (x - 10, y - 10),
                      (x + TILE_SIZE + 10, y + TILE_SIZE + 10),
                      COLOR_PANEL, -1)

        # draw border (highlighted if selected)
        border_color = COLOR_SELECTED if is_selected else COLOR_BORDER
        thickness = 3 if is_selected else 1
        cv2.rectangle(frame, (x - 10, y - 10),
                      (x + TILE_SIZE + 10, y + TILE_SIZE + 10),
                      border_color, thickness)

        # draw item tile
        tile_img = images.get(item.tile)
        if tile_img is not None:
            img = tile_img[:, :, :3] if tile_img.shape[2] >= 3 else tile_img
            if tile_img.shape[2] == 4:
                # alpha-aware draw
                mask = tile_img[:, :, 3] > 0
                roi = frame[y:y + TILE_SIZE, x:x + TILE_SIZE]
                roi[mask] = tile_img[:, :, :3][mask]
            else:
                frame[y:y + TILE_SIZE, x:x + TILE_SIZE] = img

        # draw item name below slot
        cv2.putText(frame, item.name,
                    org=(x - 8, y + TILE_SIZE + 30),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.45, color=COLOR_WHITE, thickness=1)

        # draw cost below name
        cost_color = COLOR_GREEN if game.coins >= item.cost else COLOR_RED
        cv2.putText(frame, f"{item.cost} coins",
                    org=(x - 5, y + TILE_SIZE + 50),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.4, color=cost_color, thickness=1)

        # draw "OWNED" if already in inventory
        if item.tile in game.items:
            cv2.putText(frame, "OWNED",
                        org=(x + 2, y + TILE_SIZE // 2 + 5),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.5, color=COLOR_GREEN, thickness=2)

    # draw description panel for selected item
    selected_item = shop.items[shop.selected]
    desc_y = SCREEN_SIZE_Y - 100
    cv2.rectangle(frame, (30, desc_y - 10), (SCREEN_SIZE_X - 30, desc_y + 55),
                  COLOR_DESC_BG, -1)
    cv2.rectangle(frame, (30, desc_y - 10), (SCREEN_SIZE_X - 30, desc_y + 55),
                  COLOR_BORDER, 1)

    cv2.putText(frame, selected_item.name,
                org=(45, desc_y + 15),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.6, color=COLOR_GOLD, thickness=2)
    cv2.putText(frame, selected_item.description,
                org=(45, desc_y + 40),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.4, color=COLOR_GRAY, thickness=1)

    cv2.imshow(GAME_TITLE, frame)


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

        elif action == "right":
            if shop.selected % SHOP_COLS < SHOP_COLS - 1 and shop.selected + 1 < len(shop.items):
                shop.selected += 1

        elif action == "up":
            if shop.selected - SHOP_COLS >= 0:
                shop.selected -= SHOP_COLS

        elif action == "down":
            if shop.selected + SHOP_COLS < len(shop.items):
                shop.selected += SHOP_COLS

        elif action == "buy":
            item = shop.items[shop.selected]
            if item.tile not in game.items and game.coins >= item.cost:
                game.coins -= item.cost
                game.items.append(item.tile)

    cv2.destroyWindow(GAME_TITLE)
