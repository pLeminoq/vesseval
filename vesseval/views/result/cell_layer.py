import cv2 as cv
import numpy as np
import tkinter as tk
from tkinter import ttk

from ...state import (
    HigherState,
    computed_state,
    IntState,
    FloatState,
    StringState,
    ImageState,
    DisplayImageState,
    ResolutionState,
    ContourState,
    ImageConfigState,
)
from ...widgets.canvas import Contour, DisplayContourState, Image
from ...widgets import Label, Table, TableState, RowState
from ...util import compute_thickness, compute_contours


class CellLayerState(HigherState):

    def __init__(
        self,
        image: ImageState,
        mask: ImageState,
        inner_contour: ContourState,
        outer_contour: ContourState,
        scale: float,
        image_config: ImageConfigState,
    ):
        super().__init__()

        self.image = image
        self.mask = mask
        self.inner_contour = inner_contour
        self.outer_contour = outer_contour
        self.scale = scale
        self.image_config = image_config

        self.inner_length = FloatState(self.compute_contour_length(self.inner_contour))
        self.inner_length.depends_on(
            [self.inner_contour],
            lambda *args: self.compute_contour_length(self.inner_contour),
            element_wise=True,
        )

        self.outer_length = FloatState(self.compute_contour_length(self.outer_contour))
        self.outer_length.depends_on(
            [self.outer_contour],
            lambda *args: self.compute_contour_length(self.outer_contour),
            element_wise=True,
        )

        self.thickness = FloatState(self.compute_thickness())
        self.thickness.depends_on(
            [self.inner_contour, self.outer_contour],
            lambda *args: self.compute_thickness(),
            element_wise=True,
        )

        self.surround = FloatState(self.compute_surround())

        self.contour_mask = ImageState(self.compute_contour_mask())
        self.contour_mask.depends_on(
            [self.mask, self.inner_contour, self.outer_contour],
            lambda *args: self.compute_contour_mask(),
            element_wise=True,
        )

        self.contour_area = self.contour_area(
            self.contour_mask, self.scale, self.image_config.pixel_size
        )
        self.cell_area = self.cell_area(
            self.mask, self.contour_mask, self.scale, self.image_config.pixel_size
        )

        self.colored_mask = self.colored_mask(self.image, self.mask)

    def compute_surround(self):
        n_angles = 100
        _angle_step = 360.0 / n_angles
        cnt_inner, _ = compute_contours(self.mask.value, angle_step=_angle_step)
        return len(cnt_inner) / n_angles

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
        length = length * self.scale.value * self.image_config.pixel_size.value
        return length

    def compute_thickness(self):
        contour_inner = self.inner_contour.to_numpy()
        contour_outer = self.outer_contour.to_numpy()

        thickness = compute_thickness(contour_inner, contour_outer)
        return float((thickness * self.image_config.pixel_size.value) / self.scale.value)

    @computed_state
    def colored_mask(self, image: ImageState, mask: ImageState):
        mask = mask.value.repeat(3).reshape(image.value.shape) / 255
        mask_inv = 1.0 - mask
        colored_mask = image.value * mask + image.value * 0.4 * mask_inv
        colored_mask = colored_mask.astype(np.uint8)
        return ImageState(colored_mask)

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
                                f"{state.value:.2f} {self.state.image_config.size_unit.value}"
                            )
                        ),
                    ),
                    RowState(
                        key="Outer Length",
                        value=state.outer_length.transform(
                            lambda state: StringState(
                                f"{state.value:.2f} {self.state.image_config.size_unit.value}"
                            )
                        ),
                    ),
                    RowState(
                        key="Contour Area",
                        value=state.contour_area.transform(
                            lambda state: StringState(
                                f"{state.value:.2f} {self.state.image_config.size_unit.value}²"
                            )
                        ),
                    ),
                    RowState(
                        key="Cell Area",
                        value=state.cell_area.transform(
                            lambda state: StringState(
                                f"{state.value:.2f} {self.state.image_config.size_unit.value}²"
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
                                f"{state.value:.2f} {self.state.image_config.size_unit.value}"
                            )
                        ),
                    ),
                ]
            ),
        )

        self.canvas.grid(column=0, row=0, padx=(5, 5), pady=(5, 5))
        self.table.grid(column=0, row=1, pady=(5, 5))
