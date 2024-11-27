from __future__ import annotations

from typing import Optional, Tuple

import cv2 as cv
import numpy as np
from numpy.typing import NDArray

from widget_state import (
    computed_state,
    FloatState,
    HigherOrderState,
    IntState,
    ObjectState,
    DictState,
    StringState,
)


class ImageConfigState(HigherOrderState):
    def __init__(self) -> None:
        super().__init__()

        self.pixel_size = FloatState(0.74588)
        self.size_unit = StringState("μm")


class ImageState(ObjectState):
    def __init__(self, value: NDArray[np.uint8]) -> None:
        super().__init__(value)


class ResolutionState(DictState):
    def __init__(self, width: int | IntState, height: int | IntState) -> None:
        """
        State defining the resolution of a displayed image.
        """
        super().__init__()

        self.width = IntState(width) if isinstance(width, int) else width
        self.height = IntState(height) if isinstance(height, int) else height


class DisplayImageState(HigherOrderState):
    def __init__(
        self,
        image_state: ImageState,
        resolution_state: Optional[ResolutionState] = None,
        interpolation: int = cv.INTER_NEAREST,
    ) -> None:
        super().__init__()

        self._interpolation = interpolation
        self.image_state = image_state
        self.resolution_state = (
            resolution_state
            if resolution_state is not None
            else ResolutionState(
                width=self.image_state.value.shape[1],
                height=self.image_state.value.shape[0],
            )
        )
        self.scale_state = self.scale_state(self.image_state, self.resolution_state)
        self.display_image_state = self.display_image_state(
            self.image_state, self.scale_state
        )

    @computed_state
    def scale_state(
        self, image_state: ImageState, resolution_state: ResolutionState
    ) -> FloatState:
        width, height = resolution_state.values()
        shape = image_state.value.shape

        scale_x = width / shape[1]
        scale_y = height / shape[0]
        scale = min(scale_x, scale_y)
        return FloatState(scale)

    @computed_state
    def display_image_state(
        self, image_state: ImageState, scale_state: FloatState
    ) -> ImageState:
        scale = scale_state.value
        return ImageState(
            cv.resize(
                image_state.value,
                None,
                fx=scale,
                fy=scale,
                interpolation=self._interpolation,
            )
        )

    def copy(self) -> DisplayImageState:
        return DisplayImageState(
            ImageState(self.image_state.value),
            ResolutionState(*self.resolution_state.values()),
        )

    def to_image_coords(self, x, y):
        shape = self.display_image_state.value.shape

        t_x = (self.resolution_state.width.value - shape[1]) // 2
        t_y = (self.resolution_state.height.value - shape[0]) // 2

        x = round((x - t_x) / self.scale_state.value)
        y = round((y - t_y) / self.scale_state.value)
        return x, y

    def to_display(self, x, y):
        shape = self.display_image_state.value.shape
        scale = self.scale_state.value

        t_x = (self.resolution_state.width.value - shape[1]) // 2
        t_y = (self.resolution_state.height.value - shape[0]) // 2

        x = round(x * scale + t_x)
        y = round(y * scale + t_y)
        return x, y


