from typing import Optional

import tkinter as tk

from ...state import PointState, HigherState, StringState
from .lib import CanvasItem


class LineState(HigherState):

    def __init__(
        self, start_state: PointState, end_state: PointState, color_state: StringState
    ):
        super().__init__()

        self.start_state = start_state
        self.end_state = end_state
        self.color_state = color_state


class Line(CanvasItem):

    def __init__(self, canvas: tk.Canvas, state: LineState):
        super().__init__(canvas, state)

        self.id = self.canvas.create_line(
            *self.state.start_state.values(),
            *self.state.end_state.values(),
            fill=self.state.color_state.value,
        )

    def redraw(self, state):
        self.canvas.coords(
            self.id, *state.start_state.values(), *state.end_state.values()
        )
        self.canvas.itemconfig(self.id, fill=state.color_state.value)
