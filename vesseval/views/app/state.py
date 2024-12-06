import json
import os

import cv2 as cv
import numpy as np
from widget_state import computed_state, FloatState, HigherOrderState, StringState, ObjectState

from ...state import (
    ContourState,
    DisplayImageState,
    ImageState,
    ImageConfigState,
    ResolutionState,
)

placeholder_image = np.zeros((512, 512, 3), np.uint8)

class AppState(HigherOrderState):

    def __init__(self):
        super().__init__()

        self.filename_state = StringState("")
        self.save_directory = StringState("")

        self.image_config = ImageConfigState()
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

    def load(self, _dir: str):
        state_json = os.path.join(_dir, "app_state.json")
        if not os.path.isfile(state_json):
            print(f"Cannot find file {state_json} to restore state")
            return

        with self:
            file_image = os.path.join(_dir, "image.png")
            if os.path.isfile(file_image):
                self.filename_state.value = file_image

            with open(state_json, mode="r") as f:
                self.deserialize(json.load(f))


app_state = AppState()
