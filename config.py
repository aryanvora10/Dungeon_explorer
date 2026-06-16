import os
import numpy as np
import cv2

TILE_PATH = os.path.split(__file__)[0] + '/tiles'
TILE_SIZE = 64
SCREEN_SIZE_X, SCREEN_SIZE_Y = 1200, 800


def read_image(filename: str) -> np.ndarray:
    """
    Reads an image from the given filename and doubles its size.
    If the image file does not exist, an error is created.
    """
    img = cv2.imread(filename, cv2.IMREAD_UNCHANGED)  # preserve alpha channel
    if img is None:
        raise IOError(f"Image not found: '{filename}'")
    img = np.kron(img, np.ones((2, 2, 1), dtype=img.dtype))  # double image size
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
