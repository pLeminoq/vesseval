import tkinter as tk
from tkinter import filedialog, ttk

from ....state import StringState, HigherState
from ....widgets import Label
from ....widgets import TextField


class FileSelectionState(HigherState):

    def __init__(
        self, label: StringState, filename: StringState = "", file_type="file"
    ):
        super().__init__()

        self.label = label
        self.filename = filename
        self.file_type = file_type


class FileSelection(tk.Frame):
    """
    Widget used to select a file.

    It displays as: <label> <text> <button>
    The user can either type the filename in the text field or
    open a dialog by clicking on the button.
    """

    def __init__(self, parent: tk.Widget, state: FileSelectionState):
        """
        Create a new file selection widget.

        Parameters
        ----------
        parent: tk.Widget
            the parent widget
        label: str
            text displayed to the user to identify the kind of file to be opened
        """
        super().__init__(parent)

        self.state = state

        self.label = Label(self, self.state.label, anchor=tk.E, width=20)
        self.textfield = TextField(self, self.state.filename, width=80)
        self.button = ttk.Button(
            self,
            text="Open",
            width=15,
            command=lambda *args: self.state.filename.set(
                filedialog.askopenfilename()
                if self.state.file_type.value == "file"
                else filedialog.askdirectory()
            ),
        )

        self.label.grid(column=0, row=0, padx=5)
        self.textfield.grid(column=1, row=0, padx=5)
        self.button.grid(column=2, row=0, padx=(5, 10))
