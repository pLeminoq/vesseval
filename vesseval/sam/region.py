import os
import tkinter as tk

import cv2 as cv
import numpy as np
from numpy.typing import NDArray

from ..state import ImageState, DisplayImageState, ResolutionState
from ..widgets.canvas import Image

from .state import app_state


class RegionView(tk.Frame):

    def __init__(self, parent: tk.Widget):
        super().__init__(parent)
        self.configure(bg="#9E9E9E", borderwidth=2)

        self.res = 256 + 128

        self.canvas = tk.Canvas(self, width=self.res, height=self.res)
        self.canvas.configure(bg="#757575")

        self.image_state = ImageState(np.zeros((self.res, self.res, 3), dtype=np.uint8))
        self.image = Image(
            self.canvas,
            DisplayImageState(
                image_state=self.image_state,
                resolution_state=ResolutionState(self.res, self.res),
            ),
        )

        self.canvas.grid(row=0, column=0, sticky="n")

        self.image_state.depends_on(
            [app_state.selected_region_index, app_state.final_image], self.compute_image
        )

        self.table = tk.Frame(self, bg="#AEAEAE", borderwidth=2)
        self.table.grid(row=1, column=0, sticky="nswe")
        self.table.rowconfigure(0, minsize=128)
        self.table.columnconfigure(0, minsize=self.res // 2)
        self.table.columnconfigure(1, minsize=self.res // 2)

        self.cat = tk.Label(self.table, text="Category", background="#AEAEAE")
        self.cat.grid(row=0, column=0, sticky="nswe")

        self.ops = self.read_categories()
        self.op = tk.StringVar(value=self.ops[0])
        self.opts_menu = tk.OptionMenu(self.table, self.op, *self.ops)
        self.opts_menu.configure()
        self.opts_menu["menu"].configure()
        self.opts_menu.grid(row=0, column=1)

        self.op.trace_add("write", self.set_label)

    def set_label(self, *_):
        try:
            selected_region = app_state.regions[app_state.selected_region_index.value]
            selected_region.label.value = self.op.get()
        except:
            pass

    def compute_image(self) -> NDArray:
        try:
            selected_region = app_state.regions[app_state.selected_region_index.value]

            self.op.set(
                self.ops[0]
                if selected_region.label.value is None
                else selected_region.label.value
            )

            cnt = selected_region.contour.to_numpy()
            bb = cv.boundingRect(cnt)

            base_img = app_state.final_image.value
            img = base_img[bb[1] : bb[1] + bb[3], bb[0] : bb[0] + bb[2]]
            return img
        except:
            return np.zeros((self.res, self.res, 3), np.uint8)

    def read_categories(self):
        default = ["Category 1", "Category 2", "Category 3"]
        cat_file = os.path.join(os.getcwd(), "categories.txt")
        if not os.path.isfile(cat_file):
            return default

        with open(cat_file, mode="r") as f:
            return list(map(lambda _str: _str.strip(), f.read().split(",")))
