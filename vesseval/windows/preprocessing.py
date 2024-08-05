import tkinter as tk
from tkinter import ttk

import cv2 as cv
import numpy as np

from ..state import (
    app_state,
    ResolutionState,
    DisplayImageState,
    ImageState,
)
from ..widgets.canvas.contour import ContourState
from ..widgets.canvas.image import Image
from ..widgets.scale import Scale, ScaleState
from ..table_view import ResultView, CellLayerState

from .masking_view import MaskingView, MaskingState

from ..util import mask_image


def compute_contours(mask, angle_step: int = 10):
    cnt_inner = []
    cnt_outer = []

    center = np.array(mask.shape[::-1]) / 2
    for angle_deg in range(0, 360, angle_step):
        angle = np.deg2rad(angle_deg)
        direction = np.array([np.cos(angle), np.sin(angle)]) * max(mask.shape)

        _line = np.zeros(mask.shape, np.uint8)
        _line = cv.line(
            _line,
            tuple(center.astype(int)),
            tuple((center + direction).astype(int)),
            255,
            1,
        )
        _line = cv.bitwise_and(mask, mask, mask=_line)
        left, top, width, height = cv.boundingRect(_line)
        if width == 0 and height == 0:
            continue

        if 0 <= angle_deg < 90:
            cnt_inner.append((left, top))
            cnt_outer.append((left + width, top + height))
        elif 90 <= angle_deg < 180:
            cnt_inner.append((left + width, top))
            cnt_outer.append((left, top + height))
        elif 180 <= angle_deg < 270:
            cnt_inner.append((left + width, top + height))
            cnt_outer.append((left, top))
        else:
            cnt_inner.append((left, top + height))
            cnt_outer.append((left + width, top))

    return np.array(cnt_inner), np.array(cnt_outer)


class ThresholdView(tk.Toplevel):

    def __init__(self):
        super().__init__()

        image = mask_image(app_state)

        self.state = DisplayImageState(ImageState(image), ResolutionState(512, 400))

        self.canvas = tk.Canvas(self)
        self.image = Image(self.canvas, self.state)

        self.masking_view_green = MaskingView(
            self,
            state=MaskingState(self.state, channel=1),
        )
        self.masking_view_red = MaskingView(
            self,
            state=MaskingState(self.state, channel=0),
        )

        self.canvas.grid(row=0, column=0, rowspan=2)

        self.masking_view_green.grid(row=0, column=1, padx=10, pady=5)
        self.masking_view_red.grid(row=1, column=1, padx=10, pady=5)

        self.button = ttk.Button(self, text="Process", command=self.process)
        self.button.grid(row=2, column=0, columnspan=2, pady=5)

        self.bind("<Key-q>", lambda event: self.destroy())

    def process(self, *args):

        angle_step = 6

        mask = self.masking_view_green.state.processed_mask.image_state.value
        cnt_inner, cnt_outer = compute_contours(mask, angle_step=angle_step)
        cell_layer_state_1 = CellLayerState(
            self.state.display_image_state,
            self.masking_view_green.state.mask.image_state,
            ContourState.from_numpy(cnt_inner),
            ContourState.from_numpy(cnt_outer),
            scale=self.state.scale_state,
            angle_step=angle_step,
        )

        mask = self.masking_view_red.state.processed_mask.image_state.value
        cnt_inner, cnt_outer = compute_contours(mask, angle_step=angle_step)
        cell_layer_state_2 = CellLayerState(
            self.state.display_image_state,
            self.masking_view_red.state.mask.image_state,
            ContourState.from_numpy(cnt_inner),
            ContourState.from_numpy(cnt_outer),
            scale=self.state.scale_state,
            angle_step=angle_step,
        )

        ResultView([cell_layer_state_1, cell_layer_state_2])

        self.withdraw()
        self.destroy()
