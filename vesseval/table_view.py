import cv2 as cv
import numpy as np
import tkinter as tk
from tkinter import ttk

from .state import (
    HigherState,
    computed_state,
    IntState,
    FloatState,
    StringState,
    ImageState,
    DisplayImageState,
    ResolutionState,
    app_state,
)
from .widgets.canvas.contour import Contour, ContourState, DisplayContourState
from .widgets.canvas.image import Image


class CellLayerState(HigherState):

    def __init__(
        self,
        image: ImageState,
        mask: ImageState,
        inner_contour: ContourState,
        outer_contour: ContourState,
        scale: float,
        angle_step: int,
    ):
        super().__init__()

        self.image = image
        self.mask = mask
        self.inner_contour = inner_contour
        self.outer_contour = outer_contour
        self.scale = scale
        self.angle_step = angle_step
        self.pixel_size = app_state.pixel_size_state
        self.size_unit = app_state.size_unit_state

        self.inner_length = FloatState(self.compute_contour_length(self.inner_contour))
        self.outer_length = FloatState(self.compute_contour_length(self.outer_contour))
        self.thickness = FloatState(self.compute_thickness())
        for state in [self.scale, self.pixel_size]:
            state.on_change(lambda _: self.inner_length.set(self.compute_contour_length(self.inner_contour)))
            state.on_change(lambda _: self.outer_length.set(self.compute_contour_length(self.outer_contour)))
            state.on_change(lambda _: self.thickness.set(self.compute_thickness()))

        self.surround = self.surround(self.inner_contour, self.angle_step)

        self.contour_mask = ImageState(self.compute_contour_mask())
        for state in [self.mask, self.inner_contour, self.outer_contour]:
            state.on_change(lambda state: self.contour_mask.set(self.compute_contour_mask()))
        self.contour_area = self.contour_area(
            self.contour_mask, self.scale, self.pixel_size
        )
        self.cell_area = self.cell_area(
            self.mask, self.contour_mask, self.scale, self.pixel_size
        )

        for pt in [*self.inner_contour, *self.outer_contour]:
            pt.on_change(lambda _: self.inner_length.set(self.compute_contour_length(self.inner_contour)))
            pt.on_change(lambda _: self.outer_length.set(self.compute_contour_length(self.outer_contour)))
            pt.on_change(lambda _: self.thickness.set(self.compute_thickness()))
            pt.on_change(lambda _: self.contour_mask.set(self.compute_contour_mask()))

        self.colored_mask = self.colored_mask(self.image, self.mask)

    def compute_contour_mask(self) -> np.ndarray:
        contour_mask = np.zeros(self.mask.value.shape, np.uint8)
        contour_mask = cv.drawContours(
            contour_mask, [self.outer_contour.to_numpy()], 0, 255, -1
        )
        contour_mask = cv.drawContours(
            contour_mask, [self.inner_contour.to_numpy()], 0, 0, -1
        )
        return contour_mask

    def compute_contour_length(self, contour: ContourState):
        length = cv.arcLength(contour.to_numpy(), closed=True)
        length = length * self.scale.value * self.pixel_size.value
        return length

    def compute_thickness(self):
        diff = self.inner_contour.to_numpy() - self.outer_contour.to_numpy()
        distances = np.linalg.norm(diff, axis=1)
        thickness = np.average(distances) / self.scale.value * self.pixel_size.value
        return thickness

    @computed_state
    def colored_mask(self, image: ImageState, mask: ImageState):
        mask = mask.value.repeat(3).reshape(image.value.shape) / 255
        mask_inv = 1.0 - mask
        colored_mask = image.value * mask + image.value * 0.4 * mask_inv
        colored_mask = colored_mask.astype(np.uint8)
        return ImageState(colored_mask)

    @computed_state
    def contour_length(
        self, contour: ContourState, scale: FloatState, pixel_size: FloatState
    ) -> FloatState:
        # TODO: this actually depends on the positions of each point
        length = cv.arcLength(contour.to_numpy(), closed=True)
        length = length * scale.value * pixel_size.value
        return FloatState(length)

    @computed_state
    def surround(self, contour: ContourState, angle_step: IntState) -> FloatState:
        return FloatState(len(contour) * angle_step.value / 360.0)


    @computed_state
    def contour_area(
        self, contour_mask: ImageState, scale: FloatState, pixel_size: FloatState
    ) -> FloatState:
        n_pixels = contour_mask.value.sum() // 255
        area = n_pixels / (scale.value**2) * (pixel_size.value**2)
        return FloatState(area)

    @computed_state
    def cell_area(
        self,
        mask: ImageState,
        contour_mask: ImageState,
        scale: FloatState,
        pixel_size: FloatState,
    ) -> FloatState:
        _mask = cv.bitwise_and(contour_mask.value, contour_mask.value, mask=mask.value)
        n_pixels = _mask.sum() // 255
        area = n_pixels / (scale.value**2) * (pixel_size.value**2)
        return FloatState(area)



class Label(tk.Label):

    def __init__(self, parent: tk.Widget, state: StringState):
        super().__init__(parent, text=state.value)

        self.state = state
        self.state.on_change(lambda state: self.config(text=state.value))


class Table(tk.Frame):

    def __init__(self, parent: tk.Widget, state: CellLayerState):
        super().__init__(parent)

        self.state = state

        self.label = Label(self, StringState("Inner Length"))
        self.value = Label(
            self,
            state.inner_length.transform(
                lambda state: StringState(
                    f"{state.value:.2f} {self.state.size_unit.value}"
                )
            ),
        )

        self.label_2 = Label(self, StringState("Outer Length"))
        self.value_2 = Label(
            self,
            state.outer_length.transform(
                lambda state: StringState(
                    f"{state.value:.2f} {self.state.size_unit.value}"
                )
            ),
        )

        self.label_3 = Label(self, StringState("Contour Area"))
        self.value_3 = Label(
            self,
            state.contour_area.transform(
                lambda state: StringState(
                    f"{state.value:.2f} {self.state.size_unit.value}²"
                )
            ),
        )

        self.label_4 = Label(self, StringState("Cell Area"))
        self.value_4 = Label(
            self,
            state.cell_area.transform(
                lambda state: StringState(
                    f"{state.value:.2f} {self.state.size_unit.value}²"
                )
            ),
        )

        self.label_5 = Label(self, StringState("Surround"))
        self.value_5 = Label(
            self,
            state.surround.transform(
                lambda state: StringState(f"{100 * state.value:.2f}%")
            ),
        )

        self.label_6 = Label(self, StringState("Thickness"))
        self.value_6 = Label(
            self,
            state.thickness.transform(
                lambda state: StringState(
                    f"{state.value:.2f} {self.state.size_unit.value}"
                )
            ),
        )

        self.label.grid(column=0, row=0)
        self.value.grid(column=1, row=0)
        self.label_2.grid(column=0, row=1)
        self.value_2.grid(column=1, row=1)
        self.label_3.grid(column=0, row=2)
        self.value_3.grid(column=1, row=2)
        self.label_4.grid(column=0, row=3)
        self.value_4.grid(column=1, row=3)
        self.label_5.grid(column=0, row=4)
        self.value_5.grid(column=1, row=4)
        self.label_6.grid(column=0, row=5)
        self.value_6.grid(column=1, row=5)


class ResultView(tk.Toplevel):

    def __init__(self, state: CellLayerState):
        super().__init__()

        self.state = state

        self.canvas = tk.Canvas(self)
        self.image = Image(self.canvas, DisplayImageState(self.state.colored_mask))
        self.contour_inner = Contour(
            self.canvas,
            DisplayContourState(
                self.state.inner_contour, rectangle_color="blue", rectangle_size=7
            ),
        )
        self.contour_outer = Contour(
            self.canvas,
            DisplayContourState(
                self.state.outer_contour, rectangle_color="red", rectangle_size=7
            ),
        )

        self.table = Table(self, state)

        self.canvas.grid(column=0, row=0)
        self.table.grid(column=0, row=1)

        self.bind("<Key-q>", lambda event: exit(0))
