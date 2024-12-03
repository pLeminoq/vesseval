import tkinter as tk
from tkinter import ttk
from widget_state import BoolState, HigherOrderState

from ..resources import icons

"""
Die Toolbar erlaubt das auswählen eines von mehreren Modis
Modi implementieren:
  * 
"""


class ToolbarState(HigherOrderState):

    def __init__(self):
        super().__init__()

        self.point_mode = BoolState(True)
        self.box_mode = BoolState(False)

        self._default_mode = self.point_mode

        self._modes = [self.point_mode, self.box_mode]
        for mode in self._modes:
            mode.on_change(self.one_of)

    def one_of(self, state):
        """
        If a mode becomes active, deactivate all other modes.

        Ensure that at least one mode is active at all times.
        """
        if not state.value:
            # if no mode is active, activate the default mode
            if not any(map(lambda s: s.value, self._modes)):
                self._default_mode.value = True
            return

        for i, mode in enumerate(self._modes):
            if mode == state:
                continue
            else:
                mode.set(False)


class Toolbar(tk.Frame):

    def __init__(self, parent: tk.Widget, state: ToolbarState = None):
        super().__init__(parent, bg="#aeaeae")

        self.state = state if state is not None else ToolbarState()

        self.point_image = icons["arrow"].tk_image(height=40)
        self.point_button = tk.Button(
            self,
            image=self.point_image,
            command=lambda *args: self.state.point_mode.set(True),
        )
        self.state.point_mode.on_change(
            lambda state: self.point_button.config(
                state=tk.DISABLED if state.value else tk.NORMAL
            ),
            trigger=True,
        )

        self.box_image = icons["rectangle"].tk_image(height=40)
        self.box_button = tk.Button(
            self,
            image=self.box_image,
            command=lambda *args: self.state.box_mode.set(True),
        )
        self.state.box_mode.on_change(
            lambda state: self.box_button.config(
                state=tk.DISABLED if state.value else tk.NORMAL
            ),
            trigger=True,
        )

        self.point_button.grid(
            column=0, row=0, padx=(10, 0), pady=(10, 10), sticky=tk.W
        )
        self.box_button.grid(column=1, row=0, padx=(5, 0), pady=(10, 10), sticky=tk.W)
