import cv2 as cv
import numpy as np
import tkinter as tk
from tkinter import ttk

from .state import HigherState, computed_state, IntState, FloatState, StringState, ImageState, DisplayImageState, ResolutionState
from .widgets.canvas.contour import Contour, ContourState, DisplayContourState
from .widgets.canvas.image import Image


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
        return IntState(_mask.sum() // 255)

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

class ResultView(tk.Toplevel):

    def __init__(self, state: CellLayerState):
        super().__init__()

        self.state = state

        self.canvas = tk.Canvas(self)
        self.image = Image(self.canvas, DisplayImageState(self.state.mask_state))
        self.contour_inner = Contour(self.canvas, DisplayContourState(self.state.inner_contour_state, rectangle_color="blue", rectangle_size=7))
        self.contour_outer = Contour(self.canvas, DisplayContourState(self.state.outer_contour_state, rectangle_color="red", rectangle_size=7))

        self.table = Table(self, state)

        self.canvas.grid(column=0, row=0)
        self.table.grid(column=0, row=1)

        self.bind("<Key-q>", lambda event: exit(0))

# root = tk.Tk()

# cell_layer_state = CellLayerState(ImageState(mask), ContourState.from_numpy(cnt_inner), ContourState.from_numpy(cnt_outer))
# result_view = ResultView(cell_layer_state)

# ttk.Style().theme_use("clam")

# root.bind("<Key-q>", lambda event: exit(0))
# root.mainloop()
