import cv2
import os
import numpy as np
from config import SCREEN_SIZE_X, SCREEN_SIZE_Y
from sound import select_sound


def show_cutscene():
    # load the title image
    title_path = os.path.split(__file__)[0] + "/title.png"
    img = cv2.imread(title_path)
    if img is None:
        return False

    # Scale the image to fit the screen dimensions while preserving aspect ratio
    h_orig, w_orig = img.shape[:2]
    scale = min(SCREEN_SIZE_X / w_orig, SCREEN_SIZE_Y / h_orig)
    w_new, h_new = int(w_orig * scale), int(h_orig * scale)
    img_resized = cv2.resize(img, (w_new, h_new))

    # Create a full-screen black frame
    frame = np.zeros((SCREEN_SIZE_Y, SCREEN_SIZE_X, 3), dtype=np.uint8)

    # Calculate centering offsets
    dx = (SCREEN_SIZE_X - w_new) // 2
    dy = (SCREEN_SIZE_Y - h_new) // 2

    # Copy the resized image into the center of the frame
    frame[dy : dy + h_new, dx : dx + w_new] = img_resized

    # Make the bottom part of the centered image black for text (scale the original 100px)
    text_bar_height = int(80 * scale)

    # display everything on the fullscreen window
    cv2.namedWindow("Dungeon Explorer", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(
        "Dungeon Explorer", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
    )

    selected_option = 0  # 0 for PLAY, 1 for EXIT

    while True:
        # Clear the bottom text bar area
        frame[dy + h_new - text_bar_height : dy + h_new, dx : dx + w_new] = 0

        # Draw left text or title (Dungeon Explorer)
        cv2.putText(
            frame,
            "Dungeon Explorer",
            org=(
                dx + int(30 * scale),
                dy + h_new - int(30 * scale),
            ),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=1.0 * scale,
            color=(255, 255, 255),  # white
            thickness=max(1, int(2 * scale)),
        )

        # Draw "PLAY" option
        play_text = "> PLAY <" if selected_option == 0 else "  PLAY  "
        play_color = (100, 255, 255) if selected_option == 0 else (160, 160, 160)
        cv2.putText(
            frame,
            play_text,
            org=(
                dx + w_new - int(380 * scale),
                dy + h_new - int(30 * scale),
            ),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=1.0 * scale,
            color=play_color,
            thickness=max(1, int(2 * scale)),
        )

        # Draw "EXIT" option
        exit_text = "> EXIT <" if selected_option == 1 else "  EXIT  "
        exit_color = (100, 255, 255) if selected_option == 1 else (160, 160, 160)
        cv2.putText(
            frame,
            exit_text,
            org=(
                dx + w_new - int(180 * scale),
                dy + h_new - int(30 * scale),
            ),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=1.0 * scale,
            color=exit_color,
            thickness=max(1, int(2 * scale)),
        )

        cv2.imshow("Dungeon Explorer", frame)

        # Get key input
        key = cv2.waitKey(0) & 0xFF
        char = chr(key) if key < 256 else ""

        if char in ("a", "A") or key in (37, 81):  # Left arrow or 'a'
            if selected_option != 0:
                selected_option = 0
                select_sound.play()
        elif char in ("d", "D") or key in (39, 83):  # Right arrow or 'd'
            if selected_option != 1:
                selected_option = 1
                select_sound.play()
        elif key == 13 or key == 32:  # Enter or Space
            break
        

    return selected_option == 0
