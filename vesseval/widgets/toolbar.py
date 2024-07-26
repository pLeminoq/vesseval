import tkinter as tk
from tkinter import ttk

from ..state import BoolState, HigherState


class ToolbarState(HigherState):

    def __init__(self):
        super().__init__()

        self.mouse_mode = BoolState(False)
        self.bounding_box_mode = BoolState(True)

        self._modes = [self.mouse_mode, self.bounding_box_mode]
        for mode in self._modes:
            mode.on_change(self.one_of)

    def one_of(self, state):
        if not state.value:
            return

        for mode in self._modes:
            if mode == state:
                continue
            else:
                mode.set(False)


class Toolbar(tk.Frame):

    def __init__(self, parent: tk.Widget, state: ToolbarState = None):
        super().__init__(parent)

        self.state = state if state is not None else ToolbarState()

        self.button_mouse = tk.Button(
            self, text="Mouse", command=lambda *args: self.state.mouse_mode.set(True)
        )
        self.button_mouse.config(
            state=tk.DISABLED if self.state.mouse_mode.value else tk.NORMAL
        )
        self.state.mouse_mode.on_change(
            lambda state: self.button_mouse.config(
                state=tk.DISABLED if state.value else tk.NORMAL
            )
        )

        self.button_bb = tk.Button(
            self,
            text="Bounding Box",
            command=lambda *args: self.state.bounding_box_mode.set(True),
        )
        self.button_bb.config(
            state=tk.DISABLED if self.state.bounding_box_mode.value else tk.NORMAL
        )
        self.state.bounding_box_mode.on_change(
            lambda state: self.button_bb.config(
                state=tk.DISABLED if state.value else tk.NORMAL
            )
        )

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=7)

        self.button_mouse.grid(column=0, row=0, padx=(10, 0), pady=(10, 10), sticky="W")
        self.button_bb.grid(column=1, row=0, padx=(5, 0), pady=(10, 10), sticky="W")
