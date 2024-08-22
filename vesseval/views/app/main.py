import cv2 as cv
import numpy as np
import tkinter as tk

from ...state import PointState

from ...widgets.canvas import Image
from ...widgets.canvas import Contour, DisplayContourState
from ...util import mask_image

from ..preprocessing import PreprocessingView, PreprocessingViewState

from .footer import Footer, FooterState
from .state import app_state
from .menu import MenuBar
from .toolbar import Toolbar


class App(tk.Tk):

    def __init__(self):
        super().__init__()

        self.state = app_state

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=2)
        self.rowconfigure(1, weight=10)
        self.rowconfigure(2, weight=1)

        self.menu_bar = MenuBar(self)

        self.toolbar = Toolbar(self)
        self.toolbar.grid(column=0, row=0, sticky=tk.W + tk.E)

        self.canvas = tk.Canvas(self)
        self.canvas.grid(column=0, row=1)

        self.footer = Footer(self, state=FooterState())
        self.footer.grid(column=0, row=2, sticky="nswe")
        self.state.contour_state.on_change(self.update_info, element_wise=True)

        self.bb_mode_bindings = {}
        self.toolbar.state.bounding_box_mode.on_change(self.on_bb_mode, trigger=True)

        self.image = Image(self.canvas, app_state.display_image_state)
        self.contour = Contour(
            self.canvas,
            DisplayContourState(self.state.contour_state, rectangle_color="white"),
        )

        self.bind("<Key-q>", lambda event: exit(0))
        self.bind("<Return>", self.on_return)

    def update_info(self, *args):
        contour = self.state.contour_state.to_numpy()
        if len(contour) <= 1:
            self.footer.state.info_text.value = ""
            return

        _, radius = cv.minEnclosingCircle(contour)
        diameter = radius * 2
        diameter = (
            diameter
            * self.state.image_config.pixel_size.value
            / self.state.display_image_state.scale_state.value
        )

        self.footer.state.info_text.value = (
            f"Size of Vessel: {diameter:.1f}{self.state.image_config.size_unit.value}"
        )

    def on_return(self, *args):
        PreprocessingView(
            PreprocessingViewState(
                mask_image(self.state.display_image_state, self.state.contour_state)
            )
        )

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
