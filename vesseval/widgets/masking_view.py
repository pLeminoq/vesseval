import cv2 as cv
import numpy as np
import tkinter as tk
from tktooltip import ToolTip

from ..state import HigherState, computed_state, IntState, BoolState
from .canvas.image import Image, ImageState
from .scale import Scale, ScaleState
from .chechbox import Checkbox, CheckboxState


class MaskingState(HigherState):

    def __init__(
        self,
        image_state: ImageState,
        channel: int,
        threshold: int = 100,
        opening: bool = True,
        opening_size: int = 3,
        closing: bool = True,
        closing_size: int = 10,
    ):
        super().__init__()

        self._channel = channel
        self._resolution = (image_state.value.shape[1], image_state.value.shape[0])

        self.image_state = image_state
        self.threshold_state = threshold
        self.thresholded_state = self.thresholded_state(self.image_state, self.threshold_state)

        self.opening_state = opening
        self.opening_size_state = opening_size

        self.closing_state = closing
        self.closing_size_state = closing_size

        self.mask_state = self.mask_state(self.thresholded_state, self.opening_state, self.opening_size_state, self.closing_state, self.closing_size_state)

    @computed_state
    def thresholded_state(self, image_state: ImageState, threshold_state: IntState):
        image = image_state.value
        mask = image[:, :, self._channel] > threshold_state.value
        mask = (mask * 255).astype(np.uint8)
        return ImageState(mask)


    @computed_state
    def mask_state(
        self,
        thresholded_state: ImageState,
        opening_state: BoolState,
        opening_size_state: IntState,
        closing_state: BoolState,
        closing_size_state: IntState,
    ) -> ImageState:
        image = self.image_state.value
        mask = thresholded_state.value

        if self.opening_state.value:
            _size = self.opening_size_state.value * 2 - 1
            mask = cv.morphologyEx(mask, cv.MORPH_OPEN, np.ones((_size, _size)))

        if self.closing_state.value:
            _size = self.closing_size_state.value * 2 - 1
            mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, np.ones((_size, _size)))

        mask = cv.bitwise_and(image, image, mask=mask)

        return ImageState(mask)


class CheckedScaleState(ScaleState):

    def __init__(self, bool_state: BoolState, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bool_state = bool_state


class CheckedScale(Scale):

    def __init__(self, parent: tk.Frame, state: CheckedScaleState):
        super().__init__(parent, state)

        self.chechbox = Checkbox(
            self, CheckboxState(self.state.bool_state, label_state="Test")
        )
        self.state.bool_state.on_change(
            lambda state: self.scale.state(["!disabled" if state.value else "disabled"])
        )

        if self.state._orientation == tk.HORIZONTAL:
            self.chechbox.grid(column == 3, row=0)
        else:
            self.chechbox.grid(column=0, row=3)


class MaskingView(tk.Frame):

    def __init__(self, parent: tk.Frame, state: MaskingState):
        super().__init__(parent)
        self.state = state

        self.canvas = tk.Canvas(
            self, width=self.state._resolution[0], height=self.state._resolution[1]
        )
        self.image = Image(self.canvas, self.state.mask_state)

        self.frame = tk.Frame(self)
        self.title_1 = tk.Label(self.frame, text="Treshold", width=10)
        self.scale_1 = Scale(
            self.frame,
            ScaleState(
                self.state.threshold_state,
                value_range=[255, 0],
                length=round(self.state._resolution[1] * 0.7),
                orientation=tk.VERTICAL,
            ),
        )
        self.title_2 = tk.Label(self.frame, text="Opening", width=10)
        self.chechbox_2 = Checkbox(self.frame, CheckboxState(self.state.opening_state))
        self.scale_2 = Scale(
            self.frame,
            ScaleState(
                self.state.opening_size_state,
                value_range=[20, 1],
                length=round(self.state._resolution[1] * 0.7),
                orientation=tk.VERTICAL,
            ),
        )
        self.title_3 = tk.Label(self.frame, text="Closing", width=10)
        self.chechbox_3 = Checkbox(self.frame, CheckboxState(self.state.closing_state))
        self.scale_3 = Scale(
            self.frame,
            ScaleState(
                self.state.closing_size_state,
                value_range=[30, 1],
                length=round(self.state._resolution[1] * 0.7),
                orientation=tk.VERTICAL,
            ),
        )

        self.tool_tip_opening = ToolTip(self.title_2, msg="Opening removes small isolated regions", delay=0.5)
        self.tool_tip_closing = ToolTip(self.title_3, msg="Closing connects regions close to each other", delay=0.5)

        self.title_1.grid(row=0, column=0)
        self.title_2.grid(row=0, column=1)
        self.title_3.grid(row=0, column=2)
        self.chechbox_2.grid(row=1, column=1)
        self.chechbox_3.grid(row=1, column=2)
        self.scale_1.grid(row=2, column=0)
        self.scale_2.grid(row=2, column=1)
        self.scale_3.grid(row=2, column=2)

        self.canvas.grid(column=0, row=0)
        self.frame.grid(column=2, row=0)
