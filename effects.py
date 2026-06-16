import numpy as np
import cv2
from pydantic import BaseModel
from config import TILE_SIZE

class Effect(BaseModel):

    x: int
    y: int
    countdown: int

    def draw(self, frame):
        pass


class RandomBlur(Effect):

    def draw(self, frame):
        random_tile = np.random.randint(0, 255, size=(TILE_SIZE, TILE_SIZE, 3), dtype=np.uint8)
        frame[self.y * TILE_SIZE: self.y * TILE_SIZE + TILE_SIZE,
            self.x * TILE_SIZE: self.x * TILE_SIZE + TILE_SIZE] = random_tile


class FadeIn(Effect):

    def draw(self, frame):
        tile = frame[self.y * TILE_SIZE: self.y * TILE_SIZE + TILE_SIZE,
            self.x * TILE_SIZE: self.x * TILE_SIZE + TILE_SIZE]
        tile[tile > (255 - self.countdown)] = 0
        frame[self.y * TILE_SIZE: self.y * TILE_SIZE + TILE_SIZE,
            self.x * TILE_SIZE: self.x * TILE_SIZE + TILE_SIZE] = tile

class Flash(Effect):

    def draw(self, frame):
        overlay = np.full_like(frame, self.countdown, dtype=np.uint8)
        frame[:] = np.clip(frame.astype(np.int16) + overlay, 0, 255).astype(np.uint8)

class ColorText(Effect):

    text: str

    def draw(self, frame):
        if self.countdown % 2 == 0:
            color = (255, 0, 255)
        else:
            color = (0, 255, 255)
        cv2.putText(frame,
            self.text,
            org=(self.y * TILE_SIZE, self.x * TILE_SIZE),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=1.0,
            color=color,
            thickness=2,
        )
