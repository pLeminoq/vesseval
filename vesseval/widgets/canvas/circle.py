from widget_state import HigherOrderState, IntState, StringState
import tkinter as tk

from ...state import PointState
from .lib import CanvasItem


class CircleState(HigherOrderState):
    def __init__(
        self,
        center: PointState,
        radius: IntState = 9,
        color: StringState = "green",
        outline: StringState = "black",
        outline_width: IntState = 1,
    ):
        super().__init__()

        self.center = center
        self.radius = radius
        self.color = color
        self.outline = outline
        self.outline_width = outline_width

    def ltbr(self):
        radius = self.radius.value
        cx, cy = self.center.values()
        return [
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
        ]


class Circle(CanvasItem):

    def __init__(self, canvas: tk.Canvas, state: CircleState):
        super().__init__(canvas, state)

        self.id = self.canvas.create_oval(
            *self.state.ltbr(),
            fill=self.state.color.value,
        )

    def redraw(self, state):
        self.canvas.coords(self.id, *state.ltbr())
        self.canvas.itemconfig(
            self.id,
            fill=state.color.value,
            outline=state.outline.value,
            width=state.outline_width.value,
        )
