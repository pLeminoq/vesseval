import cv2 as cv
import numpy as np

from .lib import computed_state, FloatState, HigherState, StringState, ObjectState

placeholder_image = np.zeros((512, 512, 3), np.uint8)


class AppState(HigherState):

    def __init__(self):
        super().__init__()

        self.filename_state = StringState("")
        self.pixel_size_state = FloatState(0.74588)
        self.size_unit_state = StringState("μm")

        self.image_state = self.image_state(self.filename_state)

    @computed_state
    def image_state(self, filename_state: StringState):
        filename = filename_state.value

        if filename == "":
            return ObjectState(placeholder_image)

        image = cv.imread(filename)
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        return ObjectState(image)


app_state = AppState()
