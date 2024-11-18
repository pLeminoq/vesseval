from typing import Callable
from typing_extensions import Self

import tkinter as tk
from widget_state import State


class CanvasItem:

    def __init__(self, canvas: tk.Canvas, state: State):
        self.canvas = canvas
        self.state = state
        self.bindings = []

        self.state.on_change(self.redraw)

    def redraw(self, state):
        pass

    def tag_bind(self, binding: str, callback: Callable[[tk.Event, Self], None]):
        self.bindings.append(binding)
        self.canvas.tag_bind(self.id, binding, lambda event: callback(event, self))

    def delete(self):
        for binding in self.bindings:
            self.canvas.tag_unbind(self.id, binding)

        self.canvas.delete(self.id)
