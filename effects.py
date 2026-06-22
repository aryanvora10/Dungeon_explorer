import numpy as np
import cv2
from pydantic import BaseModel
from config import TILE_SIZE, OFFSET_X, OFFSET_Y


class Effect(BaseModel):

    x: int
    y: int
    countdown: int

    def draw(self, frame):
        pass


class RandomBlur(Effect):

    def draw(self, frame):
        random_tile = np.random.randint(
            0, 255, size=(TILE_SIZE, TILE_SIZE, 3), dtype=np.uint8
        )
        y_start = OFFSET_Y + self.y * TILE_SIZE
        x_start = OFFSET_X + self.x * TILE_SIZE
        frame[y_start : y_start + TILE_SIZE, x_start : x_start + TILE_SIZE] = (
            random_tile
        )


class FadeIn(Effect):

    def draw(self, frame):
        y_start = OFFSET_Y + self.y * TILE_SIZE
        x_start = OFFSET_X + self.x * TILE_SIZE
        tile = frame[y_start : y_start + TILE_SIZE, x_start : x_start + TILE_SIZE]
        tile[tile > (255 - self.countdown)] = 0
        frame[y_start : y_start + TILE_SIZE, x_start : x_start + TILE_SIZE] = tile


class Flash(Effect):

    def draw(self, frame):  # <-- numpy array
        frame[frame < self.countdown] = self.countdown
        # if the countdown is bigger than a pixel value:
        #    set pixel to countdown
        # else:
        #    leave pixel as it is
        # frame[:, :] = self.countdown


class ColorText(Effect):

    text: str

    def draw(self, frame):
        if self.countdown % 2 == 0:
            color = (255, 0, 255)
        else:
            color = (0, 255, 255)
        scale_factor = TILE_SIZE / 64.0
        cv2.putText(
            frame,
            self.text,
            org=(OFFSET_X + self.y * TILE_SIZE, OFFSET_Y + self.x * TILE_SIZE),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=1.0 * scale_factor,
            color=color,
            thickness=max(1, int(2 * scale_factor)),
        )
