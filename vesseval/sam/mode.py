"""
The GUI behaves different depending on the current mode.
To be more exact, the canvas allows different interactions, e.g.
double-clicking to create a new region or drawing a bounding box.
Thus, a mode consists of bindings for the canvas, which are registered
when the mode becomes active.

Different modes can be activated using the toolbar.
"""

from typing import Callable

import cv2 as cv
import tkinter as tk
from widget_state import BoolState

from ..state import PointState, BoundingBoxState
from ..widgets.canvas import BoundingBox

from .state import app_state, RegionState


class AbstractMode:
    """
    Abstract mode which handle the bindings on a canvas of a mode.

    Mode implementations must overwrite the `register_bindings` method.
    """

    def __init__(self, canvas: tk.Canvas, state: bool | BoolState = False) -> None:
        self.canvas = canvas
        self.state = BoolState(state) if isinstance(state, bool) else state

        self.binding_ids: dict[str, str] = {}
        self.bindings: dict[str, Callable[[tk.Event], None]] = {}
        self.register_bindings()

        self.state.on_change(
            lambda _: self.bind() if self.state.value else self.unbind(),
            trigger=True,
        )

    def register_bindings(self) -> None:
        raise NotImplementedError("Call to abtstract method <regster_bindings>!")

    def bind(self) -> None:
        for binding, callback in self.bindings.items():
            id = self.canvas.bind(binding, callback)
            self.binding_ids[binding] = id

    def unbind(self) -> None:
        for binding, id in self.binding_ids.items():
            self.canvas.unbind(binding, id)
        self.binding_ids.clear()


class PointMode(AbstractMode):

    def __init__(self, canvas: tk.Canvas, state: bool | BoolState = False) -> None:
        super().__init__(canvas=canvas, state=state)

    def register_bindings(self) -> None:
        self.bindings["<Double-Button-1>"] = self.add_region
        self.bindings["<Double-Button-3>"] = self.add_bg_point
        self.bindings["<Button-1>"] = self.select_region

    def add_region(self, event: tk.Event) -> None:
        point = (event.x, event.y)
        # transform location of event from canvas coordinates to image coordinates
        point = app_state.display_image.to_image_coords(*point)

        region = RegionState(pt=point)
        app_state.regions.append(region)
        # updating the selected region will update drawn foreground markers
        app_state.selected_region_index.value = len(app_state.regions) - 1

    def select_region(self, event: tk.Event):
        # Check if the click is on an object.
        # This is required because background points can be on other regions.
        #
        # How does it work?
        #  `overlapping` returns a list of object ids under the event.
        #  This will always be at least 1 because the image is also an object.
        #  Thus, if `len(overlapping) > 1` something other than the image has been clicked.
        overlapping = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        if len(overlapping) > 1:
            return

        point = (event.x, event.y)
        # transform location of event from canvas coordinates to image coordinates
        point = app_state.display_image.to_image_coords(*point)

        for i, region in enumerate(app_state.regions):
            contour = region.contour.to_numpy()
            if len(contour) == 0:
                continue

            is_inside = (
                cv.pointPolygonTest(region.contour.to_numpy(), point, measureDist=False)
                > 0
            )
            if is_inside:
                app_state.selected_region_index.value = i
                break

    def add_bg_point(self, event: tk.Event):
        point = (event.x, event.y)
        # transform location of event from canvas coordinates to image coordinates
        point = app_state.display_image.to_image_coords(*point)

        try:
            if app_state.selected_region_index.value < 0:
                return
            app_state.get_selected_region().background_points.append(PointState(*point))
        except IndexError:
            # ignore points that cannot be added because no region is active
            pass


class BoxMode(AbstractMode):

    def __init__(self, canvas: tk.Canvas, state: bool | BoolState = False) -> None:
        super().__init__(canvas=canvas, state=state)

        self.bounding_box = None

    def register_bindings(self) -> None:
        self.bindings["<Button-1>"] = self.init_box
        self.bindings["<B1-Motion>"] = self.draw_box
        self.bindings["<B1-ButtonRelease>"] = self.finish_box

    def init_box(self, event: tk.Event) -> None:
        x1, y1 = event.x, event.y
        x2, y2 = x1 + 1, y1 + 1
        self.bounding_box = BoundingBox(self.canvas, BoundingBoxState(x1, y1, x2, y2))

    def draw_box(self, event: tk.Event) -> None:
        self.bounding_box.state.bottom_right().set(event.x, event.y)

    def finish_box(self, event: tk.Event) -> None:
        x1, y1 = self.bounding_box.state.top_left().values()
        x2, y2 = self.bounding_box.state.bottom_right().values()

        x1, y1 = app_state.display_image.to_image_coords(x1, y1)
        x2, y2 = app_state.display_image.to_image_coords(x2, y2)

        self.bounding_box.delete()
        self.bounding_box = None

        # call unbind manually because otherwise, other bindings might
        # be register before which confuses tkinter
        self.unbind()
        self.state.value = False

        app_state.add_region(RegionState(bb=(x1, y1, x2, y2)))
