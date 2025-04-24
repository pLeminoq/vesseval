import json
import os
import time
from threading import Thread
from typing import Any, Optional

import cv2 as cv
import diplib as dip
import numpy as np
from widget_state import (
    HigherOrderState,
    StringState,
    ListState,
    ObjectState,
    IntState,
    computed_state,
    FloatState,
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
from .util import Geometry, get_active_monitor


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

        self._skip_update = False

        self.label = StringState(None)

        self.foreground_point = (
            PointState(UNUSED_VALUE, UNUSED_VALUE) if pt is None else PointState(*pt)
        )
        self.background_points = ContourState()
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

        """
        Note: this is a workaround because `asynchron` as a decorator had the bug
        that an instance method would be synchronized across all instances. Using
        the lambda, it is ensured that the synchronization happens per-instance.
        The bug is fixed but I am not able to update depencies because my colleagues
        currently cannot instlal new dependencies.
        TODO: replace decorator on instance method with `async_once` on new 
        release of reacTk dependency.
        """
        self._update_contour_async = asynchron(lambda: self.update_contour())
        self._update_contour_async()

        self.foreground_point.on_change(lambda _: self._update_contour_async())
        self.background_points.on_change(
            lambda _: self._update_contour_async(), element_wise=True
        )
        self.foreground_box.on_change(lambda _: self._update_contour_async())

    # @asynchron
    def update_contour(self):
        if self._skip_update:
            return

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

            if input_points is None and input_box is None:
                return

            cnt = IMAGE_PREDICTOR.predict_as_contour(
                point_coords=input_points,
                point_labels=input_labels,
                box=input_box,
            )

            self.contour.extend(ContourState.from_numpy(cnt))

    def deserialize(self, data):
        self._skip_update = True
        super().deserialize(data)
        self._skip_update = False


class RegionList(ListState):

    def __init__(self):
        super().__init__()

    def deserialize(self, data: list[dict[str, Any]]) -> None:
        with self:
            self.clear()

            for value in data:
                region_state = RegionState()
                region_state.deserialize(value)
                self.append(region_state)


class AppState(HigherOrderState):

    def __init__(self):
        super().__init__()

        self.filename_save = StringState("")
        self.filename_save.on_change(lambda _: self.save())

        self.pixel_size_x = FloatState(1.0)
        self.pixel_size_y = FloatState(1.0)
        self.pixel_unit = StringState("mm")

        self.filename = StringState("")
        self.filename.on_change(self.update_pixel_size)

        self.regions = RegionList()
        self.contours = virtual_list(
            self.regions, lambda region_state: region_state.contour
        )
        self.selected_region_index = IntState(-1)
        self.filename.on_change(lambda _: self.regions.clear())
        self.filename.on_change(lambda _: self.selected_region_index.set(-1))

        self.original_image = self.load_image(self.filename)

        # original image resolution - is needed for evaluation of region stats in original size
        self.original_resolution = ResolutionState(0, 0)
        self.original_image.on_change(
            lambda _: self.original_resolution.set(
                *self.original_image.value.shape[:2][::-1]
            ),
            trigger=True,
        )

        # internal resolution is for internal processing
        # it ensures that the image will be smaller than 1024 pixel so that processing
        # by the SAM model remains fast
        self.internal_resolution = ResolutionState(0, 0)
        self.original_resolution.on_change(
            lambda _: self.internal_resolution.set(
                *self.compute_internal_resolution(self.original_resolution)
            ),
            trigger=True,
        )

        # canvas resolution
        # this resolution determines the size of the displayed canvas/GUI
        self.canvas_resolution = ResolutionState(1600, 900)

        # TODO: internal resolution must depend on the aspect ratio of the image
        self.image = self.resize_image(self.original_image, self.internal_resolution)
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
            resolution_state=self.canvas_resolution,
        )

    @computed_state
    def load_image(self, filename: StringState) -> ImageState:
        if filename.value == "":
            image = np.zeros((1024, 1024, 3), np.uint8)
        else:
            image = cv.imread(filename.value)
            image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        return ImageState(image)

    def update_pixel_size(self, filename: StringState):
        dip_img = dip.ImageRead(filename.value)
        pixel_size = dip_img.PixelSize()

        physical_q_x = pixel_size[0]
        self.pixel_size_x.value = physical_q_x.magnitude
        self.pixel_unit.value = physical_q_x.units

        physical_q_y = pixel_size[1]
        self.pixel_size_y.value = physical_q_y.magnitude

    def compute_internal_resolution(
        self, original_resolution: ResolutionState
    ) -> tuple[int, int]:
        original_resolution = original_resolution.values()

        max_dim = np.argmax(original_resolution)
        max_res = min(original_resolution[max_dim], 1024)

        scale = max_res / original_resolution[max_dim]

        width = round(original_resolution[0] * scale)
        height = round(original_resolution[1] * scale)

        return width, height

    @computed_state
    def resize_image(
        self, original_image: ImageState, internal_resolution: ResolutionState
    ) -> ImageState:
        return ImageState(cv.resize(original_image.value, internal_resolution.values()))

    def configure_canvas_resolution(self, geometry_str: str):
        geometry = Geometry.from_str(geometry_str)
        monitor = get_active_monitor(geometry)
        height = monitor.height - 200 - geometry.y
        width = round(height * 16.0 / 9.0)
        self.canvas_resolution.set(width, height)

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

    def eval_regions(self):
        contours = list(map(lambda cnt: cnt.to_numpy(), self.contours))

        scale_y = self.original_resolution.height.value / self.image.value.shape[0]
        scale_x = self.original_resolution.width.value / self.image.value.shape[1]

        table = {
            "index": [],
            "category": [],
            "area": [],
            "perimeter": [],
            "cut_off": [],
            "roundness": [],
            "circularity": [],
            "feret_max": [],
            "feret_min": [],
            "feret_perp_min": [],
            "feret_max_angle": [],
            "feret_min_angle": [],
            "filename": [],
        }
        rows = []

        for i, contour in enumerate(contours, start=1):
            cut_off_min = (contour <= 0).any()
            cut_off_max_x = (
                contour[:, 0].max() >= (self.image.value.shape[1] - 1)
            ).any()
            cut_off_max_y = (
                contour[:, 1].max() >= (self.image.value.shape[0] - 1)
            ).any()
            cut_off = cut_off_min or cut_off_max_x or cut_off_max_y

            contour[:, 0] = np.rint(contour[:, 0] * scale_x)
            contour[:, 1] = np.rint(contour[:, 1] * scale_x)

            label = 1
            label_img = np.zeros(
                (
                    self.original_resolution.height.value,
                    self.original_resolution.width.value,
                ),
                dtype=np.uint8,
            )
            label_img = cv.drawContours(
                label_img, [contour], contourIdx=-1, color=label, thickness=-1
            )

            # convert image to dip and configure pixel size
            _img = dip.Image(label_img)
            _img.SetPixelSize(
                dip.PixelSize(
                    (
                        app_state.pixel_size_x.value
                        * dip.PhysicalQuantity(app_state.pixel_unit.value),
                        app_state.pixel_size_y.value
                        * dip.PhysicalQuantity(app_state.pixel_unit.value),
                    )
                )
            )
            label_img = dip.Label(_img > 0)

            measures = dip.MeasurementTool.Measure(
                label_img,
                features=["Size", "Perimeter", "Feret", "Roundness", "Circularity"],
            )

            table["filename"].append(self.filename.value)
            table["index"].append(i)
            table["category"].append(self.regions[i - 1].label.value)
            table["area"].append(measures[label]["Size"][0])
            table["perimeter"].append(measures[label]["Perimeter"][0])
            table["cut_off"].append(cut_off)
            table["roundness"].append(measures[label]["Roundness"][0])
            table["circularity"].append(measures[label]["Circularity"][0])
            table["feret_max"].append(measures[label]["Feret"][0])
            table["feret_min"].append(measures[label]["Feret"][1])
            table["feret_perp_min"].append(measures[label]["Feret"][2])
            table["feret_max_angle"].append(measures[label]["Feret"][3])
            table["feret_min_angle"].append(measures[label]["Feret"][4])

        return table

    def serialize(self) -> dict[str, Any]:
        data = super().serialize()
        del data["contours"]
        return data

    def save(self):
        filename, _ = os.path.splitext(self.filename_save.value)
        filename = filename + ".json"
        with open(filename, mode="w") as f:
            json.dump(self.serialize(), f, indent=2)

    def load(self, filename: str):
        with self:
            with open(filename, mode="r") as f:
                self.deserialize(json.load(f))

        store = self.selected_region_index.value
        self.selected_region_index.value = store - 1
        self.selected_region_index.value = store


app_state = AppState()
