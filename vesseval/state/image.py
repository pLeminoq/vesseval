from typing import Tuple

import cv2 as cv
import numpy as np

from .lib import (
    computed_state,
    FloatState,
    HigherState,
    IntState,
    ObjectState,
    SequenceState,
    StringState,
)


class ImageConfigState(HigherState):

    def __init__(self):
        super().__init__()

        self.pixel_size = FloatState(0.74588)
        self.size_unit = StringState("μm")


class ImageState(ObjectState):

    def __init__(self, value: np.ndarray):
        super().__init__(value)


class ResolutionState(SequenceState):

    def __init__(self, width: IntState, height: IntState):
        """
        State defining the resolution of a displayed image.
        """
        super().__init__(values=[width, height], labels=["width", "height"])


class DisplayImageState(HigherState):

    def __init__(
        self,
        image_state: ImageState,
        resolution_state: ResolutionState = None,
        interpolation=cv.INTER_NEAREST,
    ):
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

    def copy(self):
        return DisplayImageState(
            ImageState(self.image_state.value),
            ResolutionState(*self.resolution_state.values()),
        )
