import cv2 as cv
import numpy as np
import tkinter as tk

from .state import app_state, PointState

from .widgets.canvas.image import Image
from .widgets.canvas.contour import Contour, DisplayContourState

from .widgets.menu import MenuBar
from .widgets.toolbar import Toolbar

from .windows.preprocessing import ThresholdView

from .util import mask_image


class App(tk.Tk):

    def __init__(self):
        super().__init__()

        self.state = app_state

        self.menu_bar = MenuBar(self)

        self.toolbar = Toolbar(self)
        self.toolbar.grid(column=0, row=0, sticky=tk.W + tk.E)

        self.canvas = tk.Canvas(self)
        self.canvas.grid(column=0, row=1)

        self.bb_mode_bindings = {}
        self.toolbar.state.bounding_box_mode.on_change(self.on_bb_mode, trigger=True)

        self.image = Image(self.canvas, app_state.display_image_state)
        self.contour = Contour(
            self.canvas,
            DisplayContourState(self.state.contour_state, rectangle_color="white"),
        )

        self.bind("<Key-q>", lambda event: exit(0))
        self.bind("<Return>", self.on_return)

    def on_bb_mode(self, state):
        if state.value:
            self.bb_mode_bindings["<Button-1>"] = self.canvas.bind(
                "<Button-1>", self.bb_mode_new_contour
            )
            self.bb_mode_bindings["<B1-Motion>"] = self.canvas.bind(
                "<B1-Motion>", self.bb_mode_init_contour
            )
            self.bb_mode_bindings["<B1-ButtonRelease>"] = self.canvas.bind(
                "<B1-ButtonRelease>",
                lambda event: self.toolbar.state.mouse_mode.set(True),
            )
        else:
            for binding, _id in self.bb_mode_bindings.items():
                self.canvas.unbind(binding, _id)
            self.bb_mode_bindings.clear()

    def bb_mode_new_contour(self, event):
        if len(self.state.contour_state) > 0:
            self.state.contour_state.clear()

        x, y = event.x, event.y
        self.state.contour_state.extend(
            [
                PointState(x, y),
                PointState(x + 1, y),
                PointState(x + 1, y + 1),
                PointState(x, y + 1),
            ]
        )

    def bb_mode_init_contour(self, event):
        x, y = event.x, event.y

        self.state.contour_state[1].x.set(x)
        self.state.contour_state[2].x.set(x)
        self.state.contour_state[2].y.set(y)
        self.state.contour_state[3].y.set(y)

    def on_return(self, *args):
        img = app_state.display_image_state.image_state.value
        cnt = self.state.contour_state.to_numpy()

        ThresholdView()
