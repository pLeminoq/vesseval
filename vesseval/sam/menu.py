"""
Components of the menu bar.
"""

import os

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from widget_state import StringState

from ..state.util import to_tk_string_var
from ..views.dialog.open import OpenFileDialog, SaveAsFileDialog
from ..widgets.textfield import FloatTextField
from ..widgets.label import Label
from .state import app_state


class MenuFile(tk.Menu):
    """
    The File menu containing options to
      * open an image
    """

    def __init__(self, menu_bar):
        super().__init__(menu_bar)

        menu_bar.add_cascade(menu=self, label="File")

        # add commands
        self.add_command(label="Open", command=self.open)
        self.add_separator()
        self.add_command(label="Save", command=self.save)
        self.add_command(label="Save As", command=self.save_as)
        self.add_separator()
        self.add_command(label="Load", command=self.load)

        app_state.filename_save.on_change(
            lambda state: self.entryconfigure(
                2, state=tk.DISABLED if state.value == "" else tk.ACTIVE
            ),
            trigger=True,
        )

    def open(self):
        """
        Open a new image with a user dialog.
        """
        # OpenFileDialog(app_state.filename, label="Image")
        app_state.filename.set(filedialog.askopenfilename())

    def save_as(self):
        SaveAsFileDialog(app_state.filename_save)

    def save(self):
        app_state.save()

    def load(self):
        filename = StringState("")
        filename.on_change(lambda state: app_state.load(state.value))

        OpenFileDialog(filename, label="App State")


class MenuTools(tk.Menu):
    """
    The File menu containing options to
      * open an image
    """

    def __init__(self, menu_bar):
        super().__init__(menu_bar)

        menu_bar.add_cascade(menu=self, label="Tools")

        # add commands
        self.add_command(label="Eval", command=self.eval)

    def eval(self):
        table = app_state.eval_regions()

        rows = []
        for i in range(len(table["filename"])):
            row = list(map(lambda key: str(table[key][i]), table.keys()))
            rows.append("\t".join(row))
        txt = "\n".join(rows)
        print("\t".join(list(table.keys())))
        print(txt)
        print()

        self.clipboard_clear()
        self.clipboard_append(txt)

class MenuOptions(tk.Menu):
    """
    The File menu containing options to
      * open an image
    """

    def __init__(self, menu_bar):
        super().__init__(menu_bar)

        menu_bar.add_cascade(menu=self, label="Options")

        # add commands
        self.add_command(label="Config", command=self.config)

    def config(self):
        config_view = tk.Toplevel()
        config_view.bind("<Key-q>", lambda _: config_view.destroy())

        units = ["m", "mm", "µm", "nm"]

        size_x_text_field = FloatTextField(config_view, app_state.pixel_size_x)
        size_x_text_field.grid(row=0, column=1, padx=(2, 10), pady=5)
        size_x_label = Label(config_view, StringState("Pixel Size X:"))
        size_x_label.grid(row=0, column=0, sticky="w", padx=(10, 2))

        size_y_text_field = FloatTextField(config_view, app_state.pixel_size_y)
        size_y_text_field.grid(row=1, column=1, padx=(2, 10), pady=5)
        size_y_label = Label(config_view, StringState("Pixel Size Y:"))
        size_y_label.grid(row=1, column=0, sticky="w", padx=(10, 2))

        unit_dropdown = tk.OptionMenu(config_view, to_tk_string_var(app_state.pixel_unit), *units)
        unit_dropdown.grid(row=0, column=2, rowspan=2)
        
        button = ttk.Button(config_view, text="Save", command=lambda *_: config_view.destroy())
        button.grid(row=2, column=0, columnspan=3, pady=5)


class MenuBar(tk.Menu):
    """
    Menu bar of the app.
    """

    def __init__(self, root: tk.Widget):
        super().__init__(root)

        root.option_add("*tearOff", False)
        root["menu"] = self

        self.menu_file = MenuFile(self)
        self.menu_tools = MenuTools(self)
        self.menu_options = MenuOptions(self)
