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
from tkinter import ttk
from widget_state import BoolState, HigherOrderState, StringState

from ..state import PointState, BoundingBoxState
from ..widgets.canvas import BoundingBox, Circle, CircleState
from ..widgets.canvas.grid import Grid, GridState
from ..widgets.label import Label
from ..widgets.textfield import IntTextField

from .state import app_state, RegionState, PointState, IMAGE_PREDICTOR


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



class GridConfigView(tk.Toplevel):

    def __init__(self, grid) -> None:
        super().__init__()

        self.grid = grid

        self.label_x = Label(self, StringState("Points x:"), justify=tk.LEFT)
        self.label_x.grid(column=0, row=0, padx=(10, 2), pady=(10, 5), sticky=tk.W)

        self.label_y = Label(self, StringState("Points y:"), justify=tk.LEFT)
        self.label_y.grid(column=0, row=1, padx=(10, 2), pady=(10, 5), sticky=tk.W)

        self.n_points_x_textfield = IntTextField(self, self.grid.state.n_points_x)
        self.n_points_x_textfield.grid(column=1, row=0, pady=(5, 5))
        self.n_points_x_textfield.bind("<Left>", lambda _: self.grid.state.n_points_x.set(max(2, self.grid.state.n_points_x.value - 1)))
        self.n_points_x_textfield.bind("<Right>", lambda _: self.grid.state.n_points_x.set(min(40, self.grid.state.n_points_x.value + 1)))

        self.n_points_y_textfield = IntTextField(self, self.grid.state.n_points_y)
        self.n_points_y_textfield.grid(column=1, row=1, pady=(5, 5))
        self.n_points_y_textfield.bind("<Left>", lambda _: self.grid.state.n_points_y.set(max(2, self.grid.state.n_points_y.value - 1)))
        self.n_points_y_textfield.bind("<Right>", lambda _: self.grid.state.n_points_y.set(min(40, self.grid.state.n_points_y.value + 1)))

        self.button = ttk.Button(self, text="Confirm", command=self.on_confirm)
        self.button.grid(column=0, row=2, columnspan=2, pady=(5, 10))

        self.bind("<Key-q>", lambda event: exit(0))

    def on_confirm(self, *args) -> None:
        coords = []
        for pt in self.grid.points:
            c = app_state.display_image.to_image_coords(pt.state.center.x.value, pt.state.center.y.value)
            
            img_shape = app_state.display_image.image_state.value.shape
            if c[0] < 0 or c[1] < 0 or c[0] > img_shape[1] or c[1] > img_shape[0]:
                continue

            coords.append(c)
            pt.delete()
        self.grid.delete()

        points, contours = IMAGE_PREDICTOR.predict_multiple_as_contour(coords) 
        for pt, cnt in zip(points, contours):
            app_state.add_region(RegionState(pt=pt, cnt=cnt))

        self.withdraw()
        self.destroy()


class GridMode(AbstractMode):

    def __init__(self, canvas: tk.Canvas, state: bool | BoolState = False) -> None:
        super().__init__(canvas=canvas, state=state)

        self.grid = None
        self.grid_config = None

    def register_bindings(self) -> None:
        self.bindings["<Button-1>"] = self.draw_grid
        self.bindings["<B1-Motion>"] = self.draw_grid
        self.bindings["<B1-ButtonRelease>"] = self.finish_grid

    def draw_grid(self, event: tk.Event) -> None:
        if self.grid is None:
            grid_state = GridState()
            grid_state.x.value = event.x
            grid_state.y.value = event.y
            self.grid = Grid(self.canvas, grid_state)

            self.grid_config = GridConfigView(self.grid)
            return

        grid_state = self.grid.state
        grid_state.width.value = event.x - grid_state.x.value
        grid_state.height.value = event.y - grid_state.y.value

    def finish_grid(self, event: tk.Event) -> None:
        self.unbind()
        self.state.value = False
