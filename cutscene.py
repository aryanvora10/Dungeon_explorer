import cv2
import os

def show_cutscene():
    # load the title image
    img = cv2.imread(os.path.split(__file__)[0] + "/title.png")

    # make the last 100 pixel rows black for text
    img[-100:] = 0

    # write text on the image
    img = cv2.putText(
        img,
        "Hello World",
        org=(15, 600),  # x/y position of the text
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=1,
        color=(255, 255, 255),  # white
        thickness=2,
    )

    # display everything on the screen
    cv2.imshow("Cutscene", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()