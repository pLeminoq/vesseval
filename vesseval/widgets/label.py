import tkinter as tk

from ..state import StringState


class Label(tk.Label):

    def __init__(self, parent: tk.Widget, state: StringState, **kwargs):
        super().__init__(parent, text=state.value, **kwargs)

        self.state = state
        self.state.on_change(lambda state: self.config(text=state.value))
