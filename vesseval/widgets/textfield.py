import tkinter as tk
from tkinter import ttk
from widget_state import IntState, StringState, FloatState

from ..state.util import to_tk_string_var


class TextField(ttk.Entry):
    """
    Text field displaying the value of a `StringState`.
    """

    def __init__(self, parent: tk.Widget, state: StringState, **kwargs):
        super().__init__(parent, textvariable=to_tk_string_var(state), **kwargs)

        self.state = state


class IntTextField(TextField):
    """
    Text field displaying the value of an `IntState`.
    """

    def __init__(self, parent: tk.Widget, state: IntState, **kwargs):
        as_str = state.transform(lambda state: StringState(f"{state.value}"))
        as_str.on_change(lambda _: state.set(state.value if as_str.value == "" else int(as_str.value)))
        super().__init__(
            parent,
            as_str,
            validate="key",
            validatecommand=(parent.register(self.validate), "%P"),
        )

    def validate(self, text: str) -> bool:
        return text == "" or text.isdigit()


class FloatTextField(TextField):
    """
    Text field displaying the value of a `FloatState`.
    """

    def __init__(self, parent: tk.Widget, state: FloatState, **kwargs):
        as_str = state.transform(lambda state: StringState(f"{state.value}"))
        as_str.on_change(lambda _: state.set(state.value if as_str.value == "" else float(as_str.value)))
        super().__init__(
            parent,
            as_str,
            validate="key",
            validatecommand=(parent.register(self.validate), "%P"),
            justify="right",
        )

    def validate(self, text: str) -> bool:
        if text == "":
            return True

        try:
            float(text)
        except ValueError:
            return False

        return True

