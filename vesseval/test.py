import tkinter as tk
from tkinter import ttk

import cv2 as cv
import numpy as np

from .state import HigherState, computed_state, IntState, ResolutionState, PointState
from .widgets.canvas.image import Image, ImageState
from .widgets.scale import Scale, ScaleState
from .widgets.masking_view import MaskingView, MaskingState


def compute_contours(mask, angle_step:int=5):
    cnt_inner = []
    cnt_outer = []

    center = np.array(mask.shape[::-1]) / 2
    for angle_deg in range(0, 360, angle_step):
        angle = np.deg2rad(angle_deg)
        direction = np.array([np.cos(angle), np.sin(angle)]) * max(mask.shape)

        _line = np.zeros(mask.shape, np.uint8)
        _line = cv.line(_line, tuple(center.astype(int)), tuple((center + direction).astype(int)), 255, 1)
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


def resize(image, max_size):
    scale_x = max_size / image.shape[1]
    scale_y = max_size / image.shape[0]
    scale = min(scale_x, scale_y)
    return cv.resize(image, None, fx=scale, fy=scale, interpolation=cv.INTER_NEAREST)


class ThresholdState(HigherState):

    def __init__(self, image: np.ndarray):
        super().__init__()

        self.image_size_state = 512
        self.image_state = ImageState(cv.cvtColor(image, cv.COLOR_BGR2RGB))

        self.resized_image_state = self.resized_image_state(
            self.image_state, self.image_size_state
        )

    @computed_state
    def resized_image_state(
        self, image_state: ImageState, image_size_state: IntState
    ) -> ImageState:
        return ImageState(resize(image_state.value, image_size_state.value))


class ThresholdView(tk.Frame):

    def __init__(self, parent: tk.Frame, state: ThresholdState):
        super().__init__(parent)

        self.state = state

        self.canvas_1 = tk.Canvas(
            self,
            width=self.state.resized_image_state.value.shape[1],
            height=self.state.resized_image_state.value.shape[0],
        )
        self.image_1 = Image(self.canvas_1, self.state.resized_image_state)

        self.masking_view_green = MaskingView(
            self,
            state=MaskingState(self.state.resized_image_state, channel=1),
        )
        self.masking_view_red = MaskingView(
            self,
            state=MaskingState(self.state.resized_image_state, channel=0),
        )

        self.canvas_1.grid(row=0, column=0, rowspan=2)

        self.masking_view_green.grid(row=0, column=1, padx=10, pady=5)
        self.masking_view_red.grid(row=1, column=1, padx=10, pady=5)

        self.button = ttk.Button(self, text="Processs ...", command=self.process)
        self.button.grid(row=2, column=0, columnspan=2, pady=5)


        
    def process(self, *args):
        print(f"Process")

        mask = self.masking_view_green.state.thresholded_state.value
        print(mask.shape)

        cnt_inner, cnt_outer = compute_contours(mask, angle_step=10)
        print(cnt_inner.shape)

        # length_inner = 

        from .widgets.canvas.contour import Contour, ContourState
        cnt = Contour(self.masking_view_green.canvas, ContourState.from_numpy(cnt_inner))
        cnt2 = Contour(self.masking_view_green.canvas, ContourState.from_numpy(cnt_outer))



img = cv.imread("data/Lunge_Overlay_scalebar.tif")

l, t, w, h = 400, 570, 90, 70
img = img[t : t + h, l : l + w]

root = tk.Tk()
root.clipboard_clear()
root.clipboard_append("1\t2\t")

threshold_view = ThresholdView(root, ThresholdState(img))
threshold_view.grid()

ttk.Style().theme_use("clam")

root.bind("<Key-q>", lambda event: exit(0))
root.mainloop()
