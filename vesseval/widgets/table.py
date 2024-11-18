from typing import List

import tkinter as tk
from widget_state import HigherOrderState, ListState, StringState

from .label import Label


class RowState(HigherOrderState):

    def __init__(self, key: StringState, value: StringState):
        super().__init__()

        self.key = key
        self.value = value


class TableState(ListState):

    def __init__(self, value: List[RowState]):
        super().__init__(value)


class Table(tk.Frame):

    def __init__(self, parent: tk.Widget, state: TableState):
        super().__init__(parent)

        self.state = state

        key_width = max(map(lambda row: len(row.key.value), self.state)) + 2
        val_width = max(map(lambda row: len(row.value.value), self.state)) + 2

        self.key_labels = [
            Label(self, row.key, width=key_width, anchor=tk.W, bg="#9e9e9e", borderwidth=1, relief="groove") for row in self.state
        ]
        self.value_labels = [
            Label(self, row.value, width=val_width, bg="#9e9e9e", borderwidth=1, relief="groove") for row in self.state
        ]

        for i, (k_label, v_label) in enumerate(zip(self.key_labels, self.value_labels)):
            k_label.grid(row=i, column=0)
            v_label.grid(row=i, column=1)
