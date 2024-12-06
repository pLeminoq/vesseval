"""
Components of the menu bar.
"""

import os

import tkinter as tk
from tkinter import filedialog
from widget_state import StringState

from ..views.dialog.open import OpenFileDialog, SaveAsFileDialog
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
        OpenFileDialog(app_state.filename, label="Image")

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
        print(txt)
        print()

        self.clipboard_clear()
        self.clipboard_append(txt)


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
