"""
Components for a dialog to open a file.
"""

import os

import tkinter as tk
from tkinter import filedialog, ttk

from ...state import StringState

from .widgets import FileSelection, FileSelectionState


class AbstractOpenDialog(tk.Toplevel):

    def __init__(
        self, filename_state: StringState, label: str = "Image", file_type: str = "file"
    ):
        super().__init__()

        self.filename_state = filename_state
        self.file_selection = FileSelection(
            self,
            FileSelectionState(
                # the filename is a copy of the internal state, so that an update of the given
                # value only occurs on confirmation
                label=label,
                filename=self.filename_state.value,
                file_type=file_type,
            ),
        )

        self.button = ttk.Button(self, text="Confirm", command=self.on_confirm)
        self.enable_button()

        self.file_selection.state.filename.on_change(self.on_confirm)

        self.file_selection.grid(column=0, row=0, pady=5)
        self.button.grid(column=0, row=1, pady=5)

        self.bind("<Return>", self.on_confirm)

    def selection_is_valid(self):
        raise TypeError(
            f"selection_is_valid not implemented for abstract class: {type(self)}"
        )

    def enable_button(self, *args):
        """
        Enable/Disable the confirmation button.
        """
        self.button["state"] = tk.ACTIVE if self.selection_is_valid() else tk.DISABLED

    def on_confirm(self, *args):
        if not self.selection_is_valid():
            return

        self.filename_state.value = self.file_selection.state.filename.value

        # remove the dialog after confirmation
        self.destroy()
        self.update()


class OpenFileDialog(AbstractOpenDialog):
    """
    Dialog to select a file to be opened.
    """

    def __init__(self, filename_state: StringState, label: str = "File"):
        super().__init__(filename_state, label)

    def selection_is_valid(self):
        """
        Validate if the selection is valid (files exist).
        """
        return os.path.isfile(self.file_selection.state.filename.value)


class SaveAsFileDialog(AbstractOpenDialog):

    def __init__(self, filename_state: StringState, label: str = "Save as"):
        super().__init__(filename_state, label, file_type="save")

    def selection_is_valid(self):
        filename = self.file_selection.state.filename.value
        if not os.path.exists(filename):
            return True

        return os.path.splitext(filename)[1] == ".zip"


class OpenDirectoryDialog(AbstractOpenDialog):
    """
    Dialog to select a directory.
    """

    def __init__(self, filename_state: StringState, label: str = "Directory"):
        super().__init__(filename_state, label, file_type="directory")

    def selection_is_valid(self):
        """
        Validate if the selection is a directory.
        """
        return os.path.isdir(self.file_selection.state.filename.value)
