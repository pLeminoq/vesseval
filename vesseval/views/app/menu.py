"""
Components of the menu bar.
"""

import os

import tkinter as tk
from tkinter import filedialog

from ...state.app import app_state
from ..preprocessing import PreprocessingView
from ..dialog.open_image import OpenImageDialog


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
        OpenImageDialog()


class MenuTools(tk.Menu):

    def __init__(self, menu_bar: tk.Menu):
        super().__init__(menu_bar)

        menu_bar.add_cascade(menu=self, label="Tools")

        self.add_command(label="Process Contour", command=lambda *args: PreprocessingView())
        app_state.contour_state.on_change(self.on_contour, trigger=True)

    def on_contour(self, contour_state):
        self.entryconfigure(
            0, state=tk.DISABLED if len(contour_state) < 3 else tk.ACTIVE
        )


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
