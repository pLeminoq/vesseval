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
from .widgets.label import Label
from .widgets.table import Table, TableState, RowState
from .util import compute_thickness


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

        self.inner_length = FloatState(0)
        self.inner_length.depends_on([self.inner_contour], lambda *args: self.compute_contour_length(self.inner_contour), init=True, element_wise=True)
        # self.inner_length = FloatState(self.compute_contour_length(self.inner_contour))
        self.outer_length = FloatState(self.compute_contour_length(self.outer_contour))
        self.thickness = FloatState(self._compute_thickness())
        # self.thickness = FloatState(0)
        # self.thickness.depends_on([self.inner_contour, self.outer_contour, *self.inner_contour, *self.outer_contour])
        for state in [self.scale, self.pixel_size]:
            # state.on_change(
                # lambda _: self.inner_length.set(
                    # self.compute_contour_length(self.inner_contour)
                # )
            # )
            state.on_change(
                lambda _: self.outer_length.set(
                    self.compute_contour_length(self.outer_contour)
                )
            )
            state.on_change(lambda _: self.thickness.set(self._compute_thickness()))

        self.surround = self.surround(self.inner_contour, self.angle_step)

        self.contour_mask = ImageState(self.compute_contour_mask())
        for state in [self.mask, self.inner_contour, self.outer_contour]:
            state.on_change(
                lambda state: self.contour_mask.set(self.compute_contour_mask())
            )
            state.on_change(lambda _: self.thickness.set(self._compute_thickness()))
            # state.on_change(
                # lambda _: self.inner_length.set(
                    # self.compute_contour_length(self.inner_contour)
                # )
            # )
            state.on_change(
                lambda _: self.outer_length.set(
                    self.compute_contour_length(self.outer_contour)
                )
            )
        self.contour_area = self.contour_area(
            self.contour_mask, self.scale, self.pixel_size
        )
        self.cell_area = self.cell_area(
            self.mask, self.contour_mask, self.scale, self.pixel_size
        )

        for pt in [*self.inner_contour, *self.outer_contour]:
            # pt.on_change(
                # lambda _: self.inner_length.set(
                    # self.compute_contour_length(self.inner_contour)
                # )
            # )
            pt.on_change(
                lambda _: self.outer_length.set(
                    self.compute_contour_length(self.outer_contour)
                )
            )
            pt.on_change(lambda _: self.thickness.set(self._compute_thickness()))
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

    def _compute_thickness(self):
        contour_inner = self.inner_contour.to_numpy()
        contour_outer = self.outer_contour.to_numpy()

        thickness = compute_thickness(contour_inner, contour_outer)
        return (thickness * self.pixel_size.value) / self.scale.value

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


class CellLayerView(tk.Frame):

    def __init__(self, parent: tk.Widget, state: CellLayerState):
        super().__init__(parent)

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

        self.table = Table(
            self,
            TableState(
                [
                    RowState(
                        key="Inner Length",
                        value=state.inner_length.transform(
                            lambda state: StringState(
                                f"{state.value:.2f} {self.state.size_unit.value}"
                            )
                        ),
                    ),
                    RowState(
                        key="Outer Length",
                        value=state.outer_length.transform(
                            lambda state: StringState(
                                f"{state.value:.2f} {self.state.size_unit.value}"
                            )
                        ),
                    ),
                    RowState(
                        key="Contour Area",
                        value=state.contour_area.transform(
                            lambda state: StringState(
                                f"{state.value:.2f} {self.state.size_unit.value}²"
                            )
                        ),
                    ),
                    RowState(
                        key="Cell Area",
                        value=state.cell_area.transform(
                            lambda state: StringState(
                                f"{state.value:.2f} {self.state.size_unit.value}²"
                            )
                        ),
                    ),
                    RowState(
                        key="Surround",
                        value=state.surround.transform(
                            lambda state: StringState(f"{100 * state.value:.2f}%")
                        ),
                    ),
                    RowState(
                        key="Thickness",
                        value=state.thickness.transform(
                            lambda state: StringState(
                                f"{state.value:.2f} {self.state.size_unit.value}"
                            )
                        ),
                    ),
                ]
            ),
        )

        self.canvas.grid(column=0, row=0, padx=(5, 5), pady=(5, 5))
        self.table.grid(column=0, row=1, pady=(5, 5))

class ResultView(tk.Toplevel):

    def __init__(self, cell_layer_states):
        super().__init__()

        self.cell_layer_states = cell_layer_states

        self.cell_layer_view_1 = CellLayerView(self, cell_layer_states[0])
        self.cell_layer_view_2 = CellLayerView(self, cell_layer_states[1])
        self.button = ttk.Button(self, text="Copy", command=self.on_copy)

        self.cell_layer_view_1.grid(row=0, column=0, padx=5)
        self.cell_layer_view_2.grid(row=0, column=1, padx=5)
        self.button.grid(row=1, column=0, columnspan=2, pady=5)

        self.bind("<Key-q>", lambda event: self.destroy())

    def on_copy(self, *args):
        values = []
        for state in self.cell_layer_states:
            values.append(state.inner_length.value)
            values.append(state.outer_length.value)
            values.append(state.contour_area.value)
            values.append(state.cell_area.value)
            values.append(state.surround.value)
            values.append(state.thickness.value)
        values = list(map(str, values))

        self.clipboard_clear()
        self.clipboard_append("\t".join(values))

