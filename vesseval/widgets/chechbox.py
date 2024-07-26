import tkinter as tk

from ..state import BoolState, HigherState, StringState

class CheckboxState(HigherState):

    def __init__(self, bool_state: BoolState, label_state: StringState = ""):
        super().__init__()

        self.bool_state = bool_state
        self.label_state = label_state

class Checkbox(tk.Frame):

    def __init__(self, parent: tk.Frame, state: CheckboxState):
        super().__init__(parent)

        self.state = state
        self.var = tk.BooleanVar(value=self.state.bool_state.value)

        self.state.bool_state.on_change(lambda state: self.var.set(state.value))
        self.var.trace_add("write", lambda *args: self.state.bool_state.set(self.var.get()))

        self.checkbutton = tk.Checkbutton(self, text=self.state.label_state.value, variable=self.var)
        self.checkbutton.grid()

