import tkinter as tk

from ..state import PointState
from ..widgets.canvas import Image, Circle, CircleState

from .state import app_state


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.configure(bg="#757575")

        self.state = app_state

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=2)
        self.rowconfigure(1, weight=10)
        # self.rowconfigure(2, weight=1)

        # self.menu_bar = MenuBar(self)

        # self.toolbar = Toolbar(self)
        # self.toolbar.grid(column=0, row=0, sticky=tk.W + tk.E)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.configure(bg="#757575")
        self.canvas.grid(column=0, row=1)
        self.canvas.bind("<Double-Button-1>", self.add_point)

        self.circles_fg = []
        self.state.points_fg.on_change(lambda _: self.redraw_points())

        # self.bb_mode_bindings = {}
        # self.erase_mode = {}
        # self.toolbar.state.bounding_box_mode.on_change(self.on_bb_mode, trigger=True)
        # self.toolbar.state.erase_mode.on_change(self.on_erase_mode, trigger=True)

        self.image = Image(self.canvas, app_state.display_image)

        self.bind("<Key-q>", lambda event: exit(0))

    def add_point(self, event):
        # TODO: differentiate fg and bg mode
        img_coords = self.state.display_image.to_image_coords(event.x, event.y)
        bg_points = list(
            map(
                lambda pt: self.state.display_image.to_image_coords(*pt.values()),
                self.state.points_fg,
            )
        )
        self.state.predict_mask(img_coords, bg_points)
        self.state.points_fg.append(PointState(event.x, event.y))

    def redraw_points(self):
        # TODO: differentiate fg and bg mode
        for circle in self.circles_fg:
            circle.delete()
        self.circles_fg.clear()

        for pt in self.state.points_fg:
            circle = Circle(
                self.canvas,
                state=CircleState(pt, color="white", radius=5, outline="black"),
            )
            circle.tag_bind("<B1-Motion>", self.move_circle)
            circle.tag_bind("<Button-3>", self.delete_circle)
            self.circles_fg.append(circle)

    def move_circle(self, event, circle):
        circle.state.center.set(event.x, event.y)

    def delete_circle(self, event, circle):
        if circle.state.center in self.state.points_fg:
            self.state.points_fg.remove(circle.state.center)
