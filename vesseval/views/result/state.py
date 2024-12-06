import json
import os
import shutil
import tempfile

import cv2 as cv
from widget_state import HigherOrderState, StringState

from .cell_layer import CellLayerState

from ..app.state import app_state

class ResultViewState(HigherOrderState):

    def __init__(
        self, cell_layer_state_1: CellLayerState, cell_layer_state_2: CellLayerState
    ):
        super().__init__()

        self.cell_layer_state_1 = cell_layer_state_1
        self.cell_layer_state_2 = cell_layer_state_2

        self.save_filename = StringState("")
        self.save_filename.on_change(lambda _: self.save())

    def save(self):
        _serialized = self.serialize()
        _serialized["app_state-contour"] = app_state.contour_state.serialize()
        _serialized["app_state-filename"] = app_state.filename_state.serialize()

        with tempfile.TemporaryDirectory() as _dir:

            filename_state = os.path.join(_dir, "state.json")
            with open(filename_state, mode="w") as f:
                json.dump(_serialized, f, indent=2)

            image = self.cell_layer_state_1.image.value
            image = cv.cvtColor(image, cv.COLOR_RGB2BGR)
            filename_image = os.path.join(_dir, "cell_layer_image.png")
            cv.imwrite(filename_image, image)

            image = cv.imread(app_state.filename_state.value)
            filename_image = os.path.join(_dir, "image.png")
            cv.imwrite(filename_image, image)

            for i, cell_layer_state in enumerate(
                [self.cell_layer_state_1, self.cell_layer_state_2]
            ):
                mask = cell_layer_state.mask.value
                filename_mask = os.path.join(_dir, f"mask_{i}.png")
                cv.imwrite(filename_mask, mask)

            _save_filename, _ = os.path.splitext(self.save_filename.value)
            shutil.make_archive(_save_filename, format="zip", root_dir=_dir)
