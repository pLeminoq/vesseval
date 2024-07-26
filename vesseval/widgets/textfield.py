import tkinter as tk
from tkinter import ttk

from ..state import IntState


class IntTextField(tk.Frame):
    """
    Text field displaying the value of a DoubleVar.

    It shows a label to identify the variable and the variable is modifiable
    in a text field with input validation.
    """

    def __init__(self, parent: tk.Widget, state: IntState):
        super().__init__(parent)

        self.state = state

        self.text_var = tk.StringVar(value=f"{state.value}")
        self.text_var.trace_add(
            "write", lambda *args: self.state.set(int(self.text_var.get()))
        )
        self.state.on_change(lambda state: self.text_var.set(f"{state.value}"))

        self.entry = ttk.Entry(
            self,
            textvariable=self.text_var,
            validate="key",
            validatecommand=(self.register(self.validate), "%P"),
        )

        self.entry.grid()

    def validate(self, text: str) -> bool:
        return text.isdigit()
