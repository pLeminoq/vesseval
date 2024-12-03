import functools

import tkinter as tk
from widget_state import State


def stateful(cls):
    """
    Make a widget stateful.

    This means that it has a state attribute and if its
    state changes, its `draw` method is called so
    that its appearance changes.

    There are three conditions:
      * the widget must either extend from the tk.Widget class or
        return a tk.Widget via its `widget` attribute
      * the widget must receive a `State` as positional or keyword argument
      * the widget must implement a `draw` method

    Note: This functions maps a change of the `state` to a virtual
    tkinter event. The reason for this is that state changes may
    occur in separate threads. Firing a tkinter event means that the
    GUI thread is responsible for executing the `draw` function.
    """
    orig_init = cls.__init__

    @functools.wraps(orig_init)
    def __init__(self, *args, **kwargs):
        if "state" in kwargs and isinstance(kwargs["state"], State):
            state = kwargs["state"]
        else:
            for arg in args:
                if isinstance(arg, State):
                    state = arg
                    break
        assert state is not None, f"Could not detect state in {args=} or {kwargs=}"

        self.state = state
        self.event_id = f"<<{hash(self.state)}_{self.state.__class__.__name__}>>"

        orig_init(self, *args, **kwargs)

        assert isinstance(self, tk.Widget) or (
            hasattr(self, "widget") and isinstance(self.widget, tk.Widget)
        ), f"Widget {cls.__name__} is not a tk.Widget nor does it provide access to one via a `widget` attribute"
        assert hasattr(
            self, "draw"
        ), f"Widget {cls.__name__} doe not provide a `draw` function"

        widget = self if isinstance(self, tk.Widget) else self.widget

        self.state.on_change(lambda _: widget.event_generate(self.event_id))
        widget.bind(self.event_id, lambda _: self.draw())

        self.draw()

    cls.__init__ = __init__
    return cls
