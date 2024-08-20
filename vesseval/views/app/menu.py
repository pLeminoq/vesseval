"""
Components of the menu bar.
"""

import os

import tkinter as tk
from tkinter import filedialog

from ...state import StringState
from ...util import mask_image
from ..preprocessing import PreprocessingView, PreprocessingViewState
from ..dialog.open import OpenFileDialog, OpenDirectoryDialog
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

        app_state.save_directory.on_change(
            lambda save_directory: self.entryconfigure(
                2, state=tk.DISABLED if save_directory.value == "" else tk.ACTIVE
            ),
            trigger=True,
        )

    def open(self):
        """
        Open a new image with a user dialog.
        """
        OpenFileDialog(app_state.filename_state, label="Image")

    def save_as(self):
        OpenDirectoryDialog(app_state.save_directory, label="Save Directory")

    def save(self):
        app_state.save()

    def load(self):
        load_directory = StringState("")
        load_directory.on_change(lambda state: app_state.load(state.value))

        OpenDirectoryDialog(load_directory, label="Save Directory")


class MenuTools(tk.Menu):

    def __init__(self, menu_bar: tk.Menu):
        super().__init__(menu_bar)

        menu_bar.add_cascade(menu=self, label="Tools")

        self.add_command(
            label="Process Contour",
            command=lambda *args: PreprocessingView(
                PreprocessingViewState(
                    mask_image(
                        app_state.state.display_image_state,
                        app_state.state.contour_state,
                    )
                )
            ),
        )
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
