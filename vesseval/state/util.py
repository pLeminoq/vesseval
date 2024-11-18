import tkinter as tk

from widget_state import StringState

def to_tk_string_var(state: StringState) -> tk.StringVar:
    """
    Create a `tk.StringVar` connected to a `StringState`.

    This means that both will have the same value all the time.

    Returns
    -------
    tk.StringVar
    """

    string_var = tk.StringVar(value=state.value)
    string_var.trace_add("write", lambda *args: state.set(string_var.get()))
    state.on_change(lambda _: string_var.set(state.value))
    return string_var
