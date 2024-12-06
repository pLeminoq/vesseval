from typing import List

import numpy as np
import tkinter as tk
from widget_state import HigherOrderState, StringState, IntState

from ...state import PointState, BoundingBoxState
from ..util import stateful
from .line import Line, LineState
from .rectangle import Rectangle, RectangleState


class BoundingBoxStyle(HigherOrderState):

    def __init__(self):
        self.rectangle_color = StringState("white")
        self.rectangle_size = IntState(10)
        self.rectangle_outline = StringState("black")
        self.rectangle_outline_width = 2
        self.line_color = StringState("black")
        self.line_width = 2


class BoundingBox:

    def __init__(self, canvas: tk.Canvas, state: BoundingBoxState):
        self.canvas = canvas
        self.widget = canvas
        self.state = state

        self.style = BoundingBoxStyle()
        self.lines = {}
        self.rectangles = {}

        self.draw()

    def draw(self):
        names = ["top", "left", "bottom", "right"]
        pt_pairs = [
            (self.state.top_left(), self.state.top_right()),
            (self.state.top_left(), self.state.bottom_left()),
            (self.state.bottom_left(), self.state.bottom_right()),
            (self.state.bottom_right(), self.state.top_right()),
        ]
        for name, (start, end) in zip(names, pt_pairs):
            self.lines[name] = Line(
                self.canvas,
                state=LineState(
                    start,
                    end,
                    color_state=self.style.line_color,
                    width=self.style.line_width,
                ),
            )

        names = ["top_left", "top_right", "bottom_left", "bottom_right"]
        pts = [
            self.state.top_left(),
            self.state.top_right(),
            self.state.bottom_left(),
            self.state.bottom_right(),
        ]
        for name, pt in zip(names, pts):
            self.rectangles[name] = Rectangle(
                self.canvas,
                state=RectangleState(
                    pt,
                    size_state=self.style.rectangle_size,
                    color_state=self.style.rectangle_color,
                    outline=self.style.rectangle_outline,
                    outline_width=self.style.rectangle_outline_width,
                ),
            )

    def delete(self) -> None:
        for line in self.lines.values():
            line.delete()

        for rectangle in self.rectangles.values():
            rectangle.delete()
