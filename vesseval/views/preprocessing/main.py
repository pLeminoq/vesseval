import tkinter as tk
from tkinter import ttk

import cv2 as cv
import numpy as np
from widget_state import HigherOrderState

from ...state import (
    ContourState,
    ResolutionState,
    DisplayImageState,
    ImageState,
)
from ...widgets.canvas import Image
from ...widgets import Scale, ScaleState
from ...util import compute_contours

from ..app.state import app_state

from ..result.cell_layer import CellLayerState
from ..result.main import ResultView
from ..result.state import ResultViewState

from .masking import MaskingView, MaskingState


class PreprocessingViewState(HigherOrderState):

    def __init__(self, image: np.ndarray):
        super().__init__()

        self.display_image = DisplayImageState(
            ImageState(image),
            ResolutionState(512, 400),
        )

        self.masking_view_green = MaskingState(self.display_image, channel=1)
        self.masking_view_red = MaskingState(self.display_image, channel=0)


class PreprocessingView(tk.Toplevel):

    def __init__(self, state: PreprocessingViewState):
        super().__init__()
        self.configure(bg="#757575")

        self.state = state
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.configure(bg="#757575")
        self.image = Image(self.canvas, self.state.display_image)

        self.masking_view_green = MaskingView(
            self,
            state=self.state.masking_view_green,
        )
        self.masking_view_red = MaskingView(
            self,
            state=self.state.masking_view_red,
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
            self.state.display_image.display_image_state,
            self.state.masking_view_green.mask.image_state,
            ContourState.from_numpy(cnt_inner),
            ContourState.from_numpy(cnt_outer),
            scale=self.state.display_image.scale_state,
            image_config=app_state.image_config,
        )

        mask = self.masking_view_red.state.processed_mask.image_state.value
        cnt_inner, cnt_outer = compute_contours(mask, angle_step=angle_step)
        cell_layer_state_2 = CellLayerState(
            self.state.display_image.display_image_state,
            self.state.masking_view_red.mask.image_state,
            ContourState.from_numpy(cnt_inner),
            ContourState.from_numpy(cnt_outer),
            scale=self.state.display_image.scale_state,
            image_config=app_state.image_config,
        )

        ResultView(ResultViewState(cell_layer_state_1, cell_layer_state_2))

        self.withdraw()
        self.destroy()


if __name__ == "__main__":
    root = tk.Tk()

    preprocessing_view = PreprocessingView(state=PreprocessingViewState())

    root.mainloop()
