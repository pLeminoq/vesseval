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
from .widgets.toolbar import Toolbar

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

class App(tk.Tk):

    def __init__(self):
        super().__init__()

        self.menu_bar = MenuBar(self)

        self.toolbar = Toolbar(self)
        self.toolbar.grid(column=0, row=0)

        self.canvas = tk.Canvas(self)
        self.canvas.grid(column=0, row=1)

        self.bb_mode_bindings = {}
        self.toolbar.state.bounding_box_mode.on_change(self.on_bb_mode, trigger=True)

        self.image = Image(self.canvas, app_state.image_state)

        self.contour_state = None
        self.contour = None

        self.bind("<Key-q>", lambda event: exit(0))

    def on_bb_mode(self, state):
        if state.value:
            self.bb_mode_bindings["<Button-1>"] = self.canvas.bind("<Button-1>", self.bb_mode_new_contour)
            self.bb_mode_bindings["<B1-Motion>"] = self.canvas.bind("<B1-Motion>", self.bb_mode_init_contour)
            self.bb_mode_bindings["<B1-ButtonRelease>"] = self.canvas.bind("<B1-ButtonRelease>", lambda event: self.toolbar.state.mouse_mode.set(True))
        else:
            for binding, _id in self.bb_mode_bindings.items():
                self.canvas.unbind(binding, _id)
            self.bb_mode_bindings.clear()

    def bb_mode_new_contour(self, event):
        if self.contour is not None:
            self.contour.clear() 

        x, y = event.x, event.y
        self.contour_state = ContourState([PointState(x, y), PointState(x + 1, y), PointState(x + 1, y + 1), PointState(x, y + 1)])
        self.contour = Contour(self.canvas, self.contour_state)

    def bb_mode_init_contour(self, event):
        x, y = event.x, event.y

        self.contour_state[1].x.set(x)

        self.contour_state[2].x.set(x)
        self.contour_state[2].y.set(y)

        self.contour_state[3].y.set(y)

app = App()
app.mainloop()
