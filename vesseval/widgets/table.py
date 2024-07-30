from typing import List

import tkinter as tk

from ..state import HigherState, ListState, StringState
from .label import Label

class RowState(HigherState):

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
        self.key_labels = [Label(self, row.key) for row in self.state]
        self.value_labels = [Label(self, row.value) for row in self.state]

        for i, (k_label, v_label) in enumerate(zip(self.key_labels, self.value_labels)):
            k_label.grid(row=i, column=0)
            v_label.grid(row=i, column=1)

