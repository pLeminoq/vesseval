import cv2 as cv
import numpy as np
import tkinter as tk

from ...state import PointState

from ...widgets.canvas import Image, Rectangle, RectangleState
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
        self.erase_mode = {}
        self.toolbar.state.bounding_box_mode.on_change(self.on_bb_mode, trigger=True)
        self.toolbar.state.erase_mode.on_change(self.on_erase_mode, trigger=True)

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

    def on_erase_mode(self, state):
        if state.value:
            self.erase_mode["rectangle"] = Rectangle(
                self.canvas,
                RectangleState(
                    PointState(-20, -20),
                    size_state=15,
                    color_state="",
                    outline="white",
                ),
            )
            self.erase_mode["bindings"] = {
                "motion": self.canvas.bind("<Motion>", self.on_erase_motion),
                "button_1": self.canvas.bind("<Button-1>", self.on_erase_click),
                "b1_motion": self.canvas.bind("<B1-Motion>", self.on_erase_click),
            }
        else:
            if "rectangle" in self.erase_mode:
                self.erase_mode["rectangle"].delete()
                del self.erase_mode["rectangle"]

                for binding, _id in self.erase_mode["bindings"].items():
                    self.canvas.unbind(binding, _id)

    def on_erase_motion(self, event):
        self.erase_mode["rectangle"].state.center_state.set(event.x, event.y)

    def on_erase_click(self, event):
        self.on_erase_motion(event)

        display_image_state = self.state.display_image_state
        image_state = display_image_state.image_state

        resolution_state = display_image_state.resolution_state
        display_shape = display_image_state.display_image_state.value.shape

        t_x = (resolution_state.width.value - display_shape[1]) // 2
        t_y = (resolution_state.height.value - display_shape[0]) // 2

        # transform mouse position into image coordinates
        pt = np.array([event.x, event.y])
        pt[0] = pt[0] - t_x
        pt[1] = pt[1] - t_y
        pt = np.rint(pt / display_image_state.scale_state.value).astype(int)
        pt = tuple(pt.tolist())

        # transform size into image size
        size = self.erase_mode["rectangle"].state.size_state.value
        size = round(size / display_image_state.scale_state.value)

        # translate pt rectangle top-left
        size_h = size // 2
        pt = (pt[0] - size_h, pt[1] - size_h)

        image_state.value = cv.rectangle(
            image_state.value, pt, (pt[0] + size, pt[1] + size), (0, 0, 0), -1
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
