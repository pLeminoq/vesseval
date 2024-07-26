import tkinter as tk

import cv2 as cv

from .state import PointState
from .widgets.canvas.image import Image, ImageState
from .widgets.canvas.rectangle import Rectangle, RectangleState
from .widgets.canvas.line import Line, LineState
from .widgets.canvas.contour import Contour, ContourState

# class App(tk.Tk):

# def __init__(self):

# c = tk.Canvas(
# self,
# width=img.shape[1],
# height=img.shape[0],
# )
# self.image = Image(self.canvas, ImageState(img))

# self.canvas.grid(column=0, row=0)

img = cv.imread("data/Lunge_Overlay_scalebar.tif")

points = [
    PointState(400, 570),
    PointState(400 + 90, 570),
    PointState(400 + 90, 570 + 70),
    PointState(400, 570 + 70),
]

root = tk.Tk()

canvas = tk.Canvas(root, width=img.shape[1], height=img.shape[0])
canvas.grid(column=0, row=0)

image = Image(canvas, ImageState(cv.cvtColor(img, cv.COLOR_RGB2BGR)))
contour = Contour(canvas, ContourState(points))

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
