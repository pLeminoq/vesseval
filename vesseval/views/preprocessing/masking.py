import cv2 as cv
import numpy as np
import tkinter as tk
from tktooltip import ToolTip
from widget_state import computed_state, HigherOrderState, IntState, BoolState

from ...state import (
    DisplayImageState,
    ImageState,
)
from ...widgets.canvas import Image
from ...widgets import Scale, ScaleState, Checkbox, CheckboxState


class MorphOpsState(HigherOrderState):

    def __init__(self):
        super().__init__()

        self.opening = BoolState(False)
        self.opening_size = IntState(6)
        self.closing = BoolState(False)
        self.closing_size = IntState(10)


class MaskingState(HigherOrderState):

    def __init__(
        self,
        display_image_state: DisplayImageState,
        channel: int,
        threshold: int = 100,
    ):
        super().__init__()

        self._channel = channel

        self.display_image_state = display_image_state
        _image = self.display_image_state.image_state

        self.threshold_state = threshold
        self.morph_ops = MorphOpsState()

        self.mask = DisplayImageState(
            image_state=self.threshold_image(
                self.display_image_state.display_image_state, self.threshold_state
            ),
            resolution_state=self.display_image_state.resolution_state,
        )
        self.processed_mask = DisplayImageState(
            image_state=self.process_mask(
                self.mask.display_image_state, self.morph_ops
            ),
            resolution_state=self.display_image_state.resolution_state,
        )
        self.colored_mask = DisplayImageState(
            image_state=self.color_mask(
                self.processed_mask.display_image_state,
                self.display_image_state.display_image_state,
            ),
            resolution_state=self.display_image_state.resolution_state,
        )

    @computed_state
    def threshold_image(self, image: ImageState, threshold: IntState) -> ImageState:
        mask = image.value[:, :, self._channel] > threshold.value
        mask = (mask * 255).astype(np.uint8)
        return ImageState(mask)

    @computed_state
    def process_mask(self, mask: ImageState, morph_ops: MorphOpsState) -> ImageState:
        processed_mask = mask.value

        if morph_ops.opening.value:
            _size = morph_ops.opening_size.value * 2 - 1
            processed_mask = cv.morphologyEx(
                processed_mask, cv.MORPH_OPEN, np.ones((_size, _size))
            )

        if morph_ops.closing.value:
            _size = morph_ops.closing_size.value * 2 - 1
            processed_mask = cv.morphologyEx(
                processed_mask, cv.MORPH_CLOSE, np.ones((_size, _size))
            )

        return ImageState(processed_mask)

    @computed_state
    def color_mask(self, mask: ImageState, image: ImageState) -> ImageState:
        colored_mask = cv.bitwise_and(image.value, image.value, mask=mask.value)
        return ImageState(colored_mask)


class MaskingView(tk.Frame):

    def __init__(self, parent: tk.Frame, state: MaskingState):
        super().__init__(parent)
        self.configure(bg="#757575", highlightthickness=0)
        self.state = state

        self.canvas = tk.Canvas(self)
        self.canvas.configure(bg="#757575", highlightthickness=0)
        self.image = Image(self.canvas, self.state.colored_mask)

        self.frame = tk.Frame(self)
        self.frame.configure(bg="#757575")
        self.frame.configure(bg="#757575", highlightthickness=0)
        self.title_1 = tk.Label(self.frame, text="Threshold", width=10, bg="#757575")
        self.scale_1 = Scale(
            self.frame,
            ScaleState(
                self.state.threshold_state,
                value_range=[255, 0],
                length=round(
                    self.state.display_image_state.resolution_state.width.value * 0.7
                ),
                orientation=tk.VERTICAL,
            ),
            bg="#757575",
        )
        self.title_2 = tk.Label(self.frame, text="Opening", width=10, bg="#757575")
        self.chechbox_2 = Checkbox(
            self.frame, CheckboxState(self.state.morph_ops.opening),
            bg="#757575",
        )
        self.scale_2 = Scale(
            self.frame,
            ScaleState(
                self.state.morph_ops.opening_size,
                value_range=[20, 1],
                length=round(
                    self.state.display_image_state.resolution_state.width.value * 0.7
                ),
                orientation=tk.VERTICAL,
            ),
            bg="#757575",
        )
        self.title_3 = tk.Label(self.frame, text="Closing", width=10, bg="#757575") 
        self.chechbox_3 = Checkbox(
            self.frame, CheckboxState(self.state.morph_ops.closing), bg="#757575",
        )
        self.scale_3 = Scale(
            self.frame,
            ScaleState(
                self.state.morph_ops.closing_size,
                value_range=[30, 1],
                length=round(
                    self.state.display_image_state.resolution_state.width.value * 0.7
                ),
                orientation=tk.VERTICAL,
            ),
            bg="#757575",
        )

        self.tool_tip_opening = ToolTip(
            self.title_2, msg="Opening removes small isolated regions", delay=0.5
        )
        self.tool_tip_closing = ToolTip(
            self.title_3, msg="Closing connects regions close to each other", delay=0.5
        )

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
