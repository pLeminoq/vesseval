"""
Components for a dialog to open a file.
"""

import os

import tkinter as tk
from tkinter import filedialog, ttk

from ...state import app_state, StringState

from .widgets import FileSelection, FileSelectionState


class OpenImageDialog(tk.Toplevel):
    """
    Dialog to select the image to be reoriented.
    """

    def __init__(self):
        super().__init__()

        self.app_state = app_state

        self.file_selection = FileSelection(
            self,
            FileSelectionState(
                label="Image", filename=self.app_state.filename_state.value
            ),
        )
        self.button = ttk.Button(self, text="Confirm", command=self.on_confirm)

        self.file_selection.state.filename.on_change(self.enable_button, trigger=True)

        self.file_selection.grid(column=0, row=0, pady=5)
        self.button.grid(column=0, row=1, pady=5)

        self.bind("<Return>", self.on_confirm)

    def selection_is_valid(self):
        """
        Validate if the selection is valid (files exist).
        """
        return os.path.isfile(self.file_selection.state.filename.value)

    def enable_button(self, *args):
        """
        Enable/Disable the confirmation button.
        """
        self.button["state"] = tk.ACTIVE if self.selection_is_valid() else tk.DISABLED

    def on_confirm(self, *args):
        """
        Update the app state on confirmation.
        """
        if not self.selection_is_valid():
            return

        self.app_state.filename_state.value = self.file_selection.state.filename.value

        # remove the dialog after confirmation
        self.destroy()
        self.update()
