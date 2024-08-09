import tkinter as tk
from tkinter import ttk

from ..state import IntState, StringState


class TextField(ttk.Entry):
    """
    Text field displaying the value of a `StringState`.
    """

    def __init__(self, parent: tk.Widget, state: StringState, **kwargs):
        super().__init__(parent, textvariable=state.to_tk_string_var(), **kwargs)

        self.state = state


class IntTextField(TextField):
    """
    Text field displaying the value of an `IntState`.
    """

    def __init__(self, parent: tk.Widget, state: IntState, **kwargs):
        super().__init__(
            parent,
            state.transform(lambda state: StringState(f"{state.value}")),
            validate="key",
            validatecommand=(self.register(self.validate), "%P"),
        )

    def validate(self, text: str) -> bool:
        return text.isdigit()
