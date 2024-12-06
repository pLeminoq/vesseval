from typing import Optional

import tkinter as tk
from widget_state import HigherOrderState, StringState, IntState

from ...state import PointState
from ..util import stateful
from .lib import CanvasItem


class LineState(HigherOrderState):

    def __init__(
        self,
        start_state: PointState,
        end_state: PointState,
        color_state: StringState,
        width: IntState = 1,
    ):
        super().__init__()

        self.start_state = start_state
        self.end_state = end_state
        self.color_state = color_state
        self.width = width


@stateful
class Line(CanvasItem):

    def __init__(self, canvas: tk.Canvas, state: LineState):
        super().__init__(canvas, state)

        self.id = None

    def draw(self):
        state = self.state
        if self.id is None:
            self.id = self.canvas.create_line(
                *self.state.start_state.values(),
                *self.state.end_state.values(),
                fill=self.state.color_state.value,
                width=self.state.width.value,
            )

        self.canvas.coords(
            self.id, *state.start_state.values(), *state.end_state.values()
        )
        self.canvas.itemconfig(
            self.id, fill=state.color_state.value, width=state.width.value
        )
