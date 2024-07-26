from typing import Callable, Optional

import tkinter as tk

from ...state import PointState, HigherState, IntState, StringState
from .lib import CanvasItem


class RectangleState(HigherState):

    def __init__(
        self,
        center_state: PointState,
        size_state: IntState = 9,
        color_state: StringState = "green",
    ):
        super().__init__()

        self.center_state = center_state
        self.size_state = size_state
        self.color_state = color_state

    def ltbr(self):
        size_state_h = self.size_state.value // 2
        x, y = self.center_state.values()
        return [
            x - size_state_h,
            y - size_state_h,
            x + size_state_h,
            y + size_state_h,
        ]


class Rectangle(CanvasItem):

    def __init__(self, canvas: tk.Canvas, state: RectangleState):
        super().__init__(canvas, state)

        self.id = self.canvas.create_rectangle(
            *self.state.ltbr(),
            fill=self.state.color_state.value,
        )

    def redraw(self, state):
        self.canvas.coords(self.id, *state.ltbr())
        self.canvas.itemconfig(self.id, fill=state.color_state.value)
