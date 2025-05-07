import tkinter as tk
from widget_state import HigherOrderState, IntState

from ...state import BoundingBoxState, PointState
from ..util import stateful
from .bounding_box import BoundingBox
from .circle import Circle, CircleState
from .lib import CanvasItem


class GridState(HigherOrderState):

    def __init__(self):
        super().__init__()

        self.x = IntState(0)
        self.y = IntState(0)
        self.width = IntState(1)
        self.height = IntState(1)
        self.n_points_x = IntState(3)
        self.n_points_y = IntState(3)


@stateful
class Grid:

    def __init__(self, canvas: tk.Canvas, state: GridState):
        self.widget = canvas
        self.canvas = canvas
        self.state = state

        self.bounding_box = None
        self.points = []

    def draw(self):
        self.delete()

        state = self.state

        # draw bounding box
        self.bounding_box = BoundingBox(
            self.canvas,
            BoundingBoxState(
                state.x,
                state.y,
                state.x.value + state.width.value,
                state.y.value + state.height.value,
            ),
        )
        self.bounding_box.style.rectangle_size.value = 0
        self.bounding_box.style.line_color.value = "white"

        # draw points
        t, l = self.bounding_box.state.top_left()
        b, r = self.bounding_box.state.bottom_right()

        n_rows = self.state.n_points_x.value
        n_cols = self.state.n_points_y.value
        step_x = (r.value - l.value) / n_rows
        step_y = (b.value - t.value) / n_cols
        for i in range(n_rows + 1):
            t_x = step_x * i
            for j in range(n_cols + 1):
                t_y = step_y * j

                pt = Circle(
                    self.canvas,
                    CircleState(
                        PointState(t.value + t_y, l.value + t_x),
                        color="white",
                        radius=3,
                        outline="black",
                    ),
                )
                self.points.append(pt)

    def delete(self) -> None:
        if self.bounding_box is not None:
            self.bounding_box.delete()
            self.bounding_box = None

        for pt in self.points:
            pt.delete()
        self.points.clear()
