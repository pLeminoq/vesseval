import json
import os

import cv2 as cv
import numpy as np

from .contour import ContourState
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
        self.save_directory = StringState("")

        self.pixel_size_state = FloatState(0.74588)
        self.size_unit_state = StringState("μm")
        self.contour_state = ContourState()

        self.display_resolution_state = ResolutionState(1600, 900)
        self.display_image_state = DisplayImageState(
            ImageState(placeholder_image),
            self.display_resolution_state,
            interpolation=cv.INTER_AREA,
        )

        self.filename_state.on_change(self.on_filename)
        self.save_directory.on_change(lambda _: self.save())

    def on_filename(self, state: StringState):
        filename = state.value

        if filename == "":
            self.display_image_state.image_state.set(placeholder_image)
            return

        image = cv.imread(filename)
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        self.display_image_state.image_state.set(image)

    def save(self):
        _dir = self.save_directory.value

        if not os.path.isdir(_dir):
            print(
                f"Cannot save app state at {_dir}, since it is not an existing directory"
            )
            return

        # write state
        state_json = os.path.join(_dir, "app_state.json")
        with open(state_json, mode="w") as f:
            json.dump(self.serialize(), f, indent=2)

        # write image if available
        if self.filename_state.value == "":
            return

        file_image = os.path.join(_dir, "image.png")
        cv.imwrite(file_image, cv.imread(self.filename_state.value))


app_state = AppState()
