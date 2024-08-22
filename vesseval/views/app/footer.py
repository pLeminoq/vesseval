import tkinter as tk

from ...state import StringState, HigherState
from ...widgets.label import Label


class FooterState(HigherState):

    def __init__(self):
        super().__init__()

        self.background_color = StringState("#aeaeae")
        self.info_text = StringState("")


class Footer(tk.Frame):

    def __init__(self, parent: tk.Widget, state: FooterState):
        super().__init__(parent)

        self.state = state
        self.state.on_change(lambda state: self.config(bg=state.background_color.value), trigger=True)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.info_label = Label(self, state=self.state.info_text, bg=self.state.background_color.value)
        self.info_label.grid(column=0, row=0)

