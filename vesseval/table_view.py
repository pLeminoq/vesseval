import cv2 as cv
import numpy as np
import tkinter as tk
from tkinter import ttk

from .state import HigherState, computed_state, IntState, FloatState, StringState
from .widgets.canvas.contour import Contour, ContourState
from .widgets.canvas.image import Image, ImageState


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


img = cv.imread("data/Lunge_Overlay_scalebar.tif")

l, t, w, h = 400, 570, 90, 70
img = img[t : t + h, l : l + w]

mask = img[:, :, 1] > 100
mask = (mask * 255).astype(np.uint8)
mask = cv.resize(mask, (512, 512), interpolation=cv.INTER_NEAREST)
mask = cv.morphologyEx(mask, cv.MORPH_OPEN, np.ones((7, 7)))
# mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, np.ones((20, 20)))

cnt_inner, cnt_outer = compute_contours(mask)

img = cv.resize(img, (512, 512), interpolation=cv.INTER_NEAREST)
mask_colored = cv.bitwise_and(img, img, mask=mask)

class ContourStatsState(HigherState):

    def __init__(self, contour_state: ContourState):
        super().__init__()

        self.contour_state = contour_state
        self.contour_length_state = self.contour_length_state(self.contour_state)

    @computed_state
    def contour_length_state(self, contour_state: ContourState) -> IntState:
        cnt = contour_state.to_numpy()
        return FloatState(cv.arcLength(cnt, closed=True))

class CellLayerState(HigherState):

    def __init__(self, mask_state: ImageState, inner_contour_state: ContourState, outer_contour_state: ContourState):
        super().__init__()

        self.mask_state = mask_state
        self.inner_contour_state = inner_contour_state
        self.outer_contour_state = outer_contour_state

        self.inner_length_state = self.contour_length(self.inner_contour_state)
        self.outer_length_state = self.contour_length(self.outer_contour_state)

        self.contour_mask_state = self.contour_mask_state(self.mask_state, self.inner_contour_state, self.outer_contour_state)
        self.area_state = self.contour_mask_state.create_transformed_state(lambda image: image.sum() // 255)
        self.cell_area_state = self.cell_area_state(self.mask_state, self.contour_mask_state)

        # TODO:
        #  * multiply lengthes and values by pixel_size value
        # Values:
        # * Abstand innen und außen (thickness)
        # * Prozent umschlossen 

    @computed_state
    def contour_length(self, contour_state: ContourState) -> FloatState:
        #TODO: this actually depends on the positions of each point
        return IntState(cv.arcLength(contour_state.to_numpy(), closed=True))

    @computed_state
    def contour_mask_state(self, mask_state: ImageState, inner_contour_state: ContourState, outer_contour_state: ContourState) -> ImageState:
        contour_mask = np.zeros(mask_state.value.shape, np.uint8)
        contour_mask = cv.drawContours(contour_mask, [outer_contour_state.to_numpy()], 0, 255, -1)
        contour_mask = cv.drawContours(contour_mask, [inner_contour_state.to_numpy()], 0, 0, -1)
        return ImageState(contour_mask)

    @computed_state
    def cell_area_state(self, mask_state: ImageState, contour_mask_state: ImageState) -> IntState:
        _mask = cv.bitwise_and(contour_mask_state.value, contour_mask_state.value, mask=mask_state.value)
        return _mask.sum() // 255

class Label(tk.Label):

    def __init__(self, parent: tk.Widget, state: StringState):
        super().__init__(parent, text=state.value)

        self.state = state
        self.state.on_change(lambda state: self.config(text=state.value))


class Table(tk.Frame):

    def __init__(self, parent: tk.Widget, state: CellLayerState):
        super().__init__(parent)

        self.staet = state

        self.label = Label(self, StringState("Inner Length"))
        self.value = Label(self, state.inner_length_state.create_transformed_state(lambda x: f"{x:.3f}"))

        self.label_2 = Label(self, StringState("Outer Length"))
        self.value_2 = Label(self, state.outer_length_state.create_transformed_state(lambda x: f"{x:.2f}"))

        self.label_3 = Label(self, StringState("Area"))
        self.value_3 = Label(self, state.area_state.create_transformed_state(str))

        self.label_4 = Label(self, StringState("Cell Area"))
        self.value_4 = Label(self, state.cell_area_state.create_transformed_state(str))

        self.label.grid(column=0, row=0)
        self.value.grid(column=1, row=0)
        self.label_2.grid(column=0, row=1)
        self.value_2.grid(column=1, row=1)
        self.label_3.grid(column=0, row=2)
        self.value_3.grid(column=1, row=2)
        self.label_4.grid(column=0, row=3)
        self.value_4.grid(column=1, row=3)

root = tk.Tk()

cell_layer_state = CellLayerState(ImageState(mask), ContourState.from_numpy(cnt_inner), ContourState.from_numpy(cnt_outer))

canvas = tk.Canvas(root, width=mask.shape[1], height=mask.shape[0])
_image = Image(canvas, ImageState(mask_colored))
_cnt_inner = Contour(canvas, cell_layer_state.inner_contour_state)
_cnt_outer = Contour(canvas, cell_layer_state.outer_contour_state)
canvas.grid(column=0, row=0)

table = Table(root, cell_layer_state)
table.grid(column=0, row=1)

test = np.zeros(mask.shape, np.uint8)
test = cv.drawContours(test, [cnt_outer], 0, 1, -1)
test = cv.drawContours(test, [cnt_inner], 0, 0, -1)
# print(test.sum(), test.sum() // 255)
print(test.sum())
x = cv.bitwise_and(test, test, mask=mask)
print(x.sum())

ttk.Style().theme_use("clam")

root.bind("<Key-q>", lambda event: exit(0))
root.mainloop()
