import cv2 as cv
import tkinter as tk

from ..state import PointState, BoundingBoxState
from ..widgets.canvas import Image, Circle, CircleState, BoundingBox

from .menu import MenuBar
from .mode import PointMode, BoxMode
from .region import RegionView
from .state import app_state, RegionState
from .toolbar import Toolbar


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.configure(bg="#757575")

        self.state = app_state

        self.update_idletasks()
        self.state.configure_canvas_resolution(self.winfo_geometry())

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=2)
        self.rowconfigure(1, weight=10)

        self.menu_bar = MenuBar(self)

        self.toolbar = Toolbar(self)
        self.toolbar.grid(column=0, row=0, sticky=tk.W + tk.E, columnspan=2)
        # self.toolbar.grid(column=0, row=0, sticky=tk.W + tk.E, rowspan=2)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.configure(bg="#757575")
        self.canvas.grid(column=0, row=1)

        self.point_mode = PointMode(self.canvas, self.toolbar.state.point_mode)
        self.box_mode = BoxMode(self.canvas, self.toolbar.state.box_mode)

        self.image = Image(self.canvas, app_state.display_image)

        self.fg_circle = None
        self.bg_circles = []
        self.fg_box = None

        self.state.selected_region_index.on_change(lambda _: self.on_select_region())

        self.region_view = RegionView(self)
        self.region_view.grid(row=1, column=1, sticky="nswe")

        self.bind("<Key-q>", lambda event: exit(0))

    def on_select_region(self):
        self.clear_selected_region_markers()

        if self.state.selected_region_index.value < 0:
            return

        selected_region = self.state.regions[self.state.selected_region_index.value]

        self.draw_foregound_circle(selected_region)
        self.draw_foregound_box(selected_region)
        selected_region.background_points.on_change(
            lambda _: self.redraw_background_points(), trigger=True
        )

    def clear_selected_region_markers(self):
        # clear markers
        if self.fg_circle is not None:
            self.fg_circle.delete()
            self.fg_circle = None

        if self.fg_box is not None:
            self.fg_box.delete()
            self.fg_box = None

        self.clear_background_circles()

    def clear_background_circles(self):
        for circle in self.bg_circles:
            circle.delete()
        self.bg_circles.clear()

    def draw_foregound_circle(self, selected_region: RegionState) -> None:
        # initialize position of circle and react to selected_region changes
        circle_center = PointState(0, 0)
        selected_region.foreground_point.on_change(
            lambda state: circle_center.set(
                *self.state.display_image.to_display(*state.values())
            ),
            trigger=True,
        )

        # draw circle
        self.fg_circle = Circle(
            self.canvas,
            state=CircleState(
                circle_center,
                color="white",
                radius=5,
                outline="black",
            ),
        )

        # handle events
        self.fg_circle.tag_bind(
            "<B1-Motion>",
            lambda ev, _: selected_region.foreground_point.set(
                *self.state.display_image.to_image_coords(ev.x, ev.y)
            ),
        )
        self.fg_circle.tag_bind(
            "<Button-3>",
            lambda ev, _: self.state.remove_region(selected_region),
        )

    def draw_foregound_box(self, selected_region: RegionState) -> None:
        # initialize bounding box and react to selected_region changes
        top_left = PointState(0, 0)
        bottom_right = PointState(0, 0)
        selected_region.foreground_box.top_left().on_change(
            lambda state: top_left.set(
                *self.state.display_image.to_display(*state.values())
            ),
            trigger=True,
        )
        selected_region.foreground_box.bottom_right().on_change(
            lambda state: bottom_right.set(
                *self.state.display_image.to_display(*state.values())
            ),
            trigger=True,
        )

        self.fg_box = BoundingBox(
            self.canvas,
            state=BoundingBoxState(
                top_left.x, top_left.y, bottom_right.x, bottom_right.y
            ),
        )

        for name, rectangle in self.fg_box.rectangles.items():
            rectangle.tag_bind(
                "<Button-3>",
                lambda *_: self.state.remove_region(selected_region),
            )

        self.fg_box.rectangles["top_left"].tag_bind(
            "<B1-Motion>",
            lambda ev, _: selected_region.foreground_box.top_left().set(
                *self.state.display_image.to_image_coords(ev.x, ev.y)
            ),
        )
        self.fg_box.rectangles["top_right"].tag_bind(
            "<B1-Motion>",
            lambda ev, _: selected_region.foreground_box.top_right().set(
                *self.state.display_image.to_image_coords(ev.x, ev.y)
            ),
        )
        self.fg_box.rectangles["bottom_left"].tag_bind(
            "<B1-Motion>",
            lambda ev, _: selected_region.foreground_box.bottom_left().set(
                *self.state.display_image.to_image_coords(ev.x, ev.y)
            ),
        )
        self.fg_box.rectangles["bottom_right"].tag_bind(
            "<B1-Motion>",
            lambda ev, _: selected_region.foreground_box.bottom_right().set(
                *self.state.display_image.to_image_coords(ev.x, ev.y)
            ),
        )

    def redraw_background_points(self):
        self.clear_background_circles()

        selected_region = self.state.regions[self.state.selected_region_index.value]
        for i, background_point in enumerate(selected_region.background_points):
            circle_center = PointState(0, 0)
            background_point.on_change(
                lambda state: circle_center.set(
                    *self.state.display_image.to_display(*state.values())
                ),
                trigger=True,
            )

            background_circle = Circle(
                self.canvas,
                state=CircleState(
                    circle_center,
                    color="black",
                    radius=5,
                    outline="white",
                ),
            )
            background_circle.tag_bind(
                "<B1-Motion>",
                lambda ev, _: background_point.set(
                    *self.state.display_image.to_image_coords(ev.x, ev.y)
                ),
            )

            background_circle.tag_bind(
                "<Button-3>",
                # assignment trick (i=i) so that the value is stored in the function
                # see: https://stackoverflow.com/a/10865170
                lambda *_, i=i: selected_region.background_points.pop(i),
            )
            self.bg_circles.append(background_circle)
