import cv2 as cv
import numpy as np

from .image import DisplayImageState, ImageState, ResolutionState
from .lib import (
    computed_state,
    FloatState,
    HigherState,
    StringState,
    ObjectState,
)

placeholder_image = np.zeros((512, 512, 3), np.uint8)


class AppState(HigherState):

    def __init__(self):
        super().__init__()

        self.filename_state = StringState("")
        self.pixel_size_state = FloatState(0.74588)
        self.size_unit_state = StringState("μm")

        self.display_resolution_state = ResolutionState(1600, 900)
        self.display_image_state = DisplayImageState(
            ImageState(placeholder_image),
            self.display_resolution_state,
            interpolation=cv.INTER_AREA,
        )

        self.filename_state.on_change(self.on_filename)

    def on_filename(self, state: StringState):
        filename = state.value

        if filename == "":
            self.display_image_state.image_state.set(placeholder_image)
            return

        image = cv.imread(filename)
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        self.display_image_state.image_state.set(image)


app_state = AppState()
