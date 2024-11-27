import time
from threading import Thread

import cv2 as cv
import numpy as np
from widget_state import HigherOrderState, StringState, ListState, ObjectState

from ..state import ResolutionState, DisplayImageState, ImageState, ContourState
from .sam import IMAGE_PREDICTOR

ALPHA = 0.4
# https://gist.github.com/afcotroneo/ca9716f755128b5e9b2ed1fe4186f4df#file-omni-dutch-field
COLORS = np.array(
    [
        [230, 0, 73],
        [11, 180, 255],
        [80, 233, 145],
        [230, 216, 0],
        [155, 25, 245],
        [255, 163, 0],
        [220, 10, 180],
        [179, 212, 255],
        [0, 191, 160],
    ]
)


class AppState(HigherOrderState):

    def __init__(self):
        super().__init__()

        self.points_fg = ContourState()
        self.points_bg = ContourState()

        self.filename = StringState(
            "../segment_anything/data/ED002_004_8b_gridE425.tif"
        )

        self.image = ImageState(
            cv.cvtColor(cv.imread(self.filename.value), cv.COLOR_BGR2RGB)
        )
        self.masks = ListState([])
        self.contours = ListState([])

        IMAGE_PREDICTOR.set_image(self.image.value)

        self.display_image = DisplayImageState(
            image_state=ImageState(cv.cvtColor(self.image.value, cv.COLOR_RGB2RGBA)),
            resolution_state=ResolutionState(1600, 900),
        )

        # self.masks.on_change(lambda _: self.display_image.image_state.set(self.compute_image(self.image, self.masks)))
        self.contours.on_change(
            lambda cnts: self.display_image.image_state.set(
                self.compute_image(self.image, cnts)
            )
        )

    def predict_mask(self, pt, pts_bg):
        input_points = np.array([pt]).astype(int)
        input_labels = np.array([1])

        mask = IMAGE_PREDICTOR.predict(
            point_coords=input_points, point_labels=input_labels
        )

        mask = mask.astype(np.uint8)
        cnts, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        areas = list(map(lambda cnt: cv.contourArea(cnt), cnts))
        cnt = cnts[np.argmax(areas)]

        self.contours.append(ObjectState(cnt))

    def compute_image(self, image: ImageState, contours: ListState):
        _image = image.value.copy()
        since = time.time()
        colored_masks = np.zeros(_image.shape)
        for i, contour in enumerate(contours):
            color = COLORS[i % len(COLORS)].tolist()

            cnt = contour.value
            x, y, w, h = cv.boundingRect(cnt)
            x2, y2 = x + w, y + h

            mask = np.zeros((h, w, 3), np.uint8)
            cv.drawContours(mask, [cnt], -1, color, -1, offset=(-x, -y))

            _image[y:y2, x:x2] = cv.addWeighted(
                _image[y:y2, x:x2], 1.0, mask, ALPHA, 0, 0
            )

            # _mask = mask.value
            # _mask = _mask.reshape(*_mask.shape, 1) * color.reshape(1, 1, -1)
            # _mask = _mask.astype(np.uint8)
            # colored_masks = colored_masks + _mask
            # _image = cv.drawContours(_image, [contour.value], -1, color=color, thickness=-1)

        # cv.imshow("Test", _image)
        # cv.waitKey(50)
        # colored_masks = colored_masks.astype(np.uint8)
        # print(f"{_image.dtype=}, {_image.shape}, {_mask.dtype}, {_mask.shape}")
        # _image = cv.addWeighted(_image, 1.0, colored_masks, ALPHA, 0.0)
        return _image

    def on_filename(self):
        # TODO: update self.image to new file
        pass

    def on_image(self):
        # TODO: update self.display_image to new image
        pass


app_state = AppState()
