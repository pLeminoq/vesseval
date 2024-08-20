import tkinter as tk
from tkinter import ttk

from ..dialog.open import SaveAsFileDialog

from .cell_layer import CellLayerView, CellLayerState
from .state import ResultViewState


class MenuFileResult(tk.Menu):

    def __init__(self, menu_bar: tk.Menu, state: ResultViewState):
        super().__init__(menu_bar)

        self.state = state
        self.save_filename = self.state.save_filename

        menu_bar.add_cascade(menu=self, label="File")

        self.add_command(label="Save", command=self.save)
        self.add_command(label="Save as", command=self.save_as)

        self.save_filename.on_change(
            lambda state: self.entryconfigure(
                0, state=tk.DISABLED if state.value == "" else tk.ACTIVE
            ),
            trigger=True,
        )

    def save(self):
        self.state.save()

    def save_as(self):
        SaveAsFileDialog(self.save_filename)


class ResultMenuBar(tk.Menu):
    def __init__(self, top_level: tk.Toplevel, state: ResultViewState):
        super().__init__(top_level)

        top_level.option_add("*tearOff", False)
        top_level["menu"] = self

        self.menu_file = MenuFileResult(self, state)


class ResultView(tk.Toplevel):

    def __init__(self, state: ResultViewState):
        super().__init__()

        self.state = state

        self.menu_bar = ResultMenuBar(self, self.state)

        self.cell_layer_view_1 = CellLayerView(self, self.state.cell_layer_state_1)
        self.cell_layer_view_2 = CellLayerView(self, self.state.cell_layer_state_2)
        self.button = ttk.Button(self, text="Copy", command=self.on_copy)

        self.cell_layer_view_1.grid(row=0, column=0, padx=5)
        self.cell_layer_view_2.grid(row=0, column=1, padx=5)
        self.button.grid(row=1, column=0, columnspan=2, pady=5)

        self.bind("<Key-q>", lambda event: self.destroy())

    def on_copy(self, *args):
        values = []
        for state in [self.state.cell_layer_state_1, self.state.cell_layer_state_2]:
            values.append(state.inner_length.value)
            values.append(state.outer_length.value)
            values.append(state.contour_area.value)
            values.append(state.cell_area.value)
            values.append(state.surround.value)
            values.append(state.thickness.value)
        values = list(map(str, values))

        self.clipboard_clear()
        self.clipboard_append("\t".join(values))

