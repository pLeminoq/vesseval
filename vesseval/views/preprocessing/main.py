import tkinter as tk
from tkinter import ttk

import cv2 as cv
import numpy as np

from ...state import (
    app_state,
    ContourState,
    ResolutionState,
    DisplayImageState,
    ImageState,
)
from ...widgets.canvas import Image
from ...widgets import Scale, ScaleState
from ...table_view import ResultView, CellLayerState, ResultViewState
from ...util import compute_contours, mask_image

from .masking import MaskingView, MaskingState


class PreprocessingView(tk.Toplevel):

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

        ResultView(ResultViewState(cell_layer_state_1, cell_layer_state_2))

        self.withdraw()
        self.destroy()
