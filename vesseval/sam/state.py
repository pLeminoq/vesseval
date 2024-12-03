import time
from threading import Thread
from typing import Optional

import cv2 as cv
import numpy as np
from widget_state import (
    HigherOrderState,
    StringState,
    ListState,
    ObjectState,
    IntState,
    computed_state,
)

from ..state import (
    BoundingBoxState,
    ResolutionState,
    DisplayImageState,
    ImageState,
    ContourState,
    PointState,
)
from ..state.processing import asynchron
from ..state.util import virtual_list

from .sam import ImagePredictor

IMAGE_PREDICTOR = ImagePredictor()

ALPHA = 0.4
RGB_COLOR = tuple[int, int, int]
COLOR_BLACK: RGB_COLOR = (0, 0, 0)
# https://gist.github.com/afcotroneo/ca9716f755128b5e9b2ed1fe4186f4df#file-omni-dutch-field
COLOR_PALETTE: list[RGB_COLOR] = [
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

UNUSED_VALUE = -100


class RegionState(HigherOrderState):

    def __init__(self, pt=None, bb=None):
        super().__init__()

        self.foreground_point = (
            PointState(UNUSED_VALUE, UNUSED_VALUE) if pt is None else PointState(*pt)
        )
        self.background_points = ListState()
        self.foreground_box = (
            BoundingBoxState(
                UNUSED_VALUE,
                UNUSED_VALUE,
                UNUSED_VALUE,
                UNUSED_VALUE,
            )
            if bb is None
            else BoundingBoxState(*bb)
        )
        self.contour = ContourState()
        self.update_contour()

        self.foreground_point.on_change(lambda _: self.update_contour())
        self.background_points.on_change(
            lambda _: self.update_contour(), element_wise=True
        )
        self.foreground_box.on_change(lambda _: self.update_contour())

    @asynchron
    def update_contour(self):
        with self.contour:
            self.contour.clear()

            input_points = [
                self.foreground_point.values(),
                *map(lambda pt: pt.values(), self.background_points),
            ]
            input_labels = [1, *([0] * len(self.background_points))]
            if self.foreground_point.x.value == UNUSED_VALUE:
                input_points.pop(0)
                input_labels.pop(0)

            input_points = np.array(input_points) if len(input_points) > 0 else None
            input_labels = np.array(input_labels) if input_points is not None else None

            if self.foreground_box.x1.value == UNUSED_VALUE:
                input_box = None
            else:
                input_box = np.array([self.foreground_box.tlbr()])

            cnt = IMAGE_PREDICTOR.predict_as_contour(
                point_coords=input_points,
                point_labels=input_labels,
                box=input_box,
            )

            self.contour.extend(ContourState.from_numpy(cnt))


class AppState(HigherOrderState):

    def __init__(self):
        super().__init__()

        self.filename = StringState(
            "../segment_anything/data/ED002_004_8b_gridE425.tif"
        )

        self.regions = ListState()
        self.contours = virtual_list(self.regions, lambda region_state: region_state.contour)
        self.selected_region_index = IntState(-1)

        # TODO:
        #  * define internal resolution
        #  * make computed state based on filename and internal resolution
        self.image = self.load_image(self.filename)
        self.image.on_change(lambda _: self.clear_regions)
        self.image.on_change(
            lambda state: IMAGE_PREDICTOR.set_image(self.image.value), trigger=True
        )

        self.colored_regions_image = ImageState(self.draw_regions())
        self.colored_regions_image.depends_on(
            [self.image, self.contours], self.draw_regions, element_wise=True
        )

        self.final_image = ImageState(self.highlight_selected_region())
        self.final_image.depends_on(
            [self.colored_regions_image, self.contours, self.selected_region_index],
            self.highlight_selected_region,
            element_wise=True,
        )

        self.display_image = DisplayImageState(
            image_state=self.final_image,
            resolution_state=ResolutionState(1600, 900),
        )

    @computed_state
    def load_image(self, filename: StringState) -> ImageState:
        # TODO load empty image if filename is empty
        return ImageState(
            cv.cvtColor(
                cv.resize(cv.imread(self.filename.value), (1024, 1024)),
                cv.COLOR_BGR2RGB,
            )
        )

    def clear_regions(self):
        self.regions.clear()
        self.selected_region_index.value = -1

    def draw_regions(self):
        colored_regions_image = self.image.value.copy()

        for i, region in enumerate(self.regions):
            contour = region.contour.to_numpy()
            if len(contour) == 0:
                return colored_regions_image

            color = COLOR_PALETTE[i % len(COLOR_PALETTE)]

            x1, y1, w, h = cv.boundingRect(contour)
            x2, y2 = x1 + w, y1 + h

            _image = np.zeros((h, w, 3), np.uint8)
            cv.drawContours(_image, [contour], -1, color, -1, offset=(-x1, -y1))

            colored_regions_image[y1:y2, x1:x2] = cv.addWeighted(
                colored_regions_image[y1:y2, x1:x2], 1.0, _image, ALPHA, 0, 0
            )

        return colored_regions_image

    def highlight_selected_region(self):
        image = self.colored_regions_image.value.copy()
        index = self.selected_region_index.value

        if index < 0 or index >= len(self.regions):
            return image

        image = cv.drawContours(
            image,
            [self.regions[index].contour.to_numpy()],
            -1,
            COLOR_BLACK,
            thickness=3,
        )
        return image

    @computed_state
    def final_image(
        self, image: ImageState, regions: ListState, selected_region_index: IntState
    ) -> ImageState:
        image = image.value.copy()

        if selected_region_index.value < 0 or selected_region_index.value >= len(
            regions
        ):
            return ImageState(image)

        image = cv.drawContours(
            image,
            [regions[selected_region_index.value].contour.to_numpy()],
            -1,
            (0, 0, 0),
            thickness=3,
        )
        return ImageState(image)

    def get_selected_region(self) -> RegionState:
        return self.regions[self.selected_region_index.value]

    def add_region(self, region: RegionState) -> None:
        self.regions.append(region)
        self.selected_region_index.value = len(self.regions) - 1

    def remove_region(self, region: RegionState) -> None:
        self.regions.remove(region)
        self.selected_region_index.value = -1


app_state = AppState()
