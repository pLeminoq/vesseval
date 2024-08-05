from typing import List

import numpy as np
import tkinter as tk

from ...state import HigherState, ContourState

from .line import Line, LineState
from .rectangle import Rectangle, RectangleState


class DisplayContourState(HigherState):

    def __init__(
        self,
        contour: ContourState,
        rectangle_size: int = 9,
        rectangle_color: str = "blue",
        line_color: str = "white",
    ):
        super().__init__()

        self.contour = contour
        self.rectangle_size = rectangle_size
        self.rectangle_color = rectangle_color
        self.line_color = line_color


class Contour:

    def __init__(self, canvas: tk.Canvas, state: DisplayContourState):
        self.canvas = canvas
        self.state = (
            state if type(state) == DisplayContourState else DisplayContourState(state)
        )

        self.canvas_items = []

        self.redraw()
        self.state.on_change(lambda *args: self.redraw())

    def redraw(self):
        self.clear()

        if len(self.state.contour) == 0:
            return

        for point_state in self.state.contour:
            rectangle = Rectangle(
                self.canvas,
                RectangleState(
                    point_state,
                    color_state=self.state.rectangle_color,
                    size_state=self.state.rectangle_size,
                ),
            )
            rectangle.tag_bind("<B1-Motion>", self.move_rectangle)
            rectangle.tag_bind("<Button-3>", self.delete_rectangle)
            self.canvas_items.append(rectangle)
        lowest_rectanlge = self.canvas_items[0]

        for pt_1, pt_2 in zip(
            self.state.contour, [*self.state.contour[1:], self.state.contour[0]]
        ):
            line = Line(self.canvas, LineState(pt_1, pt_2, self.state.line_color))
            line.tag_bind("<Double-Button-1>", self.create_rectangle)
            self.canvas.tag_lower(line.id, lowest_rectanlge.id)
            self.canvas_items.append(line)

    def clear(self):
        for obj in self.canvas_items:
            obj.delete()

        self.canvas_items = []

    def move_rectangle(self, event, rectangle):
        # TODO: validate that not moved outside of canvas
        rectangle.state.center_state.set(event.x, event.y)

    def delete_rectangle(self, event, rectangle):
        self.state.contour.remove(rectangle.state.center_state)

    def create_rectangle(self, event, line):
        idx = self.state.contour.index(line.state.end_state)
        self.state.contour.insert(idx, PointState(event.x, event.y))
