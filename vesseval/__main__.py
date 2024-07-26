import argparse
import tkinter as tk

import cv2 as cv
import numpy as np

from .state import PointState
from .state.app import app_state
from .widgets.canvas.image import Image, ImageState
from .widgets.canvas.rectangle import Rectangle, RectangleState
from .widgets.canvas.line import Line, LineState
from .widgets.canvas.contour import Contour, ContourState
from .widgets.menu import MenuBar

# class App(tk.Tk):

# def __init__(self):

# c = tk.Canvas(
# self,
# width=img.shape[1],
# height=img.shape[0],
# )
# self.image = Image(self.canvas, ImageState(img))

# self.canvas.grid(column=0, row=0)

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--image", type=str, default="")
args = parser.parse_args()

app_state.filename_state.set(args.image)


points = [
    PointState(400, 570),
    PointState(400 + 90, 570),
    PointState(400 + 90, 570 + 70),
    PointState(400, 570 + 70),
]

root = tk.Tk()
menu_bar = MenuBar(root)

canvas = tk.Canvas(root)
canvas.grid(column=0, row=0)

image = Image(canvas, app_state.image_state)
contour_state = ContourState(points)
contour = Contour(canvas, contour_state)

from .test import ThresholdView, ThresholdState

def on_return(*args):
    img = app_state.image_state.value
    cnt = contour_state.to_numpy()

    mask = np.zeros(img.shape[:2], np.uint8)
    mask = cv.drawContours(mask, [cnt], 0, 255, -1)

    l, t, w, h = cv.boundingRect(cnt)
    _img = cv.bitwise_and(img, img, mask=mask)
    _img = _img[t:t+h, l:l+w]

    ThresholdView(_img)

root.bind("<Return>", on_return)


# image = Image(canvas, ImageState(cv.cvtColor(img, cv.COLOR_BGR2RGB)))
# rects = []
# for i, pt in enumerate(contour):
    # rect = Rectangle(canvas, RectangleState(pt))
    # def update_position(*args):
        # print(f"Update position of rect {i}, {rect.id} to {get_pointer_xy()}")
        # rect.state.center_state.set(*get_pointer_xy())
    # rects.append(rect)


# for pt_1, pt_2 in zip(contour, [*contour[1:], contour[0]]):
    # Line(canvas, LineState(pt_1, pt_2, "white"))


# canvas.grid(column=0, row=0)

root.bind("<Key-q>", lambda event: exit(0))


root.mainloop()
