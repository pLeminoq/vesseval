"""
Components of the menu bar.
"""

import os

import tkinter as tk
from tkinter import filedialog

from ..state.app import app_state
from .file_dialog import FileDialog


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

    def open(self):
        """
        Open a new image with a user dialog.
        """
        FileDialog()


class MenuBar(tk.Menu):
    """
    Menu bar of the app.
    """

    def __init__(self, root: tk.Widget):
        super().__init__(root)

        root.option_add("*tearOff", False)
        root["menu"] = self

        self.menu_file = MenuFile(self)
