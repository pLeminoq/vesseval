from typing import List

import numpy as np
import tkinter as tk

from ...state import ListState, PointState

from .line import Line, LineState
from .rectangle import Rectangle, RectangleState


class ContourState(ListState):

    def __init__(self, points: List[PointState]):
        super().__init__(points)

    @classmethod
    def from_numpy(cls, contour:np.array):
        return cls([PointState(*pt) for pt in contour])

    def to_numpy(self):
        return np.array([(pt.x.value, pt.y.value) for pt in self])





class Contour:

    def __init__(self, canvas: tk.Canvas, state: ContourState):
        self.canvas = canvas
        self.state = state

        self.canvas_items = []

        self.redraw()
        self.state.on_change(lambda *args: self.redraw())

    def redraw(self):
        self.clear()

        for point_state in self.state:
            rectangle = Rectangle(
                self.canvas, RectangleState(point_state, color_state="red")
            )
            rectangle.tag_bind("<B1-Motion>", self.move_rectangle)
            rectangle.tag_bind("<Button-3>", self.delete_rectangle)
            self.canvas_items.append(rectangle)
        lowest_rectanlge = self.canvas_items[0]

        for pt_1, pt_2 in zip(self.state, [*self.state[1:], self.state[0]]):
            line = Line(self.canvas, LineState(pt_1, pt_2, "white"))
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
        self.state.remove(rectangle.state.center_state)

    def create_rectangle(self, event, line):
        idx = self.state.index(line.state.end_state)
        self.state.insert(idx, PointState(event.x, event.y))
