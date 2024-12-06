import tkinter as tk

from widget_state import StringState, ListState


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


def virtual_list(list_state, acces_func) -> ListState:
    _virtual_list = ListState()

    def update_virtual_list(*args):
        _list = list(map(acces_func, list_state))

        changed = False
        if len(_virtual_list) != len(_list):
            changed = True
        else:
            for virtual, real in zip(_virtual_list, _list):
                if virtual != real:
                    changed = True
                    break

        if not changed:
            return

        with _virtual_list:
            _virtual_list.clear()
            _virtual_list.extend(_list)

    list_state.on_change(update_virtual_list, trigger=True)
    return _virtual_list
