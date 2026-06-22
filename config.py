import os
import numpy as np
import cv2


def get_screen_resolution() -> tuple[int, int]:
    """Detects screen resolution on Windows with DPI awareness, or returns default 1080p."""
    try:
        import ctypes

        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        if width > 0 and height > 0:
            return width, height
    except Exception:
        pass
    return 1920, 1080


SCREEN_SIZE_X, SCREEN_SIZE_Y = get_screen_resolution()

# Grid is 15x11 tiles. Sidebar width is 3.75 * TILE_SIZE. Total width is 18.75 tiles.
TILE_SIZE = int(min(SCREEN_SIZE_X / 18.75, SCREEN_SIZE_Y / 11))
if TILE_SIZE < 32:
    TILE_SIZE = 32

GAME_BOARD_W = 15 * TILE_SIZE
UI_PANEL_W = int(3.75 * TILE_SIZE)
TOTAL_GAME_W = GAME_BOARD_W + UI_PANEL_W
TOTAL_GAME_H = 11 * TILE_SIZE

OFFSET_X = (SCREEN_SIZE_X - TOTAL_GAME_W) // 2
OFFSET_Y = (SCREEN_SIZE_Y - TOTAL_GAME_H) // 2

TILE_PATH = os.path.split(__file__)[0] + "/tiles"


def read_image(filename: str) -> np.ndarray:
    """
    Reads an image from the given filename and resizes it to the dynamic TILE_SIZE.
    If the image file does not exist, an error is created.
    """
    img = cv2.imread(filename, cv2.IMREAD_UNCHANGED)  # preserve alpha channel
    if img is None:
        raise IOError(f"Image not found: '{filename}'")
    # Resize to dynamic tile size using nearest-neighbor to preserve pixel art aesthetics.
    # explosion_pixelfied.png is a 4x4 spritesheet, so we scale it to 4 * TILE_SIZE.
    if "explosion_pixelfied" in filename:
        img = cv2.resize(
            img, (4 * TILE_SIZE, 4 * TILE_SIZE), interpolation=cv2.INTER_NEAREST
        )
    else:
        img = cv2.resize(img, (TILE_SIZE, TILE_SIZE), interpolation=cv2.INTER_NEAREST)
    # drop alpha channel if fully opaque (avoids slow blending for walls/floors)
    if img.shape[2] == 4 and np.all(img[:, :, 3] == 255):
        img = img[:, :, :3]
    return img


def read_images():
    return {
        filename[:-4]: read_image(os.path.join(TILE_PATH, filename))
        for filename in os.listdir(TILE_PATH)
        if filename.endswith(".png")
    }
